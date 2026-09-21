#!/usr/bin/env python3
"""Phase A machine-readable v4 failure analysis (deterministic; no input).

Pulls the exact numbers from the replay artifacts written earlier in this
wave and emits attempt-01/v4-failure-analysis.json.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
OUT = os.path.join(HERE, os.pardir, "attempt-01", "v4-failure-analysis.json")


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def sha(rel):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, rel), "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


frames = ["a08r1", "a08r2", "a09"]
dom = load("evidence/20260921-replan-v6/replay/row-domain-recompute.json")
v6 = {n: load("evidence/20260921-replan-v6/replay/%s-v6.json" % n) for n in frames}

inputs = {
    "attempt-08/album-card-locate.json": "evidence/20260916-route/attempt-08/album-card-locate.json",
    "attempt-08/album-card-locate-r2.json": "evidence/20260916-route/attempt-08/album-card-locate-r2.json",
    "attempt-08/run-ledger.json": "evidence/20260916-route/attempt-08/run-ledger.json",
    "attempt-08/frame-pre.png": "evidence/20260916-route/attempt-08/frame-pre.png",
    "attempt-08/frame-pre-r2.png": "evidence/20260916-route/attempt-08/frame-pre-r2.png",
    "attempt-09/frame-pre.png": "evidence/20260916-route/attempt-09/frame-pre.png",
    "attempt-09/album-card-locate.json": "evidence/20260916-route/attempt-09/album-card-locate.json",
    "attempt-09/s1-s2-observation.json": "evidence/20260916-route/attempt-09/s1-s2-observation.json",
    "attempt-09/s3-comparison-attempt08.json": "evidence/20260916-route/attempt-09/s3-comparison-attempt08.json",
    "attempt-09/run-ledger.json": "evidence/20260916-route/attempt-09/run-ledger.json",
    "attempt-07/album-card-locate.json": "evidence/20260916-route/attempt-07/album-card-locate.json",
    "attempt-07/screen-probe.json": "evidence/20260916-route/attempt-07/screen-probe.json",
    "tools/v4/locate_album_card.py": "evidence/20260916-route/tools/v4/locate_album_card.py",
    "tools/v4/vision_reader.py": "evidence/20260916-route/tools/v4/vision_reader.py",
}
replay_inputs = {
    "v4-replay/a08r1.json": "evidence/20260921-replan-v6/replay/v4-replay/a08r1.json",
    "v4-replay/a08r2.json": "evidence/20260921-replan-v6/replay/v4-replay/a08r2.json",
    "v4-replay/a09.json": "evidence/20260921-replan-v6/replay/v4-replay/a09.json",
    "geometry/a08r1.json": "evidence/20260921-replan-v6/replay/geometry/a08r1.json",
    "geometry/a08r2.json": "evidence/20260921-replan-v6/replay/geometry/a08r2.json",
    "geometry/a09.json": "evidence/20260921-replan-v6/replay/geometry/a09.json",
    "row-domain-recompute.json": "evidence/20260921-replan-v6/replay/row-domain-recompute.json",
    "v6-replay/a08r1-v6.json": "evidence/20260921-replan-v6/replay/a08r1-v6.json",
    "v6-replay/a08r2-v6.json": "evidence/20260921-replan-v6/replay/a08r2-v6.json",
    "v6-replay/a09-v6.json": "evidence/20260921-replan-v6/replay/a09-v6.json",
}

result = {
    "schema": "v6-phaseA-v4-failure-analysis/1",
    "task": {"group": "旻謙允禎成長日記", "album": "2024/05/13～05/17", "expected_count": 57},
    "gui_input_count": 0,
    "statement": ("Frozen v4's band/margin rule is evaluated on the mean of the ENTIRE "
                  "screenshot row. On full-screen frames where the LINE window occupies "
                  "≈28.5 % of the row width, no window-local brightness can lift that "
                  "mean to the frozen bright=100 threshold below the title, so v4 returns "
                  "UNSAFE_MARGINS with band_bottom_bright_row=null / margin_below_px=null "
                  "in three distinct arrangements - a spatial-domain mismatch, not a "
                  "screen-placement defect."),
    "v4_mechanism_observed": {
        "source": "evidence/20260916-route/tools/v4/locate_album_card.py",
        "source_sha256": sha("evidence/20260916-route/tools/v4/locate_album_card.py"),
        "title": {
            "how": "OCR (macOS Vision via frozen vision_reader, scale 3) -> find_title(): "
                   "concatenates digit runs of up to 4 consecutive words; keeps spans whose "
                   "digits contain '20240513' and then '20240517' or its last 4 digits "
                   "'0517'; picks the minimal span; bbox = union of the selected words' "
                   "boxes (full-frame pixel coordinates).",
            "lines": "locate_album_card.py L68-L88 (find_title), L150-L151 (call)",
        },
        "count": {
            "how": "crop box (x0-8, y1+2, x0+160, y1+32) from the title bbox; OCR at "
                   "scale 10; digits concatenated; MATCH iff '57' occurs; MISMATCH "
                   "refuses (exit 5); UNREADABLE does not refuse.",
            "lines": "L118-L124 (ocr_digits_region), L175-L186 (call + verdict)",
        },
        "band_top_bright_row": {
            "how": "scan y upward from title y0-1 to 0; first y with row_mean(y) >= 100; "
                   "null if none.",
            "lines": "L104-L112 (bright_band_edges top loop), L169",
        },
        "band_bottom_bright_row": {
            "how": "scan y downward from title y1+1 to height-1; first y with "
                   "row_mean(y) >= 100; null if none.",
            "lines": "L104-L112 (bottom loop), L169",
        },
        "row_mean_spatial_domain": {
            "how": "row_mean(im, y) = (sum over x in range(im.size[0]) of pixel_gray(x, y)) "
                   "/ im.size[0]; the domain is ALL x of the image passed to the tool. In "
                   "attempt-08/09 that image is the full-screen capture (2294x1490 px), so "
                   "the domain is the full screenshot row, NOT the LINE window and NOT the "
                   "album card.",
            "lines": "L96-L101",
            "measured_window_width_share": 0.2851,
            "max_possible_window_contribution_if_row_were_white": round(0.2851 * 255, 1),
        },
        "bright_threshold": 100,
        "margin_definitions": {"margin_above_px": "center_y - band_top", "margin_below_px":
                               "band_bottom - center_y"},
        "unsafe_margins_boolean_condition": ("click_point is None or margin_above_px is "
                                             "None or margin_below_px is None or "
                                             "margin_above_px < 10 or margin_below_px < 10"),
        "click_point_derivation": ("click_point = [x0+12, (y0+y1)//2] iff "
                                   "0 <= x0+12 <= width-20 and x0+12 <= x1+40; null "
                                   "otherwise (frozen v4 rule, unchanged in v6)"),
        "unsafe_margins_lines": "L196-L198",
    },
    "replay": {
        "command": "/opt/homebrew/bin/python3 evidence/20260916-route/tools/v4/"
                   "locate_album_card.py <frame> --expect-start 2024/05/13 "
                   "--expect-end 2024/05/17 --expect-count 57 --out <out>",
        "determinism": "two independent replays of the same frame are byte-identical "
                       "except reader.helper.binary_sha256 (locally rebuilt Vision helper "
                       "binary); the frozen attempt-09 output is byte-identical to the "
                       "replay including the helper hash",
        "frozen_vs_replay": {
            "a08r1": "identical to attempts evidence except helper binary hash",
            "a08r2": "identical to attempts evidence except helper binary hash",
            "a09": "byte-identical to the frozen attempts evidence",
        },
        "per_frame": {},
    },
    "inputs_sha256": {k: sha(v) for k, v in inputs.items()},
    "replay_sha256": {k: sha(v) for k, v in replay_inputs.items()},
    "attempt07": {
        "recorded": load("evidence/20260916-route/attempt-07/album-card-locate.json"),
        "frame_preserved": False,
        "note": "attempt-07's analysed frame (/tmp/route7_frame_pre.jpg, sha 2897628770dd) "
                "no longer exists on disk; its window-local recomputation is impossible and "
                "is not fabricated. Even there the full-row >=100 row below the title "
                "cannot be produced by the LINE window alone at 28.5 % width; whether that "
                "row was the card's real grid boundary or a composite of unrelated bright "
                "screen content is UNKNOWN without the frame.",
    },
    "conclusions": {
        "observed": [
            "attempt-08 r1/r2 and attempt-09 all reproduce exit 4 UNSAFE_MARGINS with "
            "band_bottom_bright_row=null and margin_below_px=null.",
            "The maximum FULL-ROW mean below the title is 78.878 (a08r1, y=1101), 91.836 "
            "(a08r2, y=1353) and 66.679 (a09, y=1168) - all below the frozen bright=100 "
            "threshold, so the bottom band can never be found in these frames.",
            "The same v4 rule restricted to the LINE-window x-range finds the bottom band "
            "at y=1078 / 1042 / 1210 with margins 45/102, 44/103, 46/101 px.",
            "The three v4 band_top rows are y=72 (full-row mean 164.870; the wallpaper row "
            "above the LINE window, whose top edge is y≈123), y=601 (mean 103.291; a row "
            "inside the grid above), y=35 (mean 106.406; the macOS menu-bar row above the "
            "window).",
            "The LINE window occupies 28.5 % of the frame width; even a fully white window "
            "row could contribute at most 72.7 to the full-row mean.",
            "The frozen frames, ledgers and attempt-09 S1-S2 evidence all record zero GUI "
            "input; the album-card click, Save All, chooser and download counts are 0.",
        ],
        "inferred": [
            "v4's margin_above_px values (904/338/1074) are not a card-local signal at all: "
            "they measure the distance from the title to wallpaper/menu-bar rows.",
            "Any v4 'ELIGIBLE' outcome on a full-screen frame depends on unrelated screen "
            "content brightening the same row; it is arrangement-luck, not a property of "
            "the target card's local safety.",
            "The failure is architectural (full-screenshot row domain vs window-local card "
            "content), not a screen-placement problem: in all three frames the card's local "
            "structure (grid above / caption strip / grid below) is intact.",
        ],
        "unknown": [
            "Which pixels lifted attempt-07's row y=1002 to mean >= 100 (frame not "
            "preserved).",
            "Whether any other display arrangement could make v4 report a non-null but "
            "semantically wrong bottom margin (no frame available to test).",
        ],
    },
}

for name in frames:
    e = dom["frames"][name]
    v6e = v6[name]
    result["replay"]["per_frame"][name] = {
        "frame": e["frame"], "frame_sha256": e["frame_sha256"],
        "roi": e["roi"], "title_bbox": e["title_bbox"], "title_center_y": e["title_center_y"],
        "v4_full_row_recompute": e["full_row_domain"]["rule_recompute"],
        "v4_full_row_max_below_title": e["full_row_domain"]["max_mean_below_title"],
        "roi_local_v4_rule_recompute": e["roi_domain"]["rule_recompute"],
        "roi_local_max_below_title": e["roi_domain"]["max_mean_below_title"],
        "v6_verdict": v6e["verdict"], "v6_click_point": v6e["click_point"],
        "v6_margins": v6e["margins"],
    }

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
print("written", OUT)
