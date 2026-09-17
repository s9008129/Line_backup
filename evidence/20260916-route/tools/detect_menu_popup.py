#!/usr/bin/env python3
"""Detect a newly rendered popup/menu by comparing a pre and a post capture.

Read-only analysis. It never sends input; the single permitted ellipsis click is
executed separately (see the route runbook).

Verdict rules (both required, fail-closed):
  geometry: at least one 4-connected changed-pixel component (|post-pre| > --delta)
            whose bounding box is >= --min-w x --min-h and whose size is >= --min-pixels.
  text:     at least --min-strings OCR strings of >= --min-strlen characters inside
            that component's bounding box (tesseract, 3x upscale, chi_tra+eng).
OCR alone or geometry alone never yields menu_detected=true.

Exit codes: 0 menu_detected true; 3 not detected; 6 BAD_INPUT (missing/unreadable/size mismatch).
"""
import argparse
import hashlib
import io
import json
import os
import subprocess

from PIL import Image


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ocr_strings(img, box):
    """OCR the bbox and return the transcribed strings (empty list on failure).

    Fail-closed: a tesseract failure never raises; it returns None so the caller
    can record OCR_FAILED and keep the verdict NOT_DETECTED.
    """
    crop = img.crop(box)
    w, h = crop.size
    up = crop.resize((max(1, w * 3), max(1, h * 3)), Image.LANCZOS)
    buf = io.BytesIO()
    up.save(buf, format="PNG")
    try:
        proc = subprocess.run(
            ["tesseract", "-", "stdout", "-l", "chi_tra+eng", "--psm", "6", "tsv"],
            input=buf.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    text = proc.stdout.decode("utf-8", errors="replace")
    strings = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 12 or parts[0] == "level":
            continue
        value = parts[11].strip()
        if value:
            strings.append(value)
    return strings


def emit(result, out_path):
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pre")
    ap.add_argument("post")
    ap.add_argument("--out")
    ap.add_argument("--delta", type=int, default=12)
    ap.add_argument("--min-w", type=int, default=40)
    ap.add_argument("--min-h", type=int, default=20)
    ap.add_argument("--min-pixels", type=int, default=200)
    ap.add_argument("--min-strings", type=int, default=2)
    ap.add_argument("--min-strlen", type=int, default=2)
    args = ap.parse_args()

    result = {"tool": "detect_menu_popup", "pre": args.pre, "post": args.post,
              "params": {"delta": args.delta, "min_w": args.min_w, "min_h": args.min_h,
                         "min_pixels": args.min_pixels, "min_strings": args.min_strings,
                         "min_strlen": args.min_strlen}}
    for path in (args.pre, args.post):
        if not os.path.exists(path):
            result["verdict"] = "BAD_INPUT"
            result["reason"] = f"missing file: {path}"
            emit(result, args.out)
            return 6
    pre = Image.open(args.pre).convert("L")
    post = Image.open(args.post).convert("L")
    result["pre_sha256"] = sha256_file(args.pre)
    result["post_sha256"] = sha256_file(args.post)
    result["pre_size"] = list(pre.size)
    result["post_size"] = list(post.size)
    if pre.size != post.size:
        result["verdict"] = "BAD_INPUT"
        result["reason"] = "size mismatch between pre and post"
        emit(result, args.out)
        return 6

    w, h = pre.size
    px, qx = pre.load(), post.load()
    marked = set()
    for y in range(h):
        for x in range(w):
            if abs(px[x, y] - qx[x, y]) > args.delta:
                marked.add((x, y))
    seen = set()
    components = []
    for point in list(marked):
        if point in seen:
            continue
        stack = [point]
        seen.add(point)
        pixels = []
        while stack:
            cx, cy = stack.pop()
            pixels.append((cx, cy))
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if (nx, ny) in marked and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    stack.append((nx, ny))
        xs = [p[0] for p in pixels]
        ys = [p[1] for p in pixels]
        components.append({"bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1],
                           "pixels": len(pixels),
                           "w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1})
    components.sort(key=lambda c: c["pixels"], reverse=True)
    result["changed_pixels_total"] = len(marked)
    result["components"] = components[:10]

    eligible = [c for c in components
                if c["w"] >= args.min_w and c["h"] >= args.min_h and c["pixels"] >= args.min_pixels]
    if not eligible:
        result["verdict"] = "NOT_DETECTED"
        result["reason"] = "no changed region meeting the geometry rule"
        emit(result, args.out)
        return 3

    best = eligible[0]
    x0, y0, x1, y1 = best["bbox"]
    m = 4
    box = (max(0, x0 - m), max(0, y0 - m), min(w, x1 + m), min(h, y1 + m))
    ocr = ocr_strings(post, box)
    result["chosen_bbox"] = best["bbox"]
    if ocr is None:
        result["ocr_strings"] = []
        result["ocr_status"] = "OCR_FAILED"
        result["verdict"] = "NOT_DETECTED"
        result["reason"] = "geometry present but OCR could not run (fail-closed)"
        emit(result, args.out)
        return 3
    result["ocr_status"] = "OK"
    strings = [s for s in ocr if len(s) >= args.min_strlen]
    result["ocr_strings"] = strings
    if len(strings) < args.min_strings:
        result["verdict"] = "NOT_DETECTED"
        result["reason"] = "geometry present but OCR strings below the rule"
        emit(result, args.out)
        return 3
    result["verdict"] = "MENU_DETECTED"
    result["reason"] = "new region plus transcribed menu strings"
    emit(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
