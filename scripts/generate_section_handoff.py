#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from content_governance import (
    capacity_summary,
    normalize_claims,
    normalize_gap_registry,
    normalize_sections,
    read_json_file,
    section_package_summary,
)


def load_json(path: Path) -> dict:
    data, err = read_json_file(path)
    if err or not isinstance(data, dict):
        return {}
    return data


def compact_list(items: list[Any]) -> list[str]:
    return [str(item).strip() for item in items if str(item).strip()]


def find_section(project_dir: Path, section_id: str) -> dict:
    payload = load_json(project_dir / "section_packages.json")
    for section in normalize_sections(payload):
        if section["section_id"] == section_id:
            return section
    known = ", ".join(section["section_id"] for section in normalize_sections(payload)) or "none"
    raise SystemExit(f"[ERROR] section_id not found: {section_id}. Known sections: {known}")


def filter_claims(project_dir: Path, claim_ids: list[str]) -> list[dict]:
    claim_payload = load_json(project_dir / "deck_claim_map.json")
    claims = normalize_claims(claim_payload)
    if not claim_ids:
        return []
    allowed = set(claim_ids)
    return [claim for claim in claims if str(claim.get("claim_id")) in allowed]


def filter_gaps(project_dir: Path, claim_ids: list[str]) -> list[dict]:
    gap_payload = load_json(project_dir / "deck_gap_registry.json")
    gaps = normalize_gap_registry(gap_payload)
    if not claim_ids:
        return []
    allowed = set(claim_ids)
    return [gap for gap in gaps if str(gap.get("claim_id")) in allowed]


def build_payload(project_dir: Path, section_id: str) -> dict:
    capacity_payload = load_json(project_dir / "deck_capacity_plan.json")
    capacity = capacity_summary(capacity_payload, project_dir)
    section_summary = section_package_summary(project_dir, capacity)
    section = find_section(project_dir, section_id)
    claim_ids = compact_list(section.get("claim_ids", []))
    claims = filter_claims(project_dir, claim_ids)
    gaps = filter_gaps(project_dir, claim_ids)
    return {
        "project_dir": str(project_dir),
        "section": {
            "section_id": section["section_id"],
            "title": section["title"],
            "objective": section["objective"],
            "page_count": section["page_count"],
            "page_ids": compact_list(section.get("page_ids", [])),
            "claim_ids": claim_ids,
            "allowed_evidence": compact_list(section.get("allowed_evidence", [])),
            "allowed_topics": compact_list(section.get("allowed_topics", [])),
            "forbidden_topics": compact_list(section.get("forbidden_topics", [])),
            "input_transition": section["input_transition"],
            "output_transition": section["output_transition"],
            "density_level": section["density_level"],
            "dense_archetype": section["dense_archetype"],
            "suggested_archetypes": compact_list(section.get("suggested_archetypes", [])),
        },
        "claims": claims,
        "gaps": gaps,
        "capacity": {
            "target_pages": capacity.get("target_pages"),
            "recommended_pages": capacity.get("recommended_pages"),
            "max_supported_pages": capacity.get("max_supported_pages"),
            "budget_summary": capacity.get("budget_summary", {}),
        },
        "section_package_summary": {
            "total_sections": section_summary.get("total_sections"),
            "total_pages": section_summary.get("total_pages"),
            "target_pages": section_summary.get("target_pages"),
            "issues": section_summary.get("issues", []),
        },
        "source_paths": {
            "source_digest": str((project_dir / "deck_source_digest.md").resolve()),
            "claim_map": str((project_dir / "deck_claim_map.json").resolve()),
            "gap_registry": str((project_dir / "deck_gap_registry.json").resolve()),
            "capacity_plan": str((project_dir / "deck_capacity_plan.json").resolve()),
            "section_packages": str((project_dir / "section_packages.json").resolve()),
            "dense_archetypes": str((Path(__file__).resolve().parent.parent / "references" / "dense_page_archetypes.md").resolve()),
        },
    }


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- 无"]


def claim_lines(claims: list[dict]) -> list[str]:
    if not claims:
        return ["- 当前章节包未绑定 claim_id；先补 `section_packages.json.claim_ids`。"]
    lines: list[str] = []
    for claim in claims:
        text = str(claim.get("claim_text", "")).strip()
        evidence = str(claim.get("full_text", "")).strip()
        lines.append(f"- `{claim.get('claim_id', 'unknown')}`：{text}")
        if evidence and evidence != text:
            one_line = " ".join(evidence.split())
            lines.append(f"  证据摘要：{one_line[:260]}")
    return lines


def gap_lines(gaps: list[dict]) -> list[str]:
    if not gaps:
        return ["- 当前章节没有已登记缺口。"]
    lines: list[str] = []
    for gap in gaps:
        desc = str(gap.get("desc") or gap.get("topic") or "").strip()
        lines.append(
            f"- `{gap.get('gap_id', 'unknown')}`：{gap.get('gap_type', 'unknown')}，状态 `{gap.get('status', 'open')}`，{desc}"
        )
    return lines


def build_markdown(payload: dict) -> str:
    section = payload["section"]
    capacity = payload["capacity"]
    budget = capacity.get("budget_summary", {})
    dense = section.get("dense_archetype") or ", ".join(section.get("suggested_archetypes", [])) or "未指定"
    lines = [
        f"# Section Handoff: {section['section_id']}",
        "",
        "## 章节目标",
        "",
        f"- 标题：{section['title']}",
        f"- 目标：{section['objective']}",
        f"- 页数配额：{section['page_count']}",
        f"- 页面范围：{', '.join(section['page_ids']) if section['page_ids'] else '未绑定'}",
        f"- 输入过渡：{section['input_transition'] or '待补'}",
        f"- 输出过渡：{section['output_transition'] or '待补'}",
        "",
        "## 页数预算边界",
        "",
        f"- 全 deck 目标页数：{capacity.get('target_pages')}",
        f"- 推荐页数：{capacity.get('recommended_pages')}",
        f"- 最大可支撑页数：{capacity.get('max_supported_pages')}",
        f"- 当前是否超过推荐档：{budget.get('target_over_recommended')}",
        f"- 当前是否有扩写策略：{budget.get('has_extension_strategy')}",
        "",
        "## 可用论点与证据",
        "",
        *claim_lines(payload.get("claims", [])),
        "",
        "## 本章节缺口",
        "",
        *gap_lines(payload.get("gaps", [])),
        "",
        "## 可复用边界",
        "",
        "### 允许复用证据",
        "",
        *bullet_lines(section.get("allowed_evidence", [])),
        "",
        "### 允许话题",
        "",
        *bullet_lines(section.get("allowed_topics", [])),
        "",
        "### 禁止重复话题",
        "",
        *bullet_lines(section.get("forbidden_topics", [])),
        "",
        "## 高密度版式要求",
        "",
        f"- 密度级别：{section.get('density_level') or '未指定'}",
        f"- 建议原型：{dense}",
        "- 写稿时必须绑定视觉主角、信息单元数和拆页条件。",
        "- 高密度原型说明见 `references/dense_page_archetypes.md`。",
        "",
        "## 输出要求",
        "",
        "- 只产出当前章节范围内的逐页稿。",
        "- 不引入其他章节的 claim、案例或证据。",
        "- 遇到缺口先标记为待补，不靠相近话题重复扩写。",
        "- 每页必须说明 `dense_archetype`、`density_level`、`info_units`、`split_trigger`、`visual_protagonist`。",
        "",
        "## 源文件路径",
        "",
    ]
    for name, path in payload["source_paths"].items():
        lines.append(f"- `{name}`：`{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a focused handoff package for one longform deck section.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--section-id", required=True)
    parser.add_argument("--output")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    payload = build_payload(project_dir, args.section_id)
    output = Path(args.output).expanduser().resolve() if args.output else project_dir / f"{args.section_id}_handoff.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(payload), encoding="utf-8")
    if args.output_json:
        output_json = Path(args.output_json).expanduser().resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
