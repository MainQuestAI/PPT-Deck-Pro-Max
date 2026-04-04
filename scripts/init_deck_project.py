#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

TEMPLATES = {
    "deck_brief.md": "# Deck Brief\n\n## 产品主语\n\n## 产品定位\n\n## 第一受众\n\n## 第一购买理由\n\n## 最强差异化\n\n## 最强证据\n\n## 首单入口\n\n## 最终 CTA\n",
    "deck_vibe_brief.md": "# Vibe Brief\n\n## 视觉气质\n\n## 配色系统\n\n## 字体系统\n\n## 图形语言\n\n## 密度上限\n",
    "deck_narrative_arc.md": "# Narrative Arc\n\n## 弧线模板\n\n（待锁定）\n\n## 逐页 Beat\n\n| 页码 | Beat | 情绪目标 | 过渡逻辑 |\n|------|------|---------|--------|\n\n## 信心拐点\n\n（待锁定）\n\n## 呼吸页\n\n（待锁定）\n",
    "deck_hero_pages.md": "# Hero Pages\n\n## 关键页\n\n1. 封面\n2. 痛点/诊断\n3. 样例/证据\n4. 核心能力/系统\n5. CTA\n",
    "deck_layout_v1.md": "# Layout Draft\n",
    "deck_clean_pages.md": "# Clean Pages\n",
    "deck_visual_system.md": "# Visual System\n\n## 页面原型\n\n## 组件系统\n\n## 视觉特征锁定\n",
    "deck_component_tokens.md": "# Component Tokens\n\n## 组件清单\n",
    "deck_geometry_rules.md": "# Deck Geometry Rules\n\n## 页面安全区\n\n- 左右边距：\n- 上下边距：\n\n## archetype 几何规则\n\n### hero_cover\n- 左文区占比：\n- 右视觉区占比：\n- 标签区关系：\n\n### diagnostic_board\n- 主体区占比：\n- 三卡总宽度：\n- 卡片高度上限：\n\n### process_or_timeline\n- 中轴 x：\n- 节点间距：\n- 卡片离轴距离：\n\n## 连线规则\n\n- 连线来源：节点中心 / 卡片锚点 / 中轴交点\n- 禁止自由手写孤立线坐标\n",
    "deck_page_skeletons.md": "# Deck Page Skeletons\n\n## 第 1 页\n- archetype:\n- 主体区边界:\n- 主视觉边界:\n- 对齐轴:\n- 组件组关系:\n- 预期占比:\n\n## 第 2 页\n- archetype:\n- 主体区边界:\n- 主视觉边界:\n- 对齐轴:\n- 组件组关系:\n- 预期占比:\n",
    "deck_theme_tokens.json": "{\n  \"theme\": \"default\",\n  \"colors\": {},\n  \"typography\": {},\n  \"spacing\": {},\n  \"components\": {}\n}\n",
    "layout_manifest.json": "{\n  \"pages\": []\n}\n",
    "deck_review_report.md": "# Deck Review Report\n",
    "deck_review_findings.json": "[]\n",
    "review_rollback_plan.json": "{\n  \"project_dir\": \"\",\n  \"summary\": {},\n  \"page_actions\": [],\n  \"stage_actions\": []\n}\n",
    "review_rollback_plan.md": "# Review Rollback Plan\n",
    "review_package.json": "{\n  \"project_dir\": \"\",\n  \"artifacts\": {},\n  \"page_images\": [],\n  \"required_output\": {}\n}\n",
    "commercial_scorecard.json": "{\n  \"overall_score\": null,\n  \"dimensions\": {\n    \"audience_fit\": null,\n    \"buying_reason_clarity\": null,\n    \"proof_strength\": null,\n    \"objection_coverage\": null,\n    \"narrative_flow\": null,\n    \"commercial_ask\": null\n  },\n  \"summary\": \"\",\n  \"recommended_action\": \"\",\n  \"weak_dimensions\": []\n}\n",
}

EXAMPLE_DIR_NAME = "example_project"


def init_project(out_dir: Path, with_example: bool = False) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for name, content in TEMPLATES.items():
        path = out_dir / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(path.name)

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
    args = parser.parse_args()

    out_dir = Path(args.output).expanduser().resolve()
    created = init_project(out_dir, with_example=args.with_example)

    print(f"[OK] project initialized: {out_dir}")
    if created:
        print("[OK] created files:")
        for item in created:
            print(f"  - {item}")
    else:
        print("[OK] no new files created")


if __name__ == "__main__":
    main()
