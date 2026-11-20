import os

from dp_explorer import cli, render
from dp_explorer.core import solve


def test_text_table_marks_path():
    r = solve("knapsack", "tab", [1, 3, 4, 5], [1, 4, 5, 7], 7)
    text = render.text_table(r)
    assert "9*" in text and "item 4 (w5,v7)" in text
    assert "no table" in render.text_table(solve("lcs", "naive", "A", "A"))


def test_memo_table_shows_uncomputed_cells_as_dots():
    r = solve("lcs", "memo", "ABCBDAB", "BDCABA")
    assert " . " in render.text_table(r) or " ." in render.text_table(r)


def test_save_figure(tmp_path):
    r = solve("lcs", "tab", "ABCBDAB", "BDCABA")
    out = tmp_path / "t.png"
    render.save_table_figure(r, str(out), title="LCS", highlight=(3, 3))
    assert out.exists() and out.stat().st_size > 1000


def test_cli_runs_all_problems(capsys):
    assert cli.main(["knapsack", "--weights", "1,3,4,5", "--values", "1,4,5,7",
                     "--capacity", "7", "--method", "all"]) == 0
    assert "Maximum value: 9" in capsys.readouterr().out
    assert cli.main(["lcs", "--a", "ABCBDAB", "--b", "BDCABA"]) == 0
    assert "LCS length: 4" in capsys.readouterr().out
    assert cli.main(["coins", "--coins", "5,10", "--amount", "3", "--no-table"]) == 0
    assert "Impossible" in capsys.readouterr().out


def test_cli_reports_bad_input(capsys):
    assert cli.main(["knapsack", "--weights", "1,x", "--values", "1,2", "--capacity", "5"]) == 2
    assert "Input error" in capsys.readouterr().err
