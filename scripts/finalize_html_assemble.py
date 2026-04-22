#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize an HTML assemble batch and mark assets/pages as embedded.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--html-path")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    assemble_manifest_path = project_dir / "assemble" / args.batch_id / "assemble_manifest.json"
    assemble_manifest = load_json(assemble_manifest_path)
    if not assemble_manifest:
        raise SystemExit(f"[ERROR] assemble manifest not found: {assemble_manifest_path}")

    html_path = Path(args.html_path).expanduser().resolve() if args.html_path else Path(assemble_manifest.get("output_html", ""))
    if not html_path or not html_path.exists():
        raise SystemExit(f"[ERROR] html output not found: {html_path}")

    asset_manifest_path = project_dir / "asset_manifest.json"
    jobs_path = project_dir / "image_build_jobs.json"
    slide_state_path = project_dir / "slide_state.json"
    asset_manifest = load_json(asset_manifest_path)
    jobs_payload = load_json(jobs_path)
    slide_state = load_json(slide_state_path)

    page_ids = [page.get("page_id", "") for page in assemble_manifest.get("pages", []) if page.get("page_id")]
    embedded_asset_ids = {
        asset.get("asset_id", "")
        for page in assemble_manifest.get("pages", [])
        for asset in page.get("approved_assets", [])
        if asset.get("asset_id")
    }

    for asset in asset_manifest.get("assets", []):
        if asset.get("id") in embedded_asset_ids:
            asset["status"] = "embedded"

    for job in jobs_payload.get("jobs", []):
        if job.get("asset_id") in embedded_asset_ids:
            job["status"] = "embedded"

    for batch in jobs_payload.get("batches", []):
        if batch.get("batch_id") != args.batch_id:
            continue
        batch["status"] = "completed"

    for page in slide_state.get("pages", []):
        if page.get("page_id") not in page_ids:
            continue
        page["status"] = "awaiting_review"
        page["qa_status"] = "pending"
        page["qa_reason"] = ""

    slide_state["global_status"] = "awaiting_review"

    save_json(asset_manifest_path, asset_manifest)
    save_json(jobs_path, jobs_payload)
    save_json(slide_state_path, slide_state)
    print(f"[OK] finalized HTML assemble for batch: {args.batch_id}")
    print(f"[OK] html output: {html_path}")


if __name__ == "__main__":
    main()
