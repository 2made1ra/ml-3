---
name: log-iteration
description: Log an experiment iteration of a lab — what changed, metrics from runs/ and MLflow, comparison with the best result, hypotheses and next step — into lab-N/reports/iterations/vN.md and update reports/results.md. Use after training or an experiment, or when the user asks to record results or save the iteration state.
argument-hint: "[lab-N] [what changed]"
---

# /log-iteration

Rules for these files: `.claude/rules/experiments.md`.

## 1. Collect facts

- Lab and iteration: the latest `runs/vN/` without a matching `reports/iterations/vN.md`.
- Sources, in priority order:
  1. `runs/vN/summary.json` (metrics, config, device, host, MLflow run id) and `runs/vN/history.csv` (val loss minimum, overfitting). If the folder is missing after PC training, remind the user to `git pull`.
  2. MLflow, for what the snapshot lacks (e.g. per-step metrics). A run from this machine: by `tracker_run`. A run from the other machine has only snapshot data after `uv run python -m src.sync_mlflow`.
  3. Notebook outputs and what the user said in chat.
- Config diff: `config` in `runs/vN/summary.json` vs `runs/v(N-1)/summary.json`. Code diff: `git diff` of `src/` since the previous iteration's commit.
- Complications: `grep -n "# усложнение:" src/` and the «Усложнения» sections of `/code-lab` reports in this session. A complication in the code diff without such a comment is logged as «причина не зафиксирована» and reported to the user.
- Missing data: ask one question or write `TODO`. Never guess.

## 2. Write reports/iterations/vN.md (Russian)

```markdown
# vN: <суть итерации>

Дата: YYYY-MM-DD · Машина: Mac M4 / RTX 4090 · MLflow run: <tracker_run> · Время обучения: <если известно>

## Что изменилось относительно v(N-1)

| Параметр | v(N-1) | vN |
| --- | ---: | ---: |

Изменения в коде: <1–3 пункта>

Усложнения: <что — зачем это нужно для цели; или «нет»>

## Результаты

| Модель | split | loss | <основная метрика> | <доп. метрика> |
| --- | --- | ---: | ---: | ---: |

Кривые обучения: <переобучение с эпохи K / плато / нестабильность>

## Сравнение с лучшим

Лучший до этого: vK — <метрика>. Сейчас: <метрика> (Δ <+/−>).

## Интерпретация

<гипотезы, привязанные к числам>

## Что дальше

- <следующий эксперимент и ожидаемый эффект>
```

## 3. Update reports/results.md

Create if missing:

```markdown
| Итерация | Суть | Модель | val <метрика> | test <метрика> | Run |
| --- | --- | --- | ---: | ---: | --- |
```

Mark the best row in **bold**. Do not edit old rows except to fix clear errors.

## 4. Finish

Tell the user in 2–3 lines: result, Δ to the best, proposed next step. If the notebook does not show this run yet (`load_run('vN')`), propose adding it via `/code-lab`. Commit only on request: `docs(labN): итерация vN — ...`.
