# Lecture 04 - Spatial Join Exercise

In this exercise you will implement one algorithm for a **spatial inner join** conditioned on **overlap of minimum bounding rectangles**.

## Algorithm Overview

Index | Algorithm | Estimated Implementation Difficulty
--|--|--
01 | Bruteforce | Given
02 | Synchronous R-Tree Traversal | Easy
03 | Spatial Hash Join | Medium
04 | Partition Based Spatial Merge Join | Medium
05 | Indexed Nested Loop Join | Easy
06 | Sort and Match Spatial Join | Medium
07 | Slot Index Spatial Join | Difficult

## Data and Dependency Preparation

Download datasets.

1. Download cellular tower dataset

```bash
curl -L -o cellular-tower-locations-dataset.zip https://www.kaggle.com/api/v1/datasets/download/thedevastator/cellular-tower-locations-dataset
unzip cellular-tower-locations-dataset.zip && rm cellular-tower-locations-dataset.zip
mv Cellular_Towers.csv ./data/Cellular_Towers.csv
```

2. Download city dataset

```bash
curl -L -o united-states-cities-database.zip https://www.kaggle.com/api/v1/datasets/download/sergejnuss/united-states-cities-database
unzip united-states-cities-database.zip
mv uscities.csv ./data/uscities.csv
```

3. Setup the virtual environment

```bash
# Create virtual environment
python3 -m venv .venv
# Activate virtual environment
source .venv/bin/activate
# Install requirements
pip install -r requirements.txt
```

4. (Optional) Visualize the datasets
```bash
# Activate the virtual environment if not already active
source .venv/bin/activate
# Start the visualization
python3 visualize.py
```

## Your Task

Implement the algorithm you selected. The implementation should be put into `xx-<algorithm name>/implementation.py`. This is a single file program. Do not add extra files as the automatic benchmarking might not work otherwise.

Your task is to fill the `join` function.
The `prepare` function will receive two lists of points with extent as argument.
Contrary to the spatial object definition in exercise 3, the point now has a extent in terms of a radius.
In the `prepare` function index structures are built for which the algorithm assumes the data to be in.
For example, R-Trees are initialized here.
The return value of the `prepare` function is fed as argument into the `join` function.
The processing is split into `prepare` and `join` so that we can estimate the runtime of building and maintaining the index structure independent from the query operator runtime.

**IMPORTANT: ONLY CHANGE THE `JOIN` FUNCTION.**

In case your algorithm depends on an R-Tree, an adapted version to the new `Point` definition has been implemented in `rtree/rtree.py`.
As R-Trees define spatial extents as rectangles, each point now has an MBR that can be accessed with `Point.mbr`.
You can use all implementations, i.e. `Point`, `Node`, `MinimumBoundingRectangle`, and `RTree` from that package.
Simply import the classes with `from rtree.rtree import Point, Node, MinimumBoundingRectangle, RTree`.

### Test your implementation

Run your implementation with `python3 benchmark.py --limit 10000 <path to your implementation file>`.
The benchmark script accepts multiple implementations that are run consecutively.
You can use the given brute force implementation to check if the number of returned tuples matches your implementation.

```python
python3 benchmark.py --limit 10000 01-bruteforce/implementation.py <path to your implementation file>
```

### Upload your implementation

Create a pull request with your implementation. Make sure to only change the implementation file in your commit(s).

### Explain Algorithm

So that everyone can understand each algorithm, each team will present their algorithm in 3 minutes.
For that, prepare 1-2 slides that cover the most important aspects of your algorithm.
A link to the Google Presentation slide deck is given in the Moodle.
