# Week 2 Focused Implementation Guide - Schema v7.0

**Date**: October 13, 2025
**Ultrathinking Analysis**: Critical path optimization for 501-field schema
**Philosophy**: Incremental implementation with continuous validation

---

## 🎯 Ultrathinking Analysis: What's the REAL Critical Path?

### The Traditional Approach (DON'T DO THIS)

❌ **Naive approach**: Copy ZeldaDemo → Add all Gracian fields → Test at end
- **Problem 1**: 1,800 line schema changes are hard to debug
- **Problem 2**: Breaking changes discovered too late
- **Problem 3**: No validation until everything is built
- **Risk**: High chance of starting over

### The Optimal Approach (DO THIS)

✅ **Incremental approach**: Build → Test → Validate → Iterate
- **Layer 1**: Core ExtractionField enhancement (50 lines) → Test (10 tests)
- **Layer 2**: Swedish-first pattern (200 lines) → Test (20 tests)
- **Layer 3**: Tolerant validation (300 lines) → Test (30 tests)
- **Layer 4**: Specialized notes (400 lines) → Test (40 tests)
- **Layer 5**: Integration with extractors → End-to-end tests

**Why this works**:
- Each layer is independently testable
- Breaking changes discovered immediately
- Can stop and review at any layer
- Reduces risk from HIGH → LOW

---

## 📊 Critical Path Analysis

### What MUST be done vs What CAN wait

| Task | Week 2? | Why? | Dependencies |
|------|---------|------|--------------|
| **ExtractionField enhancement** | ✅ YES | Foundation for everything | None |
| **Swedish-first financial fields** | ✅ YES | Required for ground truth creation | ExtractionField |
| **Tolerant validation** | ✅ YES | Required for agent training | ExtractionField |
| **Specialized note structures** | ✅ YES | Required for 92 note fields | ExtractionField |
| **ALL 501 fields implemented** | ❌ NO | Can be gradual | Can add in Week 3-4 |
| **SYNONYM_MAPPING integration** | ⚠️ PARTIAL | Core 50 terms YES, all 250 can wait | None |
| **Migration from v6 to v7** | ❌ NO | Not needed yet | v7 complete |
| **Data quality scoring** | ⚠️ PARTIAL | Basic version YES, advanced can wait | ExtractionField |

**Key Insight**: We don't need ALL 501 fields implemented in Week 2. We need the ARCHITECTURE that supports 501 fields.

**Minimum Viable Schema v7.0** (Week 2 target):
- ✅ Enhanced ExtractionField (6 fields)
- ✅ Swedish-first pattern (applied to 50 key fields)
- ✅ Tolerant validation (3-tier system)
- ✅ Specialized notes (Note 8, Note 9)
- ✅ Core field groups (Metadata, Organization, Governance, Property, Financial)
- ✅ 100 tests passing

**Total Week 2 implementation**: ~800 lines of schema code + 400 lines of tests = 1,200 lines

**Remaining fields** (Weeks 3-4): Add incrementally as agents are trained

---

## 🏗️ Day-by-Day Implementation Plan (Week 2)

### Day 1 (Monday): Foundation Setup

**Goal**: Create schema_v7.py with enhanced ExtractionField
**Time**: 4-5 hours
**Output**: 150 lines schema + 20 tests passing

#### Step 1.1: Copy Base (30 minutes)
```bash
cd ~/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian\ Pipeline/experiments/docling_advanced
cp ~/Dropbox/Zelda/ZeldaDemo/Ground\ Truth,\ Schema,\ Mappings/schema.py schema_v7.py

# Update header
# Change version from 6.0 to 7.0
# Add merge attribution
```

#### Step 1.2: Enhance ExtractionField (1 hour)

**Current ZeldaDemo ExtractionField**:
```python
class ExtractionField(BaseModel):
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Optional[str] = None
```

**Enhanced v7.0 ExtractionField**:
```python
from datetime import datetime

class ExtractionField(BaseModel):
    """
    Base model for extraction fields with confidence and source tracking.

    Version 7.0 enhancements:
    - Enhanced evidence tracking (evidence_pages, extraction_method, model_used)
    - Validation status (valid/warning/error for tolerant validation)
    - Alternative values (for multi-source extraction)
    - Extraction timestamp (for tracking when field was extracted)
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    # Core fields (from v6.0)
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    source: Optional[str] = None

    # Enhanced evidence tracking (from Gracian)
    evidence_pages: List[int] = Field(
        default_factory=list,
        description="List of page numbers where this field was found (1-indexed)"
    )
    extraction_method: Optional[str] = Field(
        None,
        description="Method used: 'table_extraction', 'text_extraction', 'calculated', 'manual'"
    )
    model_used: Optional[str] = Field(
        None,
        description="Model/tool used: 'gpt-4o', 'gpt-4o-mini', 'docling', 'gemini-2.5-pro', 'manual'"
    )

    # Validation status (for tolerant 3-tier validation)
    validation_status: Optional[str] = Field(
        None,
        description="Validation result: 'valid', 'warning', 'error', 'unknown'"
    )

    # Alternative values (for multi-source extraction and conflict resolution)
    alternative_values: List[Any] = Field(
        default_factory=list,
        description="Alternative values found from other sources (for comparison)"
    )

    # Extraction timestamp
    extraction_timestamp: Optional[datetime] = Field(
        None,
        description="When this field was extracted (UTC)"
    )
```

#### Step 1.3: Update Typed Fields (1.5 hours)

Add enhanced fields to StringField, NumberField, IntegerField, BooleanField:
```python
class StringField(ExtractionField):
    value: Optional[str] = None

class NumberField(ExtractionField):
    value: Optional[Union[float, str]] = None  # Allow string for Swedish number format

    def model_dump(self, *args, **kwargs):
        """Override to ensure clean number strings."""
        dump = super().model_dump(*args, **kwargs)
        val = dump.get('value')
        if isinstance(val, float) and val == int(val):
            dump['value'] = str(int(val))  # 14460.0 → "14460"
        elif isinstance(val, float):
            dump['value'] = str(val).rstrip('0').rstrip('.')
        elif isinstance(val, str) and val.endswith('.0'):
            dump['value'] = val[:-2]
        return dump

class IntegerField(ExtractionField):
    value: Optional[int] = None

class BooleanField(ExtractionField):
    value: Optional[bool] = None

# Add from Gracian
class DateField(ExtractionField):
    value: Optional[str] = None  # Store as ISO string "YYYY-MM-DD"

class ListField(ExtractionField):
    value: Optional[List[Any]] = None

class DictField(ExtractionField):
    value: Optional[Dict[str, Any]] = None
```

#### Step 1.4: Write Tests (1.5 hours)

Create `test_schema_v7_base.py`:
```python
import pytest
from datetime import datetime
from schema_v7 import (
    ExtractionField, StringField, NumberField, IntegerField,
    BooleanField, DateField, ListField, DictField
)

class TestExtractionFieldEnhancements:
    """Test v7.0 ExtractionField enhancements."""

    def test_basic_field_creation(self):
        """Test basic field creation with core fields."""
        field = StringField(
            value="Test Value",
            confidence=0.95,
            source="page 5"
        )
        assert field.value == "Test Value"
        assert field.confidence == 0.95
        assert field.source == "page 5"

    def test_evidence_pages_tracking(self):
        """Test evidence_pages list tracking."""
        field = StringField(
            value="BRF Sjöstaden 2",
            confidence=0.98,
            evidence_pages=[1, 2, 5]
        )
        assert field.evidence_pages == [1, 2, 5]
        assert len(field.evidence_pages) == 3

    def test_extraction_method_tracking(self):
        """Test extraction_method tracking."""
        field = NumberField(
            value=301339818,
            confidence=1.0,
            extraction_method="table_extraction"
        )
        assert field.extraction_method == "table_extraction"

    def test_model_used_tracking(self):
        """Test model_used tracking."""
        field = StringField(
            value="Rolf Johansson",
            confidence=0.95,
            model_used="gpt-4o"
        )
        assert field.model_used == "gpt-4o"

    def test_validation_status(self):
        """Test validation_status for tolerant validation."""
        # Valid status
        field_valid = NumberField(
            value=20000,
            validation_status="valid"
        )
        assert field_valid.validation_status == "valid"

        # Warning status
        field_warning = NumberField(
            value=20500,
            validation_status="warning"
        )
        assert field_warning.validation_status == "warning"

        # Error status (but data preserved!)
        field_error = NumberField(
            value=25000,
            validation_status="error"
        )
        assert field_error.validation_status == "error"
        assert field_error.value == 25000  # Data still preserved!

    def test_alternative_values(self):
        """Test alternative_values for multi-source extraction."""
        field = NumberField(
            value=301339818,  # Primary value
            alternative_values=[301339000, 301340000],  # From other sources
            confidence=0.90
        )
        assert field.value == 301339818
        assert len(field.alternative_values) == 2
        assert 301339000 in field.alternative_values

    def test_extraction_timestamp(self):
        """Test extraction_timestamp tracking."""
        now = datetime.utcnow()
        field = StringField(
            value="Test",
            extraction_timestamp=now
        )
        assert field.extraction_timestamp == now

    def test_complete_field_with_all_enhancements(self):
        """Test field with ALL v7.0 enhancements."""
        field = NumberField(
            value=99538124,
            confidence=0.95,
            source="page 7, Balance Sheet",
            evidence_pages=[7],
            extraction_method="table_extraction",
            model_used="gpt-4o",
            validation_status="valid",
            alternative_values=[99538000, 99538200],
            extraction_timestamp=datetime.utcnow()
        )

        assert field.value == 99538124
        assert field.confidence == 0.95
        assert field.source == "page 7, Balance Sheet"
        assert field.evidence_pages == [7]
        assert field.extraction_method == "table_extraction"
        assert field.model_used == "gpt-4o"
        assert field.validation_status == "valid"
        assert len(field.alternative_values) == 2
        assert field.extraction_timestamp is not None


class TestTypedFieldEnhancements:
    """Test typed field classes (StringField, NumberField, etc.)."""

    def test_string_field(self):
        field = StringField(value="769606-2533")
        assert field.value == "769606-2533"
        assert isinstance(field, ExtractionField)

    def test_number_field_float(self):
        field = NumberField(value=301339818.0)
        assert field.value == 301339818.0

    def test_number_field_string(self):
        field = NumberField(value="301 339 818")  # Swedish format
        assert field.value == "301 339 818"

    def test_number_field_dump_clean(self):
        """Test NumberField.model_dump() cleans float strings."""
        field = NumberField(value=14460.0)
        dump = field.model_dump()
        assert dump['value'] == "14460"  # Not "14460.0"

    def test_integer_field(self):
        field = IntegerField(value=42)
        assert field.value == 42
        assert isinstance(field.value, int)

    def test_boolean_field(self):
        field = BooleanField(value=True)
        assert field.value is True

    def test_date_field(self):
        field = DateField(value="2021-12-31")
        assert field.value == "2021-12-31"

    def test_list_field(self):
        field = ListField(value=["item1", "item2", "item3"])
        assert len(field.value) == 3
        assert "item1" in field.value

    def test_dict_field(self):
        field = DictField(value={"key1": "value1", "key2": 42})
        assert field.value["key1"] == "value1"
        assert field.value["key2"] == 42


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run tests**:
```bash
cd ~/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian\ Pipeline/experiments/docling_advanced
pytest test_schema_v7_base.py -v
```

**Success criteria**: All 20 tests passing ✅

---

### Day 2 (Tuesday): Swedish-First Pattern

**Goal**: Implement Swedish-first pattern for key financial fields
**Time**: 5-6 hours
**Output**: 250 lines schema + 30 tests passing

#### Step 2.1: Add Tolerance Functions (1 hour)

Add at top of schema_v7.py (before classes):
```python
# =============================================================================
# TOLERANCE FUNCTIONS (for Tolerant 3-Tier Validation)
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

    Examples:
        >>> get_financial_tolerance(50_000)   # Small
        7500.0  # max(5k, 50k * 0.15) = 7.5k
        >>> get_financial_tolerance(5_000_000)  # Medium
        500000.0  # max(50k, 5M * 0.10) = 500k
        >>> get_financial_tolerance(50_000_000)  # Large
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

    Args:
        value_per_sqm: Per-unit value (kr/m² or kr/m²/år)
        metric_type: "debt" or "fee"

    Returns:
        Tolerance threshold in same units as input

    Examples:
        >>> get_per_sqm_tolerance(20000, "debt")  # Debt per sqm
        2000.0  # max(1000, 20000 * 0.10)
        >>> get_per_sqm_tolerance(600, "fee")  # Fee per sqm annual
        100.0  # max(100, 600 * 0.10)
    """
    value_per_sqm = abs(value_per_sqm)

    if metric_type == "debt":
        return max(1_000, value_per_sqm * 0.10)
    elif metric_type == "fee":
        return max(100, value_per_sqm * 0.10)
    else:
        return max(500, value_per_sqm * 0.10)
```

#### Step 2.2: Implement Swedish-First YearlyFinancialData (2 hours)

Find `YearlyFinancialData` class and enhance:
```python
class YearlyFinancialData(BaseModel):
    """
    Financial data for a single year - Swedish-first semantic fields.

    Version 7.0 enhancement: Swedish fields are primary, English fields are aliases.
    This ensures extraction agents use Swedish terminology (which is what appears
    in the PDFs) while maintaining backward compatibility.
    """

    year: int = Field(..., ge=1900, le=2100, description="The fiscal year")

    # =============================================================================
    # SWEDISH-FIRST FIELDS (Primary - v7.0)
    # =============================================================================

    # Income statement (Swedish primary)
    nettoomsattning_tkr: Optional[NumberField] = Field(
        None, description="Nettoomsättning (net revenue) in tkr"
    )
    driftskostnader_tkr: Optional[NumberField] = Field(
        None, description="Driftskostnader (operating expenses) in tkr"
    )
    driftsoverskott_tkr: Optional[NumberField] = Field(
        None, description="Driftsöverskott (operating surplus) in tkr"
    )
    arsresultat_tkr: Optional[NumberField] = Field(
        None, description="Årsresultat (annual result) in tkr"
    )

    # Balance sheet (Swedish primary)
    tillgangar_tkr: Optional[NumberField] = Field(
        None, description="Tillgångar (assets) in tkr"
    )
    skulder_tkr: Optional[NumberField] = Field(
        None, description="Skulder (liabilities) in tkr"
    )
    eget_kapital_tkr: Optional[NumberField] = Field(
        None, description="Eget kapital (equity) in tkr"
    )
    soliditet_procent: Optional[NumberField] = Field(
        None, description="Soliditet (solidarity) in %"
    )

    # Metadata (v7.0 addition)
    terminology_found: Optional[str] = Field(
        None,
        description="Which Swedish terminology was found: 'nettoomsättning', 'intäkter', etc."
    )
    unit_verified: Optional[bool] = Field(
        None,
        description="Whether units (tkr, SEK, etc.) were explicitly verified in source"
    )

    # =============================================================================
    # ENGLISH ALIAS FIELDS (Secondary - for backward compatibility)
    # =============================================================================

    net_revenue_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for nettoomsättning_tkr"
    )
    operating_expenses_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for driftskostnader_tkr"
    )
    operating_surplus_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for driftsöverskott_tkr"
    )
    total_assets_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for tillgångar_tkr"
    )
    total_liabilities_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for skulder_tkr"
    )
    equity_tkr: Optional[NumberField] = Field(
        None, description="ALIAS for eget_kapital_tkr"
    )
    solidarity_percent: Optional[NumberField] = Field(
        None, description="ALIAS for soliditet_procent", alias="soliditet_percent"
    )

    # Keep existing fields from v6.0
    result_after_financial_tkr: Optional[float] = None
    annual_fee_per_kvm: Optional[float] = None
    debt_per_total_kvm: Optional[float] = None
    debt_per_residential_kvm: Optional[float] = None

    # Dynamic metric storage (keep from v6.0)
    metrics: Dict[str, Optional[float]] = Field(default_factory=dict)

    # Metadata
    is_complete: bool = Field(False)
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1)
    data_source: Optional[str] = None

    @model_validator(mode='after')
    def sync_swedish_english_financial_aliases(self):
        """
        Synchronize Swedish primary fields with English alias fields.

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
```

#### Step 2.3: Write Tests (2 hours)

Create `test_schema_v7_swedish_first.py`:
```python
import pytest
from schema_v7 import YearlyFinancialData, NumberField

class TestSwedishFirstPattern:
    """Test Swedish-first semantic field pattern."""

    def test_swedish_primary_english_alias_sync_swedish_to_english(self):
        """Test sync from Swedish (primary) to English (alias)."""
        year_data = YearlyFinancialData(
            year=2021,
            nettoomsattning_tkr=NumberField(value=5000, confidence=0.95)
        )

        # After model_validator, English alias should be populated
        assert year_data.net_revenue_tkr is not None
        assert year_data.net_revenue_tkr.value == 5000
        assert year_data.net_revenue_tkr.confidence == 0.95

    def test_swedish_primary_english_alias_sync_english_to_swedish(self):
        """Test sync from English (for backward compatibility) to Swedish."""
        year_data = YearlyFinancialData(
            year=2021,
            net_revenue_tkr=NumberField(value=5000, confidence=0.95)
        )

        # After model_validator, Swedish primary should be populated
        assert year_data.nettoomsattning_tkr is not None
        assert year_data.nettoomsattning_tkr.value == 5000

    def test_all_financial_field_aliases(self):
        """Test all Swedish-English alias pairs."""
        year_data = YearlyFinancialData(
            year=2021,
            nettoomsattning_tkr=NumberField(value=5000),
            driftskostnader_tkr=NumberField(value=4000),
            driftsoverskott_tkr=NumberField(value=1000),
            tillgangar_tkr=NumberField(value=10000),
            skulder_tkr=NumberField(value=6000),
            eget_kapital_tkr=NumberField(value=4000),
            soliditet_procent=NumberField(value=40.0)
        )

        # All English aliases should be populated
        assert year_data.net_revenue_tkr.value == 5000
        assert year_data.operating_expenses_tkr.value == 4000
        assert year_data.operating_surplus_tkr.value == 1000
        assert year_data.total_assets_tkr.value == 10000
        assert year_data.total_liabilities_tkr.value == 6000
        assert year_data.equity_tkr.value == 4000
        assert year_data.solidarity_percent.value == 40.0

    def test_terminology_metadata(self):
        """Test terminology_found metadata tracking."""
        year_data = YearlyFinancialData(
            year=2021,
            nettoomsattning_tkr=NumberField(value=5000),
            terminology_found="nettoomsättning"
        )

        assert year_data.terminology_found == "nettoomsättning"

    def test_unit_verified_metadata(self):
        """Test unit_verified metadata tracking."""
        year_data = YearlyFinancialData(
            year=2021,
            nettoomsattning_tkr=NumberField(value=5000),
            unit_verified=True
        )

        assert year_data.unit_verified is True

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run tests**:
```bash
pytest test_schema_v7_swedish_first.py -v
```

**Success criteria**: All 30 tests passing (20 base + 30 Swedish-first = 50 total) ✅

---

### Day 3 (Wednesday): Tolerant Validation

**Goal**: Implement 3-tier tolerant validation in CalculatedFinancialMetrics
**Time**: 5-6 hours
**Output**: 300 lines schema + 40 tests passing

[Continue with similar detailed implementation for Days 3-5...]

---

## 🎯 Week 2 Success Metrics

### Code Metrics
- [ ] `schema_v7.py`: 800-1,000 lines (core architecture)
- [ ] Test files: 400-500 lines
- [ ] 100 tests passing (not 130 yet - that's Week 3)
- [ ] Zero breaking changes to existing extractors

### Architectural Completeness
- [ ] ExtractionField fully enhanced ✅
- [ ] Swedish-first pattern implemented for 50 key fields ✅
- [ ] Tolerant validation (3-tier) working ✅
- [ ] Specialized notes (Note 8, Note 9) added ✅
- [ ] Core field groups present (Metadata, Org, Governance, Property, Financial) ✅

### Integration Readiness
- [ ] Can import `from schema_v7 import BRFExtraction`
- [ ] Can create instances with v6.0 data (backward compatible)
- [ ] Can serialize/deserialize to JSON
- [ ] tolerance functions working and tested

---

## 🚀 Why This Approach is Optimal

### Traditional Approach Problems
1. **Big Bang Integration**: Try to do everything at once → high risk of failures
2. **Late Testing**: Test only at end → breaking changes discovered too late
3. **No Iteration**: Can't adjust based on learnings → forced to finish even if approach is wrong

### This Approach Advantages
1. **Incremental Building**: Each day adds one layer → manageable complexity
2. **Continuous Validation**: Test after each layer → immediate feedback
3. **Early Detection**: Breaking changes found within hours → easy to fix
4. **Flexibility**: Can adjust next day based on previous day learnings
5. **Reviewable**: Can review/approve after each day → confidence in progress

### Real-World Benefit
If we discover on Day 3 that tolerant validation doesn't work as expected:
- ❌ Traditional: Wasted Days 1-3, start over
- ✅ This approach: Adjust Day 3, Days 1-2 still valid

---

## 📋 Next Steps After Week 2

Once Week 2 is complete (core architecture working):

**Week 3**: Add remaining fields incrementally
- Add 50 fields/day while testing
- By end of week: 250 total fields implemented

**Week 4-5**: Ground truth creation
- Use schema_v7.py (even if not 100% complete)
- Missing fields can be added in Week 6

**Week 6**: Final integration
- Complete any missing fields
- Full end-to-end testing
- Migration from current pipeline

---

## ✅ Decision: Start Week 2 Implementation

**Recommendation**: Begin Day 1 implementation immediately

**First action**:
```bash
cd ~/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian\ Pipeline/experiments/docling_advanced
cp ~/Dropbox/Zelda/ZeldaDemo/Ground\ Truth,\ Schema,\ Mappings/schema.py schema_v7.py
```

**Estimated time**: 4-5 hours for Day 1 (ExtractionField enhancement + 20 tests)

---

**Status**: ✅ **ULTRATHINKING COMPLETE - READY FOR FOCUSED IMPLEMENTATION**

**Philosophy**: "Build incrementally, test continuously, adjust rapidly"
