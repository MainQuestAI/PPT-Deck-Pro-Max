from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from page_parser import extract_page_slices  # noqa: E402


class PageParserTests(unittest.TestCase):
    def test_extract_page_slices_supports_multiple_heading_formats(self) -> None:
        text = """
## 第 1 页
内容 A

**第 2 页**
内容 B

Page 03
内容 C

slide_04
内容 D
"""
        sections = extract_page_slices(text)
        self.assertEqual(set(sections.keys()), {1, 2, 3, 4})
        self.assertIn("内容 A", sections[1])
        self.assertIn("内容 B", sections[2])
        self.assertIn("内容 C", sections[3])
        self.assertIn("内容 D", sections[4])


if __name__ == "__main__":
    unittest.main()
