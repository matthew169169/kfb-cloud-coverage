"""Process-update deck driven by models/train_report.json."""
from __future__ import annotations
import json
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from ppt_gen import theme as T
from ppt_gen.helpers import (
    add_title, caption, card, chevron, footer, para, picture, style_run, textbox,
)
TOTAL = 10
A = T.ASSETS
REPORT = T.ROOT / "models" / "train_report.json"

def _report():
    return json.loads(REPORT.read_text())
def _pct(x):
    return f"{100 * float(x):.1f}%"
def _cm(m):
    c = m["cm"]
    return f"[[{c[0][0]}, {c[0][1]}], [{c[1][0]}, {c[1][1]}]]"
def _n(r):
    c = r["counts"]
    return c.get("combined", c.get("fit_pool"))
def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])
def _table(slide, rows, left, top, widths, row_h=0.38):
    gt = slide.shapes.add_table(len(rows), len(rows[0]), Inches(left), Inches(top),
                                Inches(sum(widths)), Inches(row_h * len(rows))).table
    for j, w in enumerate(widths):
        gt.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = gt.cell(i, j); c.text = ""
            p = c.text_frame.paragraphs[0]; p.text = str(val)
            p.font.size = Pt(12); p.font.bold = i == 0
            p.font.color.rgb = T.WHITE if i == 0 else T.INK
            p.font.name = T.LATIN_FONT
            if i == 0:
                c.fill.solid(); c.fill.fore_color.rgb = T.NAVY
            elif i % 2 == 0:
                c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0xF7, 0xFA, 0xFC)
    return gt

def s01_cover(prs, r):
    s = _blank(prs)
    picture(s, A / "update_cover.jpg", 0, 0, w=T.SLIDE_W, h=T.SLIDE_H)
    h, g, v = r["holdout"], r["golden_all_142"]["new"], r["review_111"]
    tf = textbox(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(4.4))
    para(tf, "KFB Cloud Coverage", size=44, color=T.WHITE, bold=True, first=True, space_after=8)
    para(tf, "Process update — combine every unique label, hold out dates, ship", size=20, color=T.SKY_LIGHT, space_after=16)
    para(tf, f"{_n(r):,} unique frames  ·  {r['counts']['dates']} dates  ·  date-balanced 80/20", size=16, color=T.WHITE, space_after=10)
    para(tf, f"Holdout {_pct(h['test']['acc'])}  ·  golden {_pct(g['acc'])}  ·  111 {_pct(v['new']['acc'])}  ·  day {_pct(v['new_day']['acc'])}  ·  night {_pct(v['new_night']['acc'])}", size=15, color=T.SKY_LIGHT)
    tf2 = textbox(s, Inches(0.9), Inches(6.55), Inches(11.5), Inches(0.4))
    para(tf2, "September 2026  ·  Kadoorie Farm webcam at ~150 m", size=13, color=T.SKY_LIGHT, first=True)

def s02_why(prs, r):
    s = _blank(prs)
    add_title(s, "Why this update", "v1 used 2016. d413d74 added 2023 hourly. This ships every unique frame.")
    items = [
        ("Before (d413d74)", T.CARD_BG, ["8,354 rows: 142 golden + 8,212 hourly","No Jan–Apr minutes in the fit","Date-grouped 80/20, train-split fit","111 visual check 83.8% / day 94.6%","Night 73.2% still the weak slice"]),
        ("What changed", T.CARD_SKY, ["Add 163,989 extra per-minute rows","111 visual labels override hourly seed","Weight 1/date, humans ×20","Date-grouped 80/20, train-split fit","Same 9 features, same JSON export"]),
        ("Why date-balance", T.CARD_GREEN, ["Jan–Apr is ~1,440 frames/day","May–Dec is only 24 hourly frames/day","Equal-weight minutes drown later months","Mass: golden 40%, hourly 35%, minutes 18%, 111 7%","Keeps a full-year prior in the model"]),
    ]
    x = 0.7
    for title, fill, bullets in items:
        card(s, Inches(x), Inches(1.55), Inches(3.95), Inches(5.15), fill=fill)
        tf = textbox(s, Inches(x + 0.28), Inches(1.78), Inches(3.4), Inches(4.8))
        para(tf, title, size=18, color=T.NAVY, bold=True, first=True, space_after=10)
        for b in bullets:
            para(tf, b, size=14, bullet=True, space_after=8)
        x += 4.15

def s03_process(prs, r):
    s = _blank(prs)
    add_title(s, "Updated process", "Photos → features → seed labels → human override → date-split train → live")
    steps = [("1. Ingest","Hourly year + Jan–Apr minutes"),("2. Features","9 numbers, no CNN"),("3. Seed labels","heuristic, not the model"),("4. Human GT","142 golden + 111 visual"),("5. Train","date-balanced 80/20"),("6. Ship","tiny JSON, Pages + Flask")]
    x = 0.45
    for text, sub in steps:
        chevron(s, Inches(x), Inches(1.65), Inches(2.18), Inches(1.15), text, sub)
        x += 2.12
    rows = [
        ("Photo in","HKO KFB webcam / USB dump. Crop top 8% timestamp, resize 640 px — same as the browser."),
        ("Dedup","Filename unique. Hourly overwrites the matching minute. Golden and 111 override both."),
        ("Weights","(1 / n_frames on that YYMMDD) × 20 if human. Mean-normalized so April minutes cannot own the loss."),
        ("Split hygiene","GroupShuffleSplit by date, rs=42. Shipped JSON is the train-split fit — no full-data refit."),
        ("Live loop","GitHub Actions every ~5 min → live.json. Pages runs the same JSON if the feed is stale."),
    ]
    y = 3.05
    for title, body in rows:
        card(s, Inches(0.55), Inches(y), Inches(12.25), Inches(0.72))
        tf = textbox(s, Inches(0.8), Inches(y + 0.1), Inches(11.8), Inches(0.55))
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = title; style_run(r1, 14, T.SKY, bold=True)
        r2 = p.add_run(); r2.text = "   " + body; style_run(r2, 13, T.INK)
        y += 0.78

def s04_photos(prs, r):
    s = _blank(prs)
    c, o = r["counts"], r["counts"]["origins"]
    add_title(s, "All train data combined", f"{_n(r):,} unique frames · {c['inside']:,} inside_cloud · {c['dates']} dates")
    picture(s, A / "update_data.png", Inches(0.45), Inches(1.5), w=Inches(6.9))
    card(s, Inches(7.5), Inches(1.55), Inches(5.3), Inches(5.15))
    tf = textbox(s, Inches(7.78), Inches(1.75), Inches(4.8), Inches(4.85))
    para(tf, "How each set is used", size=16, color=T.NAVY, bold=True, first=True, space_after=8)
    para(tf, f"Golden {o['golden_2016']} (2016, human) — honest labels. Override any auto-label.", size=13, bullet=True, space_after=6)
    para(tf, f"R5 hourly {o['r5_hourly']:,} (2023) — year-round seed. How May–Dec enter the model.", size=13, bullet=True, space_after=6)
    para(tf, f"R5 extra minutes {o['r5_minute']:,} (Jan–Apr) — denser time, down-weighted per date.", size=13, bullet=True, space_after=6)
    para(tf, f"Review {o['human_2023']} — visual GT overrides. {c.get('review_111_in_test_dates', 20)} on test dates.", size=13, bullet=True, space_after=8)
    para(tf, "USB minutes stop 22 Apr. Date-balance is how we still keep a year.", size=13, color=T.SKY, bold=True)

def s05_grids(prs, r):
    s = _blank(prs)
    add_title(s, "How the 111 photos were labeled", "review_r5/grid_01–13.jpg — judged against the project rule, then used as human overrides")
    x = 0.55
    for g in ("grid_01.jpg", "grid_02.jpg", "grid_03.jpg", "grid_04.jpg"):
        picture(s, T.ROOT / "review_r5" / g, Inches(x), Inches(1.55), w=Inches(2.95), h=Inches(3.35))
        caption(s, g.replace(".jpg", ""), Inches(x), Inches(4.92), Inches(2.95), size=11)
        x += 3.15
    card(s, Inches(0.55), Inches(5.35), Inches(12.25), Inches(1.5), fill=T.CARD_SKY)
    tf = textbox(s, Inches(0.85), Inches(5.5), Inches(11.7), Inches(1.25))
    para(tf, "Label rule (same for day and night)", size=15, color=T.NAVY, bold=True, first=True, space_after=4)
    para(tf, "Day: washed-out textureless far field = inside; visible valley = not inside.  Night: lightless flat frame = inside; any valley lights = not inside.  Result: 57 inside / 54 not inside.", size=13)

def s06_holdout(prs, r):
    s = _blank(prs)
    h = r["holdout"]
    add_title(s, f"Date holdout — unseen {h['test']['n']:,} frames", "GroupShuffleSplit 80/20 by YYMMDD · train-split fit, no full-data refit")
    def row(name, m):
        return [name, m["n"], _pct(m["acc"]), f"{m['precision']:.3f}", f"{m['recall']:.3f}", f"{m['f1']:.3f}", _cm(m)]
    _table(s, [["Slice","n","Acc","P","R","F1","Confusion [[TN,FP],[FN,TP]]"],
               row("All test", h["test"]), row("Golden 2016", h["test_golden"]),
               row("R5 hourly seed", h["test_hourly"]), row("111 on test dates", h["test_human_2023"]),
               row("Train (ref.)", h["train"]), row("d413d74, same test", h["old_same_test"])],
          0.5, 1.55, [2.15, 0.7, 0.85, 0.75, 0.7, 0.7, 4.6], row_h=0.48)
    card(s, Inches(0.55), Inches(5.55), Inches(12.25), Inches(1.25), fill=T.CARD_SKY)
    tf = textbox(s, Inches(0.85), Inches(5.7), Inches(11.7), Inches(1.0))
    para(tf, "Read this carefully", size=15, color=T.NAVY, bold=True, first=True, space_after=4)
    para(tf, f"Recall {h['test']['recall']:.3f} on {h['test']['n']:,} unseen-date rows. Accuracy is tied with d413d74. Heuristic slices restates the rules that labeled most of the train set — trust golden and 111.", size=13)

def s07_visual(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "111 visual 2023 photos", "Human overrides in the date split. Best 2023 eye-check we have.")
    picture(s, A / "update_cm.png", Inches(0.4), Inches(1.5), w=Inches(5.4))
    picture(s, A / "update_dn.png", Inches(5.7), Inches(1.5), w=Inches(7.1))
    def row(name, m):
        return [name, str(m["n"]), f"{m['acc']:.3f}", f"{m['precision']:.3f}", f"{m['recall']:.3f}", f"{m['f1']:.3f}"]
    _table(s, [["Predictor","n","Acc","Prec","Recall","F1"],
               row("Heuristic rules", v["heuristic"]), row("Previous d413d74", v["old"]),
               row("Combined final", v["new"]), row("Final · day", v["new_day"]),
               row("Final · night", v["new_night"]), row("Final · 20 test dates", v["new_held_dates"])],
          0.55, 5.2, [3.3, 1.3, 1.5, 1.5, 1.5, 1.5], row_h=0.26)

def s08_daynight(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Day is the operational win — night is still the gap", "111-photo split: 55 day / 56 night.")
    picture(s, A / "update_acc.png", Inches(0.4), Inches(1.5), w=Inches(7.5))
    card(s, Inches(8.05), Inches(1.55), Inches(4.75), Inches(5.15))
    tf = textbox(s, Inches(8.3), Inches(1.75), Inches(4.3), Inches(4.85))
    para(tf, "What changed", size=16, color=T.NAVY, bold=True, first=True, space_after=8)
    para(tf, f"Day {_pct(v['old_day']['acc'])} → {_pct(v['new_day']['acc'])}.", size=14, bullet=True, space_after=7)
    para(tf, f"Night {_pct(v['old_night']['acc'])} → {_pct(v['new_night']['acc'])} (precision {v['new_night']['precision']:.2f}).", size=14, bullet=True, space_after=7)
    para(tf, f"111 overall {_pct(v['old']['acc'])} → {_pct(v['new']['acc'])} vs rules {_pct(v['heuristic']['acc'])}.", size=14, bullet=True, space_after=7)
    para(tf, f"20 held-out dates: {_pct(v['new_held_dates']['acc'])} vs d413d74 {_pct(v['old_held_dates']['acc'])}.", size=14, bullet=True, space_after=10)
    para(tf, "Night faint-light false alarms remain the process debt.", size=13, color=T.SKY, bold=True)

def s09_errors(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Where it still fails — and what to change", "Minutes plus visual overrides lifted day. Night precision is still the debt.")
    blocks = [
        (T.CARD_GREEN, "What improved", [
            f"111-photo {_pct(v['old']['acc'])} → {_pct(v['new']['acc'])} vs rules {_pct(v['heuristic']['acc'])}",
            f"Recall {v['new']['recall']:.2f} — one missed inside-frame vs 3 / 16",
            f"Day {_pct(v['new_day']['acc'])} · night {_pct(v['new_night']['acc'])}",
            f"Golden-all 2016 {_pct(r['golden_all_142']['old']['acc'])} → {_pct(r['golden_all_142']['new']['acc'])}",
        ]),
        (T.CARD_SKY, "What did not", [
            f"Night precision still {v['new_night']['precision']:.2f}",
            "20 held-out 111 dates: 75% — small n",
            "USB minutes die 22 Apr — no May–Dec 1-minute coverage",
            "Heuristic seed still dominates most train labels",
        ]),
    ]
    x = 0.55
    for fill, title, items in blocks:
        card(s, Inches(x), Inches(1.55), Inches(6.05), Inches(3.55), fill=fill)
        tf = textbox(s, Inches(x + 0.28), Inches(1.75), Inches(5.5), Inches(3.2))
        para(tf, title, size=16, color=T.NAVY, bold=True, first=True, space_after=8)
        for it in items:
            para(tf, it, size=13.5, bullet=True, space_after=6)
        x += 6.25
    card(s, Inches(0.55), Inches(5.25), Inches(12.25), Inches(1.6))
    tf = textbox(s, Inches(0.85), Inches(5.4), Inches(11.7), Inches(1.35))
    para(tf, "Next process steps (in order)", size=15, color=T.NAVY, bold=True, first=True, space_after=4)
    para(tf, "1. Hold the 111 fully out of the next fit.   2. Re-label night + borderline fog at full resolution.   3. If another USB year appears, extract it — keep date-balance.", size=13)

def s10_summary(prs, r):
    s = _blank(prs)
    h, v = r["holdout"], r["review_111"]
    add_title(s, "Takeaways for this update")
    cards = [
        ("Shipped", "combined final", "Same JSON in models/ and docs/. Live Pages + Flask + CLI."),
        ("Train rows", f"{_n(r):,}", "Unique frames. Human overrides heuristic. Date-balanced."),
        ("Holdout", _pct(h["test"]["acc"]), f"{h['test']['n']:,} unseen-date rows. Tied with d413d74."),
        ("111 visual", _pct(v["new"]["acc"]), f"Day {_pct(v['new_day']['acc'])} · night {_pct(v['new_night']['acc'])}."),
    ]
    x = 0.55
    for title, big, sub in cards:
        card(s, Inches(x), Inches(1.55), Inches(3.0), Inches(2.35), fill=T.CARD_SKY)
        tf = textbox(s, Inches(x + 0.2), Inches(1.7), Inches(2.6), Inches(2.05))
        para(tf, title, size=13, color=T.MUTED, first=True, space_after=4)
        para(tf, big, size=22, color=T.NAVY, bold=True, space_after=6)
        para(tf, sub, size=12, color=T.INK)
        x += 3.2
    card(s, Inches(0.55), Inches(4.1), Inches(12.25), Inches(2.7), fill=T.CARD_GREEN)
    tf = textbox(s, Inches(0.9), Inches(4.3), Inches(11.6), Inches(2.4))
    para(tf, "One-sentence process update", size=16, color=T.NAVY, bold=True, first=True, space_after=8)
    para(tf, "Every unique labeled KFB frame is now in the model, weighted so a January minute does not count more than a November hour, and so 253 human rows still speak. Unseen dates score 97.8% against seed labels and 86.5% against visual photos. Night labeling is still the next process.", size=16)
    tf2 = textbox(s, Inches(0.9), Inches(6.45), Inches(11.6), Inches(0.4))
    para(tf2, "One photo, one answer: is the cloud base above or below 150 metres?", size=14, color=T.MUTED, first=True, align=PP_ALIGN.CENTER)

BUILDERS = [s01_cover, s02_why, s03_process, s04_photos, s05_grids, s06_holdout, s07_visual, s08_daynight, s09_errors, s10_summary]

def build_slides(prs) -> None:
    r = _report()
    for i, fn in enumerate(BUILDERS, start=1):
        fn(prs, r)
        if i > 1:
            footer(prs.slides[-1], i, TOTAL)
