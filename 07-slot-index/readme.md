# Slot Index Spatial Join

**High Level Overview**: Given an R-Tree and an non indexed dataset, create a hash with k buckets. The buckets are built based on partitions from the highest tree level that consists at least of k nodes. Group nodes of that level into k partitions. Insert non indexed points into partitions and run join algorithm.

**Implementation Difficulty**: Difficult
