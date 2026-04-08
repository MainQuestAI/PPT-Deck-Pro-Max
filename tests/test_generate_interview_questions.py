from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_interview_questions import (  # noqa: E402
    extract_claims,
    detect_gaps,
    compute_richness,
    prioritize_gaps,
    extract_brief_concerns,
)


class ExtractClaimsTests(unittest.TestCase):
    def test_extracts_one_claim_per_page(self) -> None:
        text = "## 第 1 页\n标题：`封面`\n内容\n\n## 第 2 页\n标题：`诊断`\n三层断裂\n\n## 第 3 页\n标题：`闭环`\n持续循环"
        state = {"pages": [
            {"page_id": "slide_01", "role": "hero_cover"},
            {"page_id": "slide_02", "role": "hero_problem"},
            {"page_id": "slide_03", "role": "hero_system"},
        ]}
        claims = extract_claims(text, state)
        self.assertEqual(len(claims), 3)
        self.assertEqual(claims[0]["claim_id"], "claim_01")
        self.assertEqual(claims[0]["claim_text"], "封面")
        self.assertTrue(claims[0]["is_hero"])

    def test_hero_detection(self) -> None:
        text = "## 第 1 页\n标题：`普通页`\n内容"
        state = {"pages": [{"page_id": "slide_01", "role": "unassigned"}]}
        claims = extract_claims(text, state)
        self.assertFalse(claims[0]["is_hero"])


class MultiClaimTests(unittest.TestCase):
    def test_numbered_list_splits_into_multiple_claims(self) -> None:
        text = (
            "## 第 1 页\n标题：`三层断裂`\n"
            "1. 认知层断裂导致系统无法理解用户意图\n"
            "2. 决策层断裂导致策略无法精准执行\n"
            "3. 内容层断裂导致触达千人一面\n"
        )
        state = {"pages": [{"page_id": "slide_01", "role": "hero_problem"}]}
        claims = extract_claims(text, state)
        self.assertGreaterEqual(len(claims), 2)
        # All claims should reference the same page
        for c in claims:
            self.assertEqual(c["page_no"], 1)
            self.assertEqual(c["source_pages"], [1])
            self.assertTrue(c["is_hero"])
        # claim_ids should be like claim_01a, claim_01b, claim_01c
        ids = [c["claim_id"] for c in claims]
        self.assertTrue(ids[0].startswith("claim_01"))
        self.assertNotEqual(ids[0], ids[1])

    def test_single_argument_page_stays_single_claim(self) -> None:
        text = "## 第 5 页\n标题：`产品定位`\n这是一个简单的单论点页面"
        state = {"pages": [{"page_id": "slide_05", "role": "unassigned"}]}
        claims = extract_claims(text, state)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim_id"], "claim_05")

    def test_source_pages_field_exists(self) -> None:
        text = "## 第 3 页\n标题：`测试`\n内容"
        state = {"pages": [{"page_id": "slide_03", "role": "hero_cover"}]}
        claims = extract_claims(text, state)
        self.assertEqual(claims[0]["source_pages"], [3])


class DetectGapsTests(unittest.TestCase):
    def test_detects_case_gap(self) -> None:
        claim = {
            "claim_text": "系统越建越重",
            "claim_type": "assertion",
            "full_text": "系统越建越重，认知层断裂导致经营效率低下",
        }
        gaps = detect_gaps(claim)
        types = [g["gap_type"] for g in gaps]
        self.assertIn("case", types)

    def test_no_case_gap_when_example_present(self) -> None:
        claim = {
            "claim_text": "系统问题",
            "claim_type": "assertion",
            "full_text": "例如 XX 品牌有 2000 万会员但只用 12 个人群包",
        }
        gaps = detect_gaps(claim)
        types = [g["gap_type"] for g in gaps]
        self.assertNotIn("case", types)

    def test_detects_data_gap(self) -> None:
        claim = {
            "claim_text": "断裂很严重",
            "claim_type": "assertion",
            "full_text": "认知层断裂非常严重，系统完全无法理解用户意图",
        }
        gaps = detect_gaps(claim)
        types = [g["gap_type"] for g in gaps]
        self.assertIn("data", types)

    def test_detects_objection_gap_with_concerns(self) -> None:
        claim = {
            "claim_text": "数据安全方案",
            "claim_type": "assertion",
            "full_text": "系统会处理客户的数据安全和隐私合规问题",
        }
        concerns = ["数据安全——我的数据会怎样"]
        gaps = detect_gaps(claim, concerns)
        types = [g["gap_type"] for g in gaps]
        self.assertIn("objection", types)


class ComputeRichnessTests(unittest.TestCase):
    def test_empty_claim_scores_zero(self) -> None:
        claim = {"full_text": "系统需要升级"}
        self.assertEqual(compute_richness(claim), 0)

    def test_rich_claim_scores_high(self) -> None:
        claim = {"full_text": "例如某品牌因为标签没变状态，导致 2000 万会员只有 < 1% 活跃人群包，就像自动贩卖机，不是推翻重做而是增量升级"}
        score = compute_richness(claim)
        self.assertGreaterEqual(score, 3)


class PrioritizeGapsTests(unittest.TestCase):
    def test_hero_gaps_first(self) -> None:
        claims = [
            {"claim_id": "c1", "is_hero": True, "richness_score": 1, "gaps": [
                {"gap_type": "case", "topic": "t1", "desc": "d1", "status": "open"}
            ]},
            {"claim_id": "c2", "is_hero": False, "richness_score": 0, "gaps": [
                {"gap_type": "data", "topic": "t2", "desc": "d2", "status": "open"}
            ]},
        ]
        result = prioritize_gaps(claims)
        self.assertTrue(result[0]["is_hero"])


class ExtractBriefConcernsTests(unittest.TestCase):
    def test_extracts_concerns(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Brief\n\n## 关键顾虑\n\n1. 可信度——真的有用吗\n2. 落地复杂度——要配多少人\n\n## 下一节\n")
            f.flush()
            concerns = extract_brief_concerns(Path(f.name))
            self.assertEqual(len(concerns), 2)
            self.assertIn("可信度", concerns[0])


if __name__ == "__main__":
    unittest.main()
