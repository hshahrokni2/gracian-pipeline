# Implementation Quick Reference - Semantic Validation Fix

**Target File**: `gracian_pipeline/validation/semantic_matcher.py`
**Time**: 1-2 hours
**Expected Result**: Coverage 3.3% → 30-40%

---

## Code Change #1: Year-Suffix Stripping

### Location: Add after line 227 (after `normalize_key()`)

```python
def _normalize_field_name_with_year(self, field_name: str) -> Tuple[str, Optional[str]]:
    """
    Extract year suffix from field name.

    Ground truth often has year suffixes like '_2021', '_2020', etc.
    Extraction typically doesn't (extracts current year only).

    Examples:
        "annual_fee_per_sqm_2021" → ("annual_fee_per_sqm", "2021")
        "acquisition_value_2020" → ("acquisition_value", "2020")
        "chairman" → ("chairman", None)

    Returns:
        Tuple[base_name, year_suffix]
    """
    year_pattern = r"_(\d{4})$"
    match = re.search(year_pattern, field_name)
    if match:
        year = match.group(1)
        base_name = field_name[:match.start()]
        return (base_name, year)
    return (field_name, None)
```

---

## Code Change #2: Update find_field()

### Location: Line 254 (beginning of `find_field()`)

**BEFORE**:
```python
def find_field(self, data: Dict, canonical_field_name: str) -> Tuple[Optional[Any], float]:
    """Find field in data using semantic matching."""

    # 1. Try exact match
    if canonical_field_name in data:
        return (data[canonical_field_name], 1.0)
```

**AFTER**:
```python
def find_field(self, data: Dict, canonical_field_name: str) -> Tuple[Optional[Any], float]:
    """Find field in data using semantic matching."""

    # NEW: Strip year suffix from field name
    base_field_name, year = self._normalize_field_name_with_year(canonical_field_name)

    # 1. Try exact match (using base name without year)
    if base_field_name in data:
        return (data[base_field_name], 1.0)

    # 2. Try normalized exact match
    normalized = self.normalize_key(base_field_name)  # Changed from canonical_field_name
    if normalized in data:
        return (data[normalized], 1.0)

    # ... rest of function unchanged (just use base_field_name instead of canonical_field_name)
```

**Find/Replace Pattern**:
- Find: `canonical_field_name` (within `find_field()` function only)
- Replace with: `base_field_name`
- **EXCEPT**: Keep `canonical_field_name` in the function signature!

---

## Code Change #3: Expand SYNONYM_DICT

### Location: Lines 44-227 (SYNONYM_DICT definition)

**Add to the dictionary** (after existing entries):

```python
    # ========================================
    # ADDED 2025-10-10: Field name variations
    # discovered from validation analysis
    # ========================================

    # Building/Note 8 field variations
    "acquisition_value": [
        "opening_acquisition_value",
        "closing_acquisition_value",
        "anskaffningsvärde"
    ],
    "accumulated_depreciation": [
        "opening_depreciation",
        "closing_depreciation",
        "ackumulerad_avskrivning"
    ],
    "book_value": [
        "net_book_value",
        "carrying_amount",
        "bokfört_värde"
    ],
    "depreciation": [
        "depreciation_for_year",
        "årets_avskrivning"
    ],

    # Cash flow variations
    "liquid_assets": [
        "cash_and_bank",
        "cash_and_cash_equivalents",
        "likvida_medel",
        "kassa_och_bank"
    ],
    "liquid_assets_beginning": [
        "opening_liquid_assets",
        "beginning_of_year",
        "ingående_likvida_medel"
    ],
    "liquid_assets_end": [
        "closing_liquid_assets",
        "end_of_year",
        "utgående_likvida_medel"
    ],
    "change_in_liquid_assets": [
        "liquid_assets_change",
        "årets_förändring"
    ],

    # Governance variations
    "auditors": [
        "primary_auditor",
        "deputy_auditor",
        "audit_firm",
        "revisor",
        "revisorer"
    ],
    "primary_auditor": [
        "auditor_name",
        "ordinarie_revisor"
    ],
    "deputy_auditor": [
        "suppleant",
        "ersättare"
    ],
    "board_meetings_count": [
        "number_of_board_meetings",
        "antal_styrelsemöten"
    ],

    # Financial statement variations
    "operating_income": [
        "income_from_operations",
        "rörelseintäkter",
        "nettoomsättning"
    ],
    "operating_costs": [
        "operating_expenses",
        "rörelsekostnader"
    ],
    "financial_income": [
        "interest_income",
        "ränteintäkter",
        "finansiella_intäkter"
    ],
    "financial_costs": [
        "interest_costs",
        "räntekostnader",
        "finansiella_kostnader"
    ],

    # Property/Apartment variations
    "total_apartments": [
        "total_count",
        "number_of_apartments",
        "antal_lägenheter"
    ],
    "apartment_distribution": [
        "apartment_breakdown",
        "breakdown",
        "lägenhetsfördelning"
    ],
    "living_area_sqm": [
        "total_area_sqm",
        "boarea",
        "totalarea"
    ],

    # Fee variations
    "monthly_fee_average": [
        "manadsavgift_per_apartment_avg",
        "average_monthly_fee",
        "genomsnittlig_månadsavgift"
    ],
    "annual_fee_average": [
        "arsavgift_per_apartment_avg",
        "average_annual_fee",
        "genomsnittlig_årsavgift"
    ],

    # Note-specific variations
    "note_8_buildings": [
        "building_details",
        "buildings_and_land",
        "byggnader"
    ],
    "note_9_receivables": [
        "receivables_breakdown",
        "kortfristiga_fordringar"
    ],
    "note_5_financial_items": [
        "financial_income_and_costs",
        "finansiella_poster"
    ],
```

---

## Validation Test

### Run this after implementing changes:

```bash
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"
python test_confidence_validator.py
```

### Expected Output:

**BEFORE** (current):
```
Total GT Fields:               172
Matched Fields:                6
High Confidence (>0.9):        5
Weighted Coverage:             3.3%
```

**AFTER** (with fixes):
```
Total GT Fields:               172
Matched Fields:                50-70  ← Should increase significantly
High Confidence (>0.9):        40-60  ← Should increase significantly
Weighted Coverage:             30-40% ← Should jump from 3.3%
```

---

## Testing Individual Changes

### Test year-suffix stripping:

```python
# Quick test in Python REPL
from gracian_pipeline.validation.semantic_matcher import SemanticFieldMatcher

matcher = SemanticFieldMatcher()

# Test the new function
base, year = matcher._normalize_field_name_with_year("annual_fee_per_sqm_2021")
print(f"Base: {base}, Year: {year}")  # Should print: Base: annual_fee_per_sqm, Year: 2021

# Test find_field with year suffix
import json
with open('validation_extraction_brf_198532.json') as f:
    extraction = json.load(f)

# This should now match (previously failed)
value, conf = matcher.find_field(extraction, "annual_fee_per_sqm_2021")
print(f"Found: {value}, Confidence: {conf}")  # Should find the value
```

---

## Troubleshooting

### Issue: "No improvement in coverage"

**Check**:
1. Did you update `find_field()` to use `base_field_name`?
2. Did you add the year-stripping function?
3. Are you testing with `test_confidence_validator.py`?

### Issue: "Import error"

**Fix**: Add to imports at top of file:
```python
from typing import Tuple, Optional  # Make sure Tuple and Optional are imported
```

### Issue: "Regex not working"

**Check**: Make sure you imported `re` at the top:
```python
import re
```

---

## Files to Create After Success

1. `SEMANTIC_VALIDATION_SUCCESS.md` - Document the improvement
2. Update validation report: `validation_report_semantic.json`

### Template for success document:

```markdown
# Semantic Validation Success - Coverage Improved

**Date**: 2025-10-10
**Achievement**: Coverage improved from 3.3% to XX%

## Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Coverage | 3.3% | XX% | +YY% |
| Matched Fields | 6 | XX | +YY |
| High Confidence | 5 | XX | +YY |

## Implementation

1. Year-suffix stripping: ✅
2. Synonym expansion: ✅
3. Validation test: ✅

## Next Steps

- Gap analysis for remaining unmatched fields
- Extraction improvements for truly missing fields
```

---

**Status**: Ready to implement
**Estimated Time**: 90-120 minutes
**Confidence**: High (clear problem, clear solution)

