"""Обучение CatBoost baseline: uv run python -m src.train --run vN [--benchmark K]."""

import argparse
import time
from dataclasses import replace

import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

from src.config import Config
from src.data import CLASSES, load_splits, to_xy
from src.results import save_run
from src.tracking import init_tracker
from src.utils import seed_everything


def compute_metrics(y_true, y_pred, proba) -> dict:
    """F1 macro, balanced accuracy, F1 weighted, ROC AUC OvR (метки 0..5)."""
    return {
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "balanced_acc": balanced_accuracy_score(y_true, y_pred),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "roc_auc_ovr": roc_auc_score(
            y_true, proba, multi_class="ovr", labels=list(range(len(CLASSES)))
        ),
    }


def make_model(cfg: Config) -> CatBoostClassifier:
    """CatBoost с параметрами из cfg."""
    return CatBoostClassifier(
        iterations=cfg.cb_iterations,
        learning_rate=cfg.cb_learning_rate,
        depth=cfg.cb_depth,
        l2_leaf_reg=cfg.cb_l2_leaf_reg,
        border_count=cfg.cb_border_count,
        auto_class_weights="Balanced",
        random_seed=cfg.seed,
        verbose=0,
        allow_writing_files=False,  # без папки catboost_info
    )


def train(cfg: Config) -> dict:
    """Обучает CatBoost, оценивает лучшую модель на val и test, сохраняет ран."""
    seed_everything(cfg.seed)
    tracker = init_tracker(cfg)
    train_df, val_df, test_df = load_splits(cfg.seed)
    X_train, y_train = to_xy(train_df)
    X_val, y_val = to_xy(val_df)
    X_test, y_test = to_xy(test_df)

    model = make_model(cfg)
    start = time.time()
    model.fit(
        X_train,
        y_train,
        eval_set=(X_val, y_val),
        early_stopping_rounds=cfg.cb_early_stopping,
    )
    train_time = time.time() - start

    evals = model.get_evals_result()
    train_loss = evals["learn"]["MultiClass"]
    val_loss = evals["validation"]["MultiClass"]
    history = []
    for i, (tl, vl) in enumerate(zip(train_loss, val_loss, strict=True), start=1):
        history.append({"epoch": i, "train_loss": tl, "val_loss": vl})
        tracker.log({"train_loss": tl, "val_loss": vl}, step=i)

    metrics = {}
    for name, X, y in [("val", X_val, y_val), ("test", X_test, y_test)]:
        proba = model.predict_proba(X)
        pred = proba.argmax(axis=1)
        metrics.update({f"{name}_{k}": v for k, v in compute_metrics(y, pred, proba).items()})
    metrics.update(
        best_iteration=model.get_best_iteration(),
        train_time_sec=train_time,
        n_train=len(train_df),
        n_val=len(val_df),
        n_test=len(test_df),
    )
    tracker.summary(metrics)
    model.save_model(f"artifacts/{cfg.run_name}_best.cbm")

    proba = model.predict_proba(X_test)
    predictions = pd.DataFrame(
        {"y_true": y_test + CLASSES[0], "y_pred": proba.argmax(axis=1) + CLASSES[0]}
    )
    for i, c in enumerate(CLASSES):
        predictions[f"prob_{c}"] = proba[:, i]

    save_run(cfg, history, metrics, predictions, device="cpu", tracker_run=tracker.run_ref)
    tracker.finish()
    print(
        f"val F1 macro: {metrics['val_f1_macro']:.4f}, test F1 macro: {metrics['test_f1_macro']:.4f}"
    )
    return metrics


def benchmark(cfg: Config, k: int) -> None:
    """Замер времени k итераций на полных данных, оценка полного обучения."""
    train_df, val_df, _ = load_splits(cfg.seed)
    X, y = to_xy(pd.concat([train_df, val_df]))
    model = make_model(replace(cfg, cb_iterations=k))
    start = time.time()
    model.fit(X, y)
    sec_per_iter = (time.time() - start) / k
    print(f"{sec_per_iter:.4f} сек/итерация")
    print(
        f"оценка полного обучения ({cfg.cb_iterations} итераций): {sec_per_iter * cfg.cb_iterations:.1f} сек"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="v1")
    parser.add_argument("--benchmark", type=int, default=None)
    args = parser.parse_args()
    cfg = Config(run_name=args.run).smoke_if_needed()
    if args.benchmark:
        benchmark(cfg, args.benchmark)
    else:
        train(cfg)
