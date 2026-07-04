#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from page_parser import extract_page_slices


DEFAULT_FORBIDDEN_TERMS = (
    "这一页负责",
    "本页用于",
    "本页解决",
    "用这一页说明",
    "客户顾虑回应",
    "回答顾虑",
    "proof 页",
    "hero page",
    "proof",
    "tension beat",
    "objection handling",
    "batch_id",
    "source_id",
    "prompt_id",
    "generation_status",
    "build_context",
    "review_package",
    "deck_clean_pages",
    "production_note",
    "layout_note",
    "agent_trace",
    "review_note",
    "prompt_meta",
)

PRIVATE_FIELD_NAMES = {
    "production_note",
    "layout_note",
    "agent_trace",
    "review_note",
    "prompt_meta",
    "batch_id",
    "prompt_id",
    "generation_status",
}

IGNORED_CLEAN_PAGE_LABELS = {"制作备注", "讲者提示", "配图"}
DEFAULT_REPORT_NAME = "language_gate_report.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_forbidden_terms(contract_path: Path | None = None) -> list[str]:
    terms = list(DEFAULT_FORBIDDEN_TERMS)
    if contract_path and contract_path.exists():
        payload = load_json(contract_path)
        if isinstance(payload, dict):
            extra_terms = payload.get("forbidden_terms", [])
            if isinstance(extra_terms, list):
                terms.extend(str(term) for term in extra_terms if str(term).strip())
            voice = payload.get("voice", {})
            if isinstance(voice, dict) and isinstance(voice.get("forbidden"), list):
                terms.extend(str(term) for term in voice["forbidden"] if str(term).strip())
    return sorted(set(terms), key=len, reverse=True)


def first_forbidden_term(text: str, forbidden_terms: list[str] | tuple[str, ...] | None = None) -> str | None:
    terms = list(forbidden_terms or DEFAULT_FORBIDDEN_TERMS)
    for term in terms:
        if term and term in text:
            return term
    return None


def _next_command(project_dir: Path) -> str:
    return (
        "python3 scripts/run_deck_pipeline.py handoff "
        f"--project-dir {project_dir} --role external-expression"
    )


def _violation(project_dir: Path, file: str, page_id: str, field: str, term: str) -> dict[str, str]:
    return {
        "file": file,
        "page_id": page_id,
        "field": field,
        "forbidden_term": term,
        "next_command": _next_command(project_dir),
    }


def _dedupe_violations(violations: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for violation in violations:
        key = (
            violation.get("file", ""),
            violation.get("page_id", ""),
            violation.get("field", ""),
            violation.get("forbidden_term", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(violation)
    return deduped


def _field_label(line: str) -> str | None:
    match = re.match(r"^>\s*([^:：]+)\s*[:：]", line.strip())
    return match.group(1).strip() if match else None


def _scan_text(
    project_dir: Path,
    file: str,
    page_id: str,
    field: str,
    text: str,
    forbidden_terms: list[str],
) -> list[dict[str, str]]:
    term = first_forbidden_term(text, forbidden_terms)
    if not term:
        return []
    return [_violation(project_dir, file, page_id, field, term)]


def validate_clean_pages(project_dir: Path, clean_pages_path: Path, forbidden_terms: list[str]) -> list[dict[str, str]]:
    if not clean_pages_path.exists():
        return []

    violations: list[dict[str, str]] = []
    sections = extract_page_slices(clean_pages_path.read_text(encoding="utf-8"))
    for page_no, section in sections.items():
        page_id = f"slide_{page_no:02d}"
        current_ignored_label: str | None = None
        for line in section.splitlines():
            label = _field_label(line)
            if label:
                current_ignored_label = label if label in IGNORED_CLEAN_PAGE_LABELS else None
            elif not line.strip().startswith(">"):
                current_ignored_label = None
            if current_ignored_label:
                continue
            field = label or "clean_pages"
            violations.extend(_scan_text(project_dir, clean_pages_path.name, page_id, field, line, forbidden_terms))
    return violations


def _walk_json_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            items.append((child_path, str(key)))
            items.extend(_walk_json_strings(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            items.extend(_walk_json_strings(child, f"{path}[{idx}]"))
    elif isinstance(value, str):
        items.append((path, value))
    return items


def validate_json_file(
    project_dir: Path,
    path: Path,
    forbidden_terms: list[str],
    *,
    page_id_key: str = "page_id",
) -> list[dict[str, str]]:
    if not path.exists():
        return []
    payload = load_json(path)
    violations: list[dict[str, str]] = []

    page_nodes = _json_page_nodes(payload, page_id_key=page_id_key)
    if page_nodes:
        for page_path, page_id, page in page_nodes:
            for field_path, value in _walk_json_strings(page, page_path):
                last_key = field_path.rsplit(".", 1)[-1]
                if value == last_key and value in PRIVATE_FIELD_NAMES:
                    continue
                term = first_forbidden_term(value, forbidden_terms)
                if term:
                    violations.append(_violation(project_dir, path.name, page_id, field_path, term))
            for field_path, key in _walk_json_keys(page, page_path):
                if key in PRIVATE_FIELD_NAMES:
                    violations.append(_violation(project_dir, path.name, page_id, key, key))
        return violations

    for field_path, value in _walk_json_strings(payload):
        page_id = "__global__"
        last_key = field_path.rsplit(".", 1)[-1]
        if not (value == last_key and value in PRIVATE_FIELD_NAMES):
            term = first_forbidden_term(value, forbidden_terms)
            if term:
                violations.append(_violation(project_dir, path.name, page_id, field_path, term))
        if last_key in PRIVATE_FIELD_NAMES:
            violations.append(_violation(project_dir, path.name, page_id, field_path, last_key))
    return violations


def _json_page_nodes(payload: Any, *, page_id_key: str = "page_id") -> list[tuple[str, str, dict[str, Any]]]:
    if isinstance(payload, dict):
        for collection_key in ("pages", "slides"):
            pages = payload.get(collection_key)
            if isinstance(pages, list):
                nodes: list[tuple[str, str, dict[str, Any]]] = []
                for idx, page in enumerate(pages):
                    if isinstance(page, dict):
                        page_id = str(page.get(page_id_key, f"slide_{idx + 1:02d}"))
                        nodes.append((f"$.{collection_key}[{idx}]", page_id, page))
                return nodes
    if isinstance(payload, list):
        nodes = []
        for idx, page in enumerate(payload):
            if isinstance(page, dict):
                page_id = str(page.get(page_id_key, f"slide_{idx + 1:02d}"))
                nodes.append((f"$[{idx}]", page_id, page))
        return nodes
    return []


def _walk_json_keys(value: Any, path: str = "$") -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            items.append((child_path, str(key)))
            items.extend(_walk_json_keys(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            items.extend(_walk_json_keys(child, f"{path}[{idx}]"))
    return items


def validate_speaker_notes_json(project_dir: Path, path: Path, forbidden_terms: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    payload = load_json(path)
    violations: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for page_id, text in payload.items():
            violations.extend(_scan_text(project_dir, path.name, str(page_id), "speaker_script", str(text), forbidden_terms))
    return violations


def extract_html_notes(html_text: str) -> list[str]:
    return re.findall(r"<aside[^>]*class=[\"'][^\"']*notes[^\"']*[\"'][^>]*>(.*?)</aside>", html_text, re.IGNORECASE | re.DOTALL)


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def validate_html_notes(project_dir: Path, path: Path, forbidden_terms: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    violations: list[dict[str, str]] = []
    for idx, note in enumerate(extract_html_notes(path.read_text(encoding="utf-8")), start=1):
        violations.extend(_scan_text(project_dir, str(path), f"slide_{idx:02d}", "html_notes", _strip_tags(note), forbidden_terms))
    return violations


def extract_pptx_notes_text(path: Path) -> list[str]:
    if not path.exists():
        return []
    notes: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("ppt/notesSlides/") or not name.endswith(".xml"):
                continue
            xml_text = archive.read(name).decode("utf-8", errors="ignore")
            notes.append(re.sub(r"<[^>]+>", " ", xml_text))
    return notes


def validate_pptx_notes(project_dir: Path, path: Path, forbidden_terms: list[str]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for idx, note in enumerate(extract_pptx_notes_text(path), start=1):
        violations.extend(_scan_text(project_dir, str(path), f"slide_{idx:02d}", "pptx_notes", note, forbidden_terms))
    return violations


def validate_project_language(
    project_dir: Path,
    *,
    contract_path: Path | None = None,
    require_contract: bool = False,
    clean_pages_path: Path | None = None,
    message_pack_path: Path | None = None,
    customer_copy_path: Path | None = None,
    speaker_notes_path: Path | None = None,
    html_path: Path | None = None,
    pptx_path: Path | None = None,
) -> list[dict[str, str]]:
    contract_path = contract_path or project_dir / "audience_language_contract.json"
    if require_contract and not contract_path.exists():
        return [_violation(project_dir, str(contract_path), "__global__", "audience_language_contract", "missing_contract")]

    forbidden_terms = load_forbidden_terms(contract_path if contract_path.exists() else None)
    violations: list[dict[str, str]] = []

    violations.extend(validate_clean_pages(project_dir, clean_pages_path or project_dir / "deck_clean_pages.md", forbidden_terms))
    violations.extend(validate_json_file(project_dir, message_pack_path or project_dir / "deck_external_message_pack.json", forbidden_terms))
    violations.extend(validate_json_file(project_dir, customer_copy_path or project_dir / "customer_visible_copy.json", forbidden_terms))
    violations.extend(validate_speaker_notes_json(project_dir, speaker_notes_path or project_dir / "speaker_notes.json", forbidden_terms))

    if html_path:
        violations.extend(validate_html_notes(project_dir, html_path, forbidden_terms))
    if pptx_path:
        violations.extend(validate_pptx_notes(project_dir, pptx_path, forbidden_terms))
    return _dedupe_violations(violations)


def resolve_scanned_files(
    project_dir: Path,
    *,
    clean_pages_path: Path | None = None,
    message_pack_path: Path | None = None,
    customer_copy_path: Path | None = None,
    speaker_notes_path: Path | None = None,
    html_path: Path | None = None,
    pptx_path: Path | None = None,
) -> list[str]:
    candidates = [
        clean_pages_path or project_dir / "deck_clean_pages.md",
        message_pack_path or project_dir / "deck_external_message_pack.json",
        customer_copy_path or project_dir / "customer_visible_copy.json",
        speaker_notes_path or project_dir / "speaker_notes.json",
    ]
    if html_path:
        candidates.append(html_path)
    if pptx_path:
        candidates.append(pptx_path)
    return [str(path) for path in candidates if path.exists()]


def build_language_gate_report(project_dir: Path, violations: list[dict[str, str]], scanned_files: list[str]) -> dict[str, Any]:
    term_counts: dict[str, int] = {}
    field_counts: dict[str, int] = {}
    for violation in violations:
        term = violation.get("forbidden_term", "")
        field = violation.get("field", "")
        if term:
            term_counts[term] = term_counts.get(term, 0) + 1
        if field:
            field_counts[field] = field_counts.get(field, 0) + 1

    return {
        "status": "failed" if violations else "passed",
        "project_dir": str(project_dir),
        "scanned_files": scanned_files,
        "scanned_file_count": len(scanned_files),
        "violation_count": len(violations),
        "fields": [
            {"field": field, "count": count}
            for field, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "top_terms": [
            {"term": term, "count": count}
            for term, count in sorted(term_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "violations": violations,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate customer-visible language boundaries.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--language-contract")
    parser.add_argument("--require-contract", action="store_true")
    parser.add_argument("--clean-pages")
    parser.add_argument("--message-pack")
    parser.add_argument("--customer-copy")
    parser.add_argument("--speaker-notes")
    parser.add_argument("--html-path")
    parser.add_argument("--pptx-path")
    parser.add_argument("--json-output", help="Write machine-readable validation result")
    parser.add_argument("--report-output", help=f"Write language gate report, defaults to {DEFAULT_REPORT_NAME}")
    parser.add_argument("--no-report", action="store_true", help="Skip writing language gate report")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    contract_path = Path(args.language_contract).expanduser().resolve() if args.language_contract else None
    clean_pages_path = Path(args.clean_pages).expanduser().resolve() if args.clean_pages else None
    message_pack_path = Path(args.message_pack).expanduser().resolve() if args.message_pack else None
    customer_copy_path = Path(args.customer_copy).expanduser().resolve() if args.customer_copy else None
    speaker_notes_path = Path(args.speaker_notes).expanduser().resolve() if args.speaker_notes else None
    html_path = Path(args.html_path).expanduser().resolve() if args.html_path else None
    pptx_path = Path(args.pptx_path).expanduser().resolve() if args.pptx_path else None
    violations = validate_project_language(
        project_dir,
        contract_path=contract_path,
        require_contract=args.require_contract,
        clean_pages_path=clean_pages_path,
        message_pack_path=message_pack_path,
        customer_copy_path=customer_copy_path,
        speaker_notes_path=speaker_notes_path,
        html_path=html_path,
        pptx_path=pptx_path,
    )
    scanned_files = resolve_scanned_files(
        project_dir,
        clean_pages_path=clean_pages_path,
        message_pack_path=message_pack_path,
        customer_copy_path=customer_copy_path,
        speaker_notes_path=speaker_notes_path,
        html_path=html_path,
        pptx_path=pptx_path,
    )
    report = build_language_gate_report(project_dir, violations, scanned_files)
    result = {"status": report["status"], "violations": violations, "summary": report}
    if args.json_output:
        write_json(Path(args.json_output).expanduser().resolve(), result)
    if not args.no_report:
        report_output = Path(args.report_output).expanduser().resolve() if args.report_output else project_dir / DEFAULT_REPORT_NAME
        write_json(report_output, report)
    if violations:
        print("[ERROR] external language contract failed")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print(f"[OK] external language contract passed; scanned_files={len(scanned_files)}")


if __name__ == "__main__":
    main()
