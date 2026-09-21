#!/usr/bin/env python3
"""ALBUM_DETAIL_WINDOW_LINEAGE_GUARD (v7, append-only new tool).

Purpose: fail-closed, deterministic, read-only verification that the CURRENT
focused LINE window is an album-DETAIL window of the established lineage
(the window that owned the attempt-13 menu), using only current-round evidence.
It exists because the frozen album-open verifier (v4/v5 verify_album_open.py)
returned ALBUM_OPEN_VERIFIED for a frame pair in which NO album-detail window
was open: the album-LIST surface itself shows the target date-range title and
the photo count, so title + count + changed_fraction cannot identify the
detail surface (Rev27 Gate A attempt-03).

This tool never sends input, never reads historical coordinates, never falls
back to a previous round's geometry. Every rect used is derived from the
supplied same-round AX window inventory. Ambiguity, missing evidence, a
binding failure, a non-detail AX surface or a non-detail header all refuse.

Inputs (all captured in the same round; file sha256s are recorded):
  --window-inventory   frozen ax_window_bounds_readonly JSON (v2 schema)
  --window-ax-state    CU read-only AX state text of the FOCUSED window
                       (full-tree form; CU diff/"no change" forms are refused)
  --window-screenshot  CU read-only window screenshot of that focused window
  --frame              full-screen capture of the same moment
  --expect-start/--expect-end/--expect-count  target album identity
  --reader-dir         directory containing the frozen vision reader
                       (locate_album_card.py + vision_reader.py); OCR is the
                       frozen macOS Vision reader, read-only
  --frozen-album-open-json (optional) the frozen verifier verdict JSON; when
                       given, the tool also evaluates the composite rule
                       (frozen verdict == ALBUM_OPEN_VERIFIED AND its post
                       frame sha256 == this round's --frame sha256).

Verdicts: ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED | REFUSED (with reasons).
Exit codes: 0 verified (and composite PASS when requested), 2 lineage refused,
3 lineage verified but composite FAIL, 6 bad input.
Deterministic: identical inputs => byte-identical JSON (no timestamps).
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys

from PIL import Image

BUNDLE = "jp.naver.line.mac"
MAD_MAX = 12.0
HEADER_Y_FRAC_MAX = 0.30

LIST_MARKERS = ["列表", "文字欄位"]
DETAIL_CHROME = ["關閉按鈕", "縮到最小按鈕"]
LIST_TAB_TOKENS = ["相簿", "記事本"]
PHOTO_CONTEXT_TOKEN = "張照片"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def refuse(reasons, code):
    return {"verdict": "REFUSED", "refusal_reasons": reasons, "exit_code": code}


def parse_ax_state(text):
    """Classify the CU AX state text. Returns (form, facts). Forms:
    FULL_TREE | DIFF_FORM | EMPTY. Only FULL_TREE can positively verify."""
    stripped = text.strip()
    if not stripped:
        return "EMPTY", {}
    if stripped.startswith("The following is a diff") or \
       stripped.startswith("There has been no change"):
        return "DIFF_FORM", {}
    facts = {
        "standard_window": "標準視窗" in stripped,
        "close_button": "關閉按鈕" in stripped,
        "minimize_button": "縮到最小按鈕" in stripped,
        "list_element": any(m in stripped for m in LIST_MARKERS),
        "row_tokens": len(re.findall(r"(?m)^\s*\d+\s+row\s*$", stripped)),
        "focused_is_window": bool(re.search(
            r"(?m)^The focused UI element is \d+ 標準視窗", stripped)),
    }
    return "FULL_TREE", facts


def gray_mad(crop, shot):
    px, qx = crop.load(), shot.load()
    w, h = crop.size
    total = 0
    gt8 = 0
    for y in range(h):
        for x in range(w):
            d = abs(px[x, y] - qx[x, y])
            total += d
            if d > 8:
                gt8 += 1
    return round(total / float(w * h), 4), round(gt8 / float(w * h), 6)


def load_reader(reader_dir):
    path = os.path.join(reader_dir, "locate_album_card.py")
    if not os.path.isfile(path):
        return None, "reader module missing: " + path
    spec = importlib.util.spec_from_file_location("card_{0}".format(os.getpid()), path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # fail-closed on any reader import failure
        return None, "reader import failed: %s" % exc
    return module, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-inventory", required=True)
    ap.add_argument("--window-ax-state", required=True)
    ap.add_argument("--window-screenshot", required=True)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--expect-start", required=True)
    ap.add_argument("--expect-end", required=True)
    ap.add_argument("--expect-count", default="57")
    ap.add_argument("--reader-dir", default=os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "v5")))
    ap.add_argument("--frozen-album-open-json", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    result = {
        "tool": "album_detail_lineage_guard",
        "version": "v7",
        "purpose": "ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED for the CURRENT focused "
                   "LINE window; fail-closed; current-round evidence only",
        "no_historical_coordinates": True,
        "gui_inputs": 0,
        "thresholds": {"mad_max": MAD_MAX, "header_y_frac_max": HEADER_Y_FRAC_MAX,
                       "list_markers": LIST_MARKERS, "detail_chrome": DETAIL_CHROME,
                       "list_tab_tokens": LIST_TAB_TOKENS,
                       "photo_context_token": PHOTO_CONTEXT_TOKEN},
        "inputs": {},
        "checks": [],
        "frozen_album_open": {"provided": False},
        "composite": {"verdict": "NOT_EVALUATED", "reasons": []},
    }

    def emit(out_result, code):
        payload = json.dumps(out_result, ensure_ascii=False, indent=1)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(payload + "\n")
        print(payload)
        return code

    # C0 evidence presence + hashes
    for key, path in (("window_inventory", args.window_inventory),
                      ("window_ax_state", args.window_ax_state),
                      ("window_screenshot", args.window_screenshot),
                      ("frame", args.frame)):
        if not os.path.isfile(path):
            result["checks"].append({"id": "C0_EVIDENCE", "verdict": "REFUSE",
                                     "detail": "missing input: " + path})
            result.update(refuse(["EVIDENCE_MISSING:" + key], 6))
            return emit(result, 6)
        result["inputs"][key] = {"path": path, "sha256": sha256_file(path)}
    try:
        with open(args.window_ax_state, "r", encoding="utf-8") as f:
            state_text = f.read()
        with open(args.window_inventory, "r", encoding="utf-8") as f:
            inventory = json.load(f)
        frame = Image.open(args.frame).convert("L")
        shot = Image.open(args.window_screenshot).convert("L")
    except Exception as exc:
        result["checks"].append({"id": "C0_EVIDENCE", "verdict": "REFUSE",
                                 "detail": "unreadable input: %s" % exc})
        result.update(refuse(["EVIDENCE_MALFORMED"], 6))
        return emit(result, 6)

    # C0b inventory schema
    display = inventory.get("display") or {}
    windows = inventory.get("windows")
    req_top = ["bundle_id", "ax_frontmost", "frontmost_application", "ax_api_trusted",
               "running", "pid", "window_count"]
    req_display = ["nsscreen_backing_scale_factor", "display_bounds_points",
                   "cg_display_mode_pixel_wh"]
    req_win = ["index", "role", "subrole", "title", "position_points", "size_points",
               "minimized", "main", "focused", "is_ax_focused_window"]
    schema_problems = [k for k in req_top if k not in inventory]
    schema_problems += ["display." + k for k in req_display if k not in display]
    if not isinstance(windows, list) or not windows:
        schema_problems.append("windows[]")
    else:
        for i, w in enumerate(windows):
            schema_problems += ["windows[%d].%s" % (i, k) for k in req_win if k not in w]
    result["checks"].append({"id": "C0_SCHEMA", "verdict": "PASS" if not schema_problems
                             else "REFUSE", "detail": schema_problems or "ok"})
    if schema_problems:
        result.update(refuse(["EVIDENCE_MALFORMED"], 6))
        return emit(result, 6)

    scale = float(display["nsscreen_backing_scale_factor"])
    bounds = display["display_bounds_points"]
    mode_px = display["cg_display_mode_pixel_wh"]
    expected_frame_px = [int(round(bounds[2] * scale)), int(round(bounds[3] * scale))]
    frame_consistent = (list(frame.size) == expected_frame_px == list(mode_px)
                        and scale > 0)
    result["checks"].append({
        "id": "C0_FRAME_SCALE", "verdict": "PASS" if frame_consistent else "REFUSE",
        "detail": {"frame_size": list(frame.size), "scale": scale,
                   "display_bounds_points": bounds, "cg_display_mode_pixel_wh": mode_px,
                   "expected_frame_px": expected_frame_px}})
    if not frame_consistent:
        result.update(refuse(["EVIDENCE_MALFORMED:frame_scale"], 6))
        return emit(result, 6)

    # C1 frontmost identity
    frontmost = (inventory.get("bundle_id") == BUNDLE
                 and inventory.get("frontmost_application") == BUNDLE
                 and inventory.get("ax_frontmost") is True
                 and inventory.get("ax_api_trusted") is True
                 and inventory.get("running") is True)
    result["checks"].append({"id": "C1_FRONTMOST", "verdict": "PASS" if frontmost
                             else "REFUSE",
                             "detail": {"bundle_id": inventory.get("bundle_id"),
                                        "frontmost_application": inventory.get("frontmost_application"),
                                        "ax_frontmost": inventory.get("ax_frontmost"),
                                        "ax_api_trusted": inventory.get("ax_api_trusted")}})
    if not frontmost:
        result.update(refuse(["NOT_FRONTMOST"], 2))
        return emit(result, 2)

    # C2 unique focused/main target window
    focused = [w for w in windows if w.get("is_ax_focused_window") is True]
    main = [w for w in windows if w.get("main") is True]
    target = None
    ambiguity = []
    if len(focused) != 1:
        ambiguity.append("focused_windows=%d" % len(focused))
    if len(main) != 1:
        ambiguity.append("main_windows=%d" % len(main))
    if not ambiguity and focused[0]["index"] != main[0]["index"]:
        ambiguity.append("focused!=main")
    if not ambiguity:
        target = focused[0]
        if target.get("minimized") is not False:
            ambiguity.append("target_minimized")
        if not (target.get("role") == "AXWindow" and target.get("subrole") == "AXStandardWindow"):
            ambiguity.append("target_not_standard_window")
    result["checks"].append({"id": "C2_TARGET_UNIQUE", "verdict": "PASS" if target
                             else "REFUSE", "detail": ambiguity or "single focused main target"})
    if target is None:
        result.update(refuse(["TARGET_AMBIGUOUS"] + ambiguity, 2))
        return emit(result, 2)

    rect_pt = [target["position_points"][0], target["position_points"][1],
               target["size_points"][0], target["size_points"][1]]
    result["derived_target_window"] = {
        "index": target["index"], "title": target["title"], "role": target["role"],
        "subrole": target["subrole"], "rect_pt": rect_pt,
        "main": target["main"], "is_ax_focused_window": target["is_ax_focused_window"],
        "source": "derived from THIS round's AX inventory; no historical coordinate used"}

    # C3 no duplicate-geometry ambiguity
    duplicates = [w["index"] for w in windows
                  if w["index"] != target["index"]
                  and w["position_points"] == target["position_points"]
                  and w["size_points"] == target["size_points"]]
    inside = (0 <= rect_pt[0] and 0 <= rect_pt[1]
              and (rect_pt[0] + rect_pt[2]) * scale <= frame.size[0]
              and (rect_pt[1] + rect_pt[3]) * scale <= frame.size[1])
    c3_pass = (not duplicates) and inside
    result["checks"].append({"id": "C3_GEOMETRY_DOUBT", "verdict": "PASS" if c3_pass
                             else "REFUSE",
                             "detail": {"duplicate_geometry_indexes": duplicates,
                                        "target_inside_frame": inside}})
    if not c3_pass:
        result.update(refuse(["GEOMETRY_DOUBT"], 2))
        return emit(result, 2)

    # C4 AX surface class of the focused window
    form, facts = parse_ax_state(state_text)
    c4_pass = (form == "FULL_TREE" and facts["standard_window"]
               and facts["close_button"] and facts["minimize_button"]
               and not facts["list_element"] and facts["row_tokens"] == 0
               and facts["focused_is_window"])
    c4_detail = {"state_form": form}
    c4_detail.update(facts)
    reasons4 = []
    if form != "FULL_TREE":
        reasons4.append("SURFACE_AX_NOT_FULL_TREE:%s" % form)
    else:
        if facts["list_element"]:
            reasons4.append("SURFACE_HAS_LIST_CONTROLS")
        if facts["row_tokens"]:
            reasons4.append("SURFACE_HAS_LIST_ROWS")
        if not facts["focused_is_window"]:
            reasons4.append("FOCUSED_ELEMENT_NOT_WINDOW")
        if not (facts["standard_window"] and facts["close_button"]
                and facts["minimize_button"]):
            reasons4.append("SURFACE_NOT_CUSTOM_DRAWN_WINDOW")
    result["checks"].append({"id": "C4_AX_SURFACE_CLASS", "verdict": "PASS" if c4_pass
                             else "REFUSE", "detail": c4_detail})
    if not c4_pass:
        result.update(refuse(reasons4, 2))
        return emit(result, 2)

    # C5 frame/window pixel binding (visibility + provenance + occlusion)
    rect_px = [int(round(rect_pt[0] * scale)), int(round(rect_pt[1] * scale)),
               int(round((rect_pt[0] + rect_pt[2]) * scale)),
               int(round((rect_pt[1] + rect_pt[3]) * scale))]
    crop = frame.crop(tuple(rect_px))
    try:
        down = crop.resize((int(crop.size[0] / scale), int(crop.size[1] / scale)),
                           Image.LANCZOS)
    except Exception as exc:
        result["checks"].append({"id": "C5_BINDING", "verdict": "REFUSE",
                                 "detail": "resize failed: %s" % exc})
        result.update(refuse(["BINDING_FAILED"], 2))
        return emit(result, 2)
    dims_ok = (down.size == shot.size
               and list(shot.size) == [int(rect_pt[2]), int(rect_pt[3])])
    if dims_ok:
        mad, frac_gt8 = gray_mad(down, shot)
    else:
        mad, frac_gt8 = None, None
    c5_pass = dims_ok and mad is not None and mad <= MAD_MAX
    result["checks"].append({
        "id": "C5_BINDING", "verdict": "PASS" if c5_pass else "REFUSE",
        "detail": {"rect_px": rect_px, "crop_size": list(crop.size),
                   "downscaled_size": list(down.size), "screenshot_size": list(shot.size),
                   "dims_exact": dims_ok, "mad_mean": mad, "fraction_gt8": frac_gt8,
                   "mad_max": MAD_MAX,
                   "meaning": "the focused window's own pixels equal the frame region at "
                              "its rect => window visible/unoccluded; binding derived from "
                              "this round's inventory only"}})
    if not c5_pass:
        result.update(refuse(["BINDING_FAILED"], 2))
        return emit(result, 2)

    # C6 detail header context (frozen Vision reader on the BOUND window screenshot)
    reasons6 = []
    reader, reader_error = load_reader(args.reader_dir)
    ocr = {"reader_dir": args.reader_dir, "reader_error": reader_error,
           "scale": 3, "title": None, "title_y_frac": None,
           "photo_context_token": None, "list_tab_tokens": None}
    if reader is None:
        reasons6.append("READER_UNAVAILABLE")
    else:
        try:
            words = reader.ocr_words(shot, scale=3)
        except Exception as exc:
            words = []
            ocr["reader_error"] = "ocr failed: %s" % exc
        title = reader.find_title(words, args.expect_start, args.expect_end)
        ocr["words_seen"] = [w["text"] for w in words][:40]
        ocr["title"] = title
        if title is None:
            reasons6.append("HEADER_TITLE_NOT_FOUND")
        else:
            y_frac = round(title["bbox"][3] / float(shot.size[1]), 4)
            ocr["title_y_frac"] = y_frac
            if y_frac > HEADER_Y_FRAC_MAX:
                reasons6.append("TITLE_NOT_IN_HEADER_BAND")
        photo_tokens = [w["text"] for w in words if PHOTO_CONTEXT_TOKEN in w["text"]]
        ocr["photo_context_token"] = photo_tokens
        photo_count_ok = any(re.sub(r"\D", "", t) == args.expect_count
                             for t in photo_tokens)
        if not photo_count_ok:
            reasons6.append("PHOTO_COUNT_CONTEXT_MISSING_OR_MISMATCH")
        tab_tokens = [w["text"] for w in words if w["text"] in LIST_TAB_TOKENS]
        ocr["list_tab_tokens"] = tab_tokens
        if tab_tokens:
            reasons6.append("LIST_TAB_MARKERS_PRESENT")
    c6_pass = not reasons6
    result["checks"].append({"id": "C6_HEADER_CONTEXT", "verdict": "PASS" if c6_pass
                             else "REFUSE", "detail": ocr})
    if not c6_pass:
        result.update(refuse(reasons6, 2))
        return emit(result, 2)

    result["lineage_verdict"] = "ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED"

    # C7 optional composite with the frozen verifier artifact
    composite_code = 0
    if args.frozen_album_open_json is not None:
        frozen = {"provided": True, "path": args.frozen_album_open_json}
        reasons7 = []
        if not os.path.isfile(args.frozen_album_open_json):
            reasons7.append("FROZEN_ARTIFACT_MISSING")
        else:
            frozen["sha256"] = sha256_file(args.frozen_album_open_json)
            try:
                with open(args.frozen_album_open_json, "r", encoding="utf-8") as f:
                    fz = json.load(f)
            except Exception as exc:
                fz = None
                reasons7.append("FROZEN_ARTIFACT_MALFORMED:%s" % exc)
            if fz is not None:
                frozen["verdict"] = fz.get("verdict")
                frozen["post_sha256"] = fz.get("post_sha256")
                frozen["pre_sha256"] = fz.get("pre_sha256")
                if fz.get("verdict") != "ALBUM_OPEN_VERIFIED":
                    reasons7.append("FROZEN_VERDICT_NOT_ALBUM_OPEN_VERIFIED")
                if fz.get("post_sha256") != result["inputs"]["frame"]["sha256"]:
                    reasons7.append("FROZEN_POST_FRAME_NOT_BOUND_TO_THIS_FRAME")
                    frozen["bound_to_frame"] = False
                else:
                    frozen["bound_to_frame"] = True
                if not fz.get("pre_sha256"):
                    reasons7.append("FROZEN_PRE_FRAME_HASH_MISSING")
        result["frozen_album_open"] = frozen
        composite_pass = not reasons7
        result["composite"] = {
            "rule": "frozen album-open verifier == ALBUM_OPEN_VERIFIED AND lineage "
                    "guard == ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED AND frozen post "
                    "frame sha256 == this round's frame sha256",
            "verdict": "ALBUM_OPEN_VERIFIED_COMPOSITE_PASS" if composite_pass
                       else "ALBUM_OPEN_VERIFIED_COMPOSITE_FAIL",
            "reasons": reasons7}
        if not composite_pass:
            composite_code = 3

    result["verdict"] = "ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED"
    result["refusal_reasons"] = []
    return emit(result, composite_code)


if __name__ == "__main__":
    raise SystemExit(main())
