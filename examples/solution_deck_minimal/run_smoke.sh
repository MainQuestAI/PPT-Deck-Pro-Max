#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${1:-/tmp/deck_solution_minimal}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf "$OUT_DIR"

"$PYTHON_BIN" "$ROOT_DIR/scripts/run_deck_pipeline.py" init \
  --project-dir "$OUT_DIR" \
  --pages 3 \
  --preset solution_deck \
  --production-mode quick

"$PYTHON_BIN" "$ROOT_DIR/scripts/run_deck_pipeline.py" handoff \
  --project-dir "$OUT_DIR" \
  --role build \
  --page-ids slide_01

"$PYTHON_BIN" "$ROOT_DIR/scripts/run_deck_pipeline.py" qa \
  --project-dir "$OUT_DIR" \
  --write-state

echo "[OK] smoke project: $OUT_DIR"
echo "[OK] handoff: $OUT_DIR/build_handoff.md"
echo "[OK] QA report: $OUT_DIR/deck_review_report.md"
