"""Module 2 - Table viewer: the interactive Tkinter application."""
from __future__ import annotations

import time
import tkinter as tk
import tracemalloc
from tkinter import filedialog, messagebox, ttk

from . import parser, render
from .core import (METHOD_NAMES, METHODS, InputTooLarge, NaiveLimitExceeded, Result, explain,
                   solve)

CELL_W, CELL_H = 46, 28
MAX_DRAW_ROWS, MAX_DRAW_COLS = 60, 80
PROBLEMS = {"knapsack": "0/1 Knapsack", "lcs": "Longest Common Subsequence",
            "coins": "Coin Change"}
DEFAULTS = {
    "knapsack": ("1, 3, 4, 5", "1, 4, 5, 7", "7"),
    "lcs": ("ABCBDAB", "BDCABA"),
    "coins": ("1, 5, 6, 9", "11"),
}


def run_once(problem: str, method: str, args: tuple):
    """Solve once and also measure wall time and peak memory."""
    start = time.perf_counter()
    result = solve(problem, method, *args)
    elapsed_ms = (time.perf_counter() - start) * 1000
    tracemalloc.start()
    try:
        solve(problem, method, *args)
        peak_kib = tracemalloc.get_traced_memory()[1] / 1024
    finally:
        tracemalloc.stop()
    return result, elapsed_ms, peak_kib


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dynamic Programming Explorer")
        self.geometry("1180x760")
        self.minsize(900, 600)
        self.result: Result | None = None
        self.selected = None
        self._build()
        self.on_problem_change()

    #layout
    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Problem:").grid(row=0, column=0, sticky="w")
        self.problem_var = tk.StringVar(value="knapsack")
        box = ttk.Combobox(top, state="readonly", width=28, textvariable=self.problem_var,
                           values=[PROBLEMS[k] for k in PROBLEMS])
        box.current(0)
        box.grid(row=0, column=1, padx=6)
        box.bind("<<ComboboxSelected>>", lambda e: self.on_problem_change())
        self.problem_box = box
        ttk.Label(top, text="Approach:").grid(row=0, column=2, padx=(16, 0))
        self.method_var = tk.StringVar(value="tab")
        for k, m in enumerate(METHODS):
            ttk.Radiobutton(top, text=METHOD_NAMES[m], value=m,
                            variable=self.method_var).grid(row=0, column=3 + k, padx=4)

        self.inputs = ttk.LabelFrame(self, text="Input", padding=8)
        self.inputs.pack(fill="x", padx=8)
        self.fields: dict[str, tk.StringVar] = {}

        buttons = ttk.Frame(self, padding=(8, 6))
        buttons.pack(fill="x")
        for text, cmd in (("Solve", self.on_solve), ("Random input", self.on_random),
                          ("Compare all approaches", self.on_compare),
                          ("Save table image...", self.on_save)):
            ttk.Button(buttons, text=text, command=cmd).pack(side="left", padx=4)

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=4)
        left = ttk.Frame(body)
        body.add(left, weight=4)
        self.canvas = tk.Canvas(left, background="white", highlightthickness=1,
                                highlightbackground="#999")
        xs = ttk.Scrollbar(left, orient="horizontal", command=self.canvas.xview)
        ys = ttk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        xs.pack(side="bottom", fill="x")
        ys.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        right = ttk.Frame(body, padding=(8, 0))
        body.add(right, weight=2)
        ttk.Label(right, text="Answer", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.answer = tk.Text(right, height=6, width=42, wrap="word", state="disabled")
        self.answer.pack(fill="x", pady=(0, 6))
        ttk.Label(right, text="Selected cell", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.explain_box = tk.Text(right, height=7, width=42, wrap="word", state="disabled")
        self.explain_box.pack(fill="x", pady=(0, 6))
        ttk.Label(right, text="Metrics", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        cols = ("approach", "time_ms", "mem_kib", "cells", "calls", "hits", "ops")
        self.metrics = ttk.Treeview(right, columns=cols, show="headings", height=4)
        for c, label, w in (("approach", "Approach", 96), ("time_ms", "ms", 52),
                            ("mem_kib", "KiB", 52), ("cells", "Cells", 54),
                            ("calls", "Calls", 54), ("hits", "Hits", 44), ("ops", "Ops", 60)):
            self.metrics.heading(c, text=label)
            self.metrics.column(c, width=w, anchor="e" if c != "approach" else "w")
        self.metrics.pack(fill="x")
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w",
                  padding=(6, 2)).pack(fill="x", side="bottom")

    @property
    def problem(self) -> str:
        return {v: k for k, v in PROBLEMS.items()}[self.problem_box.get()]

    def on_problem_change(self):
        for child in self.inputs.winfo_children():
            child.destroy()
        self.fields = {}
        labels = {"knapsack": [("weights", "Weights (comma separated)"),
                               ("values", "Values (comma separated)"),
                               ("capacity", "Capacity")],
                  "lcs": [("a", "First string"), ("b", "Second string")],
                  "coins": [("coins", "Coin values (comma separated)"),
                            ("amount", "Target amount")]}[self.problem]
        for row, (key, label) in enumerate(labels):
            ttk.Label(self.inputs, text=label).grid(row=row, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            ttk.Entry(self.inputs, textvariable=var, width=60).grid(row=row, column=1,
                                                                    padx=8, sticky="w")
            self.fields[key] = var
        for var, text in zip(self.fields.values(), DEFAULTS[self.problem]):
            var.set(text)
        self.clear_output()

    def clear_output(self):
        self.result = None
        self.selected = None
        self.canvas.delete("all")
        self.set_text(self.answer, "")
        self.set_text(self.explain_box, "")
        for row in self.metrics.get_children():
            self.metrics.delete(row)

    @staticmethod
    def set_text(widget: tk.Text, text: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    # actions
    def read_args(self):
        f = {k: v.get() for k, v in self.fields.items()}
        if self.problem == "knapsack":
            return parser.parse_knapsack(f["weights"], f["values"], f["capacity"])
        if self.problem == "lcs":
            return parser.parse_lcs(f["a"], f["b"])
        return parser.parse_coins(f["coins"], f["amount"])

    def on_random(self):
        seed = int(time.time()) % 10_000
        if self.problem == "knapsack":
            w, v, c = parser.random_knapsack(8, seed=seed)
            vals = (", ".join(map(str, w)), ", ".join(map(str, v)), str(c))
        elif self.problem == "lcs":
            vals = parser.random_lcs(9, 8, seed=seed)
        else:
            coins, amount = parser.random_coins(4, 15, 40, seed=seed)
            vals = (", ".join(map(str, coins)), str(amount))
        for var, text in zip(self.fields.values(), vals):
            var.set(text)
        self.on_solve()

    def on_solve(self):
        try:
            args = self.read_args()
            self.result, ms, kib = run_once(self.problem, self.method_var.get(), args)
        except parser.InputError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        except (NaiveLimitExceeded, InputTooLarge) as exc:
            messagebox.showwarning("Input too large for this approach", str(exc))
            return
        self.selected = None
        self.show_answer(self.result)
        self.draw_table()
        self.set_text(self.explain_box, "Click a cell in the table to see how it was computed."
                      if self.result.table else "Naive recursion keeps no table.")
        for row in self.metrics.get_children():
            self.metrics.delete(row)
        self.add_metric(self.result, ms, kib)
        self.status.set(f"Solved with {METHOD_NAMES[self.result.method]}.")

    def on_compare(self):
        try:
            args = self.read_args()
        except parser.InputError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        for row in self.metrics.get_children():
            self.metrics.delete(row)
        notes = []
        for m in METHODS:
            try:
                res, ms, kib = run_once(self.problem, m, args)
            except (NaiveLimitExceeded, InputTooLarge) as exc:
                notes.append(f"{METHOD_NAMES[m]}: {exc}")
                continue
            self.add_metric(res, ms, kib)
        self.status.set("Compared all approaches." + ("  " + " | ".join(notes) if notes else ""))

    def add_metric(self, r: Result, ms: float, kib: float):
        self.metrics.insert("", "end", values=(METHOD_NAMES[r.method], f"{ms:.3f}",
                                               f"{kib:.1f}", r.cells or "-", r.calls or "-",
                                               r.cache_hits or "-", r.ops))

    def show_answer(self, r: Result):
        if r.problem == "knapsack":
            wts = r.inputs["weights"]
            chosen = ", ".join(f"item {i + 1} (w{wts[i]}, v{r.inputs['values'][i]})"
                               for i in r.solution) or "no items"
            text = (f"Maximum value: {r.value}\nTotal weight: "
                    f"{sum(wts[i] for i in r.solution)} / {r.inputs['capacity']}\n"
                    f"Chosen: {chosen}")
        elif r.problem == "lcs":
            text = f"LCS length: {r.value}\nOne LCS: '{r.solution}'"
        elif r.value is None:
            text = "Impossible: no combination of these coins makes the target amount."
        else:
            text = (f"Fewest coins: {r.value}\nCoins used: {', '.join(map(str, r.solution)) or 'none'}")
        self.set_text(self.answer, text)

    #table
    def draw_table(self):
        self.canvas.delete("all")
        r = self.result
        if r is None or r.table is None:
            return
        t = r.table
        if t.rows > MAX_DRAW_ROWS or t.cols > MAX_DRAW_COLS:
            self.canvas.create_text(20, 20, anchor="nw", fill="#a00",
                                    text=f"Table is {t.rows} x {t.cols}: too large to draw "
                                         f"(limit {MAX_DRAW_ROWS} x {MAX_DRAW_COLS}).\n"
                                         "The answer and metrics are still shown.")
            return
        rows, cols = render.axis_labels(r)
        lw = max(60, 8 * max(len(x) for x in rows) + 14)
        self._lw = lw
        on_path = set(r.path)
        parents = set()
        if self.selected is not None:
            d = explain(r, *self.selected)
            if d:
                parents = set(d.inputs)
        for j, c in enumerate(cols):
            self.canvas.create_text(lw + j * CELL_W + CELL_W / 2, CELL_H / 2, text=c,
                                    font=("TkDefaultFont", 9, "bold"))
        for i, name in enumerate(rows):
            y = (i + 1) * CELL_H
            self.canvas.create_text(lw - 6, y + CELL_H / 2, text=name, anchor="e",
                                    font=("TkDefaultFont", 9, "bold"))
            for j in range(t.cols):
                v = t.get(i, j)
                if (i, j) == self.selected:
                    fill = render.SELECTED_COLOR
                elif (i, j) in parents:
                    fill = render.PARENT_COLOR
                elif (i, j) in on_path:
                    fill = render.PATH_COLOR
                elif v is None:
                    fill = render.SKIPPED_COLOR
                else:
                    fill = render.CELL_COLOR
                x = lw + j * CELL_W
                self.canvas.create_rectangle(x, y, x + CELL_W, y + CELL_H, fill=fill,
                                             outline="#666")
                self.canvas.create_text(x + CELL_W / 2, y + CELL_H / 2,
                                        text=render.cell_text(v))
        self.canvas.configure(scrollregion=(0, 0, lw + t.cols * CELL_W + 10,
                                            (t.rows + 1) * CELL_H + 10))

    def on_canvas_click(self, event):
        r = self.result
        if r is None or r.table is None or not hasattr(self, "_lw"):
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        j, i = int((x - self._lw) // CELL_W), int(y // CELL_H) - 1
        if not (0 <= i < r.table.rows and 0 <= j < r.table.cols):
            return
        self.select_cell(i, j)

    def select_cell(self, i: int, j: int):
        d = explain(self.result, i, j)
        self.selected = (i, j)
        self.draw_table()
        if d is None:
            self.set_text(self.explain_box, f"Cell ({i}, {j}) was never computed: "
                          "memoization only solves the subproblems the answer needs.")
        else:
            self.set_text(self.explain_box, f"Cell ({i}, {j}), decision: {d.label}\n\n{d.text}")

    def on_save(self):
        if self.result is None or self.result.table is None:
            messagebox.showinfo("Nothing to save", "Solve with memoization or tabulation first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG image", "*.png")])
        if path:
            render.save_table_figure(self.result, path, highlight=self.selected)
            self.status.set(f"Saved {path}")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
