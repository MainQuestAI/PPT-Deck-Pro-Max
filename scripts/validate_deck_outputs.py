#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required deck outputs exist.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--output-mode", default="pptx+html", choices=["pptx", "html", "pptx+html"])
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    required = [
        "deck_brief.md",
        "deck_vibe_brief.md",
        "deck_hero_pages.md",
        "deck_layout_v1.md",
        "deck_clean_pages.md",
        "deck_visual_system.md",
        "deck_component_tokens.md",
        "deck_theme_tokens.json",
        "slide_state.json",
    ]
    if args.output_mode in {"pptx", "pptx+html"}:
        required.append("v1.pptx")
    if args.output_mode in {"html", "pptx+html"}:
        required.append("v1.html")

    missing = [name for name in required if not (project_dir / name).exists()]
    if missing:
        print("[ERROR] missing outputs:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)

    print("[OK] required outputs exist")


if __name__ == "__main__":
    main()
