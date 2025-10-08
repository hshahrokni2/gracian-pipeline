"""
Ultra-comprehensive Pydantic schema for Swedish BRF Annual Reports.

This schema extracts EVERY fact from BRF documents (skip only signatures and boilerplate).
Designed for scalability, robustness, and maximum information capture.

MIGRATION NOTE (2025-10-07):
Week 1 Day 3-4 - Migrating to ExtractionField base classes for confidence tracking.
See base_fields.py for ExtractionField implementation.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Literal, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

# Import ExtractionField types for confidence tracking
from .base_fields import (
    StringField,
    NumberField,
    DateField,
    ListField,
    BooleanField,
    DictField,
)


# =============================================================================
# LEVEL 1: DOCUMENT METADATA
# =============================================================================

class DocumentMetadata(BaseModel):
    """Top-level document identification and context."""

    # Document Identity (System-generated)
    document_id: str = Field(..., description="Unique identifier (org_number_year)")
    document_type: Literal["arsredovisning", "ekonomisk_plan", "stadgar", "energideklaration"]

    # Extracted Fields (with confidence tracking)
    fiscal_year: Optional[NumberField] = Field(None, description="Fiscal year from PDF (extracted)")
    report_date: Optional[DateField] = Field(None, description="Report date from PDF (extracted)")
    brf_name: Optional[StringField] = Field(None, description="BRF name from PDF (extracted)")
    organization_number: Optional[StringField] = Field(None, description="Organization number from PDF (extracted)")

    # Document Quality (System-generated)
    pages_total: int = Field(..., gt=0)
    is_machine_readable: bool = True
    ocr_confidence: Optional[float] = Field(None, ge=0, le=1)

    # Processing Metadata (System-generated)
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    extraction_mode: Literal["fast", "deep", "auto"] = "auto"
    extraction_version: str = "v2.0"

    # File Information (System-generated)
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash_sha256: Optional[str] = None


# =============================================================================
# LEVEL 2: GOVERNANCE (COMPLETE DETAIL)
# =============================================================================

class BoardMember(BaseModel):
    """Individual board member with full details."""
    full_name: Optional[StringField] = Field(None, description="Board member name (extracted)")
    role: Optional[Literal["ordforande", "vice_ordforande", "ledamot", "suppleant"]] = None
    term_start: Optional[DateField] = Field(None, description="Term start date (extracted)")
    term_end: Optional[DateField] = Field(None, description="Term end date (extracted)")
    elected_at_meeting: Optional[DateField] = Field(None, description="Election date (extracted)")
    is_employee_representative: Optional[BooleanField] = Field(None, description="Employee rep status (extracted)")
    contact_info: Optional[StringField] = Field(None, description="Contact information (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class Auditor(BaseModel):
    """Auditor details."""
    name: Optional[StringField] = Field(None, description="Auditor name (extracted)")
    firm: Optional[StringField] = Field(None, description="Audit firm (extracted)")
    certification: Optional[StringField] = Field(None, description="e.g., Auktoriserad revisor (extracted)")
    contact_info: Optional[StringField] = Field(None, description="Contact information (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class GovernanceStructure(BaseModel):
    """Complete governance information."""

    # Board
    chairman: Optional[StringField] = Field(None, description="Chairman name (extracted)")
    vice_chairman: Optional[StringField] = Field(None, description="Vice chairman name (extracted)")
    board_members: List[BoardMember] = Field(default_factory=list)
    board_size: Optional[NumberField] = Field(None, description="Number of board members (extracted)")
    board_term_years: Optional[NumberField] = Field(None, description="Mandate period in years (extracted)")

    # Auditors
    primary_auditor: Optional[Auditor] = None
    deputy_auditor: Optional[Auditor] = None
    audit_period: Optional[StringField] = Field(None, description="Audit period (extracted)")

    # Nomination Committee
    nomination_committee: Optional[ListField] = Field(None, description="Nomination committee members (extracted)")
    nomination_committee_details: Optional[StringField] = Field(None, description="Nomination committee details (extracted)")

    # Annual Meeting
    annual_meeting_date: Optional[DateField] = Field(None, description="Annual meeting date (extracted)")
    annual_meeting_location: Optional[StringField] = Field(None, description="Annual meeting location (extracted)")
    annual_meeting_attendees: Optional[NumberField] = Field(None, description="Annual meeting attendees count (extracted)")
    extraordinary_meetings: Optional[ListField] = Field(None, description="Extraordinary meeting dates (extracted)")

    # Governance Documents
    stadgar_last_updated: Optional[DateField] = Field(None, description="Bylaws last updated date (extracted)")
    bylaws_references: Optional[ListField] = Field(None, description="Bylaws references (extracted)")

    # Evidence
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# LEVEL 3: FINANCIAL (ULTRA-COMPREHENSIVE)
# =============================================================================

class FinancialLineItem(BaseModel):
    """Individual line item in financial statements."""
    category: Optional[StringField] = Field(None, description="Line item category (extracted)")
    subcategory: Optional[StringField] = Field(None, description="Line item subcategory (extracted)")
    description: Optional[StringField] = Field(None, description="Line item description (extracted)")
    amount_current_year: Optional[NumberField] = Field(None, description="Current year amount (extracted)")
    amount_previous_year: Optional[NumberField] = Field(None, description="Previous year amount (extracted)")
    note_reference: Optional[NumberField] = Field(None, description="Note reference number (extracted)")
    percentage_of_total: Optional[NumberField] = Field(None, description="Percentage of total (extracted)")
    source_page: Optional[int] = None


class IncomeStatement(BaseModel):
    """Complete income statement (Resultaträkning)."""

    # Revenue (Intäkter)
    revenue_total: Optional[NumberField] = Field(None, description="Total revenue (extracted)")
    revenue_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Expenses (Kostnader)
    expenses_total: Optional[NumberField] = Field(None, description="Total expenses (extracted)")
    expenses_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Operating Result
    operating_result: Optional[NumberField] = Field(None, description="Operating result (extracted)")

    # Financial Items
    financial_income: Optional[NumberField] = Field(None, description="Financial income (extracted)")
    financial_expenses: Optional[NumberField] = Field(None, description="Financial expenses (extracted)")

    # Result
    result_before_tax: Optional[NumberField] = Field(None, description="Result before tax (extracted)")
    tax: Optional[NumberField] = Field(None, description="Tax (extracted)")
    result_after_tax: Optional[NumberField] = Field(None, description="Result after tax (extracted)")

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class BalanceSheet(BaseModel):
    """Complete balance sheet (Balansräkning)."""

    # Assets
    assets_total: Optional[NumberField] = Field(None, description="Total assets (extracted)")
    fixed_assets: Optional[NumberField] = Field(None, description="Fixed assets (extracted)")
    current_assets: Optional[NumberField] = Field(None, description="Current assets (extracted)")
    assets_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Liabilities
    liabilities_total: Optional[NumberField] = Field(None, description="Total liabilities (extracted)")
    equity_total: Optional[NumberField] = Field(None, description="Total equity (extracted)")
    long_term_liabilities: Optional[NumberField] = Field(None, description="Long-term liabilities (extracted)")
    short_term_liabilities: Optional[NumberField] = Field(None, description="Short-term liabilities (extracted)")
    liabilities_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")

    @model_validator(mode='after')
    def check_balance(self):
        """Validate balance sheet equation: Assets = Liabilities + Equity

        Uses tolerant validation (6% threshold) - flags issues but never nulls data.
        Extracts .value from NumberField objects for comparison.
        Updates liabilities_total.validation_status if imbalance detected.
        """
        # Check if all required fields are present
        if self.liabilities_total is None or self.assets_total is None or self.equity_total is None:
            return self

        # Extract numeric values from NumberField objects
        liabilities = self.liabilities_total.value if hasattr(self.liabilities_total, 'value') else self.liabilities_total
        assets = self.assets_total.value if hasattr(self.assets_total, 'value') else self.assets_total
        equity = self.equity_total.value if hasattr(self.equity_total, 'value') else self.equity_total

        # Apply balance sheet equation validation with 6% tolerance
        if all(x is not None for x in [liabilities, assets, equity]):
            from decimal import Decimal
            calculated_total = liabilities + equity
            tolerance = abs(assets * Decimal('0.06'))  # 6% tolerance for rounding/extraction errors
            difference = abs(assets - calculated_total)

            if difference > tolerance:
                # Create new NumberField with validation_status='warning' (tolerant validation)
                from gracian_pipeline.models.base_fields import NumberField

                self.liabilities_total = NumberField(
                    value=self.liabilities_total.value,
                    confidence=self.liabilities_total.confidence,
                    source=self.liabilities_total.source,
                    evidence_pages=self.liabilities_total.evidence_pages,
                    extraction_method=self.liabilities_total.extraction_method,
                    model_used=self.liabilities_total.model_used,
                    validation_status='warning',  # Set warning status
                    alternative_values=self.liabilities_total.alternative_values,
                    extraction_timestamp=self.liabilities_total.extraction_timestamp
                )

        return self


class CashFlowStatement(BaseModel):
    """Cash flow statement (Kassaflödesanalys)."""
    operating_activities: Optional[NumberField] = Field(None, description="Operating activities (extracted)")
    investing_activities: Optional[NumberField] = Field(None, description="Investing activities (extracted)")
    financing_activities: Optional[NumberField] = Field(None, description="Financing activities (extracted)")
    cash_flow_total: Optional[NumberField] = Field(None, description="Total cash flow (extracted)")
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# CALCULATED FINANCIAL METRICS (WITH TOLERANT VALIDATION)
# Week 2 Day 1-2 Implementation (2025-10-07)
# =============================================================================

def get_financial_tolerance(amount: float) -> float:
    """
    Calculate dynamic tolerance based on amount magnitude.

    Thresholds based on Swedish BRF report analysis:
    - Small amounts (<100k SEK): ±5k or ±15% (OCR errors common)
    - Medium amounts (100k-10M SEK): ±50k or ±10% (balance precision)
    - Large amounts (>10M SEK): ±500k or ±5% (tight relative tolerance)

    Args:
        amount: Financial amount in SEK

    Returns:
        Tolerance threshold in SEK

    Example:
        >>> get_financial_tolerance(50_000)  # Small amount
        7500.0  # max(5k, 50k * 0.15) = 7.5k
        >>> get_financial_tolerance(5_000_000)  # Medium amount
        500000.0  # max(50k, 5M * 0.10) = 500k
        >>> get_financial_tolerance(50_000_000)  # Large amount
        2500000.0  # max(500k, 50M * 0.05) = 2.5M
    """
    amount = abs(amount)  # Handle negative amounts

    if amount < 100_000:
        return max(5_000, amount * 0.15)
    elif amount < 10_000_000:
        return max(50_000, amount * 0.10)
    else:
        return max(500_000, amount * 0.05)


def get_per_sqm_tolerance(value_per_sqm: float, metric_type: str = "debt") -> float:
    """
    Calculate tolerance for per-unit metrics (kr/m², kr/m²/år).

    Thresholds for Swedish BRF per-unit metrics:
    - Debt per sqm (typically 10k-50k kr/m²): ±10% or ±1,000 kr minimum
    - Fee per sqm (typically 500-2,000 kr/m²/år): ±10% or ±100 kr minimum

    Week 2 Day 5: Specialized tolerance function for per-unit metrics to fix
    validation threshold calibration issues.

    Args:
        value_per_sqm: Per-unit value (kr/m² or kr/m²/år)
        metric_type: "debt" or "fee"

    Returns:
        Tolerance threshold in same units as input

    Examples:
        >>> get_per_sqm_tolerance(20000, "debt")  # Debt per sqm
        2000.0  # max(1000, 20000 * 0.10) = 2000 kr/m²

        >>> get_per_sqm_tolerance(600, "fee")  # Fee per sqm annual
        100.0  # max(100, 600 * 0.10) = 100 kr/m²/år
    """
    value_per_sqm = abs(value_per_sqm)

    if metric_type == "debt":
        # Debt per sqm: ±10% or ±1,000 kr/m² minimum
        return max(1_000, value_per_sqm * 0.10)
    elif metric_type == "fee":
        # Fee per sqm: ±10% or ±100 kr/m²/år minimum
        return max(100, value_per_sqm * 0.10)
    else:
        # Default: ±10% or ±500 kr minimum
        return max(500, value_per_sqm * 0.10)


class CalculatedFinancialMetrics(BaseModel):
    """
    Financial metrics with tolerant validation.

    Key principles:
    1. NEVER null data - preserve both extracted and calculated values
    2. 3-tier validation: valid (green), warning (yellow), error (red)
    3. Dynamic tolerance based on amount magnitude
    4. Cross-validate extracted vs calculated values

    Example metrics:
    - debt_per_sqm: Total debt / Total area (SEK/m²)
    - solidarity_percent: (Equity / Assets) * 100 (%)
    - fee_per_sqm_annual: (Monthly fee * 12) / Area (SEK/m²/år)

    Week 2 Day 1-2 Implementation (2025-10-07)
    """

    # Debt per square meter (SEK/m²)
    total_debt_extracted: Optional[NumberField] = Field(None, description="Total debt extracted from balance sheet")
    total_area_sqm_extracted: Optional[NumberField] = Field(None, description="Total area extracted from property details")
    debt_per_sqm_extracted: Optional[NumberField] = Field(None, description="Debt per sqm extracted directly")
    debt_per_sqm_calculated: Optional[float] = Field(None, description="Debt per sqm calculated (total_debt / total_area_sqm)")

    # Solidarity percentage (Soliditet)
    equity_extracted: Optional[NumberField] = Field(None, description="Equity extracted from balance sheet")
    assets_extracted: Optional[NumberField] = Field(None, description="Total assets extracted from balance sheet")
    solidarity_percent_extracted: Optional[NumberField] = Field(None, description="Solidarity % extracted directly")
    solidarity_percent_calculated: Optional[float] = Field(None, description="Solidarity % calculated (equity / assets * 100)")

    # Fee per square meter (Avgift per m²/år)
    monthly_fee_extracted: Optional[NumberField] = Field(None, description="Monthly fee extracted")
    apartment_area_extracted: Optional[NumberField] = Field(None, description="Apartment area extracted")
    fee_per_sqm_annual_extracted: Optional[NumberField] = Field(None, description="Annual fee per sqm extracted")
    fee_per_sqm_annual_calculated: Optional[float] = Field(None, description="Annual fee per sqm calculated (monthly_fee * 12 / area)")

    # Validation metadata (3-tier system)
    validation_status: str = Field(default="unknown", description="Overall validation status: valid|warning|error|unknown|no_data")
    validation_warnings: List[str] = Field(default_factory=list, description="List of validation warnings (yellow)")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors (red)")
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Aggregated confidence from all metrics")

    # Metric-specific validation status
    debt_per_sqm_status: str = Field(default="unknown", description="Validation status for debt_per_sqm")
    solidarity_percent_status: str = Field(default="unknown", description="Validation status for solidarity_percent")
    fee_per_sqm_status: str = Field(default="unknown", description="Validation status for fee_per_sqm")

    @model_validator(mode='after')
    def calculate_and_validate_with_tolerance(self):
        """
        Calculate derived metrics and perform tolerant validation.

        Validation tiers:
        1. Pass (green): Within tolerance → status = "valid", confidence = 0.95
        2. Warning (yellow): Within 2x tolerance → status = "warning", confidence = 0.70
        3. Error (red): Beyond 2x tolerance → status = "error", confidence = 0.40

        CRITICAL: All tiers preserve extracted data. Never null.
        """
        confidences = []

        # ============================================================
        # METRIC 1: Debt per Square Meter
        # ============================================================
        if self.total_debt_extracted and self.total_debt_extracted.value is not None:
            if self.total_area_sqm_extracted and self.total_area_sqm_extracted.value is not None:
                debt = self.total_debt_extracted.value
                area = self.total_area_sqm_extracted.value

                if area > 0:  # Avoid division by zero
                    # Calculate derived metric
                    # Week 2 Day 5 Fix: Assume debt is in tkr, convert to kr for kr/m² output
                    calc = (debt * 1000) / area  # Convert tkr → kr, then divide by m²
                    self.debt_per_sqm_calculated = round(calc, 0)

                    # If extracted value exists, cross-validate
                    if self.debt_per_sqm_extracted and self.debt_per_sqm_extracted.value is not None:
                        extracted = self.debt_per_sqm_extracted.value
                        diff = abs(extracted - calc)
                        # Week 2 Day 5 Fix: Use specialized per-sqm tolerance function
                        tolerance = get_per_sqm_tolerance(calc, metric_type="debt")

                        if diff <= tolerance:
                            # PASS: Within tolerance
                            self.debt_per_sqm_status = "valid"
                            confidences.append(0.95)
                        elif diff <= tolerance * 2:
                            # WARNING: Within 2x tolerance
                            self.debt_per_sqm_status = "warning"
                            self.validation_warnings.append(
                                f"debt_per_sqm: extracted={extracted:.0f}, calculated={calc:.0f}, "
                                f"diff={diff:.0f} SEK/m² (tolerance={tolerance:.0f}, 2x={tolerance*2:.0f})"
                            )
                            confidences.append(0.70)
                        else:
                            # ERROR: Beyond 2x tolerance (but still preserve data)
                            self.debt_per_sqm_status = "error"
                            self.validation_errors.append(
                                f"debt_per_sqm: Large discrepancy - extracted={extracted:.0f}, "
                                f"calculated={calc:.0f}, diff={diff:.0f} SEK/m² (>2x tolerance)"
                            )
                            confidences.append(0.40)
                    else:
                        # No extracted value to compare, calculated only
                        self.debt_per_sqm_status = "calculated_only"
                        confidences.append(0.85)

        # ============================================================
        # METRIC 2: Solidarity Percentage
        # ============================================================
        if self.equity_extracted and self.equity_extracted.value is not None:
            if self.assets_extracted and self.assets_extracted.value is not None:
                equity = self.equity_extracted.value
                assets = self.assets_extracted.value

                if assets > 0:  # Avoid division by zero
                    # Calculate derived metric
                    calc = (equity / assets) * 100
                    self.solidarity_percent_calculated = round(calc, 1)

                    # If extracted value exists, cross-validate
                    if self.solidarity_percent_extracted and self.solidarity_percent_extracted.value is not None:
                        extracted = self.solidarity_percent_extracted.value
                        diff = abs(extracted - calc)
                        tolerance = 2.0  # ±2 percentage points

                        if diff <= tolerance:
                            # PASS: Within tolerance
                            self.solidarity_percent_status = "valid"
                            confidences.append(0.95)
                        elif diff <= tolerance * 2:
                            # WARNING: Within 2x tolerance
                            self.solidarity_percent_status = "warning"
                            self.validation_warnings.append(
                                f"solidarity_percent: extracted={extracted:.1f}%, calculated={calc:.1f}%, "
                                f"diff={diff:.1f} pp (tolerance={tolerance:.1f} pp, 2x={tolerance*2:.1f} pp)"
                            )
                            confidences.append(0.70)
                        else:
                            # ERROR: Beyond 2x tolerance (but still preserve data)
                            self.solidarity_percent_status = "error"
                            self.validation_errors.append(
                                f"solidarity_percent: Large discrepancy - extracted={extracted:.1f}%, "
                                f"calculated={calc:.1f}%, diff={diff:.1f} pp (>2x tolerance)"
                            )
                            confidences.append(0.40)
                    else:
                        # No extracted value to compare, calculated only
                        self.solidarity_percent_status = "calculated_only"
                        confidences.append(0.85)

        # ============================================================
        # METRIC 3: Fee per Square Meter (Annual)
        # ============================================================
        if self.monthly_fee_extracted and self.monthly_fee_extracted.value is not None:
            if self.apartment_area_extracted and self.apartment_area_extracted.value is not None:
                monthly_fee = self.monthly_fee_extracted.value
                area = self.apartment_area_extracted.value

                if area > 0:  # Avoid division by zero
                    # Calculate derived metric (annual)
                    calc = (monthly_fee * 12) / area
                    self.fee_per_sqm_annual_calculated = round(calc, 0)

                    # If extracted value exists, cross-validate
                    if self.fee_per_sqm_annual_extracted and self.fee_per_sqm_annual_extracted.value is not None:
                        extracted = self.fee_per_sqm_annual_extracted.value
                        diff = abs(extracted - calc)
                        # Week 2 Day 5 Fix: Use specialized per-sqm tolerance function for fees
                        tolerance = get_per_sqm_tolerance(calc, metric_type="fee")

                        if diff <= tolerance:
                            # PASS: Within tolerance
                            self.fee_per_sqm_status = "valid"
                            confidences.append(0.95)
                        elif diff <= tolerance * 2:
                            # WARNING: Within 2x tolerance
                            self.fee_per_sqm_status = "warning"
                            self.validation_warnings.append(
                                f"fee_per_sqm_annual: extracted={extracted:.0f}, calculated={calc:.0f}, "
                                f"diff={diff:.0f} SEK/m²/år (tolerance={tolerance:.0f}, 2x={tolerance*2:.0f})"
                            )
                            confidences.append(0.70)
                        else:
                            # ERROR: Beyond 2x tolerance (but still preserve data)
                            self.fee_per_sqm_status = "error"
                            self.validation_errors.append(
                                f"fee_per_sqm_annual: Large discrepancy - extracted={extracted:.0f}, "
                                f"calculated={calc:.0f}, diff={diff:.0f} SEK/m²/år (>2x tolerance)"
                            )
                            confidences.append(0.40)
                    else:
                        # No extracted value to compare, calculated only
                        self.fee_per_sqm_status = "calculated_only"
                        confidences.append(0.85)

        # ============================================================
        # AGGREGATE VALIDATION STATUS
        # ============================================================
        if confidences:
            self.overall_confidence = sum(confidences) / len(confidences)

            # Determine overall status based on individual metrics
            statuses = [self.debt_per_sqm_status, self.solidarity_percent_status, self.fee_per_sqm_status]
            if any(s == "error" for s in statuses):
                self.validation_status = "error"
            elif any(s == "warning" for s in statuses):
                self.validation_status = "warning"
            elif any(s == "valid" for s in statuses):
                self.validation_status = "valid"
            elif any(s == "calculated_only" for s in statuses):
                self.validation_status = "calculated_only"
            else:
                self.validation_status = "unknown"
        else:
            self.validation_status = "no_data"
            self.overall_confidence = 0.0

        return self


class FinancialData(BaseModel):
    """Complete financial information."""
    income_statement: Optional[IncomeStatement] = None
    balance_sheet: Optional[BalanceSheet] = None
    cash_flow: Optional[CashFlowStatement] = None
    calculated_metrics: Optional[CalculatedFinancialMetrics] = Field(
        None,
        description="Calculated financial metrics with tolerant validation (Week 2 Day 1-2)"
    )


# =============================================================================
# MULTI-YEAR FINANCIAL DATA (DYNAMIC 2-10+ YEARS)
# =============================================================================

class MultiYearTableOrientation(str, Enum):
    """Enum for multi-year table orientation detection."""
    YEARS_AS_COLUMNS = "years_columns"  # Most common: years in header
    YEARS_AS_ROWS = "years_rows"        # Years in first column
    MIXED = "mixed"                      # Mixed orientation
    UNKNOWN = "unknown"                  # Could not determine


class YearlyFinancialData(BaseModel):
    """
    Single year of financial data with Swedish-first semantic fields.

    Week 2 Day 4: Swedish-first semantic fields added.
    Swedish fields are primary, English fields are aliases.
    """

    # Required year identifier
    year: int = Field(..., ge=1900, le=2100, description="Fiscal year")

    # =============================================================================
    # SWEDISH-FIRST FIELDS (Primary - Week 2 Day 4)
    # =============================================================================

    # Income statement
    nettoomsattning_tkr: Optional[NumberField] = Field(None, description="Nettoomsättning (net revenue) in tkr (extracted)")
    driftskostnader_tkr: Optional[NumberField] = Field(None, description="Driftskostnader (operating expenses) in tkr (extracted)")
    driftsoverskott_tkr: Optional[NumberField] = Field(None, description="Driftsöverskott (operating surplus) in tkr (extracted)")
    arsresultat_tkr: Optional[NumberField] = Field(None, description="Årsresultat (annual result) in tkr (extracted)")

    # Balance sheet
    tillgangar_tkr: Optional[NumberField] = Field(None, description="Tillgångar (assets) in tkr (extracted)")
    skulder_tkr: Optional[NumberField] = Field(None, description="Skulder (liabilities) in tkr (extracted)")
    eget_kapital_tkr: Optional[NumberField] = Field(None, description="Eget kapital (equity) in tkr (extracted)")
    soliditet_procent: Optional[NumberField] = Field(None, description="Soliditet (solidarity) in % (extracted)")

    # Metadata fields (Week 2 Day 4)
    terminology_found: Optional[str] = Field(None, description="Which Swedish terminology was found: 'nettoomsättning', 'intäkter', 'omsättning'")
    unit_verified: Optional[bool] = Field(None, description="Whether units (tkr, SEK, etc.) were explicitly verified")

    # =============================================================================
    # ENGLISH ALIAS FIELDS (Secondary - for backward compatibility)
    # =============================================================================

    # Core financial metrics (with confidence tracking)
    net_revenue_tkr: Optional[NumberField] = Field(None, description="Net revenue in tkr (ALIAS for nettoomsättning_tkr)")
    operating_expenses_tkr: Optional[NumberField] = Field(None, description="Operating expenses in tkr (ALIAS for driftskostnader_tkr)")
    operating_surplus_tkr: Optional[NumberField] = Field(None, description="Operating surplus in tkr (ALIAS for driftsöverskott_tkr)")
    total_assets_tkr: Optional[NumberField] = Field(None, description="Total assets in tkr (ALIAS for tillgångar_tkr)")
    total_liabilities_tkr: Optional[NumberField] = Field(None, description="Total liabilities in tkr (ALIAS for skulder_tkr)")
    equity_tkr: Optional[NumberField] = Field(None, description="Equity in tkr (ALIAS for eget_kapital_tkr)")
    solidarity_percent: Optional[NumberField] = Field(None, description="Solidarity percentage (ALIAS for soliditet_procent)")

    # Metadata
    is_complete: bool = Field(False, description="All core fields extracted successfully")
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence for this year")
    source_page: Optional[int] = Field(None, description="Page where this year's data was found")

    @model_validator(mode='after')
    def sync_swedish_english_financial_aliases(self):
        """
        Synchronize Swedish primary fields with English alias fields.
        Week 2 Day 4: Swedish-first semantic fields.

        Strategy:
        - If Swedish field exists, copy to English alias
        - If English field exists but Swedish doesn't, copy to Swedish
        - Prefer Swedish as source of truth
        """
        # Revenue: nettoomsättning_tkr <-> net_revenue_tkr
        if self.nettoomsattning_tkr and not self.net_revenue_tkr:
            self.net_revenue_tkr = self.nettoomsattning_tkr
        elif self.net_revenue_tkr and not self.nettoomsattning_tkr:
            self.nettoomsattning_tkr = self.net_revenue_tkr

        # Expenses: driftskostnader_tkr <-> operating_expenses_tkr
        if self.driftskostnader_tkr and not self.operating_expenses_tkr:
            self.operating_expenses_tkr = self.driftskostnader_tkr
        elif self.operating_expenses_tkr and not self.driftskostnader_tkr:
            self.driftskostnader_tkr = self.operating_expenses_tkr

        # Surplus: driftsöverskott_tkr <-> operating_surplus_tkr
        if self.driftsoverskott_tkr and not self.operating_surplus_tkr:
            self.operating_surplus_tkr = self.driftsoverskott_tkr
        elif self.operating_surplus_tkr and not self.driftsoverskott_tkr:
            self.driftsoverskott_tkr = self.operating_surplus_tkr

        # Assets: tillgångar_tkr <-> total_assets_tkr
        if self.tillgangar_tkr and not self.total_assets_tkr:
            self.total_assets_tkr = self.tillgangar_tkr
        elif self.total_assets_tkr and not self.tillgangar_tkr:
            self.tillgangar_tkr = self.total_assets_tkr

        # Liabilities: skulder_tkr <-> total_liabilities_tkr
        if self.skulder_tkr and not self.total_liabilities_tkr:
            self.total_liabilities_tkr = self.skulder_tkr
        elif self.total_liabilities_tkr and not self.skulder_tkr:
            self.skulder_tkr = self.total_liabilities_tkr

        # Equity: eget_kapital_tkr <-> equity_tkr
        if self.eget_kapital_tkr and not self.equity_tkr:
            self.equity_tkr = self.eget_kapital_tkr
        elif self.equity_tkr and not self.eget_kapital_tkr:
            self.eget_kapital_tkr = self.equity_tkr

        # Solidarity: soliditet_procent <-> solidarity_percent
        if self.soliditet_procent and not self.solidarity_percent:
            self.solidarity_percent = self.soliditet_procent
        elif self.solidarity_percent and not self.soliditet_procent:
            self.soliditet_procent = self.solidarity_percent

        return self


class DynamicMultiYearOverview(BaseModel):
    """
    Flexible multi-year financial data container.
    Handles 2-10+ years without hardcoded columns.
    Designed for Swedish BRF reports with varying year counts.
    """

    # Core data
    years: List[YearlyFinancialData] = Field(default_factory=list, description="List of yearly financial data")
    years_covered: List[int] = Field(default_factory=list, description="Sorted list of years [2021, 2022, 2023, ...]")
    num_years: int = Field(0, description="Number of years extracted")

    # Extraction metadata
    table_orientation: MultiYearTableOrientation = Field(
        default=MultiYearTableOrientation.UNKNOWN,
        description="How years are organized in source table"
    )
    extraction_method: str = Field(default="unknown", description="Method used for extraction")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall extraction confidence")

    @model_validator(mode='after')
    def compute_metadata(self):
        """Auto-compute years_covered and num_years from years list."""
        self.years_covered = sorted([y.year for y in self.years])
        self.num_years = len(self.years_covered)
        return self

    def get_year(self, year: int) -> Optional[YearlyFinancialData]:
        """
        Retrieve data for specific year.

        Args:
            year: Fiscal year to retrieve

        Returns:
            YearlyFinancialData if found, None otherwise
        """
        for y in self.years:
            if y.year == year:
                return y
        return None

    def get_metric_timeseries(self, metric: str) -> Dict[int, Optional[float]]:
        """
        Extract time series for a specific metric across all years.

        Args:
            metric: Field name (e.g., 'net_revenue_tkr', 'solidarity_percent')

        Returns:
            Dictionary mapping year to value: {2021: 1234.5, 2022: 1456.7, ...}
        """
        result = {}
        for y in self.years:
            field = getattr(y, metric, None)
            if field and isinstance(field, NumberField):
                result[y.year] = field.value
            else:
                result[y.year] = None
        return result


# =============================================================================
# LEVEL 4: NOTES (COMPLETE EXTRACTION)
# =============================================================================

class Note(BaseModel):
    """Individual note with full details."""
    note_number: Optional[NumberField] = Field(None, description="Note number (extracted)")
    title: Optional[StringField] = Field(None, description="Note title (extracted)")
    content: Optional[StringField] = Field(None, description="Note content (extracted)")
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class BuildingDetails(BaseModel):
    """Note 8: Building details (ultra-comprehensive)."""

    # Acquisition Values
    opening_acquisition_value: Optional[NumberField] = Field(None, description="Opening acquisition value (extracted)")
    additions: Optional[NumberField] = Field(None, description="Additions (extracted)")
    disposals: Optional[NumberField] = Field(None, description="Disposals (extracted)")
    closing_acquisition_value: Optional[NumberField] = Field(None, description="Closing acquisition value (extracted)")

    # Depreciation
    opening_depreciation: Optional[NumberField] = Field(None, description="Opening depreciation (extracted)")
    current_year_depreciation: Optional[NumberField] = Field(None, description="Current year depreciation (extracted)")
    disposals_depreciation: Optional[NumberField] = Field(None, description="Disposals depreciation (extracted)")
    closing_depreciation: Optional[NumberField] = Field(None, description="Closing depreciation (extracted)")

    # Residual Values
    planned_residual_value: Optional[NumberField] = Field(None, description="Planned residual value (extracted)")

    # Tax Values
    tax_assessment_building: Optional[NumberField] = Field(None, description="Tax assessment building (extracted)")
    tax_assessment_land: Optional[NumberField] = Field(None, description="Tax assessment land (extracted)")
    tax_assessment_year: Optional[NumberField] = Field(None, description="Tax assessment year (extracted)")

    # Depreciation Method
    depreciation_method: Optional[StringField] = Field(None, description="Depreciation method (extracted)")
    depreciation_period_years: Optional[NumberField] = Field(None, description="Depreciation period years (extracted)")

    # Components (if detailed)
    building_components: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed component breakdown")

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class ReceivablesBreakdown(BaseModel):
    """Note 9: Receivables (every line item)."""
    tax_account: Optional[NumberField] = Field(None, description="Tax account (extracted)")
    vat_deduction: Optional[NumberField] = Field(None, description="VAT deduction (extracted)")
    client_funds: Optional[NumberField] = Field(None, description="Client funds (extracted)")
    receivables: Optional[NumberField] = Field(None, description="Receivables (extracted)")
    other_deductions: Optional[NumberField] = Field(None, description="Other deductions (extracted)")
    prepaid_expenses: Optional[NumberField] = Field(None, description="Prepaid expenses (extracted)")
    accrued_income: Optional[NumberField] = Field(None, description="Accrued income (extracted)")
    other_items: List[FinancialLineItem] = Field(default_factory=list)
    total: Optional[NumberField] = Field(None, description="Total receivables (extracted)")
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class NotesCollection(BaseModel):
    """All notes from annual report."""

    # Standard Notes
    note_1_accounting_principles: Optional[Note] = None
    note_2_revenue: Optional[Note] = None
    note_3_personnel: Optional[Note] = None
    note_4_operating_costs: Optional[Note] = None
    note_5_financial_items: Optional[Note] = None
    note_6_tax: Optional[Note] = None
    note_7_intangible_assets: Optional[Note] = None
    note_8_buildings: Optional[BuildingDetails] = None
    note_9_receivables: Optional[ReceivablesBreakdown] = None
    note_10_cash: Optional[Note] = None
    note_11_equity: Optional[Note] = None
    note_12_liabilities: Optional[Note] = None
    note_13_contingencies: Optional[Note] = None
    note_14_pledged_assets: Optional[Note] = None
    note_15_related_parties: Optional[Note] = None

    # Additional Notes (variable)
    additional_notes: List[Note] = Field(default_factory=list)

    # Count
    total_notes: int = 0


# =============================================================================
# LEVEL 5: PROPERTY (MAXIMUM DETAIL)
# =============================================================================

class ApartmentUnit(BaseModel):
    """Individual apartment details."""
    apartment_number: Optional[StringField] = Field(None, description="Apartment number (extracted)")
    room_count: Optional[NumberField] = Field(None, description="Number of rooms (extracted)")
    size_sqm: Optional[NumberField] = Field(None, description="Size in sqm (extracted)")
    floor: Optional[NumberField] = Field(None, description="Floor number (extracted)")
    monthly_fee: Optional[NumberField] = Field(None, description="Monthly fee (extracted)")
    owner_name: Optional[StringField] = Field(None, description="Owner name if public (extracted)")


class ApartmentDistribution(BaseModel):
    """Apartment distribution by size."""
    one_room: int = Field(0, alias="1_rok")
    two_rooms: int = Field(0, alias="2_rok")
    three_rooms: int = Field(0, alias="3_rok")
    four_rooms: int = Field(0, alias="4_rok")
    five_rooms: int = Field(0, alias="5_rok")
    more_than_five: int = Field(0, alias=">5_rok")

    class Config:
        populate_by_name = True

    @property
    def total_apartments(self) -> int:
        return sum([
            self.one_room, self.two_rooms, self.three_rooms,
            self.four_rooms, self.five_rooms, self.more_than_five
        ])


class CommercialTenant(BaseModel):
    """Commercial tenant information."""
    business_name: Optional[StringField] = Field(None, description="Business name (extracted)")
    business_type: Optional[StringField] = Field(None, description="Business type (extracted)")
    lease_area_sqm: Optional[NumberField] = Field(None, description="Lease area sqm (extracted)")
    lease_start_date: Optional[DateField] = Field(None, description="Lease start date (extracted)")
    lease_end_date: Optional[DateField] = Field(None, description="Lease end date (extracted)")
    annual_rent: Optional[NumberField] = Field(None, description="Annual rent (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class CommonArea(BaseModel):
    """Common area/facility."""
    name: Optional[StringField] = Field(None, description="Common area name (extracted)")
    area_type: Optional[Literal["gym", "laundry", "storage", "garage", "courtyard", "sauna", "other"]] = None
    size_sqm: Optional[NumberField] = Field(None, description="Size sqm (extracted)")
    description: Optional[StringField] = Field(None, description="Description (extracted)")
    maintenance_responsibility: Optional[StringField] = Field(None, description="Maintenance responsibility (extracted)")


class PropertyDetails(BaseModel):
    """Ultra-comprehensive property information."""

    # Property Identity (Extracted with confidence tracking)
    property_designation: Optional[StringField] = Field(None, description="Fastighetsbeteckning (extracted)")
    address: Optional[StringField] = Field(None, description="Address (extracted)")
    postal_code: Optional[StringField] = Field(None, description="Postal code (extracted)")
    city: Optional[StringField] = Field(None, description="City (extracted)")
    municipality: Optional[StringField] = Field(None, description="Municipality (extracted)")
    county: Optional[StringField] = Field(None, description="County (extracted)")
    coordinates: Optional[DictField] = Field(None, description="lat/lng coordinates (extracted)")

    # Building Information (Extracted with confidence tracking)
    built_year: Optional[NumberField] = Field(None, description="Year built (extracted)")
    renovation_years: Optional[ListField] = Field(None, description="Renovation years (extracted)")
    building_type: Optional[StringField] = Field(None, description="Building type (extracted)")
    number_of_buildings: Optional[NumberField] = Field(None, description="Number of buildings (extracted)")
    number_of_floors: Optional[NumberField] = Field(None, description="Number of floors (extracted)")
    total_area_sqm: Optional[NumberField] = Field(None, description="Total area sqm (extracted)")
    living_area_sqm: Optional[NumberField] = Field(None, description="Living area sqm (extracted)")
    commercial_area_sqm: Optional[NumberField] = Field(None, description="Commercial area sqm (extracted)")

    # Apartments (Extracted with confidence tracking)
    total_apartments: Optional[NumberField] = Field(None, description="Total apartments (extracted)")
    apartment_distribution: Optional[ApartmentDistribution] = None
    apartment_units: List[ApartmentUnit] = Field(default_factory=list, description="If detailed list available")

    # Commercial (Extracted with confidence tracking)
    commercial_tenants: List[CommercialTenant] = Field(default_factory=list)
    number_of_commercial_units: Optional[NumberField] = Field(None, description="Number of commercial units (extracted)")

    # Common Areas (Structural - list of complex objects)
    common_areas: List[CommonArea] = Field(default_factory=list)

    # Land (Extracted with confidence tracking)
    land_area_sqm: Optional[NumberField] = Field(None, description="Land area sqm (extracted)")
    land_lease: Optional[BooleanField] = Field(None, description="Land lease (extracted)")
    land_lease_expiry: Optional[DateField] = Field(None, description="Land lease expiry (extracted)")

    # Ownership (Extracted with confidence tracking)
    cooperative_type: Optional[Literal["bostadsratt", "hyresratt", "mixed"]] = None
    samfallighet_percentage: Optional[NumberField] = Field(None, description="Samfällighet percentage (extracted)")
    samfallighet_description: Optional[StringField] = Field(None, description="Samfällighet description (extracted)")

    # Energy (Extracted with confidence tracking)
    energy_class: Optional[StringField] = Field(None, description="Energy class (extracted)")
    energy_performance_kwh_sqm_year: Optional[NumberField] = Field(None, description="Energy performance kWh/sqm/year (extracted)")
    energy_declaration_date: Optional[DateField] = Field(None, description="Energy declaration date (extracted)")
    heating_type: Optional[StringField] = Field(None, description="Heating type (extracted)")

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# LEVEL 6: FEES & FINANCES (DETAILED)
# =============================================================================

class FeeStructure(BaseModel):
    """
    Complete fee structure with Swedish-first semantic fields.

    Week 2 Day 4: Swedish-first semantic fields added.
    Swedish fields are primary, English fields are aliases.
    """

    # =============================================================================
    # SWEDISH-FIRST FIELDS (Primary - Week 2 Day 4)
    # =============================================================================

    # Annual fees (most common in Swedish BRF documents)
    arsavgift_per_sqm_total: Optional[NumberField] = Field(None, description="Årsavgift kr/m²/år (most common, extracted)")
    arsavgift_per_apartment_avg: Optional[NumberField] = Field(None, description="Genomsnittlig årsavgift kr/lägenhet/år (extracted)")

    # Monthly fees (less common but present)
    manadsavgift_per_sqm: Optional[NumberField] = Field(None, description="Månadsavgift kr/m²/mån (extracted)")
    manadsavgift_per_apartment_avg: Optional[NumberField] = Field(None, description="Genomsnittlig månadsavgift kr/lägenhet/mån (extracted)")

    # What's included in fee (Swedish terminology)
    inkluderar_vatten: Optional[BooleanField] = Field(None, description="Inkluderar vatten (water included, extracted)")
    inkluderar_uppvarmning: Optional[BooleanField] = Field(None, description="Inkluderar uppvärmning (heating included, extracted)")
    inkluderar_el: Optional[BooleanField] = Field(None, description="Inkluderar el (electricity included, extracted)")
    inkluderar_bredband: Optional[BooleanField] = Field(None, description="Inkluderar bredband (broadband included, extracted)")

    # Metadata fields (Week 2 Day 4)
    terminology_found: Optional[str] = Field(None, description="Which terminology was found in document: 'årsavgift', 'månadsavgift', 'avgift', etc.")
    unit_verified: Optional[bool] = Field(None, description="Whether unit (kr/m²/år, kr/m²/mån) was explicitly verified in source")

    # =============================================================================
    # ENGLISH ALIAS FIELDS (Secondary - for backward compatibility)
    # =============================================================================

    # Current Fees (Extracted with confidence tracking)
    monthly_fee_average: Optional[NumberField] = Field(None, description="Monthly fee average (ALIAS for månadsavgift_per_apartment_avg)")
    monthly_fee_per_sqm: Optional[NumberField] = Field(None, description="Monthly fee per sqm (ALIAS for månadsavgift_per_sqm)")
    annual_fee_per_sqm: Optional[NumberField] = Field(None, description="Annual fee per sqm (ALIAS for årsavgift_per_sqm_total)")

    # Fee by Apartment Size (Extracted with confidence tracking)
    fee_1_rok: Optional[NumberField] = Field(None, description="Fee 1 rok (extracted)")
    fee_2_rok: Optional[NumberField] = Field(None, description="Fee 2 rok (extracted)")
    fee_3_rok: Optional[NumberField] = Field(None, description="Fee 3 rok (extracted)")
    fee_4_rok: Optional[NumberField] = Field(None, description="Fee 4 rok (extracted)")
    fee_5_rok: Optional[NumberField] = Field(None, description="Fee 5 rok (extracted)")

    # Fee Calculation (Extracted with confidence tracking)
    fee_calculation_basis: Optional[StringField] = Field(None, description="Fee calculation basis (extracted)")
    fee_includes: List[str] = Field(default_factory=list, description="What's included in fee (legacy list)")
    fee_excludes: List[str] = Field(default_factory=list)

    # Fee Changes (Extracted with confidence tracking)
    last_fee_increase_date: Optional[DateField] = Field(None, description="Last fee increase date (extracted)")
    last_fee_increase_percentage: Optional[NumberField] = Field(None, description="Last fee increase percentage (extracted)")
    planned_fee_changes: List[Dict[str, Any]] = Field(default_factory=list)

    # Special Fees (Structural - list of complex objects)
    special_assessments: List[Dict[str, Any]] = Field(default_factory=list, description="One-time assessments")

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")

    @model_validator(mode='after')
    def sync_swedish_english_aliases(self):
        """
        Synchronize Swedish primary fields with English alias fields.
        Week 2 Day 4: Swedish-first semantic fields.

        Strategy:
        - If Swedish field exists, copy to English alias
        - If English field exists but Swedish doesn't, copy to Swedish
        - Prefer Swedish as source of truth
        """
        # Annual fee per sqm: årsavgift_per_sqm_total <-> annual_fee_per_sqm
        if self.arsavgift_per_sqm_total and not self.annual_fee_per_sqm:
            self.annual_fee_per_sqm = self.arsavgift_per_sqm_total
        elif self.annual_fee_per_sqm and not self.arsavgift_per_sqm_total:
            self.arsavgift_per_sqm_total = self.annual_fee_per_sqm

        # Monthly fee per sqm: månadsavgift_per_sqm <-> monthly_fee_per_sqm
        if self.manadsavgift_per_sqm and not self.monthly_fee_per_sqm:
            self.monthly_fee_per_sqm = self.manadsavgift_per_sqm
        elif self.monthly_fee_per_sqm and not self.manadsavgift_per_sqm:
            self.manadsavgift_per_sqm = self.monthly_fee_per_sqm

        # Monthly fee average: månadsavgift_per_apartment_avg <-> monthly_fee_average
        if self.manadsavgift_per_apartment_avg and not self.monthly_fee_average:
            self.monthly_fee_average = self.manadsavgift_per_apartment_avg
        elif self.monthly_fee_average and not self.manadsavgift_per_apartment_avg:
            self.manadsavgift_per_apartment_avg = self.monthly_fee_average

        # Cross-validation: Check if monthly*12 ≈ annual (with tolerance)
        if self.manadsavgift_per_sqm and self.arsavgift_per_sqm_total:
            monthly_val = self.manadsavgift_per_sqm.value if isinstance(self.manadsavgift_per_sqm, NumberField) else self.manadsavgift_per_sqm
            annual_val = self.arsavgift_per_sqm_total.value if isinstance(self.arsavgift_per_sqm_total, NumberField) else self.arsavgift_per_sqm_total

            if monthly_val and annual_val:
                expected_annual = monthly_val * 12
                diff = abs(annual_val - expected_annual)
                tolerance = max(100, annual_val * 0.10)  # ±10% or ±100 kr, whichever is larger

                if diff > tolerance:
                    # Log warning but don't fail - preserve data
                    if not hasattr(self, '_validation_warnings'):
                        self._validation_warnings = []
                    self._validation_warnings.append(
                        f"månadsavgift*12={expected_annual:.0f} vs årsavgift={annual_val:.0f}, diff={diff:.0f} kr/m² (tolerance={tolerance:.0f})"
                    )

        return self


class LoanDetails(BaseModel):
    """Individual loan information."""
    loan_number: Optional[StringField] = Field(None, description="Loan number (extracted)")
    lender: Optional[StringField] = Field(None, description="Lender name (extracted)")
    original_amount: Optional[NumberField] = Field(None, description="Original loan amount (extracted)")
    outstanding_balance: Optional[NumberField] = Field(None, description="Outstanding balance (extracted)")
    interest_rate: Optional[NumberField] = Field(None, description="Interest rate (extracted)")
    interest_type: Optional[Literal["fixed", "variable"]] = None
    maturity_date: Optional[DateField] = Field(None, description="Maturity date (extracted)")
    amortization_schedule: Optional[StringField] = Field(None, description="Amortization schedule (extracted)")
    collateral: Optional[StringField] = Field(None, description="Collateral description (extracted)")
    covenants: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class ReserveFund(BaseModel):
    """Reserve fund details."""
    fund_name: Optional[StringField] = Field(None, description="Fund name (extracted)")
    balance: Optional[NumberField] = Field(None, description="Current balance (extracted)")
    purpose: Optional[StringField] = Field(None, description="Fund purpose (extracted)")
    target_amount: Optional[NumberField] = Field(None, description="Target amount (extracted)")
    annual_contribution: Optional[NumberField] = Field(None, description="Annual contribution (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# LEVEL 7: OPERATIONS & MAINTENANCE
# =============================================================================

class Supplier(BaseModel):
    """Supplier/contractor information."""
    company_name: Optional[StringField] = Field(None, description="Company name (extracted)")
    service_type: Optional[StringField] = Field(None, description="Service type (extracted)")
    contract_value_annual: Optional[NumberField] = Field(None, description="Annual contract value (extracted)")
    contract_start: Optional[DateField] = Field(None, description="Contract start date (extracted)")
    contract_end: Optional[DateField] = Field(None, description="Contract end date (extracted)")
    renewal_terms: Optional[StringField] = Field(None, description="Renewal terms (extracted)")
    contact_info: Optional[StringField] = Field(None, description="Contact information (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class MaintenanceItem(BaseModel):
    """Planned maintenance item."""
    description: Optional[StringField] = Field(None, description="Maintenance description (extracted)")
    planned_year: Optional[NumberField] = Field(None, description="Planned year (extracted)")
    estimated_cost: Optional[NumberField] = Field(None, description="Estimated cost (extracted)")
    priority: Optional[Literal["high", "medium", "low"]] = None
    status: Optional[Literal["planned", "in_progress", "completed", "deferred"]] = None
    actual_cost: Optional[NumberField] = Field(None, description="Actual cost (extracted)")
    completion_date: Optional[DateField] = Field(None, description="Completion date (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class OperationsData(BaseModel):
    """Operations and maintenance information."""

    # Service Providers (Extracted with confidence tracking)
    property_manager: Optional[StringField] = Field(None, description="Property manager name (extracted)")
    property_management_fee: Optional[NumberField] = Field(None, description="Property management fee (extracted)")
    suppliers: List[Supplier] = Field(default_factory=list)

    # Maintenance (Extracted with confidence tracking)
    maintenance_plan_years: Optional[NumberField] = Field(None, description="Maintenance plan years (extracted)")
    planned_maintenance: List[MaintenanceItem] = Field(default_factory=list)
    completed_maintenance: List[MaintenanceItem] = Field(default_factory=list)

    # Insurance (Extracted with confidence tracking)
    insurance_provider: Optional[StringField] = Field(None, description="Insurance provider (extracted)")
    insurance_coverage_types: List[str] = Field(default_factory=list)
    insurance_premium_annual: Optional[NumberField] = Field(None, description="Annual insurance premium (extracted)")
    insurance_deductible: Optional[NumberField] = Field(None, description="Insurance deductible (extracted)")

    # Utilities (Extracted with confidence tracking)
    electricity_provider: Optional[StringField] = Field(None, description="Electricity provider (extracted)")
    heating_provider: Optional[StringField] = Field(None, description="Heating provider (extracted)")
    water_provider: Optional[StringField] = Field(None, description="Water provider (extracted)")
    broadband_provider: Optional[StringField] = Field(None, description="Broadband provider (extracted)")

    # Staff (Extracted with confidence tracking)
    number_of_employees: Optional[NumberField] = Field(None, description="Number of employees (extracted)")
    employee_roles: List[str] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# LEVEL 8: EVENTS & POLICIES
# =============================================================================

class Event(BaseModel):
    """Significant event during the year."""
    event_date: Optional[DateField] = Field(None, description="Event date (extracted)")
    event_type: Optional[StringField] = Field(None, description="Event type (extracted)")
    description: Optional[StringField] = Field(None, description="Event description (extracted)")
    financial_impact: Optional[NumberField] = Field(None, description="Financial impact (extracted)")
    related_documents: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class Policy(BaseModel):
    """BRF policy or rule."""
    policy_name: Optional[StringField] = Field(None, description="Policy name (extracted)")
    policy_type: Optional[Literal["financial", "operational", "governance", "environmental", "other"]] = None
    policy_description: Optional[StringField] = Field(None, description="Policy description (extracted)")
    effective_date: Optional[DateField] = Field(None, description="Effective date (extracted)")
    review_date: Optional[DateField] = Field(None, description="Review date (extracted)")
    approved_by: Optional[StringField] = Field(None, description="Approved by (extracted)")
    source_page: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


class EnvironmentalData(BaseModel):
    """Environmental and sustainability information."""

    # Energy (Extracted with confidence tracking)
    total_energy_consumption_kwh: Optional[NumberField] = Field(None, description="Total energy consumption kWh (extracted)")
    renewable_energy_percentage: Optional[NumberField] = Field(None, description="Renewable energy percentage (extracted)")
    energy_efficiency_improvements: List[str] = Field(default_factory=list)

    # Waste (Extracted with confidence tracking)
    waste_management_system: Optional[StringField] = Field(None, description="Waste management system (extracted)")
    recycling_rate: Optional[NumberField] = Field(None, description="Recycling rate (extracted)")

    # Water (Extracted with confidence tracking)
    water_consumption_m3: Optional[NumberField] = Field(None, description="Water consumption m3 (extracted)")
    water_saving_measures: List[str] = Field(default_factory=list)

    # Certifications (Structural - list of strings)
    environmental_certifications: List[str] = Field(default_factory=list)

    # Green Investments (Structural - list of complex objects)
    green_investments: List[Dict[str, Any]] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list, description="DEPRECATED: Use evidence_pages in fields instead")


# =============================================================================
# MASTER DOCUMENT MODEL
# =============================================================================

class BRFAnnualReport(BaseModel):
    """Complete Swedish BRF Annual Report - Maximum Information Extraction."""

    # Metadata
    metadata: DocumentMetadata

    # Core Sections
    governance: Optional[GovernanceStructure] = None
    financial: Optional[FinancialData] = None
    multi_year_overview: Optional[DynamicMultiYearOverview] = Field(
        None,
        description="Multi-year financial comparison (2-10+ years dynamically)"
    )
    notes: Optional[NotesCollection] = None
    property: Optional[PropertyDetails] = None
    fees: Optional[FeeStructure] = None

    # Detailed Sections
    loans: List[LoanDetails] = Field(default_factory=list)
    reserves: List[ReserveFund] = Field(default_factory=list)
    operations: Optional[OperationsData] = None

    # Events & Policies
    events: List[Event] = Field(default_factory=list)
    policies: List[Policy] = Field(default_factory=list)
    environmental: Optional[EnvironmentalData] = None

    # Free-Form Sections (Extracted with confidence tracking)
    chairman_statement: Optional[StringField] = Field(None, description="Chairman statement text (extracted)")
    board_report: Optional[StringField] = Field(None, description="Board report text (extracted)")
    auditor_report: Optional[StringField] = Field(None, description="Auditor report text (extracted)")

    # Quality Metrics
    extraction_quality: Dict[str, float] = Field(default_factory=dict)
    coverage_percentage: float = Field(0, ge=0, le=100)
    confidence_score: float = Field(0, ge=0, le=1)

    # Source Evidence
    all_source_pages: List[int] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "brf_name": "BRF Björk och Plaza",
                    "fiscal_year": 2023,
                    "document_id": "716433-6651_2023",
                    "organization_number": "716433-6651"
                },
                "governance": {
                    "chairman": "Elvy Maria Löfvenberg"
                },
            }
        }
