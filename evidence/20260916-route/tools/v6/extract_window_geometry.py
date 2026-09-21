#!/usr/bin/env python3
"""v6 window-geometry extractor - deterministic, offline, current-frame-only.

Purpose: produce the `--window-geometry` input artifact that
`locate_album_card.py` (v6) requires for its album-card S3 safety decision.

This tool exists because v6 needs an analysis region (ROI) with explicit
provenance and must never rely on historical coordinates:

  * LIVE route (future wave): the geometry artifact is expected to come from a
    read-only AX window-bounds observation of the LINE window for the fresh
    frame (window rect in points, times the capture scale factor -> device
    pixels of the full-screen screenshot), bound to the fresh frame's SHA-256.
  * OFFLINE replay (this tool): no AX read exists for the frozen frames, so the
    window rectangle is derived from the frame's own pixels by the documented
    deterministic method below and bound to the frame's SHA-256.

Method (deterministic; no timestamps; no historical coordinate):
  1. Machine-read the target title from THIS frame with the frozen v4 Vision
     reader and the frozen v4 title rule (same identity semantics as v6).
  2. Detect vertical window border-line columns: a column x qualifies when at
     least MIN_RUN_ROWS rows satisfy
       LINE_COLOR_MIN <= gray(x,y) <= LINE_COLOR_MAX
       gray(x,y) - gray(x+6,y) >= RIGHT_STEP_MIN
       (x < 6  or  gray(x,y) - gray(x-6,y) >= LEFT_STEP_MIN)
     and the qualifying rows span at least MIN_SPAN_ROWS.
  3. Pair each qualifying column xc with the nearest qualifying column xr to
     its right (xr - xc >= MIN_WINDOW_W) whose row-span overlaps xc's row-span
     by >= SPAN_OVERLAP_MIN rows. The candidate rect is the intersection of the
     two spans. Rects thinner than MIN_WINDOW_H rows are dropped.
  4. Keep the rects that contain the machine-read title bbox with at least
     TITLE_INSET_MIN px on every side. Exactly one such rect must exist; zero
     or several refuse (NO_UNIQUE_WINDOW_RECT) - fail closed.

Refusals: 2 TARGET_TITLE_NOT_FOUND, 3 NO_UNIQUE_WINDOW_RECT, 6 BAD_FRAME.
Nothing is written to --out unless a rect was proven.

Interpreter: /opt/homebrew/bin/python3 (Pillow + numpy required).
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re

import numpy as np
from PIL import Image

V4_READER_SHA256 = "22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8"

LINE_COLOR_MIN = 56
LINE_COLOR_MAX = 92
RIGHT_STEP_MIN = 12
LEFT_STEP_MIN = 8
SIDE_K = 6
MIN_RUN_ROWS = 300
MIN_SPAN_ROWS = 400
MIN_WINDOW_W = 200
MIN_WINDOW_H = 400
SPAN_OVERLAP_MIN = 300
TITLE_INSET_MIN = 8


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


def border_columns(gray):
    """Return {x: {y_min, y_max, rows}} for qualifying border-line columns."""
    H, W = gray.shape
    out = {}
    for x in range(W):
        col = gray[:, x]
        right = gray[:, min(x + SIDE_K, W - 1)]
        cond = (col >= LINE_COLOR_MIN) & (col <= LINE_COLOR_MAX) & (col - right >= RIGHT_STEP_MIN)
        if x >= SIDE_K:
            left = gray[:, x - SIDE_K]
            cond &= (col - left >= LEFT_STEP_MIN)
        ys = np.nonzero(cond)[0]
        if ys.size >= MIN_RUN_ROWS and int(ys.max()) - int(ys.min()) >= MIN_SPAN_ROWS:
            out[x] = {"y_min": int(ys.min()), "y_max": int(ys.max()), "rows": int(ys.size)}
    return out


def candidate_rects(cands):
    """Deterministic xc -> nearest valid xr pairing (documented rule)."""
    rects = []
    xs = sorted(cands)
    for xc in xs:
        left = cands[xc]
        for xr in xs:
            if xr - xc < MIN_WINDOW_W:
                continue
            right = cands[xr]
            overlap = min(left["y_max"], right["y_max"]) - max(left["y_min"], right["y_min"])
            if overlap < SPAN_OVERLAP_MIN:
                continue
            y0 = max(left["y_min"], right["y_min"])
            y1 = min(left["y_max"], right["y_max"])
            if y1 - y0 < MIN_WINDOW_H:
                continue
            rects.append({"x0": xc, "x1": xr, "y0": y0, "y1": y1})
            break
    return rects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--expect-start", required=True)
    ap.add_argument("--expect-end", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.frame):
        print(json.dumps({"verdict": "BAD_FRAME", "frame": args.frame}))
        return 6
    try:
        with open(args.frame, "rb") as f:
            frame_bytes = f.read()
        frame_sha = sha256_bytes(frame_bytes)
        im = Image.open(io.BytesIO(frame_bytes))
        im.load()
        width, height = im.size
        gray = np.asarray(im.convert("L"), dtype=np.int16)
    except Exception:
        print(json.dumps({"verdict": "BAD_FRAME", "frame": args.frame}))
        return 6

    words = vision_reader.read_words(im.convert("L"), 3) or []
    title = find_title(words, args.expect_start, args.expect_end)
    if not title:
        print(json.dumps({"verdict": "TARGET_TITLE_NOT_FOUND", "frame": args.frame,
                          "frame_sha256": frame_sha}, ensure_ascii=False))
        return 2
    tx0, ty0, tx1, ty1 = title["bbox"]

    cands = border_columns(gray)
    rects = candidate_rects(cands)
    containing = []
    for rect in rects:
        if (tx0 - rect["x0"] >= TITLE_INSET_MIN and rect["x1"] - tx1 >= TITLE_INSET_MIN
                and ty0 - rect["y0"] >= TITLE_INSET_MIN and rect["y1"] - ty1 >= TITLE_INSET_MIN):
            containing.append(rect)

    diagnostics = {
        "title": title,
        "border_columns": {str(k): v for k, v in sorted(cands.items())},
        "candidate_rects": rects,
        "rects_containing_title": containing,
    }
    if len(containing) != 1:
        print(json.dumps({"verdict": "NO_UNIQUE_WINDOW_RECT", "frame": args.frame,
                          "frame_sha256": frame_sha, "diagnostics": diagnostics},
                         ensure_ascii=False))
        return 3

    rect = containing[0]
    tool_sha = sha256_file(os.path.abspath(__file__))
    left_col = cands[rect["x0"]]
    right_col = cands[rect["x1"]]
    source = (
        "offline deterministic extraction from this frame by "
        "evidence/20260916-route/tools/v6/extract_window_geometry.py "
        "(sha256 %s): window border-line columns detected in this frame's own pixels "
        "(left column x=%d rows %d..%d; right column x=%d rows %d..%d); rect = the "
        "nearest right border column over the overlapping vertical span; unique rect "
        "containing the machine-read target title. No historical coordinate used; "
        "rect is in full-screen capture device-pixel coordinates."
        % (tool_sha, rect["x0"], left_col["y_min"], left_col["y_max"],
           rect["x1"], right_col["y_min"], right_col["y_max"]))
    payload = {
        "schema": "v6-window-geometry/1",
        "frame": args.frame,
        "frame_sha256": frame_sha,
        "frame_size": [width, height],
        "x0": rect["x0"], "y0": rect["y0"], "x1": rect["x1"], "y1": rect["y1"],
        "source": source,
        "method": {
            "tool": "evidence/20260916-route/tools/v6/extract_window_geometry.py",
            "tool_sha256": tool_sha,
            "constants": {"line_color": [LINE_COLOR_MIN, LINE_COLOR_MAX],
                          "right_step_min": RIGHT_STEP_MIN, "left_step_min": LEFT_STEP_MIN,
                          "side_k": SIDE_K, "min_run_rows": MIN_RUN_ROWS,
                          "min_span_rows": MIN_SPAN_ROWS, "min_window_w": MIN_WINDOW_W,
                          "min_window_h": MIN_WINDOW_H, "span_overlap_min": SPAN_OVERLAP_MIN,
                          "title_inset_min": TITLE_INSET_MIN},
        },
        "diagnostics": diagnostics,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdict": "GEOMETRY_OK", "out": args.out,
                      "rect": [rect["x0"], rect["y0"], rect["x1"], rect["y1"]],
                      "frame_sha256": frame_sha}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
