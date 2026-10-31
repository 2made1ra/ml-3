---
name: write-conclusion
description: Draft a lab conclusion in the author's personal voice (Russian) — a local conclusion after a plot, table or training result, or the notebook's final section. Use when the user asks to write a conclusion, conclusions, summary or lab results.
argument-hint: "[target: cell / experiment / final]"
---

# /write-conclusion

A draft the user will edit. It must sound like the author and rest only on real numbers. The output is Russian; the "Communication style" section of `CLAUDE.md` does not apply to it — `style-guide.md` does.

## 1. Read the style

Read `style-guide.md` (next to this file) in full before writing.

## 2. Collect facts

- Local conclusion: outputs of the cells above the insertion point and the data behind the plot — `runs/<run>/summary.json`, `history.csv`, `predictions.csv` (a Plotly output holds no readable numbers).
- Final conclusion: `task/task.md` (what was required), `reports/results.md`, `reports/iterations/*.md` (decisions, failures, rejected ideas — the best material for honest personal remarks).
- Pick 2–4 concrete facts with numbers. If a plot has no data in `runs/`, ask the user what it shows or use MLflow / iteration files. Never invent numbers or events that did not happen.

## 3. Write

- Local: `> **Вывод:**` + 1–3 paragraphs: result → contrast → cause → interpretation or next step. A short one fits on the `> **Вывод:**` line.
- Final: `## 1. Обзор результатов`, `## 2. Анализ ошибок`, `## 3. Возможные направления улучшения`, adapted to the assignment. Lists only in recommendations.
- At most one personal remark per conclusion. Terms, models, metrics and classes in backticks. Numbers with the source's precision.

## 4. Insert

- Insert as a markdown cell right after the related cell (NotebookEdit, `cell_type: markdown`), unless the user asked to see it in chat.
- Tell the user which spots to check: hedged interpretations and the personal remark (they must confirm it matches their experience).
