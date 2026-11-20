import pytest

from dp_explorer import parser
from dp_explorer.parser import InputError


def test_parse_lists_with_mixed_separators():
    assert parser.parse_int_list("1, 3 4;5", "x") == [1, 3, 4, 5]
    assert parser.parse_int_list("", "x") == []
    assert parser.parse_int_list("   ", "x") == []


@pytest.mark.parametrize("text", ["1, two, 3", "1.5", "-4", "1,,a"])
def test_non_numbers_and_negatives_are_rejected(text):
    with pytest.raises(InputError):
        parser.parse_int_list(text, "Values")


def test_error_message_names_the_field():
    with pytest.raises(InputError, match="Weights"):
        parser.parse_int_list("x", "Weights")


def test_knapsack_parsing_and_mismatch():
    assert parser.parse_knapsack("1 2", "3 4", "5") == ([1, 2], [3, 4], 5)
    with pytest.raises(InputError, match="must match"):
        parser.parse_knapsack("1 2 3", "4 5", "5")
    with pytest.raises(InputError):
        parser.parse_knapsack("1", "2", "")
    with pytest.raises(InputError):
        parser.parse_knapsack("1", "2", "1 2")
    with pytest.raises(InputError, match="maximum"):
        parser.parse_knapsack("1", "2", str(parser.MAX_CAPACITY + 1))
    assert parser.parse_knapsack("", "", "0") == ([], [], 0)


def test_too_many_items():
    big = " ".join(["1"] * (parser.MAX_ITEMS + 1))
    with pytest.raises(InputError, match="At most"):
        parser.parse_knapsack(big, big, "5")


def test_lcs_parsing():
    assert parser.parse_lcs("abc", "") == ("abc", "")
    assert parser.parse_lcs(None, None) == ("", "")
    with pytest.raises(InputError, match="longer"):
        parser.parse_lcs("A" * (parser.MAX_STRING + 1), "B")


def test_coin_parsing():
    assert parser.parse_coins("5, 1, 5, 10", "12") == ([1, 5, 10], 12)
    assert parser.parse_coins("", "0") == ([], 0)
    with pytest.raises(InputError):
        parser.parse_coins("0, 5", "10")
    with pytest.raises(InputError):
        parser.parse_coins("1, 5", "-1")
    with pytest.raises(InputError, match="maximum"):
        parser.parse_coins("1", str(parser.MAX_AMOUNT + 1))


def test_random_generators_are_reproducible():
    assert parser.random_knapsack(6, seed=5) == parser.random_knapsack(6, seed=5)
    assert parser.random_knapsack(6, seed=5) != parser.random_knapsack(6, seed=6)
    assert parser.random_lcs(5, 7, seed=1) == parser.random_lcs(5, 7, seed=1)
    a, b = parser.random_lcs(5, 7, seed=1)
    assert len(a) == 5 and len(b) == 7
    coins, amount = parser.random_coins(4, 10, 33, seed=2)
    assert amount == 33 and coins == sorted(set(coins)) and all(c >= 1 for c in coins)
    w, v, cap = parser.random_knapsack(10, seed=0)
    assert len(w) == len(v) == 10 and cap >= 1
