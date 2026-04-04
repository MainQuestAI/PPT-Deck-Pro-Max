#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
REQUIRED_FIELDS = ("page_id", "severity", "type", "reason", "suggested_fix", "source_image")


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_findings(findings: list[dict]) -> None:
    if not isinstance(findings, list):
        raise SystemExit("[ERROR] review findings must be a JSON array.")
    for idx, item in enumerate(findings):
        if not isinstance(item, dict):
            raise SystemExit(f"[ERROR] review finding #{idx} must be an object.")
        for field in REQUIRED_FIELDS:
            if field not in item:
                raise SystemExit(f"[ERROR] review finding #{idx} missing field: {field}")
        if item["severity"] not in SEVERITY_ORDER:
            raise SystemExit(f"[ERROR] review finding #{idx} invalid severity: {item['severity']}")
        page_id = str(item["page_id"])
        if not page_id.startswith("slide_") and not page_id.startswith("__"):
            raise SystemExit(f"[ERROR] review finding #{idx} invalid page_id: {page_id}")


def pick_primary_route(routes: list[dict]) -> dict | None:
    if not routes:
        return None
    return sorted(
        routes,
        key=lambda route: (
            SEVERITY_ORDER.get(route.get("severity", "low"), 0),
            len(route.get("target_files", [])),
        ),
        reverse=True,
    )[0]


DIMENSION_TO_FINDING_TYPE: dict[str, str] = {
    "audience_fit": "audience_mismatch",
    "buying_reason_clarity": "buying_reason_blurry",
    "proof_strength": "proof_not_visible",
    "objection_coverage": "objection_unanswered",
    "narrative_flow": "narrative_broken",
    "commercial_ask": "commercial_ask_unclear",
}


def synthesize_scorecard_findings(scorecard: dict | None, min_score: float = 3.0) -> list[dict]:
    """Convert low-scoring commercial scorecard dimensions into routable findings."""
    if not isinstance(scorecard, dict):
        return []
    overall = scorecard.get("overall_score")
    if overall is None:
        return []
    findings: list[dict] = []
    for key, value in scorecard.get("dimensions", {}).items():
        if not isinstance(value, (int, float)) or value >= min_score:
            continue
        finding_type = DIMENSION_TO_FINDING_TYPE.get(key, "cta_weak")
        findings.append({
            "page_id": "__global__",
            "severity": "high" if value < 2 else "medium",
            "type": finding_type,
            "reason": f"商业评分维度 `{key}` 得分 {value}/5，低于最低阈值 {min_score}",
            "suggested_fix": scorecard.get("recommended_action", f"重点加强 {key} 相关页面"),
            "source_image": "",
        })
    return findings


def build_plan(project_dir: Path, findings: list[dict], rollback_map: dict, state: dict | None) -> dict:
    per_page_routes: dict[str, list[dict]] = defaultdict(list)
    by_stage: dict[str, dict] = {}
    by_severity = Counter()
    by_type = Counter()

    for item in findings:
        mapping = rollback_map.get(item["type"], rollback_map["other"])
        route = {
            "type": item["type"],
            "severity": item["severity"],
            "reason": item["reason"],
            "suggested_fix": item["suggested_fix"],
            "source_image": item["source_image"],
            "rollback_stage": mapping["rollback_stage"],
            "recommended_role": mapping["recommended_role"],
            "target_files": list(mapping["target_files"]),
            "why": mapping["why"],
            "suggested_action": mapping["suggested_action"],
        }
        page_id = item["page_id"]
        per_page_routes[page_id].append(route)
        by_severity[item["severity"]] += 1
        by_type[item["type"]] += 1

        stage_entry = by_stage.setdefault(
            mapping["rollback_stage"],
            {
                "rollback_stage": mapping["rollback_stage"],
                "recommended_role": mapping["recommended_role"],
                "target_files": [],
                "page_ids": [],
                "finding_types": [],
                "reasons": [],
                "suggested_action": mapping["suggested_action"],
            },
        )
        stage_entry["target_files"] = sorted(set(stage_entry["target_files"]) | set(mapping["target_files"]))
        stage_entry["page_ids"] = sorted(set(stage_entry["page_ids"]) | {page_id})
        stage_entry["finding_types"] = sorted(set(stage_entry["finding_types"]) | {item["type"]})
        stage_entry["reasons"].append(item["reason"])

    page_actions = []
    for page_id, routes in sorted(per_page_routes.items()):
        primary = pick_primary_route(routes)
        highest_severity = max((route["severity"] for route in routes), key=lambda s: SEVERITY_ORDER[s])
        page_actions.append(
            {
                "page_id": page_id,
                "highest_severity": highest_severity,
                "routing_status": "rollback_required",
                "primary_route": primary,
                "routes": routes,
            }
        )

    stage_actions = sorted(
        (
            {
                **entry,
                "reasons": sorted(set(entry["reasons"])),
            }
            for entry in by_stage.values()
        ),
        key=lambda item: item["rollback_stage"],
    )

    total_pages = len(state.get("pages", [])) if isinstance(state, dict) else 0
    impacted_pages = len(page_actions)

    return {
        "project_dir": str(project_dir),
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "summary": {
            "total_findings": len(findings),
            "impacted_pages": impacted_pages,
            "total_pages": total_pages,
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
        },
        "page_actions": page_actions,
        "stage_actions": stage_actions,
    }


def write_markdown(path: Path, plan: dict) -> None:
    lines = [
        "# Review Rollback Plan",
        "",
        f"- 项目目录：`{plan['project_dir']}`",
        f"- 生成时间：`{plan['generated_at']}`",
        f"- findings 总数：`{plan['summary']['total_findings']}`",
        f"- 受影响页数：`{plan['summary']['impacted_pages']}` / `{plan['summary']['total_pages']}`",
        "",
        "## 阶段级返工路由",
        "",
    ]

    if not plan["stage_actions"]:
        lines.append("- 当前没有需要回退的阶段。")
    else:
        for stage in plan["stage_actions"]:
            lines.extend(
                [
                    f"### `{stage['rollback_stage']}`",
                    "",
                    f"- 推荐角色：`{stage['recommended_role']}`",
                    f"- 目标文件：{', '.join(f'`{item}`' for item in stage['target_files'])}",
                    f"- 影响页面：{', '.join(f'`{item}`' for item in stage['page_ids'])}",
                    f"- 问题类型：{', '.join(f'`{item}`' for item in stage['finding_types'])}",
                    f"- 建议动作：{stage['suggested_action']}",
                    "",
                ]
            )

    lines.extend(["## 页面级返工说明", ""])
    if not plan["page_actions"]:
        lines.append("- 当前没有页面需要返工。")
    else:
        for action in plan["page_actions"]:
            primary = action.get("primary_route") or {}
            lines.extend(
                [
                    f"### `{action['page_id']}`",
                    "",
                    f"- 最高严重度：`{action['highest_severity']}`",
                    f"- 主要回退层：`{primary.get('rollback_stage', 'manual_review')}`",
                    f"- 推荐角色：`{primary.get('recommended_role', 'review')}`",
                    f"- 主要目标文件：{', '.join(f'`{item}`' for item in primary.get('target_files', [])) or '无'}",
                ]
            )
            for route in action.get("routes", []):
                lines.extend(
                    [
                        f"- `{route['type']}` / `{route['severity']}`：{route['reason']}",
                        f"  建议：{route['suggested_action']}",
                    ]
                )
            lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def detect_recurring_findings(state: dict, findings: list[dict], threshold: int = 3) -> list[dict]:
    """Escalate findings that recur on the same page with the same type across iterations."""
    history: dict[str, dict[str, int]] = {}
    for page in state.get("pages", []):
        page_id = page.get("page_id", "")
        for route in page.get("rollback_routes", []):
            key = route.get("type", "")
            if key:
                history.setdefault(page_id, {}).setdefault(key, 0)
                history[page_id][key] += 1

    escalated: list[dict] = []
    for item in findings:
        page_id = item.get("page_id", "")
        ftype = item.get("type", "")
        past_count = history.get(page_id, {}).get(ftype, 0)
        if past_count >= threshold:
            escalated.append({
                **item,
                "type": "other",
                "reason": f"[ESCALATED x{past_count + 1}] {item.get('reason', '')}",
                "suggested_fix": f"同一问题已连续 {past_count + 1} 轮未解决，需人工介入。原建议：{item.get('suggested_fix', '')}",
            })
        else:
            escalated.append(item)
    return escalated


def apply_plan_to_state(state: dict, plan: dict) -> dict:
    lookup = {page.get("page_id"): page for page in state.get("pages", [])}
    routed_pages = {item["page_id"]: item for item in plan.get("page_actions", [])}
    for page_id, page in lookup.items():
        action = routed_pages.get(page_id)
        if not action:
            page["rollback_stage"] = ""
            page["rollback_owner"] = ""
            page["rollback_targets"] = []
            page["rollback_reason"] = ""
            page["rollback_routes"] = []
            continue
        primary = action.get("primary_route") or {}
        page["rollback_stage"] = primary.get("rollback_stage", "")
        page["rollback_owner"] = primary.get("recommended_role", "")
        page["rollback_targets"] = list(primary.get("target_files", []))
        page["rollback_reason"] = "; ".join(route["reason"] for route in action.get("routes", []))
        page["rollback_routes"] = action.get("routes", [])
        if page.get("qa_status") == "failed" and page.get("status") == "ready":
            page["status"] = "qa_failed"
    state["review_iteration"] = state.get("review_iteration", 0) + 1
    if plan.get("page_actions"):
        state["global_status"] = "qa_failed"
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Route structured review findings into rollback stages and target files.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--review-findings", required=True)
    parser.add_argument("--commercial-scorecard")
    parser.add_argument("--min-commercial-dimension-score", type=float, default=3.0)
    parser.add_argument("--max-iterations", type=int, default=3, help="Max review iterations before global escalation")
    parser.add_argument("--recurrence-threshold", type=int, default=3, help="Same page+type recurrence count to auto-escalate")
    parser.add_argument("--state")
    parser.add_argument("--map-file")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md")
    parser.add_argument("--write-state", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    findings_path = Path(args.review_findings).expanduser().resolve()
    state_path = Path(args.state).expanduser().resolve() if args.state else project_dir / "slide_state.json"
    map_path = Path(args.map_file).expanduser().resolve() if args.map_file else Path(__file__).resolve().parent.parent / "references" / "review_rollback_map.json"
    output_json = Path(args.output_json).expanduser().resolve()
    output_md = Path(args.output_md).expanduser().resolve() if args.output_md else None

    findings = load_json(findings_path)
    validate_findings(findings if isinstance(findings, list) else [])
    rollback_map = load_json(map_path)
    state = load_json(state_path) if state_path.exists() else None
    if not isinstance(rollback_map, dict):
        raise SystemExit("[ERROR] rollback map must be an object.")

    all_findings = list(findings if isinstance(findings, list) else [])
    if args.commercial_scorecard:
        scorecard_path = Path(args.commercial_scorecard).expanduser().resolve()
        if scorecard_path.exists():
            scorecard = load_json(scorecard_path)
            if isinstance(scorecard, dict):
                all_findings.extend(synthesize_scorecard_findings(scorecard, args.min_commercial_dimension_score))

    # Convergence: check iteration count
    current_iteration = (state.get("review_iteration", 0) if isinstance(state, dict) else 0) + 1
    if current_iteration > args.max_iterations:
        print(f"[WARN] review iteration {current_iteration} exceeds max {args.max_iterations} — escalating all findings to manual_review")
        all_findings = [{**f, "type": "other", "reason": f"[ESCALATED iter={current_iteration}] {f.get('reason', '')}"} for f in all_findings]
    elif isinstance(state, dict):
        all_findings = detect_recurring_findings(state, all_findings, args.recurrence_threshold)

    plan = build_plan(project_dir, all_findings, rollback_map, state if isinstance(state, dict) else None)
    save_json(output_json, plan)
    print(f"[OK] wrote rollback plan: {output_json}")

    if output_md:
        write_markdown(output_md, plan)
        print(f"[OK] wrote rollback summary: {output_md}")

    if args.write_state and isinstance(state, dict):
        updated = apply_plan_to_state(state, plan)
        save_json(state_path, updated)
        print(f"[OK] updated state with rollback routing: {state_path}")


if __name__ == "__main__":
    main()
