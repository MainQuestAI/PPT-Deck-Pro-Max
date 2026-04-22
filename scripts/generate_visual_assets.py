#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path

from page_parser import extract_page_slices, page_id_to_number


ROLE_PRIORITY = {
    "hero_cover": 0,
    "hero_proof": 1,
    "hero_system": 2,
    "hero_diff": 3,
    "hero_value": 4,
    "hero_problem": 5,
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def page_priority(page: dict) -> tuple[int, int]:
    role = page.get("role", "")
    page_no = page_id_to_number(page.get("page_id", "")) or 999
    return ROLE_PRIORITY.get(role, 20), page_no


def compute_content_hash(asset: dict, page_text: str, visual_text: str, style_lock: dict) -> str:
    raw = json.dumps(
        {
            "asset": {
                "id": asset.get("id"),
                "desc": asset.get("desc"),
                "prompt_intent": asset.get("prompt_intent"),
                "style_group": asset.get("style_group"),
                "position": asset.get("position"),
                "frame": asset.get("frame"),
                "aspect_ratio": asset.get("aspect_ratio"),
            },
            "page_text": page_text,
            "visual_text": visual_text,
            "style_lock": style_lock,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def build_prompt_payload(asset: dict, page: dict, page_text: str, visual_text: str, style_lock: dict) -> dict:
    return {
        "page_id": page.get("page_id", ""),
        "role": page.get("role", ""),
        "asset_id": asset.get("id", ""),
        "brief": asset.get("desc", ""),
        "page_excerpt": page_text,
        "visual_composition": visual_text,
        "style_lock": style_lock,
        "layout_constraints": {
            "position": asset.get("position", "right"),
            "frame": asset.get("frame", "none"),
            "aspect_ratio": asset.get("aspect_ratio", "16:9"),
        },
        "generation_rules": {
            "text_in_image": style_lock.get("visual_rules", {}).get("text_in_image", "avoid"),
            "negative_prompts": style_lock.get("visual_rules", {}).get("negative_prompts", []),
            "variant_count": asset.get("variant_count", 2),
        },
    }


def assign_batches(assets: list[dict], state: dict, batch_size: int) -> OrderedDict[str, list[str]]:
    page_lookup = {page.get("page_id", ""): page for page in state.get("pages", [])}
    candidate_pages = []
    for asset in assets:
        pid = asset.get("page_id", "")
        if pid and pid not in candidate_pages:
            candidate_pages.append(pid)
    candidate_pages.sort(key=lambda pid: page_priority(page_lookup.get(pid, {"page_id": pid})))
    first_batch_pages = candidate_pages[:batch_size]
    remaining = candidate_pages[batch_size:]

    batches: OrderedDict[str, list[str]] = OrderedDict()
    batches["batch_01"] = first_batch_pages
    batch_no = 2
    for idx in range(0, len(remaining), batch_size):
        batches[f"batch_{batch_no:02d}"] = remaining[idx: idx + batch_size]
        batch_no += 1
    return batches


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Codex-facing image build jobs from asset manifest and page context.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--state")
    parser.add_argument("--clean-pages")
    parser.add_argument("--visual-composition")
    parser.add_argument("--style-lock")
    parser.add_argument("--output")
    parser.add_argument("--batch-size", type=int, default=3)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    manifest_path = Path(args.manifest or project_dir / "asset_manifest.json").expanduser().resolve()
    state_path = Path(args.state or project_dir / "slide_state.json").expanduser().resolve()
    clean_pages_path = Path(args.clean_pages or project_dir / "deck_clean_pages.md").expanduser().resolve()
    visual_path = Path(args.visual_composition or project_dir / "deck_visual_composition.md").expanduser().resolve()
    style_lock_path = Path(args.style_lock or project_dir / "style_lock.json").expanduser().resolve()
    output = Path(args.output or project_dir / "image_build_jobs.json").expanduser().resolve()

    manifest = load_json(manifest_path)
    state = load_json(state_path)
    style_lock = load_json(style_lock_path)
    clean_slices = extract_page_slices(read_text(clean_pages_path))
    visual_slices = extract_page_slices(read_text(visual_path))
    page_lookup = {page.get("page_id", ""): page for page in state.get("pages", [])}

    generate_assets = [asset for asset in manifest.get("assets", []) if asset.get("source_mode") == "generate"]
    batches = assign_batches(generate_assets, state, args.batch_size)
    page_to_batch = {
        page_id: batch_id
        for batch_id, page_ids in batches.items()
        for page_id in page_ids
    }

    jobs = []
    for asset in generate_assets:
        page_id = asset.get("page_id", "")
        page_no = page_id_to_number(page_id) or 0
        page = page_lookup.get(page_id, {})
        page_text = clean_slices.get(page_no, "")
        visual_text = visual_slices.get(page_no, "")
        content_hash = compute_content_hash(asset, page_text, visual_text, style_lock)
        if asset.get("content_hash") and asset.get("content_hash") != content_hash:
            asset["stale"] = True
        batch_id = page_to_batch.get(page_id, "batch_01")
        asset["batch_id"] = batch_id
        asset["content_hash"] = content_hash
        asset["prompt_payload"] = build_prompt_payload(asset, page, page_text, visual_text, style_lock)
        if asset.get("status") in {"pending", "missing", "rejected"} or asset.get("stale"):
            asset["status"] = "queued"
        job = {
            "job_id": f"{batch_id}:{asset.get('id', page_id)}",
            "batch_id": batch_id,
            "page_id": page_id,
            "page_no": page_no,
            "role": page.get("role", ""),
            "asset_id": asset.get("id", ""),
            "status": asset.get("status", "queued"),
            "content_hash": content_hash,
            "prompt_intent": asset.get("prompt_intent", ""),
            "prompt_payload": asset.get("prompt_payload", {}),
            "variant_count": asset.get("variant_count", 2),
            "style_group": asset.get("style_group", "deck_primary"),
        }
        jobs.append(job)

    batch_payloads = []
    for batch_id, page_ids in batches.items():
        job_statuses = [job.get("status") for job in jobs if job.get("batch_id") == batch_id]
        status = "completed" if job_statuses and all(s in {"approved", "embedded"} for s in job_statuses) else "queued"
        batch_payloads.append({
            "batch_id": batch_id,
            "page_ids": page_ids,
            "status": status,
        })

    manifest["assets"] = manifest.get("assets", [])
    save_json(manifest_path, manifest)
    payload = {
        "batch_size": args.batch_size,
        "initial_review_batch": "batch_01",
        "batches": batch_payloads,
        "jobs": jobs,
    }
    save_json(output, payload)
    print(f"[OK] wrote image build jobs: {output}")
    print(f"[OK] queued {len(jobs)} generation job(s)")


if __name__ == "__main__":
    main()
