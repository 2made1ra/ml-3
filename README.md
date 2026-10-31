# Deep Learning — лабораторные, семестр 3

Каждая лаба — папка `lab-N/` со своим uv-окружением.

## Один раз на машине

```bash
nvidia-smi   # только PC: CUDA должна быть ≥ 13.2
```

Токены — в штатных хранилищах на каждой машине, в репозиторий ничего не кладём:

- **Kaggle:** kaggle.com → Settings → API → создать токен, положить в `~/.kaggle/` и выполнить `chmod 600 ~/.kaggle/*`.
- **Hugging Face:** `uvx --from huggingface_hub hf auth login` (токен — huggingface.co → Settings → Access Tokens, хватает read).

Трекинг — MLflow, локально на каждой машине, ничего настраивать не нужно. База одна на все лабы: `~/.mlflow/mlflow.db`. Посмотреть раны (из папки любой лабы):

```bash
uv run mlflow ui --backend-store-uri sqlite:///$HOME/.mlflow/mlflow.db   # → http://127.0.0.1:5000
```

## Новая лаба

1. **Положить задание** (pdf / ipynb / md) в `lab-N/` и вызвать скилл:
   ```
   /new-lab N
   ```
   Появятся каркас, окружение, заготовка ноутбука `lab-N/lab-N.ipynb` и чеклист `lab-N/task/task.md`. Проверить чеклист и ответить на «Неясности».

2. **Код.** Три режима, можно смешивать:
   ```
   /code-lab all                                  # план по task.md, шаги по одному с подтверждением
   /code-lab baseline CNN и обучение              # один кусок
   /code-lab перепиши аугментации в data.py на ...  # переписать кусок: меняется только названное
   /code-lab review                               # проверить код, который я написал сам
   ```
   Код пишет субагент, Opus проверяет: ruff + ty + smoke + ревью диффа. Прогресс — галочки в `task/task.md`.

   **Свой код:** пометить `# user-owned` строкой над `def`/`class` (защищает функцию), первой строкой файла (весь файл) или ячейки. Агенты такой код не меняют без прямой просьбы; при упаковке маркер вырезается.

3. **Обучение:**
   ```
   /train
   ```
   Агент оценит время на Mac и посоветует, где учить.

   - **На Mac:**
     ```bash
     cd lab-N && uv run python -m src.train --run v1
     ```
   - **На PC:** закоммитить и запушить код на Mac, затем на PC:
     ```bash
     git pull && cd lab-N && uv sync
     uv run python -m src.train --run v1
     git add runs/v1 && git commit -m "run(labN): v1 — <суть>" && git push
     ```
     Затем на Mac:
     ```bash
     git pull && cd lab-N && uv run python -m src.sync_mlflow   # ран с PC появится в MLflow на Mac
     ```

   Результат — `lab-N/runs/v1/` (метрики, история, предсказания) + ран в MLflow.

4. **Разбор итерации:**
   ```
   /log-iteration
   ```
   Запись в `reports/iterations/v1.md` и сводку `reports/results.md`. Дальше — снова `/code-lab` → `/train`, пока результат не устроит.

5. **Сдача:**
   ```
   /write-conclusion      # черновики выводов в ноутбук — отсмотр результатов и предварительных выводов обязательна
   /lab-review            # сверка с заданием, утечки, числа в выводах
   /pack-submission       # единый ipynb → lab-N/submission/lab-N.ipynb
   ```

## Полезно знать

- Ноутбук не обучает модели — он читает `runs/` и строит графики (Plotly), поэтому выполняется за секунды.
- `SMOKE=1` перед командой — быстрый прогон на паре батчей; такие раны попадают в `runs/*-smoke/` и не коммитятся.
- Трекер переключается переменной: `TRACKER=none` — без MLflow. Во время обучения на PC живые кривые — в `mlflow ui` на самом PC.
- Зависимости — только `uv add <pkg>` внутри `lab-N/`; `uv.lock` коммитится.
- Подробные правила для Claude — в `CLAUDE.md` и `.claude/`.
