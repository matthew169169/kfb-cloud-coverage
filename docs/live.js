/* Live mode: show the newest KFB webcam photo + model prediction,
 * refreshed every 5 minutes.
 *
 * Primary source: live.json published to the repo's `live-data` branch by a
 * GitHub Actions cron job (analysis runs server-side with the full Python
 * pipeline; raw.githubusercontent.com sends CORS headers, so this works for
 * every visitor with no third-party proxy).
 *
 * Fallback: analyze on-device — probe recent frames, fetch pixels through
 * public CORS proxies, and score with predictInside from index.html.
 */
(function () {
  "use strict";

  var LIVE_JSON = "https://raw.githubusercontent.com/matthew169169/kfb-cloud-coverage/live-data/live.json";
  var FRESH_MS = 30 * 60 * 1000;

  var FRAME_BASE = "https://www.weather.gov.hk/wxinfo/aws/hko_mica/kfb/";
  var STEP_MS = 5 * 60 * 1000;
  var MAX_LOOKBACK = 9;      // probe up to 45 minutes back for an existing frame
  var ANALYZE_FRAMES = 3;    // try pixel analysis on up to 3 recent frames
  var PROXIES = [
    function (u) { return "https://wsrv.nl/?url=" + encodeURIComponent(u); },
    function (u) { return "https://corsproxy.io/?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.allorigins.win/raw?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.codetabs.com/v1/proxy?quest=" + u; }
  ];

  var busy = false;

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  function hktFloorNow() {
    return new Date(Math.floor((Date.now() + 8 * 3600 * 1000) / STEP_MS) * STEP_MS);
  }

  function frameName(d) {
    return "imgKFB_" +
      pad2(d.getUTCFullYear() % 100) + pad2(d.getUTCMonth() + 1) + pad2(d.getUTCDate()) +
      "_" + pad2(d.getUTCHours()) + pad2(d.getUTCMinutes()) + ".jpg";
  }

  function fmtHKT(d) {
    return d.getUTCFullYear() + "-" + pad2(d.getUTCMonth() + 1) + "-" + pad2(d.getUTCDate()) +
      " " + pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes()) + " HKT";
  }

  function setLive(text, isErr) {
    var out = document.getElementById("live-out");
    out.style.display = "block";
    out.className = "result" + (isErr ? " err" : "");
    out.textContent = text;
  }

  function setMeta(text) {
    document.getElementById("live-meta").textContent = text;
  }

  function showImage(url) {
    var img = document.getElementById("live-img");
    img.src = url;
    img.style.display = "block";
  }

  /* ---------- primary: precomputed JSON from GitHub Actions ---------- */

  async function tryPrecomputed() {
    var res = await fetch(LIVE_JSON + "?ts=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error("live.json HTTP " + res.status);
    var data = await res.json();
    if (!data.ok) throw new Error(data.error || "live.json reports failure");
    var ageMs = Date.now() - Date.parse(data.updated_utc);
    if (!(ageMs >= 0 && ageMs < FRESH_MS)) throw new Error("live.json is stale");
    showImage(data.image_url);
    setLive("Photo " + data.photo_time + "\n" + data.message, false);
    setMeta("Analyzed on GitHub Actions " + Math.max(1, Math.round(ageMs / 60000)) +
      " min ago \u00b7 auto-updates every 5 min \u00b7 last checked " +
      new Date().toLocaleTimeString());
  }

  /* ---------- fallback: analyze on-device via CORS proxies ---------- */

  function probe(url) {
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () { resolve(true); };
      img.onerror = function () { resolve(false); };
      img.src = url;
    });
  }

  async function findRecentFrames() {
    var base = hktFloorNow();
    var found = [];
    for (var i = 0; i < MAX_LOOKBACK && found.length < ANALYZE_FRAMES; i++) {
      var d = new Date(base.getTime() - i * STEP_MS);
      var url = FRAME_BASE + frameName(d);
      if (await probe(url)) found.push({ date: d, url: url });
    }
    return found;
  }

  async function fetchPixels(url) {
    for (var i = 0; i < PROXIES.length; i++) {
      try {
        var res = await fetch(PROXIES[i](url));
        if (res.ok) {
          var blob = await res.blob();
          if (blob && blob.size > 1000 &&
              (blob.type.indexOf("image") === 0 || blob.type === "")) {
            return blob;
          }
        }
      } catch (e) { /* proxy down — try the next one */ }
    }
    return null;
  }

  async function tryOnDevice() {
    setLive("Looking for the latest KFB photo\u2026", false);
    var frames = await findRecentFrames();
    if (!frames.length) throw new Error("no recent frame found (network issue?)");
    showImage(frames[0].url);

    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      setLive("Photo " + fmtHKT(f.date) + " \u2014 analyzing on your device\u2026", false);
      var blob = await fetchPixels(f.url);
      if (!blob) continue;  // proxies may fail per-frame; try an older frame
      var packed = await loadImageToCanvas(blob);
      var feats = extractFeatures(packed.ctx, packed.w, packed.h);
      var period = feats.is_day >= 0.5 ? "day" : "night";
      var inside = predictInside(feats);
      showImage(f.url);
      setLive("Photo " + fmtHKT(f.date) + "\n" + formatMessage(inside, period), false);
      setMeta("Analyzed on your device \u00b7 auto-updates every 5 min \u00b7 last checked " +
        new Date().toLocaleTimeString());
      return;
    }
    setLive(
      "Photo " + fmtHKT(frames[0].date) + " loaded, but analysis is unavailable " +
      "right now (server data pending and CORS proxies failed). " +
      "It will retry in 5 minutes, or save the photo and use the upload box above.",
      true
    );
  }

  async function refreshLive() {
    if (busy) return;
    busy = true;
    try {
      try {
        await tryPrecomputed();
      } catch (e) {
        await tryOnDevice();
      }
    } catch (e) {
      setLive("Live update failed: " + (e && e.message ? e.message : e), true);
    } finally {
      busy = false;
    }
  }

  document.getElementById("live-refresh").addEventListener("click", refreshLive);
  refreshLive();
  setInterval(refreshLive, STEP_MS);
})();
