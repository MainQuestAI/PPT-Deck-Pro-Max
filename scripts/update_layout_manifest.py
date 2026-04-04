#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"pages": []}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_page(manifest: dict, page: dict) -> dict:
    lookup = {item.get("page_id"): idx for idx, item in enumerate(manifest.get("pages", [])) if isinstance(item, dict)}
    page_id = page.get("page_id")
    if not page_id:
        raise SystemExit("[ERROR] page payload missing `page_id`.")
    if page_id in lookup:
        current = manifest["pages"][lookup[page_id]]
        current.update(page)
    else:
        manifest.setdefault("pages", []).append(page)
        manifest["pages"].sort(key=lambda item: item.get("page_id", ""))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Upsert page-level geometry metadata into layout_manifest.json.")
    parser.add_argument("--project-dir")
    parser.add_argument("--manifest")
    parser.add_argument("--json-file")
    parser.add_argument("--page-id")
    parser.add_argument("--archetype")
    parser.add_argument("--role")
    parser.add_argument("--center-x", type=float)
    parser.add_argument("--expected-center-x", type=float)
    parser.add_argument("--tolerance", type=float)
    parser.add_argument("--occupancy-ratio", type=float)
    parser.add_argument("--occupancy-min", type=float)
    parser.add_argument("--occupancy-max", type=float)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve() if args.project_dir else None
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else (project_dir / "layout_manifest.json" if project_dir else None)
    if not manifest_path:
        raise SystemExit("[ERROR] 需要提供 --project-dir 或 --manifest。")

    manifest = load_json(manifest_path)
    if args.json_file:
        page = json.loads(Path(args.json_file).expanduser().resolve().read_text(encoding="utf-8"))
    else:
        if not args.page_id:
            raise SystemExit("[ERROR] 直接更新模式下必须提供 --page-id。")
        page = {
            "page_id": args.page_id,
            "archetype": args.archetype or "",
            "role": args.role or "",
            "main_group": {
                "center_x": args.center_x if args.center_x is not None else 0.5,
                "expected_center_x": args.expected_center_x if args.expected_center_x is not None else 0.5,
                "tolerance": args.tolerance if args.tolerance is not None else 0.06,
            },
            "occupancy": {
                "ratio": args.occupancy_ratio if args.occupancy_ratio is not None else 0.42,
                "min": args.occupancy_min if args.occupancy_min is not None else 0.24,
                "max": args.occupancy_max if args.occupancy_max is not None else 0.60,
            },
        }

    updated = upsert_page(manifest, page)
    save_json(manifest_path, updated)
    print(f"[OK] updated {manifest_path}")


if __name__ == "__main__":
    main()
