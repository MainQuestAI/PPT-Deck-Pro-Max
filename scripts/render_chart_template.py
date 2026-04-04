#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def normalize_value(value: object, *, raw: bool) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = "" if value is None else str(value)
    return text if raw else html.escape(text)


def render(template_text: str, mapping: dict[str, object], raw_keys: set[str] | None = None) -> str:
    raw_keys = raw_keys or set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in mapping:
            return match.group(0)
        return normalize_value(mapping[key], raw=key in raw_keys)

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a chart template by replacing {{PLACEHOLDER}} tokens.")
    parser.add_argument("--template", required=True)
    parser.add_argument("--data", required=True, help="JSON file with placeholder mappings")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    template_path = Path(args.template).expanduser().resolve()
    data_path = Path(args.data).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    template_text = template_path.read_text(encoding="utf-8")
    mapping = json.loads(data_path.read_text(encoding="utf-8"))
    raw_keys = set(mapping.pop("__raw__", [])) if isinstance(mapping, dict) else set()
    output_text = render(template_text, mapping, raw_keys)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"[OK] rendered {output_path}")


if __name__ == "__main__":
    main()
