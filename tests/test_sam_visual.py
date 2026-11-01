"""Unit tests for SAM 3.1 visual inspector."""
from __future__ import annotations

import unittest
from inneros_meta_guardian.sam_inspector import SAMInspector


class SAMInspectorTests(unittest.TestCase):
    def test_inspect_lab_core_switch(self):
        inspector = SAMInspector()
        result = inspector.inspect_lab_asset("lab_rack_switch_led")
        self.assertTrue(result["ok"])
        self.assertEqual("SIMULATED_FIXTURE", result["status"])
        self.assertEqual("meta-sam-3.1", result["model"])
        self.assertFalse(result["model_executed"])
        self.assertEqual("SIMULATED_FIXTURE", result["truth"])
        self.assertGreaterEqual(len(result["detected_objects"]), 2)
        for obj in result["detected_objects"]:
            self.assertIn("label", obj)
            self.assertIn("confidence", obj)
            self.assertIn("bbox", obj)
            self.assertGreater(obj["confidence"], 0.8)
            self.assertEqual("STATIC_EXAMPLE_NOT_MODEL", obj["confidence_source"])

    def test_inspect_optical_fiber_tray(self):
        inspector = SAMInspector()
        result = inspector.inspect_lab_asset("lab_optical_patch_panel")
        self.assertTrue(result["ok"])
        self.assertEqual("lab_hw_02_fiber_tray", result["asset_id"])
        self.assertIn("single_mode_patch_yellow", [o["label"] for o in result["detected_objects"]])


if __name__ == "__main__":
    unittest.main()
