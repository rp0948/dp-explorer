"""Module 2 - static table rendering: text tables and matplotlib figures."""
from __future__ import annotations

from typing import Optional

from .core import INF, Result

PATH_COLOR = "#a8e6a1"      
CELL_COLOR = "#ffffff"
SKIPPED_COLOR = "#e4e4e4"  
PARENT_COLOR = "#ffd59e"
SELECTED_COLOR = "#8ec5ff"


def cell_text(value) -> str:
    if value is None:
        return ""
    return "inf" if value == INF else str(value)


def axis_labels(result: Result):
    """Row and column labels for a result's table."""
    inp = result.inputs
    if result.problem == "knapsack":
        n, cap = len(inp["weights"]), inp["capacity"]
        rows = ["0 items"] + [f"item {i} (w{inp['weights'][i-1]},v{inp['values'][i-1]})"
                              for i in range(1, n + 1)]
        return rows, [str(w) for w in range(cap + 1)]
    if result.problem == "lcs":
        return (["''"] + list(inp["a"]), ["''"] + list(inp["b"]))
    return ["coins"], [str(a) for a in range(inp["amount"] + 1)]


def text_table(result: Result) -> str:
    """Plain-text rendering of the DP table."""
    t = result.table
    if t is None:
        return "(naive recursion keeps no table)"
    rows, cols = axis_labels(result)
    width = max(3, max(len(c) for c in cols))
    label_w = max(len(r) for r in rows)
    on_path = set(result.path)
    lines = [" " * label_w + " | " + " ".join(c.rjust(width + 1) for c in cols)]
    lines.append("-" * len(lines[0]))
    for i, r in enumerate(rows):
        cells = []
        for j in range(t.cols):
            txt = cell_text(t.get(i, j)) or "."
            cells.append((txt + "*" if (i, j) in on_path else txt).rjust(width + 1))
        lines.append(r.ljust(label_w) + " | " + " ".join(cells))
    lines.append("(* marks the cells used to reconstruct the answer)")
    return "\n".join(lines)


def save_table_figure(result: Result, path: str, title: Optional[str] = None,
                      highlight: Optional[tuple] = None, dpi: int = 200) -> None:
    """Draw the DP table to an image: path cells green, uncomputed cells grey."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    from .core import explain

    t = result.table
    if t is None:
        raise ValueError("naive recursion keeps no table to draw")
    row_labels, col_labels = axis_labels(result)
    on_path = set(result.path)
    parents = set()
    if highlight is not None:
        d = explain(result, *highlight)
        if d is not None:
            parents = set(d.inputs)

    cw, ch = 0.55, 0.42
    label_w = 0.12 * max(len(r) for r in row_labels) + 0.3
    fig_w = label_w + cw * t.cols + 0.3
    fig_h = ch * (t.rows + 1) + 0.9
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(-label_w / cw, t.cols)
    ax.set_ylim(t.rows + 0.6, -1.1)
    ax.axis("off")
    for j, c in enumerate(col_labels):
        ax.text(j + 0.5, -0.5, c, ha="center", va="center", fontsize=8, fontweight="bold")
    for i, r in enumerate(row_labels):
        ax.text(-0.1, i + 0.5, r, ha="right", va="center", fontsize=8, fontweight="bold")
        for j in range(t.cols):
            v = t.get(i, j)
            if (i, j) == highlight:
                color = SELECTED_COLOR
            elif (i, j) in parents:
                color = PARENT_COLOR
            elif (i, j) in on_path:
                color = PATH_COLOR
            elif v is None:
                color = SKIPPED_COLOR
            else:
                color = CELL_COLOR
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=color, edgecolor="#555555", lw=0.6))
            ax.text(j + 0.5, i + 0.5, cell_text(v), ha="center", va="center", fontsize=8)
    if title:
        ax.set_title(title, fontsize=10, pad=6)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
