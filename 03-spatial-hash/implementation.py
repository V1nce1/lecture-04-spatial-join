from rtree.rtree import Point, Node
from typing import List, Tuple
import random

def prepare(points_a: List[Point], points_b: List[Point], bucket_count: int=100) -> dict:
    return {"points_a": points_a, "points_b": points_b, "bucket_count": bucket_count}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    points_a = prepared["points_a"]
    points_b = prepared["points_b"]
    bucket_count = prepared["bucket_count"]

    buckets = []

    for i in range(bucket_count):
        index = random.randint(0, len(points_a) - 1)
        point = points_a.pop(index)

        bucket = Node([point])
        bucket.update_mbr()
        buckets.append(bucket)

    for point in points_a:
        min_enlargement = float("inf")
        best_bucket: Node = None
        for bucket in buckets:
            enlargement_factor = bucket.mbr.enlarged_area_with_point(point)
            if enlargement_factor < min_enlargement:
                min_enlargement = enlargement_factor
                best_bucket = bucket
        best_bucket.children.append(point)
        best_bucket.update_mbr()
    

    for point_b in points_b:
        for bucket in buckets:
            if bucket.mbr.intersects(point_b.mbr):
                for point_a in bucket.children:
                    if point_a.mbr.intersects(point_b.mbr):
                        result.append((point_b, point_a))


    return result
