---
paths:
  - "**/reports/**"
---

# Experiment log

- One iteration = one file `reports/iterations/vN.md`, template in `/log-iteration`. Numbering is continuous per lab. Never rewrite past iterations; only append.
- `reports/results.md` is the summary table of all iterations with the best one marked. Updated on every `/log-iteration`.
- Numbers come from `runs/vN/summary.json` and `history.csv` first, then notebook outputs or MLflow. A missing number is written as `TODO: взять из runs/vN`, never guessed.
- One iteration tests one hypothesis (Google Tuning Playbook): one scientific change (architecture, augmentation, loss, data) and its expected effect, written in «Гипотеза». Hyperparameters re-tuned for that change (usually lr) are nuisance changes and named as such; everything else stays fixed. Unrelated changes go to separate iterations.
- Scientific options are compared fairly only when their nuisance hyperparameters are tuned for each option. If the difference is small or depends on lr, tune via `/tune`.
- Record every complication in the code with its reason (section «Усложнения»).
- Record failures and rejected ideas with the reason: they are the raw material for the final conclusions.
- These files are deliverables: write them in Russian.
