"""Hand-checked validation cases.python -m dp_explorer.validation`` runs every case with every approach and prints an expected-versus-actual table.
"""
from __future__ import annotations

import csv
import sys

from .core import METHODS, solve
CASES = [
    ("K1", "knapsack", ([1, 3, 4, 5], [1, 4, 5, 7], 7), 9, "items of weight 3 and 4"),
    ("K2", "knapsack", ([10, 20, 30], [60, 100, 120], 50), 220, "classic textbook case"),
    ("K3", "knapsack", ([5, 4, 6, 3], [10, 40, 30, 50], 10), 90, "items of weight 4 and 3"),
    ("K4", "knapsack", ([1, 2, 3], [10, 20, 30], 6), 60, "all items fit"),
    ("K5", "knapsack", ([1, 2], [3, 4], 0), 0, "zero capacity"),
    ("K6", "knapsack", ([], [], 10), 0, "no items"),
    ("K7", "knapsack", ([10], [5], 5), 0, "only item is too heavy"),
    ("L1", "lcs", ("ABCBDAB", "BDCABA"), 4, "textbook example"),
    ("L2", "lcs", ("AGGTAB", "GXTXAYB"), 4, "LCS is GTAB"),
    ("L3", "lcs", ("HELLO", "HELLO"), 5, "identical strings"),
    ("L4", "lcs", ("ABC", "XYZ"), 0, "no common character"),
    ("L5", "lcs", ("", "ABC"), 0, "empty first string"),
    ("L6", "lcs", ("", ""), 0, "both strings empty"),
    ("L7", "lcs", ("AAAA", "AA"), 2, "repeated characters"),
    ("C1", "coins", ([1, 5, 6, 9], 11), 2, "5 + 6 (greedy would use 3 coins)"),
    ("C2", "coins", ([1, 2, 5], 11), 3, "5 + 5 + 1"),
    ("C3", "coins", ([1], 7), 7, "single coin of 1"),
    ("C4", "coins", ([5, 10], 3), None, "impossible amount"),
    ("C5", "coins", ([2], 3), None, "impossible: odd amount, even coin"),
    ("C6", "coins", ([3, 7], 11), None, "impossible: 3a + 7b = 11 has no solution"),
    ("C7", "coins", ([1, 5, 10], 0), 0, "zero amount"),
    ("C8", "coins", ([], 0), 0, "no coins, zero amount"),
    ("C9", "coins", ([], 5), None, "no coins, positive amount"),
]


def run_cases():
    """Yield one row per (case, approach): id, problem, method, expected, actual, ok."""
    for cid, problem, args, expected, note in CASES:
        for method in METHODS:
            actual = solve(problem, method, *args).value
            yield {"case": cid, "problem": problem, "method": method, "note": note,
                   "expected": "impossible" if expected is None else expected,
                   "actual": "impossible" if actual is None else actual,
                   "ok": actual == expected}


def main(argv=None) -> int:
    rows = list(run_cases())
    print(f"{'case':5} {'problem':9} {'method':6} {'expected':>10} {'actual':>10}  result")
    for r in rows:
        print(f"{r['case']:5} {r['problem']:9} {r['method']:6} {str(r['expected']):>10} "
              f"{str(r['actual']):>10}  {'PASS' if r['ok'] else 'FAIL'}")
    failed = [r for r in rows if not r["ok"]]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} checks passed")
    out = (argv or sys.argv[1:] or [None])[0]
    if out:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
