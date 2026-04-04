# Deck Production Orchestrator

> Turn business briefs into product-grade commercial decks — not generic AI slides.

A production-grade AI skill that orchestrates the full lifecycle of commercial slide deck creation: from business brief to narrative arc, visual system, page build, and structured QA with rollback routing.

## What Makes This Different

Most AI PPT tools convert documents into slides. This skill treats deck creation as a **production workflow** with stage gates, role isolation, and structured quality control.

| Capability | Generic AI PPT | This Skill |
|-----------|---------------|------------|
| Workflow | One-shot generation | 8-step forced pipeline with gates |
| Content strategy | Dump text on slides | Brief locking, hero page selection, evidence preservation |
| Narrative | None | Beat-based arc (setup/tension/resolution/proof/action) |
| Visual system | Random styling | Locked tokens, archetypes, geometry rules |
| Multi-agent | Single model | 4 isolated roles (Brief / Visual / Build / Review) |
| QA | Manual review | Automated density, geometry, component drift, commercial scoring |
| Rollback | Start over | Structured findings route to correct upstream stage and role |

## Quick Start

```bash
# Initialize a 12-page solution deck
python scripts/run_deck_pipeline.py init \
  --project-dir ./my-deck --pages 12 --preset solution_deck

# Generate a handoff prompt for Brief AI
python scripts/run_deck_pipeline.py handoff \
  --project-dir ./my-deck --role brief

# Generate build context for a specific page
python scripts/run_deck_pipeline.py build-context \
  --project-dir ./my-deck --page-ids slide_05

# Run QA with review findings and commercial scorecard
python scripts/run_deck_pipeline.py qa \
  --project-dir ./my-deck --write-state \
  --require-review --review-findings ./my-deck/deck_review_findings.json

# Validate all required outputs exist
python scripts/run_deck_pipeline.py validate \
  --project-dir ./my-deck --output-mode pptx+html
```

## Forced Workflow

```
Step 0  Classify the task
Step 1  Lock the Brief              → deck_brief.md
Step 2  Lock the Vibe               → deck_vibe_brief.md
Step 3  Narrative Arc & Hero Pages  → deck_narrative_arc.md + deck_hero_pages.md
Step 4  Layout Draft                → deck_layout_v1.md
Step 5  Editorial Compression       → deck_clean_pages.md (with speaker notes)
Step 6  Visual Component System     → tokens, geometry, skeletons
Step 7  Build the Deck              → .pptx / .html + slide_state.json
Step 8  QA & Review Loop            → findings, scorecard, rollback plan
```

Each step has a gate. You cannot skip to build without locking the brief. You cannot claim ready without passing QA.

## Role Isolation

Four AI workers, each with controlled context visibility:

| Role | Sees | Does Not See |
|------|------|-------------|
| **Brief AI** | Raw business material, history | Implementation code, visual patches |
| **Visual AI** | Brief, vibe, clean pages | Raw long documents, review conversations |
| **Build AI** | Current page slice, tokens, state | Other pages' code, raw documents |
| **Review AI** | Outputs, state, package | Intended answers, subjective conclusions |

## Narrative Arc System

Every deck follows a beat sequence that controls the persuasion journey:

- **setup** — recognition, empathy
- **tension** — urgency, discomfort
- **resolution** — clarity, direction
- **proof** — confidence, credibility
- **action** — momentum, low barrier

Five preset arc templates ship with the skill (solution, product intro, internal strategy, industry POV, business partnership).

## Project Structure

```
SKILL.md                    Main skill instructions
references/                 Design guides, schemas, templates
  narrative_arc_guide.md    Beat types and arc validation
  pacing_rhythm_guide.md    Density curves and breathing pages
  objection_handling_guide.md  Objection categories and placement
  commercial_scorecard.md   Commercial persuasion scoring
  ...                       (19 reference files total)
scripts/                    Pipeline automation (20 Python scripts)
  run_deck_pipeline.py      Unified CLI orchestrator
  page_parser.py            Markdown page extraction + speaker notes
  ...
assets/
  chart_templates/          6 reusable HTML chart templates
  presets/                  5 business scenario presets
  theme_tokens/             Dark glass + light paper themes
  example_project/          10-page MirrorWorld reference project
  html_deck_starter/        HTML deck boilerplate
  pptx_deck_starter/        PPTX generation boilerplate
tests/                      Unit tests
```

## Requirements

```bash
pip install -r requirements.txt
```

- Python 3.10+
- `python-pptx` (for PPTX geometry extraction)
- `Pillow` (for montage generation; optional — graceful degradation)

## Presets

| Preset | Use Case | Arc Pattern |
|--------|----------|-------------|
| `solution_deck` | Solution / proposal | setup → tension → resolution → proof → action |
| `product_intro` | Product introduction | setup → proof → resolution → tension → action |
| `internal_strategy` | Internal strategy review | tension → resolution → proof → action |
| `industry_pov` | Industry point of view | tension → setup → resolution → proof → action |
| `business_partnership` | Business partnership | setup → resolution → proof → tension → action |

## Contributing

1. Fork the repo
2. Create a feature branch
3. Run tests: `python -m pytest tests/`
4. Submit a PR with a clear description

## License

[MIT](LICENSE)

---

Built by [MainQuest AI](https://github.com/MainQuestAI).
