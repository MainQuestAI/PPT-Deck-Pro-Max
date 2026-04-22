# Deck Production Orchestrator

[中文文档](README.zh-CN.md)

> Turn business briefs into product-grade commercial decks — not generic AI slides.

An AI skill that orchestrates the full lifecycle of commercial slide deck creation: from business brief to narrative arc, visual composition design, page build, and structured QA with rollback routing.

**This is not a build engine.** It's the orchestration layer that sits above build tools (like Anthropic's `$slides` / `$frontend-design`, or any PPTX/HTML generation tool) and ensures the output is commercially viable, visually rich, and narratively coherent.

## What Makes This Different

Most AI PPT tools convert documents into slides. This skill treats deck creation as a **visual communication production system** with stage gates, role isolation, and quality control.

| Capability | Generic AI PPT | Manus-style Image Gen | This Skill |
|-----------|---------------|----------------------|------------|
| Workflow | One-shot | One-shot | 8-step forced pipeline with gates |
| Content richness | What's in the doc | Compressed | **Expert Mode** — AI interviews the expert to extract cases, data, causal chains |
| Content density | Too sparse or too dense | Compressed | **Document-mode default** (250-350 chars/page, self-explanatory) |
| Visual design | Text in boxes | AI-generated images | **Visual composition spec** per page (chart type, icons, data viz, layout) |
| Narrative | None | None | Beat-based arc (setup/tension/resolution/proof/action) |
| Evidence | Screenshots or nothing | Concept mockups | **Asset pipeline** (auto-capture, device mockups, concept UI skeletons) |
| Multi-agent | Single model | Single model | 5 isolated roles (Brief / Visual / Build / Review / **Expert Interviewer**) |
| QA | Manual | None | 25+ automated checks, commercial scoring, world-completeness |
| When it fails | Start over | Start over | **Structured rollback** to correct upstream stage and role |
| Editability | Varies | Flat images | Fully editable PPTX/HTML with real shapes |

## Core Design Philosophy

**The Skill thinks in "visual compositions," not "text structures."**

Every page gets a visual protagonist (chart, icon chain, gauge, diagram, concept UI) — not just text panels. The compression step doesn't just shorten text; it translates business logic into visual communication specs that the Build AI can execute.

**Content richness comes from the expert, not from AI inference.** v2.0 introduces Expert Mode: the AI analyzes source material, identifies 5 types of knowledge gaps (case, causal, data, contrast, objection), and conducts a structured 15-20 minute interview with the domain expert. The result is real cases, real numbers, and real causal judgments — not AI-inferred approximations.

**80% of commercial decks are read, not presented.** Document mode is the default. Every page must be self-explanatory without a presenter.

**World-completeness over visual polish.** A reader flipping through should feel "this system already exists," not "this is a proposal." Empty placeholders are forbidden; concept UI skeletons replace them.

## Quick Start

```bash
# Initialize a 12-page solution deck
python scripts/run_deck_pipeline.py init \
  --project-dir ./my-deck --pages 12 --preset solution_deck

# Expert Mode (v2.0): extract claims + gaps for expert interview
python scripts/run_deck_pipeline.py expert-interview \
  --project-dir ./my-deck

# Expert Mode: finalize interview after redaction review
python scripts/run_deck_pipeline.py finalize-interview \
  --project-dir ./my-deck

# Generate visual composition spec (per-page chart/icon/data decisions)
python scripts/run_deck_pipeline.py visual-composition \
  --project-dir ./my-deck

# Generate a handoff prompt for Build AI
python scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck --role build --page-ids slide_05

# Generate a batch handoff for key pages (auto-resolve pages from image_build_jobs.json)
python scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck --role build --batch-id batch_01

# Generate a per-page subagent dispatch package for a batch
python scripts/run_deck_pipeline.py dispatch-build \
  --project-dir ./my-deck --batch-id batch_01

# Sync asset / job / batch status after human approval
python scripts/run_deck_pipeline.py asset-status \
  --project-dir ./my-deck --asset-id slide_03_screenshot --status approved \
  --final-path generated/slide_03_selected.png --clear-stale

# Once a batch is approved, prepare the HTML assemble package
python scripts/run_deck_pipeline.py prepare-assemble \
  --project-dir ./my-deck --batch-id batch_01

# Assemble the approved batch into starter/index.html
python scripts/run_deck_pipeline.py assemble-html \
  --project-dir ./my-deck --batch-id batch_01

# After HTML assemble is done, mark the batch embedded / awaiting_review
python scripts/run_deck_pipeline.py finalize-assemble \
  --project-dir ./my-deck --batch-id batch_01

# Or close the batch in one shot: finalize -> screenshot -> review package -> QA
python scripts/run_deck_pipeline.py post-assemble-qa \
  --project-dir ./my-deck --batch-id batch_01

# Plan assets (identify which pages need screenshots)
python scripts/run_deck_pipeline.py asset-plan \
  --project-dir ./my-deck

# Capture screenshots from URLs (requires Playwright)
python scripts/run_deck_pipeline.py capture-assets \
  --project-dir ./my-deck --cookies cookies.json

# Apply device mockup frames
python scripts/run_deck_pipeline.py apply-mockups \
  --project-dir ./my-deck

# Run QA with formal review validation
python scripts/run_deck_pipeline.py qa \
  --project-dir ./my-deck --write-state \
  --require-review --review-findings ./my-deck/deck_review_findings.json

# Validate all outputs (formal review mode)
python scripts/run_deck_pipeline.py validate \
  --project-dir ./my-deck --output-mode pptx+html --formal
```

## Forced Workflow

```
Step 0     Classify the task
Step 1     Lock the Brief                    → deck_brief.md          🔔 User confirms
Step 1.5 ★ Expert Interview (expert mode)    → interview_preparation.json
Step 1.6 ★ Redaction Review (expert mode)    → deck_expert_context.md 🔔 User confirms
Step 2     Lock the Vibe                     → deck_vibe_brief.md
Step 3     Narrative Arc & Hero Pages        → deck_narrative_arc.md  🔔 User confirms
Step 4     Layout Draft                      → deck_layout_v1.md
Step 5     Compression + Visual Composition  → deck_clean_pages.md
                                             → deck_visual_composition.md (per-page visual spec)
Step 5.5   Plan Assets                       → deck_asset_plan.md     🔔 User confirms
Step 6     Visual Component System           → tokens, geometry, skeletons
Step 7     Build the Deck                    → .pptx / .html
Step 8     QA & Review Loop                  → findings, scorecard, rollback plan
```

Steps marked ★ are Expert Mode only (default). Set `production_mode: quick` in the Brief to skip them. Each step has a gate. You cannot skip to build without locking the brief. You cannot claim ready without passing QA. If QA fails, the system routes findings to the correct upstream stage and role — not "start over."

## Visual Composition Layer (v1.0+)

The key differentiator. Between content compression and build, every page gets a **visual construction spec**:

```markdown
## Page 3 — Three-Layer Fracture

### Visual Protagonist
Type: gauge_chart × 3
Position: bottom of each column, 30% of page

### Illustrative Data
Metric: Deep intent understanding rate | value=28% | gauge | illustrative=true
Metric: Dynamic strategy adjustment  | value=21% | gauge | illustrative=true

### Icons
brain → Cognition fracture | settings → Decision fracture | file-text → Content fracture

### Concept UI (when screenshots unavailable)
Type: concept_ui | Title: Fracture diagnostic console | Style: terminal_window
```

Build AI receives this as a first-class input — not just "three diagnostic cards" in text, but exact chart types, data values, icons, and layout proportions.

## Expert Mode (v2.0)

The biggest gap in AI-generated decks isn't visual design — it's **content richness**. AI can compress what's in the source material, but it can't create real customer cases, real data points, or real causal judgments from nothing.

Expert Mode solves this by adding a structured interview step between Brief and Narrative:

1. **AI analyzes** the source material and extracts claims (one or more per page)
2. **AI detects 5 types of gaps** per claim: case, causal, data, contrast, objection
3. **AI interviews the expert** with hypothesis-driven questions (not open-ended "anything to add?")
4. **Anti-bias built in**: at least 1 counter-hypothesis question per 3-4 questions
5. **Coverage-driven**: targets hero claims gap fill rate >= 80%, not a fixed number of rounds
6. **Redaction gate**: sensitive information is flagged and reviewed before entering downstream

The output is `deck_expert_context.md` — structured expert knowledge bound to semantic claims, not page numbers. Compression then merges this with priority: expert cases > AI summaries, expert numbers > AI-inferred data.

Set `production_mode: quick` in the Brief to skip Expert Mode (same as v1.x behavior).

## Role Isolation

Five AI workers, each with controlled context visibility:

| Role | Sees | Does Not See |
|------|------|-------------|
| **Brief AI** | Raw business material, narrative arc | Implementation code, visual patches |
| **Expert Interviewer AI** | Brief, claims, gaps, source material | Build code, visual system |
| **Visual AI** | Brief, vibe, clean pages | Raw long documents, review conversations |
| **Build AI** | Current page slice, **visual composition**, **expert context**, tokens | Other pages' code, raw documents |
| **Review AI** | Outputs, montage, state, scorecard schema, **expert artifacts** | Intended answers, subjective conclusions |

## Asset Pipeline

Real product screenshots make proof pages 10x more convincing. The asset pipeline handles the full flow:

1. **Plan** — AI scans clean pages, identifies which pages need screenshots
2. **Capture** — Playwright auto-captures from URLs with cookie auth support
3. **Mockup** — Pillow renders device shells (MacBook, browser, iPhone, tablet, terminal)
4. **Placeholder** — When screenshots unavailable, branded placeholders or **concept UI skeletons** maintain world-completeness
5. **QA** — Proof pages without real assets get `asset_missing` findings

## Project Structure

```
SKILL.md                         Main skill instructions (the "brain")
references/                      33 design guides + JSON schemas
  expert_interview_guide.md      5 gap types, anti-bias, coverage-driven interview
  title_writing_guide.md         Judgment sentences, 30 chars, 2 lines max
  cta_design_guide.md            Threshold control, deliverable promises, urgency
  information_design_guide.md    Data relationship → visual form mapping (8 types)
  visual_composition_guide.md    How to generate per-page visual specs
  concept_ui_guide.md            Concept UI skeletons for world-completeness
  illustrative_data_guide.md     5-level evidence source hierarchy (expert > factual > inferred)
  compression_rules.md           Document mode + 6-layer richness model + audience adaptation
  narrative_arc_guide.md         Beat types, arc templates, emotional curves
  commercial_scorecard.md        Commercial persuasion scoring (6 dimensions)
  build_contract.md              HTML/PPTX assembly contract for build skills
  ...and 22 more
scripts/                         30 Python scripts
  run_deck_pipeline.py           Unified CLI (17 subcommands)
  generate_interview_questions.py Claim extraction + 5-gap detection + richness scoring
  finalize_interview.py          Step 1.6 executor — session validation + expert context generation
  generate_visual_composition.py Per-page visual spec generator
  capture_assets.py              Playwright screenshot capture
  apply_mockup.py                Device shell rendering (5 frame types)
  route_review_findings.py       Structured rollback routing
  build_montage_and_report.py    QA engine with expert-mode checks
  ...and 22 more
assets/
  chart_templates/               6 reusable HTML chart templates
  mockup_frames/                 5 device shell specs
  presets/                       5 business scenario presets
  theme_tokens/                  Dark glass + light paper themes
  example_project/               10-page reference project with full artifacts
  fonts/                         Google Fonts loading
tests/                           78 tests (unit + integration + e2e)
.github/workflows/ci.yml         Python 3.10/3.11/3.12 CI
```

## Requirements

```bash
pip install -r requirements.txt
```

- **Python 3.10+**
- `python-pptx` — PPTX geometry extraction
- `Pillow` — Montage generation + device mockups
- `jsonschema` — Runtime contract validation
- `playwright` (optional) — Auto screenshot capture + page-level visual QA

## Presets

| Preset | Default Task | Arc Pattern |
|--------|-------------|-------------|
| `solution_deck` | Sponsor | setup → tension → resolution → proof → action |
| `product_intro` | Sponsor | setup → proof → resolution → tension → action |
| `internal_strategy` | Owner | tension → resolution → proof → action |
| `industry_pov` | Sponsor | tension → setup → resolution → proof → action |
| `business_partnership` | Sponsor | setup → resolution → proof → tension → action |

## QA Dimensions

The QA engine checks 25+ dimensions across 7 categories:

- **Density** — text overflow, document-mode minimum (150 chars), hero page thresholds
- **Component drift** — undefined visual components
- **Layout stability** — center offset, connector detachment, occupancy
- **Speaker notes** — hero pages must have presenter notes
- **Assets** — proof pages must have screenshots or concept UIs
- **Visual flatness** — pages without visual protagonists
- **World-completeness** — does the deck feel like "a system that exists"
- **Expert mode** — content_thin (hero richness < 3), expert_data_ignored, redaction_incomplete
- **Commercial scoring** — 6-dimension persuasion scorecard with minimum threshold
- **Narrative** — arc coherence, pacing monotony, transition gaps

## License

[MIT](LICENSE)

---

Built by [MainQuest AI](https://github.com/MainQuestAI).
