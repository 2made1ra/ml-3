"""Импорт слепков runs/ в локальный MLflow этой машины — чтобы раны с другой машины были видны в UI.

Запуск из папки лабы после git pull:
    uv run python -m src.sync_mlflow

Пропускает smoke-раны, раны, уже записанные в этот MLflow напрямую (по id рана), и уже
импортированные (тег snapshot = <run_name>@<finished_at>). Повторный запуск безопасен.
"""

import json
import math
from datetime import datetime

import pandas as pd
from mlflow import MlflowClient
from mlflow.entities import Metric, Param
from mlflow.exceptions import MlflowException

from src.results import RUNS_DIR
from src.tracking import setup_mlflow

BATCH = 100  # лимит MLflow на число params/metrics в одном log_batch — с запасом


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, f"{key}."))
        else:
            out[key] = v
    return out


def _exists(client: MlflowClient, run_id: str | None) -> bool:
    if not run_id:
        return False
    try:
        client.get_run(run_id)
    except MlflowException:
        return False
    return True


def _import_run(client: MlflowClient, summary: dict, history: pd.DataFrame, snapshot: str) -> None:
    exp_id = setup_mlflow(summary["config"]["project"])
    ts = int(datetime.fromisoformat(summary["finished_at"]).timestamp() * 1000)
    run = client.create_run(
        exp_id,
        run_name=summary["run_name"],
        start_time=ts,
        tags={
            "snapshot": snapshot,
            "source": "runs-import",
            "host": str(summary.get("host")),
            "device": str(summary.get("device")),
            "git_commit": str(summary.get("git_commit")),
            **{f"env.{k}": str(v) for k, v in _flatten(summary.get("env") or {}).items()},
            **{f"data.{k}": str(v) for k, v in _flatten(summary.get("data") or {}).items()},
        },
    )
    run_id = run.info.run_id

    params = [Param(k, str(v)) for k, v in _flatten(summary["config"]).items()]
    metrics = [
        Metric(col, float(row[col]), ts, int(row["epoch"]))
        for _, row in history.iterrows()
        for col in history.columns
        if col != "epoch" and pd.notna(row[col])
    ]
    metrics += [
        Metric(f"final/{k}", float(v), ts, 0)
        for k, v in _flatten(summary["metrics"]).items()
        if isinstance(v, int | float) and math.isfinite(v)
    ]
    for i in range(0, len(params), BATCH):
        client.log_batch(run_id, params=params[i : i + BATCH])
    for i in range(0, len(metrics), BATCH):
        client.log_batch(run_id, metrics=metrics[i : i + BATCH])
    client.set_terminated(run_id, end_time=ts)


def sync() -> None:
    """Импортирует в MLflow все раны из runs/, которых в нём ещё нет."""
    if not RUNS_DIR.exists():
        print("runs/ нет — нечего импортировать")
        return
    client = None
    for run_dir in sorted(p for p in RUNS_DIR.iterdir() if p.is_dir()):
        if run_dir.name.endswith("-smoke") or not (run_dir / "summary.json").exists():
            continue
        summary = json.loads((run_dir / "summary.json").read_text())
        exp_id = setup_mlflow(summary["config"]["project"])
        client = client or MlflowClient()
        snapshot = f"{summary['run_name']}@{summary['finished_at']}"
        if _exists(client, summary.get("tracker_run")):
            print(f"{run_dir.name}: уже есть в MLflow (обучен на этой машине)")
            continue
        found = client.search_runs([exp_id], filter_string=f"tags.snapshot = '{snapshot}'")
        if found:
            print(f"{run_dir.name}: уже импортирован")
            continue
        _import_run(client, summary, pd.read_csv(run_dir / "history.csv"), snapshot)
        print(f"{run_dir.name}: импортирован ({summary.get('host')}, {summary.get('device')})")


if __name__ == "__main__":
    sync()
