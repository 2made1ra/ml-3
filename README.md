# Deep Learning

Каждая лабораторная — папка `lab-N/` со своим uv-окружением.

## Один раз на машине

```bash
nvidia-smi                 # только PC: CUDA должна быть ≥ 13.2
uv tool install prek       # проверки перед коммитом: секреты, файлы > 5 МБ, ruff
prek install               # в корне репозитория, после каждого git clone
```

Токены — в штатных хранилищах на каждой машине, в репозиторий ничего не кладём:

- **Kaggle:** kaggle.com → Settings → API → создать токен, положить в `~/.kaggle/` и выполнить `chmod 600 ~/.kaggle/*`.
- **Hugging Face:** `uvx --from huggingface_hub hf auth login` (токен — huggingface.co → Settings → Access Tokens, хватает read).
- **kvatask** (доска задач): на каждой машине свой ключ. Положите его в `secrets.yaml` в корне репозитория строкой `kvatask_api_key: <ключ>`; файл не коммитится. На Mac — скопировать ключ и в корне репозитория выполнить `printf 'kvatask_api_key: %s\n' "$(pbpaste)" > secrets.yaml && chmod 600 secrets.yaml`. Подключение описано в `.mcp.json`.

Трекинг — MLflow, локально на каждой машине, ничего настраивать не нужно. База одна на все лабы: `~/.mlflow/mlflow.db`. Посмотреть раны (из папки любой лабы):

```bash
uv run mlflow ui --backend-store-uri sqlite:///$HOME/.mlflow/mlflow.db   # → http://127.0.0.1:5000
```

## Работа над лабой

Пошаговый гайд с примером лабы 1 — [docs/workflow.md](docs/workflow.md). Коротко:

```
/new-lab N → /code-lab all → (/tune) → /train → /log-iteration → … → /write-conclusion → /lab-review → /pack-submission → /prep-defense
```

## Полезно знать

- Ноутбук не обучает модели — он читает `runs/` и строит графики (Plotly), поэтому выполняется за секунды.
- `SMOKE=1` перед командой — быстрый прогон на паре батчей; такие раны попадают в `runs/*-smoke/` и не коммитятся.
- Трекер переключается переменной: `TRACKER=none` — без MLflow. Во время обучения на PC живые кривые — в `mlflow ui` на самом PC.
- Зависимости — только `uv add <pkg>` внутри `lab-N/`; `uv.lock` коммитится.
- Файлы токенов закрыты для Claude правилами в `.claude/settings.json`; секрет в коммите поймает gitleaks.
- Подробные правила для Claude — в `CLAUDE.md` и `.claude/`.
