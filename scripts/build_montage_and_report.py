#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from check_layout_stability import detect_layout_stability_issues
from page_parser import extract_page_slices, extract_speaker_notes

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None


ROLE_DENSITY_THRESHOLDS: dict[str, tuple[int, int]] = {
    "hero_cover": (90, 130),
    "hero_problem": (260, 360),
    "diagnostic_board": (320, 420),
    "hero_proof": (240, 340),
    "hero_system": (240, 340),
    "hero_diff": (240, 340),
    "hero_value": (220, 320),
    "hero_cta": (120, 180),
}

ALLOWED_REVIEW_SEVERITY = {"low", "medium", "high", "critical"}
REQUIRED_REVIEW_FIELDS = ("page_id", "severity", "type", "reason", "suggested_fix", "source_image")
REQUIRED_SCORECARD_FIELDS = ("overall_score", "dimensions", "summary", "recommended_action")
REQUIRED_SCORECARD_DIMENSIONS = (
    "audience_fit",
    "buying_reason_clarity",
    "proof_strength",
    "objection_coverage",
    "narrative_flow",
    "commercial_ask",
)


def maybe_build_montage(images: list[Path], output: Path) -> bool:
    if not Image or not images:
        return False

    thumbs = []
    for path in images:
        img = Image.open(path).convert("RGB")
        img.thumbnail((360, 203))
        canvas = Image.new("RGB", (380, 240), "white")
        x = (380 - img.width) // 2
        y = 12
        canvas.paste(img, (x, y))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 214), path.stem, fill="black")
        thumbs.append(canvas)

    cols = 3
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 400, rows * 260), "#f4f6f8")
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * 400 + 10
        y = (idx // cols) * 260 + 10
        sheet.paste(thumb, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return True


def load_json(path: Path | None) -> dict | list | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def detect_component_drift(state: dict, theme: dict | None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    allowed = set((theme or {}).get("components", {}).keys())
    if not allowed:
        return issues
    for page in state.get("pages", []):
        page_id = page.get("page_id", "unknown")
        for component in page.get("css_components_used", []):
            if component not in allowed:
                issues.setdefault(page_id, []).append(f"undefined_component:{component}")
    return issues


def detect_density_issues(state: dict, clean_pages_text: str | None, warn_chars: int, fail_chars: int) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    if not clean_pages_text:
        return issues
    sections = extract_page_slices(clean_pages_text)
    for page in state.get("pages", []):
        page_id = page.get("page_id", "")
        match = re.search(r"(\d+)", page_id)
        if not match:
            continue
        section = sections.get(int(match.group(1)), "")
        if not section:
            continue
        role = page.get("role", "")
        role_warn, role_fail = ROLE_DENSITY_THRESHOLDS.get(role, (warn_chars, fail_chars))
        char_count = len(re.sub(r"\s+", "", section))
        if char_count > role_fail:
            issues.setdefault(page_id, []).append(f"text_overflow:{char_count}")
            if role.startswith("hero_"):
                issues.setdefault(page_id, []).append(f"hero_page_density:{char_count}")
        elif char_count > role_warn:
            issues.setdefault(page_id, []).append(f"text_dense:{char_count}")
    return issues


def detect_missing_speaker_notes(state: dict, clean_pages_text: str | None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    if not clean_pages_text:
        return issues
    notes = extract_speaker_notes(clean_pages_text)
    for page in state.get("pages", []):
        role = page.get("role", "")
        if not role.startswith("hero_"):
            continue
        page_id = page.get("page_id", "")
        match = re.search(r"(\d+)", page_id)
        if not match:
            continue
        page_no = int(match.group(1))
        if page_no not in notes:
            issues.setdefault(page_id, []).append("speaker_notes_missing")
    return issues


def merge_review_findings(findings: dict | list | None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    if not findings:
        return issues
    if isinstance(findings, dict):
        for page_id, value in findings.items():
            if isinstance(value, list):
                issues[page_id] = [str(v) for v in value]
            else:
                issues[page_id] = [str(value)]
    elif isinstance(findings, list):
        for item in findings:
            if isinstance(item, dict) and item.get("page_id") and item.get("reason"):
                severity = str(item.get("severity", "")).strip()
                issue_type = str(item.get("type", "")).strip()
                label = ":".join(part for part in [severity, issue_type, str(item["reason"])] if part)
                issues.setdefault(str(item["page_id"]), []).append(label)
    return issues


def validate_review_findings(findings: dict | list | None) -> None:
    if findings is None:
        return
    if isinstance(findings, dict):
        # backward compatible mode
        return
    if not isinstance(findings, list):
        raise SystemExit("[ERROR] review_findings must be a list or legacy dict.")
    for idx, item in enumerate(findings):
        if not isinstance(item, dict):
            raise SystemExit(f"[ERROR] review finding #{idx} must be an object.")
        for field in REQUIRED_REVIEW_FIELDS:
            if field not in item:
                raise SystemExit(f"[ERROR] review finding #{idx} missing field: {field}")
        if item["severity"] not in ALLOWED_REVIEW_SEVERITY:
            raise SystemExit(f"[ERROR] review finding #{idx} invalid severity: {item['severity']}")
        if not str(item["page_id"]).startswith("slide_"):
            raise SystemExit(f"[ERROR] review finding #{idx} invalid page_id: {item['page_id']}")


def is_scorecard_scaffold(scorecard: dict) -> bool:
    """Return True if the scorecard is an unfilled scaffold (all scores are null)."""
    overall = scorecard.get("overall_score")
    if overall is None:
        return True
    dimensions = scorecard.get("dimensions")
    if isinstance(dimensions, dict) and all(v is None for v in dimensions.values()):
        return True
    return False


def validate_commercial_scorecard(scorecard: dict | None) -> None:
    if scorecard is None:
        return
    if not isinstance(scorecard, dict):
        raise SystemExit("[ERROR] commercial_scorecard must be an object.")
    if is_scorecard_scaffold(scorecard):
        return
    for field in REQUIRED_SCORECARD_FIELDS:
        if field not in scorecard:
            raise SystemExit(f"[ERROR] commercial_scorecard missing field: {field}")
    dimensions = scorecard.get("dimensions")
    if not isinstance(dimensions, dict):
        raise SystemExit("[ERROR] commercial_scorecard.dimensions must be an object.")
    for key in REQUIRED_SCORECARD_DIMENSIONS:
        value = dimensions.get(key)
        if value is None:
            continue
        if not isinstance(value, (int, float)):
            raise SystemExit(f"[ERROR] commercial_scorecard dimension `{key}` must be numeric.")
        if value < 1 or value > 5:
            raise SystemExit(f"[ERROR] commercial_scorecard dimension `{key}` must be within 1-5.")
    overall = scorecard.get("overall_score")
    if overall is not None and (not isinstance(overall, (int, float)) or overall < 1 or overall > 5):
        raise SystemExit("[ERROR] commercial_scorecard.overall_score must be within 1-5.")


def merge_issue_maps(*maps: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for issue_map in maps:
        for page_id, reasons in issue_map.items():
            merged.setdefault(page_id, []).extend(reasons)
    for page_id in list(merged.keys()):
        merged[page_id] = sorted(set(merged[page_id]))
    return merged


def apply_qa_to_state(state: dict, issues: dict[str, list[str]]) -> dict:
    page_lookup = {page.get("page_id"): page for page in state.get("pages", [])}
    for page_id, page in page_lookup.items():
        reasons = issues.get(page_id, [])
        if reasons:
            page["qa_status"] = "failed"
            page["qa_reason"] = "; ".join(reasons)
            if page.get("status") == "ready":
                page["status"] = "qa_failed"
        else:
            if page.get("qa_status") in {"pending", "failed"}:
                page["qa_status"] = "passed"
            page["qa_reason"] = ""
    state["global_status"] = "qa_failed" if issues else state.get("global_status", "ready")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Build montage from page images and write a simple review report.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--montage", required=True)
    parser.add_argument("--clean-pages")
    parser.add_argument("--layout-manifest")
    parser.add_argument("--theme-tokens")
    parser.add_argument("--review-findings")
    parser.add_argument("--commercial-scorecard")
    parser.add_argument("--warn-chars", type=int, default=700)
    parser.add_argument("--fail-chars", type=int, default=1000)
    parser.add_argument("--require-review", action="store_true")
    parser.add_argument("--require-commercial-scorecard", action="store_true")
    parser.add_argument("--min-commercial-score", type=float, default=3.3)
    parser.add_argument("--require-layout-manifest", action="store_true")
    parser.add_argument("--write-state", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    state_path = Path(args.state).expanduser().resolve()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    images = sorted(project_dir.glob("slide_*.png"))
    montage_ok = maybe_build_montage(images, Path(args.montage).expanduser().resolve())
    clean_pages_text = Path(args.clean_pages).read_text(encoding="utf-8") if args.clean_pages and Path(args.clean_pages).exists() else None
    layout_manifest_path = (
        Path(args.layout_manifest).expanduser().resolve()
        if args.layout_manifest
        else (project_dir / "layout_manifest.json")
    )
    layout_manifest = load_json(layout_manifest_path) if layout_manifest_path.exists() else None
    theme = load_json(Path(args.theme_tokens).expanduser().resolve()) if args.theme_tokens else None
    review_findings = load_json(Path(args.review_findings).expanduser().resolve()) if args.review_findings else None
    commercial_scorecard = load_json(Path(args.commercial_scorecard).expanduser().resolve()) if args.commercial_scorecard else None
    if args.require_review and review_findings is None:
        raise SystemExit("[ERROR] require-review is enabled but no review findings were provided.")
    if args.require_commercial_scorecard and commercial_scorecard is None:
        raise SystemExit("[ERROR] require-commercial-scorecard is enabled but no commercial scorecard was provided.")
    validate_review_findings(review_findings)
    validate_commercial_scorecard(commercial_scorecard if isinstance(commercial_scorecard, dict) else None)
    layout_issues, layout_meta = detect_layout_stability_issues(
        state,
        layout_manifest if isinstance(layout_manifest, dict) else None,
        args.require_layout_manifest,
    )

    commercial_issues: dict[str, list[str]] = {}
    if isinstance(commercial_scorecard, dict) and not is_scorecard_scaffold(commercial_scorecard):
        weak_dimensions = [
            key for key, value in commercial_scorecard.get("dimensions", {}).items()
            if isinstance(value, (int, float)) and value < 3
        ]
        if weak_dimensions:
            commercial_issues.setdefault("__commercial__", []).append(
                "commercial_score_low:" + ",".join(sorted(weak_dimensions))
            )
        overall = commercial_scorecard.get("overall_score")
        if isinstance(overall, (int, float)) and overall < args.min_commercial_score:
            commercial_issues.setdefault("__commercial__", []).append(f"commercial_score_overall:{overall:.2f}")

    issues = merge_issue_maps(
        detect_component_drift(state, theme if isinstance(theme, dict) else None),
        detect_density_issues(state, clean_pages_text, args.warn_chars, args.fail_chars),
        detect_missing_speaker_notes(state, clean_pages_text),
        layout_issues,
        merge_review_findings(review_findings),
        commercial_issues,
    )
    state = apply_qa_to_state(state, issues)

    if args.write_state:
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Deck Review Report",
        "",
        f"- 项目状态：`{state.get('global_status', 'unknown')}`",
        f"- 输出模式：`{state.get('output_mode', 'unknown')}`",
        f"- 视觉已锁定：`{state.get('visual_locked', False)}`",
        f"- 页数：`{len(state.get('pages', []))}`",
        f"- 多模态评审：`{'强制' if args.require_review else '非强制'}`",
        f"- 评审 findings：`{'已提供' if review_findings is not None else '未提供'}`",
        f"- 商业评分卡：`{'已提供' if commercial_scorecard is not None else '未提供'}`",
        f"- 几何 manifest：`{'已提供' if layout_meta.get('layout_manifest_present') else '未提供'}`",
        f"- 几何强校验：`{'强制' if args.require_layout_manifest else '非强制'}`",
        f"- 几何覆盖页数：`{layout_meta.get('covered_pages', 0)}` / `{layout_meta.get('checked_pages', 0)}`",
        f"- 缩略总览：`{'已生成' if montage_ok else '未生成（缺少 PNG 页面或 Pillow）'}`",
        f"- 自动问题页数：`{len(issues)}`",
        "",
    ]
    if isinstance(commercial_scorecard, dict):
        report_lines.extend(
            [
                "## 商业说服力评分",
                "",
                f"- 总分：`{commercial_scorecard.get('overall_score')}` / `5`",
                f"- 建议动作：{commercial_scorecard.get('recommended_action', '')}",
                f"- 摘要：{commercial_scorecard.get('summary', '')}",
                "",
            ]
        )

    report_lines.extend([
        "## 页级状态",
        "",
    ])
    for page in state.get("pages", []):
        report_lines.append(
            f"- `{page.get('page_id')}` | status=`{page.get('status')}` | qa=`{page.get('qa_status')}` | reason=`{page.get('qa_reason', '')}`"
        )

    if issues:
        report_lines.extend(["", "## 自动检测发现", ""])
        for page_id, reasons in issues.items():
            report_lines.append(f"- `{page_id}`: {', '.join(reasons)}")

    report = Path(args.report).expanduser().resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote report: {report}")
    if montage_ok:
        print(f"[OK] wrote montage: {Path(args.montage).expanduser().resolve()}")


if __name__ == "__main__":
    main()
