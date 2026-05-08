from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from doctor import run_checks  # noqa: E402
from init_deck_project import init_project  # noqa: E402
from init_slide_state import build_state  # noqa: E402


SKILL_ROOT = Path(__file__).resolve().parents[1]


class DoctorTests(unittest.TestCase):
    def test_repo_checks_cover_layout_and_schema_inventory(self) -> None:
        checks = run_checks(skill_root=SKILL_ROOT)
        by_name = {check.name: check for check in checks}
        self.assertEqual(by_name["path:SKILL.md"].status, "ok")
        self.assertEqual(by_name["path:scripts/run_deck_pipeline.py"].status, "ok")
        self.assertEqual(by_name["schema:inventory"].status, "ok")

    def test_project_check_accepts_fresh_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            init_project(project_dir)
            state = build_state("doctor_test", 3, "pptx+html")
            (project_dir / "slide_state.json").write_text(__import__("json").dumps(state), encoding="utf-8")

            checks = run_checks(skill_root=SKILL_ROOT, project_dir=project_dir)
            by_name = {check.name: check for check in checks}
            self.assertEqual(by_name["project:dir"].status, "ok")
            self.assertEqual(by_name["project:core-artifacts"].status, "ok")


if __name__ == "__main__":
    unittest.main()
