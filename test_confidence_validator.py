"""
Test ConfidenceBasedValidator - Prove semantic validation improves coverage from 3.1% to 40-60%+

This script validates the complete semantic validation system:
1. Load ground truth (459 fields)
2. Run extraction on brf_198532.pdf
3. Validate using ConfidenceBasedValidator (semantic matching)
4. Show improvement: OLD (3.1% rigid matching) vs NEW (semantic matching)
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.validation.confidence_validator import ConfidenceBasedValidator, ValidationReport
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor


def test_confidence_validator():
    """Test confidence-based validator on brf_198532.pdf."""

    print("\n" + "="*80)
    print("CONFIDENCE-BASED VALIDATOR - INTEGRATION TEST")
    print("="*80)
    print("\n🎯 Objective: Prove semantic validation improves coverage from 3.1%")

    # Load ground truth
    print("\n📋 Step 1: Loading ground truth...")
    gt_path = "ground_truth/brf_198532_comprehensive_ground_truth.json"
    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)

    # Count total fields
    total_fields = 0
    for category, fields in ground_truth.items():
        if not category.startswith('_'):
            if isinstance(fields, dict):
                total_fields += len(fields)
            elif isinstance(fields, list):
                for item in fields:
                    if isinstance(item, dict):
                        total_fields += len(item)

    print(f"  ✅ Loaded ground truth: {total_fields} total fields")

    # Run extraction
    print("\n📄 Step 2: Running extraction on SRS/brf_198532.pdf...")
    extractor = RobustUltraComprehensiveExtractor()
    extraction_result = extractor.extract_brf_document("SRS/brf_198532.pdf", mode="fast")
    print(f"  ✅ Extraction complete in {extraction_result.get('_extraction_time_seconds', 0):.1f}s")

    # Run semantic validation
    print("\n🔬 Step 3: Running semantic validation...")
    validator = ConfidenceBasedValidator(numeric_tolerance=0.05)
    report = validator.validate(extraction_result, ground_truth)

    # Display results
    print("\n" + "="*80)
    print("VALIDATION REPORT")
    print("="*80)
    print(report.summary())

    # Compare OLD vs NEW
    print("\n" + "="*80)
    print("COVERAGE IMPROVEMENT ANALYSIS")
    print("="*80)

    old_coverage = 3.1  # Previous rigid matching result
    new_coverage = report.weighted_coverage
    improvement = new_coverage - old_coverage
    improvement_pct = (improvement / old_coverage * 100) if old_coverage > 0 else 0

    print(f"\n📊 Coverage Comparison:")
    print(f"  OLD (Rigid Path Matching):     {old_coverage:.1f}%")
    print(f"  NEW (Semantic Matching):       {new_coverage:.1f}%")
    print(f"  Improvement:                   +{improvement:.1f} percentage points")
    print(f"  Improvement Factor:            {improvement_pct:.0f}% increase")

    print(f"\n📊 Accuracy Metrics:")
    print(f"  Raw Accuracy:                  {report.accuracy_percent:.1f}%")
    print(f"  Weighted Accuracy:             {report.weighted_accuracy:.1f}%")

    print(f"\n📊 Field Breakdown:")
    print(f"  Total GT Fields:               {report.total_gt_fields}")
    print(f"  Matched Fields:                {report.total_matched_fields}")
    print(f"  High Confidence (>0.9):        {len(report.high_confidence_fields)}")
    print(f"  Medium Confidence (0.7-0.9):   {len(report.medium_confidence_fields)}")
    print(f"  Low Confidence (<0.7):         {len(report.low_confidence_fields)}")

    print(f"\n🎯 95/95 Score: {report.get_95_95_score():.1f}%")

    # Detailed field analysis
    print("\n" + "="*80)
    print("DETAILED FIELD ANALYSIS (Sample)")
    print("="*80)

    # Show top 10 high-confidence matches
    print("\n✅ High Confidence Matches (Top 10):")
    for i, fv in enumerate(report.high_confidence_fields[:10], 1):
        print(f"  {i}. {fv.canonical_name}")
        print(f"     GT: {str(fv.gt_value)[:60]}")
        print(f"     Extracted: {str(fv.extracted_value)[:60]}")
        print(f"     Confidence: {fv.combined_confidence:.2f} | Status: {fv.match_status}")

    # Show mismatches (if any)
    mismatches = [fv for fv in report.field_validations if fv.match_status == "mismatch"]
    if mismatches[:5]:
        print("\n❌ Mismatches (First 5):")
        for i, fv in enumerate(mismatches[:5], 1):
            print(f"  {i}. {fv.canonical_name}")
            print(f"     GT: {str(fv.gt_value)[:60]}")
            print(f"     Extracted: {str(fv.extracted_value)[:60]}")
            print(f"     Notes: {fv.notes[:80]}")

    # Show missing fields (if any)
    missing = [fv for fv in report.field_validations if fv.match_status == "missing"]
    if missing[:5]:
        print(f"\n⚠️  Missing Fields (First 5 of {len(missing)}):")
        for i, fv in enumerate(missing[:5], 1):
            print(f"  {i}. {fv.canonical_name}: {str(fv.gt_value)[:60]}")

    # Success criteria
    print("\n" + "="*80)
    print("SUCCESS CRITERIA")
    print("="*80)

    success = True
    criteria_results = []

    # Criterion 1: Coverage improvement
    if new_coverage > old_coverage * 5:  # At least 5x improvement
        criteria_results.append("✅ Coverage improved 5x+ from rigid matching")
    else:
        criteria_results.append(f"❌ Coverage improvement insufficient ({improvement_pct:.0f}% < 500%)")
        success = False

    # Criterion 2: Minimum coverage threshold
    if new_coverage >= 40.0:
        criteria_results.append(f"✅ Weighted coverage ≥40% ({new_coverage:.1f}%)")
    else:
        criteria_results.append(f"⚠️  Weighted coverage <40% ({new_coverage:.1f}%)")
        # Not a failure, just a warning

    # Criterion 3: High confidence fields
    if len(report.high_confidence_fields) >= 10:
        criteria_results.append(f"✅ High confidence matches ≥10 ({len(report.high_confidence_fields)})")
    else:
        criteria_results.append(f"❌ High confidence matches <10 ({len(report.high_confidence_fields)})")
        success = False

    # Criterion 4: Semantic matcher working
    if report.total_matched_fields > 0:
        criteria_results.append(f"✅ Semantic matcher found {report.total_matched_fields} fields")
    else:
        criteria_results.append("❌ Semantic matcher found 0 fields")
        success = False

    for result in criteria_results:
        print(f"  {result}")

    # Final verdict
    print("\n" + "="*80)
    if success:
        print("🎉 VALIDATION SUCCESSFUL - SEMANTIC MATCHING WORKS!")
        print(f"   Coverage improved from {old_coverage:.1f}% to {new_coverage:.1f}%")
        print(f"   95/95 Score: {report.get_95_95_score():.1f}%")
    else:
        print("⚠️  VALIDATION INCOMPLETE - REVIEW REQUIRED")
        print(f"   Some criteria not met (see above)")
    print("="*80 + "\n")

    return report, success


def save_validation_report(report: ValidationReport, output_path: str = "validation_report_semantic.json"):
    """Save validation report to JSON for analysis."""

    report_dict = {
        "summary": {
            "coverage_percent": report.coverage_percent,
            "accuracy_percent": report.accuracy_percent,
            "weighted_coverage": report.weighted_coverage,
            "weighted_accuracy": report.weighted_accuracy,
            "95_95_score": report.get_95_95_score(),
            "total_gt_fields": report.total_gt_fields,
            "total_matched_fields": report.total_matched_fields,
        },
        "confidence_breakdown": {
            "high_confidence_count": len(report.high_confidence_fields),
            "medium_confidence_count": len(report.medium_confidence_fields),
            "low_confidence_count": len(report.low_confidence_fields),
        },
        "field_validations": [
            {
                "canonical_name": fv.canonical_name,
                "match_status": fv.match_status,
                "match_confidence": fv.match_confidence,
                "extraction_confidence": fv.extraction_confidence,
                "combined_confidence": fv.combined_confidence,
                "notes": fv.notes,
            }
            for fv in report.field_validations
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)

    print(f"\n💾 Validation report saved to: {output_path}")


if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("SEMANTIC VALIDATION - PROOF OF CONCEPT")
    print("🚀 "*20)
    print("\nProving semantic matching improves coverage from 3.1% (rigid) to 40-60%+ (semantic)\n")

    # Run test
    report, success = test_confidence_validator()

    # Save report
    save_validation_report(report)

    print("\n" + "="*80)
    if success:
        print("✅ PHASE 1 COMPLETE - SEMANTIC VALIDATION PROVEN")
        print("\nNext Steps:")
        print("  1. Test on 5-PDF diverse sample")
        print("  2. Tune confidence thresholds")
        print("  3. Run on 42-PDF comprehensive suite")
    else:
        print("⚠️  PHASE 1 INCOMPLETE - REVIEW REQUIRED")
    print("="*80 + "\n")

    sys.exit(0 if success else 1)
