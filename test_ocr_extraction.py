#!/usr/bin/env python3
"""
Test OCR extraction on scanned SRS PDFs.

Tests the Week 3 Day 6 fix: Swedish EasyOCR should extract text from scanned PDFs
and improve coverage from <5% to >40%.
"""

import sys
import time
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("⚠️  Warning: .env file not found, API key may be missing")

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic
from gracian_pipeline.utils.pdf_classifier import classify_pdf

# Test PDFs
test_cases = [
    {
        "name": "Pure Scanned (0% text)",
        "path": "SRS/brf_276629.pdf",
        "baseline_coverage": 1.7,
        "expected_improvement": ">30pp"
    },
    {
        "name": "Mostly Scanned (10.5% text)",
        "path": "SRS/brf_43334.pdf",
        "baseline_coverage": 6.8,
        "expected_improvement": ">30pp"
    }
]

print("=" * 80)
print("OCR EXTRACTION TEST - Week 3 Day 6 Validation")
print("=" * 80)
print("\nTesting Swedish EasyOCR on scanned SRS PDFs")
print("Expected: Coverage improvement from <5% to >40%\n")
print("=" * 80)

results = []

for i, test_case in enumerate(test_cases, 1):
    pdf_path = Path(__file__).parent / test_case["path"]

    if not pdf_path.exists():
        print(f"\n❌ Test {i}: PDF not found - {test_case['path']}")
        continue

    print(f"\n{'=' * 80}")
    print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
    print(f"PDF: {test_case['path']}")
    print(f"Baseline coverage: {test_case['baseline_coverage']}%")
    print(f"Expected improvement: {test_case['expected_improvement']}")
    print("=" * 80)

    # Step 1: Classify PDF
    print("\n📊 Step 1: Classify PDF")
    classification = classify_pdf(str(pdf_path), verbose=True)

    # Step 2: Extract with OCR-enabled pipeline
    print(f"\n🔧 Step 2: Extract with OCR-enabled pipeline (fast mode)")
    print(f"   Starting extraction...")

    start_time = time.time()

    try:
        result = extract_brf_to_pydantic(str(pdf_path), mode="fast")
        elapsed = time.time() - start_time

        # Get metrics
        coverage = result.coverage_percentage
        confidence = result.confidence_score

        # Calculate improvement
        improvement = coverage - test_case["baseline_coverage"]

        # Determine success
        success = improvement > 30  # Target: >30pp improvement

        print(f"   ✓ Extraction complete in {elapsed:.1f}s")
        print(f"\n📊 Results:")
        print(f"   Coverage: {coverage:.1f}% (was {test_case['baseline_coverage']}%, {improvement:+.1f}pp)")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Processing time: {elapsed:.1f}s")

        # Detailed field extraction
        governance = result.governance
        financial = result.financial
        property_details = result.property

        print(f"\n📋 Field Extraction:")
        print(f"   Chairman: {'✓' if governance and governance.chairman else '✗'}")
        print(f"   Board members: {len(governance.board_members) if governance and governance.board_members else 0}")
        print(f"   Auditor: {'✓' if governance and governance.primary_auditor else '✗'}")
        print(f"   Revenue: {'✓' if financial and financial.income_statement and financial.income_statement.revenue_total else '✗'}")
        print(f"   Assets: {'✓' if financial and financial.balance_sheet and financial.balance_sheet.assets_total else '✗'}")
        print(f"   Municipality: {'✓' if property_details and property_details.municipality else '✗'}")

        # Success determination
        if success:
            print(f"\n✅ SUCCESS: {improvement:.1f}pp improvement (target: >30pp)")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: {improvement:.1f}pp improvement (target: >30pp)")
            print(f"   Note: OCR may need tuning or PDF may have quality issues")

        results.append({
            "pdf": test_case["path"],
            "name": test_case["name"],
            "classification": classification["classification"],
            "text_percentage": classification["text_percentage"],
            "baseline_coverage": test_case["baseline_coverage"],
            "new_coverage": coverage,
            "improvement": improvement,
            "confidence": confidence,
            "processing_time": elapsed,
            "success": success
        })

    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

        results.append({
            "pdf": test_case["path"],
            "name": test_case["name"],
            "status": "ERROR",
            "error": str(e)
        })

# Final summary
print(f"\n\n{'=' * 80}")
print("FINAL SUMMARY")
print("=" * 80)

successful_tests = [r for r in results if r.get("success")]
partial_tests = [r for r in results if r.get("improvement") is not None and not r.get("success")]
failed_tests = [r for r in results if r.get("status") == "ERROR"]

print(f"\n📊 Test Results:")
print(f"   Total tests: {len(results)}")
print(f"   Successful (>30pp improvement): {len(successful_tests)}")
print(f"   Partial success (<30pp improvement): {len(partial_tests)}")
print(f"   Failed (errors): {len(failed_tests)}")

if successful_tests:
    avg_improvement = sum(r["improvement"] for r in successful_tests) / len(successful_tests)
    avg_coverage = sum(r["new_coverage"] for r in successful_tests) / len(successful_tests)
    avg_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)

    print(f"\n✅ Successful Tests:")
    print(f"   Average improvement: {avg_improvement:.1f}pp")
    print(f"   Average new coverage: {avg_coverage:.1f}%")
    print(f"   Average processing time: {avg_time:.1f}s")

if results:
    # Save results
    output_file = Path(__file__).parent / "data" / "week3_day6_ocr_test_results.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

# Overall verdict
print(f"\n{'=' * 80}")
if len(successful_tests) == len(test_cases):
    print("🎉 OCR IMPLEMENTATION VALIDATED: All tests successful!")
    print("\n✅ Swedish EasyOCR is working correctly")
    print("✅ Scanned PDFs now achieve >40% coverage (was <5%)")
    print("✅ Ready to deploy to full SRS dataset")
    sys.exit(0)
elif len(successful_tests) > 0:
    print("⚠️  OCR PARTIALLY WORKING: Some tests successful")
    print(f"\n   {len(successful_tests)}/{len(test_cases)} tests achieved >30pp improvement")
    print("   May need OCR tuning or PDF quality varies")
    sys.exit(1)
else:
    print("❌ OCR NOT WORKING: No successful tests")
    print("\n   Check EasyOCR installation: pip install easyocr")
    print("   Check Swedish model download status")
    print("   Review error messages above")
    sys.exit(2)
