#!/usr/bin/env python3
"""Take screenshots of HTML deck pages using Playwright for visual QA.

Requires: pip install playwright && playwright install chromium
Falls back gracefully if Playwright is not installed.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


def find_html_deck(project_dir: Path) -> Path | None:
    candidates = [project_dir]
    for child in sorted(project_dir.iterdir()):
        if child.is_dir() and (child.name.startswith("build_") or child.name.startswith("dist")):
            candidates.append(child)
    for base in candidates:
        for pattern in ("index.html", "deck*.html", "*.html"):
            for match in sorted(base.glob(pattern)):
                if match.is_file() and not match.name.startswith("."):
                    return match
    return None


def screenshot_html_pages(
    html_path: Path,
    output_dir: Path,
    viewport: str = "1280x720",
) -> list[Path]:
    if not HAS_PLAYWRIGHT:
        print("[SKIP] Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return []

    w, h = (int(x) for x in viewport.split("x"))
    output_dir.mkdir(parents=True, exist_ok=True)
    file_url = f"file://{html_path.resolve()}"
    outputs: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(file_url, wait_until="networkidle", timeout=30000)

        # Try to detect sections (slides)
        sections = page.query_selector_all("section, .slide, [data-slide]")
        if sections:
            for idx, section in enumerate(sections, start=1):
                section.scroll_into_view_if_needed()
                page.wait_for_timeout(200)
                out = output_dir / f"slide_{idx:02d}.png"
                section.screenshot(path=str(out))
                outputs.append(out)
                print(f"[OK] screenshot -> {out}")
        else:
            # Single page fallback
            out = output_dir / "slide_01.png"
            page.screenshot(path=str(out), full_page=True)
            outputs.append(out)
            print(f"[OK] full page screenshot -> {out}")

        browser.close()
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Take screenshots of HTML deck pages for visual QA.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--html-path", help="Path to the HTML deck file (auto-detected if omitted)")
    parser.add_argument("--output-dir", help="Directory for screenshot PNGs (default: project_dir)")
    parser.add_argument("--viewport", default="1280x720")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    html_path = Path(args.html_path).expanduser().resolve() if args.html_path else find_html_deck(project_dir)
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else project_dir

    if not html_path or not html_path.exists():
        print("[SKIP] No HTML deck found. Build the deck first or provide --html-path.")
        return

    outputs = screenshot_html_pages(html_path, output_dir, args.viewport)
    print(f"[OK] {len(outputs)} page screenshot(s) generated")


if __name__ == "__main__":
    main()
