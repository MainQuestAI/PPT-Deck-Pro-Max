#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from page_parser import extract_page_slices, page_id_to_number


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_starter(starter_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in starter_dir.iterdir():
        destination = target_dir / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare an HTML assemble package for an approved build batch.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    jobs_payload = load_json(project_dir / "image_build_jobs.json")
    asset_manifest = load_json(project_dir / "asset_manifest.json")
    slide_state = load_json(project_dir / "slide_state.json")
    batch = next((item for item in jobs_payload.get("batches", []) if item.get("batch_id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` not found.")
    batch_status = batch.get("status", "")
    if batch_status not in {"approved", "completed"}:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` is `{batch_status}`. Expected approved/completed before HTML assemble.")

    page_ids = [str(page_id) for page_id in batch.get("page_ids", []) if str(page_id)]
    if not page_ids:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` has no page_ids.")

    clean_slices = extract_page_slices(read_text(project_dir / "deck_clean_pages.md"))
    visual_slices = extract_page_slices(read_text(project_dir / "deck_visual_composition.md"))
    theme_tokens = load_json(project_dir / "deck_theme_tokens.json")
    style_lock = load_json(project_dir / "style_lock.json")
    state_lookup = {page.get("page_id", ""): page for page in slide_state.get("pages", [])}

    approved_assets_by_page: dict[str, list[dict]] = {}
    for asset in asset_manifest.get("assets", []):
        page_id = asset.get("page_id", "")
        if page_id not in page_ids:
            continue
        if asset.get("status") not in {"approved", "embedded", "captured", "provided", "mockup_applied"}:
            continue
        approved_assets_by_page.setdefault(page_id, []).append(
            {
                "asset_id": asset.get("id", ""),
                "final_path": asset.get("final_path", ""),
                "position": asset.get("position", ""),
                "frame": asset.get("frame", ""),
                "desc": asset.get("desc", ""),
            }
        )

    missing_pages = [page_id for page_id in page_ids if not approved_assets_by_page.get(page_id)]
    if missing_pages:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` still has no approved assets for: {', '.join(missing_pages)}")

    output_dir = project_dir / "assemble" / args.batch_id
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else output_dir / "assemble_manifest.json"
    output_md = Path(args.output_md).expanduser().resolve() if args.output_md else output_dir / "assemble_handoff.md"
    starter_dir = Path(__file__).resolve().parent.parent / "assets" / "html_deck_starter"
    working_dir = output_dir / "starter"
    output_html = working_dir / "index.html"
    output_css = working_dir / "styles.css"
    copy_starter(starter_dir, working_dir)

    pages_payload = []
    lines = [
        f"# HTML Assemble Handoff — {args.batch_id}",
        "",
        f"- 批次：`{args.batch_id}`",
        "- 进入条件：本批次已通过人工确认，可进入 HTML 组装。",
        f"- HTML starter：`{starter_dir}`",
        f"- 工作目录：`{working_dir}`",
        f"- 目标 HTML：`{output_html}`",
        "",
        "## 装配规则",
        "",
        "- 只装配当前批次页面，不重写其他批次页面。",
        "- 必须以 `assemble_context.json` 为第一输入，而不是重新扫描整个项目目录。",
        "- 每页先按 visual composition 建主角区，再嵌入 approved assets。",
        "- 输出必须保留 `<section class=\"slide\" data-slide=\"...\">` 结构，便于后续截图和 QA。",
        "",
        "## 页面装配要求",
        "",
    ]

    for page_id in page_ids:
        page_no = page_id_to_number(page_id) or 0
        page_payload = {
            "page_id": page_id,
            "page_no": page_no,
            "role": state_lookup.get(page_id, {}).get("role", ""),
            "clean_page": clean_slices.get(page_no, ""),
            "visual_composition": visual_slices.get(page_no, ""),
            "approved_assets": approved_assets_by_page.get(page_id, []),
        }
        pages_payload.append(page_payload)
        lines.extend(
            [
                f"### `{page_id}`",
                f"- role: `{page_payload['role']}`",
                f"- approved assets: {', '.join(f'`{asset['asset_id']}`' for asset in page_payload['approved_assets'])}",
                "- 先按 visual composition 放置主角，再将 approved assets 嵌入既定位置。",
                "",
            ]
        )

    manifest = {
        "batch_id": args.batch_id,
        "starter_dir": str(starter_dir.resolve()),
        "working_dir": str(working_dir.resolve()),
        "output_html": str(output_html.resolve()),
        "output_css": str(output_css.resolve()),
        "rendered_dir": str((project_dir / "rendered").resolve()),
        "theme_tokens_path": str((project_dir / "deck_theme_tokens.json").resolve()),
        "style_lock_path": str((project_dir / "style_lock.json").resolve()),
        "pages": pages_payload,
        "theme_tokens": theme_tokens,
        "style_lock": style_lock,
    }
    save_json(output_json, manifest)
    assemble_context_path = output_dir / "assemble_context.json"
    save_json(assemble_context_path, manifest)
    lines.extend(
        [
            "## 必看输入",
            "",
            f"- `assemble_context.json`：`{assemble_context_path}`",
            f"- `index.html` starter：`{output_html}`",
            f"- `styles.css` starter：`{output_css}`",
            "",
            "## 完成信号",
            "",
            "- 当前批次页面都已进入 `index.html`，且每页都有 `data-slide`。",
            "- `approved_assets` 已按指定 `position` 嵌入。",
            "- 输出可被 `screenshot_pages.py` 正常截图用于 QA。",
            "",
        ]
    )
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote html assemble manifest: {output_json}")
    print(f"[OK] wrote html assemble context: {assemble_context_path}")
    print(f"[OK] wrote html assemble handoff: {output_md}")


if __name__ == "__main__":
    main()
