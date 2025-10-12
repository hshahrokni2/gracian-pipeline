#!/usr/bin/env python3
"""
Full pipeline integration test with comprehensive logging.

Tests mixed-mode detection and vision extraction on brf_83301.pdf.

Expected:
- Detection triggers: empty_tables_detected_8of14
- Vision extraction runs on pages 9-12
- Coverage improves from 13.7% → 30-35%
"""
import sys
import os
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Verify API key
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not found in environment")
    print("Please set it in .env file or export it")
    sys.exit(1)

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

print("\n" + "="*80)
print("FULL PIPELINE INTEGRATION TEST")
print("="*80)
print("PDF: SRS/brf_83301.pdf")
print("Expected: Mixed-mode triggers, coverage improves 13.7% → 30-35%")
print("="*80 + "\n")

# Run extraction with all debug logging
try:
    result = extract_brf_to_pydantic('SRS/brf_83301.pdf', mode='fast')

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"Coverage: {result.coverage_percentage:.1f}%")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Fields extracted: {sum(1 for field_name in dir(result) if not field_name.startswith('_') and getattr(result, field_name) is not None)}")

    # Check financial fields specifically
    if result.financial:
        print("\nFinancial Data:")
        if result.financial.balance_sheet:
            bs = result.financial.balance_sheet
            print(f"  Assets: {bs.assets_total.value if bs.assets_total else 'Not extracted'}")
            print(f"  Liabilities: {bs.liabilities_total.value if bs.liabilities_total else 'Not extracted'}")
            print(f"  Equity: {bs.equity_total.value if bs.equity_total else 'Not extracted'}")
        if result.financial.income_statement:
            inc = result.financial.income_statement
            print(f"  Revenue: {inc.revenue_total.value if inc.revenue_total else 'Not extracted'}")
            print(f"  Expenses: {inc.expenses_total.value if inc.expenses_total else 'Not extracted'}")

    print("="*80 + "\n")

    # Validation
    if result.coverage_percentage >= 30:
        print("✅ SUCCESS: Coverage improved to expected range (30-35%)")
    elif result.coverage_percentage > 13.7:
        print(f"🟡 PARTIAL SUCCESS: Coverage improved from 13.7% to {result.coverage_percentage:.1f}% (expected 30-35%)")
    else:
        print(f"❌ FAIL: Coverage unchanged at {result.coverage_percentage:.1f}% (expected 30-35%)")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
