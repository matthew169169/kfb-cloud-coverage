const DAY_BRIGHT_MIN = 80;
const CAMERA_ALT_M = 150;

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

  // Far field (exclude bottom ~28% trees)
  const fy0 = Math.floor(cropH * 0.05);
  const fy1 = Math.max(fy0 + 1, Math.floor(cropH * 0.72));
  let farSum = 0;
  let farSumSq = 0;
  let farWash = 0;
  let farN = 0;
  let gx = 0;
  let gy = 0;
  let gxN = 0;
  let gyN = 0;
  for (let y = fy0; y < fy1; y++) {
    for (let x = 0; x < w; x++) {
      const v = gray[y * w + x];
      farSum += v;
      farSumSq += v * v;
      farN += 1;
      if (v > 170) farWash += 1;
      if (x + 1 < w) {
        gx += Math.abs(v - gray[y * w + (x + 1)]);
        gxN += 1;
      }
      if (y + 1 < fy1) {
        gy += Math.abs(v - gray[(y + 1) * w + x]);
        gyN += 1;
      }
    }
  }
  const farMean = farSum / farN;
  const farStd = Math.sqrt(Math.max(0, farSumSq / farN - farMean * farMean));
  const farGrad = gx / Math.max(1, gxN) + gy / Math.max(1, gyN);

  return {
    brightness_mean: mean,
    brightness_std: std,
    edge_density: lapSum / n / 255,
    saturation_mean: satSum / n,
    upper_lower_contrast: Math.abs(upper - lower) / 255,
    bright_spot_ratio: brightSpots / n,
    far_grad: farGrad,
    far_wash: farWash / farN,
    far_std: farStd,
    is_day: mean >= DAY_BRIGHT_MIN ? 1 : 0,
  };
}

function heuristicInside(feats) {
  const day = feats.is_day >= 0.5;
  if (day) {
    if (feats.far_grad <= 3.5 && feats.far_wash >= 0.65) return true;
    if (feats.far_std <= 28.0 && feats.far_wash >= 0.8) return true;
    if (feats.far_grad <= 4.3 && feats.far_wash >= 0.88 && feats.far_std <= 32.0)
      return true;
    return false;
  }
  if (feats.bright_spot_ratio >= 0.004) return false;
  if (feats.bright_spot_ratio < 0.0015 && feats.brightness_std < 22.0) return true;
  if (
    feats.bright_spot_ratio < 0.003 &&
    feats.brightness_std < 30.0 &&
    feats.upper_lower_contrast < 0.1
  ) {
    return true;
  }
  return false;
}

async function analyzeFile(file) {
  const { ctx, w, h } = await loadImageToCanvas(file);
  const preview = document.getElementById("preview");
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";

  const feats = extractFeatures(ctx, w, h);
  const period = feats.is_day >= 0.5 ? "day" : "night";
  const inside = heuristicInside(feats);
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
