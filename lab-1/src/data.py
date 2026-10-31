"""Wine Quality (red): загрузка, производные признаки, разбиение train/val/test."""

import hashlib
import shutil
from pathlib import Path

import kagglehub
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

DATASET = "uciml/red-wine-quality-cortez-et-al-2009/versions/2"
DATA_DIR = Path("data")  # относительный путь, как RUNS_DIR
TARGET = "quality"
CLASSES = [3, 4, 5, 6, 7, 8]
NEW_FEATURES = [
    "total_acidity",
    "vol_fixed_ratio",
    "free_so2_ratio",
    "alc_density_prod",
    "sugar_alc_ratio",
]


def load_raw() -> pd.DataFrame:
    """Исходная таблица winequality-red.csv (1599 строк, 11 признаков + quality)."""
    path = DATA_DIR / "winequality-red.csv"
    if not path.exists():
        DATA_DIR.mkdir(exist_ok=True)
        src = Path(kagglehub.dataset_download(DATASET)) / "winequality-red.csv"
        shutil.copy(src, path)
    return pd.read_csv(path)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Копия таблицы с 5 производными признаками (формулы из ml-2 ЛР1)."""
    df = df.copy()
    df["total_acidity"] = df["fixed acidity"] + df["volatile acidity"] + df["citric acid"]
    df["vol_fixed_ratio"] = df["volatile acidity"] / (df["fixed acidity"] + 1e-5)
    df["free_so2_ratio"] = df["free sulfur dioxide"] / (df["total sulfur dioxide"] + 1e-5)
    df["alc_density_prod"] = df["alcohol"] * df["density"]
    df["sugar_alc_ratio"] = df["residual sugar"] / (df["alcohol"] + 1e-5)
    return df


def load_splits(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """train/val/test (1023/256/320): 16 признаков + quality, исходные индексы строк."""
    df = load_raw()
    X = add_features(df).drop(columns=TARGET)
    y = df[TARGET]
    # test всегда с random_state=42: тот же test, что в ml-2 ЛР1
    X_rest, X_test, y_rest, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_rest, y_rest, test_size=0.2, random_state=seed, stratify=y_rest
    )
    # масштабирование не здесь: CatBoost к нему инвариантен, нейросети обучают своё на train
    train = X_train.assign(quality=y_train)
    val = X_val.assign(quality=y_val)
    test = X_test.assign(quality=y_test)
    return train, val, test


def fingerprint(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Отпечаток данных: датасет, sha256 CSV и sha256 отсортированных индексов строк каждого split."""
    split_hash = {
        name: hashlib.sha256(str(sorted(df.index)).encode()).hexdigest()
        for name, df in [("train", train), ("val", val), ("test", test)]
    }
    csv_hash = hashlib.sha256((DATA_DIR / "winequality-red.csv").read_bytes()).hexdigest()
    return {"source": DATASET, "csv_sha256": csv_hash, "split_sha256": split_hash}


def to_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Признаки и метки quality - 3 (0..5)."""
    return df.drop(columns=TARGET), df[TARGET].to_numpy() - CLASSES[0]
