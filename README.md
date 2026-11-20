# Dynamic Programming Explorer

**Comparing Memoization and Tabulation with Visual Tables**
CSCE 4110 – Algorithms, final project
Author : Rudrakumar Patel

## What it does

| Problem                                            | Time (DP) | Space (DP) |
| -------------------------------------------------- | --------- | ---------- |
| 0/1 Knapsack (n items, capacity W)                 | O(nW)     | O(nW)      |
| Longest Common Subsequence (lengths m, n)          | O(mn)     | O(mn)      |
| Coin Change, fewest coins (n coin types, target V) | O(nV)     | O(V)       |

Every problem is solved three ways: **memoization** , **tabulation** and **naive recursive** baseline for small inputs. For each approach the tool

- draws the filled DP table and explains the decision behind any cell you click,
- reconstructs the answer (chosen items, one LCS, or the coins used),
- reports running time, peak memory and operation counts,
- validates input and handles special cases (empty strings, zero capacity, impossible amounts).

## Requirements

- Python 3.11 or newer.
- tkinter,matplotlib,pytest.

## Installation

```bash
git clone <this repository's URL>
cd dp-explorer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running it

**Graphical viewer**:

```bash
python -m dp_explorer
```

**Command line** (no GUI needed):

```bash
python -m dp_explorer.cli knapsack --weights 1,3,4,5 --values 1,4,5,7 --capacity 7 --method all
python -m dp_explorer.cli lcs --a ABCBDAB --b BDCABA --method memo
python -m dp_explorer.cli coins --coins 1,5,6,9 --amount 11
python -m dp_explorer.cli coins --coins 5,10 --amount 3 --no-table
```

**Benchmarks**

```bash
python -m dp_explorer.benchmark
python -m dp_explorer.benchmark --quick
```

**Tests and validation:**

```bash
python -m pytest
python -m dp_explorer.validation
python tools/make_figures.py
```

## Example usage

```text
$ python -m dp_explorer.cli coins --coins 1,5,6,9 --amount 11 --method tab
=== Tabulation ===
Fewest coins: 2
Coins used  : [5, 6]
Time 0.03 ms | cells 12 | calls 0 | cache hits 0 | operations 27
```

A greedy strategy would pick 9 + 1 + 1 (three coins); dynamic programming finds 5 + 6.
