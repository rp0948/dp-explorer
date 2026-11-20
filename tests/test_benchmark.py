import os

from dp_explorer import benchmark
def test_quick_benchmark_runs_and_writes_files(tmp_path):
    assert benchmark.main(["--quick", "--out", str(tmp_path), "--repeats", "1"]) == 0
    for name in ("benchmark_results.csv", "benchmark_summary.json", "fig_runtime_scaling.png",
                 "fig_time_vs_ops.png", "fig_memory.png", "fig_naive_vs_dp.png",
                 "fig_naive_time.png"):
        assert os.path.getsize(tmp_path / name) > 0


def test_measure_reports_counters():
    m = benchmark.measure("lcs", "tab", ("ABCD", "ABD"), repeats=2)
    assert m["ops"] == m["cells"] == 5 * 4 and m["value"] == 3
    assert m["peak_kib"] > 0 and m["time_s"] >= 0


def test_instances_are_deterministic():
    assert benchmark.make_instance("knapsack", 20) == benchmark.make_instance("knapsack", 20)
    assert benchmark.make_instance("coins", 50) == (benchmark.COINS, 50)
