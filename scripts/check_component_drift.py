#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether slide state uses undefined components.")
    parser.add_argument("--state", required=True)
    parser.add_argument("--theme-tokens", required=True)
    args = parser.parse_args()

    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    theme = json.loads(Path(args.theme_tokens).read_text(encoding="utf-8"))
    allowed = set(theme.get("components", {}).keys())

    unknown = []
    for page in state.get("pages", []):
        used = page.get("css_components_used", [])
        for component in used:
            if allowed and component not in allowed:
                unknown.append((page.get("page_id", "unknown"), component))

    if unknown:
        print("[ERROR] undefined components found:")
        for page_id, component in unknown:
            print(f"  - {page_id}: {component}")
        sys.exit(1)

    print("[OK] no component drift detected")


if __name__ == "__main__":
    main()
