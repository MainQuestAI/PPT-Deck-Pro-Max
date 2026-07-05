#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from sync_install import DEFAULT_DECK_MASTER_CURRENT, inspect_install
from validate_deck_outputs import CORE_ARTIFACTS
from validate_schema import validate_project


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def add_check(checks: list[Check], name: str, ok: bool, detail: str, *, warning: bool = False) -> None:
    if ok:
        status = "ok"
    else:
        status = "warn" if warning else "error"
    checks.append(Check(name=name, status=status, detail=detail))


def check_python(checks: list[Check]) -> None:
    version = sys.version_info
    add_check(
        checks,
        "python",
        version >= (3, 10),
        f"{version.major}.{version.minor}.{version.micro} (requires 3.10+)",
    )


def check_dependencies(checks: list[Check]) -> None:
    dependencies = [
        ("python-pptx", "pptx", False),
        ("Pillow", "PIL", False),
        ("jsonschema", "jsonschema", False),
        ("pytest", "pytest", True),
        ("playwright", "playwright", True),
    ]
    for label, module_name, optional in dependencies:
        found = module_available(module_name)
        suffix = "optional" if optional else "required"
        add_check(checks, f"dependency:{label}", found, f"{suffix} module `{module_name}`", warning=optional)


def check_repo_layout(checks: list[Check], skill_root: Path) -> None:
    required_paths = [
        "SKILL.md",
        "README.md",
        "README.zh-CN.md",
        "scripts/run_deck_pipeline.py",
        "scripts/validate_schema.py",
        "references/slide_state.schema.json",
        "references/build_contract.md",
        "assets/html_deck_starter/index.html",
        "assets/pptx_deck_starter/starter.js",
        "tests",
    ]
    for rel_path in required_paths:
        path = skill_root / rel_path
        add_check(checks, f"path:{rel_path}", path.exists(), str(path))


def check_schema_inventory(checks: list[Check], skill_root: Path) -> None:
    schemas = sorted((skill_root / "references").glob("*.schema.json"))
    add_check(checks, "schema:inventory", bool(schemas), f"{len(schemas)} schema file(s) found")
    for schema_path in schemas:
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            add_check(checks, f"schema:{schema_path.name}", False, str(exc))


def check_build_support(checks: list[Check], skill_root: Path) -> None:
    html_starter = skill_root / "assets" / "html_deck_starter" / "index.html"
    pptx_starter = skill_root / "assets" / "pptx_deck_starter" / "starter.js"
    add_check(checks, "build:html-starter", html_starter.exists(), str(html_starter))
    add_check(checks, "build:pptx-starter", pptx_starter.exists(), str(pptx_starter))
    add_check(
        checks,
        "build:node",
        shutil.which("node") is not None,
        "Node.js is needed for the PPTX starter; HTML-only pipelines can ignore this warning",
        warning=True,
    )
    checks.append(
        Check(
            name="build:agent-skills",
            status="warn",
            detail="CLI cannot introspect Codex skills; confirm imagegen/frontend-design/slides availability in the agent host.",
        )
    )


def check_project(checks: list[Check], project_dir: Path) -> None:
    add_check(checks, "project:dir", project_dir.exists() and project_dir.is_dir(), str(project_dir))
    if not project_dir.exists():
        return

    missing_core = [name for name in CORE_ARTIFACTS if not (project_dir / name).exists()]
    add_check(
        checks,
        "project:core-artifacts",
        not missing_core,
        "all core artifacts present" if not missing_core else f"missing: {', '.join(missing_core)}",
        warning=True,
    )

    schema_errors = validate_project(project_dir, strict=False)
    if schema_errors:
        detail = "; ".join(f"{name}: {len(errors)} error(s)" for name, errors in schema_errors.items())
        add_check(checks, "project:schema", False, detail)
    else:
        add_check(checks, "project:schema", True, "known project JSON files validate")


def check_install_status(checks: list[Check], skill_root: Path, deck_master_current: Path | None = None) -> None:
    deck_master_current = deck_master_current or DEFAULT_DECK_MASTER_CURRENT
    report = inspect_install(source_root=skill_root, deck_master_current=deck_master_current)
    next_command = report["next_command"]
    add_check(
        checks,
        "install:deck-master-current",
        bool(report["deck_master_current_exists"]),
        f"{report['deck_master_current']}; next={next_command}",
        warning=True,
    )
    add_check(
        checks,
        "install:ppt-deck-pro-max-entry",
        bool(report["entry_exists"]),
        f"{report['entry_path']}; type={report['entry_type']}; next={next_command}",
        warning=True,
    )
    add_check(
        checks,
        "install:source-version",
        report["source_version"] != "unknown",
        f"version={report['source_version']} commit={report['source_commit']}",
        warning=True,
    )
    add_check(
        checks,
        "install:entry-up-to-date",
        bool(report["entry_up_to_date"]),
        f"status={report['status']}; customer-language-first={report['entry_contains_customer_language_first']}; next={next_command}",
        warning=True,
    )
    gitignore = skill_root / ".gitignore"
    ignored = any(line.strip() == "docs/" for line in gitignore.read_text(encoding="utf-8").splitlines()) if gitignore.exists() else False
    add_check(checks, "install:docs-ignored", ignored, f"{gitignore}; docs/ must stay private")


def run_checks(
    skill_root: Path = SKILL_ROOT,
    project_dir: Path | None = None,
    *,
    include_install_status: bool = False,
    deck_master_current: Path | None = None,
) -> list[Check]:
    checks: list[Check] = []
    check_python(checks)
    check_dependencies(checks)
    check_repo_layout(checks, skill_root)
    check_schema_inventory(checks, skill_root)
    check_build_support(checks, skill_root)
    if include_install_status:
        check_install_status(checks, skill_root, deck_master_current=deck_master_current)
    if project_dir is not None:
        check_project(checks, project_dir.expanduser().resolve())
    return checks


def print_human(checks: list[Check]) -> None:
    for check in checks:
        label = {"ok": "[OK]", "warn": "[WARN]", "error": "[ERROR]"}[check.status]
        print(f"{label} {check.name}: {check.detail}")

    errors = sum(1 for check in checks if check.status == "error")
    warnings = sum(1 for check in checks if check.status == "warn")
    print(f"[SUMMARY] errors={errors} warnings={warnings} checks={len(checks)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run environment and project health checks for Deck Production Orchestrator.")
    parser.add_argument("--project-dir", help="Optional deck project directory to validate")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--install-status", action="store_true", help="Also inspect local Deck Master install entry")
    parser.add_argument("--deck-master-current", help="Override ~/.deck-master/current for install status checks")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    project_dir = Path(args.project_dir) if args.project_dir else None
    deck_master_current = Path(args.deck_master_current) if args.deck_master_current else None
    checks = run_checks(
        project_dir=project_dir,
        include_install_status=args.install_status or args.json,
        deck_master_current=deck_master_current,
    )

    if args.json:
        print(json.dumps([asdict(check) for check in checks], ensure_ascii=False, indent=2))
    else:
        print_human(checks)

    has_errors = any(check.status == "error" for check in checks)
    has_warnings = any(check.status == "warn" for check in checks)
    if has_errors or (args.strict and has_warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
