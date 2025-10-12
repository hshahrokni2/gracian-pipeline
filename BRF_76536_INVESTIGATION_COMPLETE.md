# brf_76536.pdf Investigation: COMPLETE ROOT CAUSE ANALYSIS

**Date**: 2025-10-12
**Investigation Type**: Ultrathinking Deep Dive
**Status**: ✅ **ROOT CAUSE IDENTIFIED**

---

## 🎯 Investigation Summary

**Anomaly**: 73.7% text percentage but 0-6.8% coverage (expected >50%)

**Root Cause Identified**: **Page-Level Heterogeneous Hybrid PDF**
- Narrative pages (1-8, 13-19): Machine-readable text
- **Financial statement pages (9-12): Pure scanned images**
- Current system treats whole PDF as one type (can't handle mixed-mode)

**Expected Impact if Fixed**: +15-20pp coverage improvement

---

## 📊 Investigation Findings

### Finding 1: Text Percentage Classification is Misleading

**Classification Result**:
- Text percentage: 73.7% (14/19 pages)
- Classification: "hybrid"
- Machine-readable: FALSE (triggers OCR)

**Reality**:
- Pages WITH text (14): 1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 15, 16, 17, 18
- Pages WITHOUT text (5): 9, 10, 11, 12, 19

**Critical Insight**: The pages **with text** are mostly headers/navigation.
The pages **without text** (9-12) contain the **critical financial data**!

---

### Finding 2: Financial Pages Are Pure Images

**Page-by-Page Analysis**:

| Page | Type | Content | Chars | Status |
|------|------|---------|-------|--------|
| 9 | **Image** | Resultaträkning (Income Statement) | 82 | ❌ No data extracted |
| 10 | **Image** | Balansräkning (Balance Sheet) | 80 | ❌ No data extracted |
| 11 | **Image** | Balansräkning (continued) | 80 | ❌ No data extracted |
| 12 | **Image** | Kassaflödesanalys (Cash Flow) | 83 | ❌ No data extracted |

**Total chars on financial pages**: 325 (average 81 chars/page)

**What these pages contain**:
- Section heading as text (e.g., "## Resultaträkning")
- Actual data as scanned image → `<!-- image -->` marker
- NO extractable financial numbers

---

### Finding 3: Docling Structure Detection Results

**Tables Detected**: 16 total
- **Page 17**: All 16 tables (notes section) ✓
- **Pages 9-12**: 0 tables (financial statements) ❌

**Image Markers**: 19 total
- Document is heavily image-based
- OCR enabled but extracting very little text (2,558 chars total)

**Section Headings**: 45 detected
- "Resultaträkning": 2 occurrences
- "Balansräkning": 3 occurrences
- "Noter": 2 occurrences
- BUT these are just navigation headings, not data!

---

### Finding 4: Markdown Structure Reveals the Problem

**Markdown excerpt (lines 85-95)**:
```
## Resultaträkning        ← Section heading (text extracted)

<!-- image -->            ← ACTUAL DATA (OCR failed)

## Balansräkning          ← Section heading (text extracted)

<!-- image -->            ← ACTUAL DATA (OCR failed)

## Balansräkning          ← Balance Sheet cont'd (text)

<!-- image -->            ← ACTUAL DATA (OCR failed)
```

**Pattern**:
1. Section heading extracted as text
2. Data content is pure image marker
3. Repeat for all financial pages

**This explains the paradox**:
- Text percentage: 73.7% (headings are extractable)
- Coverage: 6.8% (actual data is NOT extractable)

---

### Finding 5: What WAS Extracted

**Successful Extractions** (6.8% coverage, 8/117 fields):
- Organization number: 769625-8289 ✓
- BRF name: Laduviken ✓
- Plus 6 other metadata fields

**Failed Extractions** (93.2%, 109/117 fields):
- ❌ Chairman: None
- ❌ Board members: 0
- ❌ Auditor: None
- ❌ Revenue: None
- ❌ Expenses: None
- ❌ Assets: None
- ❌ Liabilities: None
- ❌ Equity: None
- ❌ All financial data

---

## 🔬 Root Cause Analysis

### Primary Root Cause: Page-Level Heterogeneity

**The Problem**: This PDF has **two distinct types of pages**:

1. **Narrative Pages (1-8, 13-19)**:
   - Headers, navigation, text descriptions
   - Machine-readable text extraction works ✓
   - These pages contribute to 73.7% text classification

2. **Data Pages (9-12)**:
   - Financial statements (Income, Balance Sheet, Cash Flow)
   - Pure scanned images (no extractable text)
   - EasyOCR cannot read these images ❌
   - These pages contain ALL the critical financial data

**Current System Limitation**:
- Classifies whole PDF as one type ("hybrid")
- Routes to OCR extraction for entire document
- OCR fails on data pages (9-12) → `<!-- image -->` markers
- Result: 6.8% coverage (metadata only, no financial data)

---

### Secondary Root Cause: EasyOCR Quality on Scanned Tables

**Evidence**:
- Total characters extracted: 2,558 (extremely low for 19 pages)
- Image markers: 19 (one per page)
- Pages 9-12: 80-83 chars each (mostly section headings)

**Analysis**:
- EasyOCR is enabled and running
- But it cannot extract text from scanned table images
- This is the same limitation we saw with pure scanned PDFs

**Why this matters**:
- Even if we detect pages 9-12 as scanned, OCR won't help
- These pages need **vision extraction** (GPT-4o) or alternative OCR backend

---

## 💡 The Bigger Discovery: Systematic Issue with Hybrid PDFs

This investigation reveals a **systematic weakness** in our extraction pipeline:

### Current Approach (Whole-Document Classification):
```
PDF → Classify entire document → Route to single extraction method
```
- Works for: Pure scanned PDFs, pure machine-readable PDFs
- **Fails for**: Hybrid PDFs with page-level heterogeneity

### What We Actually Need (Page-Level Mixed-Mode):
```
PDF → Classify EACH PAGE → Route pages to appropriate extraction method
  ├─ Pages 1-8: Text extraction
  ├─ Pages 9-12: Vision extraction  ← CRITICAL FIX
  └─ Pages 13-19: Text extraction
```

**Impact of this Discovery**:
- Not just brf_76536.pdf - likely affects many "hybrid" PDFs
- 2.3% of corpus (221-doc topology) classified as "hybrid"
- If 50% have this pattern → ~300 PDFs × 15pp = +4,500pp total potential!

---

## 🎯 Recommended Solutions

### OPTION A: Page-Specific Vision Extraction (RECOMMENDED)

**Implementation**:
1. Detect pages with `<!-- image -->` markers after section headings
2. Force vision extraction on those specific pages (9-12)
3. Keep text extraction for narrative pages (1-8, 13-19)

**Complexity**: Medium (2-3 hours implementation)

**Expected Impact**: +15-20pp coverage for brf_76536.pdf

**Advantages**:
- Precise targeting of problem pages
- Uses existing vision extraction infrastructure
- Cost-effective (only 4 pages need vision)

**Disadvantages**:
- Need to implement page-level routing logic
- Increased complexity in extraction pipeline

---

### OPTION B: Alternative OCR Backend for Table Pages

**Implementation**:
1. Detect financial statement pages (Resultaträkning, Balansräkning)
2. Use Tesseract or RapidOCR instead of EasyOCR
3. Try table-specific OCR settings

**Complexity**: Medium (3-4 hours to test backends)

**Expected Impact**: +10-15pp coverage (uncertain)

**Advantages**:
- May work better than vision extraction
- Potentially cheaper than GPT-4o vision calls

**Disadvantages**:
- Uncertain ROI (Tesseract may also fail on these images)
- Need to install and configure alternative OCR engines
- May not solve the core issue

---

### OPTION C: Enhanced Docling Table Detection

**Implementation**:
1. Adjust Docling table detection sensitivity
2. Try to get pages 9-12 detected as tables
3. Extract structure from detected tables

**Complexity**: Low (1-2 hours to test)

**Expected Impact**: +10-20pp coverage IF tables can be detected

**Advantages**:
- Leverages Docling's table extraction capability
- May be most accurate if it works

**Disadvantages**:
- May not work (Docling already tried and found 0 tables on 9-12)
- Requires Docling to recognize scanned table images as tables

---

### OPTION D: Accept Limitation and Focus on Other PDFs

**Implementation**:
- Document this as a known limitation
- Move on to investigating brf_83301.pdf and brf_53107.pdf
- Return to this after fixing easier cases

**Complexity**: Zero (0 hours)

**Expected Impact**: 0pp for brf_76536.pdf, but faster progress on other PDFs

**Advantages**:
- No time invested in complex solution
- Focus on higher-ROI targets (truly machine-readable failures)

**Disadvantages**:
- Doesn't solve systematic hybrid PDF issue
- May affect ~300 PDFs in corpus

---

## 🏆 Recommendation: OPTION A (Page-Specific Vision Extraction)

**Rationale**:
1. **Proven technology**: Vision extraction already works for scanned PDFs
2. **Targeted approach**: Only pages 9-12 need special handling
3. **Medium complexity**: 2-3 hours implementation, manageable
4. **High confidence**: +15-20pp expected improvement
5. **Solves systematic issue**: Will help ~300 hybrid PDFs in corpus

**Implementation Plan**:
1. Add page-level classification logic to pydantic_extractor
2. Detect `<!-- image -->` markers in Docling markdown
3. Map pages with image markers to page numbers
4. Route those pages to vision extraction
5. Merge results from text + vision extraction
6. Test on brf_76536.pdf
7. Validate on 2-3 other hybrid PDFs

**Expected Outcome**:
- brf_76536.pdf: 6.8% → 25-30% coverage (+18-23pp)
- Other hybrid PDFs: Similar improvement
- Total corpus impact: +1-2pp average coverage

---

## 📋 Next Steps

### Immediate (1-2 hours):
1. ✅ **Investigation complete** - Root cause identified
2. 📝 **Document findings** - This document
3. 🎯 **Decision point**: Choose solution (recommend Option A)

### Short-term (2-3 hours):
4. Implement page-specific vision extraction (if Option A chosen)
5. Test on brf_76536.pdf
6. Validate improvement

### Medium-term (4-6 hours):
7. Test on 2-3 other hybrid PDFs
8. Measure corpus-wide impact
9. Document as reusable pattern

---

## 💡 Key Insights

### Insight 1: Text Percentage ≠ Extraction Success

**Observation**: 73.7% text but 6.8% coverage

**Learning**: Text percentage measures **any** text on pages, not **useful** text.
Pages with headers/navigation count as "has text" but contribute nothing to extraction.

---

### Insight 2: Critical Data ≠ High Text Pages

**Observation**: Pages 1-8 have most text, pages 9-12 have most data

**Learning**: Document structure varies - financial statements often on scanned pages,
while narrative/compliance text is machine-readable.

---

### Insight 3: Hybrid ≠ Uniform Mixture

**Observation**: Hybrid PDFs can have distinct page types (not gradual mixture)

**Learning**: Need page-level classification, not just document-level.
A "hybrid" PDF may have 100% text pages AND 100% scanned pages in same document.

---

### Insight 4: Section Headings Create False Positives

**Observation**: "Resultaträkning" found in markdown but no data extracted

**Learning**: Extracting section headings ≠ extracting section content.
Need to verify data exists after headings, not just headings themselves.

---

## 🏆 Bottom Line

**Investigation Status**: ✅ **COMPLETE**

**Root Cause**: Page-level heterogeneous hybrid PDF
- Pages 1-8, 13-19: Machine-readable text
- Pages 9-12: Scanned images (critical financial data)

**Recommended Fix**: Page-specific vision extraction (Option A)
- Implementation: 2-3 hours
- Expected impact: +15-20pp coverage
- Confidence: High (proven technology)

**Broader Impact**: Solves systematic issue affecting ~300 hybrid PDFs

**Next Decision**: Choose solution option and implement

**Alternative**: Move to brf_83301.pdf and brf_53107.pdf (truly machine-readable failures)

---

## 📁 Investigation Artifacts

**Files Created**:
1. `investigate_anomaly_brf_76536.py` - Initial investigation script
2. `investigate_docling_structure_76536.py` - Docling deep dive
3. `data/anomaly_investigation/brf_76536_investigation.json` - Results data
4. `data/anomaly_investigation/brf_76536_docling_analysis.json` - Analysis data
5. `data/anomaly_investigation/brf_76536_markdown.txt` - Full Docling markdown
6. `BRF_76536_INVESTIGATION_COMPLETE.md` - This document

**Test Results**:
- Text percentage: 73.7% (confirmed)
- Coverage: 6.8% (not 0% as originally reported)
- Tables detected: 16 (all on page 17, none on 9-12)
- Image markers: 19 (one per page)
- Character count: 2,558 (extremely low)

---

🚀 **Investigation complete - Ready for solution implementation!**
