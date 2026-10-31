---
name: train
description: Prepare a full training run of an iteration — estimate Mac time via --benchmark, recommend a machine (Mac M4 or PC with RTX 4090), give exact commands and ask who starts the run (the user, or Claude on the Mac in the background). Use when code is ready to train or the user asks where to train or how long it takes.
argument-hint: "[lab-N] [vN] [mac|pc]"
---

# /train

Training uses the same command on either machine. The user chooses who starts it (section 3). Output: `runs/vN/` (committed) and a run in that machine's local MLflow.

## 1. Prepare

- Run name: next after the latest `runs/v*` (excluding `-smoke`), unless the user names one.
- Smoke must pass (see "Checks" in `CLAUDE.md`).
- Code is committed, also before a Mac run (commit only with the user's consent): then `git_commit` in `summary.json` identifies it; otherwise the run is marked `git_dirty`.
- If the iteration needs nuisance hyperparameters (usually lr) tuned, run `/tune` first.

## 2. Estimate Mac time

Skip if the user already chose the machine: in chat or in «Решения» of `task/task.md`.

```bash
uv run python -m src.train --run vN --benchmark 30
```

Total ≈ `sec/step × steps/epoch × epochs` + 15–25% for validation. The 4090 is 5–15× faster than M4/MPS; less for small models bound by the dataloader. The Mac has 16 GB unified memory: a large batch or model may not fit or may swap.

Recommend:
- **Mac** if the estimate is ≤ 15–20 min and memory fits: saves the push/pull round trip.
- **PC** if longer, if the Mac OOMs or swaps, or for a series of runs or a hyperparameter search.

Show the estimate and the recommendation; the user chooses.

## 3. Commands

From `lab-N/`.

**Mac:** `uv run python -m src.train --run vN`, then `/log-iteration`.

Show the command, then ask who starts it with one AskUserQuestion, giving the time estimate: «Запусти ты» / «Запущу сам». Never start a full run without that answer.
- **Claude starts:** Bash from `lab-N/` with `run_in_background: true`; do not poll, the exit notification arrives on its own. Then check the exit code and `runs/vN/summary.json`, report the duration and the main val metric, and continue with `/log-iteration`. A failure → section 4.
- **The user starts:** wait for their «готово», then `/log-iteration`.

**PC** (always started by the user: Claude has no access to it): first commit and push the code on the Mac (only with the user's consent: `feat(labN): ...`). Then on the PC:

```bash
git pull && cd lab-N && uv sync
uv run python -m src.train --run vN
git add runs/vN && git commit -m "run(labN): vN — <суть>" && git push
```

Live curves during training: `mlflow ui` on the PC. Then on the Mac: `git pull` → `uv run python -m src.sync_mlflow` → `/log-iteration`.

The PC commits only `runs/vN/`, so editing the notebook and `src/` on the Mac meanwhile causes no conflicts.

## 4. Failures

When the user brings a traceback from the PC: find the cause (CUDA OOM → batch size, AMP, gradient accumulation; version mismatch → `uv sync`; NaN → lr, AMP) and fix via `/code-lab`.
