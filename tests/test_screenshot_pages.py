from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from screenshot_pages import build_slide_filename  # noqa: E402


class ScreenshotPagesTests(unittest.TestCase):
    def test_build_slide_filename_prefers_data_slide_id(self) -> None:
        self.assertEqual(build_slide_filename("slide_03", 1), "slide_03.png")
        self.assertEqual(build_slide_filename("slide-04", 1), "slide_04.png")

    def test_build_slide_filename_falls_back_to_sequence(self) -> None:
        self.assertEqual(build_slide_filename("", 2), "slide_02.png")
        self.assertEqual(build_slide_filename("cover", 5), "slide_05.png")


if __name__ == "__main__":
    unittest.main()
