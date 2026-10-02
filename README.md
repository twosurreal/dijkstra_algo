# Dijkstra's Algorithm, Part (a): Adjacency Matrix + Array

Algorithm Design and Analysis, Project 2.

**Part (a) of the brief:** the input graph G = (V, E) is stored in an **adjacency matrix** and an **array** is used for the priority queue. Implement Dijkstra's algorithm in this setting and analyze its time complexity with respect to |V| and |E|, both theoretically and empirically.

This folder holds the implementation, the tests, the experiments, and the results of our full run.

## Contents

| File | What it is |
|---|---|
| `dijkstra_matrix.py` | The implementation, with comments. Contains `build_matrix`, `dijkstra_matrix` (the version we time), `dijkstra_matrix_counted` (same algorithm, also counts glances) and `get_path`. |
| `actual_dijkstra.py` | The same algorithm with no comments, for reading. |
| `graph_gen.py` | Makes random directed weighted test graphs with NetworkX. |
| `test_correctness.py` | Checks the code gives correct answers. |
| `experiments.py` | Runs the three experiments and writes the charts and CSV files. |
| `results_vary_V.csv`, `exp1_vary_V.png` | Experiment 1 results. |
| `results_vary_E.csv`, `exp2_vary_E.png` | Experiment 2 results. |
| `results_complete.csv`, `exp3_complete.png` | Experiment 3 results. |
| `glance_count.png` | Glance counts from experiments 1 and 3. |

## Setup

You need Python 3. Open a terminal in this folder and install the two packages the code uses:

```
python -m pip install matplotlib networkx
```

On Windows, use `py` in place of `python` if `python` is not recognised. `matplotlib` draws the charts and `networkx` makes the random test graphs.

## How to run

```
python test_correctness.py        # should end with: ALL TESTS PASSED
python experiments.py --quick     # small sizes, finishes in seconds
python experiments.py             # full run, takes a few minutes
```

Add `--show` to also pop up the charts on screen. For clean timings, do not run other heavy programs during the full run.

## Vocabulary

1. **V** is the number of vertices (nodes). They are numbered 0 to V-1.
2. **E** is the number of edges (arrows). The graphs are **directed**, with no self loops and no duplicate edges.
3. **Weight** is the cost of one edge. Weights here are whole numbers from 1 to 100.
4. **Distance** is the total cost from the start vertex to a vertex, adding the weights along the best route.
5. **Glance** is the program looking at one entry: one row of the distance table or one cell of the matrix.
6. **Complete graph** is a graph where every possible edge exists, so E = V(V-1).

## Input format and a small example

A graph is a list of edges written as `(from, to, weight)`. `build_matrix` turns the list into the V by V matrix, where row = from, column = to, and `INF` means no edge.

```python
from dijkstra_matrix import build_matrix, dijkstra_matrix, get_path

edges = [(0, 1, 2), (0, 2, 7), (1, 2, 3), (1, 3, 9), (2, 3, 1),
         (2, 4, 5), (3, 4, 4), (3, 0, 6), (4, 1, 8), (4, 0, 10)]

matrix = build_matrix(5, edges)
dist, parent = dijkstra_matrix(matrix, 0)   # start at vertex 0

print(dist)                      # [0, 2, 5, 6, 10]
print(parent)                    # [-1, 0, 1, 2, 2]   (-1 means no previous vertex)
print(get_path(parent, 0, 4))    # [0, 1, 2, 4]
```

## The algorithm in short

1. Set the start vertex's distance to 0 and every other distance to infinity.
2. Repeat V times:
   1. Look down the distance table and pick the unfinished vertex with the smallest distance (this is the array priority queue). Mark it finished.
   2. Look along that vertex's row of the matrix. For each real edge, if (its distance + edge weight) is smaller than the number in the table for the neighbour, replace it and record the previous vertex.
3. Follow the previous-vertex column backwards to read off a route.

Dijkstra only works when no weight is negative. `build_matrix` raises an error if it sees one.

## Theory

1. There are V rounds.
2. Each round makes V glances down the distance table and V glances along one matrix row, so 2V glances.
3. Total: V x 2V = **2 x V x V glances**. This does not depend on E, because the matrix is always V by V.
4. Each real edge also costs a little extra work (add, compare, maybe update). That is at most E edges in total.
5. So the time is O(V^2 + E). Since E is at most V(V-1), this is **O(V^2)**.

## Experiments

Every setting builds 5 random graphs, times only the call to `dijkstra_matrix` (graph building and matrix building are not timed, and garbage collection is switched off while timing), and averages the 5 times. The start vertex is always 0. Every vertex is reachable from vertex 0. Seeds are fixed, so the graphs are identical on every run.

| Experiment | What changes | What is fixed |
|---|---|---|
| 1 | V from 200 to 1400 | E = 5000 |
| 2 | E from 1,000 to 200,000 | V = 500 |
| 3 | V from 100 to 800 | complete graphs, E = V(V-1) |

Each CSV has the columns `V, E, seconds, glances, updates`. `glances` is the glance count and `updates` is how many times a distance in the table was lowered.

## Results of the full run

**Experiment 1: time vs V (E = 5000).** The time divided by V x V stays at about 34 to 43 nanoseconds, mostly about 37. Making V 7 times bigger made the time about 49 times longer. The growth exponent is about 2.00, where "exponent k" means time grows like V to the power k.

| V | 200 | 400 | 600 | 800 | 1000 | 1200 | 1400 |
|---|---|---|---|---|---|---|---|
| time (ms) | 1.47 | 6.84 | 12.20 | 24.16 | 35.90 | 52.75 | 71.69 |

**Experiment 2: time vs E (V = 500).** The glance count is 500,000 at every E. Time is flat at about 9 ms while E is small, then rises to about 13 to 15 ms once E is a large fraction of V x V (250,000 here).

| E | 1,000 | 5,000 | 20,000 | 50,000 | 100,000 | 150,000 | 200,000 |
|---|---|---|---|---|---|---|---|
| time (ms) | 9.45 | 9.06 | 9.04 | 11.31 | 12.81 | 15.17 | 13.33 |

**Experiment 3: time vs V on complete graphs.** The time divided by V x V stays at 54 to 58 nanoseconds, and the growth exponent is about 2.00. Complete graphs cost about 1.5 times more than the sparse graphs of experiment 1 at the same V, because every edge costs extra work.

| V | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 |
|---|---|---|---|---|---|---|---|---|
| time (ms) | 0.56 | 2.33 | 5.04 | 8.64 | 13.80 | 19.88 | 27.31 | 35.91 |

**Glance counts.** The count is exactly 2 x V x V in every test, sparse or complete. For example V = 1400 gives 3,920,000.

**Conclusion for part (a).** Time grows like V x V (O(V^2)) both for graphs with few edges and for complete graphs. More edges raise the constant (the cost per V x V) but not the growth rate.

## Limitations

1. Timings come from one laptop and vary between runs. For example, at V = 500 and E = 200,000, the same graphs took 24.7 ms in one run and 13.3 ms in another. The glance counts do not vary at all.
2. Absolute times depend on the computer. Compare timings only when they were measured on the same machine.
3. NetworkX's random graph generator does not guarantee that every vertex is reachable from vertex 0, so `graph_gen.py` adds a few edges to repair this and removes the same number of other edges, which keeps E exact. The graphs are therefore very close to, but not exactly, plain random graphs.
4. The glance count covers only the table and matrix scans, not the extra work done on each real edge.
