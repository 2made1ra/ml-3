from dataclasses import dataclass, replace

from src.utils import is_smoke


@dataclass
class Config:
    """Все гиперпараметры эксперимента."""

    # эксперимент
    project: str = "dl-lab-N"
    run_name: str = "v1"
    tracker: str = "mlflow"  # mlflow | none (можно переопределить env TRACKER)
    seed: int = 42
    stage: int = 0  # этап из task.md
    hypothesis: str = ""  # H<n> из «Гипотез» этапа
    baseline_run: str = ""  # ран, с которым сравниваем

    # данные
    batch_size: int = 64
    num_workers: int = 4
    data_fraction: float = 1.0  # доля train для быстрых экспериментов

    # обучение
    epochs: int = 20
    lr: float = 1e-3
    weight_decay: float = 1e-4

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
            data_fraction=0.01,
        )
