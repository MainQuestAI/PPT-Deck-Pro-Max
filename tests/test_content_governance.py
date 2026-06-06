from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from content_governance import (  # noqa: E402
    summarize_content_governance,
    validate_content_governance,
    validate_longform_governance,
)


def write_governance_files(project: Path, *, target: int = 24, max_supported: int = 30, blocking: bool = False) -> None:
    (project / "deck_brief.md").write_text("production_mode: expert\n", encoding="utf-8")
    (project / "deck_source_digest.md").write_text("# Source Digest\n\n- 已覆盖核心业务资料和可用证据。\n", encoding="utf-8")
    (project / "deck_capacity_plan.md").write_text("# Capacity Plan\n\n- 当前资料可支撑 30 页以内的专家模式 deck。\n", encoding="utf-8")
    (project / "deck_question_queue.md").write_text("# Question Queue\n\n1. 请补充一个可公开案例。\n", encoding="utf-8")
    (project / "deck_claim_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "claim_01",
                        "page_no": 1,
                        "claim_text": "内容容量需要前置判断",
                        "role": "hero_problem",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_capacity_plan.json").write_text(
        json.dumps(
            {
                "target_pages": target,
                "recommended_pages": min(target, max_supported),
                "max_supported_pages": max_supported,
            }
        ),
        encoding="utf-8",
    )
    gap = {
        "gap_id": "gap_01",
        "claim_id": "claim_01",
        "gap_type": "case",
        "desc": "缺少可公开案例",
        "status": "blocking" if blocking else "open",
    }
    (project / "deck_gap_registry.json").write_text(json.dumps({"gaps": [gap]}, ensure_ascii=False), encoding="utf-8")


def write_longform_files(project: Path) -> None:
    write_governance_files(project, target=6, max_supported=8)
    (project / "slide_state.json").write_text(
        json.dumps(
            {
                "pages": [
                    {"page_id": f"slide_{idx:02d}", "role": "hero_problem" if idx == 1 else "content"}
                    for idx in range(1, 7)
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_claim_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {"claim_id": "claim_01", "page_no": 1, "claim_text": "先判断资料容量", "role": "hero_problem", "evidence": ["访谈记录"]},
                    {"claim_id": "claim_02", "page_no": 4, "claim_text": "分章节生产能降低重复", "role": "proof", "evidence": ["生产复盘"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_capacity_plan.json").write_text(
        json.dumps(
            {
                "target_pages": 6,
                "recommended_pages": 4,
                "max_supported_pages": 8,
                "budget_tiers": {
                    "conservative": {"pages": 3, "core_pages": 2, "proof_pages": 1, "extension_pages": 0, "appendix_pages": 0, "required_inputs": []},
                    "recommended": {"pages": 4, "core_pages": 2, "proof_pages": 1, "extension_pages": 1, "appendix_pages": 0, "required_inputs": []},
                    "extended": {"pages": 6, "core_pages": 2, "proof_pages": 2, "extension_pages": 2, "appendix_pages": 0, "required_inputs": ["补一个案例"]},
                    "appendix_heavy": {"pages": 8, "core_pages": 2, "proof_pages": 2, "extension_pages": 1, "appendix_pages": 3, "required_inputs": ["补来源清单"]},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_section_packages.md").write_text(
        "# Section Packages\n\n## Section 1\n\n覆盖诊断与容量判断。\n\n## Section 2\n\n覆盖分章节生产与去重。\n",
        encoding="utf-8",
    )
    (project / "section_packages.json").write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "section_01",
                        "title": "容量诊断",
                        "objective": "判断资料能支撑多少页",
                        "page_count": 3,
                        "page_ids": ["slide_01", "slide_02", "slide_03"],
                        "claim_ids": ["claim_01"],
                        "allowed_evidence": ["访谈记录"],
                        "allowed_topics": ["容量判断"],
                        "forbidden_topics": ["报价"],
                        "input_transition": "从 brief 进入资料判断",
                        "output_transition": "转入章节拆包",
                        "density_level": "high",
                        "dense_archetype": "evidence_wall",
                    },
                    {
                        "section_id": "section_02",
                        "title": "章节生产",
                        "objective": "按章节降低重复扩写",
                        "page_count": 3,
                        "page_ids": ["slide_04", "slide_05", "slide_06"],
                        "claim_ids": ["claim_02"],
                        "allowed_evidence": ["生产复盘"],
                        "allowed_topics": ["章节拆包"],
                        "forbidden_topics": ["容量判断细节"],
                        "input_transition": "承接容量判断",
                        "output_transition": "进入逐页稿",
                        "density_level": "medium",
                        "suggested_archetypes": ["roadmap_risk_sidebar"],
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class ContentGovernanceTests(unittest.TestCase):
    def test_validate_content_governance_passes_when_capacity_and_gaps_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project)
            errors, summary = validate_content_governance(project)
            self.assertEqual(errors, [])
            self.assertTrue(summary["review_ready"])
            self.assertEqual(summary["claim_summary"]["total_claims"], 1)

    def test_validate_content_governance_fails_on_blocking_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project, blocking=True)
            errors, summary = validate_content_governance(project)
            self.assertTrue(any(error.startswith("blocking_gaps:") for error in errors))
            self.assertEqual(summary["gap_summary"]["blocking_gaps"], 1)

    def test_string_false_blocking_flag_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project)
            registry = json.loads((project / "deck_gap_registry.json").read_text(encoding="utf-8"))
            registry["gaps"][0]["blocking"] = "false"
            registry["gaps"][0]["status"] = "open"
            (project / "deck_gap_registry.json").write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
            errors, summary = validate_content_governance(project)
            self.assertEqual(errors, [])
            self.assertEqual(summary["gap_summary"]["blocking_gaps"], 0)

    def test_validate_content_governance_fails_when_target_exceeds_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project, target=80, max_supported=30)
            errors, summary = validate_content_governance(project)
            self.assertIn("capacity_over_target:80>30", errors)
            self.assertTrue(summary["capacity"]["over_capacity"])

    def test_validate_content_governance_fails_on_placeholder_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project)
            (project / "deck_question_queue.md").write_text(
                "# Question Queue\n\n（由 expert-interview 生成；进入逐页稿前先补齐 blocking gap）\n",
                encoding="utf-8",
            )
            errors, _ = validate_content_governance(project)
            self.assertIn("markdown_placeholder:deck_question_queue.md", errors)

    def test_quick_mode_disables_review_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_governance_files(project)
            (project / "deck_brief.md").write_text("production_mode: quick\n", encoding="utf-8")
            summary = summarize_content_governance(project)
            self.assertFalse(summary["enabled"])

    def test_validate_longform_governance_passes_when_budget_and_sections_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            errors, summary = validate_longform_governance(project)
            self.assertEqual(errors, [])
            self.assertTrue(summary["review_ready"])
            self.assertEqual(summary["section_summary"]["total_sections"], 2)
            self.assertTrue(summary["budget_summary"]["target_over_recommended"])

    def test_validate_longform_governance_fails_when_budget_tier_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            capacity = json.loads((project / "deck_capacity_plan.json").read_text(encoding="utf-8"))
            del capacity["budget_tiers"]["appendix_heavy"]
            (project / "deck_capacity_plan.json").write_text(json.dumps(capacity, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertIn("budget_tiers_missing:appendix_heavy", errors)

    def test_validate_longform_governance_fails_when_budget_tier_pages_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            capacity = json.loads((project / "deck_capacity_plan.json").read_text(encoding="utf-8"))
            capacity["budget_tiers"]["recommended"]["pages"] = None
            capacity["budget_tiers"]["recommended"]["core_pages"] = None
            capacity["budget_tiers"]["recommended"]["proof_pages"] = None
            capacity["budget_tiers"]["recommended"]["extension_pages"] = None
            capacity["budget_tiers"]["recommended"]["appendix_pages"] = None
            (project / "deck_capacity_plan.json").write_text(json.dumps(capacity, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertIn("budget_tier_missing_pages:recommended", errors)
            self.assertIn("budget_tier_missing_page_mix:recommended", errors)

    def test_validate_longform_governance_requires_extension_strategy_over_recommended(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            capacity = json.loads((project / "deck_capacity_plan.json").read_text(encoding="utf-8"))
            capacity["budget_tiers"]["extended"]["required_inputs"] = []
            capacity["budget_tiers"]["appendix_heavy"]["required_inputs"] = []
            capacity["budget_tiers"]["appendix_heavy"]["appendix_pages"] = 0
            (project / "deck_capacity_plan.json").write_text(json.dumps(capacity, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertIn("budget_requires_extension_strategy", errors)

    def test_validate_longform_governance_fails_on_section_page_total_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            sections = json.loads((project / "section_packages.json").read_text(encoding="utf-8"))
            sections["sections"][1]["page_count"] = 2
            (project / "section_packages.json").write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertIn("section_page_total_mismatch:5!=6", errors)

    def test_validate_longform_governance_detects_forbidden_topic_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            sections = json.loads((project / "section_packages.json").read_text(encoding="utf-8"))
            sections["sections"][0]["forbidden_topics"] = ["章节拆包"]
            (project / "section_packages.json").write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertTrue(any(error.startswith("forbidden_topic_conflict:") for error in errors))

    def test_validate_longform_governance_detects_unassigned_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            sections = json.loads((project / "section_packages.json").read_text(encoding="utf-8"))
            sections["sections"][1]["page_ids"] = ["slide_04", "slide_05"]
            (project / "section_packages.json").write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
            errors, _ = validate_longform_governance(project)
            self.assertIn("unassigned_pages:slide_06", errors)

    def test_validate_longform_governance_detects_dense_archetype_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_longform_files(project)
            sections = json.loads((project / "section_packages.json").read_text(encoding="utf-8"))
            sections["sections"][0]["dense_archetype"] = "unknown_dense"
            (project / "section_packages.json").write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
            errors, summary = validate_longform_governance(project)
            self.assertIn("dense_archetype_unknown:section_01:unknown_dense", errors)
            self.assertIn("evidence_wall", summary["known_dense_archetypes"])


if __name__ == "__main__":
    unittest.main()
