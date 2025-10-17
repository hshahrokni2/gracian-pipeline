# 🧠 ULTRATHINKING: Year Naming Strategy for Time-Series Fields

**Date**: 2025-10-16
**Critical Issue**: Hardcoded years (_2023, _2022) break schema portability across years
**User Discovery**: "Why are we hardcoding years? We will have many different years over time."

---

## 🔴 THE PROBLEM

### **Current Schema (BROKEN)**
```python
"lokaler_revenue_2023": int
"lokaler_revenue_2022": int
"cash_to_debt_ratio_2023": float
"cash_to_debt_ratio_2022": float
"cash_to_debt_ratio_2021": float
```

### **Why This Breaks**

**Processing 2024 PDF**:
- Schema expects: `*_2023`, `*_2022`
- PDF contains: 2024 data (current), 2023 data (prior)
- **Result**: ❌ Mismatch - can't store 2024 data in `*_2023` field!

**Processing 2020 PDF**:
- Schema expects: `*_2023`, `*_2022`
- PDF contains: 2020 data (current), 2019 data (prior)
- **Result**: ❌ Complete mismatch - no 2023 data in 2020 report!

**Processing 27K PDFs (2015-2024 range)**:
- Schema expects: Only 2021-2023 years
- Corpus spans: 10 years (2015-2024)
- **Result**: ❌ Schema works for 3/10 years only (30%)!

---

## 🔍 EXISTING SCHEMA ANALYSIS

### **Base Schema (schema.py)**
```python
"metadata_agent": {
    "report_year": "num",  # ✅ Stores the fiscal year (2023, 2024, etc.)
    "multi_year_metrics": "list",  # ✅ Flexible time series data
}
```

**Pattern**: Uses `report_year` as metadata + flexible lists for time series

### **Synonyms (synonyms.py)**
```python
LOAN_SYNONYMS = {
    "utg.skuld": "loan_amount_current_year",  # ✅ Relative naming!
    "utgående skuld": "loan_amount_current_year",
    "ing.skuld": "loan_amount_previous_year",  # ✅ Relative naming!
    "ingående skuld": "loan_amount_previous_year",
}
```

**Pattern**: Already using `_current_year` and `_previous_year` suffixes!

### **Comprehensive Schema (schema_comprehensive.py - HAS BUGS)**
```python
# ❌ EXISTING HARDCODED YEARS (ALREADY A PROBLEM!)
"electricity_increase_percent_2021_2022": "float"
"heating_increase_percent_2021_2022": "float"
"water_increase_percent_2021_2022": "float"
```

**Discovery**: The existing comprehensive schema ALREADY has this bug! They hardcoded `_2021_2022` which only works for reports comparing those specific years.

---

## 💡 SOLUTION OPTIONS ANALYSIS

### **Option 1: Relative Year Naming** (RECOMMENDED)
```python
# Metadata context
"fiscal_year": int  # 2023, 2024, etc. - THE year this report covers

# Data fields - relative to fiscal_year
"lokaler_revenue_current_year": int      # Report year (e.g., 2023 if fiscal_year=2023)
"lokaler_revenue_prior_year": int        # Year before report (e.g., 2022)
"lokaler_revenue_prior_2_years": int     # 2 years before (e.g., 2021)
```

**Pros**:
- ✅ Works for ANY fiscal year (2015-2030+)
- ✅ Follows existing pattern in synonyms.py
- ✅ Clear semantic meaning (current vs prior)
- ✅ Easy calculations (current - prior = YoY change)
- ✅ Compact schema (3 fields for 3-year trend)

**Cons**:
- ⚠️ Need to join with fiscal_year to get absolute years
- ⚠️ "Current" could be ambiguous (but context makes it clear)

**How It Works**:
```
2024 PDF: fiscal_year=2024
  → lokaler_revenue_current_year = 2024 data
  → lokaler_revenue_prior_year = 2023 data

2020 PDF: fiscal_year=2020
  → lokaler_revenue_current_year = 2020 data
  → lokaler_revenue_prior_year = 2019 data

Same schema fields, different years! ✅
```

---

### **Option 2: Explicit Year Fields (2015-2030)**
```python
"lokaler_revenue_2015": int
"lokaler_revenue_2016": int
# ... one field per year ...
"lokaler_revenue_2030": int
```

**Pros**:
- ✅ Explicit, no ambiguity about which year
- ✅ Easy to query specific years ("show all 2023 data")
- ✅ Natural for multi-year analysis

**Cons**:
- ❌ **Field explosion**: 16 years × 20 metrics = **320 additional fields**!
- ❌ Schema needs updating if we process pre-2015 or post-2030 PDFs
- ❌ Mostly null fields (each PDF has 2-3 years, leaves 13+ years null)
- ❌ Harder to maintain

**Field Count Impact**:
```
Metrics needing year-over-year: ~20 fields
Years to cover (2015-2030): 16 years
Total: 20 × 16 = 320 fields (vs 20 × 3 = 60 with relative naming)
```

---

### **Option 3: Time Series Dictionaries**
```python
"lokaler_revenue": {
    "2020": 1000000,
    "2021": 1050000,
    "2022": 1100000,
    "2023": 1200000
}
```

**Pros**:
- ✅ Most flexible (works for any year, any number of years)
- ✅ Compact schema (1 field instead of N year fields)
- ✅ Natural time series representation

**Cons**:
- ❌ Harder to query in SQL/DataFrames (`json_extract` required)
- ❌ More complex validation (nested structure)
- ❌ Less explicit in schema definition
- ❌ Pydantic validation more complex

---

### **Option 4: Hybrid Approach**
```python
# For most metrics (2-3 years needed)
"lokaler_revenue_current_year": int
"lokaler_revenue_prior_year": int

# For multi-year trends (5+ years)
"multi_year_lokaler_revenue": {
    "2019": 900000,
    "2020": 950000,
    "2021": 1000000,
    "2022": 1050000,
    "2023": 1100000
}
```

**Pros**:
- ✅ Best of both worlds
- ✅ Simple for common case (2-3 years)
- ✅ Flexible for rare multi-year analysis

**Cons**:
- ⚠️ Mixed patterns (some relative, some dictionary)
- ⚠️ More complex to understand

---

## 🎯 RECOMMENDED SOLUTION

### **Adopt Option 1: Relative Year Naming**

**Why**:
1. ✅ **Already used in existing codebase** (synonyms.py has `_current_year`, `_previous_year`)
2. ✅ **Works for 100% of PDFs** regardless of year (2015-2030+)
3. ✅ **Compact** (3 fields vs 320 fields for explicit years)
4. ✅ **Clear semantics** (current vs prior)
5. ✅ **Easy calculations** (YoY change = current - prior)
6. ✅ **Follows BRF reporting convention** (reports always show current + prior year)

### **Naming Convention**

| Old (❌ Hardcoded) | New (✅ Relative) | Alternative Names |
|-------------------|------------------|-------------------|
| `*_2023` | `*_current_year` | `*_fy0`, `*_report_year` |
| `*_2022` | `*_prior_year` | `*_fy1`, `*_prior_1_year` |
| `*_2021` | `*_prior_2_years` | `*_fy2` |
| `*_2020` | `*_prior_3_years` | `*_fy3` |

**Selected Pattern**: `*_current_year`, `*_prior_year`, `*_prior_2_years`
- Clear and readable
- Follows existing synonyms.py convention
- Semantic (describes relationship to report year)

---

## 📋 IMPLEMENTATION IMPACT

### **Fields to Rename**

#### **Category: Lokaler Revenue (property_agent)**
| Old | New |
|-----|-----|
| `lokaler_revenue_2023` | `lokaler_revenue_current_year` |
| `lokaler_revenue_2022` | `lokaler_revenue_prior_year` |

#### **Category: Tomträtt Costs (property_agent)**
| Old | New |
|-----|-----|
| `tomtratt_annual_cost_2023` | `tomtratt_annual_cost_current_year` |
| `tomtratt_annual_cost_2022` | `tomtratt_annual_cost_prior_year` |

#### **Category: Fee Analysis (fees_agent)**
| Old | New |
|-----|-----|
| `fee_increase_count_2023` | `fee_increase_count_current_year` |

#### **Category: Refinancing Risk (loans_agent)**
No year-specific fields (uses `maturity_cluster_date` which is already flexible)

#### **Category: Energy Analysis (energy_agent)**
| Old | New |
|-----|-----|
| `government_energy_support_2023` | `government_energy_support_current_year` |

#### **Category: Depreciation Paradox (key_metrics_agent)**
| Old | New |
|-----|-----|
| `result_without_depreciation_2023` | `result_without_depreciation_current_year` |
| `result_without_depreciation_2022` | `result_without_depreciation_prior_year` |
| `depreciation_as_percent_of_revenue_2023` | `depreciation_as_percent_of_revenue_current_year` |

#### **Category: Cash Crisis (balance_sheet_agent)**
| Old | New |
|-----|-----|
| `total_liquidity_2023` | `total_liquidity_current_year` |
| `total_liquidity_2022` | `total_liquidity_prior_year` |
| `cash_to_debt_ratio_2023` | `cash_to_debt_ratio_current_year` |
| `cash_to_debt_ratio_2022` | `cash_to_debt_ratio_prior_year` |
| `cash_to_debt_ratio_2021` | `cash_to_debt_ratio_prior_2_years` |

**Total Fields to Rename**: ~18 fields

---

## ✅ VERIFICATION AGAINST EXISTING SCHEMA

### **Missing From Base Schema.py**
Base schema uses:
- `report_year`: ✅ Already have this (metadata)
- `multi_year_metrics`: ✅ Could use for 5-year flerårsöversikt

**Our enhancements**: Add specific time-series fields for 2-3 year analysis (more detailed than generic multi_year_metrics)

### **Consistent With Synonyms.py**
Synonyms already use:
- `loan_amount_current_year` ✅
- `loan_amount_previous_year` ✅

**Our enhancements**: Follow same pattern (`*_current_year`, `*_prior_year`)

### **Fix Existing Bugs in Comprehensive Schema**
Comprehensive schema has:
- ❌ `electricity_increase_percent_2021_2022` (HARDCODED!)
- ❌ Should be: `electricity_increase_percent_prior_to_current` or `electricity_yoy_increase_percent`

---

## 🔧 REQUIRED CHANGES

### **Files to Update**
1. ✅ `config/schema_v2_fields.yaml` - Rename 18 fields
2. ✅ `gracian_pipeline/core/schema_comprehensive.py` - Rename field names
3. ✅ `config/comprehensive_schema_v2.json` - Update validation
4. ⚠️ **BONUS**: Fix existing bugs (`electricity_increase_percent_2021_2022` → `electricity_yoy_increase_percent`)

### **Time Estimate**
- Schema updates: 20-30 minutes
- Testing: 10 minutes
- **Total**: 30-40 minutes

---

## 📊 COMPARISON SUMMARY

| Criteria | Relative Naming | Explicit Years | Dictionary | Hybrid |
|----------|----------------|----------------|------------|--------|
| **Works for all years** | ✅ Yes | ⚠️ Only 2015-2030 | ✅ Yes | ✅ Yes |
| **Schema size** | ✅ Compact (60 fields) | ❌ Large (320 fields) | ✅ Compact (20 fields) | ✅ Medium |
| **SQL queryability** | ✅ Easy | ✅ Easy | ❌ Requires json_extract | ⚠️ Mixed |
| **Clarity** | ✅ Clear | ✅ Very explicit | ⚠️ Nested structure | ⚠️ Mixed patterns |
| **Validation complexity** | ✅ Simple | ✅ Simple | ❌ Complex | ⚠️ Mixed |
| **Matches existing patterns** | ✅ Yes (synonyms.py) | ❌ No | ❌ No | ⚠️ Partial |
| **Maintenance** | ✅ Easy | ❌ Needs updates for new years | ✅ Easy | ⚠️ Moderate |

**Winner**: ✅ **Relative Naming** (Option 1)

---

## 🎯 FINAL RECOMMENDATION

**Adopt Relative Year Naming with these suffixes**:
- `_current_year`: The fiscal year being reported (from metadata.report_year)
- `_prior_year`: One year before report year
- `_prior_2_years`: Two years before report year
- `_prior_3_years`: Three years before (if needed for 4-year trends)

**Example**:
```python
# Metadata
"fiscal_year": 2023

# Data fields
"lokaler_revenue_current_year": 1488000  # 2023 data
"lokaler_revenue_prior_year": 1425000    # 2022 data

# When processing 2024 PDF, same schema:
"fiscal_year": 2024
"lokaler_revenue_current_year": 1650000  # 2024 data
"lokaler_revenue_prior_year": 1488000    # 2023 data
```

**Proceed with implementation?**
- Update 3 schema files (~30-40 minutes)
- Fix existing bugs in comprehensive schema (bonus)
- Clean foundation for Week 2+ agent prompts

---

## 🚨 CRITICAL INSIGHT

**User was absolutely right**: Hardcoding years is a fundamental design flaw that would have broken the schema as soon as we process PDFs from different years.

**This catch saved**:
- ❌ Complete schema refactor after Week 2 re-extraction
- ❌ All agent prompts needing updates (would reference wrong years)
- ❌ Failed validation when processing 2024 PDFs
- ❌ Confusion when scaling to 27K PDFs (spanning 10 years)

**Thank you for catching this early!** 🙏
