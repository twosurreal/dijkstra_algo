"""
dijkstra_matrix.py
PART (a): Dijkstra's algorithm using
    - an ADJACENCY MATRIX to store the graph
    - a plain ARRAY as the priority queue (finding the minimum = scanning the array)

Vocabulary used in this project:
    glance = the program looking at ONE entry, either one row of the distance table
             or one cell of the matrix.

Time complexity: O(V^2)
    The main loop runs V times (one round per vertex). In every round we do two scans of length V:
    (1) glance down the dist array to find the closest unvisited vertex -> V glances
    (2) glance along one row of the matrix to look at that vertex's edges -> V glances
    So there are 2 * V * V glances in total. The number of edges E does not change this count,
    because the matrix is always V x V. (Each real edge also costs a little extra work to add
    and compare, at most E times in total, and E is never more than about V * V.)

Names used here versus the lecture slides:
    dist    = the distance column of the table
    parent  = the "previous node" column (called par in the lecture)

This file has two versions of the algorithm:
    dijkstra_matrix(...)          the clean version. This is the one we TIME.
    dijkstra_matrix_counted(...)  the same algorithm, but it also counts the glances.
                                  Counting does not depend on how fast the computer is, so it
                                  is a second way to check the V^2 theory.
"""

INF = float("inf")  # stands for "no edge" in the matrix and "not reached yet" in dist


def build_matrix(V, edges):
    """
    Turn a list of edges (u, v, w) into a V x V adjacency matrix.
    matrix[u][v] = weight of the edge u -> v, or INF if there is no such edge.
    The diagonal is 0 by convention (a vertex to itself costs nothing).

    Dijkstra only works when every weight is zero or positive, so a negative
    weight raises an error instead of silently giving wrong answers.
    """
    matrix = [[INF] * V for _ in range(V)]
    for i in range(V):
        matrix[i][i] = 0
    for u, v, w in edges:
        if w < 0:
            raise ValueError(
                f"Edge {u} -> {v} has negative weight {w}. "
                "Dijkstra's algorithm requires non-negative weights."
            )
        matrix[u][v] = w  # directed: only this one cell is filled
    return matrix


def dijkstra_matrix(matrix, source):
    """
    Shortest distances from `source` to every vertex.

    Returns (dist, parent):
      dist[v]   = shortest distance from source to v (INF if v cannot be reached)
      parent[v] = the vertex just before v on a shortest path (-1 for source / unreachable)
    """
    V = len(matrix)

    dist = [INF] * V       # best known distance to each vertex (this IS the "array priority queue")
    parent = [-1] * V      # the "previous node" column from the table
    visited = [False] * V  # True once a vertex's distance is final

    dist[source] = 0

    for _ in range(V):
        # (1) EXTRACT-MIN by scanning the whole array: V glances
        u = -1
        best = INF
        for v in range(V):
            if not visited[v] and dist[v] < best:
                best = dist[v]
                u = v

        if u == -1:
            break  # everything left is unreachable, nothing more to do

        visited[u] = True  # dist[u] is now final

        # (2) RELAX every outgoing edge of u by scanning its matrix row: V glances
        row = matrix[u]
        for v in range(V):
            w = row[v]
            if w != INF and not visited[v]:
                candidate = dist[u] + w
                if candidate < dist[v]:  # strictly shorter: overwrite
                    dist[v] = candidate
                    parent[v] = u

    return dist, parent


def dijkstra_matrix_counted(matrix, source):
    """
    Exactly the same algorithm as dijkstra_matrix, plus glance counting.

    Returns (dist, parent, counts) where counts is a dictionary:
      counts["table_glances"] = glances at rows of the distance table (hunting for the minimum)
      counts["row_glances"]   = glances at cells of the matrix rows
      counts["total"]         = table_glances + row_glances   (theory says 2 * V^2)
      counts["updates"]       = how many times a dist value was actually lowered
                                (this is the only number that can depend on E)

    Kept as a separate function so the counting itself never slows down the timed version.
    """
    V = len(matrix)

    dist = [INF] * V
    parent = [-1] * V
    visited = [False] * V

    table_glances = 0
    row_glances = 0
    updates = 0

    dist[source] = 0

    for _ in range(V):
        u = -1
        best = INF
        for v in range(V):
            table_glances += 1
            if not visited[v] and dist[v] < best:
                best = dist[v]
                u = v

        if u == -1:
            break

        visited[u] = True

        row = matrix[u]
        for v in range(V):
            row_glances += 1
            w = row[v]
            if w != INF and not visited[v]:
                candidate = dist[u] + w
                if candidate < dist[v]:
                    dist[v] = candidate
                    parent[v] = u
                    updates += 1

    counts = {
        "table_glances": table_glances,
        "row_glances": row_glances,
        "total": table_glances + row_glances,
        "updates": updates,
    }
    return dist, parent, counts


def get_path(parent, source, target):
    """
    Rebuild the path from `source` to `target` by following the parent column backwards.
    Returns a list of vertices like [0, 1, 2, 3], or [] if target cannot be reached.
    """
    path = [target]
    while path[-1] != source:
        p = parent[path[-1]]
        if p == -1:
            return []  # walked back to a dead end: no path from source
        path.append(p)
    path.reverse()
    return path
