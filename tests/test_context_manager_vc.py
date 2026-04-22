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

    def test_context_files_expected_by_build_runtime_can_be_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "style_lock.json").write_text('{"style_id":"demo","visual_rules":{"text_in_image":"avoid"}}', encoding="utf-8")
            (root / "asset_manifest.json").write_text(
                '{"assets":[{"id":"a1","page_id":"slide_02","status":"approved","final_path":"assets/a1.png","source_mode":"generate"}]}',
                encoding="utf-8",
            )
            (root / "image_build_jobs.json").write_text(
                '{"initial_review_batch":"batch_01","batches":[{"batch_id":"batch_01","page_ids":["slide_02"],"status":"queued"}],"jobs":[{"job_id":"j1","page_id":"slide_02","batch_id":"batch_01","asset_id":"a1","status":"queued"}]}',
                encoding="utf-8",
            )
            self.assertTrue((root / "style_lock.json").exists())
            self.assertTrue((root / "asset_manifest.json").exists())
            self.assertTrue((root / "image_build_jobs.json").exists())


if __name__ == "__main__":
    unittest.main()
