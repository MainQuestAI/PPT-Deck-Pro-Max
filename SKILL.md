---
name: deck-production-orchestrator
description: Production orchestrator for high-quality commercial slide decks. Use when Codex needs to turn a business brief, long-form strategy document, product narrative, solution material, or reference presentation into a product-grade commercial deck rather than a generic AI PPT. Trigger for requests such as “做一套高质量商业Deck”, “把这个方案做成产品级PPT”, “不要普通AI味”, “输出可成交的presentation”, “按 Vibe Coding 做 Deck”, “需要 Agent 协同做 PPT”, or any task requiring a forced workflow across brief, vibe, hero pages, editorial compression, visual components, build, and QA.
---

# Deck Production Orchestrator

## Overview

Use this skill to orchestrate the full production of a high-quality commercial deck. Do not treat the task as “convert document to slides.” Treat it as a production workflow: business brief, sales narrative, visual system, hero pages, clean page copy, build, and QA.

## Use This Skill vs. Other Skills

Use this skill when the user needs a new deck, a major remake, or a deck that must feel product-grade, sales-ready, and visually unified.

Do **not** use this skill as the default for:

1. Small edits to an existing `.pptx`
2. One-slide fixes
3. Simple document-style presentations
4. Pure slide reading or comparison work

For those cases, prefer:

- `$pptx` for inspection and editing
- `$slides` for direct `.pptx` creation
- `$frontend-design` for visual implementation help

## Forced Workflow

Do not skip steps unless the required artifact already exists and is still valid.

### Step 0: Classify the Task

Identify:

1. Deck type: product intro, solution, internal strategy, industry point of view, or business partnership
2. Input type: long document, page outline, reference deck, or raw request
3. Output type: `pptx`, `html deck`, or both

If the business target is still unclear, create `deck_brief.md` first.

### Step 1: Lock the Brief

Create or update `deck_brief.md`.

It must lock:

1. Product subject
2. Product positioning
3. Audience
4. First buying reason
5. Strongest differentiation
6. Strongest proof
7. Pilot entry point
8. Final CTA

Read `references/deck_brief_template.md` if the brief is missing or weak.

### Step 2: Lock the Vibe

Create or update `deck_vibe_brief.md`.

It must lock:

1. Visual mood
2. Color system
3. Typography
4. Numeric/metric style
5. Graphic language
6. Density ceiling

Read `references/vibe_brief_template.md` and `references/component_system.md`.

### Step 3: Define Hero Pages

Create or update `deck_hero_pages.md`.

Hero pages usually include:

1. Cover
2. Diagnosis / pain point
3. Proof / sample page
4. Core capability or architecture
5. Differentiation
6. CTA / commercial entry

Read `references/hero_pages_guide.md`.

At the end of this step, pause for lightweight human confirmation when the user is collaborating live.

### Step 4: Build the Layout Draft

Create or update `deck_layout_v1.md`.

Each page should include:

1. Title
2. Main conclusion
3. Region structure
4. Visual or chart suggestion
5. Closing line or footer logic

Read `references/layout_page_guide.md`.

### Step 5: Editorial Compression

Create or update `deck_clean_pages.md`.

Enforce:

1. One conclusion per page
2. Replace paragraphs with visual structures where possible
3. Remove internal discussion traces
4. Preserve evidence

Read `references/compression_rules.md` before compressing.

### Step 6: Lock the Visual Component System

Create or update:

- `deck_visual_system.md`
- `deck_component_tokens.md`
- `deck_theme_tokens.json`
- `deck_geometry_rules.md`
- `deck_page_skeletons.md`

Lock:

1. Page archetypes
2. Component family
3. Color tokens
4. Type tokens
5. Spacing tokens
6. Chart rules
7. CSS / visual signatures
8. Geometry and alignment rules
9. Page-level skeletons and occupancy targets

Read `references/component_system.md`, `references/chart_strategy.md`, and `references/layout_geometry_rules.md`.

At the end of this step, pause for lightweight human confirmation when the user is collaborating live.

### Step 7: Build the Deck

Choose the correct build path:

- Use `$slides` for editable `.pptx`
- Use `$frontend-design` for HTML deck or high-fidelity visual exploration
- Use `$ui-ux-pro-max` when visual direction or component decisions need strengthening
- Use `$pptx` if a reference deck must be analyzed before rebuild

Always maintain `slide_state.json`.

For Deck Build work, use `scripts/context_manager.py` to keep context minimal. Generate one page at a time, or at most three pages in a small batch. Never let the build model accumulate long code from many previous pages.

Do not let the build model freehand page geometry when the page has already been classified. Prefer building from:

1. archetype
2. page skeleton
3. geometry rules
4. component family

If the build path supports it, also emit `layout_manifest.json` or page-level layout metadata so later QA can validate geometry instead of only validating copy density.

If the build path does not yet emit geometry metadata natively, generate or refresh the manifest through `scripts/generate_layout_manifest.py` before formal QA.

### Step 8: QA and Review Loop

Run QA before claiming the deck is ready.

Minimum QA outputs:

- `montage.png`
- `deck_review_report.md`
- `review_package.json`
- `deck_review_findings.json`（正式评审版建议强制）
- `commercial_scorecard.json`（正式评审版建议强制）
- `review_rollback_plan.json`
- `review_rollback_plan.md`

Read `references/qa_checklist.md`.

Use:

- `scripts/validate_deck_outputs.py`
- `scripts/check_component_drift.py`
- `scripts/check_layout_stability.py`
- `scripts/update_slide_state.py`
- `scripts/build_montage_and_report.py`
- `scripts/generate_review_package.py`
- `scripts/generate_layout_manifest.py`
- `scripts/generate_commercial_scorecard.py`
- `scripts/update_layout_manifest.py`

If the deck is moving from build stage into formal review, generate `review_package.json` first and require structured review findings before marking the deck as ready.

Do not stop at findings. After structured findings are available, route them into a rollback plan so the system can tell:

1. which stage to roll back to
2. which files must be edited
3. which AI role should own the rework
4. which pages should be rebuilt first

After the rollback plan is generated, prefer producing role-specific rework handoffs instead of forwarding the full plan to every worker. The rework handoff should contain only:

1. tasks assigned to that role
2. impacted pages for that role
3. target files to modify
4. success criteria for that role

If QA fails, roll back to the right stage instead of patching blindly:

- copy too long -> `deck_clean_pages.md`
- wrong chart logic -> `references/chart_strategy.md`
- visual drift -> `deck_visual_system.md`
- geometry unstable -> `references/layout_geometry_rules.md` or `deck_page_skeletons.md`
- weak hero pages -> `deck_hero_pages.md`

Use:

- `scripts/route_review_findings.py`
- `scripts/generate_rework_handoff.py`
- `references/review_rollback_map.json`

If a `.pptx` artifact already exists, prefer extracting real page geometry before formal QA:

- `scripts/extract_layout_from_pptx.py`
- `scripts/update_layout_manifest.py`

## Role Isolation Rules

Do not give every AI worker the same context.

Read `references/context_handoff_rules.md` before splitting work across multiple agents.

Critical rule:

1. Brief / Narrative AI may see raw business material
2. Visual System AI should see brief + clean pages, not raw long documents
3. Deck Build AI should see only current page nodes, visual system, tokens, and `slide_state.json`
4. Review AI should see outputs and state, not intended answers

## Chart Strategy Rule

Do not ask the build model to invent complex chart code from scratch when a stable template can be mapped.

Prefer:

1. choose the business relationship
2. choose the simplest valid chart structure
3. map data into a tested template

Read `references/chart_strategy.md` and reuse assets under `assets/chart_templates/`.

## Evidence Preservation Rule

During compression, do not drop business proof just to make a page cleaner.

Preserve:

1. Specific numbers
2. Named customers, brands, or segments
3. Important system nodes
4. Concrete case anchors

If the page becomes too dense, split it or convert it into a chart. Do not remove the evidence.

## Project Initialization

When starting a new deck project, use:

```bash
python scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages <n> --output-mode pptx+html
```

For stage operations, prefer:

```bash
python scripts/run_deck_pipeline.py build-context --project-dir <project-dir> --page-ids slide_05
python scripts/run_deck_pipeline.py stage --project-dir <project-dir> --global-status building
python scripts/run_deck_pipeline.py manifest --project-dir <project-dir> --merge-existing
python scripts/run_deck_pipeline.py extract-layout --project-dir <project-dir>
python scripts/run_deck_pipeline.py review-package --project-dir <project-dir>
python scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role review
python scripts/run_deck_pipeline.py qa --project-dir <project-dir> --extract-layout-from-pptx --require-review --require-commercial-scorecard --review-findings <deck_review_findings.json> --commercial-scorecard <commercial_scorecard.json> --write-state
python scripts/run_deck_pipeline.py validate --project-dir <project-dir> --output-mode pptx+html
```

For common business scenarios, use presets:

```bash
python scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages 12 --preset solution_deck
python scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset internal_strategy
python scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset industry_pov
python scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset business_partnership
python scripts/run_deck_pipeline.py preset --project-dir <project-dir> --preset product_intro
```

For AI worker delegation, generate handoff prompts:

```bash
python scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role brief
python scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role visual
python scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role build --page-ids slide_05
python scripts/run_deck_pipeline.py handoff --project-dir <project-dir> --role review
```

## Resources

Use these files intentionally:

- `references/workflow.md`
  - full production flow and stage gates
- `references/deck_brief_template.md`
  - brief structure
- `references/vibe_brief_template.md`
  - visual direction structure
- `references/hero_pages_guide.md`
  - hero page selection and priority rules
- `references/layout_page_guide.md`
  - page draft format
- `references/compression_rules.md`
  - editorial compression and evidence preservation
- `references/chart_strategy.md`
  - chart selection and anti-fake-chart rules
- `references/component_system.md`
  - page archetypes, tokens, and component locking
- `references/context_handoff_rules.md`
  - multi-agent context isolation
- `references/qa_checklist.md`
  - pre-delivery QA checks
- `references/prompt_templates.md`
  - prompts for brief, visual, build, and review roles
- `references/review_findings.schema.json`
  - required review output structure for multimodal review
- `references/commercial_scorecard.md`
  - commercial persuasion scoring rubric
- `references/commercial_scorecard.schema.json`
  - commercial scoring validation contract
- `references/slide_state.schema.json`
  - state machine validation contract
- `references/layout_manifest.schema.json`
  - geometry validation contract for page layout metadata
- `references/review_rollback_plan.schema.json`
  - rollback plan validation contract

## Success Criteria

This skill succeeds only if the final deck is:

1. commercially clear
2. visually consistent
3. proof-led instead of definition-led
4. not document-like
5. geometry-stable in the actual built artifact, not only in the skeleton
6. above the minimum commercial score threshold
7. ready for delivery in `pptx`, `html`, or both
