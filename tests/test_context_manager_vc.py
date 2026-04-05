from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from context_manager import select_clean_pages  # noqa: E402
from page_parser import extract_page_slices  # noqa: E402


class VisualCompositionSliceTests(unittest.TestCase):
    """Test that visual composition can be sliced the same way as clean pages."""

    def test_vc_slices_by_page_number(self) -> None:
        vc_text = (
            "# Visual Composition\n\n"
            "## 第 1 页\n\n视觉主角：gauge_chart\n\n---\n\n"
            "## 第 2 页\n\n视觉主角：comparison_table\n\n---\n\n"
            "## 第 3 页\n\n视觉主角：circular_loop_diagram\n"
        )
        slices = extract_page_slices(vc_text)
        self.assertIn(1, slices)
        self.assertIn(2, slices)
        self.assertIn(3, slices)
        self.assertIn("gauge_chart", slices[1])
        self.assertIn("comparison_table", slices[2])
        self.assertIn("circular_loop_diagram", slices[3])

    def test_select_clean_pages_works_for_vc(self) -> None:
        vc_text = (
            "## 第 1 页\n视觉主角：metric_card\n\n"
            "## 第 2 页\n视觉主角：icon_flow_chain\n"
        )
        selected, warnings = select_clean_pages(vc_text, ["slide_02"], False)
        self.assertIn("slide_02", selected)
        self.assertIn("icon_flow_chain", selected["slide_02"])
        self.assertNotIn("slide_01", selected)


if __name__ == "__main__":
    unittest.main()
