from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from content_governance import summarize_content_governance, validate_content_governance  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
