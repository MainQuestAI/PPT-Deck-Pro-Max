#!/usr/bin/env python3
from __future__ import annotations

import re


HEADING_PATTERN = re.compile(
    r"""
    ^\s*
    (?:
      \#{1,6}\s* |
      \*\*\s*
    )?
    (?:
      (?:final\s+)?page\s*0*(\d+)\b |
      slide[_\s-]*0*(\d+)\b |
      页面\s*0*(\d+)\b |
      第\s*0*(\d+)\s*页\b
    )
    (?:\s*\*\*)?
    .*$
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
)


def page_id_to_number(page_id: str) -> int | None:
    match = re.search(r"(\d+)", page_id or "")
    return int(match.group(1)) if match else None


def extract_page_slices(text: str) -> dict[int, str]:
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return {}

    sections: dict[int, str] = {}
    for idx, match in enumerate(matches):
        page_no = next(int(group) for group in match.groups() if group is not None)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[page_no] = text[start:end].strip()
    return sections
