#!/usr/bin/env python3
"""
Quick validation test for semantic matcher fix - uses existing extraction results.
"""

import sys
import json
from pathlib import Path
from gracian_pipeline.validation.confidence_validator import ConfidenceBasedValidator

def test_semantic_fix():
    """Test semantic matcher fix on existing extraction results."""

    # Load existing extraction
    extraction_path = Path("data/raw_pdfs/extraction_results.json")
    with open(extraction_path) as f:
        extraction_data = json.load(f)

    # Get extraction for brf_198532.pdf
    pdf_key = "data/raw_pdfs/Hjorthagen/brf_198532.pdf"
    extraction = extraction_data.get(pdf_key)

    if not extraction:
        print(f"❌ No extraction found for {pdf_key}")
        return

    # Load ground truth
    gt_path = Path("ground_truth/brf_198532_comprehensive_ground_truth.json")
    with open(gt_path) as f:
        ground_truth = json.load(f)

    # Run validation
    print("=" * 80)
    print("SEMANTIC MATCHER FIX VALIDATION")
    print("=" * 80)
    print(f"\nTest Document: brf_198532.pdf")
    print(f"Extraction Structure: agent-based (governance_agent, financial_agent, etc.)")
    print(f"Ground Truth Structure: semantic (metadata, governance, property, etc.)")
    print("\n" + "-" * 80)

    validator = ConfidenceBasedValidator(numeric_tolerance=0.05)
    report = validator.validate(extraction, ground_truth)

    # Print results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"\n{report.summary()}")
    print("\n" + "=" * 80)

    # Compare with previous results
    print("\nCOMPARISON TO PREVIOUS SESSION:")
    print("-" * 80)
    print("BEFORE FIX: 3.3% coverage (6/172 fields matched)")
    print(f"AFTER FIX:  {report.coverage_percent:.1f}% coverage ({report.total_matched_fields}/{report.total_gt_fields} fields matched)")
    print()

    if report.coverage_percent > 40.0:
        print("✅ SUCCESS: Coverage > 40% (exceeded 40-60% target)")
    elif report.coverage_percent > 20.0:
        print("⚠️  PARTIAL SUCCESS: Coverage improved but below target")
    else:
        print("❌ UNEXPECTED: Coverage did not improve as expected - investigation needed")

    print("=" * 80)

    # Show matched fields
    matched_validations = [fv for fv in report.field_validations if fv.is_match]

    print("\nMATCHED FIELDS:")
    print("-" * 80)
    for i, field in enumerate(matched_validations[:10], 1):
        print(f"{i}. {field.canonical_name}")
        print(f"   GT: {field.gt_value}")
        print(f"   Extracted: {field.extracted_value}")
        print(f"   Status: {field.match_status} (combined confidence: {field.combined_confidence:.2f})")
        print(f"   Notes: {field.notes}")
        print()

    if len(matched_validations) > 10:
        print(f"... and {len(matched_validations) - 10} more matches")

    # Save detailed results
    output_path = Path("validation_report_after_fix.json")
    report_dict = {
        "coverage_percent": report.coverage_percent,
        "weighted_coverage": report.weighted_coverage,
        "accuracy_percent": report.accuracy_percent,
        "weighted_accuracy": report.weighted_accuracy,
        "total_gt_fields": report.total_gt_fields,
        "total_matched_fields": report.total_matched_fields,
        "matched_fields": [
            {
                "canonical_name": fv.canonical_name,
                "gt_value": str(fv.gt_value),
                "extracted_value": str(fv.extracted_value),
                "match_status": fv.match_status,
                "match_confidence": fv.match_confidence,
                "extraction_confidence": fv.extraction_confidence,
                "combined_confidence": fv.combined_confidence,
                "notes": fv.notes
            }
            for fv in matched_validations
        ],
        "summary": report.summary()
    }

    with open(output_path, "w") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Detailed results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    test_semantic_fix()
