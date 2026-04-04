from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REFERENCE_DIR = Path(__file__).resolve().parents[1] / "references"
sys.path.insert(0, str(SCRIPT_DIR))

from route_review_findings import build_plan, load_json  # noqa: E402


class RouteReviewFindingsTests(unittest.TestCase):
    def test_build_plan_routes_findings_to_expected_stages(self) -> None:
        rollback_map = load_json(REFERENCE_DIR / "review_rollback_map.json")
        findings = [
            {
                "page_id": "slide_01",
                "severity": "high",
                "type": "geometry_broken",
                "reason": "连线未锚定到节点中心",
                "suggested_fix": "回到骨架层修正锚点",
                "source_image": "slide_01.png",
            },
            {
                "page_id": "slide_02",
                "severity": "medium",
                "type": "cta_weak",
                "reason": "下一步动作不明确",
                "suggested_fix": "重锁 CTA",
                "source_image": "slide_02.png",
            },
        ]
        state = {"pages": [{"page_id": "slide_01"}, {"page_id": "slide_02"}]}
        plan = build_plan(Path("/tmp/project"), findings, rollback_map, state)
        stage_names = {item["rollback_stage"] for item in plan["stage_actions"]}
        self.assertEqual(stage_names, {"geometry", "brief"})
        page_primary = {item["page_id"]: item["primary_route"]["rollback_stage"] for item in plan["page_actions"]}
        self.assertEqual(page_primary["slide_01"], "geometry")
        self.assertEqual(page_primary["slide_02"], "brief")

    def test_build_plan_supports_new_commercial_types(self) -> None:
        rollback_map = load_json(REFERENCE_DIR / "review_rollback_map.json")
        findings = [
            {
                "page_id": "slide_03",
                "severity": "high",
                "type": "buying_reason_blurry",
                "reason": "前五页没有立住为什么现在值得买",
                "suggested_fix": "重写第一购买理由和前置顺序",
                "source_image": "slide_03.png",
            }
        ]
        state = {"pages": [{"page_id": "slide_03"}]}
        plan = build_plan(Path("/tmp/project"), findings, rollback_map, state)
        self.assertEqual(plan["page_actions"][0]["primary_route"]["rollback_stage"], "brief")


if __name__ == "__main__":
    unittest.main()
