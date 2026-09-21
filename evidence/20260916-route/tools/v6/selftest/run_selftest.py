#!/usr/bin/env python3
"""v6 album-card S3 locator self-tests (deterministic; offline; zero GUI input).

Uses ONLY frozen frames already on disk plus synthesized variants built from
them under evidence/20260921-replan-v6/replay/negatives/. No live capture, no
LINE interaction, no input of any kind.

Success criterion = every case produces its expected refusal/exit and the
global assertions hold. An ELIGIBLE verdict on attempt-09 is NOT a success
criterion; refusals with precise local safety reasons are equally valid.

Run with: /opt/homebrew/bin/python3 run_selftest.py
Writes:  evidence/20260921-replan-v6/replay/selftest/results.json
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir))
V6 = os.path.join(ROOT, "evidence/20260916-route/tools/v6/locate_album_card.py")
EXTRACT = os.path.join(ROOT, "evidence/20260916-route/tools/v6/extract_window_geometry.py")
REPLAY = os.path.join(ROOT, "evidence/20260921-replan-v6/replay")
SELF = os.path.join(REPLAY, "selftest")
NEG = os.path.join(REPLAY, "negatives")
GEOM = os.path.join(REPLAY, "geometry")

FRAMES = {
    "a08r1": os.path.join(ROOT, "evidence/20260916-route/attempt-08/frame-pre.png"),
    "a08r2": os.path.join(ROOT, "evidence/20260916-route/attempt-08/frame-pre-r2.png"),
    "a09": os.path.join(ROOT, "evidence/20260916-route/attempt-09/frame-pre.png"),
}
EXPECT = ["--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]
BG = np.array([45, 46, 48], dtype=np.uint8)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(path):
    """Repo-relative path so subprocess outputs are byte-stable across machines."""
    return os.path.relpath(os.path.abspath(path), ROOT)


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def load_frame(name):
    return np.asarray(Image.open(FRAMES[name]).convert("RGB"), dtype=np.uint8).copy()


def save_frame(name, arr):
    path = os.path.join(NEG, name)
    Image.fromarray(arr, "RGB").save(path, format="PNG", optimize=False)
    return path


def erase_rect(arr, x0, y0, x1, y1):
    arr[y0:y1 + 1, x0:x1 + 1] = BG


def cut_rows(arr, y0, y1):
    return np.vstack([arr[:y0], arr[y1 + 1:]])


def draw_dots(arr, cx, cy, color=(230, 230, 230)):
    for dy in (-6, 0, 6):
        arr[cy + dy - 1:cy + dy + 2, cx - 1:cx + 2] = color


def write_geometry(path, frame_path, rect, label):
    payload = {
        "schema": "v6-window-geometry/1",
        "frame": frame_path,
        "frame_sha256": sha256(frame_path),
        "frame_size": list(Image.open(frame_path).size),
        "x0": rect[0], "y0": rect[1], "x1": rect[2], "y1": rect[3],
        "source": "selftest fabricated ROI (%s) - test input, not a route artifact" % label,
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    return path


def main():
    os.makedirs(SELF, exist_ok=True)
    os.makedirs(NEG, exist_ok=True)
    results = {"schema": "v6-selftest-results/1", "gui_input_count": 0,
               "interpreter": sys.executable, "cases": [], "global_assertions": []}

    # ---------- positive replays (frozen frames) ----------
    for name in ("a08r1", "a08r2", "a09"):
        frame = FRAMES[name]
        geo_out = os.path.join(SELF, "regen-%s-geometry.json" % name)
        rc_g, out_g, _ = run([sys.executable, rel(EXTRACT), rel(frame)] + EXPECT + ["--out", rel(geo_out)])
        assert rc_g == 0, "extractor failed on %s: %s" % (name, out_g)
        committed = os.path.join(GEOM, "%s.json" % name)
        geometry_identical = open(geo_out, "rb").read() == open(committed, "rb").read()
        verdict_out = os.path.join(SELF, "replay-%s-v6.json" % name)
        rc, out, err = run([sys.executable, rel(V6), rel(frame)] + EXPECT +
                           ["--expect-count", "57", "--window-geometry", rel(geo_out), "--out", rel(verdict_out)])
        payload = json.load(open(verdict_out, encoding="utf-8")) if os.path.exists(verdict_out) else {}
        title = payload.get("title") or {}
        bbox = title.get("bbox")
        derived = [bbox[0] + 12, (bbox[1] + bbox[3]) // 2] if bbox else None
        results["cases"].append({
            "id": "replay-%s" % name, "kind": "replay", "frame": frame,
            "frame_sha256": sha256(frame), "geometry_committed": committed,
            "geometry_byte_identical_to_committed": geometry_identical,
            "exit": rc, "expected_exit": [0],
            "verdict": payload.get("verdict"), "click_point": payload.get("click_point"),
            "click_point_equals_frame_ocr_derivation": payload.get("click_point") == derived,
            "margins": payload.get("margins"),
            "passed": rc in (0,) and geometry_identical
                      and payload.get("click_point") == derived
                      and payload.get("dispatch", {}).get("dispatched", False) is False,
        })

    # ---------- negative cases ----------
    cases = []

    def add(cid, desc, argv, expected, frame=None, geometry=None):
        cases.append({"id": cid, "desc": desc, "argv": argv, "expected_exit": expected,
                      "frame": frame, "geometry": geometry})

    geo_a09 = os.path.join(GEOM, "a09.json")
    geo_a08r1 = os.path.join(GEOM, "a08r1.json")

    add("wrong_date",
        "expected start/end that do not exist in the frame -> TARGET_TITLE_NOT_FOUND",
        [rel(FRAMES["a09"]), "--expect-start", "2023/01/01", "--expect-end", "2023/01/05",
         "--window-geometry", rel(geo_a09)], [2], FRAMES["a09"])

    add("wrong_count",
        "readable count 57 != expected 58 -> TARGET_COUNT_MISMATCH",
        [rel(FRAMES["a09"])] + EXPECT + ["--expect-count", "58", "--window-geometry", rel(geo_a09)], [5],
        FRAMES["a09"])

    # erased title (same size frame; original geometry passed but title is checked first)
    arr = load_frame("a09")
    erase_rect(arr, 20, 1092, 264, 1128)
    f_erased = save_frame("a09-title-erased.png", arr)
    add("no_target_title",
        "title band erased -> TARGET_TITLE_NOT_FOUND (before geometry is trusted)",
        [rel(f_erased)] + EXPECT + ["--window-geometry", rel(geo_a09)], [2], f_erased)

    add("missing_geometry",
        "no --window-geometry -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT, [7], FRAMES["a09"])

    add("unbound_geometry_sha",
        "geometry of a different frame (sha mismatch) -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(geo_a08r1)], [7], FRAMES["a09"])

    bad_json = os.path.join(NEG, "geometry-not-json.json")
    with open(bad_json, "w", encoding="utf-8") as f:
        f.write("this is not json\n")
    add("geometry_not_json",
        "geometry file unreadable -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(bad_json)], [7], FRAMES["a09"])

    missing_fields = os.path.join(NEG, "geometry-missing-fields.json")
    with open(missing_fields, "w", encoding="utf-8") as f:
        f.write(json.dumps({"x0": 0, "y0": 100, "x1": 640}) + "\n")
    add("geometry_missing_fields",
        "geometry missing fields -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(missing_fields)], [7], FRAMES["a09"])

    oob = write_geometry(os.path.join(NEG, "geometry-out-of-frame.json"), FRAMES["a09"],
                         (-5, 100, 660, 1300), "outside frame")
    add("geometry_out_of_frame",
        "rect outside frame -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(oob)], [7], FRAMES["a09"])

    small = write_geometry(os.path.join(NEG, "geometry-too-small.json"), FRAMES["a09"],
                           (0, 900, 199, 1307), "width 199")
    add("roi_too_small",
        "ROI width 199 < 200 -> WINDOW_ROI_MISSING_OR_INVALID",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(small)], [7], FRAMES["a09"])

    clip = write_geometry(os.path.join(NEG, "geometry-right-tail-clipped.json"), FRAMES["a08r1"],
                          (10, 123, 320, 1334), "right edge 320 (tail 53)")
    add("target_near_roi_edge",
        "ROI right tail 320-267=53 < 120 -> IDENTITY_NOT_ROI_BOUND",
        [rel(FRAMES["a08r1"])] + EXPECT + ["--window-geometry", rel(clip)], [8], FRAMES["a08r1"])

    below_title = write_geometry(os.path.join(NEG, "geometry-title-above-roi.json"), FRAMES["a08r1"],
                                 (10, 980, 663, 1334), "top edge below the title")
    add("target_above_roi",
        "title top 963 above ROI top 980 -> IDENTITY_NOT_ROI_BOUND",
        [rel(FRAMES["a08r1"])] + EXPECT + ["--window-geometry", rel(below_title)], [8], FRAMES["a08r1"])

    shift = write_geometry(os.path.join(NEG, "geometry-candidate-left-of-inset.json"), FRAMES["a08r1"],
                           (40, 123, 663, 1334), "left edge 40")
    add("candidate_out_of_bounds",
        "candidate x=49 < ROI left 40+16 -> CANDIDATE_OUT_OF_BOUNDS",
        [rel(FRAMES["a08r1"])] + EXPECT + ["--window-geometry", rel(shift)], [11], FRAMES["a08r1"])

    full = write_geometry(os.path.join(NEG, "geometry-full-frame.json"), FRAMES["a09"],
                          (0, 0, 2294, 1490), "full frame")
    add("roi_is_full_frame",
        "ROI = whole screenshot (foreign content in domain) -> must refuse (4/9/10 acceptable)",
        [rel(FRAMES["a09"])] + EXPECT + ["--window-geometry", rel(full)], [4, 9, 10], FRAMES["a09"])

    # synthesized separations
    arr = load_frame("a08r1")
    f_up = save_frame("a08r1-grid-above-30px-closer.png", cut_rows(arr, 932, 961))
    geo_up = os.path.join(SELF, "geo-up.png")
    rc_g, _, _ = run([sys.executable, rel(EXTRACT), rel(f_up)] + EXPECT + ["--out", rel(geo_up)])
    assert rc_g == 0, "extractor failed on synthesized upper-separation frame"
    add("insufficient_upper_separation",
        "grid above moved 30 px closer (margin_above ~15 px < 27) -> UNSAFE_MARGINS",
        [rel(f_up)] + EXPECT + ["--window-geometry", rel(geo_up)], [4], f_up)

    arr = load_frame("a09")
    erase_rect(arr, 15, 1123, 195, 1157)   # count text blanked (avoid MISMATCH noise)
    arr = cut_rows(arr, 1125, 1224)        # grid below 100 px closer (below the 24 px floor)
    f_down = save_frame("a09-grid-below-100px-closer.png", arr)
    geo_down = os.path.join(SELF, "geo-down.png")
    rc_g, _, _ = run([sys.executable, rel(EXTRACT), rel(f_down)] + EXPECT + ["--out", rel(geo_down)])
    assert rc_g == 0, "extractor failed on synthesized lower-separation frame"
    add("insufficient_lower_separation",
        "grid below moved 100 px closer (margin_below < 24 px floor) -> UNSAFE_MARGINS",
        [rel(f_down)] + EXPECT + ["--window-geometry", rel(geo_down)], [4], f_down)

    arr = load_frame("a08r1")
    draw_dots(arr, 120, 1050)              # extra control-like cluster in the caption strip
    f_dots = save_frame("a08r1-extra-strip-cluster.png", arr)
    geo_dots = os.path.join(SELF, "geo-dots.png")
    rc_g, _, _ = run([sys.executable, rel(EXTRACT), rel(f_dots)] + EXPECT + ["--out", rel(geo_dots)])
    assert rc_g == 0, "extractor failed on synthesized ambiguous-strip frame"
    add("ambiguous_strip_cluster",
        "second control-like cluster inside the caption strip -> STRIP_CONTENT_UNEXPECTED",
        [rel(f_dots)] + EXPECT + ["--window-geometry", rel(geo_dots)], [10], f_dots)

    # adversarial: an extra border-like vertical line makes the extractor pick a narrower
    # rect; v6's independent identity/right-tail check must then refuse.
    arr = load_frame("a08r1")
    arr[130:1332, 350] = np.array([67, 67, 69], dtype=np.uint8)
    f_line = save_frame("a08r1-extra-border-line.png", arr)
    geo_line = os.path.join(SELF, "geo-line.png")
    rc_l, out_l, _ = run([sys.executable, rel(EXTRACT), rel(f_line)] + EXPECT + ["--out", rel(geo_line)])
    line_rect = None
    if os.path.exists(geo_line):
        line_payload = json.load(open(geo_line, encoding="utf-8"))
        line_rect = [line_payload["x0"], line_payload["y0"], line_payload["x1"], line_payload["y1"]]
    add("extractor_ambiguous_border_line",
        "painted extra border-like line narrows the extracted ROI -> v6 must refuse (8)",
        [rel(f_line)] + EXPECT + ["--window-geometry", rel(geo_line)], [8], f_line)
    results.setdefault("adversarial_notes", {})["extractor_ambiguous_border_line"] = {
        "extractor_exit": rc_l, "extractor_rect": line_rect,
        "note": "the extractor itself returns GEOMETRY_OK on the painted frame; v6's "
                "independent right-tail check (identity-not-ROI-bound) is the gate",
    }

    malformed = os.path.join(NEG, "malformed-frame.png")
    with open(malformed, "w", encoding="utf-8") as f:
        f.write("not a png\n")
    add("malformed_frame",
        "undecodable frame file -> BAD_FRAME",
        [rel(malformed)] + EXPECT, [6], malformed)

    for case in cases:
        out_path = os.path.join(SELF, "neg-%s.json" % case["id"])
        argv = case["argv"] + (["--out", rel(out_path)] if os.path.exists(case["argv"][0]) else [])
        rc, out, err = run([sys.executable, rel(V6)] + argv)
        payload = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
        entry = {
            "id": case["id"], "kind": "negative", "desc": case["desc"],
            "frame": case["frame"], "frame_sha256": sha256(case["frame"]) if case["frame"] and os.path.exists(case["frame"]) else None,
            "geometry": case["geometry"],
            "exit": rc, "expected_exit": case["expected_exit"],
            "verdict": payload.get("verdict"),
            "click_point": payload.get("click_point"),
            "dispatched": payload.get("dispatch", {}).get("dispatched", None),
            "passed": rc in case["expected_exit"] and payload.get("verdict") != "ELIGIBLE"
                      and payload.get("dispatch", {}).get("dispatched", False) is not True,
        }
        if case["id"] in ("insufficient_upper_separation", "insufficient_lower_separation"):
            entry["margins"] = payload.get("margins")
            entry["structure"] = payload.get("structure")
        if case["id"] == "ambiguous_strip_cluster":
            entry["strip_clusters"] = payload.get("strip", {}).get("clusters")
        if case["id"] == "roi_is_full_frame":
            entry["note"] = "any refusal is acceptable here; ELIGIBLE would be a safety failure"
        results["cases"].append(entry)

    # ---------- global assertions ----------
    def assert_global(name, ok, detail):
        results["global_assertions"].append({"assertion": name, "ok": bool(ok), "detail": detail})

    forbidden = ["39, 1109", "39,1109", "[39, 1109]", "[39,1109]",
                 "49, 939", "49,939", "[49, 939]", "[49,939]",
                 "42, 895", "42,895", "[42, 895]", "[42,895]",
                 "304, 50", "304,50", "305, 50", "305,50"]
    tool_text = open(V6, encoding="utf-8").read()
    extract_text = open(EXTRACT, encoding="utf-8").read()
    hits = [tok for tok in forbidden if tok in tool_text or tok in extract_text]
    assert_global("no_historical_click_coordinate_literal_in_v6_sources", not hits,
                  "forbidden literals found: %s" % hits if hits else "none of the five historical points appear")

    clicks = [c.get("click_point") for c in results["cases"] if c["kind"] == "replay"]
    derived_ok = all(c.get("click_point_equals_frame_ocr_derivation") for c in results["cases"] if c["kind"] == "replay")
    assert_global("candidate_derived_per_frame", len(set(map(str, clicks))) == 3 and derived_ok,
                  "replay click points: %s" % clicks)

    negatives = [c for c in results["cases"] if c["kind"] == "negative"]
    assert_global("no_negative_case_eligible_or_dispatched",
                  all(n["verdict"] != "ELIGIBLE" and n["dispatched"] is not True for n in negatives),
                  "%d negative cases" % len(negatives))

    attempt07_frame = "2897628770ddacd125be3e8224ea4dfdd970aa1056acb9ca277c060553e7e7d3"
    assert_global("attempt07_replay_not_possible_frame_absent",
                  not os.path.exists("/tmp/route7_frame_pre.jpg"),
                  "attempt-07 frame sha %s is not preserved on disk; attempt-07 replay is "
                  "recorded as not-possible rather than simulated" % attempt07_frame)

    total = len(results["cases"])
    passed = sum(1 for c in results["cases"] if c["passed"])
    glob_ok = all(a["ok"] for a in results["global_assertions"])
    results["summary"] = {
        "cases_total": total, "cases_passed": passed,
        "global_assertions_passed": sum(1 for a in results["global_assertions"] if a["ok"]),
        "global_assertions_total": len(results["global_assertions"]),
        "all_passed": passed == total and glob_ok,
        "note": "ELIGIBLE is not a success criterion; every negative case must refuse with "
                "its expected code or be a documented refusal-set member.",
    }
    out_path = os.path.join(SELF, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(results, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(json.dumps(results["summary"], ensure_ascii=False, indent=1))
    return 0 if results["summary"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
