#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from page_parser import extract_page_slices, extract_speaker_notes, page_id_to_number


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def select_clean_pages(text: str, page_ids: list[str], allow_full_fallback: bool) -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    if not page_ids:
        return {"full_document": text}, warnings

    slices = extract_page_slices(text)
    selected: dict[str, str] = {}
    missing: list[str] = []
    for page_id in page_ids:
        page_no = page_id_to_number(page_id)
        if page_no is None or page_no not in slices:
            missing.append(page_id)
            continue
        selected[page_id] = slices[page_no]

    if missing:
        warnings.append(f"missing_page_slices: {', '.join(missing)}")
        if allow_full_fallback and not selected:
            warnings.append("fallback_to_full_clean_pages")
            return {"full_document": text}, warnings
    return selected, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a minimal context bundle for deck roles.")
    parser.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    parser.add_argument("--clean-pages")
    parser.add_argument("--visual-composition")
    parser.add_argument("--visual-system")
    parser.add_argument("--component-tokens")
    parser.add_argument("--theme-tokens")
    parser.add_argument("--slide-state")
    parser.add_argument("--page-ids", nargs="*", default=[])
    parser.add_argument("--allow-full-fallback", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    bundle = {"role": args.role, "page_ids": args.page_ids, "inputs": {}, "warnings": []}

    if args.clean_pages:
        clean_pages_text = read(Path(args.clean_pages))
        selected, warnings = select_clean_pages(clean_pages_text, args.page_ids, args.allow_full_fallback)
        bundle["inputs"]["deck_clean_pages"] = selected
        bundle["warnings"].extend(warnings)
        notes = extract_speaker_notes(clean_pages_text)
        if notes:
            page_notes: dict[str, str] = {}
            for page_id in args.page_ids or []:
                page_no = page_id_to_number(page_id)
                if page_no and page_no in notes:
                    page_notes[page_id] = notes[page_no]
            if page_notes:
                bundle["inputs"]["speaker_notes"] = page_notes
    # Visual composition — slice per page for build context
    if args.visual_composition:
        vc_text = read(Path(args.visual_composition))
        if vc_text:
            vc_slices = extract_page_slices(vc_text)
            if args.page_ids:
                selected_vc: dict[str, str] = {}
                for page_id in args.page_ids:
                    page_no = page_id_to_number(page_id)
                    if page_no and page_no in vc_slices:
                        selected_vc[page_id] = vc_slices[page_no]
                if selected_vc:
                    bundle["inputs"]["visual_composition"] = selected_vc
                else:
                    bundle["warnings"].append("missing_visual_composition_slices")
            else:
                bundle["inputs"]["visual_composition"] = {"full_document": vc_text}

    # Expert context — claim-based, keyed by claim_id (not page number)
    expert_context_path = Path(args.clean_pages).parent / "deck_expert_context.md" if args.clean_pages else None
    if expert_context_path and expert_context_path.exists():
        ec_text = read(expert_context_path)
        if ec_text and "（待生成" not in ec_text:
            # For build context, include the full expert context since claims may span pages
            bundle["inputs"]["expert_context"] = ec_text

    if args.visual_system:
        bundle["inputs"]["deck_visual_system"] = read(Path(args.visual_system))
    if args.component_tokens:
        bundle["inputs"]["deck_component_tokens"] = read(Path(args.component_tokens))
    if args.theme_tokens:
        bundle["inputs"]["deck_theme_tokens"] = read(Path(args.theme_tokens))
    style_lock_path = Path(args.clean_pages).parent / "style_lock.json" if args.clean_pages else None
    if style_lock_path and style_lock_path.exists():
        try:
            bundle["inputs"]["style_lock"] = json.loads(style_lock_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            bundle["warnings"].append("invalid_style_lock")
    # Include asset references for build context
    asset_manifest_path = Path(args.clean_pages).parent / "asset_manifest.json" if args.clean_pages else None
    if asset_manifest_path and asset_manifest_path.exists():
        try:
            manifest = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
            page_assets: dict[str, list[dict]] = {}
            asset_runtime: dict[str, list[dict]] = {}
            for asset in manifest.get("assets", []):
                pid = asset.get("page_id", "")
                if not args.page_ids or pid in args.page_ids:
                    asset_runtime.setdefault(pid, []).append({
                        "id": asset.get("id"),
                        "status": asset.get("status", ""),
                        "source_mode": asset.get("source_mode", ""),
                        "batch_id": asset.get("batch_id", ""),
                        "stale": asset.get("stale", False),
                        "final_path": asset.get("final_path", ""),
                        "desc": asset.get("desc", ""),
                    })
                    if asset.get("status") in {"approved", "embedded", "captured", "provided", "mockup_applied"}:
                        page_assets.setdefault(pid, []).append({
                            "id": asset.get("id"),
                            "final_path": asset.get("final_path", ""),
                            "frame": asset.get("frame", ""),
                            "position": asset.get("position", ""),
                            "desc": asset.get("desc", ""),
                        })
            if page_assets:
                bundle["inputs"]["assets"] = page_assets
            if asset_runtime:
                bundle["inputs"]["asset_runtime"] = asset_runtime
        except (json.JSONDecodeError, OSError):
            pass
    image_jobs_path = Path(args.clean_pages).parent / "image_build_jobs.json" if args.clean_pages else None
    if image_jobs_path and image_jobs_path.exists():
        try:
            jobs_payload = json.loads(image_jobs_path.read_text(encoding="utf-8"))
            page_jobs: dict[str, list[dict]] = {}
            for job in jobs_payload.get("jobs", []):
                pid = job.get("page_id", "")
                if not args.page_ids or pid in args.page_ids:
                    page_jobs.setdefault(pid, []).append(job)
            if page_jobs:
                bundle["inputs"]["generation_jobs"] = page_jobs
                bundle["inputs"]["generation_batch_summary"] = {
                    "initial_review_batch": jobs_payload.get("initial_review_batch", "batch_01"),
                    "batches": jobs_payload.get("batches", []),
                }
        except (json.JSONDecodeError, OSError):
            bundle["warnings"].append("invalid_image_build_jobs")

    if args.slide_state:
        slide_state_text = read(Path(args.slide_state))
        try:
            bundle["inputs"]["slide_state"] = json.loads(slide_state_text)
        except json.JSONDecodeError:
            bundle["inputs"]["slide_state"] = slide_state_text

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
