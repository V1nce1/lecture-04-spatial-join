from rtree.rtree import Point
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    return {"points_a": points_a, "points_b": points_b}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    points_a = prepared["points_a"]
    points_b = prepared["points_b"]
    return result
