"""Lightweight web UI for Render free tier (Gradio is too memory-heavy)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Keep BLAS/OpenMP from spawning many threads (saves RAM on small instances).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("MALLOC_ARENA_MAX", "2")

from flask import Flask, jsonify, request, render_template_string
from waitress import serve

from src.live import predict_latest
from src.predict import predict_path

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>KFB Cloud Coverage</title>
  <style>
    :root { color-scheme: light; }
    body { font-family: system-ui, sans-serif; max-width: 36rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.45; }
    h1 { font-size: 1.35rem; margin-bottom: 0.35rem; }
    p.sub { color: #444; margin-top: 0; }
    form { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1.25rem 0; }
    input[type=file] { width: 100%; }
    button { margin-top: 0.75rem; padding: 0.55rem 1rem; font-size: 1rem; cursor: pointer; }
    .result { background: #f4f7fb; border-left: 4px solid #2b6cb0; padding: 0.85rem 1rem; margin-top: 1rem; }
    .err { background: #fff5f5; border-left-color: #c53030; }
  </style>
</head>
<body>
  <h1>KFB Cloud Coverage</h1>
  <p class="sub">Upload a weather-camera photo. Day/night is from image brightness; result also estimates cloud base vs ~150&nbsp;m.</p>
  <form method="post" enctype="multipart/form-data">
    <label for="photo">Photo</label><br/>
    <input id="photo" type="file" name="photo" accept="image/*" required/>
    <br/>
    <button type="submit">Analyze</button>
  </form>
  {% if result %}
  <div class="result {% if error %}err{% endif %}">{{ result }}</div>
  {% endif %}

  <h2 style="font-size:1.1rem;margin-top:1.75rem">Live &mdash; latest KFB photo</h2>
  <p class="sub" style="font-size:0.9rem">
    Newest photo from the
    <a href="https://www.hko.gov.hk/tc/wxinfo/ts/webcam/KFB_photo.htm" target="_blank" rel="noopener">HKO KFB webcam</a>,
    re-checked every 5 minutes.
  </p>
  <img id="live-img" style="max-width:100%;border-radius:6px;display:none" alt="latest KFB photo"/>
  <div id="live-out" class="result" style="display:none;white-space:pre-wrap"></div>

  <script>
    async function refreshLive() {
      var out = document.getElementById("live-out");
      out.style.display = "block";
      try {
        var res = await fetch("/live");
        var data = await res.json();
        if (!data.ok) {
          out.className = "result err";
          out.textContent = data.error;
          return;
        }
        out.className = "result";
        out.textContent = "Photo " + data.photo_time + "\\n" + data.message;
        var img = document.getElementById("live-img");
        img.src = data.image_url;
        img.style.display = "block";
      } catch (e) {
        out.className = "result err";
        out.textContent = "Live update failed: " + e;
      }
    }
    refreshLive();
    setInterval(refreshLive, 5 * 60 * 1000);
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(PAGE, result=None, error=False)


@app.get("/live")
def live():
    try:
        return jsonify(predict_latest())
    except Exception as e:
        return jsonify({"ok": False, "error": f"Live fetch failed: {e}"}), 502


@app.post("/")
def analyze():
    f = request.files.get("photo")
    if not f or not f.filename:
        return render_template_string(PAGE, result="Please choose a photo.", error=True), 400
    suffix = Path(f.filename).suffix or ".jpg"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            f.save(tmp.name)
            path = Path(tmp.name)
        try:
            msg = predict_path(path)
        finally:
            path.unlink(missing_ok=True)
        return render_template_string(PAGE, result=msg, error=False)
    except Exception as e:
        return render_template_string(PAGE, result=f"Could not analyze: {e}", error=True), 500


def main() -> None:
    port = int(os.environ.get("PORT", "7861"))
    # Waitress is lighter/safer than Flask debug server for production.
    serve(app, host="0.0.0.0", port=port, threads=1)


if __name__ == "__main__":
    main()
