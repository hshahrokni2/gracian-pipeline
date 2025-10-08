# Integration Strategy: Gracian + ZeldaDemo Schema Merge
## Ultrathinking Session - Post-Compaction

**Date**: 2025-10-07
**Context**: Phase 1 complete (Pydantic schema + comparison). Now ultrathinking optimal integration path.
**Critical Constraint**: NEVER null data due to validation failures. Tolerant validation with warnings.

---

## Executive Summary

**Goal**: Merge Gracian's field breadth (150-200 fields, 8-level hierarchy) with ZeldaDemo's validation maturity (confidence tracking, multi-year, calculated metrics, 200+ synonyms).

**Expected Outcome**: 220-250 field unified schema with:
- ✅ Full confidence tracking on all fields
- ✅ Dynamic multi-year support (2-10+ years)
- ✅ Tolerant calculated metrics (preserve both extracted + calculated)
- ✅ 200+ Swedish synonym mappings
- ✅ Swedish-first semantic fields for all financial/fee metrics
- ✅ Graceful degradation (structured → semi-structured → LLM → not_found)

**Integration Approach**: Enhance Gracian Pydantic (keeps 8-level hierarchy) + bolt on ZeldaDemo features.

---

## Topic 1: Validation Tolerance Calibration

### Problem
Need to define tolerance thresholds that:
1. Catch genuine extraction errors
2. Don't reject data from poorly formatted tables
3. Work across document quality spectrum (machine-readable vs scanned)

### Proposed Thresholds (Evidence-Based)

#### Financial Amounts (SEK)
```python
TOLERANCE_FINANCIAL = {
    "small_amounts": {  # <100k SEK
        "absolute": 5_000,  # ±5k SEK
        "relative": 0.15,   # ±15%
        "logic": "Small amounts in tables often have OCR errors"
    },
    "medium_amounts": {  # 100k-10M SEK
        "absolute": 50_000,  # ±50k SEK
        "relative": 0.10,    # ±10%
        "logic": "Most common range, balance precision vs tolerance"
    },
    "large_amounts": {  # >10M SEK
        "absolute": 500_000,  # ±500k SEK
        "relative": 0.05,     # ±5%
        "logic": "Large numbers need tighter relative tolerance"
    }
}

def get_financial_tolerance(amount: float) -> float:
    """Dynamic tolerance based on magnitude."""
    if amount < 100_000:
        return max(5_000, amount * 0.15)
    elif amount < 10_000_000:
        return max(50_000, amount * 0.10)
    else:
        return max(500_000, amount * 0.05)
```

#### Percentages
```python
TOLERANCE_PERCENTAGE = {
    "solidarity": {
        "absolute": 2.0,  # ±2 percentage points
        "logic": "Soliditet calculations from balance sheet"
    },
    "occupancy": {
        "absolute": 3.0,  # ±3 percentage points
        "logic": "Apartment counts may vary (sublets, renovations)"
    },
    "yoy_change": {
        "flag_threshold": 50.0,  # Flag if >50% change, but don't reject
        "logic": "Large changes are unusual but valid (renovations, refinancing)"
    }
}
```

#### Balance Sheet Validation
```python
TOLERANCE_BALANCE = {
    "assets_liabilities_equity": {
        "relative": 0.01,  # ±1% of total assets
        "logic": "Assets = Liabilities + Equity (accounting identity)"
    },
    "revenue_expense_surplus": {
        "relative": 0.02,  # ±2% of revenue
        "logic": "Surplus = Revenue - Expenses (may have rounding)"
    }
}
```

### Implementation Strategy

**3-Tier Validation**:
1. **Pass** (green): Within tolerance → `validation_status = "valid"`
2. **Warning** (yellow): Outside tolerance but plausible → `validation_status = "warning"`, add to warnings list
3. **Error** (red): Impossible values (negative equity, >100% occupancy) → `validation_status = "error"`, add to errors list

**CRITICAL**: All 3 tiers preserve the extracted data. Never null.

```python
class CalculatedFinancialMetrics(BaseModel):
    """Financial metrics with tolerant validation."""

    # Extracted values (always preserved)
    total_debt_extracted: Optional[float] = None
    total_area_sqm_extracted: Optional[float] = None
    debt_per_sqm_extracted: Optional[float] = None

    # Calculated values (derived, never overwrites extracted)
    debt_per_sqm_calculated: Optional[float] = None

    # Validation metadata
    validation_status: str = "unknown"  # valid|warning|error|unknown
    validation_warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def calculate_and_validate_with_tolerance(self):
        """Tolerant validation: warn, don't reject."""

        # Calculate derived metrics
        if self.total_debt_extracted and self.total_area_sqm_extracted:
            calc = self.total_debt_extracted / self.total_area_sqm_extracted
            self.debt_per_sqm_calculated = round(calc, 0)

            # If extracted value also exists, cross-validate
            if self.debt_per_sqm_extracted:
                diff = abs(self.debt_per_sqm_extracted - calc)
                tolerance = get_financial_tolerance(calc)

                if diff <= tolerance:
                    self.validation_status = "valid"
                    self.confidence = 0.95
                elif diff <= tolerance * 2:  # Double tolerance = warning
                    self.validation_status = "warning"
                    self.validation_warnings.append(
                        f"debt_per_sqm: extracted={self.debt_per_sqm_extracted:.0f}, "
                        f"calculated={calc:.0f}, diff={diff:.0f} "
                        f"(tolerance={tolerance:.0f}, 2x={tolerance*2:.0f})"
                    )
                    self.confidence = 0.70
                else:  # >2x tolerance = error (but still preserve data)
                    self.validation_status = "error"
                    self.validation_errors.append(
                        f"debt_per_sqm: Large discrepancy - extracted={self.debt_per_sqm_extracted:.0f}, "
                        f"calculated={calc:.0f}, diff={diff:.0f} (>2x tolerance)"
                    )
                    self.confidence = 0.40

        return self
```

### Testing Plan

**Dataset**: Analyze 50 documents across quality spectrum:
- 15 machine-readable (pristine)
- 20 scanned + OCR (medium quality)
- 15 scanned + poor OCR (low quality)

**Metrics**:
- Validation pass rate (target: >80%)
- False positive rate (flagged but actually correct, target: <5%)
- False negative rate (missed errors, target: <2%)
- Data loss rate (nulled fields, target: 0%)

**Calibration**: Adjust thresholds based on results.

---

## Topic 2: Confidence Scoring Strategy

### Problem
Need consistent confidence scoring across extraction methods with different reliability profiles.

### Proposed Confidence Framework

#### Base Confidence by Extraction Method

```python
CONFIDENCE_BY_METHOD = {
    "structured_table": {
        "base": 0.90,
        "conditions": [
            ("header_match_exact", +0.05),
            ("numeric_validation_pass", +0.03),
            ("cross_field_validation_pass", +0.02),
        ],
        "penalties": [
            ("ocr_quality_low", -0.15),
            ("table_malformed", -0.10),
            ("missing_headers", -0.10),
        ]
    },
    "semi_structured_regex": {
        "base": 0.70,
        "conditions": [
            ("pattern_strong_match", +0.10),  # e.g., "Org.nr: 556789-1234"
            ("context_present", +0.05),       # Surrounding text confirms
        ],
        "penalties": [
            ("multiple_candidates", -0.15),   # Found 3 org numbers
            ("weak_pattern", -0.10),          # Loose regex match
        ]
    },
    "vision_llm_extraction": {
        "base": 0.60,  # Varies by model
        "model_adjustments": {
            "gpt-4-vision": +0.15,
            "gemini-2.5-pro": +0.10,
            "qwen-2.5-vl": +0.05,
            "grok-vision": 0.00,
        },
        "conditions": [
            ("multiple_evidence_pages", +0.10),  # Found on 3+ pages
            ("llm_expressed_confidence", +0.05), # "very confident"
        ],
        "penalties": [
            ("scanned_document", -0.10),
            ("conflicting_values", -0.20),
        ]
    },
    "calculated_from_other_fields": {
        "base": 0.85,
        "conditions": [
            ("both_inputs_high_confidence", +0.10),  # Both >0.9
            ("validation_pass", +0.05),
        ],
        "penalties": [
            ("input_low_confidence", -0.20),  # Input <0.5
            ("validation_warning", -0.10),
        ]
    },
    "not_found": {
        "base": 0.0,
        "logic": "Field not extracted, but we tried (evidence_pages tracked)"
    }
}
```

#### Confidence Aggregation for Multi-Source Fields

```python
def aggregate_confidence(extractions: List[Dict]) -> float:
    """
    When multiple extraction methods return same field.

    Strategy:
    1. If all agree → use highest confidence
    2. If disagree → use weighted vote, penalty for disagreement
    """

    if len(extractions) == 1:
        return extractions[0]["confidence"]

    # Check agreement
    values = [e["value"] for e in extractions]
    confidences = [e["confidence"] for e in extractions]

    if all_values_agree(values):
        # Agreement → boost confidence
        max_conf = max(confidences)
        num_sources = len(extractions)
        boost = min(0.10, num_sources * 0.03)  # +3% per source, max +10%
        return min(1.0, max_conf + boost)
    else:
        # Disagreement → weighted vote
        weighted_sum = sum(c * get_value_weight(v) for v, c in zip(values, confidences))
        total_weight = sum(confidences)
        base_conf = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Penalty for disagreement
        penalty = 0.15
        return max(0.0, base_conf - penalty)
```

#### Field-Specific Confidence Adjustments

```python
FIELD_CONFIDENCE_ADJUSTMENTS = {
    "organization_number": {
        "checksum_validation": +0.10,  # Swedish org.nr has checksum
        "format_validation": +0.05,    # XXXXXX-XXXX format
    },
    "board_members": {
        "structured_list": +0.10,      # Found in table/list
        "name_format_valid": +0.05,    # Swedish name patterns
        "count_reasonable": +0.03,     # 3-9 members typical
    },
    "solidarity_percent": {
        "balance_sheet_match": +0.15,  # Calculated from Assets/Equity matches
        "in_reasonable_range": +0.05,  # 10-90% typical
    },
    "arsavgift_per_sqm": {
        "unit_verified": +0.10,        # Confirmed "kr/m²/år"
        "in_reasonable_range": +0.05,  # 200-2000 kr/m²/år typical
    }
}
```

### Implementation: ExtractionField Base Class

```python
class ExtractionField(BaseModel):
    """Base for all extracted fields with confidence tracking."""

    value: Optional[Any] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    # Provenance
    source: Optional[str] = None  # "structured_table|regex|vision_llm|calculated"
    evidence_pages: List[int] = Field(default_factory=list)

    # Quality metadata
    extraction_method: Optional[str] = None
    model_used: Optional[str] = None  # For LLM extractions
    validation_status: Optional[str] = None  # "valid|warning|error|unknown"

    # Multi-source tracking
    alternative_values: List[Dict] = Field(default_factory=list)  # Other extractions

    def add_alternative(self, value: Any, confidence: float, source: str):
        """Track alternative extractions for the same field."""
        self.alternative_values.append({
            "value": value,
            "confidence": confidence,
            "source": source
        })

    def resolve_best_value(self):
        """
        If multiple extractions exist, pick best.
        Strategy: Highest confidence if agree, weighted vote if disagree.
        """
        if not self.alternative_values:
            return

        all_extractions = [
            {"value": self.value, "confidence": self.confidence, "source": self.source}
        ] + self.alternative_values

        # Apply aggregation logic
        best = max(all_extractions, key=lambda x: x["confidence"])
        self.value = best["value"]
        self.confidence = aggregate_confidence(all_extractions)
        self.source = "multi_source_aggregated"

# Specialized field types
class StringField(ExtractionField):
    value: Optional[str] = None

class NumberField(ExtractionField):
    value: Optional[float] = None

class ListField(ExtractionField):
    value: List[Any] = Field(default_factory=list)
```

### Testing Plan

**Dataset**: 30 documents, extract same field with multiple methods:
1. Chairman name: vision LLM + regex + structured table
2. Total debt: financial table + calculated from balance sheet + LLM
3. Solidarity %: calculated + extracted from KPIs table

**Metrics**:
- Confidence calibration: For extractions marked 0.9, actual accuracy should be ~90%
- Agreement rate: When multiple methods agree, confidence should be >0.9
- Disagreement handling: When methods disagree, does weighted vote pick correct value?

---

## Topic 3: Multi-Year Table Parsing

### Problem
Swedish BRF reports show 2-10+ years of financial data in various table orientations and formats.

### Table Orientation Detection

```python
class MultiYearTableOrientation(str, Enum):
    YEARS_AS_COLUMNS = "years_columns"  # Most common
    YEARS_AS_ROWS = "years_rows"
    MIXED = "mixed"  # Some metrics in columns, others in rows
    UNKNOWN = "unknown"

def detect_table_orientation(table_data: Dict) -> MultiYearTableOrientation:
    """
    Detect if years are columns or rows.

    Heuristics:
    1. Check header row for year patterns (2021, 2022, 2023)
    2. Check first column for year patterns
    3. Count year occurrences in rows vs columns
    """

    header_has_years = any(is_year(cell) for cell in table_data.get("header", []))
    first_col_has_years = any(is_year(row[0]) for row in table_data.get("rows", []))

    if header_has_years and not first_col_has_years:
        return MultiYearTableOrientation.YEARS_AS_COLUMNS
    elif first_col_has_years and not header_has_years:
        return MultiYearTableOrientation.YEARS_AS_ROWS
    elif header_has_years and first_col_has_years:
        return MultiYearTableOrientation.MIXED
    else:
        return MultiYearTableOrientation.UNKNOWN

def is_year(value: Any) -> bool:
    """Check if value looks like a year (1900-2100)."""
    if isinstance(value, int):
        return 1900 <= value <= 2100
    if isinstance(value, str):
        # Handle "2023/2024", "2023-24", "2023"
        match = re.search(r'\b(19|20)\d{2}\b', value)
        return match is not None
    return False
```

### Dynamic Multi-Year Schema

```python
class YearlyFinancialData(BaseModel):
    """Single year of financial data."""
    year: int = Field(..., ge=1900, le=2100)

    # Core metrics (with confidence tracking)
    net_revenue_tkr: Optional[NumberField] = None
    operating_expenses_tkr: Optional[NumberField] = None
    operating_surplus_tkr: Optional[NumberField] = None
    total_assets_tkr: Optional[NumberField] = None
    total_liabilities_tkr: Optional[NumberField] = None
    equity_tkr: Optional[NumberField] = None
    solidarity_percent: Optional[NumberField] = None

    # Metadata
    is_complete: bool = Field(False)
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0)
    source_page: Optional[int] = None

class DynamicMultiYearOverview(BaseModel):
    """
    Flexible multi-year data container.
    Handles 2-10+ years without hardcoded columns.
    """

    years: List[YearlyFinancialData] = Field(default_factory=list)
    years_covered: List[int] = Field(default_factory=list)  # [2021, 2022, 2023, 2024]
    num_years: int = Field(0)

    # Metadata
    table_orientation: MultiYearTableOrientation = MultiYearTableOrientation.UNKNOWN
    extraction_method: str = "unknown"
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def compute_metadata(self):
        """Auto-compute years_covered and num_years."""
        self.years_covered = sorted([y.year for y in self.years])
        self.num_years = len(self.years_covered)
        return self

    def get_year(self, year: int) -> Optional[YearlyFinancialData]:
        """Retrieve data for specific year."""
        for y in self.years:
            if y.year == year:
                return y
        return None

    def get_metric_timeseries(self, metric: str) -> Dict[int, Optional[float]]:
        """
        Extract time series for a metric.
        Returns: {2021: 1234.5, 2022: 1456.7, ...}
        """
        result = {}
        for y in self.years:
            field = getattr(y, metric, None)
            if field and isinstance(field, NumberField):
                result[y.year] = field.value
            else:
                result[y.year] = None
        return result
```

### Multi-Year Table Extraction Pipeline

```python
def extract_multi_year_table(
    table_data: Dict,
    expected_metrics: List[str]
) -> DynamicMultiYearOverview:
    """
    Extract multi-year financial data from table.

    Steps:
    1. Detect orientation (years as columns or rows)
    2. Identify year values
    3. Map metric names to canonical fields (using SYNONYM_MAPPING)
    4. Extract values with confidence
    5. Validate cross-year consistency
    """

    orientation = detect_table_orientation(table_data)

    if orientation == MultiYearTableOrientation.YEARS_AS_COLUMNS:
        return extract_years_as_columns(table_data, expected_metrics)
    elif orientation == MultiYearTableOrientation.YEARS_AS_ROWS:
        return extract_years_as_rows(table_data, expected_metrics)
    else:
        # Fallback: Try both, use higher confidence result
        result_cols = extract_years_as_columns(table_data, expected_metrics)
        result_rows = extract_years_as_rows(table_data, expected_metrics)
        return result_cols if result_cols.confidence > result_rows.confidence else result_rows

def extract_years_as_columns(table_data: Dict, expected_metrics: List[str]) -> DynamicMultiYearOverview:
    """
    Extract when years are column headers.

    Example:
    | Metric                | 2022    | 2023    | 2024    |
    |-----------------------|---------|---------|---------|
    | Nettoomsättning (tkr) | 12,345  | 13,456  | 14,567  |
    | Driftskostnader (tkr) | 10,123  | 11,234  | 12,345  |
    """

    overview = DynamicMultiYearOverview(
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method="structured_table"
    )

    # Parse header to find year columns
    header = table_data.get("header", [])
    year_columns = {}  # {col_idx: year}
    for idx, cell in enumerate(header):
        if is_year(cell):
            year_columns[idx] = extract_year_from_cell(cell)

    if not year_columns:
        overview.confidence = 0.0
        return overview

    # Initialize YearlyFinancialData for each year
    for year in year_columns.values():
        overview.years.append(YearlyFinancialData(year=year))

    # Parse rows to extract metrics
    for row in table_data.get("rows", []):
        metric_name_raw = row[0] if row else ""
        metric_canonical = map_to_canonical_field(metric_name_raw)

        if metric_canonical not in expected_metrics:
            continue

        # Extract values for each year
        for col_idx, year in year_columns.items():
            if col_idx < len(row):
                value_raw = row[col_idx]
                value_parsed = parse_swedish_number(value_raw)

                # Find corresponding YearlyFinancialData
                year_data = overview.get_year(year)
                if year_data and value_parsed is not None:
                    # Set field with confidence
                    field = NumberField(
                        value=value_parsed,
                        confidence=0.90,  # Structured table base
                        source="structured_table",
                        evidence_pages=[table_data.get("page", 0)]
                    )
                    setattr(year_data, metric_canonical, field)

    # Compute overall confidence
    overview.confidence = compute_multi_year_confidence(overview)
    return overview

def extract_years_as_rows(table_data: Dict, expected_metrics: List[str]) -> DynamicMultiYearOverview:
    """
    Extract when years are in first column.

    Example:
    | År   | Nettoomsättning | Driftskostnader | Resultat |
    |------|-----------------|-----------------|----------|
    | 2022 | 12,345          | 10,123          | 2,222    |
    | 2023 | 13,456          | 11,234          | 2,222    |
    | 2024 | 14,567          | 12,345          | 2,222    |
    """

    overview = DynamicMultiYearOverview(
        table_orientation=MultiYearTableOrientation.YEARS_AS_ROWS,
        extraction_method="structured_table"
    )

    # Parse header to find metric columns
    header = table_data.get("header", [])
    metric_columns = {}  # {col_idx: canonical_field}
    for idx, cell in enumerate(header[1:], start=1):  # Skip first column (years)
        canonical = map_to_canonical_field(cell)
        if canonical in expected_metrics:
            metric_columns[idx] = canonical

    if not metric_columns:
        overview.confidence = 0.0
        return overview

    # Parse rows to extract years + values
    for row in table_data.get("rows", []):
        if not row or not is_year(row[0]):
            continue

        year = extract_year_from_cell(row[0])
        year_data = YearlyFinancialData(year=year)

        # Extract metric values
        for col_idx, canonical_field in metric_columns.items():
            if col_idx < len(row):
                value_raw = row[col_idx]
                value_parsed = parse_swedish_number(value_raw)

                if value_parsed is not None:
                    field = NumberField(
                        value=value_parsed,
                        confidence=0.90,
                        source="structured_table",
                        evidence_pages=[table_data.get("page", 0)]
                    )
                    setattr(year_data, canonical_field, field)

        overview.years.append(year_data)

    overview.confidence = compute_multi_year_confidence(overview)
    return overview

def compute_multi_year_confidence(overview: DynamicMultiYearOverview) -> float:
    """
    Compute overall confidence for multi-year extraction.

    Factors:
    - Number of years extracted (2-3 years = good, 5+ years = excellent)
    - Completeness of each year
    - Cross-year consistency (no wild swings)
    """

    base = 0.85  # Structured table base

    # Bonus for more years
    if overview.num_years >= 5:
        base += 0.10
    elif overview.num_years >= 3:
        base += 0.05

    # Check completeness
    completeness_scores = []
    for year_data in overview.years:
        fields_filled = sum(1 for f in [
            year_data.net_revenue_tkr,
            year_data.operating_expenses_tkr,
            year_data.total_assets_tkr,
            year_data.total_liabilities_tkr,
            year_data.equity_tkr
        ] if f is not None and f.value is not None)
        completeness_scores.append(fields_filled / 5.0)

    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
    base *= avg_completeness

    # Penalty for inconsistent data (e.g., revenue doubles year-over-year)
    inconsistency_penalty = check_cross_year_consistency(overview)
    base -= inconsistency_penalty

    return max(0.0, min(1.0, base))

def check_cross_year_consistency(overview: DynamicMultiYearOverview) -> float:
    """
    Check if year-over-year changes are reasonable.
    Returns penalty (0.0 = consistent, 0.2 = very inconsistent).
    """

    penalty = 0.0

    # Check net revenue trend
    revenue_ts = overview.get_metric_timeseries("net_revenue_tkr")
    sorted_years = sorted(revenue_ts.keys())

    for i in range(len(sorted_years) - 1):
        y1, y2 = sorted_years[i], sorted_years[i + 1]
        v1, v2 = revenue_ts[y1], revenue_ts[y2]

        if v1 and v2 and v1 > 0:
            yoy_change = abs(v2 - v1) / v1
            if yoy_change > 0.50:  # >50% change
                penalty += 0.05  # Flag but don't heavily penalize
            if yoy_change > 1.0:  # >100% change (doubles)
                penalty += 0.10

    return min(0.2, penalty)
```

### Missing Year Handling

```python
def handle_missing_years(overview: DynamicMultiYearOverview) -> DynamicMultiYearOverview:
    """
    If some years are missing in sequence, try to fill gaps.

    Example: Have 2021, 2023, 2024 → missing 2022
    Strategy: Mark as missing but keep placeholder for consistency
    """

    if overview.num_years < 2:
        return overview

    min_year = min(overview.years_covered)
    max_year = max(overview.years_covered)

    for year in range(min_year, max_year + 1):
        if year not in overview.years_covered:
            # Add placeholder
            placeholder = YearlyFinancialData(
                year=year,
                is_complete=False,
                extraction_confidence=0.0
            )
            overview.years.append(placeholder)

    # Re-sort and recompute
    overview.years.sort(key=lambda y: y.year)
    overview.compute_metadata()

    return overview
```

### Testing Plan

**Dataset**: 20 documents with multi-year tables:
- 10 with years as columns
- 5 with years as rows
- 5 with mixed orientation

**Metrics**:
- Orientation detection accuracy (target: >95%)
- Year extraction accuracy (target: 100% - critical)
- Metric extraction completeness (target: >90%)
- Cross-year validation pass rate (target: >85%)

---

## Topic 4: Integration Sequencing

### Problem
Need to sequence integration work to minimize risk and maximize learning.

### Proposed Sequencing (3 Weeks)

#### **Week 1: Foundation - ExtractionField + DynamicMultiYear**

**Why First**: These are the most foundational changes. All other features depend on them.

**Tasks**:
1. **Day 1-2**: Create `gracian_pipeline/models/base_fields.py`
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional, Any, List, Dict

   class ExtractionField(BaseModel):
       """Base class for all extracted fields."""
       value: Optional[Any] = None
       confidence: float = Field(0.0, ge=0.0, le=1.0)
       source: Optional[str] = None
       evidence_pages: List[int] = Field(default_factory=list)
       extraction_method: Optional[str] = None
       validation_status: Optional[str] = None
       alternative_values: List[Dict] = Field(default_factory=list)

   class StringField(ExtractionField):
       value: Optional[str] = None

   class NumberField(ExtractionField):
       value: Optional[float] = None

   class ListField(ExtractionField):
       value: List[Any] = Field(default_factory=list)
   ```

2. **Day 3-4**: Migrate `brf_schema.py` to use ExtractionField
   - Replace all `Optional[str]` → `Optional[StringField]`
   - Replace all `Optional[float]` → `Optional[NumberField]`
   - Replace all `List[...]` → `Optional[ListField]`
   - Update 150+ field definitions

3. **Day 4-5**: Add DynamicMultiYearOverview
   - Create `YearlyFinancialData` model
   - Create `DynamicMultiYearOverview` model
   - Add to `BRFAnnualReport.financial.multi_year_overview`

4. **Day 5**: Test on 5 documents
   - Verify schema still validates
   - Check confidence tracking works
   - Validate multi-year extraction

**Success Criteria**:
- All tests pass
- No null data introduced
- Confidence scores populated (even if all 0.5 initially)

---

#### **Week 2: Validation + Synonyms**

**Why Second**: Foundation in place, now add intelligence.

**Tasks**:
1. **Day 1-2**: Add CalculatedFinancialMetrics with tolerant validation
   ```python
   class CalculatedFinancialMetrics(BaseModel):
       # All metrics with _extracted and _calculated variants
       total_debt_extracted: Optional[NumberField] = None
       total_debt_calculated: Optional[NumberField] = None

       validation_warnings: List[str] = Field(default_factory=list)
       validation_errors: List[str] = Field(default_factory=list)
       validation_status: str = "unknown"

       @model_validator(mode='after')
       def calculate_and_validate(self):
           # Implement tolerant validation
           # Test with 10 documents
           return self
   ```

2. **Day 2-3**: Integrate synonym mapping
   - Copy `ZeldaDemo/mappings.py` SYNONYM_MAPPING to `gracian_pipeline/core/synonyms.py`
   - Update extraction pipeline to use synonym mapping
   - Test on 10 documents with varied terminology

3. **Day 4**: Apply Swedish-first semantic fields
   - Expand beyond fees_agent to all financial metrics
   - Add `arsavgift_per_sqm`, `arsavgift_total`, etc.
   - Add metadata fields: `_terminology_found`, `_unit_verified`

4. **Day 5**: Test validation thresholds
   - Run on 20 documents
   - Measure: validation pass rate, false positive rate, data loss rate
   - Calibrate thresholds if needed

**Success Criteria**:
- Validation pass rate >80%
- Data loss rate = 0%
- Synonym mapping improves extraction coverage by >15%

---

#### **Week 3: Testing + Documentation**

**Why Last**: Validate entire integration works end-to-end.

**Tasks**:
1. **Day 1-2**: Comprehensive testing
   - Test on all 43 PDFs (15 Hjorthagen + 28 SRS)
   - Measure: coverage, confidence, validation rates, data loss
   - Compare before/after integration

2. **Day 3**: Ground truth validation
   - Create ground truth for 2-3 documents (full manual extraction)
   - Compare automated extraction to ground truth
   - Target: 95% accuracy

3. **Day 4**: Documentation
   - Write migration guide: old dict schema → new Pydantic
   - Update CLAUDE.md with new schema structure
   - Document confidence scoring and validation logic

4. **Day 5**: Final review
   - Code review of all changes
   - Security review (API keys, data handling)
   - Update PROJECT_INDEX.json

**Success Criteria**:
- Overall coverage ≥95%
- Confidence calibration accurate (0.9 confidence → ~90% accuracy)
- Validation pass rate >85%
- Data loss rate = 0%
- Documentation complete

---

### Risk Mitigation

**Risk 1**: Schema migration breaks existing extraction
- **Mitigation**: Keep old schema as fallback, run both in parallel for Week 1
- **Rollback**: Revert to commit before Week 1 Day 3

**Risk 2**: Validation too strict, causes data loss
- **Mitigation**: Monitor data loss rate daily, adjust thresholds immediately if >0%
- **Rollback**: Disable validation, investigate, fix tolerances

**Risk 3**: Integration takes longer than 3 weeks
- **Mitigation**: Prioritize Week 1 (foundation), Week 2 and 3 can be extended
- **Contingency**: Ship Week 1 + Week 2 Day 1-2 as MVP, defer rest

---

## Topic 5: Swedish-First Expansion

### Problem
Current Gracian schema uses English field names for Swedish concepts, causing semantic mismatch (e.g., "monthly_fee" when documents show "årsavgift" = annual fee).

### Proposed Expansion Strategy

#### **Phase 1: Financial Metrics** (Priority: HIGH)

```python
class FinancialData(BaseModel):
    """Financial data with Swedish-first semantic fields."""

    # SWEDISH-FIRST (primary)
    nettoomsattning_tkr: Optional[NumberField] = None  # Net revenue (tkr)
    driftskostnader_tkr: Optional[NumberField] = None  # Operating expenses
    driftsoverskott_tkr: Optional[NumberField] = None  # Operating surplus
    arsresultat_tkr: Optional[NumberField] = None      # Annual result

    # Balance sheet
    tillgangar_tkr: Optional[NumberField] = None       # Assets
    skulder_tkr: Optional[NumberField] = None          # Liabilities
    eget_kapital_tkr: Optional[NumberField] = None     # Equity

    # Key ratios
    soliditet_procent: Optional[NumberField] = None    # Solidarity %

    # ENGLISH (secondary, for backwards compatibility)
    net_revenue_tkr: Optional[NumberField] = None      # Alias for nettoomsattning_tkr
    total_assets_tkr: Optional[NumberField] = None     # Alias for tillgangar_tkr

    # Metadata for validation
    _financial_terminology_found: Optional[str] = None  # "nettoomsättning|net revenue"
    _currency_verified: Optional[str] = None            # "SEK|tkr|MSEK"

    @model_validator(mode='after')
    def sync_swedish_english_aliases(self):
        """Keep Swedish and English fields in sync."""
        if self.nettoomsattning_tkr and not self.net_revenue_tkr:
            self.net_revenue_tkr = self.nettoomsattning_tkr
        elif self.net_revenue_tkr and not self.nettoomsattning_tkr:
            self.nettoomsattning_tkr = self.net_revenue_tkr

        # Same for all other aliases
        return self
```

#### **Phase 2: Fees & Charges** (Priority: HIGH)

```python
class FeeStructure(BaseModel):
    """Fee structure with Swedish-first semantic fields."""

    # SWEDISH-FIRST (primary)
    arsavgift_per_sqm_total: Optional[NumberField] = None      # kr/m²/år (MOST COMMON)
    arsavgift_per_apartment_avg: Optional[NumberField] = None  # kr/apt/år

    manadsavgift_per_sqm: Optional[NumberField] = None         # kr/m²/mån (less common)
    manadsavgift_per_apartment_avg: Optional[NumberField] = None

    # Included in fee
    inkluderar_vatten: Optional[bool] = None                   # Water included?
    inkluderar_varme: Optional[bool] = None                    # Heating included?
    inkluderar_el: Optional[bool] = None                       # Electricity included?
    inkluderar_bredband: Optional[bool] = None                 # Internet included?

    # Special fees
    varmeavgift_separat_per_sqm: Optional[NumberField] = None  # Separate heating fee
    tilläggsavgift_per_sqm: Optional[NumberField] = None       # Additional fee

    # ENGLISH (secondary)
    annual_fee_per_sqm: Optional[NumberField] = None           # Alias for arsavgift_per_sqm_total
    monthly_fee_per_sqm: Optional[NumberField] = None          # Alias for manadsavgift_per_sqm

    # Metadata
    _fee_terminology_found: Optional[str] = None               # "årsavgift|årsavgift/m²"
    _fee_unit_verified: Optional[str] = None                   # "kr/m²/år|kr/m²/mån"
    _fee_period_verified: Optional[str] = None                 # "år|månad"

    @model_validator(mode='after')
    def validate_fee_consistency(self):
        """
        Validate fee calculations and terminology.
        CRITICAL: Tolerant validation, never null.
        """

        # If both årsavgift and månadsavgift found, cross-validate
        if self.arsavgift_per_sqm_total and self.manadsavgift_per_sqm:
            expected_annual = self.manadsavgift_per_sqm.value * 12
            if self.arsavgift_per_sqm_total.value:
                diff = abs(self.arsavgift_per_sqm_total.value - expected_annual)
                tolerance = get_financial_tolerance(expected_annual)

                if diff > tolerance:
                    # WARNING, not error
                    self.arsavgift_per_sqm_total.validation_status = "warning"
                    if not hasattr(self, 'validation_warnings'):
                        self.validation_warnings = []
                    self.validation_warnings.append(
                        f"Fee mismatch: årsavgift={self.arsavgift_per_sqm_total.value:.0f}, "
                        f"månadsavgift*12={expected_annual:.0f}, diff={diff:.0f}"
                    )

        return self
```

#### **Phase 3: Property Details** (Priority: MEDIUM)

```python
class PropertyDetails(BaseModel):
    """Property details with Swedish-first semantic fields."""

    # SWEDISH-FIRST
    fastighetsbeteckning: Optional[StringField] = None         # Property designation
    adress_gata: Optional[StringField] = None                  # Street address
    postnummer: Optional[StringField] = None                   # Postal code
    postort: Optional[StringField] = None                      # City
    kommun: Optional[StringField] = None                       # Municipality

    byggnadsår: Optional[NumberField] = None                   # Construction year
    antal_byggnader: Optional[NumberField] = None              # Number of buildings
    antal_lagenheter: Optional[NumberField] = None             # Number of apartments
    total_yta_boarea_sqm: Optional[NumberField] = None         # Total area (BRA)
    total_yta_loa_sqm: Optional[NumberField] = None            # Total area (LOA)

    # ENGLISH (secondary)
    property_designation: Optional[StringField] = None         # Alias
    construction_year: Optional[NumberField] = None            # Alias
    num_apartments: Optional[NumberField] = None               # Alias
```

#### **Phase 4: Governance** (Priority: LOW)

```python
class GovernanceStructure(BaseModel):
    """Governance with Swedish-first semantic fields."""

    # SWEDISH-FIRST
    ordförande_namn: Optional[StringField] = None              # Chairman name
    styrelseledamöter: Optional[ListField] = None              # Board members
    revisor_namn: Optional[StringField] = None                 # Auditor name
    revisor_företag: Optional[StringField] = None              # Audit firm

    # ENGLISH (secondary)
    chairman_name: Optional[StringField] = None                # Alias
    board_members: Optional[ListField] = None                  # Alias
```

### Synonym Mapping Integration

```python
SWEDISH_FIRST_SYNONYMS = {
    # Financial metrics
    "nettoomsättning": "nettoomsattning_tkr",
    "rörelseintäkter": "nettoomsattning_tkr",
    "driftskostnader": "driftskostnader_tkr",
    "rörelsekostnader": "driftskostnader_tkr",
    "driftsöverskott": "driftsoverskott_tkr",
    "rörelseresultat": "driftsoverskott_tkr",
    "årets resultat": "arsresultat_tkr",

    # Balance sheet
    "tillgångar": "tillgangar_tkr",
    "summa tillgångar": "tillgangar_tkr",
    "skulder": "skulder_tkr",
    "summa skulder": "skulder_tkr",
    "eget kapital": "eget_kapital_tkr",
    "soliditet": "soliditet_procent",

    # Fees
    "årsavgift": "arsavgift_per_sqm_total",
    "årsavgift/m²": "arsavgift_per_sqm_total",
    "månadsavgift": "manadsavgift_per_sqm",
    "månadsavgift/m²": "manadsavgift_per_sqm",

    # Property
    "fastighetsbeteckning": "fastighetsbeteckning",
    "byggnadsår": "byggnadsår",
    "antal lägenheter": "antal_lagenheter",
    "boarea": "total_yta_boarea_sqm",

    # Governance
    "ordförande": "ordförande_namn",
    "styrelseledamöter": "styrelseledamöter",
    "styrelse": "styrelseledamöter",
    "revisor": "revisor_namn",
}
```

### Implementation Priority

1. **Week 2 Day 4**: Add Swedish-first to financial metrics (nettoomsattning, soliditet, etc.)
2. **Week 2 Day 4**: Add Swedish-first to fees (årsavgift, månadsavgift)
3. **Week 3**: Add Swedish-first to property details (optional, time permitting)
4. **Post-Week 3**: Add Swedish-first to governance (lowest priority, English names work fine)

### Testing Plan

**Dataset**: 20 documents, half with Swedish terminology, half with mixed Swedish/English

**Metrics**:
- Terminology match rate: How often does extraction find Swedish vs English terms?
- Extraction improvement: Does Swedish-first improve coverage?
- Validation effectiveness: Do metadata fields (_terminology_found) help debugging?

---

## Topic 6: Error Recovery Patterns

### Problem
Extraction can fail at multiple stages. Need graceful degradation strategy that never gives up without trying all methods.

### Proposed Graceful Degradation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Extraction Waterfall                    │
└─────────────────────────────────────────────────────────────┘

Level 1: STRUCTURED TABLE EXTRACTION (Highest Confidence: 0.85-0.95)
   ↓ (If fails or low confidence <0.7)

Level 2: SEMI-STRUCTURED REGEX (Medium Confidence: 0.65-0.80)
   ↓ (If fails or low confidence <0.6)

Level 3: VISION LLM (SINGLE PAGE) (Medium Confidence: 0.60-0.85)
   ↓ (If fails or low confidence <0.5)

Level 4: VISION LLM (MULTI PAGE) (Lower Confidence: 0.50-0.75)
   ↓ (If fails)

Level 5: MARK AS NOT_FOUND (Confidence: 0.0, with evidence_pages)
   ↓

NEVER: NULL WITHOUT EVIDENCE
```

### Implementation

```python
class ExtractionAttempt(BaseModel):
    """Track a single extraction attempt."""
    method: str  # "structured|regex|vision_single|vision_multi"
    success: bool
    confidence: float
    value: Optional[Any]
    error_message: Optional[str]
    execution_time_ms: float

class FieldExtractionHistory(BaseModel):
    """Complete history of extraction attempts for a field."""
    field_name: str
    attempts: List[ExtractionAttempt] = Field(default_factory=list)
    final_value: Optional[Any] = None
    final_confidence: float = 0.0
    final_method: str = "not_found"
    evidence_pages: List[int] = Field(default_factory=list)

def extract_field_with_graceful_degradation(
    pdf_path: str,
    field_name: str,
    agent_id: str,
    pages: List[int]
) -> FieldExtractionHistory:
    """
    Extract field using graceful degradation.
    Try all methods, never give up without trying everything.
    """

    history = FieldExtractionHistory(field_name=field_name)

    # Level 1: Structured table extraction
    attempt1 = try_structured_extraction(pdf_path, field_name, pages)
    history.attempts.append(attempt1)

    if attempt1.success and attempt1.confidence >= 0.70:
        history.final_value = attempt1.value
        history.final_confidence = attempt1.confidence
        history.final_method = "structured_table"
        history.evidence_pages = pages
        return history

    # Level 2: Semi-structured regex
    attempt2 = try_regex_extraction(pdf_path, field_name, pages)
    history.attempts.append(attempt2)

    if attempt2.success and attempt2.confidence >= 0.60:
        # If both Level 1 and Level 2 succeeded, aggregate
        if attempt1.success:
            history.final_value = aggregate_values([attempt1, attempt2])
            history.final_confidence = max(attempt1.confidence, attempt2.confidence)
            history.final_method = "multi_source"
        else:
            history.final_value = attempt2.value
            history.final_confidence = attempt2.confidence
            history.final_method = "semi_structured_regex"
        history.evidence_pages = pages
        return history

    # Level 3: Vision LLM (single page)
    # Try most likely page first (from sectionizer)
    most_likely_page = get_most_likely_page(agent_id, pages)
    attempt3 = try_vision_llm_single_page(pdf_path, field_name, most_likely_page)
    history.attempts.append(attempt3)

    if attempt3.success and attempt3.confidence >= 0.50:
        history.final_value = attempt3.value
        history.final_confidence = attempt3.confidence
        history.final_method = "vision_llm_single"
        history.evidence_pages = [most_likely_page]
        return history

    # Level 4: Vision LLM (multi page)
    # Last resort: pass all pages to vision LLM
    attempt4 = try_vision_llm_multi_page(pdf_path, field_name, pages)
    history.attempts.append(attempt4)

    if attempt4.success:
        history.final_value = attempt4.value
        history.final_confidence = attempt4.confidence
        history.final_method = "vision_llm_multi"
        history.evidence_pages = pages
        return history

    # Level 5: Mark as not_found (but with evidence of trying)
    history.final_value = None
    history.final_confidence = 0.0
    history.final_method = "not_found"
    history.evidence_pages = pages  # We tried these pages

    return history

def try_structured_extraction(pdf_path: str, field_name: str, pages: List[int]) -> ExtractionAttempt:
    """Level 1: Structured table extraction."""
    start_time = time.time()

    try:
        # Extract tables from pages
        tables = extract_tables_from_pages(pdf_path, pages)

        # Search for field in tables using synonym mapping
        for table in tables:
            value = search_table_for_field(table, field_name, SWEDISH_FIRST_SYNONYMS)
            if value:
                confidence = 0.90  # Base confidence for structured
                # Boost confidence if validation passes
                if validate_value(field_name, value):
                    confidence += 0.05

                return ExtractionAttempt(
                    method="structured_table",
                    success=True,
                    confidence=confidence,
                    value=value,
                    error_message=None,
                    execution_time_ms=(time.time() - start_time) * 1000
                )

        # No table found or field not in tables
        return ExtractionAttempt(
            method="structured_table",
            success=False,
            confidence=0.0,
            value=None,
            error_message="Field not found in structured tables",
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return ExtractionAttempt(
            method="structured_table",
            success=False,
            confidence=0.0,
            value=None,
            error_message=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )

def try_regex_extraction(pdf_path: str, field_name: str, pages: List[int]) -> ExtractionAttempt:
    """Level 2: Semi-structured regex extraction."""
    start_time = time.time()

    try:
        # Extract text from pages
        text = extract_text_from_pages(pdf_path, pages)

        # Get regex pattern for field
        pattern = get_regex_pattern_for_field(field_name)
        if not pattern:
            return ExtractionAttempt(
                method="semi_structured_regex",
                success=False,
                confidence=0.0,
                value=None,
                error_message="No regex pattern defined for field",
                execution_time_ms=(time.time() - start_time) * 1000
            )

        # Search text using regex
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = parse_match(match, field_name)
            confidence = 0.70  # Base for regex

            # Check if strong match (exact format)
            if is_strong_pattern_match(match, field_name):
                confidence += 0.10

            return ExtractionAttempt(
                method="semi_structured_regex",
                success=True,
                confidence=confidence,
                value=value,
                error_message=None,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        return ExtractionAttempt(
            method="semi_structured_regex",
            success=False,
            confidence=0.0,
            value=None,
            error_message="Regex pattern did not match",
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return ExtractionAttempt(
            method="semi_structured_regex",
            success=False,
            confidence=0.0,
            value=None,
            error_message=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )

def try_vision_llm_single_page(pdf_path: str, field_name: str, page: int) -> ExtractionAttempt:
    """Level 3: Vision LLM extraction (single page, cost-effective)."""
    start_time = time.time()

    try:
        # Render page to image
        page_image = render_pdf_page_to_image(pdf_path, page, dpi=220)

        # Build prompt
        prompt = build_vision_prompt_for_field(field_name)

        # Call vision LLM (try Grok first, fallback to GPT-4V)
        result = call_vision_llm(page_image, prompt, model="grok-vision-beta")

        if result["value"]:
            confidence = 0.60  # Base for vision
            # Boost if LLM expressed high confidence
            if result.get("llm_confidence") == "high":
                confidence += 0.15

            return ExtractionAttempt(
                method="vision_llm_single",
                success=True,
                confidence=confidence,
                value=result["value"],
                error_message=None,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        return ExtractionAttempt(
            method="vision_llm_single",
            success=False,
            confidence=0.0,
            value=None,
            error_message="Vision LLM returned no value",
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return ExtractionAttempt(
            method="vision_llm_single",
            success=False,
            confidence=0.0,
            value=None,
            error_message=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )

def try_vision_llm_multi_page(pdf_path: str, field_name: str, pages: List[int]) -> ExtractionAttempt:
    """Level 4: Vision LLM extraction (multi page, expensive but thorough)."""
    start_time = time.time()

    try:
        # Limit pages to max 10 (cost control)
        pages_limited = pages[:10]

        # Render pages to images
        page_images = [render_pdf_page_to_image(pdf_path, p, dpi=220) for p in pages_limited]

        # Build prompt
        prompt = build_vision_prompt_for_field(field_name)

        # Call vision LLM with multiple pages
        result = call_vision_llm_multi(page_images, prompt, model="gpt-4-vision")

        if result["value"]:
            confidence = 0.50  # Base for multi-page vision
            # Boost if found on multiple pages (consistency)
            if result.get("found_on_multiple_pages"):
                confidence += 0.15

            return ExtractionAttempt(
                method="vision_llm_multi",
                success=True,
                confidence=confidence,
                value=result["value"],
                error_message=None,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        return ExtractionAttempt(
            method="vision_llm_multi",
            success=False,
            confidence=0.0,
            value=None,
            error_message="Vision LLM (multi) returned no value",
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return ExtractionAttempt(
            method="vision_llm_multi",
            success=False,
            confidence=0.0,
            value=None,
            error_message=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )
```

### Regex Pattern Library

```python
REGEX_PATTERNS = {
    "organization_number": r"org(?:anisations)?(?:nummer|nr|\.?\s*nr\.?)[:.\s]*(\d{6}[-\s]?\d{4})",
    "fastighetsbeteckning": r"fastighets?beteckning[:.\s]*([A-ZÅÄÖ][A-ZÅÄÖ\s\d:-]+)",
    "byggnadsår": r"byggnads?år[:.\s]*(\d{4})",
    "antal_lagenheter": r"antal\s+(?:bostadsrätts)?lägenheter[:.\s]*(\d+)",
    "ordförande": r"ordförande[:.\s]*([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
    "soliditet": r"soliditet[:.\s]*(\d+(?:[,.]\d+)?)\s*%",
    "arsavgift_per_sqm": r"års?avgift(?:\s*(?:per|/)\s*m²)?[:.\s]*(\d+(?:\s?\d{3})*(?:[,.]\d+)?)\s*kr",
}
```

### Testing Plan

**Dataset**: 20 documents, deliberately include:
- 5 pristine (structured tables, everything works)
- 10 medium quality (some tables, some text)
- 5 poor quality (scanned, OCR errors, malformed tables)

**Metrics**:
- Coverage by degradation level (% extracted at Level 1, Level 2, Level 3, Level 4)
- Average attempts per field (target: 1.5-2.0, meaning most fields extracted early)
- Not_found rate (target: <5% after all 4 levels)
- Cost per document (track API calls)

---

## Topic 7: Quality Scoring Refinement

### Problem
Current quality scoring (in `bench.py`) is heuristic-based. Need weighted, comprehensive scoring that accounts for confidence, validation, and completeness.

### Proposed Weighted Quality Score

```python
class QualityScore(BaseModel):
    """Comprehensive quality score for extraction."""

    # Component scores (0.0-1.0)
    coverage_score: float = 0.0       # % of required fields extracted
    confidence_score: float = 0.0     # Avg confidence of extracted fields
    validation_score: float = 0.0     # % of fields passing validation
    evidence_score: float = 0.0       # % of fields with evidence_pages
    consistency_score: float = 0.0    # Cross-field validation pass rate

    # Weighted overall score
    overall_score: float = 0.0

    # Metadata
    num_fields_extracted: int = 0
    num_fields_required: int = 0
    num_validation_warnings: int = 0
    num_validation_errors: int = 0

    @model_validator(mode='after')
    def calculate_overall_score(self):
        """
        Weighted overall score.

        Weights:
        - Coverage: 35% (most important - did we extract the data?)
        - Confidence: 25% (how sure are we?)
        - Validation: 20% (does it pass cross-checks?)
        - Evidence: 10% (can we prove it?)
        - Consistency: 10% (does everything make sense together?)
        """

        weights = {
            "coverage": 0.35,
            "confidence": 0.25,
            "validation": 0.20,
            "evidence": 0.10,
            "consistency": 0.10
        }

        self.overall_score = (
            weights["coverage"] * self.coverage_score +
            weights["confidence"] * self.confidence_score +
            weights["validation"] * self.validation_score +
            weights["evidence"] * self.evidence_score +
            weights["consistency"] * self.consistency_score
        )

        return self

def compute_quality_score(extracted_data: BRFAnnualReport) -> QualityScore:
    """
    Compute comprehensive quality score for extraction.
    """

    score = QualityScore()

    # 1. Coverage Score
    required_fields = get_required_fields(extracted_data)
    extracted_fields = get_extracted_fields(extracted_data)
    score.num_fields_required = len(required_fields)
    score.num_fields_extracted = len(extracted_fields)
    score.coverage_score = len(extracted_fields) / len(required_fields) if required_fields else 0.0

    # 2. Confidence Score
    confidences = get_all_confidences(extracted_data)
    score.confidence_score = sum(confidences) / len(confidences) if confidences else 0.0

    # 3. Validation Score
    validation_statuses = get_all_validation_statuses(extracted_data)
    num_valid = sum(1 for v in validation_statuses if v == "valid")
    num_warning = sum(1 for v in validation_statuses if v == "warning")
    num_error = sum(1 for v in validation_statuses if v == "error")

    score.num_validation_warnings = num_warning
    score.num_validation_errors = num_error

    # Validation score: valid=1.0, warning=0.7, error=0.3, unknown=0.5
    validation_points = (
        num_valid * 1.0 +
        num_warning * 0.7 +
        num_error * 0.3 +
        (len(validation_statuses) - num_valid - num_warning - num_error) * 0.5
    )
    score.validation_score = validation_points / len(validation_statuses) if validation_statuses else 0.0

    # 4. Evidence Score
    fields_with_evidence = get_fields_with_evidence(extracted_data)
    score.evidence_score = len(fields_with_evidence) / score.num_fields_extracted if score.num_fields_extracted > 0 else 0.0

    # 5. Consistency Score
    consistency_checks = run_consistency_checks(extracted_data)
    num_pass = sum(1 for c in consistency_checks if c["pass"])
    score.consistency_score = num_pass / len(consistency_checks) if consistency_checks else 0.0

    # Compute overall
    score.calculate_overall_score()

    return score

def get_required_fields(data: BRFAnnualReport) -> List[str]:
    """
    Get list of required fields for this document type.

    Required fields (example):
    - Metadata: document_id, brf_name, organization_number, fiscal_year
    - Governance: chairman, board_members
    - Financial: net_revenue, total_assets, equity
    - Property: property_designation, num_apartments
    """

    required = [
        "metadata.document_id",
        "metadata.brf_name",
        "metadata.organization_number",
        "metadata.fiscal_year",
        "governance.chairman",
        "governance.board_members",
        "financial.nettoomsattning_tkr",
        "financial.tillgangar_tkr",
        "financial.eget_kapital_tkr",
        "financial.soliditet_procent",
        "property.fastighetsbeteckning",
        "property.antal_lagenheter",
        "fees.arsavgift_per_sqm_total",
    ]

    return required

def get_extracted_fields(data: BRFAnnualReport) -> List[str]:
    """
    Get list of fields that were successfully extracted (value is not None).
    """

    extracted = []

    # Walk through schema and collect non-None fields
    for section in ["metadata", "governance", "financial", "property", "fees"]:
        section_data = getattr(data, section, None)
        if not section_data:
            continue

        for field_name, field_value in section_data.__dict__.items():
            if field_name.startswith("_"):
                continue

            if isinstance(field_value, ExtractionField):
                if field_value.value is not None:
                    extracted.append(f"{section}.{field_name}")
            elif field_value is not None:
                extracted.append(f"{section}.{field_name}")

    return extracted

def get_all_confidences(data: BRFAnnualReport) -> List[float]:
    """Get all confidence scores from extracted fields."""

    confidences = []

    for section in ["governance", "financial", "property", "fees"]:
        section_data = getattr(data, section, None)
        if not section_data:
            continue

        for field_value in section_data.__dict__.values():
            if isinstance(field_value, ExtractionField) and field_value.value is not None:
                confidences.append(field_value.confidence)

    return confidences

def run_consistency_checks(data: BRFAnnualReport) -> List[Dict]:
    """
    Run cross-field consistency checks.

    Examples:
    1. Assets = Liabilities + Equity (balance sheet identity)
    2. Surplus = Revenue - Expenses
    3. Solidarity % = Equity / Assets * 100
    4. Debt per m² = Total Debt / Total Area
    """

    checks = []

    # Check 1: Balance sheet identity
    if (data.financial and
        data.financial.tillgangar_tkr and data.financial.tillgangar_tkr.value and
        data.financial.skulder_tkr and data.financial.skulder_tkr.value and
        data.financial.eget_kapital_tkr and data.financial.eget_kapital_tkr.value):

        assets = data.financial.tillgangar_tkr.value
        liabilities = data.financial.skulder_tkr.value
        equity = data.financial.eget_kapital_tkr.value

        expected_assets = liabilities + equity
        diff = abs(assets - expected_assets)
        tolerance = get_financial_tolerance(assets) * 2  # More generous for consistency checks

        checks.append({
            "name": "balance_sheet_identity",
            "pass": diff <= tolerance,
            "details": f"Assets={assets:.0f}, Liabilities+Equity={expected_assets:.0f}, diff={diff:.0f}"
        })

    # Check 2: Solidarity calculation
    if (data.financial and
        data.financial.eget_kapital_tkr and data.financial.eget_kapital_tkr.value and
        data.financial.tillgangar_tkr and data.financial.tillgangar_tkr.value and
        data.financial.soliditet_procent and data.financial.soliditet_procent.value):

        equity = data.financial.eget_kapital_tkr.value
        assets = data.financial.tillgangar_tkr.value
        solidarity_extracted = data.financial.soliditet_procent.value

        solidarity_calculated = (equity / assets * 100) if assets > 0 else 0
        diff = abs(solidarity_extracted - solidarity_calculated)

        checks.append({
            "name": "solidarity_calculation",
            "pass": diff <= 2.0,  # ±2 percentage points
            "details": f"Extracted={solidarity_extracted:.1f}%, Calculated={solidarity_calculated:.1f}%"
        })

    # Check 3: Fee calculation (if both annual and monthly found)
    if (data.fees and
        data.fees.arsavgift_per_sqm_total and data.fees.arsavgift_per_sqm_total.value and
        data.fees.manadsavgift_per_sqm and data.fees.manadsavgift_per_sqm.value):

        annual = data.fees.arsavgift_per_sqm_total.value
        monthly = data.fees.manadsavgift_per_sqm.value

        annual_from_monthly = monthly * 12
        diff = abs(annual - annual_from_monthly)
        tolerance = get_financial_tolerance(annual)

        checks.append({
            "name": "fee_annual_monthly_consistency",
            "pass": diff <= tolerance,
            "details": f"Annual={annual:.0f}, Monthly*12={annual_from_monthly:.0f}"
        })

    return checks
```

### Quality Score Interpretation

```python
def interpret_quality_score(score: QualityScore) -> str:
    """
    Interpret overall quality score.

    Ranges:
    - 0.95-1.00: Excellent (production-ready)
    - 0.85-0.94: Good (minor issues)
    - 0.70-0.84: Fair (needs review)
    - 0.50-0.69: Poor (significant issues)
    - 0.00-0.49: Failed (major extraction problems)
    """

    if score.overall_score >= 0.95:
        return "Excellent - Production ready"
    elif score.overall_score >= 0.85:
        return "Good - Minor issues, acceptable"
    elif score.overall_score >= 0.70:
        return "Fair - Needs manual review"
    elif score.overall_score >= 0.50:
        return "Poor - Significant extraction issues"
    else:
        return "Failed - Major problems, reject"
```

### Testing Plan

**Dataset**: 50 documents with manual ground truth

**Metrics**:
- Correlation: Does higher quality score correlate with fewer errors?
- Calibration: Does 0.95 overall score → ~95% accuracy?
- Component breakdown: Which component (coverage, confidence, validation) is most predictive?

---

## Summary & Next Steps

### Integration Summary

**What we're building**: Unified schema merging Gracian's breadth (150-200 fields, 8 levels) with ZeldaDemo's maturity (confidence tracking, multi-year, validation).

**Key Principles**:
1. **Tolerant Validation**: Never null data, warn instead of reject
2. **Graceful Degradation**: Try all extraction methods before giving up
3. **Confidence Tracking**: All fields have confidence scores
4. **Swedish-First**: Semantic fields match document terminology
5. **Evidence-Based**: All extractions cite source pages

### Week-by-Week Plan

**Week 1**: Foundation (ExtractionField + MultiYear)
**Week 2**: Intelligence (Validation + Synonyms + Swedish-First)
**Week 3**: Testing (Coverage, accuracy, documentation)

### Success Criteria

✅ **Coverage**: ≥95% of required fields extracted
✅ **Confidence**: Average ≥0.85, calibrated (0.9 → ~90% accuracy)
✅ **Validation**: ≥85% pass rate, 0% data loss
✅ **Evidence**: ≥95% of extractions cite source pages
✅ **Quality**: Overall score ≥0.95 for production-ready documents

### Risk Mitigation

- Daily monitoring of data loss rate (must stay 0%)
- Parallel running of old + new schema (Week 1)
- Rollback plan at each week boundary
- Tolerance calibration based on real documents (not hardcoded)

---

## Questions for Ultrathinking Round 2

1. **Tolerance Calibration**: Should thresholds vary by document quality (pristine vs scanned)?
2. **Confidence Aggregation**: When multiple methods disagree, is weighted vote optimal?
3. **Multi-Year Parsing**: How to handle missing years in sequence (gap-filling strategy)?
4. **Integration Sequencing**: Is 3 weeks realistic, or should we plan for 4?
5. **Swedish-First Priority**: Should all fields be Swedish-first, or only financial/fees?
6. **Error Recovery**: Is 4-level degradation too expensive (API costs)?
7. **Quality Scoring**: Should we add more components (e.g., extraction speed, cost)?

---

**Status**: Ready for implementation. Awaiting user feedback on ultrathinking analysis.
