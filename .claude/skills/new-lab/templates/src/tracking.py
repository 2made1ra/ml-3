"""Единая точка логирования. Бэкенд — Config.tracker или env TRACKER: mlflow | none.

MLflow по умолчанию пишет в одну базу на машину: ~/.mlflow/mlflow.db (все лабы — разные experiments).
UI: `uv run mlflow ui --backend-store-uri sqlite:///$HOME/.mlflow/mlflow.db` из папки любой лабы.
Если задан MLFLOW_TRACKING_URI (например, сервер в локальной сети) — используется он.
"""

import os
from dataclasses import asdict
from pathlib import Path

MLFLOW_HOME = Path.home() / ".mlflow"


def _backend(cfg) -> str:
    return os.environ.get("TRACKER", cfg.tracker)


def setup_mlflow(experiment: str) -> str:
    """Настраивает tracking URI и experiment, возвращает experiment_id."""
    import mlflow

    local = not os.environ.get("MLFLOW_TRACKING_URI")
    if local:
        MLFLOW_HOME.mkdir(exist_ok=True)
        mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_HOME / 'mlflow.db'}")
    exp = mlflow.get_experiment_by_name(experiment)
    if exp is not None:
        return exp.experiment_id
    artifacts = (MLFLOW_HOME / "artifacts" / experiment).as_uri() if local else None
    return mlflow.create_experiment(experiment, artifact_location=artifacts)


class Tracker:
    """Логирование метрик в выбранный трекер (mlflow или none)."""

    def __init__(self, cfg):
        self.backend = _backend(cfg)
        self.run_ref = None  # id рана MLflow — уходит в runs/<run>/summary.json
        params = asdict(cfg)
        if self.backend == "mlflow":
            import mlflow

            exp_id = setup_mlflow(cfg.project)
            run = mlflow.start_run(experiment_id=exp_id, run_name=cfg.run_name)
            mlflow.log_params(params)
            self.run_ref = run.info.run_id
        elif self.backend != "none":
            raise ValueError(f"Неизвестный трекер: {self.backend}")

    def log(self, metrics: dict, step: int | None = None) -> None:
        """Метрики шага (эпохи)."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.log_metrics(metrics, step=step)

    def summary(self, metrics: dict) -> None:
        """Финальные метрики (test и т.п.) — с префиксом final/, чтобы не смешивать с кривыми."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.log_metrics({f"final/{k}": v for k, v in metrics.items()})

    def finish(self) -> None:
        """Закрывает ран."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.end_run()


def init_tracker(cfg) -> Tracker:
    """Создаёт трекер по cfg.tracker или env TRACKER."""
    return Tracker(cfg)


def make_lightning_logger(cfg):
    """Логгер для Lightning Trainer; None — без логирования."""
    backend = _backend(cfg)
    if backend == "mlflow":
        import mlflow
        from lightning.pytorch.loggers import MLFlowLogger

        setup_mlflow(cfg.project)
        logger = MLFlowLogger(
            experiment_name=cfg.project,
            run_name=cfg.run_name,
            tracking_uri=mlflow.get_tracking_uri(),
        )
    else:
        return None
    logger.log_hyperparams(asdict(cfg))
    return logger
