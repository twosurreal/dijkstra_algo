"""
graph_gen.py
Makes random DIRECTED weighted graphs for testing and experiments, using NetworkX.

NetworkX must be installed:   python -m pip install networkx

A graph is returned as a list of edges. Each edge is a tuple (u, v, w):
    u = the vertex the edge starts at   (0 to V-1)
    v = the vertex the edge ends at     (0 to V-1)
    w = the weight (a positive whole number)

Rules this generator follows:
  - Directed: the edge (2, 5, 7) does NOT also create (5, 2, 7).
  - No self loops (no edge from a vertex to itself).
  - No duplicate edges (at most one edge for each ordered pair u -> v).
  - Every vertex is reachable from vertex 0, so a run of Dijkstra starting
    at 0 gives a real distance for every vertex (no infinities).

Because of those rules, E must satisfy:   V - 1  <=  E  <=  V * (V - 1)
"""

import random

import networkx as nx


def random_directed_graph(V, E, max_weight=100, seed=None):
    """
    Return a list of E random directed edges (u, v, w) on V vertices.

    The random edges come from NetworkX (nx.gnm_random_graph: "V vertices, exactly E random
    edges"). That function does not promise that every vertex can be reached from vertex 0,
    and our experiments need that (otherwise Dijkstra stops early and the V^2 pattern gets
    blurred). So after NetworkX makes the graph we:
      1. find the vertices that vertex 0 cannot reach
      2. connect each one to a random reachable vertex (this adds some edges)
      3. remove the same number of random edges that are NOT on a breadth first tree from 0,
         so every vertex stays reachable and the total is exactly E again.

    The same seed always gives the same graph, so experiments can be repeated exactly.
    """
    max_edges = V * (V - 1)
    if V < 1:
        raise ValueError("V must be at least 1")
    if E < V - 1 or E > max_edges:
        raise ValueError(
            f"For V={V}, E must be between {V - 1} and {max_edges}, got E={E}"
        )

    rng = random.Random(seed)  # our own random generator, used for the repairs and the weights

    # NetworkX does the main random generation: directed, no self loops, no duplicates
    G = nx.gnm_random_graph(V, E, seed=rng.randrange(2**31), directed=True)

    # steps 1 and 2: make every vertex reachable from vertex 0
    reachable = nx.descendants(G, 0) | {0}
    reachable_list = sorted(reachable)
    added = 0
    for v in rng.sample(range(V), V):  # shuffled order
        if v in reachable:
            continue
        u = rng.choice(reachable_list)
        G.add_edge(u, v)  # v was unreachable, so this edge cannot already exist
        added += 1
        for x in nx.descendants(G, v) | {v}:
            if x not in reachable:
                reachable.add(x)
                reachable_list.append(x)

    # step 3: give back the edges we added, taking them from edges that are not needed
    if added:
        tree_edges = set(nx.bfs_edges(G, 0))  # V - 1 edges that already reach everything
        spare = [e for e in G.edges if e not in tree_edges]
        for e in rng.sample(spare, added):
            G.remove_edge(*e)

    return [(u, v, rng.randint(1, max_weight)) for u, v in G.edges]
