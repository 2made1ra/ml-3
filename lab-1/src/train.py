"""Обучение CatBoost / FT-Transformer / GANDALF / TabLDM / TabM: uv run python -m src.train --run vN --model M [--set KEY=VALUE ...]."""

import argparse
import copy
import time
from dataclasses import replace

import numpy as np
import pandas as pd
import pytorch_lightning as pl
import torch
from catboost import CatBoostClassifier
from huggingface_hub import hf_hub_download
from pytorch_tabular import TabularModel
from pytorch_tabular.config import DataConfig, OptimizerConfig, TrainerConfig
from pytorch_tabular.models import FTTransformerConfig, GANDALFConfig
from rtdl_num_embeddings import PiecewiseLinearEmbeddings, compute_bins
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import QuantileTransformer
from sklearn.utils.class_weight import compute_class_weight
from tabldm import TabLDMClassifier
from tabm import TabM

from src.config import Config
from src.data import (
    CLASSES,
    DATASET,
    TARGET,
    fingerprint,
    load_splits,
    manual_objects,
    to_xy,
)
from src.plots import plot_confusion
from src.results import check_new_run, save_run
from src.tracking import init_tracker
from src.utils import get_device, seed_everything

ACCELERATORS = {"cuda": "gpu", "mps": "mps", "cpu": "cpu"}

# усложнение: ревизия чекпоинта закреплена — воспроизводимость, встроенная загрузка tabldm ревизию не фиксирует (task.md, «Решения»)
TABLDM_REPO = "occams/Xiaomi-TabLDM"
TABLDM_CKPT = "checkpoints/clf_default.ckpt"
TABLDM_REVISION = "712e5635be9fd8728084cd5ae105ddecb31dc03c"
PRIOR_ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)


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


def permutation_importance(
    proba_fn, X: pd.DataFrame, y: np.ndarray, n_repeats: int, seed: int
) -> pd.DataFrame:
    """Падение F1 macro при перемешивании признака: perm_mean и perm_std по n_repeats."""
    rng = np.random.default_rng(seed)
    base = f1_score(y, proba_fn(X).argmax(axis=1), average="macro", zero_division=0)
    rows = []
    for feature in X.columns:
        drops = []
        for _ in range(n_repeats):
            X_shuffled = X.copy()
            X_shuffled[feature] = rng.permutation(X[feature].to_numpy())
            score = f1_score(
                y, proba_fn(X_shuffled).argmax(axis=1), average="macro", zero_division=0
            )
            drops.append(base - score)
        rows.append({"feature": feature, "perm_mean": np.mean(drops), "perm_std": np.std(drops)})
    return pd.DataFrame(rows)


def save_analysis(
    run_dir, cfg: Config, proba_fn, X_test: pd.DataFrame, y_test: np.ndarray, builtin: np.ndarray
) -> None:
    """Пишет importance.csv (permutation + встроенный) и manual.csv (предсказания на ручных объектах)."""
    # на test только анализ финальных моделей, для выбора моделей он не используется
    importance = permutation_importance(proba_fn, X_test, y_test, cfg.perm_repeats, cfg.seed)
    importance["builtin"] = builtin
    importance.to_csv(run_dir / "importance.csv", index=False)

    objects = manual_objects()
    proba = proba_fn(objects[X_test.columns.tolist()])
    manual = pd.DataFrame(
        {"id": objects["id"], "type": objects["type"], "y_pred": proba.argmax(axis=1) + CLASSES[0]}
    )
    for i, c in enumerate(CLASSES):
        manual[f"prob_{c}"] = proba[:, i]
    manual.to_csv(run_dir / "manual.csv", index=False)


def finish_run(
    cfg: Config,
    tracker,
    proba_fn,
    history: list[dict],
    metrics: dict,
    device: str,
    builtin: np.ndarray,
) -> dict:
    """Метрики val и test, анализ, сохранение рана и трекер; proba_fn принимает DataFrame признаков."""
    train_df, val_df, test_df = load_splits(cfg.seed)
    X_val, y_val = to_xy(val_df)
    X_test, y_test = to_xy(test_df)

    proba_val = proba_fn(X_val)
    metrics.update(
        {
            f"val_{k}": v
            for k, v in compute_metrics(y_val, proba_val.argmax(axis=1), proba_val).items()
        }
    )
    start = time.time()
    proba = proba_fn(X_test)
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

    predictions = pd.DataFrame({"y_true": y_test + CLASSES[0], "y_pred": pred + CLASSES[0]})
    for i, c in enumerate(CLASSES):
        predictions[f"prob_{c}"] = proba[:, i]

    tracker.log_inputs({"train": train_df, "val": val_df, "test": test_df}, source=DATASET)
    run_dir = save_run(
        cfg,
        history,
        metrics,
        predictions,
        device=device,
        tracker_run=tracker.run_ref,
        data=fingerprint(train_df, val_df, test_df),
    )
    save_analysis(run_dir, cfg, proba_fn, X_test, y_test, builtin)
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
    train_df, val_df, _ = load_splits(cfg.seed)
    X_train, y_train = to_xy(train_df)
    X_val, y_val = to_xy(val_df)

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

    metrics = {"best_iteration": model.get_best_iteration(), "train_time_sec": train_time}
    model.save_model(f"artifacts/{cfg.run_name}_best.cbm")
    return finish_run(
        cfg, tracker, model.predict_proba, history, metrics, "cpu", model.get_feature_importance()
    )


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
    model.save_model(f"artifacts/{cfg.run_name}_best")

    def proba_fn(X: pd.DataFrame) -> np.ndarray:
        return predict_proba(model, X.reset_index(drop=True))

    features = load_splits(cfg.seed)[2].drop(columns=TARGET).columns
    builtin = model.feature_importance().set_index("Features")["importance"]
    return finish_run(
        cfg,
        tracker,
        proba_fn,
        history,
        metrics,
        get_device().type,
        builtin.loc[features].to_numpy(),
    )


def make_tabldm(cfg: Config) -> TabLDMClassifier:
    """TabLDM на устройстве get_device() с закреплённым чекпоинтом."""
    return TabLDMClassifier(
        n_estimators=cfg.tabldm_n_estimators,
        enhance_candidates=cfg.tabldm_enhance,
        norm_methods=cfg.tabldm_norm_methods.split(","),
        device=str(get_device()),
        random_state=cfg.seed,
        model_path=hf_hub_download(TABLDM_REPO, TABLDM_CKPT, revision=TABLDM_REVISION),
    )


def prior_correct(proba: np.ndarray, prior: np.ndarray, alpha: float) -> np.ndarray:
    """Делит вероятности на приоры в степени alpha и нормирует строки к сумме 1."""
    p = proba / prior**alpha
    return p / p.sum(axis=1, keepdims=True)


def train_tabldm(cfg: Config) -> dict:
    """TabLDM: предобученная модель без обучения весов, fit только строит контекст из train."""
    seed_everything(cfg.seed)
    tracker = init_tracker(cfg)
    train_df, val_df, _ = load_splits(cfg.seed)
    X_train, y_train = to_xy(train_df)

    clf = make_tabldm(cfg)
    start = time.time()
    # DataFrame принимается (проверено), аннотация библиотеки — np.ndarray
    clf.fit(X_train, y_train)  # ty: ignore[invalid-argument-type]  # нормализация внутри, scaler не нужен
    train_time = time.time() - start

    metrics = {
        "n_params": sum(p.numel() for p in clf.model_.parameters()),
        "train_time_sec": train_time,
    }
    proba_fn = clf.predict_proba
    if cfg.tabldm_prior_correction:
        prior = np.bincount(y_train, minlength=len(CLASSES)) / len(y_train)
        X_val, y_val = to_xy(val_df)
        proba_val = clf.predict_proba(X_val)  # ty: ignore[invalid-argument-type]  # DataFrame принимается, как в fit
        f1s = [
            f1_score(
                y_val,
                prior_correct(proba_val, prior, a).argmax(axis=1),
                average="macro",
                zero_division=0,
            )
            for a in PRIOR_ALPHAS
        ]
        for a, f1 in zip(PRIOR_ALPHAS, f1s, strict=True):
            metrics[f"val_f1_macro_alpha_{a}"] = f1
            print(f"alpha {a}: val F1 macro {f1:.4f}")
        best = PRIOR_ALPHAS[
            int(np.argmax(f1s))
        ]  # argmax берёт первый максимум — при равенстве меньший alpha
        metrics["tabldm_alpha"] = best
        print(f"Выбран alpha {best} по val F1 macro")
        proba_fn = lambda X: prior_correct(clf.predict_proba(X), prior, best)  # noqa: E731
    return finish_run(
        cfg,
        tracker,
        proba_fn,
        [],
        metrics,
        get_device().type,
        np.full(X_train.shape[1], np.nan),
    )


def fit_tabm(cfg: Config, tracker=None) -> tuple:
    """Обучение TabM с early stopping по val: функция predict_proba(DataFrame), история, val-метрики."""
    if cfg.class_weights != "none":
        raise ValueError("class_weights для TabM не реализованы")
    seed_everything(cfg.seed)
    device = get_device()
    train_df, val_df, _ = load_splits(cfg.seed)
    X_train, y_train = to_xy(train_df)
    X_val, y_val = to_xy(val_df)

    # усложнение: квантильное преобразование и кусочно-линейные эмбеддинги по бинам train — рекомендуемое кодирование чисел для TabM (task.md, этап 6); эмбеддинги выключаются tabm_num_embeddings=none (H8)
    qt = QuantileTransformer(
        output_distribution="normal", n_quantiles=min(1000, len(X_train)), random_state=cfg.seed
    )

    def to_tensor(X: pd.DataFrame) -> torch.Tensor:
        return torch.tensor(qt.transform(X), dtype=torch.float32, device=device)

    qt.fit(X_train)
    x_train, x_val = to_tensor(X_train), to_tensor(X_val)
    t_train = torch.tensor(y_train, device=device)
    t_val = torch.tensor(y_val, device=device)
    if cfg.tabm_num_embeddings == "ple":
        bins = compute_bins(x_train.cpu(), n_bins=cfg.tabm_n_bins)
        num_embeddings = PiecewiseLinearEmbeddings(
            bins, d_embedding=cfg.tabm_d_embedding, activation=False, version="B"
        )
    elif cfg.tabm_num_embeddings == "none":
        num_embeddings = None
    else:
        raise ValueError(f"tabm_num_embeddings: ple | none, получено {cfg.tabm_num_embeddings}")

    model = TabM.make(
        n_num_features=x_train.shape[1],
        d_out=len(CLASSES),
        num_embeddings=num_embeddings,
        k=cfg.tabm_k,
        n_blocks=cfg.tabm_n_blocks,
        d_block=cfg.tabm_d_block,
        dropout=cfg.tabm_dropout,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    generator = torch.Generator().manual_seed(cfg.seed)
    k = cfg.tabm_k

    history = []
    best_loss, best_state, bad_epochs = float("inf"), {}, 0
    start = time.time()
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        batch_losses = []
        for idx in torch.randperm(len(x_train), generator=generator).split(cfg.batch_size):
            idx = idx.to(device)
            logits = model(x_train[idx])  # (B, k, классы)
            # каждая из k голов обучается независимо со своей CrossEntropy
            loss = torch.nn.functional.cross_entropy(
                logits.reshape(-1, logits.shape[-1]), t_train[idx].repeat_interleave(k)
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())

        model.eval()
        with torch.inference_mode():
            probs = model(x_val).softmax(dim=-1).mean(dim=1)
        val_loss = torch.nn.functional.nll_loss(probs.clamp_min(1e-12).log(), t_val).item()
        row = {
            "epoch": epoch,
            "train_loss": sum(batch_losses) / len(batch_losses),
            "val_loss": val_loss,
        }
        history.append(row)
        if tracker is not None:
            tracker.log({"train_loss": row["train_loss"], "val_loss": val_loss}, step=epoch)

        if val_loss < best_loss:
            best_loss, bad_epochs = val_loss, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            bad_epochs += 1
            if bad_epochs >= cfg.patience:
                break
    train_time = time.time() - start
    model.load_state_dict(best_state)
    model.eval()

    def proba_fn(X: pd.DataFrame) -> np.ndarray:
        """Вероятности классов (n, 6): среднее по k головам."""
        x = to_tensor(X)
        with torch.inference_mode():
            parts = [model(b).softmax(dim=-1).mean(dim=1) for b in x.split(1024)]
        return torch.cat(parts).cpu().numpy()

    proba = proba_fn(X_val)
    metrics = {
        f"val_{name}": v for name, v in compute_metrics(y_val, proba.argmax(axis=1), proba).items()
    }
    metrics.update(
        best_epoch=min(history, key=lambda r: r["val_loss"])["epoch"],
        epochs_trained=len(history),
        n_params=sum(p.numel() for p in model.parameters() if p.requires_grad),
        train_time_sec=train_time,
    )
    return proba_fn, model, history, metrics


def train_tabm(cfg: Config) -> dict:
    """Обучает TabM, оценивает лучшую модель на test, сохраняет ран."""
    tracker = init_tracker(cfg)
    proba_fn, model, history, metrics = fit_tabm(cfg, tracker)
    torch.save(model.state_dict(), f"artifacts/{cfg.run_name}_best.pt")
    return finish_run(
        cfg, tracker, proba_fn, history, metrics, get_device().type, np.full(16, np.nan)
    )


def train(cfg: Config) -> dict:
    """Обучение выбранной cfg.model."""
    check_new_run(cfg.run_name)
    trainers = {
        "catboost": train_catboost,
        "tabldm": train_tabldm,
        "tabm": train_tabm,
        "ft_transformer": train_nn,
        "gandalf": train_nn,
    }
    return trainers[cfg.model](cfg)


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


def benchmark_tabm(cfg: Config, k: int) -> None:
    """Замер времени k эпох TabM без early stopping, оценка полного обучения."""
    # patience=k: за k эпох early stopping не успевает сработать
    *_, metrics = fit_tabm(replace(cfg, epochs=k, patience=k))
    sec_per_epoch = metrics["train_time_sec"] / k
    print(f"{sec_per_epoch:.3f} сек/эпоха")
    print(
        f"оценка полного обучения (до {cfg.epochs} эпох, верхняя граница): "
        f"{sec_per_epoch * cfg.epochs:.1f} сек"
    )


def benchmark_tabldm(cfg: Config) -> None:
    """Замер fit и predict на test для TabLDM, оценка полного рана."""
    train_df, _, test_df = load_splits(cfg.seed)
    X_train, y_train = to_xy(train_df)
    X_test, _ = to_xy(test_df)
    clf = make_tabldm(cfg)
    start = time.time()
    clf.fit(X_train, y_train)  # ty: ignore[invalid-argument-type]
    fit_time = time.time() - start
    start = time.time()
    clf.predict_proba(X_test)  # ty: ignore[invalid-argument-type]
    predict_time = time.time() - start
    print(f"fit: {fit_time:.1f} сек, predict на test: {predict_time:.1f} сек")
    # predict: val + test + permutation importance (16 признаков × perm_repeats); ручные объекты малы
    total = fit_time + predict_time * (2 + 16 * cfg.perm_repeats)
    print(f"оценка полного рана: {total:.1f} сек")


def benchmark(cfg: Config, k: int) -> None:
    """Замер времени k итераций на полных данных, оценка полного обучения."""
    if cfg.model == "tabm":
        return benchmark_tabm(cfg, k)
    if cfg.model == "tabldm":
        return benchmark_tabldm(cfg)
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


def apply_set(cfg: Config, items: list[str]) -> Config:
    """Возвращает cfg с переопределениями полей из строк KEY=VALUE."""
    for item in items:
        key, value = item.split("=", 1)
        field_type = type(getattr(cfg, key))
        # bool("False") is True, поэтому для bool разбираем строку явно
        parsed = value.lower() == "true" if field_type is bool else field_type(value)
        cfg = replace(cfg, **{key: parsed})
    return cfg


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
    cfg = apply_set(cfg, args.set).smoke_if_needed()
    if args.benchmark:
        benchmark(cfg, args.benchmark)
    else:
        train(cfg)
