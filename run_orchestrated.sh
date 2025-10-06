#!/usr/bin/env bash
set -euo pipefail

# Load .env if present (XAI/GEMINI/OPENROUTER may be there)
if [[ -f .env ]]; then
  set -a
  source ./.env
  set +a
fi

INPUT_DIR=${1:-"./data/raw_pdfs"}
BATCH=${2:-1}

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set. Export it before running or add it to .env"
  exit 1
fi

export OPENAI_MODEL=${OPENAI_MODEL:-gpt-5}
export OPENAI_RESPONSES=${OPENAI_RESPONSES:-true}
export OPENAI_ONLY=${OPENAI_ONLY:-true}

# Orchestrated mode with 95 acceptance and chunked pages
export ORCHESTRATE=${ORCHESTRATE:-true}
export ORCHESTRATOR_MAX_ROUNDS=${ORCHESTRATOR_MAX_ROUNDS:-5}
export ORCHESTRATOR_TARGET_SCORE=${ORCHESTRATOR_TARGET_SCORE:-95}
export ORCHESTRATOR_CONCURRENCY=${ORCHESTRATOR_CONCURRENCY:-2}

# Keep requests reliable and focused
export VISION_PAGES_PER_CALL=${VISION_PAGES_PER_CALL:-10}
export SECTIONIZER_PAGES_PER_CALL=${SECTIONIZER_PAGES_PER_CALL:-6}
export SECTIONIZER_PACE_MS=${SECTIONIZER_PACE_MS:-500}
export PASS_PAGE_LABELS=${PASS_PAGE_LABELS:-true}

# Hard gating for numerics/evidence
export ENFORCE_VERIFICATION=${ENFORCE_VERIFICATION:-strict}
export STRICT_NEEDS_EVIDENCE=${STRICT_NEEDS_EVIDENCE:-true}

echo "Running orchestrated pipeline on ${INPUT_DIR} (batch=${BATCH})"
python run_gracian.py --input-dir "${INPUT_DIR}" --batch-size "${BATCH}"

