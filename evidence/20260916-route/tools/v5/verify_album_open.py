#!/usr/bin/env python3
"""Verify that the one directed album-card click actually opened the target album.

Read-only analysis of two frozen frames (the pre-click frame and the immediate
post-click frame). This tool never sends input; the click itself is executed
separately (route-runbook.md attempt-05, S4).

Verdict rules (fail-closed; every rule and its inputs are recorded in the emitted
JSON):
  ALBUM_OPEN_VERIFIED  the target date title (start + end tokens inside one
                       title-sized window) is readable in the post frame AND the
                       surface changed substantively: the fraction of pixels whose
                       gray level differs by more than --delta is at least
                       --min-diff-fraction.
  TARGET_MISMATCH      the post frame shows a readable date-like title that does not
                       match the target, or a readable plausible photo count (1-3
                       digits) that is not the expected count.
  NO_EFFECT            the two frames are effectively identical (change below the
                       rule).
  INCONCLUSIVE         the surface changed but no target date title could be read.

Reading rules: OCR is the frozen card locator's reader. The count text below the
title is best-effort. An empty digit read is recorded UNREADABLE and never refuses;
a longer digit read that is not a plausible standalone count (for example a date
fragment) is recorded AMBIGUOUS_READ and never refuses. Only a readable plausible
count other than the expected one refuses.

Exit codes: 0 ALBUM_OPEN_VERIFIED, 3 NO_EFFECT, 4 TARGET_MISMATCH, 5 INCONCLUSIVE,
6 BAD_INPUT. Historical frames are never used: both frames must be the ones captured
for this run.

v4 (Rev21): the reader layer is macOS Vision (sibling vision_reader module); all v3 rules above are unchanged.
"""
import argparse
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


card = _load_sibling("locate_album_card")

DATE_LIKE = re.compile(r"\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,2}")


def emit(result, out_path):
    result["reader"] = card.vision_reader.record()
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    print(payload)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")


def diff_stats(pre, post, delta):
    w, h = pre.size
    px, qx = pre.load(), post.load()
    changed = 0
    x0 = y0 = None
    x1 = y1 = None
    grid = [[0] * 8 for _ in range(8)]
    for y in range(h):
        gy = min(7, y * 8 // h)
        for x in range(w):
            if abs(px[x, y] - qx[x, y]) > delta:
                changed += 1
                grid[gy][min(7, x * 8 // w)] += 1
                if x0 is None or x < x0:
                    x0 = x
                if y0 is None or y < y0:
                    y0 = y
                if x1 is None or x > x1:
                    x1 = x
                if y1 is None or y > y1:
                    y1 = y
    return {
        "changed_pixels": changed,
        "changed_fraction": round(changed / float(w * h), 6),
        "changed_bbox": None if x0 is None else [x0, y0, x1 + 1, y1 + 1],
        "changed_grid_8x8": grid,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pre")
    ap.add_argument("post")
    ap.add_argument("--expect-start", required=True)
    ap.add_argument("--expect-end", required=True)
    ap.add_argument("--expect-count", default="57")
    ap.add_argument("--delta", type=int, default=12)
    ap.add_argument("--min-diff-fraction", type=float, default=0.05)
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {
        "tool": "verify_album_open",
        "pre": args.pre,
        "post": args.post,
        "expected": {"start": args.expect_start, "end": args.expect_end,
                     "count": args.expect_count},
        "params": {"delta": args.delta, "min_diff_fraction": args.min_diff_fraction},
    }
    for path in (args.pre, args.post):
        if not os.path.exists(path):
            result["verdict"] = "BAD_INPUT"
            result["reason"] = "missing file: " + path
            emit(result, args.out)
            return 6
    pre = Image.open(args.pre).convert("L")
    post = Image.open(args.post).convert("L")
    result["pre_sha256"] = card.sha256_file(args.pre)
    result["post_sha256"] = card.sha256_file(args.post)
    result["pre_size"] = list(pre.size)
    result["post_size"] = list(post.size)
    if pre.size != post.size:
        result["verdict"] = "BAD_INPUT"
        result["reason"] = "size mismatch between pre and post"
        emit(result, args.out)
        return 6

    words = card.ocr_words(post)
    title = card.find_title(words, args.expect_start, args.expect_end)
    date_like = sorted({w["text"] for w in words if DATE_LIKE.search(w["text"])})
    result["post_ocr_words_seen"] = [w["text"] for w in words][:60]
    result["target_title_in_post"] = title
    result["date_like_tokens_in_post"] = date_like

    count_text = None
    if title:
        x0, y0, x1, y1 = title["bbox"]
        box = (max(0, x0 - 8), y1 + 2,
               min(post.size[0], x0 + 160), min(post.size[1], y1 + 32))
        digits_read = card.ocr_digits_region(post, box)
        result["count_box"] = list(box)
        result["count_digits_read"] = digits_read
        if digits_read == "":
            count_text = "UNREADABLE"
        elif args.expect_count in digits_read:
            count_text = "MATCH"
        elif len(digits_read) <= 3:
            count_text = "MISMATCH"
        else:
            count_text = "AMBIGUOUS_READ"
        result["count_text"] = count_text

    stats = diff_stats(pre, post, args.delta)
    result["diff"] = stats
    result["rules"] = [
        "ALBUM_OPEN_VERIFIED = target title readable in post AND changed_fraction >= min_diff_fraction",
        "TARGET_MISMATCH = readable non-target date-like title OR readable plausible count != expected",
        "NO_EFFECT = changed_fraction < min_diff_fraction (checked before the title rule)",
        "INCONCLUSIVE = surface changed but no target title readable",
    ]

    if count_text == "MISMATCH" or (title is None and date_like):
        result["verdict"] = "TARGET_MISMATCH"
        emit(result, args.out)
        return 4
    if stats["changed_fraction"] < args.min_diff_fraction:
        result["verdict"] = "NO_EFFECT"
        emit(result, args.out)
        return 3
    if title:
        result["verdict"] = "ALBUM_OPEN_VERIFIED"
        emit(result, args.out)
        return 0
    result["verdict"] = "INCONCLUSIVE"
    emit(result, args.out)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
