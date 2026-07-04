from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_montage_and_report import detect_missing_speaker_notes, validate_commercial_scorecard  # noqa: E402


class BuildMontageAndReportTests(unittest.TestCase):
    def test_validate_commercial_scorecard_accepts_complete_payload(self) -> None:
        scorecard = {
            "overall_score": 4.1,
            "dimensions": {
                "audience_fit": 4,
                "buying_reason_clarity": 4,
                "proof_strength": 5,
                "objection_coverage": 4,
                "narrative_flow": 4,
                "commercial_ask": 4,
            },
            "summary": "前五页已经建立起可信度和合作动作。",
            "recommended_action": "进入正式外发前再精修一轮关键页。",
        }
        validate_commercial_scorecard(scorecard)

    def test_detect_missing_speaker_notes_accepts_new_script_format(self) -> None:
        state = {"pages": [{"page_id": "slide_01", "role": "hero_problem"}]}
        clean_pages = "## 第 1 页\n> 讲者话术: 市场不会等待研究流程结束。\n"
        self.assertEqual(detect_missing_speaker_notes(state, clean_pages), {})

    def test_detect_missing_speaker_notes_flags_internal_language(self) -> None:
        state = {"pages": [{"page_id": "slide_01", "role": "hero_problem"}]}
        clean_pages = "## 第 1 页\n> 讲者话术: 这一页负责建立信任。\n"
        issues = detect_missing_speaker_notes(state, clean_pages)
        self.assertIn("slide_01", issues)
        self.assertTrue(any(issue.startswith("internal_language_leak:") for issue in issues["slide_01"]))


if __name__ == "__main__":
    unittest.main()
