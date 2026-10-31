---
name: new-lab
description: Scaffold a new Deep Learning lab — read the assignment (pdf/ipynb/md), create lab-N/ from the template with its own uv environment, a notebook skeleton per requirement and the checklist task/task.md. Writes no solution code (that is /code-lab). Use when the user starts a new lab or brings a new assignment.
argument-hint: "<lab number> [path to assignment]"
---

# /new-lab

Scaffold and assignment analysis only. Data, models and training come later via `/code-lab`.

## 1. Inputs

- Lab number and assignment files. If `lab-N/` exists, inspect it (the assignment may already be there) and overwrite nothing.
- Read the whole assignment: PDF via Read with `pages`, ipynb including the teacher's example code.

## 2. Scaffold

Target layout: see "Layout" in `CLAUDE.md`.

- `cp -R .claude/skills/new-lab/templates/src lab-N/src`; copy `templates/pyproject.toml` with `lab-N` replaced; set `project = "dl-lab-N"` in `src/config.py`.
- Put the assignment originals in `lab-N/task/`. If they are elsewhere, ask: move or copy.
- Create empty `runs/`, `reports/iterations/`, `submission/`.
- `cd lab-N && uv sync`. Verify that `uv.lock` has the same torch version for darwin and linux.
- Run the static checks from "Checks" in `CLAUDE.md` (no smoke yet: there is no `train.py`). The template must pass.

## 3. task/task.md

The lab's main document; `/code-lab` and `/lab-review` work from it. Written in Russian:

```markdown
# Лабораторная N: <тема>

Источник: task/<файл>

## Цель
<1–3 предложения>

## Требования
- [ ] 1. <пункт задания, близко к оригиналу> — <что должно быть в ноутбуке>

## Ограничения
- <запрещено/обязательно: архитектуры, библиотеки, метрики, датасет>

## Критерии оценки / сдача
- <если есть в задании>

## Неясности
- <что можно трактовать по-разному>
```

## 4. Notebook skeleton lab-N.ipynb

- First cell: `%load_ext autoreload  # dev-only` and `%autoreload 2  # dev-only`.
- Lab title, then one `## N. ...` section per `task.md` requirement: a markdown cell with the requirement, an empty code cell, a placeholder for `> **Вывод:**`.
- A final section «Итоговые выводы».

## 5. Finish

- Show the user the requirements checklist and the ambiguities. Never resolve ambiguities silently.
- Next step: `/code-lab`, usually starting with data and EDA.
