from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_montage_and_report import find_page_images  # noqa: E402
from validate_deck_outputs import find_artifact  # noqa: E402


class RenderedDirQaTests(unittest.TestCase):
    def test_find_page_images_prefers_rendered_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "slide_01.png").write_text("root", encoding="utf-8")
            rendered = project / "rendered"
            rendered.mkdir(parents=True, exist_ok=True)
            (rendered / "slide_03.png").write_text("rendered", encoding="utf-8")
            images = find_page_images(project)
            self.assertEqual(images, [rendered / "slide_03.png"])

    def test_find_artifact_detects_assemble_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            html_path = project / "assemble" / "batch_01" / "starter" / "index.html"
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text("<html></html>", encoding="utf-8")
            found = find_artifact(project, ["*.html", "index.html"])
            self.assertEqual(found, html_path)


if __name__ == "__main__":
    unittest.main()
