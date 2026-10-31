"""Обучение CatBoost / FT-Transformer / GANDALF: uv run python -m src.train --run vN --model M [--set KEY=VALUE ...]."""

import argparse
import time
from dataclasses import replace

import numpy as np
import pandas as pd
import pytorch_lightning as pl
import torch
from catboost import CatBoostClassifier
from pytorch_tabular import TabularModel
from pytorch_tabular.config import DataConfig, OptimizerConfig, TrainerConfig
from pytorch_tabular.models import FTTransformerConfig, GANDALFConfig
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

from src.config import Config
from src.data import CLASSES, DATASET, TARGET, fingerprint, load_splits, to_xy
from src.plots import plot_confusion
from src.results import check_new_run, save_run
from src.tracking import init_tracker
from src.utils import get_device, seed_everything

ACCELERATORS = {"cuda": "gpu", "mps": "mps", "cpu": "cpu"}


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


def train_catboost(cfg: Config) -> dict:
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
    start = time.time()
    model.predict_proba(X_test)
    inference_time = time.time() - start
    metrics.update(
        best_iteration=model.get_best_iteration(),
        inference_time_sec=inference_time,
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

    tracker.log_inputs({"train": train_df, "val": val_df, "test": test_df}, source=DATASET)
    run_dir = save_run(
        cfg,
        history,
        metrics,
        predictions,
        device="cpu",
        tracker_run=tracker.run_ref,
        data=fingerprint(train_df, val_df, test_df),
    )
    tracker.log_artifacts(run_dir)
    tracker.log_figure(
        plot_confusion(
            predictions, labels=[str(c) for c in CLASSES], title=f"{cfg.run_name}: test"
        ),
        "confusion_test.html",
    )
    tracker.finish()
    print(
        f"val F1 macro: {metrics['val_f1_macro']:.4f}, test F1 macro: {metrics['test_f1_macro']:.4f}"
    )
    return metrics


# усложнение: callback пишет историю по эпохам — pytorch_tabular не отдаёт её, а кривые нужны для 1.3
class HistoryCallback(pl.Callback):
    """Записывает train_loss и val_loss в конце каждой эпохи."""

    def __init__(self, tracker=None):
        self.history: list[dict] = []
        self.tracker = tracker
        self.batch_losses: list[float] = []

    def on_train_epoch_start(self, trainer, pl_module):
        """Сбрасывает потери батчей."""
        self.batch_losses = []

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx):
        """Копит loss батча: train_loss в логах pytorch_tabular — только последний шаг."""
        self.batch_losses.append(outputs["loss"].item())

    def on_train_epoch_end(self, trainer, pl_module):
        """val-проход эпохи уже прошёл, sanity check пропускаем."""
        if trainer.sanity_checking:
            return
        m = trainer.callback_metrics
        row = {
            "epoch": trainer.current_epoch + 1,
            "train_loss": sum(self.batch_losses) / len(self.batch_losses),
            "val_loss": m["valid_loss"].item(),
        }
        self.history.append(row)
        if self.tracker is not None:
            self.tracker.log({k: v for k, v in row.items() if k != "epoch"}, step=row["epoch"])


def make_tabular_model(cfg: Config, benchmark: bool = False) -> TabularModel:
    """TabularModel для cfg.model; benchmark: без early stopping и чекпоинтов."""
    if cfg.model == "ft_transformer":
        model_config = FTTransformerConfig(
            input_embed_dim=cfg.ft_embed_dim,
            num_heads=cfg.ft_num_heads,
            num_attn_blocks=cfg.ft_num_attn_blocks,
            attn_dropout=cfg.ft_attn_dropout,
            ff_dropout=cfg.ft_ff_dropout,
            task="classification",
            learning_rate=cfg.lr,
        )
    else:
        model_config = GANDALFConfig(
            gflu_stages=cfg.gandalf_stages,
            gflu_dropout=cfg.gandalf_dropout,
            gflu_feature_init_sparsity=cfg.gandalf_init_sparsity,
            task="classification",
            learning_rate=cfg.lr,
        )
    features = load_splits(cfg.seed)[0].drop(columns=TARGET).columns.tolist()
    return TabularModel(
        data_config=DataConfig(
            target=[TARGET], continuous_cols=features, num_workers=cfg.num_workers
        ),
        model_config=model_config,
        optimizer_config=OptimizerConfig(
            optimizer="Adam", optimizer_params={"weight_decay": cfg.weight_decay}
        ),
        trainer_config=TrainerConfig(
            max_epochs=cfg.epochs,
            batch_size=cfg.batch_size,
            accelerator=ACCELERATORS[get_device().type],
            early_stopping=None if benchmark else "valid_loss",
            early_stopping_patience=cfg.patience,
            checkpoints=None if benchmark else "valid_loss",
            load_best=not benchmark,
            seed=cfg.seed,
            progress_bar="none",
            checkpoints_path="artifacts",
        ),
        verbose=False,
    )


def nn_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Признаки и метки 0..5 в колонке quality."""
    X, y = to_xy(df)
    return X.reset_index(drop=True).assign(**{TARGET: y})


def predict_proba(model: TabularModel, df: pd.DataFrame):
    """Вероятности классов 0..5 формы (n, 6)."""
    pred = model.predict(df)
    return pred[[f"{TARGET}_{i}_probability" for i in range(len(CLASSES))]].to_numpy()


def fit(cfg: Config, tracker=None) -> tuple[TabularModel, list[dict], dict]:
    """Обучение нейросети с early stopping по val: лучшая модель, история, val-метрики."""
    seed_everything(cfg.seed)
    train_df, val_df, _ = load_splits(cfg.seed)
    callback = HistoryCallback(tracker)
    model = make_tabular_model(cfg)
    train_frame = nn_frame(train_df)
    loss = None
    if cfg.class_weights == "balanced":
        # веса только по меткам train, без val/test
        w = compute_class_weight(
            "balanced", classes=np.arange(len(CLASSES)), y=train_frame[TARGET].to_numpy()
        )
        print(f"Веса классов (balanced): {np.round(w, 2).tolist()}")
        loss = torch.nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32))
    start = time.time()
    # seed=: иначе fit берёт свой seed=42 и cfg.seed игнорируется
    model.fit(
        train=train_frame,
        validation=nn_frame(val_df),
        callbacks=[callback],
        seed=cfg.seed,
        loss=loss,
    )
    train_time = time.time() - start

    history = callback.history
    val_frame = nn_frame(val_df)
    proba = predict_proba(model, val_frame)
    y_val = val_frame[TARGET].to_numpy()
    metrics = {
        f"val_{k}": v for k, v in compute_metrics(y_val, proba.argmax(axis=1), proba).items()
    }
    metrics.update(
        best_epoch=min(history, key=lambda r: r["val_loss"])["epoch"],
        epochs_trained=len(history),
        # model.model после fit не None, ty этого не знает
        n_params=sum(p.numel() for p in model.model.parameters() if p.requires_grad),  # ty: ignore[unresolved-attribute]
        train_time_sec=train_time,
    )
    return model, history, metrics


def train_nn(cfg: Config) -> dict:
    """Обучает нейросеть, оценивает лучшую модель на test, сохраняет ран."""
    tracker = init_tracker(cfg)
    model, history, metrics = fit(cfg, tracker)
    train_df, val_df, test_df = load_splits(cfg.seed)
    test_frame = nn_frame(test_df)
    y_test = test_frame[TARGET].to_numpy()
    start = time.time()
    proba = predict_proba(model, test_frame)
    inference_time = time.time() - start
    pred = proba.argmax(axis=1)
    metrics.update({f"test_{k}": v for k, v in compute_metrics(y_test, pred, proba).items()})
    metrics.update(
        inference_time_sec=inference_time,
        n_train=len(train_df),
        n_val=len(val_df),
        n_test=len(test_df),
    )
    tracker.summary(metrics)
    model.save_model(f"artifacts/{cfg.run_name}_best")

    predictions = pd.DataFrame({"y_true": y_test + CLASSES[0], "y_pred": pred + CLASSES[0]})
    for i, c in enumerate(CLASSES):
        predictions[f"prob_{c}"] = proba[:, i]

    tracker.log_inputs({"train": train_df, "val": val_df, "test": test_df}, source=DATASET)
    run_dir = save_run(
        cfg,
        history,
        metrics,
        predictions,
        device=get_device().type,
        tracker_run=tracker.run_ref,
        data=fingerprint(train_df, val_df, test_df),
    )
    tracker.log_artifacts(run_dir)
    tracker.log_figure(
        plot_confusion(
            predictions, labels=[str(c) for c in CLASSES], title=f"{cfg.run_name}: test"
        ),
        "confusion_test.html",
    )
    tracker.finish()
    print(
        f"val F1 macro: {metrics['val_f1_macro']:.4f}, test F1 macro: {metrics['test_f1_macro']:.4f}"
    )
    return metrics


def train(cfg: Config) -> dict:
    """Обучение выбранной cfg.model."""
    check_new_run(cfg.run_name)
    return train_catboost(cfg) if cfg.model == "catboost" else train_nn(cfg)


def benchmark_nn(cfg: Config, k: int) -> None:
    """Замер времени k эпох нейросети без early stopping, оценка полного обучения."""
    seed_everything(cfg.seed)
    train_df, val_df, _ = load_splits(cfg.seed)
    model = make_tabular_model(replace(cfg, epochs=k), benchmark=True)
    start = time.time()
    model.fit(train=nn_frame(train_df), validation=nn_frame(val_df), seed=cfg.seed)
    sec_per_epoch = (time.time() - start) / k
    print(f"{sec_per_epoch:.3f} сек/эпоха")
    print(
        f"оценка полного обучения (до {cfg.epochs} эпох, верхняя граница): "
        f"{sec_per_epoch * cfg.epochs:.1f} сек"
    )


def benchmark(cfg: Config, k: int) -> None:
    """Замер времени k итераций на полных данных, оценка полного обучения."""
    if cfg.model != "catboost":
        return benchmark_nn(cfg, k)
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
    parser.add_argument("--model", default=Config.model)
    parser.add_argument("--epochs", type=int, default=Config.epochs)
    parser.add_argument("--lr", type=float, default=Config.lr)
    parser.add_argument("--weight-decay", type=float, default=Config.weight_decay)
    parser.add_argument("--benchmark", type=int, default=None)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    cfg = Config(
        run_name=args.run,
        model=args.model,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    for item in args.set:
        key, value = item.split("=", 1)
        if not hasattr(cfg, key):
            parser.error(f"неизвестное поле Config: {key}")
        cfg = replace(cfg, **{key: type(getattr(cfg, key))(value)})
    cfg = cfg.smoke_if_needed()
    if args.benchmark:
        benchmark(cfg, args.benchmark)
    else:
        train(cfg)
