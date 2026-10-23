#!/usr/bin/env python3
"""Derive a Save All menu point only from same-frame display/OCR evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def center(box):
    x, y, width, height = box
    return (x + width / 2.0, y + height / 2.0)


def rect(window):
    frame = window["frame_points"]
    return (float(frame["x"]), float(frame["y"]),
            float(frame["x"] + frame["width"]), float(frame["y"] + frame["height"]))


def exact_observation(ocr, label):
    matches = []
    for result in ocr.get("results", []):
        for observation in result.get("observations", []):
            candidates = observation.get("top_candidates", [])
            if candidates and candidates[0].get("text") == label:
                box = observation.get("source_bbox_pixels_top_left", {})
                matches.append((candidates[0], [float(box[k]) for k in ("x", "y", "width", "height")]))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one OCR row {label!r}, got {len(matches)}")
    return matches[0]


def compute(capture, ocr, anchors, profile, detail_id, popup_id, cua_size):
    capture_hash = capture.get("image_sha256")
    if not capture_hash or ocr.get("input_sha256") != capture_hash:
        raise ValueError("OCR and capture are not bound to the same image hash")
    if ocr.get("profile", {}).get("processing_scale") != profile.get("processing_scale"):
        raise ValueError("OCR processing scale does not match the frozen profile")
    width = int(capture["image_width_pixels"])
    height = int(capture["image_height_pixels"])
    display = capture["display_size_points"]
    sx = width / float(display["width"])
    sy = height / float(display["height"])
    if abs(sx - sy) > 1e-9 or abs(sx - float(capture["filter_point_pixel_scale"])) > 1e-9:
        raise ValueError("display pixel/point scale is inconsistent")
    scale = sx

    windows = {int(w["window_id"]): w for w in capture["sck_window_inventory"]}
    detail = windows.get(detail_id)
    popup = windows.get(popup_id)
    if not detail or not popup or not detail.get("on_screen") or not popup.get("on_screen"):
        raise ValueError("the identified detail and popup windows must both be on-screen")
    if capture.get("selected_window_id") != detail_id:
        raise ValueError("selected full-display target is not the detail window")

    detail_rect = rect(detail)
    popup_rect = rect(popup)
    ix0, iy0 = max(detail_rect[0], popup_rect[0]), max(detail_rect[1], popup_rect[1])
    ix1, iy1 = min(detail_rect[2], popup_rect[2]), min(detail_rect[3], popup_rect[3])
    intersection = ((ix1 - ix0) * scale, (iy1 - iy0) * scale)
    minimum_intersection = float(profile["geometry_policy"]["minimum_actionable_intersection_width_pixels"])
    minimum_height = float(profile["geometry_policy"]["minimum_actionable_intersection_height_pixels"])
    if intersection[0] < minimum_intersection or intersection[1] < minimum_height:
        raise ValueError("popup/detail actionable intersection is too small")

    cua_width, cua_height = map(int, cua_size)
    expected_width = int(round((detail_rect[2] - detail_rect[0]) * scale))
    expected_height = int(round((detail_rect[3] - detail_rect[1]) * scale))
    if (cua_width, cua_height) != (expected_width, expected_height):
        raise ValueError("CUA screenshot dimensions do not match the selected window at display scale")

    required_anchors = int(profile["geometry_policy"]["minimum_distributed_anchors"])
    observed_anchors = anchors.get("anchors", [])
    if anchors.get("source_capture_sha256") != capture_hash or anchors.get("detail_window_id") != detail_id:
        raise ValueError("anchor evidence is not bound to this capture/detail window")
    if len(observed_anchors) < required_anchors:
        raise ValueError("not enough distributed cross-frame anchors")
    residuals = []
    points = []
    for anchor in observed_anchors:
        source = center(anchor["display_bbox_pixels"])
        cua = center(anchor["cua_bbox_pixels"])
        predicted = (detail_rect[0] * scale + cua[0], detail_rect[1] * scale + cua[1])
        residual = ((source[0] - predicted[0]) ** 2 + (source[1] - predicted[1]) ** 2) ** 0.5
        residuals.append({"name": anchor["name"], "residual_source_pixels": residual})
        points.append(cua)
    max_residual = max(item["residual_source_pixels"] for item in residuals)
    maximum_residual = float(profile["geometry_policy"]["maximum_anchor_residual_source_pixels"])
    if max_residual > maximum_residual:
        raise ValueError("cross-frame anchor residual exceeds frozen profile")
    max_distance = max(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
                       for i, a in enumerate(points) for b in points[i + 1:])
    if max_distance < 100:
        raise ValueError("anchors are not spatially distributed")

    before, before_box = exact_observation(ocr, "修改相簿名稱")
    target, target_box = exact_observation(ocr, "儲存全部")
    after, after_box = exact_observation(ocr, "刪除相簿")
    before_y, target_y, after_y = (center(box)[1] for box in (before_box, target_box, after_box))
    if not before_y < target_y < after_y:
        raise ValueError("Save All is not visually bracketed by Rename and Delete")
    upper = (before_y + target_y) / 2.0
    lower = (target_y + after_y) / 2.0
    row_margin = min(target_y - upper, lower - target_y)
    uncertainty = max(float(profile["geometry_policy"]["minimum_mapping_uncertainty_source_pixels"]), max_residual)
    clearance_required = uncertainty + 4.0
    if row_margin < clearance_required:
        raise ValueError("Save All row margin is below uncertainty plus the frozen safety allowance")

    # The CUA-controlled detail window overlaps the left side of the native
    # popup. Use the center of that observed intersection, then map back into
    # the CUA screenshot's pixel coordinate space.
    display_x = ((ix0 + ix1) / 2.0) * scale
    display_y = target_y
    cua_x = display_x - detail_rect[0] * scale
    cua_y = display_y - detail_rect[1] * scale
    if not (0 <= cua_x < cua_width and 0 <= cua_y < cua_height):
        raise ValueError("derived input point is outside the CUA window screenshot")
    if not (popup_rect[0] * scale <= display_x < popup_rect[2] * scale and
            popup_rect[1] * scale <= display_y < popup_rect[3] * scale):
        raise ValueError("derived point is outside the observed popup")

    return {
        "format_version": 1,
        "candidate": "observed-menu-coordinate-fix-v2",
        "capture_nonce": capture["nonce"],
        "capture_sha256": capture_hash,
        "ocr_input_sha256": ocr["input_sha256"],
        "profile_id": profile["profile_id"],
        "detail_window_id": detail_id,
        "popup_window_id": popup_id,
        "display_pixels_per_point": scale,
        "detail_frame_points": detail["frame_points"],
        "popup_frame_points": popup["frame_points"],
        "cua_screenshot_pixels": {"width": cua_width, "height": cua_height},
        "anchors": residuals,
        "maximum_anchor_residual_source_pixels": max_residual,
        "mapping_uncertainty_source_pixels": uncertainty,
        "save_all_bracketing_rows": {
            "above": before["text"],
            "target": target["text"],
            "below": after["text"],
            "observed_centers_display_pixels": {"above": before_y, "target": target_y, "below": after_y},
            "safe_vertical_interior_display_pixels": [upper, lower],
            "target_clearance_display_pixels": row_margin,
            "required_clearance_display_pixels": clearance_required
        },
        "actionable_intersection_pixels": {"width": intersection[0], "height": intersection[1]},
        "derived_save_all_cua_screenshot_pixel": {"x": cua_x, "y": cua_y},
        "derived_save_all_display_pixel": {"x": display_x, "y": display_y},
        "pre_dispatch_ready": True,
        "limitations": ["This geometry result does not create an intent or authorize a Save All dispatch."]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--detail-window-id", type=int, required=True)
    parser.add_argument("--popup-window-id", type=int, required=True)
    parser.add_argument("--cua-size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compute(read_json(args.capture), read_json(args.ocr), read_json(args.anchors),
                     read_json(args.profile), args.detail_window_id, args.popup_window_id, args.cua_size)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pre_dispatch_ready": result["pre_dispatch_ready"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"pre_dispatch_ready": False, "error": str(error)}), file=sys.stderr)
        raise SystemExit(1)
