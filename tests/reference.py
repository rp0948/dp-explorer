"""Independent reference solvers used only by the tests."""
from itertools import combinations
from collections import deque


def knapsack_bruteforce(weights, values, capacity):
    best = 0
    n = len(weights)
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if mask >> i & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity and v > best:
            best = v
    return best


def lcs_bruteforce(a, b):
    """Longest subsequence of the shorter string that is a subsequence of the other."""
    s, t = (a, b) if len(a) <= len(b) else (b, a)

    def is_subseq(x, y):
        it = iter(y)
        return all(ch in it for ch in x)

    for length in range(len(s), -1, -1):
        for idx in combinations(range(len(s)), length):
            if is_subseq("".join(s[i] for i in idx), t):
                return length
    return 0


def coins_bfs(coins, amount):
    """Fewest coins by breadth-first search over amounts ."""
    if amount == 0:
        return 0
    seen = {0}
    queue = deque([(0, 0)])
    while queue:
        total, count = queue.popleft()
        for c in coins:
            nxt = total + c
            if nxt == amount:
                return count + 1
            if nxt < amount and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, count + 1))
    return None


def is_subsequence(x, y):
    it = iter(y)
    return all(ch in it for ch in x)
