#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from init_deck_project import init_project
from init_slide_state import build_state


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PRESET_CHOICES = ["solution_deck", "product_intro", "internal_strategy", "industry_pov", "business_partnership"]


def run_script(script_name: str, *args: str) -> None:
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path), *args]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"[ERROR] {script_name} failed with exit code {exc.returncode}")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_batch_page_ids(project_dir: Path, batch_id: str) -> list[str]:
    jobs_path = project_dir / "image_build_jobs.json"
    jobs_payload = load_json(jobs_path)
    for batch in jobs_payload.get("batches", []):
        if batch.get("batch_id") == batch_id:
            page_ids = [str(page_id) for page_id in batch.get("page_ids", []) if str(page_id)]
            if page_ids:
                return page_ids
            raise SystemExit(f"[ERROR] batch `{batch_id}` exists but has no page_ids.")
    raise SystemExit(f"[ERROR] batch `{batch_id}` not found in {jobs_path}.")


def find_latest_pptx(project_dir: Path) -> Path | None:
    candidates = [project_dir]
    for child in sorted(project_dir.iterdir()) if project_dir.exists() else []:
        if child.is_dir() and (
            child.name.startswith("build_")
            or child.name.startswith("dist")
            or child.name.startswith("output")
            or child.name.endswith("_build")
        ):
            candidates.append(child)
    matches: list[Path] = []
    for base in candidates:
        for pattern in ("deck*.pptx", "*deck*.pptx", "*.pptx"):
            matches.extend(
                path for path in base.glob(pattern)
                if path.is_file() and not path.name.startswith(".") and not path.name.startswith(".~") and not path.name.startswith("~$")
            )
    if not matches:
        return None
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def cmd_init(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    created = init_project(project_dir, with_example=args.with_example)
    state_path = project_dir / "slide_state.json"
    if not state_path.exists() or args.force_state:
        state = build_state(args.project_id or project_dir.name, args.pages, args.output_mode)
        state_path.write_text(__import__("json").dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append("slide_state.json")

    if args.preset:
        preset_path = SKILL_ROOT / "assets" / "presets" / f"{args.preset}.json"
        if not preset_path.exists():
            raise SystemExit(f"[ERROR] preset not found: {preset_path}")
        run_script("apply_deck_preset.py", "--project-dir", str(project_dir), "--preset-file", str(preset_path))
    run_script("generate_layout_manifest.py", "--project-dir", str(project_dir), "--merge-existing")

    print(f"[OK] initialized pipeline project: {project_dir}")
    if created:
        print("[OK] ensured files:")
        for item in created:
            print(f"  - {item}")
    if args.preset:
        print(f"[OK] applied preset shortcut: {args.preset}")


def cmd_build_context(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else project_dir / "build_context.json"
    cmd = [
        "--role", "build",
        "--clean-pages", str(project_dir / "deck_clean_pages.md"),
        "--visual-composition", str(project_dir / "deck_visual_composition.md"),
        "--visual-system", str(project_dir / "deck_visual_system.md"),
        "--component-tokens", str(project_dir / "deck_component_tokens.md"),
        "--theme-tokens", str(project_dir / "deck_theme_tokens.json"),
        "--slide-state", str(project_dir / "slide_state.json"),
        "--output", str(output),
    ]
    if args.allow_full_fallback:
        cmd.append("--allow-full-fallback")
    if args.page_ids:
        cmd.extend(["--page-ids", *args.page_ids])
    run_script("context_manager.py", *cmd)


def cmd_stage(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--state", str(project_dir / "slide_state.json")]
    if args.global_status:
        cmd.extend(["--global-status", args.global_status])
    if args.visual_locked is not None:
        cmd.extend(["--visual-locked", "true" if args.visual_locked else "false"])
    if args.page_id:
        cmd.extend(["--page-id", args.page_id])
    if args.role:
        cmd.extend(["--role", args.role])
    if args.status:
        cmd.extend(["--status", args.status])
    if args.qa_status:
        cmd.extend(["--qa-status", args.qa_status])
    if args.qa_reason is not None:
        cmd.extend(["--qa-reason", args.qa_reason])
    if args.content_hash is not None:
        cmd.extend(["--content-hash", args.content_hash])
    for component in args.add_component or []:
        cmd.extend(["--add-component", component])
    run_script("update_slide_state.py", *cmd)


def cmd_qa(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    report = Path(args.report).expanduser().resolve() if args.report else project_dir / "deck_review_report.md"
    montage = Path(args.montage).expanduser().resolve() if args.montage else project_dir / "montage.png"
    theme = Path(args.theme_tokens).expanduser().resolve() if args.theme_tokens else SKILL_ROOT / "assets" / "theme_tokens" / "default_dark_glass.json"
    layout_manifest = Path(args.layout_manifest).expanduser().resolve() if args.layout_manifest else project_dir / "layout_manifest.json"
    commercial_scorecard = Path(args.commercial_scorecard).expanduser().resolve() if args.commercial_scorecard else project_dir / "commercial_scorecard.json"
    deck_path = Path(args.deck_path).expanduser().resolve() if args.deck_path else find_latest_pptx(project_dir)
    if args.require_review and not args.review_findings:
        raise SystemExit("[ERROR] `qa --require-review` 需要提供 `--review-findings`。")
    if args.require_commercial_scorecard and not commercial_scorecard.exists():
        raise SystemExit("[ERROR] `qa --require-commercial-scorecard` 需要提供 `commercial_scorecard.json`。")
    if args.extract_layout_from_pptx:
        if not deck_path or not deck_path.exists():
            raise SystemExit("[ERROR] `qa --extract-layout-from-pptx` 需要可用的 `.pptx` 产物。")
        run_script(
            "extract_layout_from_pptx.py",
            "--project-dir", str(project_dir),
            "--deck-path", str(deck_path),
            "--manifest", str(layout_manifest),
        )
    cmd = [
        "--project-dir", str(project_dir),
        "--state", str(project_dir / "slide_state.json"),
        "--clean-pages", str(project_dir / "deck_clean_pages.md"),
        "--layout-manifest", str(layout_manifest),
        "--theme-tokens", str(theme),
        "--report", str(report),
        "--montage", str(montage),
        "--warn-chars", str(args.warn_chars),
        "--fail-chars", str(args.fail_chars),
    ]
    if args.review_findings:
        cmd.extend(["--review-findings", str(Path(args.review_findings).expanduser().resolve())])
    if commercial_scorecard.exists():
        cmd.extend(["--commercial-scorecard", str(commercial_scorecard)])
    if args.require_review:
        cmd.append("--require-review")
    if args.require_commercial_scorecard:
        cmd.append("--require-commercial-scorecard")
    if args.min_commercial_score is not None:
        cmd.extend(["--min-commercial-score", str(args.min_commercial_score)])
    if args.require_layout_manifest:
        cmd.append("--require-layout-manifest")
    if args.write_state:
        cmd.append("--write-state")
    # Expert-mode artifacts are auto-discovered from project_dir by build_montage_and_report.py
    run_script("build_montage_and_report.py", *cmd)
    if args.review_findings and not args.skip_route_review:
        rollback_plan = Path(args.rollback_plan).expanduser().resolve() if args.rollback_plan else project_dir / "review_rollback_plan.json"
        rollback_plan_md = Path(args.rollback_plan_md).expanduser().resolve() if args.rollback_plan_md else project_dir / "review_rollback_plan.md"
        route_cmd = [
            "--project-dir", str(project_dir),
            "--review-findings", str(Path(args.review_findings).expanduser().resolve()),
            "--state", str(project_dir / "slide_state.json"),
            "--output-json", str(rollback_plan),
            "--output-md", str(rollback_plan_md),
        ]
        if commercial_scorecard.exists():
            route_cmd.extend(["--commercial-scorecard", str(commercial_scorecard)])
        if args.write_state:
            route_cmd.append("--write-state")
        run_script("route_review_findings.py", *route_cmd)


def cmd_validate(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--output-mode", args.output_mode]
    if args.require_review or getattr(args, "formal", False):
        cmd.append("--require-review")
    if getattr(args, "expert_mode", False):
        cmd.append("--expert-mode")
    run_script("validate_deck_outputs.py", *cmd)


def cmd_preset(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    preset_path = SKILL_ROOT / "assets" / "presets" / f"{args.preset}.json"
    if not preset_path.exists():
        raise SystemExit(f"[ERROR] preset not found: {preset_path}")
    run_script("apply_deck_preset.py", "--project-dir", str(project_dir), "--preset-file", str(preset_path))
    run_script("generate_layout_manifest.py", "--project-dir", str(project_dir), "--merge-existing")


def cmd_handoff(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    resolved_page_ids = list(args.page_ids or [])
    if args.role == "build" and args.batch_id and not resolved_page_ids:
        resolved_page_ids = resolve_batch_page_ids(project_dir, args.batch_id)

    if args.output:
        output = Path(args.output).expanduser().resolve()
    elif args.role == "build" and args.batch_id:
        output = project_dir / f"build_{args.batch_id}_handoff.md"
    else:
        output = project_dir / f"{args.role}_handoff.md"
    cmd = ["--project-dir", str(project_dir), "--role", args.role, "--output", str(output)]
    if resolved_page_ids:
        cmd.extend(["--page-ids", *resolved_page_ids])
    if args.batch_id:
        cmd.extend(["--batch-id", args.batch_id])
    if args.role == "build" and resolved_page_ids:
        if args.batch_id:
            ctx_output = project_dir / "contexts" / f"{args.batch_id}.json"
        elif len(resolved_page_ids) == 1:
            ctx_output = project_dir / "contexts" / f"{resolved_page_ids[0]}.json"
        else:
            ctx_output = project_dir / "build_context.json"
        build_cmd = [
            "build-context",
            "--project-dir", str(project_dir),
            "--output", str(ctx_output),
            "--page-ids", *resolved_page_ids,
        ]
        main_parser = build_parser()
        parsed = main_parser.parse_args(build_cmd)
        if getattr(parsed, "visual_unlocked", False):
            parsed.visual_locked = False
        elif getattr(parsed, "visual_locked", False):
            parsed.visual_locked = True
        else:
            parsed.visual_locked = None
        parsed.func(parsed)
        cmd.extend(["--context-path", str(ctx_output)])
    if args.role == "review":
        review_package = project_dir / "review_package.json"
        run_script("generate_review_package.py", "--project-dir", str(project_dir), "--output", str(review_package))
        cmd.extend(["--context-path", str(review_package)])
    run_script("generate_role_prompt.py", *cmd)


def cmd_review_package(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.rendered_dir:
        cmd.extend(["--rendered-dir", str(Path(args.rendered_dir).expanduser().resolve())])
    if args.montage:
        cmd.extend(["--montage", str(Path(args.montage).expanduser().resolve())])
    if args.deck_path:
        cmd.extend(["--deck-path", str(Path(args.deck_path).expanduser().resolve())])
    run_script("generate_review_package.py", *cmd)


def cmd_manifest(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.skeletons:
        cmd.extend(["--skeletons", str(Path(args.skeletons).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.merge_existing:
        cmd.append("--merge-existing")
    run_script("generate_layout_manifest.py", *cmd)


def cmd_extract_layout(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    deck_path = Path(args.deck_path).expanduser().resolve() if args.deck_path else find_latest_pptx(project_dir)
    if not deck_path or not deck_path.exists():
        raise SystemExit("[ERROR] 没有找到可用的 `.pptx` 产物，请用 `--deck-path` 指定。")
    cmd = [
        "--project-dir", str(project_dir),
        "--deck-path", str(deck_path),
    ]
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    run_script("extract_layout_from_pptx.py", *cmd)


def cmd_layout_update(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.json_file:
        cmd.extend(["--json-file", str(Path(args.json_file).expanduser().resolve())])
    if args.page_id:
        cmd.extend(["--page-id", args.page_id])
    if args.archetype:
        cmd.extend(["--archetype", args.archetype])
    if args.role:
        cmd.extend(["--role", args.role])
    for arg_name, cli_name in (
        ("center_x", "--center-x"),
        ("expected_center_x", "--expected-center-x"),
        ("tolerance", "--tolerance"),
        ("occupancy_ratio", "--occupancy-ratio"),
        ("occupancy_min", "--occupancy-min"),
        ("occupancy_max", "--occupancy-max"),
    ):
        value = getattr(args, arg_name)
        if value is not None:
            cmd.extend([cli_name, str(value)])
    run_script("update_layout_manifest.py", *cmd)


def cmd_route_review(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    review_findings = Path(args.review_findings).expanduser().resolve() if args.review_findings else project_dir / "deck_review_findings.json"
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else project_dir / "review_rollback_plan.json"
    output_md = Path(args.output_md).expanduser().resolve() if args.output_md else project_dir / "review_rollback_plan.md"
    cmd = [
        "--project-dir", str(project_dir),
        "--review-findings", str(review_findings),
        "--state", str(project_dir / "slide_state.json"),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
    ]
    if args.map_file:
        cmd.extend(["--map-file", str(Path(args.map_file).expanduser().resolve())])
    if args.write_state:
        cmd.append("--write-state")
    run_script("route_review_findings.py", *cmd)


def cmd_rework_handoff(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    rollback_plan = Path(args.rollback_plan).expanduser().resolve() if args.rollback_plan else project_dir / "review_rollback_plan.json"
    if not rollback_plan.exists():
        raise SystemExit(f"[ERROR] rollback plan not found: {rollback_plan}")

    selected_page_ids = list(args.page_ids or [])
    context_path = None
    if args.role == "build":
        plan = json.loads(rollback_plan.read_text(encoding="utf-8"))
        if not selected_page_ids:
            selected_page_ids = [item.get("page_id") for item in plan.get("page_actions", []) if item.get("page_id")]
        if selected_page_ids:
            if len(selected_page_ids) == 1:
                context_path = project_dir / "contexts" / f"{selected_page_ids[0]}.json"
            else:
                context_path = project_dir / "build_context.json"
            build_cmd = [
                "build-context",
                "--project-dir", str(project_dir),
                "--output", str(context_path),
                "--page-ids", *selected_page_ids,
            ]
            main_parser = build_parser()
            parsed = main_parser.parse_args(build_cmd)
            if getattr(parsed, "visual_unlocked", False):
                parsed.visual_locked = False
            elif getattr(parsed, "visual_locked", False):
                parsed.visual_locked = True
            else:
                parsed.visual_locked = None
            parsed.func(parsed)

    output = Path(args.output).expanduser().resolve() if args.output else project_dir / f"{args.role}_rework_handoff.md"
    cmd = [
        "--project-dir", str(project_dir),
        "--role", args.role,
        "--rollback-plan", str(rollback_plan),
        "--output", str(output),
    ]
    if selected_page_ids:
        cmd.extend(["--page-ids", *selected_page_ids])
    if context_path:
        cmd.extend(["--context-path", str(context_path)])
    run_script("generate_rework_handoff.py", *cmd)


def cmd_visual_composition(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.clean_pages:
        cmd.extend(["--clean-pages", str(Path(args.clean_pages).expanduser().resolve())])
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    run_script("generate_visual_composition.py", *cmd)


def cmd_expert_interview(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.clean_pages:
        cmd.extend(["--clean-pages", str(Path(args.clean_pages).expanduser().resolve())])
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.brief:
        cmd.extend(["--brief", str(Path(args.brief).expanduser().resolve())])
    if getattr(args, "output_md", None):
        cmd.extend(["--output-md", str(Path(args.output_md).expanduser().resolve())])
    if getattr(args, "output_json", None):
        cmd.extend(["--output-json", str(Path(args.output_json).expanduser().resolve())])
    run_script("generate_interview_questions.py", *cmd)


def cmd_finalize_interview(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.session:
        cmd.extend(["--session", str(Path(args.session).expanduser().resolve())])
    if args.preparation:
        cmd.extend(["--preparation", str(Path(args.preparation).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.force:
        cmd.append("--force")
    run_script("finalize_interview.py", *cmd)


def cmd_asset_plan(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.clean_pages:
        cmd.extend(["--clean-pages", str(Path(args.clean_pages).expanduser().resolve())])
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    run_script("generate_asset_plan.py", *cmd)


def cmd_style_lock(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.vibe:
        cmd.extend(["--vibe", str(Path(args.vibe).expanduser().resolve())])
    if args.theme_tokens:
        cmd.extend(["--theme-tokens", str(Path(args.theme_tokens).expanduser().resolve())])
    if args.visual_system:
        cmd.extend(["--visual-system", str(Path(args.visual_system).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    run_script("generate_style_lock.py", *cmd)


def cmd_generate_assets(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--batch-size", str(args.batch_size)]
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.state:
        cmd.extend(["--state", str(Path(args.state).expanduser().resolve())])
    if args.clean_pages:
        cmd.extend(["--clean-pages", str(Path(args.clean_pages).expanduser().resolve())])
    if args.visual_composition:
        cmd.extend(["--visual-composition", str(Path(args.visual_composition).expanduser().resolve())])
    if args.style_lock:
        cmd.extend(["--style-lock", str(Path(args.style_lock).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    run_script("generate_visual_assets.py", *cmd)


def cmd_dispatch_build(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--batch-id", args.batch_id]
    if args.output_json:
        cmd.extend(["--output-json", str(Path(args.output_json).expanduser().resolve())])
    if args.output_md:
        cmd.extend(["--output-md", str(Path(args.output_md).expanduser().resolve())])
    run_script("generate_build_dispatch.py", *cmd)


def cmd_asset_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--asset-id", args.asset_id, "--status", args.status]
    if args.final_path is not None:
        cmd.extend(["--final-path", args.final_path])
    if args.selected_variant is not None:
        cmd.extend(["--selected-variant", args.selected_variant])
    if args.clear_stale:
        cmd.append("--clear-stale")
    run_script("update_asset_runtime.py", *cmd)


def cmd_prepare_assemble(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--batch-id", args.batch_id]
    if args.output_json:
        cmd.extend(["--output-json", str(Path(args.output_json).expanduser().resolve())])
    if args.output_md:
        cmd.extend(["--output-md", str(Path(args.output_md).expanduser().resolve())])
    run_script("prepare_html_assemble.py", *cmd)


def cmd_finalize_assemble(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--batch-id", args.batch_id]
    if args.html_path:
        cmd.extend(["--html-path", str(Path(args.html_path).expanduser().resolve())])
    run_script("finalize_html_assemble.py", *cmd)


def cmd_assemble_html(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--batch-id", args.batch_id]
    if args.context:
        cmd.extend(["--context", str(Path(args.context).expanduser().resolve())])
    run_script("assemble_html_batch.py", *cmd)


def cmd_screenshot_pages(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir), "--viewport", args.viewport]
    if args.html_path:
        cmd.extend(["--html-path", str(Path(args.html_path).expanduser().resolve())])
    if args.output_dir:
        cmd.extend(["--output-dir", str(Path(args.output_dir).expanduser().resolve())])
    run_script("screenshot_pages.py", *cmd)


def cmd_post_assemble_qa(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    assemble_manifest_path = project_dir / "assemble" / args.batch_id / "assemble_manifest.json"
    assemble_manifest = load_json(assemble_manifest_path)
    if not assemble_manifest:
        raise SystemExit(f"[ERROR] assemble manifest not found: {assemble_manifest_path}")

    html_path = Path(args.html_path).expanduser().resolve() if args.html_path else Path(assemble_manifest.get("output_html", ""))
    if not html_path:
        raise SystemExit(f"[ERROR] html output not found in assemble manifest: {assemble_manifest_path}")
    rendered_dir = Path(args.rendered_dir).expanduser().resolve() if args.rendered_dir else project_dir / "rendered"
    review_package = Path(args.review_package).expanduser().resolve() if args.review_package else project_dir / "review_package.json"
    report = Path(args.report).expanduser().resolve() if args.report else project_dir / "deck_review_report.md"
    montage = Path(args.montage).expanduser().resolve() if args.montage else project_dir / "montage.png"
    theme = Path(args.theme_tokens).expanduser().resolve() if args.theme_tokens else SKILL_ROOT / "assets" / "theme_tokens" / "default_dark_glass.json"
    layout_manifest = Path(args.layout_manifest).expanduser().resolve() if args.layout_manifest else project_dir / "layout_manifest.json"

    run_script("finalize_html_assemble.py", "--project-dir", str(project_dir), "--batch-id", args.batch_id, "--html-path", str(html_path))
    run_script(
        "screenshot_pages.py",
        "--project-dir", str(project_dir),
        "--html-path", str(html_path),
        "--output-dir", str(rendered_dir),
        "--viewport", args.viewport,
    )
    run_script(
        "generate_review_package.py",
        "--project-dir", str(project_dir),
        "--output", str(review_package),
        "--rendered-dir", str(rendered_dir),
        "--deck-path", str(html_path),
    )
    qa_cmd = [
        "--project-dir", str(project_dir),
        "--state", str(project_dir / "slide_state.json"),
        "--clean-pages", str(project_dir / "deck_clean_pages.md"),
        "--layout-manifest", str(layout_manifest),
        "--theme-tokens", str(theme),
        "--report", str(report),
        "--montage", str(montage),
        "--warn-chars", str(args.warn_chars),
        "--fail-chars", str(args.fail_chars),
        "--write-state",
    ]
    run_script("build_montage_and_report.py", *qa_cmd)


def cmd_capture_assets(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.cookies:
        cmd.extend(["--cookies", str(Path(args.cookies).expanduser().resolve())])
    cmd.extend(["--viewport", args.viewport])
    if args.only_ids:
        cmd.extend(["--only-ids", *args.only_ids])
    run_script("capture_assets.py", *cmd)


def cmd_apply_mockups(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.spec:
        cmd.extend(["--spec", str(Path(args.spec).expanduser().resolve())])
    run_script("apply_mockup.py", *cmd)


def cmd_validate_schema(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.strict:
        cmd.append("--strict")
    run_script("validate_schema.py", *cmd)


def cmd_generate_placeholders(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    cmd = ["--project-dir", str(project_dir)]
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.theme_tokens:
        cmd.extend(["--theme-tokens", str(Path(args.theme_tokens).expanduser().resolve())])
    run_script("generate_placeholders.py", *cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deck production pipeline stages with one orchestration script.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a deck project and slide state")
    p_init.add_argument("--project-dir", required=True)
    p_init.add_argument("--pages", type=int, required=True)
    p_init.add_argument("--project-id")
    p_init.add_argument("--output-mode", default="pptx+html", choices=["pptx", "html", "pptx+html"])
    p_init.add_argument("--with-example", action="store_true")
    p_init.add_argument("--preset", choices=PRESET_CHOICES)
    p_init.add_argument("--force-state", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_ctx = sub.add_parser("build-context", help="Generate a minimal build context bundle")
    p_ctx.add_argument("--project-dir", required=True)
    p_ctx.add_argument("--page-ids", nargs="*", default=[])
    p_ctx.add_argument("--output")
    p_ctx.add_argument("--allow-full-fallback", action="store_true")
    p_ctx.set_defaults(func=cmd_build_context)

    p_stage = sub.add_parser("stage", help="Update global or page-level stage state")
    p_stage.add_argument("--project-dir", required=True)
    p_stage.add_argument("--global-status")
    p_stage.add_argument("--visual-locked", action="store_true")
    p_stage.add_argument("--visual-unlocked", action="store_true")
    p_stage.add_argument("--page-id")
    p_stage.add_argument("--role")
    p_stage.add_argument("--status")
    p_stage.add_argument("--qa-status")
    p_stage.add_argument("--qa-reason")
    p_stage.add_argument("--content-hash")
    p_stage.add_argument("--add-component", action="append")
    p_stage.set_defaults(func=cmd_stage)

    p_qa = sub.add_parser("qa", help="Run QA aggregation and write report")
    p_qa.add_argument("--project-dir", required=True)
    p_qa.add_argument("--theme-tokens")
    p_qa.add_argument("--review-findings")
    p_qa.add_argument("--commercial-scorecard")
    p_qa.add_argument("--layout-manifest")
    p_qa.add_argument("--deck-path")
    p_qa.add_argument("--report")
    p_qa.add_argument("--montage")
    p_qa.add_argument("--warn-chars", type=int, default=700)
    p_qa.add_argument("--fail-chars", type=int, default=1000)
    p_qa.add_argument("--require-review", action="store_true")
    p_qa.add_argument("--require-commercial-scorecard", action="store_true")
    p_qa.add_argument("--min-commercial-score", type=float, default=3.3)
    p_qa.add_argument("--require-layout-manifest", action="store_true")
    p_qa.add_argument("--extract-layout-from-pptx", action="store_true")
    p_qa.add_argument("--skip-route-review", action="store_true")
    p_qa.add_argument("--rollback-plan")
    p_qa.add_argument("--rollback-plan-md")
    p_qa.add_argument("--write-state", action="store_true")
    p_qa.set_defaults(func=cmd_qa)

    p_validate = sub.add_parser("validate", help="Validate output completeness")
    p_validate.add_argument("--project-dir", required=True)
    p_validate.add_argument("--output-mode", default="pptx+html", choices=["pptx", "html", "pptx+html"])
    p_validate.add_argument("--require-review", action="store_true", help="Also check review/QA artifacts including montage and review_package")
    p_validate.add_argument("--formal", action="store_true", help="Alias for --require-review: full formal review validation")
    p_validate.add_argument("--expert-mode", action="store_true", help="Also check expert interview artifacts")
    p_validate.set_defaults(func=cmd_validate)

    p_preset = sub.add_parser("preset", help="Apply a common deck preset")
    p_preset.add_argument("--project-dir", required=True)
    p_preset.add_argument("--preset", required=True, choices=PRESET_CHOICES)
    p_preset.set_defaults(func=cmd_preset)

    p_expert = sub.add_parser("expert-interview", help="Prepare claims + gaps analysis for Expert Interview")
    p_expert.add_argument("--project-dir", required=True)
    p_expert.add_argument("--clean-pages")
    p_expert.add_argument("--state")
    p_expert.add_argument("--brief")
    p_expert.add_argument("--output-md")
    p_expert.add_argument("--output-json")
    p_expert.set_defaults(func=cmd_expert_interview)

    p_finalize = sub.add_parser("finalize-interview", help="Finalize Expert Interview: validate redaction and produce deck_expert_context.md")
    p_finalize.add_argument("--project-dir", required=True)
    p_finalize.add_argument("--session", help="Path to interview_session.json")
    p_finalize.add_argument("--preparation", help="Path to interview_preparation.json")
    p_finalize.add_argument("--output", help="Path to deck_expert_context.md")
    p_finalize.add_argument("--force", action="store_true", help="Proceed even if validation fails")
    p_finalize.set_defaults(func=cmd_finalize_interview)

    p_handoff = sub.add_parser("handoff", help="Generate a ready-to-send AI worker handoff prompt")
    p_handoff.add_argument("--project-dir", required=True)
    p_handoff.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    p_handoff.add_argument("--page-ids", nargs="*", default=[])
    p_handoff.add_argument("--batch-id")
    p_handoff.add_argument("--output")
    p_handoff.set_defaults(func=cmd_handoff)

    p_review_pkg = sub.add_parser("review-package", help="Generate a multimodal review package manifest")
    p_review_pkg.add_argument("--project-dir", required=True)
    p_review_pkg.add_argument("--output")
    p_review_pkg.add_argument("--rendered-dir")
    p_review_pkg.add_argument("--montage")
    p_review_pkg.add_argument("--deck-path")
    p_review_pkg.set_defaults(func=cmd_review_package)

    p_manifest = sub.add_parser("manifest", help="Generate or refresh layout_manifest.json from state and page skeletons")
    p_manifest.add_argument("--project-dir", required=True)
    p_manifest.add_argument("--state")
    p_manifest.add_argument("--skeletons")
    p_manifest.add_argument("--output")
    p_manifest.add_argument("--merge-existing", action="store_true")
    p_manifest.set_defaults(func=cmd_manifest)

    p_extract = sub.add_parser("extract-layout", help="Extract real page geometry from built PPTX into layout_manifest.json")
    p_extract.add_argument("--project-dir", required=True)
    p_extract.add_argument("--deck-path")
    p_extract.add_argument("--state")
    p_extract.add_argument("--manifest")
    p_extract.set_defaults(func=cmd_extract_layout)

    p_layout_update = sub.add_parser("layout-update", help="Upsert real page geometry into layout_manifest.json")
    p_layout_update.add_argument("--project-dir", required=True)
    p_layout_update.add_argument("--manifest")
    p_layout_update.add_argument("--json-file")
    p_layout_update.add_argument("--page-id")
    p_layout_update.add_argument("--archetype")
    p_layout_update.add_argument("--role")
    p_layout_update.add_argument("--center-x", type=float)
    p_layout_update.add_argument("--expected-center-x", type=float)
    p_layout_update.add_argument("--tolerance", type=float)
    p_layout_update.add_argument("--occupancy-ratio", type=float)
    p_layout_update.add_argument("--occupancy-min", type=float)
    p_layout_update.add_argument("--occupancy-max", type=float)
    p_layout_update.set_defaults(func=cmd_layout_update)

    p_route = sub.add_parser("route-review", help="Map structured review findings into rollback stages and target files")
    p_route.add_argument("--project-dir", required=True)
    p_route.add_argument("--review-findings")
    p_route.add_argument("--map-file")
    p_route.add_argument("--output-json")
    p_route.add_argument("--output-md")
    p_route.add_argument("--write-state", action="store_true")
    p_route.set_defaults(func=cmd_route_review)

    p_rework = sub.add_parser("rework-handoff", help="Generate a role-specific rework handoff from rollback plan")
    p_rework.add_argument("--project-dir", required=True)
    p_rework.add_argument("--role", required=True, choices=["brief", "visual", "build", "review"])
    p_rework.add_argument("--rollback-plan")
    p_rework.add_argument("--page-ids", nargs="*", default=[])
    p_rework.add_argument("--output")
    p_rework.set_defaults(func=cmd_rework_handoff)

    p_vc = sub.add_parser("visual-composition", help="Generate visual composition spec from clean pages")
    p_vc.add_argument("--project-dir", required=True)
    p_vc.add_argument("--clean-pages")
    p_vc.add_argument("--state")
    p_vc.add_argument("--output")
    p_vc.set_defaults(func=cmd_visual_composition)

    p_asset_plan = sub.add_parser("asset-plan", help="Generate asset plan from clean pages and slide state")
    p_asset_plan.add_argument("--project-dir", required=True)
    p_asset_plan.add_argument("--clean-pages")
    p_asset_plan.add_argument("--state")
    p_asset_plan.add_argument("--output")
    p_asset_plan.add_argument("--manifest")
    p_asset_plan.set_defaults(func=cmd_asset_plan)

    p_style_lock = sub.add_parser("style-lock", help="Generate a deck-level style lock for image-led build")
    p_style_lock.add_argument("--project-dir", required=True)
    p_style_lock.add_argument("--vibe")
    p_style_lock.add_argument("--theme-tokens")
    p_style_lock.add_argument("--visual-system")
    p_style_lock.add_argument("--output")
    p_style_lock.set_defaults(func=cmd_style_lock)

    p_generate_assets = sub.add_parser("generate-assets", help="Generate batched image build jobs for Codex/subagent execution")
    p_generate_assets.add_argument("--project-dir", required=True)
    p_generate_assets.add_argument("--manifest")
    p_generate_assets.add_argument("--state")
    p_generate_assets.add_argument("--clean-pages")
    p_generate_assets.add_argument("--visual-composition")
    p_generate_assets.add_argument("--style-lock")
    p_generate_assets.add_argument("--output")
    p_generate_assets.add_argument("--batch-size", type=int, default=3)
    p_generate_assets.set_defaults(func=cmd_generate_assets)

    p_dispatch_build = sub.add_parser("dispatch-build", help="Generate per-page subagent dispatch package for a build batch")
    p_dispatch_build.add_argument("--project-dir", required=True)
    p_dispatch_build.add_argument("--batch-id", required=True)
    p_dispatch_build.add_argument("--output-json")
    p_dispatch_build.add_argument("--output-md")
    p_dispatch_build.set_defaults(func=cmd_dispatch_build)

    p_asset_status = sub.add_parser("asset-status", help="Update asset/job/batch runtime status together")
    p_asset_status.add_argument("--project-dir", required=True)
    p_asset_status.add_argument("--asset-id", required=True)
    p_asset_status.add_argument("--status", required=True)
    p_asset_status.add_argument("--final-path")
    p_asset_status.add_argument("--selected-variant")
    p_asset_status.add_argument("--clear-stale", action="store_true")
    p_asset_status.set_defaults(func=cmd_asset_status)

    p_prepare_assemble = sub.add_parser("prepare-assemble", help="Prepare an approved batch for HTML assemble")
    p_prepare_assemble.add_argument("--project-dir", required=True)
    p_prepare_assemble.add_argument("--batch-id", required=True)
    p_prepare_assemble.add_argument("--output-json")
    p_prepare_assemble.add_argument("--output-md")
    p_prepare_assemble.set_defaults(func=cmd_prepare_assemble)

    p_finalize_assemble = sub.add_parser("finalize-assemble", help="Finalize an HTML assemble batch and mark it embedded")
    p_finalize_assemble.add_argument("--project-dir", required=True)
    p_finalize_assemble.add_argument("--batch-id", required=True)
    p_finalize_assemble.add_argument("--html-path")
    p_finalize_assemble.set_defaults(func=cmd_finalize_assemble)

    p_assemble_html = sub.add_parser("assemble-html", help="Assemble approved batch context into starter HTML")
    p_assemble_html.add_argument("--project-dir", required=True)
    p_assemble_html.add_argument("--batch-id", required=True)
    p_assemble_html.add_argument("--context")
    p_assemble_html.set_defaults(func=cmd_assemble_html)

    p_screenshot = sub.add_parser("screenshot-pages", help="Take per-slide screenshots from an HTML deck")
    p_screenshot.add_argument("--project-dir", required=True)
    p_screenshot.add_argument("--html-path")
    p_screenshot.add_argument("--output-dir")
    p_screenshot.add_argument("--viewport", default="1280x720")
    p_screenshot.set_defaults(func=cmd_screenshot_pages)

    p_post_assemble_qa = sub.add_parser("post-assemble-qa", help="Finalize a batch, screenshot it, refresh review package, and run QA")
    p_post_assemble_qa.add_argument("--project-dir", required=True)
    p_post_assemble_qa.add_argument("--batch-id", required=True)
    p_post_assemble_qa.add_argument("--html-path")
    p_post_assemble_qa.add_argument("--rendered-dir")
    p_post_assemble_qa.add_argument("--review-package")
    p_post_assemble_qa.add_argument("--report")
    p_post_assemble_qa.add_argument("--montage")
    p_post_assemble_qa.add_argument("--layout-manifest")
    p_post_assemble_qa.add_argument("--theme-tokens")
    p_post_assemble_qa.add_argument("--viewport", default="1280x720")
    p_post_assemble_qa.add_argument("--warn-chars", type=int, default=700)
    p_post_assemble_qa.add_argument("--fail-chars", type=int, default=1000)
    p_post_assemble_qa.set_defaults(func=cmd_post_assemble_qa)

    p_capture = sub.add_parser("capture-assets", help="Capture product screenshots from URLs")
    p_capture.add_argument("--project-dir", required=True)
    p_capture.add_argument("--manifest")
    p_capture.add_argument("--cookies")
    p_capture.add_argument("--viewport", default="1280x800")
    p_capture.add_argument("--only-ids", nargs="*", default=[])
    p_capture.set_defaults(func=cmd_capture_assets)

    p_mockups = sub.add_parser("apply-mockups", help="Apply device mockup frames to captured screenshots")
    p_mockups.add_argument("--project-dir", required=True)
    p_mockups.add_argument("--manifest")
    p_mockups.add_argument("--spec")
    p_mockups.set_defaults(func=cmd_apply_mockups)

    p_placeholders = sub.add_parser("generate-placeholders", help="Generate branded placeholder images for missing assets")
    p_placeholders.add_argument("--project-dir", required=True)
    p_placeholders.add_argument("--manifest")
    p_placeholders.add_argument("--theme-tokens")
    p_placeholders.set_defaults(func=cmd_generate_placeholders)

    p_schema = sub.add_parser("validate-schema", help="Validate project JSON files against their schemas")
    p_schema.add_argument("--project-dir", required=True)
    p_schema.add_argument("--strict", action="store_true")
    p_schema.set_defaults(func=cmd_validate_schema)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "visual_unlocked", False):
        args.visual_locked = False
    elif getattr(args, "visual_locked", False):
        args.visual_locked = True
    else:
        args.visual_locked = None
    args.func(args)


if __name__ == "__main__":
    main()
