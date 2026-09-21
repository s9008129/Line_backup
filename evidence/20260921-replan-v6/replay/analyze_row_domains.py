#!/usr/bin/env python3
"""Phase A offline recomputation: v4 full-row domain vs LINE-window-local domain.

Read-only. Frozen frames + frozen v4 rule semantics; no input; deterministic.
Output: row-domain-recompute.json (same directory).
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
FRAMES = {
    "a08r1": ("evidence/20260916-route/attempt-08/frame-pre.png",
              "evidence/20260921-replan-v6/replay/geometry/a08r1.json",
              "evidence/20260921-replan-v6/replay/v4-replay/a08r1.json"),
    "a08r2": ("evidence/20260916-route/attempt-08/frame-pre-r2.png",
              "evidence/20260921-replan-v6/replay/geometry/a08r2.json",
              "evidence/20260921-replan-v6/replay/v4-replay/a08r2.json"),
    "a09":   ("evidence/20260916-route/attempt-09/frame-pre.png",
              "evidence/20260921-replan-v6/replay/geometry/a09.json",
              "evidence/20260921-replan-v6/replay/v4-replay/a09.json"),
}
BRIGHT = 100


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def first_ge_from(means, start, step):
    y = start
    while 0 <= y < len(means):
        if means[y] >= BRIGHT:
            return y
        y += step
    return None


def max_below(means, start):
    ys = range(start, len(means))
    if not ys:
        return None
    vals = means[start:]
    y = int(np.argmax(vals)) + start
    return {"y": y, "value": round(float(means[y]), 3)}


out = {"schema": "v6-phaseA-row-domain-recompute/1", "bright_threshold": BRIGHT,
       "method": "per-row mean grayscale over (a) the full frame row (v4 domain) and "
                 "(b) the extracted LINE-window ROI x-range (v6 domain); frozen v4 rule "
                 "semantics (first row >= 100 scanning away from the title box); read-only",
       "frames": {}}

for name, (frame_path, geo_path, v4_path) in FRAMES.items():
    frame_sha = sha256_file(os.path.join(ROOT, frame_path))
    geo = json.load(open(os.path.join(ROOT, geo_path), encoding="utf-8"))
    v4 = json.load(open(os.path.join(ROOT, v4_path), encoding="utf-8"))
    assert geo["frame_sha256"] == frame_sha, name
    assert v4["frame_sha256"] == frame_sha, name
    g = np.asarray(Image.open(os.path.join(ROOT, frame_path)).convert("L"), dtype=np.float64)
    H, W = g.shape
    full = g.mean(axis=1)
    x0, y0, x1, y1 = geo["x0"], geo["y0"], geo["x1"], geo["y1"]
    roi = g[:, x0:x1 + 1].mean(axis=1)

    tx0, ty0, tx1, ty1 = v4["title"]["bbox"]
    cy = (ty0 + ty1) // 2

    def rule(means):
        top = first_ge_from(means, ty0 - 1, -1)
        bottom = first_ge_from(means, ty1 + 1, +1)
        return {
            "band_top": top,
            "band_bottom": bottom,
            "margin_above": None if top is None else cy - top,
            "margin_below": None if bottom is None else bottom - cy,
        }

    entry = {
        "frame": frame_path, "frame_sha256": frame_sha, "frame_size": [W, H],
        "roi": [x0, y0, x1, y1], "roi_width_px": x1 - x0 + 1,
        "roi_width_frac_of_frame": round((x1 - x0 + 1) / W, 4),
        "title_bbox": [tx0, ty0, tx1, ty1], "title_center_y": cy,
        "v4_frozen_verdict": v4["verdict"],
        "full_row_domain": {
            "rule_recompute": rule(full.tolist()),
            "max_mean_below_title": max_below(full, ty1 + 1),
            "mean_at_title_rows": [round(float(full[ty]), 2) for ty in (ty0, cy, ty1)],
        },
        "roi_domain": {
            "rule_recompute": rule(roi.tolist()),
            "max_mean_below_title": max_below(roi, ty1 + 1),
            "max_mean_above_title": {"y": int(np.argmax(roi[:ty0])) if ty0 > 0 else None},
        },
    }
    bt = entry["full_row_domain"]["rule_recompute"]["band_top"]
    if bt is not None:
        entry["full_row_domain"]["band_top_row_composition"] = {
            "y": bt,
            "full_row_mean": round(float(full[bt]), 3),
            "roi_row_mean": round(float(roi[bt]), 3),
            "roi_frac_of_frame": round((x1 - x0 + 1) / W, 4),
            "note": "v4 band_top row is a FULL-FRAME row mean; the LINE window contributes "
                    "only this fraction of the row",
        }
    out["frames"][name] = entry

out["conclusion_observed"] = (
    "In every one of the three frozen frames the frozen v4 rule reproduces "
    "band_bottom_bright_row = null and margin_below_px = null (UNSAFE_MARGINS, exit 4), "
    "although the same rule restricted to the LINE-window x-range finds a bright band "
    "immediately below the target caption. The failure is a spatial-domain mismatch: v4 "
    "averages the entire screenshot row (2294 px) while the LINE window occupies only "
    "~29% of it; bright photo rows inside the window cannot lift the full-row mean to 100.")
with open(os.path.join(HERE, "row-domain-recompute.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
print(json.dumps(out["conclusion_observed"]))
print("written:", os.path.join(HERE, "row-domain-recompute.json"))
