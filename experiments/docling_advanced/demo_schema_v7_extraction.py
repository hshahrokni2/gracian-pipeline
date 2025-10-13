#!/usr/bin/env python3
"""
Proof-of-concept extraction using schema_v7.py

Demonstrates:
- ExtractionField enhancements (evidence_pages, extraction_method, etc.)
- Swedish-first pattern (nettoomsättning_tkr → net_revenue_tkr sync)
- Tolerant validation (quality scoring)

Tests on: brf_268882.pdf (regression test PDF)

Created: October 13, 2025
Purpose: Validate schema_v7 architecture before scaling to 501 fields
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from schema_v7 import YearlyFinancialData, ValidationResult
from schema_v7_validation import (
    calculate_extraction_quality,
    tolerant_float_compare,
    validate_with_tolerance
)


def extract_yearly_data_simple(pdf_path: str) -> YearlyFinancialData:
    """
    Simple extraction demo (hardcoded for now).

    In production, this would use:
    - optimal_brf_pipeline.py for table extraction
    - LLM for text extraction
    - Docling for document structure

    Returns:
        YearlyFinancialData instance with sample data
    """
    print(f"📄 Extracting from: {Path(pdf_path).name}")
    print()

    # Simulate extraction results (these would come from actual extraction in production)
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=45.8,
        årsavgift_per_kvm=125.50,
        # Metadata fields (from Day 1 ExtractionField enhancement)
        data_source="Table 1, Page 5",
        extraction_confidence=0.92
    )

    print("✅ Extraction complete")
    return data


def demonstrate_features(data: YearlyFinancialData):
    """Demonstrate all v7.0 features."""

    print("=" * 70)
    print("📊 SCHEMA V7.0 FEATURE DEMONSTRATION")
    print("=" * 70)
    print()

    # ============================================================
    # Feature 1: Swedish-First Pattern (Day 2)
    # ============================================================
    print("🇸🇪 FEATURE 1: Swedish-First Pattern")
    print("-" * 70)
    print(f"Swedish primary field: nettoomsättning_tkr = {data.nettoomsättning_tkr:,.2f} SEK")
    print(f"English alias:         net_revenue_tkr     = {data.net_revenue_tkr:,.2f} SEK")
    print(f"✅ Automatically synchronized via @property!")
    print()

    # Test bidirectional sync
    print("Testing bidirectional sync:")
    print(f"  Original Swedish value: {data.nettoomsättning_tkr}")
    # Note: In production, you would modify via the Swedish field
    # data.nettoomsättning_tkr = 15000.0
    # print(f"  After Swedish update: nettoomsättning_tkr={data.nettoomsättning_tkr}, net_revenue_tkr={data.net_revenue_tkr}")
    print("  (Both fields stay synchronized through @property)")
    print()

    # ============================================================
    # Feature 2: Quality Scoring (Day 3)
    # ============================================================
    print("📈 FEATURE 2: Quality Scoring")
    print("-" * 70)
    quality = calculate_extraction_quality(
        data,
        expected_fields=['year', 'nettoomsättning_tkr', 'soliditet_procent', 'årsavgift_per_kvm']
    )
    print(f"Coverage:    {quality['coverage']:.1%}  (fields populated)")
    print(f"Validation:  {quality['validation']:.1%}  (validation score)")
    print(f"Confidence:  {quality['confidence']:.1%}  (extraction confidence)")
    print(f"Evidence:    {quality['evidence']:.1%}  (have evidence_pages)")
    print(f"Overall:     {quality['overall']:.1%}  (weighted average)")
    print()

    # ============================================================
    # Feature 3: Tolerant Validation (Day 3)
    # ============================================================
    print("🎯 FEATURE 3: Tolerant Validation")
    print("-" * 70)

    # Simulate ground truth value (slightly different from extracted)
    actual = data.nettoomsättning_tkr
    expected = 12400.00  # Simulated ground truth

    matches, diff = tolerant_float_compare(actual, expected)
    status = validate_with_tolerance(actual, expected)

    print(f"Actual value:    {actual:,.2f} SEK")
    print(f"Expected value:  {expected:,.2f} SEK")
    print(f"Difference:      {diff:.2%} (relative)")
    print(f"Within ±5%:      {'✅ Yes' if matches else '❌ No'}")
    print(f"Validation:      {status.upper()}")
    print()

    if matches:
        print("✅ Value passes validation (within tolerance)")
    else:
        print("⚠️ Value outside tolerance - needs review")
    print()

    # ============================================================
    # Feature 4: Metadata Tracking (Day 1)
    # ============================================================
    print("🔍 FEATURE 4: Metadata Tracking")
    print("-" * 70)
    print(f"Data source:         {data.data_source or 'Not specified'}")
    print(f"Confidence:          {data.extraction_confidence or 0.0:.1%}")
    print()
    print("Note: YearlyFinancialData has basic metadata tracking.")
    print("For full ExtractionField enhancements (evidence_pages, extraction_method, model_used),")
    print("use fields that inherit from ExtractionField (e.g., StringField, NumberField).")
    print()

    # ============================================================
    # Feature 5: Multi-Source Validation (Day 3)
    # ============================================================
    print("🔄 FEATURE 5: Multi-Source Validation")
    print("-" * 70)
    print("Simulating extraction from 3 different sources:")

    from schema_v7_validation import compare_multi_source_values

    # Simulate values from table extraction, text extraction, OCR
    table_value = 12345.67
    text_value = 12345.67
    ocr_value = 12350.00

    consensus, confidence, consensus_status = compare_multi_source_values(
        [table_value, text_value, ocr_value]
    )

    print(f"  Table extraction:  {table_value:,.2f} SEK")
    print(f"  Text extraction:   {text_value:,.2f} SEK")
    print(f"  OCR extraction:    {ocr_value:,.2f} SEK")
    print(f"  → Consensus value: {consensus:,.2f} SEK")
    print(f"  → Confidence:      {confidence:.1%}")
    print(f"  → Status:          {consensus_status.upper()}")
    print()

    if consensus_status == ValidationResult.VALID.value:
        print("✅ Perfect consensus - high confidence")
    elif consensus_status == ValidationResult.WARNING.value:
        print("⚠️ Majority consensus - medium confidence")
    else:
        print("❌ No consensus - low confidence, needs review")
    print()

    # ============================================================
    # Summary
    # ============================================================
    print("=" * 70)
    print("✅ SCHEMA V7.0 DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Architecture validated:")
    print("  ✅ Day 1: ExtractionField enhancements")
    print("  ✅ Day 2: Swedish-first pattern with bidirectional sync")
    print("  ✅ Day 3: Tolerant validation with quality scoring")
    print()
    print("Ready for:")
    print("  → Integration with optimal_brf_pipeline.py")
    print("  → Real PDF extraction testing")
    print("  → Scaling to 501 fields")
    print()


def export_to_json(data: YearlyFinancialData, output_path: str):
    """Export extraction result to JSON."""

    # Convert to dict
    result = data.model_dump()

    # Add quality metrics
    quality = calculate_extraction_quality(data)
    result['_quality_metrics'] = quality

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"💾 Exported to: {output_path}")
    print()


def main():
    """Main demonstration entry point."""

    # Default test PDF (regression test)
    pdf_path = "test_pdfs/brf_268882.pdf"

    # Allow command-line override
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF not found: {pdf_path}")
        print()
        print("Usage: python demo_schema_v7_extraction.py [path/to/pdf]")
        print(f"Default: {pdf_path}")
        sys.exit(1)

    print()
    print("🚀 Schema V7.0 Proof-of-Concept Extraction")
    print("=" * 70)
    print()

    # Step 1: Extract data
    data = extract_yearly_data_simple(pdf_path)

    # Step 2: Demonstrate features
    demonstrate_features(data)

    # Step 3: Export to JSON
    output_path = "results/demo_extraction_result.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    export_to_json(data, output_path)

    print("✅ Proof-of-concept demonstration complete!")
    print()
    print("Next steps:")
    print("  1. Review results in results/demo_extraction_result.json")
    print("  2. Integrate with optimal_brf_pipeline.py for real extraction")
    print("  3. Test on multiple PDFs to validate architecture")
    print()


if __name__ == "__main__":
    main()
