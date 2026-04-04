#!/usr/bin/env python3
"""Generate branded placeholder images for missing assets.

Uses Pillow to draw rectangles with the theme accent color and asset description text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_placeholder(
    output_path: Path,
    desc: str,
    width: int = 1280,
    height: int = 800,
    bg_color: str = "#0a3553",
    accent_color: str = "#4da3ff",
    text_color: str = "#b9c2cf",
) -> bool:
    if not HAS_PILLOW:
        print(f"[SKIP] Pillow not installed, cannot generate placeholder: {output_path}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Border
    border_width = 3
    draw.rectangle(
        [border_width, border_width, width - border_width - 1, height - border_width - 1],
        outline=accent_color,
        width=border_width,
    )

    # Label
    label = "SCREENSHOT PLACEHOLDER"
    try:
        font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_desc = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except Exception:
        font_label = ImageFont.load_default()
        font_desc = font_label

    bbox = draw.textbbox((0, 0), label, font=font_label)
    lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - lw) / 2, height / 2 - lh - 16), label, fill=accent_color, font=font_label)

    # Description
    desc_display = desc[:80] + "..." if len(desc) > 80 else desc
    bbox = draw.textbbox((0, 0), desc_display, font=font_desc)
    dw = bbox[2] - bbox[0]
    draw.text(((width - dw) / 2, height / 2 + 8), desc_display, fill=text_color, font=font_desc)

    img.save(output_path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate branded placeholder images for missing deck assets.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--theme-tokens")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=800)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    manifest_path = Path(args.manifest or project_dir / "asset_manifest.json").expanduser().resolve()
    manifest = load_json(manifest_path)

    theme = load_json(Path(args.theme_tokens).expanduser().resolve()) if args.theme_tokens else {}
    colors = theme.get("colors", {})
    bg = colors.get("background", "#0a3553")
    accent = colors.get("accent", "#4da3ff")
    text_secondary = colors.get("text_secondary", "#b9c2cf")

    count = 0
    for asset in manifest.get("assets", []):
        if asset.get("status") not in ("pending", "missing"):
            continue
        asset_id = asset.get("id", "unknown")
        desc = asset.get("desc", asset_id)
        output_path = project_dir / "assets" / f"{asset_id}_placeholder.png"

        ok = generate_placeholder(output_path, desc, args.width, args.height, bg, accent, text_secondary)
        if ok:
            asset["status"] = "placeholder"
            asset["final_path"] = str(output_path.relative_to(project_dir))
            count += 1
            print(f"[OK] placeholder -> {output_path}")

    save_json(manifest_path, manifest)
    print(f"[OK] {count} placeholder(s) generated")


if __name__ == "__main__":
    main()
