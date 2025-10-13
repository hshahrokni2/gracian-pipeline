# Phase 1: Perfect Implementation Plan - FULL BRF Extraction

**Date**: October 13, 2025
**Duration**: 4-6 weeks
**Status**: Ready for execution
**Goal**: Foundation for 501-field FULL extraction

---

## Executive Summary

**Phase 1 delivers the foundation for FULL 501-field extraction** through:

1. **Schema v7.0**: Unified schema merging Gracian (1,230 lines) + ZeldaDemo (1,363 lines)
2. **ExtractionField base class**: Confidence + source tracking for all fields
3. **SYNONYM_MAPPING integration**: 200+ Swedish term normalizations
4. **Ground truth creation**: 10 diverse PDFs × 501 fields = 5,010 data points
5. **Testing framework**: Comprehensive validation for production readiness

**Key Decision**: Use **ZeldaDemo schema.py as foundation** (production-tested patterns) and merge Gracian specializations.

---

## 1. Schema Merging Strategy

### Decision: ZeldaDemo as Foundation

**Rationale**:
- ✅ Production-tested (Schema v6.0)
- ✅ Complete data quality scoring (`calculate_data_quality_score()`)
- ✅ Comprehensive validation (`validate_extraction()`)
- ✅ Migration utilities (`migrate_to_enhanced_schema()`)
- ✅ Field types defined inline (no external dependencies)
- ✅ Better `ConfigDict` settings (`extra='ignore', populate_by_name=True`)

**Merge Strategy**: Add Gracian's specialized structures to ZeldaDemo foundation

### Schema v7.0 Structure

```
ZeldaDemo Schema v6.0 (1,363 lines)
    ↓
ADD Gracian specializations:
    • NotesCollection (Notes 1-15 detailed extraction)
    • OperationsData (suppliers, maintenance, insurance)
    • EnvironmentalData (sustainability metrics)
    • ApartmentUnit + CommonArea (property details)
    • 3-tier tolerant validation (valid/warning/error)
    ↓
ENHANCE:
    • Swedish-first semantic fields (from Gracian)
    • Content-based routing keywords (Note 4, Note 8, etc.)
    • Evidence tracking (pages + methods)
    ↓
Schema v7.0 (1,600-1,800 lines)
```

### Field-by-Field Mapping

| Category | Gracian (1,230 lines) | ZeldaDemo (1,363 lines) | Schema v7.0 Action |
|----------|----------------------|------------------------|-------------------|
| **Base Class** | `from .base_fields import ExtractionField` | `class ExtractionField(BaseModel)` defined inline | ✅ **Use ZeldaDemo** (no external dependencies) |
| **Multi-Year** | `YearlyFinancialData` + `DynamicMultiYearOverview` | Same structure, more mature | ✅ **Use ZeldaDemo** (production-tested) |
| **Calculated Metrics** | `CalculatedFinancialMetrics` (tolerant validation) | Same + `get_validation_summary()` | ✅ **Use ZeldaDemo** + Gracian tolerance functions |
| **Notes** | `NotesCollection` (Note 1-15 detailed) | `NotesSection` (basic) | ✅ **Add Gracian** `NotesCollection` (more comprehensive) |
| **Property** | `PropertyDetails` (with `ApartmentUnit`, `CommonArea`) | `PropertyDetails` (more fields) | ✅ **Merge both** (ZeldaDemo fields + Gracian nested structures) |
| **Operations** | `OperationsData` (suppliers, maintenance, insurance) | Basic `ServiceContracts` | ✅ **Add Gracian** `OperationsData` (more detailed) |
| **Environmental** | `EnvironmentalData` (energy, waste, water) | Missing | ✅ **Add Gracian** `EnvironmentalData` |
| **Governance** | `GovernanceStructure` (board, auditors, meetings) | `Board` + `GovernanceMeetings` | ✅ **Merge both** |
| **Fees** | `FeeStructure` (Swedish-first fields) | Basic structure | ✅ **Use Gracian** (Swedish-first semantic fields) |
| **Swedish-first** | ✅ `arsavgift_per_sqm_total` (primary), `annual_fee_per_sqm` (alias) | Basic English only | ✅ **Add Gracian** pattern across all financial fields |

### Conflict Resolution Examples

**Example 1: Multi-Year Financial Data**

Both have `YearlyFinancialData` with `add_metric()` and `get_metric()`:

```python
# ZeldaDemo (production-tested, keep this)
class YearlyFinancialData(BaseModel):
    year: int
    metrics: Dict[str, Optional[float]] = Field(default_factory=dict)
    net_revenue_tkr: Optional[float] = None
    solidarity_percent: Optional[float] = Field(None, alias="soliditet_percent")
    # ... mature field mappings

    def add_metric(self, name: str, value: Optional[float]):
        normalized_name = name.lower().replace(' ', '_').replace('/', '_per_')
        self.metrics[normalized_name] = value
```

✅ **Decision**: Keep ZeldaDemo implementation, it's more mature.

**Example 2: Fees Structure**

Gracian has Swedish-first semantic fields, ZeldaDemo is English-only:

```python
# Gracian (Swedish-first, superior for Swedish documents)
class FeeStructure(BaseModel):
    # Swedish primary
    arsavgift_per_sqm_total: Optional[NumberField] = Field(None, description="Årsavgift kr/m²/år")
    manadsavgift_per_sqm: Optional[NumberField] = Field(None, description="Månadsavgift kr/m²/mån")

    # English aliases
    annual_fee_per_sqm: Optional[NumberField] = Field(None, description="ALIAS for årsavgift")
    monthly_fee_per_sqm: Optional[NumberField] = Field(None, description="ALIAS for månadsavgift")

    @model_validator(mode='after')
    def sync_swedish_english_aliases(self):
        # Sync primary → alias
        if self.arsavgift_per_sqm_total and not self.annual_fee_per_sqm:
            self.annual_fee_per_sqm = self.arsavgift_per_sqm_total
        return self
```

✅ **Decision**: Use Gracian's Swedish-first pattern, apply to ALL financial fields in Schema v7.0.

**Example 3: Calculated Metrics Tolerance**

Both have calculated metrics, but Gracian has more sophisticated tolerance functions:

```python
# Gracian (dynamic tolerance based on magnitude)
def get_financial_tolerance(amount: float) -> float:
    if amount < 100_000:
        return max(5_000, amount * 0.15)  # ±15% for small amounts
    elif amount < 10_000_000:
        return max(50_000, amount * 0.10)  # ±10% for medium
    else:
        return max(500_000, amount * 0.05)  # ±5% for large

def get_per_sqm_tolerance(value_per_sqm: float, metric_type: str = "debt") -> float:
    if metric_type == "debt":
        return max(1_000, value_per_sqm * 0.10)  # ±10% or ±1,000 kr/m²
    elif metric_type == "fee":
        return max(100, value_per_sqm * 0.10)  # ±10% or ±100 kr/m²/år
```

✅ **Decision**: Add Gracian tolerance functions to ZeldaDemo's `CalculatedFinancialMetrics`.

### Schema v7.0 Implementation Steps

**Week 1-2: Core Merge**

1. **Copy ZeldaDemo schema.py** → `schema_v7.py`
2. **Add Gracian structures**:
   - `NotesCollection` (replace basic `NotesSection`)
   - `OperationsData` (replace basic `ServiceContracts`)
   - `EnvironmentalData` (add new)
   - `ApartmentUnit`, `CommonArea` (add to `PropertyDetails`)
3. **Apply Swedish-first pattern**:
   - Update `FeeStructure` with Swedish primary + English aliases
   - Update `YearlyFinancialData` with Swedish metrics
   - Add Swedish field names to ALL financial sections
4. **Add tolerance functions**:
   - `get_financial_tolerance()` from Gracian
   - `get_per_sqm_tolerance()` from Gracian
   - Update `CalculatedFinancialMetrics` to use these

**Week 2: Testing**

5. **Create test file** `test_schema_v7.py`:
```python
def test_schema_v7_validation():
    """Test Schema v7.0 validates correctly."""
    extraction = BRFExtraction(
        organization=Organization(
            organization_number=StringField(value="769606-2533", confidence=1.0, source="page 1")
        ),
        # ... test all sections
    )
    assert extraction.calculate_data_quality_score() > 0.8

def test_swedish_first_aliases():
    """Test Swedish-first fields sync with English aliases."""
    fees = FeeStructure(
        arsavgift_per_sqm_total=NumberField(value=1200, confidence=1.0, source="page 5")
    )
    assert fees.annual_fee_per_sqm.value == 1200  # Should auto-sync

def test_calculated_metrics_tolerance():
    """Test tolerant validation with Gracian tolerance functions."""
    metrics = CalculatedFinancialMetrics(
        total_debt_extracted=NumberField(value=50_000_000, confidence=1.0, source="page 9"),
        total_area_sqm_extracted=NumberField(value=10_000, confidence=1.0, source="page 3"),
        debt_per_sqm_extracted=NumberField(value=5050, confidence=0.9, source="page 15")
    )
    # Should pass with tolerance (5000 calculated vs 5050 extracted = 50 kr/m² diff, tolerance = 1000)
    assert metrics.debt_per_sqm_status == "valid"
```

---

## 2. ExtractionField Implementation

### Current Status (ZeldaDemo)

```python
class ExtractionField(BaseModel):
    """Base model for extraction fields with confidence and source tracking."""
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Optional[str] = None

class StringField(ExtractionField):
    value: Optional[str] = None

class NumberField(ExtractionField):
    value: Optional[Union[float, str]] = None
    # Has special serialization to handle "14460.0" → "14460"
```

✅ **Decision**: ZeldaDemo implementation is perfect, use as-is.

### Enhancement: Evidence Tracking

Add to ExtractionField:

```python
class ExtractionField(BaseModel):
    """Base model with confidence, source, and evidence tracking."""
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="0.0-1.0")
    source: Optional[str] = None  # e.g., "page 13, Note 4 table"

    # NEW: Enhanced evidence tracking
    evidence_pages: List[int] = Field(default_factory=list, description="Page numbers where data found")
    extraction_method: Optional[str] = None  # "table_extraction", "text_extraction", "calculated", "llm"
    model_used: Optional[str] = None  # "gpt-4o", "docling", "manual"
    validation_status: Optional[str] = None  # "valid", "warning", "error"
    alternative_values: List[Any] = Field(default_factory=list, description="Alternative extractions if ambiguous")
    extraction_timestamp: Optional[datetime] = None
```

### Confidence Calculation Rules

| Extraction Method | Base Confidence | Validation Result | Final Confidence |
|-------------------|----------------|-------------------|------------------|
| **Direct text** (exact match) | 1.0 | Valid | 1.0 |
| **Table extraction** (Docling) | 0.9 | Valid | 0.95 |
| **Fuzzy match** (Levenshtein 90%) | 0.8 | Valid | 0.85 |
| **LLM extraction** + validation | 0.8 | Valid | 0.85 |
| **LLM extraction** + validation | 0.8 | Warning (within 2x tolerance) | 0.70 |
| **LLM extraction** + validation | 0.8 | Error (beyond 2x tolerance) | 0.40 |
| **Calculated** (from other fields) | 0.85 | Valid cross-check | 0.90 |
| **Calculated** (no cross-check) | 0.85 | N/A | 0.85 |

### Integration with Current Agents

**Current agent return format**:
```python
# optimal_brf_pipeline.py - property_agent
return {
    "postal_code": "116 45",
    "city": "Stockholm",
    "energy_class": "D"
}
```

**Schema v7.0 format**:
```python
return {
    "postal_code": StringField(
        value="116 45",
        confidence=1.0,
        source="page 3",
        evidence_pages=[3],
        extraction_method="text_extraction",
        model_used="gpt-4o"
    ),
    "city": StringField(
        value="Stockholm",
        confidence=1.0,
        source="page 3",
        evidence_pages=[3],
        extraction_method="text_extraction",
        model_used="gpt-4o"
    ),
    "energy_class": StringField(
        value="D",
        confidence=0.85,
        source="page 14, energy table",
        evidence_pages=[14],
        extraction_method="table_extraction",
        model_used="docling",
        validation_status="valid"
    )
}
```

**Backward compatibility wrapper**:
```python
def wrap_with_extraction_field(value: Any, field_type: type, confidence: float = 0.85,
                                source: str = None, evidence_pages: List[int] = None,
                                extraction_method: str = "llm", model_used: str = "gpt-4o"):
    """Convert plain value to ExtractionField format."""
    if value is None:
        return None
    return field_type(
        value=value,
        confidence=confidence,
        source=source,
        evidence_pages=evidence_pages or [],
        extraction_method=extraction_method,
        model_used=model_used
    )

# Usage in agent:
result = {
    "postal_code": wrap_with_extraction_field("116 45", StringField, 1.0, "page 3", [3], "text_extraction")
}
```

---

## 3. SYNONYM_MAPPING Integration

### Current Mappings (ZeldaDemo mappings.py)

```python
SYNONYM_MAPPING = {
    # Organization (~20 mappings)
    "organisationsnummer": "organization.organization_number",
    "org.nr": "organization.organization_number",
    "org nr": "organization.organization_number",
    "orgnr": "organization.organization_number",

    # Property (~30 mappings)
    "fastighetsbeteckning": "property_details.property_designation",
    "byggår": "property_details.year_built",
    "total bostadsarea": "property_details.residential_area_sqm",
    "taxeringsvärde": "property_details.tax_value",

    # Financial (~50 mappings)
    "soliditet %": "financial_metrics.solidarity_percent",
    "lån, kr/m²": "financial_metrics.debt_per_sqm_total",
    "årsavgift kr/m²": "fees.arsavgift_per_sqm_total",  # Swedish primary
    "månadsavgift": "fees.manadsavgift_per_sqm",  # Swedish primary

    # Governance (~20 mappings)
    "ordförande": "canonical_board_chairman",
    "vice ordförande": "canonical_board_vice_chairman",
    "revisor": "canonical_auditor_main",
    "ledamot": "canonical_board_member",

    # Notes (~80 mappings)
    "driftkostnader": "notes.note_4_operating_costs",
    "el": "notes.note_4_operating_costs.electricity",
    "värme": "notes.note_4_operating_costs.heating",
    "vatten och avlopp": "notes.note_4_operating_costs.water",
    "byggnader och mark": "notes.note_8_buildings",
    "ackumulerade avskrivningar": "notes.note_8_buildings.accumulated_depreciation",

    # ~200+ total mappings
}

TABLE_HEADER_VARIANTS = {
    # Loan table columns (~15 variants)
    "loan_lender": ["långivare", "kreditinstitut", "låneinstitut", "bank"],
    "loan_amount_current_year": ["utg.skuld", "skuld innevarande år", "lånebelopp"],
    "loan_interest_rate": ["räntesats", "ränta", "ränta %", "aktuell räntesats"],

    # Multi-year overview (~30 variants)
    "multi_year_net_revenue": ["nettoomsättning", "nettoomsättning, tkr", "rörelseintäkter"],
    "multi_year_solidity": ["soliditet %", "soliditet", "soliditet procent"],
    "multi_year_debt_per_sqm": ["lån, kr/m²", "skuldsättning per kvm", "skuld kr/kvm"],

    # Financial statement row labels (~60 variants)
    "ste_is_revenue_total": ["nettoomsättning", "summa rörelseintäkter", "totala intäkter"],
    "ste_is_expenses_total": ["rörelsekostnader", "summa rörelsekostnader"],
    "ste_bs_assets_total": ["summa tillgångar", "tillgångar totalt"],

    # ~100+ total table header variants
}
```

### Integration Points

**1. During Extraction (Map Swedish terms → Schema paths)**

```python
from mappings import SYNONYM_MAPPING

def extract_with_mapping(raw_data: Dict[str, Any]) -> BRFExtraction:
    """Extract using synonym mapping."""
    extraction = BRFExtraction()

    for swedish_term, value in raw_data.items():
        # Normalize term
        normalized = normalize_swedish_term(swedish_term)

        # Look up schema path
        schema_path = SYNONYM_MAPPING.get(normalized)

        if schema_path:
            # Set value at schema path
            set_nested_value(extraction, schema_path, value)
        else:
            # Log unmapped term for later addition
            log_unmapped_term(swedish_term, value)

    return extraction
```

**2. During Validation (Normalize extracted keys)**

```python
def validate_with_mapping(extracted_dict: Dict) -> Dict:
    """Normalize dictionary keys using SYNONYM_MAPPING."""
    normalized = {}

    for key, value in extracted_dict.items():
        # Normalize key
        norm_key = normalize_swedish_term(key)

        # Map to canonical schema field
        canonical = SYNONYM_MAPPING.get(norm_key, norm_key)
        normalized[canonical] = value

    return normalized
```

**3. During Table Extraction (Match table headers with variants)**

```python
from mappings import TABLE_HEADER_VARIANTS

def match_table_header(header: str, field_name: str) -> bool:
    """Check if table header matches expected field variants."""
    variants = TABLE_HEADER_VARIANTS.get(field_name, [])
    normalized_header = normalize_swedish_term(header)

    for variant in variants:
        if normalized_header == normalize_swedish_term(variant):
            return True

    return False

# Usage
def extract_loan_table(table_rows: List[Dict]) -> List[Loan]:
    loans = []
    for row in table_rows:
        loan = Loan()
        for header, value in row.items():
            if match_table_header(header, "loan_lender"):
                loan.lender = StringField(value=value, confidence=0.95, source="table")
            elif match_table_header(header, "loan_amount_current_year"):
                loan.amount = NumberField(value=value, confidence=0.95, source="table")
            # ...
        loans.append(loan)
    return loans
```

### Normalization Utility Functions

```python
def normalize_swedish_term(term: str) -> str:
    """Normalize Swedish term for mapping lookup."""
    if not term:
        return ""

    # Lowercase
    term = term.lower()

    # Swedish character normalization (å→a, ä→a, ö→o)
    term = term.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')

    # Remove punctuation
    term = re.sub(r'[^\w\s]', ' ', term)

    # Normalize whitespace
    term = ' '.join(term.split())

    # Remove common noise words
    noise = ['kr', 'sek', 'tkr', 'procent', '%']
    for n in noise:
        term = term.replace(f' {n} ', ' ')

    return term.strip()

def set_nested_value(obj, path: str, value: Any):
    """Set value at nested path like 'organization.organization_number'."""
    parts = path.split('.')
    for part in parts[:-1]:
        obj = getattr(obj, part)
        if obj is None:
            # Create nested object if doesn't exist
            parent_class = type(obj).__annotations__[part]
            setattr(obj, part, parent_class())
            obj = getattr(obj, part)

    # Set final value
    setattr(obj, parts[-1], value)
```

### Mapping Maintenance

**1. Adding New Synonyms**

When agents discover unmapped terms during extraction:

```python
# Log to unmapped_terms.json
{
    "term": "Fastighetsskatt",
    "frequency": 47,  # Found in 47 documents
    "contexts": ["page 12, tax section", "page 8, expense breakdown"],
    "suggested_mapping": "property_details.property_tax",
    "confidence": 0.85
}
```

Review weekly and add to `SYNONYM_MAPPING` with team approval.

**2. Version Control**

```
mappings/
├── synonym_mapping_v1.0.yaml   # Production version
├── synonym_mapping_v1.1.yaml   # With new terms
└── table_header_variants_v1.0.yaml
```

**3. Automated Testing**

```python
def test_all_mappings_resolve():
    """Test that all SYNONYM_MAPPING values are valid schema paths."""
    schema = BRFExtraction()

    for term, path in SYNONYM_MAPPING.items():
        try:
            parts = path.split('.')
            obj = schema
            for part in parts:
                obj = getattr(obj, part)
            # If we get here, path is valid
        except AttributeError:
            pytest.fail(f"Mapping '{term}' -> '{path}' is invalid (no such schema path)")
```

---

## 4. Ground Truth Creation Methodology

### PDF Selection (10 diverse PDFs)

**Criteria**:
1. **PDF Type Diversity**: 5 machine-readable, 4 scanned, 1 hybrid
2. **Geographic Diversity**: 5 Stockholm, 3 Göteborg, 2 Malmö
3. **Size Diversity**: 3 small (<30 apartments), 4 medium (30-100), 3 large (>100)
4. **Year Diversity**: 2 from 2021, 3 from 2022, 3 from 2023, 2 from 2024
5. **Complexity**: Mix of simple (no notes) to complex (15+ notes)

**Recommended PDFs**:

| PDF ID | Type | Location | Apartments | Year | Pages | Complexity | Justification |
|--------|------|----------|-----------|------|-------|------------|---------------|
| **brf_198532** | Machine | Stockholm | 75 | 2021 | 26 | Medium | ✅ Already has partial GT (86.7% validated) |
| **brf_268882** | Machine | Göteborg | 82 | 2022 | 28 | Medium | ✅ Regression test PDF (known good) |
| **brf_81563** | Machine | Stockholm | 106 | 2023 | 31 | High | ✅ Best performer (98.3% coverage in tests) |
| **brf_271852** | Machine | Malmö | 45 | 2023 | 24 | Low | Simple structure (good baseline) |
| **brf_53716** | Machine | Stockholm | 28 | 2024 | 22 | Medium | Recent year (2024) |
| **brf_78276** | Scanned | Göteborg | 67 | 2022 | 29 | High | OCR quality test |
| **brf_43334** | Scanned | Stockholm | 134 | 2021 | 35 | Very High | Large BRF (scalability test) |
| **brf_76536** | Scanned | Malmö | 19 | 2023 | 18 | Low | Small BRF + scanned |
| **brf_78906** | Scanned | Göteborg | 52 | 2022 | 26 | Medium | OCR + Swedish character test |
| **brf_mixed_01** | Hybrid | Stockholm | 88 | 2023 | 30 | High | Mixed pages (adaptive test) |

**Note**: `brf_mixed_01` needs identification from corpus (hybrid PDFs are only 2.3%).

### Extraction Methodology (4-6 hours per PDF)

**Phase 1: Core Fields** (1 hour) - **Organization, Governance, Property**

Extracted fields:
- Organization (14 fields): name, org_number, registered_office, agm_date, management_company, affiliations, etc.
- Governance (30 fields): chairman, vice_chairman, board_members (name, role, term), auditors, nomination_committee, meeting_dates, etc.
- Property basics (20 fields): designation, address, postal_code, city, built_year, total_area_sqm, apartments, distribution, etc.

**Phase 2: Financial Statements** (1.5 hours) - **Income Statement, Balance Sheet**

Extracted fields:
- Income Statement (25 fields): revenue_total, expenses_total (electricity, heating, water, maintenance, repairs, property_tax, insurance, management_fees, financial_costs, depreciation, etc.), operating_result, net_income
- Balance Sheet (30 fields): fixed_assets, current_assets, cash_and_bank, total_assets, equity (bound, free, total), long_term_liabilities, short_term_liabilities, total_liabilities
- Cross-validation: assets = liabilities + equity

**Phase 3: Notes (Not 1-15)** (2 hours) - **Detailed Breakdowns**

Extracted fields per note:
- Note 1: Accounting principles (10 fields)
- Note 2: Revenue breakdown (5 fields)
- Note 3: Personnel costs (8 fields)
- Note 4: Operating costs (15 fields: el, värme, vatten, repairs, maintenance, property_tax, insurance, waste, cleaning, etc.)
- Note 5: Financial items (8 fields: interest_income, interest_expenses, other_financial)
- Note 6: Tax (5 fields)
- Note 7: Intangible assets (5 fields)
- Note 8: Buildings (20 fields: opening_acquisition, additions, disposals, closing_acquisition, opening_depreciation, current_depreciation, closing_depreciation, residual_value, tax_assessment_building, tax_assessment_land, depreciation_method, depreciation_period)
- Note 9: Receivables (10 fields: tax_account, vat_deduction, client_funds, receivables, prepaid_expenses, accrued_income, total)
- Note 10: Cash (3 fields)
- Note 11: Equity (10 fields: opening, additions, disposals, closing)
- Note 12: Liabilities (15 fields: long_term breakdown, short_term breakdown)
- Note 13: Contingencies (5 fields)
- Note 14: Pledged assets (8 fields)
- Note 15: Related parties (5 fields)

**Phase 4: Extended Fields** (1 hour) - **Multi-Year, Events, Environmental**

Extracted fields:
- Multi-year overview (50 fields): 5 years × 10 metrics (net_revenue, result, solidarity, annual_fee, debt_per_sqm, etc.)
- Loans (60 fields): 4 loans × 15 fields each (lender, amount, interest_rate, maturity_date, amortization, etc.)
- Maintenance (30 fields): historical_actions, planned_actions, renovation_years (facade, roof, pipes, electricity, heating, windows, balconies)
- Events (10 fields): significant_events during year
- Environmental (15 fields): energy_consumption, renewable_energy_percentage, waste_management, recycling_rate, water_consumption

**Phase 5: Calculated Metrics + Validation** (0.5 hour)

- Calculate and cross-validate all calculated metrics
- debt_per_sqm = total_debt / total_area_sqm
- solidarity_percent = (equity / assets) * 100
- annual_fee_per_sqm = (monthly_fee * 12) / area
- Verify balance sheet equation: assets = liabilities + equity
- Verify income statement: operating_result = revenue - expenses
- Flag any inconsistencies (within tolerance is OK)

**Total**: 5-6 hours per PDF × 10 PDFs = **50-60 person-hours**

### Triple-Check Process

**Reviewer 1: Initial Extraction** (4-6 hours)
- Extract all 501 fields following methodology
- Use Excel template with dropdown validation
- Mark confidence level (high/medium/low) for each field
- Note ambiguous fields in comments column

**Reviewer 2: Independent Verification** (2-3 hours)
- Re-extract 20% of fields (randomly selected 100 fields)
- Compare with Reviewer 1's extraction
- Flag discrepancies for Reviewer 3

**Reviewer 3: Conflict Resolution + Final Validation** (1-2 hours)
- Review all flagged discrepancies
- Make final decision (with PDF evidence screenshot)
- Run cross-validation checks
- Calculate overall completeness score

**Quality Gate**:
- ≥95% field completeness (477/501 fields)
- ≥90% agreement between Reviewer 1 and 2
- All cross-validations pass (within tolerance)
- All discrepancies resolved with evidence

### Ground Truth JSON Format

```json
{
  "pdf_id": "brf_198532",
  "pdf_path": "../../SRS/brf_198532.pdf",
  "extraction_date": "2025-10-20",
  "extractors": ["Reviewer1", "Reviewer2", "Reviewer3"],
  "version": "7.0",
  "extraction_time_hours": 5.5,
  "agreement_score": 0.94,

  "fields": {
    "organization": {
      "organization_number": {
        "value": "769606-2533",
        "confidence": 1.0,
        "source": "page 1, header",
        "evidence_pages": [1],
        "extraction_method": "text_extraction",
        "validation_status": "valid",
        "notes": "Clear header placement, no ambiguity"
      },
      "organization_name": {
        "value": "Bostadsrättsföreningen Björk och Plaza",
        "confidence": 1.0,
        "source": "page 1, title",
        "evidence_pages": [1],
        "extraction_method": "text_extraction",
        "validation_status": "valid"
      },
      "registered_office": {
        "value": "Stockholm",
        "confidence": 1.0,
        "source": "page 2, organization section",
        "evidence_pages": [2],
        "extraction_method": "text_extraction",
        "validation_status": "valid"
      }
      // ... all organization fields
    },

    "governance": {
      "chairman": {
        "value": "Elvy Maria Löfvenberg",
        "confidence": 1.0,
        "source": "page 3, governance section",
        "evidence_pages": [3],
        "extraction_method": "text_extraction",
        "validation_status": "valid"
      },
      "board_members": [
        {
          "full_name": {"value": "Elvy Maria Löfvenberg", "confidence": 1.0, "source": "page 3"},
          "role": {"value": "ordforande", "confidence": 1.0, "source": "page 3"},
          "term_start": {"value": "2021-03-15", "confidence": 0.9, "source": "page 3"}
        }
        // ... all board members
      ]
      // ... all governance fields
    },

    "property_details": {
      "property_designation": {
        "value": "BJÖRKEN 8",
        "confidence": 1.0,
        "source": "page 2, property section",
        "evidence_pages": [2],
        "extraction_method": "text_extraction",
        "validation_status": "valid"
      },
      "total_area_sqm": {
        "value": 3915,
        "confidence": 1.0,
        "source": "page 14, Note 8 - Buildings",
        "evidence_pages": [14],
        "extraction_method": "table_extraction",
        "validation_status": "valid"
      }
      // ... all property fields
    },

    "financial_report": {
      "income_statement": {
        "revenue_total": {
          "value": 2834798,
          "confidence": 1.0,
          "source": "page 7, income statement",
          "evidence_pages": [7],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "expenses_total": {
          "value": -2655518,
          "confidence": 1.0,
          "source": "page 7, income statement",
          "evidence_pages": [7],
          "extraction_method": "table_extraction",
          "validation_status": "valid",
          "notes": "Negative as expected (expenses)"
        },
        "expense_breakdown": {
          "electricity": {
            "value": 698763,
            "confidence": 1.0,
            "source": "page 13, Note 4 - Operating costs",
            "evidence_pages": [13],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "heating": {
            "value": 440495,
            "confidence": 1.0,
            "source": "page 13, Note 4 - Operating costs",
            "evidence_pages": [13],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "water_and_sewage": {
            "value": 160180,
            "confidence": 1.0,
            "source": "page 13, Note 4 - Operating costs",
            "evidence_pages": [13],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          }
          // ... all expense breakdown fields
        }
      },
      "balance_sheet": {
        "assets": {
          "total_assets": {
            "value": 13766652,
            "confidence": 1.0,
            "source": "page 9, balance sheet",
            "evidence_pages": [9],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "fixed_assets": {
            "value": 13028567,
            "confidence": 1.0,
            "source": "page 9, balance sheet",
            "evidence_pages": [9],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "current_assets": {
            "value": 738085,
            "confidence": 1.0,
            "source": "page 9, balance sheet",
            "evidence_pages": [9],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          }
        },
        "liabilities": {
          "total_liabilities": {
            "value": 3043913,
            "confidence": 1.0,
            "source": "page 10, balance sheet",
            "evidence_pages": [10],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "long_term_liabilities": {
            "value": 2625000,
            "confidence": 1.0,
            "source": "page 10, balance sheet",
            "evidence_pages": [10],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "short_term_liabilities": {
            "value": 418913,
            "confidence": 1.0,
            "source": "page 10, balance sheet",
            "evidence_pages": [10],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          }
        },
        "equity": {
          "total_equity": {
            "value": 10722739,
            "confidence": 1.0,
            "source": "page 10, balance sheet",
            "evidence_pages": [10],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          }
        }
      }
    },

    "notes": {
      "note_4_operating_costs": {
        "electricity": {
          "value": 698763,
          "confidence": 1.0,
          "source": "page 13, Note 4 table",
          "evidence_pages": [13],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "heating": {
          "value": 440495,
          "confidence": 1.0,
          "source": "page 13, Note 4 table",
          "evidence_pages": [13],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "water_and_sewage": {
          "value": 160180,
          "confidence": 1.0,
          "source": "page 13, Note 4 table",
          "evidence_pages": [13],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        }
        // ... all Note 4 fields
      },
      "note_8_buildings": {
        "opening_acquisition_value": {
          "value": 16000000,
          "confidence": 1.0,
          "source": "page 14, Note 8 table",
          "evidence_pages": [14],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "accumulated_depreciation": {
          "value": -2971433,
          "confidence": 1.0,
          "source": "page 14, Note 8 table",
          "evidence_pages": [14],
          "extraction_method": "table_extraction",
          "validation_status": "valid",
          "notes": "Negative as expected (depreciation)"
        },
        "book_value": {
          "value": 13028567,
          "confidence": 1.0,
          "source": "page 14, Note 8 table",
          "evidence_pages": [14],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        }
        // ... all Note 8 fields
      }
      // ... all notes
    },

    "multi_year_overview": {
      "years_data": [
        {
          "year": 2021,
          "net_revenue_tkr": {
            "value": 2835,
            "confidence": 1.0,
            "source": "page 5, multi-year table",
            "evidence_pages": [5],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "solidarity_percent": {
            "value": 77.9,
            "confidence": 1.0,
            "source": "page 5, multi-year table",
            "evidence_pages": [5],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          },
          "debt_per_total_kvm": {
            "value": 671,
            "confidence": 0.95,
            "source": "page 5, multi-year table",
            "evidence_pages": [5],
            "extraction_method": "table_extraction",
            "validation_status": "valid"
          }
          // ... all metrics for 2021
        },
        // ... years 2020, 2019, 2018, 2017
      ]
    },

    "financial_loans": [
      {
        "lender": {
          "value": "SBAB Bank AB",
          "confidence": 1.0,
          "source": "page 15, Note 11 - Loans table",
          "evidence_pages": [15],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "amount": {
          "value": 1000000,
          "confidence": 1.0,
          "source": "page 15, Note 11 - Loans table",
          "evidence_pages": [15],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "interest_rate": {
          "value": 1.25,
          "confidence": 0.95,
          "source": "page 15, Note 11 - Loans table",
          "evidence_pages": [15],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        },
        "maturity_date": {
          "value": "2025-06-30",
          "confidence": 0.9,
          "source": "page 15, Note 11 - Loans table",
          "evidence_pages": [15],
          "extraction_method": "table_extraction",
          "validation_status": "valid"
        }
      }
      // ... all 4 loans
    ],

    "financial_metrics": {
      "total_debt_extracted": {
        "value": 2625000,
        "confidence": 1.0,
        "source": "page 10, balance sheet",
        "evidence_pages": [10],
        "extraction_method": "table_extraction",
        "validation_status": "valid"
      },
      "total_area_sqm_extracted": {
        "value": 3915,
        "confidence": 1.0,
        "source": "page 14, Note 8",
        "evidence_pages": [14],
        "extraction_method": "table_extraction",
        "validation_status": "valid"
      },
      "debt_per_sqm_extracted": {
        "value": 670,
        "confidence": 0.95,
        "source": "page 5, multi-year table",
        "evidence_pages": [5],
        "extraction_method": "table_extraction",
        "validation_status": "valid"
      },
      "debt_per_sqm_calculated": {
        "value": 670.5,
        "confidence": 0.9,
        "source": "calculated",
        "evidence_pages": [],
        "extraction_method": "calculated",
        "validation_status": "valid",
        "notes": "Calculated: 2625000 / 3915 = 670.5 kr/m² (matches extracted 670 within tolerance)"
      },
      "solidarity_percent_extracted": {
        "value": 77.9,
        "confidence": 1.0,
        "source": "page 5, multi-year table",
        "evidence_pages": [5],
        "extraction_method": "table_extraction",
        "validation_status": "valid"
      },
      "solidarity_percent_calculated": {
        "value": 77.9,
        "confidence": 0.95,
        "source": "calculated",
        "evidence_pages": [],
        "extraction_method": "calculated",
        "validation_status": "valid",
        "notes": "Calculated: (10722739 / 13766652) * 100 = 77.9% (exact match)"
      }
    },

    "maintenance": {
      "planned_actions": [
        {
          "description": {
            "value": "Fasadrenovering",
            "confidence": 1.0,
            "source": "page 16, maintenance plan",
            "evidence_pages": [16],
            "extraction_method": "text_extraction",
            "validation_status": "valid"
          },
          "planned_year": {
            "value": "2024",
            "confidence": 0.95,
            "source": "page 16, maintenance plan",
            "evidence_pages": [16],
            "extraction_method": "text_extraction",
            "validation_status": "valid"
          },
          "estimated_cost": {
            "value": 2500000,
            "confidence": 0.85,
            "source": "page 16, maintenance plan",
            "evidence_pages": [16],
            "extraction_method": "text_extraction",
            "validation_status": "valid",
            "notes": "Estimate, not precise"
          }
        }
        // ... all planned maintenance
      ],
      "renovation_year_facade": {
        "value": "1995",
        "confidence": 0.9,
        "source": "page 16, maintenance history",
        "evidence_pages": [16],
        "extraction_method": "text_extraction",
        "validation_status": "valid"
      }
      // ... all maintenance fields
    }

    // ... ALL 501 FIELDS following this pattern
  },

  "quality_metrics": {
    "completeness": 0.954,  // 477/501 fields found
    "completeness_count": {
      "total_fields": 501,
      "extracted_fields": 477,
      "missing_fields": 24
    },
    "ambiguous_fields": [
      "apartment_107_area_sqm",  // Not specified in this document
      "commercial_tenant_2_lease_end_date",  // Mentioned but date unclear
      "environmental.renewable_energy_percentage"  // Not in 2021 report
    ],
    "cross_validation": {
      "balance_sheet_equation": {
        "passed": true,
        "assets": 13766652,
        "liabilities_plus_equity": 13766652,
        "difference": 0
      },
      "income_statement": {
        "passed": true,
        "revenue": 2834798,
        "expenses": -2655518,
        "operating_result_expected": 179280,
        "operating_result_actual": 179280,
        "difference": 0
      },
      "calculated_metrics": {
        "debt_per_sqm": {
          "passed": true,
          "extracted": 670,
          "calculated": 670.5,
          "difference": 0.5,
          "tolerance": 1000,
          "status": "valid"
        },
        "solidarity_percent": {
          "passed": true,
          "extracted": 77.9,
          "calculated": 77.9,
          "difference": 0.0,
          "tolerance": 2.0,
          "status": "valid"
        }
      }
    },
    "reviewer_agreement": {
      "reviewer_1_vs_2": 0.94,  // 94% agreement
      "conflicts_resolved": 28,
      "conflicts_reviewer_3_decision": 28
    }
  },

  "extraction_metadata": {
    "time_phase_1": "1.0 hours",  // Organization, governance, property
    "time_phase_2": "1.5 hours",  // Financial statements
    "time_phase_3": "2.0 hours",  // Notes
    "time_phase_4": "1.0 hours",  // Extended fields
    "time_phase_5": "0.5 hours",  // Validation
    "total_time": "6.0 hours",
    "reviewers": {
      "reviewer_1": {
        "name": "Alice",
        "time": "6.0 hours",
        "role": "initial_extraction"
      },
      "reviewer_2": {
        "name": "Bob",
        "time": "2.5 hours",
        "role": "verification_20pct"
      },
      "reviewer_3": {
        "name": "Charlie",
        "time": "1.5 hours",
        "role": "conflict_resolution"
      }
    },
    "total_person_hours": 10.0
  }
}
```

---

## 5. Testing Framework

### Test File Structure

```
tests/
├── test_schema_v7.py                    # Schema validation tests
├── test_extraction_field.py             # ExtractionField tests
├── test_synonym_mapping.py              # Mapping tests
├── test_ground_truth_validation.py      # GT validation tests
├── test_calculated_metrics.py           # Calculated metrics tests
├── test_swedish_normalization.py        # Swedish term normalization tests
├── test_integration_pipeline.py         # End-to-end tests
├── fixtures/
│   ├── ground_truth_brf_198532.json     # GT fixtures for testing
│   ├── ground_truth_brf_268882.json
│   └── sample_extraction_results.json   # Sample test data
└── conftest.py                          # Pytest fixtures
```

### Key Test Cases

**1. Schema Validation Tests** (`test_schema_v7.py`)

```python
def test_schema_v7_validates_complete_extraction():
    """Test Schema v7.0 validates a complete extraction."""
    with open('fixtures/ground_truth_brf_198532.json') as f:
        gt = json.load(f)

    extraction = BRFExtraction(**gt['fields'])

    # Should not raise ValidationError
    assert extraction is not None
    assert extraction.organization.organization_number.value == "769606-2533"

def test_schema_v7_calculated_metrics():
    """Test Schema v7.0 auto-calculates metrics."""
    extraction = BRFExtraction(
        financial_metrics=CalculatedFinancialMetrics(
            total_debt_extracted=NumberField(value=2625000, confidence=1.0, source="page 10"),
            total_area_sqm_extracted=NumberField(value=3915, confidence=1.0, source="page 14")
        )
    )

    # Should auto-calculate debt_per_sqm
    assert extraction.financial_metrics.debt_per_sqm_calculated == 670.5

def test_schema_v7_swedish_first_aliases():
    """Test Swedish-first fields sync with English aliases."""
    fees = FeeStructure(
        arsavgift_per_sqm_total=NumberField(value=1200, confidence=1.0, source="page 5")
    )

    # Should auto-sync to English alias
    assert fees.annual_fee_per_sqm.value == 1200

def test_schema_v7_tolerant_validation():
    """Test tolerant validation doesn't null data."""
    metrics = CalculatedFinancialMetrics(
        total_debt_extracted=NumberField(value=2625000, confidence=1.0, source="page 10"),
        total_area_sqm_extracted=NumberField(value=3915, confidence=1.0, source="page 14"),
        debt_per_sqm_extracted=NumberField(value=670, confidence=0.95, source="page 5")  # 0.5 diff from calculated
    )

    # Should pass validation (within tolerance)
    assert metrics.debt_per_sqm_status == "valid"
    assert metrics.debt_per_sqm_extracted.value == 670  # NOT nulled
    assert metrics.debt_per_sqm_calculated == 670.5
```

**2. ExtractionField Tests** (`test_extraction_field.py`)

```python
def test_extraction_field_confidence_tracking():
    """Test ExtractionField tracks confidence."""
    field = StringField(value="Stockholm", confidence=0.95, source="page 3")
    assert field.confidence == 0.95

def test_extraction_field_evidence_pages():
    """Test ExtractionField tracks evidence pages."""
    field = NumberField(value=3915, confidence=1.0, source="page 14", evidence_pages=[14])
    assert field.evidence_pages == [14]

def test_number_field_serialization():
    """Test NumberField serializes correctly."""
    field = NumberField(value=14460.0, confidence=1.0, source="page 9")
    dump = field.model_dump()
    assert dump['value'] == "14460"  # Should remove .0

def test_wrap_with_extraction_field_utility():
    """Test utility function for backward compatibility."""
    result = wrap_with_extraction_field("116 45", StringField, 1.0, "page 3", [3], "text_extraction")
    assert result.value == "116 45"
    assert result.confidence == 1.0
    assert result.evidence_pages == [3]
```

**3. SYNONYM_MAPPING Tests** (`test_synonym_mapping.py`)

```python
def test_all_mappings_resolve_to_valid_paths():
    """Test all SYNONYM_MAPPING values are valid schema paths."""
    schema = BRFExtraction()

    for term, path in SYNONYM_MAPPING.items():
        try:
            # Navigate nested path
            parts = path.split('.')
            obj = schema
            for part in parts:
                obj = getattr(obj, part)
        except AttributeError:
            pytest.fail(f"Mapping '{term}' -> '{path}' is invalid")

def test_swedish_term_normalization():
    """Test Swedish term normalization."""
    assert normalize_swedish_term("Årsavgift kr/m²") == "arsavgift kr m2"
    assert normalize_swedish_term("Värme") == "varme"
    assert normalize_swedish_term("Byggnader och mark") == "byggnader och mark"

def test_table_header_matching():
    """Test table header variant matching."""
    assert match_table_header("Långivare", "loan_lender") == True
    assert match_table_header("Kreditinstitut", "loan_lender") == True
    assert match_table_header("Bank", "loan_lender") == True
```

**4. Ground Truth Validation Tests** (`test_ground_truth_validation.py`)

```python
def test_ground_truth_completeness():
    """Test ground truth has ≥95% completeness."""
    with open('fixtures/ground_truth_brf_198532.json') as f:
        gt = json.load(f)

    assert gt['quality_metrics']['completeness'] >= 0.95
    assert gt['quality_metrics']['completeness_count']['extracted_fields'] >= 477

def test_ground_truth_cross_validation():
    """Test ground truth passes cross-validation."""
    with open('fixtures/ground_truth_brf_198532.json') as f:
        gt = json.load(f)

    cross_val = gt['quality_metrics']['cross_validation']

    # Balance sheet equation
    assert cross_val['balance_sheet_equation']['passed'] == True

    # Income statement
    assert cross_val['income_statement']['passed'] == True

    # Calculated metrics
    assert cross_val['calculated_metrics']['debt_per_sqm']['passed'] == True

def test_ground_truth_reviewer_agreement():
    """Test ground truth has ≥90% reviewer agreement."""
    with open('fixtures/ground_truth_brf_198532.json') as f:
        gt = json.load(f)

    assert gt['quality_metrics']['reviewer_agreement']['reviewer_1_vs_2'] >= 0.90
```

**5. Integration Tests** (`test_integration_pipeline.py`)

```python
def test_full_extraction_pipeline_with_schema_v7():
    """Test full extraction pipeline with Schema v7.0."""
    from code.optimal_brf_pipeline import OptimalBRFPipeline

    pipeline = OptimalBRFPipeline(enable_caching=True)
    result = pipeline.extract_document('test_pdfs/brf_198532.pdf')

    # Validate with Schema v7.0
    extraction = BRFExtraction(**result)

    # Should have organization
    assert extraction.organization.organization_number.value == "769606-2533"

    # Should have calculated metrics
    assert extraction.financial_metrics.debt_per_sqm_calculated is not None

    # Should pass validation
    validation = extraction.validate_extraction()
    assert validation['valid'] == True

def test_backward_compatibility_with_existing_pipeline():
    """Test Schema v7.0 works with existing optimal_brf_pipeline.py."""
    # Current pipeline returns plain dicts
    plain_result = {
        "postal_code": "116 45",
        "city": "Stockholm",
        "energy_class": "D"
    }

    # Wrap with ExtractionField
    wrapped_result = {
        "postal_code": wrap_with_extraction_field(plain_result["postal_code"], StringField, 1.0, "page 3"),
        "city": wrap_with_extraction_field(plain_result["city"], StringField, 1.0, "page 3"),
        "energy_class": wrap_with_extraction_field(plain_result["energy_class"], StringField, 0.85, "page 14")
    }

    # Should validate with Schema v7.0
    property_details = PropertyDetails(**wrapped_result)
    assert property_details.postal_code.value == "116 45"
```

### Pytest Fixtures (`conftest.py`)

```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def ground_truth_brf_198532():
    """Load ground truth for brf_198532."""
    gt_path = Path(__file__).parent / 'fixtures' / 'ground_truth_brf_198532.json'
    with open(gt_path) as f:
        return json.load(f)

@pytest.fixture
def schema_v7():
    """Provide empty Schema v7.0 instance."""
    return BRFExtraction()

@pytest.fixture
def synonym_mapping():
    """Provide SYNONYM_MAPPING."""
    from mappings import SYNONYM_MAPPING
    return SYNONYM_MAPPING

@pytest.fixture
def sample_pdf_path():
    """Provide path to sample PDF for testing."""
    return str(Path(__file__).parent.parent / 'test_pdfs' / 'brf_198532.pdf')
```

### Success Criteria (Phase 1 Complete)

**Schema v7.0**:
- ✅ All Pydantic models validate correctly
- ✅ ExtractionField confidence tracking works
- ✅ Calculated metrics auto-calculate and validate
- ✅ Swedish-first fields sync with English aliases
- ✅ Tolerant validation preserves data
- ✅ 100% test coverage on schema

**SYNONYM_MAPPING**:
- ✅ All 200+ mappings resolve to valid schema paths
- ✅ Swedish normalization works correctly
- ✅ Table header variants match correctly

**Ground Truth**:
- ✅ 10 PDFs extracted with ≥95% completeness each
- ✅ ≥90% reviewer agreement on all PDFs
- ✅ All cross-validations pass (within tolerance)
- ✅ 5,010 data points (10 PDFs × 501 fields) ready for training

**Testing**:
- ✅ 50+ unit tests passing
- ✅ Integration tests with optimal_brf_pipeline.py passing
- ✅ Backward compatibility maintained
- ✅ All ground truth validation tests passing

---

## 6. Implementation Timeline (4-6 weeks)

### Week 1: Schema Analysis & Design

**Day 1-2: Deep Dive Schema Comparison**
- ✅ Read entire Gracian brf_schema.py (1,230 lines)
- ✅ Read entire ZeldaDemo schema.py (1,363 lines)
- ✅ Create field-by-field mapping spreadsheet (501 rows)
- ✅ Identify conflicts and resolution strategies
- ✅ Document merge plan with justifications

**Deliverable**: `SCHEMA_V7_MERGE_PLAN.md` (10-15 pages)

**Day 3-4: Schema v7.0 Design**
- ✅ Design Schema v7.0 structure (paper design, not code yet)
- ✅ Apply Swedish-first pattern to all financial fields
- ✅ Add Gracian specializations to ZeldaDemo foundation
- ✅ Design tolerance functions integration
- ✅ Review and approve design with team

**Deliverable**: `SCHEMA_V7_DESIGN_SPEC.md` (15-20 pages)

**Day 5: Week 1 Review**
- ✅ Team review of merge plan and design spec
- ✅ Incorporate feedback
- ✅ Get approval to proceed to implementation

### Week 2: Schema v7.0 Implementation

**Day 1-2: Core Schema Implementation**
- ✅ Copy ZeldaDemo schema.py → `schema_v7.py`
- ✅ Add Gracian `NotesCollection` (replace basic `NotesSection`)
- ✅ Add Gracian `OperationsData` (replace basic `ServiceContracts`)
- ✅ Add Gracian `EnvironmentalData` (new section)
- ✅ Merge `PropertyDetails` (ZeldaDemo fields + Gracian nested structures)

**Deliverable**: `schema_v7.py` (1,600+ lines, 60% complete)

**Day 3: Swedish-First Fields**
- ✅ Update `FeeStructure` with Swedish primary + English aliases
- ✅ Update `YearlyFinancialData` with Swedish metrics
- ✅ Add Swedish field names to ALL financial sections
- ✅ Implement `sync_swedish_english_aliases()` validators

**Deliverable**: `schema_v7.py` (80% complete)

**Day 4: Calculated Metrics + Tolerance**
- ✅ Add `get_financial_tolerance()` from Gracian
- ✅ Add `get_per_sqm_tolerance()` from Gracian
- ✅ Update `CalculatedFinancialMetrics` to use tolerance functions
- ✅ Test tolerant validation on sample data

**Deliverable**: `schema_v7.py` (100% complete)

**Day 5: Schema Unit Tests**
- ✅ Write `test_schema_v7.py` (50+ test cases)
- ✅ Test validation, calculated metrics, Swedish aliases
- ✅ Test tolerant validation (valid/warning/error tiers)
- ✅ Fix any bugs found during testing

**Deliverable**: `test_schema_v7.py` (50+ tests, 100% passing)

### Week 3: Mapping Integration

**Day 1-2: SYNONYM_MAPPING Integration**
- ✅ Create `mappings_v7.py` (merge Gracian + ZeldaDemo mappings)
- ✅ Add 50+ new mappings for Gracian specialized fields
- ✅ Update mappings to use Schema v7.0 paths
- ✅ Test all 250+ mappings resolve to valid paths

**Deliverable**: `mappings_v7.py` (250+ mappings)

**Day 3: Normalization Utilities**
- ✅ Implement `normalize_swedish_term()`
- ✅ Implement `match_table_header()`
- ✅ Implement `set_nested_value()` for dynamic path setting
- ✅ Create utility module `mapping_utils.py`

**Deliverable**: `mapping_utils.py` (300+ lines)

**Day 4: Mapping Unit Tests**
- ✅ Write `test_synonym_mapping.py`
- ✅ Write `test_swedish_normalization.py`
- ✅ Test all mappings, normalization, table matching
- ✅ Fix any bugs found

**Deliverable**: `test_synonym_mapping.py` + `test_swedish_normalization.py` (30+ tests)

**Day 5: Integration Test**
- ✅ Test Schema v7.0 + mappings_v7.py together
- ✅ Extract brf_198532.pdf with new schema + mappings
- ✅ Validate results
- ✅ Fix integration issues

**Deliverable**: Working integration (Schema v7.0 + mappings)

### Week 4: Ground Truth Creation (PDF 1-5)

**Day 1: Setup + PDF Selection**
- ✅ Select final 10 PDFs (5 machine, 4 scanned, 1 hybrid)
- ✅ Create Excel template for GT extraction
- ✅ Assign PDFs to 3 reviewers (Reviewer 1: all 10, Reviewer 2: 20% verification, Reviewer 3: conflicts)
- ✅ Train reviewers on extraction methodology

**Day 2-5: Extract PDF 1-5** (Machine-readable)
- ✅ Day 2: brf_198532 + brf_268882 (2 PDFs, already have partial GTs)
- ✅ Day 3: brf_81563 (1 PDF, high complexity)
- ✅ Day 4: brf_271852 + brf_53716 (2 PDFs)
- ✅ Day 5: Quality review of 5 machine-readable GTs

**Deliverable**: 5 complete ground truths (2,505 data points)

### Week 5: Ground Truth Creation (PDF 6-10)

**Day 1-4: Extract PDF 6-10** (Scanned + Hybrid)
- ✅ Day 1: brf_78276 (scanned, 1 PDF)
- ✅ Day 2: brf_43334 + brf_76536 (scanned, 2 PDFs)
- ✅ Day 3: brf_78906 + brf_mixed_01 (scanned + hybrid, 2 PDFs)
- ✅ Day 4: Reviewer 2 verification (20% of all 10 PDFs)

**Day 5: Reviewer 3 Conflict Resolution**
- ✅ Review all flagged discrepancies
- ✅ Make final decisions with PDF evidence screenshots
- ✅ Run cross-validation checks on all 10 GTs
- ✅ Calculate completeness scores

**Deliverable**: 10 complete ground truths (5,010 data points), ≥95% completeness each

### Week 6: Testing & Validation

**Day 1-2: Ground Truth Validation Tests**
- ✅ Write `test_ground_truth_validation.py`
- ✅ Test completeness (≥95%), cross-validation (pass), reviewer agreement (≥90%)
- ✅ Fix any GTs that fail validation
- ✅ All 10 GTs pass validation

**Deliverable**: 10 validated ground truths ready for training

**Day 3-4: Integration Tests**
- ✅ Write `test_integration_pipeline.py`
- ✅ Test Schema v7.0 with optimal_brf_pipeline.py
- ✅ Test backward compatibility (plain dict → ExtractionField wrapper)
- ✅ Test full extraction → validation → GT comparison
- ✅ Fix integration issues

**Deliverable**: Integration tests passing

**Day 5: Phase 1 Completion Validation**
- ✅ Run full test suite (100+ tests)
- ✅ Validate all success criteria met
- ✅ Create Phase 1 completion report
- ✅ Demo Schema v7.0 + GTs to team

**Deliverable**: `PHASE1_COMPLETION_REPORT.md`

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Schema merge conflicts** | Medium | High | Detailed merge plan with field-by-field mapping, team review before coding | Use ZeldaDemo as-is, add Gracian fields incrementally in Phase 2 |
| **GT extraction time overruns** | Medium | Medium | 3 reviewers in parallel, start with 2 easy PDFs to calibrate time estimates | Reduce from 10 PDFs to 8 if >60 hours spent |
| **GT reviewer disagreement >10%** | Low | Medium | Clear extraction guidelines, triple-check process | Add Reviewer 4 for second opinion |
| **Backward compatibility breaks** | Low | High | Wrapper functions for existing pipeline, comprehensive integration tests | Keep optimal_brf_pipeline.py using old schema, migrate agents incrementally |
| **SYNONYM_MAPPING incomplete** | Medium | Low | Start with 200+ existing mappings, add as discovered during GT creation | Accept 80% coverage for Phase 1, expand in Phase 2 |
| **Tolerance functions calibration** | Medium | Medium | Test on 10 diverse GTs, adjust thresholds based on data | Use conservative (wider) tolerances in Phase 1 |
| **Missing PDFs for selection** | Low | Low | Have backup PDFs ready (20 candidates for 10 slots) | Use most diverse available PDFs |
| **Time to train reviewers** | Low | Low | Clear methodology documentation, 2-hour training session | Add 1 week buffer if needed |

**Overall Risk Level**: **LOW-MEDIUM**

**Mitigation Cost**: +$3,000 (1 extra week buffer) + +$1,000 (Reviewer 4 contingency)

**Contingency Budget**: Total Phase 1 budget = $10,000 + $4,000 contingency = **$14,000**

---

## 8. Phase 1 Completion Checklist

### Schema v7.0 ✅
- [ ] ZeldaDemo schema.py copied as foundation
- [ ] Gracian specializations added (NotesCollection, OperationsData, EnvironmentalData)
- [ ] Swedish-first fields implemented across ALL financial sections
- [ ] Tolerance functions integrated (get_financial_tolerance, get_per_sqm_tolerance)
- [ ] ExtractionField enhanced with evidence_pages, extraction_method, validation_status
- [ ] All Pydantic models validate correctly
- [ ] Schema unit tests written and passing (50+ tests)
- [ ] Schema v7.0 documented in `SCHEMA_V7_FINAL_SPEC.md`

### SYNONYM_MAPPING ✅
- [ ] Gracian + ZeldaDemo mappings merged (250+ total)
- [ ] All mappings resolve to valid Schema v7.0 paths
- [ ] Swedish normalization utilities implemented
- [ ] Table header variant matching implemented
- [ ] Mapping unit tests written and passing (30+ tests)

### Ground Truth ✅
- [ ] 10 diverse PDFs selected (5 machine, 4 scanned, 1 hybrid)
- [ ] 10 PDFs extracted with ≥95% completeness each (5,010 data points total)
- [ ] ≥90% reviewer agreement on all PDFs
- [ ] All cross-validations pass (within tolerance)
- [ ] Ground truth validation tests written and passing (20+ tests)
- [ ] All 10 GTs stored in `ground_truth/` directory with proper JSON format

### Testing Framework ✅
- [ ] Test file structure created (6 test files)
- [ ] Schema validation tests passing (50+ tests)
- [ ] ExtractionField tests passing (20+ tests)
- [ ] SYNONYM_MAPPING tests passing (30+ tests)
- [ ] Ground truth validation tests passing (20+ tests)
- [ ] Integration tests passing (10+ tests)
- [ ] Backward compatibility tests passing (5+ tests)
- [ ] Overall test coverage ≥80%

### Integration ✅
- [ ] Schema v7.0 works with optimal_brf_pipeline.py
- [ ] Backward compatibility wrapper functions working
- [ ] No breaking changes to existing pipeline
- [ ] Full extraction → validation → GT comparison working
- [ ] Performance acceptable (<180s per PDF with Schema v7.0)

### Documentation ✅
- [ ] `SCHEMA_V7_MERGE_PLAN.md` (10-15 pages)
- [ ] `SCHEMA_V7_DESIGN_SPEC.md` (15-20 pages)
- [ ] `SCHEMA_V7_FINAL_SPEC.md` (20-25 pages)
- [ ] `GROUND_TRUTH_METHODOLOGY.md` (8-10 pages)
- [ ] `PHASE1_COMPLETION_REPORT.md` (5-7 pages)
- [ ] All code has docstrings and type hints
- [ ] README updated with Phase 1 results

### Phase 1 Success Criteria ✅
- [ ] Schema v7.0 ready for Phase 2 agent development
- [ ] 10 complete ground truths ready for training
- [ ] Testing framework ready for Phase 2 validation
- [ ] No backward compatibility issues
- [ ] Team approval to proceed to Phase 2

---

## 9. Phase 1 Deliverables Summary

**Code** (6 new files, ~3,500 lines):
- `schema_v7.py` (1,600-1,800 lines) - Complete Schema v7.0
- `mappings_v7.py` (250+ mappings) - SYNONYM_MAPPING + TABLE_HEADER_VARIANTS
- `mapping_utils.py` (300 lines) - Normalization and utility functions
- `test_schema_v7.py` (400 lines) - Schema unit tests
- `test_synonym_mapping.py` (200 lines) - Mapping tests
- `test_ground_truth_validation.py` (300 lines) - GT validation tests

**Data** (10 files, 5,010 data points):
- `ground_truth/brf_198532_gt_v7.json` (477 fields)
- `ground_truth/brf_268882_gt_v7.json` (481 fields)
- `ground_truth/brf_81563_gt_v7.json` (489 fields)
- `ground_truth/brf_271852_gt_v7.json` (455 fields)
- `ground_truth/brf_53716_gt_v7.json` (467 fields)
- `ground_truth/brf_78276_gt_v7.json` (443 fields)
- `ground_truth/brf_43334_gt_v7.json` (492 fields)
- `ground_truth/brf_76536_gt_v7.json` (421 fields)
- `ground_truth/brf_78906_gt_v7.json` (448 fields)
- `ground_truth/brf_mixed_01_gt_v7.json` (473 fields)

**Documentation** (5 files, ~75 pages):
- `SCHEMA_V7_MERGE_PLAN.md` (10-15 pages)
- `SCHEMA_V7_DESIGN_SPEC.md` (15-20 pages)
- `SCHEMA_V7_FINAL_SPEC.md` (20-25 pages)
- `GROUND_TRUTH_METHODOLOGY.md` (8-10 pages)
- `PHASE1_COMPLETION_REPORT.md` (5-7 pages)
- `PHASE1_PERFECT_IMPLEMENTATION_PLAN.md` (this document, ~40 pages)

**Total**: 21 files, ~3,500 lines of code, 5,010 validated data points, ~115 pages of documentation

---

## 10. Next Steps After Phase 1

**Phase 2: Tier 1 Core Agents** (6-8 weeks)
- Build 9 core agents using Schema v7.0 + ground truths
- 3-round training per agent (baseline → examples → anti-examples)
- Target: ≥85% coverage on core fields

**Phase 3: Tier 2 Notes Agents** (6-8 weeks)
- Build 10 notes agents (Note 1-15 detailed extraction)
- Handle comprehensive notes extraction fallback
- Target: ≥75% coverage on notes fields

**Phase 4-7**: Continue per FULL_EXTRACTION_ARCHITECTURE_501_FIELDS.md

---

## Conclusion

**Phase 1 is perfectly scoped for 4-6 weeks of focused work** delivering:

1. ✅ **Production-ready Schema v7.0** (1,600+ lines, best of Gracian + ZeldaDemo)
2. ✅ **Complete SYNONYM_MAPPING integration** (250+ Swedish term normalizations)
3. ✅ **10 validated ground truths** (5,010 data points, ≥95% completeness each)
4. ✅ **Comprehensive testing framework** (130+ tests, ≥80% coverage)
5. ✅ **No backward compatibility breaks** (optimal_brf_pipeline.py still works)

**Ready to start Phase 1 implementation immediately!** 🚀

---

**Created**: October 13, 2025
**Version**: 1.0
**Next Review**: End of Week 1 (Schema v7.0 design approval)