"""Module 3 - Input parser: validation, special cases and random test cases."""
from __future__ import annotations

import random
import re
from typing import List, Tuple

MAX_ITEMS = 500
MAX_CAPACITY = 5_000
MAX_STRING = 1_000
MAX_AMOUNT = 10_000
MAX_COINS = 100
MAX_NUMBER = 1_000_000


class InputError(ValueError):
    """Raised with a user-friendly message when the input is not valid."""


def parse_int_list(text: str, name: str, minimum: int = 0) -> List[int]:
    """Parse '1, 3 4;5' into [1, 3, 4, 5]; an empty string gives []."""
    parts = [p for p in re.split(r"[,\s;]+", (text or "").strip()) if p]
    numbers = []
    for p in parts:
        try:
            number = int(p)
        except ValueError:
            raise InputError(f"{name}: '{p}' is not a whole number.") from None
        if number < minimum:
            raise InputError(f"{name}: {number} is below the minimum of {minimum}.")
        if number > MAX_NUMBER:
            raise InputError(f"{name}: {number} is above the maximum of {MAX_NUMBER:,}.")
        numbers.append(number)
    return numbers


def parse_single_int(text: str, name: str, maximum: int) -> int:
    values = parse_int_list(text, name)
    if len(values) != 1:
        raise InputError(f"{name}: enter exactly one whole number (not negative).")
    if values[0] > maximum:
        raise InputError(f"{name}: {values[0]} is above the maximum of {maximum:,}.")
    return values[0]


def parse_knapsack(weights_text: str, values_text: str,
                   capacity_text: str) -> Tuple[List[int], List[int], int]:
    weights = parse_int_list(weights_text, "Weights")
    values = parse_int_list(values_text, "Values")
    if len(weights) != len(values):
        raise InputError(
            f"There are {len(weights)} weights but {len(values)} values; they must match.")
    if len(weights) > MAX_ITEMS:
        raise InputError(f"At most {MAX_ITEMS} items are supported.")
    capacity = parse_single_int(capacity_text, "Capacity", MAX_CAPACITY)
    return weights, values, capacity


def parse_lcs(a: str, b: str) -> Tuple[str, str]:
    a, b = (a or "").strip("\r\n"), (b or "").strip("\r\n")
    for name, s in (("First string", a), ("Second string", b)):
        if len(s) > MAX_STRING:
            raise InputError(f"{name} is longer than {MAX_STRING} characters.")
    return a, b


def parse_coins(coins_text: str, amount_text: str) -> Tuple[List[int], int]:
    coins = parse_int_list(coins_text, "Coins", minimum=1)
    if len(coins) > MAX_COINS:
        raise InputError(f"At most {MAX_COINS} coin values are supported.")
    amount = parse_single_int(amount_text, "Target amount", MAX_AMOUNT)
    return sorted(set(coins)), amount


#random test cases 
def random_knapsack(n: int, max_weight: int = 20, max_value: int = 50,
                    seed: int = 0) -> Tuple[List[int], List[int], int]:
    """n random items; capacity is about half of the total weight."""
    rng = random.Random(seed)
    weights = [rng.randint(1, max_weight) for _ in range(n)]
    values = [rng.randint(1, max_value) for _ in range(n)]
    return weights, values, max(1, sum(weights) // 2)


def random_lcs(m: int, n: int, alphabet: str = "ACGT", seed: int = 0) -> Tuple[str, str]:
    rng = random.Random(seed)
    return ("".join(rng.choice(alphabet) for _ in range(m)),
            "".join(rng.choice(alphabet) for _ in range(n)))


def random_coins(k: int = 4, max_coin: int = 25, amount: int = 60,
                 seed: int = 0) -> Tuple[List[int], int]:
    rng = random.Random(seed)
    coins = sorted({rng.randint(1, max_coin) for _ in range(k)})
    return coins, amount
