#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def extract_section(markdown: str, title: str) -> str:
    pattern = re.compile(rf"^##\s*{re.escape(title)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", markdown[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end].strip()


def infer_material_finish(theme_name: str) -> str:
    lowered = (theme_name or "").lower()
    if "light" in lowered or "paper" in lowered:
        return "paper architecture"
    if "glass" in lowered or "dark" in lowered:
        return "glass editorial"
    return "editorial product-grade"


def build_style_lock(vibe_text: str, visual_system_text: str, theme_tokens: dict, vibe_path: Path, theme_path: Path, visual_system_path: Path) -> dict:
    theme_name = str(theme_tokens.get("theme", "default"))
    palette = theme_tokens.get("colors", {}) if isinstance(theme_tokens.get("colors"), dict) else {}
    return {
        "version": 1,
        "style_id": f"{theme_name or 'default'}-style-lock",
        "visual_mood": extract_section(vibe_text, "视觉气质") or "高密度、产品级、连续视觉系统",
        "color_system": extract_section(vibe_text, "配色系统") or theme_name or "default",
        "typography": extract_section(vibe_text, "字体系统") or "延续 theme tokens 的标题/正文层级",
        "graphic_language": extract_section(vibe_text, "图形语言") or "产品界面 + 图表主角 + editorial 质感",
        "density_ceiling": extract_section(vibe_text, "密度上限") or "单页可独立阅读，但保留明确视觉主角",
        "palette": palette,
        "visual_rules": {
            "material_finish": infer_material_finish(theme_name),
            "lighting": "soft studio",
            "perspective": "three-quarter editorial",
            "text_in_image": "avoid",
            "negative_prompts": [
                "random stock photo look",
                "generic ai poster look",
                "floating text embedded in image",
                "inconsistent camera angle across slides",
            ],
            "system_cues": extract_section(visual_system_text, "视觉特征锁定") or "沿用 deck_visual_system 的组件和视觉母体",
        },
        "source_files": {
            "deck_vibe_brief": str(vibe_path.resolve()),
            "deck_theme_tokens": str(theme_path.resolve()),
            "deck_visual_system": str(visual_system_path.resolve()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deck-level style_lock.json from vibe/theme/visual system.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--vibe")
    parser.add_argument("--theme-tokens")
    parser.add_argument("--visual-system")
    parser.add_argument("--output")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    vibe_path = Path(args.vibe or project_dir / "deck_vibe_brief.md").expanduser().resolve()
    theme_path = Path(args.theme_tokens or project_dir / "deck_theme_tokens.json").expanduser().resolve()
    visual_system_path = Path(args.visual_system or project_dir / "deck_visual_system.md").expanduser().resolve()
    output = Path(args.output or project_dir / "style_lock.json").expanduser().resolve()

    payload = build_style_lock(
        read_text(vibe_path),
        read_text(visual_system_path),
        load_json(theme_path),
        vibe_path,
        theme_path,
        visual_system_path,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote style lock: {output}")


if __name__ == "__main__":
    main()
