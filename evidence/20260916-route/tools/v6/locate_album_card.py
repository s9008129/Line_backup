#!/usr/bin/env python3
"""v6 album-card S3 safety locator - LINE-window-local, current-frame-only.

Scope: album-card S3 safety decision ONLY. v6 does not locate an ellipsis,
does not verify an album-open (S5) and does not detect menus. It produces an
offline evidence verdict; it NEVER dispatches input.

Safety architecture (why this exists):
  Frozen v4 evaluated bright-content bands by the mean of the ENTIRE
  screenshot row (all x of the frame). On a full-screen frame where the LINE
  window occupies only part of the width, that domain mixes unrelated
  application pixels into the margin rule; v4 returned UNSAFE_MARGINS with
  margin_below_px = null in three distinct arrangements even though the
  target card's local geometry (grid above / caption strip / grid below) was
  intact (see evidence/20260921-replan-v6/attempt-01/v4-failure-analysis.md).

  v6 keeps the frozen identity semantics (OCR title must match the expected
  date range; count mismatch refuses) and replaces the spatial domain: all
  geometry is measured inside a caller-supplied LINE-window ROI that is
  bound to THIS frame's SHA-256, using the frame's own local background color
  (theme-adaptive; the observed surface may be light or dark). The candidate
  point is derived from this frame's OCR title box exactly as v4 derived it
  (title left edge + 12 px, title vertical centre) and must sit inside the
  caption strip between the two local content bands, with bounded separation
  to those bands and to the caption's right-side control (the ellipsis),
  with fail-closed refusals when any structure is unresolved.

Refusals (exit codes):
  2 TARGET_TITLE_NOT_FOUND, 4 UNSAFE_MARGINS, 5 TARGET_COUNT_MISMATCH,
  6 BAD_FRAME, 7 WINDOW_ROI_MISSING_OR_INVALID, 8 IDENTITY_NOT_ROI_BOUND,
  9 CARD_STRUCTURE_UNRESOLVED, 10 STRIP_CONTENT_UNEXPECTED,
  11 CANDIDATE_OUT_OF_BOUNDS.  0 = ELIGIBLE.

No fallback to a v4 candidate. No historical coordinate is accepted: the
window-geometry input must carry the SHA-256 of the frame being analysed and
is refused on mismatch. Unreadable count text is recorded but is not a
refusal (same semantics as frozen v4); a readable count different from the
expected one refuses.

Title/count logic is copied from the frozen v4 tool
(evidence/20260916-route/tools/v4/locate_album_card.py
sha256 bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162);
OCR uses the frozen v4 vision_reader module
(sha256 22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8)
without modifying it. v4/v5 files are never written by v6.

Interpreter: /opt/homebrew/bin/python3 (Pillow + numpy required).
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
from collections import deque

import numpy as np
from PIL import Image

V4_READER_SHA256 = "22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8"
V4_LOCATE_SHA256 = "bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162"

# --- v6 safety constants (documented; see tools/v6/README.md) ---
CONTENT_DIFF = 60        # per-pixel max-channel distance from local background
BAND_FRAC_THRESHOLD = 0.45   # row content fraction that marks a content band
BAND_MIN_ROWS = 20       # a real photo-grid band is far thicker than this
STRIP_FRAC_MAX = 0.30    # rows of the caption strip stay below this
STRIP_MIN_ROWS = 40      # a caption strip thinner than this is not trusted
BG_MAD_MAX = 5.0         # sampled background patch must be flat
SEP_MIN_ABS_PX = 24      # absolute floor for candidate->content separation
SEP_MIN_TITLE_H = 1.0    # separation floor in title-height units
ROI_MIN_W, ROI_MIN_H = 200, 200
ROI_INSET_PX = 8         # identity must sit this far inside the ROI
ROI_RIGHT_TAIL_PX = 120  # ROI must extend this far right of the title box
ROI_CANDIDATE_MARGIN_PX = 16
CONTROL_MAX_W, CONTROL_MAX_H = 48, 80
CONTROL_MIN_GAP_PX = 100  # control must sit this far right of title/candidate
CLUSTER_MIN_PX = 5
CLUSTER_MERGE_GAP = 12
SCAN_RANGE_PX = 500


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_sibling_v4_reader():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(here, os.pardir, "v4", "vision_reader.py"))
    spec = importlib.util.spec_from_file_location("v4_vision_reader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vision_reader = _load_sibling_v4_reader()


def digits(text):
    return re.sub(r"\D", "", text)


def find_title(words, expect_start, expect_end):
    """Copied verbatim from frozen v4 locate_album_card.py (sha bb52aff1...)."""
    want_start = digits(expect_start)
    end_keys = {digits(expect_end), digits(expect_end)[-4:]}
    if not want_start or not all(end_keys):
        return None
    candidates = []
    for i in range(len(words)):
        combined = ""
        for j in range(i, min(i + 4, len(words))):
            combined += digits(words[j]["text"])
            if len(combined) > 24:
                break
            if want_start in combined:
                rest = combined[combined.index(want_start) + len(want_start):]
                if any(key in rest for key in end_keys):
                    candidates.append((j - i, len(combined), i, j))
    if not candidates:
        return None
    _, _, i0, i1 = min(candidates)
    sel = words[i0:i1 + 1]
    x0 = min(w["x"] for w in sel)
    y0 = min(w["y"] for w in sel)
    x1 = max(w["x"] + w["w"] for w in sel)
    y1 = max(w["y"] + w["h"] for w in sel)
    return {"texts": [w["text"] for w in sel],
            "bbox": [round(x0), round(y0), round(x1), round(y1)]}


def ocr_words(im, scale=3, psm=6):
    return vision_reader.read_words(im, scale) or []


def ocr_digits_region(im, box, scale=10, psm=7):
    crop = im.crop(box)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        return ""
    words = vision_reader.read_words(crop, scale) or []
    return digits("".join(w["text"] for w in words))


def load_geometry(path, frame_sha256, width, height):
    """Return (rect, record) or (None, reason). Fail-closed on every problem."""
    if not path:
        return None, "window geometry not provided"
    if not os.path.exists(path):
        return None, "window geometry file missing"
    try:
        with open(path, "r", encoding="utf-8") as f:
            geo = json.load(f)
    except (OSError, ValueError):
        return None, "window geometry file unreadable or not JSON"
    if not isinstance(geo, dict):
        return None, "window geometry is not an object"
    rect_keys = ["x0", "y0", "x1", "y1"]
    for key in rect_keys + ["source", "frame_sha256"]:
        if key not in geo:
            return None, "window geometry missing field %s" % key
    for key in rect_keys:
        value = geo[key]
        if isinstance(value, bool) or not isinstance(value, int):
            return None, "window geometry field %s is not an integer" % key
    x0, y0, x1, y1 = geo["x0"], geo["y0"], geo["x1"], geo["y1"]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        return None, "window geometry rect outside frame or inverted"
    if x1 - x0 < ROI_MIN_W or y1 - y0 < ROI_MIN_H:
        return None, "window geometry rect too small"
    source = geo["source"]
    if not isinstance(source, str) or not source.strip():
        return None, "window geometry source missing"
    if str(geo["frame_sha256"]).lower() != frame_sha256.lower():
        return None, "window geometry is not bound to this frame (sha256 mismatch)"
    record = {"path": path, "rect": [x0, y0, x1, y1], "source": source,
              "frame_sha256": geo["frame_sha256"], "raw": geo}
    return (x0, y0, x1, y1), record


def rows_content_fraction(rgb, bg, x0, x1):
    seg = rgb[:, x0:x1, :]
    diff = np.abs(seg - bg[None, None, :]).max(axis=2)
    return (diff >= CONTENT_DIFF).mean(axis=1)


def threshold_runs(frac, y_from, y_to, threshold):
    """Contiguous [start, end] runs (inclusive) with frac >= threshold inside y range."""
    runs = []
    y = min(y_from, y_to)
    end = max(y_from, y_to)
    while y <= end:
        if frac[y] >= threshold:
            s = y
            while y + 1 <= end and frac[y + 1] >= threshold:
                y += 1
            runs.append((s, y))
        y += 1
    return runs


def connected_components(mask, x_offset, y_offset):
    """Sparse deterministic 8-connected components over a bool numpy mask."""
    ys, xs = np.nonzero(mask)
    cells = set(zip(ys.tolist(), xs.tolist()))
    comps = []
    while cells:
        seed = min(cells)
        cells.discard(seed)
        q = deque([seed])
        miny = maxy = seed[0]
        minx = maxx = seed[1]
        n = 0
        while q:
            y, x = q.popleft()
            n += 1
            miny = min(miny, y)
            maxy = max(maxy, y)
            minx = min(minx, x)
            maxx = max(maxx, x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    cell = (y + dy, x + dx)
                    if cell in cells:
                        cells.discard(cell)
                        q.append(cell)
        comps.append({"n": n, "x0": minx + x_offset, "x1": maxx + x_offset,
                      "y0": miny + y_offset, "y1": maxy + y_offset})
    return comps


def merge_close(comps, gap):
    comps = [dict(c) for c in comps]
    changed = True
    while changed:
        changed = False
        out = []
        used = [False] * len(comps)
        for i in range(len(comps)):
            if used[i]:
                continue
            a = dict(comps[i])
            for j in range(i + 1, len(comps)):
                if used[j]:
                    continue
                b = comps[j]
                if (b["x0"] > a["x1"] + gap or a["x0"] > b["x1"] + gap
                        or b["y0"] > a["y1"] + gap or a["y0"] > b["y1"] + gap):
                    continue
                a = {"n": a["n"] + b["n"], "x0": min(a["x0"], b["x0"]),
                     "x1": max(a["x1"], b["x1"]), "y0": min(a["y0"], b["y0"]),
                     "y1": max(a["y1"], b["y1"])}
                used[j] = True
                changed = True
            out.append(a)
            used[i] = True
        comps = out
    return comps


def emit(result, out_path):
    result["reader"] = vision_reader.record()
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--expect-start", required=True)
    ap.add_argument("--expect-end", required=True)
    ap.add_argument("--expect-count", default="57")
    ap.add_argument("--window-geometry", required=False)
    ap.add_argument("--out")
    args = ap.parse_args()

    tool_sha = sha256_file(os.path.abspath(__file__))
    result = {
        "tool": "locate_album_card_v6",
        "tool_sha256": tool_sha,
        "scope": "album-card S3 safety location only; offline evidence; never dispatched",
        "frame": args.frame,
        "expected": {"start": args.expect_start, "end": args.expect_end,
                     "count": args.expect_count},
        "constants": {
            "content_diff": CONTENT_DIFF, "band_frac_threshold": BAND_FRAC_THRESHOLD,
            "band_min_rows": BAND_MIN_ROWS, "strip_frac_max": STRIP_FRAC_MAX,
            "strip_min_rows": STRIP_MIN_ROWS, "bg_mad_max": BG_MAD_MAX,
            "sep_min": "max(%d, title_height * %.1f)" % (SEP_MIN_ABS_PX, SEP_MIN_TITLE_H),
            "roi_inset_px": ROI_INSET_PX, "roi_right_tail_px": ROI_RIGHT_TAIL_PX,
            "roi_candidate_margin_px": ROI_CANDIDATE_MARGIN_PX,
            "control_max_wh": [CONTROL_MAX_W, CONTROL_MAX_H],
            "control_min_gap_px": CONTROL_MIN_GAP_PX,
            "cluster_min_px": CLUSTER_MIN_PX, "cluster_merge_gap": CLUSTER_MERGE_GAP,
            "scan_range_px": SCAN_RANGE_PX},
        "provenance": {
            "title_count_logic_copied_from": {
                "path": "evidence/20260916-route/tools/v4/locate_album_card.py",
                "sha256": V4_LOCATE_SHA256},
            "reader": {"module": "evidence/20260916-route/tools/v4/vision_reader.py",
                       "sha256": V4_READER_SHA256},
            "historical_coordinates_used": False,
            "fallback_to_v4_candidate": False},
    }

    if not os.path.exists(args.frame):
        result["verdict"] = "BAD_FRAME"
        emit(result, args.out)
        return 6
    try:
        with open(args.frame, "rb") as f:
            frame_bytes = f.read()
        result["frame_sha256"] = sha256_bytes(frame_bytes)
        result["frame_bytes"] = len(frame_bytes)
        im_rgb = Image.open(io.BytesIO(frame_bytes))
        im_rgb.load()
        width, height = im_rgb.size
        result["frame_size"] = [width, height]
        im_gray = im_rgb.convert("L")
        rgb = np.asarray(im_rgb.convert("RGB"), dtype=np.int16)
    except Exception:
        result["verdict"] = "BAD_FRAME"
        emit(result, args.out)
        return 6

    # Identity is machine-read from THIS frame before any geometry is trusted.
    words = ocr_words(im_gray)
    title = find_title(words, args.expect_start, args.expect_end)
    result["title"] = title
    result["ocr_words_seen"] = [w["text"] for w in words][:60]
    if not title:
        result["verdict"] = "TARGET_TITLE_NOT_FOUND"
        emit(result, args.out)
        return 2

    # The analysis region must be supplied as an input artifact bound to this
    # exact frame (sha256). Missing/unbound/implausible geometry refuses.
    rect, geo_record = load_geometry(args.window_geometry, result["frame_sha256"], width, height)
    if rect is None:
        result["window_geometry"] = {"error": geo_record}
        result["verdict"] = "WINDOW_ROI_MISSING_OR_INVALID"
        emit(result, args.out)
        return 7
    result["window_geometry"] = geo_record
    result["coordinate_space"] = ("current-frame screenshot pixels (device pixels of the "
                                  "full-screen capture); window ROI and click_point share "
                                  "this space")
    roi_x0, roi_y0, roi_x1, roi_y1 = rect

    tx0, ty0, tx1, ty1 = title["bbox"]
    center_y = (ty0 + ty1) // 2
    title_h = ty1 - ty0
    click_point = [tx0 + 12, center_y]
    result["click_point"] = click_point
    result["click_point_derivation"] = "title left edge + 12 px, title vertical centre"

    candidate_checks = {
        "title_width_px": tx1 - tx0,
        "candidate_x": click_point[0],
        "roi_left_margin_px": click_point[0] - roi_x0,
        "roi_right_margin_px": roi_x1 - click_point[0],
    }
    result["candidate_bounds"] = candidate_checks
    if (tx1 - tx0 < 24 or click_point[0] < roi_x0 + ROI_CANDIDATE_MARGIN_PX
            or click_point[0] > roi_x1 - ROI_CANDIDATE_MARGIN_PX):
        result["verdict"] = "CANDIDATE_OUT_OF_BOUNDS"
        emit(result, args.out)
        return 11

    count_box = (max(0, tx0 - 8), ty1 + 2, min(width, tx0 + 160), min(height, ty1 + 32))
    identity = {
        "title_bbox": [tx0, ty0, tx1, ty1],
        "title_inset_px": {"left": tx0 - roi_x0, "top": ty0 - roi_y0,
                           "right": roi_x1 - tx1, "bottom": roi_y1 - ty1},
        "count_box": list(count_box),
        "roi_right_tail_px": roi_x1 - tx1,
    }
    result["identity"] = identity
    if (identity["title_inset_px"]["left"] < ROI_INSET_PX
            or identity["title_inset_px"]["top"] < ROI_INSET_PX
            or identity["title_inset_px"]["right"] < ROI_INSET_PX
            or identity["title_inset_px"]["bottom"] < ROI_INSET_PX
            or count_box[0] < roi_x0 or count_box[2] > roi_x1
            or count_box[3] > roi_y1
            or identity["roi_right_tail_px"] < ROI_RIGHT_TAIL_PX):
        result["verdict"] = "IDENTITY_NOT_ROI_BOUND"
        emit(result, args.out)
        return 8

    count_digits = ocr_digits_region(im_gray, count_box)
    result["count_box"] = list(count_box)
    result["count_digits_read"] = count_digits
    if count_digits == "":
        result["count_text"] = "UNREADABLE"
    elif args.expect_count in count_digits:
        result["count_text"] = "MATCH"
    else:
        result["count_text"] = "MISMATCH"
    if result["count_text"] == "MISMATCH":
        result["verdict"] = "TARGET_COUNT_MISMATCH"
        emit(result, args.out)
        return 5

    # ---- local background sample (right of the title text, same row band) ----
    sx0 = tx1 + 24
    sx1 = min(tx1 + 84, roi_x1 - 8)
    sample = rgb[ty0:ty1 + 1, sx0:sx1 + 1, :].reshape(-1, 3)
    if sx1 - sx0 < 20 or sample.shape[0] < 10:
        result["background"] = {"error": "background sample region unavailable"}
        result["verdict"] = "CARD_STRUCTURE_UNRESOLVED"
        emit(result, args.out)
        return 9
    bg = np.median(sample, axis=0)
    bg_mad = float(np.abs(sample - bg[None, :]).mean())
    result["background"] = {"sample_rect": [sx0, ty0, sx1, ty1],
                            "color": [int(v) for v in bg], "mad": round(bg_mad, 3)}
    if bg_mad > BG_MAD_MAX:
        result["background"]["error"] = "background patch not flat"
        result["verdict"] = "CARD_STRUCTURE_UNRESOLVED"
        emit(result, args.out)
        return 9

    frac = rows_content_fraction(rgb, bg, roi_x0 + 4, roi_x1 - 4)
    scan_lo = max(roi_y0 + 1, center_y - SCAN_RANGE_PX)
    scan_hi = min(roi_y1 - 1, center_y + SCAN_RANGE_PX)
    above_runs = threshold_runs(frac, scan_lo, center_y - 4, BAND_FRAC_THRESHOLD)
    below_runs = threshold_runs(frac, center_y + 4, scan_hi, BAND_FRAC_THRESHOLD)
    above_runs = [r for r in above_runs if r[1] - r[0] + 1 >= BAND_MIN_ROWS]
    below_runs = [r for r in below_runs if r[1] - r[0] + 1 >= BAND_MIN_ROWS]
    above_bottom = max((r[1] for r in above_runs), default=None)
    below_top = min((r[0] for r in below_runs), default=None)
    structure = {
        "scan_y_range": [scan_lo, scan_hi],
        "above_band_runs": [list(r) for r in above_runs],
        "below_band_runs": [list(r) for r in below_runs],
        "above_band_bottom_row": above_bottom,
        "below_band_top_row": below_top,
    }
    result["structure"] = structure
    if above_bottom is None or below_top is None:
        result["verdict"] = "CARD_STRUCTURE_UNRESOLVED"
        emit(result, args.out)
        return 9

    sep_min = max(SEP_MIN_ABS_PX, int(round(title_h * SEP_MIN_TITLE_H)))
    margin_up = center_y - above_bottom
    margin_down = below_top - center_y
    result["margins"] = {
        "margin_above_px": margin_up, "margin_below_px": margin_down,
        "sep_min_px": sep_min, "rule": "max(%d, round(title_height*%.1f))" % (
            SEP_MIN_ABS_PX, SEP_MIN_TITLE_H),
        "title_height_px": title_h,
    }

    strip_rows = [yy for yy in range(above_bottom + 1, below_top) if frac[yy] <= STRIP_FRAC_MAX]
    result["strip"] = {"rows_total": below_top - above_bottom - 1,
                       "rows_kept": len(strip_rows),
                       "frac_max_used": STRIP_FRAC_MAX}
    if len(strip_rows) < STRIP_MIN_ROWS:
        result["verdict"] = "CARD_STRUCTURE_UNRESOLVED"
        emit(result, args.out)
        return 9

    if margin_up < sep_min or margin_down < sep_min:
        result["verdict"] = "UNSAFE_MARGINS"
        emit(result, args.out)
        return 4

    # ---- caption-strip content audit ----
    strip_mask = np.zeros((roi_y1 - roi_y0, roi_x1 - roi_x0), dtype=bool)
    seg = rgb[:, roi_x0:roi_x1, :]
    diff = np.abs(seg - bg[None, None, :]).max(axis=2)
    mask = diff >= CONTENT_DIFF
    for yy in strip_rows:
        strip_mask[yy - roi_y0, :] = mask[yy, :]
    allowed_rects = [
        (tx0 - 6 - roi_x0, ty0 - 6 - roi_y0, tx1 + 6 - roi_x0, ty1 + 6 - roi_y0),
        (count_box[0] - 6 - roi_x0, count_box[1] - 6 - roi_y0,
         count_box[2] + 6 - roi_x0, count_box[3] + 6 - roi_y0),
    ]
    for (ax0, ay0, ax1, ay1) in allowed_rects:
        ax0 = max(0, ax0); ay0 = max(0, ay0)
        ax1 = min(strip_mask.shape[1] - 1, ax1); ay1 = min(strip_mask.shape[0] - 1, ay1)
        if ax0 <= ax1 and ay0 <= ay1:
            strip_mask[ay0:ay1 + 1, ax0:ax1 + 1] = False
    comps = connected_components(strip_mask, roi_x0, roi_y0)
    comps = [c for c in comps if c["n"] >= CLUSTER_MIN_PX]
    merged = merge_close(comps, CLUSTER_MERGE_GAP)
    clusters = [{"bbox": [c["x0"], c["y0"], c["x1"], c["y1"]],
                 "width": c["x1"] - c["x0"] + 1, "height": c["y1"] - c["y0"] + 1,
                 "px": c["n"]} for c in merged]
    result["strip"]["clusters"] = clusters
    if len(merged) != 1:
        result["strip"]["error"] = ("expected exactly one caption control cluster (the ellipsis); "
                                    "found %d" % len(merged))
        result["verdict"] = "STRIP_CONTENT_UNEXPECTED"
        emit(result, args.out)
        return 10
    control = merged[0]
    control_checks = {
        "control_width_px": control["x1"] - control["x0"] + 1,
        "control_height_px": control["y1"] - control["y0"] + 1,
        "gap_right_of_title_px": control["x0"] - tx1,
        "gap_left_of_candidate_px": control["x0"] - click_point[0],
    }
    result["control"] = control_checks
    if (control_checks["control_width_px"] > CONTROL_MAX_W
            or control_checks["control_height_px"] > CONTROL_MAX_H
            or control_checks["gap_right_of_title_px"] < CONTROL_MIN_GAP_PX
            or control_checks["gap_left_of_candidate_px"] < CONTROL_MIN_GAP_PX):
        result["strip"]["error"] = "caption control cluster violates separation bounds"
        result["verdict"] = "STRIP_CONTENT_UNEXPECTED"
        emit(result, args.out)
        return 10

    result["verdict"] = "ELIGIBLE"
    result["dispatch"] = {"dispatched": False, "note": "offline evidence only; no input was sent"}
    emit(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
