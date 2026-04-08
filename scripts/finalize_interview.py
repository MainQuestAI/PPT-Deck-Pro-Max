#!/usr/bin/env python3
"""Finalize Expert Interview: validate redaction status and produce deck_expert_context.md.

This script implements Step 1.6 (Redaction Review gate):
1. Read interview_session.json — verify state is completed/aborted
2. Check all redaction decisions are resolved (no needs_redaction remaining)
3. Generate the final deck_expert_context.md from confirmed insights only
4. Optionally extract brief_feedback if the interview revealed Brief changes
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Valid state transitions for interview_session.state
VALID_TRANSITIONS: dict[str, set[str]] = {
    "preparing": {"in_progress", "aborted"},
    "in_progress": {"completed", "aborted"},
    "completed": {"finalized"},
    "aborted": {"finalized"},
    "finalized": set(),  # terminal
}

ALL_STATES = set(VALID_TRANSITIONS.keys())


def validate_state_transition(current: str, target: str) -> str | None:
    """Return an error message if the transition is illegal, or None if valid."""
    if current not in ALL_STATES:
        return f"unknown current state '{current}'"
    if target not in ALL_STATES:
        return f"unknown target state '{target}'"
    if target not in VALID_TRANSITIONS[current]:
        allowed = ", ".join(sorted(VALID_TRANSITIONS[current])) or "(none — terminal)"
        return f"illegal transition '{current}' → '{target}'; allowed: {allowed}"
    return None


def validate_session(session: dict) -> list[str]:
    """Check that the interview session is in a finalizable state."""
    errors = []
    state = session.get("state", "")
    if state not in ("completed", "aborted"):
        errors.append(f"session state is '{state}', expected 'completed' or 'aborted'")

    # Verify the transition to 'finalized' is legal
    transition_err = validate_state_transition(state, "finalized")
    if transition_err and state in ALL_STATES:
        errors.append(transition_err)

    redaction_pending = session.get("redaction_pending", 0)
    if redaction_pending > 0:
        errors.append(f"{redaction_pending} redaction decision(s) still pending")

    return errors


def compute_coverage(session: dict) -> dict:
    """Extract coverage metrics from session."""
    coverage = session.get("coverage", {})
    return {
        "hero_claims_total": coverage.get("hero_claims_total", 0),
        "hero_claims_enriched": coverage.get("hero_claims_enriched", 0),
        "hero_gap_fill_rate": coverage.get("hero_gap_fill_rate", 0),
        "target_fill_rate": coverage.get("target_fill_rate", 0.8),
    }


def generate_expert_context(session: dict, preparation: dict) -> str:
    """Generate the final deck_expert_context.md from session + preparation data."""
    coverage = compute_coverage(session)
    claims = preparation.get("claims", [])

    lines = [
        "# Expert Context",
        "",
        "## 元数据",
        f"- session_id: {session.get('session_id', 'unknown')}",
        f"- production_mode: expert",
        f"- state: {session.get('state', 'unknown')}",
        f"- hero_gap_fill_rate: {coverage['hero_gap_fill_rate']:.0%}",
        f"- total_claims: {len(claims)}",
        f"- insights_collected: {session.get('insights_collected', 0)}",
        f"- redaction_status: all_clear",
        "",
        "## Claims",
        "",
    ]

    enriched_claims = []
    skipped_claims = []

    for claim in claims:
        richness = claim.get("richness_score", 0)
        gaps = claim.get("gaps", [])
        filled_gaps = [g for g in gaps if g.get("status") == "filled"]
        open_gaps = [g for g in gaps if g.get("status") in ("open", "asked")]
        skipped_gaps = [g for g in gaps if g.get("status") == "skipped"]

        if filled_gaps or richness >= 2:
            enriched_claims.append(claim)
            lines.extend([
                f"### {claim['claim_id']}",
                f"主题：{claim.get('claim_text', '')}",
                f"类型：{claim.get('claim_type', '')}",
                f"Beat 倾向：{claim.get('beat_hint', 'N/A')}",
                f"Richness：{richness}/5",
                "",
            ])
            if filled_gaps:
                lines.append("已填补缺口：")
                for g in filled_gaps:
                    lines.append(f"- [{g['gap_type']}] {g.get('desc', '')}")
                lines.append("")
            if open_gaps or skipped_gaps:
                lines.append("未覆盖缺口：")
                for g in open_gaps + skipped_gaps:
                    lines.append(f"- [{g['gap_type']}] {g.get('desc', '')} (status: {g.get('status', '')})")
                lines.append("")
            lines.append(f"页面分配：待 Narrative Arc 决定")
            lines.append("")
            lines.append("---")
            lines.append("")
        else:
            skipped_claims.append(claim)

    if skipped_claims:
        lines.extend([
            "## 未覆盖话题 (skipped / ai_inferred)",
            "",
        ])
        for claim in skipped_claims:
            lines.append(f"- {claim['claim_id']}: {claim.get('claim_text', '')} (richness: {claim.get('richness_score', 0)}/5)")
        lines.append("")

    # Brief feedback section (placeholder — populated by AI at runtime)
    lines.extend([
        "## Brief Feedback",
        "",
        "（如有 Interview 中发现的 Brief 修正建议，记录在此。用户在 Step 1.6 审批时决定是否更新 Brief。）",
        "",
    ])

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize Expert Interview and generate deck_expert_context.md.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--session", help="Path to interview_session.json")
    parser.add_argument("--preparation", help="Path to interview_preparation.json")
    parser.add_argument("--output", help="Path to deck_expert_context.md")
    parser.add_argument("--force", action="store_true", help="Proceed even if validation fails (with warnings)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    session_path = Path(args.session or project_dir / "interview_session.json").expanduser().resolve()
    preparation_path = Path(args.preparation or project_dir / "interview_preparation.json").expanduser().resolve()
    output_path = Path(args.output or project_dir / "deck_expert_context.md").expanduser().resolve()

    session = load_json(session_path)
    preparation = load_json(preparation_path)

    # Validate
    errors = validate_session(session)
    if errors and not args.force:
        print("[ERROR] Interview session not ready for finalization:")
        for err in errors:
            print(f"  - {err}")
        raise SystemExit(1)
    elif errors:
        print("[WARN] Proceeding with force despite validation errors:")
        for err in errors:
            print(f"  - {err}")

    # Generate final artifact
    content = generate_expert_context(session, preparation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[OK] wrote {output_path}")

    # Update session state with transition validation
    old_state = session.get("state", "")
    transition_err = validate_state_transition(old_state, "finalized")
    if transition_err and not args.force:
        print(f"[ERROR] {transition_err}")
        raise SystemExit(1)
    session["state"] = "finalized"
    save_json(session_path, session)
    print(f"[OK] session state {old_state} → finalized")

    # Summary
    coverage = compute_coverage(session)
    print(f"[OK] hero gap fill rate: {coverage['hero_gap_fill_rate']:.0%}")
    print(f"[OK] insights collected: {session.get('insights_collected', 0)}")


if __name__ == "__main__":
    main()
