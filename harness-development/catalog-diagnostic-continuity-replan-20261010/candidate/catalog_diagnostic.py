#!/usr/bin/env python3
# catalog_diagnostic.py -- task-local evaluator for the LINE album catalog diagnostic
# (TASK-20261010-catalog-diagnostic-continuity-replan).
#
# Read-only with respect to the OS: it reads saved artifacts, never captures the
# screen, never sends input, and writes only into NEW output directories using
# exclusive creation. It does not import third-party packages (stdlib only).
#
# Subcommands:
#   prepare-replay  --source OLD_TASK --out replay
#   verify-packet   --packet-root TASK
#   evaluate        --mode replay|live --binding FILE --frame-manifest FILE \
#                   --modern FILE --legacy FILE --previous FILE_OR_NONE --out NEW_DIRECTORY
#
# Normative spec: harness-development/catalog-diagnostic-continuity-replan-20261010/diagnostic-spec.json
# Frozen handoff: .../handoff.md (sha256 in that spec)

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date

PROG = "catalog_diagnostic"
FORMAT = "local-catalog-diagnostic-1"
FULL_COLLECTION_COVERAGE = "NOT_ESTABLISHED"

# ---------------------------------------------------------------- small utils


class DiagError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def fail(code, detail=""):
    raise DiagError(code, detail)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    with open(path, "rb") as fh:
        return json.load(fh)


def require_regular_file(path):
    if path is None:
        fail("INPUT_MISSING", "null path")
    if os.path.islink(path):
        fail("INPUT_IS_SYMLINK", path)
    if not os.path.isfile(path):
        fail("INPUT_MISSING", path)
    return path


def create_new_directory(path):
    if os.path.islink(path):
        fail("OUTPUT_IS_SYMLINK", path)
    if os.path.exists(path):
        fail("OUTPUT_DIRECTORY_EXISTS", path)
    os.makedirs(path, exist_ok=False)


def write_new_file(path, data):
    if os.path.islink(path):
        fail("OUTPUT_IS_SYMLINK", path)
    if os.path.exists(path):
        fail("OUTPUT_EXISTS", path)
    with open(path, "xb") as fh:
        fh.write(data)


def write_json_new(path, obj):
    data = json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    write_new_file(path, data)


def fail_json(path, obj, exit_status=1):
    write_json_new(path, obj)
    sys.exit(exit_status)


# ---------------------------------------------------------------- geometry


def rect_from_obj(obj, where):
    if not isinstance(obj, dict):
        fail("RECT_NOT_OBJECT", where)
    try:
        x0 = int(obj["x0"]); y0 = int(obj["y0"]); x1 = int(obj["x1"]); y1 = int(obj["y1"])
    except (KeyError, TypeError, ValueError):
        fail("RECT_FIELDS_MISSING", where)
    if x0 < 0 or y0 < 0 or x0 >= x1 or y0 >= y1:
        fail("RECT_INVALID", f"{where}={obj}")
    return (x0, y0, x1, y1)


def rect_intersect(a, b):
    x0 = max(a[0], b[0]); y0 = max(a[1], b[1])
    x1 = min(a[2], b[2]); y1 = min(a[3], b[3])
    if x0 < x1 and y0 < y1:
        return (x0, y0, x1, y1)
    return None


def rect_within_inner(inner, outer):
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def region_bytes(rgba, width, rect):
    x0, y0, x1, y1 = rect
    out = bytearray()
    for y in range(y0, y1):
        base = (y * width + x0) * 4
        out += rgba[base:base + (x1 - x0) * 4]
    return bytes(out)


def region_hash(rgba, width, rect):
    return sha256_bytes(region_bytes(rgba, width, rect))


def region_diff_mask(rgba_a, rgba_b, width, rect):
    """Pixel coordinates where RGBA differs inside rect (row-major order)."""
    x0, y0, x1, y1 = rect
    diffs = []
    for y in range(y0, y1):
        base = (y * width + x0) * 4
        a = rgba_a[base:base + (x1 - x0) * 4]
        b = rgba_b[base:base + (x1 - x0) * 4]
        if a != b:
            for i in range(0, len(a), 4):
                if a[i:i + 4] != b[i:i + 4]:
                    diffs.append((x0 + i // 4, y))
    return diffs


def load_rgba(decoded_path, width, height):
    require_regular_file(decoded_path)
    with open(decoded_path, "rb") as fh:
        data = fh.read()
    if len(data) != width * height * 4:
        fail("RGBA_SIZE_MISMATCH", f"{decoded_path}: {len(data)} != {width*height*4}")
    return data


# ---------------------------------------------------------------- OCR items


def normalize_ocr_items(payload, where):
    """Normalize a modern/legacy OCR artifact into a list of dicts.

    Returns (items, completeness) where completeness is COMPLETE only when every
    item carried an explicit candidates list; legacy single-candidate artifacts
    (no candidates array) are recorded as UNKNOWN, never invented.
    """
    if not isinstance(payload, dict):
        fail("OCR_ARTIFACT_NOT_OBJECT", where)
    raw = payload.get("items")
    if not isinstance(raw, list) or not raw:
        fail("OCR_ITEMS_MISSING", where)
    items = []
    completeness = "COMPLETE"
    for idx, it in enumerate(raw):
        if not isinstance(it, dict):
            fail("OCR_ITEM_NOT_OBJECT", f"{where}[{idx}]")
        text = it.get("text")
        if not isinstance(text, str):
            fail("OCR_ITEM_TEXT_MISSING", f"{where}[{idx}]")
        conf = it.get("confidence")
        box = it.get("boxTopLeftSourcePixels")
        if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
            fail("OCR_ITEM_BOX_MISSING", f"{where}[{idx}]")
        cands = it.get("candidates")
        if isinstance(cands, list) and cands:
            cand_list = []
            for c in cands:
                if not isinstance(c, dict) or not isinstance(c.get("text"), str):
                    fail("OCR_CANDIDATE_INVALID", f"{where}[{idx}]")
                cc = c.get("confidence")
                cand_list.append({"text": c["text"], "confidence": cc if isinstance(cc, (int, float)) else None})
        elif isinstance(cands, list) and not cands:
            cand_list = [{"text": text, "confidence": conf if isinstance(conf, (int, float)) else None}]
            completeness = "UNKNOWN"
        else:
            cand_list = [{"text": text, "confidence": conf if isinstance(conf, (int, float)) else None}]
            completeness = "UNKNOWN"
        items.append({
            "text": text,
            "confidence": conf if isinstance(conf, (int, float)) else None,
            "box": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
            "candidates": cand_list,
        })
    return items, completeness


# ---------------------------------------------------------------- parsing


DATE_RE = re.compile(
    r"^(?P<sy>\d{4})/(?P<sm>\d{1,2})/(?P<sd>\d{1,2})"
    r"[~～〜\-]"
    r"(?:(?P<ey>\d{4})/)?(?P<em>\d{1,2})/(?P<ed>\d{1,2})$"
)
DATE_SHAPE_RE = re.compile(r"^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}[~～〜\-].+$")
COUNT_RE = re.compile(r"^[0-9]+$")


def strip_ws(s):
    return re.sub(r"\s+", "", s)


def parse_date_text(text):
    """Return ISO (start, end) or None. Format normalization only; no glyph guessing."""
    if not isinstance(text, str):
        return None
    core = strip_ws(text)
    if not core:
        return None
    m = DATE_RE.match(core)
    if not m:
        return None
    sy = int(m.group("sy")); sm = int(m.group("sm")); sd = int(m.group("sd"))
    ey = int(m.group("ey")) if m.group("ey") else sy
    em = int(m.group("em")); ed = int(m.group("ed"))
    if not (1 <= sm <= 12 and 1 <= em <= 12):
        return None
    try:
        start = date(sy, sm, sd)
    except ValueError:
        return None
    try:
        end = date(ey, em, ed)
    except ValueError:
        return None
    if start > end:
        return None
    return (start.isoformat(), end.isoformat())


def parse_count_text(text):
    """Return a positive ASCII integer or None. No O/l/S substitutions."""
    if not isinstance(text, str):
        return None
    core = strip_ws(text)
    if not core or not COUNT_RE.match(core):
        return None
    value = int(core)
    if value <= 0:
        return None
    return value


COUNT_NOISE_RE = re.compile(r"^[0-9OoIlSsBbZzGgqQ\s]+$")


def count_like_without_valid_parse(text):
    """True when a string is digit-bearing count-like OCR noise (e.g. 6O, 0, O6).

    Such a string must not be silently dropped: it is recorded as a partial
    count candidate (fail closed). Pure non-digit strings such as labels are not
    count-like.
    """
    if not isinstance(text, str):
        return False
    core = strip_ws(text)
    if not core or not COUNT_NOISE_RE.match(core):
        return False
    return any(ch.isdigit() for ch in core)


def row_extent(item):
    x, y, w, h = item["box"]
    return (x, y, x + w, y + h)


# ---------------------------------------------------------------- pixel guard (text continuity)


def pixel_guard(current_rgba, current_w, previous_rgba, previous_w, guard, exclusions, image_rect):
    """Exact RGBA guard over the frozen full text slots.

    Returns a dict with status PASS/UNKNOWN/CONFLICT. No tolerance is ever added.
    """
    result = {
        "guard_rect": list(guard),
        "exclusions": [list(e) for e in exclusions],
        "pixel_diff_count": None,
        "first_diff": None,
        "current_region_sha256": None,
        "previous_region_sha256": None,
    }
    if not rect_within_inner(guard, image_rect):
        result["status"] = "UNKNOWN"
        result["reason"] = "guard rect outside image"
        return result
    for ex in exclusions:
        if rect_intersect(guard, ex):
            result["status"] = "UNKNOWN"
            result["reason"] = f"guard overlaps frozen exclusion {ex}"
            return result
    if current_rgba is None or previous_rgba is None:
        result["status"] = "UNKNOWN"
        result["reason"] = "missing decoded RGBA for guard comparison"
        return result
    result["current_region_sha256"] = region_hash(current_rgba, current_w, guard)
    result["previous_region_sha256"] = region_hash(previous_rgba, previous_w, guard)
    if current_w != previous_w:
        result["status"] = "CONFLICT"
        result["reason"] = "frame widths differ; guard not comparable"
        return result
    diffs = region_diff_mask(current_rgba, previous_rgba, current_w, guard)
    result["pixel_diff_count"] = len(diffs)
    if diffs:
        result["first_diff"] = list(diffs[0])
        result["status"] = "CONFLICT"
        result["reason"] = "text slot pixels differ from previous frame"
        return result
    result["status"] = "PASS"
    result["reason"] = "full-slot RGBA identical"
    return result


# ---------------------------------------------------------------- indicator


def luma_of(r, g, b):
    return (54 * r + 183 * g + 19 * b) >> 8


def bright_mask(rgba, width, rect, threshold=128):
    x0, y0, x1, y1 = rect
    cells = set()
    for y in range(y0, y1):
        base = y * width * 4
        for x in range(x0, x1):
            i = base + x * 4
            if luma_of(rgba[i], rgba[i + 1], rgba[i + 2]) >= threshold:
                cells.add((x, y))
    return cells


def connected_components_8(cells):
    remaining = set(cells)
    comps = []
    while remaining:
        seed = remaining.pop()
        comp = [seed]
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    n = (x + dx, y + dy)
                    if n in remaining:
                        remaining.remove(n)
                        comp.append(n)
                        stack.append(n)
        comps.append(comp)
    return comps


def bbox_of(cells):
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def indicator_check(rgba, width, indicator, image_rect):
    """Independent structural check of the selected-tab indicator.

    Region: the frozen indicator search band (album + notes tab width).
    Signal: fixed luma formula, bright >= 128, 8-connectivity, no component
    dropping, no dilation/erosion.
    """
    result = {
        "region": list(indicator["region"]),
        "album_region": list(indicator["album_region"]),
        "notes_region": list(indicator["notes_region"]),
        "threshold": 128,
        "raw_rgba_retained": True,
    }
    def _rect(obj, where):
        if isinstance(obj, dict):
            return rect_from_obj(obj, where)
        if isinstance(obj, (list, tuple)) and len(obj) == 4:
            return tuple(int(v) for v in obj)
        fail("INDICATOR_REGION_INVALID", where)

    album_region = _rect(indicator["album_region"], "album_region")
    notes_region = _rect(indicator["notes_region"], "notes_region")
    full_region = _rect(indicator["region"], "region")
    for key, rect in (("region", full_region), ("album_region", album_region),
                      ("notes_region", notes_region)):
        if not rect_within_inner(rect, image_rect):
            result["status"] = "UNKNOWN"
            result["reason"] = f"{key} outside image"
            return result
    if rgba is None:
        result["status"] = "UNKNOWN"
        result["reason"] = "missing decoded RGBA for indicator"
        return result
    notes_cells = bright_mask(rgba, width, notes_region)
    result["notes_bright_pixels"] = len(notes_cells)
    if notes_cells:
        result["status"] = "CONFLICT"
        result["reason"] = "bright structure present under 記事本 tab"
        return result
    album_cells = bright_mask(rgba, width, album_region)
    result["album_bright_pixels"] = len(album_cells)
    if not album_cells:
        result["status"] = "UNKNOWN"
        result["reason"] = "no selected indicator found under 相簿 tab"
        return result
    comps = connected_components_8(album_cells)
    if len(comps) != 1:
        result["status"] = "CONFLICT"
        result["reason"] = f"{len(comps)} separate bright components under 相簿 tab"
        result["component_count"] = len(comps)
        return result
    comp = comps[0]
    bbox = bbox_of(comp)
    result["component_count"] = 1
    result["baseline_bbox"] = list(indicator["baseline_bbox"])
    result["baseline_mask_sha256"] = indicator["baseline_mask_sha256"]
    result["observed_bbox"] = list(bbox)
    result["observed_mask_sha256"] = sha256_bytes(
        json.dumps(sorted(comp), separators=(",", ":")).encode("utf-8"))
    if bbox[2] - bbox[0] <= bbox[3] - bbox[1]:
        result["status"] = "CONFLICT"
        result["reason"] = "indicator component is not wider than tall"
        return result
    cx = (bbox[0] + bbox[2]) / 2
    album_tab = tuple(indicator["album_tab_horizontal"])
    if not (album_tab[0] <= cx <= album_tab[1]):
        result["status"] = "CONFLICT"
        result["reason"] = "indicator horizontal center outside 相簿 tab"
        return result
    if result["observed_mask_sha256"] != indicator["baseline_mask_sha256"] or bbox != tuple(indicator["baseline_bbox"]):
        result["status"] = "CONFLICT"
        result["reason"] = "indicator structure differs from frozen baseline"
        return result
    result["status"] = "PASS"
    result["reason"] = "single horizontal bright component under 相簿; 記事本 clear; matches baseline"
    return result


# ---------------------------------------------------------------- identity rows


def boxes_fit(item, image_rect, viewport):
    x, y, w, h = item["box"]
    box = (x, y, x + w, y + h)
    if not rect_within_inner(box, image_rect):
        return False, box
    if not rect_within_inner(box, viewport):
        return False, box
    return True, box


def classify_date_items(items, image_rect, viewport):
    """Parse date items. Returns (rows, partial_rows, conflicts).

    Every OCR item whose best candidate parses as a calendar date becomes a row.
    Items that are neither valid dates nor valid counts are ignored as non-metadata
    text. Candidate disagreement on a date row is an identity conflict.
    """
    rows, partial, conflicts = [], [], []
    for idx, it in enumerate(items):
        best = it["candidates"][0]
        best_parsed = parse_date_text(best["text"])
        all_parsed = []
        seen = set()
        for c in it["candidates"]:
            p = parse_date_text(c["text"])
            if p is not None and p not in seen:
                seen.add(p)
                all_parsed.append((c["text"], p))
        fits, box = boxes_fit(it, image_rect, viewport)
        if best_parsed is None:
            if any(p is not None for _, p in all_parsed):
                conflicts.append({
                    "kind": "date_candidate_disagreement",
                    "index": idx, "text": best["text"], "box": list(box),
                    "detail": "best date candidate does not parse but another candidate does",
                    "alternatives": [
                        {"text": t, "parsed": list(p)} for t, p in all_parsed],
                })
                continue
            if DATE_SHAPE_RE.match(strip_ws(best["text"])):
                partial.append({
                    "index": idx, "text": best["text"], "confidence": it["confidence"],
                    "box": list(box), "parsed": None, "raw_candidates": it["candidates"],
                    "fits": fits, "visibility": "invalid",
                    "row_completeness": "COMPLETE" if it.get("completeness") != "UNKNOWN" else "UNKNOWN",
                    "detail": "date-shaped text that is not a valid calendar interval (invalid date or start>end)",
                })
            continue
        if len(all_parsed) > 1:
            conflicts.append({
                "kind": "date_candidate_disagreement",
                "index": idx, "text": best["text"], "box": list(box),
                "detail": "multiple candidates parse to different valid dates",
                "alternatives": [{"text": t, "parsed": list(p)} for t, p in all_parsed],
            })
            continue
        row = {
            "index": idx, "text": best["text"], "confidence": it["confidence"],
            "box": list(box), "parsed": list(best_parsed),
            "raw_candidates": it["candidates"], "fits": fits,
            "row_completeness": "COMPLETE" if it.get("completeness") != "UNKNOWN" else "UNKNOWN",
        }
        if not fits:
            row["visibility"] = "clipped"
            partial.append({**row, "detail": "date box not fully inside image/viewport"})
        else:
            row["visibility"] = "visible"
            rows.append(row)
    return rows, partial, conflicts


def classify_count_items(items, date_indices, image_rect, viewport):
    """Count items = best-candidate pure ASCII decimal, positioned below a date row.

    Strings that are count-like but do not parse (6O, 0, O6) are returned
    separately as noise so the decision can fail closed instead of silently
    dropping a count candidate.
    """
    count_items = []
    noise_items = []
    for idx, it in enumerate(items):
        if idx in date_indices:
            continue
        best = it["candidates"][0]
        parsed = parse_count_text(best["text"])
        if parsed is None:
            if count_like_without_valid_parse(best["text"]):
                noise_items.append({
                    "index": idx, "text": best["text"], "confidence": it["confidence"],
                    "box": list(row_extent(it)),
                })
            continue
        fits, box = boxes_fit(it, image_rect, viewport)
        conflicts = []
        seen = set()
        for c in it["candidates"]:
            p = parse_count_text(c["text"])
            if p is not None and p not in seen:
                seen.add(p)
                conflicts.append({"text": c["text"], "parsed": p})
        count_items.append({
            "index": idx, "text": best["text"], "confidence": it["confidence"],
            "box": list(box), "parsed": parsed, "raw_candidates": it["candidates"],
            "fits": fits,
            "candidate_conflict": len(conflicts) > 1,
            "candidate_parses": conflicts,
            "row_completeness": "COMPLETE" if it.get("completeness") != "UNKNOWN" else "UNKNOWN",
        })
    return count_items, noise_items


def pair_rows(date_rows, count_items, noise_items=None):
    """Pair each date row with the unique count row directly below it.

    Geometric pairing only; never confidence. Returns (complete_rows, partial_rows,
    ambiguous, conflicts). Count-like noise rows and dates with no count row at
    all fail closed as partial/ambiguous; they are never silently dropped.
    """
    complete, partial, ambiguous, conflicts = [], [], [], []
    used_counts = {}
    noise_items = noise_items or []
    for drow in date_rows:
        dx0, dy0, dx1, dy1 = drow["box"]
        dh = dy1 - dy0
        eligible = []
        for crow in count_items:
            cx0, cy0, cx1, cy1 = crow["box"]
            ch = cy1 - cy0
            if not (cy0 >= dy1):
                continue
            if (cy0 - dy1) > 2 * max(dh, ch):
                continue
            if abs(cx0 - dx0) > max(dh, ch):
                continue
            eligible.append(crow)
        noise_below = [n for n in noise_items
                       if n["box"][1] >= dy1 and (n["box"][1] - dy1) <= 2 * dh
                       and abs(n["box"][0] - dx0) <= dh]
        if len(eligible) == 0 and noise_below:
            ambiguous.append({
                "kind": "count_like_without_valid_parse",
                "date_text": drow["text"], "box": list(drow["box"]),
                "noise": [{"text": n["text"], "box": n["box"]} for n in noise_below],
                "detail": "digit-bearing count-like OCR below the date is not a complete "
                          "ASCII decimal; identity not fabricated",
            })
            continue
        if len(eligible) == 0:
            partial.append({
                **drow, "count_candidates": [],
                "detail": "no count row found directly below the date",
            })
            continue
        if len(eligible) != 1:
            partial.append({
                **drow, "count_candidates": [c["index"] for c in eligible],
                "detail": "no unique count row directly below date" if not eligible else "multiple count rows eligible",
            })
            continue
        crow = eligible[0]
        if not crow["fits"]:
            partial.append({**drow, "count_candidates": [crow["index"]],
                            "detail": "count box clipped"})
            continue
        if crow["candidate_conflict"]:
            conflicts.append({
                "kind": "count_candidate_disagreement", "date_text": drow["text"],
                "count_text": crow["text"],
                "detail": "count candidates parse to different valid numbers",
                "alternatives": crow["candidate_parses"],
            })
            continue
        if crow["index"] in used_counts:
            conflicts.append({
                "kind": "count_reused", "date_text": drow["text"],
                "previous_date_text": used_counts[crow["index"]],
                "count_text": crow["text"],
            })
            continue
        used_counts[crow["index"]] = drow["text"]
        complete.append({
            "identity_dates": list(drow["parsed"]),
            "count": crow["parsed"],
            "date_text": drow["text"], "count_text": crow["text"],
            "date_box": list(drow["box"]), "count_box": list(crow["box"]),
            "date_confidence": drow["confidence"], "count_confidence": crow["confidence"],
            "date_candidates": drow.get("raw_candidates"),
            "count_candidates": crow.get("raw_candidates"),
        })
    if ambiguous:
        return complete, partial, ambiguous, conflicts
    return complete, partial, ambiguous, conflicts


def qualified_overlap_rows(complete_rows, modern_items, legacy_items):
    """Rows whose identity is read identically by BOTH APIs.

    Legacy-only or modern-only rows stay unconfirmed; missing legacy reads are never
    treated as agreement.
    """
    legacy_dates, legacy_counts = [], []
    for it in legacy_items:
        best = it["candidates"][0]
        p = parse_date_text(best["text"])
        if p is not None:
            legacy_dates.append({"text": best["text"], "parsed": list(p), "box": list(row_extent(it))})
            continue
        c = parse_count_text(best["text"])
        if c is not None:
            legacy_counts.append({"text": best["text"], "parsed": c, "box": list(row_extent(it))})
    qualified, conflicts = [], []
    for row in complete_rows:
        ld = None
        for cand in legacy_dates:
            if list(cand["parsed"]) == row["identity_dates"]:
                ld = cand
                break
        other_dates = [c for c in legacy_dates
                       if c["box"][1] >= row["date_box"][1] - 2 and c["box"][1] <= row["count_box"][3] + 2
                       and list(c["parsed"]) != row["identity_dates"]]
        if other_dates:
            conflicts.append({
                "kind": "legacy_modern_date_disagreement",
                "modern": {"text": row["date_text"], "parsed": row["identity_dates"]},
                "legacy": [{"text": c["text"], "parsed": c["parsed"]} for c in other_dates],
                "detail": "legacy reads a different valid date inside the same metadata block",
            })
            continue
        if ld is None:
            continue
        lc = None
        for cand in legacy_counts:
            if cand["parsed"] == row["count"] and cand["box"][1] >= row["count_box"][1] - 4 \
                    and cand["box"][3] <= row["count_box"][3] + 4:
                lc = cand
                break
        other_counts = [c for c in legacy_counts
                        if c["box"][1] >= row["date_box"][1] - 2 and c["box"][3] <= row["count_box"][3] + 4
                        and c["parsed"] != row["count"]]
        if other_counts:
            conflicts.append({
                "kind": "legacy_modern_count_disagreement",
                "modern": {"text": row["count_text"], "parsed": row["count"]},
                "legacy": [{"text": c["text"], "parsed": c["parsed"]} for c in other_counts],
                "detail": "legacy reads a different valid count inside the same metadata block",
            })
            continue
        if lc is None:
            continue
        qualified.append({**row, "legacy_date_text": ld["text"], "legacy_count_text": lc["text"],
                          "legacy_date_box": ld["box"], "legacy_count_box": lc["box"]})
    return qualified, conflicts


# ---------------------------------------------------------------- movement / overlap


def ordered_ids(complete_rows):
    return [f"{r['identity_dates'][0]}_{r['identity_dates'][1]}_{r['count']}" for r in
            sorted(complete_rows, key=lambda r: (r["date_box"][1], r["date_box"][0]))]


def ordered_overlap(previous_ids, current_ids):
    limit = min(len(previous_ids), len(current_ids))
    matches = [k for k in range(1, limit + 1) if previous_ids[-k:] == current_ids[:k]]
    return {
        "previous_ordered_ids": list(previous_ids),
        "current_ordered_ids": list(current_ids),
        "matches": matches,
        "overlap": "PASS" if matches else "FAIL",
        "max_overlap": max(matches) if matches else 0,
    }


def movement_evidence(previous_qualified, current_qualified):
    """Joint D range and center deltas over all shared qualified identities.

    D is an OCR-box-supported displacement range, not a calibrated bound.
    """
    previous_by_id = {f"{r['identity_dates'][0]}_{r['identity_dates'][1]}_{r['count']}": r
                      for r in previous_qualified}
    current_by_id = {f"{r['identity_dates'][0]}_{r['identity_dates'][1]}_{r['count']}": r
                     for r in current_qualified}
    shared = [key for key in current_by_id if key in previous_by_id]
    shared.sort(key=lambda key: current_by_id[key]["date_box"][1])
    result = {
        "shared_identities": shared,
        "fields": {},
        "center_deltas": [],
        "horizontal_overlap": "UNKNOWN",
        "joint": None,
        "movement": "UNKNOWN",
    }
    if not shared:
        result["reason"] = "no shared qualified identity between frames"
        return result
    lows, highs = [], []
    all_upper_negative = True
    all_horizontal = True
    for key in shared:
        prev = previous_by_id[key]
        cur = current_by_id[key]
        for field, pkey, ckey in (("date", "date_box", "date_box"), ("count", "count_box", "count_box")):
            pb = prev[pkey]; cb = cur[ckey]
            d_low = cb[1] - pb[3]
            d_high = cb[3] - pb[1]
            lows.append(d_low); highs.append(d_high)
            if not d_high < 0:
                all_upper_negative = False
            x_low = max(pb[0], cb[0]); x_high = min(pb[2], cb[2])
            h_overlap = x_high - x_low
            if h_overlap <= 0:
                all_horizontal = False
            result["fields"].setdefault(field, []).append({
                "identity": key, "previous_box": list(pb), "current_box": list(cb),
                "D": [d_low, d_high],
                "center_delta": [round((cb[0] + cb[2]) / 2 - (pb[0] + pb[2]) / 2, 6),
                                 round((cb[1] + cb[3]) / 2 - (pb[1] + pb[3]) / 2, 6)],
                "horizontal_projection_overlap": h_overlap,
            })
            result["center_deltas"].append({
                "identity": key, "field": field,
                "center_delta": result["fields"][field][-1]["center_delta"],
                "previous_center": [round((pb[0] + pb[2]) / 2, 6), round((pb[1] + pb[3]) / 2, 6)],
                "current_center": [round((cb[0] + cb[2]) / 2, 6), round((cb[1] + cb[3]) / 2, 6)],
            })
    joint_low = max(lows); joint_high = min(highs)
    result["joint"] = [joint_low, joint_high]
    result["horizontal_overlap"] = "PASS" if all_horizontal else "FAIL"
    if all_upper_negative and joint_low <= joint_high and all_horizontal:
        result["movement"] = "YES"
        result["reason"] = "all fields every identity moved up; joint D non-empty; x overlap positive"
    else:
        result["movement"] = "NO"
        reasons = []
        if not all_upper_negative:
            reasons.append("some D.high >= 0")
        if joint_low > joint_high:
            reasons.append("joint D empty")
        if not all_horizontal:
            reasons.append("missing positive horizontal projection overlap")
        result["reason"] = "; ".join(reasons)
    return result


# ---------------------------------------------------------------- decision core


def decide_frame(binding, frame, previous_frame, modern_payload, legacy_payload,
                 current_rgba, previous_rgba, previous_metadata=None):
    """Pure decision core for one frame transition.

    binding:  frozen bootstrap binding (see candidate/README.md for the schema)
    frame:    current frame manifest (decoded RGBA + OCR artifacts)
    previous_frame: previous frame manifest, or None for the bootstrap frame
    previous_metadata: dict(complete_rows=..., qualified=..., ordered_ids=...) from
        the previous evaluation, used for movement and ordered overlap. For the
        bootstrap frame, pass the current frame's own metadata (self-overlap).
    """
    def _rect(obj, where):
        if isinstance(obj, dict):
            return rect_from_obj(obj, where)
        if isinstance(obj, (list, tuple)) and len(obj) == 4:
            return tuple(int(v) for v in obj)
        fail("RECT_INVALID", where)

    image_rect = (0, 0, binding["width"], binding["height"])
    viewport = _rect(binding["list_viewport"], "list_viewport")
    guard_rect = _rect(binding["text_slot_guard"], "text_slot_guard")
    exclusions = [_rect(e, "exclusion") for e in binding.get("exclusions", [])]
    indicator_spec = dict(binding["indicator"])
    decision = {}

    # --- binding validity -------------------------------------------------
    checks = {
        "mode_match": frame["mode"] == binding["mode"],
        "run_id_match": frame["run_id"] == binding["run_id"],
        "observation_match": frame["observation_id"] == binding["observation_id"],
        "width_match": frame["width"] == binding["width"],
        "height_match": frame["height"] == binding["height"],
        "rgba_source_sha_match": frame["rgba"]["source_sha256"] == frame["source_artifact_sha256"],
    }
    binding_status = "VALID"
    for key, ok in checks.items():
        if not ok:
            binding_status = "INVALID"
    decision["binding_validity"] = {
        "status": binding_status,
        "checks": checks,
        "binding_run_id": binding["run_id"],
        "frame_run_id": frame["run_id"],
    }
    if frame["mode"] == "replay":
        decision["binding_validity"]["note"] = (
            "replay-only diagnostic binding; never reusable as live binding")

    # --- continuity -------------------------------------------------------
    continuity = {"status": "UNKNOWN", "guard": None, "previous_frame_id": None}
    if previous_frame is None:
        continuity["status"] = "BOOTSTRAP"
        continuity["note"] = "bootstrap frame; no previous frame to compare"
    else:
        prev_checks = {
            "previous_frame_id_match": previous_frame["frame_id"] == frame["previous_frame_id"],
            "previous_run_id_match": previous_frame["run_id"] == frame["run_id"],
            "previous_observation_match": previous_frame["observation_id"] == frame["observation_id"],
            "previous_width_match": previous_frame["width"] == frame["width"],
            "previous_height_match": previous_frame["height"] == frame["height"],
        }
        continuity["previous_frame_id"] = previous_frame["frame_id"]
        continuity["previous_checks"] = prev_checks
        guard = pixel_guard(current_rgba, frame["width"], previous_rgba, previous_frame["width"],
                            guard_rect, exclusions, image_rect)
        continuity["guard"] = guard
        if not all(prev_checks.values()):
            continuity["status"] = "CONFLICT"
            continuity["reason"] = "previous frame identity/dimensions do not match"
        elif guard["status"] != "PASS":
            continuity["status"] = guard["status"]
            continuity["reason"] = guard["reason"]
        else:
            continuity["status"] = "PASS"
            continuity["reason"] = "all identity checks and full-slot guard pass"
    decision["continuity"] = continuity

    # --- indicator --------------------------------------------------------
    decision["selected_indicator"] = indicator_check(current_rgba, frame["width"],
                                                     indicator_spec, image_rect)

    # --- OCR artifacts / identity ----------------------------------------
    modern_items, modern_completeness = normalize_ocr_items(modern_payload, frame["modern_path"])
    legacy_items, legacy_completeness = normalize_ocr_items(legacy_payload, frame["legacy_path"])
    decision["raw_ocr_artifacts"] = {
        "modern_path": frame["modern_path"],
        "modern_sha256": frame.get("modern_sha256"),
        "modern_completeness": modern_completeness,
        "legacy_path": frame["legacy_path"],
        "legacy_sha256": frame.get("legacy_sha256"),
        "legacy_completeness": legacy_completeness,
        "modern_item_count": len(modern_items),
        "legacy_item_count": len(legacy_items),
        "confidenceCalibration": "UNKNOWN",
        "apis_independent": False,
        "text_replacements_applied": 0,
        "confidence_threshold_applied": None,
    }
    date_rows, partial_rows, identity_conflicts = classify_date_items(modern_items, image_rect, viewport)
    date_indices = {r["index"] for r in date_rows}
    count_items, noise_items = classify_count_items(modern_items, date_indices, image_rect, viewport)
    complete_rows, pair_partials, ambiguous, pair_conflicts = pair_rows(date_rows, count_items, noise_items)

    # same-date drift / duplicate / non-adjacent reappearance checks
    seen_dates = {}
    for row in complete_rows:
        key = tuple(row["identity_dates"])
        if key in seen_dates and seen_dates[key] != row["count"]:
            pair_conflicts.append({
                "kind": "same_date_count_drift", "identity_dates": list(key),
                "counts": [seen_dates[key], row["count"]],
                "detail": "same date visible twice with different counts",
            })
        seen_dates[key] = row["count"]
    identity_keys = [f"{r['identity_dates'][0]}_{r['identity_dates'][1]}_{r['count']}" for r in complete_rows]
    if len(set(identity_keys)) != len(identity_keys):
        pair_conflicts.append({
            "kind": "duplicate_identity", "identities": identity_keys,
            "detail": "duplicate complete identity in one frame",
        })

    qualified, legacy_conflicts = qualified_overlap_rows(complete_rows, modern_items, legacy_items)
    conflicts = identity_conflicts + pair_conflicts + legacy_conflicts

    if conflicts:
        identity_status = "IDENTITY_CONFLICT"
    elif complete_rows:
        identity_status = "COMPLETE"
    elif partial_rows:
        identity_status = "PARTIAL"
    else:
        identity_status = "NONE"
    if not qualified:
        identity_status = identity_status if identity_status == "IDENTITY_CONFLICT" else "UNCONFIRMED"

    decision["identity_status"] = identity_status
    decision["complete_rows"] = complete_rows
    decision["partial_rows"] = partial_rows
    decision["ambiguous"] = ambiguous
    decision["conflicts"] = conflicts
    decision["qualified_overlap_rows"] = qualified
    decision["ordered_complete_ids"] = ordered_ids(complete_rows)
    decision["ordered_qualified_ids"] = ordered_ids(qualified)

    # --- movement + ordered overlap --------------------------------------
    if previous_metadata is None:
        previous_metadata = {
            "complete_rows": complete_rows, "qualified": qualified,
            "ordered_qualified_ids": decision["ordered_qualified_ids"],
        }
        decision["movement_reference"] = "self (bootstrap frame)"
    else:
        decision["movement_reference"] = "previous frame"
    movement = movement_evidence(previous_metadata["qualified"], qualified)
    decision["movement"] = movement["movement"]
    decision["movement_evidence"] = movement
    overlap = ordered_overlap(previous_metadata["ordered_qualified_ids"],
                              decision["ordered_qualified_ids"])
    decision["ordered_overlap"] = overlap

    # --- auxiliary uncertainty -------------------------------------------
    auxiliary = []
    tab_texts_ok = continuity["status"] in ("PASS", "BOOTSTRAP")
    indicator_ok = decision["selected_indicator"]["status"] == "PASS"
    if identity_status != "IDENTITY_CONFLICT" and tab_texts_ok and indicator_ok:
        for it in modern_items:
            core = strip_ws(it["candidates"][0]["text"])
            if core and any(ch in core for ch in ("簿", "溥", "薄")) and len(core) <= 4:
                if core not in ("相簿",):
                    auxiliary.append({
                        "kind": "tab_ocr_auxiliary_uncertainty",
                        "observed": it["candidates"][0]["text"],
                        "confidence": it["candidates"][0]["confidence"],
                        "scope": "tab label OCR only; never date/count; raw text preserved",
                    })
    decision["auxiliary_ocr_uncertainty"] = auxiliary

    # --- permissions ------------------------------------------------------
    effect_proven = movement["movement"] == "YES"
    capture_age = frame.get("capture_age_seconds")
    freshness_ok = isinstance(capture_age, (int, float)) and not isinstance(capture_age, bool) \
        and 0 <= capture_age <= 5
    decision["scroll_eligible"] = bool(
        frame["mode"] == "live"
        and binding_status == "VALID"
        and continuity["status"] == "PASS"
        and decision["selected_indicator"]["status"] == "PASS"
        and identity_status == "COMPLETE"
        and effect_proven
        and overlap["overlap"] == "PASS"
        and frame.get("safety_observation") == "OBSERVED"
        and freshness_ok
    )
    if frame["mode"] == "replay":
        decision["scroll_eligible"] = False
    decision["can_open_album"] = False
    decision["can_save_all"] = False
    decision["live_state_write_allowed"] = False
    decision["full_collection_coverage"] = FULL_COLLECTION_COVERAGE

    # --- chain + stop -----------------------------------------------------
    chain_extended = bool(
        frame["mode"] == "live"
        and binding_status == "VALID"
        and continuity["status"] == "PASS"
        and identity_status == "COMPLETE"
        and effect_proven
        and overlap["overlap"] == "PASS"
    )
    decision["chain_extended"] = chain_extended
    decision["chain_edge"] = {
        "from_frame": previous_frame["frame_id"] if previous_frame else None,
        "to_frame": frame["frame_id"],
        "overlap": overlap["overlap"],
        "max_overlap": overlap["max_overlap"],
        "movement": movement["movement"],
        "joint_D": movement["joint"],
    } if chain_extended else None

    stop_reasons = []
    if binding_status != "VALID":
        stop_reasons.append("binding invalid")
    if continuity["status"] not in ("PASS", "BOOTSTRAP"):
        stop_reasons.append(f"continuity {continuity['status']}")
    if decision["selected_indicator"]["status"] != "PASS":
        stop_reasons.append(f"indicator {decision['selected_indicator']['status']}")
    if identity_status == "IDENTITY_CONFLICT":
        stop_reasons.append("identity conflict")
    elif identity_status in ("PARTIAL", "NONE", "UNCONFIRMED"):
        stop_reasons.append(f"identity {identity_status}")
    if movement["movement"] != "YES" and previous_frame is not None:
        stop_reasons.append(f"movement {movement['movement']}")
    if frame["mode"] == "live" and not freshness_ok:
        stop_reasons.append("capture age unknown or over 5s")
    if previous_frame is not None and overlap["overlap"] != "PASS":
        stop_reasons.append("ordered overlap gap")
    decision["stop_reason"] = "; ".join(stop_reasons) if stop_reasons else None

    # --- facts that were not obtained ------------------------------------
    decision["facts_not_obtained"] = []
    if frame["mode"] == "replay":
        decision["safety_observation"] = "UNKNOWN"
        decision["facts_not_obtained"].append(
            "live runtime provenance, capture timestamps and safety observation are not available in replay")
    else:
        decision["safety_observation"] = frame.get("safety_observation", "UNKNOWN")
    if legacy_completeness == "UNKNOWN":
        decision["facts_not_obtained"].append(
            "legacy candidate completeness UNKNOWN (single stored candidate; not fabricated)")
    decision["mode"] = frame["mode"]
    decision["frame_id"] = frame["frame_id"]
    decision["source_artifact_sha256"] = frame["source_artifact_sha256"]
    decision["decoded_rgba_sha256"] = frame.get("rgba", {}).get("decoded_rgba_sha256")
    decision["candidate_hash"] = binding.get("candidate_hash")
    decision["profile_hashes"] = binding.get("profile_hashes")
    decision["decoder_hash"] = binding.get("decoder_hash")
    decision["binding_hash"] = binding.get("binding_hash")
    decision["format"] = FORMAT
    return decision


# ---------------------------------------------------------------- evaluate CLI


def load_frame_manifest(path):
    require_regular_file(path)
    return read_json(path)


def cmd_evaluate(args):
    binding = read_json(require_regular_file(args.binding))
    frame = load_frame_manifest(args.frame_manifest)
    modern_payload = read_json(require_regular_file(args.modern))
    legacy_payload = read_json(require_regular_file(args.legacy))
    if args.previous in (None, "", "NONE", "none"):
        previous_frame = None
        previous_rgba = None
        previous_metadata = None
    else:
        previous_frame = load_frame_manifest(args.previous)
        # previous frame manifest points at its own decoded RGBA
        previous_width = previous_frame["width"]
        previous_height = previous_frame["height"]
        previous_rgba = load_rgba(previous_frame["rgba"]["path"], previous_width, previous_height)
        if sha256_file(previous_frame["rgba"]["path"]) != previous_frame["rgba"]["decoded_rgba_sha256"]:
            fail("PREVIOUS_RGBA_HASH_MISMATCH", previous_frame["rgba"]["path"])
        previous_metadata = previous_frame.get("metadata")
    if frame["mode"] not in ("replay", "live"):
        fail("MODE_INVALID", frame["mode"])
    rgba = load_rgba(frame["rgba"]["path"], frame["width"], frame["height"])
    if sha256_file(frame["rgba"]["path"]) != frame["rgba"]["decoded_rgba_sha256"]:
        fail("RGBA_HASH_MISMATCH", frame["rgba"]["path"])
    frame["modern_path"] = os.path.abspath(args.modern)
    frame["legacy_path"] = os.path.abspath(args.legacy)
    frame["modern_sha256"] = sha256_file(args.modern)
    frame["legacy_sha256"] = sha256_file(args.legacy)
    decision = decide_frame(binding, frame, previous_frame, modern_payload, legacy_payload,
                            rgba, previous_rgba, previous_metadata)
    create_new_directory(args.out)
    write_json_new(os.path.join(args.out, "decision.json"), decision)
    print(json.dumps({
        "out": args.out,
        "frame_id": decision["frame_id"],
        "binding_validity": decision["binding_validity"]["status"],
        "continuity": decision["continuity"]["status"],
        "selected_indicator": decision["selected_indicator"]["status"],
        "identity_status": decision["identity_status"],
        "movement": decision["movement"],
        "ordered_overlap": decision["ordered_overlap"]["overlap"],
        "scroll_eligible": decision["scroll_eligible"],
    }, ensure_ascii=False, sort_keys=True))


# ---------------------------------------------------------------- prepare-replay


REPLAY_COPIES = [
    "scan-000.png", "scan-000.scale2.png", "scan-000.ocr.json", "scan-000.modern_ocr.json",
    "scan-000.transform.json", "scan-000.ax.txt",
    "scan-001.png", "scan-001.scale2.png", "scan-001.ocr.json", "scan-001.modern_ocr.json",
    "scan-001.transform.json", "scan-001.ax.txt",
    "scan-002.png", "scan-002.scale2.png", "scan-002.ocr.json", "scan-002.modern_ocr.json",
    "scan-002.transform.json", "scan-002.ax.txt",
    "scan-003.png", "scan-003.scale2.png", "scan-003.ocr.json", "scan-003.modern_ocr.json",
    "scan-003.transform.json", "scan-003.ax.txt",
    "step-001.pre.json", "step-001.action.json",
    "step-002.pre.json", "step-002.action.json",
    "step-003.pre.json", "step-003.action.json",
    "scan-000.agreement.json", "scan-001.agreement.json", "scan-002.agreement.json",
    "scan-003.failure.json",
    "baseline.json", "preservation.json", "report.md", "implementer.result.json",
    "plan.md", "plan-contract-02.json", "handoff-02.json",
    "initial.png", "frame-000.png",
]

CONTENT_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
}


def sniff_image_format(path):
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    return "UNKNOWN"


def cmd_prepare_replay(args):
    src_root = os.path.abspath(args.source)
    if not os.path.isdir(src_root):
        fail("SOURCE_TASK_MISSING", src_root)
    out = args.out
    create_new_directory(out)
    records = []
    for name in REPLAY_COPIES:
        src = os.path.join(src_root, name)
        require_regular_file(src)
        dst = os.path.join(out, name)
        write_new_file(dst, open(src, "rb").read())
        src_sha = sha256_file(src)
        copy_sha = sha256_file(dst)
        if src_sha != copy_sha:
            fail("COPY_HASH_MISMATCH", name)
        ext = os.path.splitext(name)[1].lower()
        content_format = CONTENT_FORMATS.get(ext, "TEXT")
        if ext == ".png":
            content_format = sniff_image_format(dst)
        records.append({
            "source_path": src,
            "copy_path": os.path.abspath(dst),
            "bytes": os.path.getsize(dst),
            "source_sha256": src_sha,
            "copy_sha256": copy_sha,
            "content_format": content_format,
        })
    manifest = {
        "format": "local-replay-manifest-1",
        "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
        "source_root": src_root,
        "copy_root": os.path.abspath(out),
        "records": records,
        "immutable_note": "Copies are byte-exact and must never be overwritten; reruns need a new directory.",
    }
    write_json_new(os.path.join(out, "manifest.json"), manifest)
    print(json.dumps({"out": out, "records": len(records)}))


# ---------------------------------------------------------------- verify-packet


def cmd_verify_packet(args):
    root = os.path.abspath(args.packet_root)
    manifest_path = os.path.join(root, "source-manifest.json")
    require_regular_file(manifest_path)
    manifest = read_json(manifest_path)
    results = []
    required_failed = []
    for rec in manifest["records"]:
        # manifest paths are repository-relative
        path = rec["path"] if os.path.isabs(rec["path"]) else os.path.abspath(rec["path"])
        exists = os.path.isfile(path)
        actual_sha = sha256_file(path) if exists else None
        actual_bytes = os.path.getsize(path) if exists else None
        ok = exists and actual_sha == rec["sha256"] and actual_bytes == rec["bytes"]
        results.append({
            "path": rec["path"], "verification": rec["verification"],
            "exists": exists, "expected_sha256": rec["sha256"], "actual_sha256": actual_sha,
            "expected_bytes": rec["bytes"], "actual_bytes": actual_bytes,
            "match": ok,
        })
        if rec["verification"] == "REQUIRED_CURRENT_HASH" and not ok:
            required_failed.append(rec["path"])

    # contract <-> handoff byte equality
    contract_equals_handoff = None
    try:
        contract_equals_handoff = sha256_file(os.path.join(root, "plan-contract.json")) == \
            sha256_file(os.path.join(root, "handoff.json"))
    except DiagError as exc:
        contract_equals_handoff = f"ERROR {exc.code}"

    spec = read_json(os.path.join(root, "diagnostic-spec.json"))
    handoff_sha = sha256_file(os.path.join(root, "handoff.md"))
    handoff_bytes = os.path.getsize(os.path.join(root, "handoff.md"))
    spec_binding_ok = (handoff_sha == spec["normative_procedure"]["sha256"]
                       and handoff_bytes == spec["normative_procedure"]["bytes"])
    plan_sha = sha256_file(os.path.join(root, "plan-as-submitted.md"))
    plan_binding_ok = plan_sha == spec["reviewed_plan"]["sha256"]
    review_sha = sha256_file(os.path.join(root, "plan-review-01.result.json"))
    review_binding_ok = review_sha == spec["review_result"]["sha256"]

    report = {
        "format": "local-packet-verification-1",
        "packet_root": root,
        "records": results,
        "records_checked": len(results),
        "required_current_mismatches": required_failed,
        "contract_equals_handoff_bytes": contract_equals_handoff,
        "spec_handoff_binding": spec_binding_ok,
        "spec_plan_binding": plan_binding_ok,
        "spec_review_binding": review_binding_ok,
        "verdict": "PASS" if (not required_failed and contract_equals_handoff is True
                              and spec_binding_ok and plan_binding_ok and review_binding_ok) else "FAIL",
        "note": "JSON parse + byte binding only; this is not controller schema VALID.",
    }
    if args.out:
        create_new_directory(args.out)
        write_json_new(os.path.join(args.out, "verify-packet.json"), report)
        print(json.dumps({"out": args.out, "verdict": report["verdict"],
                          "records_checked": len(results)}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
    if report["verdict"] != "PASS":
        sys.exit(2)


# ---------------------------------------------------------------- CLI


def build_parser():
    parser = argparse.ArgumentParser(prog=PROG, description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare-replay")
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_prepare_replay)

    p = sub.add_parser("verify-packet")
    p.add_argument("--packet-root", required=True)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_verify_packet)

    p = sub.add_parser("evaluate")
    p.add_argument("--mode", required=True, choices=["replay", "live"])
    p.add_argument("--binding", required=True)
    p.add_argument("--frame-manifest", required=True)
    p.add_argument("--modern", required=True)
    p.add_argument("--legacy", required=True)
    p.add_argument("--previous", default="NONE")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_evaluate)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except DiagError as exc:
        print(f"ERROR {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
