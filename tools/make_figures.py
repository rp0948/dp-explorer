"""Regenerate the example table figures used in the report."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dp_explorer.core import solve
from dp_explorer.render import save_table_figure

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "figures")
os.makedirs(OUT, exist_ok=True)

knap = solve("knapsack", "tab", [1, 3, 4, 5], [1, 4, 5, 7], 7)
save_table_figure(knap, os.path.join(OUT, "knapsack_tab.png"), highlight=(3, 7))

lcs_tab = solve("lcs", "tab", "ABCBDAB", "BDCABA")
save_table_figure(lcs_tab, os.path.join(OUT, "lcs_tab.png"), highlight=(4, 4))
lcs_memo = solve("lcs", "memo", "ABCBDAB", "BDCABA")
save_table_figure(lcs_memo, os.path.join(OUT, "lcs_memo.png"), highlight=(4, 4))

coin = solve("coins", "tab", [1, 5, 6, 9], 11)
save_table_figure(coin, os.path.join(OUT, "coins_tab.png"), highlight=(0, 11))
print("figures written to", OUT)
