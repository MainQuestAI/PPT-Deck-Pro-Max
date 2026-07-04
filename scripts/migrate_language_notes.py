#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LEGACY_NOTE_RE = re.compile(r"^(?P<prefix>\s*>\s*)演讲备注(?P<suffix>\s*[:：]\s*)(?P<body>.*)$")
PRODUCTION_NOTE_TERMS = (
    "左侧",
    "右侧",
    "上方",
    "下方",
    "布局",
    "排版",
    "视觉",
    "图表",
    "卡片",
    "配图",
    "图片",
    "素材",
    "背景",
    "组件",
    "字号",
    "留白",
    "动效",
    "icon",
    "Icon",
    "页面结构",
    "页面布局",
    "放置",
    "放一个",
    "hero page",
    "proof 页",
)


def is_probable_production_note(text: str) -> bool:
    return any(term in text for term in PRODUCTION_NOTE_TERMS)


def _next_command(project_dir: Path) -> str:
    return (
        "python3 scripts/run_deck_pipeline.py migrate-language "
        f"--project-dir {project_dir} --write --confirm-production-notes"
    )


def migrate_text(text: str, *, confirm_production_notes: bool = False) -> tuple[str, list[dict[str, Any]], bool]:
    output_lines: list[str] = []
    actions: list[dict[str, Any]] = []
    blocked = False

    for line_no, line in enumerate(text.splitlines(keepends=True), start=1):
        line_body = line[:-1] if line.endswith("\n") else line
        line_end = "\n" if line.endswith("\n") else ""
        match = LEGACY_NOTE_RE.match(line_body)
        if not match:
            output_lines.append(line)
            continue

        body = match.group("body")
        if is_probable_production_note(body):
            target_label = "制作备注"
            status = "migrated" if confirm_production_notes else "needs_confirmation"
            if not confirm_production_notes:
                blocked = True
                output_lines.append(line)
            else:
                output_lines.append(
                    f"{match.group('prefix')}{target_label}{match.group('suffix')}{body}{line_end}"
                )
        else:
            target_label = "讲者话术"
            status = "migrated"
            output_lines.append(f"{match.group('prefix')}{target_label}{match.group('suffix')}{body}{line_end}")

        actions.append(
            {
                "line": line_no,
                "from": "演讲备注",
                "to": target_label,
                "status": status,
            }
        )

    return "".join(output_lines), actions, blocked


def migrate_file(
    path: Path,
    *,
    project_dir: Path,
    dry_run: bool,
    write: bool,
    confirm_production_notes: bool,
) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    migrated, actions, blocked = migrate_text(original, confirm_production_notes=confirm_production_notes)
    changed = bool(actions) and migrated != original

    if write and blocked:
        return {
            "file": str(path),
            "changed": False,
            "blocked": True,
            "actions": actions,
            "next_command": _next_command(project_dir),
        }

    if write and changed:
        path.write_text(migrated, encoding="utf-8")

    return {
        "file": str(path),
        "changed": bool(write and changed),
        "would_change": bool(dry_run and changed),
        "blocked": blocked,
        "actions": actions,
        "next_command": _next_command(project_dir) if blocked else "",
    }


def build_summary(report: dict[str, Any]) -> dict[str, int]:
    actions = report.get("actions", [])
    return {
        "legacy_notes": len(actions),
        "speaker_scripts": sum(1 for action in actions if action.get("to") == "讲者话术"),
        "production_notes": sum(1 for action in actions if action.get("to") == "制作备注"),
        "needs_confirmation": sum(1 for action in actions if action.get("status") == "needs_confirmation"),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy speaker notes to customer-language-first labels.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--clean-pages", help="Defaults to deck_clean_pages.md in project dir")
    parser.add_argument("--dry-run", action="store_true", help="Report planned changes without writing")
    parser.add_argument("--write", action="store_true", help="Write migrated labels")
    parser.add_argument("--confirm-production-notes", action="store_true", help="Allow suspected production notes to become `> 制作备注:`")
    parser.add_argument("--report-output", help="Write migration report JSON")
    args = parser.parse_args()

    if args.dry_run == args.write:
        raise SystemExit("[ERROR] choose exactly one of --dry-run or --write")

    project_dir = Path(args.project_dir).expanduser().resolve()
    clean_pages = Path(args.clean_pages).expanduser().resolve() if args.clean_pages else project_dir / "deck_clean_pages.md"
    if not clean_pages.exists():
        raise SystemExit(f"[ERROR] clean pages not found: {clean_pages}")

    report = migrate_file(
        clean_pages,
        project_dir=project_dir,
        dry_run=args.dry_run,
        write=args.write,
        confirm_production_notes=args.confirm_production_notes,
    )
    report["summary"] = build_summary(report)

    if args.report_output:
        write_json(Path(args.report_output).expanduser().resolve(), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("blocked"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
