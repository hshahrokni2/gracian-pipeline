"""
Multi-Layer Validation Engine for BRF Annual Report Extraction

Four-layer validation pyramid:
1. Schema validation (Pydantic types) - delegated to Pydantic models
2. Cross-reference validation (internal consistency)
3. Pattern validation (format/range checks)
4. Ground truth validation (known correct patterns)

Implements validation patterns from ULTRATHINKING_ROBUST_SCALABLE_ARCHITECTURE.md
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "ERROR"  # Critical issue, data is wrong
    WARNING = "WARNING"  # Suspicious data, may be wrong
    INFO = "INFO"  # Informational, for tracking


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: ValidationSeverity
    field: str  # Dot-notation path to field (e.g., "loans[0].outstanding_balance")
    value: Any  # The problematic value
    message: str  # Human-readable error message
    suggestion: Optional[str] = None  # How to fix the issue

    def to_dict(self) -> Dict[str, Any]:
        """Export for JSON serialization"""
        return {
            "severity": self.severity.value,
            "field": self.field,
            "value": str(self.value),
            "message": self.message,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationReport:
    """Complete validation report with all issues found"""
    schema_valid: bool
    issues: List[ValidationIssue]

    def has_errors(self) -> bool:
        """Check if any ERROR-level issues exist"""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if any WARNING-level issues exist"""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    def error_count(self) -> int:
        """Count of ERROR-level issues"""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)

    def warning_count(self) -> int:
        """Count of WARNING-level issues"""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        """Export for JSON serialization"""
        return {
            "schema_valid": self.schema_valid,
            "error_count": self.error_count(),
            "warning_count": self.warning_count(),
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
            "issues": [issue.to_dict() for issue in self.issues]
        }

    def summary(self) -> str:
        """Human-readable summary"""
        if not self.issues:
            return "✅ All validations passed"

        errors = self.error_count()
        warnings = self.warning_count()

        parts = []
        if errors > 0:
            parts.append(f"❌ {errors} error(s)")
        if warnings > 0:
            parts.append(f"⚠️ {warnings} warning(s)")

        return ", ".join(parts)


# Known Swedish banks for lender validation
KNOWN_SWEDISH_BANKS = {
    "SEB", "Swedbank", "Nordea", "Handelsbanken",
    "SBAB", "Länsförsäkringar", "Danske Bank",
    "Skandiabanken", "ICA Banken", "Marginalen Bank",
    "Resurs Bank", "Santander", "Bluestep Bank",
    # Also accept with spaces and capitalization variations
    "SEB Bank", "Swedbank AB", "Nordea Bank",
    "Svenska Handelsbanken", "Handelsbanken AB"
}


# Validation pattern library (from ULTRATHINKING spec lines 228-283)
VALIDATION_PATTERNS = {
    "loans": {
        "lender": {
            "type": "enum",
            "values": KNOWN_SWEDISH_BANKS,
            "error": "Unknown lender - possible hallucination",
            "suggestion": "Verify lender name from source PDF"
        },
        "outstanding_balance": {
            "type": "number",
            "min": 100000,  # Minimum loan size (100k SEK)
            "max": 500000000,  # Maximum loan size (500M SEK)
            "not_equal": ["0", 0, "null", None],  # Red flag values
            "error": "Loan balance cannot be zero or null",
            "suggestion": "Re-extract Note 5 table with vision extraction"
        },
        "interest_rate": {
            "type": "number",
            "min": 0.001,  # 0.1% (minimum Swedish interest rate)
            "max": 0.10,   # 10% (maximum reasonable rate)
            "error": "Interest rate out of reasonable range",
            "suggestion": "Verify interest rate from loan note"
        }
    },

    "property": {
        "property_designation": {
            "type": "regex",
            "pattern": r"^[A-ZÅÄÖ\s]+-\d{1,4}:\d{1,4}$",
            "examples": ["HJORTHAGEN 1:1", "SOLNA 2:3"],
            "error": "Property designation format invalid",
            "suggestion": "Should match pattern 'NAME-N:N' (e.g., 'HJORTHAGEN 1:1')"
        },
        "built_year": {
            "type": "number",
            "min": 1800,
            "max": 2025,
            "error": "Built year out of valid range",
            "suggestion": "Verify year from property section"
        },
        "total_area_sqm": {
            "type": "number",
            "min": 100,     # Minimum BRF size (very small)
            "max": 50000,   # Maximum BRF size (very large)
            "error": "Total area out of reasonable range",
            "suggestion": "Verify from property details section"
        }
    },

    "fees": {
        "monthly_fee": {
            "type": "number",
            "min": 100,     # Minimum monthly fee (very small apartment)
            "max": 50000,   # Maximum monthly fee (luxury penthouse)
            "error": "Monthly fee out of reasonable range",
            "suggestion": "Verify from fee structure section"
        },
        "annual_fee": {
            "type": "number",
            "min": 1200,    # 12 months × 100
            "max": 600000,  # 12 months × 50000
            "error": "Annual fee out of reasonable range",
            "suggestion": "Should be approximately 12 × monthly fee"
        }
    },

    "cross_references": {
        "apartment_total_check": {
            "rule": "property.total_apartments == sum(property.apartment_distribution)",
            "tolerance": 0,  # Exact match required
            "error": "Total apartments doesn't match distribution sum",
            "suggestion": "Re-extract apartment distribution table"
        },
        "balance_sheet_equation": {
            "rule": "financial.assets == financial.liabilities + financial.equity",
            "tolerance": 0.05,  # ±5% tolerance
            "error": "Balance sheet equation doesn't balance (Assets ≠ Liabilities + Equity)",
            "suggestion": "Verify financial statement extraction"
        },
        "loan_total_check": {
            "rule": "financial.total_loans == sum(loans[].outstanding_balance)",
            "tolerance": 0.01,  # ±1% tolerance
            "error": "Total loans doesn't match sum of individual loans",
            "suggestion": "Re-extract loan details from Note 5"
        },
        "fee_monthly_annual_check": {
            "rule": "fees.annual_fee ≈ fees.monthly_fee × 12",
            "tolerance": 0.05,  # ±5% tolerance
            "error": "Annual fee doesn't match 12 × monthly fee",
            "suggestion": "Verify fee structure section"
        }
    }
}


class ValidationEngine:
    """Multi-layer validation engine with ground truth patterns"""

    def __init__(self):
        """Initialize validation engine with pattern library"""
        self.patterns = VALIDATION_PATTERNS

    def validate_extraction(
        self,
        result: Dict[str, Any],
        pdf_path: Optional[str] = None
    ) -> ValidationReport:
        """
        Run all 4 validation layers:
        1. Schema validation (delegated to Pydantic)
        2. Cross-reference validation
        3. Pattern validation
        4. Ground truth validation

        Returns:
            ValidationReport with all issues found
        """
        issues = []

        # Layer 1: Schema validation (already done by Pydantic, assume passed)
        schema_valid = True

        # Layer 2: Cross-reference validation
        issues.extend(self.validate_cross_references(result))

        # Layer 3: Pattern validation
        issues.extend(self.validate_patterns(result))

        # Layer 4: Ground truth validation (if ground truth available)
        if pdf_path:
            issues.extend(self.validate_ground_truth(result, pdf_path))

        return ValidationReport(
            schema_valid=schema_valid,
            issues=issues
        )

    def validate_loans(self, loans: List[Dict]) -> List[ValidationIssue]:
        """Validate loan data against patterns (CRITICAL - catches loan balance = 0)"""
        issues = []

        if not loans:
            return issues

        loan_patterns = self.patterns["loans"]

        for i, loan in enumerate(loans):
            # Extract loan data (handle ExtractionField wrapper)
            lender_field = loan.get('lender', {})
            lender = lender_field.get('value') if isinstance(lender_field, dict) else lender_field

            balance_field = loan.get('outstanding_balance', {})
            balance = balance_field.get('value') if isinstance(balance_field, dict) else balance_field

            rate_field = loan.get('interest_rate', {})
            rate = rate_field.get('value') if isinstance(rate_field, dict) else rate_field

            # Validate lender name
            if lender:
                lender_pattern = loan_patterns["lender"]
                if lender not in lender_pattern["values"]:
                    # Check case-insensitive match
                    lender_upper = lender.upper() if isinstance(lender, str) else str(lender).upper()
                    if not any(lender_upper == bank.upper() for bank in lender_pattern["values"]):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field=f"loans[{i}].lender",
                            value=lender,
                            message=lender_pattern["error"],
                            suggestion=lender_pattern["suggestion"]
                        ))

            # Validate outstanding balance (CRITICAL CHECK)
            if balance is not None:
                balance_pattern = loan_patterns["outstanding_balance"]

                # Convert to number
                try:
                    balance_num = float(balance) if balance != "" else 0
                except (ValueError, TypeError):
                    balance_num = 0

                # Check if balance is zero (RED FLAG)
                if balance_num in balance_pattern["not_equal"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field=f"loans[{i}].outstanding_balance",
                        value=balance,
                        message=balance_pattern["error"],
                        suggestion=balance_pattern["suggestion"]
                    ))

                # Check if balance is in valid range
                elif balance_num < balance_pattern["min"] or balance_num > balance_pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field=f"loans[{i}].outstanding_balance",
                        value=balance,
                        message=f"Loan balance out of typical range ({balance_pattern['min']:,} - {balance_pattern['max']:,} SEK)",
                        suggestion="Verify loan amount from source document"
                    ))

            # Validate interest rate
            if rate is not None:
                rate_pattern = loan_patterns["interest_rate"]

                try:
                    rate_num = float(rate) if rate != "" else 0
                except (ValueError, TypeError):
                    rate_num = 0

                if rate_num < rate_pattern["min"] or rate_num > rate_pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field=f"loans[{i}].interest_rate",
                        value=rate,
                        message=rate_pattern["error"],
                        suggestion=rate_pattern["suggestion"]
                    ))

        return issues

    def validate_property(self, property_data: Dict) -> List[ValidationIssue]:
        """Validate property data against patterns"""
        issues = []

        if not property_data:
            return issues

        prop_patterns = self.patterns["property"]

        # Validate property designation
        designation_field = property_data.get('property_designation', {})
        designation = designation_field.get('value') if isinstance(designation_field, dict) else designation_field

        if designation:
            pattern = prop_patterns["property_designation"]
            if not re.match(pattern["pattern"], str(designation)):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="property.property_designation",
                    value=designation,
                    message=pattern["error"],
                    suggestion=pattern["suggestion"]
                ))

        # Validate built year
        built_year_field = property_data.get('built_year', {})
        built_year = built_year_field.get('value') if isinstance(built_year_field, dict) else built_year_field

        if built_year:
            pattern = prop_patterns["built_year"]
            try:
                year = int(built_year)
                if year < pattern["min"] or year > pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="property.built_year",
                        value=built_year,
                        message=pattern["error"],
                        suggestion=pattern["suggestion"]
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="property.built_year",
                    value=built_year,
                    message="Built year must be a number",
                    suggestion="Verify from property section"
                ))

        # Validate total area
        area_field = property_data.get('total_area_sqm', {})
        area = area_field.get('value') if isinstance(area_field, dict) else area_field

        if area:
            pattern = prop_patterns["total_area_sqm"]
            try:
                area_num = float(area)
                if area_num < pattern["min"] or area_num > pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="property.total_area_sqm",
                        value=area,
                        message=pattern["error"],
                        suggestion=pattern["suggestion"]
                    ))
            except (ValueError, TypeError):
                pass  # Non-numeric area, skip validation

        return issues

    def validate_fees(self, fee_data: Dict) -> List[ValidationIssue]:
        """Validate fee structure data"""
        issues = []

        if not fee_data:
            return issues

        fee_patterns = self.patterns["fees"]

        # Validate monthly fee
        monthly_field = fee_data.get('avgift_1_rok', {})  # Swedish field name
        monthly = monthly_field.get('value') if isinstance(monthly_field, dict) else monthly_field

        if monthly:
            pattern = fee_patterns["monthly_fee"]
            try:
                monthly_num = float(monthly)
                if monthly_num < pattern["min"] or monthly_num > pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="fees.avgift_1_rok",
                        value=monthly,
                        message=pattern["error"],
                        suggestion=pattern["suggestion"]
                    ))
            except (ValueError, TypeError):
                pass

        # Validate annual fee
        annual_field = fee_data.get('avgift_arsavgift', {})  # Swedish field name
        annual = annual_field.get('value') if isinstance(annual_field, dict) else annual_field

        if annual:
            pattern = fee_patterns["annual_fee"]
            try:
                annual_num = float(annual)
                if annual_num < pattern["min"] or annual_num > pattern["max"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="fees.avgift_arsavgift",
                        value=annual,
                        message=pattern["error"],
                        suggestion=pattern["suggestion"]
                    ))
            except (ValueError, TypeError):
                pass

        return issues

    def validate_cross_references(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate cross-field relationships (Layer 2)
        Examples:
        - total_apartments == sum(apartment_distribution)
        - assets == liabilities + equity (±5%)
        - total_loans == sum(individual_loan_balances)
        """
        issues = []

        # Cross-reference 1: Apartment total check
        property_data = result.get('property_agent', {})
        total_apts_field = property_data.get('total_apartments', {})
        total_apts = total_apts_field.get('value') if isinstance(total_apts_field, dict) else total_apts_field

        apt_dist = property_data.get('apartment_breakdown', {})

        if total_apts and apt_dist and isinstance(apt_dist, dict):
            try:
                total_apts_num = int(total_apts)
                dist_sum = sum(int(v) for v in apt_dist.values() if isinstance(v, (int, str)) and str(v).isdigit())

                if total_apts_num != dist_sum:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="property.total_apartments",
                        value=f"total={total_apts}, distribution_sum={dist_sum}",
                        message=self.patterns["cross_references"]["apartment_total_check"]["error"],
                        suggestion=self.patterns["cross_references"]["apartment_total_check"]["suggestion"]
                    ))
            except (ValueError, TypeError):
                pass  # Skip if conversion fails

        # Cross-reference 2: Balance sheet equation
        financial_data = result.get('financial_agent', {})
        assets = self._get_numeric_value(financial_data, 'assets')
        liabilities = self._get_numeric_value(financial_data, 'liabilities')
        equity = self._get_numeric_value(financial_data, 'equity')

        if all(x is not None for x in [assets, liabilities, equity]):
            tolerance = self.patterns["cross_references"]["balance_sheet_equation"]["tolerance"]
            lhs = assets
            rhs = liabilities + equity
            diff_ratio = abs(lhs - rhs) / max(lhs, 1)  # Avoid division by zero

            if diff_ratio > tolerance:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="financial.balance_sheet",
                    value=f"Assets={assets:,.0f}, Liabilities+Equity={rhs:,.0f}, Diff={diff_ratio*100:.1f}%",
                    message=self.patterns["cross_references"]["balance_sheet_equation"]["error"],
                    suggestion=self.patterns["cross_references"]["balance_sheet_equation"]["suggestion"]
                ))

        # Cross-reference 3: Loan total check
        total_loans = self._get_numeric_value(financial_data, 'total_loans')
        loans = result.get('loans', [])

        if total_loans and loans:
            loan_sum = sum(
                self._get_numeric_value(loan, 'outstanding_balance') or 0
                for loan in loans
            )

            tolerance = self.patterns["cross_references"]["loan_total_check"]["tolerance"]
            if loan_sum > 0:  # Only validate if we have loan data
                diff_ratio = abs(total_loans - loan_sum) / max(total_loans, 1)

                if diff_ratio > tolerance:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="financial.total_loans",
                        value=f"Total={total_loans:,.0f}, Sum={loan_sum:,.0f}, Diff={diff_ratio*100:.1f}%",
                        message=self.patterns["cross_references"]["loan_total_check"]["error"],
                        suggestion=self.patterns["cross_references"]["loan_total_check"]["suggestion"]
                    ))

        return issues

    def validate_patterns(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate field patterns (Layer 3)
        Checks format, ranges, enums
        """
        issues = []

        # Validate loans
        loans = result.get('loans', [])
        if loans:
            issues.extend(self.validate_loans(loans))

        # Validate property
        property_data = result.get('property_agent', {})
        if property_data:
            issues.extend(self.validate_property(property_data))

        # Validate fees
        fee_data = result.get('fee_agent', {})
        if fee_data:
            issues.extend(self.validate_fees(fee_data))

        return issues

    def validate_ground_truth(self, result: Dict[str, Any], pdf_path: str) -> List[ValidationIssue]:
        """
        Validate against ground truth (Layer 4)
        Currently a placeholder - would load ground truth file if available
        """
        issues = []

        # TODO: Implement ground truth validation
        # Would check if ground truth JSON exists for this PDF
        # And compare extracted values against known-correct values

        # Example:
        # ground_truth_path = pdf_path.replace('.pdf', '_ground_truth.json')
        # if os.path.exists(ground_truth_path):
        #     with open(ground_truth_path) as f:
        #         ground_truth = json.load(f)
        #     issues.extend(self._compare_to_ground_truth(result, ground_truth))

        return issues

    def _get_numeric_value(self, data: Dict, field_name: str) -> Optional[float]:
        """Helper to extract numeric value from field (handles ExtractionField wrapper)"""
        field = data.get(field_name, {})
        value = field.get('value') if isinstance(field, dict) else field

        if value is None or value == "":
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None
