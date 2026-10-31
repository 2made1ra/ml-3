---
name: code-lab
description: Write, fix, rewrite or review lab code (data, models, training, notebook). Modes — `all` (stages of task/task.md one by one), `stage K`, `<task>` (implement something, fix a bug, or rewrite code the user dislikes), `review` (check code the user wrote, no generation). The main model decides and verifies; the lab-coder subagent (Sonnet) writes code. Use to implement stages, fix bugs, rewrite code, or review the user's own code.
argument-hint: "all | stage K | review [scope] | <what to implement, fix or rewrite> [lab-N]"
---

# /code-lab

You decide and verify; `lab-coder` writes code. You write no `src/` code yourself, except one-line fixes after review. Code marked `# user-owned` is protected (see `.claude/rules/training-code.md`).

## Modes

| Argument | Mode |
| --- | --- |
| `all` or empty | Stages of `task/task.md`, one by one |
| `stage K` / `этап K` | One task: stage K of `task/task.md` |
| `review [scope]` | Review the user's code only |
| anything else | One task: new code, a bug fix or a rewrite |

Board: when work on a stage starts, set its kvatask task to «в работе»; after ticking a stage, run `/kva-sync` (`.claude/skills/kva-sync/SKILL.md`).

## Mode: all

1. The plan is the stage list in `task/task.md` (made by `/plan-lab`). Take the first unchecked stage.
2. Run it through "One task". A stage too big for one review becomes several specs, in order. Inside a stage, keep the order: data + EDA → input-independent baseline (majority class or mean predictor, computed in the notebook; the reference point for conclusions) → first model + training loop → experiments (one hypothesis each, `.claude/rules/experiments.md`; nuisance hyperparameters via `/tune`) → notebook results (plots from `runs/`).
3. After each stage report in 2–3 lines (what was done, smoke result) plus «Усложнения» (step 5), and wait for the user's go: the user may inspect results or write the next piece themselves.
4. When the stage's «Готово, когда» holds, tick it (`### [x] Этап K`) and fill its «Результаты».

## Mode: one task

### 1. Decide

- Read the stage in `task/task.md` and the `task/assignment.md` sections it references, current `src/`, the notebook and recent `reports/iterations/*.md` (do not repeat rejected ideas).
- By kind of task:
  - **New code**: files, functions/classes, architecture, loss, metrics, augmentations, default hyperparameters, what to log and save to `runs/`. An experiment states its hypothesis: the scientific change and the expected effect (`.claude/rules/experiments.md`).
  - **Bug fix** (wrong number, crash, suspicious curve): reproduce it first — smoke, the failing cell, or a minimal script in the scratchpad — and write down the symptom and the reproduction command. Find the root cause before writing the spec (read code, run diagnostics in the scratchpad). If the bug changed results, list the affected runs: `runs/*/summary.json` whose `git_commit` contains the buggy code.
  - **Rewrite** (the user dislikes code): state what exactly is disliked and the target state. If the current code is correct and the rewrite only adds complexity, say so and let the user decide. If it changes model or training behavior, the next training run is a new iteration; the old code stays in git history.
- First make sure the design meets the requirement, then make it as simple as possible ("Priorities" in `.claude/rules/training-code.md`).
- List every complication you put into the spec with its reason tied to the goal. No reason, no complication.
- Define the scope: exact files and functions to change, what stays.
- If the scope touches `# user-owned` code, ask the user before writing the spec.
- For a real fork (architecture choice within the assignment's limits, an ambiguous requirement), ask one AskUserQuestion with your recommendation. Decide technical details yourself.

### 2. Spec

Call `Agent` with `subagent_type: "lab-coder"` (in `all` mode, continue the same subagent via `SendMessage` while its context helps; start a fresh one if context is stale). The spec is in English and self-contained; rules already in `.claude/rules/` need no repeating.

```
Lab: <absolute path to lab-N>
Goal: <one sentence>
Stage: <stage number and title from task.md>

Bug (fixes only):
- Symptom: <what is wrong>
- Reproduce: <command>
- Root cause: <file:function, why>

Change (only these):
- src/data.py: <source pinned to a version (kaggle `owner/name/versions/N` or HF id + revision sha), preprocessing, split, augmentations, make_loaders(cfg)>
- src/models.py: <classes, layers, sizes, init>
- src/train.py: <loss, optimizer, scheduler, metrics, early stopping on ..., contents of history/metrics/predictions>
- src/config.py: <new fields and defaults>
- lab-N.ipynb: <cells to add/change, in which sections>

Do not touch: <everything else in scope that must stay, incl. user-owned code>
Complications: <each one with its reason, or "none">
Constraints: <from task.md>
Done when: checks pass, <specific criterion; for a bug: the reproduction passes>.
```

### 3. Verify

Do not trust the report. From `lab-N/`, run "Checks" from `CLAUDE.md`; for a bug fix, also rerun the reproduction. Review `git diff -- lab-N/` for what linters miss:

- matches the spec and `task.md`; nothing outside the declared scope changed; `# user-owned` code untouched;
- the goal is met: the spec's "Done when" holds; nothing the goal needs was dropped for simplicity;
- complications: each one is in the spec or in the subagent's report with a reason tied to the goal. Each carries its `# усложнение:` comment. An unjustified complication is a finding to remove; a justified one added by the subagent goes to the user report;
- simplicity and docstrings: every item of the "Simplicity" and "Docstrings and comments" sections of `.claude/rules/training-code.md` holds. Anything not required (extra options, abstractions, defensive code, long docstrings) is a finding to fix, not a style nit;
- no leakage: normalization stats and vocabularies from train only; test never selects the model;
- `model.eval()` + `inference_mode` on val/test; metric aggregation is correct (per sample vs per batch, macro vs micro);
- the best checkpoint is the one evaluated and saved; `save_run` is called;
- device: the smoke run's `summary.json` shows `mps` on the Mac (`cuda` on the PC). `cpu` only for gradient boosting or with a justified fallback (`.claude/rules/training-code.md`, "Device").

Sanity checks — once per new model, loss or data pipeline (not for hyperparameter-only changes). Run them as a one-off script in the scratchpad, adapted to the lab; it adds no lab code. From `lab-N/`: `PYTHONPATH=. uv run python <scratchpad>/sanity.py`.

- Batch: one batch exactly as the model sees it: shape, dtype, value range, labels.
- Loss at init: the untrained model's first-batch loss; with cross-entropy over C balanced classes ≈ ln(C). A large deviation means a bug in init, labels or loss.
- Overfit one batch: 8–32 fixed samples, ~300 steps; the loss must approach zero (< 0.05 for classification). If it does not, there is a bug.

```python
import math, torch
from src.config import Config
from src.data import make_loaders
from src.models import Net  # adapt to the lab
from src.utils import get_device, seed_everything

cfg = Config(); seed_everything(cfg.seed); device = get_device()
x, y = next(iter(make_loaders(cfg)[0]))  # adapt: the train loader
x, y = x[:16].to(device), y[:16].to(device)
print(x.shape, x.dtype, x.min().item(), x.max().item(), y.tolist())
model, loss_fn = Net().to(device), torch.nn.CrossEntropyLoss()
print("loss@init", loss_fn(model(x), y).item(), "expected", math.log(NUM_CLASSES))
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
for _ in range(300):
    loss = loss_fn(model(x), y); opt.zero_grad(); loss.backward(); opt.step()
print("overfit loss", loss.item())
```

### 4. Fix loop

Send findings to the same subagent via `SendMessage`, in English: what, where, expected. Repeat step 3. If it fails twice on the same bug, find the cause yourself and give an exact instruction.

### 5. Report to the user (Russian)

- What was implemented, key decisions, smoke result (duration), what remains.
- Bug fix: cause (`файл:функция`), what changed, reproduction before → after. Affected runs, if any: they must be retrained or excluded from conclusions; the next `/log-iteration` records it.
- Sanity results, if run: `loss@init X (ожидалось ln C = Y)`, `overfit 1 batch: loss Z за N шагов`.
- Mandatory section «Усложнения»: every complication in the final code (from the spec or added by the subagent), one line each: what — why the goal needs it. If none: «Усложнений нет».
- Next step is usually `/train`.

## Mode: review

For code the user wrote. No subagent, no edits.

1. Scope: the argument, else uncommitted changes (`git diff -- lab-N/`), else files the user names.
2. Run "Checks" from `CLAUDE.md`.
3. Review against `task.md`, `.claude/rules/` and the ML checks from "Verify" above. Also check that the code fits the template contracts (`save_run`, `Config`, `tracking`) so `/train` and the notebook keep working.
4. Report in Russian, most severe first: `файл:строка — проблема — как исправить`. Separate real bugs from style remarks. List complications without a reason tied to the goal as findings.
5. Fix only on the user's request; then the fix goes through "One task" with a scope limited to the findings.
