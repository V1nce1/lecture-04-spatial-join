import csv
import random
from typing import Iterator, Tuple, List
from pathlib import Path
from rtree.rtree import Point

def load_cellular_towers(file_path: str) -> Iterator[Point]:
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            idx = int(row[0])
            x = float(row[1])
            y = float(row[2])
            radius = min(25, max(2, (random.gauss(20, 9))))
            radius = radius / 111.0  # Approximate conversion from km to degrees
            yield Point(x, y, radius)

def load_uscities(file_path: str) -> Iterator[Point]:
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        lat_idx = header.index('lat')
        lon_idx = header.index('lng')
        population_idx = header.index('population')
        density_idx = header.index('density')
        for row in reader:
            lat = float(row[lat_idx])
            lon = float(row[lon_idx])
            population = float(row[population_idx])
            density = float(row[density_idx])
            area = population / density if density > 0 and population > 0 else 5.0 # Simple estimation in km2
            radius_km = max(0.5, min(1000.0, (area / 3.14) ** 0.5))  # Convert area to radius
            # Approximate conversion from km to degrees (1 degree ~ 111 km)
            radius = radius_km / 111.0
            yield Point(lon, lat, radius)

def load_both_datasets(limit: int = None) -> Tuple[List[Point], List[Point]]:
    """Load both cellular towers and US cities datasets.
    
    Returns:
        Tuple of (towers, cities) where each is a list of Points
    """
    repo_root = Path(__file__).parent.parent
    towers_path = repo_root / 'data' / 'Cellular_Towers.csv'
    cities_path = repo_root / 'data' / 'uscities.csv'
    
    towers = list(load_cellular_towers(str(towers_path)))
    cities = list(load_uscities(str(cities_path)))
    
    if limit is not None:
        towers = towers[:limit // 2] if limit > 1 else towers[:limit]
        cities = cities[:limit // 2] if limit > 1 else []
    
    return towers, cities
