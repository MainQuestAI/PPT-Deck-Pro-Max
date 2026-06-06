#!/usr/bin/env python3
"""Shared helpers for content governance artifacts.

The P0 gate is intentionally conservative: AI authors the governance files,
while scripts validate structure, blocking gaps, and page-capacity risk.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CONTENT_GOVERNANCE_ARTIFACTS = [
    "deck_source_digest.md",
    "deck_claim_map.json",
    "deck_capacity_plan.md",
    "deck_capacity_plan.json",
    "deck_gap_registry.json",
    "deck_question_queue.md",
]

CONTENT_GOVERNANCE_JSON_ARTIFACTS = [
    "deck_claim_map.json",
    "deck_capacity_plan.json",
    "deck_gap_registry.json",
]

CONTENT_GOVERNANCE_MARKDOWN_ARTIFACTS = [
    "deck_source_digest.md",
    "deck_capacity_plan.md",
    "deck_question_queue.md",
]

LONGFORM_GOVERNANCE_ARTIFACTS = [
    "deck_section_packages.md",
    "section_packages.json",
]

BUDGET_TIER_ORDER = ["conservative", "recommended", "extended", "appendix_heavy"]

KNOWN_DENSE_ARCHETYPES = {
    "evidence_wall",
    "decision_matrix",
    "three_layer_diagnostic",
    "roadmap_risk_sidebar",
    "case_breakdown",
    "appendix_reference",
}

PLACEHOLDER_SIGNALS = [
    "待提炼",
    "待填写",
    "待登记",
    "由 expert-interview 生成",
    "待拆包",
]

BLOCKING_STATUSES = {
    "blocked",
    "blocking",
    "must_fill",
    "required",
    "open_blocking",
    "unresolved_blocking",
}

BLOCKING_SEVERITIES = {"blocking", "critical", "p0"}


def read_json_file(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, f"file not found: {path.name}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"{path.name}: {exc}"


def _first_text(item: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _as_page_no(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group(0))
    return None


def _as_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        nums = re.findall(r"\d+", value)
        if nums:
            return int(nums[-1])
    return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1", "on"}:
            return True
        if normalized in {"false", "no", "n", "0", "off", ""}:
            return False
    return False


def _find_number(data: dict, keys: list[str]) -> int | None:
    for key in keys:
        if "." in key:
            current: Any = data
            for part in key.split("."):
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(part)
            value = current
        else:
            value = data.get(key)
        number = _as_number(value)
        if number is not None:
            return number
    return None


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,，、\n]+", value) if item.strip()]
    return [value]


def _as_text_set(value: Any) -> set[str]:
    return {str(item).strip() for item in _as_list(value) if str(item).strip()}


def _page_count_from_section(section: dict) -> int:
    for key in ("page_count", "pages", "page_quota", "target_pages"):
        number = _as_number(section.get(key))
        if number is not None:
            return number
    page_ids = _as_list(section.get("page_ids"))
    if page_ids:
        return len(page_ids)
    start = _as_number(section.get("page_start"))
    end = _as_number(section.get("page_end"))
    if start is not None and end is not None and end >= start:
        return end - start + 1
    return 0


def _join_evidence(item: dict) -> str:
    evidence = item.get("evidence") or item.get("sources") or item.get("proof")
    if not evidence:
        return ""
    if isinstance(evidence, str):
        return evidence
    if isinstance(evidence, list):
        parts: list[str] = []
        for entry in evidence:
            if isinstance(entry, dict):
                parts.append(_first_text(entry, ["text", "summary", "source", "desc", "description"]))
            elif entry is not None:
                parts.append(str(entry))
        return "\n".join(part for part in parts if part)
    if isinstance(evidence, dict):
        return "\n".join(str(v) for v in evidence.values() if v)
    return str(evidence)


def _claim_entries(claim_map: Any) -> list[dict]:
    if isinstance(claim_map, list):
        return [item for item in claim_map if isinstance(item, dict)]
    if not isinstance(claim_map, dict):
        return []
    for key in ("claims", "claim_map", "items"):
        value = claim_map.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    sections = claim_map.get("sections")
    if isinstance(sections, list):
        entries: list[dict] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_claims = section.get("claims")
            if isinstance(section_claims, list):
                for claim in section_claims:
                    if isinstance(claim, dict):
                        merged = dict(claim)
                        merged.setdefault("section", section.get("section") or section.get("title"))
                        entries.append(merged)
        return entries
    return []


def normalize_claims(claim_map: Any) -> list[dict]:
    claims: list[dict] = []
    for idx, item in enumerate(_claim_entries(claim_map), 1):
        claim_id = _first_text(item, ["claim_id", "id"], f"claim_{idx:02d}")
        page_no = _as_page_no(item.get("page_no") or item.get("page") or item.get("page_id"))
        if page_no is None:
            source_pages = item.get("source_pages")
            if isinstance(source_pages, list) and source_pages:
                page_no = _as_page_no(source_pages[0])
        source_pages = item.get("source_pages")
        if isinstance(source_pages, list):
            normalized_source_pages = [_as_page_no(page) for page in source_pages]
            normalized_source_pages = [page for page in normalized_source_pages if page is not None]
        else:
            normalized_source_pages = []
        if not normalized_source_pages and page_no is not None:
            normalized_source_pages = [page_no]

        role = _first_text(item, ["role", "page_role"], "unassigned")
        claim_text = _first_text(
            item,
            ["claim_text", "text", "statement", "title", "claim", "summary"],
            f"Claim {idx}",
        )
        evidence_text = _join_evidence(item)
        full_text = _first_text(item, ["full_text", "context", "source_text", "description"], claim_text)
        if evidence_text:
            full_text = f"{full_text}\n{evidence_text}"

        claims.append({
            "claim_id": claim_id,
            "page_no": page_no or idx,
            "source_pages": normalized_source_pages or [page_no or idx],
            "claim_text": claim_text,
            "subtitle": _first_text(item, ["subtitle"], ""),
            "claim_type": _first_text(item, ["claim_type", "type"], "assertion"),
            "role": role,
            "beat_hint": _first_text(item, ["beat_hint", "beat"], ""),
            "full_text": full_text,
            "gaps": item.get("gaps") if isinstance(item.get("gaps"), list) else [],
            "richness_score": item.get("richness_score"),
            "is_hero": bool(item.get("is_hero")) or role.startswith("hero_"),
        })
    return claims


def normalize_gap_registry(gap_registry: Any) -> list[dict]:
    if isinstance(gap_registry, list):
        items = gap_registry
    elif isinstance(gap_registry, dict):
        items = []
        for key in ("gaps", "items"):
            value = gap_registry.get(key)
            if isinstance(value, list):
                items.extend(value)
        blocking = gap_registry.get("blocking_gaps")
        if isinstance(blocking, list):
            for item in blocking:
                if isinstance(item, dict):
                    merged = dict(item)
                    merged["blocking"] = True
                    items.append(merged)
    else:
        items = []

    normalized: list[dict] = []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        normalized.append({
            "gap_id": _first_text(item, ["gap_id", "id"], f"gap_{idx:02d}"),
            "claim_id": _first_text(item, ["claim_id", "claim"], ""),
            "gap_type": _first_text(item, ["gap_type", "type"], "unknown"),
            "topic": _first_text(item, ["topic", "title", "claim_text"], ""),
            "desc": _first_text(item, ["desc", "description", "reason"], ""),
            "status": _first_text(item, ["status"], "open"),
            "severity": _first_text(item, ["severity", "priority"], ""),
            "blocking": _as_bool(item.get("blocking")),
        })
    return normalized


def is_blocking_gap(gap: dict) -> bool:
    status = str(gap.get("status", "")).strip().lower()
    severity = str(gap.get("severity", "")).strip().lower()
    return _as_bool(gap.get("blocking")) or status in BLOCKING_STATUSES or severity in BLOCKING_SEVERITIES


def markdown_artifact_issue(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"markdown_unreadable:{path.name}:{exc}"
    meaningful_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.strip().startswith("#")
        and not set(line.strip()) <= {"|", "-", " "}
    ]
    if not meaningful_lines:
        return f"markdown_empty:{path.name}"
    if any(signal in text for signal in PLACEHOLDER_SIGNALS):
        return f"markdown_placeholder:{path.name}"
    return None


def attach_registry_gaps(claims: list[dict], registry_gaps: list[dict]) -> list[dict]:
    by_claim: dict[str, list[dict]] = {}
    for gap in registry_gaps:
        claim_id = gap.get("claim_id")
        if claim_id:
            by_claim.setdefault(str(claim_id), []).append(gap)
    for claim in claims:
        existing = claim.get("gaps") if isinstance(claim.get("gaps"), list) else []
        seen = {(gap.get("gap_type"), gap.get("desc")) for gap in existing if isinstance(gap, dict)}
        for gap in by_claim.get(str(claim.get("claim_id")), []):
            marker = (gap.get("gap_type"), gap.get("desc"))
            if marker not in seen:
                existing.append(gap)
        claim["gaps"] = existing
    return claims


def capacity_summary(capacity_plan: Any, project_dir: Path | None = None) -> dict:
    data = capacity_plan if isinstance(capacity_plan, dict) else {}
    target_pages = _find_number(data, [
        "target_pages",
        "planned_pages",
        "requested_pages",
        "page_budget.target_pages",
        "deck.target_pages",
    ])
    if target_pages is None and project_dir is not None:
        state_data, _ = read_json_file(project_dir / "slide_state.json")
        if isinstance(state_data, dict):
            pages = state_data.get("pages")
            if isinstance(pages, list) and pages:
                target_pages = len(pages)

    recommended_pages = _find_number(data, [
        "recommended_pages",
        "recommended_page_count",
        "page_budget.recommended_pages",
        "deck.recommended_pages",
    ])
    max_supported_pages = _find_number(data, [
        "max_supported_pages",
        "supported_pages",
        "capacity_pages",
        "recommended_max_pages",
        "page_budget.max_supported_pages",
        "deck.max_supported_pages",
    ])
    if max_supported_pages is None:
        max_supported_pages = recommended_pages

    over_capacity = (
        target_pages is not None
        and max_supported_pages is not None
        and target_pages > max_supported_pages
    )
    return {
        "target_pages": target_pages,
        "recommended_pages": recommended_pages,
        "max_supported_pages": max_supported_pages,
        "over_capacity": over_capacity,
        "budget_summary": budget_summary(data, target_pages),
    }


def _budget_tier_entries(data: dict) -> dict[str, dict]:
    raw = data.get("budget_tiers") or data.get("page_budget_tiers") or data.get("tiers")
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    if isinstance(raw, list):
        entries: dict[str, dict] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            tier = item.get("tier") or item.get("name") or item.get("id")
            if tier:
                entries[str(tier)] = item
        return entries
    return {}


def _tier_page_count(tier: dict) -> int | None:
    return _find_number(tier, ["pages", "page_count", "total_pages", "target_pages", "max_pages"])


def _tier_has_extension_plan(tier: dict) -> bool:
    fields = [
        "required_inputs",
        "needs",
        "supplemental_info",
        "required_supplements",
        "appendix_sources",
        "assumptions",
    ]
    return any(_as_list(tier.get(field)) for field in fields)


def budget_summary(capacity_plan: Any, target_pages: int | None = None) -> dict:
    data = capacity_plan if isinstance(capacity_plan, dict) else {}
    entries = _budget_tier_entries(data)
    tiers: dict[str, dict] = {}
    for tier_name in BUDGET_TIER_ORDER:
        tier = entries.get(tier_name, {})
        if not isinstance(tier, dict):
            tier = {}
        tiers[tier_name] = {
            "pages": _tier_page_count(tier),
            "core_pages": _as_number(tier.get("core_pages")),
            "proof_pages": _as_number(tier.get("proof_pages")),
            "extension_pages": _as_number(tier.get("extension_pages")),
            "appendix_pages": _as_number(tier.get("appendix_pages")),
            "required_inputs": _as_list(tier.get("required_inputs") or tier.get("needs") or tier.get("supplemental_info")),
            "has_extension_plan": _tier_has_extension_plan(tier),
        }
    missing_tiers = [name for name in BUDGET_TIER_ORDER if name not in entries]
    recommended_pages = tiers["recommended"]["pages"] or _find_number(data, ["recommended_pages", "recommended_page_count"])
    max_tier_pages = max((tier["pages"] or 0 for tier in tiers.values()), default=0) or None
    target_over_recommended = (
        target_pages is not None
        and recommended_pages is not None
        and target_pages > recommended_pages
    )
    target_exceeds_all_tiers = (
        target_pages is not None
        and max_tier_pages is not None
        and target_pages > max_tier_pages
    )
    has_extension_strategy = (
        tiers["extended"]["has_extension_plan"]
        or tiers["appendix_heavy"]["has_extension_plan"]
        or (tiers["appendix_heavy"]["appendix_pages"] or 0) > 0
    )
    return {
        "tiers": tiers,
        "missing_tiers": missing_tiers,
        "target_over_recommended": target_over_recommended,
        "target_exceeds_all_tiers": target_exceeds_all_tiers,
        "has_extension_strategy": has_extension_strategy,
        "max_tier_pages": max_tier_pages,
    }


def _brief_is_quick(project_dir: Path) -> bool:
    brief_path = project_dir / "deck_brief.md"
    if not brief_path.exists():
        return False
    return "production_mode: quick" in brief_path.read_text(encoding="utf-8")


def summarize_content_governance(project_dir: Path) -> dict:
    project_dir = project_dir.expanduser().resolve()
    missing_artifacts = [name for name in CONTENT_GOVERNANCE_ARTIFACTS if not (project_dir / name).exists()]
    invalid_artifacts: dict[str, str] = {}
    loaded: dict[str, Any] = {}
    for name in CONTENT_GOVERNANCE_JSON_ARTIFACTS:
        path = project_dir / name
        data, err = read_json_file(path)
        if err:
            if path.exists():
                invalid_artifacts[name] = err
        else:
            loaded[name] = data
    markdown_issues = [
        issue
        for name in CONTENT_GOVERNANCE_MARKDOWN_ARTIFACTS
        for issue in [markdown_artifact_issue(project_dir / name)]
        if issue
    ]

    claims = normalize_claims(loaded.get("deck_claim_map.json"))
    gaps = normalize_gap_registry(loaded.get("deck_gap_registry.json"))
    blocking_gaps = [gap for gap in gaps if is_blocking_gap(gap)]
    capacity = capacity_summary(loaded.get("deck_capacity_plan.json"), project_dir)

    issues: list[str] = []
    issues.extend(f"missing_artifact:{name}" for name in missing_artifacts)
    issues.extend(f"invalid_json:{name}" for name in sorted(invalid_artifacts))
    issues.extend(markdown_issues)
    if "deck_claim_map.json" in loaded and not claims:
        issues.append("claim_map_empty")
    if "deck_capacity_plan.json" in loaded:
        if capacity["max_supported_pages"] is None:
            issues.append("capacity_missing_max_supported_pages")
        if capacity["target_pages"] is None:
            issues.append("capacity_missing_target_pages")
        if capacity["over_capacity"]:
            issues.append(
                f"capacity_over_target:{capacity['target_pages']}>{capacity['max_supported_pages']}"
            )
    if blocking_gaps:
        ids = ",".join(gap.get("gap_id", "unknown") for gap in blocking_gaps[:8])
        issues.append(f"blocking_gaps:{ids}")

    enabled = not _brief_is_quick(project_dir) and (
        bool(claims)
        or any((project_dir / name).exists() for name in CONTENT_GOVERNANCE_ARTIFACTS)
    )
    review_ready = enabled and not issues and not missing_artifacts
    return {
        "enabled": enabled,
        "review_ready": review_ready,
        "missing_artifacts": missing_artifacts,
        "invalid_artifacts": invalid_artifacts,
        "capacity": capacity,
        "claim_summary": {
            "total_claims": len(claims),
            "hero_claims": sum(1 for claim in claims if claim.get("is_hero")),
        },
        "gap_summary": {
            "total_gaps": len(gaps),
            "blocking_gaps": len(blocking_gaps),
            "open_gaps": sum(1 for gap in gaps if str(gap.get("status", "")).lower() == "open"),
        },
        "blocking_gap_ids": [gap.get("gap_id", "unknown") for gap in blocking_gaps],
        "issues": issues,
        "review_focus": [
            "核对目标页数是否超过当前资料容量",
            "优先补齐 blocking gap，再进入逐页稿",
            "确认 claim map 中的核心论点都有来源或证据锚点",
        ] if enabled else [],
    }


def validate_content_governance(project_dir: Path) -> tuple[list[str], dict]:
    summary = summarize_content_governance(project_dir)
    errors = list(summary.get("issues", []))
    return errors, summary


def load_section_packages(project_dir: Path) -> tuple[dict, str | None]:
    data, err = read_json_file(project_dir / "section_packages.json")
    if err:
        return {}, err
    return data if isinstance(data, dict) else {}, None


def normalize_sections(section_packages: Any) -> list[dict]:
    if isinstance(section_packages, list):
        raw_sections = section_packages
    elif isinstance(section_packages, dict):
        raw_sections = section_packages.get("sections", [])
    else:
        raw_sections = []
    sections: list[dict] = []
    for idx, section in enumerate(raw_sections, 1):
        if not isinstance(section, dict):
            continue
        section_id = _first_text(section, ["section_id", "id"], f"section_{idx:02d}")
        page_ids = [str(item) for item in _as_list(section.get("page_ids"))]
        if not page_ids:
            start = _as_number(section.get("page_start"))
            end = _as_number(section.get("page_end"))
            if start is not None and end is not None and end >= start:
                page_ids = [f"slide_{page_no:02d}" for page_no in range(start, end + 1)]
        suggested = _as_list(
            section.get("suggested_archetypes")
            or section.get("dense_archetypes")
            or section.get("suggested_dense_archetypes")
        )
        sections.append({
            "section_id": section_id,
            "title": _first_text(section, ["title", "section_title"], section_id),
            "objective": _first_text(section, ["objective", "goal", "section_goal"], ""),
            "page_count": _page_count_from_section(section),
            "page_ids": page_ids,
            "claim_ids": [str(item) for item in _as_list(section.get("claim_ids"))],
            "allowed_evidence": [str(item) for item in _as_list(section.get("allowed_evidence"))],
            "allowed_topics": [str(item) for item in _as_list(section.get("allowed_topics"))],
            "forbidden_topics": [str(item) for item in _as_list(section.get("forbidden_topics"))],
            "input_transition": _first_text(section, ["input_transition", "from_previous"], ""),
            "output_transition": _first_text(section, ["output_transition", "to_next"], ""),
            "density_level": _first_text(section, ["density_level", "density"], ""),
            "suggested_archetypes": [str(item) for item in suggested],
            "dense_archetype": _first_text(section, ["dense_archetype"], ""),
            "raw": section,
        })
    return sections


def section_package_summary(project_dir: Path, capacity: dict) -> dict:
    payload, err = load_section_packages(project_dir)
    sections = normalize_sections(payload)
    issues: list[str] = []
    if err:
        issues.append(f"invalid_section_packages:{err}")
    if not sections:
        issues.append("section_packages_empty")

    required_fields = ["objective", "input_transition", "output_transition"]
    for section in sections:
        for field in required_fields:
            if not section.get(field):
                issues.append(f"section_missing_{field}:{section['section_id']}")
        if section["page_count"] <= 0:
            issues.append(f"section_missing_page_count:{section['section_id']}")
        if not section["page_ids"]:
            issues.append(f"section_missing_page_ids:{section['section_id']}")
        if not section["suggested_archetypes"] and not section["dense_archetype"]:
            issues.append(f"section_missing_archetype:{section['section_id']}")

    target_pages = capacity.get("target_pages")
    total_pages = sum(section["page_count"] for section in sections)
    if target_pages is not None and total_pages and total_pages != target_pages:
        issues.append(f"section_page_total_mismatch:{total_pages}!={target_pages}")

    page_owner: dict[str, str] = {}
    duplicate_pages: list[str] = []
    for section in sections:
        for page_id in section["page_ids"]:
            if page_id in page_owner and page_owner[page_id] != section["section_id"]:
                duplicate_pages.append(page_id)
            page_owner[page_id] = section["section_id"]
    if duplicate_pages:
        issues.append("duplicate_page_assignment:" + ",".join(sorted(set(duplicate_pages))[:12]))

    state_data, _ = read_json_file(project_dir / "slide_state.json")
    state_pages = []
    if isinstance(state_data, dict):
        state_pages = [
            str(page.get("page_id"))
            for page in state_data.get("pages", [])
            if isinstance(page, dict) and page.get("page_id")
        ]
    if state_pages:
        unassigned = sorted(set(state_pages) - set(page_owner))
        unknown = sorted(set(page_owner) - set(state_pages))
        if unassigned:
            issues.append("unassigned_pages:" + ",".join(unassigned[:12]))
        if unknown:
            issues.append("unknown_page_ids:" + ",".join(unknown[:12]))

    claim_owner: dict[str, str] = {}
    duplicate_claims: list[str] = []
    for section in sections:
        for claim_id in section["claim_ids"]:
            if claim_id in claim_owner and claim_owner[claim_id] != section["section_id"]:
                duplicate_claims.append(claim_id)
            claim_owner[claim_id] = section["section_id"]
    if duplicate_claims:
        issues.append("duplicate_claim_assignment:" + ",".join(sorted(set(duplicate_claims))[:8]))

    forbidden_by_section = {section["section_id"]: _as_text_set(section["forbidden_topics"]) for section in sections}
    allowed_by_section = {section["section_id"]: _as_text_set(section["allowed_topics"]) for section in sections}
    conflicts: list[str] = []
    for section_id, forbidden in forbidden_by_section.items():
        for other_id, allowed in allowed_by_section.items():
            if section_id == other_id:
                continue
            overlap = sorted(forbidden & allowed)
            if overlap:
                conflicts.append(f"{section_id}->{other_id}:{','.join(overlap[:4])}")
    if conflicts:
        issues.append("forbidden_topic_conflict:" + ";".join(conflicts[:4]))

    dense_sections = [
        section for section in sections
        if section["density_level"].lower() in {"high", "dense", "高", "高密度"}
        or section["dense_archetype"]
    ]
    unknown_dense: list[str] = []
    missing_dense: list[str] = []
    for section in dense_sections:
        dense_id = section["dense_archetype"] or next((a for a in section["suggested_archetypes"] if a in KNOWN_DENSE_ARCHETYPES), "")
        if not dense_id:
            missing_dense.append(section["section_id"])
        elif dense_id not in KNOWN_DENSE_ARCHETYPES:
            unknown_dense.append(f"{section['section_id']}:{dense_id}")
    if missing_dense:
        issues.append("dense_archetype_missing:" + ",".join(missing_dense[:8]))
    if unknown_dense:
        issues.append("dense_archetype_unknown:" + ",".join(unknown_dense[:8]))

    return {
        "sections": sections,
        "total_sections": len(sections),
        "total_pages": total_pages,
        "target_pages": target_pages,
        "dense_sections": len(dense_sections),
        "known_dense_archetypes": sorted(KNOWN_DENSE_ARCHETYPES),
        "issues": issues,
    }


def summarize_longform_governance(project_dir: Path) -> dict:
    content_errors, content_summary = validate_content_governance(project_dir)
    capacity = content_summary.get("capacity", {})
    budget = capacity.get("budget_summary", {})
    section_summary = section_package_summary(project_dir, capacity)
    markdown_issue = markdown_artifact_issue(project_dir / "deck_section_packages.md")

    issues: list[str] = []
    issues.extend(f"content:{issue}" for issue in content_errors)
    missing = [name for name in LONGFORM_GOVERNANCE_ARTIFACTS if not (project_dir / name).exists()]
    issues.extend(f"missing_artifact:{name}" for name in missing)
    if markdown_issue:
        issues.append(markdown_issue)
    missing_tiers = budget.get("missing_tiers", [])
    if missing_tiers:
        issues.append("budget_tiers_missing:" + ",".join(missing_tiers))
    tiers = budget.get("tiers", {})
    missing_pages = [name for name in BUDGET_TIER_ORDER if isinstance(tiers.get(name), dict) and tiers[name].get("pages") is None]
    if missing_pages:
        issues.append("budget_tier_missing_pages:" + ",".join(missing_pages))
    missing_mix = []
    for name in BUDGET_TIER_ORDER:
        tier = tiers.get(name, {})
        if not isinstance(tier, dict):
            continue
        mix_fields = ["core_pages", "proof_pages", "extension_pages", "appendix_pages"]
        if all(tier.get(field) is None for field in mix_fields):
            missing_mix.append(name)
    if missing_mix:
        issues.append("budget_tier_missing_page_mix:" + ",".join(missing_mix))
    if budget.get("target_exceeds_all_tiers"):
        issues.append("budget_target_exceeds_all_tiers")
    if budget.get("target_over_recommended") and not budget.get("has_extension_strategy"):
        issues.append("budget_requires_extension_strategy")
    issues.extend(section_summary.get("issues", []))

    enabled = not _brief_is_quick(project_dir) and (
        any((project_dir / name).exists() for name in LONGFORM_GOVERNANCE_ARTIFACTS)
        or bool(section_summary.get("sections"))
    )
    return {
        "enabled": enabled,
        "review_ready": enabled and not issues,
        "content_governance_summary": content_summary,
        "budget_summary": budget,
        "section_summary": {
            "total_sections": section_summary["total_sections"],
            "total_pages": section_summary["total_pages"],
            "target_pages": section_summary["target_pages"],
            "dense_sections": section_summary["dense_sections"],
        },
        "known_dense_archetypes": section_summary["known_dense_archetypes"],
        "issues": issues,
        "review_focus": [
            "确认目标页数落在已声明的预算档位内",
            "确认每个章节包都有页数配额、证据复用边界和过渡要求",
            "确认高密度章节已绑定 dense archetype",
        ] if enabled else [],
    }


def validate_longform_governance(project_dir: Path) -> tuple[list[str], dict]:
    summary = summarize_longform_governance(project_dir)
    return list(summary.get("issues", [])), summary
