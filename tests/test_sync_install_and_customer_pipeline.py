from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
RUN_DECK = SCRIPT_DIR / "run_deck_pipeline.py"
EXAMPLES = REPO_ROOT / "examples" / "customer_language_first"


def run_cli(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUN_DECK), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def copy_fixture(name: str, target: Path) -> None:
    shutil.copytree(EXAMPLES / name, target)


class SyncInstallAndCustomerPipelineTests(unittest.TestCase):
    def test_sync_install_dry_run_reports_difference_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deck_current = Path(tmp) / "current"
            entry = deck_current / "skills" / "ppt-deck-pro-max" / "SKILL.md"
            entry.parent.mkdir(parents=True)
            old_text = "# PPT Deck Pro Max Compatibility Entry\n\nFor new Deck Master workflows, prefer `deck-producer`.\n"
            entry.write_text(old_text, encoding="utf-8")
            report_path = Path(tmp) / "sync_report.json"

            run_cli(
                [
                    "sync-install",
                    "--deck-master-current",
                    str(deck_current),
                    "--dry-run",
                    "--json-output",
                    str(report_path),
                ]
            )

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(entry.read_text(encoding="utf-8"), old_text)
            self.assertTrue(report["entry_exists"])
            self.assertFalse(report["entry_up_to_date"])
            self.assertEqual(report["wrote"], False)
            self.assertIn("sync-install --write", report["next_command"])

    def test_sync_install_write_updates_compat_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deck_current = Path(tmp) / "current"
            entry = deck_current / "skills" / "ppt-deck-pro-max" / "SKILL.md"
            entry.parent.mkdir(parents=True)
            entry.write_text("# old wrapper\n", encoding="utf-8")
            report_path = Path(tmp) / "sync_report.json"

            run_cli(
                [
                    "sync-install",
                    "--deck-master-current",
                    str(deck_current),
                    "--write",
                    "--json-output",
                    str(report_path),
                ]
            )

            text = entry.read_text(encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("customer-language-first", text)
            self.assertIn("deck-producer", text)
            self.assertIn("<!-- customer-language-first:v1 -->", text)
            self.assertTrue(report["entry_up_to_date"])
            self.assertEqual(report["wrote"], True)

    def test_customer_language_first_clean_fixture_passes_and_exports_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "pass"
            copy_fixture("pass", project)
            result_path = project / "pipeline_result.json"
            report_path = project / "language_gate_report.json"

            run_cli(
                [
                    "customer-language-first",
                    "--project-dir",
                    str(project),
                    "--preset",
                    "solution_deck",
                    "--json-output",
                    str(result_path),
                    "--report-output",
                    str(report_path),
                ]
            )

            result = json.loads(result_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            notes = json.loads((project / "speaker_notes.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "passed")
            self.assertEqual(report["status"], "passed")
            self.assertIn("slide_01", notes)
            self.assertNotIn("制作备注", notes["slide_01"])
            self.assertNotIn("讲者提示", notes["slide_01"])

    def test_customer_language_first_fail_fixture_blocks_with_next_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "fail"
            copy_fixture("fail_internal_language", project)
            result_path = project / "pipeline_result.json"

            result = run_cli(
                [
                    "customer-language-first",
                    "--project-dir",
                    str(project),
                    "--preset",
                    "solution_deck",
                    "--json-output",
                    str(result_path),
                ],
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["step"], "validate-language")
            self.assertEqual(payload["violations"][0]["step"], "validate-language")
            self.assertIn("next_command", payload["violations"][0])

    def test_customer_language_first_skip_notes_does_not_generate_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "pass"
            copy_fixture("pass", project)
            result_path = project / "pipeline_result.json"

            run_cli(
                [
                    "customer-language-first",
                    "--project-dir",
                    str(project),
                    "--preset",
                    "solution_deck",
                    "--skip-notes",
                    "--json-output",
                    str(result_path),
                ]
            )

            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "passed")
            self.assertFalse((project / "speaker_notes.json").exists())

    def test_customer_language_first_legacy_notes_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "legacy"
            copy_fixture("legacy_migration", project)

            run_cli(
                [
                    "customer-language-first",
                    "--project-dir",
                    str(project),
                    "--preset",
                    "solution_deck",
                    "--legacy-speaker-notes",
                ]
            )

            notes = json.loads((project / "speaker_notes.json").read_text(encoding="utf-8"))
            self.assertIn("slide_01", notes)

    def test_docs_directory_remains_gitignored(self) -> None:
        result = subprocess.run(
            ["git", "check-ignore", "docs/private-note.md"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
