"""
Layer 2: Data Validation & Normalization

Validates and normalizes extracted data before classification.
Ensures data quality, handles missing values, and normalizes units.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    field: str
    severity: ValidationSeverity
    message: str
    original_value: Any = None
    corrected_value: Any = None


@dataclass
class ValidationResult:
    """Result of data validation."""
    valid: bool
    warnings: List[ValidationIssue] = field(default_factory=list)
    errors: List[ValidationIssue] = field(default_factory=list)
    normalized_data: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0-1, based on data completeness


class DataValidator:
    """
    Validates and normalizes extracted BRF data before classification.

    Performs:
    - Range validation (e.g., soliditet 0-100%)
    - Unit normalization (TSEK → SEK)
    - Calculated field verification
    - Missing data handling
    - Data quality scoring
    """

    # Valid ranges for common fields
    VALID_RANGES = {
        'soliditet_pct': (0, 100),
        'cash_to_debt_ratio_current_year': (0, 100),
        'cash_to_debt_ratio_prior_year': (0, 100),
        'interest_rate': (0, 20),  # 0-20%
        'depreciation_as_percent_of_revenue_current_year': (0, 100),
        'fee_increase_count_current_year': (0, 10),  # Max 10 increases per year
        'short_term_debt_pct': (0, 100),
    }

    # Fields that should be positive
    POSITIVE_FIELDS = [
        'total_debt',
        'total_assets',
        'total_liquidity_current_year',
        'total_liquidity_prior_year',
        'monthly_fee',
        'total_area_sqm',
        'total_apartments',
    ]

    # Critical fields needed for classification
    CRITICAL_FIELDS = [
        'soliditet_pct',
        'total_debt',
        'interest_expense_current_year',
    ]

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate and normalize extracted data.

        Args:
            data: Raw extracted data from agent extraction

        Returns:
            ValidationResult with validation status, issues, and normalized data
        """
        warnings = []
        errors = []
        normalized = data.copy()
        missing = []

        # 1. Check for missing critical fields
        for field in self.CRITICAL_FIELDS:
            if field not in data or data[field] is None:
                missing.append(field)

        # 2. Range validation
        range_issues = self._validate_ranges(data)
        warnings.extend([i for i in range_issues if i.severity == ValidationSeverity.WARNING])
        errors.extend([i for i in range_issues if i.severity == ValidationSeverity.ERROR])

        # Apply corrections from range validation
        for issue in range_issues:
            if issue.corrected_value is not None:
                normalized[issue.field] = issue.corrected_value

        # 3. Positive value validation
        positive_issues = self._validate_positive_values(data)
        warnings.extend([i for i in positive_issues if i.severity == ValidationSeverity.WARNING])
        errors.extend([i for i in positive_issues if i.severity == ValidationSeverity.ERROR])

        # 4. Unit normalization
        unit_issues, unit_normalized = self._normalize_units(data)
        warnings.extend(unit_issues)
        normalized.update(unit_normalized)

        # 5. Calculated field verification
        calc_issues = self._verify_calculated_fields(data)
        warnings.extend(calc_issues)

        # 6. Cross-field consistency
        consistency_issues = self._check_consistency(data)
        warnings.extend(consistency_issues)

        # Calculate confidence based on data completeness
        total_fields = len(self.CRITICAL_FIELDS)
        present_fields = total_fields - len(missing)
        confidence = present_fields / total_fields if total_fields > 0 else 0

        # Reduce confidence for warnings/errors
        confidence *= (1 - 0.1 * len(errors))  # -10% per error
        confidence *= (1 - 0.05 * len(warnings))  # -5% per warning
        confidence = max(0, min(1, confidence))  # Clamp to 0-1

        # Determine if valid (can proceed to classification)
        valid = len(missing) < len(self.CRITICAL_FIELDS) // 2 and len(errors) == 0

        return ValidationResult(
            valid=valid,
            warnings=warnings,
            errors=errors,
            normalized_data=normalized,
            missing_fields=missing,
            confidence=confidence
        )

    def _validate_ranges(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate that values are within expected ranges."""
        issues = []

        for field, (min_val, max_val) in self.VALID_RANGES.items():
            if field in data and data[field] is not None:
                value = data[field]

                if not isinstance(value, (int, float)):
                    continue

                if value < min_val or value > max_val:
                    issues.append(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Value {value} outside valid range [{min_val}, {max_val}]",
                        original_value=value,
                        corrected_value=None  # Mark as invalid
                    ))

        return issues

    def _validate_positive_values(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate that values that should be positive are positive."""
        issues = []

        for field in self.POSITIVE_FIELDS:
            if field in data and data[field] is not None:
                value = data[field]

                if isinstance(value, (int, float)) and value < 0:
                    issues.append(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.WARNING,
                        message=f"Expected positive value, got {value}",
                        original_value=value,
                        corrected_value=None
                    ))

        return issues

    def _normalize_units(self, data: Dict[str, Any]) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Normalize units (e.g., TSEK → SEK).

        Heuristic: If a monetary value is < 100,000, assume it's in TSEK.
        """
        issues = []
        normalized = {}

        monetary_fields = [
            'interest_expense_current_year',
            'interest_expense_prior_year',
            'total_debt',
            'total_assets',
            'total_liquidity_current_year',
            'total_liquidity_prior_year',
            'result_without_depreciation_current_year',
            'result_without_depreciation_prior_year',
        ]

        for field in monetary_fields:
            if field in data and data[field] is not None:
                value = data[field]

                if isinstance(value, (int, float)) and 0 < value < 100_000:
                    # Likely in TSEK, convert to SEK
                    normalized_value = value * 1000
                    normalized[f"{field}_sek"] = normalized_value

                    issues.append(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.INFO,
                        message=f"Converted {value} TSEK → {normalized_value} SEK",
                        original_value=value,
                        corrected_value=normalized_value
                    ))

        return issues, normalized

    def _verify_calculated_fields(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Verify calculated fields against raw data."""
        issues = []

        # Verify cash-to-debt ratio
        if all(k in data for k in ['total_liquidity_current_year', 'total_debt',
                                    'cash_to_debt_ratio_current_year']):
            liquidity = data['total_liquidity_current_year']
            debt = data['total_debt']
            extracted_ratio = data['cash_to_debt_ratio_current_year']

            if liquidity and debt and debt > 0 and extracted_ratio is not None:
                calculated_ratio = (liquidity / debt) * 100

                if abs(calculated_ratio - extracted_ratio) > 1.0:  # >1% difference
                    issues.append(ValidationIssue(
                        field='cash_to_debt_ratio_current_year',
                        severity=ValidationSeverity.WARNING,
                        message=f"Extracted ratio {extracted_ratio:.2f}% differs from "
                               f"calculated {calculated_ratio:.2f}%",
                        original_value=extracted_ratio,
                        corrected_value=calculated_ratio
                    ))

        # Verify depreciation as % of revenue
        if all(k in data for k in ['depreciation_current_year', 'total_revenue',
                                    'depreciation_as_percent_of_revenue_current_year']):
            depreciation = data.get('depreciation_current_year')
            revenue = data.get('total_revenue')
            extracted_pct = data.get('depreciation_as_percent_of_revenue_current_year')

            if depreciation and revenue and revenue > 0 and extracted_pct is not None:
                calculated_pct = (depreciation / revenue) * 100

                if abs(calculated_pct - extracted_pct) > 1.0:  # >1% difference
                    issues.append(ValidationIssue(
                        field='depreciation_as_percent_of_revenue_current_year',
                        severity=ValidationSeverity.WARNING,
                        message=f"Extracted {extracted_pct:.2f}% differs from "
                               f"calculated {calculated_pct:.2f}%",
                        original_value=extracted_pct,
                        corrected_value=calculated_pct
                    ))

        return issues

    def _check_consistency(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check cross-field consistency."""
        issues = []

        # Check year-over-year liquidity trend
        if all(k in data for k in ['total_liquidity_current_year', 'total_liquidity_prior_year']):
            current = data['total_liquidity_current_year']
            prior = data['total_liquidity_prior_year']

            if current and prior and current > 0 and prior > 0:
                change_pct = ((current - prior) / prior) * 100

                if abs(change_pct) > 90:  # >90% change is suspicious
                    issues.append(ValidationIssue(
                        field='total_liquidity',
                        severity=ValidationSeverity.WARNING,
                        message=f"Large liquidity change: {change_pct:.1f}% "
                               f"({prior:,} → {current:,}). Verify data.",
                        original_value=(prior, current)
                    ))

        # Check soliditet consistency with debt/equity
        if all(k in data for k in ['soliditet_pct', 'total_assets', 'total_debt']):
            soliditet = data['soliditet_pct']
            assets = data['total_assets']
            debt = data['total_debt']

            if soliditet and assets and debt and assets > 0:
                equity = assets - debt
                calculated_soliditet = (equity / assets) * 100

                if abs(calculated_soliditet - soliditet) > 5.0:  # >5% difference
                    issues.append(ValidationIssue(
                        field='soliditet_pct',
                        severity=ValidationSeverity.WARNING,
                        message=f"Soliditet {soliditet:.1f}% differs from calculated "
                               f"{calculated_soliditet:.1f}% (from assets-debt)",
                        original_value=soliditet,
                        corrected_value=calculated_soliditet
                    ))

        return issues

    def get_data_quality_report(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Generate a summary report of data quality."""
        return {
            'valid': validation_result.valid,
            'confidence': validation_result.confidence,
            'completeness': 1 - (len(validation_result.missing_fields) /
                               len(self.CRITICAL_FIELDS)),
            'error_count': len(validation_result.errors),
            'warning_count': len(validation_result.warnings),
            'missing_critical_fields': validation_result.missing_fields,
            'data_quality_grade': self._calculate_grade(validation_result),
        }

    def _calculate_grade(self, result: ValidationResult) -> str:
        """Calculate A-F grade for data quality."""
        confidence = result.confidence

        if confidence >= 0.95:
            return "A"
        elif confidence >= 0.85:
            return "B"
        elif confidence >= 0.75:
            return "C"
        elif confidence >= 0.60:
            return "D"
        else:
            return "F"
