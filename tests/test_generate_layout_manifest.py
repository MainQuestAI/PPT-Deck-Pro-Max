from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_layout_manifest import build_manifest, parse_skeletons  # noqa: E402


class GenerateLayoutManifestTests(unittest.TestCase):
    def test_parse_skeletons_reads_page_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deck_page_skeletons.md"
            path.write_text(
                "# Skeletons\n\n## 第 1 页\n- archetype: hero_cover\n- 预期占比: 0.38\n",
                encoding="utf-8",
            )
            parsed = parse_skeletons(path)
            self.assertEqual(parsed[1]["archetype"], "hero_cover")
            self.assertEqual(parsed[1]["预期占比"], "0.38")

    def test_build_manifest_generates_page_entries_from_state(self) -> None:
        state = {
            "pages": [
                {"page_id": "slide_01", "role": "hero_cover"},
                {"page_id": "slide_02", "role": "hero_cta"},
            ]
        }
        manifest = build_manifest(state, {1: {"archetype": "hero_cover", "预期占比": "0.38"}}, None)
        self.assertEqual(len(manifest["pages"]), 2)
        self.assertEqual(manifest["pages"][0]["archetype"], "hero_cover")
        self.assertAlmostEqual(manifest["pages"][0]["occupancy"]["ratio"], 0.38)
        self.assertEqual(manifest["pages"][1]["archetype"], "cta_board")


if __name__ == "__main__":
    unittest.main()
