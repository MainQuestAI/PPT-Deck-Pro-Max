from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from migrate_language_notes import migrate_text  # noqa: E402
from validate_schema import validate_project  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class LanguageProductizationTests(unittest.TestCase):
    def test_language_schemas_are_auto_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_json(
                project / "audience_language_contract.json",
                {
                    "audience": "客户高层",
                    "scenario": "解决方案汇报",
                    "voice": {"allowed": ["结论先行"], "forbidden": ["生产过程描述"]},
                    "forbidden_terms": ["这一页负责"],
                    "expression_examples": [{"internal_form": "这一页负责", "customer_form": "业务风险可闭环"}],
                },
            )
            write_json(
                project / "deck_external_message_pack.json",
                {
                    "pages": [
                        {
                            "page_id": "slide_01",
                            "business_problem": "响应速度成为增长上限",
                            "customer_relevance": "影响转化效率",
                            "allowed_claims": ["缩短决策链路"],
                            "evidence_refs": [],
                            "visual_refs": [],
                        }
                    ]
                },
            )
            write_json(
                project / "customer_visible_copy.json",
                {
                    "pages": [
                        {
                            "page_id": "slide_01",
                            "title": "响应速度成为增长上限",
                            "body": ["机会窗口正在缩短"],
                            "insight": "领先企业正在压缩决策周期",
                            "speaker_script": "市场不会等待研究流程结束。",
                        }
                    ]
                },
            )

            self.assertEqual(validate_project(project), {})

            write_json(
                project / "audience_language_contract.json",
                {
                    "audience": "客户高层",
                    "scenario": "解决方案汇报",
                    "forbidden_terms": ["这一页负责"],
                    "expression_examples": [{"internal_form": "这一页负责", "customer_form": "业务风险可闭环"}],
                },
            )
            self.assertIn("audience_language_contract.json", validate_project(project))

    def test_migrate_language_dry_run_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            clean_pages = project / "deck_clean_pages.md"
            clean_pages.write_text("## 第 1 页\n> 演讲备注: 客户现场可说的话\n", encoding="utf-8")

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "migrate_language_notes.py"),
                    "--project-dir",
                    str(project),
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn('"would_change": true', dry_run.stdout)
            self.assertIn("> 演讲备注:", clean_pages.read_text(encoding="utf-8"))

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "migrate_language_notes.py"),
                    "--project-dir",
                    str(project),
                    "--write",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("> 讲者话术:", clean_pages.read_text(encoding="utf-8"))

    def test_migration_requires_confirmation_for_production_notes(self) -> None:
        text = "## 第 1 页\n> 演讲备注: 左侧放图表，右侧放结论卡片\n"
        migrated, actions, blocked = migrate_text(text, confirm_production_notes=False)
        self.assertTrue(blocked)
        self.assertEqual(migrated, text)
        self.assertEqual(actions[0]["status"], "needs_confirmation")

        migrated, actions, blocked = migrate_text(text, confirm_production_notes=True)
        self.assertFalse(blocked)
        self.assertIn("> 制作备注:", migrated)
        self.assertEqual(actions[0]["to"], "制作备注")

    def test_validate_language_writes_json_result_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_json(project / "audience_language_contract.json", {"forbidden_terms": ["这一页负责"]})
            (project / "deck_clean_pages.md").write_text(
                "## 第 1 页\n> 讲者话术: 这一页负责建立信任。\n",
                encoding="utf-8",
            )
            json_output = project / "language_gate_result.json"
            report_output = project / "language_gate_report.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "validate_external_language_contract.py"),
                    "--project-dir",
                    str(project),
                    "--require-contract",
                    "--json-output",
                    str(json_output),
                    "--report-output",
                    str(report_output),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(json_output.read_text(encoding="utf-8"))
            report = json.loads(report_output.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(report["violation_count"], 1)
            self.assertEqual(report["top_terms"][0]["term"], "这一页负责")
            self.assertNotIn("这一页负责建立信任", json.dumps(report, ensure_ascii=False))

    def test_language_contract_preset_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "language-contract",
                    "--project-dir",
                    str(project),
                    "--preset",
                    "formal_bid_image_led",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads((project / "audience_language_contract.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["preset"], "formal_bid_image_led")
            self.assertIn("评标专家", payload["audience"])
            self.assertIn("打动评委", payload["forbidden_terms"])


if __name__ == "__main__":
    unittest.main()
