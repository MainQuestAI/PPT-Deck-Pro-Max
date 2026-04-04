from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from check_layout_stability import detect_layout_stability_issues  # noqa: E402


class LayoutStabilityTests(unittest.TestCase):
    def test_detects_center_offset_and_detached_connector(self) -> None:
        manifest = {
            "pages": [
                {
                    "page_id": "slide_01",
                    "main_group": {"center_x": 8.5, "expected_center_x": 6.6, "tolerance": 0.2},
                    "connectors": [
                        {
                            "label": "loop_1",
                            "start": {"x": 1.0, "y": 1.0},
                            "from_anchor": {"x": 1.2, "y": 1.0},
                            "end": {"x": 4.0, "y": 4.0},
                            "to_anchor": {"x": 4.0, "y": 4.3},
                            "tolerance": 0.05,
                        }
                    ],
                }
            ]
        }
        issues, meta = detect_layout_stability_issues({"pages": [{"page_id": "slide_01"}]}, manifest)
        self.assertTrue(meta["layout_manifest_present"])
        self.assertIn("slide_01", issues)
        self.assertTrue(any("layout_alignment" in item for item in issues["slide_01"]))
        self.assertTrue(any("geometry_broken" in item for item in issues["slide_01"]))

    def test_require_layout_manifest_raises_global_issue_when_missing(self) -> None:
        issues, meta = detect_layout_stability_issues({"pages": [{"page_id": "slide_01"}]}, None, True)
        self.assertFalse(meta["layout_manifest_present"])
        self.assertIn("__global__", issues)


if __name__ == "__main__":
    unittest.main()
