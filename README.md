# Deep Learning — лабораторные, семестр 3

Каждая лаба — папка `lab-N/` со своим uv-окружением. Код пишет Claude Code (решения принимает Opus, код пишет субагент `lab-coder` на Sonnet), обучение запускаю я — на Mac M4 или на PC с RTX 4090.

## Один раз на машине

```bash
uv run --project lab-N wandb login   # после создания первой лабы, на Mac и на PC
nvidia-smi                           # только PC: CUDA должна быть ≥ 13.2
```

## Новая лаба

1. **Положить задание** (pdf / ipynb / md) в `lab-N/` и в Claude Code вызвать:
   ```
   /new-lab N
   ```
   Появятся каркас, окружение, заготовка ноутбука `lab-N/lab-N.ipynb` и чеклист `lab-N/task/task.md`. Проверить чеклист и ответить на «Неясности».

2. **Код** — по пунктам задания, сколько угодно раз:
   ```
   /code-lab загрузка данных и EDA
   /code-lab baseline CNN и обучение
   ```
   Каждый вызов заканчивается проверками ruff + ty + smoke-прогоном.

3. **Обучение:**
   ```
   /train
   ```
   Claude оценит время на Mac и посоветует, где учить.

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
     и `git pull` на Mac.

   Результат — `lab-N/runs/v1/` (метрики, история, предсказания) + ран в W&B.

4. **Разбор итерации:**
   ```
   /log-iteration
   ```
   Запись в `reports/iterations/v1.md` и сводку `reports/results.md`. Дальше — снова `/code-lab` → `/train`, пока результат не устроит.

5. **Сдача:**
   ```
   /write-conclusion      # черновики выводов в ноутбук — потом поправить руками
   /lab-review            # сверка с заданием, утечки, числа в выводах
   /pack-submission       # единый ipynb → lab-N/submission/lab-N.ipynb
   ```

## Полезно знать

- Ноутбук не обучает модели — он читает `runs/` и строит графики (Plotly), поэтому выполняется за секунды.
- `SMOKE=1` перед командой — быстрый прогон на паре батчей; такие раны попадают в `runs/*-smoke/` и не коммитятся.
- Трекер переключается переменной: `TRACKER=mlflow` или `TRACKER=none`.
- Зависимости — только `uv add <pkg>` внутри `lab-N/`; `uv.lock` коммитится.
- Подробные правила для Claude — в `CLAUDE.md` и `.claude/`.
