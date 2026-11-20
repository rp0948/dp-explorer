"""Module 1 - Algorithm core.Memoized, tabulated and naive recursive solvers for 0/1 Knapsack, LCS and Coin Change, each with solution reconstruction."""
from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

INF = float("inf")

#: A naive run is aborted after this many recursive calls.
NAIVE_CALL_LIMIT = 3_000_000
#: Largest recursion depth the memoized solvers are allowed to use.
MAX_RECURSION_DEPTH = 12_000

Cell = Tuple[int, int]


class NaiveLimitExceeded(RuntimeError):
    """Raised when naive recursion exceeds :data:`NAIVE_CALL_LIMIT` calls."""


class InputTooLarge(ValueError):
    """Raised when a memoized solver would need too deep a recursion."""

# Data structures shared by all modules
class Table:
    """A DP table that is either tabulation or sparse.
    A sparse table only stores the cells that were actually computed, which is
    what makes the memory difference between the two approaches visible.
    """

    def __init__(self, rows: int, cols: int, dense: bool):
        self.rows = rows
        self.cols = cols
        self.dense = dense
        if dense:
            self._data: list = [[None] * cols for _ in range(rows)]
        else:
            self._data = {}

    def get(self, i: int, j: int):
        if self.dense:
            return self._data[i][j]
        return self._data.get((i, j))

    def set(self, i: int, j: int, value) -> None:
        if self.dense:
            self._data[i][j] = value
        else:
            self._data[(i, j)] = value

    def computed(self, i: int, j: int) -> bool:
        return self.get(i, j) is not None

    def count_computed(self) -> int:
        if self.dense:
            return sum(1 for row in self._data for v in row if v is not None)
        return len(self._data)

    def as_rows(self) -> List[list]:
        return [[self.get(i, j) for j in range(self.cols)] for i in range(self.rows)]


@dataclass
class Decision:

    cell: Cell
    label: str                 
    parent: Optional[Cell]    
    inputs: List[Cell]        
    text: str                  


@dataclass
class Result:
    problem: str               
    method: str                
    value: Optional[int]       
    solution: object           
    table: Optional[Table]     
    path: List[Cell]           
    ops: int = 0
    cells: int = 0
    calls: int = 0
    cache_hits: int = 0
    inputs: dict = field(default_factory=dict)


METHODS = ("memo", "tab", "naive")
METHOD_NAMES = {"memo": "Memoization", "tab": "Tabulation", "naive": "Naive recursion"}


@contextmanager
def _recursion_guard(depth_needed: int):
    """Temporarily raise Python's recursion limit for deep memoized recursion."""
    if depth_needed > MAX_RECURSION_DEPTH:
        raise InputTooLarge(
            f"memoization would need recursion depth {depth_needed}, "
            f"above the supported maximum of {MAX_RECURSION_DEPTH}; use tabulation"
        )
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, depth_needed + 500))
    try:
        yield
    finally:
        sys.setrecursionlimit(old)


class _Counter:
    """Counts recursive calls and enforces the naive-call limit."""

    __slots__ = ("calls",)

    def __init__(self):
        self.calls = 0

    def tick(self):
        self.calls += 1
        if self.calls > NAIVE_CALL_LIMIT:
            raise NaiveLimitExceeded(
                f"naive recursion stopped after {NAIVE_CALL_LIMIT:,} calls"
            )

# 0/1 Knapsack  table T[i][w], 0 <= i <= n items, 0 <= w <= W
def _knap_inputs(weights, values, capacity):
    return {"weights": list(weights), "values": list(values), "capacity": capacity}


def _knap_check(weights, values, capacity):
    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")
    if capacity < 0 or any(w < 0 for w in weights) or any(v < 0 for v in values):
        raise ValueError("capacity, weights and values must be non-negative")


def _knap_reconstruct(table: Table, weights, n, capacity):
    """Walk back from T[n][W]; prefer *skip* on ties."""
    items, path = [], []
    w = capacity
    for i in range(n, 0, -1):
        path.append((i, w))
        if table.get(i, w) == table.get(i - 1, w):
            continue
        items.append(i - 1)
        w -= weights[i - 1]
    path.append((0, w))
    items.reverse()
    return items, path


def knapsack_tab(weights: Sequence[int], values: Sequence[int], capacity: int) -> Result:
    _knap_check(weights, values, capacity)
    n = len(weights)
    table = Table(n + 1, capacity + 1, dense=True)
    cells = 0
    for w in range(capacity + 1):
        table.set(0, w, 0)
        cells += 1
    for i in range(1, n + 1):
        wt, val = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            best = table.get(i - 1, w)
            if wt <= w:
                best = max(best, table.get(i - 1, w - wt) + val)
            table.set(i, w, best)
            cells += 1
    items, path = _knap_reconstruct(table, weights, n, capacity)
    return Result("knapsack", "tab", table.get(n, capacity), items, table, path,
                  ops=cells, cells=cells, inputs=_knap_inputs(weights, values, capacity))


def knapsack_memo(weights: Sequence[int], values: Sequence[int], capacity: int) -> Result:
    _knap_check(weights, values, capacity)
    n = len(weights)
    table = Table(n + 1, capacity + 1, dense=False)
    stats = {"calls": 0, "hits": 0}

    def f(i: int, w: int) -> int:
        stats["calls"] += 1
        cached = table.get(i, w)
        if cached is not None:
            stats["hits"] += 1
            return cached
        if i == 0:
            best = 0
        else:
            best = f(i - 1, w)
            if weights[i - 1] <= w:
                best = max(best, f(i - 1, w - weights[i - 1]) + values[i - 1])
        table.set(i, w, best)
        return best

    with _recursion_guard(n + 2):
        value = f(n, capacity)
    items, path = _knap_reconstruct(table, weights, n, capacity)
    cells = table.count_computed()
    return Result("knapsack", "memo", value, items, table, path, ops=cells, cells=cells,
                  calls=stats["calls"], cache_hits=stats["hits"],
                  inputs=_knap_inputs(weights, values, capacity))


def knapsack_naive(weights: Sequence[int], values: Sequence[int], capacity: int) -> Result:
    _knap_check(weights, values, capacity)
    counter = _Counter()

    def g(i: int, w: int):
        counter.tick()
        if i == 0:
            return 0, ()
        skip_v, skip_s = g(i - 1, w)
        if weights[i - 1] <= w:
            take_v, take_s = g(i - 1, w - weights[i - 1])
            take_v += values[i - 1]
            if take_v > skip_v:
                return take_v, take_s + (i - 1,)
        return skip_v, skip_s

    with _recursion_guard(len(weights) + 2):
        value, items = g(len(weights), capacity)
    return Result("knapsack", "naive", value, list(items), None, [], ops=counter.calls,
                  calls=counter.calls, inputs=_knap_inputs(weights, values, capacity))

# LCS  table T[i][j], 0 <= i <= m, 0 <= j <= n

def _lcs_inputs(a, b):
    return {"a": a, "b": b}


def _lcs_reconstruct(table: Table, a: str, b: str):
    """Walk back from T[m][n]; on a mismatch prefer *up* on ties."""
    i, j = len(a), len(b)
    chars, path = [], []
    while i > 0 and j > 0:
        path.append((i, j))
        if a[i - 1] == b[j - 1]:
            chars.append(a[i - 1])
            i, j = i - 1, j - 1
        elif table.get(i - 1, j) >= table.get(i, j - 1):
            i -= 1
        else:
            j -= 1
    path.append((i, j))
    return "".join(reversed(chars)), path


def lcs_tab(a: str, b: str) -> Result:
    m, n = len(a), len(b)
    table = Table(m + 1, n + 1, dense=True)
    cells = 0
    for j in range(n + 1):
        table.set(0, j, 0)
        cells += 1
    for i in range(1, m + 1):
        table.set(i, 0, 0)
        cells += 1
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                table.set(i, j, table.get(i - 1, j - 1) + 1)
            else:
                table.set(i, j, max(table.get(i - 1, j), table.get(i, j - 1)))
            cells += 1
    sol, path = _lcs_reconstruct(table, a, b)
    return Result("lcs", "tab", table.get(m, n), sol, table, path, ops=cells, cells=cells,
                  inputs=_lcs_inputs(a, b))


def lcs_memo(a: str, b: str) -> Result:
    m, n = len(a), len(b)
    table = Table(m + 1, n + 1, dense=False)
    stats = {"calls": 0, "hits": 0}

    def f(i: int, j: int) -> int:
        stats["calls"] += 1
        cached = table.get(i, j)
        if cached is not None:
            stats["hits"] += 1
            return cached
        if i == 0 or j == 0:
            best = 0
        elif a[i - 1] == b[j - 1]:
            best = f(i - 1, j - 1) + 1
        else:
            best = max(f(i - 1, j), f(i, j - 1))
        table.set(i, j, best)
        return best

    with _recursion_guard(m + n + 2):
        value = f(m, n)
    sol, path = _lcs_reconstruct(table, a, b)
    cells = table.count_computed()
    return Result("lcs", "memo", value, sol, table, path, ops=cells, cells=cells,
                  calls=stats["calls"], cache_hits=stats["hits"], inputs=_lcs_inputs(a, b))


def lcs_naive(a: str, b: str) -> Result:
    counter = _Counter()

    def g(i: int, j: int):
        counter.tick()
        if i == 0 or j == 0:
            return 0, ""
        if a[i - 1] == b[j - 1]:
            length, s = g(i - 1, j - 1)
            return length + 1, s + a[i - 1]
        up_len, up_s = g(i - 1, j)
        left_len, left_s = g(i, j - 1)
        return (up_len, up_s) if up_len >= left_len else (left_len, left_s)

    with _recursion_guard(len(a) + len(b) + 2):
        value, sol = g(len(a), len(b))
    return Result("lcs", "naive", value, sol, None, [], ops=counter.calls,
                  calls=counter.calls, inputs=_lcs_inputs(a, b))

# Coin Change table T[0][a], 0 <= a <= V
def _coin_prepare(coins, amount):
    if amount < 0:
        raise ValueError("amount must be non-negative")
    if any(c <= 0 for c in coins):
        raise ValueError("coin values must be positive")
    return sorted(set(coins))


def _coin_inputs(coins, amount):
    return {"coins": list(coins), "amount": amount}


def _coin_reconstruct(table: Table, coins, amount):
    """Walk back from V; use the smallest coin that achieves the optimum."""
    if table.get(0, amount) == INF:
        return None, [(0, amount)]
    used, path, a = [], [], amount
    while a > 0:
        path.append((0, a))
        for c in coins:
            if c <= a and table.get(0, a - c) + 1 == table.get(0, a):
                used.append(c)
                a -= c
                break
    path.append((0, 0))
    return used, path


def coins_tab(coins: Sequence[int], amount: int) -> Result:
    coin_list = _coin_prepare(coins, amount)
    table = Table(1, amount + 1, dense=True)
    table.set(0, 0, 0)
    ops = 0
    for a in range(1, amount + 1):
        best = INF
        for c in coin_list:
            if c > a:
                break
            ops += 1
            cand = table.get(0, a - c) + 1
            if cand < best:
                best = cand
        table.set(0, a, best)
    value = table.get(0, amount)
    solution, path = _coin_reconstruct(table, coin_list, amount)
    return Result("coins", "tab", None if value == INF else value, solution, table, path,
                  ops=ops, cells=amount + 1, inputs=_coin_inputs(coins, amount))


def coins_memo(coins: Sequence[int], amount: int) -> Result:
    coin_list = _coin_prepare(coins, amount)
    table = Table(1, amount + 1, dense=False)
    stats = {"calls": 0, "hits": 0, "ops": 0}

    def f(a: int):
        stats["calls"] += 1
        cached = table.get(0, a)
        if cached is not None:
            stats["hits"] += 1
            return cached
        if a == 0:
            best = 0
        else:
            best = INF
            for c in coin_list:
                if c > a:
                    break
                stats["ops"] += 1
                cand = f(a - c) + 1
                if cand < best:
                    best = cand
        table.set(0, a, best)
        return best

    with _recursion_guard(amount + 2):
        value = f(amount)
    solution, path = _coin_reconstruct(table, coin_list, amount)
    return Result("coins", "memo", None if value == INF else value, solution, table, path,
                  ops=stats["ops"], cells=table.count_computed(), calls=stats["calls"],
                  cache_hits=stats["hits"], inputs=_coin_inputs(coins, amount))


def coins_naive(coins: Sequence[int], amount: int) -> Result:
    coin_list = _coin_prepare(coins, amount)
    counter = _Counter()

    def g(a: int):
        counter.tick()
        if a == 0:
            return 0, ()
        best, best_s = INF, None
        for c in coin_list:
            if c > a:
                break
            cnt, s = g(a - c)
            if cnt + 1 < best:
                best, best_s = cnt + 1, (c,) + s
        return best, best_s

    with _recursion_guard(amount + 2):
        value, sol = g(amount)
    return Result("coins", "naive", None if value == INF else value,
                  None if value == INF else list(sol), None, [], ops=counter.calls,
                  calls=counter.calls, inputs=_coin_inputs(coins, amount))

# Dispatch and cell explanations (used by the table viewer)
SOLVERS = {
    ("knapsack", "memo"): knapsack_memo, ("knapsack", "tab"): knapsack_tab,
    ("knapsack", "naive"): knapsack_naive,
    ("lcs", "memo"): lcs_memo, ("lcs", "tab"): lcs_tab, ("lcs", "naive"): lcs_naive,
    ("coins", "memo"): coins_memo, ("coins", "tab"): coins_tab, ("coins", "naive"): coins_naive,
}


def solve(problem: str, method: str, *args) -> Result:
    """Run ``method`` on ``problem``; ``args`` are the problem's inputs."""
    try:
        solver = SOLVERS[(problem, method)]
    except KeyError:
        raise ValueError(f"unknown problem/method: {problem!r}/{method!r}") from None
    return solver(*args)


def _fmt(v) -> str:
    return "inf" if v == INF else str(v)


def explain(result: Result, i: int, j: int) -> Optional[Decision]:
    """Explain how cell (i, j) got its value, or None if it was not computed."""
    t = result.table
    if t is None or not t.computed(i, j):
        return None
    inp = result.inputs
    v = t.get(i, j)
    if result.problem == "knapsack":
        wts, vals = inp["weights"], inp["values"]
        if i == 0:
            return Decision((i, j), "base", None, [], "No items considered: value is 0.")
        wt, val = wts[i - 1], vals[i - 1]
        skip = (i - 1, j)
        if wt > j:
            return Decision((i, j), "skip", skip, [skip],
                            f"Item {i} (weight {wt}) does not fit in capacity {j}, "
                            f"so copy the cell above: {v}.")
        take = (i - 1, j - wt)
        take_val = t.get(*take) + val if t.computed(*take) else None
        skip_val = t.get(*skip)
        if v == skip_val:
            return Decision((i, j), "skip", skip, [skip, take],
                            f"Skip item {i}: {skip_val} is at least as good as taking it "
                            f"({_fmt(take_val)}). Value {v}.")
        return Decision((i, j), "take", take, [skip, take],
                        f"Take item {i} (weight {wt}, value {val}): "
                        f"{t.get(*take)} + {val} = {v}, better than skipping ({skip_val}).")
    if result.problem == "lcs":
        a, b = inp["a"], inp["b"]
        if i == 0 or j == 0:
            return Decision((i, j), "base", None, [], "An empty prefix: LCS length is 0.")
        diag, up, left = (i - 1, j - 1), (i - 1, j), (i, j - 1)
        if a[i - 1] == b[j - 1]:
            return Decision((i, j), "match", diag, [diag],
                            f"'{a[i - 1]}' = '{b[j - 1]}' match: extend the diagonal cell "
                            f"{t.get(*diag)} by 1 = {v}.")
        if t.get(*up) >= t.get(*left):
            return Decision((i, j), "up", up, [up, left],
                            f"'{a[i - 1]}' != '{b[j - 1]}': take the larger of above "
                            f"({t.get(*up)}) and left ({t.get(*left)}) = {v}, from above.")
        return Decision((i, j), "left", left, [up, left],
                        f"'{a[i - 1]}' != '{b[j - 1]}': take the larger of above "
                        f"({t.get(*up)}) and left ({t.get(*left)}) = {v}, from the left.")
    # coins
    coins = sorted(set(inp["coins"]))
    a = j
    if a == 0:
        return Decision((i, j), "base", None, [], "Amount 0 needs 0 coins.")
    inputs, parent, chosen = [], None, None
    for c in coins:
        if c > a:
            break
        inputs.append((0, a - c))
        if parent is None and t.computed(0, a - c) and t.get(0, a - c) + 1 == v:
            parent, chosen = (0, a - c), c
    if v == INF:
        return Decision((i, j), "coin", None, inputs,
                        f"Amount {a} cannot be made with these coins.")
    return Decision((i, j), "coin", parent, inputs,
                    f"Use a coin of {chosen}: T[{a - chosen}] + 1 = "
                    f"{t.get(*parent)} + 1 = {_fmt(v)}.")
