"""Optuna-исследование lr и weight_decay для моделей pytorch_tabular и TabM."""

import argparse
import os
from dataclasses import replace

import optuna

from src.config import Config
from src.tracking import init_tracker
from src.train import apply_set, fit, fit_tabm


def suggest(trial: optuna.Trial, model: str) -> dict:
    """Пространство поиска раунда: переопределения полей Config."""
    if model == "tabm":
        return {
            "lr": trial.suggest_float("lr", 2e-4, 2e-2, log=True),
            "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
        }
    return {
        "lr": trial.suggest_float("lr", 1e-4, 1e-2, log=True),
        "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True),
    }


def objective(trial: optuna.Trial, base: Config) -> float:
    """Обучает модель с параметрами trial и возвращает val macro F1 (test не используется)."""
    cfg = replace(
        base,
        **suggest(trial, base.model),
        run_name=f"{base.run_name}-t{trial.number}",
    )
    tracker = init_tracker(cfg, nested=True)
    if base.model == "tabm":
        _, _, _, metrics = fit_tabm(cfg, tracker)
    else:
        _, _, metrics = fit(cfg, tracker)
    tracker.summary(metrics)
    tracker.finish()
    return metrics["val_f1_macro"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True)
    parser.add_argument("--trials", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=Config.epochs)
    parser.add_argument("--model", required=True, choices=["ft_transformer", "gandalf", "tabm"])
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()

    base = apply_set(
        Config(run_name=args.study, model=args.model, epochs=args.epochs), args.set
    ).smoke_if_needed()
    os.makedirs("runs/tune", exist_ok=True)
    study = optuna.create_study(
        study_name=base.run_name,
        storage=f"sqlite:///runs/tune/{base.run_name}.db",
        load_if_exists=True,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=base.seed),
    )
    parent = init_tracker(base)
    study.optimize(lambda trial: objective(trial, base), n_trials=args.trials)
    parent.summary(
        {
            "best_val_f1_macro": study.best_value,
            **{f"best_{k}": v for k, v in study.best_params.items()},
            "n_trials": len(study.trials),
        }
    )
    parent.finish()
    print(f"Лучшее значение val F1 macro: {study.best_value:.4f}")
    print(f"Лучшие параметры: {study.best_params}")
