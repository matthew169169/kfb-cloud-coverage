# KFB cloud coverage

Detect whether the Kadoorie Farm webcam is inside cloud (day/night) and emit a cloud-base message relative to camera altitude 150 m.

## Setup
```bash
python3 -m pip install -r requirements.txt
```

## Web UI（上传照片）
```bash
python3 -m src.app
```
浏览器会打开页面：上传照片即可看到日夜 + 是否在云内的结果。

## Pipeline
```bash
python3 -m src.auto_label
python3 -m src.train
python3 -m src.predict image/imgKFB_160101_1200.jpg
```

（可选）改正 `data/labels.csv` 的 `label` 列（`inside_cloud` | `not_inside`）后再跑 `train`。

## Tests
```bash
python3 -m pytest -v
```

## Notes
- `image/` holds local KFB JPEGs (gitignored).
- Heuristic labels are seeds — spot-check before trusting metrics.
- Model artifact: `models/cloud_clf.joblib` (gitignored; regenerate with train).
