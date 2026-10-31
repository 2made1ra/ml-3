---
name: tune
description: Tune hyperparameters with Optuna following the Google Deep Learning Tuning Playbook — plan a study round (scientific / nuisance / fixed hyperparameters, search space, budget), get src/tune.py implemented, give the run commands, analyze the study and apply the result. Use when an experiment needs hyperparameters (usually lr) tuned, when options must be compared fairly, or when the user asks to tune or search hyperparameters.
argument-hint: "[lab-N] [study name] [what to tune or compare]"
---

# /tune

Optuna searches; the Playbook decides what to search. Code contract: "Only if the lab uses `/tune`" in `.claude/rules/training-code.md`. Who starts a study is the user's choice, as for training (section 3).

## 1. Plan the round

- Goal, one sentence: a scientific question ("is the deeper model better?") or "tune lr for vN".
- Classify the hyperparameters that matter:
  - **scientific**: what the round compares. One study per value: set the value in `Config`, commit, run a study under its own name;
  - **nuisance**: tuned in every study so the comparison is fair. Usually lr, then weight decay; 1–3 parameters;
  - **fixed**: everything else, listed. Conclusions hold only for these values.
- Batch size is not tuned for accuracy: take the largest that fits and runs fast (`--benchmark`), and re-tune lr after changing it.
- Search space: log scale for lr and weight decay, about two orders of magnitude around the current default.
- Budget: trials × time per trial. Time per trial ≈ the `/train` estimate for one run, or less with a reduced `--epochs` (then `--epochs` is a fixed hyperparameter of the round). 20–40 trials for 1–3 parameters with TPE. Pick the machine like `/train` does.
- Show the plan (goal, three groups, space, budget, machine, estimated time) and wait for approval.

## 2. Code

If `fit` or `src/tune.py` is missing, or the space changes, go through `/code-lab` with the contract and the planned `suggest`. Add the dependency with `uv add optuna`. Smoke:

```bash
SMOKE=1 uv run python -m src.tune --study <name> --trials 2
```

## 3. Commands

From `lab-N/`, on the chosen machine:

```bash
uv run python -m src.tune --study <name> --trials N [--epochs E]
```

Who starts it: ask as in `/train`, section 3 (Claude runs only on the Mac, in the background).

On the PC, then: `git add runs/tune/<name>.db && git commit -m "run(labN): tune <name> — <цель раунда>" && git push`. Re-running with the same `--study` resumes it.

## 4. Analyze

`study = optuna.load_study(study_name="<name>", storage="sqlite:///runs/tune/<name>.db")`:

- best value and params; top trials via `study.trials_dataframe()`;
- boundary: if a parameter's best value is near the edge of its range, widen the range and resume the study;
- importance: `optuna.importance.get_param_importances(study)`; drop unimportant parameters from the next round;
- robustness: if the top trials differ by noise only, take a round value from the good region rather than the single best trial.

Decide with the user: show best value and params, importances, the boundary and robustness checks, the top 5 trials; then one AskUserQuestion with your recommendation first — fix the values, widen the range and resume, or another round on other parameters. The choice feeds the next hypothesis batch (`/lab-flow`, «Hypotheses»).

In the notebook's tuning section: `optuna.visualization.plot_optimization_history`, `plot_slice`, `plot_param_importances` (Plotly; import `src.plots` first so the PNG fallback applies).

## 5. Apply

- Chosen values become `Config` defaults (via `/code-lab`), then `/train vN` with the full budget. Only that run has test metrics.
- `/log-iteration` for vN records the round: study, trials, space, chosen values as «вспомогательный» parameters.
- Report to the user (Russian): round goal, chosen values vs old defaults, importance, boundary check, next step.
