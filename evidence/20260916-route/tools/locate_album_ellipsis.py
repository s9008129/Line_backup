#!/usr/bin/env python3
"""Locate the album-level vertical ellipsis (three stacked dots) inside the opened album.

Read-only analysis of one frozen frame. It never sends input; the single permitted
album-level ellipsis click is executed separately (route-runbook.md attempt-05, S8).

Census (whole frame): the frame is scanned row by row. A row contributes candidates
only when its background is flat: at least --flat-fraction of its pixels lie within
--flat-tol gray levels of that row's median, so photo-grid rows are excluded. In a
flat row every pixel deviating from the row median by at least --delta is marked;
marked pixels of all flat rows are joined into 4-connected components; components of
at most --max-area pixels and at most --max-side pixels per side are kept as dots.

Candidates: exactly one vertical three-dot pattern (3..10 px between consecutive
dots, same column +-3 px, total span <= 24 px), the same rule as the frozen v2 card
locator. A candidate whose middle dot lies inside a readable multi-character OCR word
(at least two characters and at least one letter or digit, within --text-margin px) is
classified inside_text and is never eligible: glyph runs are not controls. A
punctuation-only token never blocks a candidate, because the control's own dots are
recognized by OCR as a colon-like token; the overlapping token is recorded as
evidence either way.

Eligibility: a candidate is eligible only when its middle dot lies inside the album
title row band derived from the verified title bbox (--title-bbox, the S5 value; when
omitted the title is re-derived here by OCR) and to the right of the title. Candidates
inside the group-title row band (--group-title-bbox, or --expect-group-title when that
name is readable on the frame) are never eligible; when they are the only candidates
the verdict is GROUP_LEVEL_ONLY.

Exit codes: 0 ELIGIBLE, 2 TARGET_TITLE_NOT_FOUND, 3 NO_ELLIPSIS_FOUND,
4 AMBIGUOUS_ELLIPSIS, 5 GROUP_LEVEL_ONLY, 6 BAD_FRAME. Historical coordinates are
never used: every run must be given the frame captured for the current surface.
"""
import argparse
import importlib.util
import json
import os

from PIL import Image


def _load_sibling(name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


card = _load_sibling("locate_album_card")


def emit(result, out_path):
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def census_dots(im, delta, flat_tol, flat_fraction, max_area, max_side):
    width, height = im.size
    px = im.load()
    marked = set()
    flat_rows = 0
    row_medians = {}
    for y in range(height):
        values = list(im.crop((0, y, width, y + 1)).tobytes())
        ordered = sorted(values)
        median = ordered[len(ordered) // 2]
        flat = sum(1 for v in values if abs(v - median) <= flat_tol)
        flatness = flat / float(len(values))
        row_medians[y] = median
        if flatness < flat_fraction:
            continue
        flat_rows += 1
        for x in range(width):
            if abs(px[x, y] - median) >= delta:
                marked.add((x, y))

    seen = set()
    dots = []
    large = 0
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
        if len(pixels) > max_area or w > max_side or h > max_side:
            large += 1
            continue
        cy = sum(ys) / len(ys)
        dots.append({"cx": sum(xs) / len(xs), "cy": cy,
                     "area": len(pixels), "w": w, "h": h,
                     "row_median": row_medians.get(int(round(cy)))})
    dots.sort(key=lambda d: (d["cy"], d["cx"]))
    return dots, {"rows": height, "flat_rows": flat_rows,
                  "marked_pixels": len(marked), "large_components": large}


def find_triples(components):
    triples = []
    for i in range(len(components) - 2):
        for j in range(i + 1, len(components) - 1):
            for k in range(j + 1, len(components)):
                d1, d2, d3 = components[i], components[j], components[k]
                if not (d1["cy"] <= d2["cy"] <= d3["cy"]):
                    continue
                if abs(d1["cx"] - d2["cx"]) > 3 or abs(d2["cx"] - d3["cx"]) > 3:
                    continue
                if not (3 <= d2["cy"] - d1["cy"] <= 10 and 3 <= d3["cy"] - d2["cy"] <= 10):
                    continue
                if d3["cy"] - d1["cy"] > 24:
                    continue
                triples.append({"dots": [d1, d2, d3]})
    return triples


def word_boxes(words):
    return [(w["x"], w["y"], w["x"] + w["w"], w["y"] + w["h"], w["text"]) for w in words]


def blocking_word(cx, cy, words, margin):
    for w in words:
        x0, y0, x1, y1 = w["x"], w["y"], w["x"] + w["w"], w["y"] + w["h"]
        if x0 - margin <= cx <= x1 + margin and y0 - margin <= cy <= y1 + margin:
            text = w["text"]
            alnum = any(c.isalnum() for c in text)
            if len(text) >= 2 and alnum:
                return {"text": text, "conf": round(w["conf"], 1)}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--expect-start", required=True)
    ap.add_argument("--expect-end", required=True)
    ap.add_argument("--title-bbox", help="verified title bbox x0,y0,x1,y1 from S5")
    ap.add_argument("--expect-group-title", help="group name, when readable on the frame")
    ap.add_argument("--group-title-bbox", help="group title row bbox x0,y0,x1,y1")
    ap.add_argument("--delta", type=int, default=45)
    ap.add_argument("--flat-tol", type=int, default=25)
    ap.add_argument("--flat-fraction", type=float, default=0.6)
    ap.add_argument("--max-area", type=int, default=16)
    ap.add_argument("--max-side", type=int, default=5)
    ap.add_argument("--text-margin", type=int, default=6)
    ap.add_argument("--out")
    args = ap.parse_args()

    if not os.path.exists(args.frame):
        emit({"tool": "locate_album_ellipsis", "verdict": "BAD_FRAME", "frame": args.frame},
             args.out)
        return 6

    im = Image.open(args.frame).convert("L")
    width, height = im.size
    words = card.ocr_words(im)
    boxes = word_boxes(words)

    title_bbox = None
    title_source = None
    if args.title_bbox:
        parts = [int(v) for v in args.title_bbox.split(",")]
        if len(parts) == 4:
            title_bbox = parts
            title_source = "given (S5 verify_album_open)"
    if title_bbox is None:
        derived = card.find_title(words, args.expect_start, args.expect_end)
        if derived:
            title_bbox = derived["bbox"]
            title_source = "ocr re-derivation"

    result = {
        "tool": "locate_album_ellipsis",
        "frame": args.frame,
        "frame_sha256": card.sha256_file(args.frame),
        "frame_size": [width, height],
        "params": {"delta": args.delta, "flat_tol": args.flat_tol,
                   "flat_fraction": args.flat_fraction,
                   "max_area": args.max_area, "max_side": args.max_side,
                   "text_margin": args.text_margin},
        "ocr_words_seen": [w["text"] for w in words][:60],
        "title_bbox": title_bbox,
        "title_bbox_source": title_source,
    }
    if title_bbox is None:
        result["verdict"] = "TARGET_TITLE_NOT_FOUND"
        emit(result, args.out)
        return 2

    group_bbox = None
    if args.group_title_bbox:
        parts = [int(v) for v in args.group_title_bbox.split(",")]
        if len(parts) == 4:
            group_bbox = parts
            result["group_title_bbox_source"] = "given"
    elif args.expect_group_title:
        wanted = "".join(args.expect_group_title.split())
        for x0, y0, x1, y1, text in boxes:
            if wanted and wanted in "".join(text.split()):
                group_bbox = [x0, y0, x1, y1]
                result["group_title_bbox_source"] = "ocr word match"
                break
    result["group_title_bbox"] = group_bbox

    dots, census = census_dots(im, args.delta, args.flat_tol, args.flat_fraction,
                               args.max_area, args.max_side)
    result["census"] = census
    result["dots"] = [
        {"cx": round(d["cx"], 1), "cy": round(d["cy"], 1), "area": d["area"],
         "w": d["w"], "h": d["h"], "row_median": d["row_median"]} for d in dots
    ]

    tx0, ty0, tx1, ty1 = title_bbox
    band = {"x0": tx1 + 2, "x1": width - 1, "y0": max(0, ty0 - 6), "y1": min(height - 1, ty1 + 10)}
    result["album_title_band"] = band

    triples = find_triples(dots)
    classified = []
    for triple in triples:
        mid = triple["dots"][1]
        cx, cy = mid["cx"], mid["cy"]
        blocker = blocking_word(cx, cy, words, args.text_margin)
        triple["overlapping_ocr_token"] = blocker
        if blocker:
            region = "inside_text"
        elif group_bbox and group_bbox[1] - 6 <= cy <= group_bbox[3] + 6:
            region = "group_title_band"
        elif band["y0"] <= cy <= band["y1"]:
            region = "album_title_band" if cx >= band["x0"] else "album_title_band_left_of_title"
        elif cy < band["y0"]:
            region = "above_album_title_band"
        else:
            region = "below_album_title_band"
        triple["region"] = region
        triple["middle"] = {"cx": round(cx, 1), "cy": round(cy, 1)}
        classified.append(triple)

    result["triples"] = [
        {"region": t["region"], "middle": t["middle"],
         "overlapping_ocr_token": t["overlapping_ocr_token"],
         "dots": [[round(d["cx"], 1), round(d["cy"], 1)] for d in t["dots"]]}
        for t in classified
    ]
    eligible = [t for t in classified if t["region"] == "album_title_band"]

    if len(eligible) > 1:
        result["verdict"] = "AMBIGUOUS_ELLIPSIS"
        emit(result, args.out)
        return 4
    if len(eligible) == 0:
        if classified and group_bbox and all(t["region"] == "group_title_band" for t in classified):
            result["verdict"] = "GROUP_LEVEL_ONLY"
            emit(result, args.out)
            return 5
        result["verdict"] = "NO_ELLIPSIS_FOUND"
        emit(result, args.out)
        return 3

    chosen = eligible[0]
    middle = chosen["dots"][1]
    result["verdict"] = "ELIGIBLE"
    result["ellipsis_dots"] = [[round(d["cx"], 1), round(d["cy"], 1)] for d in chosen["dots"]]
    result["click_point"] = [round(middle["cx"]), round(middle["cy"])]
    emit(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
