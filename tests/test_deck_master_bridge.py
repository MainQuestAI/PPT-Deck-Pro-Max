from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from deck_master_bridge import BridgeError, export_deck_master_results, import_deck_master_dispatch  # noqa: E402


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc"
    b"\xff\x1f\x00\x03\x03\x02\x00\xef\xbf\xa7\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_dispatch(run_dir: Path, *, tasks: list[dict] | None = None, source_fingerprint: str | None = None) -> Path:
    path = run_dir / "generation_dispatch" / "dispatch_package.json"
    write_json(
        path,
        {
            "schema_version": "deck_generation_dispatch_package.v1",
            "run_id": "dm-run",
            "session_id": "session-1",
            "source_fingerprint": source_fingerprint or ("a" * 64),
            "tasks": tasks
            or [
                {
                    "task_id": "generation_001_slide_03",
                    "page_id": "slide_03",
                    "beat_id": "slide_03",
                    "page_title": "Proof Page",
                    "source_decision": "generate",
                }
            ],
        },
    )
    return path


def write_assembled_page(project: Path, *, page_id: str = "slide_03", batch_id: str = "batch_01") -> None:
    starter = project / "assemble" / batch_id / "starter"
    rendered = project / "rendered"
    starter.mkdir(parents=True, exist_ok=True)
    rendered.mkdir(parents=True, exist_ok=True)
    html_path = starter / "index.html"
    html_path.write_text(
        f'<!doctype html><html><body><section class="slide" data-slide="{page_id}"><h1>{page_id}</h1></section></body></html>\n',
        encoding="utf-8",
    )
    (rendered / f"{page_id}.png").write_bytes(PNG_1X1)
    write_json(
        project / "assemble" / batch_id / "assemble_manifest.json",
        {
            "batch_id": batch_id,
            "output_html": str(html_path.resolve()),
            "rendered_dir": str(rendered.resolve()),
            "pages": [{"page_id": page_id, "role": "proof"}],
        },
    )


class DeckMasterBridgeTests(unittest.TestCase):
    def test_import_preserves_dispatch_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            project = root / "ppt-project"
            dispatch = write_dispatch(run_dir)

            payload = import_deck_master_dispatch(dispatch, project)

            bridge = read_json(project / "deck_master_bridge.json")
            state = read_json(project / "slide_state.json")
            self.assertEqual("imported", payload["status"])
            self.assertEqual("dm-run", bridge["run_id"])
            self.assertEqual("session-1", bridge["session_id"])
            self.assertEqual("a" * 64, bridge["source_fingerprint"])
            self.assertEqual("generation_001_slide_03", bridge["tasks"][0]["task_id"])
            self.assertEqual("slide_03", state["pages"][0]["page_id"])

    def test_export_writes_canonical_v2_results_from_real_project_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            project = root / "ppt-project"
            dispatch = write_dispatch(run_dir)
            import_deck_master_dispatch(dispatch, project)
            write_assembled_page(project)

            payload = export_deck_master_results(project)

            self.assertEqual("exported", payload["status"])
            self.assertEqual(1, payload["result_count"])
            result_path = Path(payload["results"][0])
            result = read_json(result_path)
            self.assertEqual("deck_generation_result.v2", result["schema_version"])
            self.assertEqual("dm-run", result["run_id"])
            self.assertEqual("session-1", result["session_id"])
            self.assertEqual("generation_001_slide_03", result["task_id"])
            self.assertEqual("deck_html", result["artifacts"][0]["kind"])
            self.assertEqual("page_png", result["preview"]["kind"])
            self.assertEqual(result["artifacts"][0]["path"], result["artifact_path"])
            self.assertEqual(result["preview"]["path"], result["preview_path"])
            self.assertTrue((run_dir / result["artifact_path"]).exists())
            self.assertTrue((run_dir / result["preview_path"]).exists())
            self.assertEqual(64, len(result["preview"]["sha256"]))

    def test_export_blocks_missing_assembled_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            project = root / "ppt-project"
            dispatch = write_dispatch(run_dir)
            import_deck_master_dispatch(dispatch, project)

            with self.assertRaises(BridgeError):
                export_deck_master_results(project)

    def test_export_blocks_output_outside_deck_master_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            project = root / "ppt-project"
            dispatch = write_dispatch(run_dir)
            import_deck_master_dispatch(dispatch, project)
            write_assembled_page(project)

            with self.assertRaises(BridgeError):
                export_deck_master_results(project, root / "outside-results")

    def test_import_blocks_path_like_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            dispatch = write_dispatch(run_dir, tasks=[{"task_id": "../bad", "page_id": "slide_03"}])

            with self.assertRaises(BridgeError):
                import_deck_master_dispatch(dispatch, root / "ppt-project")

    def test_cli_import_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "dm-run"
            project = root / "ppt-project"
            dispatch = write_dispatch(run_dir)

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "deck-master-import",
                    "--input",
                    str(dispatch),
                    "--project-dir",
                    str(project),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            write_assembled_page(project)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "deck-master-export",
                    "--project-dir",
                    str(project),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual("exported", payload["status"])
            self.assertEqual(1, payload["result_count"])


if __name__ == "__main__":
    unittest.main()
