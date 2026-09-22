# Model d413d74 — Training & Evaluation Report

Commit: `d413d74` ("retrain logreg on R5 hourly + golden, 80/20 grouped-by-date split").
Pushed to `origin/main`; `models/cloud_logreg.json` and `docs/cloud_logreg.json` (same weights, Pages + server share them).
Recipe: `StandardScaler` + `LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")`, scaler folded into coef/intercept (single dot-product inference, identical in Python and JS).

## 1. Data used — 8,354 rows total

| Source | Rows | not_inside | inside_cloud | Dates | Label origin |
|---|---|---|---|---|---|
| `data/golden_labels.csv` (human) | 142 | 108 | 34 | 13 (2016) | Hand-verified `golden` column; `heuristic_v5` disagrees on ~30 rows, proving independence from rules |
| `data/labels_r5_kfb2023.csv` (R5 USB KFB hourly) | 8,212 | 7,544 | 668 | 344 (2023) | Auto-labels, `source=heuristic_r5_hourly` (`src/features.py` + `src/heuristic.py`), no human review |

**Fit set (6,652 rows, 285 dates)** — the only rows the saved weights were fit on:
golden 96 (69 not_inside / 27 inside) + R5 6,556 (6,026 not_inside / 530 inside).

**Held-out set (1,702 rows, 72 dates)** — used for model selection (`golden_w`) and reporting, never fit:
golden 46 (39 not_inside / 7 inside) + R5 1,656 (1,518 not_inside / 138 inside).

Split: `GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)` grouped by date (`YYMMDD`); no date appears on both sides. The pipe was saved directly from the split fit (no full-data refit), so test metrics stay honest.

## 2. Test-set performance (unseen 1,702)

Overall test accuracy **0.9724**, confusion matrix `[[TN=1510, FP=47], [FN=0, TP=145]]` (rows = truth, cols = prediction; zero missed inside-cloud frames).

| Slice | n | Acc | Confusion matrix |
|---|---|---|---|
| All test | 1,702 | 0.9724 | [[1510, 47], [0, 145]] |
| Golden-human only | 46 | **0.9783** | [[38, 1], [0, 7]] |
| R5-heuristic only | 1,656 | 0.9722 | [[1472, 46], [0, 138]] |
| Train (reference) | 6,652 | 0.9714 | [[5915, 180], [10, 547]] |

Previous model on the same split: 0.9506 overall / 0.9565 golden-slice → **+2.2 pts** from adding R5 data.

Caveat: the R5 slice measures agreement with the heuristic rules that also generated the train labels, so it is optimistic. The golden-human slice is the honest number.

## 3. Independent check — 111 new ground-truth labels (2023, labeled by inspection)

`review_r5/manifest.csv` `golden` column was empty (0/111); all 111 cells of `review_r5/grid_01..13.jpg` were visually labeled against the project rule (day: washed-out textureless far field = inside, visible valley = not_inside; night: lightless flat = inside, any valley lights = not_inside). Result: 57 inside / 54 not_inside (heuristic had said 55 / 56).

| Predictor | Acc | Precision | Recall | F1 | Confusion matrix |
|---|---|---|---|---|---|
| Heuristic rules | 0.7297 | 0.7455 | 0.7193 | 0.7321 | [[40, 14], [16, 41]] |
| Model d413d74 | **0.8378** | 0.7826 | **0.9474** | **0.8571** | [[39, 15], [3, 54]] |

Model beats rules by **+10.8 pts**, driven by recall (3 missed inside-frames vs 16).

| Slice | Heuristic acc | Model acc | Model confusion |
|---|---|---|---|
| Day (55) | 0.7818 | **0.9455** | [[20, 2], [1, 32]] |
| Night (56) | 0.6786 | **0.7321** | [[19, 13], [2, 22]] |

## 4. Error analysis & next steps

* Model–heuristic agreement on the 111: 95/111. Of the 18 model misses, 15 are night false positives on faint-light frames (model says inside_cloud, truth not_inside); remaining: #83, #107 (missed inside) and day #87.
* Night discrimination is the weak spot for both predictors (model night precision 0.6286). The train set holds only 34 golden inside-frames, mostly day.
* Recommended next gain: hand-verify night frames (re-label the 111 at full resolution, especially borderline fog cases #10, #17, #22, #25, #37, #40, #50, #75, #87, #88 and lens-obstruction frame #107), add them as a second golden set, and retrain with golden up-weighting.
* The full per-minute R5 extraction (`tools/extract_r5_kfb_full.py`, ~46k/570k rows at time of writing) is still running; an interim model trained on that partial Jan-only data scored 0.9085 on golden holdout vs 0.9507 for d413d74, so it was correctly **not** pushed.
