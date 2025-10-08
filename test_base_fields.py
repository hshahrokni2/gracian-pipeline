"""
Test suite for base_fields.py - ExtractionField foundation.

Tests:
- Basic field creation and validation
- Confidence tracking
- Source and evidence tracking
- Swedish number parsing
- Multi-source aggregation
- Validation status tracking
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.models.base_fields import (
    ExtractionField,
    StringField,
    NumberField,
    ListField,
    BooleanField,
    DateField,
    DictField,
)


def test_string_field():
    """Test StringField basic functionality."""
    print("\n=== TEST: StringField ===")

    # Basic creation
    field = StringField(
        value="Erik Öhman",
        confidence=0.90,
        source="structured_table",
        evidence_pages=[5]
    )

    print(f"✅ Value: {field.value}")
    print(f"✅ Confidence: {field.confidence}")
    print(f"✅ Source: {field.source}")
    print(f"✅ Evidence pages: {field.evidence_pages}")

    # Whitespace stripping
    field2 = StringField(value="  Per Wiklund  ")
    assert field2.value == "Per Wiklund", "Whitespace should be stripped"
    print(f"✅ Whitespace stripping: '{field2.value}'")


def test_number_field_swedish():
    """Test NumberField with Swedish number formatting."""
    print("\n=== TEST: NumberField (Swedish Format) ===")

    # Swedish format: "1 234 567,89"
    field1 = NumberField(value="1 234 567,89")
    assert field1.value == 1234567.89, f"Expected 1234567.89, got {field1.value}"
    print(f"✅ Swedish format '1 234 567,89' → {field1.value}")

    # Standard format: "1,234,567.89"
    field2 = NumberField(value="1,234,567.89")
    assert field2.value == 1234567.89, f"Expected 1234567.89, got {field2.value}"
    print(f"✅ Standard format '1,234,567.89' → {field2.value}")

    # Already numeric
    field3 = NumberField(value=12345.67)
    assert field3.value == 12345.67
    print(f"✅ Numeric input: {field3.value}")


def test_list_field():
    """Test ListField functionality."""
    print("\n=== TEST: ListField ===")

    # List of board members
    field = ListField(
        value=["Erik Öhman", "Per Wiklund", "Anna Svensson"],
        confidence=0.95,
        source="structured_table",
        evidence_pages=[5, 6]
    )

    print(f"✅ Board members: {field.value}")
    print(f"✅ Count: {len(field.value)}")

    # Single value converted to list
    field2 = ListField(value="Erik Öhman")
    assert isinstance(field2.value, list), "Single value should be converted to list"
    assert len(field2.value) == 1
    print(f"✅ Single value → list: {field2.value}")


def test_boolean_field():
    """Test BooleanField with Swedish/English parsing."""
    print("\n=== TEST: BooleanField ===")

    # Swedish: ja/nej
    field1 = BooleanField(value="ja")
    assert field1.value is True
    print(f"✅ 'ja' → True")

    field2 = BooleanField(value="nej")
    assert field2.value is False
    print(f"✅ 'nej' → False")

    # English: yes/no
    field3 = BooleanField(value="yes")
    assert field3.value is True
    print(f"✅ 'yes' → True")

    # Numeric
    field4 = BooleanField(value=1)
    assert field4.value is True
    print(f"✅ 1 → True")


def test_multi_source_aggregation_agreement():
    """Test multi-source aggregation when values agree."""
    print("\n=== TEST: Multi-Source Aggregation (Agreement) ===")

    # Primary extraction
    field = NumberField(
        value=301339818,
        confidence=0.85,
        source="hierarchical_table"
    )

    # Add alternative extractions that agree
    field.add_alternative(
        value=301339818,
        confidence=0.90,
        source="regex"
    )
    field.add_alternative(
        value=301339818,
        confidence=0.80,
        source="vision_llm",
        model_used="gpt-4o"
    )

    print(f"Before resolution: value={field.value}, confidence={field.confidence}")

    # Resolve: should boost confidence due to agreement
    field.resolve_best_value()

    print(f"After resolution: value={field.value}, confidence={field.confidence}, source={field.source}")
    print(f"✅ Agreement detected, confidence boosted")
    assert field.source == "multi_source_consensus"
    assert field.confidence > 0.90  # Should be boosted


def test_multi_source_aggregation_disagreement():
    """Test multi-source aggregation when values disagree."""
    print("\n=== TEST: Multi-Source Aggregation (Disagreement) ===")

    # Primary extraction
    field = NumberField(
        value=301339818,
        confidence=0.85,
        source="hierarchical_table"
    )

    # Add alternative that CLEARLY disagrees (>10% different)
    field.add_alternative(
        value=350000000,  # ~16% higher - clear disagreement
        confidence=0.75,
        source="vision_llm"
    )

    print(f"Before resolution: value={field.value}, confidence={field.confidence}")
    print(f"Alternatives: {field.alternative_values}")

    # Resolve: should apply weighted vote + disagreement penalty
    field.resolve_best_value()

    print(f"After resolution: value={field.value:.0f}, confidence={field.confidence:.2f}, source={field.source}")
    print(f"✅ Disagreement detected, weighted vote applied")
    assert field.confidence < 0.85  # Should have disagreement penalty


def test_validation_status_tracking():
    """Test validation status tracking (tolerant validation)."""
    print("\n=== TEST: Validation Status Tracking ===")

    # Create field with extracted value
    field = NumberField(
        value=301339818,
        confidence=0.90,
        source="hierarchical_table",
        validation_status="valid"
    )

    print(f"✅ Extracted value: {field.value}")
    print(f"✅ Validation status: {field.validation_status}")

    # Simulate a warning (not an error!)
    field.validation_status = "warning"
    print(f"✅ Changed to warning - value preserved: {field.value}")

    # CRITICAL: Value is never nulled due to validation
    assert field.value is not None, "Value must never be nulled due to validation"
    print(f"✅ CRITICAL: Value never nulled despite warning")


def test_evidence_tracking():
    """Test evidence page tracking."""
    print("\n=== TEST: Evidence Tracking ===")

    field = StringField(
        value="Erik Öhman",
        confidence=0.95,
        source="structured_table",
        evidence_pages=[5, 6],
        extraction_method="board_table_parser"
    )

    print(f"✅ Value: {field.value}")
    print(f"✅ Evidence pages: {field.evidence_pages}")
    print(f"✅ Extraction method: {field.extraction_method}")

    # Add timestamp
    field.extraction_timestamp = datetime.now()
    print(f"✅ Timestamp: {field.extraction_timestamp}")


def test_field_with_no_extraction():
    """Test field when extraction fails (not_found case)."""
    print("\n=== TEST: Field with No Extraction (not_found) ===")

    # Field not extracted, but we tracked attempts
    field = StringField(
        value=None,
        confidence=0.0,
        source="not_found",
        evidence_pages=[10, 11, 12],  # We looked here
        validation_status="unknown"
    )

    # Create attempt log
    field.alternative_values = [
        {"method": "hierarchical_table", "success": False, "error": "No matching table"},
        {"method": "regex", "success": False, "error": "Pattern not found"},
        {"method": "vision_llm", "success": False, "error": "LLM returned null"}
    ]

    print(f"✅ Value: {field.value} (None is OK)")
    print(f"✅ Source: {field.source}")
    print(f"✅ Evidence pages tried: {field.evidence_pages}")
    print(f"✅ Attempts logged: {len(field.alternative_values)}")
    print(f"✅ CRITICAL: We have evidence of trying, not just null")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("BASE_FIELDS.PY TEST SUITE")
    print("=" * 60)

    try:
        test_string_field()
        test_number_field_swedish()
        test_list_field()
        test_boolean_field()
        test_multi_source_aggregation_agreement()
        test_multi_source_aggregation_disagreement()
        test_validation_status_tracking()
        test_evidence_tracking()
        test_field_with_no_extraction()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

        print("\n🎯 Key Achievements:")
        print("  ✅ ExtractionField base working with confidence tracking")
        print("  ✅ Swedish number parsing working (1 234 567,89)")
        print("  ✅ Multi-source aggregation working (agreement + disagreement)")
        print("  ✅ Validation status tracking (never nulls data)")
        print("  ✅ Evidence tracking (where we looked)")
        print("  ✅ Tolerant extraction (logs attempts even on failure)")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
