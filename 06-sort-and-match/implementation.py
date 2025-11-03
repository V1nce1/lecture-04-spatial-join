import math
from rtree.rtree import Node, Point, RTree, MinimalBoundingRectangle
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    rtree_a = RTree(node_capacity=32)
    rtree_a.bulk_load(points_a)

    return {"rtree_a": rtree_a, "points_b": points_b, "leaf_size": 32}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    rtree_a = prepared["rtree_a"]
    points_b = prepared["points_b"]
    leaf_size = prepared["leaf_size"]
    return result
