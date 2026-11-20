"""Command-line interface."""
from __future__ import annotations

import argparse
import sys
import time

from . import parser, render
from .core import METHOD_NAMES, METHODS, InputTooLarge, NaiveLimitExceeded, solve


def describe(result) -> str:
    if result.problem == "knapsack":
        wts = result.inputs["weights"]
        chosen = [f"item {i + 1} (w={wts[i]}, v={result.inputs['values'][i]})"
                  for i in result.solution]
        return (f"Maximum value: {result.value}\n"
                f"Chosen items : {', '.join(chosen) if chosen else 'none'}\n"
                f"Total weight : {sum(wts[i] for i in result.solution)} "
                f"of {result.inputs['capacity']}")
    if result.problem == "lcs":
        return f"LCS length: {result.value}\nOne LCS   : '{result.solution}'"
    if result.value is None:
        return "Impossible: the target amount cannot be made with these coins."
    return f"Fewest coins: {result.value}\nCoins used  : {result.solution}"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dp_explorer.cli", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="problem", required=True)
    k = sub.add_parser("knapsack", help="0/1 Knapsack")
    k.add_argument("--weights", required=True)
    k.add_argument("--values", required=True)
    k.add_argument("--capacity", required=True)
    l = sub.add_parser("lcs", help="Longest Common Subsequence")
    l.add_argument("--a", default="", help="first string")
    l.add_argument("--b", default="", help="second string")
    c = sub.add_parser("coins", help="Coin Change (fewest coins)")
    c.add_argument("--coins", required=True)
    c.add_argument("--amount", required=True)
    for s in (k, l, c):
        s.add_argument("--method", choices=list(METHODS) + ["all"], default="tab")
        s.add_argument("--no-table", action="store_true", help="do not print the DP table")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.problem == "knapsack":
            inputs = parser.parse_knapsack(args.weights, args.values, args.capacity)
        elif args.problem == "lcs":
            inputs = parser.parse_lcs(args.a, args.b)
        else:
            inputs = parser.parse_coins(args.coins, args.amount)
    except parser.InputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    methods = METHODS if args.method == "all" else (args.method,)
    for method in methods:
        print(f"=== {METHOD_NAMES[method]} ===")
        try:
            start = time.perf_counter()
            result = solve(args.problem, method, *inputs)
            elapsed = (time.perf_counter() - start) * 1000
        except (NaiveLimitExceeded, InputTooLarge) as exc:
            print(f"Skipped: {exc}")
            continue
        print(describe(result))
        print(f"Time {elapsed:.3f} ms | cells {result.cells} | calls {result.calls} | "
              f"cache hits {result.cache_hits} | operations {result.ops}")
        if not args.no_table and result.table is not None and result.table.cols <= 40:
            print(render.text_table(result))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
