---
name: lab-review
description: Review a lab before submission — check the notebook against the stages of task/task.md and the teacher's formatting and submission rules, find missing requirements, data leakage, reproducibility issues, unlabeled plots, conclusions without numbers. Use before submitting, before /pack-submission, or when the user asks whether the lab is ready.
argument-hint: "[lab-N]"
---

# /lab-review

Review and report only. Fix nothing without the user's consent.

## 1. Read

- `task/task.md` and `task/assignment.md` (the plan may miss something).
- `lab-N.ipynb` in full, with outputs; `src/*.py`; `reports/results.md`.

## 2. Check

**Stages**: for each stage of `task.md`, its «Готово, когда» holds: done / partial / missing, with a cell or section reference. Every item of «Оформление и сдача» holds (notebook formatting, required flags, file naming, what to submit). Assignment constraints (forbidden models, required metrics, dataset) are met.

**ML correctness**
- No leakage: scalers, vocabularies, normalization fitted on train only; test is not used for early stopping, tuning or model selection.
- `model.eval()` + `no_grad`/`inference_mode` on val and test; `model.train()` restored.
- The metric fits the task (imbalance → macro F1 / balanced accuracy, not accuracy alone).
- Reported numbers come from the best checkpoint, not the last epoch, unless stated otherwise.

**Reproducibility**
- Conventions from `.claude/rules/training-code.md` hold: seeding, seeded splits, `get_device()`.
- The notebook ran top to bottom: monotonic `execution_count`, no error outputs, no cells depending on deleted code.
- No smoke leftovers in outputs (tiny epoch/data counts, `-smoke` run names).
- Final runs have `git_dirty: false` in `summary.json`; dataset versions are pinned in `data.py`.
- Every `load_run(...)` target exists in `runs/` and is committed; notebook numbers match `runs/*/summary.json`; the final run is the best on val, not on test.

**Presentation**: conventions from `.claude/rules/notebooks.md` hold (plot titles and labels, `> **Вывод:**` after key plots, `src` import form). Numbers in conclusions and `reports/` match their sources: run the `numbers-checker` agent (Haiku) on every `> **Вывод:**` cell, `reports/iterations/*.md` and `reports/results.md`, with all `runs/` as Sources; confirm each mismatch yourself before reporting it. The final conclusions section answers the assignment's questions.

## 3. Report (Russian)

```
## Готовность: <готово / почти / нет>

### Этапы
| Этап | Пункты условия | Статус | Где |
| Оформление и сдача | — | <статус> | <что не выполнено> |

### Проблемы (по важности)
1. [критично] ... — ячейка N — как исправить
2. [важно] ...
3. [косметика] ...
```

Ask what to fix. After fixes, propose `/pack-submission`.
