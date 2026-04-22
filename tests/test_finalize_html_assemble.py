from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


class FinalizeHtmlAssembleTests(unittest.TestCase):
    def test_finalize_html_assemble_marks_assets_embedded_and_pages_awaiting_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            assemble_dir = project / "assemble" / "batch_01" / "starter"
            assemble_dir.mkdir(parents=True, exist_ok=True)
            (assemble_dir / "index.html").write_text("<html></html>", encoding="utf-8")
            (project / "assemble" / "batch_01" / "assemble_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch_01",
                        "output_html": str((assemble_dir / "index.html").resolve()),
                        "pages": [
                            {
                                "page_id": "slide_03",
                                "approved_assets": [{"asset_id": "slide_03_screenshot"}],
                            },
                            {
                                "page_id": "slide_04",
                                "approved_assets": [{"asset_id": "slide_04_screenshot"}],
                            },
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
                            {"id": "slide_03_screenshot", "status": "approved"},
                            {"id": "slide_04_screenshot", "status": "approved"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "image_build_jobs.json").write_text(
                json.dumps(
                    {
                        "batches": [{"batch_id": "batch_01", "status": "approved"}],
                        "jobs": [
                            {"asset_id": "slide_03_screenshot", "status": "approved"},
                            {"asset_id": "slide_04_screenshot", "status": "approved"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "slide_state.json").write_text(
                json.dumps(
                    {
                        "global_status": "building",
                        "pages": [
                            {"page_id": "slide_03", "status": "building", "qa_status": "pending", "qa_reason": ""},
                            {"page_id": "slide_04", "status": "building", "qa_status": "pending", "qa_reason": ""},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "finalize_html_assemble.py"), "--project-dir", str(project), "--batch-id", "batch_01"],
                check=True,
            )

            assets = json.loads((project / "asset_manifest.json").read_text(encoding="utf-8"))
            jobs = json.loads((project / "image_build_jobs.json").read_text(encoding="utf-8"))
            state = json.loads((project / "slide_state.json").read_text(encoding="utf-8"))
            self.assertTrue(all(asset["status"] == "embedded" for asset in assets["assets"]))
            self.assertTrue(all(job["status"] == "embedded" for job in jobs["jobs"]))
            self.assertEqual(jobs["batches"][0]["status"], "completed")
            self.assertEqual(state["global_status"], "awaiting_review")
            self.assertTrue(all(page["status"] == "awaiting_review" for page in state["pages"]))


if __name__ == "__main__":
    unittest.main()
