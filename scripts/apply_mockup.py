#!/usr/bin/env python3
"""Apply device mockup frames to raw screenshots.

Renders device shells (MacBook, browser, iPhone, etc.) using pure Pillow
drawing — no external image assets required. This ensures the skill is
fully self-contained and open-source distributable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SPEC_PATH = SKILL_ROOT / "assets" / "mockup_frames" / "mockup_spec.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rounded_rect(draw: ImageDraw.ImageDraw, bbox: tuple, radius: int, fill: str, outline: str | None = None) -> None:
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline)


def add_shadow(img: Image.Image, offset: int = 12, blur: int = 30) -> Image.Image:
    shadow = Image.new("RGBA", (img.width + blur * 2, img.height + blur * 2), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 60))
    shadow.paste(shadow_layer, (blur + offset, blur + offset))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    shadow.paste(img, (blur, blur), img if img.mode == "RGBA" else None)
    return shadow


def render_macbook(screenshot: Image.Image, spec: dict) -> Image.Image:
    cw, ch = spec["canvas"]
    vw, vh = spec["viewport"]
    vx, vy = spec["viewport_offset"]
    bw = spec["bezel_width"]
    cr = spec["corner_radius"]
    base_h = spec["base_height"]

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Screen bezel
    rounded_rect(draw, [vx - bw, vy - bw, vx + vw + bw, vy + vh + bw], cr + bw, spec["bezel_color"])
    # Screen area (white bg)
    rounded_rect(draw, [vx, vy, vx + vw, vy + vh], cr, "#ffffff")
    # Paste screenshot
    resized = screenshot.resize((vw, vh), Image.LANCZOS)
    canvas.paste(resized, (vx, vy))
    # Base
    base_top = vy + vh + bw
    draw.polygon([
        (vx - bw - 40, base_top + base_h),
        (vx - bw + 10, base_top),
        (vx + vw + bw - 10, base_top),
        (vx + vw + bw + 40, base_top + base_h),
    ], fill="#2a2a2a")

    return add_shadow(canvas, spec.get("shadow_offset", 12), spec.get("shadow_blur", 30))


def render_browser(screenshot: Image.Image, spec: dict) -> Image.Image:
    cw, ch = spec["canvas"]
    vw, vh = spec["viewport"]
    vx, vy = spec["viewport_offset"]
    cr = spec["corner_radius"]
    th = spec["toolbar_height"]
    tc = spec["toolbar_color"]

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Window frame
    rounded_rect(draw, [vx - 12, vy - th - 12, vx + vw + 12, vy + vh + 12], cr, "#1e1e1e")
    # Toolbar
    draw.rectangle([vx - 8, vy - th - 8, vx + vw + 8, vy - 4], fill=tc)
    # Traffic light dots
    for i, color in enumerate(spec.get("dot_colors", [])):
        draw.ellipse([vx + 8 + i * 20, vy - th + 4, vx + 20 + i * 20, vy - th + 16], fill=color)
    # Viewport
    draw.rectangle([vx, vy, vx + vw, vy + vh], fill="#ffffff")
    resized = screenshot.resize((vw, vh), Image.LANCZOS)
    canvas.paste(resized, (vx, vy))

    return add_shadow(canvas, spec.get("shadow_offset", 8), spec.get("shadow_blur", 24))


def render_iphone(screenshot: Image.Image, spec: dict) -> Image.Image:
    cw, ch = spec["canvas"]
    vw, vh = spec["viewport"]
    vx, vy = spec["viewport_offset"]
    cr = spec["corner_radius"]
    bw = spec["bezel_width"]

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    rounded_rect(draw, [vx - bw, vy - bw, vx + vw + bw, vy + vh + bw], cr, spec["bezel_color"])
    rounded_rect(draw, [vx, vy, vx + vw, vy + vh], cr - bw, "#ffffff")
    resized = screenshot.resize((vw, vh), Image.LANCZOS)
    canvas.paste(resized, (vx, vy))

    # Notch
    nw = spec.get("notch_width", 120)
    nh = spec.get("notch_height", 28)
    nx = vx + (vw - nw) // 2
    rounded_rect(draw, [nx, vy - bw, nx + nw, vy - bw + nh], 12, spec["bezel_color"])

    return add_shadow(canvas, spec.get("shadow_offset", 8), spec.get("shadow_blur", 20))


def render_generic(screenshot: Image.Image, spec: dict) -> Image.Image:
    """Fallback for tablet and terminal — simple bezel + viewport."""
    cw, ch = spec["canvas"]
    vw, vh = spec["viewport"]
    vx, vy = spec["viewport_offset"]
    cr = spec["corner_radius"]

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    bezel_color = spec.get("bezel_color", spec.get("toolbar_color", "#1e1e1e"))
    rounded_rect(draw, [vx - 14, vy - 14, vx + vw + 14, vy + vh + 14], cr, bezel_color)

    th = spec.get("toolbar_height", 0)
    if th:
        draw.rectangle([vx, vy, vx + vw, vy + th], fill=spec.get("toolbar_color", "#2d2d2d"))
        title = spec.get("title", "")
        if title:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
            except Exception:
                font = ImageFont.load_default()
            draw.text((vx + 12, vy + 8), title, fill="#999999", font=font)

    draw.rectangle([vx, vy + th, vx + vw, vy + vh], fill="#ffffff")
    resized = screenshot.resize((vw, vh - th), Image.LANCZOS)
    canvas.paste(resized, (vx, vy + th))

    return add_shadow(canvas, spec.get("shadow_offset", 8), spec.get("shadow_blur", 20))


RENDERERS = {
    "macbook": render_macbook,
    "browser": render_browser,
    "iphone": render_iphone,
    "tablet": render_generic,
    "terminal": render_generic,
}


def apply_mockup(screenshot_path: Path, frame: str, output_path: Path, specs: dict) -> bool:
    if not HAS_PILLOW:
        print(f"[SKIP] Pillow not installed, cannot apply mockup: {screenshot_path}")
        return False
    if frame == "none" or frame not in specs:
        # No mockup needed, just copy
        output_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot = Image.open(screenshot_path).convert("RGB")
        screenshot.save(output_path)
        return True

    spec = specs[frame]
    renderer = RENDERERS.get(frame, render_generic)
    screenshot = Image.open(screenshot_path).convert("RGB")
    result = renderer(screenshot, spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply device mockup frames to raw screenshots.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--input", help="Single screenshot to process")
    parser.add_argument("--frame", default="macbook", choices=list(RENDERERS.keys()) + ["none"])
    parser.add_argument("--output", help="Output path for single screenshot mode")
    parser.add_argument("--spec", help="Path to mockup_spec.json")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    spec_path = Path(args.spec).expanduser().resolve() if args.spec else SPEC_PATH
    specs = load_json(spec_path)

    if args.input:
        # Single file mode
        input_path = Path(args.input).expanduser().resolve()
        output_path = Path(args.output).expanduser().resolve() if args.output else input_path.with_stem(input_path.stem + "_mockup")
        ok = apply_mockup(input_path, args.frame, output_path, specs)
        if ok:
            print(f"[OK] mockup -> {output_path}")
        return

    # Batch mode: process all captured/provided assets in manifest
    manifest_path = Path(args.manifest or project_dir / "asset_manifest.json").expanduser().resolve()
    manifest = load_json(manifest_path)

    count = 0
    for asset in manifest.get("assets", []):
        status = asset.get("status", "")
        if status not in ("captured", "provided"):
            continue
        raw = asset.get("raw_path", "")
        if not raw:
            # For provided assets, raw_path might be empty; use final_path
            raw = asset.get("final_path", "")
        if not raw:
            continue
        raw_path = project_dir / raw
        if not raw_path.exists():
            continue

        frame = asset.get("frame", "macbook")
        asset_id = asset.get("id", "unknown")
        output_path = project_dir / "assets" / f"{asset_id}.png"

        ok = apply_mockup(raw_path, frame, output_path, specs)
        if ok:
            asset["status"] = "mockup_applied"
            asset["final_path"] = str(output_path.relative_to(project_dir))
            count += 1
            print(f"[OK] mockup {frame} -> {output_path}")

    save_json(manifest_path, manifest)
    print(f"[OK] {count} mockup(s) applied")


if __name__ == "__main__":
    main()
