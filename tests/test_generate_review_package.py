from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_review_package import find_latest_matching  # noqa: E402


class GenerateReviewPackageTests(unittest.TestCase):
    def test_find_latest_matching_ignores_hidden_and_office_lock_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "deck_v1.pptx"
            lock = root / ".~deck_v2.pptx"
            hidden = root / ".deck_hidden.pptx"
            good.write_text("ok", encoding="utf-8")
            lock.write_text("lock", encoding="utf-8")
            hidden.write_text("hidden", encoding="utf-8")
            found = find_latest_matching([root], ["*.pptx"])
            self.assertEqual(found, good)


if __name__ == "__main__":
    unittest.main()
