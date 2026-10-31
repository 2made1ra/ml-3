---
name: pack-submission
description: Build one self-contained submission ipynb from the lab notebook and src/ modules (module code replaces the imports). Use when the user prepares a lab for submission or asks for a single notebook file.
argument-hint: "[lab-N] [--clear-outputs]"
---

# /pack-submission

1. If `/lab-review` was not run, suggest it once.
2. Pack:
   ```bash
   uv run --project lab-N python .claude/skills/pack-submission/pack.py lab-N/lab-N.ipynb
   ```
   Output: `lab-N/submission/lab-N.ipynb`, outputs kept; rename it if «Оформление и сдача» in `task/task.md` sets a file name (`-o`). `--clear-outputs` only if the user wants to submit without them.
3. `Error:` from the script means an import convention is broken (`.claude/rules/notebooks.md`). Fix the import with the user's consent; never work around the script.
4. Smoke-test: copy the packed notebook and `runs/` into an empty scratchpad folder (no `src/` next to it) and run `SMOKE=1 uv run --project <lab-N path> jupyter nbconvert --to notebook --execute lab-N.ipynb --output-dir out` there. EDA data downloads into that folder or needs a path — check `data.py`.
5. Report to the user: file path, script warnings, smoke result. If the teacher must be able to re-run the notebook, discuss: attach `runs/` or embed the snapshots.

How it works: at the first `from src.x import ...`, cells with `src/x.py` and its `src` dependencies are inserted (each module once, dependencies first); `as` aliases become assignments; `# dev-only` lines, `# user-owned` markers and `if __name__ == "__main__":` blocks are removed.
