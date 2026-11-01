---
name: mlflow-ui
description: Start, stop or check the local MLflow UI on this machine's DB (~/.mlflow/mlflow.db) in the background. Use when the user wants to see runs and curves in MLflow, asks to raise or restart MLflow, or after /train and sync_mlflow to look at results.
argument-hint: "[start|stop|status|restart] [--port N] [--lab N]"
---

# /mlflow-ui

One script does it: `.claude/skills/mlflow-ui/scripts/mlflow_ui.sh`. It runs `mlflow ui` from a lab's uv env on `~/.mlflow/mlflow.db` (all labs, lab = experiment), in the background, on `127.0.0.1:5050` (5000 is taken by AirPlay on macOS). PID and port: `~/.mlflow/ui.pid`, log: `~/.mlflow/ui.log`.

```bash
.claude/skills/mlflow-ui/scripts/mlflow_ui.sh start     # default; no-op if already running
.claude/skills/mlflow-ui/scripts/mlflow_ui.sh status
.claude/skills/mlflow-ui/scripts/mlflow_ui.sh stop
.claude/skills/mlflow-ui/scripts/mlflow_ui.sh restart --port 5051
```

- Default `$ARGUMENTS` is `start`. Run the script with them and give the user the printed URL; open it in the browser pane only if asked.
- The env comes from `--lab N`, else the newest `lab-*` with a `.venv`.
- The DB is per machine. Runs from the other machine appear after `git pull && uv run python -m src.sync_mlflow` (`CLAUDE.md`, "Stack").
- If `MLFLOW_TRACKING_URI` points to a remote server, the script is not needed.
