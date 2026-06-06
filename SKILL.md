---
name: ppt-deck-pro-max
description: "PPT Deck Pro Max builds product-grade PPT/HTML decks from briefs, strategy docs, product narratives, or solution materials. It manages brief, narrative, visual system, image-led build, QA, and rollback."
---

# PPT Deck Pro Max

## Overview

Use this skill to produce a high-quality PPT/HTML deck from raw materials. Do not treat the task as “convert document to slides.” Treat it as a production workflow: brief, narrative, visual system, hero pages, clean page copy, build, and QA.

Before production work, run:

```bash
python3 scripts/run_deck_pipeline.py doctor
```

Use `--production-mode expert` for high-value decks that need expert enrichment. Use `--production-mode quick` for smaller decks where the Expert Interview startup cost would outweigh the value.

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

Artifact validity means:

1. Freshness: it reflects the current brief, audience, output mode, and page count
2. Schema: required JSON files validate against the matching schema when a schema exists
3. Coverage: every required page or beat has a non-empty entry
4. Review state: any human approval, redaction decision, or QA status is recorded in the artifact or `slide_state.json`
5. Traceability: the artifact names its source inputs or can be regenerated from the current project files

If any item fails, refresh the artifact before moving forward.

## Production Sub-Modes

Choose a production sub-mode during Step 0 and record it in `deck_brief.md` and `slide_state.json` when those artifacts exist.

Default to `standard_deck` unless the request clearly matches a specialized sub-mode.

### `standard_deck`

Use for product intros, solution decks, strategy decks, industry point-of-view decks, and business partnership decks that will be built as editable PPTX, HTML, or a mixed deck.

Follow the main forced workflow from Step 0 to Step 8.

### `formal_bid_image_led`

Use for formal bid, tender, RFP response, technical proposal, or leave-behind decks where pages may be assembled from generated full-page images.

This sub-mode adds stricter gates for:

1. Page registry and actual PPT page mapping
2. Source-id image traceability
3. Candidate / Go / No-Go image separation
4. Final assembly naming
5. Delivery QA for page ratio, title hygiene, placeholders, internal-language leakage, and backup coverage

When this sub-mode is active, the mode-specific requirements below are mandatory in addition to the main forced workflow.

### Step 0: Classify the Task

Identify:

1. Deck type: product intro, solution, internal strategy, industry point of view, or business partnership
2. Input type: long document, page outline, reference deck, or raw request
3. Output type: `pptx`, `html deck`, or both
4. Production sub-mode: `standard_deck` or `formal_bid_image_led`

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

### Step 1.2: Content Governance Gate (expert / longform)

Before writing narrative pages, create the content governance artifacts:

1. `deck_source_digest.md`: source inventory, key facts, usable proof, explicit gaps
2. `deck_claim_map.json`: core claims with source pages, roles, evidence, and risk notes
3. `deck_capacity_plan.md` + `deck_capacity_plan.json`: target pages, recommended pages, and max supported pages
4. `deck_gap_registry.json`: open gaps, with `blocking: true`, `status: blocking`, or `severity: critical` for hard blockers
5. `deck_question_queue.md`: prioritized questions for the user / domain expert

The three JSON artifacts are covered by `scripts/validate_schema.py`.

Gate rule:

- Do not enter page-by-page drafting when `target_pages > max_supported_pages`
- Do not enter page-by-page drafting while any blocking gap remains open
- Do not pass this gate with empty placeholder markdown artifacts
- Quick mode may skip this gate unless the user explicitly asks for content governance

Use:

```bash
python3 scripts/run_deck_pipeline.py validate \
  --project-dir <project-dir> --output-mode pptx+html --expert-mode --content-governance
```

### Step 1.5: Expert Interview (expert mode only)

If `production_mode: expert` (default), run a structured interview with the user to enrich the deck's content with implicit expert knowledge.

The AI role here is **co-creator, not interviewer**. It brings its own understanding of the source material, identifies content gaps, and asks targeted questions with hypotheses attached.

Process:
1. Run `scripts/generate_interview_questions.py` after Step 1.2; it reads `deck_claim_map.json`, `deck_gap_registry.json`, and `deck_capacity_plan.json` when available
2. If content governance artifacts are absent, the command falls back to `deck_clean_pages.md` for legacy projects
3. AI reads the gap analysis and source material, then constructs hypothesis-led questions at runtime
4. Dialogue is coverage-driven: target hero claims gap fill rate ≥ 80%
5. Every 3-4 questions, include at least one counter-hypothesis question (anti-bias)
6. Output: `deck_question_queue.md`, `interview_preparation.json`, `interview_session.json` (runtime state) + insights collected

Read `references/expert_interview_guide.md`.

### Step 1.6: Redaction Review (expert mode only)

After Expert Interview, review all sensitive information collected. This is an independent gate.

Process:
1. Present all `needs_redaction` items to the user
2. User confirms: clear / redact / remove for each item
3. Generate `deck_expert_context.md` (final artifact, claims + confirmed insights only)
4. Include `brief_feedback` section if the interview revealed Brief inaccuracies

Only proceed to Step 2 after all redaction decisions are made.

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

### Step 3: Define Narrative Arc & Hero Pages

First create or update `deck_narrative_arc.md`.

The narrative arc must lock:

1. Beat sequence (setup / tension / resolution / proof / action per page)
2. Emotional curve with at least one confidence inflection point
3. Transition logic between pages
4. Breathing page placement

Read `references/narrative_arc_guide.md` and `references/pacing_rhythm_guide.md`.

Then create or update `deck_hero_pages.md`.

Hero pages usually include:

1. Cover
2. Diagnosis / pain point
3. Proof / sample page
4. Core capability or architecture
5. Differentiation
6. CTA / commercial entry

Hero page selection must align with beat types: tension beats and strong proof beats are more likely to be heroes.

Read `references/hero_pages_guide.md` and `references/objection_handling_guide.md`.

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

### Step 5: Content Compression + Visual Composition Design

This step has two outputs, produced together:

1. `deck_clean_pages.md` — compressed page copy with visual declarations
2. `deck_visual_composition.md` — per-page visual construction spec

**The goal of this step is not just "make text shorter." It is "translate business logic into visual communication specs."**

For the content compression, enforce:

1. One conclusion per page
2. Replace paragraphs with visual structures where possible
3. Remove internal discussion traces
4. Preserve evidence

For the visual composition, enforce:

1. Every page must have a **visual protagonist** (chart, icon chain, big metric, diagram, or screenshot) — pure text panels are not acceptable
2. Identify each page's core **data relationship** (comparison, gap, flow, loop, category, metric) and choose the matching visual form
3. Generate **illustrative data** when concepts can be quantified but the source lacks numbers — mark as `illustrative=true`
4. Specify **icons** for each conceptual element — not emoji, but named icons (brain, gear, target, shield, etc.)
5. Define **visual weight distribution** — what the eye sees first (60%), second (30%), last (10%)

Read `references/compression_rules.md`, `references/visual_composition_guide.md`, `references/information_design_guide.md`, and `references/illustrative_data_guide.md`.

### Step 5.5: Plan Assets

After compression, review each page and identify which pages need real product screenshots.

Create or update `deck_asset_plan.md` and `asset_manifest.json`.

For proof beat pages, hero_proof, hero_system, and sample pages, strongly recommend real product screenshots over abstract illustrations.

Pause and ask the user:

1. Can you provide a product URL for automatic screenshots?
2. Do you have screenshot files to provide directly?
3. Should we use placeholders for now?

If the user provides URLs, use `scripts/capture_assets.py` with optional `--cookies` for authenticated pages. If not, use `scripts/generate_placeholders.py` to create branded placeholders that maintain deck structure.

Read `references/asset_pipeline_guide.md`.

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

### Step 6.5: `formal_bid_image_led` Page Registry Gate

Run this gate only when the active production sub-mode is `formal_bid_image_led`.

Before generating or assembling images, lock a page registry from the project's source-of-truth files. This prevents page drift, wrong section ranges, and accidental exposure of production page numbers.

Required source-of-truth inputs, when available:

1. next-page or generation checklist, such as `*_下一阶段待生成页面清单.md`
2. formal page scripts, such as `正式版逐页稿/`
3. implementation method table, such as `*_逐页制作实现方式总表.md`
4. direct-reference page list, appendix list, or non-counted chapter list
5. current passed image directory, candidate image directory, and batch manifests

Create or update:

- `page_registry.md`
- `image_generation_manifest.md`
- `actual_page_mapping.md`
- `known_issue_log.md`

The page registry must record:

1. source page id, such as `F-02`, `C-01`, `027`, `S-04`
2. actual PPT page number after front matter, non-counted chapters, core pages, and appendix/service pages are placed
3. chapter and page title from the formal page script
4. generation status: `planned`, `candidate`, `Go`, `No-Go`, `replaced`, or `direct-reference`
5. source prompt or page script path
6. approved image path
7. known issues and fix owner

For large formal bid decks, preserve two naming systems:

1. source-id directory: stable source IDs for traceability, such as `已过线PPT页面图片/059.png`
2. actual-page directory: assembly-ready names, such as `065_059_定制开发总体方案.png`

Do not overwrite the source-id directory with actual page names. Create a new actual-page directory and keep a timestamped backup before bulk renaming or replacing images.

If the deck has direct-reference pages that are not generated images, leave explicit holes in `actual_page_mapping.md` so PPT assembly can reserve those page positions.

### Step 7: Build the Deck

Choose the correct build path:

- Use `$slides` for editable `.pptx`
- Use `$frontend-design` for HTML deck or high-fidelity visual exploration
- Use `$ui-ux-pro-max` when visual direction or component decisions need strengthening
- If the user is running Codex and the deck is image-led, recommend `$imagegen` to generate raster page visuals, hero images, product mockups, and concept UI assets before assembly
- Use `$pptx` if a reference deck must be analyzed before rebuild

Always maintain `slide_state.json`.

For Codex image-led builds, add one explicit image iteration before final assembly:

1. Run `generate-assets` / `dispatch-build` to create page-level image jobs.
2. Use `$imagegen` for each approved job prompt; save final assets inside the project, not only under `$CODEX_HOME`.
3. Update asset/job/batch status with `asset-status`.
4. Assemble only after the first batch of hero/proof/system images is approved.

When the active production sub-mode is `formal_bid_image_led`, use a stricter production loop:

1. Generate page prompts from `page_registry.md`, not from loose file names.
2. Process pages in small batches and write one batch manifest per batch.
3. Store Image2 candidates in `图片生成候选结果/<batch_id>/` or an equivalent candidate directory.
4. Move only `Go` pages into the passed image directory.
5. Record every Go decision in `image_go.md` or `image_generation_manifest.md`.
6. Keep `No-Go` pages out of the passed image directory until regenerated.
7. After all pages pass, create an actual-page directory from the source-id passed directory.
8. Verify source count equals actual-page count, except for documented direct-reference holes.

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
- `deck_review_findings.json` (required for formal review)
- `commercial_scorecard.json` (required for formal review)
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

For expert or longform decks, run validate with `--content-governance` before formal delivery.

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

When the active production sub-mode is `formal_bid_image_led`, run these additional checks before delivery or PPT assembly:

1. Image ratio: every passed image must match the requested slide ratio, usually 16:9. A wrong-ratio image is a blocker because PPT will stretch, crop, or letterbox it.
2. Actual page mapping: section ranges on directory or response pages must match the implementation table and final page count.
3. Title hygiene: visible titles must not include production-only source IDs, such as `27 |`, unless the deck style explicitly uses visible section numbering.
4. Placeholder hygiene: pages containing placeholders like `公司名称`, `截图占位`, `待补`, or generic role labels are blockers unless the user explicitly accepts manual replacement.
5. Internal-language hygiene: no visible text may expose source paths, source page markers, production notes, batch ids, prompt ids, or generation status.
6. Naming audit: final image filenames must sort in PPT assembly order and include enough source-id traceability for debugging.
7. Backup audit: original passed images must have a timestamped backup before bulk replacement, page-fix, or actual-page renaming.

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

When starting a new deck project, use the orchestration script first:

```bash
python3 scripts/run_deck_pipeline.py init --project-dir <project-dir> --pages <n> --output-mode pptx+html
```

For stage commands, presets, batch build, review, and rework handoff, read `references/workflow.md`.

## Resources

Use these files intentionally:

- `references/workflow.md`
  - full production flow and stage gates
- `references/expert_interview_guide.md`
  - claim extraction, gap detection, anti-bias, coverage-driven dialogue
- `references/title_writing_guide.md`
  - judgment sentences, length limits, 3-second test
- `references/cta_design_guide.md`
  - threshold control, deliverable promises, urgency
- `references/deck_brief_template.md`
  - brief structure
- `references/vibe_brief_template.md`
  - visual direction structure
- `references/narrative_arc_guide.md`
  - beat types, arc templates, and emotional curve validation
- `references/pacing_rhythm_guide.md`
  - density alternation, breathing pages, and transition logic
- `references/objection_handling_guide.md`
  - common objection categories and placement strategy
- `references/concept_ui_guide.md`
  - concept UI skeletons for world-completeness when real screenshots are unavailable
- `references/asset_pipeline_guide.md`
  - product screenshot capture, device mockups, and placeholder system
- `references/build_contract.md`
  - multi-page assembly and output naming conventions for build skills
- `references/font_loading_guide.md`
  - web font and PPTX font configuration
- `references/hero_pages_guide.md`
  - hero page selection and priority rules
- `references/layout_page_guide.md`
  - page draft format
- `references/compression_rules.md`
  - editorial compression and evidence preservation
- `references/visual_composition_guide.md`
  - how to generate per-page visual construction specs
- `references/information_design_guide.md`
  - data relationship → visual form mapping rules
- `references/illustrative_data_guide.md`
  - when and how to generate illustrative data for visualization
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

1. **world-complete** — a reader flipping through alone should feel "this system already exists," not "this is a proposal"
2. **self-explanatory** — every page is independently readable without a presenter (document mode density by default)
3. commercially clear — the business case is obvious
4. visually consistent — no rogue styles, no competing decorations
5. proof-led instead of definition-led
6. **no unfinished signals** — no empty placeholders, no "SCREENSHOT PLACEHOLDER" rectangles; use concept UI skeletons instead
7. geometry-stable in the actual built artifact, not only in the skeleton
8. above the minimum commercial score threshold
9. ready for delivery in `pptx`, `html`, or both

### Quantitative Gates

Use these thresholds unless the project brief sets stricter ones:

1. `commercial_scorecard.json` overall score >= 3.3/5, with no core dimension below 3.0/5
2. Content governance: `target_pages <= max_supported_pages`, with zero blocking gaps
3. Expert mode hero claims gap fill rate >= 80%, and average `richness_score` >= 3/5
4. Page copy density: warn at >700 characters per page, fail at >1000 characters per page unless the page is explicitly marked as appendix/reference
5. Visual protagonist coverage: every non-appendix page has one visual protagonist, occupying >= 40% of the intended main visual area
6. Geometry tolerance: actual center alignment deviation <= 3% of slide width for centered archetypes; occupancy ratio stays within the page skeleton's min/max range
7. Review blockers: zero unresolved `redaction_incomplete`, `world_incomplete`, `geometry_broken`, or `internal_language_leak` findings before delivery

### Definition of Done

A deck is deliverable only when:

1. Required planning artifacts are current: brief, vibe, narrative arc, hero pages, layout, clean pages, visual composition, asset plan, visual system, component tokens, theme tokens, geometry rules, page skeletons, and `slide_state.json`
2. The requested final artifact exists: `.pptx`, HTML deck, or both
3. Formal QA artifacts exist: `montage.png`, `deck_review_report.md`, `review_package.json`, `deck_review_findings.json`, `commercial_scorecard.json`, `review_rollback_plan.json`, and `review_rollback_plan.md`
4. `validate_deck_outputs.py` passes for the requested output mode; expert / longform decks also pass `--content-governance`
5. Formal review blockers are either resolved or explicitly accepted by the user with the remaining risk recorded

When the active production sub-mode is `formal_bid_image_led`, Definition of Done also requires:

1. `page_registry.md` or equivalent page registry exists and covers all generated and direct-reference pages
2. passed source-id image directory exists
3. actual-page image directory exists and sorts in final PPT order
4. actual page mapping file exists and explains front matter, core pages, service pages, appendix pages, and direct-reference holes
5. all passed images have valid aspect ratio
6. all known blocking issues are fixed or explicitly accepted by the user
