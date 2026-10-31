---
paths:
  - "**/src/**/*.py"
---

# Код обучения в src/

- Устройство — только через `get_device()` из `src/utils.py`. Никаких `.cuda()`, `device="cuda"`. Для AMP: `torch.autocast(device_type=device.type, ...)`, на MPS — `float16` с осторожностью, bf16 на CUDA (4090 поддерживает).
- `num_workers`: на macOS `DataLoader` с `num_workers>0` требует, чтобы датасет был определён в модуле (не в ноутбуке) — поэтому датасеты в `src/data.py`. `pin_memory=True` только для CUDA.
- Тесты не пишем; качество кода держат `ruff` и `ty` (конфиг в `pyproject.toml` лабы).
- Все гиперпараметры — в `Config` (dataclass) в `src/config.py`; у него есть `smoke_if_needed()`, который при `SMOKE=1` урезает эпохи/батчи/размер данных и ставит `tracker="none"`.
- Логирование метрик — только через `src/tracking.py`. Прямых `wandb.log` / `mlflow.log_metric` в остальном коде нет. В трекер уходит весь `asdict(cfg)`.
- Seed: `seed_everything(cfg.seed)` в начале запуска, `generator` с сидом в `random_split` / `DataLoader`.
- В конце обучения — `save_run(cfg, history, metrics, predictions, device=..., tracker_url=...)` из `src/results.py`: слепок `runs/<run_name>/` коммитится и по нему ноутбук строит графики. Конвенции колонок — в docstring `results.py`. Если для анализа в ноутбуке нужны веса (Grad-CAM, примеры ошибок) — посчитать это в конце обучения и сохранить в `runs/<run_name>/` маленьким файлом.
- CLI `src/train.py`: `--run vN` (имя рана), `--benchmark K` (K шагов на полной конфигурации, печать `sec/step`, `steps/epoch`, оценка полного времени) — нужен для `/train`.
- Чекпоинты лучшей модели (по val-метрике) — в `artifacts/`, имя содержит модель и итерацию (`artifacts/v3_resnet18_best.pt`).
- Модуль не должен ничего запускать при импорте. CLI-точка входа — только внутри `if __name__ == "__main__":` (при упаковке в ipynb этот блок вырезается).
- Внутри `src` импортируем соседние модули как `from src.utils import ...` (не относительные импорты) — так проще упаковщику и ноутбуку.
- Пишем код, который читается студенту и преподавателю: явный train/eval loop с понятными именами лучше абстракций ради абстракций. Lightning — только если лаба создана с ним.
