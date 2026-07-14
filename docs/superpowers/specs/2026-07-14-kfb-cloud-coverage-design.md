# KFB Cloud Coverage Determination — Design Spec

**Date:** 2026-07-14  
**Author:** Matthew / Cursor agent  
**Status:** Awaiting user review  
**Target:** mid-July 2026

## Problem

CAD drone rules require pilots to know approximate cloud-base height. Hong Kong has few direct cloud-base observations. HKO hill weather cameras (e.g. Kadoorie Farm) sit at known altitudes: if the camera is inside cloud/fog (whitish blur / lost distant detail), cloud base is at or below camera altitude; if not, minimum cloud base is above camera altitude.

## Goals (v1)

1. From a KFB webcam image, decide whether the camera is **inside cloud** (day or night).
2. Emit fixed messages:
   - Inside: `Camera is inside cloud ({day|night}). Cloud base at or below ~150 m.`
   - Not inside: `I am not inside cloud. The cloud base should be above 150 m.`
3. Heuristic auto-label → human spot-check → train a lightweight classifier → test.

## Non-goals (v1)

- Relative humidity (RH) fusion
- Web UI / API server
- Multi-site cameras (Tai Mo Shan, Victoria Peak, etc.)
- Continuous cloud-base height regression (only binary vs 150 m camera altitude)

## Decisions already agreed

| Item | Choice |
|------|--------|
| Labeling | Heuristic auto-label + human correction |
| Camera altitude | 150 m |
| Night images | In scope (same pipeline, night-specific features) |
| RH | Image-only for v1 |
| Approach | Classical features + sklearn classifier (not CNN, not pure rules-only) |

## Architecture

```
image/*.jpg
  → feature extraction (day/night branch)
  → heuristic auto-label (editable)
  → train lightweight classifier
  → predict: inside_cloud? + day/night
  → fixed message output
```

### Layout

| Path | Role |
|------|------|
| `src/features.py` | Features + day/night |
| `src/auto_label.py` | Heuristic initial labels |
| `src/train.py` | Train + save model |
| `src/predict.py` | Single/batch inference + messages |
| `data/labels.csv` | Labels (auto + corrections) |
| `models/cloud_clf.joblib` | Trained model |
| `tests/` | Unit + smoke tests |
| `image/` | Existing ~3497 KFB JPEGs (unchanged) |

## Features & day/night

**Day/night:** filename time `imgKFB_YYMMDD_HHMM` plus mean brightness. Roughly 07:00–18:00 and bright enough → `day`, else `night` (January HK; thresholds tunable).

**Shared features** (after cropping top-left timestamp overlay):

- Brightness mean / std (whiteout → high mean, low std)
- Edge density (Laplacian/Sobel; inside cloud → fewer edges)
- Saturation (inside cloud → greyer, lower saturation)
- Upper vs lower half contrast (distant scene washed out or not)

**Night extras:**

- Bright-spot count / area ratio (valley lights visible?)
- Few/no point lights + uniform dark/grey → lean `inside_cloud`

**Heuristic seed labels:**

- Day: high brightness + low contrast/edges → `inside_cloud`; clear foreground + layered distance → `not_inside`
- Night: almost no light spots + low contrast → `inside_cloud`; clear valley lights → `not_inside`

## Training & inference

- Split: ~80% train / 20% test by **date** (avoid same-day leakage)
- Model: sklearn RandomForest (logistic regression as optional baseline)
- Input: feature vector; output: `inside_cloud` | `not_inside`
- Artifact: `models/cloud_clf.joblib`
- Metrics: accuracy + confusion matrix printed by `train`

### Commands

```bash
python -m src.auto_label          # write data/labels.csv
# spot-check / edit label column
python -m src.train               # fit model, report metrics
python -m src.predict path.jpg    # print message
```

### Label correction

Edit `data/labels.csv` column `label` (`inside_cloud` / `not_inside`), then re-run `train`.

## Testing

- Unit: feature extraction, day/night from filename, message formatting
- Smoke: a few hand-picked day/night clear vs whiteout images end-to-end

## Success criteria

- Pipeline runs end-to-end on the local `image/` set
- Day and night both produce a message in the two fixed forms
- After spot-check corrections, test-set accuracy is reported (exploratory; no hard % gate in v1)
- Speculative RH / multi-camera / CNN deferred until image-only baseline is useful

## Out of scope notes (ponytail)

- No custom DL stack until RF fails on corrected labels
- No RH until a paired RH file exists
- Camera altitude is a constant `150`, not a config framework
