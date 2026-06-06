from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


def write_project(project: Path) -> None:
    (project / "deck_brief.md").write_text("production_mode: expert\n", encoding="utf-8")
    (project / "deck_capacity_plan.json").write_text(
        json.dumps(
            {
                "target_pages": 4,
                "recommended_pages": 4,
                "max_supported_pages": 6,
                "budget_tiers": {
                    "conservative": {"pages": 2, "core_pages": 1, "proof_pages": 1, "extension_pages": 0, "appendix_pages": 0, "required_inputs": []},
                    "recommended": {"pages": 4, "core_pages": 2, "proof_pages": 1, "extension_pages": 1, "appendix_pages": 0, "required_inputs": []},
                    "extended": {"pages": 5, "core_pages": 2, "proof_pages": 2, "extension_pages": 1, "appendix_pages": 0, "required_inputs": ["补案例"]},
                    "appendix_heavy": {"pages": 6, "core_pages": 2, "proof_pages": 2, "extension_pages": 1, "appendix_pages": 1, "required_inputs": ["补附录"]},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_claim_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {"claim_id": "claim_01", "page_no": 1, "claim_text": "当前章节 claim", "evidence": ["章节证据"]},
                    {"claim_id": "claim_02", "page_no": 3, "claim_text": "其他章节 claim", "evidence": ["其他证据"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "deck_gap_registry.json").write_text(
        json.dumps(
            {
                "gaps": [
                    {"gap_id": "gap_01", "claim_id": "claim_01", "gap_type": "case", "status": "open", "desc": "补当前章节案例"},
                    {"gap_id": "gap_02", "claim_id": "claim_02", "gap_type": "data", "status": "open", "desc": "补其他章节数据"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project / "section_packages.json").write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "section_01",
                        "title": "当前章节",
                        "objective": "只写当前章节",
                        "page_count": 2,
                        "page_ids": ["slide_01", "slide_02"],
                        "claim_ids": ["claim_01"],
                        "allowed_evidence": ["章节证据"],
                        "allowed_topics": ["当前主题"],
                        "forbidden_topics": ["其他章节主题"],
                        "input_transition": "进入当前章节",
                        "output_transition": "转到下一章节",
                        "density_level": "high",
                        "dense_archetype": "evidence_wall",
                    },
                    {
                        "section_id": "section_02",
                        "title": "其他章节",
                        "objective": "保留给其他 worker",
                        "page_count": 2,
                        "page_ids": ["slide_03", "slide_04"],
                        "claim_ids": ["claim_02"],
                        "allowed_evidence": ["其他证据"],
                        "allowed_topics": ["其他章节主题"],
                        "forbidden_topics": ["当前主题"],
                        "input_transition": "承接当前章节",
                        "output_transition": "进入收口",
                        "density_level": "medium",
                        "suggested_archetypes": ["roadmap_risk_sidebar"],
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class GenerateSectionHandoffTests(unittest.TestCase):
    def test_section_handoff_contains_only_current_section_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(project)
            output = project / "section_01_handoff.md"
            output_json = project / "section_01_handoff.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "section-handoff",
                    "--project-dir",
                    str(project),
                    "--section-id",
                    "section_01",
                    "--output",
                    str(output),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            text = output.read_text(encoding="utf-8")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertIn("claim_01", text)
            self.assertIn("gap_01", text)
            self.assertIn("evidence_wall", text)
            self.assertNotIn("claim_02", text)
            self.assertNotIn("gap_02", text)
            self.assertEqual([claim["claim_id"] for claim in payload["claims"]], ["claim_01"])
            self.assertEqual([gap["gap_id"] for gap in payload["gaps"]], ["gap_01"])


if __name__ == "__main__":
    unittest.main()
