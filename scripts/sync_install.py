#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_DECK_MASTER_CURRENT = Path.home() / ".deck-master" / "current"
ENTRY_REL_PATH = Path("skills") / "ppt-deck-pro-max" / "SKILL.md"
CUSTOMER_LANGUAGE_MARKER = "<!-- customer-language-first:v1 -->"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def source_commit(source_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "--short", "HEAD"],
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def source_version(source_root: Path) -> str:
    version_path = source_root / "VERSION"
    return read_text(version_path).strip() or "unknown"


def build_compat_entry(source_root: Path) -> str:
    version = source_version(source_root)
    commit = source_commit(source_root)
    pipeline = source_root / "scripts" / "run_deck_pipeline.py"
    return f"""---
name: ppt-deck-pro-max
description: Deck Master bundled production intelligence compatibility entry for PPT Deck Pro Max, with customer-language-first source workflow access.
triggers:
  - start a generation session
  - run page production
  - import generation results
  - ppt deck pro max
  - customer-language-first
---

# PPT Deck Pro Max Compatibility Entry

This compatibility entry is kept for existing prompts and local installs.
For new Deck Master production workflows, prefer `deck-producer`.
For source-level customer language workflows, use the commands below.

## Source Alignment

- Source root: `{source_root}`
- Source version: `{version}`
- Source commit: `{commit}`
- Sync check: `python3 {pipeline} sync-install --dry-run`

## Customer Language First

```bash
python3 {pipeline} customer-language-first --project-dir <project-dir> --preset solution_deck
python3 {pipeline} migrate-language --project-dir <project-dir> --dry-run
python3 {pipeline} validate-language --project-dir <project-dir>
```

The source workflow keeps customer-visible copy, speaker scripts, HTML notes, and PPTX notes inside the audience language contract boundary.

## First Checks

```bash
~/.deck-master/bin/deck-master setup-status --include-suite --output json
~/.deck-master/bin/deck-master generation-session status --run-dir <run_dir> --run-id <run_id>
```

## Allowed Deck Master Commands

```bash
~/.deck-master/bin/deck-master generation-session create --run-dir <run_dir> --run-id <run_id>
~/.deck-master/bin/deck-master run-generation --run-dir <run_dir> --run-id <run_id>
~/.deck-master/bin/deck-master generation-session dispatch --run-dir <run_dir> --run-id <run_id>
~/.deck-master/bin/deck-master generation-session import-results --run-dir <run_dir> --run-id <run_id> --input <result.json>
~/.deck-master/bin/deck-master generation-session import-results --run-dir <run_dir> --run-id <run_id> --input <result_dir>
```

## Production Dispatch

Production `run-generation` writes `generation_dispatch/dispatch_package.json` and sets the session to `awaiting_agent_execution`.
Read the dispatch package, produce real assets under the run directory, then write `deck_generation_result.v2` files into `generation_results/`.

Each completed result must include run/session binding, run-relative paths, SHA-256 checksums, byte sizes, `source_fingerprint`, and `producer` metadata.
Bundled placeholder output is fixture/dev only and cannot be imported as production output.


{CUSTOMER_LANGUAGE_MARKER}
<!-- skill-os-contract:v1 -->
## Public Stage
Maps to public stage: deck-producer. This is a compatibility wrapper; prefer the public `deck-producer` skill for new Deck Master runs.
"""


def classify_entry(text: str, entry_path: Path, source_root: Path) -> str:
    if not text:
        return "missing"
    try:
        if entry_path.is_symlink() and entry_path.resolve() == (source_root / "SKILL.md").resolve():
            return "source_symlink"
    except OSError:
        pass
    if CUSTOMER_LANGUAGE_MARKER in text:
        return "customer_language_first_wrapper"
    if "PPT Deck Pro Max Compatibility Entry" in text and "deck-producer" in text:
        return "deck_master_compat_wrapper"
    if "name: ppt-deck-pro-max" in text and "# PPT Deck Pro Max" in text:
        return "source_skill"
    return "custom"


def inspect_install(source_root: Path = SKILL_ROOT, deck_master_current: Path = DEFAULT_DECK_MASTER_CURRENT) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    deck_master_current = deck_master_current.expanduser().resolve()
    entry_path = deck_master_current / ENTRY_REL_PATH
    desired = build_compat_entry(source_root)
    current = read_text(entry_path)
    entry_exists = entry_path.exists()
    up_to_date = entry_exists and current == desired
    contains_customer_language = "customer-language-first" in current and CUSTOMER_LANGUAGE_MARKER in current
    entry_mtime = entry_path.stat().st_mtime if entry_exists else None
    next_command = (
        "python3 scripts/run_deck_pipeline.py sync-install --write"
        if not up_to_date
        else "python3 scripts/run_deck_pipeline.py doctor --install-status"
    )
    return {
        "status": "up_to_date" if up_to_date else "needs_sync",
        "source_root": str(source_root),
        "source_version": source_version(source_root),
        "source_commit": source_commit(source_root),
        "deck_master_current": str(deck_master_current),
        "deck_master_current_exists": deck_master_current.exists(),
        "entry_path": str(entry_path),
        "entry_exists": entry_exists,
        "entry_type": classify_entry(current, entry_path, source_root),
        "entry_updated_at": entry_mtime,
        "entry_contains_customer_language_first": contains_customer_language,
        "entry_up_to_date": up_to_date,
        "would_write": not up_to_date,
        "next_command": next_command,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_human(report: dict[str, Any]) -> None:
    label = "[OK]" if report["entry_up_to_date"] else "[WARN]"
    print(f"{label} install status: {report['status']}")
    print(f"source: {report['source_version']} @ {report['source_commit']}")
    print(f"entry: {report['entry_path']}")
    print(f"entry_type: {report['entry_type']}")
    print(f"customer_language_first: {report['entry_contains_customer_language_first']}")
    print(f"next_command: {report['next_command']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect or sync the local ppt-deck-pro-max compatibility entry.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report install status without writing")
    mode.add_argument("--write", action="store_true", help="Update the local ppt-deck-pro-max compatibility entry")
    parser.add_argument("--source-root", default=str(SKILL_ROOT))
    parser.add_argument("--deck-master-current", default=str(DEFAULT_DECK_MASTER_CURRENT))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--json-output", help="Write machine-readable JSON report")
    args = parser.parse_args(argv)

    source_root = Path(args.source_root).expanduser().resolve()
    deck_master_current = Path(args.deck_master_current).expanduser().resolve()
    report = inspect_install(source_root=source_root, deck_master_current=deck_master_current)

    if args.write and report["would_write"]:
        entry_path = Path(report["entry_path"])
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        entry_path.write_text(build_compat_entry(source_root), encoding="utf-8")
        report = inspect_install(source_root=source_root, deck_master_current=deck_master_current)
        report["wrote"] = True
    else:
        report["wrote"] = False

    if args.json_output:
        write_json(Path(args.json_output).expanduser().resolve(), report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
