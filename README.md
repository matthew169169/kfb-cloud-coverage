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

## Use online

This Space is the public app — open the Space page and upload a photo. No install needed.

## Run locally

```bash
python3 -m pip install -r requirements.txt
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
- Bundled model: `models/cloud_clf.joblib` (trained on heuristic seed labels; spot-check before operational use).
