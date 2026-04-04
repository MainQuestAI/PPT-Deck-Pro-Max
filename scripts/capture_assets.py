#!/usr/bin/env python3
"""Capture product screenshots from URLs using Playwright.

Requires: pip install playwright && playwright install chromium
Falls back gracefully if Playwright is not installed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"assets": []}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cookies(cookies_path: Path | None) -> list[dict] | None:
    if not cookies_path or not cookies_path.exists():
        return None
    return json.loads(cookies_path.read_text(encoding="utf-8"))


def capture_url(
    url: str,
    output_path: Path,
    viewport: str = "1280x800",
    wait_selector: str | None = None,
    cookies: list[dict] | None = None,
) -> bool:
    if not HAS_PLAYWRIGHT:
        print(f"[SKIP] Playwright not installed, cannot capture: {url}")
        return False

    w, h = (int(x) for x in viewport.split("x"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": w, "height": h})
        if cookies:
            context.add_cookies(cookies)
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        if wait_selector:
            page.wait_for_selector(wait_selector, timeout=15000)
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture product screenshots from URLs for deck assets.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--cookies", help="Path to cookies JSON file for authenticated pages")
    parser.add_argument("--viewport", default="1280x800")
    parser.add_argument("--only-ids", nargs="*", default=[], help="Only capture these asset IDs")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    manifest_path = Path(args.manifest or project_dir / "asset_manifest.json").expanduser().resolve()
    manifest = load_json(manifest_path)
    cookies = load_cookies(Path(args.cookies).expanduser().resolve() if args.cookies else None)
    only_ids = set(args.only_ids) if args.only_ids else None

    captured_count = 0
    for asset in manifest.get("assets", []):
        asset_id = asset.get("id", "")
        if only_ids and asset_id not in only_ids:
            continue
        url = asset.get("url", "").strip()
        if not url:
            continue
        if asset.get("status") in ("captured", "mockup_applied") and not only_ids:
            continue

        viewport = asset.get("viewport", args.viewport)
        wait = asset.get("wait", "")
        output_path = project_dir / "assets" / f"{asset_id}_raw.png"

        print(f"[...] capturing {asset_id}: {url}")
        ok = capture_url(url, output_path, viewport, wait or None, cookies)
        if ok:
            asset["status"] = "captured"
            asset["raw_path"] = str(output_path.relative_to(project_dir))
            captured_count += 1
            print(f"[OK] captured -> {output_path}")
        else:
            asset["status"] = "pending"

    save_json(manifest_path, manifest)
    print(f"[OK] {captured_count} asset(s) captured, manifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
