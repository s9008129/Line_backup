#!/usr/bin/env python3
"""validate_live_geometry.py - attempt-10 live ROI provenance cross-check (read-only).

Binds the AX-derived LINE-window rect (points) to the fresh full-screen frame
(device pixels, x2 capture scale) by reproducing the read-only CU window
screenshot inside the frame:

  1. dimension check: crop size must equal AX size (pt) x capture scale (2);
     the CU window screenshot must be exactly AX size (pt) at 1x.
  2. content check  : the 2x frame crop, downscaled by 2 (LANCZOS, gray), is
     compared against the CU window screenshot -> mean absolute difference.

Pre-declared PASS rule (fixed before running; not tuned against this frame):
  dims exact AND mad_mean <= 12.0 gray levels.
Rationale for 12.0: accepted same-content comparisons in this evidence line
measured MAD 1.6-3.9 (attempt-05 screen-probe cross-checks), while
different-content comparisons measured >= 34 (attempt-05 environment note,
window absent) and 59 (full-screen change). 12.0 sits far from both.

The script never writes to LINE, never sends input, and never modifies any
frozen tool. It only reads the frame, the CU screenshot and the AX JSON.

Usage:
  validate_live_geometry.py FRAME CU_SHOT AX_JSON WINDOW_INDEX OUT_JSON
"""
import json
import sys

import numpy as np
from PIL import Image

MAD_PASS_MAX = 12.0
CAPTURE_SCALE = 2  # NSScreen.backingScaleFactor on this host; frame dims are re-checked below


def gray(a):
    return np.asarray(a.convert("L"), dtype=np.int16)


def mad(a, b):
    return float(np.abs(a - b).mean())


def main():
    frame_path, shot_path, ax_path, index, out_path = sys.argv[1:6]
    index = int(index)

    frame = Image.open(frame_path).convert("RGB")
    shot = Image.open(shot_path).convert("RGB")
    ax = json.load(open(ax_path, encoding="utf-8"))
    win = ax["windows"][index]
    x, y = win["position_points"]
    w, h = win["size_points"]

    result = {
        "tool": "validate_live_geometry",
        "frame": frame_path,
        "cu_shot": shot_path,
        "ax_json": ax_path,
        "window_index": index,
        "ax_window": win,
        "frame_size": list(frame.size),
        "cu_shot_size": list(shot.size),
        "capture_scale": CAPTURE_SCALE,
        "pass_rule": {"dims_exact": True, "mad_mean_max": MAD_PASS_MAX},
    }

    crop_px = [x * CAPTURE_SCALE, y * CAPTURE_SCALE,
               (x + w) * CAPTURE_SCALE, (y + h) * CAPTURE_SCALE]
    result["frame_crop_px"] = crop_px
    checks = {"cu_shot_dims_equal_ax_pt": list(shot.size) == [w, h],
              "frame_crop_inside_frame": (crop_px[0] >= 0 and crop_px[1] >= 0
                                          and crop_px[2] <= frame.size[0]
                                          and crop_px[3] <= frame.size[1]),
              "frame_scale_matches_display": list(frame.size) == [i * CAPTURE_SCALE for i in
                                                                  [ax["display"]["display_bounds_points"][2],
                                                                   ax["display"]["display_bounds_points"][3]]]}
    result["dims_checks"] = checks

    if not all(checks.values()):
        result["verdict"] = "GEOMETRY_BINDING_FAIL"
        result["reason"] = "dimension precondition failed"
        json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return 2

    crop = frame.crop(tuple(crop_px))
    result["crop_size_px"] = list(crop.size)
    crop_half = crop.resize((w, h), Image.LANCZOS)
    g_frame = gray(crop_half)
    g_shot = gray(shot)
    diff = np.abs(g_frame - g_shot)
    result["comparison"] = {
        "method": "frame crop (x%d) downscaled by %d with LANCZOS vs CU window screenshot; gray MAD" % (CAPTURE_SCALE, CAPTURE_SCALE),
        "mad_mean": round(mad(g_frame, g_shot), 3),
        "pixels_gt8_gray": int((diff > 8).sum()),
        "fraction_gt8_gray": round(float((diff > 8).mean()), 5),
    }
    diag = {}
    for dy in (-4, 0, 4):
        for dx in (-4, 0, 4):
            c = frame.crop((crop_px[0] + dx, crop_px[1] + dy,
                            crop_px[2] + dx, crop_px[3] + dy)).resize((w, h), Image.LANCZOS)
            diag["dx%+d_dy%+d" % (dx, dy)] = round(mad(gray(c), g_shot), 3)
    result["shift_diagnostics"] = diag

    ok = checks and result["comparison"]["mad_mean"] <= MAD_PASS_MAX
    result["verdict"] = "GEOMETRY_BINDING_PASS" if ok else "GEOMETRY_BINDING_FAIL"
    if not ok:
        result["reason"] = "mad_mean above pre-declared bound" if checks else "dimension check failed"
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
