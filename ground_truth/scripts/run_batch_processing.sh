#!/bin/bash
# Run batch processing of Hjorthagen + NDS with schema evolution

cd "$(dirname "$0")"
PROJECT_ROOT="$(cd ../.. && pwd)"

# Load API key from .env (filter out comments and invalid exports)
export OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" "$PROJECT_ROOT/.env" | cut -d'=' -f2-)

echo "🚀 Batch Processing: Hjorthagen + NDS"
echo "====================================="
echo ""
echo "API Key: ${OPENAI_API_KEY:0:20}..."
echo "Project Root: $PROJECT_ROOT"
echo ""

# Set up Python path
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/ground_truth/scripts:$PROJECT_ROOT/experiments/docling_advanced/code:$PYTHONPATH"

# Change to experiments directory for config files
cd "$PROJECT_ROOT/experiments/docling_advanced"

# Run batch processor
python3 "$PROJECT_ROOT/ground_truth/scripts/process_hjorthagen_nds.py" 2>&1 | tee "$PROJECT_ROOT/ground_truth/batch_results/processing_log.txt"

echo ""
echo "✅ Processing complete!"
echo "Check results in: $PROJECT_ROOT/ground_truth/batch_results/"
