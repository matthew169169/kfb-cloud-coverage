/* Live mode: show the freshest KFB photo that has an analysis — the photo
 * and the prediction always refer to the SAME frame. Rechecks every minute;
 * new frames appear about every 5 minutes.
 *
 * Preference order:
 *   1. Newest published frame analyzed on-device (pixels fetched through a
 *      CORS proxy, scored with the same model as everywhere else).
 *   2. live.json published by the GitHub Actions cron — its image_url and
 *      message describe the same frame, served from raw.githubusercontent.com
 *      which sends CORS headers.
 * Whichever source covers the newer frame wins; photo and analysis are never
 * mixed across frames.
 */
(function () {
  "use strict";

  var LIVE_JSON = "https://raw.githubusercontent.com/matthew169169/kfb-cloud-coverage/live-data/live.json";
  var FRESH_MS = 20 * 60 * 1000;   // server data older than this is ignored
  var CHECK_MS = 60 * 1000;        // re-check every minute for a newer result

  var FRAME_BASE = "https://www.weather.gov.hk/wxinfo/aws/hko_mica/kfb/";
  var STEP_MS = 5 * 60 * 1000;     // HKO frame cadence
  var MAX_LOOKBACK = 9;      // probe up to 45 minutes back
  var ANALYZE_FRAMES = 3;    // attempt on-device analysis on up to 3 frames
  var PROXIES = [
    function (u) { return "https://wsrv.nl/?url=" + encodeURIComponent(u); },
    function (u) { return "https://corsproxy.io/?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.allorigins.win/raw?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.codetabs.com/v1/proxy?quest=" + u; }
  ];

  var busy = false;
  var lastShownTime = null;  // frame time of the currently displayed result

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
    document.getElementById("live-meta").textContent =
      text + " \u00b7 rechecks every minute \u00b7 last checked " +
      new Date().toLocaleTimeString();
  }

  function showImage(url) {
    var img = document.getElementById("live-img");
    if (img.getAttribute("src") !== url) img.src = url;
    img.style.display = "block";
  }

  function showResult(url, time, message, sourceNote) {
    showImage(url);
    setLive("Photo " + time + "\n" + message, false);
    setMeta(sourceNote);
    lastShownTime = time;
  }

  async function fetchLiveJson() {
    try {
      var res = await fetch(LIVE_JSON + "?ts=" + Date.now(), { cache: "no-store" });
      if (!res.ok) return null;
      var data = await res.json();
      if (!data.ok) return null;
      var age = Date.now() - Date.parse(data.updated_utc);
      return (age >= 0 && age < FRESH_MS) ? data : null;
    } catch (e) {
      return null;
    }
  }

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
      if (await probe(url)) found.push({ date: d, url: url, time: fmtHKT(d) });
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

  async function analyzeOnDevice(frame) {
    var blob = await fetchPixels(frame.url);
    if (!blob) return null;
    var packed = await loadImageToCanvas(blob);
    var feats = extractFeatures(packed.ctx, packed.w, packed.h);
    var period = feats.is_day >= 0.5 ? "day" : "night";
    return formatMessage(predictInside(feats, 150), period, 150);
  }

  async function refreshLive() {
    if (busy) return;
    busy = true;
    try {
      if (lastShownTime === null) {
        setLive("Checking for the latest KFB photo\u2026", false);
      }
      var server = await fetchLiveJson();          // may be null
      var frames = await findRecentFrames();       // newest first

      if (!frames.length && !server) {
        throw new Error("no recent frame found (network issue?)");
      }

      // Nothing newer than what is on screen: just bump the checked clock.
      var newest = frames.length ? frames[0].time : server.photo_time;
      if (server && server.photo_time > newest) newest = server.photo_time;
      if (lastShownTime !== null && newest <= lastShownTime) {
        var prev = document.getElementById("live-meta").textContent;
        setMeta(prev.split(" \u00b7 ")[0] || "Up to date");
        return;
      }

      // Server already covers the newest published frame — done.
      if (server && frames.length && server.photo_time === frames[0].time) {
        showResult(server.image_url, server.photo_time, server.message,
          "Analyzed on GitHub Actions " + serverAge(server) + " min ago");
        return;
      }

      // Try to analyze frames newer than the server result, newest first.
      for (var i = 0; i < frames.length; i++) {
        var f = frames[i];
        if (server && f.time <= server.photo_time) break;  // older than server
        if (lastShownTime === null) {
          setLive("Photo " + f.time + " \u2014 analyzing on your device\u2026", false);
        }
        var msg = await analyzeOnDevice(f);
        if (msg) {
          showResult(f.url, f.time, msg, "Analyzed on your device");
          return;
        }
      }

      // Fall back to the server's own frame (photo and analysis stay paired).
      if (server) {
        showResult(server.image_url, server.photo_time, server.message,
          "Analyzed on GitHub Actions " + serverAge(server) + " min ago");
        return;
      }

      // No analysis available for any recent frame. Keep whatever result is
      // already on screen; only surface the error state on first load.
      if (lastShownTime === null) {
        showImage(frames[0].url);
        setLive(
          "Photo " + frames[0].time + " loaded, but analysis is unavailable right now " +
          "(server data pending and CORS proxies failed). It retries every minute, " +
          "or save the photo and use the upload box above.",
          true
        );
      }
    } catch (e) {
      if (lastShownTime === null) {
        setLive("Live update failed: " + (e && e.message ? e.message : e), true);
      }
    } finally {
      busy = false;
    }
  }

  function serverAge(server) {
    return Math.max(1, Math.round((Date.now() - Date.parse(server.updated_utc)) / 60000));
  }

  document.getElementById("live-refresh").addEventListener("click", refreshLive);
  refreshLive();
  setInterval(refreshLive, CHECK_MS);
})();
