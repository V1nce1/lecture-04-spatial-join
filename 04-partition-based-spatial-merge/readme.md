# Partition Based Spatial Merge Join

**High Level Overview**: Given two datasets A and B, subdivide covered space into n*n partitions, where n is the number of partitions per row. Sort elements into partitions and join. Assume only 1k elements fit into each partition. You can also assume that data is evenly distributed and not skewed. That means you do not go further than orthogonally split the space into even partitions. However, you can if you want to.

**Implementation Difficulty**: Medium
