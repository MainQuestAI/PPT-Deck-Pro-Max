#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_GLOBAL_STATUS = {"briefing", "designing", "building", "awaiting_review", "reworking", "qa_failed", "ready"}
ALLOWED_PAGE_STATUS = {"pending", "awaiting_visual_lock", "building", "awaiting_review", "reworking", "ready", "qa_failed", "done"}
ALLOWED_QA_STATUS = {"pending", "passed", "failed"}
ALLOWED_VISUAL_STATUS = {"pending", "locked", "needs_rework"}


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def find_page(state: dict, page_id: str) -> dict:
    for page in state.get("pages", []):
        if page.get("page_id") == page_id:
            return page
    raise SystemExit(f"[ERROR] page not found: {page_id}")


def validate_choice(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise SystemExit(f"[ERROR] invalid {name}: {value}. Allowed: {allowed_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update slide_state.json deterministically.")
    parser.add_argument("--state", required=True)
    parser.add_argument("--global-status")
    parser.add_argument("--visual-locked", choices=["true", "false"])
    parser.add_argument("--page-id")
    parser.add_argument("--role")
    parser.add_argument("--status")
    parser.add_argument("--qa-status")
    parser.add_argument("--qa-reason")
    parser.add_argument("--visual-status")
    parser.add_argument("--rollback-stage")
    parser.add_argument("--rollback-owner")
    parser.add_argument("--rollback-target", action="append", default=[])
    parser.add_argument("--rollback-reason")
    parser.add_argument("--clear-rollback", action="store_true")
    parser.add_argument("--content-hash")
    parser.add_argument("--add-component", action="append", default=[])
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = load_state(state_path)

    if args.global_status:
        validate_choice("global-status", args.global_status, ALLOWED_GLOBAL_STATUS)
        state["global_status"] = args.global_status
    if args.visual_locked:
        state["visual_locked"] = args.visual_locked == "true"

    if args.page_id:
        page = find_page(state, args.page_id)
        if args.role:
            page["role"] = args.role
        if args.status:
            validate_choice("status", args.status, ALLOWED_PAGE_STATUS)
            page["status"] = args.status
        if args.qa_status:
            validate_choice("qa-status", args.qa_status, ALLOWED_QA_STATUS)
            page["qa_status"] = args.qa_status
        if args.qa_reason is not None:
            page["qa_reason"] = args.qa_reason
        if args.visual_status:
            validate_choice("visual-status", args.visual_status, ALLOWED_VISUAL_STATUS)
            page["visual_status"] = args.visual_status
        if args.clear_rollback:
            page["rollback_stage"] = ""
            page["rollback_owner"] = ""
            page["rollback_targets"] = []
            page["rollback_reason"] = ""
            page["rollback_routes"] = []
        if args.rollback_stage is not None:
            page["rollback_stage"] = args.rollback_stage
        if args.rollback_owner is not None:
            page["rollback_owner"] = args.rollback_owner
        if args.rollback_reason is not None:
            page["rollback_reason"] = args.rollback_reason
        if args.rollback_target:
            current_targets = set(page.get("rollback_targets", []))
            current_targets.update(args.rollback_target)
            page["rollback_targets"] = sorted(current_targets)
        if args.content_hash is not None:
            page["content_hash"] = args.content_hash
        if args.add_component:
            current = set(page.get("css_components_used", []))
            current.update(args.add_component)
            page["css_components_used"] = sorted(current)

    save_state(state_path, state)
    print(f"[OK] updated {state_path}")


if __name__ == "__main__":
    main()
