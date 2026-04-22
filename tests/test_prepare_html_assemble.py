from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


class PrepareHtmlAssembleTests(unittest.TestCase):
    def test_prepare_html_assemble_requires_approved_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "image_build_jobs.json").write_text(
                json.dumps({"batches": [{"batch_id": "batch_01", "page_ids": ["slide_03"], "status": "in_review"}], "jobs": []}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "asset_manifest.json").write_text(json.dumps({"assets": []}, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "prepare_html_assemble.py"), "--project-dir", str(project), "--batch-id", "batch_01"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Expected approved/completed", result.stderr + result.stdout)

    def test_prepare_html_assemble_outputs_manifest_for_approved_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "deck_clean_pages.md").write_text("# Clean Pages\n\n## 第 3 页\n样例文案\n", encoding="utf-8")
            (project / "deck_visual_composition.md").write_text("# Visual Composition\n\n## 第 3 页\n主视觉规格\n", encoding="utf-8")
            (project / "deck_theme_tokens.json").write_text('{"theme":"default","colors":{"accent":"#fff"}}', encoding="utf-8")
            (project / "style_lock.json").write_text('{"visual_rules":{"text_in_image":"avoid"}}', encoding="utf-8")
            (project / "slide_state.json").write_text(
                json.dumps({"pages": [{"page_id": "slide_03", "role": "hero_proof"}]}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "image_build_jobs.json").write_text(
                json.dumps(
                    {"batches": [{"batch_id": "batch_01", "page_ids": ["slide_03"], "status": "approved"}], "jobs": []},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "asset_manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "id": "slide_03_screenshot",
                                "page_id": "slide_03",
                                "status": "approved",
                                "final_path": "generated/slide_03.png",
                                "position": "right",
                                "frame": "browser",
                                "desc": "proof visual",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "prepare_html_assemble.py"), "--project-dir", str(project), "--batch-id", "batch_01"],
                check=True,
            )
            manifest = json.loads((project / "assemble" / "batch_01" / "assemble_manifest.json").read_text(encoding="utf-8"))
            assemble_context = json.loads((project / "assemble" / "batch_01" / "assemble_context.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["batch_id"], "batch_01")
            self.assertEqual(manifest["pages"][0]["page_id"], "slide_03")
            self.assertEqual(manifest["pages"][0]["approved_assets"][0]["asset_id"], "slide_03_screenshot")
            self.assertEqual(assemble_context["output_html"], manifest["output_html"])
            self.assertTrue((project / "assemble" / "batch_01" / "starter" / "index.html").exists())
            self.assertTrue((project / "assemble" / "batch_01" / "starter" / "styles.css").exists())


if __name__ == "__main__":
    unittest.main()
