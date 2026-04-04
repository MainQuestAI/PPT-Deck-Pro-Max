from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_montage_and_report import validate_commercial_scorecard  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
