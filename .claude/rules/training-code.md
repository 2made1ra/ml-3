---
paths:
  - "**/src/**/*.py"
---

# Training code in src/

## Priorities

1. The requirement is met correctly (the assignment and the spec's "Done when").
2. Among working solutions, the simplest one wins.

Simplicity never justifies dropping something the goal needs. Complexity is allowed only when the goal needs it, and then it must be justified.

## Complications

A complication is anything beyond the straightforward implementation: an item from the forbidden list below, or an extra technique (AMP, gradient accumulation, custom loss, custom scheduler, mixed or custom sampling, caching, multiprocessing tricks, a hand-written replacement for a library primitive).

- Each complication has a reason tied to the goal: a requirement, a measured problem (OOM, NaN, too slow, metric not reached), or a constraint of the assignment. "Might help" or "best practice" is not a reason.
- Each complication carries a one-line Russian comment with its reason where it is introduced: `# усложнение: <зачем> (<чем подтверждено>)`, e.g. `# усложнение: accumulation 4 шага — batch 128 не влезает в 24 GB (OOM на v2)`.
- Each complication is reported to the user with its reason (see `/code-lab`), and logged in the iteration file (see `/log-iteration`).

## Simplicity

Lab code is read by a student and a teacher. Applies to `src/` and notebook code cells.

- Implement exactly what the spec or requirement asks. No extra features, options, CLI flags, `Config` fields or "nice to have" metrics.
- A `Config` field only for a value that actually changes between experiments. Everything else is a plain constant or argument.
- Functions over classes. A class only where the framework requires one (`nn.Module`, `Dataset`, `LightningModule`) or it holds real state (`Tracker`).
- Forbidden unless the spec names them as a justified complication: inheritance hierarchies beyond the framework base class, abstract base classes, registries, factories, builder or strategy patterns, custom decorators, metaclasses, `Protocol`/generic typing, plugin or hook systems.
- No generalization for hypothetical cases: no parameters, branches or modules for "future" models, datasets or devices.
- Use library primitives instead of hand-written equivalents: `nn.Sequential`, torchvision/`timm` models, `torchvision.transforms.v2`, `sklearn.metrics`, `torch.optim.lr_scheduler`.
- Flat and explicit: a train/eval loop written out step by step. Guidelines, not limits: nesting depth about 3, a function about one screen (~40 lines). Split only by meaning (`train_one_epoch`, `evaluate`), never just to hit a number.
- No defensive code for impossible states. `try/except` only for a specific expected error, never bare or broad.
- Type hints on public function signatures with plain types (`int`, `Tensor`, `pd.DataFrame`, `X | None`).
- Files: the template modules + `data.py`, `models.py`, `train.py`. A new module only if the spec names it.
- If you see a simpler solution than the spec, do not deviate silently: implement the spec and propose the simpler variant in the report.
- If the simple solution cannot meet the goal, do not cut the goal: add the minimal complication that fixes it and report it with the reason.

## Docstrings and comments

- Every public function and class gets a docstring; private helpers (`_name`) only if non-obvious.
- One line, Russian, says what it does or returns, not how: `"""Возвращает train/val/test DataLoader'ы."""`.
- A second line only for something the signature does not show (shape, units, side effect): `"""Логиты формы (batch, num_classes)."""`.
- No `Args:`/`Returns:`/`Raises:` sections, no restating of type hints, no examples.
- Comments only for a non-obvious "why", one line. No comments that restate the code.

## Conventions

- Device: `get_device()` from `src/utils.py` only. No `.cuda()` or `device="cuda"`. AMP: `torch.autocast(device_type=device.type, ...)`; bf16 on CUDA, fp16 on MPS only if verified.
- Datasets are defined in `src/data.py`: on macOS, `DataLoader(num_workers>0)` cannot pickle classes defined in a notebook. `pin_memory=True` on CUDA only.
- All hyperparameters live in `Config` (`src/config.py`). `smoke_if_needed()` shrinks epochs, batch and data under `SMOKE=1` and sets `tracker="none"`.
- Logging goes through `src/tracking.py` only; no direct `mlflow.*` calls elsewhere. The full `asdict(cfg)` is logged; final metrics go through `tracker.summary()` (prefix `final/`).
- Seeding: `seed_everything(cfg.seed)` at run start; a seeded `generator` for `random_split` and `DataLoader`.
- At the end of training call `save_run(cfg, history, metrics, predictions, device=..., tracker_run=tracker.run_ref)` from `src/results.py`. Column conventions are in its docstring. Anything the notebook needs from model weights (Grad-CAM, error examples) is computed at the end of training and saved as a small file in `runs/<run_name>/`.
- `src/train.py` contract:
  - `train(cfg) -> dict`: train, early stopping on val, best checkpoint to `artifacts/<run_name>_best.pt`, evaluate the best checkpoint on test, `save_run(...)`.
  - CLI `uv run python -m src.train --run vN [--epochs ..] [--benchmark K]`. Build the config as `Config(run_name=args.run, ...).smoke_if_needed()` so a smoke run lands in `runs/<name>-smoke/` (gitignored).
  - `--benchmark K`: K steps on the full config, no tracker, no saving; print `sec/step`, `steps/epoch`, estimated total time.
- Importing a module must not run anything. CLI code goes under `if __name__ == "__main__":` (packing removes it).
- Import sibling modules as `from src.utils import ...`, not relative imports.
- Lightning only if the lab chose it.
- `# user-owned` marks code the user wrote: on its own line directly above a `def`/`class`, it protects that definition; as the first line of a file, the whole file. Agents may read and call it, never edit, move or reformat it without the user's explicit request. Lint and format findings in user-owned code are reported, not fixed.
- No tests. Quality gates: `ruff` and `ty` (config in the lab's `pyproject.toml`). `# noqa` / `# ty: ignore[...]` only for confirmed false positives, with a short reason.
