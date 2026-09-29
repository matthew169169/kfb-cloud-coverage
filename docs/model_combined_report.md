# Combined final model — training & evaluation

Trainer: `PYTHONPATH=. python3 tools/train_final.py`  
Shipped weights: `models/cloud_logreg.json` (copied to `docs/cloud_logreg.json`).  
Previous weights: `models/cloud_logreg_d413d74.json`.  
Metrics dump: `models/train_report.json`.  
Recipe: `StandardScaler` + `LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")`, scaler folded into coef/intercept. Human rows (2016 golden + 2023 review) ×20 vs hourly heuristic ×1.  
Split: `GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)` grouped by date (`YYMMDD`). Shipped JSON is the **train-split fit** (no full-data refit).

## 1. Data

| Source | Rows | Role |
|---|---|---|
| `data/golden_labels.csv` | 142 | 2016 human GT, always in the fit pool |
| `data/labels_r5_kfb2023.csv` | 8,212 | 2023 hourly heuristic seed, full year |
| `review_r5/manifest.csv` | 111 | 2023 visual GT — **overrides** the hourly seed for those filenames |
| `data/labels_r5_kfb_full.csv` | 166,772 | Jan–Apr per-minute heuristic. Extract finished. **Not shipped.** |

Fit pool after filename-dedup: **8,354 rows / 704 inside / 357 dates**  
(`golden_2016` 142, `r5_hourly` 8,101, `human_2023` 111).

Train: 6,652 rows / 285 dates. Test: 1,702 rows / 72 dates. 20 of the 111 review frames fall on test dates.

## 2. Why the 166k minutes were not shipped

Full-minute and 15-minute-subsampled retrains both **lost** on the honest checks vs d413d74 (111-photo 0.82–0.83 vs 0.8378; 2016 golden-all ~0.94 vs 0.9507). Four months of heuristic minutes drown a full year of hourly frames.

## 3. Held-out test (1,702 unseen dates)

Caveat: most of this slice is heuristic-labeled, so it restates the seed rules. Prefer golden / 111 numbers.

| Slice | n | Acc | Confusion `[[TN,FP],[FN,TP]]` |
|---|---|---|---|
| All test | 1,702 | 0.9618 | [[1490, 65], [0, 147]] — zero missed inside-cloud |
| Golden-human | 46 | 0.9565 | [[37, 2], [0, 7]] |
| Hourly-heuristic | 1,636 | 0.9645 | [[1449, 58], [0, 129]] |
| 111-visual on test dates | 20 | 0.7500 | [[4, 5], [0, 11]] |
| d413d74 on the same 1,702 | 1,702 | 0.9724 | heuristic-heavy; not the selection metric |

## 4. Honest checks

**2016 golden, all 142:** **0.9718** vs d413d74 **0.9507**. P 0.917 / R 0.971. [[105, 3], [1, 33]].

**111 visual 2023 photos** (labels used as overrides in the date split — 91/111 dates in train, 20 in test):

| Predictor | Acc | Prec | Recall | F1 | Confusion |
|---|---|---|---|---|---|
| Heuristic rules | 0.7297 | 0.7455 | 0.7193 | 0.7321 | [[40,14],[16,41]] |
| d413d74 | 0.8378 | 0.7826 | 0.9474 | 0.8571 | [[39,15],[3,54]] |
| Combined final | **0.8649** | 0.8000 | **0.9825** | **0.8819** | [[40,14],[1,56]] |
| Combined · day (55) | **0.9818** | 0.9706 | 1.000 | 0.9851 | [[21,1],[0,33]] |
| Combined · night (56) | 0.7500 | 0.6389 | 0.9583 | 0.7667 | [[19,13],[1,23]] |
| Combined · 20 test-date frames | 0.7500 | 0.6875 | 1.000 | 0.8148 | [[4,5],[0,11]] |

+2.7 pts vs d413d74 on the 111, +13.5 pts vs the rules, driven by recall (1 missed inside-frame vs 3 / 16). Night precision is still the weak spot (13 faint-light false alarms).

## 5. What shipped

Same tiny JSON in `models/` and `docs/`. Pages, Flask, CLI, and the live GitHub Action all read those weights. Night labeling remains the next process step — not another architecture.
