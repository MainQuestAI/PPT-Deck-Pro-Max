#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_governance import validate_content_governance


CORE_ARTIFACTS = [
    "deck_brief.md",
    "deck_vibe_brief.md",
    "deck_narrative_arc.md",
    "deck_hero_pages.md",
    "deck_layout_v1.md",
    "deck_clean_pages.md",
    "deck_visual_composition.md",
    "deck_visual_system.md",
    "deck_component_tokens.md",
    "deck_theme_tokens.json",
    "deck_asset_plan.md",
    "asset_manifest.json",
    "slide_state.json",
]

REVIEW_ARTIFACTS = [
    "montage.png",
    "review_package.json",
    "deck_review_report.md",
    "deck_review_findings.json",
    "commercial_scorecard.json",
    "review_rollback_plan.json",
    "review_rollback_plan.md",
]

FORMAL_BID_IMAGE_LED_ARTIFACTS = [
    "page_registry.md",
    "image_generation_manifest.md",
    "actual_page_mapping.md",
    "known_issue_log.md",
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def infer_production_sub_mode(project_dir: Path) -> str:
    state = load_json(project_dir / "slide_state.json")
    mode = state.get("production_sub_mode")
    if mode:
        return str(mode)

    brief_path = project_dir / "deck_brief.md"
    if brief_path.exists():
        for line in brief_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("production_sub_mode:"):
                return line.split(":", 1)[1].strip() or "standard_deck"

    return "standard_deck"


def find_artifact(project_dir: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(project_dir.glob(pattern))
        for match in matches:
            if match.is_file() and not match.name.startswith(".") and not match.name.startswith("~$"):
                return match
    for child in sorted(project_dir.iterdir()):
        if not child.is_dir():
            continue
        search_dirs: list[Path] = []
        if child.name.startswith("build_") or child.name.startswith("dist") or child.name.startswith("output"):
            search_dirs.append(child)
        elif child.name == "assemble":
            for batch_dir in sorted(child.iterdir()):
                starter = batch_dir / "starter"
                if starter.is_dir():
                    search_dirs.append(starter)
        if not search_dirs:
            continue
        for search_dir in search_dirs:
            for pattern in patterns:
                matches = sorted(search_dir.glob(pattern))
                for match in matches:
                    if match.is_file() and not match.name.startswith(".") and not match.name.startswith("~$"):
                        return match
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required deck outputs exist.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--output-mode", default="pptx+html", choices=["pptx", "html", "pptx+html"])
    parser.add_argument("--require-review", action="store_true", help="Also check review artifacts")
    parser.add_argument("--expert-mode", action="store_true", help="Also check expert interview artifacts")
    parser.add_argument("--content-governance", action="store_true", help="Also check source digest, claim map, capacity plan, and gap gate")
    parser.add_argument("--production-sub-mode", choices=["standard_deck", "formal_bid_image_led"], help="Override inferred production sub-mode")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    production_sub_mode = args.production_sub_mode or infer_production_sub_mode(project_dir)

    missing = [name for name in CORE_ARTIFACTS if not (project_dir / name).exists()]

    if args.output_mode in {"pptx", "pptx+html"}:
        if not find_artifact(project_dir, ["*.pptx"]):
            missing.append("*.pptx (no PPTX file found)")
    if args.output_mode in {"html", "pptx+html"}:
        if not find_artifact(project_dir, ["*.html", "index.html"]):
            missing.append("*.html (no HTML file found)")

    if args.require_review:
        missing.extend(name for name in REVIEW_ARTIFACTS if not (project_dir / name).exists())

    if production_sub_mode == "formal_bid_image_led":
        missing.extend(name for name in FORMAL_BID_IMAGE_LED_ARTIFACTS if not (project_dir / name).exists())

    if args.content_governance:
        governance_errors, _ = validate_content_governance(project_dir)
        missing.extend(f"content_governance:{err}" for err in governance_errors)

    if getattr(args, "expert_mode", False):
        expert_artifacts = ["deck_expert_context.md", "interview_session.json"]
        missing.extend(name for name in expert_artifacts if not (project_dir / name).exists())

        # State-based validation: check session quality, not just file existence
        session_path = project_dir / "interview_session.json"
        if session_path.exists():
            try:
                session = json.loads(session_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                session = {}

            session_state = session.get("state", "")
            if session_state != "finalized":
                missing.append(f"interview_session.state must be 'finalized' (current: '{session_state}')")

            redaction_pending = session.get("redaction_pending", 0)
            if redaction_pending > 0:
                missing.append(f"interview_session has {redaction_pending} unresolved redaction(s)")

            coverage = session.get("coverage", {})
            fill_rate = coverage.get("hero_gap_fill_rate", 0)
            target = coverage.get("target_fill_rate", 0.8)
            if fill_rate < target:
                missing.append(f"hero_gap_fill_rate {fill_rate:.0%} < target {target:.0%}")

    if missing:
        print("[ERROR] missing outputs:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)

    print("[OK] required outputs exist")


if __name__ == "__main__":
    main()
