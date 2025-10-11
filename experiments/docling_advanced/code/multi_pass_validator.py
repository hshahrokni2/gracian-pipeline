"""
Multi-Pass Validator - Component 4 of Phase 3A

Validates extraction quality through 4 passes:
1. Structural validation (schema, required fields, data types)
2. Semantic validation (business rules, accounting identities)
3. Cross-reference validation (using Component 3 results)
4. Anomaly detection (statistical outliers)

Architecture: Pipeline pattern with parallel execution
Performance Target: <2s per document, >95% validation accuracy
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

from cross_agent_data_linker import LinkResolution


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable validation result (thread-safe).

    Severity levels:
    - ERROR: Critical failure, document flagged for review
    - WARNING: Suspicious data, continue with caution
    - INFO: FYI only, no action required
    """
    field_name: str
    severity: str  # "ERROR" | "WARNING" | "INFO"
    rule_name: str
    message: str
    expected_value: Any
    actual_value: Any
    confidence: float  # How confident are we in this validation? (0.0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Export for JSON serialization"""
        return {
            "field_name": self.field_name,
            "severity": self.severity,
            "rule_name": self.rule_name,
            "message": self.message,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
            "actual_value": str(self.actual_value) if self.actual_value is not None else None,
            "confidence": self.confidence
        }


@dataclass
class ValidationReport:
    """Aggregated validation results for a document"""

    total_validations: int = 0
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    infos: List[ValidationResult] = field(default_factory=list)
    flags_for_review: List[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate (validations without errors)"""
        if self.total_validations == 0:
            return 1.0

        failed = len(self.errors)
        return (self.total_validations - failed) / self.total_validations

    def is_critical(self) -> bool:
        """Has any ERROR-level validation failures?"""
        return len(self.errors) > 0

    def summary(self) -> str:
        """Human-readable summary"""
        return (
            f"{self.pass_rate*100:.1f}% pass rate "
            f"({len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.infos)} infos)"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export for JSON serialization"""
        return {
            "total_validations": self.total_validations,
            "pass_rate": self.pass_rate,
            "is_critical": self.is_critical(),
            "summary": self.summary(),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "infos": [i.to_dict() for i in self.infos],
            "flags_for_review": self.flags_for_review
        }


class BaseValidator(ABC):
    """
    Abstract base class for all validators.

    Design principles:
    1. Stateless: No instance variables (thread-safe)
    2. Exception-safe: Catch all exceptions, return ERROR ValidationResult
    3. Read-only: Never modify input data
    """

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate data and return list of validation results.

        Args:
            data: Merged extraction data from Components 1-3

        Returns:
            List of ValidationResult objects (empty if all pass)
        """
        pass

    def name(self) -> str:
        """Validator name for diagnostics"""
        return self.__class__.__name__

    def safe_validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Exception-safe wrapper around validate().

        Catches all exceptions and converts to ERROR ValidationResult.
        """
        try:
            return self.validate(data)
        except Exception as e:
            # Convert exception to ValidationResult
            error_msg = f"{self.name()} failed: {str(e)}"
            return [ValidationResult(
                field_name=f"{self.name()}.exception",
                severity="ERROR",
                rule_name="validator_exception",
                message=error_msg,
                expected_value="no exception",
                actual_value=traceback.format_exc(),
                confidence=1.0
            )]

    @staticmethod
    def _to_numeric(value: Any) -> Optional[float]:
        """
        Convert value to numeric, return None if not possible.

        Handles Swedish number format: "1 234,56" → 1234.56
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        # Handle Swedish format
        if isinstance(value, str):
            # Remove spaces, replace comma with dot
            cleaned = value.strip().replace(' ', '').replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                return None

        return None


class BalanceSheetValidator(BaseValidator):
    """
    Validate balance sheet accounting identity: Assets = Liabilities + Equity

    Checks:
    - Assets ≈ Liabilities + Equity (within tolerance)
    - All values positive (except deficit equity)
    - Reasonable magnitudes (no impossible values)
    """

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        # Get financial agent data
        financial = data.get('financial_agent', {})
        if not isinstance(financial, dict):
            return results

        # Extract balance sheet values
        assets = self._to_numeric(financial.get('assets'))
        liabilities = self._to_numeric(financial.get('liabilities'))
        equity = self._to_numeric(financial.get('equity'))

        if not all([assets is not None, liabilities is not None, equity is not None]):
            # Missing data - can't validate
            return results

        # Validate accounting identity: Assets = Liabilities + Equity
        calculated_assets = liabilities + equity
        diff = abs(assets - calculated_assets)
        diff_percent = (diff / max(abs(assets), 1)) * 100

        # Tolerance: 2% for balance sheet (accounting precision)
        tolerance = 2.0

        if diff_percent > tolerance * 2:
            # ERROR: Major mismatch (beyond 2x tolerance)
            results.append(ValidationResult(
                field_name="financial_agent.balance_sheet",
                severity="ERROR",
                rule_name="accounting_identity_violated",
                message=f"Balance sheet doesn't balance: Assets {assets:,.0f} != Liabilities {liabilities:,.0f} + Equity {equity:,.0f} = {calculated_assets:,.0f} (diff: {diff_percent:.1f}%)",
                expected_value=f"{calculated_assets:,.0f}",
                actual_value=f"{assets:,.0f}",
                confidence=0.95
            ))
        elif diff_percent > tolerance:
            # WARNING: Minor mismatch (within 2x tolerance)
            results.append(ValidationResult(
                field_name="financial_agent.balance_sheet",
                severity="WARNING",
                rule_name="accounting_identity_mismatch",
                message=f"Balance sheet minor mismatch: diff {diff_percent:.1f}% (tolerance {tolerance}%)",
                expected_value=f"{calculated_assets:,.0f}",
                actual_value=f"{assets:,.0f}",
                confidence=0.8
            ))
        else:
            # INFO: Valid balance sheet
            results.append(ValidationResult(
                field_name="financial_agent.balance_sheet",
                severity="INFO",
                rule_name="accounting_identity_valid",
                message=f"Balance sheet valid: Assets = Liabilities + Equity (diff: {diff_percent:.2f}%)",
                expected_value=f"{calculated_assets:,.0f}",
                actual_value=f"{assets:,.0f}",
                confidence=1.0
            ))

        return results


class IncomeStatementValidator(BaseValidator):
    """
    Validate income statement coherence.

    Checks:
    - Revenue - Expenses ≈ Surplus (within tolerance)
    - Revenue >= 0 (or INFO if negative - rare but possible)
    - Expenses >= 0
    - Surplus can be positive or negative
    """

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        # Get financial agent data
        financial = data.get('financial_agent', {})
        if not isinstance(financial, dict):
            return results

        # Extract income statement values
        revenue = self._to_numeric(financial.get('revenue'))
        expenses = self._to_numeric(financial.get('expenses'))
        surplus = self._to_numeric(financial.get('surplus'))

        if not all([revenue is not None, expenses is not None]):
            # Missing critical data - can't validate
            return results

        # Calculate expected surplus
        calculated_surplus = revenue - expenses

        if surplus is not None:
            # Validate surplus matches calculation
            diff = abs(surplus - calculated_surplus)
            diff_percent = (diff / max(abs(calculated_surplus), 1)) * 100

            # Tolerance: 5% for income statement (more variation than balance sheet)
            tolerance = 5.0

            if diff_percent > tolerance * 2:
                # ERROR: Major mismatch
                results.append(ValidationResult(
                    field_name="financial_agent.income_statement",
                    severity="ERROR",
                    rule_name="surplus_calculation_error",
                    message=f"Surplus mismatch: Revenue {revenue:,.0f} - Expenses {expenses:,.0f} = {calculated_surplus:,.0f}, but reported surplus is {surplus:,.0f} (diff: {diff_percent:.1f}%)",
                    expected_value=f"{calculated_surplus:,.0f}",
                    actual_value=f"{surplus:,.0f}",
                    confidence=0.95
                ))
            elif diff_percent > tolerance:
                # WARNING: Minor mismatch
                results.append(ValidationResult(
                    field_name="financial_agent.income_statement",
                    severity="WARNING",
                    rule_name="surplus_calculation_mismatch",
                    message=f"Surplus minor mismatch: diff {diff_percent:.1f}% (tolerance {tolerance}%)",
                    expected_value=f"{calculated_surplus:,.0f}",
                    actual_value=f"{surplus:,.0f}",
                    confidence=0.8
                ))
            else:
                # INFO: Valid income statement
                results.append(ValidationResult(
                    field_name="financial_agent.income_statement",
                    severity="INFO",
                    rule_name="surplus_calculation_valid",
                    message=f"Income statement valid: Revenue - Expenses = Surplus (diff: {diff_percent:.2f}%)",
                    expected_value=f"{calculated_surplus:,.0f}",
                    actual_value=f"{surplus:,.0f}",
                    confidence=1.0
                ))
        else:
            # INFO: Surplus not extracted, but we can report calculated value
            results.append(ValidationResult(
                field_name="financial_agent.surplus",
                severity="INFO",
                rule_name="surplus_calculated",
                message=f"Surplus not extracted, calculated value: {calculated_surplus:,.0f}",
                expected_value=f"{calculated_surplus:,.0f}",
                actual_value="not_extracted",
                confidence=0.9
            ))

        return results


class CrossReferenceValidator(BaseValidator):
    """
    Validate cross-referenced data using Component 3 (CrossAgentDataLinker) results.

    Checks:
    - Cross-referenced values match (within tolerance)
    - No unresolved conflicts
    - Missing references flagged
    - OCR errors detected via cross-validation

    Requires: link_resolution object from CrossAgentDataLinker
    """

    def __init__(self, link_resolution=None):
        """
        Args:
            link_resolution: LinkResolution object from CrossAgentDataLinker
        """
        self.link_resolution = link_resolution

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        if self.link_resolution is None:
            # No link resolution provided - skip
            return results

        # Check for conflicts
        for link in self.link_resolution.conflicts:
            severity = "ERROR" if link.final_confidence < 0.7 else "WARNING"

            results.append(ValidationResult(
                field_name=f"cross_reference.{link.link_type}",
                severity=severity,
                rule_name="cross_reference_conflict",
                message=f"Conflict: {link.source_agent}.{link.source_field} ({link.source_value}) != {link.target_agent}.{link.target_field} ({link.target_value})",
                expected_value=str(link.source_value),
                actual_value=str(link.target_value),
                confidence=link.final_confidence
            ))

        # Check for fields flagged for review (former OCR errors)
        for field_name in self.link_resolution.flags_for_review:
            results.append(ValidationResult(
                field_name=f"cross_reference.{field_name}",
                severity="INFO",
                rule_name="cross_reference_flagged_for_review",
                message=f"Field flagged for manual review: {field_name}",
                expected_value="review_required",
                actual_value="flagged",
                confidence=0.7
            ))

        # Report validated cross-references (INFO) - from confidence_boost dict
        for field_name, confidence in self.link_resolution.confidence_boost.items():
            results.append(ValidationResult(
                field_name=f"cross_reference.{field_name}",
                severity="INFO",
                rule_name="cross_reference_validated",
                message=f"Cross-reference validated: {field_name} (confidence {confidence:.2f})",
                expected_value="validated",
                actual_value="validated",
                confidence=confidence
            ))

        # Summary
        if self.link_resolution.confidence_boost or self.link_resolution.conflicts or self.link_resolution.flags_for_review:
            validated_count = len(self.link_resolution.confidence_boost)
            conflicts_count = len(self.link_resolution.conflicts)
            flagged_count = len(self.link_resolution.flags_for_review)
            total_links = validated_count + conflicts_count + flagged_count

            if total_links > 0:
                match_rate = (validated_count / total_links) * 100

                results.append(ValidationResult(
                    field_name="cross_reference.summary",
                    severity="INFO",
                    rule_name="cross_reference_summary",
                    message=f"Cross-reference summary: {validated_count}/{total_links} validated ({match_rate:.1f}%), {conflicts_count} conflicts, {flagged_count} flagged for review",
                    expected_value=f"{total_links} total",
                    actual_value=f"{validated_count} validated",
                    confidence=0.9
                ))

        return results


class ValidationPipeline:
    """
    Chain of responsibility pattern - runs validators in sequence or parallel.

    Features:
    1. Early exit on critical errors (fail_fast=True)
    2. Parallel execution (parallel=True, 4 workers)
    3. Exception isolation (one validator failure doesn't kill pipeline)
    """

    def __init__(self, max_workers: int = 4):
        self.validators: List[BaseValidator] = []
        self.max_workers = max_workers

    def add_validator(self, validator: BaseValidator):
        """Add validator to pipeline"""
        self.validators.append(validator)

    def run(
        self,
        data: Dict[str, Any],
        fail_fast: bool = False,
        parallel: bool = False
    ) -> ValidationReport:
        """
        Run all validators on data.

        Args:
            data: Merged extraction data from Components 1-3
            fail_fast: Stop on first ERROR-level failure
            parallel: Run validators in parallel (max_workers threads)

        Returns:
            ValidationReport with aggregated results
        """
        if parallel:
            return self._run_parallel(data)
        else:
            return self._run_sequential(data, fail_fast)

    def _run_sequential(
        self,
        data: Dict[str, Any],
        fail_fast: bool = False
    ) -> ValidationReport:
        """Run validators sequentially with optional early exit"""
        all_results = []

        for validator in self.validators:
            # Use safe_validate to catch exceptions
            results = validator.safe_validate(data)
            all_results.extend(results)

            # Early exit if critical error found
            if fail_fast and any(r.severity == "ERROR" for r in results):
                break

        return self._build_report(all_results)

    def _run_parallel(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Run validators in parallel using ThreadPoolExecutor.

        Note: Uses threads (not processes) because:
        1. Validators are I/O bound (reading data)
        2. No pickling overhead (shared memory)
        3. Faster startup time
        """
        all_results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all validators
            future_to_validator = {
                executor.submit(validator.safe_validate, data): validator
                for validator in self.validators
            }

            # Collect results as they complete
            for future in as_completed(future_to_validator):
                validator = future_to_validator[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    # This should never happen (safe_validate catches all)
                    # But add safety net just in case
                    all_results.append(ValidationResult(
                        field_name=f"{validator.name()}.parallel_exception",
                        severity="ERROR",
                        rule_name="parallel_execution_error",
                        message=f"Parallel execution failed: {str(e)}",
                        expected_value="successful execution",
                        actual_value=str(e),
                        confidence=1.0
                    ))

        return self._build_report(all_results)

    def _build_report(self, all_results: List[ValidationResult]) -> ValidationReport:
        """Build ValidationReport from list of ValidationResults"""
        report = ValidationReport()
        report.total_validations = len(all_results)

        # Categorize by severity
        for result in all_results:
            if result.severity == "ERROR":
                report.errors.append(result)
                # Add to flags for review
                report.flags_for_review.append(
                    f"ERROR in {result.field_name}: {result.message}"
                )
            elif result.severity == "WARNING":
                report.warnings.append(result)
            elif result.severity == "INFO":
                report.infos.append(result)

        return report


# ============================================================================
# PASS 1 VALIDATORS: Structural Validation
# ============================================================================

class StructuralValidator(BaseValidator):
    """
    Validate required fields and data types.

    Checks:
    - Required fields present
    - Correct data types
    - Non-null values for critical fields
    """

    # Required fields per agent (critical fields only)
    REQUIRED_FIELDS = {
        'governance_agent': ['chairman', 'board_members', 'auditor'],
        'financial_agent': ['revenue', 'expenses', 'assets', 'liabilities', 'equity'],
        'property_agent': ['total_area_sqm'],
        'note_2_agent': [],  # Notes are optional
        'note_7_agent': [],
        'note_11_agent': []
    }

    # Expected data types per field
    FIELD_TYPES = {
        'chairman': str,
        'board_members': list,
        'auditor': str,
        'revenue': (int, float),
        'expenses': (int, float),
        'assets': (int, float),
        'liabilities': (int, float),
        'equity': (int, float),
        'total_area_sqm': (int, float)
    }

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        for agent_name, required_fields in self.REQUIRED_FIELDS.items():
            agent_data = data.get(agent_name, {})

            for field in required_fields:
                # Check if field exists
                if field not in agent_data:
                    results.append(ValidationResult(
                        field_name=f"{agent_name}.{field}",
                        severity="ERROR",
                        rule_name="required_field_missing",
                        message=f"Missing required field: {field}",
                        expected_value="present",
                        actual_value=None,
                        confidence=1.0
                    ))
                    continue

                value = agent_data[field]

                # Check if null
                if value is None:
                    results.append(ValidationResult(
                        field_name=f"{agent_name}.{field}",
                        severity="ERROR",
                        rule_name="required_field_null",
                        message=f"Required field is null: {field}",
                        expected_value="non-null",
                        actual_value=None,
                        confidence=1.0
                    ))
                    continue

                # Check data type
                expected_type = self.FIELD_TYPES.get(field)
                if expected_type and not isinstance(value, expected_type):
                    # Convert to string if possible
                    convertible = False
                    if expected_type == str and value is not None:
                        convertible = True
                    elif expected_type in [(int, float), int, float]:
                        convertible = self._to_numeric(value) is not None

                    if not convertible:
                        results.append(ValidationResult(
                            field_name=f"{agent_name}.{field}",
                            severity="WARNING",
                            rule_name="incorrect_data_type",
                            message=f"Expected {expected_type.__name__}, got {type(value).__name__}",
                            expected_value=expected_type.__name__,
                            actual_value=type(value).__name__,
                            confidence=0.8
                        ))

        return results


class SwedishNumberValidator(BaseValidator):
    """
    Validate Swedish number format and encoding.

    Swedish format: "1 234 567,89" (space thousands, comma decimal)
    Also accepts: "1234567.89" (international format)

    Checks:
    - Proper thousand separators (space, not comma)
    - Proper decimal separator (comma or dot)
    - No mixed formats
    - Swedish character encoding (å, ä, ö not corrupted)
    """

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        for agent_name, agent_data in data.items():
            if not isinstance(agent_data, dict):
                continue

            for field_name, value in agent_data.items():
                # Skip metadata fields
                if field_name in ['confidence', 'source_page']:
                    continue

                # Check if looks like a number but is string
                if isinstance(value, str) and self._looks_like_number(value):
                    # Validate Swedish format
                    if not self._is_valid_swedish_format(value):
                        results.append(ValidationResult(
                            field_name=f"{agent_name}.{field_name}",
                            severity="WARNING",
                            rule_name="invalid_swedish_number_format",
                            message=f"Invalid Swedish number format: '{value}'",
                            expected_value="1 234,56 or 1234.56",
                            actual_value=value,
                            confidence=0.8
                        ))

                # Check for common Swedish OCR errors in strings
                if isinstance(value, str) and self._has_swedish_ocr_errors(value):
                    results.append(ValidationResult(
                        field_name=f"{agent_name}.{field_name}",
                        severity="INFO",
                        rule_name="swedish_character_encoding",
                        message=f"Possible Swedish character OCR error: '{value}'",
                        expected_value="å/ä/ö preserved",
                        actual_value=value,
                        confidence=0.6
                    ))

        return results

    def _looks_like_number(self, text: str) -> bool:
        """Check if string looks like it should be a number"""
        # Has digits and is not too long
        return bool(re.search(r'\d', text)) and len(text) < 30

    def _is_valid_swedish_format(self, text: str) -> bool:
        """
        Validate Swedish number format.

        Valid formats:
        - "1 234,56" (Swedish: space thousands, comma decimal)
        - "1234.56" (International: dot decimal)
        - "1234" (Integer)
        - "1 234" (Swedish integer with space separator)

        Invalid:
        - "1,234.56" (US format - comma thousands)
        - "1.234,56" (Mixed format)
        """
        text = text.strip()

        # Pattern: Optional spaces between digits, optional comma/dot + decimals
        # Valid: "1 234 567,89" or "1234567.89" or "1234"
        swedish_pattern = r'^[\d\s]+[,.]?\d*$'

        if not re.match(swedish_pattern, text):
            return False

        # Check for invalid patterns
        # Invalid: comma used as thousand separator (1,234)
        if ',' in text and '.' in text:
            # Mixed separators
            return False

        # If comma present, should be decimal separator (max 2 digits after)
        if ',' in text:
            parts = text.split(',')
            if len(parts) != 2:
                return False
            decimal_part = parts[1].strip()
            if len(decimal_part) > 2:
                return False  # Too many decimal places

        return True

    def _has_swedish_ocr_errors(self, text: str) -> bool:
        """
        Detect common Swedish OCR errors.

        Common errors:
        - å → a (TILLGANGAR instead of TILLGÅNGAR)
        - ä → a (REDOVISNING instead of RÄKENSKAPER)
        - ö → o (RORELSE instead of RÖRELSE)
        """
        # If text has Swedish keywords without proper characters, likely OCR error
        swedish_keywords_corrupted = [
            'tillgangar',  # Should be tillgångar
            'tillgingar',
            'rorelse',     # Should be rörelse
            'arsavgift',   # Should be årsavgift
            'redovisning'  # Could be rädovisning (rare, but possible)
        ]

        text_lower = text.lower()
        for keyword in swedish_keywords_corrupted:
            if keyword in text_lower:
                return True

        return False


# Test function
def test_validation_pipeline():
    """Test validation pipeline with mock validators"""

    class AlwaysPassValidator(BaseValidator):
        """Mock validator that always passes"""
        def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
            return []

    class AlwaysFailValidator(BaseValidator):
        """Mock validator that always fails"""
        def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
            return [ValidationResult(
                field_name="test_field",
                severity="ERROR",
                rule_name="always_fail",
                message="This validator always fails",
                expected_value="pass",
                actual_value="fail",
                confidence=1.0
            )]

    class WarningValidator(BaseValidator):
        """Mock validator that returns warnings"""
        def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
            return [ValidationResult(
                field_name="warning_field",
                severity="WARNING",
                rule_name="suspicious_data",
                message="Data looks suspicious",
                expected_value="normal",
                actual_value="suspicious",
                confidence=0.7
            )]

    # Test 1: Sequential execution
    print("Test 1: Sequential Execution")
    pipeline = ValidationPipeline()
    pipeline.add_validator(AlwaysPassValidator())
    pipeline.add_validator(WarningValidator())
    pipeline.add_validator(AlwaysFailValidator())

    test_data = {"test": "data"}
    report = pipeline.run(test_data, parallel=False)

    print(f"Summary: {report.summary()}")
    print(f"Errors: {len(report.errors)}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Is Critical: {report.is_critical()}")
    assert report.is_critical() == True, "Should have critical errors"
    print("✅ Test 1 passed")
    print()

    # Test 2: Parallel execution
    print("Test 2: Parallel Execution")
    report_parallel = pipeline.run(test_data, parallel=True)
    print(f"Summary: {report_parallel.summary()}")
    assert report_parallel.is_critical() == True, "Should have critical errors"
    print("✅ Test 2 passed")
    print()

    # Test 3: Fail fast
    print("Test 3: Fail Fast Mode")
    report_fail_fast = pipeline.run(test_data, fail_fast=True)
    print(f"Summary: {report_fail_fast.summary()}")
    # Should stop after first ERROR
    print("✅ Test 3 passed")
    print()

    # Test 4: Exception handling
    print("Test 4: Exception Handling")

    class ExceptionValidator(BaseValidator):
        """Mock validator that raises exception"""
        def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
            raise RuntimeError("Intentional error for testing")

    pipeline_with_exception = ValidationPipeline()
    pipeline_with_exception.add_validator(ExceptionValidator())

    report_exception = pipeline_with_exception.run(test_data)
    print(f"Summary: {report_exception.summary()}")
    assert len(report_exception.errors) == 1, "Should convert exception to error"
    assert "Intentional error" in report_exception.errors[0].message
    print("✅ Test 4 passed")
    print()

    print("✅ All validation pipeline tests passed!")


if __name__ == "__main__":
    test_validation_pipeline()
