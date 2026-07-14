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

**One-time deploy on Render:**

1. Push this repo to GitHub (public).
2. Go to https://dashboard.render.com → **New** → **Web Service** → connect the repo.
3. Use:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python -m src.app`
   - **Instance:** Free
4. Deploy. Open the `*.onrender.com` URL and share it.

> Free tier sleeps after idle; first open may take ~30–60s to wake.

Or use `render.yaml` Blueprint: **New** → **Blueprint** → select this repo.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m src.app
```

Optional temporary public tunnel from your laptop:

```bash
GRADIO_SHARE=1 python3 -m src.app
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
- Hugging Face Gradio Spaces currently need PRO; this project targets **Render** (or any host that sets `PORT`) instead.
