# KFB cloud coverage

Upload a Hong Kong hill weather-camera photo (e.g. Kadoorie Farm).  
The app tells you **day/night** (from image brightness) and whether the camera is **inside cloud**, with a cloud-base message relative to **~150 m** camera altitude.

**Live mode:** both web versions also fetch the newest photo from the
[HKO KFB webcam](https://www.hko.gov.hk/tc/wxinfo/ts/webcam/KFB_photo.htm)
(published every 5 minutes) and show the photo time + prediction, auto-refreshing every 5 minutes.
The browser version analyzes pixels via a public CORS proxy (HKO sends no CORS headers);
the Flask version fetches server-side (`GET /live`, no proxy needed). CLI: `python -m src.live`.

## Public web app (recommended): GitHub Pages — runs on the user's device

Static site in `docs/`. **Computation runs in the visitor's browser** (no server RAM / no Render OOM).  
Anyone with the link can use it — the page is public; the photo stays on their device.

After GitHub Pages is enabled:

**https://matthew169169.github.io/kfb-cloud-coverage/**

## Optional server (Render)

`python -m src.web` — may hit free-tier memory limits. Prefer Pages above.

## Run locally (browser version)

```bash
cd docs
python3 -m http.server 8080
```

Open http://127.0.0.1:8080

## Train / retrain (optional)

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m src.auto_label   # extract features for all photos in image/
python3 -m src.train        # train on data/golden_labels.csv, export JSON
```

`data/golden_labels.csv` holds 142 hand-verified labels (the golden set);
training uses these instead of the heuristic seed labels. The trained
logistic model scores 93% leave-one-date-out CV accuracy on the golden set
vs 72% for the old rules. `src.train` writes the model JSON to both
`models/` and `docs/`.

## Notes

- Day/night uses photo brightness only (not the filename).
- Model: `models/cloud_logreg.json` (copied into `docs/` for Pages);
  inference is a single dot product, identical in Python and JS.
- Heuristic rules (`src/heuristic.py`) remain for auto-labeling and as an
  offline fallback.
