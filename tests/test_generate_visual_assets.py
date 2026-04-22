from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_visual_assets import assign_batches, build_prompt_payload, compute_content_hash  # noqa: E402
from init_slide_state import build_state  # noqa: E402


class GenerateVisualAssetsTests(unittest.TestCase):
    def test_assign_batches_prioritizes_first_three_key_pages(self) -> None:
        state = build_state("test", 5, "html")
        roles = ["hero_cover", "hero_problem", "hero_proof", "hero_system", "hero_value"]
        for page, role in zip(state["pages"], roles):
            page["role"] = role
        assets = [
            {"page_id": "slide_01"},
            {"page_id": "slide_03"},
            {"page_id": "slide_04"},
            {"page_id": "slide_05"},
        ]
        batches = assign_batches(assets, state, batch_size=3)
        self.assertEqual(batches["batch_01"], ["slide_01", "slide_03", "slide_04"])

    def test_content_hash_changes_when_page_content_changes(self) -> None:
        asset = {"id": "a1", "desc": "封面主视觉", "position": "right", "frame": "none", "aspect_ratio": "16:9"}
        style_lock = {"visual_rules": {"material_finish": "glass editorial"}}
        h1 = compute_content_hash(asset, "第一页内容", "视觉主角 A", style_lock)
        h2 = compute_content_hash(asset, "第一页内容变化", "视觉主角 A", style_lock)
        self.assertNotEqual(h1, h2)

    def test_prompt_payload_embeds_style_lock_and_layout_rules(self) -> None:
        asset = {"id": "a1", "desc": "系统页面主视觉", "position": "center", "frame": "browser", "aspect_ratio": "16:9", "variant_count": 2}
        page = {"page_id": "slide_02", "role": "hero_system"}
        style_lock = {"visual_rules": {"text_in_image": "avoid", "negative_prompts": ["generic ai poster look"]}}
        payload = build_prompt_payload(asset, page, "页面文案", "视觉规格", style_lock)
        self.assertEqual(payload["layout_constraints"]["frame"], "browser")
        self.assertEqual(payload["generation_rules"]["text_in_image"], "avoid")
        self.assertIn("generic ai poster look", payload["generation_rules"]["negative_prompts"])


if __name__ == "__main__":
    unittest.main()
