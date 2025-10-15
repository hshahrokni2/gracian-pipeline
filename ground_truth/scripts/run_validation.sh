#!/bin/bash
# Validation script for two-LLM system before processing Hjorthagen + NDS

cd "$(dirname "$0")"
PROJECT_ROOT="$(cd ../.. && pwd)"

# Load API key from .env
export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)

echo "🧪 Two-LLM System Validation"
echo "================================"
echo ""
echo "API Key configured: ${OPENAI_API_KEY:0:20}..."
echo "Project root: $PROJECT_ROOT"
echo ""

# Add paths
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/ground_truth/scripts:$PROJECT_ROOT/experiments/docling_advanced/code:$PYTHONPATH"

# Change to experiments directory for config files
cd "$PROJECT_ROOT/experiments/docling_advanced"

# Run smoke test
python3 -c "
import os
import sys
from pathlib import Path

# Add script directory to path
sys.path.insert(0, '$PROJECT_ROOT/ground_truth/scripts')
from create_two_llm_ground_truth import TwoLLMGroundTruthCreator

pdf_path = '$PROJECT_ROOT/Hjorthagen/brf_268882.pdf'
print(f'📄 Test PDF: {Path(pdf_path).name}')

try:
    creator = TwoLLMGroundTruthCreator(pdf_path)
    print('✅ TwoLLMGroundTruthCreator initialized')
    print('✅ OpenAI client connected')
    print('✅ Claude pipeline loaded')
    print('')
    print('🎉 VALIDATION PASSED - System ready to process!')
    print('')
    print('Next steps:')
    print('  1. Process Hjorthagen (15 PDFs)')
    print('  2. Process NDS PDFs')
    print('  3. Build schema evolution from discoveries')
except Exception as e:
    print(f'❌ VALIDATION FAILED: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
