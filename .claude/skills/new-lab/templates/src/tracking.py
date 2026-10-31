"""Единая точка логирования: переключение W&B <-> MLflow одной переменной TRACKER."""

import os
from dataclasses import asdict


def _backend(cfg) -> str:
    return os.environ.get("TRACKER", cfg.tracker)


class Tracker:
    def __init__(self, cfg):
        self.backend = _backend(cfg)
        self.url = None
        params = asdict(cfg)
        if self.backend == "wandb":
            import wandb

            self._run = wandb.init(project=cfg.project, name=cfg.run_name, config=params)
            self.url = self._run.url
        elif self.backend == "mlflow":
            import mlflow

            # MLFLOW_TRACKING_URI задаёт сервер (например http://<mac-ip>:5000), иначе локально
            mlflow.set_experiment(cfg.project)
            self._run = mlflow.start_run(run_name=cfg.run_name)
            mlflow.log_params(params)
            self.url = self._run.info.run_id
        elif self.backend != "none":
            raise ValueError(f"Неизвестный трекер: {self.backend}")

    def log(self, metrics: dict, step: int | None = None) -> None:
        if self.backend == "wandb":
            self._run.log(metrics, step=step)
        elif self.backend == "mlflow":
            import mlflow

            mlflow.log_metrics(metrics, step=step)

    def summary(self, metrics: dict) -> None:
        """Финальные метрики (test и т.п.)."""
        if self.backend == "wandb":
            self._run.summary.update(metrics)
        elif self.backend == "mlflow":
            import mlflow

            mlflow.log_metrics(metrics)

    def finish(self) -> None:
        if self.backend == "wandb":
            self._run.finish()
        elif self.backend == "mlflow":
            import mlflow

            mlflow.end_run()


def init_tracker(cfg) -> Tracker:
    return Tracker(cfg)


def make_lightning_logger(cfg):
    """Логгер для Lightning Trainer; None — без логирования."""
    backend = _backend(cfg)
    if backend == "wandb":
        from lightning.pytorch.loggers import WandbLogger

        logger = WandbLogger(project=cfg.project, name=cfg.run_name)
    elif backend == "mlflow":
        from lightning.pytorch.loggers import MLFlowLogger

        logger = MLFlowLogger(
            experiment_name=cfg.project,
            run_name=cfg.run_name,
            tracking_uri=os.environ.get("MLFLOW_TRACKING_URI"),
        )
    else:
        return None
    logger.log_hyperparams(asdict(cfg))
    return logger
