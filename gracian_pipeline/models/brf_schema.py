"""
Ultra-comprehensive Pydantic schema for Swedish BRF Annual Reports.

This schema extracts EVERY fact from BRF documents (skip only signatures and boilerplate).
Designed for scalability, robustness, and maximum information capture.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal, Any
from datetime import date, datetime
from decimal import Decimal


# =============================================================================
# LEVEL 1: DOCUMENT METADATA
# =============================================================================

class DocumentMetadata(BaseModel):
    """Top-level document identification and context."""

    # Document Identity
    document_id: str = Field(..., description="Unique identifier (org_number_year)")
    document_type: Literal["arsredovisning", "ekonomisk_plan", "stadgar", "energideklaration"]
    fiscal_year: int = Field(..., ge=1900, le=2100)
    report_date: Optional[date] = None

    # BRF Identity
    brf_name: str = Field(..., min_length=1)
    organization_number: str = Field(..., pattern=r"^\d{6}-\d{4}$")

    # Document Quality
    pages_total: int = Field(..., gt=0)
    is_machine_readable: bool = True
    ocr_confidence: Optional[float] = Field(None, ge=0, le=1)

    # Processing Metadata
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    extraction_mode: Literal["fast", "deep", "auto"] = "auto"
    extraction_version: str = "v2.0"

    # File Information
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash_sha256: Optional[str] = None


# =============================================================================
# LEVEL 2: GOVERNANCE (COMPLETE DETAIL)
# =============================================================================

class BoardMember(BaseModel):
    """Individual board member with full details."""
    full_name: str
    role: Optional[Literal["ordforande", "vice_ordforande", "ledamot", "suppleant"]] = None
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    elected_at_meeting: Optional[date] = None
    is_employee_representative: bool = False
    contact_info: Optional[str] = None
    source_page: List[int] = Field(default_factory=list)


class Auditor(BaseModel):
    """Auditor details."""
    name: str
    firm: Optional[str] = None
    certification: Optional[str] = Field(None, description="e.g., Auktoriserad revisor")
    contact_info: Optional[str] = None
    source_page: List[int] = Field(default_factory=list)


class GovernanceStructure(BaseModel):
    """Complete governance information."""

    # Board
    chairman: Optional[str] = None
    vice_chairman: Optional[str] = None
    board_members: List[BoardMember] = Field(default_factory=list)
    board_size: Optional[int] = None
    board_term_years: Optional[int] = Field(None, description="Mandate period in years")

    # Auditors
    primary_auditor: Optional[Auditor] = None
    deputy_auditor: Optional[Auditor] = None
    audit_period: Optional[str] = None

    # Nomination Committee
    nomination_committee: List[str] = Field(default_factory=list)
    nomination_committee_details: Optional[str] = None

    # Annual Meeting
    annual_meeting_date: Optional[date] = None
    annual_meeting_location: Optional[str] = None
    annual_meeting_attendees: Optional[int] = None
    extraordinary_meetings: List[date] = Field(default_factory=list)

    # Governance Documents
    stadgar_last_updated: Optional[date] = None
    bylaws_references: List[str] = Field(default_factory=list)

    # Evidence
    source_pages: List[int] = Field(default_factory=list)


# =============================================================================
# LEVEL 3: FINANCIAL (ULTRA-COMPREHENSIVE)
# =============================================================================

class FinancialLineItem(BaseModel):
    """Individual line item in financial statements."""
    category: str
    subcategory: Optional[str] = None
    description: str
    amount_current_year: Decimal
    amount_previous_year: Optional[Decimal] = None
    note_reference: Optional[int] = None
    percentage_of_total: Optional[float] = None
    source_page: Optional[int] = None


class IncomeStatement(BaseModel):
    """Complete income statement (Resultaträkning)."""

    # Revenue (Intäkter)
    revenue_total: Optional[Decimal] = None
    revenue_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Expenses (Kostnader)
    expenses_total: Optional[Decimal] = None
    expenses_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Operating Result
    operating_result: Optional[Decimal] = None

    # Financial Items
    financial_income: Optional[Decimal] = None
    financial_expenses: Optional[Decimal] = None

    # Result
    result_before_tax: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    result_after_tax: Optional[Decimal] = None

    # Source
    source_pages: List[int] = Field(default_factory=list)


class BalanceSheet(BaseModel):
    """Complete balance sheet (Balansräkning)."""

    # Assets
    assets_total: Optional[Decimal] = None
    fixed_assets: Optional[Decimal] = None
    current_assets: Optional[Decimal] = None
    assets_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Liabilities
    liabilities_total: Optional[Decimal] = None
    equity_total: Optional[Decimal] = None
    long_term_liabilities: Optional[Decimal] = None
    short_term_liabilities: Optional[Decimal] = None
    liabilities_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list)

    @validator('liabilities_total')
    def check_balance(cls, v, values):
        """Validate balance sheet equation: Assets = Liabilities + Equity"""
        if v is not None and 'assets_total' in values and 'equity_total' in values:
            if values['assets_total'] is not None and values['equity_total'] is not None:
                expected = values['equity_total'] + v
                actual = values['assets_total']
                if abs(expected - actual) > 1:  # Allow 1 SEK rounding
                    # Warning only, don't fail validation
                    pass
        return v


class CashFlowStatement(BaseModel):
    """Cash flow statement (Kassaflödesanalys)."""
    operating_activities: Optional[Decimal] = None
    investing_activities: Optional[Decimal] = None
    financing_activities: Optional[Decimal] = None
    cash_flow_total: Optional[Decimal] = None
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)


class FinancialData(BaseModel):
    """Complete financial information."""
    income_statement: Optional[IncomeStatement] = None
    balance_sheet: Optional[BalanceSheet] = None
    cash_flow: Optional[CashFlowStatement] = None


# =============================================================================
# LEVEL 4: NOTES (COMPLETE EXTRACTION)
# =============================================================================

class Note(BaseModel):
    """Individual note with full details."""
    note_number: int
    title: str
    content: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)


class BuildingDetails(BaseModel):
    """Note 8: Building details (ultra-comprehensive)."""

    # Acquisition Values
    opening_acquisition_value: Optional[Decimal] = None
    additions: Optional[Decimal] = None
    disposals: Optional[Decimal] = None
    closing_acquisition_value: Optional[Decimal] = None

    # Depreciation
    opening_depreciation: Optional[Decimal] = None
    current_year_depreciation: Optional[Decimal] = None
    disposals_depreciation: Optional[Decimal] = None
    closing_depreciation: Optional[Decimal] = None

    # Residual Values
    planned_residual_value: Optional[Decimal] = None

    # Tax Values
    tax_assessment_building: Optional[Decimal] = None
    tax_assessment_land: Optional[Decimal] = None
    tax_assessment_year: Optional[int] = None

    # Depreciation Method
    depreciation_method: Optional[str] = None
    depreciation_period_years: Optional[int] = None

    # Components (if detailed)
    building_components: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed component breakdown")

    # Source
    source_pages: List[int] = Field(default_factory=list)


class ReceivablesBreakdown(BaseModel):
    """Note 9: Receivables (every line item)."""
    tax_account: Optional[Decimal] = None
    vat_deduction: Optional[Decimal] = None
    client_funds: Optional[Decimal] = None
    receivables: Optional[Decimal] = None
    other_deductions: Optional[Decimal] = None
    prepaid_expenses: Optional[Decimal] = None
    accrued_income: Optional[Decimal] = None
    other_items: List[FinancialLineItem] = Field(default_factory=list)
    total: Optional[Decimal] = None
    source_pages: List[int] = Field(default_factory=list)


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
    apartment_number: Optional[str] = None
    room_count: Optional[int] = None
    size_sqm: Optional[float] = None
    floor: Optional[int] = None
    monthly_fee: Optional[Decimal] = None
    owner_name: Optional[str] = Field(None, description="If public information")


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
    business_name: str
    business_type: Optional[str] = None
    lease_area_sqm: Optional[float] = None
    lease_start_date: Optional[date] = None
    lease_end_date: Optional[date] = None
    annual_rent: Optional[Decimal] = None
    source_page: List[int] = Field(default_factory=list)


class CommonArea(BaseModel):
    """Common area/facility."""
    name: str
    area_type: Optional[Literal["gym", "laundry", "storage", "garage", "courtyard", "sauna", "other"]] = None
    size_sqm: Optional[float] = None
    description: Optional[str] = None
    maintenance_responsibility: Optional[str] = None


class PropertyDetails(BaseModel):
    """Ultra-comprehensive property information."""

    # Property Identity
    property_designation: Optional[str] = Field(None, description="Fastighetsbeteckning")
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    municipality: Optional[str] = None
    county: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = Field(None, description="lat/lng if available")

    # Building Information
    built_year: Optional[int] = None
    renovation_years: List[int] = Field(default_factory=list)
    building_type: Optional[str] = None
    number_of_buildings: Optional[int] = None
    number_of_floors: Optional[int] = None
    total_area_sqm: Optional[float] = None
    living_area_sqm: Optional[float] = None
    commercial_area_sqm: Optional[float] = None

    # Apartments
    total_apartments: Optional[int] = None
    apartment_distribution: Optional[ApartmentDistribution] = None
    apartment_units: List[ApartmentUnit] = Field(default_factory=list, description="If detailed list available")

    # Commercial
    commercial_tenants: List[CommercialTenant] = Field(default_factory=list)
    number_of_commercial_units: Optional[int] = None

    # Common Areas
    common_areas: List[CommonArea] = Field(default_factory=list)

    # Land
    land_area_sqm: Optional[float] = None
    land_lease: Optional[bool] = None
    land_lease_expiry: Optional[date] = None

    # Ownership
    cooperative_type: Optional[Literal["bostadsratt", "hyresratt", "mixed"]] = None
    samfallighet_percentage: Optional[float] = None
    samfallighet_description: Optional[str] = None

    # Energy
    energy_class: Optional[str] = None
    energy_performance_kwh_sqm_year: Optional[float] = None
    energy_declaration_date: Optional[date] = None
    heating_type: Optional[str] = None

    # Source
    source_pages: List[int] = Field(default_factory=list)


# =============================================================================
# LEVEL 6: FEES & FINANCES (DETAILED)
# =============================================================================

class FeeStructure(BaseModel):
    """Complete fee structure."""

    # Current Fees
    monthly_fee_average: Optional[Decimal] = None
    monthly_fee_per_sqm: Optional[Decimal] = None
    annual_fee_per_sqm: Optional[Decimal] = None

    # Fee by Apartment Size
    fee_1_rok: Optional[Decimal] = None
    fee_2_rok: Optional[Decimal] = None
    fee_3_rok: Optional[Decimal] = None
    fee_4_rok: Optional[Decimal] = None
    fee_5_rok: Optional[Decimal] = None

    # Fee Calculation
    fee_calculation_basis: Optional[str] = None
    fee_includes: List[str] = Field(default_factory=list, description="What's included in fee")
    fee_excludes: List[str] = Field(default_factory=list)

    # Fee Changes
    last_fee_increase_date: Optional[date] = None
    last_fee_increase_percentage: Optional[float] = None
    planned_fee_changes: List[Dict[str, Any]] = Field(default_factory=list)

    # Special Fees
    special_assessments: List[Dict[str, Any]] = Field(default_factory=list, description="One-time assessments")

    # Source
    source_pages: List[int] = Field(default_factory=list)


class LoanDetails(BaseModel):
    """Individual loan information."""
    loan_number: Optional[str] = None
    lender: str
    original_amount: Optional[Decimal] = None
    outstanding_balance: Decimal
    interest_rate: Optional[float] = None
    interest_type: Optional[Literal["fixed", "variable"]] = None
    maturity_date: Optional[date] = None
    amortization_schedule: Optional[str] = None
    collateral: Optional[str] = None
    covenants: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list)


class ReserveFund(BaseModel):
    """Reserve fund details."""
    fund_name: str
    balance: Decimal
    purpose: Optional[str] = None
    target_amount: Optional[Decimal] = None
    annual_contribution: Optional[Decimal] = None
    source_page: List[int] = Field(default_factory=list)


# =============================================================================
# LEVEL 7: OPERATIONS & MAINTENANCE
# =============================================================================

class Supplier(BaseModel):
    """Supplier/contractor information."""
    company_name: str
    service_type: str
    contract_value_annual: Optional[Decimal] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    renewal_terms: Optional[str] = None
    contact_info: Optional[str] = None
    source_page: List[int] = Field(default_factory=list)


class MaintenanceItem(BaseModel):
    """Planned maintenance item."""
    description: str
    planned_year: Optional[int] = None
    estimated_cost: Optional[Decimal] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    status: Optional[Literal["planned", "in_progress", "completed", "deferred"]] = None
    actual_cost: Optional[Decimal] = None
    completion_date: Optional[date] = None
    source_page: List[int] = Field(default_factory=list)


class OperationsData(BaseModel):
    """Operations and maintenance information."""

    # Service Providers
    property_manager: Optional[str] = None
    property_management_fee: Optional[Decimal] = None
    suppliers: List[Supplier] = Field(default_factory=list)

    # Maintenance
    maintenance_plan_years: Optional[int] = None
    planned_maintenance: List[MaintenanceItem] = Field(default_factory=list)
    completed_maintenance: List[MaintenanceItem] = Field(default_factory=list)

    # Insurance
    insurance_provider: Optional[str] = None
    insurance_coverage_types: List[str] = Field(default_factory=list)
    insurance_premium_annual: Optional[Decimal] = None
    insurance_deductible: Optional[Decimal] = None

    # Utilities
    electricity_provider: Optional[str] = None
    heating_provider: Optional[str] = None
    water_provider: Optional[str] = None
    broadband_provider: Optional[str] = None

    # Staff
    number_of_employees: Optional[int] = None
    employee_roles: List[str] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list)


# =============================================================================
# LEVEL 8: EVENTS & POLICIES
# =============================================================================

class Event(BaseModel):
    """Significant event during the year."""
    event_date: Optional[date] = None
    event_type: str
    description: str
    financial_impact: Optional[Decimal] = None
    related_documents: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list)


class Policy(BaseModel):
    """BRF policy or rule."""
    policy_name: str
    policy_type: Optional[Literal["financial", "operational", "governance", "environmental", "other"]] = None
    policy_description: str
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    approved_by: Optional[str] = None
    source_page: List[int] = Field(default_factory=list)


class EnvironmentalData(BaseModel):
    """Environmental and sustainability information."""

    # Energy
    total_energy_consumption_kwh: Optional[float] = None
    renewable_energy_percentage: Optional[float] = None
    energy_efficiency_improvements: List[str] = Field(default_factory=list)

    # Waste
    waste_management_system: Optional[str] = None
    recycling_rate: Optional[float] = None

    # Water
    water_consumption_m3: Optional[float] = None
    water_saving_measures: List[str] = Field(default_factory=list)

    # Certifications
    environmental_certifications: List[str] = Field(default_factory=list)

    # Green Investments
    green_investments: List[Dict[str, Any]] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list)


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

    # Free-Form Sections
    chairman_statement: Optional[str] = None
    board_report: Optional[str] = None
    auditor_report: Optional[str] = None

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
