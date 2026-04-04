#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def detect_layout_stability_issues(
    state: dict | None,
    manifest: dict | None,
    require_layout_manifest: bool = False,
) -> tuple[dict[str, list[str]], dict[str, int | bool]]:
    checked_pages = len((state or {}).get("pages", [])) if isinstance(state, dict) else 0
    meta = {
        "layout_manifest_present": isinstance(manifest, dict),
        "checked_pages": checked_pages,
        "covered_pages": 0,
    }
    if not isinstance(manifest, dict):
        if require_layout_manifest:
            return {"__global__": ["geometry_broken:layout_manifest_missing"]}, meta
        return {}, meta

    issues: dict[str, list[str]] = {}
    covered_pages = 0
    for page in manifest.get("pages", []):
        page_id = str(page.get("page_id", "")).strip()
        if not page_id:
            continue
        covered_pages += 1

        page_issues: list[str] = []

        main_group = page.get("main_group", {})
        center_x = _num(main_group.get("center_x"))
        expected_center_x = _num(main_group.get("expected_center_x"))
        center_tolerance = _num(main_group.get("tolerance"), 0.15)
        if center_x and expected_center_x and abs(center_x - expected_center_x) > center_tolerance:
            page_issues.append(f"layout_alignment:main_group_center_offset:{abs(center_x - expected_center_x):.3f}")

        occupancy = page.get("occupancy", {})
        ratio = _num(occupancy.get("ratio"), -1)
        min_ratio = _num(occupancy.get("min"), -1)
        max_ratio = _num(occupancy.get("max"), -1)
        if ratio >= 0 and min_ratio >= 0 and ratio < min_ratio:
            page_issues.append(f"layout_balance:occupancy_too_low:{ratio:.3f}")
        if ratio >= 0 and max_ratio >= 0 and ratio > max_ratio:
            page_issues.append(f"layout_balance:occupancy_too_high:{ratio:.3f}")

        for group in page.get("alignment_groups", []):
            coordinates = [_num(item) for item in group.get("coordinates", [])]
            tolerance = _num(group.get("tolerance"), 0.04)
            if len(coordinates) >= 2:
                spread = max(coordinates) - min(coordinates)
                if spread > tolerance:
                    axis = group.get("axis", "axis")
                    label = group.get("label", "group")
                    page_issues.append(f"layout_alignment:{label}_{axis}_spread:{spread:.3f}")

        for connector in page.get("connectors", []):
            tolerance = _num(connector.get("tolerance"), 0.05)
            start = connector.get("start", {})
            from_anchor = connector.get("from_anchor", connector.get("from", {}))
            end = connector.get("end", {})
            to_anchor = connector.get("to_anchor", connector.get("to", {}))
            start_dx = abs(_num(start.get("x")) - _num(from_anchor.get("x")))
            start_dy = abs(_num(start.get("y")) - _num(from_anchor.get("y")))
            end_dx = abs(_num(end.get("x")) - _num(to_anchor.get("x")))
            end_dy = abs(_num(end.get("y")) - _num(to_anchor.get("y")))
            if max(start_dx, start_dy) > tolerance or max(end_dx, end_dy) > tolerance:
                label = connector.get("label", connector.get("id", "connector"))
                page_issues.append(f"geometry_broken:{label}_detached")

        for card in page.get("cards", []):
            height = _num(card.get("height"))
            min_height = _num(card.get("min_height"), -1)
            max_height = _num(card.get("max_height"), -1)
            if min_height >= 0 and height and height < min_height:
                label = card.get("label", card.get("id", "card"))
                page_issues.append(f"layout_balance:{label}_too_short:{height:.3f}")
            if max_height >= 0 and height and height > max_height:
                label = card.get("label", card.get("id", "card"))
                page_issues.append(f"density_issue:{label}_too_tall:{height:.3f}")

        if page_issues:
            issues[page_id] = sorted(set(page_issues))

    meta["covered_pages"] = covered_pages
    return issues, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate layout geometry and stability from layout_manifest.json.")
    parser.add_argument("--layout-manifest", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest_path = Path(args.layout_manifest).expanduser().resolve()
    if not manifest_path.exists():
        raise SystemExit(f"[ERROR] layout manifest not found: {manifest_path}")

    manifest = load_json(manifest_path)
    issues, _meta = detect_layout_stability_issues({}, manifest if isinstance(manifest, dict) else None)

    if args.output:
        output = Path(args.output).expanduser().resolve()
        save_json(output, issues)
        print(f"[OK] wrote layout stability issues: {output}")
    else:
        print(json.dumps(issues, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
