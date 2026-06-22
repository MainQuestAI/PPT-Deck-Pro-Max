#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from init_deck_project import init_project

DISPATCH_SCHEMA_VERSION = "deck_generation_dispatch_package.v1"
BRIDGE_SCHEMA_VERSION = "ppt_deck_pro_max_deck_master_bridge.v1"
GENERATION_RESULT_SCHEMA_VERSION = "deck_generation_result.v2"


class BridgeError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeError(f"JSON file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BridgeError(f"Invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise BridgeError(f"JSON file must contain an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version() -> str:
    version_path = Path(__file__).resolve().parents[1] / "VERSION"
    if version_path.exists():
        return version_path.read_text(encoding="utf-8").strip() or "unknown"
    return "unknown"


def _run_relative(run_dir: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(run_dir.resolve()))
    except ValueError as exc:
        raise BridgeError(f"Output path escapes Deck Master run directory: {path}") from exc


def _deck_master_run_dir(dispatch_path: Path) -> Path:
    if dispatch_path.name == "dispatch_package.json" and dispatch_path.parent.name == "generation_dispatch":
        return dispatch_path.parent.parent.resolve()
    raise BridgeError("Dispatch package must be <run_dir>/generation_dispatch/dispatch_package.json")


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BridgeError(f"Dispatch package field `{field}` must be a non-empty string.")
    return value


def _required_sha256(payload: dict[str, Any], field: str) -> str:
    value = _required_string(payload, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise BridgeError(f"Dispatch package field `{field}` must be a lowercase sha256 hex string.")
    return value


def _safe_identifier(value: str, field: str) -> str:
    if value in {"", ".", ".."} or "/" in value or "\\" in value:
        raise BridgeError(f"Dispatch task field `{field}` cannot contain path separators.")
    return value


def _normalize_task(task: dict[str, Any], index: int) -> dict[str, Any]:
    task_id = _safe_identifier(str(task.get("task_id") or task.get("id") or f"task_{index:03d}"), "task_id")
    page_id = _safe_identifier(str(task.get("page_id") or task.get("beat_id") or f"page_{index:03d}"), "page_id")
    beat_id = _safe_identifier(str(task.get("beat_id") or page_id), "beat_id")
    return {
        "task_id": task_id,
        "page_id": page_id,
        "beat_id": beat_id,
        "order": index,
        "title": str(task.get("page_title") or task.get("title") or page_id),
        "source_decision": str(task.get("source_decision") or "generate"),
        "expected_outputs": task.get("expected_outputs") if isinstance(task.get("expected_outputs"), list) else [],
        "quality_requirements": task.get("quality_requirements") if isinstance(task.get("quality_requirements"), list) else [],
        "workspace_refs": task.get("workspace_refs") if isinstance(task.get("workspace_refs"), list) else [],
    }


def _load_bridge(project_dir: Path) -> dict[str, Any]:
    return _read_json(project_dir / "deck_master_bridge.json")


def import_deck_master_dispatch(input_path: str | Path, project_dir: str | Path) -> dict[str, Any]:
    dispatch_path = Path(input_path).expanduser().resolve()
    project = Path(project_dir).expanduser().resolve()
    package = _read_json(dispatch_path)
    if package.get("schema_version") != DISPATCH_SCHEMA_VERSION:
        raise BridgeError(f"Unsupported dispatch schema: {package.get('schema_version')}")
    tasks = package.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise BridgeError("Dispatch package must contain tasks[].")
    run_dir = _deck_master_run_dir(dispatch_path)
    normalized = [_normalize_task(task, index) for index, task in enumerate(tasks, start=1) if isinstance(task, dict)]
    if len(normalized) != len(tasks):
        raise BridgeError("Every dispatch task must be an object.")

    run_id = _required_string(package, "run_id")
    session_id = _required_string(package, "session_id")
    source_fingerprint = _required_sha256(package, "source_fingerprint")
    init_project(project, with_example=False, production_sub_mode="standard_deck")
    bridge = {
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "run_id": run_id,
        "session_id": session_id,
        "source_fingerprint": source_fingerprint,
        "dispatch_package": str(dispatch_path),
        "deck_master_run_dir": str(run_dir),
        "task_count": len(normalized),
        "tasks": normalized,
        "created_at": _utc_now(),
    }
    _write_json(project / "deck_master_bridge.json", bridge)
    _write_json(
        project / "slide_state.json",
        {
            "project_id": bridge["run_id"],
            "global_status": "deck_master_imported",
            "output_mode": "html",
            "production_sub_mode": "standard_deck",
            "pages": [
                {
                    "page_id": task["page_id"],
                    "role": task["title"],
                    "status": "deck_master_imported",
                    "qa_status": "pending",
                    "source_task_id": task["task_id"],
                }
                for task in normalized
            ],
        },
    )
    clean_pages = ["# Clean Pages", ""]
    visual = ["# Visual Composition", ""]
    for task in normalized:
        clean_pages.extend([f"## {task['page_id']}", "", task["title"], ""])
        visual.extend([f"## {task['page_id']}", "", f"- source_decision: {task['source_decision']}", ""])
    (project / "deck_clean_pages.md").write_text("\n".join(clean_pages), encoding="utf-8")
    (project / "deck_visual_composition.md").write_text("\n".join(visual), encoding="utf-8")
    _write_json(
        project / "layout_manifest.json",
        {
            "pages": [
                {
                    "page_id": task["page_id"],
                    "order": task["order"],
                    "title": task["title"],
                    "source": {"type": "deck_master_task", "task_id": task["task_id"]},
                }
                for task in normalized
            ]
        },
    )
    return {
        "schema_version": "ppt_deck_pro_max_deck_master_import_result.v1",
        "status": "imported",
        "project_dir": str(project),
        "run_id": bridge["run_id"],
        "session_id": bridge["session_id"],
        "task_count": len(normalized),
        "bridge_manifest": str(project / "deck_master_bridge.json"),
    }


def _artifact(
    run_dir: Path,
    *,
    artifact_id: str,
    kind: str,
    path: Path,
    media_type: str,
    page_id: str,
    editability: str,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "path": _run_relative(run_dir, path),
        "media_type": media_type,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "validation_status": "validated",
        "editability": editability,
        "page_id": page_id,
        "created_at": _utc_now(),
    }


def _project_path(project: Path, value: str | Path, *, field_name: str, must_exist: bool = True) -> Path:
    if not value:
        raise BridgeError(f"{field_name} is required.")
    raw = Path(value)
    resolved = raw.expanduser().resolve() if raw.is_absolute() else (project / raw).resolve()
    root = str(project.resolve())
    if str(resolved) != root and not str(resolved).startswith(root + "/"):
        raise BridgeError(f"{field_name} must stay inside project directory: {value}")
    if must_exist and not resolved.exists():
        raise BridgeError(f"{field_name} not found: {value}")
    return resolved


def _copy_into_run(run_dir: Path, source: Path, destination: Path) -> Path:
    _run_relative(run_dir, destination)
    if not source.is_file():
        raise BridgeError(f"Source artifact missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def _load_assembled_pages(project: Path) -> dict[str, dict[str, Any]]:
    assembled: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted((project / "assemble").glob("*/assemble_manifest.json")):
        manifest = _read_json(manifest_path)
        output_html = _project_path(project, str(manifest.get("output_html") or ""), field_name="assemble.output_html")
        rendered_dir_value = str(manifest.get("rendered_dir") or "rendered")
        rendered_dir = _project_path(project, rendered_dir_value, field_name="assemble.rendered_dir", must_exist=False)
        pages = manifest.get("pages")
        if not isinstance(pages, list):
            continue
        for index, page in enumerate(pages, start=1):
            if not isinstance(page, dict):
                continue
            page_id = str(page.get("page_id") or "")
            if not page_id:
                continue
            assembled[page_id] = {
                "assemble_manifest": manifest_path,
                "batch_id": str(manifest.get("batch_id") or manifest_path.parent.name),
                "html_path": output_html,
                "rendered_dir": rendered_dir,
                "order": index,
            }
    return assembled


def _preview_path_for_task(project: Path, assembled_page: dict[str, Any], task: dict[str, Any]) -> Path:
    rendered_dir = Path(assembled_page["rendered_dir"])
    page_id = task["page_id"]
    normalized = page_id.strip().lower().replace("-", "_")
    order = int(assembled_page.get("order") or task["order"])
    candidates = [
        rendered_dir / f"{page_id}.png",
        rendered_dir / f"{normalized}.png",
    ]
    if normalized.startswith("slide_"):
        candidates.append(rendered_dir / f"{normalized}.png")
    candidates.extend(
        [
            rendered_dir / f"slide_{order:02d}.png",
            project / "rendered" / f"{page_id}.png",
            project / "rendered" / f"{normalized}.png",
            project / "rendered" / f"slide_{order:02d}.png",
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = _project_path(project, candidate, field_name="preview", must_exist=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise BridgeError(f"Preview screenshot missing for page `{page_id}`. Run screenshot-pages before deck-master-export.")


def export_deck_master_results(project_dir: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    project = Path(project_dir).expanduser().resolve()
    bridge = _load_bridge(project)
    run_dir = Path(str(bridge.get("deck_master_run_dir") or "")).expanduser().resolve()
    if not run_dir.exists():
        raise BridgeError(f"Deck Master run directory missing: {run_dir}")
    output = Path(output_dir).expanduser().resolve() if output_dir else run_dir / "generation_results"
    _run_relative(run_dir, output)
    output.mkdir(parents=True, exist_ok=True)
    assembled_pages = _load_assembled_pages(project)

    written: list[str] = []
    for task in bridge.get("tasks", []):
        if not isinstance(task, dict):
            continue
        assembled_page = assembled_pages.get(task["page_id"])
        if not assembled_page:
            raise BridgeError(f"Assembled HTML missing for page `{task['page_id']}`. Run prepare-assemble and assemble-html first.")
        source_html = Path(assembled_page["html_path"])
        source_preview = _preview_path_for_task(project, assembled_page, task)
        artifact_dir = output / "artifacts" / task["page_id"]
        html_path = _copy_into_run(run_dir, source_html, artifact_dir / "index.html")
        png_path = _copy_into_run(run_dir, source_preview, artifact_dir / "preview.png")
        html_artifact = _artifact(
            run_dir,
            artifact_id=f"{task['page_id']}_html",
            kind="deck_html",
            path=html_path,
            media_type="text/html",
            page_id=task["page_id"],
            editability="native",
        )
        preview_artifact = _artifact(
            run_dir,
            artifact_id=f"{task['page_id']}_preview",
            kind="page_png",
            path=png_path,
            media_type="image/png",
            page_id=task["page_id"],
            editability="not_applicable",
        )
        result = {
            "schema_version": GENERATION_RESULT_SCHEMA_VERSION,
            "run_id": bridge["run_id"],
            "session_id": bridge["session_id"],
            "task_id": task["task_id"],
            "page_id": task["page_id"],
            "beat_id": task["beat_id"],
            "producer": {
                "capability": "ppt-deck-pro-max",
                "version": _version(),
                "source_ref": "scripts/deck_master_bridge.py",
            },
            "tool": "ppt-deck-pro-max",
            "status": "completed",
            "source_fingerprint": bridge["source_fingerprint"],
            "artifacts": [html_artifact, preview_artifact],
            "preview": preview_artifact,
            "artifact_type": "deck_html",
            "artifact_path": html_artifact["path"],
            "preview_path": preview_artifact["path"],
            "provenance": {
                "bridge_manifest": str((project / "deck_master_bridge.json").resolve()),
                "dispatch_package": bridge.get("dispatch_package", ""),
                "assemble_manifest": str(Path(assembled_page["assemble_manifest"]).resolve()),
                "source_html": str(source_html.resolve()),
                "source_preview": str(source_preview.resolve()),
                "batch_id": assembled_page.get("batch_id", ""),
            },
            "created_at": _utc_now(),
        }
        result_path = output / f"{task['task_id']}.json"
        _write_json(result_path, result)
        written.append(str(result_path))
    return {
        "schema_version": "ppt_deck_pro_max_deck_master_export_result.v1",
        "status": "exported",
        "run_id": bridge["run_id"],
        "session_id": bridge["session_id"],
        "output_dir": str(output),
        "result_count": len(written),
        "results": written,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import/export Deck Master bridge packages.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_import = sub.add_parser("import")
    p_import.add_argument("--input", required=True)
    p_import.add_argument("--project-dir", required=True)
    p_export = sub.add_parser("export")
    p_export.add_argument("--project-dir", required=True)
    p_export.add_argument("--output-dir")
    args = parser.parse_args()
    if args.command == "import":
        payload = import_deck_master_dispatch(args.input, args.project_dir)
    else:
        payload = export_deck_master_results(args.project_dir, args.output_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
