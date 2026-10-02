INF = float("inf")


def build_matrix(V, edges):
    matrix = [[INF] * V for _ in range(V)]
    for i in range(V):
        matrix[i][i] = 0
    for u, v, w in edges:
        matrix[u][v] = w
    return matrix


def dijkstra_matrix(matrix, source):
    V = len(matrix)

    dist = [INF] * V
    parent = [-1] * V
    visited = [False] * V

    dist[source] = 0

    for _ in range(V):
        u = -1
        best = INF
        for v in range(V):
            if not visited[v] and dist[v] < best:
                best = dist[v]
                u = v

        if u == -1:
            break

        visited[u] = True

        row = matrix[u]
        for v in range(V):
            w = row[v]
            if w != INF and not visited[v]:
                candidate = dist[u] + w
                if candidate < dist[v]:
                    dist[v] = candidate
                    parent[v] = u

    return dist, parent


def get_path(parent, source, target):
    path = [target]
    while path[-1] != source:
        p = parent[path[-1]]
        if p == -1:
            return []
        path.append(p)
    path.reverse()
    return path
