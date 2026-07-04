from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_role_prompt import build_external_expression_prompt  # noqa: E402


class GenerateRolePromptTests(unittest.TestCase):
    def test_external_expression_prompt_uses_only_allowed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "audience_language_contract.json").write_text(json.dumps({"forbidden_terms": []}), encoding="utf-8")
            (project / "deck_external_message_pack.json").write_text(json.dumps({"pages": []}), encoding="utf-8")
            prompt = build_external_expression_prompt(project)
            self.assertIn("audience_language_contract.json", prompt)
            self.assertIn("deck_external_message_pack.json", prompt)
            self.assertIn("customer_visible_copy.json", prompt)
            for forbidden in ("build_context", "review_package", "batch_id", "prompt_id", "production_note", "agent_trace"):
                self.assertNotIn(forbidden, prompt)


if __name__ == "__main__":
    unittest.main()
