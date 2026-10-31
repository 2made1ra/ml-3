---
name: new-lab
description: Start a new Deep Learning lab from its assignment (screenshot, PDF or md) — run the /plan-lab analysis (transcript, interview, stage plan task/task.md), then create lab-N/ from the template with its own uv environment and a notebook skeleton following the assignment's sections. Writes no solution code (that is /code-lab). Use when the user starts a new lab or brings a new assignment.
argument-hint: "<lab number> [assignment file or attached image]"
---

# /new-lab

Assignment analysis, scaffold and environment. Data, models and training come later via `/code-lab`.

## 0. Branch

The lab lives on branch `lab-N` ("Git" in `CLAUDE.md`). If it exists, switch to it. Otherwise:

```bash
git switch main && git pull && git switch -c lab-N
```

Uncommitted changes on `main`: ask the user first (commit them to `main`, or carry them into the branch). Assignment files already dropped into `lab-N/task/` are untracked and move with the switch.

## 1. Plan

- If `lab-N/` exists, inspect it (the assignment may already be there) and overwrite nothing.
- Follow `.claude/skills/plan-lab/SKILL.md`: transcript `task/assignment.md`, interview, stage plan `task/task.md`. Continue only when the assignment was readable.

## 2. Scaffold

Target layout: see "Layout" in `CLAUDE.md`.

- `cp -R .claude/skills/new-lab/templates/src lab-N/src`; copy `templates/pyproject.toml` with `lab-N` replaced; set `project = "dl-lab-N"` in `src/config.py`.
- Create empty `runs/`, `reports/iterations/`, `submission/`.
- `cd lab-N && uv sync`. Verify that `uv.lock` has the same torch version for darwin and linux.
- Run the static checks from "Checks" in `CLAUDE.md` (no smoke yet: there is no `train.py`). The template must pass.

## 3. Notebook skeleton lab-N.ipynb

- First cell: `%load_ext autoreload  # dev-only` and `%autoreload 2  # dev-only`.
- Lab title, then one section per assignment section with its original numbering (`## 1.2 ...`): a markdown cell with the requirement, an empty code cell, a placeholder for `> **Вывод:**`.
- Teacher-required cells from «Оформление и сдача» (e.g. a flag cell) where the assignment puts them.
- A final section «Итоговые выводы».

## 4. Finish

- Show the user the stage list, the decisions and the open questions from `task.md`. Never resolve ambiguities silently.
- Offer to commit the scaffold and push the branch: `git push -u origin lab-N`. The board links and the PC need it.
- Next step: `/code-lab all` (stage by stage) or `/code-lab stage 1`.
