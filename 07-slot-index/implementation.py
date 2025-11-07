import math
from rtree.rtree import MinimalBoundingRectangle, Point, RTree, Node
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    rtree_a = RTree(node_capacity=32)
    rtree_a.bulk_load(points_a)

    return { "rtree_a": rtree_a, "points_b": points_b, "hash_buckets": 1024 }

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    rtree_a = prepared["rtree_a"]
    points_b = prepared["points_b"]
    hash_buckets = prepared["hash_buckets"]

    # Find topmost level with at least hash_buckets nodes
    current_nodes = [rtree_a.root]
    while len(current_nodes) < hash_buckets:
        children = []
        for node in current_nodes:
            children.extend(node.children)
        current_nodes = list(children)

    # Sort the children by their lower x-bounds
    current_nodes.sort(key=lambda n: n.mbr.x1)

    # Partition children into hash_buckets buckets
    bucket_size = math.ceil(len(current_nodes) / hash_buckets)
    slots = [current_nodes[i:i + bucket_size] for i in range(0, len(current_nodes), bucket_size)]

    slot_mbrs = []
    for slot in slots:
        x1 = min(node.mbr.x1 for node in slot)
        y1 = min(node.mbr.y1 for node in slot)
        x2 = max(node.mbr.x2 for node in slot)
        y2 = max(node.mbr.y2 for node in slot)
        slot_mbrs.append(MinimalBoundingRectangle(x1, y1, x2, y2))

    buckets = [[] for _ in range(len(slots))]

    # For each point in points_b, find matching bucket
    for point_b in points_b:
        for bucket_index, bucket in enumerate(buckets):
            if slot_mbrs[bucket_index].intersects(point_b.mbr):
                bucket.append(point_b)    

    # For each slot, join points from rtree_a with points from corresponding bucket
    for slot_index, slot in enumerate(slots):
        for node in slot:
            leaf_points = node.all_points() if isinstance(node, Node) else [node]
            for point_b in buckets[slot_index]:
                for point_a in leaf_points:
                    if point_a.mbr.intersects(point_b.mbr):
                        result.append((point_a, point_b))

    return result
