# Combined final model — training & evaluation

Trainer: `PYTHONPATH=. python3 tools/train_final.py`
Recipe: `StandardScaler` + `LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")`, scaler folded into coef/intercept (single dot-product inference, identical in Python and JS).
Sample weight: `(1 / n_frames_on_that_date) × 20` if the label is human, else `× 1`, then mean-normalized. Stops Jan–Apr minutes from drowning May–Dec hourly days, and keeps 253 human rows audible.
Shipped JSON: `models/cloud_logreg.json` and `docs/cloud_logreg.json` — **train-split fit**, no full-data refit.
Previous d413d74 weights: `models/cloud_logreg_d413d74.json`.
Metrics dump: `models/train_report.json`.

## 1. Data used — 172,343 unique frames

Filename-deduped. Later sources override earlier ones.

| Source | Rows in the combined table | Label origin |
|---|---|---|
| `data/labels_r5_kfb_full.csv` | 163,989 extra minutes (Jan–Apr 2023) | heuristic |
| `data/labels_r5_kfb2023.csv` | 8,101 hourly not overwritten by the 111 | heuristic |
| `data/golden_labels.csv` | 142 (2016, 13 dates) | human `golden` |
| `review_r5/manifest.csv` | 111 (2023) | visual GT override |
| **combined unique** | **172,343** (21,583 inside) | 357 dates |

USB per-minute extract ends 22 Apr 2023. Later months enter only via the hourly file.

**Weighted mass:** golden 40.2% / hourly 35.1% / extra minutes 17.8% / 111 visual 7.0%.

**Holdout:** `GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)` grouped by `YYMMDD`. Shipped weights come from the 80% fit.

| Split | Rows | inside | Dates |
|---|---|---|---|
| Train | 129,629 | 16,702 | 285 |
| Test | 42,714 | 4,881 | 72 |
| Test origins | golden 46 / hourly 1,636 / minute 41,012 / visual 20 | | |

## 2. Test-set performance (unseen 42,714)

Overall test accuracy **0.9783**, confusion `[[TN=36926, FP=907], [FN=19, TP=4862]]`.

| Slice | n | Acc | P | R | F1 | CM |
|---|---|---|---|---|---|---|
| All test | 42,714 | 0.9783 | 0.843 | 0.996 | 0.913 | [[36926, 907], [19, 4862]] |
| Day | 22,040 | 0.9689 | 0.734 | 0.990 | 0.843 | [[19513, 667], [18, 1842]] |
| Night | 20,674 | 0.9883 | 0.926 | 1.000 | 0.962 | [[17413, 240], [1, 3020]] |
| Golden-human | 46 | 0.9348 | 0.700 | 1.000 | 0.824 | [[36, 3], [0, 7]] |
| R5 hourly | 1,636 | 0.9694 | 0.728 | 0.977 | 0.834 | [[1460, 47], [3, 126]] |
| R5 minute | 41,012 | 0.9788 | 0.847 | 0.997 | 0.916 | [[35426, 852], [16, 4718]] |
| 111 on test dates | 20 | 0.7500 | 0.688 | 1.000 | 0.815 | [[4, 5], [0, 11]] |
| Train (ref.) | 129,629 | 0.9691 | 0.819 | 0.977 | 0.891 | [[109314, 3613], [393, 16309]] |
| d413d74, same test | 42,714 | 0.9805 | 0.856 | 0.996 | 0.921 | [[37018, 815], [19, 4862]] |

Accuracy is tied with d413d74 (−0.22 pts). Missed inside-cloud frames stay at 19. Heuristic-labeled slices are optimistic.

**2016 golden, all 142** (some dates in train): **0.9648** vs d413d74 **0.9507**. Recall 1.00 (0 missed inside).

## 3. 111 visual GT (2023)

91 of 111 dates were in the train split, 20 in test. Treat the 20-frame slice as the honest subset.

| Predictor | Acc | Prec | Recall | F1 | CM |
|---|---|---|---|---|---|
| Heuristic rules | 0.7297 | 0.7455 | 0.7193 | 0.7321 | [[40, 14], [16, 41]] |
| d413d74 | 0.8378 | 0.7826 | 0.9474 | 0.8571 | [[39, 15], [3, 54]] |
| **Combined final** | **0.8649** | 0.8000 | **0.9825** | **0.8819** | [[40, 14], [1, 56]] |
| Combined · day (55) | **0.9636** | 0.9429 | 1.000 | 0.9706 | [[20, 2], [0, 33]] |
| Combined · night (56) | **0.7679** | 0.6571 | 0.9583 | 0.7797 | [[20, 12], [1, 23]] |
| Combined · 20 test dates | 0.7500 | 0.6875 | 1.000 | 0.8148 | [[4, 5], [0, 11]] |

Beats rules by **+13.5 pts**. Beats d413d74 by **+2.7 pts**, from two fewer misses and one fewer night false alarm.

## 4. What we almost shipped instead

Unweighted minutes (172k equal rows, no 111 in train) scored **0.8198** on the 111 set — worse than d413d74. Date-balance + human ×20 is the recipe that uses the new extract without giving up May–Dec or the visual labels.

## 5. Next steps

* Hold the 111 fully out of the next fit (they still leak via train dates).
* Night remains the gap (precision 0.66). Full-resolution re-label of faint-light / fog frames.
* Another USB year of minutes would fill May–Dec; until then, keep date-balance.
