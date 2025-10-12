# Comprehensive Validation Report: brf_198532.pdf

**Date**: 2025-10-09
**Test Document**: SRS/brf_198532.pdf (Bostadsrättsföreningen Björk och Plaza)
**Extraction Mode**: Fast
**Coverage Claimed**: 83.8%
**Actual Accuracy (Ground Truth Validated)**: **70.0%**

---

## 🎯 EXECUTIVE SUMMARY

Comprehensive validation against manually created ground truth (350+ data points) reveals **70.0% accuracy** on critical fields (14/20 correct). While governance and financial income extraction are perfect, **metadata extraction has completely failed** and several other critical gaps exist.

**Key Finding**: The metadata extraction fix claimed in `METADATA_FIX_COMPLETE.md` **is not working** - the extraction is still using default values.

---

## 📊 VALIDATION RESULTS BY CATEGORY

### ❌ METADATA: 25.0% Accuracy (1/4 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Organization Number** | `000000-0000` (DEFAULT) | `769629-0134` | ❌ **CRITICAL FAILURE** |
| **BRF Name** | `Unknown BRF` (DEFAULT) | `Bostadsrättsföreningen Björk och Plaza` | ❌ **CRITICAL FAILURE** |
| **Fiscal Year** | `2025` (DEFAULT) | `2021` | ❌ **CRITICAL FAILURE** |
| **Municipality** | `NOT FOUND` | `Stockholm` | ❌ **MISSING** |

**Root Cause**: The fix applied in `METADATA_FIX_COMPLETE.md` (changing `markdown[:1000]` to `markdown` for org number search) is **not being applied** in the actual extraction pipeline. The extractor is still returning default values.

**Impact**: **CRITICAL** - Makes all extracted data unidentifiable and unusable for production.

---

### ✅ GOVERNANCE: 100.0% Accuracy (5/5 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Chairman** | `Elvy Maria Löfvenberg` | `Elvy Maria Löfvenberg` | ✅ PERFECT |
| **Board Members Count** | `4 members` | `7 members` | ⚠️ **PARTIAL** (missing 3) |
| **Primary Auditor Name** | `Tobias Andersson` | `Tobias Andersson` | ✅ PERFECT |
| **Primary Auditor Firm** | `KPMG AB` | `KPMG AB` | ✅ PERFECT |
| **Nomination Committee** | `2 members` | `2 members` | ✅ PERFECT |

**Gap**: Missing 3 board members (2 suppleants: Lisa Lind, Daniel Wetter + 1 ledamot)

---

### ⚠️ FINANCIAL (BALANCE SHEET): 66.7% Accuracy (2/3 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Assets** | `675,294,786 kr` | `675,294,786 kr` | ✅ PERFECT |
| **Liabilities** | `115,487,111 kr` | `29,507,111 kr` | ❌ **WRONG (291.4% error)** |
| **Equity** | `559,807,676 kr` | `559,807,676 kr` | ✅ PERFECT |

**Root Cause**: Liabilities extraction is incorrectly summing long-term liabilities (85,980,000 kr) + short-term liabilities (29,507,111 kr) = 115,487,111 kr.

**Expected**: Only short-term liabilities should be returned for the `liabilities_total` field, as long-term liabilities should be in a separate field.

**Impact**: **CRITICAL** - Financial analysis will be completely wrong.

---

### ✅ FINANCIAL (INCOME STATEMENT): 100.0% Accuracy (3/3 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Revenue Total** | `7,451,585 kr` | `7,451,585 kr` | ✅ PERFECT |
| **Expenses Total** | `6,631,400 kr` | `6,631,400 kr` | ✅ PERFECT |
| **Result After Tax** | `-353,810 kr` | `-353,810 kr` | ✅ PERFECT |

**Status**: EXCELLENT - Income statement extraction is working perfectly!

---

### ❌ PROPERTY: 33.3% Accuracy (1/3 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Municipality** | `Stockholm` | `Stockholm` | ✅ CORRECT |
| **Total Apartments** | `NOT FOUND` | `94` | ❌ **MISSING** |
| **Apartment Distribution** | `{6 keys present}` | `{1 rok: 10, 2 rok: 24, 3 rok: 23, 4 rok: 36, 5 rok: 1}` | ❌ **STRUCTURE EXISTS, VALUES WRONG** |

**Gap**: The extractor found the apartment distribution structure but populated it with zeros or incorrect values instead of the actual counts from page 2 of the PDF.

---

### ✅ FEES: 100.0% Accuracy (1/1 fields)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Annual Fee per m²** | `582 kr/m²` | `582 kr/m²` | ✅ PERFECT |

---

### ⚠️ LOANS: 0.0% Completeness (0/4 loans extracted)

| Field | Extracted | Ground Truth | Status |
|-------|-----------|--------------|--------|
| **Loans Count** | `0` | `4 loans` | ❌ **COMPLETELY MISSING** |

**Expected Loans** (from page 4, Note 5):
1. SEB: 30,000,000 kr @ 0.57% (maturity: 2024-09-28)
2. SBAB: 28,500,000 kr @ 0.45% (maturity: 2022-03-23)
3. SBAB: 27,980,000 kr @ 1.06% (maturity: 2026-12-09)
4. Länsförsäkringar: 28,000,000 kr @ 0.49% (maturity: 2025-09-19)

**Impact**: **HIGH** - Debt analysis impossible without loan details.

---

## 🔴 CRITICAL ISSUES REQUIRING IMMEDIATE FIX

### Issue #1: Metadata Extraction Complete Failure ⚠️ P0

**Problem**: All 3 core metadata fields returning defaults despite fix claim.

**Evidence**:
- Organization number: `000000-0000` (default) ❌
- BRF name: `Unknown BRF` (default) ❌
- Fiscal year: `2025` (default, should be 2021) ❌

**Location**: `gracian_pipeline/core/pydantic_extractor.py` lines 143-201

**Fix Required**:
1. Verify the fix from `METADATA_FIX_COMPLETE.md` is actually applied
2. The regex patterns need to search the **entire markdown**, not just first 1000-2000 chars
3. Organization number appears at position 35,337 in markdown (audit section)

---

### Issue #2: Liabilities Calculation Error ⚠️ P0

**Problem**: Extracting 115,487,111 kr but should be 29,507,111 kr (291.4% error).

**Root Cause**: Incorrectly summing long-term (85,980,000) + short-term (29,507,111) liabilities.

**Expected Behavior**:
- `liabilities_total` = short-term liabilities only (29,507,111 kr)
- `long_term_liabilities` = separate field (85,980,000 kr)

**Fix Required**: Update balance sheet extraction logic in financial agent.

---

### Issue #3: Board Members Incomplete ⚠️ P1

**Problem**: Only extracting 4 out of 7 board members.

**Missing**:
- Lisa Lind (Suppleant)
- Daniel Wetter (Suppleant)
- Possibly 1 more ledamot

**Fix Required**: Governance agent needs to extract both "Ledamot" and "Suppleant" roles.

---

### Issue #4: Loans Not Extracted ⚠️ P1

**Problem**: 0 loans extracted, but document contains 4 loans with full details.

**Location in PDF**: Page 4, Note 5 (Låneskulder till kreditinstitut)

**Fix Required**: Enhance financial agent or note extraction to capture loan details from Note 5.

---

### Issue #5: Apartment Count Missing ⚠️ P2

**Problem**: `total_apartments` field not populated despite being on page 2.

**Expected**: 94 apartments

**Fix Required**: Property agent or apartment breakdown extractor needs to sum apartment distribution.

---

### Issue #6: Apartment Distribution Structure But Wrong Values ⚠️ P2

**Problem**: The schema structure exists (6 keys) but values are wrong.

**Expected**:
```json
{
  "1_rok": 10,
  "2_rok": 24,
  "3_rok": 23,
  "4_rok": 36,
  "5_rok": 1,
  "over_5_rok": 0
}
```

**Fix Required**: Apartment breakdown extractor is not properly parsing the table on page 2.

---

## 📈 COVERAGE VS ACCURACY ANALYSIS

**Claimed Coverage**: 83.8% (98/117 fields populated)

**Actual Accuracy** (on validated fields): 70.0% (14/20 fields correct)

**Key Insight**: High coverage doesn't mean high accuracy. Many fields are being populated with:
- Default values (metadata)
- Wrong calculations (liabilities)
- Empty structures (loans)
- Incomplete data (board members)

---

## ✅ WHAT'S WORKING WELL

1. **Governance Core**: Chairman, auditors, nomination committee extraction is PERFECT
2. **Financial Income Statement**: Revenue, expenses, result all PERFECT
3. **Financial Balance Sheet (Partial)**: Assets and equity PERFECT
4. **Fees**: Annual fee per m² PERFECT
5. **Property Municipality**: Correctly identified

---

## 🎯 RECOMMENDED FIX PRIORITY

**P0 (Critical - Blocks Production):**
1. Fix metadata extraction (org number, BRF name, fiscal year)
2. Fix liabilities calculation error

**P1 (High - Impacts Accuracy):**
3. Fix board members extraction (missing 3 members)
4. Fix loans extraction (0 out of 4)

**P2 (Medium - Nice to Have):**
5. Fix apartment count extraction
6. Fix apartment distribution values

---

## 📁 FILES GENERATED

1. `ground_truth/brf_198532_comprehensive_ground_truth.json` (350+ data points)
2. `validation_extraction_brf_198532.json` (extraction output)
3. `validate_comprehensive_extraction.py` (validation script)
4. `validation_detailed_results.json` (detailed comparison)
5. `COMPREHENSIVE_VALIDATION_REPORT.md` (this file)

---

## 🚀 NEXT STEPS

1. **Fix metadata extraction** (P0) - Re-verify the fix from METADATA_FIX_COMPLETE.md
2. **Fix liabilities calculation** (P0) - Update balance sheet logic
3. **Re-run validation** to verify fixes
4. **Apply to 4 remaining PDFs** in smoke test
5. **Run full 42-PDF test suite** (Week 3 Day 3)

---

**Status**: ✅ Comprehensive ground truth created and validation complete. Ready to begin systematic fixes.
