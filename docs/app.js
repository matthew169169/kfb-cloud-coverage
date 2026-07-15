const DAY_BRIGHT_MIN = 80;
const CAMERA_ALT_M = 150;

let model = null;

async function loadModel() {
  if (model) return model;
  const res = await fetch("cloud_logreg.json");
  if (!res.ok) throw new Error("Could not load model JSON");
  model = await res.json();
  return model;
}

function formatMessage(inside, period) {
  if (inside) {
    return `Camera is inside cloud (${period}). Cloud base at or below ~${CAMERA_ALT_M} m.`;
  }
  return `I am not inside cloud (${period}). The cloud base should be above ${CAMERA_ALT_M} m.`;
}

function loadImageToCanvas(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const maxSide = 640;
      let w = img.width;
      let h = img.height;
      const scale = Math.min(1, maxSide / Math.max(w, h));
      w = Math.max(1, Math.round(w * scale));
      h = Math.max(1, Math.round(h * scale));
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      ctx.drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      resolve({ ctx, w, h });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not read image"));
    };
    img.src = url;
  });
}

function extractFeatures(ctx, w, h) {
  const y0 = Math.floor(h * 0.08);
  const cropH = Math.max(1, h - y0);
  const data = ctx.getImageData(0, y0, w, cropH).data;
  const n = w * cropH;
  const gray = new Float32Array(n);

  let sum = 0;
  let satSum = 0;
  let brightSpots = 0;

  for (let i = 0; i < n; i++) {
    const o = i * 4;
    const r = data[o];
    const g = data[o + 1];
    const b = data[o + 2];
    const gy = (r + g + b) / 3;
    gray[i] = gy;
    sum += gy;
    satSum += (Math.max(r, g, b) - Math.min(r, g, b)) / 255;
    if (gy > 200) brightSpots += 1;
  }

  const mean = sum / n;
  let varSum = 0;
  for (let i = 0; i < n; i++) {
    const d = gray[i] - mean;
    varSum += d * d;
  }
  const std = Math.sqrt(varSum / n);

  let lapSum = 0;
  for (let y = 0; y < cropH; y++) {
    const yu = (y - 1 + cropH) % cropH;
    const yd = (y + 1) % cropH;
    for (let x = 0; x < w; x++) {
      const xl = (x - 1 + w) % w;
      const xr = (x + 1) % w;
      const g0 = gray[y * w + x];
      lapSum += Math.abs(
        4 * g0 -
          gray[yu * w + x] -
          gray[yd * w + x] -
          gray[y * w + xl] -
          gray[y * w + xr]
      );
    }
  }

  const mid = Math.floor(cropH / 2);
  let upperSum = 0;
  let lowerSum = 0;
  const upperN = mid * w;
  for (let i = 0; i < upperN; i++) upperSum += gray[i];
  for (let i = upperN; i < n; i++) lowerSum += gray[i];
  const upper = upperSum / Math.max(1, upperN);
  const lower = lowerSum / Math.max(1, n - upperN);

  return {
    brightness_mean: mean,
    brightness_std: std,
    edge_density: lapSum / n / 255,
    saturation_mean: satSum / n,
    upper_lower_contrast: Math.abs(upper - lower) / 255,
    bright_spot_ratio: brightSpots / n,
    is_day: mean >= DAY_BRIGHT_MIN ? 1 : 0,
  };
}

function predictInside(feats, m) {
  let score = m.intercept;
  for (let i = 0; i < m.feature_names.length; i++) {
    score += m.coef[i] * feats[m.feature_names[i]];
  }
  return score >= 0;
}

async function analyzeFile(file) {
  const m = await loadModel();
  const { ctx, w, h } = await loadImageToCanvas(file);

  const preview = document.getElementById("preview");
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";

  const feats = extractFeatures(ctx, w, h);
  const period = feats.is_day >= 0.5 ? "day" : "night";
  const inside = predictInside(feats, m);
  return formatMessage(inside, period);
}

function setOut(text, isErr) {
  const out = document.getElementById("out");
  out.style.display = "block";
  out.className = "result" + (isErr ? " err" : "");
  out.textContent = text;
}

document.getElementById("go").addEventListener("click", async () => {
  const input = document.getElementById("photo");
  const file = input.files && input.files[0];
  if (!file) {
    setOut("Please choose a photo.", true);
    return;
  }
  setOut("Analyzing on your device…", false);
  try {
    const msg = await analyzeFile(file);
    setOut(msg, false);
  } catch (e) {
    setOut("Could not analyze: " + (e && e.message ? e.message : e), true);
  }
});

loadModel().catch(() => {});
