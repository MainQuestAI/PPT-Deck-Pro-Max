#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context_manager import read as read_text, select_clean_pages
from generate_role_prompt import build_build_prompt
from page_parser import extract_page_slices, extract_speaker_notes, page_id_to_number


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_page_context(
    project_dir: Path,
    page_id: str,
    output: Path,
) -> dict:
    clean_pages = project_dir / "deck_clean_pages.md"
    vc = project_dir / "deck_visual_composition.md"
    visual_system = project_dir / "deck_visual_system.md"
    component_tokens = project_dir / "deck_component_tokens.md"
    theme_tokens = project_dir / "deck_theme_tokens.json"
    slide_state = project_dir / "slide_state.json"

    bundle = {"role": "build", "page_ids": [page_id], "inputs": {}, "warnings": []}
    clean_pages_text = read_text(clean_pages)
    selected, warnings = select_clean_pages(clean_pages_text, [page_id], False)
    bundle["inputs"]["deck_clean_pages"] = selected
    bundle["warnings"].extend(warnings)
    notes = extract_speaker_notes(clean_pages_text)
    page_no = page_id_to_number(page_id)
    if page_no and page_no in notes:
        bundle["inputs"]["speaker_notes"] = {page_id: notes[page_no]}

    vc_text = read_text(vc)
    vc_slices = extract_page_slices(vc_text)
    if page_no and page_no in vc_slices:
        bundle["inputs"]["visual_composition"] = {page_id: vc_slices[page_no]}

    expert_context = project_dir / "deck_expert_context.md"
    if expert_context.exists():
        ec_text = read_text(expert_context)
        if ec_text and "（待生成" not in ec_text:
            bundle["inputs"]["expert_context"] = ec_text

    bundle["inputs"]["deck_visual_system"] = read_text(visual_system)
    bundle["inputs"]["deck_component_tokens"] = read_text(component_tokens)
    bundle["inputs"]["deck_theme_tokens"] = read_text(theme_tokens)

    style_lock = project_dir / "style_lock.json"
    if style_lock.exists():
        bundle["inputs"]["style_lock"] = load_json(style_lock)

    asset_manifest = load_json(project_dir / "asset_manifest.json")
    page_assets = []
    asset_runtime = []
    for asset in asset_manifest.get("assets", []):
        if asset.get("page_id") != page_id:
            continue
        asset_runtime.append({
            "id": asset.get("id"),
            "status": asset.get("status", ""),
            "source_mode": asset.get("source_mode", ""),
            "batch_id": asset.get("batch_id", ""),
            "stale": asset.get("stale", False),
            "final_path": asset.get("final_path", ""),
            "desc": asset.get("desc", ""),
        })
        if asset.get("status") in {"approved", "embedded", "captured", "provided", "mockup_applied"}:
            page_assets.append({
                "id": asset.get("id"),
                "final_path": asset.get("final_path", ""),
                "frame": asset.get("frame", ""),
                "position": asset.get("position", ""),
                "desc": asset.get("desc", ""),
            })
    if page_assets:
        bundle["inputs"]["assets"] = {page_id: page_assets}
    if asset_runtime:
        bundle["inputs"]["asset_runtime"] = {page_id: asset_runtime}

    image_jobs = load_json(project_dir / "image_build_jobs.json")
    page_jobs = [job for job in image_jobs.get("jobs", []) if job.get("page_id") == page_id]
    if page_jobs:
        bundle["inputs"]["generation_jobs"] = {page_id: page_jobs}
    bundle["inputs"]["generation_batch_summary"] = {
        "initial_review_batch": image_jobs.get("initial_review_batch", "batch_01"),
        "batches": image_jobs.get("batches", []),
    }

    slide_state_payload = load_json(slide_state)
    bundle["inputs"]["slide_state"] = slide_state_payload

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate per-page subagent dispatch package for a build batch.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    jobs_payload = load_json(project_dir / "image_build_jobs.json")
    batch = next((item for item in jobs_payload.get("batches", []) if item.get("batch_id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` not found.")
    page_ids = [str(page_id) for page_id in batch.get("page_ids", []) if str(page_id)]
    if not page_ids:
        raise SystemExit(f"[ERROR] batch `{args.batch_id}` has no page_ids.")

    dispatch_dir = project_dir / "dispatch" / args.batch_id
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else dispatch_dir / "dispatch.json"
    output_md = Path(args.output_md).expanduser().resolve() if args.output_md else dispatch_dir / "dispatch.md"

    tasks = []
    lines = [
        f"# Build Dispatch — {args.batch_id}",
        "",
        f"- 批次：`{args.batch_id}`",
        f"- 页面：{', '.join(f'`{page_id}`' for page_id in page_ids)}",
        "- 调度规则：一页一个 subagent，不允许跨页写入。",
        "- 批次内页面可以并行生图，但必须在主线程统一做挑选/批准后再继续下一批。",
        "",
        "## Subagent Tasks",
        "",
    ]

    for page_id in page_ids:
        context_path = dispatch_dir / "contexts" / f"{page_id}.json"
        bundle = build_page_context(project_dir, page_id, context_path)
        handoff_path = dispatch_dir / f"{page_id}_handoff.md"
        prompt = build_build_prompt(project_dir, [page_id], context_path, args.batch_id)
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(prompt + "\n", encoding="utf-8")

        page_jobs = bundle.get("inputs", {}).get("generation_jobs", {}).get(page_id, [])
        task = {
            "task_id": f"{args.batch_id}:{page_id}",
            "page_id": page_id,
            "ownership": {
                "writes": [
                    str(context_path.resolve()),
                ],
                "asset_ids": [job.get("asset_id", "") for job in page_jobs],
            },
            "context_path": str(context_path.resolve()),
            "handoff_path": str(handoff_path.resolve()),
            "job_count": len(page_jobs),
        }
        tasks.append(task)
        lines.extend(
            [
                f"### `{page_id}`",
                f"- handoff: `{handoff_path}`",
                f"- context: `{context_path}`",
                f"- assets: {', '.join(f'`{asset}`' for asset in task['ownership']['asset_ids'] if asset) or '无'}",
                f"- 任务数: `{len(page_jobs)}`",
                "",
            ]
        )

    payload = {
        "batch_id": args.batch_id,
        "page_ids": page_ids,
        "tasks": tasks,
    }
    save_json(output_json, payload)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote build dispatch json: {output_json}")
    print(f"[OK] wrote build dispatch md: {output_md}")


if __name__ == "__main__":
    main()
