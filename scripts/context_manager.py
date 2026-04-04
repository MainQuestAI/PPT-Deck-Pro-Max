#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from page_parser import extract_page_slices, page_id_to_number


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def select_clean_pages(text: str, page_ids: list[str], allow_full_fallback: bool) -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    if not page_ids:
        return {"full_document": text}, warnings

    slices = extract_page_slices(text)
    selected: dict[str, str] = {}
    missing: list[str] = []
    for page_id in page_ids:
        page_no = page_id_to_number(page_id)
        if page_no is None or page_no not in slices:
            missing.append(page_id)
            continue
        selected[page_id] = slices[page_no]

    if missing:
        warnings.append(f"missing_page_slices: {', '.join(missing)}")
        if allow_full_fallback and not selected:
            warnings.append("fallback_to_full_clean_pages")
            return {"full_document": text}, warnings
    return selected, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a minimal context bundle for deck roles.")
    parser.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    parser.add_argument("--clean-pages")
    parser.add_argument("--visual-system")
    parser.add_argument("--component-tokens")
    parser.add_argument("--theme-tokens")
    parser.add_argument("--slide-state")
    parser.add_argument("--page-ids", nargs="*", default=[])
    parser.add_argument("--allow-full-fallback", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    bundle = {"role": args.role, "page_ids": args.page_ids, "inputs": {}, "warnings": []}

    if args.clean_pages:
        clean_pages_text = read(Path(args.clean_pages))
        selected, warnings = select_clean_pages(clean_pages_text, args.page_ids, args.allow_full_fallback)
        bundle["inputs"]["deck_clean_pages"] = selected
        bundle["warnings"].extend(warnings)
    if args.visual_system:
        bundle["inputs"]["deck_visual_system"] = read(Path(args.visual_system))
    if args.component_tokens:
        bundle["inputs"]["deck_component_tokens"] = read(Path(args.component_tokens))
    if args.theme_tokens:
        bundle["inputs"]["deck_theme_tokens"] = read(Path(args.theme_tokens))
    if args.slide_state:
        slide_state_text = read(Path(args.slide_state))
        try:
            bundle["inputs"]["slide_state"] = json.loads(slide_state_text)
        except json.JSONDecodeError:
            bundle["inputs"]["slide_state"] = slide_state_text

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
