from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_montage_and_report import detect_expert_mode_issues, summarize_expert_mode_issues  # noqa: E402
from finalize_interview import (  # noqa: E402
    validate_session,
    validate_state_transition,
    compute_coverage,
    generate_expert_context,
    VALID_TRANSITIONS,
)


class DetectExpertModeIssuesTests(unittest.TestCase):
    def test_content_thin_detects_low_richness_hero(self) -> None:
        preparation = {
            "claims": [
                {"claim_id": "claim_03", "page_no": 3, "is_hero": True, "richness_score": 1, "gaps": []},
                {"claim_id": "claim_05", "page_no": 5, "is_hero": True, "richness_score": 4, "gaps": []},
            ],
        }
        issues = detect_expert_mode_issues(None, preparation, None, None)
        self.assertIn("slide_03", issues)
        self.assertTrue(any("content_thin" in i for i in issues["slide_03"]))
        self.assertNotIn("slide_05", issues)

    def test_no_issue_when_non_hero_low_richness(self) -> None:
        preparation = {
            "claims": [
                {"claim_id": "claim_04", "page_no": 4, "is_hero": False, "richness_score": 1, "gaps": []},
            ],
        }
        issues = detect_expert_mode_issues(None, preparation, None, None)
        self.assertEqual(issues, {})

    def test_redaction_incomplete(self) -> None:
        session = {"redaction_pending": 2}
        issues = detect_expert_mode_issues(session, {"claims": []}, None, None)
        self.assertIn("__expert__", issues)
        self.assertTrue(any("redaction_incomplete" in i for i in issues["__expert__"]))

    def test_no_redaction_issue_when_zero(self) -> None:
        session = {"redaction_pending": 0}
        issues = detect_expert_mode_issues(session, {"claims": []}, None, None)
        self.assertNotIn("__expert__", issues)

    def test_expert_data_ignored_with_keyword_matching(self) -> None:
        """Enriched claims whose keywords don't appear in clean_pages trigger expert_data_ignored."""
        import tempfile
        preparation = {
            "claims": [
                {
                    "claim_id": "claim_01",
                    "page_no": 1,
                    "is_hero": True,
                    "richness_score": 4,
                    "claim_text": "认知层断裂导致效率低下",
                    "subtitle": "三层断裂诊断",
                    "gaps": [{"gap_type": "case", "desc": "缺少品牌案例", "status": "filled"}],
                },
                {
                    "claim_id": "claim_02",
                    "page_no": 2,
                    "is_hero": True,
                    "richness_score": 3,
                    "claim_text": "数据安全方案完备",
                    "gaps": [{"gap_type": "data", "desc": "缺少量化数据", "status": "filled"}],
                },
            ],
        }
        # Clean pages text that doesn't contain any of the claim keywords
        clean_pages = "这是一个完全不相关的内容页面，讲的是天气预报和旅游攻略"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Expert Context\n\nSome expert content here\n")
            f.flush()
            expert_path = Path(f.name)
            issues = detect_expert_mode_issues(None, preparation, expert_path, clean_pages)
            self.assertIn("__expert__", issues)
            self.assertTrue(any("expert_data_ignored" in i for i in issues["__expert__"]))

    def test_expert_data_not_ignored_when_keywords_present(self) -> None:
        """When clean_pages contains claim keywords, no expert_data_ignored is raised."""
        import tempfile
        preparation = {
            "claims": [
                {
                    "claim_id": "claim_01",
                    "page_no": 1,
                    "is_hero": True,
                    "richness_score": 4,
                    "claim_text": "认知层断裂导致效率低下",
                    "gaps": [{"gap_type": "case", "desc": "缺少品牌案例", "status": "filled"}],
                },
                {
                    "claim_id": "claim_02",
                    "page_no": 2,
                    "is_hero": True,
                    "richness_score": 3,
                    "claim_text": "数据安全方案完备",
                    "gaps": [{"gap_type": "data", "desc": "缺少量化数据", "status": "filled"}],
                },
            ],
        }
        # Clean pages that DOES contain the claim keywords
        clean_pages = "认知层断裂导致效率低下，品牌案例证明了数据安全方案完备的量化数据"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Expert Context\n\nContent\n")
            f.flush()
            expert_path = Path(f.name)
            issues = detect_expert_mode_issues(None, preparation, expert_path, clean_pages)
            # Should NOT have expert_data_ignored
            expert_issues = issues.get("__expert__", [])
            self.assertFalse(any("expert_data_ignored" in i for i in expert_issues))

    def test_returns_empty_without_preparation(self) -> None:
        issues = detect_expert_mode_issues(None, None, None, None)
        self.assertEqual(issues, {})

    def test_summary_blockers_promote_to_expert_issue_bucket(self) -> None:
        summary = {
            "enabled": True,
            "issues": [
                "interview_preparation_missing_or_empty",
                "deck_expert_context_missing",
            ],
        }
        issues = summarize_expert_mode_issues(summary)
        self.assertIn("__expert__", issues)
        self.assertIn("interview_preparation_missing_or_empty", issues["__expert__"])

    def test_summary_issues_ignored_when_expert_mode_disabled(self) -> None:
        issues = summarize_expert_mode_issues({"enabled": False, "issues": ["deck_expert_context_missing"]})
        self.assertEqual(issues, {})


class ValidateSessionTests(unittest.TestCase):
    def test_valid_completed_session(self) -> None:
        session = {"state": "completed", "redaction_pending": 0}
        errors = validate_session(session)
        self.assertEqual(errors, [])

    def test_invalid_state(self) -> None:
        session = {"state": "in_progress", "redaction_pending": 0}
        errors = validate_session(session)
        self.assertTrue(any("state" in e for e in errors))

    def test_pending_redaction(self) -> None:
        session = {"state": "completed", "redaction_pending": 3}
        errors = validate_session(session)
        self.assertTrue(any("redaction" in e for e in errors))

    def test_aborted_is_valid(self) -> None:
        session = {"state": "aborted", "redaction_pending": 0}
        errors = validate_session(session)
        self.assertEqual(errors, [])


class StateMachineTests(unittest.TestCase):
    def test_valid_transitions(self) -> None:
        self.assertIsNone(validate_state_transition("preparing", "in_progress"))
        self.assertIsNone(validate_state_transition("preparing", "aborted"))
        self.assertIsNone(validate_state_transition("in_progress", "completed"))
        self.assertIsNone(validate_state_transition("in_progress", "aborted"))
        self.assertIsNone(validate_state_transition("completed", "finalized"))
        self.assertIsNone(validate_state_transition("aborted", "finalized"))

    def test_illegal_transitions(self) -> None:
        # Can't skip from preparing to completed
        err = validate_state_transition("preparing", "completed")
        self.assertIsNotNone(err)
        self.assertIn("illegal", err)

        # Can't go back from completed to in_progress
        err = validate_state_transition("completed", "in_progress")
        self.assertIsNotNone(err)

        # Can't go from finalized to anything
        err = validate_state_transition("finalized", "preparing")
        self.assertIsNotNone(err)

    def test_unknown_state(self) -> None:
        err = validate_state_transition("bogus", "completed")
        self.assertIsNotNone(err)
        self.assertIn("unknown", err)

    def test_all_states_have_entries(self) -> None:
        expected = {"preparing", "in_progress", "completed", "aborted", "finalized"}
        self.assertEqual(set(VALID_TRANSITIONS.keys()), expected)

    def test_validate_session_catches_illegal_transition(self) -> None:
        # preparing -> finalized is illegal (must go through in_progress/completed first)
        session = {"state": "preparing", "redaction_pending": 0}
        errors = validate_session(session)
        self.assertTrue(any("illegal" in e or "state" in e for e in errors))


class ComputeCoverageTests(unittest.TestCase):
    def test_extracts_coverage_fields(self) -> None:
        session = {
            "coverage": {
                "hero_claims_total": 5,
                "hero_claims_enriched": 4,
                "hero_gap_fill_rate": 0.85,
                "target_fill_rate": 0.8,
            }
        }
        result = compute_coverage(session)
        self.assertEqual(result["hero_claims_total"], 5)
        self.assertAlmostEqual(result["hero_gap_fill_rate"], 0.85)

    def test_defaults_on_empty(self) -> None:
        result = compute_coverage({})
        self.assertEqual(result["hero_claims_total"], 0)
        self.assertEqual(result["hero_gap_fill_rate"], 0)


class GenerateExpertContextTests(unittest.TestCase):
    def test_generates_markdown(self) -> None:
        session = {
            "session_id": "test_001",
            "state": "completed",
            "insights_collected": 5,
            "coverage": {"hero_gap_fill_rate": 0.85},
        }
        preparation = {
            "claims": [
                {
                    "claim_id": "claim_01",
                    "claim_text": "测试论点",
                    "claim_type": "assertion",
                    "beat_hint": "setup",
                    "richness_score": 3,
                    "gaps": [
                        {"gap_type": "case", "desc": "缺少案例", "status": "filled"},
                    ],
                },
            ],
        }
        content = generate_expert_context(session, preparation)
        self.assertIn("# Expert Context", content)
        self.assertIn("test_001", content)
        self.assertIn("claim_01", content)
        self.assertIn("已填补缺口", content)


if __name__ == "__main__":
    unittest.main()
