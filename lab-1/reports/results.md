| Итерация | Суть | Модель | val F1 macro | test F1 macro | Run |
| --- | --- | --- | ---: | ---: | --- |
| v1 | baseline, параметры Optuna из ml-2 ЛР1 | CatBoost | 0.2925 | 0.3293 | runs/v1 |
| v2 | «из коробки», pytorch_tabular | FT-Transformer | 0.2742 | 0.2667 | runs/v2 |
| v3 | «из коробки», pytorch_tabular | GANDALF | 0.2782 | 0.2850 | runs/v3 |
| v4 | lr 5e-3, wd 1e-5 из Optuna (`tune-gandalf-lr`) | GANDALF | 0.2907 | 0.3041 | runs/v4 |
| v5 | lr 4e-3, wd 5e-6 из Optuna (`tune-ft-lr`) | FT-Transformer | 0.2933 | 0.2962 | runs/v5 |
| v6 | веса классов balanced в CE (lr как в v4) | GANDALF | 0.2307 | 0.2272 | runs/v6 |
| v7 | веса классов balanced в CE (lr как в v5), обучение нестабильно | FT-Transformer | 0.2010 | 0.2048 | runs/v7 |
| v8 | dropout 0.2 (lr как в v4) | GANDALF | 0.2875 | 0.3074 | runs/v8 |
| v9 | embed_dim 16, 3 блока, ff_dropout 0.3 (lr как в v5) | FT-Transformer | 0.2433 | 0.3204 | runs/v9 |
| v10 | финальный перезапуск v1 + importance, ручные объекты | CatBoost | 0.2925 | 0.3293 | runs/v10 |
| v11 | финальный перезапуск v4 + importance, ручные объекты | GANDALF | 0.2907 | 0.3041 | runs/v11 |
| v12 | финальный перезапуск v5 + importance, ручные объекты (не повторил v5: MPS) | FT-Transformer | 0.2892 | 0.3032 | runs/v12 |
| **v13** | **TabLDM «из коробки» (n_estimators 16, enhance), без обучения весов** | **TabLDM** | **0.3933** | **0.3246** | **runs/v13** |
| v14 | TabM «из коробки» (k 32, 2×512, PLE-эмбеддинги), lr 2e-3, wd 3e-4 | TabM | 0.2886 | 0.3009 | runs/v14 |
