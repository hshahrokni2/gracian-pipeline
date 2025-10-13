#!/usr/bin/env python3
"""
Tests for Schema V7.0 Tolerant 3-Tier Validation System.

Tests comprehensive validation functionality:
- Tolerant comparison functions (float, string, date, list)
- Quality scoring functions (coverage, validation, extraction quality)
- Multi-source validation support
- Edge cases and error handling
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from schema_v7 import ValidationResult, YearlyFinancialData
from schema_v7_validation import (
    tolerant_float_compare,
    tolerant_string_compare,
    tolerant_date_compare,
    tolerant_list_compare,
    calculate_field_coverage,
    calculate_validation_score,
    calculate_extraction_quality,
    validate_with_tolerance,
    compare_multi_source_values
)


# ============================================================
# Test Tolerant Float Comparison (5 tests)
# ============================================================

def test_float_exact_match():
    """Test exact float match"""
    matches, diff = tolerant_float_compare(100.0, 100.0)
    assert matches is True
    assert diff == 0.0


def test_float_within_tolerance():
    """Test float within 5% tolerance"""
    matches, diff = tolerant_float_compare(12345.67, 12400.00)
    assert matches is True
    assert diff < 0.05  # Less than 5%


def test_float_exceeds_tolerance():
    """Test float exceeding 5% tolerance"""
    matches, diff = tolerant_float_compare(12345.67, 13000.00)
    assert matches is False
    assert diff > 0.05  # Greater than 5%


def test_float_near_zero():
    """Test float comparison near zero (absolute tolerance)"""
    matches, diff = tolerant_float_compare(0.001, 0.002)
    assert matches is True
    assert diff == 0.001


def test_float_none_handling():
    """Test None value handling for floats"""
    # Both None = match
    matches, diff = tolerant_float_compare(None, None)
    assert matches is True
    assert diff == 0.0

    # One None = no match
    matches, diff = tolerant_float_compare(100.0, None)
    assert matches is False
    assert diff == float('inf')


# ============================================================
# Test Tolerant String Comparison (5 tests)
# ============================================================

def test_string_exact_match():
    """Test exact string match"""
    matches, similarity = tolerant_string_compare("Test", "Test")
    assert matches is True
    assert similarity == 1.0


def test_string_whitespace_normalization():
    """Test string comparison with whitespace normalization"""
    matches, similarity = tolerant_string_compare("Rolf Johansson", "Rolf  Johansson")
    assert matches is True
    assert similarity >= 0.90


def test_string_punctuation_normalization():
    """Test string comparison with punctuation normalization"""
    matches, similarity = tolerant_string_compare("769606-2533", "769606 2533")
    assert matches is True
    assert similarity >= 0.90


def test_string_case_insensitive():
    """Test case-insensitive string comparison (default)"""
    matches, similarity = tolerant_string_compare("Test", "test")
    assert matches is True
    assert similarity == 1.0


def test_string_case_sensitive():
    """Test case-sensitive string comparison"""
    matches, similarity = tolerant_string_compare("Test", "test", case_sensitive=True)
    assert matches is False  # Different case
    assert similarity < 1.0


# ============================================================
# Test Tolerant Date Comparison (3 tests)
# ============================================================

def test_date_exact_match():
    """Test exact date match"""
    matches, diff = tolerant_date_compare("2024-01-15", "2024-01-15")
    assert matches is True
    assert diff == 0


def test_date_with_tolerance():
    """Test date comparison with tolerance"""
    matches, diff = tolerant_date_compare("2024-01-15", "2024-01-16", tolerance_days=1)
    assert matches is True
    assert diff == 1


def test_date_invalid_format():
    """Test date comparison with invalid format"""
    matches, diff = tolerant_date_compare("invalid", "2024-01-15")
    assert matches is False
    assert diff == 999999  # Error indicator


# ============================================================
# Test Tolerant List Comparison (4 tests)
# ============================================================

def test_list_exact_match_ordered():
    """Test exact list match (ordered)"""
    matches, similarity = tolerant_list_compare([1, 2, 3], [1, 2, 3], ordered=True)
    assert matches is True
    assert similarity == 1.0


def test_list_unordered_match():
    """Test list match with different order (unordered)"""
    matches, similarity = tolerant_list_compare([1, 2, 3], [3, 2, 1], ordered=False)
    assert matches is True
    assert similarity == 1.0


def test_list_ordered_mismatch():
    """Test list mismatch with different order (ordered)"""
    matches, similarity = tolerant_list_compare([1, 2, 3], [3, 2, 1], ordered=True)
    assert matches is False
    assert similarity < 1.0


def test_list_partial_overlap():
    """Test list with partial overlap"""
    matches, similarity = tolerant_list_compare([1, 2], [1, 2, 3], ordered=False)
    assert matches is False  # Not ≥90% similarity
    assert 0.6 < similarity < 0.7  # ~67% overlap


# ============================================================
# Test Field Coverage Calculation (3 tests)
# ============================================================

def test_field_coverage_full():
    """Test 100% field coverage"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=45.8,
        årsavgift_per_kvm=125.50
    )
    coverage = calculate_field_coverage(
        data,
        expected_fields=['year', 'nettoomsättning_tkr', 'soliditet_procent', 'årsavgift_per_kvm']
    )
    assert coverage == 1.0  # All 4 fields populated


def test_field_coverage_partial():
    """Test partial field coverage"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=None,  # Not populated
        årsavgift_per_kvm=None   # Not populated
    )
    coverage = calculate_field_coverage(
        data,
        expected_fields=['year', 'nettoomsättning_tkr', 'soliditet_procent', 'årsavgift_per_kvm']
    )
    assert coverage == 0.5  # 2 out of 4 fields populated


def test_field_coverage_empty():
    """Test zero field coverage"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=None,
        soliditet_procent=None,
        årsavgift_per_kvm=None
    )
    coverage = calculate_field_coverage(
        data,
        expected_fields=['nettoomsättning_tkr', 'soliditet_procent', 'årsavgift_per_kvm']
    )
    assert coverage == 0.0  # 0 out of 3 fields populated


# ============================================================
# Test Validation Score Calculation (3 tests)
# ============================================================

def test_validation_score_all_valid():
    """Test validation score with all VALID"""
    score = calculate_validation_score(["valid", "valid", "valid"])
    assert score == 1.0


def test_validation_score_mixed():
    """Test validation score with mixed statuses"""
    score = calculate_validation_score(["valid", "valid", "warning", "error"])
    assert score == 0.625  # (1.0 + 1.0 + 0.5 + 0.0) / 4


def test_validation_score_empty():
    """Test validation score with empty list"""
    score = calculate_validation_score([])
    assert score == 0.0


# ============================================================
# Test Extraction Quality Calculation (2 tests)
# ============================================================

def test_extraction_quality_basic():
    """Test extraction quality calculation"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=45.8
    )
    quality = calculate_extraction_quality(
        data,
        expected_fields=['year', 'nettoomsättning_tkr', 'soliditet_procent', 'årsavgift_per_kvm']
    )

    # Check that all quality metrics are present
    assert 'coverage' in quality
    assert 'validation' in quality
    assert 'confidence' in quality
    assert 'evidence' in quality
    assert 'overall' in quality

    # Check that coverage is correct (3 out of 4 fields)
    assert quality['coverage'] == 0.75

    # Overall score should be between 0 and 1
    assert 0.0 <= quality['overall'] <= 1.0


def test_extraction_quality_empty():
    """Test extraction quality with minimal data"""
    data = YearlyFinancialData(year=2024)
    quality = calculate_extraction_quality(data)

    # Should return low scores for empty data (year is populated, so coverage > 0)
    assert quality['coverage'] < 0.25  # Only year field populated
    assert quality['overall'] < 0.3  # Overall quality should be low


# ============================================================
# Test Validation with Tolerance (2 tests)
# ============================================================

def test_validate_within_tolerance():
    """Test validation within tolerance returns VALID"""
    result = validate_with_tolerance(100.0, 105.0, relative_tolerance=0.05)
    assert result == "valid"  # 5% difference, within tolerance


def test_validate_exceeds_tolerance():
    """Test validation exceeding tolerance returns ERROR"""
    result = validate_with_tolerance(100.0, 120.0, relative_tolerance=0.05)
    assert result == "error"  # 20% difference, exceeds tolerance


# ============================================================
# Test Multi-Source Value Comparison (2 tests)
# ============================================================

def test_multi_source_perfect_consensus():
    """Test multi-source comparison with perfect consensus"""
    value, confidence, status = compare_multi_source_values([100.0, 100.0, 100.0])
    assert value == 100.0
    assert confidence == 1.0
    assert status == "valid"


def test_multi_source_majority_consensus():
    """Test multi-source comparison with majority consensus"""
    value, confidence, status = compare_multi_source_values([100.0, 100.0, 105.0])
    assert value == 100.0
    # 2/3 agreement = 0.6666... which is ≥0.66 threshold
    assert confidence == pytest.approx(0.67, rel=0.01)
    assert status == "warning"  # Majority consensus (≥2/3)


# ============================================================
# Test Edge Cases (3 tests)
# ============================================================

def test_validation_result_enum():
    """Test ValidationResult enum values"""
    assert ValidationResult.VALID.value == "valid"
    assert ValidationResult.WARNING.value == "warning"
    assert ValidationResult.ERROR.value == "error"
    assert ValidationResult.UNKNOWN.value == "unknown"


def test_float_compare_boundary():
    """Test float comparison at exactly 5% boundary"""
    # Exactly 5% difference
    matches, diff = tolerant_float_compare(100.0, 105.0, relative_tolerance=0.05)
    assert matches is True
    assert diff <= 0.05


def test_string_compare_unicode():
    """Test string comparison with Swedish characters"""
    matches, similarity = tolerant_string_compare(
        "Årsavgift per kvm",
        "Årsavgift per kvm"
    )
    assert matches is True
    assert similarity == 1.0


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
