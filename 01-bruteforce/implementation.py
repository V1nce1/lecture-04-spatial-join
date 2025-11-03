from rtree.rtree import Point
from typing import List, Tuple
import tqdm

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    return {"points_a": points_a, "points_b": points_b}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    points_a = prepared["points_a"]
    points_b = prepared["points_b"]
    for point_a in points_a:
        for point_b in points_b:
            if point_a.mbr.intersects(point_b.mbr):
                result.append((point_a, point_b))
    return result
