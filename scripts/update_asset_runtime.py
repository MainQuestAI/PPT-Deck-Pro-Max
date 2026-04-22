#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_ASSET_STATUS = {"pending", "queued", "captured", "provided", "generated", "approved", "rejected", "embedded", "placeholder", "mockup_applied", "missing"}
ALLOWED_JOB_STATUS = {"queued", "generating", "generated", "approved", "rejected", "embedded"}
STATUS_TO_BATCH = {
    "approved": "approved",
    "embedded": "completed",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update asset/job/batch runtime status in one place.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--final-path")
    parser.add_argument("--selected-variant")
    parser.add_argument("--clear-stale", action="store_true")
    args = parser.parse_args()

    if args.status not in ALLOWED_ASSET_STATUS:
        raise SystemExit(f"[ERROR] invalid asset status: {args.status}")

    project_dir = Path(args.project_dir).expanduser().resolve()
    manifest_path = project_dir / "asset_manifest.json"
    jobs_path = project_dir / "image_build_jobs.json"
    manifest = load_json(manifest_path)
    jobs_payload = load_json(jobs_path)

    asset = next((item for item in manifest.get("assets", []) if item.get("id") == args.asset_id), None)
    if not asset:
        raise SystemExit(f"[ERROR] asset not found: {args.asset_id}")

    asset["status"] = args.status
    asset["generated_at"] = datetime.now(timezone.utc).isoformat()
    if args.final_path is not None:
        asset["final_path"] = args.final_path
    if args.selected_variant is not None:
        asset["selected_variant"] = args.selected_variant
    if args.clear_stale:
        asset["stale"] = False

    matched_jobs = [job for job in jobs_payload.get("jobs", []) if job.get("asset_id") == args.asset_id]
    derived_job_status = args.status if args.status in ALLOWED_JOB_STATUS else None
    if derived_job_status:
        for job in matched_jobs:
            job["status"] = derived_job_status

    batch_ids = {job.get("batch_id", "") for job in matched_jobs if job.get("batch_id")}
    for batch in jobs_payload.get("batches", []):
        batch_id = batch.get("batch_id", "")
        if batch_id not in batch_ids:
            continue
        job_statuses = [job.get("status", "") for job in jobs_payload.get("jobs", []) if job.get("batch_id") == batch_id]
        if job_statuses and all(status == "embedded" for status in job_statuses):
            batch["status"] = "completed"
        elif job_statuses and all(status == "approved" for status in job_statuses):
            batch["status"] = "approved"
        elif any(status == "rejected" for status in job_statuses):
            batch["status"] = "rejected"
        elif any(status in {"generated", "generating", "approved", "embedded"} for status in job_statuses):
            batch["status"] = "in_review"
        else:
            batch["status"] = "queued"

    save_json(manifest_path, manifest)
    save_json(jobs_path, jobs_payload)
    print(f"[OK] updated asset runtime: {args.asset_id} -> {args.status}")


if __name__ == "__main__":
    main()
