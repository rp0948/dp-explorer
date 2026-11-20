"""Draw the architecture diagram used in the report (docs/figures/architecture.png)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "figures", "architecture.png")
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 52); ax.axis("off")

def box(x, y, w, h, text, fc, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=fc, ec="#333333", lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5,
            fontweight="bold" if bold else "normal")

def arrow(x1, y1, x2, y2, label=None, dy=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
                                 lw=1.2, color="#333333"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, label, ha="center", fontsize=7.5,
                color="#444444")

# Module 5 background band
ax.add_patch(FancyBboxPatch((1, 1), 98, 6.2, boxstyle="round,pad=0.3,rounding_size=1",
                            fc="#eeeeee", ec="#888888", lw=1, ls="--"))
ax.text(50, 4.1, "Module 5 - Integration: command-line interface, validation cases and pytest suite",
        ha="center", va="center", fontsize=8.5, style="italic")

box(1, 35, 17, 10, "User input\n(entry fields or\ncommand line)", "#fff4cc")
box(25, 35, 21, 10, "Module 3\nInput parser\nvalidate, generate", "#d9ead3", True)
box(53, 35, 21, 10, "Module 1\nAlgorithm core\nmemo, tab, naive", "#cfe2f3", True)
box(81, 35, 18, 10, "Result\nvalue, solution,\nTable, counters", "#fce5cd")
box(33, 15, 24, 10, "Module 2\nTable viewer\nTkinter + figures", "#d9d2e9", True)
box(73, 15, 24, 10, "Module 4\nBenchmark engine\ntime, memory, ops", "#f4cccc", True)
box(2, 15, 24, 10, "Screen: DP table,\ndecisions, answer,\nmetrics", "#ffffff")
arrow(18.4, 40, 24.6, 40, "text")
arrow(46.4, 40, 52.6, 40, "inputs")
arrow(74.4, 40, 80.6, 40)
arrow(85, 34.6, 52, 25.4, "result")
arrow(92, 34.6, 90, 25.4)
arrow(32.6, 20, 26.4, 20)
ax.text(85, 10.6, "CSV, JSON and plots", ha="center", fontsize=7.5, color="#444444")
arrow(85, 14.6, 85, 12.4)
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("saved", OUT)
