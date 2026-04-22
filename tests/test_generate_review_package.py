from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_review_package import find_latest_matching, summarize_expert_mode  # noqa: E402
from generate_role_prompt import build_review_prompt  # noqa: E402


class GenerateReviewPackageTests(unittest.TestCase):
    def test_find_latest_matching_ignores_hidden_and_office_lock_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "deck_v1.pptx"
            lock = root / ".~deck_v2.pptx"
            hidden = root / ".deck_hidden.pptx"
            good.write_text("ok", encoding="utf-8")
            lock.write_text("lock", encoding="utf-8")
            hidden.write_text("hidden", encoding="utf-8")
            found = find_latest_matching([root], ["*.pptx"])
            self.assertEqual(found, good)

    def test_summarize_expert_mode_reports_ready_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "deck_brief.md").write_text("production_mode: expert\n", encoding="utf-8")
            (root / "deck_expert_context.md").write_text("# Expert Context\n", encoding="utf-8")
            session = {
                "state": "finalized",
                "redaction_pending": 0,
                "coverage": {
                    "hero_claims_total": 2,
                    "hero_claims_enriched": 2,
                    "hero_gap_fill_rate": 0.9,
                    "target_fill_rate": 0.8,
                },
            }
            preparation = {
                "claims": [
                    {"claim_id": "claim_01", "is_hero": True, "richness_score": 4, "gaps": [{"status": "filled"}]},
                    {"claim_id": "claim_02", "is_hero": False, "richness_score": 3, "gaps": [{"status": "filled"}]},
                ]
            }
            summary = summarize_expert_mode(root, session, preparation)
            self.assertTrue(summary["enabled"])
            self.assertTrue(summary["review_ready"])
            self.assertEqual(summary["issues"], [])
            self.assertEqual(summary["claim_summary"]["enriched_claims"], 2)

    def test_summarize_expert_mode_reports_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "deck_brief.md").write_text("production_mode: expert\n", encoding="utf-8")
            session = {
                "state": "completed",
                "redaction_pending": 2,
                "coverage": {
                    "hero_claims_total": 1,
                    "hero_claims_enriched": 0,
                    "hero_gap_fill_rate": 0.5,
                    "target_fill_rate": 0.8,
                },
            }
            preparation = {
                "claims": [
                    {"claim_id": "claim_01", "is_hero": True, "richness_score": 1, "gaps": [{"status": "open"}]},
                ]
            }
            summary = summarize_expert_mode(root, session, preparation)
            self.assertFalse(summary["review_ready"])
            self.assertIn("interview_session_not_finalized:completed", summary["issues"])
            self.assertIn("redaction_pending:2", summary["issues"])
            self.assertIn("deck_expert_context_missing", summary["issues"])
            self.assertIn("thin_hero_claims:claim_01", summary["issues"])

    def test_summarize_expert_mode_defaults_to_expert_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "deck_brief.md").write_text("# Deck Brief\n\n## 产品主语\n\nMirrorWorld\n", encoding="utf-8")
            summary = summarize_expert_mode(root, {}, {})
            self.assertTrue(summary["enabled"])
            self.assertEqual(summary["production_mode"], "expert")
            self.assertIn("interview_preparation_missing_or_empty", summary["issues"])

    def test_build_review_prompt_requires_expert_artifact_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = build_review_prompt(root)
            self.assertIn("expert_mode_summary", prompt)
            self.assertIn("deck_expert_context.md", prompt)
            self.assertIn("expert_data_ignored", prompt)


if __name__ == "__main__":
    unittest.main()
