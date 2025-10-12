"""
Confidence-Based Validator - Validates extraction with semantic matching and confidence weighting.

This module provides realistic validation metrics for heterogeneous PDFs by:
1. Using SemanticFieldMatcher to find fields by meaning (not exact path)
2. Calculating confidence-weighted coverage and accuracy
3. Categorizing results by confidence tier (high/medium/low)
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import re

from .semantic_matcher import SemanticFieldMatcher


@dataclass
class FieldValidation:
    """Result of validating a single field."""
    canonical_name: str
    gt_value: Any
    extracted_value: Any
    match_confidence: float  # 0.0-1.0 (from semantic matcher)
    extraction_confidence: float  # 0.0-1.0 (from extraction metadata)
    match_status: str  # "exact", "fuzzy", "semantic", "missing", "mismatch"
    notes: str = ""

    @property
    def combined_confidence(self) -> float:
        """Combined confidence score."""
        return (self.match_confidence + self.extraction_confidence) / 2.0

    @property
    def is_match(self) -> bool:
        """Whether this is considered a match."""
        return self.match_status in ["exact", "fuzzy", "semantic"]


@dataclass
class ValidationReport:
    """Comprehensive validation report with confidence metrics."""
    # Raw metrics
    coverage_percent: float  # Traditional: extracted / ground_truth
    accuracy_percent: float  # Traditional: correct / extracted

    # Confidence-weighted metrics (NEW)
    weighted_coverage: float  # Confidence-weighted coverage
    weighted_accuracy: float  # Confidence-weighted accuracy

    # Field-level results
    field_validations: List[FieldValidation]

    # Categorized results
    high_confidence_fields: List[FieldValidation]  # >0.9
    medium_confidence_fields: List[FieldValidation]  # 0.7-0.9
    low_confidence_fields: List[FieldValidation]  # <0.7

    # Statistics
    total_gt_fields: int
    total_extracted_fields: int
    total_matched_fields: int

    def summary(self) -> str:
        """Human-readable summary."""
        return f"""
Validation Report Summary:
==========================
Coverage: {self.coverage_percent:.1f}% (raw), {self.weighted_coverage:.1f}% (weighted)
Accuracy: {self.accuracy_percent:.1f}% (raw), {self.weighted_accuracy:.1f}% (weighted)

Field Breakdown:
  Total GT fields: {self.total_gt_fields}
  Matched fields: {self.total_matched_fields}
  High confidence (>0.9): {len(self.high_confidence_fields)}
  Medium confidence (0.7-0.9): {len(self.medium_confidence_fields)}
  Low confidence (<0.7): {len(self.low_confidence_fields)}

95/95 Score: {self.get_95_95_score():.1f}%
"""

    def get_95_95_score(self) -> float:
        """
        Calculate 95/95 score using confidence-weighted metrics.

        Formula: (weighted_coverage + weighted_accuracy) / 2
        """
        return (self.weighted_coverage + self.weighted_accuracy) / 2.0


class ConfidenceBasedValidator:
    """
    Validates extraction using semantic matching + confidence scoring.

    Key Features:
    - Uses SemanticFieldMatcher to find fields by meaning
    - Calculates confidence-weighted metrics
    - Handles heterogeneous data gracefully
    """

    def __init__(self, numeric_tolerance: float = 0.05):
        """
        Initialize validator.

        Args:
            numeric_tolerance: Tolerance for numeric comparisons (default 5%)
        """
        self.matcher = SemanticFieldMatcher()
        self.numeric_tolerance = numeric_tolerance

    def validate(self, extraction: Dict, ground_truth: Dict) -> ValidationReport:
        """
        Validate extraction against ground truth using semantic matching.

        Args:
            extraction: Extraction result dictionary
            ground_truth: Ground truth dictionary

        Returns:
            ValidationReport with confidence-weighted metrics
        """
        # Flatten ground truth to get all canonical field names
        gt_flat = self._flatten_ground_truth(ground_truth)

        # Validate each ground truth field
        field_validations = []

        for canonical_name, gt_value in gt_flat.items():
            validation = self._validate_field(canonical_name, gt_value, extraction)
            field_validations.append(validation)

        # Calculate metrics
        return self._build_report(field_validations, len(gt_flat))

    def _flatten_ground_truth(self, gt: Dict) -> Dict[str, Any]:
        """
        Extract fields from ground truth preserving nested structures.

        Handles:
        - Top-level categories (metadata, governance, etc.)
        - Nested dicts (keep field names)
        - Lists of items (keep as lists for semantic comparison)

        Note: This does NOT flatten lists into separate fields (that creates
        unmatchable field names like 'commercial_tenants_0_name'). Instead,
        we keep lists intact and let the semantic matcher handle them.
        """
        flat = {}

        # Skip metadata fields (start with _)
        for category, fields in gt.items():
            if category.startswith('_'):
                continue

            if isinstance(fields, dict):
                # Extract dict fields directly
                for field_name, field_value in fields.items():
                    flat[field_name] = field_value
            elif isinstance(fields, list):
                # Keep list as a whole (don't flatten individual items)
                # The semantic matcher will try to find this list field
                flat[category] = fields

        return flat

    def _validate_field(self, canonical_name: str, gt_value: Any, extraction: Dict) -> FieldValidation:
        """Validate a single field using semantic matching."""

        # Use semantic matcher to find field
        found_value, match_confidence = self.matcher.find_field(extraction, canonical_name)

        if found_value is None:
            # Field not found
            return FieldValidation(
                canonical_name=canonical_name,
                gt_value=gt_value,
                extracted_value=None,
                match_confidence=0.0,
                extraction_confidence=0.0,
                match_status="missing",
                notes="Field not found in extraction"
            )

        # Extract actual value (handle ExtractionField wrapper)
        if isinstance(found_value, dict):
            actual_value = found_value.get('value', found_value)
            extraction_confidence = found_value.get('confidence', 1.0)
        else:
            actual_value = found_value
            extraction_confidence = 1.0

        # Compare values
        match_status, notes = self._compare_values(gt_value, actual_value, canonical_name)

        return FieldValidation(
            canonical_name=canonical_name,
            gt_value=gt_value,
            extracted_value=actual_value,
            match_confidence=match_confidence,
            extraction_confidence=extraction_confidence,
            match_status=match_status,
            notes=notes
        )

    def _compare_values(self, gt_value: Any, extracted_value: Any, field_name: str) -> Tuple[str, str]:
        """
        Compare ground truth value with extracted value.

        Returns:
            (match_status, notes) tuple
            match_status: "exact", "fuzzy", "semantic", "mismatch"
        """
        # Handle None/null
        if gt_value is None and extracted_value is None:
            return "exact", "Both null"
        if gt_value is None or extracted_value is None:
            return "mismatch", f"One is null: GT={gt_value}, Extracted={extracted_value}"

        # Numeric comparison
        if isinstance(gt_value, (int, float, Decimal)) and isinstance(extracted_value, (int, float, Decimal)):
            gt_num = float(gt_value)
            ext_num = float(extracted_value)

            if gt_num == ext_num:
                return "exact", "Exact numeric match"

            # Check tolerance
            if gt_num == 0:
                diff_pct = abs(ext_num)
            else:
                diff_pct = abs(ext_num - gt_num) / abs(gt_num)

            if diff_pct <= self.numeric_tolerance:
                return "fuzzy", f"Within tolerance ({diff_pct*100:.1f}%)"
            else:
                return "mismatch", f"Outside tolerance ({diff_pct*100:.1f}% > {self.numeric_tolerance*100:.1f}%)"

        # String comparison
        if isinstance(gt_value, str) and isinstance(extracted_value, str):
            gt_norm = self._normalize_string(gt_value)
            ext_norm = self._normalize_string(extracted_value)

            if gt_norm == ext_norm:
                return "exact", "Exact string match (normalized)"

            # Check if one contains the other
            if gt_norm in ext_norm or ext_norm in gt_norm:
                return "semantic", "Partial string match"

            # Check fuzzy similarity
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, gt_norm, ext_norm).ratio()
            if similarity > 0.8:
                return "fuzzy", f"Fuzzy match (similarity={similarity:.2f})"

            return "mismatch", f"String mismatch: '{gt_value[:30]}...' vs '{extracted_value[:30]}...'"

        # List comparison (enhanced for nested structures)
        if isinstance(gt_value, list) and isinstance(extracted_value, list):
            if len(gt_value) != len(extracted_value):
                return "fuzzy", f"List length differs: {len(gt_value)} vs {len(extracted_value)}"

            # Empty lists
            if len(gt_value) == 0:
                return "exact", "Both empty lists"

            # Compare list items
            if all(isinstance(item, dict) for item in gt_value) and all(isinstance(item, dict) for item in extracted_value):
                # Lists of dicts: compare each item
                match_count = 0
                for gt_item, ext_item in zip(gt_value, extracted_value):
                    # Recursively compare dict keys
                    gt_keys = set(gt_item.keys())
                    ext_keys = set(ext_item.keys())
                    overlap = len(gt_keys & ext_keys)
                    if overlap / len(gt_keys) > 0.5:  # At least 50% key overlap
                        match_count += 1

                match_ratio = match_count / len(gt_value)
                if match_ratio >= 0.8:
                    return "semantic", f"List of dicts: {match_count}/{len(gt_value)} items matched"
                elif match_ratio >= 0.5:
                    return "fuzzy", f"List of dicts: {match_count}/{len(gt_value)} items partially matched"
                else:
                    return "mismatch", f"List of dicts: only {match_count}/{len(gt_value)} items matched"
            else:
                # Simple list: just check length match
                return "semantic", f"List length match ({len(gt_value)} items)"

        # Dict comparison
        if isinstance(gt_value, dict) and isinstance(extracted_value, dict):
            gt_keys = set(gt_value.keys())
            ext_keys = set(extracted_value.keys())
            overlap = len(gt_keys & ext_keys)
            total = len(gt_keys | ext_keys)

            if overlap == total:
                return "exact", "All dict keys match"
            elif overlap / total > 0.7:
                return "semantic", f"Dict partial match ({overlap}/{total} keys)"
            else:
                return "fuzzy", f"Dict mismatch ({overlap}/{total} keys)"

        # Default: try string conversion
        if str(gt_value) == str(extracted_value):
            return "exact", "Match via string conversion"

        return "mismatch", f"Type/value mismatch: {type(gt_value).__name__} vs {type(extracted_value).__name__}"

    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        # Lowercase
        s = s.lower()

        # Swedish characters
        s = s.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')

        # Remove extra whitespace
        s = ' '.join(s.split())

        # Remove special characters
        s = re.sub(r'[^\w\s]', '', s)

        return s.strip()

    def _build_report(self, field_validations: List[FieldValidation], total_gt_fields: int) -> ValidationReport:
        """Build comprehensive validation report."""

        # Categorize by confidence
        high_conf = [fv for fv in field_validations if fv.combined_confidence > 0.9 and fv.is_match]
        medium_conf = [fv for fv in field_validations if 0.7 <= fv.combined_confidence <= 0.9 and fv.is_match]
        low_conf = [fv for fv in field_validations if fv.combined_confidence < 0.7 and fv.is_match]

        # Count matches
        matched_fields = [fv for fv in field_validations if fv.is_match]
        total_matched = len(matched_fields)

        # Calculate raw metrics
        coverage_percent = (total_matched / total_gt_fields * 100) if total_gt_fields > 0 else 0.0
        accuracy_percent = (total_matched / total_matched * 100) if total_matched > 0 else 0.0

        # Calculate confidence-weighted metrics
        weighted_coverage = self._calculate_weighted_coverage(field_validations, total_gt_fields)
        weighted_accuracy = self._calculate_weighted_accuracy(matched_fields)

        return ValidationReport(
            coverage_percent=coverage_percent,
            accuracy_percent=accuracy_percent,
            weighted_coverage=weighted_coverage,
            weighted_accuracy=weighted_accuracy,
            field_validations=field_validations,
            high_confidence_fields=high_conf,
            medium_confidence_fields=medium_conf,
            low_confidence_fields=low_conf,
            total_gt_fields=total_gt_fields,
            total_extracted_fields=len([fv for fv in field_validations if fv.extracted_value is not None]),
            total_matched_fields=total_matched
        )

    def _calculate_weighted_coverage(self, validations: List[FieldValidation], total_gt: int) -> float:
        """
        Calculate confidence-weighted coverage.

        Formula: Sum(match_confidence * is_match) / total_gt_fields * 100
        """
        if total_gt == 0:
            return 0.0

        weighted_sum = sum(fv.combined_confidence for fv in validations if fv.is_match)
        return (weighted_sum / total_gt) * 100

    def _calculate_weighted_accuracy(self, matched_fields: List[FieldValidation]) -> float:
        """
        Calculate confidence-weighted accuracy.

        Formula: Avg(combined_confidence) of matched fields
        """
        if not matched_fields:
            return 0.0

        avg_confidence = sum(fv.combined_confidence for fv in matched_fields) / len(matched_fields)
        return avg_confidence * 100
