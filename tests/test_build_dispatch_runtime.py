from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SKILL_ROOT = Path(__file__).resolve().parents[1]


class BuildDispatchRuntimeTests(unittest.TestCase):
    def test_dispatch_build_generates_per_page_context_and_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "deck_clean_pages.md").write_text(
                "# Clean Pages\n\n## 第 3 页\n样例\n\n## 第 4 页\n系统\n",
                encoding="utf-8",
            )
            (project / "deck_visual_composition.md").write_text(
                "# Visual Composition\n\n## 第 3 页\nproof 主视觉\n\n## 第 4 页\nsystem 主视觉\n",
                encoding="utf-8",
            )
            (project / "deck_visual_system.md").write_text("# Visual System\n", encoding="utf-8")
            (project / "deck_component_tokens.md").write_text("# Component Tokens\n", encoding="utf-8")
            (project / "deck_theme_tokens.json").write_text('{"theme":"default","colors":{"accent":"#fff"}}', encoding="utf-8")
            (project / "style_lock.json").write_text('{"visual_rules":{"text_in_image":"avoid"}}', encoding="utf-8")
            (project / "slide_state.json").write_text(
                json.dumps(
                    {
                        "output_mode": "html",
                        "pages": [
                            {"page_id": "slide_03", "role": "hero_proof"},
                            {"page_id": "slide_04", "role": "hero_system"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "asset_manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {"id": "proof_visual", "page_id": "slide_03", "status": "queued", "source_mode": "generate"},
                            {"id": "system_visual", "page_id": "slide_04", "status": "queued", "source_mode": "generate"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "image_build_jobs.json").write_text(
                json.dumps(
                    {
                        "initial_review_batch": "batch_01",
                        "batches": [{"batch_id": "batch_01", "page_ids": ["slide_03", "slide_04"], "status": "queued"}],
                        "jobs": [
                            {"job_id": "j1", "batch_id": "batch_01", "page_id": "slide_03", "asset_id": "proof_visual", "status": "queued"},
                            {"job_id": "j2", "batch_id": "batch_01", "page_id": "slide_04", "asset_id": "system_visual", "status": "queued"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "generate_build_dispatch.py"), "--project-dir", str(project), "--batch-id", "batch_01"],
                check=True,
            )
            dispatch_json = json.loads((project / "dispatch" / "batch_01" / "dispatch.json").read_text(encoding="utf-8"))
            self.assertEqual(len(dispatch_json["tasks"]), 2)
            self.assertTrue((project / "dispatch" / "batch_01" / "slide_03_handoff.md").exists())
            context = json.loads((project / "dispatch" / "batch_01" / "contexts" / "slide_03.json").read_text(encoding="utf-8"))
            self.assertIn("generation_jobs", context["inputs"])

    def test_update_asset_runtime_syncs_job_and_batch_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "asset_manifest.json").write_text(
                json.dumps({"assets": [{"id": "proof_visual", "page_id": "slide_03", "status": "queued", "stale": True}]}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "image_build_jobs.json").write_text(
                json.dumps(
                    {
                        "batches": [{"batch_id": "batch_01", "page_ids": ["slide_03"], "status": "queued"}],
                        "jobs": [{"job_id": "j1", "batch_id": "batch_01", "page_id": "slide_03", "asset_id": "proof_visual", "status": "queued"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "update_asset_runtime.py"),
                    "--project-dir",
                    str(project),
                    "--asset-id",
                    "proof_visual",
                    "--status",
                    "approved",
                    "--final-path",
                    "generated/proof.png",
                    "--clear-stale",
                ],
                check=True,
            )

            manifest = json.loads((project / "asset_manifest.json").read_text(encoding="utf-8"))
            jobs = json.loads((project / "image_build_jobs.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["assets"][0]["status"], "approved")
            self.assertFalse(manifest["assets"][0]["stale"])
            self.assertEqual(manifest["assets"][0]["final_path"], "generated/proof.png")
            self.assertEqual(jobs["jobs"][0]["status"], "approved")
            self.assertEqual(jobs["batches"][0]["status"], "approved")

    def test_update_asset_runtime_marks_partial_batch_in_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "asset_manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {"id": "proof_visual", "page_id": "slide_03", "status": "queued", "stale": False},
                            {"id": "system_visual", "page_id": "slide_04", "status": "queued", "stale": False},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "image_build_jobs.json").write_text(
                json.dumps(
                    {
                        "batches": [{"batch_id": "batch_01", "page_ids": ["slide_03", "slide_04"], "status": "queued"}],
                        "jobs": [
                            {"job_id": "j1", "batch_id": "batch_01", "page_id": "slide_03", "asset_id": "proof_visual", "status": "queued"},
                            {"job_id": "j2", "batch_id": "batch_01", "page_id": "slide_04", "asset_id": "system_visual", "status": "queued"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "update_asset_runtime.py"),
                    "--project-dir",
                    str(project),
                    "--asset-id",
                    "proof_visual",
                    "--status",
                    "approved",
                ],
                check=True,
            )
            jobs = json.loads((project / "image_build_jobs.json").read_text(encoding="utf-8"))
            self.assertEqual(jobs["batches"][0]["status"], "in_review")


if __name__ == "__main__":
    unittest.main()
