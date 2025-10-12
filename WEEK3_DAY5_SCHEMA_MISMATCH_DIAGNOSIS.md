# Week 3 Day 5: Schema Mismatch Diagnosis - The REAL Problem

## 🎯 Issue Summary

**Coverage**: 3.5% (6/172 fields matched)

**Root Cause Identified**: Ground truth schema doesn't align with extraction schema in TWO fundamental ways:

1. **Structure**: Flat (GT) vs Nested (Extraction)
2. **Temporal**: Year suffixes (GT) vs Current year only (Extraction)

## 🔬 Technical Analysis

### Extraction Schema (Nested, Semantic)

```json
{
  "metadata": { ... },
  "governance": {
    "chairman": "Elvy Maria Löfvenberg",
    "board_members": [...],
    "auditor_name": "Tobias Andersson"
  },
  "financial": {
    "revenue": 7451585,
    "expenses": 6631400,
    "assets": 675294786
  },
  "fees": {
    "annual_fee_per_sqm": 582
  },
  "multi_year_overview": {
    "2021": { ... },
    "2020": { ... }
  }
}
```

**Structure**: Deeply nested, agent-grouped (20 top-level keys)
**Temporal**: Single values for current year, with separate `multi_year_overview` section

### Ground Truth Schema (Flat, Year-Qualified)

```json
{
  "organization_number": "769629-0134",
  "brf_name": "Bostadsrättsföreningen Björk och Plaza",
  "fiscal_year": 2021,
  "chairman": "Elvy Maria Löfvenberg",
  "board_members": [...],
  "annual_fee_per_sqm_2021": 582,
  "annual_fee_per_sqm_2020": 582,
  "annual_fee_per_sqm_2019": 582,
  "revenue_breakdown_2021": { ... },
  "building_details_note8": { ... },
  "acquisition_value_2021": 682435875,
  "acquisition_value_2020": 682435875
}
```

**Structure**: Completely flat (172 top-level keys)
**Temporal**: Separate field for each year (2021, 2020, 2019, 2018)

## 📊 Mismatch Examples

### Example 1: Nested vs Flat

**Ground Truth**: `annual_fee_per_sqm_2021`
**Extraction**: `fees.annual_fee_per_sqm`

**Current Result**: "Field not found"
**Why**: Semantic matcher searches for "annual_fee_per_sqm_2021" → strips to "annual_fee_per_sqm" → searches flat structure → not found because it's nested in `fees.*`

### Example 2: Year-Qualified vs Single Year

**Ground Truth**:
- `annual_fee_per_sqm_2021`: 582
- `annual_fee_per_sqm_2020`: 582
- `annual_fee_per_sqm_2019`: 582

**Extraction**:
- `fees.annual_fee_per_sqm`: 582 (current year only)

**Current Result**: All 3 GT fields show as "missing"
**Why**: GT expects historical data, extraction only provides current year

### Example 3: Structural Complexity

**Ground Truth**: `building_details_note8`
```json
{
  "acquisition_value_2021": 682435875,
  "accumulated_depreciation_2021": -15765114,
  "book_value_2021": 666670761
}
```

**Extraction**: `notes.building_details` or `financial.building_details`
```json
{
  "ackumulerade_anskaffningsvarden": 682435875,
  "planenligt_restvarde": 666670761
}
```

**Current Result**: "Field not found"
**Why**: Different nesting AND different Swedish field names

## ✅ What's Currently Working

1. **Year-suffix stripping** ✅ (lines 388-422 in semantic_matcher.py)
2. **Nested dictionary search** ✅ (lines 452-482)
3. **349 Swedish synonyms** ✅ (lines 44-352)

## ❌ What's NOT Working

1. **Finding nested fields when GT expects flat** ❌
   - GT: `annual_fee_per_sqm_2021`
   - Search: Looks for `annual_fee_per_sqm` at top level
   - Reality: It's in `fees.annual_fee_per_sqm`

2. **Mapping year-qualified fields to current year** ❌
   - GT: `acquisition_value_2021`, `acquisition_value_2020`
   - Extraction: Only has `acquisition_value` (current)
   - Matcher: Doesn't know `_2021` means "current year"

3. **Swedish field names in nested structures** ❌
   - GT: `acquisition_value`
   - Extraction: `ackumulerade_anskaffningsvarden`
   - Matcher: Has synonym but search fails because nested

## 💡 The Solution

The `_search_nested_dict()` method ALREADY searches nested structures (lines 452-482), but it's not being triggered properly because:

1. The year-suffix strip happens (✅)
2. But then it searches for `annual_fee_per_sqm` directly
3. It finds nothing because semantic matching with synonyms happens AFTER the nested search
4. Need to integrate synonym matching INTO the nested search

## 🚀 Fix Implementation

### Current Flow (WRONG)
```python
def find_field(canonical_field):
    # 1. Strip year suffix
    base_field = "annual_fee_per_sqm"  # from "annual_fee_per_sqm_2021"

    # 2. Direct search (fails for nested)
    value = _search_nested_dict(data, "annual_fee_per_sqm")  # NOT FOUND

    # 3. Synonym search (fails because no synonyms for exact field)
    synonyms = ["avgift_per_kvm", ...]  # different keys!
    value = _search_nested_dict(data, synonym)  # NOT FOUND

    return None, 0.0
```

### Fixed Flow (CORRECT)
```python
def find_field(canonical_field):
    # 1. Strip year suffix
    base_field = "annual_fee_per_sqm"

    # 2. Get ALL possible names (canonical + synonyms)
    search_terms = [base_field] + get_synonyms(base_field)
    # ["annual_fee_per_sqm", "avgift_per_kvm", "fee_per_sqm", "annual_fee"]

    # 3. Search nested dict for ANY matching term
    for term in search_terms:
        value = _search_nested_dict(data, term)
        # Searches: fees.annual_fee_per_sqm ✅ FOUND!
        if value is not None:
            return value, 0.95

    # 4. Fuzzy fallback
    ...
```

## 📈 Expected Improvement

### Before Fix
- Coverage: 3.5% (6/172)
- Matched fields:
  1. organization_number (top-level, exact)
  2. fiscal_year (top-level, exact)
  3. municipality (nested in property)
  4. board_members (nested in governance)
  5. annual_meeting_date (nested in governance)
  6. end_2021 (nested in reserves)

### After Fix (Expected)
- Coverage: **30-40%** (52-69/172)
- Additional matches:
  - All `fees.*` fields (5-8 fields)
  - All `governance.*` fields (10-15 fields)
  - All `financial.*` nested fields (15-20 fields)
  - Year-qualified fields matching current year (10-15 fields)

## 🔧 Implementation Required

**File**: `gracian_pipeline/validation/semantic_matcher.py`

**Change**: Modify `find_field()` to search for ALL synonyms in nested structures

```python
def find_field(self, data: Dict, canonical_field_name: str) -> Tuple[Optional[Any], float]:
    # Strip year suffix
    base_field_name, year = self._normalize_field_name_with_year(canonical_field_name)

    # Get all search terms (canonical + synonyms)
    search_terms = [base_field_name] + self.field_synonyms.get(base_field_name, [])

    # Search for ANY term in nested structure
    for term in search_terms:
        value, conf = self._search_nested_dict(data, term)
        if value is not None:
            confidence = 1.0 if term == base_field_name else 0.95
            return value, confidence

    # Fuzzy fallback
    ...
```

## 📁 Files Affected

1. `gracian_pipeline/validation/semantic_matcher.py` - Modify `find_field()`
2. `test_confidence_validator.py` - Re-run validation
3. `validation_report_semantic.json` - New results

## ⏱️ Time Estimate

- Code change: 15 minutes (simple refactor)
- Testing: 15 minutes
- Documentation: 30 minutes

**Total**: 1 hour

## 🎯 Success Criteria

- Coverage: 3.5% → **30-40%**
- High confidence matches: 5 → **40-50**
- Proves semantic matching works for production

---

**Status**: ✅ **DIAGNOSIS COMPLETE**
**Next Action**: Implement fix in `find_field()` method
**Risk**: Low (refactor existing working code)
