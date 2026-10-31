import os
import random

import numpy as np
import torch


def is_smoke() -> bool:
    """SMOKE=1 — быстрый прогон для проверки, что пайплайн не падает."""
    return os.environ.get("SMOKE", "0") == "1"


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)  # noqa: NPY002 — глобальный сид для сторонних библиотек
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def count_parameters(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
