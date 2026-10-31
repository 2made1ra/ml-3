---
name: code-lab
description: Write, rewrite or review lab code (data, models, training, notebook). Modes — `all` (plan the whole lab from task.md and implement it step by step), `<task>` (one piece or a rewrite), `review` (check code the user wrote, no generation). The main model decides and verifies; the lab-coder subagent (Sonnet) writes code. Use to implement requirements, change or rewrite code, fix bugs, or review the user's own code.
argument-hint: "all | review [scope] | <what to implement or rewrite> [lab-N]"
---

# /code-lab

You decide and verify; `lab-coder` writes code. You write no `src/` code yourself, except one-line fixes after review. Code marked `# user-owned` is protected (see `.claude/rules/training-code.md`).

## Modes

| Argument | Mode |
| --- | --- |
| `all` or empty | Whole lab: plan, then steps one by one |
| `review [scope]` | Review the user's code only |
| anything else | One task: implement or rewrite |

## Mode: all

1. Build a plan from the unchecked items in `task/task.md` and the current `src/`. Order: data + EDA → baseline model → training loop → experiments → notebook results (plots from `runs/`). One step = one spec that fits one review. Map each step to its requirement numbers.
2. Show the plan to the user (numbered, one line per step) and wait for approval or edits.
3. Run each step through "One task" below. After each step report in 2–3 lines (what was done, smoke result) plus the «Усложнения» section from step 5, and wait for the user's go before the next step: the user may inspect results or write the next piece themselves.
4. When a step fully covers a requirement, tick its checkbox in `task.md`. The checkboxes are the progress state across sessions.

## Mode: one task

### 1. Decide

- Read `task/task.md`, current `src/`, the notebook and recent `reports/iterations/*.md` (do not repeat rejected ideas).
- Decide: files, functions/classes, architecture, loss, metrics, augmentations, default hyperparameters, what to log and save to `runs/`.
- First make sure the design meets the requirement, then make it as simple as possible ("Priorities" in `.claude/rules/training-code.md`).
- List every complication you put into the spec with its reason tied to the goal. No reason, no complication.
- For a rewrite, define the scope: exact files and functions to replace, what stays. If the rewrite changes model or training behavior, the next training run is a new iteration; the old code stays in git history.
- If the scope touches `# user-owned` code, ask the user before writing the spec.
- For a real fork (architecture choice within the assignment's limits, an ambiguous requirement), ask one AskUserQuestion with your recommendation. Decide technical details yourself.

### 2. Spec

Call `Agent` with `subagent_type: "lab-coder"` (in `all` mode, continue the same subagent via `SendMessage` while its context helps; start a fresh one if context is stale). The spec is in English and self-contained; rules already in `.claude/rules/` need no repeating.

```
Lab: <absolute path to lab-N>
Goal: <one sentence>
Requirements: <numbers from task.md>

Change (only these):
- src/data.py: <source (kaggle/HF id), preprocessing, split, augmentations, make_loaders(cfg)>
- src/models.py: <classes, layers, sizes, init>
- src/train.py: <loss, optimizer, scheduler, metrics, early stopping on ..., contents of history/metrics/predictions>
- src/config.py: <new fields and defaults>
- lab-N.ipynb: <cells to add/change, in which sections>

Do not touch: <everything else in scope that must stay, incl. user-owned code>
Complications: <each one with its reason, or "none">
Constraints: <from task.md>
Done when: checks pass, <specific criterion>.
```

### 3. Verify

Do not trust the report. From `lab-N/`, run "Checks" from `CLAUDE.md`. Review `git diff -- lab-N/` for what linters miss:

- matches the spec and `task.md`; nothing outside the declared scope changed; `# user-owned` code untouched;
- the goal is met: the spec's "Done when" holds; nothing the goal needs was dropped for simplicity;
- complications: each one is in the spec or in the subagent's report with a reason tied to the goal. Each carries its `# усложнение:` comment. An unjustified complication is a finding to remove; a justified one added by the subagent goes to the user report;
- simplicity and docstrings: every item of the "Simplicity" and "Docstrings and comments" sections of `.claude/rules/training-code.md` holds. Anything not required (extra options, abstractions, defensive code, long docstrings) is a finding to fix, not a style nit;
- no leakage: normalization stats and vocabularies from train only; test never selects the model;
- `model.eval()` + `inference_mode` on val/test; metric aggregation is correct (per sample vs per batch, macro vs micro);
- the best checkpoint is the one evaluated and saved; `save_run` is called.

### 4. Fix loop

Send findings to the same subagent via `SendMessage`, in English: what, where, expected. Repeat step 3. If it fails twice on the same bug, find the cause yourself and give an exact instruction.

### 5. Report to the user (Russian)

- What was implemented, key decisions, smoke result (duration), what remains.
- Mandatory section «Усложнения»: every complication in the final code (from the spec or added by the subagent), one line each: what — why the goal needs it. If none: «Усложнений нет».
- Next step is usually `/train`.

## Mode: review

For code the user wrote. No subagent, no edits.

1. Scope: the argument, else uncommitted changes (`git diff -- lab-N/`), else files the user names.
2. Run "Checks" from `CLAUDE.md`.
3. Review against `task.md`, `.claude/rules/` and the ML checks from "Verify" above. Also check that the code fits the template contracts (`save_run`, `Config`, `tracking`) so `/train` and the notebook keep working.
4. Report in Russian, most severe first: `файл:строка — проблема — как исправить`. Separate real bugs from style remarks. List complications without a reason tied to the goal as findings.
5. Fix only on the user's request; then the fix goes through "One task" with a scope limited to the findings.
