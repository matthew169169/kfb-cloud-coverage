/* Live mode: fetch the latest KFB webcam photo from HKO every 5 minutes,
 * analyze it on-device and show the photo time + prediction.
 *
 * Reuses extractFeatures / predictInside / formatMessage / loadImageToCanvas
 * defined in the inline script of index.html (must load after it).
 *
 * HKO does not send CORS headers, so pixel analysis goes through a public
 * CORS proxy; the photo itself is displayed via a direct <img> hotlink.
 */
(function () {
  "use strict";

  var FRAME_BASE = "https://www.weather.gov.hk/wxinfo/aws/hko_mica/kfb/";
  var STEP_MS = 5 * 60 * 1000;
  var MAX_LOOKBACK = 9; // try up to 45 minutes back
  var PROXIES = [
    // wsrv.nl is a Cloudflare-backed image CDN that always sends CORS headers;
    // far more reliable than generic CORS proxies (kept below as fallbacks).
    function (u) { return "https://wsrv.nl/?url=" + encodeURIComponent(u); },
    function (u) { return "https://corsproxy.io/?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.allorigins.win/raw?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.codetabs.com/v1/proxy?quest=" + u; }
  ];

  var busy = false;

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  // Date whose UTC fields hold Hong Kong time (UTC+8), floored to 5 minutes.
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

  function probe(url) {
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () { resolve(true); };
      img.onerror = function () { resolve(false); };
      img.src = url;
    });
  }

  async function findLatest() {
    var base = hktFloorNow();
    for (var i = 0; i < MAX_LOOKBACK; i++) {
      var d = new Date(base.getTime() - i * STEP_MS);
      var url = FRAME_BASE + frameName(d);
      if (await probe(url)) return { date: d, url: url };
    }
    return null;
  }

  async function fetchPixels(url) {
    for (var i = 0; i < PROXIES.length; i++) {
      try {
        var res = await fetch(PROXIES[i](url));
        if (res.ok) {
          var blob = await res.blob();
          if (blob && blob.size > 1000) return blob;
        }
      } catch (e) { /* proxy down — try the next one */ }
    }
    throw new Error("all CORS proxies failed");
  }

  function setLive(text, isErr) {
    var out = document.getElementById("live-out");
    out.style.display = "block";
    out.className = "result" + (isErr ? " err" : "");
    out.textContent = text;
  }

  async function refreshLive() {
    if (busy) return;
    busy = true;
    var meta = document.getElementById("live-meta");
    try {
      setLive("Looking for the latest KFB photo\u2026", false);
      var latest = await findLatest();
      if (!latest) throw new Error("no recent frame found (network issue?)");

      var img = document.getElementById("live-img");
      img.src = latest.url;
      img.style.display = "block";

      setLive("Photo " + fmtHKT(latest.date) + " \u2014 analyzing on your device\u2026", false);
      var blob;
      try {
        blob = await fetchPixels(latest.url);
      } catch (e) {
        setLive(
          "Photo " + fmtHKT(latest.date) + " loaded, but pixel analysis is blocked " +
          "(HKO has no CORS and every proxy failed). Save the photo and use the upload box above.",
          true
        );
        return;
      }
      var packed = await loadImageToCanvas(blob);
      var feats = extractFeatures(packed.ctx, packed.w, packed.h);
      var period = feats.is_day >= 0.5 ? "day" : "night";
      var inside = predictInside(feats);
      setLive("Photo " + fmtHKT(latest.date) + "\n" + formatMessage(inside, period), false);
      meta.textContent = "Auto-updates every 5 min \u00b7 last checked " +
        new Date().toLocaleTimeString();
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
