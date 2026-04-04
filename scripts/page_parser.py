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


ASSET_DECL_PATTERN = re.compile(
    r"^>\s*配图\s*[:：]\s*(.+?)$",
    re.MULTILINE,
)


def _parse_asset_fields(raw: str) -> dict[str, str]:
    """Parse 'key=value | key=value' into a dict."""
    fields: dict[str, str] = {}
    for part in raw.split("|"):
        part = part.strip()
        if "=" in part:
            key, _, value = part.partition("=")
            fields[key.strip()] = value.strip()
    return fields


def extract_asset_declarations(text: str) -> dict[int, list[dict[str, str]]]:
    """Extract asset declarations from deck_clean_pages.md.

    Returns a mapping of page number to list of asset declaration dicts.
    Declarations are expected in the format: > 配图: id=xxx | desc=xxx | frame=macbook
    """
    slices = extract_page_slices(text)
    assets: dict[int, list[dict[str, str]]] = {}
    for page_no, section in slices.items():
        matches = ASSET_DECL_PATTERN.findall(section)
        if matches:
            assets[page_no] = [_parse_asset_fields(m) for m in matches]
    return assets


SPEAKER_NOTE_PATTERN = re.compile(
    r"^>\s*演讲备注\s*[:：]\s*(.+?)$",
    re.MULTILINE,
)


def extract_speaker_notes(text: str) -> dict[int, str]:
    """Extract speaker notes from deck_clean_pages.md.

    Returns a mapping of page number to speaker note text.
    Notes are expected in the format: > 演讲备注: ...
    """
    slices = extract_page_slices(text)
    notes: dict[int, str] = {}
    for page_no, section in slices.items():
        matches = SPEAKER_NOTE_PATTERN.findall(section)
        if matches:
            notes[page_no] = " ".join(m.strip() for m in matches)
    return notes


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
