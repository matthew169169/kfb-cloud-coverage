# KFB cloud coverage

Upload a Hong Kong hill weather-camera photo (e.g. Kadoorie Farm).  
The app tells you **day/night** (from image brightness) and whether the camera is **inside cloud**, with a cloud-base message relative to **~150 m** camera altitude.

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
python3 -m src.auto_label
python3 -m src.train
cp models/cloud_logreg.json docs/cloud_logreg.json
```

## Notes

- Day/night uses photo brightness only (not the filename).
- Model: `models/cloud_logreg.json` (copied into `docs/` for Pages).
