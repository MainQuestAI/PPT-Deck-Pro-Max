from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_visual_composition import detect_relationship, suggest_icons, suggest_illustrative_data, generate_composition  # noqa: E402


class DetectRelationshipTests(unittest.TestCase):
    def test_detects_comparison(self) -> None:
        text = "传统 MA vs 下一代 MA 的区别"
        self.assertEqual(detect_relationship(text), "comparison")

    def test_detects_degree_gap(self) -> None:
        text = "认知层断裂：理解不足，覆盖率差距明显"
        self.assertEqual(detect_relationship(text), "degree_gap")

    def test_detects_flow_process(self) -> None:
        text = "第一步定义目标 → 然后读取状态 → 最后回写"
        self.assertEqual(detect_relationship(text), "flow_process")

    def test_detects_closed_loop(self) -> None:
        text = "闭环机制：监测 → 修复 → 反馈回流 → 持续循环优化"
        self.assertEqual(detect_relationship(text), "closed_loop")

    def test_detects_category(self) -> None:
        text = "五类核心业务价值维度"
        self.assertEqual(detect_relationship(text), "category")

    def test_detects_big_metric(self) -> None:
        text = "6.02 亿用户，覆盖率 42.8%"
        self.assertEqual(detect_relationship(text), "big_metric")

    def test_detects_layer_input_output(self) -> None:
        text = "输入层：用户上下文；处理层：智能体；输出层：内容版本"
        self.assertEqual(detect_relationship(text), "layer_input_output")

    def test_detects_timeline_evolution(self) -> None:
        text = "三代演进：标签式 CDP → 画像式 CDP → 语义型 CDP"
        self.assertEqual(detect_relationship(text), "timeline_evolution")

    def test_case_insensitive_english(self) -> None:
        text = "SEO VS GEO 的本质区别"
        self.assertEqual(detect_relationship(text), "comparison")

    def test_empty_text_defaults_to_category(self) -> None:
        self.assertEqual(detect_relationship(""), "category")


class SuggestIconsTests(unittest.TestCase):
    def test_finds_relevant_icons(self) -> None:
        text = "认知层断裂：用户理解不足，决策能力缺失"
        icons = suggest_icons(text)
        icon_names = [ic["icon"] for ic in icons]
        self.assertIn("brain", icon_names)

    def test_respects_max_limit(self) -> None:
        text = "认知、决策、内容、监测、修复、数据、Agent、转化、合规、目标"
        icons = suggest_icons(text, max_icons=3)
        self.assertLessEqual(len(icons), 3)

    def test_no_duplicate_icons(self) -> None:
        text = "用户理解、用户认知、用户状态"
        icons = suggest_icons(text)
        icon_names = [ic["icon"] for ic in icons]
        self.assertEqual(len(icon_names), len(set(icon_names)))


class SuggestIllustrativeDataTests(unittest.TestCase):
    def test_degree_gap_generates_gauges(self) -> None:
        data = suggest_illustrative_data("degree_gap", "认知层断裂、决策层不足")
        self.assertTrue(len(data) > 0)
        self.assertTrue(all(d["type"] == "gauge" for d in data))
        self.assertTrue(all(d["illustrative"] for d in data))

    def test_comparison_generates_bars(self) -> None:
        data = suggest_illustrative_data("comparison", "传统 vs AI")
        self.assertTrue(len(data) >= 2)

    def test_big_metric_returns_empty(self) -> None:
        data = suggest_illustrative_data("big_metric", "6.02 亿")
        self.assertEqual(len(data), 0)


class GenerateCompositionTests(unittest.TestCase):
    def test_generates_for_all_pages(self) -> None:
        text = "## 第 1 页\n标题：`封面`\n内容\n\n## 第 2 页\n标题：`诊断`\n三层断裂\n\n## 第 3 页\n标题：`闭环`\n持续循环反馈回流闭环"
        state = {"pages": [
            {"page_id": "slide_01", "role": "hero_cover"},
            {"page_id": "slide_02", "role": "hero_problem"},
            {"page_id": "slide_03", "role": "hero_system"},
        ]}
        comps = generate_composition(text, state)
        self.assertEqual(len(comps), 3)
        self.assertTrue(all("visual_protagonist" in c for c in comps))
        self.assertTrue(all("protagonist_position" in c for c in comps))
        self.assertTrue(all("visual_weight" in c for c in comps))

    def test_concept_ui_generated_for_flow_proof_pages(self) -> None:
        text = "## 第 1 页\n标题：`首购转化`\n首购转化流程：浏览 → 判断 → 推送 → 转化"
        state = {"pages": [{"page_id": "slide_01", "role": "hero_proof"}]}
        comps = generate_composition(text, state)
        self.assertIsNotNone(comps[0].get("concept_ui"))
        self.assertIn("conversion", comps[0]["concept_ui"].lower())


if __name__ == "__main__":
    unittest.main()
