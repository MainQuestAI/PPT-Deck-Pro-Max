#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from page_parser import extract_page_slices


ROLE_TO_ARCHETYPE = {
    "hero_cover": "hero_cover",
    "hero_problem": "diagnostic_board",
    "hero_proof": "proof_board",
    "hero_system": "system_map",
    "hero_diff": "comparison_board",
    "hero_value": "value_stack",
    "hero_cta": "cta_board",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_skeletons(path: Path | None) -> dict[int, dict]:
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    sections = extract_page_slices(text)
    parsed: dict[int, dict] = {}
    for page_no, section in sections.items():
        info: dict[str, str] = {}
        for line in section.splitlines():
            match = re.match(r"^\s*-\s*([^:：]+)\s*[:：]\s*(.+?)\s*$", line)
            if match:
                info[match.group(1).strip()] = match.group(2).strip()
        parsed[page_no] = info
    return parsed


def default_page_manifest(page_id: str, role: str, skeleton: dict | None) -> dict:
    skeleton = skeleton or {}
    archetype = skeleton.get("archetype") or ROLE_TO_ARCHETYPE.get(role, "content_board")
    occupancy_target = skeleton.get("预期占比", "0.42")
    try:
        occupancy_value = float(re.findall(r"\d+(?:\.\d+)?", occupancy_target)[0])
    except Exception:
        occupancy_value = 0.42
    return {
        "page_id": page_id,
        "role": role,
        "archetype": archetype,
        "main_group": {
            "center_x": 0.50,
            "expected_center_x": 0.50,
            "tolerance": 0.06,
        },
        "occupancy": {
            "ratio": occupancy_value,
            "min": max(0.18, occupancy_value - 0.12),
            "max": min(0.90, occupancy_value + 0.18),
        },
        "alignment_groups": [],
        "connectors": [],
        "cards": [],
        "skeleton": {
            "主体区边界": skeleton.get("主体区边界", ""),
            "主视觉边界": skeleton.get("主视觉边界", ""),
            "对齐轴": skeleton.get("对齐轴", ""),
            "组件组关系": skeleton.get("组件组关系", ""),
            "预期占比": skeleton.get("预期占比", ""),
        },
    }


def build_manifest(state: dict, skeletons: dict[int, dict], existing: dict | None = None) -> dict:
    existing_lookup = {
        item.get("page_id"): item
        for item in (existing or {}).get("pages", [])
        if isinstance(item, dict) and item.get("page_id")
    }
    pages: list[dict] = []
    for page in state.get("pages", []):
        page_id = page.get("page_id", "")
        match = re.search(r"(\d+)", page_id)
        page_no = int(match.group(1)) if match else 0
        merged = default_page_manifest(page_id, page.get("role", "unassigned"), skeletons.get(page_no))
        if page_id in existing_lookup:
            current = existing_lookup[page_id]
            for key in ("main_group", "occupancy", "alignment_groups", "connectors", "cards"):
                if current.get(key):
                    merged[key] = current[key]
            if current.get("archetype"):
                merged["archetype"] = current["archetype"]
        pages.append(merged)
    return {"pages": pages}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or refresh layout_manifest.json from slide state and page skeletons.")
    parser.add_argument("--project-dir")
    parser.add_argument("--state")
    parser.add_argument("--skeletons")
    parser.add_argument("--output")
    parser.add_argument("--merge-existing", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve() if args.project_dir else None
    state_path = Path(args.state).expanduser().resolve() if args.state else (project_dir / "slide_state.json" if project_dir else None)
    skeleton_path = Path(args.skeletons).expanduser().resolve() if args.skeletons else (project_dir / "deck_page_skeletons.md" if project_dir else None)
    output_path = Path(args.output).expanduser().resolve() if args.output else (project_dir / "layout_manifest.json" if project_dir else None)
    if not state_path or not output_path:
        raise SystemExit("[ERROR] 需要提供 --project-dir 或同时提供 --state 与 --output。")
    if not state_path.exists():
        raise SystemExit(f"[ERROR] slide_state.json not found: {state_path}")

    state = load_json(state_path)
    skeletons = parse_skeletons(skeleton_path)
    existing = load_json(output_path) if args.merge_existing and output_path.exists() else None
    manifest = build_manifest(state, skeletons, existing)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_path}")


if __name__ == "__main__":
    main()
