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
| v13 | TabLDM «из коробки» (n_estimators 16, enhance), без обучения весов | TabLDM | 0.3933 | 0.3246 | runs/v13 |
| v14 | TabM «из коробки» (k 32, 2×512, PLE-эмбеддинги), lr 2e-3, wd 3e-4 | TabM | 0.2886 | 0.3009 | runs/v14 |
| v15 | H1: lr 9e-3, wd 3e-5 из Optuna (`tune-tabm-lr`) | TabM | 0.3542 | 0.3188 | runs/v15 |
| v16 | H2: k 1 (lr 9e-3, wd 3e-5 как в v15) | TabM | 0.2881 | 0.2895 | runs/v16 |
| v17 | H2: k 8 (lr 9e-3, wd 3e-5 как в v15) | TabM | 0.2934 | 0.2624 | runs/v17 |
| v18 | H2: k 64 (lr 9e-3, wd 3e-5 как в v15) | TabM | 0.2830 | 0.2924 | runs/v18 |
| v19 | H2: k 1, lr 1e-2, wd 1e-5 из Optuna (`tune-tabm-k1`) | TabM | 0.3260 | 0.2428 | runs/v19 |
| v20 | H2: k 64, lr 7e-3, wd 4e-4 из Optuna (`tune-tabm-k64`) | TabM | 0.3811 | 0.3248 | runs/v20 |
| v21–v46 | H3: 128 × 1, 3 seeds, среднее (v21 / v29 / v38) | TabM | 0.3090 | 0.3227 | runs/v21, v29, v38 |
| v21–v46 | H3: 128 × 2, 3 seeds, среднее (v22 / v30 / v39) | TabM | 0.3259 | 0.3457 | runs/v22, v30, v39 |
| v21–v46 | H3: 128 × 3, 3 seeds, среднее (v23 / v31 / v40) | TabM | 0.3259 | 0.3186 | runs/v23, v31, v40 |
| v21–v46 | H3: 256 × 1, 3 seeds, среднее (v24 / v32 / v41) | TabM | 0.3033 | 0.2900 | runs/v24, v32, v41 |
| v21–v46 | H3: 256 × 2, 3 seeds, среднее (v25 / v33 / v42) | TabM | 0.3290 | 0.3521 | runs/v25, v33, v42 |
| v21–v46 | H3: 256 × 3, 3 seeds, среднее (v26 / v34 / v43) | TabM | 0.3632 | 0.3348 | runs/v26, v34, v43 |
| v21–v46 | H3: 512 × 1, 3 seeds, среднее (v27 / v35 / v44) | TabM | 0.3001 | 0.3127 | runs/v27, v35, v44 |
| v21–v46 | H3: 512 × 2, 3 seeds, среднее (v15 / v36 / v45) | TabM | 0.3080 | 0.3049 | runs/v15, v36, v45 |
| v21–v46 | H3: 512 × 3, 3 seeds, среднее (v28 / v37 / v46) | TabM | 0.2765 | 0.2670 | runs/v28, v37, v46 |
| v47–v49 | H4: 256 × 3, dropout 0.3, 3 seeds, среднее (v47 / v48 / v49) | TabM | 0.3346 | 0.3292 | runs/v47, v48, v49 |
| v50 | H5: n_estimators 1 | TabLDM | 0.3906 | 0.3246 | runs/v50 |
| v51 | H5: n_estimators 4 | TabLDM | 0.3906 | 0.3259 | runs/v51 |
| v52 | H5: n_estimators 8 | TabLDM | 0.4039 | 0.3246 | runs/v52 |
| v53 | H5: n_estimators 16 (повтор v13) | TabLDM | 0.3933 | 0.3246 | runs/v53 |
| v54 | H5: n_estimators 32 | TabLDM | 0.4025 | 0.3235 | runs/v54 |
| **v55** | **H6: enhance выкл, n_estimators 8** | **TabLDM** | **0.4096** | **0.3246** | **runs/v55** |
| v56 | H6: enhance выкл, n_estimators 16 | TabLDM | 0.4065 | 0.3260 | runs/v56 |
| v57 | H6: enhance выкл, n_estimators 32 | TabLDM | 0.4049 | 0.3263 | runs/v57 |
