#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_SCORECARD = {
    "overall_score": 0,
    "dimensions": {
        "audience_fit": 0,
        "buying_reason_clarity": 0,
        "proof_strength": 0,
        "objection_coverage": 0,
        "narrative_flow": 0,
        "commercial_ask": 0,
    },
    "summary": "",
    "recommended_action": "",
    "weak_dimensions": [],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a blank commercial scorecard scaffold.")
    parser.add_argument("--project-dir")
    parser.add_argument("--output")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve() if args.project_dir else None
    output = Path(args.output).expanduser().resolve() if args.output else (project_dir / "commercial_scorecard.json" if project_dir else None)
    if not output:
        raise SystemExit("[ERROR] 需要提供 --project-dir 或 --output。")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(json.dumps(DEFAULT_SCORECARD, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
