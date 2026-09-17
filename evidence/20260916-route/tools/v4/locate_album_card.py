#!/usr/bin/env python3
"""Locate the target LINE album card's safe metadata click region from a frozen frame.

Read-only analysis. It never sends input; the single permitted album-card click is
executed separately (see route-runbook.md attempt-05).

Steps:
  1. OCR the frame (tesseract chi_tra+eng via stdin/stdout, 3x upscale, psm 6) and gate
     on the expected album title (start date + end date inside one title-sized window).
  2. Derive the metadata click point on the title row (title left edge + 12 px, title
     vertical centre) and verify same-frame margins against the bright content bands
     (the photo grids) above and below the title row.
  3. Best-effort OCR of the count text below the title; a readable count other than the
     expected one refuses (TARGET_COUNT_MISMATCH). Unreadable count is recorded and
     does not refuse.

Refusals (non-zero exit): 2 TARGET_TITLE_NOT_FOUND, 4 UNSAFE_MARGINS,
5 TARGET_COUNT_MISMATCH, 6 BAD_FRAME. Historical coordinates are never used:
every run must be given the frame captured for the current surface.

v4 (Rev21): the reader layer is macOS Vision (sibling vision_reader module); all v3 rules above are unchanged.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re

from PIL import Image


def _load_sibling(name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vision_reader = _load_sibling("vision_reader")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tsv_rows(image, psm, scale):
    """v4 reader seam: the frozen tesseract TSV call became the Vision reader.

    `image` is the unscaled image; vision_reader applies the LANCZOS upscale
    (`scale`) and returns v3-shaped records (psm has no Vision equivalent)."""
    return vision_reader.read_words(image, scale)


def ocr_words(im, scale=3, psm=6):
    return _tsv_rows(im, psm, scale) or []


def digits(text):
    return re.sub(r"\D", "", text)


def find_title(words, expect_start, expect_end):
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


def row_mean(im, y):
    px = im.load()
    total = 0
    for x in range(im.size[0]):
        total += px[x, y]
    return total / im.size[0]


def bright_band_edges(im, y0, y1, bright=100):
    top = None
    for y in range(y0 - 1, -1, -1):
        if row_mean(im, y) >= bright:
            top = y
            break
    bottom = None
    for y in range(y1 + 1, im.size[1]):
        if row_mean(im, y) >= bright:
            bottom = y
            break
    return top, bottom


def ocr_digits_region(im, box, scale=10, psm=7):
    crop = im.crop(box)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        return ""
    words = _tsv_rows(crop, psm, scale) or []
    return digits("".join(w["text"] for w in words))


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
    ap.add_argument("--out")
    args = ap.parse_args()

    if not os.path.exists(args.frame):
        emit({"verdict": "BAD_FRAME", "frame": args.frame}, args.out)
        return 6

    im = Image.open(args.frame).convert("L")
    width, height = im.size
    words = ocr_words(im)
    title = find_title(words, args.expect_start, args.expect_end)
    result = {
        "tool": "locate_album_card",
        "frame": args.frame,
        "frame_sha256": sha256_file(args.frame),
        "frame_size": [width, height],
        "expected": {"start": args.expect_start, "end": args.expect_end,
                     "count": args.expect_count},
        "title": title,
        "ocr_words_seen": [w["text"] for w in words][:60],
    }
    if not title:
        result["verdict"] = "TARGET_TITLE_NOT_FOUND"
        emit(result, args.out)
        return 2

    x0, y0, x1, y1 = title["bbox"]
    center_y = (y0 + y1) // 2
    band_top, band_bottom = bright_band_edges(im, y0, y1)
    result["band_top_bright_row"] = band_top
    result["band_bottom_bright_row"] = band_bottom
    result["margin_above_px"] = None if band_top is None else center_y - band_top
    result["margin_below_px"] = None if band_bottom is None else band_bottom - center_y

    count_box = (max(0, x0 - 8), y1 + 2, min(width, x0 + 160), min(height, y1 + 32))
    count_digits = ocr_digits_region(im, count_box)
    result["count_box"] = list(count_box)
    result["count_digits_read"] = count_digits
    if count_digits == "":
        result["count_text"] = "UNREADABLE"
    elif args.expect_count in count_digits:
        result["count_text"] = "MATCH"
    else:
        result["count_text"] = "MISMATCH"

    click_point = None
    if 0 <= x0 + 12 <= width - 20 and x0 + 12 <= x1 + 40:
        click_point = [x0 + 12, center_y]
    result["click_point"] = click_point
    result["click_point_derivation"] = "title left edge + 12 px, title vertical centre"

    if result["count_text"] == "MISMATCH":
        result["verdict"] = "TARGET_COUNT_MISMATCH"
        emit(result, args.out)
        return 5
    if click_point is None or result["margin_above_px"] is None or result["margin_below_px"] is None \
            or result["margin_above_px"] < 10 or result["margin_below_px"] < 10:
        result["verdict"] = "UNSAFE_MARGINS"
        emit(result, args.out)
        return 4
    result["verdict"] = "ELIGIBLE"
    emit(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
