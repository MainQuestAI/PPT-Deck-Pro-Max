"""End-to-end integration test: init → preset → asset-plan → stage → qa pipeline."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from init_deck_project import init_project  # noqa: E402
from init_slide_state import build_state  # noqa: E402
from apply_deck_preset import resolve_hero_pages, apply_narrative_arc, apply_to_hero_pages  # noqa: E402
from generate_asset_plan import infer_asset_needs  # noqa: E402
from page_parser import extract_page_slices, extract_speaker_notes, extract_asset_declarations  # noqa: E402
from build_montage_and_report import (  # noqa: E402
    detect_density_issues,
    detect_missing_speaker_notes,
    detect_missing_assets,
    detect_formal_bid_issues,
    merge_issue_maps,
    apply_qa_to_state,
    is_scorecard_scaffold,
)
from route_review_findings import build_plan, detect_recurring_findings  # noqa: E402
from validate_schema import validate_project  # noqa: E402


SKILL_ROOT = Path(__file__).resolve().parents[1]


class PipelineIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.project_dir = Path(self.tmpdir)

    def test_init_creates_all_required_files(self) -> None:
        created = init_project(self.project_dir)
        self.assertIn("deck_brief.md", created)
        self.assertIn("deck_narrative_arc.md", created)
        self.assertIn("deck_asset_plan.md", created)
        self.assertIn("asset_manifest.json", created)
        self.assertIn("style_lock.json", created)
        self.assertIn("image_build_jobs.json", created)
        self.assertIn("commercial_scorecard.json", created)
        self.assertTrue((self.project_dir / "assets").is_dir())

    def test_init_state_has_review_iteration(self) -> None:
        state = build_state("test_project", 10, "pptx+html")
        self.assertEqual(state["review_iteration"], 0)
        self.assertEqual(state["production_sub_mode"], "standard_deck")
        self.assertEqual(len(state["pages"]), 10)
        self.assertEqual(state["pages"][0]["page_id"], "slide_01")

    def test_init_project_creates_formal_bid_artifacts_when_requested(self) -> None:
        created = init_project(self.project_dir, production_sub_mode="formal_bid_image_led")
        self.assertIn("page_registry.md", created)
        self.assertIn("image_generation_manifest.md", created)
        self.assertIn("actual_page_mapping.md", created)
        self.assertIn("known_issue_log.md", created)

    def test_cli_init_can_set_quick_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "init",
                    "--project-dir",
                    tmp,
                    "--pages",
                    "3",
                    "--production-mode",
                    "quick",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            brief = (Path(tmp) / "deck_brief.md").read_text(encoding="utf-8")
            self.assertIn("production_mode: quick", brief)

    def test_cli_init_can_set_formal_bid_sub_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "init",
                    "--project-dir",
                    tmp,
                    "--pages",
                    "3",
                    "--production-sub-mode",
                    "formal_bid_image_led",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            project = Path(tmp)
            brief = (project / "deck_brief.md").read_text(encoding="utf-8")
            state = json.loads((project / "slide_state.json").read_text(encoding="utf-8"))
            self.assertIn("production_sub_mode: formal_bid_image_led", brief)
            self.assertEqual(state["production_sub_mode"], "formal_bid_image_led")
            self.assertTrue((project / "page_registry.md").exists())

    def test_validate_formal_bid_sub_mode_requires_registry_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_project(project)
            state = build_state("test", 1, "html", "formal_bid_image_led")
            (project / "slide_state.json").write_text(json.dumps(state), encoding="utf-8")
            (project / "index.html").write_text("<html></html>", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "validate_deck_outputs.py"),
                    "--project-dir",
                    str(project),
                    "--output-mode",
                    "html",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("page_registry.md", result.stdout)

    def test_formal_bid_qa_detects_open_registry_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_project(project, production_sub_mode="formal_bid_image_led")
            state = build_state("test", 1, "html", "formal_bid_image_led")
            issues = detect_formal_bid_issues(project, state, "## 第 1 页\n截图占位\n")
            self.assertIn("__formal__", issues)
            self.assertIn("page_registry_empty", issues["__formal__"])
            self.assertIn("formal_placeholder_visible:截图占位", issues["__formal__"])

    def test_formal_bid_qa_accepts_closed_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_project(project, production_sub_mode="formal_bid_image_led")
            state = build_state("test", 1, "html", "formal_bid_image_led")
            (project / "page_registry.md").write_text(
                "| Source ID | Actual PPT Page | Chapter | Page Title | Status | Source Path | Approved Image | Known Issues | Owner |\n"
                "|-----------|-----------------|---------|------------|--------|-------------|----------------|--------------|-------|\n"
                "| F-01 | 1 | Front | Cover | Go | formal/F-01.md | passed/F-01.png |  | design |\n",
                encoding="utf-8",
            )
            (project / "image_generation_manifest.md").write_text(
                "| Batch ID | Source ID | Page ID | Candidate Directory | Decision | Selected Image | Decision Note | Decided At |\n"
                "|----------|-----------|---------|---------------------|----------|----------------|---------------|------------|\n"
                "| batch_01 | F-01 | slide_01 | candidates/batch_01 | Go | passed/F-01.png | ok | 2026-05-23 |\n",
                encoding="utf-8",
            )
            (project / "actual_page_mapping.md").write_text(
                "| Actual PPT Page | Source ID | Chapter | Page Title | Final Image Filename | Direct Reference | Notes |\n"
                "|-----------------|-----------|---------|------------|----------------------|------------------|-------|\n"
                "| 1 | F-01 | Front | Cover | 001_F-01_Cover.png | false |  |\n",
                encoding="utf-8",
            )
            issues = detect_formal_bid_issues(project, state, "## 第 1 页\n正式封面\n")
            self.assertEqual(issues, {})

    def test_formal_bid_qa_checks_actual_page_filename_and_ratio(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_project(project, production_sub_mode="formal_bid_image_led")
            state = build_state("test", 1, "html", "formal_bid_image_led")
            (project / "page_registry.md").write_text(
                "| Source ID | Actual PPT Page | Chapter | Page Title | Status | Source Path | Approved Image | Known Issues | Owner |\n"
                "|-----------|-----------------|---------|------------|--------|-------------|----------------|--------------|-------|\n"
                "| F-01 | 1 | Front | Cover | Go | formal/F-01.md | images/bad.png |  | design |\n",
                encoding="utf-8",
            )
            (project / "image_generation_manifest.md").write_text(
                "| Batch ID | Source ID | Page ID | Candidate Directory | Decision | Selected Image | Decision Note | Decided At |\n"
                "|----------|-----------|---------|---------------------|----------|----------------|---------------|------------|\n"
                "| batch_01 | F-01 | slide_01 | candidates/batch_01 | Go | images/bad.png | ok | 2026-05-23 |\n",
                encoding="utf-8",
            )
            image_dir = project / "images"
            image_dir.mkdir()
            Image.new("RGB", (800, 800), "white").save(image_dir / "bad.png")
            (project / "actual_page_mapping.md").write_text(
                "| Actual PPT Page | Source ID | Chapter | Page Title | Final Image Filename | Direct Reference | Notes |\n"
                "|-----------------|-----------|---------|------------|----------------------|------------------|-------|\n"
                "| 1 | F-01 | Front | Cover | images/bad.png | false |  |\n",
                encoding="utf-8",
            )
            issues = detect_formal_bid_issues(project, state, "## 第 1 页\n正式封面\n")
            self.assertIn("actual_page_filename_order:F-01:images/bad.png", issues["__formal__"])
            self.assertIn("formal_image_ratio:F-01:800x800", issues["__formal__"])

    def test_cli_assemble_formal_images_copies_go_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_project(project, production_sub_mode="formal_bid_image_led")
            passed = project / "passed"
            passed.mkdir()
            (passed / "F-01.png").write_bytes(b"fake-image")
            (project / "page_registry.md").write_text(
                "| Source ID | Actual PPT Page | Chapter | Page Title | Status | Source Path | Approved Image | Known Issues | Owner |\n"
                "|-----------|-----------------|---------|------------|--------|-------------|----------------|--------------|-------|\n"
                "| F-01 | 1 | Front | Cover | Go | formal/F-01.md | passed/F-01.png |  | design |\n",
                encoding="utf-8",
            )
            (project / "actual_page_mapping.md").write_text(
                "| Actual PPT Page | Source ID | Chapter | Page Title | Final Image Filename | Direct Reference | Notes |\n"
                "|-----------------|-----------|---------|------------|----------------------|------------------|-------|\n"
                "| 1 | F-01 | Front | Cover | 001_F-01_Cover.png | false |  |\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "run_deck_pipeline.py"),
                    "assemble-formal-images",
                    "--project-dir",
                    str(project),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertTrue((project / "actual_page_images" / "001_F-01_Cover.png").exists())
            manifest = json.loads((project / "actual_page_assembly_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["copied"]), 1)

    def test_preset_generates_narrative_arc(self) -> None:
        init_project(self.project_dir)
        state = build_state("test", 10, "pptx+html")
        (self.project_dir / "slide_state.json").write_text(json.dumps(state), encoding="utf-8")
        preset = json.loads((SKILL_ROOT / "assets" / "presets" / "solution_deck.json").read_text(encoding="utf-8"))
        apply_narrative_arc(self.project_dir, preset, state)
        arc_path = self.project_dir / "deck_narrative_arc.md"
        self.assertTrue(arc_path.exists())
        content = arc_path.read_text(encoding="utf-8")
        self.assertIn("setup", content)
        self.assertIn("tension", content)
        self.assertIn("action", content)

    def test_asset_plan_infers_needs_for_hero_proof(self) -> None:
        state = build_state("test", 5, "pptx+html")
        state["pages"][2]["role"] = "hero_proof"
        clean_text = "## 第 1 页\n封面\n\n## 第 2 页\n诊断\n\n## 第 3 页\n样例\n\n## 第 4 页\n系统\n\n## 第 5 页\nCTA\n"
        needs = infer_asset_needs(clean_text, state)
        proof_needs = [n for n in needs if n["page_id"] == "slide_03"]
        self.assertTrue(len(proof_needs) > 0)
        self.assertEqual(proof_needs[0]["priority"], "high")

    def test_asset_declarations_parsed_from_clean_pages(self) -> None:
        text = "## 第 5 页\n\n> 配图: id=dash | desc=仪表盘 | frame=macbook\n\n文案\n"
        assets = extract_asset_declarations(text)
        self.assertIn(5, assets)
        self.assertEqual(assets[5][0]["id"], "dash")
        self.assertEqual(assets[5][0]["frame"], "macbook")

    def test_speaker_notes_parsed(self) -> None:
        text = "## 第 1 页\n\n> 演讲备注: 核心话术是XYZ\n\n## 第 2 页\n内容\n"
        notes = extract_speaker_notes(text)
        self.assertIn(1, notes)
        self.assertNotIn(2, notes)

    def test_qa_detects_missing_assets_on_proof_pages(self) -> None:
        state = build_state("test", 3, "pptx+html")
        state["pages"][1]["role"] = "hero_proof"
        manifest = {"assets": []}
        issues = detect_missing_assets(state, manifest)
        self.assertIn("slide_02", issues)
        self.assertIn("asset_missing", issues["slide_02"])

    def test_qa_detects_missing_speaker_notes_on_hero(self) -> None:
        state = build_state("test", 3, "pptx+html")
        state["pages"][0]["role"] = "hero_cover"
        clean_text = "## 第 1 页\n封面\n\n## 第 2 页\n内容\n\n## 第 3 页\n结尾\n"
        issues = detect_missing_speaker_notes(state, clean_text)
        self.assertIn("slide_01", issues)

    def test_scorecard_scaffold_is_recognized(self) -> None:
        scaffold = {"overall_score": None, "dimensions": {"audience_fit": None}}
        self.assertTrue(is_scorecard_scaffold(scaffold))
        filled = {"overall_score": 4.0, "dimensions": {"audience_fit": 4}}
        self.assertFalse(is_scorecard_scaffold(filled))

    def test_review_convergence_escalates_recurring_findings(self) -> None:
        state = build_state("test", 2, "pptx+html")
        # Simulate 3 past iterations with same finding type on slide_01
        state["pages"][0]["rollback_routes"] = [
            {"type": "geometry_broken"},
            {"type": "geometry_broken"},
            {"type": "geometry_broken"},
        ]
        findings = [{
            "page_id": "slide_01",
            "severity": "high",
            "type": "geometry_broken",
            "reason": "连线断了",
            "suggested_fix": "修锚点",
            "source_image": "",
        }]
        result = detect_recurring_findings(state, findings, threshold=3)
        self.assertEqual(result[0]["type"], "other")
        self.assertIn("ESCALATED", result[0]["reason"])

    def test_full_qa_pipeline_no_crash(self) -> None:
        state = build_state("test", 3, "pptx+html")
        clean_text = "## 第 1 页\n封面\n\n## 第 2 页\n内容\n\n## 第 3 页\n结尾\n"
        issues = merge_issue_maps(
            detect_density_issues(state, clean_text, 700, 1000),
            detect_missing_speaker_notes(state, clean_text),
            detect_missing_assets(state, {"assets": []}),
        )
        updated = apply_qa_to_state(state, issues)
        self.assertIn("global_status", updated)

    def test_schema_validation_passes_on_fresh_init(self) -> None:
        init_project(self.project_dir)
        state = build_state("test", 3, "pptx+html")
        (self.project_dir / "slide_state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Scaffold files (review_rollback_plan, review_package) have intentionally
        # empty project_dir; exclude them from strict schema validation on fresh init.
        scaffold_files = {"review_rollback_plan.json", "review_package.json", "commercial_scorecard.json"}
        results = validate_project(self.project_dir, strict=False)
        for filename, errors in results.items():
            if filename in scaffold_files:
                continue
            self.fail(f"schema validation failed for {filename}: {errors}")


if __name__ == "__main__":
    unittest.main()
