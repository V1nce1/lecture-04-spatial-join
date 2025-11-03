# Sort and Match Spatial Join

**High Level Overview**: Given an R-Tree index and an non indexed dataset, use the efficient Sort Tile Recursive (STR) algorithm to partition non indexed points into groups. Find overlapping leafs and employ plane sweep to find matching pairs.

**Implementation Difficulty**: Medium
