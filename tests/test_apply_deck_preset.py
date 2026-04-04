from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from apply_deck_preset import apply_to_state, resolve_hero_pages  # noqa: E402


class ApplyDeckPresetTests(unittest.TestCase):
    def test_resolve_hero_pages_uses_relative_locators(self) -> None:
        state = {"pages": [{"page_id": f"slide_{i:02d}"} for i in range(1, 13)]}
        preset = {
            "hero_pages": [
                {"locator": "first", "role": "hero_cover"},
                {"locator": "ratio:0.50", "role": "hero_system"},
                {"locator": "last", "role": "hero_cta"},
            ]
        }
        hero_pages = resolve_hero_pages(state, preset)
        self.assertEqual(hero_pages[0]["page_id"], "slide_01")
        self.assertEqual(hero_pages[1]["page_id"], "slide_06")
        self.assertEqual(hero_pages[2]["page_id"], "slide_12")

    def test_apply_to_state_returns_none_if_state_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = apply_to_state(Path(tmp), {"default_output_mode": "pptx"}, [])
            self.assertIsNone(result)

    def test_apply_to_state_updates_output_mode_and_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            state_path = project_dir / "slide_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "output_mode": "pptx+html",
                        "pages": [{"page_id": "slide_01", "role": "unassigned"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            updated = apply_to_state(
                project_dir,
                {"default_output_mode": "html"},
                [{"page_id": "slide_01", "role": "hero_cover"}],
            )
            self.assertIsNotNone(updated)
            assert updated is not None
            self.assertEqual(updated["output_mode"], "html")
            self.assertEqual(updated["pages"][0]["role"], "hero_cover")


if __name__ == "__main__":
    unittest.main()
