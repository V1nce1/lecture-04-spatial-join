import argparse
import webbrowser
import hashlib
import pickle
import threading
import time
import importlib
import logging
from flask import Flask, Response, jsonify
from pathlib import Path
from typing import List, Tuple, Optional

from data.util import load_both_datasets
from rtree.rtree import RTree, Point


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def collect_leaf_mbrs(node) -> List[Tuple[float, float, float, float, int]]:
	"""Traverse Node objects and collect leaf MBRs as tuples (x1,y1,x2,y2,count).

	The function is defensive: if a node doesn't expose is_leaf/mbr, it will
	silently skip it.
	"""
	leaves: List[Tuple[float, float, float, float, int]] = []
	try:
		is_leaf = node.is_leaf()
	except Exception:
		is_leaf = False
	if is_leaf:
		m = node.mbr
		if m is not None:
			# count points directly under this leaf
			cnt = sum(1 for c in node.children if isinstance(c, Point))
			leaves.append((m.x1, m.y1, m.x2, m.y2, cnt))
	else:
		for c in node.children:
			if not isinstance(c, Point):
				leaves.extend(collect_leaf_mbrs(c))
	return leaves


def file_hash(path: Path) -> str:
	h = hashlib.sha256()
	try:
		with path.open('rb') as f:
			while True:
				chunk = f.read(8192)
				if not chunk:
					break
				h.update(chunk)
	except FileNotFoundError:
		return ''
	return h.hexdigest()


def build_site(output_dir: Path, limit: Optional[int] = None):
	"""Build visualization artifacts and write static site files into output_dir.

	Returns: (index_html, towers_points, cities_points, leaf_mbrs, bbox)
	"""
	# prepare cache directory
	cache_dir = output_dir / '.cache'
	cache_dir.mkdir(parents=True, exist_ok=True)

	repo_root = Path(__file__).parent
	csv_path = repo_root / 'data' / 'Cellular_Towers.csv'
	cities_path = repo_root / 'data' / 'uscities.csv'
	rtree_path = repo_root / 'rtree' / 'rtree.py'
	csv_hash = file_hash(csv_path)
	cities_hash = file_hash(cities_path)
	rtree_hash = file_hash(rtree_path)
	cache_key = hashlib.sha256(f"{csv_hash}:{cities_hash}:{rtree_hash}:{limit}".encode('utf-8')).hexdigest()
	cache_file = cache_dir / f'site_cache_{cache_key}.pkl'

	if cache_file.exists():
		try:
			with cache_file.open('rb') as f:
				cached = pickle.load(f)
			logger.info('Loaded visualization artifacts from cache')
			return cached['index_html'], cached['towers_points'], cached['cities_points'], cached['leaf_mbrs'], cached['bbox']
		except Exception as e:
			logger.warning('Cache load failed, rebuilding: %s', e)

	towers, cities = load_both_datasets(limit=limit)
	all_pts = towers + cities
	tree = RTree(node_capacity=16)
	for p in all_pts:
		tree.insert(p)

	output_dir.mkdir(parents=True, exist_ok=True)

	# collect leaf MBRs
	leaf_mbrs = collect_leaf_mbrs(tree.root)

	minLon = min(p.x for p in all_pts) if all_pts else -180.0
	maxLon = max(p.x for p in all_pts) if all_pts else 180.0
	minLat = min(p.y for p in all_pts) if all_pts else -90.0
	maxLat = max(p.y for p in all_pts) if all_pts else 90.0

	# prepare raw_points with radius - separate towers and cities
	towers_points = [(p.x, p.y, p.radius) for p in towers]
	cities_points = [(p.x, p.y, p.radius) for p in cities]

	with open('assets/visualize.html', 'r', encoding='utf-8') as f:
		index_html = f.read()

	# substitute placeholders with numeric values
	center_lat = (minLat + maxLat) / 2
	center_lon = (minLon + maxLon) / 2
	index_html = index_html.replace('CENTER_LAT', str(center_lat)).replace('CENTER_LON', str(center_lon))

	# save artifacts to cache
	try:
		with cache_file.open('wb') as f:
			pickle.dump({
				'index_html': index_html,
				'towers_points': towers_points,
				'cities_points': cities_points,
				'leaf_mbrs': leaf_mbrs,
				'bbox': (minLon, minLat, maxLon, maxLat),
			}, f)
		logger.info('Wrote visualization artifacts to cache: %s', cache_file)
	except Exception as e:
		logger.warning('Failed to write cache: %s', e)

	return index_html, towers_points, cities_points, leaf_mbrs, (minLon, minLat, maxLon, maxLat)

def serve_site(output_dir: Path, index_html: str, port: int = 8000, towers_points=[], cities_points=[], leaf_mbrs=[], fullmap_bbox=None):
	"""Serve the generated site and watch for source changes.

	The function launches Flask and a background watcher thread that rebuilds
	artifacts when data files or rtree.py change.
	"""
	app = Flask(__name__, static_folder=str(output_dir), static_url_path='')
	# shared state updated by watcher thread
	state = {
		'towers_points': towers_points,
		'cities_points': cities_points,
		'leaf_mbrs': leaf_mbrs,
		'fullmap_bbox': fullmap_bbox,
	}

	@app.route('/')
	def index():
		return Response(index_html, mimetype='text/html')

	@app.route('/api/data.json')
	def api_data():
		# prefer dynamic state if available
		data = {
			'towers': state.get('towers_points', []),
			'cities': state.get('cities_points', []),
			'leaf_mbrs': [
				{'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'count': cnt} for (x1, y1, x2, y2, cnt) in state.get('leaf_mbrs', [])
			],
			'bbox': state.get('fullmap_bbox') or (),
		}
		return jsonify(data)

	def watcher_thread():
		repo_root = Path(__file__).parent
		csv_path = repo_root / 'data' / 'Cellular_Towers.csv'
		cities_path = repo_root / 'data' / 'uscities.csv'
		rtree_path = repo_root / 'rtree' / 'rtree.py'
		last_csv = None
		last_cities = None
		last_rtree = None
		while True:
			try:
				cur_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest() if csv_path.exists() else ''
				cur_cities = hashlib.sha256(cities_path.read_bytes()).hexdigest() if cities_path.exists() else ''
				cur_rtree = hashlib.sha256(rtree_path.read_bytes()).hexdigest() if rtree_path.exists() else ''
				if cur_csv != last_csv or cur_cities != last_cities or cur_rtree != last_rtree:
					logger.info('Change detected: rebuilding artifacts...')
					try:
						importlib.reload(importlib.import_module('rtree'))
						index_html, towers_points, cities_points, leaf_mbrs, bbox = build_site(output_dir, limit=None)
						state.update({
							'index_html': index_html,
							'towers_points': towers_points,
							'cities_points': cities_points,
							'leaf_mbrs': leaf_mbrs,
							'fullmap_bbox': bbox
						})
						logger.info('Artifacts updated')
						last_csv, last_cities, last_rtree = cur_csv, cur_cities, cur_rtree
					except Exception as e:
						logger.exception('Rebuild failed: %s', e)
			except Exception:
				pass
			time.sleep(1.0)

	th = threading.Thread(target=watcher_thread, daemon=True)
	th.start()

	url = f'http://localhost:{port}/'
	logger.info('Serving visualization at %s', url)
	webbrowser.open(url)
	app.run(port=port)


def parse_args():
	p = argparse.ArgumentParser(description='Build and serve an R-Tree visualization site')
	p.add_argument('--out', '-o', default=str('./visualization_site'), help='Output directory for the site')
	p.add_argument('--build', action='store_true', help='Do not start a local server after building')
	p.add_argument('--port', type=int, default=8000, help='Port for the server')
	p.add_argument('--limit', type=int, default=None, help='Limit number of points loaded (for debugging)')
	return p.parse_args()


if __name__ == '__main__':
	args = parse_args()
	out = Path(args.out)
	logger.info('Building visualization site in %s', out)
	index_html, towers_points, cities_points, leaf_mbrs, fullmap_bbox = build_site(out, limit=args.limit)
	logger.info('Build complete — artifacts: %d towers, %d cities, %d leaves', len(towers_points), len(cities_points), len(leaf_mbrs))
	if not args.build:
		logger.info('Starting server to serve %s ...', out)
		serve_site(out, index_html, port=args.port, towers_points=towers_points, cities_points=cities_points, leaf_mbrs=leaf_mbrs, fullmap_bbox=fullmap_bbox)
	else:
		logger.info('Site written to %s (run with --serve to start a local server)', out)
