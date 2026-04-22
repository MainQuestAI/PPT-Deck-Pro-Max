from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


class AssembleHtmlBatchTests(unittest.TestCase):
    def test_assemble_html_writes_sections_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            starter = project / "assemble" / "batch_01" / "starter"
            starter.mkdir(parents=True, exist_ok=True)
            (starter / "styles.css").write_text(":root { --bg: #000; }\n", encoding="utf-8")
            (project / "generated").mkdir(parents=True, exist_ok=True)
            (project / "generated" / "slide_03.png").write_text("fake", encoding="utf-8")
            (project / "assemble" / "batch_01" / "assemble_context.json").write_text(
                json.dumps(
                    {
                        "output_html": str((starter / "index.html").resolve()),
                        "output_css": str((starter / "styles.css").resolve()),
                        "pages": [
                            {
                                "page_id": "slide_03",
                                "role": "hero_proof",
                                "clean_page": "## 第 3 页\n样例页标题\n第一段内容\n第二段内容",
                                "approved_assets": [
                                    {
                                        "asset_id": "slide_03_screenshot",
                                        "final_path": "generated/slide_03.png",
                                        "position": "right",
                                        "desc": "proof visual",
                                    }
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "assemble_html_batch.py"), "--project-dir", str(project), "--batch-id", "batch_01"],
                check=True,
            )
            html = (starter / "index.html").read_text(encoding="utf-8")
            css = (starter / "styles.css").read_text(encoding="utf-8")
            self.assertIn('data-slide="slide_03"', html)
            self.assertIn("样例页标题", html)
            self.assertIn("generated/slide_03.png", html)
            self.assertIn(".deck {", css)


if __name__ == "__main__":
    unittest.main()
