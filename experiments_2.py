"""
experiments.py
Empirical analysis for PART (a): matrix + array Dijkstra on DIRECTED graphs.

Vocabulary:
    glance = the program looking at ONE entry (one row of the distance table or one cell
             of the matrix). Theory says the program makes 2 * V * V glances.

Three experiments:
  Experiment 1: grow V, keep E fixed.      Theory says time grows like V * V.
  Experiment 2: grow E, keep V fixed.      Theory says the glance count does not change;
                                           time may rise a little, because each real edge
                                           costs a bit of extra work.
  Experiment 3: grow V and E together,     a COMPLETE graph: every possible edge exists,
                the most edges possible.   E = V(V-1). Theory still says time grows like V * V.

Every setting is measured in TWO ways:
  - running time in seconds (depends on the computer)
  - number of glances counted by dijkstra_matrix_counted (does NOT depend on the computer)

For every setting we build several random graphs, time ONLY the Dijkstra call
(graph generation and matrix building are not timed), and average the results.

Run it with:
    python experiments.py            full run (can take a few minutes)
    python experiments.py --quick    small sizes, finishes in seconds (good for a first try)
    python experiments.py --show     also pop up the plots on screen
Flags can be combined, for example:   python experiments.py --quick --show

The random graphs are made with NetworkX (python -m pip install networkx), see graph_gen.py.

Outputs (saved next to this file):
    exp1_vary_V.png, exp2_vary_E.png, exp3_complete.png, glance_count.png
    results_vary_V.csv, results_vary_E.csv, results_complete.csv
    CSV columns: V, E, seconds, glances, updates
"""

import csv
import gc
import sys
import time

import matplotlib

QUICK = "--quick" in sys.argv
SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")  # draw to files only, no window
import matplotlib.pyplot as plt

from graph_gen import random_directed_graph  # graphs are made with NetworkX
from dijkstra_matrix import build_matrix, dijkstra_matrix, dijkstra_matrix_counted

# ------------------------------------------------------------------ settings
if QUICK:
    REPEATS = 3
    EXP1_E = 1000                           # E held fixed
    EXP1_V = [50, 100, 150, 200, 250]       # V grows
    EXP2_V = 100                            # V held fixed
    EXP2_E = [200, 1000, 3000, 6000, 9000]  # E grows (max for V=100 is 9900)
    EXP3_V = [40, 80, 120, 160, 200]        # V grows, E = V(V-1) (complete graph)
else:
    REPEATS = 5
    EXP1_E = 5000
    EXP1_V = [200, 400, 600, 800, 1000, 1200, 1400]
    EXP2_V = 500
    EXP2_E = [1000, 5000, 20000, 50000, 100000, 150000, 200000]  # max for V=500 is 249500
    EXP3_V = [100, 200, 300, 400, 500, 600, 700, 800]

SOURCE = 0

# plot look: calm and readable. Measured data in blue/orange, theory in dashed gray.
BLUE = "#2a6fdb"
ORANGE = "#e07a1f"
GRAY = "#6b7280"
GRID = "#e5e7eb"


# ------------------------------------------------------------------ measuring
def measure(V, E):
    """
    Average over REPEATS random graphs. Returns a dictionary:
      seconds = average Dijkstra running time
      glances = average glance count (table glances + matrix row glances)
      updates = average number of times a dist value was lowered
    """
    times, glances, updates = [], [], []
    for r in range(REPEATS):
        edges = random_directed_graph(V, E, seed=V * 1_000_003 + E * 101 + r)
        matrix = build_matrix(V, edges)  # NOT timed

        gc.collect()
        gc.disable()  # stop garbage collection from adding random pauses
        start = time.perf_counter()
        dijkstra_matrix(matrix, SOURCE)  # <- the only thing we time
        elapsed = time.perf_counter() - start
        gc.enable()
        times.append(elapsed)

        # a separate, untimed run of the counting version on the same graph
        _, _, counts = dijkstra_matrix_counted(matrix, SOURCE)
        glances.append(counts["total"])
        updates.append(counts["updates"])

    n = len(times)
    return {
        "V": V,
        "E": E,
        "seconds": sum(times) / n,
        "glances": sum(glances) / n,
        "updates": sum(updates) / n,
    }


def save_csv(filename, rows):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["V", "E", "seconds", "glances", "updates"])
        for r in rows:
            writer.writerow([r["V"], r["E"], r["seconds"], r["glances"], r["updates"]])


def style_axes(ax):
    ax.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)


def plot_time_vs_V(results, title, filename, color, show_E_under_ticks=False):
    """
    Measured time against V, with the best fitting c * V * V curve for comparison.
    If show_E_under_ticks is True, the E value used at each V is written under the V tick,
    which is useful when E changes together with V.
    """
    # least squares fit of  time = c * V^2  (the dashed curve)
    c = sum(r["seconds"] * r["V"] ** 2 for r in results) / sum(r["V"] ** 4 for r in results)

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)
    xs = [r["V"] for r in results]
    ax.plot(xs, [r["seconds"] * 1000 for r in results], color=color, linewidth=2,
            marker="o", markersize=6, label="Measured")
    fine = list(range(min(xs), max(xs) + 1, max(1, (max(xs) - min(xs)) // 100)))
    ax.plot(fine, [c * V**2 * 1000 for V in fine], color=GRAY, linewidth=2,
            linestyle="--", label="Best-fit V × V curve")
    ax.set_title(title, fontsize=11, loc="left")
    if show_E_under_ticks:
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{r['V']}\nE={r['E']:,}" for r in results], fontsize=7)
        ax.set_xlabel("Number of vertices V  (with the number of edges E used at that V)")
    else:
        ax.set_xlabel("Number of vertices V")
    ax.set_ylabel("Running time (milliseconds)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(filename)


# ------------------------------------------------------------------ sweeps over V
def sweep_V(heading, V_list, E_for):
    """Run the graph sizes in V_list; E_for(V) says how many edges to use at each size."""
    print(heading)
    print(f"{'V':>6} {'E':>9} {'time (ms)':>11} {'time/V^2 (ns)':>15} {'glances':>12} {'glances/V^2':>12}")
    results = []
    for V in V_list:
        r = measure(V, E_for(V))
        results.append(r)
        print(f"{V:>6} {r['E']:>9} {r['seconds'] * 1000:>11.2f} "
              f"{r['seconds'] / V**2 * 1e9:>15.1f} {r['glances']:>12.0f} "
              f"{r['glances'] / V**2:>12.3f}")
    return results


def experiment_vary_V():
    results = sweep_V(
        f"\nExperiment 1: vary V, E fixed at {EXP1_E}  ({REPEATS} runs per point)",
        EXP1_V, lambda V: EXP1_E)
    print("If time/V^2 stays roughly constant, time grows like V * V.")
    print("glances/V^2 should be 2.000: the program makes exactly 2 * V * V glances.")

    save_csv("results_vary_V.csv", results)
    plot_time_vs_V(
        results,
        f"Matrix + array Dijkstra: time vs number of vertices (E fixed at {EXP1_E})",
        "exp1_vary_V.png", BLUE)
    print("Saved exp1_vary_V.png and results_vary_V.csv")
    return results


# ------------------------------------------------------------------ experiment 2
def experiment_vary_E():
    print(f"\nExperiment 2: vary E, V fixed at {EXP2_V}  ({REPEATS} runs per point)")
    print(f"{'E':>8} {'time (ms)':>11} {'glances':>12} {'updates':>10}")
    results = []
    for E in EXP2_E:
        r = measure(EXP2_V, E)
        results.append(r)
        print(f"{E:>8} {r['seconds'] * 1000:>11.2f} {r['glances']:>12.0f} {r['updates']:>10.0f}")
    print("The glance count does not change at all: E has no effect on the glances.")
    print("Any rise in time comes from the extra work done on each real edge (add, compare),")
    print("not from the glances.")

    save_csv("results_vary_E.csv", results)

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)
    ax.plot([r["E"] for r in results], [r["seconds"] * 1000 for r in results], color=BLUE,
            linewidth=2, marker="o", markersize=6)
    ax.set_title(f"Matrix + array Dijkstra: time vs number of edges (V fixed at {EXP2_V})",
                 fontsize=11, loc="left")
    ax.set_xlabel("Number of edges E")
    ax.set_ylabel("Running time (milliseconds)")
    ax.set_ylim(bottom=0)  # start at zero so "flat" really looks flat
    style_axes(ax)
    fig.tight_layout()
    fig.savefig("exp2_vary_E.png")
    print("Saved exp2_vary_E.png and results_vary_E.csv")
    return results


# ------------------------------------------------------------------ experiment 3
def experiment_complete():
    results = sweep_V(
        f"\nExperiment 3: complete graphs, E = V(V-1)  ({REPEATS} runs per point)",
        EXP3_V, lambda V: V * (V - 1))
    print("Here E grows like V * V as well (the most edges possible), yet time/V^2 should stay roughly constant.")

    save_csv("results_complete.csv", results)
    plot_time_vs_V(
        results,
        "Matrix + array Dijkstra on complete graphs (every possible edge present)",
        "exp3_complete.png", ORANGE, show_E_under_ticks=True)
    print("Saved exp3_complete.png and results_complete.csv")
    return results


# ------------------------------------------------------------------ glance count plot
def plot_glances(sparse, complete):
    """Glance counts from experiments 1 and 3 on one chart: they land on the same 2 * V * V curve."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)
    ax.plot([r["V"] for r in sparse], [r["glances"] / 1e6 for r in sparse],
            color=BLUE, linewidth=0, marker="o", markersize=8,
            label=f"Experiment 1 graphs (E = {EXP1_E})")
    ax.plot([r["V"] for r in complete], [r["glances"] / 1e6 for r in complete],
            color=ORANGE, linewidth=0, marker="s", markersize=6,
            label="Experiment 3 graphs (complete graphs, E = V(V-1))")
    top = max(r["V"] for r in sparse + complete)
    fine = list(range(0, top + 1, max(1, top // 100)))
    ax.plot(fine, [2 * V**2 / 1e6 for V in fine], color=GRAY, linewidth=2,
            linestyle="--", label="2 × V × V (theory)")
    ax.set_title("Glances counted depend only on V", fontsize=11, loc="left")
    ax.set_xlabel("Number of vertices V")
    ax.set_ylabel("Glances counted (millions)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig("glance_count.png")
    print("\nSaved glance_count.png")


if __name__ == "__main__":
    # one tiny untimed run first so start-up effects do not skew the first data point
    dijkstra_matrix(build_matrix(50, random_directed_graph(50, 200, seed=1)), 0)

    sparse = experiment_vary_V()
    experiment_vary_E()
    complete = experiment_complete()
    plot_glances(sparse, complete)

    if SHOW:
        plt.show()
