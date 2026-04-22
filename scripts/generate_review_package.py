#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PAGE_IMAGE_PATTERNS = [
    re.compile(r"slide[_-](\d+)\.(png|jpg|jpeg)$", re.I),
]


def find_first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def find_candidate_dirs(project_dir: Path) -> list[Path]:
    candidates = [project_dir]
    for child in sorted(project_dir.iterdir()) if project_dir.exists() else []:
        if child.is_dir() and (
            child.name.startswith("build_")
            or child.name.startswith("dist")
            or child.name.startswith("output")
            or child.name.endswith("_build")
        ):
            candidates.append(child)
    return candidates


def is_usable_artifact(path: Path) -> bool:
    name = path.name
    if name.startswith("."):
        return False
    if name.startswith(".~") or name.startswith("~$"):
        return False
    if name.endswith(".tmp") or name.endswith(".bak"):
        return False
    return path.is_file()


def find_latest_matching(paths: list[Path], patterns: list[str]) -> Path | None:
    matches: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        for pattern in patterns:
            matches.extend(path for path in base.glob(pattern) if is_usable_artifact(path))
    if not matches:
        return None
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def infer_page_id(image_path: Path) -> str | None:
    for pattern in PAGE_IMAGE_PATTERNS:
        match = pattern.search(image_path.name)
        if match:
            return f"slide_{int(match.group(1)):02d}"
    return None


def list_page_images(rendered_dir: Path) -> list[dict]:
    if not rendered_dir.exists():
        return []
    items: list[dict] = []
    for image in sorted(rendered_dir.iterdir()):
        if not image.is_file():
            continue
        page_id = infer_page_id(image)
        if page_id:
            items.append({"page_id": page_id, "image_path": str(image.resolve())})
    items.sort(key=lambda x: int(x["page_id"].split("_")[1]))
    return items


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def infer_production_mode(project_dir: Path, interview_session: dict, interview_preparation: dict) -> str:
    brief_path = project_dir / "deck_brief.md"
    brief_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    if "production_mode: quick" in brief_text:
        return "quick"
    return "expert"


def summarize_expert_mode(project_dir: Path, interview_session: dict, interview_preparation: dict) -> dict:
    expert_context_path = project_dir / "deck_expert_context.md"
    production_mode = infer_production_mode(project_dir, interview_session, interview_preparation)
    coverage = interview_session.get("coverage", {}) if isinstance(interview_session, dict) else {}
    claims = interview_preparation.get("claims", []) if isinstance(interview_preparation, dict) else []
    hero_claims = [claim for claim in claims if claim.get("is_hero")]
    enriched_claims = [
        claim for claim in claims
        if any(gap.get("status") == "filled" for gap in claim.get("gaps", []))
    ]
    thin_hero_claim_ids = [
        claim.get("claim_id", "unknown") for claim in hero_claims if claim.get("richness_score", 0) < 3
    ]

    session_state = interview_session.get("state", "") if isinstance(interview_session, dict) else ""
    redaction_pending = interview_session.get("redaction_pending", 0) if isinstance(interview_session, dict) else 0
    fill_rate = coverage.get("hero_gap_fill_rate", 0)
    target_fill_rate = coverage.get("target_fill_rate", 0.8)
    coverage_target_met = fill_rate >= target_fill_rate
    finalized = session_state == "finalized"
    expert_context_ready = expert_context_path.exists()
    review_ready = finalized and redaction_pending == 0 and coverage_target_met and expert_context_ready

    issues: list[str] = []
    if production_mode == "expert":
        if not claims:
            issues.append("interview_preparation_missing_or_empty")
        if session_state != "finalized":
            issues.append(f"interview_session_not_finalized:{session_state or 'missing'}")
        if redaction_pending > 0:
            issues.append(f"redaction_pending:{redaction_pending}")
        if not expert_context_ready:
            issues.append("deck_expert_context_missing")
        if not coverage_target_met:
            issues.append(f"coverage_below_target:{fill_rate:.0%}<{target_fill_rate:.0%}")
        if thin_hero_claim_ids:
            issues.append("thin_hero_claims:" + ",".join(thin_hero_claim_ids[:8]))

    return {
        "production_mode": production_mode,
        "enabled": production_mode == "expert",
        "review_ready": review_ready,
        "gating_status": {
            "session_state": session_state or "missing",
            "finalized": finalized,
            "redaction_pending": redaction_pending,
            "expert_context_ready": expert_context_ready,
            "coverage_target_met": coverage_target_met,
        },
        "coverage": {
            "hero_claims_total": coverage.get("hero_claims_total", len(hero_claims)),
            "hero_claims_enriched": coverage.get("hero_claims_enriched", len([c for c in enriched_claims if c.get("is_hero")])),
            "hero_gap_fill_rate": fill_rate,
            "target_fill_rate": target_fill_rate,
        },
        "claim_summary": {
            "total_claims": len(claims),
            "hero_claims": len(hero_claims),
            "enriched_claims": len(enriched_claims),
            "thin_hero_claim_ids": thin_hero_claim_ids,
        },
        "review_focus": [
            "确认 deck_expert_context.md 中的专家信息是否真正进入最终页面",
            "确认 interview_session.json 已 finalized，且 redaction_pending 为 0",
            "优先检查 hero claims 的 richness 是否足以支撑 proof 和 CTA",
        ] if production_mode == "expert" else [],
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a structured review package for multimodal deck review.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--output")
    parser.add_argument("--rendered-dir")
    parser.add_argument("--montage")
    parser.add_argument("--deck-path")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else project_dir / "review_package.json"
    candidate_dirs = find_candidate_dirs(project_dir)
    rendered_dir = (
        Path(args.rendered_dir).expanduser().resolve()
        if args.rendered_dir
        else find_first_existing([base / "rendered" for base in candidate_dirs]) or (project_dir / "rendered")
    )
    montage = (
        Path(args.montage).expanduser().resolve()
        if args.montage
        else find_latest_matching(candidate_dirs, ["montage*.png", "*montage*.png"])
    )
    deck_pptx = find_latest_matching(candidate_dirs, ["deck*.pptx", "*deck*.pptx", "*.pptx"])
    deck_html = find_latest_matching(candidate_dirs, ["deck*.html", "*deck*.html", "index.html", "*.html"])
    deck_path = (
        Path(args.deck_path).expanduser().resolve()
        if args.deck_path
        else (deck_pptx or deck_html)
    )

    skill_root = Path(__file__).resolve().parent.parent
    schema_path = skill_root / "references" / "review_findings.schema.json"
    scorecard_schema_path = skill_root / "references" / "commercial_scorecard.schema.json"
    interview_session = load_json(project_dir / "interview_session.json")
    interview_preparation = load_json(project_dir / "interview_preparation.json")

    payload = {
        "project_dir": str(project_dir),
        "review_order": [
            "先看 montage.png 做全局节奏与重心判断",
            "再看页级 PNG 检查对齐、几何关系、留白与主角性",
            "最后回看 deck_clean_pages.md、slide_state.json、视觉系统文件，以及 expert gate 摘要",
        ],
        "artifacts": {
            "deck": str(deck_path) if deck_path and deck_path.exists() else "",
            "deck_pptx": str(deck_pptx) if deck_pptx and deck_pptx.exists() else "",
            "deck_html": str(deck_html) if deck_html and deck_html.exists() else "",
            "montage": str(montage) if montage and montage.exists() else "",
            "rendered_dir": str(rendered_dir) if rendered_dir.exists() else "",
            "clean_pages": str((project_dir / "deck_clean_pages.md").resolve()) if (project_dir / "deck_clean_pages.md").exists() else "",
            "slide_state": str((project_dir / "slide_state.json").resolve()) if (project_dir / "slide_state.json").exists() else "",
            "visual_system": str((project_dir / "deck_visual_system.md").resolve()) if (project_dir / "deck_visual_system.md").exists() else "",
            "component_tokens": str((project_dir / "deck_component_tokens.md").resolve()) if (project_dir / "deck_component_tokens.md").exists() else "",
            "expert_context": str((project_dir / "deck_expert_context.md").resolve()) if (project_dir / "deck_expert_context.md").exists() else "",
            "interview_session": str((project_dir / "interview_session.json").resolve()) if (project_dir / "interview_session.json").exists() else "",
            "interview_preparation": str((project_dir / "interview_preparation.json").resolve()) if (project_dir / "interview_preparation.json").exists() else "",
        },
        "expert_mode_summary": summarize_expert_mode(project_dir, interview_session, interview_preparation),
        "page_images": list_page_images(rendered_dir),
        "required_output": {
            "schema": str(schema_path.resolve()),
            "output_file": str((project_dir / "deck_review_findings.json").resolve()),
            "commercial_scorecard_schema": str(scorecard_schema_path.resolve()),
            "commercial_scorecard_file": str((project_dir / "commercial_scorecard.json").resolve()),
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
