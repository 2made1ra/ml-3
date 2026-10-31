"""Типовые графики Plotly по данным из runs/ (см. src/results.py)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.metrics import confusion_matrix

# интерактивный график + статичный PNG: PNG видно на GitHub и в просмотрщиках без JS
pio.renderers.default = "plotly_mimetype+png"


def plot_curves(history: pd.DataFrame, metric: str, title: str | None = None) -> go.Figure:
    """Кривые train/val по эпохам для метрики (колонки train_<metric>, val_<metric>)."""
    fig = go.Figure()
    for split in ("train", "val"):
        col = f"{split}_{metric}"
        if col in history:
            fig.add_scatter(x=history["epoch"], y=history[col], mode="lines+markers", name=split)
    fig.update_layout(
        title=title or f"{metric}: train vs val", xaxis_title="epoch", yaxis_title=metric
    )
    return fig


def plot_confusion(
    predictions: pd.DataFrame,
    labels: list[str] | None = None,
    normalize: bool = True,
    title: str = "Confusion matrix (test)",
) -> go.Figure:
    """Матрица ошибок по predictions.csv (по умолчанию нормирована по строкам)."""
    cm = confusion_matrix(
        predictions["y_true"], predictions["y_pred"], normalize="true" if normalize else None
    )
    names = labels or [str(i) for i in range(cm.shape[0])]
    fig = px.imshow(
        cm,
        x=names,
        y=names,
        text_auto=".2f" if normalize else True,
        color_continuous_scale="Blues",
        labels={"x": "predicted", "y": "true", "color": "share" if normalize else "count"},
    )
    fig.update_layout(title=title)
    return fig


def plot_runs(table: pd.DataFrame, metric: str, title: str | None = None) -> go.Figure:
    """Сравнение ранов по метрике (таблица из compare_runs)."""
    fig = px.bar(table.reset_index(), x="run", y=metric, text_auto=".4f")
    fig.update_layout(
        title=title or f"{metric} по итерациям", xaxis_title="run", yaxis_title=metric
    )
    return fig
