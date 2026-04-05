# Contributing to Deck Production Orchestrator

Thank you for considering contributing. This project aims to be the best open-source AI deck production skill — contributions that improve content strategy, visual design intelligence, or pipeline reliability are especially welcome.

## Getting Started

```bash
# Clone
git clone https://github.com/MainQuestAI/MQ-deck-pro-Skill.git
cd MQ-deck-pro-Skill

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Verify all scripts compile
python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('scripts/*.py')]"

# Verify all JSON is valid
python -c "import json, glob; [json.loads(open(f).read()) for f in glob.glob('references/*.json')]"
```

## Project Layout

```
SKILL.md              ← The "brain" — all AI instructions live here
references/           ← Design knowledge (guides, schemas, templates)
scripts/              ← Python automation (CLI tools, QA, routing)
assets/               ← Chart templates, presets, themes, fonts, examples
tests/                ← Unit + integration + e2e tests
```

## How to Contribute

### Adding a Chart Template

1. Create `assets/chart_templates/your_template.html` — must be a self-contained HTML fragment with `{{PLACEHOLDER}}` tokens
2. Create `assets/chart_templates/your_template.json` — metadata (name, use_for, structure, rules)
3. Update `assets/chart_templates/README.md`
4. Reference from `references/chart_strategy.md` if it maps to a standard data relationship

### Adding a Preset

1. Create `assets/presets/your_preset.json` with `name`, `default_output_mode`, `brief_hints`, `hero_pages`, and `narrative_template`
2. Add the preset name to `PRESET_CHOICES` in `scripts/run_deck_pipeline.py`
3. Update the Presets table in `README.md`

### Adding a Reference Guide

1. Create `references/your_guide.md`
2. Add it to the Resources list in `SKILL.md`
3. If it defines a new QA dimension, also update:
   - `references/review_findings.schema.json` (new type enum value)
   - `references/review_rollback_map.json` (new rollback route)
   - `references/qa_checklist.md` (new check items)

### Modifying a Script

1. Read the existing tests in `tests/` for that script
2. Make your changes
3. Add/update tests to cover the change
4. Run the full test suite: `python -m pytest tests/ -v`
5. Verify syntax: `python -c "import py_compile; py_compile.compile('scripts/your_script.py', doraise=True)"`

## Code Standards

- **Python 3.10+** — use `from __future__ import annotations` in every file
- **Type hints** — all function signatures should have type annotations
- **No external dependencies for core pipeline** — `python-pptx`, `Pillow`, `jsonschema` are the only required deps. `playwright` is optional.
- **Graceful degradation** — if an optional dependency (Pillow, Playwright) is missing, print a `[SKIP]` message and continue, don't crash
- **JSON files** — must be valid JSON, 2-space indent, `ensure_ascii=False`
- **Markdown files** — use `## 第 N 页` as page separators in all page-level artifacts (this is the contract that `page_parser.py` depends on)

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_generate_visual_composition.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest tests/ --cov=scripts --cov-report=term-missing
```

Current test count: **46 tests** across 11 test files.

Tests should cover:
- Core parsing logic (`page_parser.py`)
- Relationship detection and visual composition generation
- Rollback routing
- QA issue detection (density, assets, speaker notes)
- Schema validation
- Full pipeline integration (init → preset → asset-plan → QA)

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Ensure all 46+ tests pass
4. Ensure all scripts compile and all JSON is valid
5. Update `CHANGELOG.md` with a brief description
6. Submit a PR with:
   - **What** — what you changed
   - **Why** — what problem it solves
   - **How to verify** — how to test the change

## Versioning

We use semantic versioning:
- **Major** (1.x → 2.0): Architecture-level changes (e.g., v1.0 visual composition layer)
- **Minor** (1.0 → 1.1): New features or significant design philosophy changes
- **Patch** (1.1.0 → 1.1.1): Bug fixes, review findings, integration fixes

## Questions?

Open an issue on GitHub. For architecture discussions, include context from `SKILL.md` and the relevant `references/` files.
