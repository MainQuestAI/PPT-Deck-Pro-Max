#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_brief_prompt(project_dir: Path) -> str:
    rollback_plan = project_dir / "review_rollback_plan.md"
    return "\n".join(
        [
            "# Brief AI Handoff",
            "",
            "请使用业务语言完成 `deck_brief.md`。",
            "",
            "## 必看输入",
            "",
            "- `deck_brief.md`",
            "",
            "## 输出要求",
            "",
            "- 锁定产品主语、产品定位、目标受众、第一购买理由、最强差异化、最强证据、首单入口、最终 CTA",
            "- 如果 `deck_narrative_arc.md` 已存在，后续页面文稿必须尊重 beat 序列和过渡逻辑",
            "- 不进入视觉系统，不进入逐页排版",
            "- 如果需要补建后续页面文稿约束，请统一要求 `deck_clean_pages.md` 使用 `## 第 N 页` 作为分页符，不得改成纯加粗标题或自由格式",
            f"- 如果 `{rollback_plan.name}` 已存在，优先处理其中分配给 `brief` 的返工项",
            "",
            "## 当前文件内容",
            "",
            "```md",
            read(project_dir / "deck_brief.md"),
            "```",
            "",
            "## 可选返工计划",
            "",
            f"`{rollback_plan}`",
            "",
            "建议调用：无强制下游技能，以业务判断为主。",
        ]
    )


def build_visual_prompt(project_dir: Path) -> str:
    rollback_plan = project_dir / "review_rollback_plan.md"
    return "\n".join(
        [
            "# Visual System AI Handoff",
            "",
            "请锁定视觉世界观、页面原型、组件系统和 token。",
            "",
            "## 必看输入",
            "",
            "- `deck_brief.md`",
            "- `deck_vibe_brief.md`",
            "- `deck_hero_pages.md`",
            "- `deck_clean_pages.md`",
            "",
            "## 输出要求",
            "",
            "- 生成 `deck_visual_system.md`、`deck_component_tokens.md`、`deck_theme_tokens.json`",
            "- 不重写业务主线",
            "- 不引入野生风格",
            "- 不改写 `deck_clean_pages.md` 的分页规则；如果需要补充约束，统一使用 `## 第 N 页` 作为分页符",
            f"- 如果 `{rollback_plan.name}` 已存在，优先处理其中分配给 `visual` 的返工项，先修骨架/组件/几何规则，再回到出图",
            "",
            "## 可选返工计划",
            "",
            f"`{rollback_plan}`",
            "",
            "建议调用：`$ui-ux-pro-max`，必要时配合 `$frontend-design`。",
        ]
    )


def build_build_prompt(project_dir: Path, page_ids: list[str], context_path: Path | None = None) -> str:
    state = json.loads(read(project_dir / "slide_state.json") or "{}")
    output_mode = state.get("output_mode", "pptx+html")
    recommended = "`$slides`"
    if output_mode == "html":
        recommended = "`$frontend-design`"
    elif output_mode == "pptx+html":
        recommended = "`$slides` + `$frontend-design`"
    context_path = context_path or (project_dir / "build_context.json")
    rollback_plan = project_dir / "review_rollback_plan.md"
    return "\n".join(
        [
            "# Build AI Handoff",
            "",
            f"**你是视觉施工员，不是排版工人。** 请根据 visual_composition 的视觉规格实现当前页面：{', '.join(page_ids) if page_ids else '未指定'}。",
            "",
            "每一页必须有视觉主角（图表/icon 链/大数字/架构图）。纯文字卡片不是合格输出。",
            "",
            "## 必看输入",
            "",
            "- `deck_visual_composition.md`（**首先看这个** — 它定义了每页的视觉主角、图表类型、icon、说明性数据）",
            "- `build_context.json`",
            "- `deck_visual_system.md`",
            "- `deck_component_tokens.md`",
            "- `deck_theme_tokens.json`",
            "- `slide_state.json`",
            "",
            "## 输出要求",
            "",
            "- 一页一个主角",
            "- 不引用其他页面实现代码",
            "- 图表优先复用 `assets/chart_templates/` 模板",
            "- 完成后回写 `slide_state.json`",
            "- 如果环境允许，请把真实页级几何数据回写到 `layout_manifest.json`，而不是只依赖骨架默认值",
            "- 如果回补或修正 `deck_clean_pages.md`，必须保持 `## 第 N 页` 分页格式",
            f"- 如果 `{rollback_plan.name}` 已存在，只处理其中分配给 `build` 或需要重建的页面，不要越权重写业务主线",
            "",
            f"建议调用：{recommended}",
            "",
            "## build_context.json 路径",
            "",
            f"`{context_path}`",
            "",
            "## 可选返工计划",
            "",
            f"`{rollback_plan}`",
            "",
            "## 可选几何回写",
            "",
            "如有真实页级几何数据，请用 `scripts/update_layout_manifest.py` 回写当前页。",
            "",
            "## 配图资产",
            "",
            "如果 build context 的 `inputs.assets` 包含当前页的图片引用，请按 `position` 和 `final_path` 将图片嵌入到页面的正确区域。",
        ]
    )


def build_review_prompt(project_dir: Path, review_package_path: Path | None = None) -> str:
    review_package_path = review_package_path or (project_dir / "review_package.json")
    schema_path = Path(__file__).resolve().parent.parent / "references" / "review_findings.schema.json"
    scorecard_schema_path = Path(__file__).resolve().parent.parent / "references" / "commercial_scorecard.schema.json"
    return "\n".join(
        [
            "# Review AI Handoff",
            "",
            "请做结构化评审，优先指出会削弱商业说服力、证据强度、关键页主角性和视觉一致性的问题。",
            "",
            "## 必看输入",
            "",
            "- `review_package.json`（优先）",
            "- 成品 deck",
            "- `deck_clean_pages.md`",
            "- `slide_state.json`",
            "- `montage.png`（如果存在）",
            "- `deck_expert_context.md`、`interview_session.json`、`interview_preparation.json`（如果 `review_package.json.expert_mode_summary.enabled=true`，这三份必须检查）",
            "",
            "## 输出要求",
            "",
            "- 输出为结构化 JSON，写入 `deck_review_findings.json`",
            "- 同时输出 `commercial_scorecard.json`，回答这套材料是否真的具备成交力",
            "- 必须符合 `review_findings.schema.json`",
            "- `commercial_scorecard.json` 必须符合 `commercial_scorecard.schema.json`",
            "- 每条 finding 至少包含 `page_id`、`severity`、`type`、`reason`、`suggested_fix`、`source_image`",
            "- findings 会被系统自动映射成 rollback plan，所以 `type` 必须准确，不要默认写成 `other`",
            "- 优先做多模态评审：先看 `montage.png`、页级 PNG 或截图，再回看 `deck_clean_pages.md` 与 `slide_state.json`",
            "- 先读取 `review_package.json` 中的 `expert_mode_summary`；如果 expert mode 已启用，必须先判断 gate 是否真的闭环，再评审页面质量",
            "- 如果 `expert_mode_summary.gating_status.finalized=false`、`redaction_pending>0`、`coverage_target_met=false` 或 `expert_context_ready=false`，必须给出对应 finding，而不是跳过",
            "- 必须核对 `deck_expert_context.md` 的专家案例/数字/因果链是否进入最终页面；如果没有被消费，优先使用 `expert_data_ignored` 或相关准确类型",
            "- 重点检查视觉层级、留白节奏、主角是否明确、是否有普通 AI 味、是否偏离既定视觉系统",
            "- 商业评分至少覆盖：受众契合度、第一购买理由、证据强度、顾虑覆盖、叙事推进和 CTA 强度",
            "- 如果环境支持视觉模型或截图能力，优先结合视觉输入做审美与信息层级判断",
            "",
            "建议调用：优先做视觉评审，必要时参考 `$frontend-design` 的高质量设计标准。",
            "",
            "## review_package.json 路径",
            "",
            f"`{review_package_path}`",
            "",
            "## review_findings.schema.json 路径",
            "",
            f"`{schema_path.resolve()}`",
            "",
            "## commercial_scorecard.schema.json 路径",
            "",
            f"`{scorecard_schema_path.resolve()}`",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a ready-to-send handoff prompt for a specific deck role.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    parser.add_argument("--page-ids", nargs="*", default=[])
    parser.add_argument("--context-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.role == "brief":
        text = build_brief_prompt(project_dir)
    elif args.role == "visual":
        text = build_visual_prompt(project_dir)
    elif args.role == "build":
        text = build_build_prompt(
            project_dir,
            args.page_ids,
            Path(args.context_path).expanduser().resolve() if args.context_path else None,
        )
    else:
        text = build_review_prompt(
            project_dir,
            Path(args.context_path).expanduser().resolve() if args.context_path else None,
        )

    output.write_text(text + "\n", encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
