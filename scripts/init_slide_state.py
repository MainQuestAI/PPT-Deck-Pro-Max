#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_state(project_id: str, pages: int, output_mode: str) -> dict:
    return {
        "project_id": project_id,
        "global_status": "briefing",
        "visual_locked": False,
        "review_iteration": 0,
        "output_mode": output_mode,
        "pages": [
            {
                "page_id": f"slide_{i:02d}",
                "role": "unassigned",
                "status": "pending",
                "qa_status": "pending",
                "qa_reason": "",
                "visual_status": "pending",
                "rollback_stage": "",
                "rollback_owner": "",
                "rollback_targets": [],
                "rollback_reason": "",
                "rollback_routes": [],
                "content_hash": "",
                "css_components_used": [],
            }
            for i in range(1, pages + 1)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an initial slide_state.json file.")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--project-id", default="deck_project", help="Project identifier")
    parser.add_argument("--pages", type=int, required=True, help="Number of slides")
    parser.add_argument("--output-mode", default="pptx+html", choices=["pptx", "html", "pptx+html"])
    args = parser.parse_args()

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    state = build_state(args.project_id, args.pages, args.output_mode)
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output}")


if __name__ == "__main__":
    main()
