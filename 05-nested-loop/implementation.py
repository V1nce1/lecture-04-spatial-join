from rtree.rtree import Node, Point, RTree
from typing import List, Tuple

def prepare(points_a: List[Point], points_b: List[Point]) -> dict:
    rtree_a = RTree(node_capacity=32)
    rtree_a.bulk_load(points_a)

    return {"rtree_a": rtree_a, "points_b": points_b}

def join(prepared: dict) -> List[Tuple[Point, Point]]:
    result = []
    rtree_a = prepared["rtree_a"]
    points_b = prepared["points_b"]

    for point_b in points_b:
        # range query
        points_a = rangeQuery(rtree_a.root, point_b)
        for point_a in points_a:
            result.append((point_a, point_b))

    return result


def rangeQuery(node: Node, query: Point) -> List[Point]:
    childrenToSearch: List[Node] = []
    results: List[Point] = []

    for child in node.children:
        if child.mbr.intersects(query.mbr):
            childrenToSearch.append(child)
    
    if node.is_leaf():
        for point in childrenToSearch:
            if point.mbr.intersects(query.mbr):
                results.append(point)
        return results

    # non-leaf so do recursion in subtree
    for child in childrenToSearch:
        recresult = rangeQuery(child, query)
        results.extend(recresult)

    return results

    