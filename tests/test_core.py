import random

import pytest

import reference as ref
from dp_explorer import core, parser
from dp_explorer.core import METHODS, NaiveLimitExceeded, solve
from dp_explorer.validation import CASES


# hand-checked cases
@pytest.mark.parametrize("cid,problem,args,expected,note", CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("method", METHODS)
def test_hand_checked_cases(cid, problem, args, expected, note, method):
    assert solve(problem, method, *args).value == expected


def test_knapsack_known_solution():
    for m in METHODS:
        r = solve("knapsack", m, [1, 3, 4, 5], [1, 4, 5, 7], 7)
        assert r.solution == [1, 2]


def test_lcs_known_unique_solution():
    for m in METHODS:
        assert solve("lcs", m, "AGGTAB", "GXTXAYB").solution == "GTAB"


def test_coin_greedy_counterexample():
    for m in METHODS:
        r = solve("coins", m, [1, 5, 6, 9], 11)
        assert r.value == 2 and sorted(r.solution) == [5, 6]


# random cross-checks vs brute force
@pytest.mark.parametrize("seed", range(60))
def test_knapsack_random(seed):
    rng = random.Random(seed)
    n = rng.randint(0, 11)
    w = [rng.randint(0, 12) for _ in range(n)]
    v = [rng.randint(0, 30) for _ in range(n)]
    cap = rng.randint(0, 40)
    expected = ref.knapsack_bruteforce(w, v, cap)
    results = [solve("knapsack", m, w, v, cap) for m in METHODS]
    for r in results:
        assert r.value == expected
        assert sum(w[i] for i in r.solution) <= cap           
        assert sum(v[i] for i in r.solution) == expected      
        assert len(set(r.solution)) == len(r.solution)        
    assert results[0].solution == results[1].solution == results[2].solution


@pytest.mark.parametrize("seed", range(60))
def test_lcs_random(seed):
    rng = random.Random(seed)
    a, b = parser.random_lcs(rng.randint(0, 9), rng.randint(0, 9), "ABC", seed)
    expected = ref.lcs_bruteforce(a, b)
    results = [solve("lcs", m, a, b) for m in METHODS]
    for r in results:
        assert r.value == expected == len(r.solution)
        assert ref.is_subsequence(r.solution, a) and ref.is_subsequence(r.solution, b)
    assert results[0].solution == results[1].solution == results[2].solution


@pytest.mark.parametrize("seed", range(60))
def test_coins_random(seed):
    rng = random.Random(seed)
    coins = sorted({rng.randint(1, 12) for _ in range(rng.randint(0, 4))})
    amount = rng.randint(0, 30)
    expected = ref.coins_bfs(coins, amount)
    results = [solve("coins", m, coins, amount) for m in METHODS]
    for r in results:
        assert r.value == expected
        if expected is not None:
            assert sum(r.solution) == amount and len(r.solution) == expected
            assert all(c in coins for c in r.solution)
        else:
            assert r.solution is None
    assert results[0].solution == results[1].solution == results[2].solution


def test_known_large_coin_case():
    coins, amount = [186, 419, 83, 408], 6249
    expected = ref.coins_bfs(coins, amount)
    assert expected == 20
    assert solve("coins", "tab", coins, amount).value == 20
    assert solve("coins", "memo", coins, amount).value == 20


# nvalid / odd inputs
def test_core_rejects_bad_numbers():
    with pytest.raises(ValueError):
        solve("knapsack", "tab", [1, 2], [3], 5)
    with pytest.raises(ValueError):
        solve("knapsack", "tab", [-1], [3], 5)
    with pytest.raises(ValueError):
        solve("coins", "tab", [0, 5], 10)
    with pytest.raises(ValueError):
        solve("coins", "tab", [1], -3)
    with pytest.raises(ValueError):
        solve("nope", "tab")


def test_zero_weight_items():
    r = solve("knapsack", "tab", [0, 2], [5, 3], 1)
    assert r.value == 5 and r.solution == [0]


def test_duplicate_coins_are_ignored():
    assert solve("coins", "tab", [5, 5, 1, 1], 6).value == 2


# counters / tables
def test_tabulation_cell_counts_match_formulas():
    assert solve("knapsack", "tab", [1, 2, 3], [1, 2, 3], 10).cells == (3 + 1) * (10 + 1)
    assert solve("lcs", "tab", "ABCD", "XYZ").cells == (4 + 1) * (3 + 1)
    assert solve("coins", "tab", [1, 5], 20).cells == 21


def test_memoization_never_does_more_cell_work_than_tabulation():
    w, v, c = parser.random_knapsack(30, seed=3)
    assert solve("knapsack", "memo", w, v, c).cells <= solve("knapsack", "tab", w, v, c).cells
    a, b = parser.random_lcs(40, 40, seed=3)
    assert solve("lcs", "memo", a, b).cells <= solve("lcs", "tab", a, b).cells


def test_memo_counters_are_consistent():
    r = solve("lcs", "memo", "ABCBDAB", "BDCABA")
    assert r.calls == r.cells + r.cache_hits
    assert r.cache_hits > 0 and r.table.count_computed() == r.cells


def test_naive_makes_many_more_calls_than_dp_cells():
    w, v, c = parser.random_knapsack(14, seed=1)
    assert solve("knapsack", "naive", w, v, c).calls > 10 * solve("knapsack", "tab", w, v, c).cells


def test_naive_limit_is_enforced(monkeypatch):
    monkeypatch.setattr(core, "NAIVE_CALL_LIMIT", 1000)
    with pytest.raises(NaiveLimitExceeded):
        solve("knapsack", "naive", [1] * 30, [1] * 30, 100)


def test_memo_depth_guard():
    with pytest.raises(core.InputTooLarge):
        solve("coins", "memo", [1], core.MAX_RECURSION_DEPTH + 10)
    assert solve("coins", "tab", [1], core.MAX_RECURSION_DEPTH + 10).value == \
        core.MAX_RECURSION_DEPTH + 10


def test_deep_memoization_works():
    assert solve("coins", "memo", [1, 5, 10, 25], 9000).value == \
        solve("coins", "tab", [1, 5, 10, 25], 9000).value


def test_recursion_limit_is_restored():
    import sys
    before = sys.getrecursionlimit()
    solve("lcs", "memo", "A" * 300, "A" * 300)
    assert sys.getrecursionlimit() == before


def test_explain_cells():
    r = solve("knapsack", "tab", [1, 3, 4, 5], [1, 4, 5, 7], 7)
    d = core.explain(r, 3, 7)
    assert d.label == "take" and d.parent == (2, 3) and (2, 7) in d.inputs
    assert core.explain(r, 0, 4).label == "base"
    lcs = solve("lcs", "tab", "AB", "AB")
    assert core.explain(lcs, 1, 1).label == "match"
    assert core.explain(solve("knapsack", "naive", [1], [1], 1), 0, 0) is None
    memo = solve("lcs", "memo", "ABCBDAB", "BDCABA")
    assert core.explain(memo, 0, 4) is None            
