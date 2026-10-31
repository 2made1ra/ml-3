"""Локальный слепок рана: runs/<run_name>/{history.csv, summary.json, predictions.csv}.

Пишется в конце обучения на любой машине (Mac или PC), коммитится в git и читается ноутбуком.
Конвенции:
- history.csv: колонки `epoch`, `train_<metric>`, `val_<metric>`, опционально `lr`;
- predictions.csv: `y_true`, `y_pred`, опционально `prob_<class>`;
- metrics: финальные метрики лучшего чекпоинта, test — с префиксом `test_`.
"""

import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

# относительный путь: train запускается из корня лабы, ноутбук лежит там же
RUNS_DIR = Path("runs")


def save_run(
    cfg,
    history: list[dict],
    metrics: dict,
    predictions: pd.DataFrame | None = None,
    *,
    device: str | None = None,
    tracker_run: str | None = None,
) -> Path:
    """Сохраняет слепок рана в runs/<run_name>/ и возвращает путь к папке."""
    run_dir = RUNS_DIR / cfg.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(run_dir / "history.csv", index=False)
    summary = {
        "run_name": cfg.run_name,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "host": platform.node(),
        "device": device,
        "tracker_run": tracker_run,
        "metrics": metrics,
        "config": asdict(cfg),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    if predictions is not None:
        predictions.to_csv(run_dir / "predictions.csv", index=False)
    return run_dir


@dataclass
class Run:
    """Загруженный слепок рана."""

    name: str
    history: pd.DataFrame
    metrics: dict
    config: dict
    device: str | None
    tracker_run: str | None
    predictions: pd.DataFrame | None


def load_run(name: str) -> Run:
    """Загружает слепок рана из runs/<name>/."""
    run_dir = RUNS_DIR / name
    if not run_dir.exists():
        raise FileNotFoundError(f"{run_dir} не найден — сделан ли git pull после обучения?")
    summary = json.loads((run_dir / "summary.json").read_text())
    pred_path = run_dir / "predictions.csv"
    return Run(
        name=name,
        history=pd.read_csv(run_dir / "history.csv"),
        metrics=summary["metrics"],
        config=summary["config"],
        device=summary.get("device"),
        tracker_run=summary.get("tracker_run"),
        predictions=pd.read_csv(pred_path) if pred_path.exists() else None,
    )


def compare_runs(names: list[str] | None = None) -> pd.DataFrame:
    """Таблица финальных метрик по ранам (smoke-раны пропускаются)."""
    if names is None:
        names = sorted(
            p.name for p in RUNS_DIR.iterdir() if p.is_dir() and not p.name.endswith("-smoke")
        )
    rows = []
    for name in names:
        run = load_run(name)
        rows.append({"run": name, "device": run.device, **run.metrics})
    return pd.DataFrame(rows).set_index("run")
