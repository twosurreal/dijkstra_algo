"""
test_correctness.py
Checks that the part (a) code gives correct answers BEFORE we trust any timings.

Run it with:   python test_correctness.py
If everything is fine it prints "ALL TESTS PASSED".
If something is wrong, Python stops at the failing line and shows which check failed.

Four kinds of tests:
  1. Hand made small cases (answers worked out by hand)
  2. Edge cases (single vertex, unreachable vertex, ties, other start vertex, negative weight)
  3. Random graphs compared against an independent reference implementation
  4. The glance counter: same answers as the plain version, and exactly 2 * V^2 glances
"""

import heapq
import random

import networkx as nx

from graph_gen import random_directed_graph
from dijkstra_matrix import (
    INF,
    build_matrix,
    dijkstra_matrix,
    dijkstra_matrix_counted,
    get_path,
)


def run(V, edges, source=0):
    """Helper: build the matrix and run our part (a) Dijkstra."""
    return dijkstra_matrix(build_matrix(V, edges), source)


# ---------------------------------------------------------------- 1. hand made
def test_hand_made_case():
    # A=0, B=1, C=2, D=3.   A->B 2, A->C 9, B->C 4, B->D 7, C->D 1
    edges = [(0, 1, 2), (0, 2, 9), (1, 2, 4), (1, 3, 7), (2, 3, 1)]
    dist, parent = run(4, edges)
    assert dist == [0, 2, 6, 7], dist
    assert parent == [-1, 0, 1, 2], parent
    assert get_path(parent, 0, 3) == [0, 1, 2, 3]


def test_video_graph():
    # The graph from the YouTube video. A=0, B=1, C=2, D=3, E=4, F=5
    edges = [
        (0, 1, 2), (0, 3, 8), (1, 4, 6), (1, 3, 5),
        (3, 4, 3), (3, 5, 2), (4, 2, 9), (4, 5, 1), (5, 2, 3),
    ]
    dist, parent = run(6, edges)
    assert dist == [0, 2, 12, 7, 8, 9], dist  # A, B, C, D, E, F
    assert get_path(parent, 0, 2) == [0, 1, 3, 5, 2]  # A, B, D, F, C


# ---------------------------------------------------------------- 2. edge cases
def test_single_vertex():
    dist, parent = run(1, [])
    assert dist == [0]
    assert parent == [-1]


def test_unreachable_vertex():
    # vertex 2 has no incoming edge, so it can never be reached from 0
    dist, parent = run(3, [(0, 1, 5)])
    assert dist == [0, 5, INF], dist
    assert get_path(parent, 0, 2) == []


def test_direction_matters():
    # the only edge is 0 -> 1, so from vertex 1 we cannot get back to 0
    dist, _ = run(2, [(0, 1, 4)], source=1)
    assert dist == [INF, 0], dist


def test_ties():
    # two equally short routes to vertex 3 (cost 2 either way)
    edges = [(0, 1, 1), (0, 2, 1), (1, 3, 1), (2, 3, 1)]
    dist, _ = run(4, edges)
    assert dist == [0, 1, 1, 2], dist


def test_negative_weight_rejected():
    # Dijkstra gives wrong answers with negative weights, so building the matrix must refuse
    try:
        build_matrix(2, [(0, 1, -3)])
    except ValueError:
        return
    raise AssertionError("a negative weight should have raised ValueError")


def test_other_start_vertex():
    edges = [(0, 1, 2), (0, 2, 9), (1, 2, 4), (1, 3, 7), (2, 3, 1)]
    dist, _ = run(4, edges, source=1)
    assert dist == [INF, 0, 4, 5], dist


def test_longer_route_beats_direct_edge():
    # direct 0 -> 2 costs 10, but 0 -> 1 -> 2 costs only 3
    dist, parent = run(3, [(0, 2, 10), (0, 1, 1), (1, 2, 2)])
    assert dist[2] == 3
    assert parent[2] == 1


# ---------------------------------------------------------------- 3. random graphs
def reference_dijkstra(V, edges, source):
    """
    A DIFFERENT implementation (adjacency list + heap) used only to check our answers.
    If our matrix version agrees with this on hundreds of random graphs, we can trust it.
    """
    adj = [[] for _ in range(V)]
    for u, v, w in edges:
        adj[u].append((v, w))
    dist = [INF] * V
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist


def test_generator_rules():
    # (V, E) pairs: first the extremes (smallest possible E, and a complete graph), then random ones
    cases = [(1, 0), (2, 1), (2, 2), (5, 4), (5, 20)]
    for _ in range(150):
        V = random.randint(2, 40)
        cases.append((V, random.randint(V - 1, V * (V - 1))))
    for V, E in cases:
        edges = random_directed_graph(V, E, max_weight=50)
        pairs = [(u, v) for u, v, _ in edges]
        assert len(edges) == E, ("wrong number of edges", V, E, len(edges))
        assert len(set(pairs)) == E, "duplicate edge found"
        assert all(u != v for u, v in pairs), "self loop found"
        assert all(0 <= u < V and 0 <= v < V for u, v in pairs), "vertex out of range"
        assert all(1 <= w <= 50 for _, _, w in edges), "weight out of range"
        dist, _ = run(V, edges)
        assert INF not in dist, "some vertex not reachable from 0"


def test_generator_same_seed_same_graph():
    # same seed must give the same graph, so experiments can be repeated exactly
    assert random_directed_graph(30, 100, seed=7) == random_directed_graph(30, 100, seed=7)


def test_random_against_reference():
    for _ in range(500):
        V = random.randint(2, 40)
        E = random.randint(V - 1, V * (V - 1))
        edges = random_directed_graph(V, E, max_weight=random.choice([1, 5, 100]))
        source = random.randrange(V)
        ours, parent = run(V, edges, source)
        assert ours == reference_dijkstra(V, edges, source), (V, E, source)

        # also check that every parent pointer really is an edge and adds up
        weight = {(u, v): w for u, v, w in edges}
        for v in range(V):
            if v != source and ours[v] != INF:
                p = parent[v]
                assert ours[v] == ours[p] + weight[(p, v)], "parent does not explain dist"


def test_counted_version_matches_plain_version():
    # the counting version must give exactly the same answers as the timed version
    for _ in range(200):
        V = random.randint(1, 40)
        E = random.randint(max(V - 1, 0), V * (V - 1))
        edges = random_directed_graph(V, E)
        matrix = build_matrix(V, edges)
        source = random.randrange(V)
        dist1, parent1 = dijkstra_matrix(matrix, source)
        dist2, parent2, counts = dijkstra_matrix_counted(matrix, source)
        assert dist1 == dist2
        assert parent1 == parent2
        assert counts["total"] == counts["table_glances"] + counts["row_glances"]
        assert counts["updates"] <= E, "cannot lower a distance more often than there are edges"


def test_glance_count_is_exactly_two_V_squared():
    # when every vertex is reachable, all V rounds run, each doing a V long scan twice,
    # so the count is exactly 2 * V^2 whatever E is (this is the theory, checked directly)
    for V in (1, 2, 5, 20, 60):
        low = V - 1
        high = V * (V - 1)
        for E in sorted({low, (low + high) // 2, high}):
            edges = random_directed_graph(V, E)
            _, _, counts = dijkstra_matrix_counted(build_matrix(V, edges), 0)
            assert counts["table_glances"] == V * V, (V, E, counts)
            assert counts["row_glances"] == V * V, (V, E, counts)
            assert counts["total"] == 2 * V * V, (V, E, counts)


def test_against_networkx():
    # NetworkX's own Dijkstra is a second independent check of our answers
    for _ in range(100):
        V = random.randint(2, 30)
        E = random.randint(V - 1, V * (V - 1))
        edges = random_directed_graph(V, E)
        G = nx.DiGraph()
        G.add_nodes_from(range(V))
        G.add_weighted_edges_from(edges)
        expected = nx.single_source_dijkstra_path_length(G, 0)
        ours, _ = run(V, edges, 0)
        for v in range(V):
            assert ours[v] == expected.get(v, INF)


# ---------------------------------------------------------------- run everything
if __name__ == "__main__":
    tests = [
        test_hand_made_case,
        test_video_graph,
        test_single_vertex,
        test_unreachable_vertex,
        test_direction_matters,
        test_ties,
        test_negative_weight_rejected,
        test_other_start_vertex,
        test_longer_route_beats_direct_edge,
        test_generator_rules,
        test_generator_same_seed_same_graph,
        test_random_against_reference,
        test_counted_version_matches_plain_version,
        test_glance_count_is_exactly_two_V_squared,
        test_against_networkx,
    ]
    for t in tests:
        t()
        print("passed:", t.__name__)
    print("\nALL TESTS PASSED")
