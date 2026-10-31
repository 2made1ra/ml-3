"""Локальный слепок рана: runs/<run_name>/{history.csv, summary.json, predictions.csv}.

Пишется в конце обучения на любой машине (Mac или PC), коммитится в git и читается ноутбуком.
Конвенции:
- history.csv: колонки `epoch`, `train_<metric>`, `val_<metric>`, опционально `lr`;
- predictions.csv: `y_true`, `y_pred`, опционально `prob_<class>`;
- metrics: финальные метрики лучшего чекпоинта, test — с префиксом `test_`;
- git_commit / git_dirty: код, на котором обучен ран (dirty — были незакоммиченные правки);
- env: версия Python, прямые зависимости из pyproject.toml и sha256 uv.lock;
- data: отпечаток данных (аргумент `data` save_run, например src.data.fingerprint);
- resources: пиковая память процесса (`peak_rss_mb`) и GPU (`peak_cuda_mb`, None без CUDA).
"""

import hashlib
import json
import platform
import resource
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import torch
from packaging.requirements import Requirement

# относительный путь: train запускается из корня лабы, ноутбук лежит там же
RUNS_DIR = Path("runs")


def _git(*args: str) -> str:
    """Вывод git-команды (пустая строка вне git-репозитория)."""
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def _env() -> dict:
    """Python, версии прямых зависимостей pyproject.toml (под маркеры платформы) и sha256 uv.lock."""
    deps = tomllib.loads(Path("pyproject.toml").read_text())["project"]["dependencies"]
    reqs = [Requirement(d) for d in deps]
    return {
        "python": platform.python_version(),
        "packages": {
            r.name: version(r.name) for r in reqs if r.marker is None or r.marker.evaluate()
        },
        "uv_lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
    }


def check_new_run(run_name: str) -> None:
    """Бросает FileExistsError, если ран уже сохранён (smoke-раны можно перезаписывать)."""
    # раны неизменяемы: перезаписываются только smoke-раны
    run_dir = RUNS_DIR / run_name
    if (run_dir / "summary.json").exists() and not run_name.endswith("-smoke"):
        raise FileExistsError(f"{run_dir} уже есть: раны не перезаписываются, нужен новый vN")


def save_run(
    cfg,
    history: list[dict],
    metrics: dict,
    predictions: pd.DataFrame | None = None,
    *,
    device: str | None = None,
    tracker_run: str | None = None,
    data: dict | None = None,
) -> Path:
    """Сохраняет слепок рана в runs/<run_name>/ и возвращает путь к папке."""
    run_dir = RUNS_DIR / cfg.run_name
    check_new_run(cfg.run_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(run_dir / "history.csv", index=False)
    summary = {
        "run_name": cfg.run_name,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "host": platform.node(),
        "device": device,
        "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        "torch": torch.__version__,
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "src", "pyproject.toml", "uv.lock")),
        "tracker_run": tracker_run,
        "metrics": metrics,
        "config": asdict(cfg),
        "env": _env(),
        "data": data,
        "resources": {
            # ru_maxrss: байты на macOS, КиБ на Linux
            "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            / (2**20 if platform.system() == "Darwin" else 2**10),
            "peak_cuda_mb": torch.cuda.max_memory_allocated() / 2**20
            if torch.cuda.is_available()
            else None,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    if predictions is not None:
        predictions.to_csv(run_dir / "predictions.csv", index=False, float_format="%.5g")
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
    """Таблица финальных метрик по ранам (smoke-раны и runs/tune пропускаются)."""
    if names is None:
        names = sorted(
            p.name
            for p in RUNS_DIR.iterdir()
            if (p / "summary.json").exists() and not p.name.endswith("-smoke")
        )
    rows = []
    for name in names:
        run = load_run(name)
        rows.append({"run": name, "device": run.device, **run.metrics})
    return pd.DataFrame(rows).set_index("run")
