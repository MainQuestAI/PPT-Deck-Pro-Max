#!/usr/bin/env python3
"""Extract narrative claims from clean pages, identify knowledge gaps, and compute richness scores.

This script handles the rule-based part of Expert Interview preparation:
- Extract claims from source material (one per page section)
- Detect 5 types of knowledge gaps per claim
- Compute richness scores
- Prioritize gaps for the interview

It does NOT generate the actual interview questions with hypotheses.
That requires LLM-level understanding and is done by the Expert Interviewer AI at runtime.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from page_parser import extract_page_slices, page_id_to_number


# Gap detection patterns
CASE_SIGNALS = ["例如", "比如", "案例", "客户", "品牌名", "公司名"]
CAUSAL_SIGNALS = ["因为", "所以", "根源", "导致", "本质上", "根因", "原因是"]
DATA_SIGNALS = ["%", "亿", "万", "率", "量", "额", "倍", "次"]
CONTRAST_SIGNALS = ["像", "类似", "就像", "好比", "比喻", "如同"]
# Objection detection needs Brief context, handled separately


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def extract_claims(clean_pages_text: str, state: dict) -> list[dict]:
    """Extract one claim per page section from clean pages."""
    slices = extract_page_slices(clean_pages_text)
    role_lookup = {}
    for page in state.get("pages", []):
        num = page_id_to_number(page.get("page_id", ""))
        if num:
            role_lookup[num] = page.get("role", "unassigned")

    claims = []
    for page_no in sorted(slices.keys()):
        section = slices[page_no]
        role = role_lookup.get(page_no, "unassigned")

        # Extract title as claim text
        title_match = re.search(r"标题：[`「](.+?)[`」]", section)
        title = title_match.group(1) if title_match else ""

        # Extract subtitle
        sub_match = re.search(r"副标题：[`「](.+?)[`」]", section)
        subtitle = sub_match.group(1) if sub_match else ""

        # Full text for gap analysis
        full_text = section

        # Determine claim type from content patterns
        claim_type = _infer_claim_type(full_text)

        # Detect beat hint from role
        beat_hint = _role_to_beat(role)

        claims.append({
            "claim_id": f"claim_{page_no:02d}",
            "page_no": page_no,
            "claim_text": title or f"第 {page_no} 页的论点",
            "subtitle": subtitle,
            "claim_type": claim_type,
            "role": role,
            "beat_hint": beat_hint,
            "full_text": full_text,
            "gaps": [],
            "richness_score": 0,
            "is_hero": role.startswith("hero_"),
        })

    return claims


def _infer_claim_type(text: str) -> str:
    if any(k in text for k in ["因为", "根源", "导致", "根因"]):
        return "causal_judgment"
    if any(k in text for k in ["场景", "转化", "首购", "复购"]):
        return "scenario_proof"
    if any(k in text for k in ["对比", "vs", "区别", "差异"]):
        return "comparison"
    if any(k in text for k in ["顾虑", "质疑", "反驳"]):
        return "objection_response"
    return "assertion"


def _role_to_beat(role: str) -> str:
    mapping = {
        "hero_cover": "setup",
        "hero_problem": "tension",
        "hero_proof": "proof",
        "hero_system": "resolution",
        "hero_diff": "resolution",
        "hero_value": "proof",
        "hero_cta": "action",
    }
    return mapping.get(role, "")


def detect_gaps(claim: dict, brief_concerns: list[str] | None = None) -> list[dict]:
    """Detect 5 types of knowledge gaps for a claim."""
    text = claim["full_text"]
    gaps = []

    # Case gap
    has_case = any(s in text for s in CASE_SIGNALS)
    # Also check for specific proper nouns (capitalized words or Chinese brand patterns)
    has_proper_noun = bool(re.search(r"[A-Z][a-z]+|[\u4e00-\u9fff]{2,4}(?:品牌|公司|集团)", text))
    if not has_case and not has_proper_noun:
        gaps.append({
            "gap_type": "case",
            "topic": claim["claim_text"],
            "desc": "缺少具体客户、品牌或场景案例",
            "status": "open",
        })

    # Causal gap
    has_causal = any(s in text for s in CAUSAL_SIGNALS)
    if not has_causal and claim["claim_type"] != "causal_judgment":
        gaps.append({
            "gap_type": "causal",
            "topic": claim["claim_text"],
            "desc": "结论是并列或描述性的，缺少因果链",
            "status": "open",
        })

    # Data gap — exclude page numbers and heading digits from detection
    text_no_headings = re.sub(r"^##?\s*第\s*\d+\s*页.*$", "", text, flags=re.MULTILINE)
    text_no_headings = re.sub(r"^slide[_\s-]*\d+.*$", "", text_no_headings, flags=re.MULTILINE | re.IGNORECASE)
    has_data = any(s in text_no_headings for s in DATA_SIGNALS) or bool(re.search(r"\d+[%亿万倍x]|\d+\.\d+", text_no_headings))
    if not has_data:
        gaps.append({
            "gap_type": "data",
            "topic": claim["claim_text"],
            "desc": "没有可量化的数据锚点",
            "status": "open",
        })

    # Contrast gap
    has_contrast = any(s in text for s in CONTRAST_SIGNALS)
    if not has_contrast and claim["claim_type"] == "comparison":
        gaps.append({
            "gap_type": "contrast",
            "topic": claim["claim_text"],
            "desc": "有对比但缺少具象化的类比",
            "status": "open",
        })

    # Objection gap (needs Brief context)
    if brief_concerns:
        for concern in brief_concerns:
            # Extract keywords: split on punctuation, then check 2+ char segments
            concern_head = concern.split("——")[0].split("——")[0]
            concern_words = [w for w in re.split(r"[、，,\s]+", concern_head) if len(w) >= 2]
            if any(keyword in text for keyword in concern_words):
                # This claim touches a concern area but might not address it
                has_objection_response = any(k in text for k in ["不是", "而是", "不需要", "只需要"])
                if not has_objection_response:
                    gaps.append({
                        "gap_type": "objection",
                        "topic": claim["claim_text"],
                        "desc": f"涉及关键顾虑「{concern[:20]}」但没有预防性回应",
                        "status": "open",
                    })
                    break  # One objection gap per claim is enough

    return gaps


def compute_richness(claim: dict) -> int:
    """Compute richness score (0-5) for a claim based on current content."""
    text = claim["full_text"]
    score = 0

    # Case: has specific example
    if any(s in text for s in CASE_SIGNALS) or bool(re.search(r"[A-Z][a-z]+", text)):
        score += 1

    # Causal: has causal reasoning
    if any(s in text for s in CAUSAL_SIGNALS):
        score += 1

    # Data: has quantifiable anchors (same logic as gap detection, excluding page numbers)
    text_no_headings = re.sub(r"^##?\s*第\s*\d+\s*页.*$", "", text, flags=re.MULTILINE)
    text_no_headings = re.sub(r"^slide[_\s-]*\d+.*$", "", text_no_headings, flags=re.MULTILINE | re.IGNORECASE)
    if bool(re.search(r"\d+[%亿万倍x]|\d+\.\d+", text_no_headings)):
        score += 1

    # Analogy: has contrast/metaphor
    if any(s in text for s in CONTRAST_SIGNALS):
        score += 1

    # Objection: has preemptive response (aligned with gap detection signals)
    if any(k in text for k in ["不是", "而是", "不需要", "只需要"]):
        score += 1

    return score


def prioritize_gaps(claims: list[dict]) -> list[dict]:
    """Sort gaps by priority: hero claims first, then by gap count and richness."""
    # Flatten all gaps with claim context
    all_gaps = []
    for claim in claims:
        for gap in claim["gaps"]:
            priority = 1 if claim["is_hero"] else 2
            # Case and data gaps are most impactful for persuasion
            if gap["gap_type"] in ("case", "data"):
                priority -= 0.5
            all_gaps.append({
                **gap,
                "claim_id": claim["claim_id"],
                "claim_richness": claim["richness_score"],
                "is_hero": claim["is_hero"],
                "priority": priority,
            })

    return sorted(all_gaps, key=lambda g: (g["priority"], g["claim_richness"]))


def extract_brief_concerns(brief_path: Path) -> list[str]:
    """Extract key concerns from deck_brief.md."""
    if not brief_path.exists():
        return []
    text = brief_path.read_text(encoding="utf-8")
    concerns = []
    in_concerns = False
    for line in text.splitlines():
        if "关键顾虑" in line:
            in_concerns = True
            continue
        if in_concerns:
            if line.startswith("##"):
                break
            stripped = line.strip().lstrip("0123456789.-) ")
            if stripped:
                concerns.append(stripped)
    return concerns


def write_output(claims: list[dict], prioritized_gaps: list[dict], output: Path) -> None:
    """Write claims + gaps analysis as markdown."""
    lines = [
        "# Interview Preparation",
        "",
        "## Claims 总览",
        "",
        f"总 claims: {len(claims)}",
        f"Hero claims: {sum(1 for c in claims if c['is_hero'])}",
        f"总 gaps: {sum(len(c['gaps']) for c in claims)}",
        f"平均 richness: {sum(c['richness_score'] for c in claims) / max(len(claims), 1):.1f}/5",
        "",
        "## 逐 Claim 分析",
        "",
    ]

    for claim in claims:
        lines.extend([
            f"### {claim['claim_id']} {'⭐ HERO' if claim['is_hero'] else ''}",
            f"论点：{claim['claim_text']}",
            f"类型：{claim['claim_type']} | Beat：{claim['beat_hint'] or 'N/A'} | Richness：{claim['richness_score']}/5",
            "",
        ])
        if claim["gaps"]:
            lines.append("缺口：")
            for gap in claim["gaps"]:
                lines.append(f"- [{gap['gap_type']}] {gap['desc']}")
            lines.append("")
        else:
            lines.append("缺口：无（内容已足够丰富）")
            lines.append("")

    lines.extend(["## Gap 优先级队列", "", "AI 运行时应按此顺序构造带假设的问题：", ""])
    for idx, gap in enumerate(prioritized_gaps[:20], 1):
        hero_tag = " ⭐" if gap["is_hero"] else ""
        lines.append(f"{idx}. [{gap['gap_type']}] {gap['topic'][:40]}{hero_tag} (richness: {gap['claim_richness']}/5)")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(claims: list[dict], prioritized_gaps: list[dict], output: Path) -> None:
    """Write claims + gaps as JSON for programmatic consumption."""
    payload = {
        "claims": [
            {
                "claim_id": c["claim_id"],
                "page_no": c["page_no"],
                "claim_text": c["claim_text"],
                "claim_type": c["claim_type"],
                "role": c["role"],
                "beat_hint": c["beat_hint"],
                "is_hero": c["is_hero"],
                "richness_score": c["richness_score"],
                "gaps": c["gaps"],
            }
            for c in claims
        ],
        "prioritized_gaps": prioritized_gaps[:20],
        "summary": {
            "total_claims": len(claims),
            "hero_claims": sum(1 for c in claims if c["is_hero"]),
            "total_gaps": sum(len(c["gaps"]) for c in claims),
            "avg_richness": round(sum(c["richness_score"] for c in claims) / max(len(claims), 1), 1),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract claims, detect gaps, and compute richness for Expert Interview.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--clean-pages")
    parser.add_argument("--state")
    parser.add_argument("--brief")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    clean_pages = Path(args.clean_pages or project_dir / "deck_clean_pages.md").expanduser().resolve()
    state_path = Path(args.state or project_dir / "slide_state.json").expanduser().resolve()
    brief_path = Path(args.brief or project_dir / "deck_brief.md").expanduser().resolve()
    output_md = Path(args.output_md or project_dir / "interview_preparation.md").expanduser().resolve()
    output_json = Path(args.output_json or project_dir / "interview_preparation.json").expanduser().resolve()

    if not clean_pages.exists():
        raise SystemExit(f"[ERROR] clean pages not found: {clean_pages}")

    text = clean_pages.read_text(encoding="utf-8")
    state = load_json(state_path)
    brief_concerns = extract_brief_concerns(brief_path)

    # Extract claims
    claims = extract_claims(text, state)

    # Detect gaps and compute richness for each claim
    for claim in claims:
        claim["gaps"] = detect_gaps(claim, brief_concerns)
        claim["richness_score"] = compute_richness(claim)

    # Prioritize gaps
    prioritized_gaps = prioritize_gaps(claims)

    # Write outputs
    write_output(claims, prioritized_gaps, output_md)
    write_json(claims, prioritized_gaps, output_json)

    hero_count = sum(1 for c in claims if c["is_hero"])
    gap_count = sum(len(c["gaps"]) for c in claims)
    avg_richness = sum(c["richness_score"] for c in claims) / max(len(claims), 1)
    print(f"[OK] {len(claims)} claims extracted, {gap_count} gaps identified, avg richness {avg_richness:.1f}/5")
    print(f"[OK] {hero_count} hero claims, {len(prioritized_gaps)} prioritized gaps")
    print(f"[OK] wrote {output_md}")
    print(f"[OK] wrote {output_json}")


if __name__ == "__main__":
    main()
