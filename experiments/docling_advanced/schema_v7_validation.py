#!/usr/bin/env python3
"""
Validation utilities for Schema V7.0 tolerant 3-tier validation system.

Provides functions for:
- Tolerant comparison (floats, strings, dates, lists)
- Quality scoring (field coverage, validation score, overall extraction quality)
- Multi-source validation support

Version 7.0 - Created: October 13, 2025
"""

from typing import Any, List, Dict, Tuple, Callable, Optional
from datetime import datetime
import string
from difflib import SequenceMatcher
from pydantic import BaseModel

from schema_v7 import ValidationResult


# ============================================================
# Tolerant Comparison Functions
# ============================================================

def tolerant_float_compare(
    value1: Optional[float],
    value2: Optional[float],
    relative_tolerance: float = 0.05,  # ±5%
    absolute_tolerance: float = 0.01   # For values near zero
) -> Tuple[bool, float]:
    """
    Compare floats with configurable tolerance for real-world extraction variation.

    Args:
        value1: First float value (or None)
        value2: Second float value (or None)
        relative_tolerance: Relative tolerance (default 5%)
        absolute_tolerance: Absolute tolerance for near-zero values

    Returns:
        (matches: bool, difference: float)
            - matches: True if values are within tolerance
            - difference: Absolute or relative difference

    Examples:
        >>> tolerant_float_compare(12345.67, 12400.00)
        (True, 0.0044)  # 0.44% difference, within 5%

        >>> tolerant_float_compare(12345.67, 13000.00)
        (False, 0.0530)  # 5.30% difference, exceeds 5%

        >>> tolerant_float_compare(0.001, 0.002)
        (True, 0.001)  # Within absolute tolerance

        >>> tolerant_float_compare(None, None)
        (True, 0.0)  # Both None = match

        >>> tolerant_float_compare(100.0, None)
        (False, inf)  # One None = no match
    """
    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 0.0)
    if value1 is None or value2 is None:
        return (False, float('inf'))

    # Both zero or near-zero - use absolute comparison
    if abs(value1) < absolute_tolerance and abs(value2) < absolute_tolerance:
        diff = abs(value1 - value2)
        return (diff <= absolute_tolerance, diff)

    # One is zero, other is not
    if abs(value1) < absolute_tolerance or abs(value2) < absolute_tolerance:
        return (False, abs(value1 - value2))

    # Relative comparison
    diff_abs = abs(value1 - value2)
    diff_rel = diff_abs / max(abs(value1), abs(value2))
    return (diff_rel <= relative_tolerance, diff_rel)


def tolerant_string_compare(
    value1: Optional[str],
    value2: Optional[str],
    case_sensitive: bool = False,
    ignore_whitespace: bool = True,
    ignore_punctuation: bool = True
) -> Tuple[bool, float]:
    """
    Compare strings with normalization for OCR and format variations.

    Args:
        value1: First string value (or None)
        value2: Second string value (or None)
        case_sensitive: Whether to compare case-sensitively
        ignore_whitespace: Whether to normalize whitespace
        ignore_punctuation: Whether to remove punctuation

    Returns:
        (matches: bool, similarity: float)
            - matches: True if strings match (≥90% similarity after normalization)
            - similarity: Similarity score 0.0-1.0

    Normalization:
        - Lowercase (if not case_sensitive)
        - Strip/normalize whitespace
        - Remove punctuation (if ignore_punctuation)

    Examples:
        >>> tolerant_string_compare("Rolf Johansson", "Rolf  Johansson")
        (True, 1.0)  # Extra space normalized

        >>> tolerant_string_compare("769606-2533", "769606 2533")
        (True, 0.95)  # Hyphen/space difference

        >>> tolerant_string_compare("Chairman", "Ordförande")
        (False, 0.0)  # Different words

        >>> tolerant_string_compare("Test", "test", case_sensitive=True)
        (False, 0.5)  # Case difference matters

        >>> tolerant_string_compare(None, None)
        (True, 1.0)  # Both None = match
    """
    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 1.0)
    if value1 is None or value2 is None:
        return (False, 0.0)

    # Normalize
    s1, s2 = value1, value2

    if not case_sensitive:
        s1, s2 = s1.lower(), s2.lower()

    if ignore_whitespace:
        s1 = ' '.join(s1.split())  # Normalize multiple spaces to single
        s2 = ' '.join(s2.split())

    if ignore_punctuation:
        translator = str.maketrans('', '', string.punctuation)
        s1 = s1.translate(translator)
        s2 = s2.translate(translator)

    # Exact match after normalization
    if s1 == s2:
        return (True, 1.0)

    # Fuzzy match using SequenceMatcher
    similarity = SequenceMatcher(None, s1, s2).ratio()
    return (similarity >= 0.90, similarity)  # 90% threshold for "match"


def tolerant_date_compare(
    value1: Optional[str],  # ISO format YYYY-MM-DD
    value2: Optional[str],
    tolerance_days: int = 0
) -> Tuple[bool, int]:
    """
    Compare dates with optional day tolerance.

    Args:
        value1: First date string (ISO format YYYY-MM-DD) or None
        value2: Second date string (ISO format YYYY-MM-DD) or None
        tolerance_days: Number of days tolerance (default 0)

    Returns:
        (matches: bool, diff_days: int)
            - matches: True if dates match within tolerance
            - diff_days: Absolute difference in days (or 999999 if error)

    Examples:
        >>> tolerant_date_compare("2024-01-15", "2024-01-15")
        (True, 0)

        >>> tolerant_date_compare("2024-01-15", "2024-01-16")
        (False, 1)

        >>> tolerant_date_compare("2024-01-15", "2024-01-16", tolerance_days=1)
        (True, 1)

        >>> tolerant_date_compare("invalid", "2024-01-15")
        (False, 999999)  # Parse error

        >>> tolerant_date_compare(None, None)
        (True, 0)  # Both None = match
    """
    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 0)
    if value1 is None or value2 is None:
        return (False, 999999)

    try:
        date1 = datetime.fromisoformat(value1)
        date2 = datetime.fromisoformat(value2)
        diff_days = abs((date1 - date2).days)
        return (diff_days <= tolerance_days, diff_days)
    except (ValueError, TypeError):
        return (False, 999999)


def tolerant_list_compare(
    list1: Optional[List[Any]],
    list2: Optional[List[Any]],
    ordered: bool = False,
    element_compare_fn: Optional[Callable] = None
) -> Tuple[bool, float]:
    """
    Compare lists with optional ordering and custom element comparison.

    Args:
        list1: First list (or None)
        list2: Second list (or None)
        ordered: Whether order matters
        element_compare_fn: Optional custom comparison function

    Returns:
        (matches: bool, similarity: float)
            - matches: True if lists match (≥90% similarity)
            - similarity: Similarity score 0.0-1.0

    Examples:
        >>> tolerant_list_compare([1, 2, 3], [1, 2, 3])
        (True, 1.0)

        >>> tolerant_list_compare([1, 2, 3], [3, 2, 1], ordered=False)
        (True, 1.0)  # Order doesn't matter

        >>> tolerant_list_compare([1, 2, 3], [3, 2, 1], ordered=True)
        (False, 0.0)  # Order matters, mismatch

        >>> tolerant_list_compare([1, 2], [1, 2, 3])
        (False, 0.67)  # 2/3 overlap

        >>> tolerant_list_compare(None, None)
        (True, 1.0)  # Both None = match
    """
    # Handle None cases
    if list1 is None and list2 is None:
        return (True, 1.0)
    if list1 is None or list2 is None:
        return (False, 0.0)

    if len(list1) == 0 and len(list2) == 0:
        return (True, 1.0)

    if ordered:
        # Ordered comparison - must match element by element
        if len(list1) != len(list2):
            return (False, 0.0)

        if element_compare_fn:
            matches = sum(1 for a, b in zip(list1, list2) if element_compare_fn(a, b)[0])
        else:
            matches = sum(1 for a, b in zip(list1, list2) if a == b)

        similarity = matches / len(list1) if list1 else 0.0
        return (similarity == 1.0, similarity)
    else:
        # Unordered comparison - set-like
        set1, set2 = set(list1), set(list2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        similarity = intersection / union if union > 0 else 0.0
        return (similarity >= 0.90, similarity)  # 90% threshold


# ============================================================
# Quality Scoring Functions
# ============================================================

def calculate_field_coverage(
    data: BaseModel,
    expected_fields: Optional[List[str]] = None
) -> float:
    """
    Calculate field coverage (0.0-1.0) based on populated fields.

    Args:
        data: Pydantic model instance
        expected_fields: List of field names to check (None = all fields)

    Returns:
        Coverage ratio (populated fields / total fields)

    Example:
        >>> class TestModel(BaseModel):
        ...     field1: Optional[int] = None
        ...     field2: Optional[str] = None
        ...     field3: Optional[float] = None
        >>> model = TestModel(field1=10, field2="test", field3=None)
        >>> calculate_field_coverage(model)
        0.6666666666666666  # 2 out of 3 fields populated
    """
    if expected_fields is None:
        expected_fields = list(type(data).model_fields.keys())  # Use class, not instance

    populated = sum(1 for field in expected_fields if getattr(data, field, None) is not None)
    return populated / len(expected_fields) if expected_fields else 0.0


def calculate_validation_score(
    validation_statuses: List[str]
) -> float:
    """
    Calculate validation score (0.0-1.0) from validation_status values.

    Scoring:
        - VALID: 1.0
        - WARNING: 0.5
        - ERROR: 0.0
        - UNKNOWN: 0.0

    Args:
        validation_statuses: List of validation status strings

    Returns:
        Average validation score

    Example:
        >>> calculate_validation_score(["valid", "valid", "warning", "error"])
        0.625  # (1.0 + 1.0 + 0.5 + 0.0) / 4
    """
    score_map = {
        ValidationResult.VALID.value: 1.0,
        ValidationResult.WARNING.value: 0.5,
        ValidationResult.ERROR.value: 0.0,
        ValidationResult.UNKNOWN.value: 0.0,
        "valid": 1.0,
        "warning": 0.5,
        "error": 0.0,
        "unknown": 0.0
    }

    if not validation_statuses:
        return 0.0

    scores = [score_map.get(status, 0.0) for status in validation_statuses]
    return sum(scores) / len(scores)


def calculate_extraction_quality(
    data: BaseModel,
    expected_fields: Optional[List[str]] = None,
    field_weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive extraction quality metrics.

    Args:
        data: Pydantic model with ExtractionField fields
        expected_fields: Fields to evaluate (None = all)
        field_weights: Importance weights for fields (None = equal weights)

    Returns:
        {
            'coverage': 0.70,        # 70% fields populated
            'validation': 0.85,      # 85% validation score
            'confidence': 0.92,      # 92% average confidence
            'evidence': 0.80,        # 80% have evidence_pages
            'overall': 0.82          # Weighted average
        }

    Example:
        >>> from schema_v7 import YearlyFinancialData
        >>> data = YearlyFinancialData(
        ...     year=2024,
        ...     nettoomsättning_tkr=12345.67,
        ...     soliditet_procent=45.8
        ... )
        >>> quality = calculate_extraction_quality(data)
        >>> quality['coverage']  # Will be > 0 since some fields populated
        0.2  # 2 out of 10 Swedish fields populated
    """
    if expected_fields is None:
        expected_fields = list(type(data).model_fields.keys())  # Use class, not instance

    # Coverage score
    coverage = calculate_field_coverage(data, expected_fields)

    # Validation score
    validation_statuses = []
    confidence_scores = []
    evidence_counts = 0
    total_fields = 0

    for field_name in expected_fields:
        field_value = getattr(data, field_name, None)

        if field_value is not None:
            total_fields += 1

            # Check if field has ExtractionField structure
            if hasattr(field_value, 'validation_status'):
                validation_statuses.append(field_value.validation_status or "unknown")

            if hasattr(field_value, 'confidence'):
                confidence_scores.append(field_value.confidence)

            if hasattr(field_value, 'evidence_pages') and field_value.evidence_pages:
                evidence_counts += 1

    validation_score = calculate_validation_score(validation_statuses) if validation_statuses else 0.0
    confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    evidence_score = evidence_counts / total_fields if total_fields > 0 else 0.0

    # Overall score (weighted average)
    overall = (
        coverage * 0.30 +      # 30% weight on coverage
        validation_score * 0.30 +  # 30% weight on validation
        confidence_score * 0.25 +  # 25% weight on confidence
        evidence_score * 0.15      # 15% weight on evidence
    )

    return {
        'coverage': coverage,
        'validation': validation_score,
        'confidence': confidence_score,
        'evidence': evidence_score,
        'overall': overall
    }


# ============================================================
# Utility Functions
# ============================================================

def validate_with_tolerance(
    actual: float,
    expected: float,
    relative_tolerance: float = 0.05,
    absolute_tolerance: float = 0.01
) -> str:
    """
    Validate a numeric value against expected with tolerance.

    Returns ValidationResult string ("valid", "warning", "error").

    Args:
        actual: Actual extracted value
        expected: Expected value (from ground truth)
        relative_tolerance: Relative tolerance (±5%)
        absolute_tolerance: Absolute tolerance for near-zero

    Returns:
        "valid", "warning", or "error"

    Example:
        >>> validate_with_tolerance(100.0, 105.0, relative_tolerance=0.05)
        'valid'  # 5% difference, within tolerance

        >>> validate_with_tolerance(100.0, 120.0, relative_tolerance=0.05)
        'error'  # 20% difference, exceeds tolerance
    """
    matches, diff = tolerant_float_compare(actual, expected, relative_tolerance, absolute_tolerance)

    if matches:
        return ValidationResult.VALID.value
    elif diff < relative_tolerance * 2:  # Within 2x tolerance = warning
        return ValidationResult.WARNING.value
    else:
        return ValidationResult.ERROR.value


def compare_multi_source_values(
    values: List[Any],
    comparison_fn: Optional[Callable] = None
) -> Tuple[Any, float, str]:
    """
    Compare values from multiple sources and determine consensus.

    Args:
        values: List of values from different sources
        comparison_fn: Optional custom comparison function

    Returns:
        (consensus_value, confidence, validation_status)

    Logic:
        - If all values match → HIGH confidence, VALID
        - If majority matches → MEDIUM confidence, WARNING
        - If no consensus → LOW confidence, ERROR

    Example:
        >>> compare_multi_source_values([100.0, 100.0, 105.0])
        (100.0, 0.67, 'warning')  # 2/3 agree on 100.0
    """
    if not values:
        return (None, 0.0, ValidationResult.UNKNOWN.value)

    # Use provided comparison function or default
    if comparison_fn is None:
        comparison_fn = lambda a, b: (a == b, 1.0 if a == b else 0.0)

    # Count occurrences
    from collections import Counter
    counter = Counter(values)
    most_common_value, most_common_count = counter.most_common(1)[0]

    # Calculate confidence and status
    agreement_ratio = most_common_count / len(values)

    if agreement_ratio == 1.0:
        # Perfect consensus
        confidence = 1.0
        status = ValidationResult.VALID.value
    elif agreement_ratio >= 0.66:  # ≥2/3 (0.6666...)
        # Majority consensus (≥2/3)
        confidence = agreement_ratio
        status = ValidationResult.WARNING.value
    else:
        # No clear consensus
        confidence = agreement_ratio
        status = ValidationResult.ERROR.value

    return (most_common_value, confidence, status)
