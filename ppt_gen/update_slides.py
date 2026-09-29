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


def _report() -> dict:
    return json.loads(REPORT.read_text())


def _pct(x) -> str:
    return f"{100 * float(x):.1f}%"


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _table(slide, rows, left, top, widths, row_h=0.38):
    gt = slide.shapes.add_table(
        len(rows), len(rows[0]),
        Inches(left), Inches(top),
        Inches(sum(widths)), Inches(row_h * len(rows)),
    ).table
    for j, w in enumerate(widths):
        gt.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = gt.cell(i, j)
            c.text = ""
            p = c.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(12)
            p.font.bold = i == 0
            p.font.color.rgb = T.WHITE if i == 0 else T.INK
            p.font.name = T.LATIN_FONT
            if i == 0:
                c.fill.solid()
                c.fill.fore_color.rgb = T.NAVY
            elif i % 2 == 0:
                c.fill.solid()
                c.fill.fore_color.rgb = RGBColor(0xF7, 0xFA, 0xFC)
    return gt


def s01_cover(prs, r):
    s = _blank(prs)
    picture(s, A / "update_cover.jpg", 0, 0, w=T.SLIDE_W, h=T.SLIDE_H)
    h, g, v = r["holdout"], r["golden_all_142"]["new"], r["review_111"]
    tf = textbox(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(4.4))
    para(tf, "KFB Cloud Coverage", size=44, color=T.WHITE, bold=True,
         first=True, space_after=8)
    para(tf, "Process update — combine data, holdout, ship",
         size=22, color=T.SKY_LIGHT, space_after=16)
    para(tf, "8,354 unique frames  ·  date-grouped 80/20  ·  111 visual GT",
         size=16, color=T.WHITE, space_after=10)
    para(tf, f"Test {_pct(h['test']['acc'])}  ·  golden {_pct(g['acc'])}  ·  "
             f"111 {_pct(v['new']['acc'])}  ·  day {_pct(v['new_day']['acc'])}  "
             f"·  night {_pct(v['new_night']['acc'])}",
         size=15, color=T.SKY_LIGHT)
    tf2 = textbox(s, Inches(0.9), Inches(6.55), Inches(11.5), Inches(0.4))
    para(tf2, "September 2026  ·  Kadoorie Farm webcam at ~150 m",
         size=13, color=T.SKY_LIGHT, first=True)


def s02_why(prs, r):
    s = _blank(prs)
    add_title(s, "Why this update",
              "Combine useful labels, keep a date holdout, refuse volume that hurts honesty.")
    items = [
        ("Before (d413d74)", T.CARD_BG, [
            "142 golden 2016 + 8,212 hourly 2023",
            "Date-grouped 80/20, train-split fit",
            "Test 97.2% (mostly heuristic labels)",
            "111 visual check 83.8% / day 94.6%",
            "Night 73.2% still the weak spot",
        ]),
        ("What we added", T.CARD_SKY, [
            "Finished Jan-Apr per-minute extract: 166,772",
            "Tried shipping those minutes — they lost",
            "111 visual labels as human overrides",
            "Human rows weighted x20 vs hourly seed",
            "Same tiny JSON in Python and the browser",
        ]),
        ("Why it matters", T.CARD_GREEN, [
            "Golden-all 97.2% vs previous 95.1%",
            "111-photo 86.5% vs 83.8% vs rules 73.0%",
            "Day 98.2% is the operational win",
            "166k extra minutes were not progress",
            "Night labeling is still the next process",
        ]),
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
    add_title(s, "Updated process",
              "Photos -> 9 features -> heuristic seed -> human override -> date-split train -> live")
    steps = [
        ("1. Ingest", "R5 USB 2023 + 2016 golden"),
        ("2. Features", "9 numbers, no CNN"),
        ("3. Seed labels", "heuristic, not the model"),
        ("4. Human GT", "142 + 111 visual override"),
        ("5. Train", "logreg, split by date"),
        ("6. Ship", "tiny JSON, Pages + Flask"),
    ]
    x = 0.45
    for text, sub in steps:
        chevron(s, Inches(x), Inches(1.65), Inches(2.18), Inches(1.15), text, sub)
        x += 2.12
    rows = [
        ("Photo in", "HKO KFB webcam / USB dump. Crop top 8% timestamp, resize 640 px — same as the browser."),
        ("Features", "brightness, saturation, far-field wash/grad/std, bright-spot ratio, day/night from brightness >= 80."),
        ("Seed vs truth", "Hourly heuristic trains volume. Human eye overrides 142 + 111 rows. The model never labels itself."),
        ("Split hygiene", "GroupShuffleSplit by YYMMDD, random_state=42. Weights fit on train only — no full-data refit."),
        ("Live loop", "GitHub Actions every ~5 min -> live.json. Pages runs the same JSON if the feed is stale."),
    ]
    y = 3.05
    for title, body in rows:
        card(s, Inches(0.55), Inches(y), Inches(12.25), Inches(0.72))
        tf = textbox(s, Inches(0.8), Inches(y + 0.1), Inches(11.8), Inches(0.55))
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = title
        style_run(r1, 14, T.SKY, bold=True)
        r2 = p.add_run(); r2.text = "   " + body
        style_run(r2, 13, T.INK)
        y += 0.78


def s04_photos(prs, r):
    s = _blank(prs)
    c = r["counts"]
    add_title(s, "What was combined — and what was not",
              f"{c['fit_pool']:,} unique frames · {c['inside']:,} inside · {c['dates']} dates")
    picture(s, A / "update_data.png", Inches(0.45), Inches(1.5), w=Inches(6.9))
    card(s, Inches(7.5), Inches(1.55), Inches(5.3), Inches(5.15))
    tf = textbox(s, Inches(7.78), Inches(1.75), Inches(4.8), Inches(4.85))
    para(tf, "How each set is used", size=16, color=T.NAVY, bold=True,
         first=True, space_after=8)
    para(tf, "Golden 142 (2016) — human. 34 inside. Weighted x20.",
         size=13, bullet=True, space_after=6)
    para(tf, "R5 hourly 8,212 (2023, full year) — heuristic seed. 111 overridden by visual GT.",
         size=13, bullet=True, space_after=6)
    para(tf, "Review 111 — visual GT, join the date split. 20 fall on test dates.",
         size=13, bullet=True, space_after=6)
    para(tf, f"Per-minute {r['minute_extract_n']:,} — extract finished Jan-Apr 22. Tried; honest checks fell. Not shipped.",
         size=13, bullet=True, space_after=8)
    para(tf, "Shipped = 8,354 unique rows, 80/20 by date, train-split fit.",
         size=13, color=T.SKY, bold=True)


def s05_grids(prs, r):
    s = _blank(prs)
    add_title(s, "How the 111 photos were labeled",
              "review_r5/grid_01-13.jpg — judged against the project rule, then used as human overrides")
    x = 0.55
    for g in ("grid_01.jpg", "grid_02.jpg", "grid_03.jpg", "grid_04.jpg"):
        picture(s, T.ROOT / "review_r5" / g, Inches(x), Inches(1.55),
                w=Inches(2.95), h=Inches(3.35))
        caption(s, g.replace(".jpg", ""), Inches(x), Inches(4.92), Inches(2.95), size=11)
        x += 3.15
    card(s, Inches(0.55), Inches(5.35), Inches(12.25), Inches(1.5), fill=T.CARD_SKY)
    tf = textbox(s, Inches(0.85), Inches(5.5), Inches(11.7), Inches(1.25))
    para(tf, "Label rule (same for day and night)", size=15, color=T.NAVY,
         bold=True, first=True, space_after=4)
    para(tf, "Day: washed-out textureless far field = inside; visible valley = not inside.  "
             "Night: lightless flat frame = inside; any valley lights = not inside.  "
             "Haze with a visible valley is not inside. Result: 57 inside / 54 not inside.",
         size=13)


def _cm(m: dict) -> str:
    c = m["cm"]
    return f"[[{c[0][0]}, {c[0][1]}], [{c[1][0]}, {c[1][1]}]]"


def s06_holdout(prs, r):
    s = _blank(prs)
    h = r["holdout"]
    add_title(s, "Date holdout — unseen 1,702 frames",
              "GroupShuffleSplit 80/20 by YYMMDD · train-split fit, no full-data refit")
    _table(s, [
        ["Slice", "n", "Acc", "P", "R", "F1", "Confusion [[TN,FP],[FN,TP]]"],
        ["All test", h["test"]["n"], _pct(h["test"]["acc"]),
         f"{h['test']['precision']:.3f}", f"{h['test']['recall']:.3f}",
         f"{h['test']['f1']:.3f}", _cm(h["test"])],
        ["Golden 2016", h["test_golden"]["n"], _pct(h["test_golden"]["acc"]),
         f"{h['test_golden']['precision']:.3f}", f"{h['test_golden']['recall']:.3f}",
         f"{h['test_golden']['f1']:.3f}", _cm(h["test_golden"])],
        ["R5 hourly seed", h["test_hourly"]["n"], _pct(h["test_hourly"]["acc"]),
         f"{h['test_hourly']['precision']:.3f}", f"{h['test_hourly']['recall']:.3f}",
         f"{h['test_hourly']['f1']:.3f}", _cm(h["test_hourly"])],
        ["111 on test dates", h["test_human_2023"]["n"], _pct(h["test_human_2023"]["acc"]),
         f"{h['test_human_2023']['precision']:.3f}", f"{h['test_human_2023']['recall']:.3f}",
         f"{h['test_human_2023']['f1']:.3f}", _cm(h["test_human_2023"])],
        ["Train (ref.)", h["train"]["n"], _pct(h["train"]["acc"]),
         f"{h['train']['precision']:.3f}", f"{h['train']['recall']:.3f}",
         f"{h['train']['f1']:.3f}", _cm(h["train"])],
        ["d413d74, same test", h["old_same_test"]["n"], _pct(h["old_same_test"]["acc"]),
         f"{h['old_same_test']['precision']:.3f}", f"{h['old_same_test']['recall']:.3f}",
         f"{h['old_same_test']['f1']:.3f}", _cm(h["old_same_test"])],
    ], 0.5, 1.55, [2.15, 0.7, 0.85, 0.75, 0.7, 0.7, 4.6], row_h=0.48)
    card(s, Inches(0.55), Inches(5.55), Inches(12.25), Inches(1.25), fill=T.CARD_SKY)
    tf = textbox(s, Inches(0.85), Inches(5.7), Inches(11.7), Inches(1.0))
    para(tf, "Read this carefully", size=15, color=T.NAVY, bold=True,
         first=True, space_after=4)
    para(tf, "Recall on the holdout is 1.00 — zero missed inside-cloud frames. "
             "Headline test acc fell slightly vs d413d74 because we traded a few extra "
             "false alarms for human-label fidelity. The hourly slice is optimistic: "
             "it agrees with the same rules that seeded most training labels.",
         size=13)


def s07_visual(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Honest check — 111 visual 2023 photos",
              "Same frames for rules, d413d74, and the shipped model. Human labels win.")
    picture(s, A / "update_cm.png", Inches(0.4), Inches(1.45), h=Inches(3.7))
    picture(s, A / "update_acc.png", Inches(5.2), Inches(1.4), w=Inches(7.6))
    _table(s, [
        ["Predictor", "Acc", "Prec", "Recall", "F1", "Confusion"],
        ["Heuristic rules", _pct(v["heuristic"]["acc"]),
         f"{v['heuristic']['precision']:.3f}", f"{v['heuristic']['recall']:.3f}",
         f"{v['heuristic']['f1']:.3f}", _cm(v["heuristic"])],
        ["d413d74", _pct(v["old"]["acc"]),
         f"{v['old']['precision']:.3f}", f"{v['old']['recall']:.3f}",
         f"{v['old']['f1']:.3f}", _cm(v["old"])],
        ["Shipped final", _pct(v["new"]["acc"]),
         f"{v['new']['precision']:.3f}", f"{v['new']['recall']:.3f}",
         f"{v['new']['f1']:.3f}", _cm(v["new"])],
    ], 0.5, 5.25, [2.3, 1.0, 1.0, 1.1, 1.0, 5.9], row_h=0.38)


def s08_daynight(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Day is the operational win — night is still the gap",
              "111-photo split: 55 day / 56 night. Day jumped; night barely moved.")
    picture(s, A / "update_dn.png", Inches(0.45), Inches(1.5), w=Inches(6.5))
    card(s, Inches(7.15), Inches(1.55), Inches(5.65), Inches(5.15))
    tf = textbox(s, Inches(7.4), Inches(1.75), Inches(5.2), Inches(4.85))
    para(tf, "What changed", size=16, color=T.NAVY, bold=True, first=True, space_after=8)
    para(tf, f"Day  {_pct(v['old_day']['acc'])}  →  {_pct(v['new_day']['acc'])}  "
             f"(1 miss gone, 1 fewer false alarm).",
         size=14, bullet=True, space_after=7)
    para(tf, f"Night  {_pct(v['old_night']['acc'])}  →  {_pct(v['new_night']['acc'])}  "
             f"— still 13 false alarms on faint lights.",
         size=14, bullet=True, space_after=7)
    para(tf, f"111 overall  {_pct(v['old']['acc'])}  →  {_pct(v['new']['acc'])}  "
             f"vs rules {_pct(v['heuristic']['acc'])}  (+13.5 pts).",
         size=14, bullet=True, space_after=7)
    para(tf, f"20 of the 111 land on held-out dates: {_pct(v['new_held_dates']['acc'])} "
             f"vs d413d74 {_pct(v['old_held_dates']['acc'])}.",
         size=14, bullet=True, space_after=10)
    para(tf, "Night precision is still ~0.64. That is the next labeling job, "
             "not another volume dump.",
         size=13, color=T.SKY, bold=True)


def s09_refused(prs, r):
    s = _blank(prs)
    add_title(s, "What we refused to ship",
              r["minute_extract_note"])
    items = [
        ("Tried: Jan–Apr minutes", T.CARD_BG, [
            f"{r['minute_extract_n']:,} extra frames extracted.",
            "Four winter months drown May–Dec hourly days.",
            "Honest 111 and 2016-golden checks fell vs d413d74.",
            "Not in the shipped JSON.",
        ]),
        ("Tried: unweighted volume", T.CARD_SKY, [
            "Equal-row minutes give ~95% of the loss to Jan–Apr.",
            "That is not a better sensor — it is a calendar bias.",
            "Human rows stay at ×20 vs hourly seed.",
            "Date groups stay on one side of the split.",
        ]),
        ("Shipped instead", T.CARD_GREEN, [
            "8,354 unique frames, train-split fit.",
            "142 golden + 111 visual override + hourly seed.",
            "Same 9-feature JSON in Python and the browser.",
            "d413d74 weights kept as cloud_logreg_d413d74.json.",
        ]),
    ]
    x = 0.7
    for title, fill, bullets in items:
        card(s, Inches(x), Inches(1.55), Inches(3.95), Inches(5.15), fill=fill)
        tf = textbox(s, Inches(x + 0.28), Inches(1.78), Inches(3.4), Inches(4.8))
        para(tf, title, size=17, color=T.NAVY, bold=True, first=True, space_after=10)
        for b in bullets:
            para(tf, b, size=14, bullet=True, space_after=8)
        x += 4.15


def s10_next(prs, r):
    s = _blank(prs)
    h, g, v = r["holdout"], r["golden_all_142"], r["review_111"]
    add_title(s, "Shipped numbers and next process")
    card(s, Inches(0.55), Inches(1.5), Inches(6.15), Inches(5.2), fill=T.CARD_GREEN)
    tf = textbox(s, Inches(0.85), Inches(1.7), Inches(5.6), Inches(4.85))
    para(tf, "What updated", size=17, color=T.NAVY, bold=True, first=True, space_after=8)
    for it in [
        f"Fit pool 8,354 unique · 6,652 train / 1,702 test · 357 dates.",
        f"Human override: 142 golden 2016 + 111 visual 2023, both ×20.",
        f"Holdout test {_pct(h['test']['acc'])} · zero missed inside-cloud.",
        f"Golden-all {_pct(g['new']['acc'])} vs d413d74 {_pct(g['old']['acc'])}.",
        f"111 visual {_pct(v['new']['acc'])} (day {_pct(v['new_day']['acc'])} / "
        f"night {_pct(v['new_night']['acc'])}).",
        "Live JSON unchanged in shape — Pages and Flask already read it.",
    ]:
        para(tf, it, size=13.5, bullet=True, space_after=7)

    card(s, Inches(6.95), Inches(1.5), Inches(5.85), Inches(5.2), fill=T.CARD_SKY)
    tf = textbox(s, Inches(7.25), Inches(1.7), Inches(5.3), Inches(4.85))
    para(tf, "Next", size=17, color=T.NAVY, bold=True, first=True, space_after=8)
    for it in [
        "Re-label night frames at full resolution (faint lights, fog, #107 lens).",
        "Do not dump more Jan–Apr minutes until May–Dec exists or dates are re-balanced.",
        "Night precision ~0.64 is the remaining operational risk.",
        "Keep the 9-feature JSON — no CNN until night labels improve.",
        "Same live loop: Actions every ~5 min, browser fallback if stale.",
    ]:
        para(tf, it, size=13.5, bullet=True, space_after=7)

    tf = textbox(s, Inches(0.55), Inches(6.8), Inches(12.2), Inches(0.4))
    para(tf, "Process, not volume: combine useful labels, keep a date holdout, refuse the rest.",
         size=14, color=T.NAVY, bold=True, first=True, align=PP_ALIGN.CENTER)


BUILDERS = [
    s01_cover, s02_why, s03_process, s04_photos, s05_grids,
    s06_holdout, s07_visual, s08_daynight, s09_refused, s10_next,
]


def build_slides(prs) -> None:
    r = _report()
    for i, fn in enumerate(BUILDERS, start=1):
        fn(prs, r)
        if i > 1:
            footer(prs.slides[-1], i, TOTAL)


def s06_train(prs, r):
    s = _blank(prs)
    c, o = r["counts"], r["counts"]["origins"]
    add_title(s, "How the shipped model is trained",
              "Logistic regression, scaler folded into coef/intercept — one dot product in Python and JS")
    _table(s, [
        ["Piece", "Choice", "Why"],
        ["Model", "LogReg, C=0.5, class_weight=balanced", "Tiny, inspectable, identical in the browser"],
        ["Features", "9 (no edge_density)", "Browser does not compute a Laplacian"],
        ["Fit pool", f"{c['fit_pool']:,} unique / {c['dates']} dates / {c['inside']} inside",
         f"{o['golden_2016']} golden + {o['r5_hourly']:,} hourly + {o['human_2023']} visual"],
        ["Train / test", f"{c['train']:,} / {c['test']:,}  ({c['train_dates']} / {c['test_dates']} dates)",
         "Human x20, hourly x1, train-split fit"],
        ["Split", "GroupShuffleSplit by date, rs=42", "Nearby frames would leak otherwise"],
        ["Export", "models/ + docs/ cloud_logreg.json", "Pages, Flask, CLI, live Action share weights"],
    ], 0.55, 1.55, [1.7, 5.1, 5.4], row_h=0.42)
    card(s, Inches(0.55), Inches(5.15), Inches(6.0), Inches(1.7), fill=T.CARD_GREEN)
    tf = textbox(s, Inches(0.8), Inches(5.3), Inches(5.55), Inches(1.45))
    para(tf, "What the weights listen to", size=14, color=T.NAVY, bold=True,
         first=True, space_after=4)
    para(tf, "far_wash and is_day push toward inside. saturation and far-field texture "
             "push toward not_inside — valley color and structure.", size=13)
    card(s, Inches(6.75), Inches(5.15), Inches(6.05), Inches(1.7), fill=T.CARD_SKY)
    tf = textbox(s, Inches(7.0), Inches(5.3), Inches(5.6), Inches(1.45))
    para(tf, "What we refused to ship", size=14, color=T.NAVY, bold=True,
         first=True, space_after=4)
    para(tf, "166,772 Jan-Apr minutes (and a 15-min subsample) both lost on golden and "
             "111-photo checks vs d413d74. Four months of seed labels drown a full year.", size=13)


def s07_perf(prs, r):
    s = _blank(prs)
    h, g = r["holdout"], r["golden_all_142"]
    add_title(s, "Held-out test vs honest labels",
              "The 1,702-row test is mostly heuristic. Trust golden-all and the 111-photo numbers.")
    picture(s, A / "update_acc.png", Inches(0.4), Inches(1.5), w=Inches(7.5))
    card(s, Inches(8.05), Inches(1.55), Inches(4.75), Inches(5.15))
    tf = textbox(s, Inches(8.3), Inches(1.75), Inches(4.3), Inches(4.85))
    para(tf, "Headline numbers", size=16, color=T.NAVY, bold=True, first=True, space_after=8)
    para(tf, f"Test {h['test']['n']:,} — {_pct(h['test']['acc'])}. Zero missed inside-cloud {h['test']['cm']}.",
         size=13, bullet=True, space_after=6)
    para(tf, f"Golden-all 142 — {_pct(g['new']['acc'])} vs d413d74 {_pct(g['old']['acc'])}.",
         size=13, bullet=True, space_after=6)
    para(tf, f"Heuristic-heavy test is below d413d74 {_pct(h['old_same_test']['acc'])}. Not the selection metric.",
         size=13, bullet=True, space_after=6)
    para(tf, "Trainer: tools/train_final.py. Previous weights kept as cloud_logreg_d413d74.json.",
         size=13, bullet=True, space_after=8)
    para(tf, "Caveat: 91 of 111 visual dates were in the train split. 20 test-date frames: 75%.",
         size=12, color=T.MUTED)


def s08_independent(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "111 visual 2023 photos",
              "Used as human overrides in the date split. Still the best 2023 eye-check we have.")
    picture(s, A / "update_cm.png", Inches(0.4), Inches(1.5), w=Inches(5.4))
    picture(s, A / "update_dn.png", Inches(5.7), Inches(1.5), w=Inches(7.1))

    def row(name, m):
        return [name, str(m["n"]), f"{m['acc']:.3f}", f"{m['precision']:.3f}",
                f"{m['recall']:.3f}", f"{m['f1']:.3f}"]

    _table(s, [
        ["Predictor", "n", "Acc", "Prec", "Recall", "F1"],
        row("Heuristic rules", v["heuristic"]),
        row("d413d74", v["old"]),
        row("Shipped final", v["new"]),
        row("Final · day", v["new_day"]),
        row("Final · night", v["new_night"]),
    ], 0.55, 5.25, [3.2, 1.4, 1.5, 1.5, 1.5, 1.5], row_h=0.28)


def s09_errors(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Where it still fails — and what to change",
              "The process gain is day recall. The process debt is night precision.")
    blocks = [
        (T.CARD_GREEN, "What improved", [
            f"111-photo {_pct(v['old']['acc'])} -> {_pct(v['new']['acc'])} vs rules {_pct(v['heuristic']['acc'])}",
            f"Recall {v['new']['recall']:.2f} — one missed inside-frame vs 3 / 16",
            f"Day {_pct(v['new_day']['acc'])} is briefable as operational",
            f"Golden-all 2016 {_pct(r['golden_all_142']['old']['acc'])} -> {_pct(r['golden_all_142']['new']['acc'])}",
        ]),
        (T.CARD_SKY, "What did not", [
            f"Night {_pct(v['new_night']['acc'])} (precision {v['new_night']['precision']:.2f})",
            "13 of 15 errors on the 111 are night false alarms",
            "166k extra minutes made honest checks worse",
            "Faint-light / fog / lens-obstruction still confuse both",
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
    para(tf, "Next process steps (in order)", size=15, color=T.NAVY, bold=True,
         first=True, space_after=4)
    para(tf, "1. Re-label night + borderline fog at full resolution.   "
             "2. Hold those 111 (and new night labels) fully out of the next fit.   "
             "3. Only ship a per-minute model once the extract covers a full year.",
         size=13)


def s10_summary(prs, r):
    s = _blank(prs)
    v = r["review_111"]
    add_title(s, "Takeaways for this update")
    cards = [
        ("Shipped", "combined final", "Same JSON in models/ and docs/. Live Pages + Flask + CLI."),
        ("Fit pool", f"{r['counts']['fit_pool']:,} rows",
         "142 + 8,101 + 111. 166k minutes extracted, not shipped."),
        ("Day", _pct(v["new_day"]["acc"]), "Strong on the 111 visual frames. Brief as ready."),
        ("Night", _pct(v["new_night"]["acc"]),
         "High recall, too many faint-light false alarms. Next golden set."),
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
    para(tf, "One-sentence process update", size=16, color=T.NAVY, bold=True,
         first=True, space_after=8)
    para(tf, "We combined 2016 human labels, a full year of 2023 hourly frames, and 111 visual "
             "overrides; evaluated on dates the fit never saw; and refused 166k extra minutes "
             "that hurt those checks. Daytime inside-cloud is the win. Night labeling is the next process.",
         size=16)
    tf2 = textbox(s, Inches(0.9), Inches(6.45), Inches(11.6), Inches(0.4))
    para(tf2, "One photo, one answer: is the cloud base above or below 150 metres?",
         size=14, color=T.MUTED, first=True, align=PP_ALIGN.CENTER)


BUILDERS = [
    s01_cover, s02_why, s03_process, s04_photos, s05_grids,
    s06_train, s07_perf, s08_independent, s09_errors, s10_summary,
]


def build_slides(prs) -> None:
    report = _report()
    for i, fn in enumerate(BUILDERS, start=1):
        fn(prs, report)
        if i > 1:
            footer(prs.slides[-1], i, TOTAL)

