---
paths:
  - "**/*.ipynb"
---

# Notebooks

- The notebook is the submission: EDA, config, plots, tables, conclusions. Models, datasets and training loops live in `src/`. One-off code (a plot, a table) may stay in a cell.
- Code cells follow "Simplicity" and "Docstrings and comments" in `.claude/rules/training-code.md`.
- Training results come from `runs/` (`load_run`, `compare_runs`, `plot_curves`, `plot_confusion`). A training cell is allowed only behind `RUN_TRAINING = False` and with `cfg = Config(...).smoke_if_needed()`.
- Import from `src` only as `from src.<module> import name[, name as alias]`. `import src.x` and `from src import x` break `/pack-submission`.
- Mark dev-only lines with a trailing `# dev-only` (e.g. the autoreload lines; use `get_ipython().run_line_magic(...)`, not `%` magics: they take the trailing comment as an argument). Packing removes them.
- A cell whose first line is `# user-owned` is the user's code: never edit it without an explicit request (see `.claude/rules/training-code.md`).
- Edit cells with NotebookEdit, one cell at a time. Never rewrite the whole notebook or clear the user's outputs.
- Smoke-test a copy, never the original: `SMOKE=1 uv run jupyter nbconvert --to notebook --execute lab-N.ipynb --output-dir <scratchpad>`.
- Sections follow the assignment's sections with their original numbering (`## 1.2 ...`, see `task/assignment.md`). Teacher-required cells and formatting: «Оформление и сдача» in `task/task.md`.
- A conclusion is a markdown cell `> **Вывод:** ...` right after the plot or table it describes. Written via `/write-conclusion`.
- Plotly only. Every plot has a title and axis labels; train and val curves share one plot.
