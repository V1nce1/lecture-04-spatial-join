from rtree.rtree import Point, RTree
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    rtree_a = RTree(node_capacity=32)
    rtree_a.bulk_load(points_a)

    rtree_b = RTree(node_capacity=32)
    rtree_b.bulk_load(points_b)

    return {"rtree_a": rtree_a, "rtree_b": rtree_b}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    rtree_a = prepared["rtree_a"]
    rtree_b = prepared["rtree_b"]
    return result
