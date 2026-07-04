from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from inject_speaker_notes import validate_notes, write_notes_json  # noqa: E402
from validate_external_language_contract import DEFAULT_FORBIDDEN_TERMS  # noqa: E402


class InjectSpeakerNotesTests(unittest.TestCase):
    def test_write_notes_json_exports_only_passed_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "speaker_notes.json"
            write_notes_json({1: "客户现场可说的话"}, output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"slide_01": "客户现场可说的话"})

    def test_validate_notes_rejects_internal_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                validate_notes({1: "这一页负责建立信任"}, list(DEFAULT_FORBIDDEN_TERMS), project_dir=Path(tmp))


if __name__ == "__main__":
    unittest.main()
