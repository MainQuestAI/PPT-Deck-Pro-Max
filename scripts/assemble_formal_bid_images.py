#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


DELIVERABLE_STATUSES = {"Go", "replaced"}


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    table_lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("|")]
    idx = 0
    while idx + 1 < len(table_lines):
        header_line = table_lines[idx]
        separator_line = table_lines[idx + 1]
        if not re.fullmatch(r"\|[\s:\-|]+\|", separator_line):
            idx += 1
            continue
        headers = [cell.strip().lower().replace(" ", "_") for cell in header_line.strip("|").split("|")]
        idx += 2
        while idx < len(table_lines):
            line = table_lines[idx]
            if re.fullmatch(r"\|[\s:\-|]+\|", line):
                break
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == len(headers) and any(cells):
                rows.append(dict(zip(headers, cells)))
            idx += 1
    return rows


def is_truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "y", "1", "direct-reference"}


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip())
    return cleaned.strip("_") or "page.png"


def resolve_project_path(project_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_dir / path


def assemble(project_dir: Path, output_dir: Path, manifest_path: Path) -> dict:
    registry_rows = parse_markdown_table(project_dir / "page_registry.md")
    mapping_rows = parse_markdown_table(project_dir / "actual_page_mapping.md")
    registry_by_source = {row.get("source_id", ""): row for row in registry_rows if row.get("source_id")}
    deliverable_source_ids = {
        row.get("source_id", "")
        for row in registry_rows
        if row.get("source_id", "") and row.get("status", "") in DELIVERABLE_STATUSES
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = ""
    if any(output_dir.iterdir()):
        backup = output_dir.parent / f"{output_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(output_dir, backup)
        backup_dir = str(backup)
        shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []
    errors = []
    mapped_source_ids = set()
    seen_actual_pages = set()

    if not mapping_rows:
        errors.append({"source_id": "__mapping__", "error": "actual_page_mapping is empty"})

    for row in mapping_rows:
        source_id = row.get("source_id", "")
        actual_page = row.get("actual_ppt_page", "")
        if is_truthy(row.get("direct_reference", "")):
            skipped.append({"source_id": source_id, "reason": "direct-reference"})
            continue
        if not source_id or not actual_page.isdigit():
            errors.append({"source_id": source_id or "unknown", "error": "invalid mapping row"})
            continue
        if actual_page in seen_actual_pages:
            errors.append({"source_id": source_id, "error": f"duplicate actual page: {actual_page}"})
            continue
        seen_actual_pages.add(actual_page)

        registry = registry_by_source.get(source_id)
        if not registry:
            errors.append({"source_id": source_id, "error": "source_id not found in page_registry"})
            continue
        mapped_source_ids.add(source_id)
        status = registry.get("status", "")
        if status not in DELIVERABLE_STATUSES:
            errors.append({"source_id": source_id, "error": f"status is not deliverable: {status or 'missing'}"})
            continue
        source_value = registry.get("approved_image", "")
        if not source_value:
            errors.append({"source_id": source_id, "error": "approved_image missing"})
            continue
        source_path = resolve_project_path(project_dir, source_value)
        if not source_path.exists():
            errors.append({"source_id": source_id, "error": f"approved_image not found: {source_value}"})
            continue

        final_name = row.get("final_image_filename", "")
        if not final_name:
            title = safe_filename(row.get("page_title", "page"))
            final_name = f"{int(actual_page):03d}_{safe_filename(source_id)}_{title}{source_path.suffix or '.png'}"
        final_name = safe_filename(Path(final_name).name)
        dest_path = output_dir / final_name
        shutil.copy2(source_path, dest_path)
        copied.append({
            "actual_ppt_page": int(actual_page),
            "source_id": source_id,
            "source": str(source_path),
            "dest": str(dest_path),
        })

    for source_id in sorted(deliverable_source_ids - mapped_source_ids):
        errors.append({"source_id": source_id, "error": "deliverable page missing from actual_page_mapping"})

    payload = {
        "project_dir": str(project_dir),
        "output_dir": str(output_dir),
        "backup_dir": backup_dir,
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy Go formal-bid source-id images into actual PPT page order.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--manifest")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else project_dir / "actual_page_images"
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else project_dir / "actual_page_assembly_manifest.json"
    payload = assemble(project_dir, output_dir, manifest_path)
    print(f"[OK] copied {len(payload['copied'])} formal image(s): {output_dir}")
    print(f"[OK] wrote assembly manifest: {manifest_path}")
    if payload["backup_dir"]:
        print(f"[OK] backed up existing output: {payload['backup_dir']}")
    if payload["errors"]:
        print("[ERROR] formal image assembly has unresolved item(s):")
        for item in payload["errors"]:
            print(f"  - {item['source_id']}: {item['error']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
