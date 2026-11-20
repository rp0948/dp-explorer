"""Module 4:Benchmark engine.Measures running time, peak memory and operation counts for every approach, writes the raw data to CSV and draws the
comparison plots.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from typing import Callable, Dict, List

from . import parser
from .core import METHOD_NAMES, NaiveLimitExceeded, solve

COINS = [1, 5, 10, 25, 50]
# problem -> (size label, sizes for DP runs, sizes for the naive comparison)
FULL = {
    "knapsack": ([25, 50, 100, 150, 200, 300, 400], list(range(4, 21, 2))),
    "lcs": ([50, 100, 200, 400, 600, 800, 1000], list(range(4, 13))),
    "coins": ([500, 1000, 2000, 4000, 6000, 8000, 10000], list(range(5, 42, 3))),
}
QUICK = {
    "knapsack": ([10, 20, 40], [4, 8, 12]),
    "lcs": ([20, 40, 80], [4, 6, 8]),
    "coins": ([100, 200, 400], [5, 8, 11]),
}
SIZE_LABEL = {"knapsack": "items n (capacity W = 5n)", "lcs": "string length m = n",
              "coins": "target amount V"}
EXPECTED = {"knapsack": "O(nW)", "lcs": "O(mn)", "coins": "O(nV)"}


def make_instance(problem: str, size: int, seed: int = 42):
    """Deterministic benchmark input for a given problem and size."""
    if problem == "knapsack":
        w, v, _ = parser.random_knapsack(size, max_weight=20, max_value=50, seed=seed)
        return (w, v, 5 * size)
    if problem == "lcs":
        return parser.random_lcs(size, size, "ACGT", seed)
    return (COINS, size)


def measure(problem: str, method: str, args: tuple, repeats: int = 5) -> Dict:
    """Time, peak memory and counters for one run."""
    times = []
    result = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = solve(problem, method, *args)
        times.append(time.perf_counter() - t0)
    tracemalloc.start()
    try:
        solve(problem, method, *args)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return {"time_s": statistics.median(times), "time_min_s": min(times),
            "time_max_s": max(times), "peak_kib": peak / 1024, "ops": result.ops,
            "cells": result.cells, "calls": result.calls, "cache_hits": result.cache_hits,
            "value": result.value}


def run_scaling(sizes_by_problem: Dict, repeats: int, log: Callable = print) -> List[Dict]:
    rows = []
    for problem, (dp_sizes, naive_sizes) in sizes_by_problem.items():
        for size in dp_sizes:
            args = make_instance(problem, size)
            values = set()
            for method in ("memo", "tab"):
                row = {"experiment": "scaling", "problem": problem, "method": method,
                       "size": size, **measure(problem, method, args, repeats)}
                values.add(row["value"])
                rows.append(row)
            assert len(values) == 1, "memoization and tabulation disagree"
            log(f"  scaling  {problem:8} size {size:6}  done")
        for size in naive_sizes:
            args = make_instance(problem, size)
            values = set()
            for method in ("naive", "memo", "tab"):
                try:
                    row = {"experiment": "naive", "problem": problem, "method": method,
                           "size": size,
                           **measure(problem, method, args, 1 if method == "naive" else repeats)}
                except NaiveLimitExceeded:
                    continue
                values.add(row["value"])
                rows.append(row)
            assert len(values) <= 1, "approaches disagree"
            log(f"  naive    {problem:8} size {size:6}  done")
    return rows


def _fit(xs, ys):
    """Least-squares line through (xs, ys); returns slope, intercept and R^2."""
    import numpy as np
    slope, intercept = np.polyfit(xs, ys, 1)
    pred = slope * np.array(xs) + intercept
    ss_res = float(((np.array(ys) - pred) ** 2).sum())
    ss_tot = float(((np.array(ys) - np.mean(ys)) ** 2).sum()) or 1.0
    return float(slope), float(intercept), 1 - ss_res / ss_tot


def analyse(rows: List[Dict]) -> Dict:
    """Growth exponents and linear fits."""
    import numpy as np
    out = {}
    for problem in ("knapsack", "lcs", "coins"):
        for method in ("memo", "tab"):
            pts = sorted((r["size"], r["time_s"], r["ops"]) for r in rows
                         if r["experiment"] == "scaling" and r["problem"] == problem
                         and r["method"] == method)
            sizes = [p[0] for p in pts]
            times = [p[1] for p in pts]
            ops = [p[2] for p in pts]
            exponent = float(np.polyfit(np.log(sizes), np.log(times), 1)[0])
            op_exponent = float(np.polyfit(np.log(sizes), np.log(ops), 1)[0])
            slope, _, r2 = _fit(ops, times)
            out[f"{problem}/{method}"] = {"time_exponent": round(exponent, 2),
                                          "ops_exponent": round(op_exponent, 2),
                                          "time_vs_ops_r2": round(r2, 4),
                                          "ns_per_op": round(slope * 1e9, 1)}
    return out


def make_plots(rows: List[Dict], outdir: str) -> List[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullFormatter, ScalarFormatter

    def size_ticks(ax, problem):
        """Label the log x-axis with the sizes actually measured."""
        ticks = FULL[problem][0]
        ticks = ticks[::2] if len(ticks) > 5 else ticks
        ax.set_xticks(ticks)
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.tick_params(axis="x", labelsize=7)

    colors = {"memo": "#1f77b4", "tab": "#d62728", "naive": "#2ca02c"}
    markers = {"memo": "o", "tab": "s", "naive": "^"}
    names = {"knapsack": "0/1 Knapsack", "lcs": "LCS", "coins": "Coin Change"}
    problems = ("knapsack", "lcs", "coins")
    files = []

    def series(experiment, problem, method, key):
        pts = sorted((r["size"], r[key]) for r in rows if r["experiment"] == experiment
                     and r["problem"] == problem and r["method"] == method)
        return [p[0] for p in pts], [p[1] for p in pts]

    def finish(fig, name):
        path = os.path.join(outdir, name)
        fig.tight_layout()
        fig.savefig(path, dpi=200)
        plt.close(fig)
        files.append(path)

    # 1. running time against size, memo vs tab
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, p in zip(axes, problems):
        for m in ("memo", "tab"):
            x, y = series("scaling", p, m, "time_s")
            ax.loglog(x, y, marker=markers[m], color=colors[m], label=METHOD_NAMES[m])
        ax.set_title(f"{names[p]}  ({EXPECTED[p]})", fontsize=10)
        size_ticks(ax, p)
        ax.set_xlabel(SIZE_LABEL[p], fontsize=8)
        ax.set_ylabel("median time (s)", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    finish(fig, "fig_runtime_scaling.png")

    # 2. time against operation count 
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, p in zip(axes, problems):
        for m in ("memo", "tab"):
            pts = sorted((r["ops"], r["time_s"]) for r in rows if r["experiment"] == "scaling"
                         and r["problem"] == p and r["method"] == m)
            ax.plot([a for a, _ in pts], [b for _, b in pts], marker=markers[m],
                    color=colors[m], label=METHOD_NAMES[m])
        ax.set_title(names[p], fontsize=10)
        ax.set_xlabel("operations", fontsize=8)
        ax.set_ylabel("median time (s)", fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    finish(fig, "fig_time_vs_ops.png")

    # 3. peak memory
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, p in zip(axes, problems):
        for m in ("memo", "tab"):
            x, y = series("scaling", p, m, "peak_kib")
            ax.loglog(x, y, marker=markers[m], color=colors[m], label=METHOD_NAMES[m])
        ax.set_title(names[p], fontsize=10)
        size_ticks(ax, p)
        ax.set_xlabel(SIZE_LABEL[p], fontsize=8)
        ax.set_ylabel("peak memory (KiB)", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    finish(fig, "fig_memory.png")

    # 4. naive recursion against DP: number of operations 
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, p in zip(axes, problems):
        for m in ("naive", "memo", "tab"):
            x, y = series("naive", p, m, "ops")
            ax.semilogy(x, y, marker=markers[m], color=colors[m], label=METHOD_NAMES[m])
        ax.set_title(names[p], fontsize=10)
        ax.set_xlabel(SIZE_LABEL[p].split(" (")[0], fontsize=8)
        ax.set_ylabel("operations (log scale)", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    finish(fig, "fig_naive_vs_dp.png")

    # 5. naive recursion against DP: running time 
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, p in zip(axes, problems):
        for m in ("naive", "memo", "tab"):
            x, y = series("naive", p, m, "time_s")
            ax.semilogy(x, y, marker=markers[m], color=colors[m], label=METHOD_NAMES[m])
        ax.set_title(names[p], fontsize=10)
        ax.set_xlabel(SIZE_LABEL[p].split(" (")[0], fontsize=8)
        ax.set_ylabel("median time (s, log scale)", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    finish(fig, "fig_naive_time.png")
    return files


def system_info() -> Dict:
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "cpu_count": os.cpu_count(), "date": time.strftime("%Y-%m-%d")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="results", help="output folder (default: results)")
    ap.add_argument("--quick", action="store_true", help="small sizes for a fast check")
    ap.add_argument("--repeats", type=int, default=None, help="runs per measurement")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    sizes = QUICK if args.quick else FULL
    repeats = args.repeats or (2 if args.quick else 5)
    print(f"Benchmarking ({'quick' if args.quick else 'full'} run, {repeats} repeats)...")
    rows = run_scaling(sizes, repeats)
    fields = ["experiment", "problem", "method", "size", "time_s", "time_min_s", "time_max_s",
              "peak_kib", "ops", "cells", "calls", "cache_hits", "value"]
    with open(os.path.join(args.out, "benchmark_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary = analyse(rows)
    with open(os.path.join(args.out, "benchmark_summary.json"), "w") as f:
        json.dump({"system": system_info(), "repeats": repeats, "fits": summary}, f, indent=2)
    make_plots(rows, args.out)
    print("\nGrowth exponent against input size (expected about 2 for Knapsack and LCS, 1 for Coin Change):")
    for key, val in summary.items():
        print(f"  {key:16} time ~ size^{val['time_exponent']:<5} "
              f"ops ~ size^{val['ops_exponent']:<5} R2(time vs ops) = {val['time_vs_ops_r2']}")
    print(f"\nResults written to {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
