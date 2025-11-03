from dataclasses import dataclass, field
import math
from typing import List, Optional, Union, Iterable, Tuple

@dataclass
class MinimalBoundingRectangle:
    """Represents an axis-aligned bounding rectangle."""
    x1: float  # minimum x coordinate
    y1: float  # minimum y coordinate
    x2: float  # maximum x coordinate
    y2: float  # maximum y coordinate

    def includes(self, point: "Point") -> bool:
        """Check if a point (with its extent/radius) is contained within this MBR."""
        return (self.x1 <= point.x - point.radius and 
                point.x + point.radius <= self.x2 and
                self.y1 <= point.y - point.radius and 
                point.y + point.radius <= self.y2)

    def area(self) -> float:
        """Calculate the area of this MBR."""
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)

    def enlarged_area_with_point(self, point: "Point") -> float:
        """Calculate the area if this MBR were expanded to include the point with its extent."""
        nx1 = min(self.x1, point.x - point.radius)
        ny1 = min(self.y1, point.y - point.radius)
        nx2 = max(self.x2, point.x + point.radius)
        ny2 = max(self.y2, point.y + point.radius)
        return max(0.0, nx2 - nx1) * max(0.0, ny2 - ny1)
    
    def intersects(self, other: "MinimalBoundingRectangle") -> bool:
        """Check if this MBR intersects with another MBR."""
        return not (self.x2 <= other.x1 or other.x2 <= self.x1 or
                   self.y2 <= other.y1 or other.y2 <= self.y1)

@dataclass
class Point:
    """Represents a 2D point with extent (radius) in space, which makes it a circle."""
    x: float
    y: float
    radius: float

    def __init__(self, x: float, y: float, radius: float) -> None:
        self.x = x
        self.y = y
        self.radius = radius
        self.mbr = MinimalBoundingRectangle(
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.radius == other.radius
    
    def __hash__(self) -> int:
        return hash((self.x, self.y, self.radius))


@dataclass
class Node:
    """Represents an internal or leaf node in the R-tree."""
    children: List[Union["Node", Point]] = field(default_factory=list)
    parent: Optional["Node"] = None

    mbr: Optional[MinimalBoundingRectangle] = None

    def update_mbr(self) -> None:
        """
        Recompute this node's MBR from its children and propagate upwards.
        This ensures that parent nodes always have MBRs that encompass all
        their descendants.
        """
        if not self.children:
            self.mbr = None
        else:
            inf = float('inf')
            neginf = float('-inf')
            x1, y1 = inf, inf
            x2, y2 = neginf, neginf

            if self.is_leaf():
                for child in self.children:
                    point_mbr = child.mbr
                    x1 = min(x1, point_mbr.x1)
                    y1 = min(y1, point_mbr.y1)
                    x2 = max(x2, point_mbr.x2)
                    y2 = max(y2, point_mbr.y2)
            else:
                for child in self.children:
                    if isinstance(child, Node):
                        child_mbr = child.mbr
                        if child_mbr is None:
                            continue
                        x1 = min(x1, child_mbr.x1)
                        y1 = min(y1, child_mbr.y1)
                        x2 = max(x2, child_mbr.x2)
                        y2 = max(y2, child_mbr.y2)
                    else:
                        raise ValueError("Non-leaf node has a Point child, which is invalid.")

            self.mbr = MinimalBoundingRectangle(x1, y1, x2, y2)

        # propagate updated MBR to parent
        if self.parent is not None:
            self.parent.update_mbr()

    def is_leaf(self) -> bool:
        """Check if this node is a leaf (contains Points rather than Nodes)."""
        return len(self.children) != 0 and isinstance(self.children[0], Point)

    def all_points(self) -> Iterable[Point]:
        """Recursively yield all points stored in this subtree."""
        for child in self.children:
            if isinstance(child, Point):
                yield child
            else:
                yield from child.all_points()

class RTree:
    """
    R-tree spatial index for 2D points.
    
    The R-tree organizes points hierarchically using bounding rectangles,
    enabling efficient spatial queries.
    """

    def __init__(self, node_capacity: int) -> None:
        """
        Initialize an empty R-tree.
        
        Args:
            node_capacity: Maximum number of children per node before splitting.
        """
        self.root: Node = Node(children=[], parent=None)
        self.node_capacity: int = node_capacity

    def bulk_load(self, points: List[Point]) -> None:
        """
        Bulk load points into the R-tree using a the Sort Tile Recursive (STR) algorithm.
        """
        if not points:
            return
        # Sort points by x-coordinate
        points.sort(key=lambda p: p.x)
        # Partition points into slices
        number_of_leafs = math.ceil(len(points) / self.node_capacity)
        num_slices = math.ceil(number_of_leafs ** 0.5)
        slice_size = (len(points) + num_slices - 1) // num_slices
        slices = [points[i * slice_size:(i + 1) * slice_size] for i in range(num_slices)]
        # sort each slice by y-coordinate and create leaf nodes
        leaf_nodes = []
        for sl in slices:
            sl.sort(key=lambda p: p.y)
            for i in range(0, len(sl), self.node_capacity):
                leaf = Node(children=sl[i:i + self.node_capacity], parent=None)
                leaf.update_mbr()
                leaf_nodes.append(leaf)

        current_nodes = leaf_nodes
        while len(current_nodes) != 1:
            number_of_new_nodes = math.ceil(len(current_nodes) / self.node_capacity)
            rest = len(current_nodes) % self.node_capacity
            children_sizes = [self.node_capacity] * number_of_new_nodes
            total = len(current_nodes)
            base, rem = divmod(total, number_of_new_nodes)
            children_sizes = [base + (1 if i < rem else 0) for i in range(number_of_new_nodes)]
            new_nodes = []
            index = 0
            for children_size in children_sizes:
                new_node = Node(children=current_nodes[index:index + children_size], parent=None)
                for child in new_node.children:
                    child.parent = new_node
                new_node.update_mbr()
                new_nodes.append(new_node)
                index += children_size
            current_nodes = new_nodes
        self.root = current_nodes[0]

    def _choose_leaf(self, point: Point) -> Node:
        """
        Find the best leaf node to insert a point.
        
        Traverses the tree, choosing at each level the child whose MBR
        needs the least enlargement to accommodate the point.
        """
        current_node = self.root
        while True:
            # if current node is a leaf, return it
            if current_node.is_leaf() or len(current_node.children) == 0:
                return current_node

            # prefer child whose mbr already includes the point
            chosen = None
            best_increase = float('inf')

            for node in current_node.children:
                # node here should be a Node (internal child)
                node_mbr = node.mbr if isinstance(node, Node) else None
                if node_mbr and node_mbr.includes(point):
                    chosen = node
                    best_increase = 0.0
                else:
                    increase = (node_mbr.enlarged_area_with_point(point) - node_mbr.area()) if node_mbr else float('inf')
                    if increase < best_increase:
                        chosen = node
                        best_increase = increase

            assert chosen is not None, "Should always find a child node"
            current_node = chosen

    def _split_node(self, node: Node) -> Node:
        """
        Split an overfull node into two nodes.
        
        Uses a simple linear split: divides children into two halves.
        Returns the newly created sibling node.
        """
        orig = list(node.children)
        orig.sort(key=lambda child: child.x if isinstance(child, Point) else child.mbr.x1 if isinstance(child, Node) and child.mbr else float('inf'))
        half = len(orig) // 2
        left = orig[:half]
        right = orig[half:]
        node.children = left
        new_node = Node(children=right, parent=node.parent)
        # fix parent links for child nodes
        for child in new_node.children:
            if isinstance(child, Node):
                child.parent = new_node
        for child in node.children:
            if isinstance(child, Node):
                child.parent = node
        # update mbrs for both nodes after the split
        node.update_mbr()
        new_node.update_mbr()
        return new_node

    def _adjust_tree(self, node: Node) -> None:
        """
        Walk up the tree from a node, splitting overfull nodes and updating MBRs.
        
        This maintains the R-tree invariants after insertion.
        """
        current = node
        while current is not None:
            # ensure current's mbr reflects its children
            current.update_mbr()

            if len(current.children) > self.node_capacity:
                new_node = self._split_node(current)
                if current.parent is None:
                    new_root = Node(children=[current, new_node], parent=None)
                    current.parent = new_root
                    new_node.parent = new_root
                    self.root = new_root
                    # set MBR for new root
                    new_root.update_mbr()
                else:
                    current.parent.children.append(new_node)
                    new_node.parent = current.parent
                    # parent's mbr will be fixed in next loop iteration

            current = current.parent

    def _find_leaf(self, node: Node, point: Point) -> Optional[Node]:
        """
        Find the leaf node containing a specific point.
        
        Returns None if the point is not found in the tree.
        """
        if len(node.children) == 0:
            return None
        if node.is_leaf():
            if point in node.children:
                return node
            return None
        for child in node.children:
            if isinstance(child, Node):
                child_mbr = child.mbr
                # Check if the point's MBR intersects with the child's MBR
                if child_mbr:
                    point_mbr = point.mbr
                    if child_mbr.intersects(point_mbr):
                        result = self._find_leaf(child, point)
                        if result:
                            return result
        return None

    def _condense_tree(self, node: Node) -> None:
        """
        Handle underfull nodes after deletion by removing and reinserting.
        
        Walks up from a node, removing any underfull nodes and reinserting
        their points to maintain tree balance.
        """
        insert_queue: List[Point] = []
        while node is not None:
            if len(node.children) < (self.node_capacity // 2):
                if node.parent:
                    try:
                        node.parent.children.remove(node)
                    except ValueError:
                        pass
                    for child in node.children:
                        if isinstance(child, Point):
                            insert_queue.append(child)
                        else:
                            insert_queue.extend(list(child.all_points()))
            node = node.parent
        # reinsert collected points
        for item in reversed(insert_queue):
            self.insert(item)
        # after reinserts, ensure root mbr is consistent
        if self.root:
            self.root.update_mbr()

    def delete(self, point: Point) -> None:
        """
        Remove a point from the R-tree.
        
        If the point exists multiple times, only one occurrence is removed.
        Does nothing if the point is not found.
        """
        leaf = self._find_leaf(self.root, point)
        if leaf is not None:
            try:
                leaf.children.remove(point)
            except ValueError:
                return
            # update leaf mbr and then condense
            leaf.update_mbr()
            self._condense_tree(leaf)

        if len(self.root.children) == 1 and isinstance(self.root.children[0], Node):
            self.root = self.root.children[0]
            self.root.parent = None
            self.root.update_mbr()

    def insert(self, point: Point) -> None:
        """
        Insert a point into the R-tree.
        
        The point is added to the most appropriate leaf, and the tree
        structure is adjusted as needed to maintain invariants.
        """
        leaf = self._choose_leaf(point)
        leaf.children.append(point)
        leaf.update_mbr()
        self._adjust_tree(leaf)

    def all_points(self) -> List[Point]:
        return list(self.root.all_points())

    def size(self) -> int:
        return len(self.all_points())
