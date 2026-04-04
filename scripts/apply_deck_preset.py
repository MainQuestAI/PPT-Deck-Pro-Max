#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def upsert_section(text: str, heading: str, body: str) -> str:
    marker = f"## {heading}"
    if marker in text:
        parts = text.split(marker, 1)
        before = parts[0]
        after = parts[1]
        next_heading_idx = after.find("\n## ")
        if next_heading_idx == -1:
            return f"{before}{marker}\n\n{body.strip()}\n"
        tail = after[next_heading_idx:]
        return f"{before}{marker}\n\n{body.strip()}\n{tail}"
    if not text.endswith("\n"):
        text += "\n"
    return f"{text}\n{marker}\n\n{body.strip()}\n"


def page_id_to_number(page_id: str) -> int | None:
    match = re.search(r"(\d+)", page_id or "")
    return int(match.group(1)) if match else None


def number_to_page_id(page_no: int) -> str:
    return f"slide_{page_no:02d}"


def resolve_locator(locator: str, total_pages: int) -> int:
    normalized = (locator or "").strip().lower()
    if normalized == "first":
        return 1
    if normalized == "last":
        return total_pages
    if normalized.startswith("last-"):
        try:
            return max(1, total_pages - int(normalized.split("-", 1)[1]))
        except ValueError:
            return total_pages
    if normalized.startswith("ratio:"):
        try:
            ratio = float(normalized.split(":", 1)[1])
            return max(1, min(total_pages, round(total_pages * ratio)))
        except ValueError:
            return 1
    if normalized.isdigit():
        return max(1, min(total_pages, int(normalized)))
    return 1


def nearest_available(target: int, total_pages: int, used: set[int]) -> int:
    if target not in used:
        return target
    for offset in range(1, total_pages + 1):
        for candidate in (target - offset, target + offset):
            if 1 <= candidate <= total_pages and candidate not in used:
                return candidate
    return target


def resolve_hero_pages(state: dict, preset: dict) -> list[dict]:
    total_pages = len(state.get("pages", []))
    used: set[int] = set()
    resolved: list[dict] = []
    for item in preset.get("hero_pages", []):
        page_no = page_id_to_number(item.get("page_id", ""))
        if page_no is None:
            page_no = resolve_locator(item.get("locator", ""), total_pages or 1)
        page_no = nearest_available(page_no, total_pages or 1, used)
        used.add(page_no)
        resolved.append(
            {
                **item,
                "page_id": number_to_page_id(page_no),
            }
        )
    return resolved


def apply_to_brief(project_dir: Path, preset: dict) -> None:
    brief_path = project_dir / "deck_brief.md"
    if not brief_path.exists():
        return
    text = brief_path.read_text(encoding="utf-8")
    hints = preset.get("brief_hints", {})
    for heading, body in hints.items():
        text = upsert_section(text, heading, body)
    brief_path.write_text(text, encoding="utf-8")


def apply_to_hero_pages(project_dir: Path, hero_pages: list[dict]) -> None:
    path = project_dir / "deck_hero_pages.md"
    if not path.exists():
        return
    lines = ["# Hero Pages", "", "## 关键页", ""]
    for idx, item in enumerate(hero_pages, start=1):
        lines.append(f"{idx}. {item.get('page_id')} | {item.get('role')} | {item.get('label')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_to_state(project_dir: Path, preset: dict, hero_pages: list[dict]) -> dict | None:
    path = project_dir / "slide_state.json"
    if not path.exists():
        return None
    state = load_json(path)
    roles = {item["page_id"]: item["role"] for item in hero_pages if item.get("page_id") and item.get("role")}
    for page in state.get("pages", []):
        if page.get("page_id") in roles:
            page["role"] = roles[page["page_id"]]
    if preset.get("default_output_mode"):
        state["output_mode"] = preset["default_output_mode"]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a deck preset to project files.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--preset-file", required=True)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    preset = load_json(Path(args.preset_file).expanduser().resolve())
    state = load_json(project_dir / "slide_state.json") if (project_dir / "slide_state.json").exists() else {"pages": []}
    hero_pages = resolve_hero_pages(state, preset)
    apply_to_brief(project_dir, preset)
    apply_to_hero_pages(project_dir, hero_pages)
    apply_to_state(project_dir, preset, hero_pages)
    print(f"[OK] applied preset: {preset.get('name', 'unknown')} -> {project_dir}")


if __name__ == "__main__":
    main()
