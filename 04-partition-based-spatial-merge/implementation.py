from rtree.rtree import Point
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point], grid_axis_divisions: int=100) -> dict:
    return {"points_a": points_a, "points_b": points_b, "grid_axis_divisions": grid_axis_divisions}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    # Create grid cells
    result = []
    points_a = prepared["points_a"]
    points_b = prepared["points_b"]
    return result
