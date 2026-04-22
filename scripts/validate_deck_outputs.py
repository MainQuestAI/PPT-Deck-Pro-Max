#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()

    missing = [name for name in CORE_ARTIFACTS if not (project_dir / name).exists()]

    if args.output_mode in {"pptx", "pptx+html"}:
        if not find_artifact(project_dir, ["*.pptx"]):
            missing.append("*.pptx (no PPTX file found)")
    if args.output_mode in {"html", "pptx+html"}:
        if not find_artifact(project_dir, ["*.html", "index.html"]):
            missing.append("*.html (no HTML file found)")

    if args.require_review:
        missing.extend(name for name in REVIEW_ARTIFACTS if not (project_dir / name).exists())

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
