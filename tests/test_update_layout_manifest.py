from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from update_layout_manifest import upsert_page  # noqa: E402


class UpdateLayoutManifestTests(unittest.TestCase):
    def test_upsert_page_inserts_and_updates_same_page(self) -> None:
        manifest = {"pages": []}
        manifest = upsert_page(manifest, {"page_id": "slide_01", "archetype": "hero_cover"})
        self.assertEqual(len(manifest["pages"]), 1)
        manifest = upsert_page(manifest, {"page_id": "slide_01", "main_group": {"center_x": 0.48}})
        self.assertEqual(len(manifest["pages"]), 1)
        self.assertEqual(manifest["pages"][0]["main_group"]["center_x"], 0.48)


if __name__ == "__main__":
    unittest.main()
