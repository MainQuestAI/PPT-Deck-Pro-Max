#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def filter_page_actions(plan: dict, role: str, page_ids: list[str]) -> list[dict]:
    page_lookup = []
    allowed_pages = set(page_ids or [])
    for action in plan.get("page_actions", []):
        primary = action.get("primary_route") or {}
        assigned_role = primary.get("recommended_role")
        current_page = action.get("page_id")
        if role == "build":
            if allowed_pages and current_page not in allowed_pages:
                continue
            page_lookup.append(action)
        else:
            if assigned_role != role:
                continue
            if allowed_pages and current_page not in allowed_pages:
                continue
            page_lookup.append(action)
    return page_lookup


def filter_stage_actions(plan: dict, role: str, page_ids: list[str]) -> list[dict]:
    allowed_pages = set(page_ids or [])
    result = []
    for action in plan.get("stage_actions", []):
        if action.get("recommended_role") != role:
            continue
        if allowed_pages and not (allowed_pages & set(action.get("page_ids", []))):
            continue
        result.append(action)
    return result


def build_brief_rework(project_dir: Path, plan: dict, page_ids: list[str]) -> str:
    page_actions = filter_page_actions(plan, "brief", page_ids)
    stage_actions = filter_stage_actions(plan, "brief", page_ids)
    lines = [
        "# Brief Rework Handoff",
        "",
        "你这轮只负责业务主线返工，不负责视觉系统和出图。",
        "",
        "## 必看输入",
        "",
        "- `deck_brief.md`",
        "- `deck_hero_pages.md`",
        "- `deck_clean_pages.md`",
        "- `review_rollback_plan.md`",
        "",
        "## 你的任务",
        "",
        "- 只处理 rollback plan 中分配给 `brief` 的问题",
        "- 优先重锁商业动作、关键页主张、证据句和 CTA",
        "- 不进入视觉风格，不进入组件系统，不直接修页面几何",
        "",
        "## 阶段级返工任务",
        "",
    ]
    if not stage_actions:
        lines.append("- 当前没有分配给 `brief` 的阶段级返工项。")
    else:
        for action in stage_actions:
            lines.extend(
                [
                    f"- 阶段：`{action['rollback_stage']}`",
                    f"  页面：{', '.join(f'`{p}`' for p in action.get('page_ids', []))}",
                    f"  必改文件：{', '.join(f'`{f}`' for f in action.get('target_files', []))}",
                    f"  建议动作：{action['suggested_action']}",
                ]
            )
    lines.extend(["", "## 页面级返工任务", ""])
    if not page_actions:
        lines.append("- 当前没有分配给 `brief` 的页面返工项。")
    else:
        for action in page_actions:
            primary = action.get("primary_route") or {}
            lines.extend(
                [
                    f"### `{action['page_id']}`",
                    f"- 主要回退层：`{primary.get('rollback_stage', '')}`",
                    f"- 目标文件：{', '.join(f'`{f}`' for f in primary.get('target_files', []))}",
                ]
            )
            for route in action.get("routes", []):
                lines.extend(
                    [
                        f"- `{route['type']}` / `{route['severity']}`：{route['reason']}",
                        f"  修订建议：{route['suggested_fix']}",
                    ]
                )
            lines.append("")
    lines.extend(
        [
            "## 完成标准",
            "",
            "- 关键页的结论句、证据句和 CTA 已重锁",
            "- `deck_clean_pages.md` 仍保持 `## 第 N 页` 分页格式",
            "- 完成后再交给 `visual` 或 `build` 角色继续后续修订",
        ]
    )
    return "\n".join(lines) + "\n"


def build_visual_rework(project_dir: Path, plan: dict, page_ids: list[str]) -> str:
    page_actions = filter_page_actions(plan, "visual", page_ids)
    stage_actions = filter_stage_actions(plan, "visual", page_ids)
    lines = [
        "# Visual Rework Handoff",
        "",
        "你这轮只负责视觉系统、组件系统、页面骨架和几何稳定性返工。",
        "",
        "## 必看输入",
        "",
        "- `deck_visual_system.md`",
        "- `deck_component_tokens.md`",
        "- `deck_theme_tokens.json`",
        "- `deck_geometry_rules.md`",
        "- `deck_page_skeletons.md`",
        "- `review_rollback_plan.md`",
        "",
        "## 你的任务",
        "",
        "- 只处理 rollback plan 中分配给 `visual` 的问题",
        "- 优先修页面骨架、组件权重、视觉层级和几何规则",
        "- 不重写业务主线，不扩写长文案",
        "",
        "## 阶段级返工任务",
        "",
    ]
    if not stage_actions:
        lines.append("- 当前没有分配给 `visual` 的阶段级返工项。")
    else:
        for action in stage_actions:
            lines.extend(
                [
                    f"- 阶段：`{action['rollback_stage']}`",
                    f"  页面：{', '.join(f'`{p}`' for p in action.get('page_ids', []))}",
                    f"  必改文件：{', '.join(f'`{f}`' for f in action.get('target_files', []))}",
                    f"  建议动作：{action['suggested_action']}",
                ]
            )
    lines.extend(["", "## 页面级返工任务", ""])
    if not page_actions:
        lines.append("- 当前没有分配给 `visual` 的页面返工项。")
    else:
        for action in page_actions:
            primary = action.get("primary_route") or {}
            lines.extend(
                [
                    f"### `{action['page_id']}`",
                    f"- 主要回退层：`{primary.get('rollback_stage', '')}`",
                    f"- 目标文件：{', '.join(f'`{f}`' for f in primary.get('target_files', []))}",
                ]
            )
            for route in action.get("routes", []):
                lines.extend(
                    [
                        f"- `{route['type']}` / `{route['severity']}`：{route['reason']}",
                        f"  修订建议：{route['suggested_fix']}",
                    ]
                )
            lines.append("")
    lines.extend(
        [
            "## 完成标准",
            "",
            "- 几何规则、骨架和视觉层级已经收紧",
            "- 不再出现线断、主体不居中、主角失焦或组件漂移",
            "- 完成后再交给 `build` 角色按页重建",
        ]
    )
    return "\n".join(lines) + "\n"


def build_build_rework(project_dir: Path, plan: dict, page_ids: list[str], context_path: Path | None) -> str:
    page_actions = filter_page_actions(plan, "build", page_ids)
    rollback_path = project_dir / "review_rollback_plan.md"
    context_text = f"`{context_path}`" if context_path else "`build_context.json`（建议先生成）"
    lines = [
        "# Build Rework Handoff",
        "",
        "你这轮只负责重建被标记的页面，不重写 brief，也不重做视觉系统定义。",
        "",
        "## 必看输入",
        "",
        "- 当前页 build context",
        "- `deck_visual_system.md`",
        "- `deck_component_tokens.md`",
        "- `deck_theme_tokens.json`",
        "- `slide_state.json`",
        "- `review_rollback_plan.md`",
        "",
        "## 你的任务",
        "",
        "- 只重建 rollback plan 中受影响的页面",
        "- 必须尊重已经修正后的 brief / visual / geometry 文件",
        "- 不自行发明新的视觉语言或页面结构",
        "",
        "## 当前 build context",
        "",
        context_text,
        "",
        "## 页面级重建任务",
        "",
    ]
    if not page_actions:
        lines.append("- 当前没有需要 `build` 重建的页面。")
    else:
        for action in page_actions:
            primary = action.get("primary_route") or {}
            lines.extend(
                [
                    f"### `{action['page_id']}`",
                    f"- 上游回退层：`{primary.get('rollback_stage', '')}`",
                    f"- 上游目标文件：{', '.join(f'`{f}`' for f in primary.get('target_files', []))}",
                ]
            )
            for route in action.get("routes", []):
                lines.extend(
                    [
                        f"- `{route['type']}` / `{route['severity']}`：{route['reason']}",
                        f"  本页重建要求：{route['suggested_fix']}",
                    ]
                )
            lines.append("")
    lines.extend(
        [
            "## 完成标准",
            "",
            f"- 严格按 `{rollback_path.name}` 中的页面问题做定向重建",
            "- 重建后回写 `slide_state.json`",
            "- 不处理未进入 rollback plan 的页面",
        ]
    )
    return "\n".join(lines) + "\n"


def build_review_rework(project_dir: Path, plan: dict, page_ids: list[str]) -> str:
    page_actions = filter_page_actions(plan, "review", page_ids)
    stage_actions = filter_stage_actions(plan, "review", page_ids)
    lines = [
        "# Review Follow-up Handoff",
        "",
        "你这轮只负责重新定性无法自动分类的问题，或验证返工后是否达标。",
        "",
        "## 必看输入",
        "",
        "- `review_rollback_plan.md`",
        "- `deck_review_findings.json`",
        "- 最新成品页截图或 montage",
        "",
        "## 你的任务",
        "",
        "- 优先处理被标记为 `manual_review` 或 `other` 的问题",
        "- 必要时重新定性 findings，让系统能把它们分派给 `brief / visual / build`",
        "",
    ]
    if stage_actions or page_actions:
        lines.extend(["## 当前需要复核的项", ""])
        for action in stage_actions:
            lines.append(f"- 阶段 `{action['rollback_stage']}`：{', '.join(action.get('reasons', []))}")
        for action in page_actions:
            lines.append(f"- 页面 `{action['page_id']}`：{'; '.join(route['reason'] for route in action.get('routes', []))}")
    else:
        lines.extend(["## 当前需要复核的项", "", "- 当前没有分配给 `review` 的返工项。"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate role-specific rework handoff from review rollback plan.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    parser.add_argument("--rollback-plan")
    parser.add_argument("--page-ids", nargs="*", default=[])
    parser.add_argument("--context-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    rollback_plan_path = Path(args.rollback_plan).expanduser().resolve() if args.rollback_plan else project_dir / "review_rollback_plan.json"
    if not rollback_plan_path.exists():
        raise SystemExit(f"[ERROR] rollback plan not found: {rollback_plan_path}")
    plan = load_json(rollback_plan_path)
    context_path = Path(args.context_path).expanduser().resolve() if args.context_path else None

    if args.role == "brief":
        text = build_brief_rework(project_dir, plan, args.page_ids)
    elif args.role == "visual":
        text = build_visual_rework(project_dir, plan, args.page_ids)
    elif args.role == "build":
        text = build_build_rework(project_dir, plan, args.page_ids, context_path)
    else:
        text = build_review_rework(project_dir, plan, args.page_ids)

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"[OK] wrote rework handoff: {output}")


if __name__ == "__main__":
    main()
