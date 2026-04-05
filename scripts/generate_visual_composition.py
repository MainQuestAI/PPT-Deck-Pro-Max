#!/usr/bin/env python3
"""Generate a visual composition spec from clean pages and slide state.

Analyzes each page's content to identify data relationships and proposes
visual protagonist types, chart/icon specifications, layout compositions,
and illustrative data anchors.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from page_parser import extract_page_slices


# Data relationship detection patterns
COMPARISON_KEYWORDS = ["vs", "对比", "传统", "下一代", "旧", "新", "区别", "差异", "比较"]
GAP_KEYWORDS = ["断裂", "不足", "缺失", "差距", "缺口", "覆盖率", "瓶颈", "问题"]
FLOW_KEYWORDS = ["流程", "阶段", "步骤", "先", "然后", "最后", "路径", "链路", "→"]
LOOP_KEYWORDS = ["闭环", "循环", "回流", "持续", "反馈", "回写"]
CATEGORY_KEYWORDS = ["五类", "六大", "三个", "四种", "模块", "场景", "维度", "价值"]
METRIC_KEYWORDS = ["亿", "万", "%", "率", "指标", "数据"]

# Visual protagonist mapping — full spec per relationship type
RELATIONSHIP_TO_VISUAL = {
    "comparison": {
        "visual": "comparison_table + radar_chart",
        "layout": "left_table_right_chart",
        "position": "right",
        "proportion": "55%",
        "weight": "chart 55% / table 35% / labels 10%",
        "template": "comparison_bar.html",
        "emphasis": "new_column_highlight_green",
        "concept_ui": False,
    },
    "degree_gap": {
        "visual": "gauge_chart",
        "layout": "multi_column_cards",
        "position": "bottom_of_each_column",
        "proportion": "30%",
        "weight": "gauge 40% / text 40% / icon 20%",
        "template": "diagnostic_board.html",
        "emphasis": "existing_green_missing_red",
        "concept_ui": False,
    },
    "flow_process": {
        "visual": "icon_flow_chain",
        "layout": "top_flow_bottom_detail",
        "position": "top_center",
        "proportion": "35%",
        "weight": "flow_chain 40% / detail_table 40% / labels 20%",
        "template": "stage_band.html",
        "emphasis": "step_numbers_and_arrows",
        "concept_ui": True,
    },
    "closed_loop": {
        "visual": "circular_loop_diagram",
        "layout": "center_diagram_side_legend",
        "position": "left_center",
        "proportion": "50%",
        "weight": "loop 55% / legend 35% / labels 10%",
        "template": "closed_loop.html",
        "emphasis": "colored_nodes_with_icons",
        "concept_ui": False,
    },
    "category": {
        "visual": "icon_card_grid",
        "layout": "multi_column_cards",
        "position": "center",
        "proportion": "60%",
        "weight": "cards 60% / title 25% / insight 15%",
        "template": None,
        "emphasis": "colored_left_border_per_card",
        "concept_ui": False,
    },
    "big_metric": {
        "visual": "metric_card",
        "layout": "center_metric",
        "position": "center",
        "proportion": "40%",
        "weight": "metric 50% / context 30% / labels 20%",
        "template": None,
        "emphasis": "oversized_number_80px",
        "concept_ui": False,
    },
    "layer_input_output": {
        "visual": "three_layer_flow",
        "layout": "three_horizontal_bands",
        "position": "left",
        "proportion": "50%",
        "weight": "layers 50% / concept_ui 35% / labels 15%",
        "template": None,
        "emphasis": "distinct_color_per_layer",
        "concept_ui": True,
    },
    "timeline_evolution": {
        "visual": "timeline_with_highlight",
        "layout": "horizontal_timeline",
        "position": "center",
        "proportion": "40%",
        "weight": "timeline 45% / labels 35% / highlight 20%",
        "template": "stage_band.html",
        "emphasis": "current_phase_glow",
        "concept_ui": False,
    },
}

# Icon suggestions by concept keywords
ICON_MAP = {
    "认知": "brain", "理解": "brain", "用户": "users", "人群": "users",
    "决策": "settings", "策略": "target", "规则": "git-branch",
    "内容": "file-text", "素材": "image", "文案": "edit",
    "监测": "eye", "观察": "search", "预警": "alert-triangle",
    "修复": "wrench", "工单": "clipboard", "诊断": "activity",
    "数据": "database", "CDP": "database", "标签": "tag",
    "自动化": "zap", "MA": "zap", "旅程": "map",
    "Agent": "bot", "智能体": "bot", "AI": "cpu",
    "转化": "trending-up", "增长": "bar-chart", "效率": "gauge",
    "合规": "shield", "审批": "check-circle", "安全": "lock",
    "目标": "target", "业务": "briefcase", "品牌": "award",
    "执行": "play", "发布": "send", "渠道": "share-2",
    "反馈": "refresh-cw", "回流": "refresh-cw", "闭环": "repeat",
    "价值": "diamond", "权益": "gift", "服务": "heart",
    "首购": "shopping-cart", "复购": "repeat", "会员": "crown",
    "沉默": "moon", "唤醒": "bell", "升层": "arrow-up",
    "预演": "play-circle", "模拟": "monitor", "试点": "flag",
}


LAYER_KEYWORDS = ["输入", "处理", "输出", "三层", "输入层", "输出层", "上下文"]
TIMELINE_KEYWORDS = ["演进", "三代", "代际", "第一代", "第二代", "Gen 1", "Gen 2", "GEN"]


def detect_relationship(text: str) -> str:
    """Detect the primary data relationship in a page's content."""
    text_lower = text.lower()
    scores = {
        "comparison": sum(1 for k in COMPARISON_KEYWORDS if k in text_lower),
        "degree_gap": sum(1 for k in GAP_KEYWORDS if k in text_lower),
        "flow_process": sum(1 for k in FLOW_KEYWORDS if k in text_lower),
        "closed_loop": sum(1 for k in LOOP_KEYWORDS if k in text_lower),
        "category": sum(1 for k in CATEGORY_KEYWORDS if k in text_lower),
        "big_metric": sum(1 for k in METRIC_KEYWORDS if k in text_lower),
        "layer_input_output": sum(1 for k in LAYER_KEYWORDS if k in text_lower),
        "timeline_evolution": sum(1 for k in TIMELINE_KEYWORDS if k in text_lower),
    }
    # Special: if page has both flow and comparison, pick the stronger
    if scores["flow_process"] > 0 and scores["comparison"] > 0:
        if scores["comparison"] >= scores["flow_process"]:
            return "comparison"
    # Closed loop is specific — if detected, prefer it
    if scores["closed_loop"] >= 2:
        return "closed_loop"
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "category"


def suggest_icons(text: str, max_icons: int = 6) -> list[dict]:
    """Suggest icons based on concept keywords found in text."""
    found = []
    seen = set()
    for keyword, icon in ICON_MAP.items():
        if keyword in text and icon not in seen:
            found.append({"icon": icon, "keyword": keyword})
            seen.add(icon)
            if len(found) >= max_icons:
                break
    return found


def suggest_illustrative_data(relationship: str, text: str) -> list[dict]:
    """Suggest illustrative data points based on content analysis."""
    data = []
    if relationship == "degree_gap":
        # Look for concepts that describe gaps
        gap_concepts = re.findall(r"([^，。：\n]{2,8})[层级]?断裂|([^，。：\n]{2,8})不足|([^，。：\n]{2,8})缺[失少]", text)
        values = [25, 20, 30, 15, 35]
        labels = ["深层理解率", "动态调整率", "智能匹配率", "闭环完成率", "主动干预率"]
        for idx in range(min(3, max(1, len(gap_concepts)))):
            data.append({
                "label": labels[idx] if idx < len(labels) else f"指标{idx+1}",
                "value": values[idx],
                "unit": "%",
                "type": "gauge",
                "illustrative": True,
            })
    elif relationship == "comparison":
        data.append({"label": "综合能力指数", "value": 140, "unit": "idx", "type": "bar", "illustrative": True})
        data.append({"label": "传统方式基准", "value": 100, "unit": "idx", "type": "bar", "illustrative": True})
    elif relationship == "category":
        # Multiple categories — suggest colored scores
        count = 0
        for k in CATEGORY_KEYWORDS:
            match = re.search(rf"(\d+)[类种个大]", text)
            if match:
                count = int(match.group(1))
                break
        if count == 0:
            count = 3
        values = [92, 88, 95, 85, 78]
        for i in range(min(count, 5)):
            data.append({"label": f"维度{i+1}", "value": values[i], "type": "bar", "illustrative": True})
    return data


def generate_composition(clean_pages_text: str, state: dict) -> list[dict]:
    """Generate visual composition specs for all pages."""
    slices = extract_page_slices(clean_pages_text)
    role_lookup = {}
    for page in state.get("pages", []):
        match = re.search(r"(\d+)", page.get("page_id", ""))
        if match:
            role_lookup[int(match.group(1))] = page.get("role", "unassigned")

    compositions = []
    for page_no in sorted(slices.keys()):
        section = slices[page_no]
        role = role_lookup.get(page_no, "unassigned")
        relationship = detect_relationship(section)
        visual_info = RELATIONSHIP_TO_VISUAL.get(relationship, RELATIONSHIP_TO_VISUAL["category"])
        icons = suggest_icons(section)
        data = suggest_illustrative_data(relationship, section)

        # Extract page title
        title_match = re.search(r"标题：[`「](.+?)[`」]", section)
        title = title_match.group(1) if title_match else f"第 {page_no} 页"

        # Detect if concept UI needed (scene/proof pages without real screenshots)
        needs_concept_ui = visual_info.get("concept_ui", False) and role in (
            "hero_proof", "hero_system", "hero_diff", "hero_value", "unassigned"
        )
        concept_ui_title = ""
        if needs_concept_ui:
            # Generate a concept UI title based on page content
            if "转化" in section or "首购" in section:
                concept_ui_title = "Private-domain conversion runtime"
            elif "内容" in section:
                concept_ui_title = "Content orchestration workbench"
            elif "会员" in section:
                concept_ui_title = "Membership runtime cockpit"
            elif "预演" in section or "模拟" in section:
                concept_ui_title = "Strategy simulation lab"
            elif "监测" in section:
                concept_ui_title = "Monitor control panel"
            else:
                concept_ui_title = f"{title} workbench"

        compositions.append({
            "page_no": page_no,
            "page_id": f"slide_{page_no:02d}",
            "title": title,
            "role": role,
            "data_relationship": relationship,
            "visual_protagonist": visual_info["visual"],
            "protagonist_position": visual_info.get("position", "center"),
            "protagonist_proportion": visual_info.get("proportion", "40%"),
            "layout_composition": visual_info["layout"],
            "visual_weight": visual_info.get("weight", "visual 50% / text 40% / labels 10%"),
            "template_ref": visual_info.get("template"),
            "emphasis": visual_info.get("emphasis", ""),
            "concept_ui": concept_ui_title if needs_concept_ui else None,
            "suggested_icons": icons,
            "illustrative_data": data,
        })

    return compositions


def write_composition_md(compositions: list[dict], output: Path) -> None:
    """Write visual composition as markdown."""
    lines = ["# Visual Composition", ""]
    for comp in compositions:
        lines.extend([
            f"## 第 {comp['page_no']} 页",
            "",
            f"页面标题：{comp['title']}",
            "",
            "### 数据关系",
            f"类型：{comp['data_relationship']}",
            "",
            "### 视觉主角",
            f"类型：{comp['visual_protagonist']}",
            f"位置：{comp.get('protagonist_position', 'center')}",
            f"占页面比例：{comp.get('protagonist_proportion', '40%')}",
            "",
            "### 布局组合",
            f"结构：{comp['layout_composition']}",
            f"视觉重量：{comp.get('visual_weight', '')}",
            "",
        ])
        if comp.get("emphasis"):
            lines.extend(["### 强调方式", f"{comp['emphasis']}", ""])
        if comp.get("template_ref"):
            lines.extend(["### 模板引用", f"模板：{comp['template_ref']}", ""])
        if comp.get("concept_ui"):
            lines.extend([
                "### 概念化 UI",
                f"类型：concept_ui",
                f"标题：{comp['concept_ui']}",
                "风格：terminal_window",
                "",
            ])
        if comp["illustrative_data"]:
            lines.append("### 数据可视化")
            for d in comp["illustrative_data"]:
                marker = "illustrative=true" if d.get("illustrative") else "illustrative=false"
                lines.append(f"指标：label={d['label']} | value={d['value']}{d.get('unit','')} | type={d['type']} | {marker}")
            lines.append("")
        if comp["suggested_icons"]:
            lines.append("### Icon 指定")
            for ic in comp["suggested_icons"]:
                lines.append(f"icon={ic['icon']} | keyword={ic['keyword']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate visual composition spec from clean pages.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--clean-pages")
    parser.add_argument("--state")
    parser.add_argument("--output")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    clean_pages = Path(args.clean_pages or project_dir / "deck_clean_pages.md").expanduser().resolve()
    state_path = Path(args.state or project_dir / "slide_state.json").expanduser().resolve()
    output = Path(args.output or project_dir / "deck_visual_composition.md").expanduser().resolve()

    if not clean_pages.exists():
        raise SystemExit(f"[ERROR] clean pages not found: {clean_pages}")

    text = clean_pages.read_text(encoding="utf-8")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"pages": []}
    compositions = generate_composition(text, state)
    write_composition_md(compositions, output)

    # Summary
    visual_types = set(c["visual_protagonist"] for c in compositions)
    with_data = sum(1 for c in compositions if c["illustrative_data"])
    print(f"[OK] wrote visual composition: {output}")
    print(f"[OK] {len(compositions)} pages, {len(visual_types)} unique visual types, {with_data} pages with data viz")


if __name__ == "__main__":
    main()
