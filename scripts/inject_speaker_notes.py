#!/usr/bin/env python3
"""Inject speaker notes from deck_clean_pages.md into existing PPTX files.

Also outputs speaker_notes.json for HTML deck integration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from page_parser import extract_speaker_notes

try:
    from pptx import Presentation

    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False


def inject_into_pptx(pptx_path: Path, notes: dict[int, str], output_path: Path | None = None) -> int:
    if not HAS_PPTX:
        print("[SKIP] python-pptx not installed, cannot inject speaker notes.")
        return 0

    prs = Presentation(str(pptx_path))
    injected = 0
    for idx, slide in enumerate(prs.slides, start=1):
        if idx not in notes:
            continue
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes[idx]
        injected += 1

    target = output_path or pptx_path
    prs.save(str(target))
    return injected


def write_notes_json(notes: dict[int, str], output_path: Path) -> None:
    payload = {f"slide_{k:02d}": v for k, v in sorted(notes.items())}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject speaker notes into PPTX and export speaker_notes.json.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--clean-pages")
    parser.add_argument("--pptx-path", help="PPTX file to inject notes into")
    parser.add_argument("--pptx-output", help="Output PPTX path (default: overwrite input)")
    parser.add_argument("--json-output", help="Output speaker_notes.json path")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    clean_pages = Path(args.clean_pages or project_dir / "deck_clean_pages.md").expanduser().resolve()

    if not clean_pages.exists():
        raise SystemExit(f"[ERROR] clean pages not found: {clean_pages}")

    notes = extract_speaker_notes(clean_pages.read_text(encoding="utf-8"))
    if not notes:
        print("[OK] no speaker notes found in clean pages")
        return

    # Export JSON (always)
    json_output = Path(args.json_output or project_dir / "speaker_notes.json").expanduser().resolve()
    write_notes_json(notes, json_output)
    print(f"[OK] wrote {json_output} ({len(notes)} note(s))")

    # Inject into PPTX (if available)
    if args.pptx_path:
        pptx_path = Path(args.pptx_path).expanduser().resolve()
        pptx_output = Path(args.pptx_output).expanduser().resolve() if args.pptx_output else None
        injected = inject_into_pptx(pptx_path, notes, pptx_output)
        print(f"[OK] injected {injected} note(s) into {pptx_output or pptx_path}")


if __name__ == "__main__":
    main()
