from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_external_language_contract import validate_project_language  # noqa: E402


class ExternalLanguageContractTests(unittest.TestCase):
    def test_clean_customer_language_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "audience_language_contract.json").write_text(
                json.dumps({"forbidden_terms": ["这一页负责"]}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "deck_clean_pages.md").write_text(
                "## 第 1 页\n### 客户标题\n业务响应速度正在成为增长上限\n> 讲者话术: 市场不会等待研究流程结束，决策链路必须提前响应。\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_project_language(project, require_contract=True), [])

    def test_internal_language_failure_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "audience_language_contract.json").write_text(
                json.dumps({"forbidden_terms": ["这一页负责"]}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "deck_clean_pages.md").write_text(
                "## 第 1 页\n> 讲者话术: 这一页负责建立信任。\n",
                encoding="utf-8",
            )
            violations = validate_project_language(project, require_contract=True)
            self.assertEqual(violations[0]["page_id"], "slide_01")
            self.assertEqual(violations[0]["field"], "讲者话术")
            self.assertEqual(violations[0]["forbidden_term"], "这一页负责")
            self.assertIn("next_command", violations[0])

    def test_private_field_in_customer_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "audience_language_contract.json").write_text("{}", encoding="utf-8")
            (project / "customer_visible_copy.json").write_text(
                json.dumps({"pages": [{"page_id": "slide_01", "production_note": "内部备注"}]}, ensure_ascii=False),
                encoding="utf-8",
            )
            violations = validate_project_language(project, require_contract=True)
            self.assertTrue(any(v["field"] == "production_note" for v in violations))

    def test_multi_page_json_reports_correct_page_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "audience_language_contract.json").write_text(
                json.dumps({"forbidden_terms": ["这一页负责"]}, ensure_ascii=False),
                encoding="utf-8",
            )
            (project / "customer_visible_copy.json").write_text(
                json.dumps(
                    {
                        "pages": [
                            {"page_id": "slide_01", "title": "客户标题", "body": [], "insight": "", "speaker_script": "可见表达"},
                            {"page_id": "slide_07", "title": "客户标题", "body": [], "insight": "", "speaker_script": "这一页负责建立信任"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            violations = validate_project_language(project, require_contract=True)
            self.assertEqual(violations[0]["page_id"], "slide_07")
            self.assertEqual(violations[0]["field"], "$.pages[1].speaker_script")


if __name__ == "__main__":
    unittest.main()
