#!/usr/bin/env python3
"""
Mixed-Mode Extraction: Batch Test on 3 Additional Hybrid PDFs
=============================================================

Tests mixed-mode extraction on 3 low-coverage SRS PDFs to validate consistency.

Test Cases:
- brf_83301.pdf (12.0% baseline)
- brf_282765.pdf (13.7% baseline)
- brf_57125.pdf (14.5% baseline)

Expected: +10-20pp improvement if mixed-mode triggers
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

# Test cases with baseline coverage from Week 3 Day 4
TEST_CASES = [
    {
        "name": "brf_83301.pdf",
        "path": "SRS/brf_83301.pdf",
        "baseline_coverage": 12.0,
        "notes": "Machine-readable (100% text) but low extraction - potential hybrid"
    },
    {
        "name": "brf_282765.pdf",
        "path": "SRS/brf_282765.pdf",
        "baseline_coverage": 13.7,
        "notes": "Low coverage, likely hybrid structure"
    },
    {
        "name": "brf_57125.pdf",
        "path": "SRS/brf_57125.pdf",
        "baseline_coverage": 14.5,
        "notes": "Low coverage, Swedish governance terms failed"
    },
]

print("=" * 80)
print("MIXED-MODE EXTRACTION: BATCH VALIDATION TEST")
print("=" * 80)
print()
print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📄 Test Cases: {len(TEST_CASES)} PDFs")
print()

results = []

for i, test_case in enumerate(TEST_CASES, 1):
    print("=" * 80)
    print(f"TEST {i}/{len(TEST_CASES)}: {test_case['name']}")
    print("=" * 80)
    print()

    pdf_path = Path(__file__).parent / test_case['path']

    if not pdf_path.exists():
        print(f"❌ ERROR: PDF not found at {test_case['path']}")
        results.append({
            **test_case,
            "success": False,
            "error": "File not found"
        })
        print()
        continue

    print(f"📄 PDF: {test_case['name']}")
    print(f"📊 Baseline Coverage: {test_case['baseline_coverage']}%")
    print(f"📝 Notes: {test_case['notes']}")
    print()

    try:
        print("🚀 Running extraction with mixed-mode support...")
        result = extract_brf_to_pydantic(str(pdf_path), mode="fast")

        print(f"   ✓ Extraction complete")
        print()

        # Check if mixed-mode was used
        mixed_mode_used = False
        if hasattr(result, '_extraction_metadata') and result._extraction_metadata:
            if result._extraction_metadata.get('mode') == 'mixed':
                mixed_mode_used = True

        # Extract financial values
        financial_extracted = False
        financial_values = {}

        if result.financial:
            if result.financial.income_statement:
                income = result.financial.income_statement
                if income.revenue_total and income.revenue_total.value:
                    financial_values['revenue'] = income.revenue_total.value
                    financial_extracted = True
                if income.expenses_total and income.expenses_total.value:
                    financial_values['expenses'] = income.expenses_total.value
                    financial_extracted = True
                if income.result_after_tax and income.result_after_tax.value:
                    financial_values['net_income'] = income.result_after_tax.value
                    financial_extracted = True

            if result.financial.balance_sheet:
                balance = result.financial.balance_sheet
                if balance.assets_total and balance.assets_total.value:
                    financial_values['assets'] = balance.assets_total.value
                    financial_extracted = True
                if balance.liabilities_total and balance.liabilities_total.value:
                    financial_values['liabilities'] = balance.liabilities_total.value
                    financial_extracted = True
                if balance.equity_total and balance.equity_total.value:
                    financial_values['equity'] = balance.equity_total.value
                    financial_extracted = True

        # Calculate improvement
        new_coverage = result.coverage_percentage
        improvement = new_coverage - test_case['baseline_coverage']

        # Summarize
        print("📊 Results:")
        print(f"   Mixed-mode used: {'✅ YES' if mixed_mode_used else '❌ NO'}")
        print(f"   Coverage: {new_coverage:.1f}% (baseline: {test_case['baseline_coverage']}%)")
        print(f"   Improvement: {improvement:+.1f}pp")
        print(f"   Financial data extracted: {'✅ YES' if financial_extracted else '❌ NO'}")
        if financial_extracted:
            print(f"   Financial fields: {len(financial_values)}/6")
        print()

        # Verdict
        if improvement >= 15:
            verdict = "🎉 EXCELLENT: Significant improvement (≥15pp)"
        elif improvement >= 10:
            verdict = "✅ GOOD: Notable improvement (10-15pp)"
        elif improvement >= 5:
            verdict = "⚠️ MODERATE: Some improvement (5-10pp)"
        elif improvement > 0:
            verdict = "⚠️ MINIMAL: Small improvement (<5pp)"
        else:
            verdict = "❌ NO IMPROVEMENT: Coverage unchanged"

        print(f"🎯 Verdict: {verdict}")
        print()

        # Store results
        results.append({
            **test_case,
            "success": True,
            "new_coverage": new_coverage,
            "improvement": improvement,
            "mixed_mode_used": mixed_mode_used,
            "financial_extracted": financial_extracted,
            "financial_fields_count": len(financial_values),
            "financial_values": financial_values,
            "verdict": verdict
        })

    except Exception as e:
        print(f"❌ EXTRACTION FAILED: {str(e)}")
        results.append({
            **test_case,
            "success": False,
            "error": str(e)
        })
        print()

print()
print("=" * 80)
print("BATCH TEST SUMMARY")
print("=" * 80)
print()

successful = sum(1 for r in results if r.get('success', False))
mixed_mode_count = sum(1 for r in results if r.get('mixed_mode_used', False))
improved = sum(1 for r in results if r.get('improvement', 0) > 0)

print(f"📊 Overall Results:")
print(f"   Total PDFs: {len(results)}")
print(f"   Successful: {successful}/{len(results)}")
print(f"   Mixed-mode triggered: {mixed_mode_count}/{successful}")
print(f"   Showed improvement: {improved}/{successful}")
print()

if successful > 0:
    avg_improvement = sum(r.get('improvement', 0) for r in results if r.get('success', False)) / successful
    print(f"📈 Average Improvement: {avg_improvement:+.1f}pp")
    print()

    print("📋 Individual Results:")
    for r in results:
        if r.get('success'):
            status = "✅" if r.get('improvement', 0) >= 10 else "⚠️" if r.get('improvement', 0) >= 5 else "❌"
            mixed = "🔀" if r.get('mixed_mode_used') else "  "
            print(f"   {status} {mixed} {r['name']}: {r['baseline_coverage']}% → {r['new_coverage']:.1f}% ({r['improvement']:+.1f}pp)")
    print()

# Save detailed results
output_dir = Path(__file__).parent / "data" / "mixed_mode_batch_test"
output_dir.mkdir(parents=True, exist_ok=True)

results_file = output_dir / f"batch_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))

print(f"💾 Detailed results saved to: {results_file.name}")
print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()

# Final recommendation
if mixed_mode_count > 0 and avg_improvement >= 10:
    print("🎉 RECOMMENDATION: Mixed-mode extraction is working consistently!")
    print(f"   Triggered on {mixed_mode_count}/{successful} PDFs")
    print(f"   Average improvement: {avg_improvement:+.1f}pp")
    print("   ✅ Ready for production deployment")
elif mixed_mode_count > 0:
    print("⚠️ RECOMMENDATION: Mixed-mode triggers but improvement is variable")
    print("   May need further tuning for optimal results")
elif improved > 0:
    print("ℹ️ OBSERVATION: Improvement without mixed-mode triggering")
    print("   These PDFs may benefit from other optimization strategies")
else:
    print("❌ OBSERVATION: No improvement detected")
    print("   These PDFs may have different root causes than brf_76536")
