# ML-3: Deep Learning labs

Lab assignments for a Deep Learning course (MSc, semester 3).

## Language

| Context | Language |
| --- | --- |
| Chat with the user | Russian |
| Agent-to-agent: Agent prompts, specs, `SendMessage`, subagent reports | English, always |
| Instruction files: `CLAUDE.md`, `.claude/**` | English |
| Deliverables: notebook markdown and conclusions, `task/assignment.md`, `task/task.md`, kvatask board tasks, `reports/`, `README.md`, `docs/`, commit messages, comments/docstrings/printed messages in lab code | Russian |

Keep ML terms in English (`backbone`, `fine-tuning`, `macro F1`) in any language.

## Communication style

Applies to chat, agent messages, instruction files and code.

- Be concrete: name the file, function, number, command. No vague wording ("some issues", "might be worth", "various", "etc.").
- Be short: one point per sentence, no restating, no filler, no preamble.
- KISS: pick the simplest solution that meets the requirement. No abstractions, options or files "for the future".
- DRY: one fact lives in one place. Reference the source (file, rule, skill) instead of copying it.
- Exception: conclusions written by `/write-conclusion` follow the author's voice from its `style-guide.md`.

## Machines

- **Mac M4, 16 GB (MPS)**: code, EDA, smoke runs, notebook, light training.
- **Linux (Omarchy) + RTX 4090 (CUDA)**: heavy training. Code gets there via `git push` / `git pull`.

`/train` decides where an iteration trains. Device-dependent code uses `get_device()` only (cuda → mps → cpu); libraries with their own device choice get it passed explicitly (`.claude/rules/training-code.md`).

## Workflow

1. `/new-lab N`: assignment analysis via `/plan-lab` (transcript, interview, stage plan `task/task.md`), scaffold, environment. `task.md` drives all later steps. `/kva-sync` mirrors it onto the kvatask board: an epic per lab, a task per stage.
2. `/code-lab <goal>`: the main model decides and writes a spec, `lab-coder` writes code, the main model verifies.
3. `/tune` (when needed): Optuna study of nuisance hyperparameters, planned by the Google Tuning Playbook.
4. `/train`: time estimate, machine choice, the command. Then it asks who starts the run: the user or Claude.
5. Training writes `runs/vN/` (committed) and a run in the machine's local MLflow.
6. `/log-iteration`: iteration log. The notebook plots from `runs/`.
7. `/write-conclusion` → `/lab-review` → `/pack-submission`; `/prep-defense` before the defense.

`runs/*/summary.json` is the source of truth for numbers. MLflow is only a dashboard. The notebook is the submission: it reads `runs/` and does not retrain.

Local files are the source of truth for tasks: `task/task.md` (stages, their content and status) and `task/assignment.md`. The kvatask board is only a view for the user:
- Never take a plan, a task's content or a status from the board.
- Nothing goes onto the board unless it is in `task.md` first.
- On a mismatch `task.md` wins. If the user confirms the board is right, change `task.md` first, then run `/kva-sync`.

## Roles

- **Main model**: decisions (task analysis, approach, experiments), specs, code review, result analysis, conclusions. Does not write `src/` code, except one-line fixes after review.
- **`lab-coder` subagent (Sonnet, medium effort)**: writes code from a spec. Defined in `.claude/agents/lab-coder.md`.
- **User**: edits conclusions; chooses who starts each full training or tuning run. Claude gives the command and asks; it never starts a full run without that answer. Claude starts runs only on the Mac, in the background; PC runs are the user's. Smoke and `--benchmark` Claude runs itself.
- Numbers in conclusions and reports come only from `runs/`, cell outputs or MLflow. Never invent them.

## Layout

```
ml-3/
├── CLAUDE.md, README.md, docs/backlog.md, .pre-commit-config.yaml, .mcp.json
├── secrets.yaml            # per-machine keys, gitignored
├── .claude/{agents,rules,skills,settings.json}
└── lab-N/                  # one lab = one uv project
    ├── pyproject.toml      # uv.lock is committed
    ├── lab-N.ipynb         # submission notebook
    ├── src/                # template: config, utils, tracking, results, plots, sync_mlflow; per lab: data, models, train
    ├── task/               # originals + assignment.md (transcript) + task.md (stage plan)
    ├── runs/vN/            # run snapshots, committed (*-smoke ignored)
    ├── runs/tune/<study>.db  # Optuna studies, committed
    ├── reports/            # iterations/vN.md, results.md
    ├── submission/         # packed notebook
    ├── data/               # datasets, gitignored
    └── artifacts/          # checkpoints, gitignored
```

The notebook sits next to `src/` and `runs/`, so `from src.x import y` and relative paths work without path hacks.

## Environment

- Each lab is its own uv project. Run everything with `uv run` from `lab-N/`. Add dependencies with `uv add`.
- Python 3.13. torch: PyPI on macOS (MPS), index `cu132` on Linux (driver must support CUDA ≥ 13.2). torch versions for both platforms in `uv.lock` must match.
- Template: `.claude/skills/new-lab/templates/`.

## Checks

From `lab-N/`. No tests.

```bash
uv run ruff check src *.ipynb && uv run ruff format --check src && uv run ty check src
SMOKE=1 uv run python -m src.train --run smoke
```

## Stack

- PyTorch by default; Lightning if chosen in `/code-lab`. If the assignment requires another stack, follow the assignment.
- Plots: Plotly. matplotlib/seaborn only when a library offers nothing else.
- Tracking: MLflow, local per machine, one DB for all labs `~/.mlflow/mlflow.db` (lab = experiment). Backend via `TRACKER=mlflow|none`. Machines sync only through `runs/` in git + `uv run python -m src.sync_mlflow`. Never commit or sync the MLflow DB. VPS hub idea: `docs/backlog.md`.
- Data: Kaggle (`kagglehub`) or HF `datasets`, downloaded in `src/data.py`, cached in `lab-N/data/`.

## Reproducibility

- `seed_everything(cfg.seed)` at the start of every run. All hyperparameters live in `Config` and go to MLflow and `summary.json`.
- Splits are seeded. Test data never drives model or hyperparameter selection.
- Dataset versions are pinned (`.claude/rules/training-code.md`). `summary.json` records `git_commit` and `git_dirty`.

## Secrets

- Secrets live in each tool's own store on each machine. Never committed: no `.env`, no `.env.example`, no config files with tokens. The one exception is `secrets.yaml` at the repo root: gitignored, one per machine, each machine with its own key. It holds keys of tools without their own store.
  - Kaggle: `~/.kaggle/` (`kaggle.json` or `access_token`, mode `600`).
  - Hugging Face: `uvx --from huggingface_hub hf auth login` → `~/.cache/huggingface/token`.
  - kvatask (task board, MCP server in `.mcp.json`): `kvatask_api_key` in `secrets.yaml`; `headersHelper` reads it at connection time.
- Code never passes tokens explicitly (`token=...`, `os.environ[...]`); libraries find them.
- Claude never asks for a secret in chat, never reads or prints token files, never enters keys. It gives the login command; the user runs it.
- On 401/403 from `kagglehub`/`datasets`, check the login on that machine first.
- Enforced, not just instructed: `Read` deny rules for token files and `secrets.yaml` in `.claude/settings.json`; gitleaks in the pre-commit hooks. Never print `secrets.yaml` via Bash either.

## Git

- Commit types: `feat(labN)`, `bug(labN)`, `docs(labN)`, `run(labN): vN — ...` (training results), `chore`. Message in Russian.
- Pre-commit hooks (prek, `.pre-commit-config.yaml`): gitleaks, files > 5 MB, `ruff check`. Never bypass them with `--no-verify`; fix the cause.
- Commit only when the user asks. Before committing, check that `data/`, `artifacts/`, `mlflow.db`, `mlruns/`, `mlartifacts/` are not staged.
- Commit notebook outputs (plots must be visible).
