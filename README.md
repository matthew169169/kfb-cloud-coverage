---
title: KFB Cloud Coverage
emoji: ☁️
colorFrom: blue
colorTo: slate
sdk: gradio
sdk_version: 5.23.1
app_file: app.py
pinned: false
license: mit
short_description: Detect if a hill weather camera is inside cloud (~150 m).
---

# KFB cloud coverage

Upload a Hong Kong hill weather-camera photo (e.g. Kadoorie Farm).  
The app tells you **day/night** (from image brightness) and whether the camera is **inside cloud**, with a cloud-base message relative to **~150 m** camera altitude.

## Public web app (Render)

Deploy this repo as a **Render Web Service** (free tier). After deploy you get a URL like:

`https://kfb-cloud-coverage.onrender.com`

Anyone with that link can upload a photo — no install.

**Settings (important for free tier memory):**

- **Build:** `pip install -r requirements.txt`
- **Start:** `python -m src.web`  ← lightweight Flask UI (not Gradio)
- **Instance:** Free

> Free tier sleeps after idle; first open may take ~30–60s to wake.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m src.web
```

Optional Gradio UI (heavier; needs `requirements-dev.txt`):

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m src.app
```

## Train / retrain (optional)

Needs a local `image/` folder of KFB JPEGs:

```bash
python3 -m src.auto_label
python3 -m src.train
```

## Notes

- Day/night uses photo brightness only (not the filename).
- Bundled model: `models/cloud_clf.joblib` (heuristic seed labels; spot-check before operational use).
- Render free instances are ~512MB RAM — Gradio often OOM; production entrypoint is `src.web`.
