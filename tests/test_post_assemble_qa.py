from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from run_deck_pipeline import cmd_post_assemble_qa  # noqa: E402


class PostAssembleQaTests(unittest.TestCase):
    def test_post_assemble_qa_runs_finalize_screenshot_review_and_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            assemble_dir = project / "assemble" / "batch_01"
            starter_dir = assemble_dir / "starter"
            starter_dir.mkdir(parents=True, exist_ok=True)
            html_path = starter_dir / "index.html"
            html_path.write_text("<html></html>", encoding="utf-8")
            (assemble_dir / "assemble_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch_01",
                        "output_html": str(html_path.resolve()),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            args = argparse.Namespace(
                project_dir=str(project),
                batch_id="batch_01",
                html_path=None,
                rendered_dir=None,
                review_package=None,
                report=None,
                montage=None,
                layout_manifest=None,
                theme_tokens=None,
                viewport="1280x720",
                warn_chars=700,
                fail_chars=1000,
            )

            with patch("run_deck_pipeline.run_script") as run_script:
                cmd_post_assemble_qa(args)

            calls = [(call.args[0], list(call.args[1:])) for call in run_script.call_args_list]
            self.assertEqual(
                [name for name, _ in calls],
                [
                    "finalize_html_assemble.py",
                    "screenshot_pages.py",
                    "generate_review_package.py",
                    "build_montage_and_report.py",
                ],
            )
            self.assertIn("--output-dir", calls[1][1])
            self.assertIn(str((project / "rendered").resolve()), calls[1][1])
            self.assertIn("--deck-path", calls[2][1])
            self.assertIn(str(html_path.resolve()), calls[2][1])
            self.assertIn("--write-state", calls[3][1])


if __name__ == "__main__":
    unittest.main()
