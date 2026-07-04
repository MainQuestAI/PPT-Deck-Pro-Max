from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from page_parser import (  # noqa: E402
    extract_page_slices,
    extract_production_notes,
    extract_speaker_cues,
    extract_speaker_notes,
    extract_speaker_scripts,
)


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

    def test_extract_speaker_scripts_prefers_new_format(self) -> None:
        text = """
## 第 1 页
> 演讲备注: 旧格式备注
> 讲者话术: 客户现场可说的话
"""
        scripts = extract_speaker_scripts(text)
        self.assertEqual(scripts[1], "客户现场可说的话")

    def test_extract_speaker_scripts_can_disable_legacy(self) -> None:
        text = """
## 第 1 页
> 演讲备注: 旧格式备注
"""
        self.assertEqual(extract_speaker_scripts(text, allow_legacy=False), {})
        self.assertEqual(extract_speaker_notes(text)[1], "旧格式备注")

    def test_extract_speaker_scripts_supports_multiline_continuation(self) -> None:
        text = """
## 第 1 页
> 讲者话术: 第一行
> 第二行继续
> 讲者提示: 停顿一秒
> 制作备注: 内部布局备注
"""
        scripts = extract_speaker_scripts(text)
        self.assertEqual(scripts[1], "第一行 第二行继续")
        self.assertEqual(extract_speaker_cues(text)[1], "停顿一秒")
        self.assertEqual(extract_production_notes(text)[1], "内部布局备注")


if __name__ == "__main__":
    unittest.main()
