const DAY_BRIGHT_MIN = 80;

const STATIONS = {
  150:  "KFBG (Kadoorie Farm)",
  957:  "Tai Mo Shan",
  396:  "Victoria Peak",
  934:  "Lantau Peak",
  702:  "Ma On Shan",
  495:  "Lion Rock",
  639:  "Pat Sin Leng",
};

const KFBG_THRESHOLDS = {
  profile: "KFBG calibrated",
  day: {
    washA: 0.65, gradA: 3.5,
    stdB: 28.0, washB: 0.8,
    washC: 0.88, gradC: 4.3, stdC: 32.0,
  },
  night: {
    lightsClear: 0.004,
    bspA: 0.0015, stdA: 22.0,
    bspB: 0.003, stdB: 30.0, ulcB: 0.1,
  },
  vis: {
    nightBspA: 0.002, nightStdA: 30,
    nightBspB: 0.005, nightBspC: 0.010,
    dayWash300: 0.50, dayWash500: 0.35, dayGrad500: 4.0,
    dayWash1k: 0.20, dayGrad1k: 8.0,
    dayWash3k: 0.08, dayGrad3k: 14.0,
  },
};

function midPeakThresholds(profile) {
  return {
    profile,
    day: {
      washA: 0.70, gradA: 3.2,
      stdB: 24.0, washB: 0.84,
      washC: 0.90, gradC: 4.0, stdC: 28.0,
    },
    night: {
      lightsClear: 0.003,
      bspA: 0.0012, stdA: 20.0,
      bspB: 0.0025, stdB: 28.0, ulcB: 0.09,
    },
    vis: {
      nightBspA: 0.0018, nightStdA: 28,
      nightBspB: 0.0045, nightBspC: 0.009,
      dayWash300: 0.56, dayWash500: 0.40, dayGrad500: 3.6,
      dayWash1k: 0.24, dayGrad1k: 7.0,
      dayWash3k: 0.10, dayGrad3k: 12.0,
    },
  };
}

function highPeakThresholds(profile) {
  return {
    profile,
    day: {
      washA: 0.75, gradA: 3.0,
      stdB: 20.0, washB: 0.86,
      washC: 0.92, gradC: 3.6, stdC: 24.0,
    },
    night: {
      lightsClear: 0.0025,
      bspA: 0.0010, stdA: 18.0,
      bspB: 0.0020, stdB: 26.0, ulcB: 0.08,
    },
    vis: {
      nightBspA: 0.0015, nightStdA: 26,
      nightBspB: 0.004, nightBspC: 0.008,
      dayWash300: 0.62, dayWash500: 0.46, dayGrad500: 3.2,
      dayWash1k: 0.28, dayGrad1k: 6.0,
      dayWash3k: 0.12, dayGrad3k: 10.0,
    },
  };
}

const STATION_THRESHOLDS = {
  150: KFBG_THRESHOLDS,
  396: midPeakThresholds("Victoria Peak starting"),
  495: midPeakThresholds("Lion Rock starting"),
  639: midPeakThresholds("Pat Sin Leng starting"),
  702: midPeakThresholds("Ma On Shan starting"),
  934: highPeakThresholds("Lantau Peak starting"),
  957: highPeakThresholds("Tai Mo Shan starting"),
};

function getThresholds(altM) {
  return STATION_THRESHOLDS[altM] || KFBG_THRESHOLDS;
}

function formatMessage(inside, period, altM) {
  if (inside) {
    return `Camera is inside cloud (${period}). Cloud base at or below ~${altM} m.`;
  }
  return `I am not inside cloud (${period}). The cloud base should be above ${altM} m.`;
}

function estimateVisibility(feats, insideCloud, altM) {
  if (insideCloud) return "Visibility: at or below 300 m (camera in cloud/fog)";
  const v = getThresholds(altM).vis;
  const { far_grad, far_wash, is_day, bright_spot_ratio, brightness_std } = feats;
  if (is_day < 0.5) {
    if (bright_spot_ratio < v.nightBspA && brightness_std < v.nightStdA) return "Visibility: at least 300 m (night, few lights visible)";
    if (bright_spot_ratio < v.nightBspB)  return "Visibility: at least 500 m (night)";
    if (bright_spot_ratio < v.nightBspC)  return "Visibility: at least 1 km (night)";
    return "Visibility: at least 3 km (night, valley lights clear)";
  }
  if (far_wash > v.dayWash300)                     return "Visibility: at least 300 m (heavy haze / low cloud nearby)";
  if (far_wash > v.dayWash500 || far_grad < v.dayGrad500)  return "Visibility: at least 500 m";
  if (far_wash > v.dayWash1k || far_grad < v.dayGrad1k)  return "Visibility: at least 1 km";
  if (far_wash > v.dayWash3k || far_grad < v.dayGrad3k) return "Visibility: at least 3 km";
  return "Visibility: at least 5 km (far field clear)";
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

function heuristicInside(feats, t) {
  t = t || KFBG_THRESHOLDS;
  const d = t.day;
  const n = t.night;
  const day = feats.is_day >= 0.5;
  if (day) {
    if (feats.far_grad <= d.gradA && feats.far_wash >= d.washA) return true;
    if (feats.far_std <= d.stdB && feats.far_wash >= d.washB) return true;
    if (feats.far_grad <= d.gradC && feats.far_wash >= d.washC && feats.far_std <= d.stdC)
      return true;
    return false;
  }
  if (feats.bright_spot_ratio >= n.lightsClear) return false;
  if (feats.bright_spot_ratio < n.bspA && feats.brightness_std < n.stdA) return true;
  if (
    feats.bright_spot_ratio < n.bspB &&
    feats.brightness_std < n.stdB &&
    feats.upper_lower_contrast < n.ulcB
  ) {
    return true;
  }
  return false;
}

async function analyzeFile(file, altM) {
  const { ctx, w, h } = await loadImageToCanvas(file);
  const preview = document.getElementById("preview");
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";

  const feats  = extractFeatures(ctx, w, h);
  const period = feats.is_day >= 0.5 ? "day" : "night";
  const t = getThresholds(altM);
  const inside = heuristicInside(feats, t);
  return {
    cloudMsg: formatMessage(inside, period, altM),
    visMsg:   estimateVisibility(feats, inside, altM),
    inside,
    profile: t.profile,
    feats,
  };
}

function setResults(cloudMsg, visMsg, isInside) {
  const block = document.getElementById("resultBlock");
  const out   = document.getElementById("out");
  const vis   = document.getElementById("vis");
  if (block) block.style.display = "block";
  out.className  = "result" + (isInside ? " inside" : "");
  out.textContent = cloudMsg;
  if (vis) vis.textContent = visMsg;
}

document.getElementById("go").addEventListener("click", async () => {
  const input = document.getElementById("photo");
  const file  = input.files && input.files[0];
  const stationEl = document.getElementById("station");
  const altM = stationEl ? parseInt(stationEl.value, 10) : 150;
  if (!file) { setResults("Please choose a photo.", "", true); return; }
  setResults("Analyzing on your device…", "", false);
  try {
    const { cloudMsg, visMsg, inside, feats, profile } = await analyzeFile(file, altM);
    setResults(cloudMsg, visMsg, inside);
    const dbg = document.getElementById("dbg");
    if (dbg) {
      dbg.textContent =
        "v8 | " + (STATIONS[altM] || altM + " m") +
        " | " + profile +
        " | far_grad=" + feats.far_grad.toFixed(2) +
        " far_wash=" + feats.far_wash.toFixed(2) +
        " far_std=" + feats.far_std.toFixed(1) +
        " bsp=" + feats.bright_spot_ratio.toFixed(4) +
        " → " + (inside ? "inside_cloud" : "not_inside");
    }
  } catch (e) {
    setResults("Could not analyze: " + (e && e.message ? e.message : e), "", true);
  }
});
