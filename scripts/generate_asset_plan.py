#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from page_parser import extract_asset_declarations, extract_page_slices, page_id_to_number


PROOF_ROLES = {"hero_proof", "hero_system", "hero_diff", "hero_value"}
PROOF_BEATS_KEYWORDS = {"proof", "resolution"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def infer_asset_needs(
    clean_pages_text: str,
    state: dict,
) -> list[dict]:
    """Analyze clean pages and slide state to infer which pages need product screenshots."""
    slices = extract_page_slices(clean_pages_text)
    declared = extract_asset_declarations(clean_pages_text)
    role_lookup = {
        page_id_to_number(p.get("page_id", "")): p
        for p in state.get("pages", [])
        if page_id_to_number(p.get("page_id", ""))
    }

    needs: list[dict] = []
    for page_no in sorted(slices.keys()):
        section = slices[page_no]
        page_info = role_lookup.get(page_no, {})
        role = page_info.get("role", "")
        page_id = page_info.get("page_id", f"slide_{page_no:02d}")

        # Already declared in clean_pages
        if page_no in declared:
            for decl in declared[page_no]:
                needs.append({
                    "page_id": page_id,
                    "page_no": page_no,
                    "role": role,
                    "priority": "high" if role in PROOF_ROLES else "medium",
                    "source": "declared",
                    **decl,
                })
            continue

        # Auto-detect: hero/proof roles likely need screenshots
        if role in PROOF_ROLES:
            needs.append({
                "page_id": page_id,
                "page_no": page_no,
                "role": role,
                "priority": "high",
                "source": "inferred",
                "id": f"{page_id}_screenshot",
                "desc": f"（需要确认）{role} 页面的产品截图",
                "frame": "macbook",
                "position": "right",
            })

    return needs


def write_asset_plan(needs: list[dict], output: Path) -> None:
    lines = [
        "# Asset Plan",
        "",
        "## 配图需求总览",
        "",
        "| 页码 | 角色 | 需要什么 | 优先级 | 来源 |",
        "|------|------|---------|--------|------|",
    ]
    for item in needs:
        lines.append(
            f"| 第 {item['page_no']} 页 | {item['role']} | {item.get('desc', '')} | {item['priority']} | {item['source']} |"
        )

    lines.extend(["", "## 逐页配图说明", ""])
    for item in needs:
        lines.extend([
            f"### 第 {item['page_no']} 页 — {item.get('desc', item['role'])}",
            "",
            f"- ID: `{item.get('id', '')}`",
            f"- 设备壳: {item.get('frame', 'macbook')}",
            f"- 位置建议: {item.get('position', 'right')}",
            f"- URL: {item.get('url', '（待用户提供）')}",
            f"- 优先级: {item['priority']}",
            "",
        ])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_asset_manifest(needs: list[dict], output: Path) -> None:
    assets = []
    for item in needs:
        has_url = bool(item.get("url"))
        source_mode = "capture" if has_url else "generate"
        asset_type = "product_screenshot" if has_url else "generated_visual"
        assets.append({
            "id": item.get("id", f"{item['page_id']}_screenshot"),
            "page_id": item["page_id"],
            "desc": item.get("desc", ""),
            "source": "url" if has_url else item.get("source", "pending"),
            "source_mode": source_mode,
            "asset_type": asset_type,
            "generation_mode": "capture" if has_url else "gptimage2",
            "url": item.get("url", ""),
            "status": "pending",
            "style_group": "deck_primary",
            "reuse_key": item.get("id", f"{item['page_id']}_screenshot"),
            "prompt_intent": item.get("desc", ""),
            "aspect_ratio": "16:9",
            "variant_count": 2 if not has_url else 1,
            "batch_id": "",
            "content_hash": "",
            "stale": False,
            "selected_variant": "",
            "generated_at": "",
            "prompt_payload": {
                "page_id": item["page_id"],
                "page_no": item.get("page_no"),
                "role": item.get("role", ""),
                "brief": item.get("desc", ""),
                "frame": item.get("frame", "macbook"),
                "position": item.get("position", "right"),
            },
            "raw_path": "",
            "final_path": "",
            "frame": item.get("frame", "macbook"),
            "position": item.get("position", "right"),
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"assets": assets}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an asset plan from clean pages and slide state.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--clean-pages")
    parser.add_argument("--state")
    parser.add_argument("--output")
    parser.add_argument("--manifest")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    clean_pages = Path(args.clean_pages or project_dir / "deck_clean_pages.md").expanduser().resolve()
    state_path = Path(args.state or project_dir / "slide_state.json").expanduser().resolve()
    output = Path(args.output or project_dir / "deck_asset_plan.md").expanduser().resolve()
    manifest = Path(args.manifest or project_dir / "asset_manifest.json").expanduser().resolve()

    if not clean_pages.exists():
        raise SystemExit(f"[ERROR] clean pages not found: {clean_pages}")

    clean_text = clean_pages.read_text(encoding="utf-8")
    state = load_json(state_path)
    needs = infer_asset_needs(clean_text, state)

    write_asset_plan(needs, output)
    write_asset_manifest(needs, manifest)
    print(f"[OK] wrote asset plan: {output}")
    print(f"[OK] wrote asset manifest: {manifest}")
    print(f"[OK] {len(needs)} asset(s) identified")


if __name__ == "__main__":
    main()
