# Comprehensive Docling Extraction - All 13 Agents

**Date**: 2025-10-06 12:41:41
**Document**: brf_198532.pdf (BRF Björk och Plaza)
**Method**: Docling + GPT-4o (Single Combined Call)

---

## 📊 **Coverage Summary**

| Metric | Value | Status |
|--------|-------|--------|
| **Total Fields** | 46 | - |
| **Extracted Fields** | 34 | - |
| **Coverage** | **73.9%** | 🔴 BELOW TARGET |
| **Processing Time** | 78.9s | ⚠️ >60s |

---

## 🔍 **Detailed Results by Agent**


### 👤 GOVERNANCE AGENT

**Coverage**: 5/5 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Chairman | Elvy Maria Löfvenberg | ✅ |
| Board Members | 7 items: Elvy Maria Löfvenberg, Torbjörn Andersson, Maria Annelie Eck Arvstrand... | ✅ |
| Auditor Name | Tobias Andersson | ✅ |
| Audit Firm | KPMG AB | ✅ |
| Nomination Committee | 2 items: Victoria Blennborn, Mattias Lovén | ✅ |
| Evidence Pages | [1, 2, 3] | 📍 |


### 💰 FINANCIAL AGENT

**Coverage**: 6/6 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Revenue (SEK) | 7,451,585 | ✅ |
| Expenses (SEK) | 6,631,400 | ✅ |
| Assets (SEK) | 675,294,786 | ✅ |
| Liabilities (SEK) | 115,487,111 | ✅ |
| Equity (SEK) | 559,807,676 | ✅ |
| Surplus (SEK) | -353,810 | ✅ |
| Evidence Pages | [4, 5, 6] | 📍 |


### 🏠 PROPERTY AGENT

**Coverage**: 4/7 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Designation | Sonfjället 2 | ✅ |
| Address | null | ❌ |
| Postal Code | null | ❌ |
| City | Stockholm | ✅ |
| Built Year | 2,015 | ✅ |
| Apartments | 94 | ✅ |
| Energy Class | null | ❌ |
| Evidence Pages | [1, 2] | 📍 |


### 📝 NOTES: DEPRECIATION

**Coverage**: 3/3 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Method | Linjär avskrivning | ✅ |
| Useful Life | 100 år | ✅ |
| Base | Byggnader | ✅ |
| Evidence Pages | [7, 8] | 📍 |


### 📝 NOTES: MAINTENANCE

**Coverage**: 1/2 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Plan | Underhållsplan 2018-2043 | ✅ |
| Budget | null | ❌ |
| Evidence Pages | [9] | 📍 |


### 📝 NOTES: TAX

**Coverage**: 1/3 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Current Tax | null | ❌ |
| Deferred Tax | null | ❌ |
| Tax Policy | Fastighetsavgift och lokalbeskattning | ✅ |
| Evidence Pages | [10] | 📍 |


### 📅 EVENTS AGENT

**Coverage**: 2/3 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Key Events | 5 items: Arbetet med att hävda A-anmärkningar från garantibesiktningen, Hyresgäst Puls & Träning uppköpt av Svenska Nérgy AB, Lån nr 41431520 hos SEB villkorsändrat... | ✅ |
| Maintenance Budget | null | ❌ |
| Annual Meeting Date | 2021-06-08 | ✅ |
| Evidence Pages | [2, 3] | 📍 |


### ✅ AUDIT AGENT

**Coverage**: 3/3 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Auditor | Tobias Andersson | ✅ |
| Opinion | Clean | ✅ |
| Clean Opinion | 1 | ✅ |
| Evidence Pages | [15, 16] | 📍 |


### 💳 LOANS AGENT

**Coverage**: 3/3 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Outstanding Loans (SEK) | 114,480,000 | ✅ |
| Interest Rate (%) | 0.57 | ✅ |
| Amortization (SEK) | 500,000 | ✅ |
| Evidence Pages | [11] | 📍 |


### 💼 RESERVES AGENT

**Coverage**: 1/2 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Reserve Fund (SEK) | 1,026,655 | ✅ |
| Monthly Fee (SEK) | null | ❌ |
| Evidence Pages | [12] | 📍 |


### ⚡ ENERGY AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Energy Class | null | ❌ |
| Performance | null | ❌ |
| Inspection Date | null | ❌ |
| Evidence Pages | [13] | 📍 |


### 💵 FEES AGENT

**Coverage**: 2/3 fields ⚠️

| Field | Value | Status |
|-------|-------|--------|
| Monthly Fee (SEK) | null | ❌ |
| Planned Change | Oförändrade närmaste året | ✅ |
| Fee Policy | Självkostnadsprincipen | ✅ |
| Evidence Pages | [14] | 📍 |


### 💸 CASHFLOW AGENT

**Coverage**: 3/3 fields ✅

| Field | Value | Status |
|-------|-------|--------|
| Cash In (SEK) | 7,641,623 | ✅ |
| Cash Out (SEK) | 5,654,782 | ✅ |
| Cash Change (SEK) | 1,986,840 | ✅ |
| Evidence Pages | [6, 7] | 📍 |


---

## 📈 **Analysis**

🔴 **NEEDS IMPROVEMENT**: 73.9% coverage below 95% target.

### **Strengths**:
- Single combined GPT-4o call captures all agents
- Docling's native table detection extracts financial data
- Swedish-specific prompting preserves exact names
- Evidence pages provided for verification

### **Next Steps**:
1. Validate extracted values against ground truth
2. Test on additional documents (SRS corpus)
3. Identify patterns in missing fields
4. Fine-tune prompts for notes sections

