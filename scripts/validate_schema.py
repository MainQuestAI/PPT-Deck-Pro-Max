#!/usr/bin/env python3
"""Validate JSON files against their schemas.

Uses jsonschema if available; falls back to basic structural checks if not.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from jsonschema import validate, ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SCHEMA_DIR = SKILL_ROOT / "references"

KNOWN_SCHEMAS: dict[str, str] = {
    "slide_state.json": "slide_state.schema.json",
    "layout_manifest.json": "layout_manifest.schema.json",
    "deck_review_findings.json": "review_findings.schema.json",
    "review_rollback_plan.json": "review_rollback_plan.schema.json",
    "commercial_scorecard.json": "commercial_scorecard.schema.json",
    "asset_manifest.json": "asset_manifest.schema.json",
    "style_lock.json": "style_lock.schema.json",
    "image_build_jobs.json": "image_build_jobs.schema.json",
}


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_file(data_path: Path, schema_path: Path) -> list[str]:
    """Validate a JSON file against a schema. Returns list of error messages."""
    errors: list[str] = []
    try:
        data = load_json(data_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"cannot read {data_path}: {exc}"]

    try:
        schema = load_json(schema_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"cannot read schema {schema_path}: {exc}"]

    if not HAS_JSONSCHEMA:
        # Basic structural check: verify required top-level fields
        required = schema.get("required", [])
        if isinstance(data, dict):
            missing = [f for f in required if f not in data]
            if missing:
                errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        errors.append(f"{exc.json_path}: {exc.message}")
    return errors


def validate_project(project_dir: Path, strict: bool = False) -> dict[str, list[str]]:
    """Validate all known JSON files in a project directory."""
    results: dict[str, list[str]] = {}
    for filename, schema_name in KNOWN_SCHEMAS.items():
        data_path = project_dir / filename
        if not data_path.exists():
            if strict:
                results[filename] = [f"file not found: {data_path}"]
            continue
        schema_path = SCHEMA_DIR / schema_name
        if not schema_path.exists():
            results[filename] = [f"schema not found: {schema_path}"]
            continue
        errors = validate_file(data_path, schema_path)
        if errors:
            results[filename] = errors
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate project JSON files against their schemas.")
    parser.add_argument("--project-dir", help="Validate all known JSON files in a project")
    parser.add_argument("--file", help="Validate a single JSON file")
    parser.add_argument("--schema", help="Schema to validate against (required with --file)")
    parser.add_argument("--strict", action="store_true", help="Report missing files as errors")
    args = parser.parse_args()

    if args.file:
        if not args.schema:
            # Try to auto-detect schema
            filename = Path(args.file).name
            schema_name = KNOWN_SCHEMAS.get(filename)
            if not schema_name:
                raise SystemExit(f"[ERROR] cannot auto-detect schema for {filename}. Use --schema.")
            schema_path = SCHEMA_DIR / schema_name
        else:
            schema_path = Path(args.schema).expanduser().resolve()
        errors = validate_file(Path(args.file).expanduser().resolve(), schema_path)
        if errors:
            print(f"[FAIL] {args.file}:")
            for err in errors:
                print(f"  - {err}")
            raise SystemExit(1)
        print(f"[OK] {args.file} is valid")
        return

    if args.project_dir:
        project_dir = Path(args.project_dir).expanduser().resolve()
        results = validate_project(project_dir, args.strict)
        if results:
            for filename, errors in results.items():
                print(f"[FAIL] {filename}:")
                for err in errors:
                    print(f"  - {err}")
            raise SystemExit(1)
        if not HAS_JSONSCHEMA:
            print("[WARN] jsonschema not installed — basic structural checks only")
        print(f"[OK] all JSON files in {project_dir} are valid")
        return

    raise SystemExit("[ERROR] provide --project-dir or --file")


if __name__ == "__main__":
    main()
