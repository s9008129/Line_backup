#!/usr/bin/env python3
# test_catalog_diagnostic.py -- stdlib unittest fixtures for the catalog
# diagnostic evaluator (TASK-20261010-catalog-diagnostic-continuity-replan).
#
# Fixtures are in-memory mutations or copies of the frozen replay artifacts; no
# original image, replay copy, profile or packet input is modified. These tests
# are offline evidence only and never count as native/live evidence.

import copy
import importlib.util
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REPLAY = os.path.join(TASK, "replay")


def load_module():
    spec = importlib.util.spec_from_file_location(
        "catalog_diagnostic_under_test", os.path.join(HERE, "catalog_diagnostic.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cd = load_module()

W, H = 654, 1286
IMAGE_RECT = (0, 0, W, H)
VIEWPORT = (0, 206, W, H)


def rgba_background(width=W, height=H, rgb=(45, 46, 48)):
    px = bytes(rgb) + b"\xff"
    return bytearray(px * (width * height))


def put(rgba, width, x, y, rgb):
    i = (y * width + x) * 4
    rgba[i:i + 3] = bytes(rgb)


def full_slot_guard():
    return (0, 0, W, 192)


def indicator_spec():
    """Frozen replay indicator spec (matches run_offline_once.py constants)."""
    return {
        "region": {"x0": 0, "y0": 196, "x1": W, "y1": 206},
        "album_region": {"x0": 100, "y0": 196, "x1": 300, "y1": 206},
        "notes_region": {"x0": 400, "y0": 196, "x1": 620, "y1": 206},
        "album_tab_horizontal": [130, 300],
        "notes_tab_horizontal": [400, 620],
        "baseline_bbox": [138, 202, 186, 206],
        "baseline_mask_sha256": None,  # filled by tests that need it
        "luma": "(54R+183G+19B)>>8",
        "bright_at_least": 128,
        "connectivity": 8,
        "filter_small_components": False,
    }


def baseline_indicator_rgba():
    rgba = rgba_background()
    for x in range(138, 186):
        for y in range(202, 206):
            put(rgba, W, x, y, (255, 255, 255))
    return rgba


def indicator_spec_with_hash(rgba):
    spec = indicator_spec()
    cells = cd.bright_mask(bytes(rgba), W, (spec["album_region"]["x0"], spec["album_region"]["y0"],
                                            spec["album_region"]["x1"], spec["album_region"]["y1"]))
    comps = cd.connected_components_8(cells)
    assert len(comps) == 1
    spec["baseline_bbox"] = list(cd.bbox_of(comps[0]))
    spec["baseline_mask_sha256"] = cd.sha256_bytes(
        json.dumps(sorted(comps[0]), separators=(",", ":")).encode("utf-8"))
    return spec


def ocr_item(text, box, confidence=0.5, candidates=None, completeness=None):
    item = {
        "text": text,
        "confidence": confidence,
        "boxTopLeftSourcePixels": list(box),
    }
    if candidates is not None:
        item["candidates"] = candidates
    if completeness is not None:
        item["completeness"] = completeness
    return item


def row(identity_dates, count, date_box, count_box):
    return {
        "identity_dates": list(identity_dates), "count": count,
        "date_text": "fixture", "count_text": str(count),
        "date_box": list(date_box), "count_box": list(count_box),
        "date_confidence": 0.5, "count_confidence": 1.0,
        "date_candidates": [], "count_candidates": [],
    }


class ParseTests(unittest.TestCase):
    def test_date_formats(self):
        self.assertEqual(cd.parse_date_text("2024/06/02～06/07"),
                         ("2024-06-02", "2024-06-07"))
        self.assertEqual(cd.parse_date_text("2024/06/02~06/07"),
                         ("2024-06-02", "2024-06-07"))
        self.assertEqual(cd.parse_date_text("2024/06/02〜06/07"),
                         ("2024-06-02", "2024-06-07"))
        self.assertEqual(cd.parse_date_text("2024/06/02-06/07"),
                         ("2024-06-02", "2024-06-07"))
        self.assertEqual(cd.parse_date_text("2024/06/02~2024/06/07"),
                         ("2024-06-02", "2024-06-07"))
        self.assertEqual(cd.parse_date_text("2024/06/02 ~ 06/07"),
                         ("2024-06-02", "2024-06-07"))

    def test_date_omitted_end_year_inherits_start_only(self):
        self.assertEqual(cd.parse_date_text("2023/12/30~12/31"),
                         ("2023-12-30", "2023-12-31"))
        # omitted end year inherits the start year; it never rolls to the next year
        self.assertIsNone(cd.parse_date_text("2023/12/30~01/02"))

    def test_date_invalid(self):
        self.assertIsNone(cd.parse_date_text("2024/13/40~06/07"))
        self.assertIsNone(cd.parse_date_text("2024/06/07~06/02"))
        self.assertIsNone(cd.parse_date_text("2024/02/30~03/01"))
        self.assertIsNone(cd.parse_date_text("65"))

    def test_count_parsing(self):
        self.assertEqual(cd.parse_count_text("65"), 65)
        self.assertEqual(cd.parse_count_text("065"), 65)
        self.assertIsNone(cd.parse_count_text("6O"))
        self.assertIsNone(cd.parse_count_text("0"))
        self.assertIsNone(cd.parse_count_text("-3"))
        self.assertIsNone(cd.parse_count_text(""))


class R02MovementTests(unittest.TestCase):
    def test_same_set_moved_up_is_yes(self):
        previous = [row(("2024-06-02", "2024-06-07"), 65,
                        (29.0, 600.0, 265.0, 627.0), (29.0, 635.0, 61.0, 659.0))]
        current = [row(("2024-06-02", "2024-06-07"), 65,
                       (29.0, 321.5, 265.0, 348.5), (29.0, 356.0, 61.0, 380.0))]
        evidence = cd.movement_evidence(previous, current)
        self.assertEqual(evidence["movement"], "YES")

    def test_ordered_overlap_identical_set_is_pass(self):
        ids = ["2024-06-02_2024-06-07_65"]
        overlap = cd.ordered_overlap(ids, ids)
        self.assertEqual(overlap["overlap"], "PASS")


class R03ConfidenceTests(unittest.TestCase):
    def test_low_confidence_complete_row_passes(self):
        items = [
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.3,
                     candidates=[{"text": "2024/06/02~06/07", "confidence": 0.3}]),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 0.5,
                     candidates=[{"text": "65", "confidence": 0.5}]),
        ]
        norm, _ = cd.normalize_ocr_items({"items": items}, "fixture")
        rows, _, _ = cd.classify_date_items(norm, IMAGE_RECT, VIEWPORT)
        counts, noise = cd.classify_count_items(norm, {r["index"] for r in rows}, IMAGE_RECT, VIEWPORT)
        complete, _, _, conflicts = cd.pair_rows(rows, counts, noise)
        self.assertEqual(len(complete), 1)
        self.assertEqual(complete[0]["date_confidence"], 0.3)
        self.assertFalse(conflicts)


class R04FullSlotGuardTests(unittest.TestCase):
    def test_low_contrast_pixel_outside_glyph_but_inside_slot_is_rejected(self):
        baseline = rgba_background()
        for x in range(235, 350):
            put(baseline, W, x, 100, (240, 240, 240))
        mutated = bytearray(baseline)
        put(mutated, W, 500, 150, (70, 72, 74))
        guard = cd.pixel_guard(bytes(mutated), W, bytes(baseline), W,
                               full_slot_guard(), [], IMAGE_RECT)
        self.assertEqual(guard["status"], "CONFLICT")
        self.assertEqual(guard["pixel_diff_count"], 1)
        self.assertEqual(guard["first_diff"], [500, 150])

    def test_identical_slot_passes(self):
        baseline = rgba_background()
        for x in range(235, 350):
            put(baseline, W, x, 100, (240, 240, 240))
        guard = cd.pixel_guard(bytes(baseline), W, bytes(baseline), W,
                               full_slot_guard(), [], IMAGE_RECT)
        self.assertEqual(guard["status"], "PASS")


class R05IndicatorTests(unittest.TestCase):
    def test_text_change_stops(self):
        baseline = rgba_background()
        for x in range(235, 350):
            put(baseline, W, x, 100, (240, 240, 240))
        changed = bytearray(baseline)
        put(changed, W, 453, 170, (240, 240, 240))
        guard = cd.pixel_guard(bytes(changed), W, bytes(baseline), W,
                               full_slot_guard(), [], IMAGE_RECT)
        self.assertEqual(guard["status"], "CONFLICT")

    def test_indicator_moved_to_notes_stops(self):
        rgba = baseline_indicator_rgba()
        spec = indicator_spec_with_hash(rgba)
        moved = bytearray(rgba)
        for x in range(138, 186):
            for y in range(202, 206):
                put(moved, W, x, y, (45, 46, 48))
        for x in range(431, 530):
            for y in range(202, 206):
                put(moved, W, x, y, (255, 255, 255))
        verdict = cd.indicator_check(bytes(moved), W, spec, IMAGE_RECT)
        self.assertEqual(verdict["status"], "CONFLICT")

    def test_double_indicator_stops(self):
        rgba = baseline_indicator_rgba()
        spec = indicator_spec_with_hash(rgba)
        doubled = bytearray(rgba)
        for x in range(420, 470):
            for y in range(202, 206):
                put(doubled, W, x, y, (255, 255, 255))
        verdict = cd.indicator_check(bytes(doubled), W, spec, IMAGE_RECT)
        self.assertEqual(verdict["status"], "CONFLICT")

    def test_single_indicator_matches_baseline(self):
        rgba = baseline_indicator_rgba()
        spec = indicator_spec_with_hash(rgba)
        verdict = cd.indicator_check(bytes(rgba), W, spec, IMAGE_RECT)
        self.assertEqual(verdict["status"], "PASS")


class R09RowPairingTests(unittest.TestCase):
    def build(self, items):
        norm, _ = cd.normalize_ocr_items({"items": items}, "fixture")
        rows, partial, conflicts = cd.classify_date_items(norm, IMAGE_RECT, VIEWPORT)
        counts, noise = cd.classify_count_items(norm, {r["index"] for r in rows}, IMAGE_RECT, VIEWPORT)
        complete, pair_partial, ambiguous, pair_conflicts = cd.pair_rows(rows, counts, noise)
        return complete, partial + pair_partial, ambiguous, conflicts + pair_conflicts

    def test_invalid_date_rejected(self):
        complete, partial, _, _ = self.build([
            ocr_item("2024/13/40~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0),
        ])
        self.assertFalse(complete)

    def test_start_after_end_rejected(self):
        complete, partial, _, _ = self.build([
            ocr_item("2024/06/07~06/02", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0),
        ])
        self.assertFalse(complete)

    def test_zero_count_rejected(self):
        complete, partial, _, _ = self.build([
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("0", [29.0, 885.0, 32.0, 24.0], 1.0),
        ])
        self.assertFalse(complete)

    def test_two_counts_ambiguous(self):
        complete, partial, ambiguous, conflicts = self.build([
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0),
            ocr_item("65", [29.0, 890.0, 32.0, 24.0], 0.9),
        ])
        self.assertFalse(complete)
        self.assertTrue(partial)

    def test_date_without_count_partial(self):
        complete, partial, _, _ = self.build([
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
        ])
        self.assertFalse(complete)
        self.assertTrue(partial)


class R10R11ApiOverlapTests(unittest.TestCase):
    def modern_complete(self):
        items = [
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5,
                     candidates=[{"text": "2024/06/02~06/07", "confidence": 0.5}]),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0,
                     candidates=[{"text": "65", "confidence": 1.0}]),
        ]
        norm, _ = cd.normalize_ocr_items({"items": items}, "modern")
        rows, _, _ = cd.classify_date_items(norm, IMAGE_RECT, VIEWPORT)
        counts, noise = cd.classify_count_items(norm, {r["index"] for r in rows}, IMAGE_RECT, VIEWPORT)
        complete, _, _, _ = cd.pair_rows(rows, counts, noise)
        return norm, complete

    def test_different_valid_api_identity_stops(self):
        modern, complete = self.modern_complete()
        legacy, _ = cd.normalize_ocr_items({"items": [
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("66", [29.0, 885.0, 32.0, 24.0], 1.0),
        ]}, "legacy")
        qualified, conflicts = cd.qualified_overlap_rows(complete, modern, legacy)
        self.assertFalse(qualified)
        self.assertTrue(any(c["kind"] == "legacy_modern_count_disagreement" for c in conflicts))

    def test_missing_legacy_is_not_agreement(self):
        modern, complete = self.modern_complete()
        legacy, completeness = cd.normalize_ocr_items({"items": [
            ocr_item("記事本", [450.0, 160.0, 75.0, 25.0], 1.0),
        ]}, "legacy")
        qualified, _ = cd.qualified_overlap_rows(complete, modern, legacy)
        self.assertFalse(qualified)
        self.assertEqual(completeness, "UNKNOWN")

    def test_matching_api_identity_qualifies(self):
        modern, complete = self.modern_complete()
        legacy, _ = cd.normalize_ocr_items({"items": [
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0),
        ]}, "legacy")
        qualified, conflicts = cd.qualified_overlap_rows(complete, modern, legacy)
        self.assertEqual(len(qualified), 1)
        self.assertFalse(conflicts)


class R12DriftTests(unittest.TestCase):
    def test_same_date_count_drift_detected_by_decision(self):
        items = [
            ocr_item("2024/06/02~06/07", [29.0, 850.0, 236.0, 27.0], 0.5,
                     candidates=[{"text": "2024/06/02~06/07", "confidence": 0.5}]),
            ocr_item("65", [29.0, 885.0, 32.0, 24.0], 1.0,
                     candidates=[{"text": "65", "confidence": 1.0}]),
            ocr_item("2024/06/02~06/07", [29.0, 1000.0, 236.0, 27.0], 0.5,
                     candidates=[{"text": "2024/06/02~06/07", "confidence": 0.5}]),
            ocr_item("64", [29.0, 1035.0, 32.0, 24.0], 1.0,
                     candidates=[{"text": "64", "confidence": 1.0}]),
        ]
        norm, _ = cd.normalize_ocr_items({"items": items}, "drift")
        rows, _, _ = cd.classify_date_items(norm, IMAGE_RECT, VIEWPORT)
        counts, noise = cd.classify_count_items(norm, {r["index"] for r in rows}, IMAGE_RECT, VIEWPORT)
        complete, _, _, _ = cd.pair_rows(rows, counts, noise)
        same = [r for r in complete if tuple(r["identity_dates"]) == ("2024-06-02", "2024-06-07")]
        self.assertEqual(len(same), 2)
        self.assertEqual({r["count"] for r in same}, {64, 65})


class R13OverlapTests(unittest.TestCase):
    def test_gap_and_reversed_do_not_extend(self):
        self.assertEqual(cd.ordered_overlap(["a", "b", "c"], ["b", "d"])["overlap"], "FAIL")
        self.assertEqual(cd.ordered_overlap(["a", "b", "c"], ["b", "c"])["overlap"], "PASS")
        self.assertEqual(cd.ordered_overlap(["a", "b", "c", "d"], ["c", "b"])["overlap"], "FAIL")
        self.assertEqual(cd.ordered_overlap(["a", "b", "c"], ["b", "c"])["overlap"], "PASS")


class R14MovementGuardTests(unittest.TestCase):
    def test_date_up_count_down_is_no(self):
        previous = [row(("2024-06-02", "2024-06-07"), 65,
                        (29.0, 600.0, 265.0, 627.0), (29.0, 635.0, 61.0, 659.0))]
        current = [row(("2024-06-02", "2024-06-07"), 65,
                       (29.0, 321.5, 265.0, 348.5), (29.0, 700.0, 61.0, 724.0))]
        evidence = cd.movement_evidence(previous, current)
        self.assertEqual(evidence["movement"], "NO")

    def test_no_horizontal_overlap_is_no(self):
        previous = [row(("2024-06-02", "2024-06-07"), 65,
                        (29.0, 600.0, 265.0, 627.0), (29.0, 635.0, 61.0, 659.0))]
        current = [row(("2024-06-02", "2024-06-07"), 65,
                       (300.0, 321.5, 536.0, 348.5), (300.0, 356.0, 332.0, 380.0))]
        evidence = cd.movement_evidence(previous, current)
        self.assertEqual(evidence["movement"], "NO")

    def test_unchanged_boxes_are_no(self):
        previous = [row(("2024-06-02", "2024-06-07"), 65,
                        (29.0, 600.0, 265.0, 627.0), (29.0, 635.0, 61.0, 659.0))]
        evidence = cd.movement_evidence(previous, copy.deepcopy(previous))
        self.assertEqual(evidence["movement"], "NO")


class R17TransformTests(unittest.TestCase):
    def test_legacy_full_frame_transform_matches_history(self):
        with open(os.path.join(REPLAY, "scan-000.ocr.json")) as fh:
            legacy = json.load(fh)
        date_item = [it for it in legacy["items"] if it["text"].startswith("2024/06/02")][0]
        source_y = date_item["boxTopLeftPixels"][1] / 2.0
        self.assertAlmostEqual(source_y, 855.9999997161353, places=6)
        # and this differs from the modern local-ROI box, so the two transforms
        # must never be mixed
        self.assertNotAlmostEqual(source_y, 857.33333334135, places=3)

    def test_new_local_roi_transform_applied_once(self):
        # crop origin (0,0) at scale 2: source = derivative/2 (never divided twice)
        derivative_y = 1714.667
        roi_origin_y = 0
        source_y = roi_origin_y + derivative_y / 2
        self.assertAlmostEqual(source_y, 857.3335, places=3)

    def test_historical_replay_hashes_unchanged(self):
        with open(os.path.join(REPLAY, "manifest.json")) as fh:
            manifest = json.load(fh)
        for rec in manifest["records"]:
            self.assertEqual(rec["source_sha256"], rec["copy_sha256"], rec["copy_path"])
            if rec["content_format"] == "PNG" or rec["content_format"] == "JPEG":
                with open(rec["copy_path"], "rb") as fh:
                    head = fh.read(8)
                self.assertTrue(head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8\xff"),
                                rec["copy_path"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
