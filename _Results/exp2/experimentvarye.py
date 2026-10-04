
"""
experiments_vary_E.py
Experiment 2 redone: how does the number of edges E change the time of the part (a)
matrix + array Dijkstra, when V is fixed?
 
Put this file in the same folder as dijkstra_matrix.py and graph_gen.py (part-a), then run:
 
    python experiments_vary_E.py            full run (V = 500, 15 graphs per E)
    python experiments_vary_E.py --quick    small and fast (V = 100, 3 graphs per E)
    python experiments_vary_E.py --show     also pop the chart up on screen
 
Outputs (saved next to this file):
    results_vary_E_theory.csv    one row per E
    exp2_vary_E_theory.png       the chart
 
WHY THESE E VALUES (this is the theory choosing the points, not the old 1,000 to 200,000):
 
    The matrix has V * V cells, and the most edges a graph can have is E_MAX = V * (V - 1).
    The theory says E only matters compared with V * V. So the useful E values are the ones
    that mark "tiny next to V * V", "a fraction of V * V", and "all of it":
 
        V - 1      the fewest edges that still reach every vertex (the baseline)
        5 * V      a typical sparse graph, 5 edges per vertex
        5%, 10%, 25%, 50%, 75% of E_MAX      the matrix filling up
        100% of E_MAX                        the complete graph (the ceiling)
 
    To change the points, edit EXTRA_E and DENSITIES below.
 
WHAT IS RECORDED AT EACH E:
    seconds_median / seconds_mean / seconds_min   time of dijkstra_matrix over several random graphs.
                                                  The median is the one to report, because one slow
                                                  outlier run cannot move it.
    glances       reads of one dist entry or one matrix cell (theory says exactly 2 * V * V)
    relax_checks  times the row scan met a real edge to an unfinished vertex and did the
                  add and compare (theory says at most E)
    updates       times a distance was actually lowered
Glances, relax checks and updates are counted, so they do not depend on the computer.
"""
 
import csv
import gc
import statistics
import sys
import time
 
import matplotlib
 
QUICK = "--quick" in sys.argv
SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")  # draw to files only, no window
import matplotlib.pyplot as plt
 
from dijkstra_matrix import INF, build_matrix, dijkstra_matrix, dijkstra_matrix_counted
from graph_gen import random_directed_graph
 
# ------------------------------------------------------------------ settings
if QUICK:
    V, REPEATS = 100, 3
else:
    V, REPEATS = 500, 15
 
SOURCE = 0
E_MAX = V * (V - 1)                           # a complete graph
EXTRA_E = [V - 1, 5 * V]                      # sparse baselines
DENSITIES = [0.05, 0.10, 0.25, 0.50, 0.75, 1.00]  # fraction of E_MAX
 
# keep only densities that are clearly above the sparse baselines, so no two points are almost equal
E_VALUES = sorted(set(EXTRA_E + [round(d * E_MAX) for d in DENSITIES if round(d * E_MAX) > 10 * V]))
 
# chart look (same colours as the other experiment charts)
BLUE = "#2a6fdb"       # running time
ORANGE = "#e07a1f"     # E-dependent work
DARK = "#4b5563"       # constant work
INK = "#1f2937"        # text
MUTED = "#6b7280"      # secondary text and reference lines
GRID = "#e5e7eb"
 
 
# ------------------------------------------------------------------ counting
def count_work(matrix, source):
    """
    Same algorithm as dijkstra_matrix, but returns (glances, relax_checks, updates).
    Kept separate so counting never slows down the timed run.
    """
    n = len(matrix)
    dist = [INF] * n
    visited = [False] * n
    dist[source] = 0
    glances = relax_checks = updates = 0
 
    for _ in range(n):
        u = -1
        best = INF
        for v in range(n):
            glances += 1                      # Scan A: one dist entry
            if not visited[v] and dist[v] < best:
                best = dist[v]
                u = v
        if u == -1:
            break
        visited[u] = True
 
        row = matrix[u]
        for v in range(n):
            glances += 1                      # Scan B: one matrix cell
            w = row[v]
            if w != INF and not visited[v]:
                relax_checks += 1             # a relax check: add and compare
                candidate = dist[u] + w
                if candidate < dist[v]:
                    dist[v] = candidate
                    updates += 1              # the check ended in an update
    return glances, relax_checks, updates
 
 
def self_check():
    """count_work must agree with the project's own counted version on a small graph."""
    edges = random_directed_graph(30, 200, seed=5)
    matrix = build_matrix(30, edges)
    _, _, counts = dijkstra_matrix_counted(matrix, SOURCE)
    glances, relax_checks, updates = count_work(matrix, SOURCE)
    assert glances == counts["total"], (glances, counts)
    assert updates == counts["updates"], (updates, counts)
    assert updates <= relax_checks <= 200
 
 
# ------------------------------------------------------------------ measuring
def measure(E):
    """Time dijkstra_matrix on REPEATS random graphs with exactly E edges and count the work."""
    times, glances, checks, updates = [], [], [], []
    for r in range(REPEATS):
        edges = random_directed_graph(V, E, seed=V * 1_000_003 + E * 101 + r)
        matrix = build_matrix(V, edges)          # not timed
 
        gc.collect()
        gc.disable()                             # no garbage collection pauses inside the timing
        start = time.perf_counter()
        dijkstra_matrix(matrix, SOURCE)          # the only thing timed
        elapsed = time.perf_counter() - start
        gc.enable()
        times.append(elapsed)
 
        g, c, u = count_work(matrix, SOURCE)     # separate, untimed run
        glances.append(g)
        checks.append(c)
        updates.append(u)
 
    return {
        "V": V,
        "E": E,
        "percent_full": 100 * E / E_MAX,
        "seconds_median": statistics.median(times),
        "seconds_mean": statistics.mean(times),
        "seconds_min": min(times),
        "glances": statistics.mean(glances),
        "relax_checks": statistics.mean(checks),
        "updates": statistics.mean(updates),
    }
 
 
def save_csv(rows, filename):
    columns = ["V", "E", "percent_full", "seconds_median", "seconds_mean",
               "seconds_min", "glances", "relax_checks", "updates"]
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for r in rows:
            writer.writerow([r[c] for c in columns])
 
 
# ------------------------------------------------------------------ chart
def style_axes(ax):
    ax.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED)
 
 
def point_label(row):
    """Two line tick label: the E value and how full the matrix is."""
    return f"{row['E']:,}\n{row['percent_full']:.3g}%"
 
 
def draw_chart(rows, filename):
    n = len(rows)
    xs = list(range(n))                          # evenly spaced: every point can be read
    labels = [point_label(r) for r in rows]
    xlabel = (f"Number of edges E and % of the maximum V(V-1) = {E_MAX:,}\n"
              "points are evenly spaced, not drawn to scale")
 
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.4), dpi=120)
 
    # ---- left: running time
    ms = [r["seconds_median"] * 1000 for r in rows]
    floor = ms[0]
    ax1.axhline(floor, color=MUTED, linewidth=1, linestyle="--")
    ax1.text(n - 1 + 0.15, floor * 0.96, "time with almost no edges",
             ha="right", va="top", color=MUTED, fontsize=8)
    ax1.plot(xs, ms, color=BLUE, linewidth=2, marker="o", markersize=8,
             markeredgecolor="white", markeredgewidth=1.5)
    for i in (0, n - 1):                         # label only the first and last point
        ax1.annotate(f"{ms[i]:.1f} ms", (xs[i], ms[i]), textcoords="offset points",
                     xytext=(0, 11), ha="center", color=INK, fontsize=9)
    ax1.set_ylim(0, max(ms) * 1.3)
    ax1.set_title(f"Running time (median of {REPEATS} random graphs per point)",
                  fontsize=11, loc="left", color=INK)
    ax1.set_ylabel("Running time (milliseconds)", color=INK)
 
    # ---- right: counted work
    glances = [r["glances"] / 1000 for r in rows]
    checks = [r["relax_checks"] / 1000 for r in rows]
    ax2.plot(xs, glances, color=DARK, linewidth=2, marker="o", markersize=8,
             markeredgecolor="white", markeredgewidth=1.5, label="Glances (the 2 x V x V part)")
    ax2.plot(xs, checks, color=ORANGE, linewidth=2, marker="o", markersize=8,
             markeredgecolor="white", markeredgewidth=1.5, label="Relax checks (the E part)")
    ax2.annotate(f"{rows[-1]['glances']:,.0f}", (xs[-1], glances[-1]), textcoords="offset points",
                 xytext=(0, 11), ha="center", color=INK, fontsize=9)
    ax2.annotate(f"{rows[-1]['relax_checks']:,.0f}", (xs[-1], checks[-1]), textcoords="offset points",
                 xytext=(0, 11), ha="center", color=INK, fontsize=9)
    ax2.annotate(f"{rows[0]['relax_checks']:,.0f}", (xs[0], checks[0]), textcoords="offset points",
                 xytext=(0, 11), ha="center", color=INK, fontsize=9)
    ax2.set_ylim(0, max(glances) * 1.3)
    ax2.set_title("Work counted per run (exact, no timing noise)",
                  fontsize=11, loc="left", color=INK)
    ax2.set_ylabel("Operations (thousands)", color=INK)
    ax2.legend(frameon=False, loc="center left", labelcolor=INK, fontsize=9)
 
    for ax in (ax1, ax2):
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, fontsize=7.5, color=MUTED)
        ax.set_xlabel(xlabel, fontsize=8.5, color=INK)
        style_axes(ax)
 
    fig.suptitle(f"Matrix + array Dijkstra with V fixed at {V}: effect of the number of edges E",
                 fontsize=12, x=0.01, ha="left", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(filename)
 
 
# ------------------------------------------------------------------ main
if __name__ == "__main__":
    self_check()
    # one small untimed run first so start up effects do not skew the first point
    dijkstra_matrix(build_matrix(50, random_directed_graph(50, 200, seed=1)), SOURCE)
 
    print(f"V = {V}, most edges possible E_MAX = {E_MAX:,}, {REPEATS} random graphs per E")
    print(f"{'E':>9} {'% full':>7} {'median ms':>10} {'glances':>10} {'relax checks':>13} {'updates':>8}")
    rows = []
    for E in E_VALUES:
        r = measure(E)
        rows.append(r)
        print(f"{r['E']:>9,} {r['percent_full']:>6.3g}% {r['seconds_median'] * 1000:>10.2f} "
              f"{r['glances']:>10,.0f} {r['relax_checks']:>13,.0f} {r['updates']:>8,.0f}", flush=True)
 
    save_csv(rows, "results_vary_E_theory.csv")
    draw_chart(rows, "exp2_vary_E_theory.png")
    print("Saved results_vary_E_theory.csv and exp2_vary_E_theory.png")
    print("glances should be exactly 2 * V * V =", f"{2 * V * V:,}", "at every E.")
 
    if SHOW:
        plt.show()
 
