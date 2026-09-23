#!/usr/bin/env python3
"""Locate the 儲存全部 (Save All) menu item inside a freshly detected menu popup.

v8 class - append-only successor of the attempt-frozen v7-class locator
(sha256 ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a).
It exists to close the attempt-05 false-negative: the v7 reference-order
cross-check demanded an exact OCR match for the non-target item 修改相簿名稱;
a single-glyph misread (稱 -> 般, glyph conf 49.77) made the whole locator
return MENU_CONTENT_UNEXPECTED even though the target row 儲存全部 itself was
read cleanly (word conf 96.95/96.99/96.56).

Design (every gate below is HARD: any non-ELIGIBLE outcome -> no candidate):

* Binding: the frame (SHA-256), a frozen-detector JSON that binds the same
  frame (post path + post_sha256) and carries a fresh popup menu bbox, and a
  frame-SHA-bound window-geometry JSON (window origin/size in points + capture
  scale). Any mismatch -> BAD_INPUT. The menu bbox must additionally pass a
  popup-shape plausibility rule (area/width/height fractions of the frame), so
  a whole-screen false-positive detector pair can never be consumed as a menu.
* Target: the menu-bbox crop is upscaled x3 (LANCZOS) and OCR'd with tesseract
  (`-l chi_tra+eng --psm 6 tsv`, image on stdin) into word boxes. Words are
  clustered into rows by vertical center; a row's CJK text is the concatenation
  of its words' CJK characters. The target item must appear as the exact string
  儲存全部 in exactly one row: no fuzzy / similar-string / partial matching;
  more than one matching row -> AMBIGUOUS, none -> NOT_FOUND.
* Structure (corruption-tolerant, still fail-closed): the menu must contain
  exactly five CJK item rows and, in top-to-bottom order, they must match the
  reference order 選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿.
  The target row must match exactly; each non-target row may differ from its
  reference item by at most ONE substituted character (the reviewed
  single-glyph OCR-variance class observed in attempt-05). Any other count or
  order mismatch -> MENU_CONTENT_UNEXPECTED. The reference order is only
  checked against the observation; it is never used to compute a row position.
* Row geometry safety: every item row band (union of its OCR word boxes) must
  lie inside the menu bbox (1 px rounding epsilon); adjacent bands must not
  overlap; the target band's height must be in range; the target row's word
  centers must be vertically cohesive. Violations -> ROW_GEOMETRY_UNSAFE.
* Candidate: x = midpoint of x_safe = (target band x-range INTERSECT
  addressable x-range) shrunk by a 2 px edge margin, requiring the raw overlap
  to be >= 20 px; the addressable region is the app window rect (from the bound
  geometry) INTERSECT the menu bbox INTERSECT the frame. y = midpoint of the
  target row's y_safe = [max(band.top + edge_margin, above.bottom + 12 px),
  min(band.bottom - edge_margin, below.top - 12 px)] with
  edge_margin = max(6 px, 0.15 x band height). An empty y_safe ->
  ROW_GEOMETRY_UNSAFE; overlap / addressability failures -> NOT_ADDRESSABLE.
  All numbers derive from this frame's own OCR, menu bbox and bound geometry;
  there is no historical-coordinate fallback anywhere in this file.
* Output spaces: frame px (screen), screen pt (= px / capture scale), app-local
  pt (= screen pt - window origin pt). The app-local form is the dispatch form.
* Read-only: no GUI/input capability, no network; the only write site is the
  --out JSON file. Deterministic: identical inputs -> byte-identical output
  (no timestamps, no randomness).

Signal classes: every entry of `checks` is tagged HARD (a false value is a
refusal). `supporting_signals` records facts that are observed but not
thresholded (OCR confidences, per-row match tiers, measured gaps/clearances).

Exit codes: 0 ELIGIBLE, 2 NOT_FOUND, 3 NOT_ADDRESSABLE, 4 AMBIGUOUS,
5 MENU_CONTENT_UNEXPECTED, 6 BAD_INPUT, 7 ROW_GEOMETRY_UNSAFE.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess

from PIL import Image

TARGET_ITEM = "儲存全部"
REFERENCE_ORDER = ["選擇項目", "修改相簿名稱", TARGET_ITEM, "刪除相簿", "分享相簿"]
UPSCALE = 3
OCR_LANG = "chi_tra+eng"
OCR_PSM = "6"

# HARD safety parameters (fixed constants - there are deliberately no runtime
# tuning flags; changing any value changes the file bytes and therefore
# invalidates the freeze record and the independent review).
ROW_TOL_FRACTION = 0.6
ROW_TOL_MIN_PX = 8.0
MIN_OVERLAP_PX = 20.0
X_EDGE_PX = 2.0
EDGE_FRACTION = 0.15
EDGE_MIN_PX = 6.0
NEIGHBOR_SEP_PX = 12.0
MIN_BAND_H_PX = 16.0
MAX_BAND_H_BBOX_FRACTION = 0.5
POPUP_MAX_AREA_FRACTION = 0.30
POPUP_MAX_WIDTH_FRACTION = 0.50
POPUP_MAX_HEIGHT_FRACTION = 0.80
TARGET_SPREAD_MIN_PX = 8.0
TARGET_SPREAD_FRACTION = 0.25
NON_TARGET_SUBSTITUTION_TOLERANCE = 1
BBOX_ROUNDING_EPS_PX = 1.0

CJK_CLASS = "\u3400-\u9fff\u3000-\u303f"
CJK_ANY = re.compile("[%s]" % CJK_CLASS)
NON_CJK = re.compile("[^%s]" % CJK_CLASS)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_ws(text):
    return re.sub(r"\s+", "", text)


def cjk_text(text):
    """CJK characters only (used for item-row identification)."""
    return NON_CJK.sub("", text)


def ocr_word_boxes(image):
    """Return (ok, words, meta). Words carry upscale-space boxes; the caller
    converts them to frame space with to_frame_box()."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    cmd = ["tesseract", "-", "stdout", "-l", OCR_LANG, "--psm", OCR_PSM, "tsv"]
    try:
        proc = subprocess.run(cmd, input=buf.getvalue(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return False, [], {"error": "tesseract not runnable: %r" % (exc,)}
    if proc.returncode != 0:
        return False, [], {"returncode": proc.returncode,
                           "stderr": proc.stderr.decode("utf-8", errors="replace")[:400]}
    words = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) < 12 or parts[0] == "level":
            continue
        if parts[0] != "5":
            continue
        text = parts[11].strip()
        if not text:
            continue
        try:
            left, top, width, height = (float(parts[6]), float(parts[7]),
                                        float(parts[8]), float(parts[9]))
            conf = float(parts[10])
        except ValueError:
            continue
        words.append({"text": text, "conf": conf,
                      "left_up": left, "top_up": top, "w_up": width, "h_up": height})
    return True, words, {"returncode": 0, "command": cmd, "upscale": UPSCALE,
                         "tesseract_version": tesseract_version()}


def tesseract_version():
    try:
        proc = subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        return proc.stdout.decode("utf-8", errors="replace").splitlines()[0].strip()
    except OSError:
        return None


def to_frame_box(word, bbox_x0, bbox_y0):
    x0 = bbox_x0 + word["left_up"] / float(UPSCALE)
    y0 = bbox_y0 + word["top_up"] / float(UPSCALE)
    x1 = bbox_x0 + (word["left_up"] + word["w_up"]) / float(UPSCALE)
    y1 = bbox_y0 + (word["top_up"] + word["h_up"]) / float(UPSCALE)
    return [x0, y0, x1, y1]


def cluster_rows(words, tol_px):
    """Greedy clustering by vertical center; returns rows sorted top->bottom.
    A row's text is the whitespace-stripped left-to-right concatenation of its
    words, so multi-glyph OCR splits still concatenate."""
    rows = []
    for word in sorted(words, key=lambda w: (w["box"][1] + w["box"][3]) / 2.0):
        cy = (word["box"][1] + word["box"][3]) / 2.0
        if rows and abs(cy - rows[-1]["mean_cy"]) <= tol_px:
            row = rows[-1]
            row["words"].append(word)
            row["sum_cy"] += cy
            row["mean_cy"] = row["sum_cy"] / len(row["words"])
        else:
            rows.append({"words": [word], "sum_cy": cy, "mean_cy": cy})
    for row in rows:
        ws = sorted(row["words"], key=lambda w: w["box"][0])
        row["text"] = strip_ws("".join(w["text"] for w in ws))
        row["cjk_text"] = cjk_text(row["text"])
        row["box"] = [min(w["box"][0] for w in ws), min(w["box"][1] for w in ws),
                      max(w["box"][2] for w in ws), max(w["box"][3] for w in ws)]
    rows.sort(key=lambda r: r["mean_cy"])
    for index, row in enumerate(rows):
        row["index"] = index
        row["mean_cy"] = round(row["mean_cy"], 3)
    return rows


def intersect(a, b):
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return None
    return [x0, y0, x1, y1]


def match_reference(text, ref, tolerance):
    """Match one reference item against one row's CJK text.

    EXACT: ref is a substring of text. TOLERANT: some length-equal window of
    text differs from ref by at most `tolerance` substituted characters. No
    insertions/deletions are ever accepted (length must match), and the target
    item itself is always matched with tolerance 0.
    """
    if ref in text:
        return True, "EXACT", None
    n = len(ref)
    if n == 0 or len(text) < n:
        return False, None, None
    for i in range(0, len(text) - n + 1):
        if sum(1 for a, b in zip(text[i:i + n], ref) if a != b) <= tolerance:
            return True, "TOLERANT_%d_SUB" % tolerance, [i, i + n]
    return False, None, None


def r3(value):
    return round(float(value), 3)


def evaluate(frame_size, bbox, scale, window_pos_pt, window_size_pt, words):
    """Pure decision core (no file I/O, no OCR, no subprocess).

    Every refusal path returns without a candidate. The function is the same
    code path used by the CLI; the deterministic selftest drives it directly
    with synthetic word-box fixtures.
    """
    result = {}
    checks = []

    def fail(verdict, code, reason):
        result["checks"] = checks
        result["verdict"] = verdict
        result["exit_code"] = code
        result["reason"] = reason
        return result

    frame_w, frame_h = frame_size
    bbox_w = bbox[2] - bbox[0]
    bbox_h = bbox[3] - bbox[1]
    shape = {
        "bbox_frame_px": [r3(v) for v in bbox],
        "bbox_w_px": r3(bbox_w), "bbox_h_px": r3(bbox_h),
        "area_fraction": r3(bbox_w * bbox_h / float(frame_w * frame_h)),
        "width_fraction": r3(bbox_w / float(frame_w)),
        "height_fraction": r3(bbox_h / float(frame_h)),
        "limits": {"max_area_fraction": POPUP_MAX_AREA_FRACTION,
                   "max_width_fraction": POPUP_MAX_WIDTH_FRACTION,
                   "max_height_fraction": POPUP_MAX_HEIGHT_FRACTION},
    }
    shape_ok = (shape["area_fraction"] <= POPUP_MAX_AREA_FRACTION
                and shape["width_fraction"] <= POPUP_MAX_WIDTH_FRACTION
                and shape["height_fraction"] <= POPUP_MAX_HEIGHT_FRACTION)
    checks.append({"name": "popup_shape", "class": "HARD", "pass": shape_ok,
                   "detail": shape})
    if not shape_ok:
        return fail("BAD_INPUT", 6,
                    "menu bbox fails the popup-shape plausibility rule")

    if not words:
        checks.append({"name": "ocr_words_present", "class": "HARD", "pass": False,
                       "detail": {"word_count": 0}})
        return fail("NOT_FOUND", 2, "no OCR words inside the menu bbox")

    heights = sorted(w["box"][3] - w["box"][1] for w in words)
    median_h = heights[len(heights) // 2]
    tol_px = max(ROW_TOL_MIN_PX, ROW_TOL_FRACTION * median_h)
    rows = cluster_rows(words, tol_px)

    result["params"] = {
        "upscale": UPSCALE, "ocr_lang": OCR_LANG, "ocr_psm": OCR_PSM,
        "row_tol_fraction": ROW_TOL_FRACTION, "row_tol_min_px": ROW_TOL_MIN_PX,
        "median_word_height_px": r3(median_h), "row_tol_px": r3(tol_px),
        "min_overlap_px": MIN_OVERLAP_PX, "x_edge_px": X_EDGE_PX,
        "edge_fraction": EDGE_FRACTION, "edge_min_px": EDGE_MIN_PX,
        "neighbor_sep_px": NEIGHBOR_SEP_PX, "min_band_h_px": MIN_BAND_H_PX,
        "max_band_h_bbox_fraction": MAX_BAND_H_BBOX_FRACTION,
        "non_target_substitution_tolerance": NON_TARGET_SUBSTITUTION_TOLERANCE,
    }
    result["rows"] = [{"index": r["index"], "text": r["text"],
                       "cjk_text": r["cjk_text"], "mean_cy_px": r["mean_cy"],
                       "band_frame_px": [r3(v) for v in r["box"]],
                       "word_count": len(r["words"])} for r in rows]

    target_rows = [r for r in rows if TARGET_ITEM in r["cjk_text"]]
    checks.append({"name": "target_unique_row", "class": "HARD",
                   "pass": len(target_rows) == 1,
                   "detail": {"matching_row_indices": [r["index"] for r in target_rows],
                              "target_item": TARGET_ITEM,
                              "rule": "exact string, no fuzzy/partial matching"}})
    if len(target_rows) > 1:
        return fail("AMBIGUOUS", 4, "target item text found in more than one row")
    if not target_rows:
        return fail("NOT_FOUND", 2, "target item text not found in any row")
    target = target_rows[0]

    item_rows = [r for r in rows if r["cjk_text"]]
    structure = {
        "expected_item_count": len(REFERENCE_ORDER),
        "item_row_indices": [r["index"] for r in item_rows],
        "item_row_cjk_texts": [r["cjk_text"] for r in item_rows],
        "matches": [],
        "target_position_ok": None,
    }
    structure_ok = len(item_rows) == len(REFERENCE_ORDER)
    if structure_ok:
        for i, ref in enumerate(REFERENCE_ORDER):
            tolerance = 0 if ref == TARGET_ITEM else NON_TARGET_SUBSTITUTION_TOLERANCE
            ok_row, tier, span = match_reference(item_rows[i]["cjk_text"], ref, tolerance)
            structure["matches"].append({"row_index": item_rows[i]["index"],
                                         "observed_cjk_text": item_rows[i]["cjk_text"],
                                         "expected": ref, "tier": tier,
                                         "span": span, "pass": ok_row})
            if not ok_row:
                structure_ok = False
        structure["target_position_ok"] = (item_rows[2]["index"] == target["index"])
        if not structure["target_position_ok"]:
            structure_ok = False
    checks.append({"name": "reference_structure", "class": "HARD",
                   "pass": structure_ok, "detail": structure})
    if not structure_ok:
        return fail("MENU_CONTENT_UNEXPECTED", 5,
                    "five-item reference structure not matched around the target row")

    band = target["box"]
    band_h = band[3] - band[1]
    above = item_rows[1]
    below = item_rows[3]
    geo = {
        "item_bands_frame_px": [{"row_index": r["index"],
                                 "band_frame_px": [r3(v) for v in r["box"]]}
                                for r in item_rows],
        "consecutive_band_gaps_px": [],
        "target_band_height_px": r3(band_h),
        "band_height_range_px": [MIN_BAND_H_PX,
                                 r3(MAX_BAND_H_BBOX_FRACTION * bbox_h)],
        "outside_bbox": [],
        "overlapping_pairs": [],
    }
    geo_ok = True
    for r in item_rows:
        b = r["box"]
        if not (b[0] >= bbox[0] - BBOX_ROUNDING_EPS_PX
                and b[1] >= bbox[1] - BBOX_ROUNDING_EPS_PX
                and b[2] <= bbox[2] + BBOX_ROUNDING_EPS_PX
                and b[3] <= bbox[3] + BBOX_ROUNDING_EPS_PX):
            geo["outside_bbox"].append(r["index"])
            geo_ok = False
    for i in range(len(item_rows) - 1):
        gap = item_rows[i + 1]["box"][1] - item_rows[i]["box"][3]
        geo["consecutive_band_gaps_px"].append(r3(gap))
        if item_rows[i + 1]["box"][1] < item_rows[i]["box"][3]:
            geo["overlapping_pairs"].append([item_rows[i]["index"],
                                             item_rows[i + 1]["index"]])
            geo_ok = False
    if not (MIN_BAND_H_PX <= band_h <= MAX_BAND_H_BBOX_FRACTION * bbox_h):
        geo_ok = False
    centers = [(w["box"][1] + w["box"][3]) / 2.0 for w in target["words"]]
    spread = max(centers) - min(centers)
    spread_tol = max(TARGET_SPREAD_MIN_PX, TARGET_SPREAD_FRACTION * band_h)
    geo["target_word_center_spread_px"] = r3(spread)
    geo["target_spread_tolerance_px"] = r3(spread_tol)
    if spread > spread_tol:
        geo_ok = False
    checks.append({"name": "row_geometry", "class": "HARD", "pass": geo_ok,
                   "detail": geo})
    if not geo_ok:
        return fail("ROW_GEOMETRY_UNSAFE", 7,
                    "target/row band geometry fails the safety rules")

    wx, wy = window_pos_pt
    ww, wh = window_size_pt
    window_rect = [wx * scale, wy * scale, (wx + ww) * scale, (wy + wh) * scale]
    frame_rect = [0.0, 0.0, float(frame_w), float(frame_h)]
    window_bbox = intersect(window_rect, bbox)
    addr = intersect(window_bbox, frame_rect) if window_bbox else None
    result["window_rect_px"] = [r3(v) for v in window_rect]
    result["addressable_region_frame_px"] = [r3(v) for v in addr] if addr else None
    if addr is None:
        checks.append({"name": "addressable_region", "class": "HARD", "pass": False,
                       "detail": {"window_rect_px": result["window_rect_px"]}})
        return fail("NOT_ADDRESSABLE", 3,
                    "menu bbox does not intersect the app window/frame")

    ox0, ox1 = max(band[0], addr[0]), min(band[2], addr[2])
    overlap_w = ox1 - ox0
    overlap_ok = overlap_w >= MIN_OVERLAP_PX
    checks.append({"name": "x_overlap", "class": "HARD", "pass": overlap_ok,
                   "detail": {"target_band_x_range": [r3(band[0]), r3(band[2])],
                              "addressable_x_range": [r3(addr[0]), r3(addr[2])],
                              "overlap_x_range": [r3(ox0), r3(ox1)],
                              "overlap_width_px": r3(overlap_w),
                              "min_required_px": MIN_OVERLAP_PX}})
    if not overlap_ok:
        return fail("NOT_ADDRESSABLE", 3,
                    "text-box x-overlap with the addressable region is below the rule")

    x_safe = [ox0 + X_EDGE_PX, ox1 - X_EDGE_PX]
    x_safe_ok = x_safe[1] > x_safe[0]
    checks.append({"name": "x_safe_region", "class": "HARD", "pass": x_safe_ok,
                   "detail": {"x_safe_frame_px": [r3(v) for v in x_safe],
                              "x_edge_px": X_EDGE_PX}})
    if not x_safe_ok:
        return fail("NOT_ADDRESSABLE", 3, "candidate x safe region is empty")

    edge_margin = max(EDGE_MIN_PX, EDGE_FRACTION * band_h)
    y_lo = max(band[1] + edge_margin, above["box"][3] + NEIGHBOR_SEP_PX)
    y_hi = min(band[3] - edge_margin, below["box"][1] - NEIGHBOR_SEP_PX)
    y_safe_ok = y_lo <= y_hi
    y_detail = {"y_safe_frame_px": [r3(y_lo), r3(y_hi)],
                "edge_margin_px": r3(edge_margin),
                "neighbor_separation_px": NEIGHBOR_SEP_PX,
                "constraints": {
                    "band_top_plus_edge": r3(band[1] + edge_margin),
                    "above_bottom_plus_sep": r3(above["box"][3] + NEIGHBOR_SEP_PX),
                    "band_bottom_minus_edge": r3(band[3] - edge_margin),
                    "below_top_minus_sep": r3(below["box"][1] - NEIGHBOR_SEP_PX)}}
    checks.append({"name": "y_safe_region", "class": "HARD", "pass": y_safe_ok,
                   "detail": y_detail})
    if not y_safe_ok:
        return fail("ROW_GEOMETRY_UNSAFE", 7,
                    "candidate y safe region is empty (row boundary / neighbor collision)")

    cx = (x_safe[0] + x_safe[1]) / 2.0
    cy = (y_lo + y_hi) / 2.0
    candidate_screen = [cx / scale, cy / scale]
    candidate_app_local = [candidate_screen[0] - wx, candidate_screen[1] - wy]
    placement = {
        "candidate_inside_menu_bbox": bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3],
        "candidate_inside_addressable_region": addr[0] <= cx <= addr[2] and addr[1] <= cy <= addr[3],
        "candidate_inside_y_safe_region": y_lo <= cy <= y_hi,
        "candidate_inside_target_band": band[1] <= cy <= band[3],
        "candidate_clear_of_row_edges": (cy - band[1] >= edge_margin
                                         and band[3] - cy >= edge_margin),
        "candidate_clear_of_neighbor_rows": (cy - above["box"][3] >= NEIGHBOR_SEP_PX
                                             and below["box"][1] - cy >= NEIGHBOR_SEP_PX),
    }
    placement_ok = all(placement.values())
    checks.append({"name": "candidate_placement", "class": "HARD", "pass": placement_ok,
                   "detail": placement})
    if not placement_ok:
        return fail("ROW_GEOMETRY_UNSAFE", 7,
                    "candidate placement check failed")

    result["target"] = {
        "text": TARGET_ITEM, "row_index": target["index"],
        "cjk_text": target["cjk_text"],
        "band_frame_px": [r3(v) for v in band],
        "words": [{"text": w["text"], "conf": r3(w["conf"]),
                   "box_frame_px": [r3(v) for v in w["box"]]}
                  for w in sorted(target["words"], key=lambda w: w["box"][0])],
    }
    result["neighbors"] = {
        "above": {"row_index": above["index"], "cjk_text": above["cjk_text"],
                  "expected": REFERENCE_ORDER[1],
                  "band_frame_px": [r3(v) for v in above["box"]]},
        "below": {"row_index": below["index"], "cjk_text": below["cjk_text"],
                  "expected": REFERENCE_ORDER[3],
                  "band_frame_px": [r3(v) for v in below["box"]]},
    }
    result["candidate"] = {
        "frame_px": [r3(cx), r3(cy)],
        "screen_pt": [r3(candidate_screen[0]), r3(candidate_screen[1])],
        "app_local_pt": [r3(candidate_app_local[0]), r3(candidate_app_local[1])],
    }
    result["candidate_derivation"] = {
        "x_safe_frame_px": [r3(x_safe[0]), r3(x_safe[1])],
        "y_safe_frame_px": [r3(y_lo), r3(y_hi)],
        "rule": "x = midpoint(x_safe); y = midpoint(y_safe)",
        "edge_margin_px": r3(edge_margin),
        "neighbor_separation_px": NEIGHBOR_SEP_PX,
    }
    result["clearances_px"] = {
        "candidate_to_band_top": r3(cy - band[1]),
        "candidate_to_band_bottom": r3(band[3] - cy),
        "candidate_to_above_band": r3(cy - above["box"][3]),
        "candidate_to_below_band": r3(below["box"][1] - cy),
        "candidate_to_bbox_left": r3(cx - bbox[0]),
        "candidate_to_bbox_right": r3(bbox[2] - cx),
        "candidate_to_bbox_top": r3(cy - bbox[1]),
        "candidate_to_bbox_bottom": r3(bbox[3] - cy),
    }
    result["supporting_signals"] = {
        "note": ("observed but not thresholded; every refusal-driving gate is in "
                 "`checks` (class HARD)"),
        "target_word_confidences": [r3(w["conf"]) for w in result["target"]["words"]],
        "row_match_tiers": [m["tier"] for m in structure["matches"]],
        "consecutive_band_gaps_px": geo["consecutive_band_gaps_px"],
    }
    result["checks"] = checks
    result["signal_classes"] = {
        "HARD": [c["name"] for c in checks],
        "SUPPORTING": ["supporting_signals"],
    }
    result["verdict"] = "ELIGIBLE"
    result["reason"] = ("exactly one exact-match target row; five-item reference "
                        "structure matched (single-glyph tolerance on non-target rows); "
                        "row geometry and candidate safe regions pass")
    result["exit_code"] = 0
    return result


def emit(result, out_path):
    payload = json.dumps(result, ensure_ascii=False, indent=1, sort_keys=False)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def finish(result, out_path, verdict, code, reason):
    result["verdict"] = verdict
    result["reason"] = reason
    result["exit_code"] = code
    emit(result, out_path)
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--detector-json", required=True,
                    help="frozen detect_menu_popup result JSON binding this frame")
    ap.add_argument("--geometry", required=True,
                    help="frame-SHA-bound window geometry JSON")
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {"tool": "locate_save_all_menu_item", "version": "v8",
              "class": ("v8-class Save All menu-item locator; append-only successor "
                        "of the frozen v7-class locator "
                        "ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a"),
              "frame": args.frame}

    for path in (args.frame, args.detector_json, args.geometry):
        if not path or not str(path).strip() or not os.path.exists(path):
            return finish(result, args.out, "BAD_INPUT", 6, "missing input: %r" % path)

    result["tool_sha256"] = sha256_file(os.path.abspath(__file__))
    frame_sha = sha256_file(args.frame)
    result["frame_sha256"] = frame_sha
    try:
        frame = Image.open(args.frame).convert("RGB")
    except Exception as exc:  # unreadable frame
        return finish(result, args.out, "BAD_INPUT", 6, "unreadable frame: %r" % (exc,))
    result["frame_size"] = list(frame.size)

    try:
        detector = json.load(open(args.detector_json, encoding="utf-8"))
    except Exception as exc:
        return finish(result, args.out, "BAD_INPUT", 6, "unreadable detector json: %r" % (exc,))
    result["detector"] = {"json": args.detector_json,
                          "json_sha256": sha256_file(args.detector_json),
                          "tool": detector.get("tool"),
                          "verdict": detector.get("verdict"),
                          "pre": detector.get("pre"),
                          "post": detector.get("post"),
                          "post_sha256": detector.get("post_sha256"),
                          "chosen_bbox": detector.get("chosen_bbox")}
    if detector.get("tool") != "detect_menu_popup" or detector.get("verdict") != "MENU_DETECTED":
        return finish(result, args.out, "BAD_INPUT", 6, "detector json is not a MENU_DETECTED result")
    if detector.get("post") != args.frame or detector.get("post_sha256") != frame_sha:
        return finish(result, args.out, "BAD_INPUT", 6, "detector json does not bind this frame")
    bbox = detector.get("chosen_bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4 and bbox[2] > bbox[0] and bbox[3] > bbox[1]):
        return finish(result, args.out, "BAD_INPUT", 6, "detector json has no valid chosen_bbox")
    bbox = [float(v) for v in bbox]
    if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > frame.size[0] or bbox[3] > frame.size[1]:
        return finish(result, args.out, "BAD_INPUT", 6, "menu bbox outside frame bounds")

    try:
        geometry = json.load(open(args.geometry, encoding="utf-8"))
    except Exception as exc:
        return finish(result, args.out, "BAD_INPUT", 6, "unreadable geometry json: %r" % (exc,))
    result["geometry"] = {"json": args.geometry,
                          "json_sha256": sha256_file(args.geometry),
                          "frame_sha256": geometry.get("frame_sha256"),
                          "capture_scale": geometry.get("capture_scale"),
                          "window_index": geometry.get("window_index"),
                          "window_position_points": geometry.get("window_position_points"),
                          "window_size_points": geometry.get("window_size_points")}
    if geometry.get("frame_sha256") != frame_sha:
        return finish(result, args.out, "BAD_INPUT", 6, "geometry json is not bound to this frame")
    scale = geometry.get("capture_scale")
    wx, wy = geometry.get("window_position_points") or (None, None)
    ww, wh = geometry.get("window_size_points") or (None, None)
    if not (isinstance(scale, (int, float)) and scale > 0
            and isinstance(wx, (int, float)) and isinstance(wy, (int, float))
            and isinstance(ww, (int, float)) and isinstance(wh, (int, float))):
        return finish(result, args.out, "BAD_INPUT", 6, "geometry json lacks window rect/capture scale")

    crop = frame.crop((int(round(bbox[0])), int(round(bbox[1])),
                       int(round(bbox[2])), int(round(bbox[3]))))
    up = crop.resize((max(1, crop.size[0] * UPSCALE), max(1, crop.size[1] * UPSCALE)),
                     Image.LANCZOS)
    ok, words, ocr_meta = ocr_word_boxes(up)
    result["ocr"] = ocr_meta
    if not ok:
        return finish(result, args.out, "BAD_INPUT", 6, "OCR could not run (fail-closed)")

    for word in words:
        word["box"] = to_frame_box(word, bbox[0], bbox[1])
    result["ocr"]["word_count"] = len(words)
    result["ocr"]["words"] = [{"text": w["text"], "conf": r3(w["conf"]),
                               "box_frame_px": [r3(v) for v in w["box"]]}
                              for w in words]

    decision = evaluate(frame.size, bbox, scale, (wx, wy), (ww, wh), words)
    for key, value in decision.items():
        result[key] = value
    return finish(result, args.out, decision["verdict"], decision["exit_code"],
                  decision["reason"])


if __name__ == "__main__":
    raise SystemExit(main())
