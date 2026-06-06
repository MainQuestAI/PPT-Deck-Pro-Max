#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PRODUCTION_SUB_MODES = ("standard_deck", "formal_bid_image_led")

TEMPLATES = {
    "deck_brief.md": "# Deck Brief\n\nproduction_mode: expert\nproduction_sub_mode: standard_deck\n\n## 产品主语\n\n## 产品定位\n\n## 第一受众\n\n## 第一购买理由\n\n## 最强差异化\n\n## 最强证据\n\n## 首单入口\n\n## 最终 CTA\n",
    "deck_source_digest.md": "# Source Digest\n\n## 资料清单\n\n| Source | Type | Coverage | Confidence |\n|--------|------|----------|------------|\n\n## 核心事实\n\n（待提炼）\n\n## 可用证据\n\n（待提炼）\n\n## 明确缺口\n\n（待登记到 deck_gap_registry.json）\n",
    "deck_claim_map.json": "{\n  \"claims\": []\n}\n",
    "deck_capacity_plan.md": "# Capacity Plan\n\n## 页数容量判断\n\n- target_pages:\n- recommended_pages:\n- max_supported_pages:\n\n## 结论\n\n（待填写当前资料能支撑的核心页、证明页和扩展页）\n",
    "deck_capacity_plan.json": "{\n  \"target_pages\": null,\n  \"recommended_pages\": null,\n  \"max_supported_pages\": null,\n  \"notes\": \"\"\n}\n",
    "deck_gap_registry.json": "{\n  \"gaps\": []\n}\n",
    "deck_question_queue.md": "# Question Queue\n\n（由 expert-interview 生成；进入逐页稿前先补齐 blocking gap）\n",
    "deck_vibe_brief.md": "# Vibe Brief\n\n## 视觉气质\n\n## 配色系统\n\n## 字体系统\n\n## 图形语言\n\n## 密度上限\n",
    "deck_narrative_arc.md": "# Narrative Arc\n\n## 弧线模板\n\n（待锁定）\n\n## 逐页 Beat\n\n| 页码 | Beat | 情绪目标 | 过渡逻辑 |\n|------|------|---------|--------|\n\n## 信心拐点\n\n（待锁定）\n\n## 呼吸页\n\n（待锁定）\n",
    "deck_hero_pages.md": "# Hero Pages\n\n## 关键页\n\n1. 封面\n2. 痛点/诊断\n3. 样例/证据\n4. 核心能力/系统\n5. CTA\n",
    "deck_visual_composition.md": "# Visual Composition\n\n（待生成 — 在 Step 5 中由 AI 根据 clean pages 内容自动产出）\n",
    "deck_expert_context.md": "# Expert Context\n\n（待生成 — Expert Interview 完成 + Redaction Review 通过后产出）\n",
    "interview_session.json": "{\n  \"session_id\": \"\",\n  \"state\": \"preparing\",\n  \"coverage\": {\"hero_claims_total\": 0, \"hero_claims_enriched\": 0, \"hero_gap_fill_rate\": 0, \"target_fill_rate\": 0.8},\n  \"topics_queue\": [],\n  \"insights_collected\": 0,\n  \"redaction_pending\": 0,\n  \"resumable\": true\n}\n",
    "deck_layout_v1.md": "# Layout Draft\n",
    "deck_clean_pages.md": "# Clean Pages\n",
    "deck_visual_system.md": "# Visual System\n\n## 页面原型\n\n## 组件系统\n\n## 视觉特征锁定\n",
    "deck_component_tokens.md": "# Component Tokens\n\n## 组件清单\n",
    "style_lock.json": "{\n  \"version\": 1,\n  \"style_id\": \"pending-style-lock\",\n  \"visual_mood\": \"\",\n  \"color_system\": \"\",\n  \"typography\": \"\",\n  \"graphic_language\": \"\",\n  \"density_ceiling\": \"\",\n  \"palette\": {},\n  \"visual_rules\": {\n    \"material_finish\": \"editorial product-grade\",\n    \"lighting\": \"soft studio\",\n    \"perspective\": \"three-quarter editorial\",\n    \"text_in_image\": \"avoid\",\n    \"negative_prompts\": []\n  },\n  \"source_files\": {\n    \"deck_vibe_brief\": \"\",\n    \"deck_theme_tokens\": \"\",\n    \"deck_visual_system\": \"\"\n  }\n}\n",
    "deck_geometry_rules.md": "# Deck Geometry Rules\n\n## 页面安全区\n\n- 左右边距：\n- 上下边距：\n\n## archetype 几何规则\n\n### hero_cover\n- 左文区占比：\n- 右视觉区占比：\n- 标签区关系：\n\n### diagnostic_board\n- 主体区占比：\n- 三卡总宽度：\n- 卡片高度上限：\n\n### process_or_timeline\n- 中轴 x：\n- 节点间距：\n- 卡片离轴距离：\n\n## 连线规则\n\n- 连线来源：节点中心 / 卡片锚点 / 中轴交点\n- 禁止自由手写孤立线坐标\n",
    "deck_page_skeletons.md": "# Deck Page Skeletons\n\n## 第 1 页\n- archetype:\n- 主体区边界:\n- 主视觉边界:\n- 对齐轴:\n- 组件组关系:\n- 预期占比:\n\n## 第 2 页\n- archetype:\n- 主体区边界:\n- 主视觉边界:\n- 对齐轴:\n- 组件组关系:\n- 预期占比:\n",
    "deck_theme_tokens.json": "{\n  \"theme\": \"default\",\n  \"colors\": {},\n  \"typography\": {},\n  \"spacing\": {},\n  \"components\": {}\n}\n",
    "layout_manifest.json": "{\n  \"pages\": []\n}\n",
    "deck_asset_plan.md": "# Asset Plan\n\n## 配图需求总览\n\n| 页码 | 角色 | 需要什么 | 优先级 | 来源 |\n|------|------|---------|--------|------|\n\n## 逐页配图说明\n\n（待生成）\n",
    "asset_manifest.json": "{\n  \"assets\": []\n}\n",
    "image_build_jobs.json": "{\n  \"batch_size\": 3,\n  \"initial_review_batch\": \"batch_01\",\n  \"batches\": [],\n  \"jobs\": []\n}\n",
    "deck_review_report.md": "# Deck Review Report\n",
    "deck_review_findings.json": "[]\n",
    "review_rollback_plan.json": "{\n  \"project_dir\": \"\",\n  \"summary\": {},\n  \"page_actions\": [],\n  \"stage_actions\": []\n}\n",
    "review_rollback_plan.md": "# Review Rollback Plan\n",
    "review_package.json": "{\n  \"project_dir\": \"\",\n  \"artifacts\": {},\n  \"expert_mode_summary\": {\n    \"production_mode\": \"expert\",\n    \"enabled\": true,\n    \"review_ready\": false,\n    \"gating_status\": {\n      \"session_state\": \"preparing\",\n      \"finalized\": false,\n      \"redaction_pending\": 0,\n      \"expert_context_ready\": false,\n      \"coverage_target_met\": false\n    },\n    \"coverage\": {\n      \"hero_claims_total\": 0,\n      \"hero_claims_enriched\": 0,\n      \"hero_gap_fill_rate\": 0,\n      \"target_fill_rate\": 0.8\n    },\n    \"claim_summary\": {\n      \"total_claims\": 0,\n      \"hero_claims\": 0,\n      \"enriched_claims\": 0,\n      \"thin_hero_claim_ids\": []\n    },\n    \"review_focus\": [],\n    \"issues\": []\n  },\n  \"asset_build_summary\": {\n    \"total_assets\": 0,\n    \"approved_assets\": 0,\n    \"generated_assets\": 0,\n    \"queued_assets\": 0,\n    \"stale_assets\": 0,\n    \"placeholder_assets\": 0,\n    \"initial_review_batch\": \"batch_01\",\n    \"incomplete_batches\": []\n  },\n  \"page_images\": [],\n  \"required_output\": {}\n}\n",
    "commercial_scorecard.json": "{\n  \"overall_score\": null,\n  \"dimensions\": {\n    \"audience_fit\": null,\n    \"buying_reason_clarity\": null,\n    \"proof_strength\": null,\n    \"objection_coverage\": null,\n    \"narrative_flow\": null,\n    \"commercial_ask\": null\n  },\n  \"summary\": null,\n  \"recommended_action\": null,\n  \"weak_dimensions\": []\n}\n",
}

FORMAL_BID_IMAGE_LED_TEMPLATES = {
    "page_registry.md": "# Page Registry\n\nproduction_sub_mode: formal_bid_image_led\n\n| Source ID | Actual PPT Page | Chapter | Page Title | Status | Source Path | Approved Image | Known Issues | Owner |\n|-----------|-----------------|---------|------------|--------|-------------|----------------|--------------|-------|\n\n## Status Values\n\nUse `planned`, `candidate`, `Go`, `No-Go`, `replaced`, or `direct-reference`.\n",
    "image_generation_manifest.md": "# Image Generation Manifest\n\nproduction_sub_mode: formal_bid_image_led\n\n| Batch ID | Source ID | Page ID | Candidate Directory | Decision | Selected Image | Decision Note | Decided At |\n|----------|-----------|---------|---------------------|----------|----------------|---------------|------------|\n\n## Directory Policy\n\n- Candidate images stay under `图片生成候选结果/<batch_id>/` or an equivalent candidate directory.\n- Only `Go` images move into the passed source-id image directory.\n- Keep `No-Go` images out of the passed directory until regenerated.\n",
    "actual_page_mapping.md": "# Actual Page Mapping\n\nproduction_sub_mode: formal_bid_image_led\n\n| Actual PPT Page | Source ID | Chapter | Page Title | Final Image Filename | Direct Reference | Notes |\n|-----------------|-----------|---------|------------|----------------------|------------------|-------|\n\n## Mapping Notes\n\nRecord front matter, core pages, service pages, appendix pages, and direct-reference holes here before final PPT assembly.\n",
    "known_issue_log.md": "# Known Issue Log\n\nproduction_sub_mode: formal_bid_image_led\n\n| ID | Source ID | Actual PPT Page | Severity | Issue | Owner | Status | Resolution |\n|----|-----------|-----------------|----------|-------|-------|--------|------------|\n\n## Blocking Status\n\nBefore delivery, every blocking issue must be fixed or explicitly accepted by the user.\n",
}

EXAMPLE_DIR_NAME = "example_project"


def write_missing_templates(out_dir: Path, templates: dict[str, str]) -> list[str]:
    created = []
    for name, content in templates.items():
        path = out_dir / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(path.name)
    return created


def upsert_field(path: Path, field: str, value: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    prefix = f"{field}:"
    if prefix in text:
        lines = [
            f"{field}: {value}" if line.startswith(prefix) else line
            for line in text.splitlines()
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        path.write_text(f"{field}: {value}\n\n{text}", encoding="utf-8")


def init_project(out_dir: Path, with_example: bool = False, production_sub_mode: str = "standard_deck") -> list[str]:
    if production_sub_mode not in PRODUCTION_SUB_MODES:
        raise ValueError(f"invalid production_sub_mode: {production_sub_mode}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "assets").mkdir(exist_ok=True)

    created = write_missing_templates(out_dir, TEMPLATES)
    upsert_field(out_dir / "deck_brief.md", "production_sub_mode", production_sub_mode)
    if production_sub_mode == "formal_bid_image_led":
        created.extend(write_missing_templates(out_dir, FORMAL_BID_IMAGE_LED_TEMPLATES))

    if with_example:
        skill_root = Path(__file__).resolve().parent.parent
        example_dir = skill_root / "assets" / EXAMPLE_DIR_NAME
        if example_dir.exists():
            for item in example_dir.iterdir():
                target = out_dir / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                created.append(item.name)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a deck production project scaffold.")
    parser.add_argument("--output", required=True, help="Project directory")
    parser.add_argument("--with-example", action="store_true", help="Copy bundled example project files")
    parser.add_argument("--production-sub-mode", default="standard_deck", choices=PRODUCTION_SUB_MODES)
    args = parser.parse_args()

    out_dir = Path(args.output).expanduser().resolve()
    created = init_project(out_dir, with_example=args.with_example, production_sub_mode=args.production_sub_mode)

    print(f"[OK] project initialized: {out_dir}")
    if created:
        print("[OK] created files:")
        for item in created:
            print(f"  - {item}")
    else:
        print("[OK] no new files created")


if __name__ == "__main__":
    main()
