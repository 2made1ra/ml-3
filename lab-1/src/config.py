from dataclasses import dataclass, replace

from src.utils import is_smoke


@dataclass
class Config:
    """Все гиперпараметры эксперимента."""

    # эксперимент
    project: str = "dl-lab-1"
    run_name: str = "v1"
    tracker: str = "mlflow"  # mlflow | none (можно переопределить env TRACKER)
    seed: int = 42
    model: str = "catboost"  # catboost | ft_transformer | gandalf

    # данные
    batch_size: int = 64
    num_workers: int = 0  # 1023 строки, воркеры на macOS только замедляют
    data_fraction: float = 1.0  # доля train для быстрых экспериментов

    # обучение
    epochs: int = 200  # максимум, останавливает early stopping
    patience: int = 20  # early stopping по val loss
    lr: float = 1e-3
    weight_decay: float = 1e-4
    class_weights: str = "none"  # none | balanced

    # CatBoost (параметры Optuna из ml-2 ЛР1)
    cb_iterations: int = 476
    cb_learning_rate: float = 0.07179
    cb_depth: int = 10
    cb_l2_leaf_reg: float = 4.9186
    cb_border_count: int = 226
    cb_early_stopping: int = 50

    # FT-Transformer (значения по умолчанию pytorch_tabular 1.2.0)
    ft_embed_dim: int = 32
    ft_num_heads: int = 8
    ft_num_attn_blocks: int = 6
    ft_attn_dropout: float = 0.1
    ft_ff_dropout: float = 0.1

    # GANDALF (значения по умолчанию pytorch_tabular 1.2.0)
    gandalf_stages: int = 6
    gandalf_dropout: float = 0.0
    gandalf_init_sparsity: float = 0.3

    def smoke_if_needed(self) -> "Config":
        """При SMOKE=1 возвращает урезанный конфиг для быстрой проверки, иначе себя."""
        if not is_smoke():
            return self
        return replace(
            self,
            run_name=f"{self.run_name}-smoke",
            tracker="none",
            epochs=1,
            batch_size=min(self.batch_size, 16),
            num_workers=0,
            cb_iterations=20,
        )
