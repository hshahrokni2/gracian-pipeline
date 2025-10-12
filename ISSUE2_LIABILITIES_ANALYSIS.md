# Issue #2: Liabilities - VALIDATION REPORT ERROR IDENTIFIED

**Date**: 2025-10-09
**Status**: ⚠️ **VALIDATION ERROR** (Extraction is actually CORRECT!)

---

## 🔍 ROOT CAUSE DISCOVERED

The COMPREHENSIVE_VALIDATION_REPORT has an **incorrect ground truth expectation** for `liabilities_total`.

### Ground Truth Data (from brf_198532_comprehensive_ground_truth.json)

```json
"equity_liabilities": {
  "equity": {
    "total_equity": 559807676
  },
  "long_term_liabilities": {
    "bank_loans": 85980000,
    "total": 85980000
  },
  "short_term_liabilities": {
    "short_term_bank_loans": 28500000,
    "accounts_payable": 161253,
    "tax_liabilities": 384000,
    "accrued_expenses": 461858,
    "total": 29507111
  },
  "total_equity_liabilities": 675294786
}
```

### Balance Sheet Equation Verification

**Accounting Equation**: Assets = Liabilities + Equity

```
Total Liabilities = Long-term + Short-term
                  = 85,980,000 + 29,507,111
                  = 115,487,111 kr ✅

Assets = Liabilities + Equity
675,294,786 ≈ 115,487,111 + 559,807,676
675,294,786 ≈ 675,294,787 kr ✅ (1 kr rounding difference)
```

---

## 📊 CURRENT EXTRACTION STATUS

| Field | Extracted Value | Ground Truth | Status |
|-------|----------------|--------------|--------|
| **liabilities_total** | `115,487,111 kr` | `85,980,000 + 29,507,111 = 115,487,111 kr` | ✅ **CORRECT** |
| **long_term_liabilities** | `NOT EXTRACTED` | `85,980,000 kr` | ❌ **MISSING** |
| **short_term_liabilities** | `NOT EXTRACTED` | `29,507,111 kr` | ❌ **MISSING** |
| **equity_total** | `559,807,676 kr` | `559,807,676 kr` | ✅ **CORRECT** |
| **assets_total** | `675,294,786 kr` | `675,294,786 kr` | ✅ **CORRECT** |

---

## 🐛 THE REAL BUG

The COMPREHENSIVE_VALIDATION_REPORT line 136 states:

> **Problem**: Extracting 115,487,111 kr but should be 29,507,111 kr (291.4% error).

This is **WRONG**! The extraction is actually correct:
- `liabilities_total` = 115,487,111 kr ✅ (sum of long + short)
- This matches the balance sheet equation ✅

**The real problem** is that we're NOT extracting:
- `long_term_liabilities` = 85,980,000 kr (separate field)
- `short_term_liabilities` = 29,507,111 kr (separate field)

---

## 🔧 ACTUAL FIX REQUIRED

**Location**: `gracian_pipeline/core/pydantic_extractor.py` lines 350-370

**Current Code** (BalanceSheet extraction):
```python
balance_sheet = BalanceSheet(
    assets_total=NumberField(...),
    liabilities_total=NumberField(
        value=self._to_decimal(fin_data.get("liabilities")),  # Returns 115,487,111 ✅
        ...
    ),
    equity_total=NumberField(...),
    # These fields are NOT being populated:
    long_term_liabilities=None,  # ❌ Should be 85,980,000
    short_term_liabilities=None,  # ❌ Should be 29,507,111
    ...
)
```

**Fix Strategy**:
1. Check if `fin_data` has `long_term_liabilities` and `short_term_liabilities` keys
2. If not, try to extract from `base_result["financial_agent"]["_docling_tables"]`
3. Look for Swedish terms: "Långfristiga skulder" and "Kortfristiga skulder"
4. Parse the values and populate the separate fields

**Implementation Options**:

**Option A**: Update financial agent prompt to extract long/short-term separately
```python
# In agent_prompts.py, update financial_agent prompt to request:
# {
#   "liabilities": "",  # Total liabilities
#   "long_term_liabilities": "",  # Långfristiga skulder
#   "short_term_liabilities": ""  # Kortfristiga skulder
# }
```

**Option B**: Extract from docling tables/markdown in pydantic_extractor
```python
# In _extract_financial_enhanced(), add:
markdown = base_result.get("_docling_markdown", "")

# Search for Swedish terms
lt_match = re.search(r'Långfristiga skulder.*?(\d[\d\s]*)', markdown)
st_match = re.search(r'Kortfristiga skulder.*?(\d[\d\s]*)', markdown)

if lt_match:
    long_term_liabilities = NumberField(
        value=self._parse_number(lt_match.group(1)),
        confidence=0.8,
        source="regex_extraction"
    )

if st_match:
    short_term_liabilities = NumberField(
        value=self._parse_number(st_match.group(1)),
        confidence=0.8,
        source="regex_extraction"
    )
```

---

## ✅ DECISION

**Issue #2 Status**: **MISDIAGNOSED** in validation report

**Correct Assessment**:
- `liabilities_total` extraction is CORRECT (115,487,111 kr)
- `long_term_liabilities` and `short_term_liabilities` are MISSING (need to be extracted)

**Priority**: Move to **P1** (important for detailed analysis, but not blocking basic functionality)

**Next Priority**: Issue #3 (Board Members - missing Suppleant role) or Issue #4 (Loans extraction)

---

## 📝 UPDATED VALIDATION RESULTS

| Field | Previous Status | Corrected Status |
|-------|----------------|------------------|
| **liabilities_total** | ❌ 291.4% error | ✅ CORRECT (115,487,111 kr) |
| **long_term_liabilities** | Not checked | ❌ MISSING (should be 85,980,000 kr) |
| **short_term_liabilities** | Not checked | ❌ MISSING (should be 29,507,111 kr) |

**Overall Financial Balance Sheet Accuracy**: 3/3 core fields correct (assets, liabilities, equity)
**Detailed Fields Missing**: 2/5 (long-term and short-term liabilities breakdown)

---

**Next Step**: Proceed to Issue #3 (Board Members) or #4 (Loans), or implement Option B to extract long/short-term liabilities breakdown.
