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
SPEAKER_SCRIPT_LABELS = {"讲者话术"}
LEGACY_SPEAKER_NOTE_LABELS = {"演讲备注"}
PRODUCTION_NOTE_LABELS = {"制作备注"}
SPEAKER_CUE_LABELS = {"讲者提示"}
BLOCKQUOTE_FIELD_PATTERN = re.compile(r"^>\s*([^:：]+)\s*[:：]\s*(.*)$")


def _extract_blockquote_fields(
    text: str,
    labels: set[str],
    *,
    allow_continuation: bool = True,
) -> dict[int, list[str]]:
    slices = extract_page_slices(text)
    fields: dict[int, list[str]] = {}
    for page_no, section in slices.items():
        current_label: str | None = None
        for raw_line in section.splitlines():
            line = raw_line.strip()
            if not line.startswith(">"):
                current_label = None
                continue
            match = BLOCKQUOTE_FIELD_PATTERN.match(line)
            if match:
                label = match.group(1).strip()
                value = match.group(2).strip()
                current_label = label if label in labels else None
                if current_label and value:
                    fields.setdefault(page_no, []).append(value)
                continue
            if allow_continuation and current_label in labels:
                continuation = line[1:].strip()
                if continuation:
                    fields.setdefault(page_no, []).append(continuation)
    return fields


def _join_field_values(values_by_page: dict[int, list[str]]) -> dict[int, str]:
    return {
        page_no: " ".join(value.strip() for value in values if value.strip())
        for page_no, values in values_by_page.items()
        if any(value.strip() for value in values)
    }


def extract_speaker_scripts(text: str, *, allow_legacy: bool = True) -> dict[int, str]:
    """Extract customer-sayable speaker scripts from deck_clean_pages.md.

    Preferred format: > 讲者话术: ...
    Legacy format: > 演讲备注: ... (only when allow_legacy=True and no new script exists on the same page)
    """
    scripts = _join_field_values(_extract_blockquote_fields(text, SPEAKER_SCRIPT_LABELS))
    if not allow_legacy:
        return scripts

    legacy_notes = extract_speaker_notes(text)
    for page_no, note in legacy_notes.items():
        scripts.setdefault(page_no, note)
    return scripts


def extract_production_notes(text: str) -> dict[int, str]:
    """Extract private production notes. These must never be exported as speaker notes."""
    return _join_field_values(_extract_blockquote_fields(text, PRODUCTION_NOTE_LABELS))


def extract_speaker_cues(text: str) -> dict[int, str]:
    """Extract private speaker operation cues such as pauses or transitions."""
    return _join_field_values(_extract_blockquote_fields(text, SPEAKER_CUE_LABELS))


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
