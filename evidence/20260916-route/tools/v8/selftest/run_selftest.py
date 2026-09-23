#!/usr/bin/env python3
"""v8 Save All menu-item locator self-tests (deterministic; offline; zero GUI input).

Two case families:

* cli-real-frame  - the frozen v8 CLI is run against real, already-frozen LINE
  frames on disk plus selftest-owned detector/geometry fixture JSONs under
  fixtures/. Real OCR is exercised; every fixture binds a frame by path + sha.
* evaluate-synthetic - the pure decision core v8.evaluate() is driven directly
  with synthetic OCR word boxes, so the full refusal matrix is exercised
  deterministically without OCR noise.

Success criterion = every case produces its expected verdict/exit, no refusal
case ever carries a candidate, every ELIGIBLE candidate satisfies the HARD
placement rules, and every case is reproducible run-to-run. An ELIGIBLE verdict
on the attempt-05 frame is required (the false-negative this revision closes);
the other ELIGIBLE verdicts are consistency replays of the same historical
frames the offline replay record already covers. An offline ELIGIBLE verdict is
NOT a live click authorization.

Run with: /opt/homebrew/bin/python3 run_selftest.py
Writes:   tools/v8/selftest/out/<case>.json and tools/v8/selftest/results.json
"""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
V8 = os.path.dirname(HERE)
TOOLS = os.path.dirname(V8)
ROUTE = os.path.dirname(TOOLS)
EVID = os.path.dirname(ROUTE)
ROOT = os.path.dirname(EVID)
TOOL = os.path.join(V8, "locate_save_all_menu_item.py")
FIX = os.path.join(HERE, "fixtures")
OUT = os.path.join(HERE, "out")
RESULTS = os.path.join(HERE, "results.json")

FRAMES = {
    "a05": "evidence/20260921-rev27-save-all/attempt-05/frame-menu-post1.png",
    "a13-pre": "evidence/20260916-route/attempt-13/frame-menu-pre.png",
    "a13": "evidence/20260916-route/attempt-13/frame-menu-post1.png",
    "a19": "evidence/20260916-route/attempt-19/frame-menu-post1.png",
    "su": "evidence/20260921-rev27-save-all/attempt-02/selftest/frame-synth-unexpected.png",
    "sa": "evidence/20260921-rev27-save-all/attempt-02/selftest/frame-synth-ambiguous.png",
}

REFUSAL_VERDICTS = ["NOT_FOUND", "NOT_ADDRESSABLE", "AMBIGUOUS",
                    "MENU_CONTENT_UNEXPECTED", "BAD_INPUT", "ROW_GEOMETRY_UNSAFE"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location("v8_locate_save_all", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(frame, det, geo, out_name):
    """Run the frozen v8 CLI from the repo root with repo-relative args."""
    out_path = os.path.join(OUT, out_name)
    fixture_prefix = os.path.relpath(FIX, ROOT) + "/"
    det = det.replace("fixtures/", fixture_prefix, 1)
    geo = geo.replace("fixtures/", fixture_prefix, 1)
    cmd = [sys.executable, "-B", TOOL, frame, "--detector-json", det,
           "--geometry", geo, "--out", out_path]
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    raw = proc.stdout.decode("utf-8", errors="replace")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw)
    return proc.returncode, raw, out_path


# ---------------------------------------------------------------- synthetic
def w(text, x0, y0, x1, y1, conf=95.0):
    return {"text": text, "conf": conf,
            "box": [float(x0), float(y0), float(x1), float(y1)]}


def base_rows():
    """Five menu rows shaped like the real attempt-05 geometry."""
    return [
        [w("選擇", 1282, 222, 1332, 246, 87.289),
         w("項目", 1341, 222, 1382, 246, 96.814)],
        [w("修改", 1282, 286, 1330, 310, 96.723),
         w("相", 1330, 274, 1355, 322, 93.195),
         w("簿", 1355, 274, 1381, 322, 92.673),
         w("名", 1381, 274, 1400, 322, 93.175),
         w("稱", 1400, 274, 1420, 322, 80.0)],
        [w("儲存", 1282, 326, 1385, 352, 96.955),
         w("全", 1341, 326, 1366, 374, 96.985),
         w("部", 1365, 326, 1384, 374, 96.556)],
        [w("刪除", 1282, 390, 1330, 414, 96.79),
         w("相", 1330, 378, 1355, 426, 93.1),
         w("簿", 1355, 378, 1384, 426, 92.9)],
        [w("分享", 1282, 442, 1330, 466, 96.5),
         w("相", 1330, 430, 1355, 478, 93.3),
         w("簿", 1355, 430, 1384, 478, 92.8)],
    ]


def base_fixture():
    return {"frame_size": [2294, 1490],
            "bbox": [1231.0, 149.0, 1489.0, 500.0],
            "scale": 2, "window_pos": [329, 41], "window_size": [327, 643],
            "rows": base_rows()}


def two_words(t1, t2, y0, y1, x0=1282.0, gap=10.0, width=50.0):
    x1 = x0 + width
    return [w(t1, x0, y0, x1, y1, 96.0),
            w(t2, x1 + gap, y0, x1 + gap + width, y1, 96.0)]


def run_evaluate(v8, fx):
    words = []
    for row in fx["rows"]:
        words.extend(copy.deepcopy(row))
    return v8.evaluate(list(fx["frame_size"]), list(fx["bbox"]), fx["scale"],
                       list(fx["window_pos"]), list(fx["window_size"]), words)


def synthetic_cases():
    cases = []

    def add(cid, title, fixture, expected_verdict=None, expected_exit=None,
            extra=None):
        cases.append({"id": cid, "title": title, "fixture": fixture,
                      "expected_verdict": expected_verdict,
                      "expected_exit": expected_exit,
                      "refusal_class": expected_verdict is None,
                      "extra": extra or []})

    add("s01-baseline-eligible",
        "synthetic five-item menu shaped like the real frame -> ELIGIBLE",
        base_fixture(), "ELIGIBLE", 0)

    fx = base_fixture()
    fx["rows"][2] = two_words("關閉", "視窗", 326, 350)
    add("s02-target-missing",
        "target row replaced by a different item -> NOT_FOUND",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"][2] = [w("儲存", 1282, 326, 1385, 352, 96.955),
                     w("全", 1341, 326, 1366, 374, 96.985),
                     w("郜", 1365, 326, 1384, 374, 49.8)]
    add("s03-target-misread-no-fuzzy",
        "target itself misread 儲存全郜 -> NOT_FOUND (no fuzzy/similar matching)",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"][2] = [w("儲存", 1282, 326, 1385, 352, 96.955),
                     w("全", 1341, 326, 1366, 374, 96.985)]
    add("s04-target-partial",
        "target truncated to 儲存全 -> NOT_FOUND (partial target not accepted)",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"].append([w("儲存", 1282, 482, 1385, 499, 96.9),
                       w("全", 1341, 482, 1366, 499, 96.9),
                       w("部", 1365, 482, 1384, 499, 96.9)])
    add("s05-target-twice",
        "target text in two rows -> AMBIGUOUS",
        fx, "AMBIGUOUS", 4)

    fx = base_fixture()
    fx["rows"][2] = [w("儲存", 1282, 326, 1385, 352, 96.955)]
    fx["rows"][4] = fx["rows"][4] + [w("全", 1341, 430, 1366, 478, 96.9),
                                     w("部", 1365, 430, 1384, 478, 96.9)]
    add("s06-target-spanning-two-rows",
        "target characters split across two rows -> NOT_FOUND (no unique row assignment)",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"][0] = two_words("複製", "貼上", 222, 246)
    fx["rows"][1] = two_words("取消", "選取", 274, 322)
    fx["rows"][3] = two_words("全選", "項目", 378, 426)
    fx["rows"][4] = two_words("說明", "偏好", 430, 478)
    add("s07-wrong-menu-with-target",
        "a different five-item menu that still contains 儲存全部 -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    fx["rows"][2] = [w("保存", 1282, 326, 1385, 352, 96.9),
                     w("全", 1341, 326, 1366, 374, 96.9),
                     w("部", 1365, 326, 1384, 374, 96.9)]
    add("s08-target-similar-string-not-target",
        "all four context rows exact but target row reads 保存全部 -> NOT_FOUND",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"][1] = [w("修改", 1282, 286, 1330, 310, 96.723),
                     w("相", 1330, 274, 1355, 322, 93.195),
                     w("簿", 1355, 274, 1381, 322, 92.673),
                     w("名", 1381, 274, 1400, 322, 93.175),
                     w("般", 1400, 274, 1420, 322, 49.772)]
    add("s09-non-target-1sub-attempt05-class",
        "attempt-05 class: 修改相簿名稱 reads 修改相簿名般 -> ELIGIBLE (the false-negative fix)",
        fx, "ELIGIBLE", 0,
        extra=[("row2_tier", lambda r: r["supporting_signals"]["row_match_tiers"][1]
                == "TOLERANT_1_SUB")])

    fx = base_fixture()
    fx["rows"][0] = two_words("選揖", "項目", 222, 246)
    fx["rows"][1] = [w("修改", 1282, 286, 1330, 310, 96.7),
                     w("相", 1330, 274, 1355, 322, 93.2),
                     w("簿", 1355, 274, 1381, 322, 92.7),
                     w("名", 1381, 274, 1400, 322, 93.2),
                     w("般", 1400, 274, 1420, 322, 49.8)]
    fx["rows"][3] = [w("刪除", 1282, 390, 1330, 414, 96.8),
                     w("相", 1330, 378, 1355, 426, 93.1),
                     w("蒲", 1355, 378, 1384, 426, 60.2)]
    add("s10-non-target-multirow-1sub-each",
        "three non-target rows each with one substituted char -> still ELIGIBLE",
        fx, "ELIGIBLE", 0,
        extra=[("row_tiers", lambda r: r["supporting_signals"]["row_match_tiers"]
                == ["TOLERANT_1_SUB", "TOLERANT_1_SUB", "EXACT",
                    "TOLERANT_1_SUB", "EXACT"])])

    fx = base_fixture()
    fx["rows"][1] = [w("修改", 1282, 286, 1330, 310, 96.7),
                     w("相", 1330, 274, 1355, 322, 93.2),
                     w("簿", 1355, 274, 1381, 322, 92.7),
                     w("般", 1381, 274, 1400, 322, 55.0),
                     w("般", 1400, 274, 1420, 322, 49.8)]
    add("s11-non-target-2sub-same-row",
        "two substituted chars in the SAME non-target row -> MENU_CONTENT_UNEXPECTED (documented boundary)",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    fx["rows"][1] = [w("修改", 1282, 286, 1330, 310, 96.7),
                     w("相", 1330, 274, 1355, 322, 93.2),
                     w("簿", 1355, 274, 1381, 322, 92.7),
                     w("名", 1381, 274, 1420, 322, 83.0)]
    add("s12-non-target-length-change",
        "non-target row lost a character (insert/delete never tolerated) -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    del fx["rows"][4]
    add("s13-item-count-4",
        "context degraded to four item rows -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    fx["rows"].append(two_words("取消", "關閉", 482, 499))
    add("s14-item-count-6",
        "context degraded to six item rows -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    rows = fx["rows"]
    old4, old5 = rows[3], rows[4]
    def shift(row, y0):
        top = min(word_box["box"][1] for word_box in row)
        delta = y0 - top
        return [w(word_box["text"], word_box["box"][0],
                  word_box["box"][1] + delta, word_box["box"][2],
                  word_box["box"][3] + delta, word_box["conf"]) for word_box in row]
    rows[3] = shift(old5, 378)
    rows[4] = shift(old4, 430)
    add("s15-item-order-swap",
        "刪除相簿 / 分享相簿 swapped (order mismatch) -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    fx = base_fixture()
    for word_box in fx["rows"][3]:
        word_box["box"][1] -= 24.0
        word_box["box"][3] -= 24.0
    add("s16-band-overlap-neighbor-collision",
        "neighbor row band overlaps the target band -> ROW_GEOMETRY_UNSAFE",
        fx, "ROW_GEOMETRY_UNSAFE", 7,
        extra=[("overlapping_pairs", lambda r: r["checks"][3]["detail"]
                ["overlapping_pairs"] == [[2, 3]])])

    fx = base_fixture()
    fx["rows"][1] = [w("修改", 1282, 282, 1330, 306, 96.7),
                     w("相", 1330, 282, 1355, 330, 93.2),
                     w("簿", 1355, 282, 1381, 330, 92.7),
                     w("名", 1381, 282, 1400, 330, 93.2),
                     w("稱", 1400, 282, 1420, 330, 83.0)]
    fx["rows"][2] = [w("儲存", 1282, 330, 1385, 346, 96.9),
                     w("全", 1341, 330, 1366, 346, 96.9),
                     w("部", 1365, 330, 1384, 346, 96.9)]
    fx["rows"][3] = [w("刪除", 1282, 372, 1330, 396, 96.8),
                     w("相", 1330, 348, 1355, 396, 93.1),
                     w("簿", 1355, 348, 1384, 396, 92.9)]
    add("s17-candidate-near-row-boundary",
        "short target band squeezed by neighbors -> empty y-safe region -> ROW_GEOMETRY_UNSAFE",
        fx, "ROW_GEOMETRY_UNSAFE", 7,
        extra=[("reason", lambda r: "y safe region is empty" in r["reason"])])

    fx = base_fixture()
    fx["rows"][2] = [w("儲存", 1150, 326, 1253, 352, 96.9),
                     w("全", 1209, 326, 1234, 374, 96.9),
                     w("部", 1233, 326, 1252, 374, 96.9)]
    add("s18-target-band-outside-bbox-x",
        "target band pushed left out of the menu bbox -> ROW_GEOMETRY_UNSAFE",
        fx, "ROW_GEOMETRY_UNSAFE", 7,
        extra=[("outside_bbox", lambda r: 2 in r["checks"][3]["detail"]["outside_bbox"])])

    fx = base_fixture()
    fx["bbox"] = [1231.0, 149.0, 1489.0, 300.0]
    add("s19-target-outside-popup-y",
        "menu bbox cropped above the target row -> rows outside popup -> ROW_GEOMETRY_UNSAFE",
        fx, "ROW_GEOMETRY_UNSAFE", 7,
        extra=[("outside_bbox", lambda r: [1, 2, 3, 4] ==
                sorted(r["checks"][3]["detail"]["outside_bbox"]))])

    fx = base_fixture()
    fx["bbox"] = [0.0, 0.0, 2294.0, 1490.0]
    add("s20-whole-screen-bbox",
        "whole-screen bbox (false-positive menu shape) -> BAD_INPUT",
        fx, "BAD_INPUT", 6)

    fx = base_fixture()
    fx["bbox"] = [500.0, 149.0, 1900.0, 500.0]
    add("s21-bbox-too-wide",
        "ambiguous bbox wider than half the frame -> BAD_INPUT",
        fx, "BAD_INPUT", 6)

    fx = base_fixture()
    fx["window_pos"] = [10, 10]
    fx["window_size"] = [100, 100]
    add("s22-window-disjoint",
        "menu bbox disjoint from the window rect -> NOT_ADDRESSABLE",
        fx, "NOT_ADDRESSABLE", 3)

    fx = base_fixture()
    fx["window_pos"] = [322, 41]
    add("s23-x-overlap-below-rule",
        "x-overlap with the addressable region below 20px -> NOT_ADDRESSABLE",
        fx, "NOT_ADDRESSABLE", 3)

    fx = base_fixture()
    fx["rows"] = []
    add("s24-empty-words",
        "no OCR words inside the menu bbox -> NOT_FOUND",
        fx, "NOT_FOUND", 2)

    fx = base_fixture()
    fx["rows"][1] = two_words("選擇", "項目", 274, 322)
    add("s25-duplicate-context-row",
        "a context row duplicates the first item (degraded identity) -> MENU_CONTENT_UNEXPECTED",
        fx, "MENU_CONTENT_UNEXPECTED", 5)

    return cases


def cli_cases():
    def add(cid, title, frame, det, geo, expected_verdict, expected_exit,
            refusal_class=False, extra=None):
        return {"id": cid, "title": title, "frame": frame, "detector": det,
                "geometry": geo, "expected_verdict": expected_verdict,
                "expected_exit": expected_exit, "refusal_class": refusal_class,
                "extra": extra or []}

    cases = []
    cases.append(add(
        "c01-attempt-05-typo-closed",
        "attempt-05 frame: the 修改相簿名般 false-negative is closed (ELIGIBLE)",
        FRAMES["a05"], "fixtures/det-a05.json", "fixtures/geo-a05.json",
        "ELIGIBLE", 0, extra=[
            ("row2_tier", lambda r: r["supporting_signals"]["row_match_tiers"][1]
             == "TOLERANT_1_SUB"),
            ("row2_text", lambda r: r["rows"][1]["cjk_text"] == "修改相簿名般"),
            ("target_row", lambda r: r["target"]["row_index"] == 2
             and r["target"]["cjk_text"] == "儲存全部"),
            ("candidate_frame_px", lambda r: close(r["candidate"]["frame_px"],
                                                   [1297.333, 351.5])),
            ("candidate_app_local", lambda r: close(r["candidate"]["app_local_pt"],
                                                    [319.667, 134.75])),
        ]))
    cases.append(add(
        "c02-attempt-13-replay",
        "attempt-13 frame replay: all five rows EXACT (ELIGIBLE)",
        FRAMES["a13"], "fixtures/det-a13.json", "fixtures/geo-a13.json",
        "ELIGIBLE", 0, extra=[
            ("row_tiers", lambda r: all(t == "EXACT" for t in
                                        r["supporting_signals"]["row_match_tiers"])),
            ("candidate_frame_px", lambda r: close(r["candidate"]["frame_px"],
                                                   [1313.5, 332.333])),
        ]))
    cases.append(add(
        "c03-attempt-19-replay",
        "attempt-19 frame replay (ELIGIBLE)",
        FRAMES["a19"], "fixtures/det-a19.json", "fixtures/geo-a19.json",
        "ELIGIBLE", 0, extra=[
            ("candidate_app_local", lambda r: close(r["candidate"]["app_local_pt"],
                                                    [319.75, 136.167])),
        ]))
    cases.append(add(
        "c04-attempt-05-origin-shifted-input-derived",
        "same frame, window origin +7pt: candidate follows current inputs (no historical constant)",
        FRAMES["a05"], "fixtures/det-a05.json",
        "fixtures/geo-a05-origin-shifted.json", "ELIGIBLE", 0, extra=[
            ("app_local_x_shifted", lambda r: close(
                [r["candidate"]["app_local_pt"][0]], [316.167])),
            ("screen_pt_y_unchanged", lambda r: close(
                [r["candidate"]["screen_pt"][1]], [175.75])),
            ("app_local_y_shifted", lambda r: close(
                [r["candidate"]["app_local_pt"][1]], [127.75])),
        ]))
    cases.append(add(
        "c05-synth-unexpected-frame",
        "attempt-02 synthetic unexpected-content frame stays MENU_CONTENT_UNEXPECTED",
        FRAMES["su"], "fixtures/det-su.json", "fixtures/geo-su.json",
        "MENU_CONTENT_UNEXPECTED", 5))
    cases.append(add(
        "c06-synth-ambiguous-frame",
        "attempt-02 synthetic two-target frame stays AMBIGUOUS",
        FRAMES["sa"], "fixtures/det-sa.json", "fixtures/geo-sa.json",
        "AMBIGUOUS", 4))
    cases.append(add(
        "c07-menu-absent-pre-frame",
        "menu-absent frame (same bbox) -> refusal, never ELIGIBLE",
        FRAMES["a13-pre"], "fixtures/det-a13-pre.json",
        "fixtures/geo-pre-a13.json", None, None, refusal_class=True))
    cases.append(add(
        "c08-crop-excludes-target",
        "crop that ends above the target row -> refusal, never ELIGIBLE",
        FRAMES["a05"], "fixtures/det-a05-truncated-bbox.json",
        "fixtures/geo-a05.json", None, None, refusal_class=True))
    cases.append(add(
        "c09-stale-frame-sha-binding",
        "geometry bound to the PRE frame sha while the POST frame is passed -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-a13.json",
        "fixtures/geo-a13-pre-binding.json", "BAD_INPUT", 6))
    cases.append(add(
        "c10-wrong-frame-binding",
        "detector bound to the attempt-05 frame while the attempt-13 frame is passed -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-a05.json", "fixtures/geo-a13.json",
        "BAD_INPUT", 6))
    cases.append(add(
        "c11-detector-not-menu-detected",
        "detector verdict is not MENU_DETECTED -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-not-detected.json", "fixtures/geo-a13.json",
        "BAD_INPUT", 6))
    cases.append(add(
        "c12-detector-missing-bbox",
        "MENU_DETECTED without a usable chosen_bbox -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-no-bbox.json", "fixtures/geo-a13.json",
        "BAD_INPUT", 6))
    cases.append(add(
        "c13-whole-screen-bbox",
        "whole-screen bbox -> popup-shape rule -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-whole-screen.json", "fixtures/geo-a13.json",
        "BAD_INPUT", 6))
    cases.append(add(
        "c14-bbox-outside-frame",
        "bbox extending beyond the frame -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-bbox-outside.json", "fixtures/geo-a13.json",
        "BAD_INPUT", 6))
    cases.append(add(
        "c15-window-disjoint",
        "window rect disjoint from the menu bbox -> NOT_ADDRESSABLE",
        FRAMES["a13"], "fixtures/det-a13.json",
        "fixtures/geo-a13-window-disjoint.json", "NOT_ADDRESSABLE", 3))
    cases.append(add(
        "c16-x-overlap-below-rule",
        "window shifted right so x-overlap < 20px -> NOT_ADDRESSABLE",
        FRAMES["a13"], "fixtures/det-a13.json",
        "fixtures/geo-a13-not-addressable.json", "NOT_ADDRESSABLE", 3))
    cases.append(add(
        "c17-missing-frame-file",
        "frame path does not exist -> BAD_INPUT",
        "evidence/20260916-route/attempt-13/no-such-frame.png",
        "fixtures/det-a13.json", "fixtures/geo-a13.json", "BAD_INPUT", 6))
    cases.append(add(
        "c18-geometry-unparseable",
        "geometry file is not valid JSON -> BAD_INPUT",
        FRAMES["a13"], "fixtures/det-a13.json", "fixtures/geo-broken.json",
        "BAD_INPUT", 6))
    return cases


def close(seq, expected, tol=0.002):
    return len(seq) == len(expected) and all(
        abs(a - b) <= tol for a, b in zip(seq, expected))


def load_fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def global_checks(results):
    checks = []

    all_pass = all(c["pass"] for c in results["cases"])
    checks.append({"name": "g01_all_cases_expected_outcome", "pass": all_pass,
                   "detail": {"cases": len(results["cases"])}})

    refusal_leaks = [c["id"] for c in results["cases"]
                     if c["refusal_class"] and c["observed"].get("verdict") not in
                     REFUSAL_VERDICTS]
    checks.append({"name": "g02_refusals_never_eligible", "pass": not refusal_leaks,
                   "detail": {"leaks": refusal_leaks}})

    eligible_blocks = []
    for case in results["cases"]:
        if case["observed"].get("verdict") != "ELIGIBLE":
            continue
        payload = case["observed"].get("candidate_payload")
        if payload is None:
            eligible_blocks.append([case["id"], "no_candidate_payload"])
            continue
        bad = [chk["name"] for chk in payload.get("checks", [])
               if not chk["pass"]]
        placement = next((chk for chk in payload.get("checks", [])
                          if chk["name"] == "candidate_placement"), None)
        if bad:
            eligible_blocks.append([case["id"], "failing_checks", bad])
        if not placement or not placement["detail"].get("candidate_inside_target_band"):
            eligible_blocks.append([case["id"], "candidate_not_in_target_band"])
    checks.append({"name": "g03_eligible_candidates_inside_target_band",
                   "pass": not eligible_blocks,
                   "detail": {"violations": eligible_blocks}})

    non_det = [c["id"] for c in results["cases"] if not c["deterministic"]]
    checks.append({"name": "g04_deterministic_run_twice", "pass": not non_det,
                   "detail": {"non_deterministic": non_det}})

    fuzzy = [c["id"] for c in results["cases"]
             if c["id"].startswith(("s03", "s04", "s06", "s08"))
             and c["observed"].get("verdict") != "NOT_FOUND"]
    checks.append({"name": "g05_no_fuzzy_target_matching", "pass": not fuzzy,
                   "detail": {"violations": fuzzy}})

    attempt05 = next(c for c in results["cases"]
                     if c["id"] == "c01-attempt-05-typo-closed")
    checks.append({"name": "g06_attempt05_false_negative_closed",
                   "pass": attempt05["observed"].get("verdict") == "ELIGIBLE",
                   "detail": {"verdict": attempt05["observed"].get("verdict")}})

    source = open(TOOL, encoding="utf-8").read()
    forbidden = ["evidence/", "makedirs", "shutil", "urlopen", "requests",
                 "1297.333", "1313.5", "351.5", "332.333", "319.75",
                 "136.167", "304", "988", "history", "historical_coordinate"]
    hits = [token for token in forbidden if token in source]
    write_opens = source.count('"w", encoding="utf-8"')
    checks.append({"name": "g07_no_historical_constants_or_extra_writes",
                   "pass": not hits and write_opens == 1,
                   "detail": {"forbidden_hits": hits,
                              "write_open_sites": write_opens}})

    c1 = next(c for c in results["cases"]
              if c["id"] == "c01-attempt-05-typo-closed")
    c4 = next(c for c in results["cases"]
              if c["id"] == "c04-attempt-05-origin-shifted-input-derived")
    p1 = c1["observed"].get("candidate_payload") or {}
    p4 = c4["observed"].get("candidate_payload") or {}
    derived = (p1.get("candidate", {}).get("app_local_pt") !=
               p4.get("candidate", {}).get("app_local_pt"))
    checks.append({"name": "g08_candidate_is_input_derived", "pass": derived,
                   "detail": {"origin_shifted_app_local":
                              p4.get("candidate", {}).get("app_local_pt")}})

    fixture_integrity = []
    for name, frame_key in (("det-a05.json", "a05"), ("det-a13.json", "a13"),
                            ("det-a19.json", "a19"), ("det-a13-pre.json", "a13-pre"),
                            ("det-su.json", "su"), ("det-sa.json", "sa"),
                            ("geo-a05.json", "a05"),
                            ("geo-a05-origin-shifted.json", "a05"),
                            ("geo-a13.json", "a13"), ("geo-a19.json", "a19"),
                            ("geo-pre-a13.json", "a13-pre"),
                            ("geo-su.json", "su"), ("geo-sa.json", "sa")):
        fixture = load_fixture(name)
        actual = sha256_file(os.path.join(ROOT, FRAMES[frame_key]))
        declared = fixture.get("post_sha256", fixture.get("frame_sha256"))
        if declared != actual:
            fixture_integrity.append([name, "sha_mismatch"])
    checks.append({"name": "g09_fixture_frame_bindings_true",
                   "pass": not fixture_integrity,
                   "detail": {"violations": fixture_integrity}})

    return checks


def main():
    os.makedirs(OUT, exist_ok=True)
    v8 = load_tool()
    tool_sha = sha256_file(TOOL)
    results = {
        "schema": "v8-selftest-results/1",
        "artifact": "evidence/20260916-route/tools/v8/selftest/results.json",
        "tool": {"path": "evidence/20260916-route/tools/v8/locate_save_all_menu_item.py",
                 "sha256": tool_sha, "version_flag": "v8"},
        "gui_input_count": 0,
        "cases": [],
        "global_assertions": [],
    }

    for case in synthetic_cases():
        first = run_evaluate(v8, case["fixture"])
        second = run_evaluate(v8, case["fixture"])
        first_txt = json.dumps(first, ensure_ascii=False, indent=1, sort_keys=True)
        second_txt = json.dumps(second, ensure_ascii=False, indent=1, sort_keys=True)
        out_path = os.path.join(OUT, case["id"] + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(
                {"case": case["id"], "input": case["fixture"], "result": first},
                ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        extra = []
        for name, fn in case["extra"]:
            try:
                extra.append({"name": name, "pass": bool(fn(first))})
            except Exception as exc:  # pragma: no cover - diagnostic only
                extra.append({"name": name, "pass": False, "error": repr(exc)})
        verdict = first.get("verdict")
        exit_code = first.get("exit_code")
        expected_ok = (case["refusal_class"] and verdict in REFUSAL_VERDICTS) or \
                      (case["expected_verdict"] == verdict and
                       case["expected_exit"] == exit_code)
        results["cases"].append({
            "id": case["id"], "kind": "evaluate-synthetic",
            "title": case["title"],
            "expected": {"verdict": case["expected_verdict"],
                         "exit_code": case["expected_exit"],
                         "refusal_class": case["refusal_class"]},
            "observed": {"verdict": verdict, "exit_code": exit_code,
                         "reason": first.get("reason"),
                         "candidate_payload": first},
            "extra_checks": extra,
            "deterministic": first_txt == second_txt,
            "output_file": os.path.relpath(out_path, ROOT),
            "output_sha256": sha256_file(out_path),
            "pass": expected_ok and all(e["pass"] for e in extra),
            "refusal_class": case["refusal_class"],
        })

    for case in cli_cases():
        rc1, out1, out_path = run_cli(case["frame"], case["detector"],
                                      case["geometry"], case["id"] + ".json")
        rc2, out2, run2_path = run_cli(case["frame"], case["detector"],
                                       case["geometry"], case["id"] + ".run2.json")
        os.remove(run2_path)
        payload = json.loads(out1)
        extra = []
        for name, fn in case["extra"]:
            try:
                extra.append({"name": name, "pass": bool(fn(payload))})
            except Exception as exc:  # pragma: no cover - diagnostic only
                extra.append({"name": name, "pass": False, "error": repr(exc)})
        verdict = payload.get("verdict")
        expected_ok = (case["refusal_class"] and verdict in REFUSAL_VERDICTS) or \
                      (case["expected_verdict"] == verdict and
                       case["expected_exit"] == rc1)
        results["cases"].append({
            "id": case["id"], "kind": "cli-real-frame",
            "title": case["title"],
            "inputs": {"frame": case["frame"], "detector_json": case["detector"],
                       "geometry_json": case["geometry"]},
            "expected": {"verdict": case["expected_verdict"],
                         "exit_code": case["expected_exit"],
                         "refusal_class": case["refusal_class"]},
            "observed": {"verdict": verdict, "exit_code": rc1,
                         "reason": payload.get("reason"),
                         "candidate_payload": payload},
            "extra_checks": extra,
            "deterministic": out1 == out2 and rc1 == rc2,
            "stdout_sha256": hashlib.sha256(out1.encode("utf-8")).hexdigest(),
            "output_file": os.path.relpath(out_path, ROOT),
            "output_sha256": sha256_file(out_path),
            "pass": expected_ok and all(e["pass"] for e in extra),
            "refusal_class": case["refusal_class"],
        })

    results["global_assertions"] = global_checks(results)
    results["summary"] = {
        "cases_total": len(results["cases"]),
        "cases_passed": sum(1 for c in results["cases"] if c["pass"]),
        "eligible_cases": [c["id"] for c in results["cases"]
                           if c["observed"]["verdict"] == "ELIGIBLE"],
        "refusal_cases": sum(1 for c in results["cases"] if c["refusal_class"]),
        "global_assertions_passed":
            sum(1 for g in results["global_assertions"] if g["pass"]),
        "global_assertions_total": len(results["global_assertions"]),
        "all_pass": (all(c["pass"] for c in results["cases"])
                     and all(g["pass"] for g in results["global_assertions"])),
    }
    payload = json.dumps(results, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with open(RESULTS, "w", encoding="utf-8") as f:
        f.write(payload)
    print(payload)
    return 0 if results["summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
