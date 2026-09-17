#!/usr/bin/env python3
"""Locate a LINE album card's vertical ellipsis (three stacked dots) from a frozen frame.

Read-only analysis. It never sends input; the single permitted ellipsis click is
executed separately (see route-runbook.md).

Steps:
  1. OCR the frame (tesseract chi_tra+eng, 3x upscale) and gate on the expected
     album title (both date groups must appear in reading order).
  2. Inside the title-row band, to the right of the title, find connected small
     blobs that deviate from the local background and require exactly one
     vertical three-dot pattern (spacing 3..10 px, same column +-3 px).
  3. Emit the click point (centre of the middle dot) plus evidence JSON.

Refusals (non-zero exit): 2 TARGET_TITLE_NOT_FOUND, 3 NO_ELLIPSIS_FOUND,
4 AMBIGUOUS_ELLIPSIS, 6 BAD_FRAME. Historical coordinates are never used:
every run must be given the frame captured for the current surface.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

from PIL import Image


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ocr_words(img3x_path):
    base = tempfile.mktemp(prefix="ocr_", dir="/tmp")
    subprocess.run(
        ["tesseract", img3x_path, base, "-l", "chi_tra+eng", "--psm", "6", "tsv"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tsv_path = base + ".tsv"
    words = []
    with open(tsv_path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 12 or parts[0] == "level":
                continue
            text = parts[11].strip()
            if not text:
                continue
            try:
                conf = float(parts[10])
            except ValueError:
                conf = -1.0
            words.append(
                {
                    "text": text,
                    "conf": conf,
                    "x": int(parts[6]) / 3.0,
                    "y": int(parts[7]) / 3.0,
                    "w": int(parts[8]) / 3.0,
                    "h": int(parts[9]) / 3.0,
                }
            )
    os.unlink(tsv_path)
    return words


def digits(text):
    return re.sub(r"\D", "", text)


def emit(result, out_path):
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def find_triples(components):
    triples = []
    for polarity in ("light", "dark"):
        ordered = sorted([c for c in components if c["polarity"] == polarity], key=lambda c: c["cy"])
        for i in range(len(ordered) - 2):
            d1, d2, d3 = ordered[i], ordered[i + 1], ordered[i + 2]
            if abs(d1["cx"] - d2["cx"]) > 3 or abs(d2["cx"] - d3["cx"]) > 3:
                continue
            if not (3 <= d2["cy"] - d1["cy"] <= 10 and 3 <= d3["cy"] - d2["cy"] <= 10):
                continue
            if d3["cy"] - d1["cy"] > 24:
                continue
            triples.append({"polarity": polarity, "dots": [d1, d2, d3]})
    return triples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--expect-start", required=True, help="album start, e.g. 2024/05/13")
    ap.add_argument("--expect-end", required=True, help="album end, e.g. 2024/05/17")
    ap.add_argument("--out")
    args = ap.parse_args()

    if not os.path.exists(args.frame):
        emit({"verdict": "BAD_FRAME", "frame": args.frame}, args.out)
        return 6

    im = Image.open(args.frame).convert("L")
    width, height = im.size
    up3 = im.resize((width * 3, height * 3), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        up3_path = tmp.name
    up3.save(up3_path)
    words = ocr_words(up3_path)
    os.unlink(up3_path)

    want_start = digits(args.expect_start)
    # The end date may appear either fully ("...~2024/05/17") or shared-year
    # compact ("2024/05/13~05/17" -> digits 202405130517), so accept the MMDD form
    # after the start key inside a title-sized window (<= 24 digits, <= 4 words).
    end_keys = {digits(args.expect_end), digits(args.expect_end)[-4:]}
    candidates = []
    if want_start and all(end_keys):
        for i in range(len(words)):
            combined = ""
            for j in range(i, min(i + 4, len(words))):
                combined += digits(words[j]["text"])
                if len(combined) > 24:
                    break
                if want_start in combined:
                    rest = combined[combined.index(want_start) + len(want_start) :]
                    if any(key in rest for key in end_keys):
                        candidates.append((j - i, len(combined), i, j))
    title = None
    if candidates:
        _, _, i0, i1 = min(candidates)
        sel = words[i0 : i1 + 1]
        x0 = min(w["x"] for w in sel)
        y0 = min(w["y"] for w in sel)
        x1 = max(w["x"] + w["w"] for w in sel)
        y1 = max(w["y"] + w["h"] for w in sel)
        title = {
            "texts": [w["text"] for w in sel],
            "bbox": [round(x0), round(y0), round(x1), round(y1)],
        }
    if not title:
        emit(
            {
                "verdict": "TARGET_TITLE_NOT_FOUND",
                "frame_sha256": sha256_file(args.frame),
                "frame_size": [width, height],
                "expected": [args.expect_start, args.expect_end],
                "ocr_words_seen": [w["text"] for w in words][:40],
            },
            args.out,
        )
        return 2

    x0, y0, x1, y1 = title["bbox"]
    band = {
        "x0": min(width - 2, x1 + 4),
        "x1": width - 1,
        "y0": max(0, y0 - 6),
        "y1": min(height - 1, y1 + 10),
    }
    samples = [
        im.getpixel((x, y))
        for y in range(band["y0"], band["y1"] + 1)
        for x in range(band["x0"], band["x1"] + 1)
    ]
    median = sorted(samples)[len(samples) // 2]

    marked = {}
    for y in range(band["y0"], band["y1"] + 1):
        for x in range(band["x0"], band["x1"] + 1):
            value = im.getpixel((x, y))
            if abs(value - median) >= 45:
                marked[(x, y)] = value

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
        w = max(xs) - min(xs) + 1
        h = max(ys) - min(ys) + 1
        if len(pixels) <= 16 and w <= 5 and h <= 5:
            sample = marked[(xs[0], ys[0])]
            components.append(
                {
                    "cx": sum(xs) / len(xs),
                    "cy": sum(ys) / len(ys),
                    "area": len(pixels),
                    "w": w,
                    "h": h,
                    "polarity": "light" if sample > median else "dark",
                }
            )

    below = [
        w["text"]
        for w in words
        if y1 + 2 <= w["y"] <= y1 + 34 and w["x"] <= x1 + 40 and w["text"].strip()
    ]

    triples = find_triples(components)
    result = {
        "frame_sha256": sha256_file(args.frame),
        "frame_size": [width, height],
        "expected": {"start": args.expect_start, "end": args.expect_end},
        "title": title,
        "title_band": band,
        "band_median_gray": median,
        "small_components": [
            {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c.items()}
            for c in components
        ],
        "nearby_texts_below_title": below,
        "triples_found": len(triples),
    }
    if not triples:
        result["verdict"] = "NO_ELLIPSIS_FOUND"
        emit(result, args.out)
        return 3
    if len(triples) > 1:
        result["verdict"] = "AMBIGUOUS_ELLIPSIS"
        result["triples"] = [
            [[round(d["cx"], 1), round(d["cy"], 1)] for d in t["dots"]] for t in triples
        ]
        emit(result, args.out)
        return 4

    chosen = triples[0]
    middle = chosen["dots"][1]
    result["verdict"] = "ELIGIBLE"
    result["ellipsis_polarity"] = chosen["polarity"]
    result["ellipsis_dots"] = [
        [round(d["cx"], 1), round(d["cy"], 1)] for d in chosen["dots"]
    ]
    result["click_point"] = [round(middle["cx"]), round(middle["cy"])]
    emit(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
