from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_review_package import find_candidate_dirs, find_latest_matching, summarize_asset_build, summarize_expert_mode  # noqa: E402
from generate_role_prompt import build_build_prompt, build_review_prompt  # noqa: E402


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

    def test_find_candidate_dirs_includes_assemble_starter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            starter = root / "assemble" / "batch_01" / "starter"
            starter.mkdir(parents=True, exist_ok=True)
            candidates = find_candidate_dirs(root)
            self.assertIn(starter, candidates)

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
            self.assertIn("asset_build_summary", prompt)
            self.assertIn("deck_expert_context.md", prompt)
            self.assertIn("expert_data_ignored", prompt)

    def test_summarize_asset_build_reports_runtime_progress(self) -> None:
        summary = summarize_asset_build(
            Path("/tmp"),
            {
                "assets": [
                    {"status": "approved", "stale": False},
                    {"status": "queued", "stale": True},
                    {"status": "placeholder", "stale": False},
                ]
            },
            {
                "initial_review_batch": "batch_01",
                "batches": [
                    {"batch_id": "batch_01", "status": "queued"},
                    {"batch_id": "batch_02", "status": "completed"},
                ],
                "jobs": [{"job_id": "a"}, {"job_id": "b"}],
            },
        )
        self.assertEqual(summary["approved_assets"], 1)
        self.assertEqual(summary["queued_assets"], 1)
        self.assertEqual(summary["stale_assets"], 1)
        self.assertEqual(summary["incomplete_batches"], ["batch_01"])

    def test_build_build_prompt_includes_batch_handoff_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "slide_state.json").write_text('{"output_mode":"html"}', encoding="utf-8")
            ctx = root / "batch_01.json"
            ctx.write_text(
                """
                {
                  "inputs": {
                    "generation_jobs": {
                      "slide_01": [
                        {"batch_id": "batch_01", "asset_id": "cover_visual", "prompt_intent": "封面主视觉"}
                      ],
                      "slide_03": [
                        {"batch_id": "batch_01", "asset_id": "proof_visual", "prompt_intent": "样例 proof 主视觉"}
                      ]
                    },
                    "generation_batch_summary": {
                      "initial_review_batch": "batch_01",
                      "batches": [{"batch_id": "batch_01", "status": "queued"}]
                    }
                  }
                }
                """,
                encoding="utf-8",
            )
            prompt = build_build_prompt(root, ["slide_01", "slide_03"], ctx, "batch_01")
            self.assertIn("当前批次", prompt)
            self.assertIn("Subagent 拆分建议", prompt)
            self.assertIn("cover_visual", prompt)
            self.assertIn("proof_visual", prompt)


if __name__ == "__main__":
    unittest.main()
