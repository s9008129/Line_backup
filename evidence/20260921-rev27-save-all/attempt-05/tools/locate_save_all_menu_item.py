#!/usr/bin/env python3
"""Locate the Save All menu item (儲存全部) inside a freshly detected menu popup (v7 class).

Read-only analysis of one frame. It never sends input; the single permitted Save All
menu-item click is executed separately (route-runbook.md attempt-02, S4).

Provenance chain (all three must bind): the frame (SHA-256), a frozen-detector result
JSON that binds the same frame (post path + post_sha256) and carries the freshly chosen
menu bbox, and a frame-SHA-bound window-geometry JSON (window origin/size in points +
capture scale). Every verdict and every input is recorded in the emitted JSON.

Identification is text-first: the menu bbox is cropped, upscaled (LANCZOS), and OCR'd
with tesseract (`-l chi_tra+eng --psm 6 tsv`, image passed on stdin) to word boxes.
Words are clustered into rows by vertical center; a row's text is the left-to-right
concatenation of its words with whitespace removed. Exactly one row must contain the
target item text (multi-glyph OCR splits are allowed by concatenation); more than one
matching row -> AMBIGUOUS, none -> NOT_FOUND.

Cross-check (never computation): the observed item rows must contain the reference item
order -- 選擇項目, 修改相簿名稱, (target), 刪除相簿, 分享相簿 -- in strictly increasing
row order around the identified row. The reference order is only checked against the
observation; it is never used to compute a row position.

Candidate: x = midpoint of (identified text box x-range ∩ addressable input region
x-range), y = vertical center of the identified text box. The addressable input region
is the intersection of the app window rect (from the bound geometry), the menu bbox and
the frame bounds. Requirements: the x-overlap is at least --min-overlap-px wide; the
candidate lies inside the menu bbox, inside the addressable region, and within the
identified row's vertical extent. Otherwise NOT_ADDRESSABLE.

Output spaces: frame px (screen), screen pt (= px / capture scale), app-local pt
(= screen pt - window origin pt). The app-local form is the dispatch form.

Exit codes: 0 ELIGIBLE, 2 NOT_FOUND, 3 NOT_ADDRESSABLE, 4 AMBIGUOUS,
5 MENU_CONTENT_UNEXPECTED, 6 BAD_INPUT.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess

from PIL import Image

TARGET_ITEM = "儲存全部"
REFERENCE_ORDER = ["選擇項目", "修改相簿名稱", TARGET_ITEM, "刪除相簿", "分享相簿"]
UPSCALE = 3
OCR_LANG = "chi_tra+eng"
OCR_PSM = "6"
CJK = re.compile(r"[\u3400-\u9fff\u3000-\u303f]")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_ws(text):
    return re.sub(r"\s+", "", text)


def ocr_word_boxes(image):
    """Return (ok, words, meta). Words carry frame-space boxes already."""
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
    return True, words, {"returncode": 0, "command": cmd,
                         "upscale": UPSCALE, "tesseract_version": tesseract_version()}


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
    """Greedy clustering by vertical center; returns rows sorted top->bottom."""
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
        row["box"] = ["%.3f" % min(w["box"][0] for w in ws),
                      "%.3f" % min(w["box"][1] for w in ws),
                      "%.3f" % max(w["box"][2] for w in ws),
                      "%.3f" % max(w["box"][3] for w in ws)]
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
    ap.add_argument("--min-overlap-px", type=float, default=20.0)
    ap.add_argument("--row-tol-fraction", type=float, default=0.6)
    ap.add_argument("--row-tol-min-px", type=float, default=8.0)
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {"tool": "locate_save_all_menu_item", "version": "v7",
              "frame": args.frame,
              "params": {"upscale": UPSCALE, "ocr_lang": OCR_LANG, "ocr_psm": OCR_PSM,
                         "min_overlap_px": args.min_overlap_px,
                         "row_tol_fraction": args.row_tol_fraction,
                         "row_tol_min_px": args.row_tol_min_px}}

    for path in (args.frame, args.detector_json, args.geometry):
        if not path or not str(path).strip() or not __import__("os").path.exists(path):
            return finish(result, args.out, "BAD_INPUT", 6, "missing input: %r" % path)

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
    result["ocr"]["words"] = [{"text": w["text"], "conf": round(w["conf"], 2),
                               "box_frame_px": [round(v, 3) for v in w["box"]]} for w in words]
    if not words:
        return finish(result, args.out, "NOT_FOUND", 2, "no OCR words inside the menu bbox")

    heights = sorted(w["box"][3] - w["box"][1] for w in words)
    median_h = heights[len(heights) // 2]
    tol_px = max(args.row_tol_min_px, args.row_tol_fraction * median_h)
    result["params"]["median_word_height_px"] = round(median_h, 3)
    result["params"]["row_tol_px"] = round(tol_px, 3)

    rows = cluster_rows(words, tol_px)
    result["rows"] = [{"index": r["index"], "text": r["text"], "mean_cy_px": r["mean_cy"],
                       "box_frame_px": [float(v) for v in r["box"]],
                       "word_count": len(r["words"])} for r in rows]
    result["reference_order"] = REFERENCE_ORDER

    target_rows = [r for r in rows if TARGET_ITEM in r["text"]]
    if len(target_rows) > 1:
        result["target_rows_found"] = [r["index"] for r in target_rows]
        return finish(result, args.out, "AMBIGUOUS", 4,
                      "target item text found in more than one row")
    if not target_rows:
        return finish(result, args.out, "NOT_FOUND", 2, "target item text not found in any row")
    target = target_rows[0]

    item_rows = [r for r in rows if CJK.search(r["text"])]
    ref_index = {}
    for ref in REFERENCE_ORDER:
        hits = [r["index"] for r in item_rows if ref in r["text"]]
        ref_index[ref] = hits
    strict_order = True
    previous = None
    for ref in REFERENCE_ORDER:
        hits = ref_index[ref]
        if len(hits) < 1:
            strict_order = False
            break
        chosen = hits[0] if ref != TARGET_ITEM else target["index"]
        if previous is not None and chosen <= previous:
            strict_order = False
            break
        previous = chosen
    result["cross_check"] = {"item_row_indices": [r["index"] for r in item_rows],
                             "item_row_texts": [r["text"] for r in item_rows],
                             "reference_hits": ref_index,
                             "strict_order": strict_order,
                             "identified_row_index": target["index"]}
    if not strict_order:
        return finish(result, args.out, "MENU_CONTENT_UNEXPECTED", 5,
                      "reference item order not found around the identified row")

    text_box = [float(v) for v in target["box"]]
    result["target"] = {"text": TARGET_ITEM, "row_index": target["index"],
                        "text_box_frame_px": text_box,
                        "row_extent_frame_px": text_box}

    window_rect = [wx * scale, wy * scale, (wx + ww) * scale, (wy + wh) * scale]
    frame_rect = [0.0, 0.0, float(frame.size[0]), float(frame.size[1])]
    addr = intersect(intersect(window_rect, bbox), frame_rect)
    result["window_rect_px"] = window_rect
    result["addressable_region_frame_px"] = addr
    if addr is None:
        return finish(result, args.out, "NOT_ADDRESSABLE", 3,
                      "menu bbox does not intersect the app window/frame")

    ox0, ox1 = max(text_box[0], addr[0]), min(text_box[2], addr[2])
    overlap_w = ox1 - ox0
    result["overlap"] = {"x_range": [ox0, ox1], "width_px": round(overlap_w, 3),
                         "min_required_px": args.min_overlap_px,
                         "pass": overlap_w >= args.min_overlap_px}
    if overlap_w < args.min_overlap_px:
        return finish(result, args.out, "NOT_ADDRESSABLE", 3,
                      "text-box x-overlap with the addressable region is below the rule")

    cx = (ox0 + ox1) / 2.0
    cy = (text_box[1] + text_box[3]) / 2.0
    candidate_frame = [cx, cy]
    candidate_screen = [cx / scale, cy / scale]
    candidate_app_local = [candidate_screen[0] - wx, candidate_screen[1] - wy]
    checks = {
        "candidate_inside_menu_bbox": bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3],
        "candidate_inside_addressable_region": addr[0] <= cx <= addr[2] and addr[1] <= cy <= addr[3],
        "candidate_within_row_extent": text_box[1] <= cy <= text_box[3],
    }
    result["candidate"] = {
        "frame_px": [round(cx, 3), round(cy, 3)],
        "screen_pt": [round(candidate_screen[0], 3), round(candidate_screen[1], 3)],
        "app_local_pt": [round(candidate_app_local[0], 3), round(candidate_app_local[1], 3)],
    }
    result["checks"] = checks
    if not all(checks.values()):
        return finish(result, args.out, "NOT_ADDRESSABLE", 3,
                      "candidate outside menu bbox / addressable region / row extent")

    return finish(result, args.out, "ELIGIBLE", 0,
                  "exactly one target row, reference order cross-check passed, candidate addressable")


if __name__ == "__main__":
    raise SystemExit(main())
