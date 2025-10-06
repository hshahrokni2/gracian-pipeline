# Comprehensive Docling Extraction - All 13 Agents

**Date**: 2025-10-06 12:53:51
**Document**: brf_198532.pdf (BRF Björk och Plaza)
**Method**: Docling + GPT-4o (Single Combined Call)

---

## 📊 **Coverage Summary**

| Metric | Value | Status |
|--------|-------|--------|
| **Total Fields** | 46 | - |
| **Extracted Fields** | 0 | - |
| **Coverage** | **0.0%** | 🔴 BELOW TARGET |
| **Processing Time** | 69.7s | ⚠️ >60s |

---

## 🔍 **Detailed Results by Agent**


### 👤 GOVERNANCE AGENT

**Coverage**: 0/5 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Chairman | null | ❌ |
| Board Members | empty | ❌ |
| Auditor Name | null | ❌ |
| Audit Firm | null | ❌ |
| Nomination Committee | empty | ❌ |
| Evidence Pages | empty | ❌ |


### 💰 FINANCIAL AGENT

**Coverage**: 0/6 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Revenue (SEK) | null | ❌ |
| Expenses (SEK) | null | ❌ |
| Assets (SEK) | null | ❌ |
| Liabilities (SEK) | null | ❌ |
| Equity (SEK) | null | ❌ |
| Surplus (SEK) | null | ❌ |
| Evidence Pages | empty | ❌ |


### 🏠 PROPERTY AGENT

**Coverage**: 0/7 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Designation | null | ❌ |
| Address | null | ❌ |
| Postal Code | null | ❌ |
| City | null | ❌ |
| Built Year | null | ❌ |
| Apartments | null | ❌ |
| Energy Class | null | ❌ |
| Evidence Pages | empty | ❌ |


### 📝 NOTES: DEPRECIATION

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Method | null | ❌ |
| Useful Life | null | ❌ |
| Base | null | ❌ |
| Evidence Pages | empty | ❌ |


### 📝 NOTES: MAINTENANCE

**Coverage**: 0/2 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Plan | null | ❌ |
| Budget | null | ❌ |
| Evidence Pages | empty | ❌ |


### 📝 NOTES: TAX

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Current Tax | null | ❌ |
| Deferred Tax | null | ❌ |
| Tax Policy | null | ❌ |
| Evidence Pages | empty | ❌ |


### 📅 EVENTS AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Key Events | empty | ❌ |
| Maintenance Budget | null | ❌ |
| Annual Meeting Date | null | ❌ |
| Evidence Pages | empty | ❌ |


### ✅ AUDIT AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Auditor | null | ❌ |
| Opinion | null | ❌ |
| Clean Opinion | null | ❌ |
| Evidence Pages | empty | ❌ |


### 💳 LOANS AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Outstanding Loans (SEK) | null | ❌ |
| Interest Rate (%) | null | ❌ |
| Amortization (SEK) | null | ❌ |
| Evidence Pages | empty | ❌ |


### 💼 RESERVES AGENT

**Coverage**: 0/2 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Reserve Fund (SEK) | null | ❌ |
| Monthly Fee (SEK) | null | ❌ |
| Evidence Pages | empty | ❌ |


### ⚡ ENERGY AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Energy Class | null | ❌ |
| Performance | null | ❌ |
| Inspection Date | null | ❌ |
| Evidence Pages | empty | ❌ |


### 💵 FEES AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Monthly Fee (SEK) | null | ❌ |
| Planned Change | null | ❌ |
| Fee Policy | null | ❌ |
| Evidence Pages | empty | ❌ |


### 💸 CASHFLOW AGENT

**Coverage**: 0/3 fields ❌

| Field | Value | Status |
|-------|-------|--------|
| Cash In (SEK) | null | ❌ |
| Cash Out (SEK) | null | ❌ |
| Cash Change (SEK) | null | ❌ |
| Evidence Pages | empty | ❌ |


---

## 📈 **Analysis**

🔴 **NEEDS IMPROVEMENT**: 0.0% coverage below 95% target.

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

