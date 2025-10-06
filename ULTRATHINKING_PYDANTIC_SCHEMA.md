# Ultrathinking: Comprehensive Pydantic Schema for Maximum Information Extraction

**Date**: 2025-10-06 21:50:00
**Purpose**: Extract EVERY fact from Swedish BRF annual reports (skip only signatures/boilerplate)
**Approach**: Scalable, robust, structured Pydantic models

---

## 🎯 DESIGN PHILOSOPHY

### Extract Everything Principle

**INCLUDE**: Every piece of business information, financial data, governance detail, property fact, event, note, policy, plan, contract, relationship, metric, and decision

**EXCLUDE ONLY**:
- Digital signatures (base64 blobs)
- Boilerplate auditor disclaimers ("We have audited in accordance with...")
- Template legal text (exact same in all documents)
- Page numbers, headers, footers

### Scalability Requirements

1. **Nested Structure**: Support arbitrary depth (e.g., Notes → Sub-notes → Line items)
2. **List Fields**: Handle variable-length data (board members, suppliers, events)
3. **Optional Fields**: Document variations (not all BRFs have same sections)
4. **Validation**: Type checking, value constraints, cross-field consistency
5. **Versioning**: Schema evolution over time

---

## 📋 COMPREHENSIVE SCHEMA ARCHITECTURE

### Level 1: Document Metadata

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal
from datetime import date, datetime
from decimal import Decimal

class DocumentMetadata(BaseModel):
    """Top-level document identification and context."""

    # Document Identity
    document_id: str = Field(..., description="Unique identifier (org_number_year)")
    document_type: Literal["arsredovisning", "ekonomisk_plan", "stadgar", "energideklaration"]
    fiscal_year: int = Field(..., ge=1900, le=2100)
    report_date: date

    # BRF Identity
    brf_name: str = Field(..., min_length=1)
    organization_number: str = Field(..., regex=r"^\d{6}-\d{4}$")

    # Document Quality
    pages_total: int = Field(..., gt=0)
    is_machine_readable: bool
    ocr_confidence: Optional[float] = Field(None, ge=0, le=1)

    # Processing Metadata
    extraction_date: datetime
    extraction_mode: Literal["fast", "deep", "auto"]
    extraction_version: str = "v2.0"

    # File Information
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    file_hash_sha256: Optional[str]
```

### Level 2: Governance (Complete Detail)

```python
class BoardMember(BaseModel):
    """Individual board member with full details."""
    full_name: str
    role: Optional[Literal["ordforande", "vice_ordforande", "ledamot", "suppleant"]]
    term_start: Optional[date]
    term_end: Optional[date]
    elected_at_meeting: Optional[date]
    is_employee_representative: bool = False
    contact_info: Optional[str]
    source_page: List[int] = Field(default_factory=list)

class Auditor(BaseModel):
    """Auditor details."""
    name: str
    firm: Optional[str]
    certification: Optional[str] = Field(None, description="e.g., Auktoriserad revisor")
    contact_info: Optional[str]
    source_page: List[int] = Field(default_factory=list)

class GovernanceStructure(BaseModel):
    """Complete governance information."""

    # Board
    chairman: Optional[str]
    vice_chairman: Optional[str]
    board_members: List[BoardMember] = Field(default_factory=list)
    board_size: Optional[int]
    board_term_years: Optional[int] = Field(None, description="Mandate period in years")

    # Auditors
    primary_auditor: Optional[Auditor]
    deputy_auditor: Optional[Auditor]
    audit_period: Optional[str]

    # Nomination Committee
    nomination_committee: List[str] = Field(default_factory=list)
    nomination_committee_details: Optional[str]

    # Annual Meeting
    annual_meeting_date: Optional[date]
    annual_meeting_location: Optional[str]
    annual_meeting_attendees: Optional[int]
    extraordinary_meetings: List[date] = Field(default_factory=list)

    # Governance Documents
    stadgar_last_updated: Optional[date]
    bylaws_references: List[str] = Field(default_factory=list)

    # Evidence
    source_pages: List[int] = Field(default_factory=list)
```

### Level 3: Financial (Ultra-Comprehensive)

```python
class FinancialLineItem(BaseModel):
    """Individual line item in financial statements."""
    category: str
    subcategory: Optional[str]
    description: str
    amount_current_year: Decimal
    amount_previous_year: Optional[Decimal]
    note_reference: Optional[int]
    percentage_of_total: Optional[float]
    source_page: int

class IncomeStatement(BaseModel):
    """Complete income statement (Resultaträkning)."""

    # Revenue (Intäkter)
    revenue_total: Decimal
    revenue_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Expenses (Kostnader)
    expenses_total: Decimal
    expenses_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Operating Result
    operating_result: Decimal

    # Financial Items
    financial_income: Optional[Decimal]
    financial_expenses: Optional[Decimal]

    # Result
    result_before_tax: Decimal
    tax: Optional[Decimal]
    result_after_tax: Decimal

    # Source
    source_pages: List[int] = Field(default_factory=list)

class BalanceSheet(BaseModel):
    """Complete balance sheet (Balansräkning)."""

    # Assets
    assets_total: Decimal
    fixed_assets: Optional[Decimal]
    current_assets: Optional[Decimal]
    assets_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Liabilities
    liabilities_total: Decimal
    equity_total: Decimal
    long_term_liabilities: Optional[Decimal]
    short_term_liabilities: Optional[Decimal]
    liabilities_line_items: List[FinancialLineItem] = Field(default_factory=list)

    # Balance Check
    @validator('liabilities_total')
    def check_balance(cls, v, values):
        if 'assets_total' in values and 'equity_total' in values:
            expected = values['equity_total'] + v
            actual = values['assets_total']
            if abs(expected - actual) > 1:  # Allow 1 SEK rounding
                raise ValueError(f"Balance sheet doesn't balance: {expected} != {actual}")
        return v

    # Source
    source_pages: List[int] = Field(default_factory=list)

class CashFlowStatement(BaseModel):
    """Cash flow statement (Kassaflödesanalys)."""
    operating_activities: Optional[Decimal]
    investing_activities: Optional[Decimal]
    financing_activities: Optional[Decimal]
    cash_flow_total: Optional[Decimal]
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)

class FinancialData(BaseModel):
    """Complete financial information."""
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow: Optional[CashFlowStatement]
```

### Level 4: Notes (Complete Extraction)

```python
class Note(BaseModel):
    """Individual note with full details."""
    note_number: int
    title: str
    content: str
    tables: List[Dict] = Field(default_factory=list)
    line_items: List[FinancialLineItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)

class BuildingDetails(BaseModel):
    """Note 8: Building details (ultra-comprehensive)."""

    # Acquisition Values
    opening_acquisition_value: Optional[Decimal]
    additions: Optional[Decimal]
    disposals: Optional[Decimal]
    closing_acquisition_value: Decimal

    # Depreciation
    opening_depreciation: Optional[Decimal]
    current_year_depreciation: Decimal
    disposals_depreciation: Optional[Decimal]
    closing_depreciation: Optional[Decimal]

    # Residual Values
    planned_residual_value: Decimal

    # Tax Values
    tax_assessment_building: Decimal
    tax_assessment_land: Decimal
    tax_assessment_year: Optional[int]

    # Depreciation Method
    depreciation_method: Optional[str]
    depreciation_period_years: Optional[int]

    # Components (if detailed)
    building_components: List[Dict] = Field(default_factory=list, description="Detailed component breakdown")

    # Source
    source_pages: List[int] = Field(default_factory=list)

class ReceivablesBreakdown(BaseModel):
    """Note 9: Receivables (every line item)."""
    tax_account: Optional[Decimal]
    vat_deduction: Optional[Decimal]
    client_funds: Optional[Decimal]
    receivables: Optional[Decimal]
    other_deductions: Optional[Decimal]
    prepaid_expenses: Optional[Decimal]
    accrued_income: Optional[Decimal]
    other_items: List[FinancialLineItem] = Field(default_factory=list)
    total: Optional[Decimal]
    source_pages: List[int] = Field(default_factory=list)

class NotesCollection(BaseModel):
    """All notes from annual report."""

    # Standard Notes
    note_1_accounting_principles: Optional[Note]
    note_2_revenue: Optional[Note]
    note_3_personnel: Optional[Note]
    note_4_operating_costs: Optional[Note]
    note_5_financial_items: Optional[Note]
    note_6_tax: Optional[Note]
    note_7_intangible_assets: Optional[Note]
    note_8_buildings: Optional[BuildingDetails]
    note_9_receivables: Optional[ReceivablesBreakdown]
    note_10_cash: Optional[Note]
    note_11_equity: Optional[Note]
    note_12_liabilities: Optional[Note]
    note_13_contingencies: Optional[Note]
    note_14_pledged_assets: Optional[Note]
    note_15_related_parties: Optional[Note]

    # Additional Notes (variable)
    additional_notes: List[Note] = Field(default_factory=list)

    # Count
    total_notes: int = 0
```

### Level 5: Property (Maximum Detail)

```python
class ApartmentUnit(BaseModel):
    """Individual apartment details."""
    apartment_number: Optional[str]
    room_count: int
    size_sqm: Optional[float]
    floor: Optional[int]
    monthly_fee: Optional[Decimal]
    owner_name: Optional[str] = Field(None, description="If public information")

class ApartmentDistribution(BaseModel):
    """Apartment distribution by size."""
    one_room: int = Field(0, alias="1_rok")
    two_rooms: int = Field(0, alias="2_rok")
    three_rooms: int = Field(0, alias="3_rok")
    four_rooms: int = Field(0, alias="4_rok")
    five_rooms: int = Field(0, alias="5_rok")
    more_than_five: int = Field(0, alias=">5_rok")

    @property
    def total_apartments(self) -> int:
        return sum([
            self.one_room, self.two_rooms, self.three_rooms,
            self.four_rooms, self.five_rooms, self.more_than_five
        ])

class CommercialTenant(BaseModel):
    """Commercial tenant information."""
    business_name: str
    business_type: Optional[str]
    lease_area_sqm: Optional[float]
    lease_start_date: Optional[date]
    lease_end_date: Optional[date]
    annual_rent: Optional[Decimal]
    source_page: List[int] = Field(default_factory=list)

class CommonArea(BaseModel):
    """Common area/facility."""
    name: str
    area_type: Optional[Literal["gym", "laundry", "storage", "garage", "courtyard", "sauna", "other"]]
    size_sqm: Optional[float]
    description: Optional[str]
    maintenance_responsibility: Optional[str]

class PropertyDetails(BaseModel):
    """Ultra-comprehensive property information."""

    # Property Identity
    property_designation: Optional[str] = Field(None, description="Fastighetsbeteckning")
    address: Optional[str]
    postal_code: Optional[str]
    city: Optional[str]
    municipality: Optional[str]
    county: Optional[str]
    coordinates: Optional[Dict[str, float]] = Field(None, description="lat/lng if available")

    # Building Information
    built_year: Optional[int]
    renovation_years: List[int] = Field(default_factory=list)
    building_type: Optional[str]
    number_of_buildings: Optional[int]
    number_of_floors: Optional[int]
    total_area_sqm: Optional[float]
    living_area_sqm: Optional[float]
    commercial_area_sqm: Optional[float]

    # Apartments
    total_apartments: Optional[int]
    apartment_distribution: Optional[ApartmentDistribution]
    apartment_units: List[ApartmentUnit] = Field(default_factory=list, description="If detailed list available")

    # Commercial
    commercial_tenants: List[CommercialTenant] = Field(default_factory=list)
    number_of_commercial_units: Optional[int]

    # Common Areas
    common_areas: List[CommonArea] = Field(default_factory=list)

    # Land
    land_area_sqm: Optional[float]
    land_lease: Optional[bool]
    land_lease_expiry: Optional[date]

    # Ownership
    cooperative_type: Optional[Literal["bostadsratt", "hyresratt", "mixed"]]
    samfallighet_percentage: Optional[float]
    samfallighet_description: Optional[str]

    # Energy
    energy_class: Optional[str]
    energy_performance_kwh_sqm_year: Optional[float]
    energy_declaration_date: Optional[date]
    heating_type: Optional[str]

    # Source
    source_pages: List[int] = Field(default_factory=list)
```

### Level 6: Fees & Finances (Detailed)

```python
class FeeStructure(BaseModel):
    """Complete fee structure."""

    # Current Fees
    monthly_fee_average: Optional[Decimal]
    monthly_fee_per_sqm: Optional[Decimal]
    annual_fee_per_sqm: Optional[Decimal]

    # Fee by Apartment Size
    fee_1_rok: Optional[Decimal]
    fee_2_rok: Optional[Decimal]
    fee_3_rok: Optional[Decimal]
    fee_4_rok: Optional[Decimal]
    fee_5_rok: Optional[Decimal]

    # Fee Calculation
    fee_calculation_basis: Optional[str]
    fee_includes: List[str] = Field(default_factory=list, description="What's included in fee")
    fee_excludes: List[str] = Field(default_factory=list)

    # Fee Changes
    last_fee_increase_date: Optional[date]
    last_fee_increase_percentage: Optional[float]
    planned_fee_changes: List[Dict] = Field(default_factory=list)

    # Special Fees
    special_assessments: List[Dict] = Field(default_factory=list, description="One-time assessments")

    # Source
    source_pages: List[int] = Field(default_factory=list)

class LoanDetails(BaseModel):
    """Individual loan information."""
    loan_number: Optional[str]
    lender: str
    original_amount: Optional[Decimal]
    outstanding_balance: Decimal
    interest_rate: Optional[float]
    interest_type: Optional[Literal["fixed", "variable"]]
    maturity_date: Optional[date]
    amortization_schedule: Optional[str]
    collateral: Optional[str]
    covenants: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list)

class ReserveFund(BaseModel):
    """Reserve fund details."""
    fund_name: str
    balance: Decimal
    purpose: Optional[str]
    target_amount: Optional[Decimal]
    annual_contribution: Optional[Decimal]
    source_page: List[int] = Field(default_factory=list)
```

### Level 7: Operations & Maintenance

```python
class Supplier(BaseModel):
    """Supplier/contractor information."""
    company_name: str
    service_type: str
    contract_value_annual: Optional[Decimal]
    contract_start: Optional[date]
    contract_end: Optional[date]
    renewal_terms: Optional[str]
    contact_info: Optional[str]
    source_page: List[int] = Field(default_factory=list)

class MaintenanceItem(BaseModel):
    """Planned maintenance item."""
    description: str
    planned_year: Optional[int]
    estimated_cost: Optional[Decimal]
    priority: Optional[Literal["high", "medium", "low"]]
    status: Optional[Literal["planned", "in_progress", "completed", "deferred"]]
    actual_cost: Optional[Decimal]
    completion_date: Optional[date]
    source_page: List[int] = Field(default_factory=list)

class OperationsData(BaseModel):
    """Operations and maintenance information."""

    # Service Providers
    property_manager: Optional[str]
    property_management_fee: Optional[Decimal]
    suppliers: List[Supplier] = Field(default_factory=list)

    # Maintenance
    maintenance_plan_years: Optional[int]
    planned_maintenance: List[MaintenanceItem] = Field(default_factory=list)
    completed_maintenance: List[MaintenanceItem] = Field(default_factory=list)

    # Insurance
    insurance_provider: Optional[str]
    insurance_coverage_types: List[str] = Field(default_factory=list)
    insurance_premium_annual: Optional[Decimal]
    insurance_deductible: Optional[Decimal]

    # Utilities
    electricity_provider: Optional[str]
    heating_provider: Optional[str]
    water_provider: Optional[str]
    broadband_provider: Optional[str]

    # Staff
    number_of_employees: Optional[int]
    employee_roles: List[str] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list)
```

### Level 8: Events & Policies

```python
class Event(BaseModel):
    """Significant event during the year."""
    event_date: Optional[date]
    event_type: str
    description: str
    financial_impact: Optional[Decimal]
    related_documents: List[str] = Field(default_factory=list)
    source_page: List[int] = Field(default_factory=list)

class Policy(BaseModel):
    """BRF policy or rule."""
    policy_name: str
    policy_type: Optional[Literal["financial", "operational", "governance", "environmental", "other"]]
    policy_description: str
    effective_date: Optional[date]
    review_date: Optional[date]
    approved_by: Optional[str]
    source_page: List[int] = Field(default_factory=list)

class EnvironmentalData(BaseModel):
    """Environmental and sustainability information."""

    # Energy
    total_energy_consumption_kwh: Optional[float]
    renewable_energy_percentage: Optional[float]
    energy_efficiency_improvements: List[str] = Field(default_factory=list)

    # Waste
    waste_management_system: Optional[str]
    recycling_rate: Optional[float]

    # Water
    water_consumption_m3: Optional[float]
    water_saving_measures: List[str] = Field(default_factory=list)

    # Certifications
    environmental_certifications: List[str] = Field(default_factory=list)

    # Green Investments
    green_investments: List[Dict] = Field(default_factory=list)

    # Source
    source_pages: List[int] = Field(default_factory=list)
```

### Master Document Model

```python
class BRFAnnualReport(BaseModel):
    """Complete Swedish BRF Annual Report - Maximum Information Extraction."""

    # Metadata
    metadata: DocumentMetadata

    # Core Sections
    governance: GovernanceStructure
    financial: FinancialData
    notes: NotesCollection
    property: PropertyDetails
    fees: FeeStructure

    # Detailed Sections
    loans: List[LoanDetails] = Field(default_factory=list)
    reserves: List[ReserveFund] = Field(default_factory=list)
    operations: OperationsData

    # Events & Policies
    events: List[Event] = Field(default_factory=list)
    policies: List[Policy] = Field(default_factory=list)
    environmental: Optional[EnvironmentalData]

    # Free-Form Sections
    chairman_statement: Optional[str]
    board_report: Optional[str]
    auditor_report: Optional[str]

    # Quality Metrics
    extraction_quality: Dict[str, float] = Field(default_factory=dict)
    coverage_percentage: float = Field(0, ge=0, le=100)
    confidence_score: float = Field(0, ge=0, le=1)

    # Source Evidence
    all_source_pages: List[int] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {"brf_name": "BRF Björk och Plaza", "fiscal_year": 2023},
                "governance": {"chairman": "Elvy Maria Löfvenberg"},
                # ... abbreviated for brevity
            }
        }
```

---

## 🔧 EXTRACTION STRATEGY

### Phase 1: Document Analysis (5s)
```python
1. Detect document type and structure
2. Identify all sections (vision-based)
3. Classify pages by content type
4. Generate extraction plan
```

### Phase 2: Base Extraction (60s)
```python
1. Docling markdown + tables
2. GPT-4o combined extraction (all fields)
3. Pattern-based structured data
4. Initial Pydantic model population
```

### Phase 3: Targeted Deep Extraction (120s)
```python
1. Vision extraction for charts/images
2. Hierarchical note processing
3. Table-specific extractors
4. Relationship mapping
```

### Phase 4: Validation & Enhancement (30s)
```python
1. Cross-field validation
2. Numeric consistency checks
3. Date/name normalization
4. Confidence scoring
5. Missing field inference
```

---

## 🚀 IMPLEMENTATION ROADMAP

### Week 1: Schema Development
- Design complete Pydantic models
- Add validators and constraints
- Create migration from current schema
- Test with sample documents

### Week 2: Extractor Enhancement
- Implement deep note extractors
- Add supplier/contract extractors
- Build maintenance plan parser
- Create event timeline extractor

### Week 3: Integration & Testing
- Integrate new extractors into pipeline
- Test on diverse documents
- Measure coverage improvement
- Validate against ground truth

### Week 4: Optimization & Deployment
- Optimize extraction speed
- Reduce API costs where possible
- Deploy to H100 infrastructure
- Scale to full corpus

---

**Status**: ✅ **DESIGN COMPLETE - READY FOR IMPLEMENTATION**
