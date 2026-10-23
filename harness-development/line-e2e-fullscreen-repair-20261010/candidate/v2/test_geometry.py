from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from geometry import compute


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"
CANDIDATE = ROOT / "candidate/v2"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = load(EVIDENCE / "e01-detail-menu-01.json")
        cls.ocr = load(EVIDENCE / "e01-detail-menu-01-v2-ocr-2x.json")
        cls.anchors = load(EVIDENCE / "e01-detail-menu-01-anchors.json")
        cls.profile = load(CANDIDATE / "profiles.json")

    def run_geometry(self, capture=None, ocr=None, anchors=None, profile=None, size=(654, 1286)):
        return compute(capture or self.capture, ocr or self.ocr, anchors or self.anchors,
                       profile or self.profile, 6743, 6778, size)

    def test_corrected_ocr_and_mapping_produce_safe_interior(self):
        result = self.run_geometry()
        point = result["derived_save_all_cua_screenshot_pixel"]
        self.assertAlmostEqual(point["x"], 610.0, places=3)
        self.assertAlmostEqual(point["y"], 271.5, places=1)
        self.assertLessEqual(result["maximum_anchor_residual_source_pixels"], 2.0)
        self.assertGreaterEqual(
            result["save_all_bracketing_rows"]["target_clearance_display_pixels"],
            result["save_all_bracketing_rows"]["required_clearance_display_pixels"],
        )
        self.assertTrue(result["pre_dispatch_ready"])

    def test_coordinate_scale_bug_regression(self):
        result = self.run_geometry()
        self.assertGreater(result["save_all_bracketing_rows"]["observed_centers_display_pixels"]["target"], 350)
        self.assertLess(result["save_all_bracketing_rows"]["observed_centers_display_pixels"]["target"], 410)

    def test_mismatched_image_hash_refuses_mapping(self):
        ocr = copy.deepcopy(self.ocr)
        ocr["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "same image hash"):
            self.run_geometry(ocr=ocr)

    def test_anchor_residual_over_two_pixels_refuses_mapping(self):
        anchors = copy.deepcopy(self.anchors)
        anchors["anchors"][0]["cua_bbox_pixels"][0] += 8
        with self.assertRaisesRegex(ValueError, "anchor residual"):
            self.run_geometry(anchors=anchors)

    def test_wrong_screenshot_dimensions_refuse_mapping(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            self.run_geometry(size=(327, 643))

    def test_undersized_popup_intersection_refuses_mapping(self):
        capture = copy.deepcopy(self.capture)
        popup = next(w for w in capture["sck_window_inventory"] if w["window_id"] == 6778)
        popup["frame_points"]["x"] = 680
        with self.assertRaisesRegex(ValueError, "intersection"):
            self.run_geometry(capture=capture)

    def test_uncertain_menu_order_refuses_mapping(self):
        ocr = copy.deepcopy(self.ocr)
        observations = ocr["results"][0]["observations"]
        save_all = next(o for o in observations if o["top_candidates"][0]["text"] == "儲存全部")
        save_all["source_bbox_pixels_top_left"]["y"] = 500
        with self.assertRaisesRegex(ValueError, "bracketed"):
            self.run_geometry(ocr=ocr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
