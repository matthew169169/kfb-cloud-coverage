# KFB cloud coverage

Detect whether the Kadoorie Farm webcam is inside cloud (day/night) and emit a cloud-base message relative to camera altitude 150 m.

## Setup
```bash
pip install -r requirements.txt
```

## Pipeline
```bash
python -m src.auto_label
# optional: edit data/labels.csv label column (inside_cloud | not_inside)
python -m src.train
python -m src.predict image/imgKFB_160101_1200.jpg
```

## Tests
```bash
pytest -v
```

## Notes
- `image/` holds local KFB JPEGs (gitignored).
- Heuristic labels are seeds — spot-check before trusting metrics.
- Model artifact: `models/cloud_clf.joblib` (gitignored; regenerate with train).
