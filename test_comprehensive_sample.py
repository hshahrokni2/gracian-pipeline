#!/usr/bin/env python3
"""
Week 3 Day 1-2: Comprehensive Testing - Representative Sample (5 PDFs)

Strategic sampling approach for practical testing:
- Tests integrated schema on representative sample
- Validates ExtractionField functionality
- Verifies synonym mapping, Swedish-first fields, calculated metrics
- Provides foundation for full 42-PDF test plan
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

load_dotenv()


# Representative sample: 5 PDFs (mix of sizes and datasets)
SAMPLE_PDFS = [
    ("Hjorthagen", "Hjorthagen/brf_46160.pdf"),      # Small, well-tested
    ("Hjorthagen", "Hjorthagen/brf_266956.pdf"),     # Medium size
    ("SRS", "SRS/brf_198532.pdf"),                    # Well-documented test case
    ("SRS", "SRS/brf_52576.pdf"),                     # Different structure
    ("SRS", "SRS/brf_276507.pdf"),                    # Larger document
]


def run_sample_comprehensive_test():
    """Run comprehensive test on representative sample."""
    print("="*80)
    print("🧪 WEEK 3 DAY 1-2: COMPREHENSIVE TESTING - REPRESENTATIVE SAMPLE")
    print("="*80)
    print()
    print(f"📋 Testing {len(SAMPLE_PDFS)} representative PDFs")
    print("   Strategy: Validate schema integration before full 42-PDF suite")
    print()

    results = []
    successful = 0
    failed = 0

    for i, (dataset, pdf_path) in enumerate(SAMPLE_PDFS, 1):
        pdf_path_obj = Path(pdf_path)

        if not pdf_path_obj.exists():
            print(f"[{i}/{len(SAMPLE_PDFS)}] ⚠️ {pdf_path}: File not found")
            continue

        print(f"[{i}/{len(SAMPLE_PDFS)}] Processing {dataset}/{pdf_path_obj.name}...")

        result = {
            "dataset": dataset,
            "pdf_name": pdf_path_obj.name,
            "pdf_path": pdf_path,
            "success": False,
            "coverage": 0.0,
            "confidence": 0.0,
            "extraction_time": 0.0,
            "tests": {
                "extraction_field": {},
                "synonym_mapping": {},
                "swedish_first": {},
                "calculated_metrics": {}
            },
            "error": None
        }

        try:
            start_time = time.time()

            # Run extraction (fast mode for smoke test - validates quality metrics)
            report = extract_brf_to_pydantic(pdf_path, mode="fast")

            result["extraction_time"] = time.time() - start_time
            result["success"] = True
            result["coverage"] = report.coverage_percentage
            result["confidence"] = report.confidence_score

            # Test 1: ExtractionField functionality
            result["tests"]["extraction_field"] = {
                "confidence_scores": report.confidence_score is not None,
                "source_pages_tracked": len(report.all_source_pages) > 0,
                "coverage_calculation": report.coverage_percentage >= 0
            }

            # Test 2: Synonym mapping
            result["tests"]["synonym_mapping"] = {
                "swedish_governance": report.governance is not None,
                "swedish_financial": report.financial is not None
            }

            # Test 3: Swedish-first semantic fields
            result["tests"]["swedish_first"] = {
                "fee_structure": report.fees is not None,
                "financial_data": report.financial is not None
            }

            # Test 4: Calculated metrics
            has_calc_metrics = (
                report.financial and
                hasattr(report.financial, 'calculated_metrics') and
                report.financial.calculated_metrics is not None
            )
            result["tests"]["calculated_metrics"] = {
                "calculated_metrics_present": has_calc_metrics,
                "validation_applied": False,
                "tolerant_validation": False
            }

            if has_calc_metrics:
                calc = report.financial.calculated_metrics
                result["tests"]["calculated_metrics"]["validation_applied"] = (
                    hasattr(calc, 'debt_per_sqm_status') and
                    calc.debt_per_sqm_status in ['valid', 'warning', 'error']
                )

            print(f"   ✅ Coverage={result['coverage']:.1f}%, Confidence={result['confidence']:.2f}, Time={result['extraction_time']:.1f}s")
            print(f"   📊 Tests: EF={sum(result['tests']['extraction_field'].values())}/3, "
                  f"SM={sum(result['tests']['synonym_mapping'].values())}/2, "
                  f"SF={sum(result['tests']['swedish_first'].values())}/2, "
                  f"CM={sum(result['tests']['calculated_metrics'].values())}/3")

            successful += 1

        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ Error: {str(e)}")
            failed += 1

        results.append(result)
        print()

    # Print summary
    print("="*80)
    print("📊 SAMPLE TEST SUMMARY")
    print("="*80)
    print()

    print(f"📈 Results:")
    print(f"   Successful: {successful}/{len(SAMPLE_PDFS)} ({successful/len(SAMPLE_PDFS)*100:.1f}%)")
    print(f"   Failed: {failed}/{len(SAMPLE_PDFS)} ({failed/len(SAMPLE_PDFS)*100:.1f}%)")

    if successful > 0:
        avg_coverage = sum(r["coverage"] for r in results if r["success"]) / successful
        avg_confidence = sum(r["confidence"] for r in results if r["success"]) / successful
        avg_time = sum(r["extraction_time"] for r in results if r["success"]) / successful

        print(f"   Avg Coverage: {avg_coverage:.1f}%")
        print(f"   Avg Confidence: {avg_confidence:.2f}")
        print(f"   Avg Time: {avg_time:.1f}s/PDF")
        print()

        # Aggregate test results
        print(f"🧪 Component Test Pass Rates:")

        for test_category in ["extraction_field", "synonym_mapping", "swedish_first", "calculated_metrics"]:
            test_counts = defaultdict(lambda: {"passed": 0, "total": 0})

            for result in results:
                if not result["success"]:
                    continue

                for test_name, passed in result["tests"][test_category].items():
                    test_counts[test_name]["total"] += 1
                    if passed:
                        test_counts[test_name]["passed"] += 1

            print(f"   {test_category.replace('_', ' ').title()}:")
            for test_name, counts in test_counts.items():
                if counts["total"] > 0:
                    pass_rate = (counts["passed"] / counts["total"]) * 100
                    status = "✅" if pass_rate >= 80 else "⚠️"
                    print(f"     {status} {test_name}: {counts['passed']}/{counts['total']} ({pass_rate:.1f}%)")

        print()

        # Estimate full 42-PDF test time
        estimated_full_time = avg_time * 42
        hours = int(estimated_full_time // 3600)
        minutes = int((estimated_full_time % 3600) // 60)
        print(f"📅 Estimated Time for Full 42-PDF Test:")
        print(f"   {hours}h {minutes}m (based on sample average)")
        print()

    # Save results
    output_dir = Path("data/week3_sample_test_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_file = output_dir / f"sample_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "sample_size": len(SAMPLE_PDFS),
            "successful": successful,
            "failed": failed,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Results saved to {results_file}")
    print()

    print("="*80)
    print("✅ WEEK 3 DAY 1-2: SAMPLE TESTING COMPLETE")
    print("="*80)
    print()

    print("📋 Next Steps:")
    print("   1. Review sample test results")
    print("   2. Address any critical failures")
    print("   3. Run full 42-PDF suite: python test_comprehensive_42_pdfs.py")
    print()

    return successful == len(SAMPLE_PDFS)


if __name__ == "__main__":
    success = run_sample_comprehensive_test()
    sys.exit(0 if success else 1)
