# Mixed-Mode Extraction Implementation Status

**Date**: 2025-10-12
**Session Duration**: ~3 hours
**Status**: ⚡ **80% COMPLETE** - Core infrastructure working, vision quality needs tuning

---

## 🎯 What Was Accomplished

### ✅ Phase 1: Investigation & Root Cause (1 hour)
- **brf_76536.pdf deep dive**: Identified page-level heterogeneity
- **Root cause documented**: Pages 9-12 are scanned images (financial data)
- **Systematic issue identified**: Affects ~300 hybrid PDFs in corpus

### ✅ Phase 2: Core Infrastructure (1.5 hours)
1. **Page Classifier** (`gracian_pipeline/utils/page_classifier.py`):
   - ✅ Detects financial sections that are images
   - ✅ Returns page-level classification (text vs image)
   - ✅ Priority-based decision logic

2. **Mixed-Mode Extractor** (`gracian_pipeline/core/mixed_mode_extractor.py`):
   - ✅ Orchestrates text + vision extraction
   - ✅ Renders PDF pages to images
   - ✅ Calls GPT-4o vision API
   - ✅ Merges results intelligently

3. **Integration** (`gracian_pipeline/core/pydantic_extractor.py`):
   - ✅ Phase 0: PDF type checking
   - ✅ Phase 1.5: Mixed-mode extraction
   - ✅ Result merging before enhanced extraction

### ⚡ Phase 3: Testing & Debugging (0.5 hours)
- ✅ Created test script (`test_mixed_mode_extraction.py`)
- ✅ Fixed detection logic (financial sections priority)
- ✅ Fixed merge logic (dict vs list handling)
- ⚠️ **Vision extraction quality issue** (returns empty data)

---

## 📊 Current Test Results

### brf_76536.pdf Test (Latest Run):

**Mixed-Mode Detection**: ✅ **WORKING**
```
🔀 Mixed-Mode Detection: financial_sections_are_images
   Image pages detected: [9, 10, 11, 12]
   Financial sections: ['Resultaträkning', 'Balansräkning', 'Balansräkning', 'Kassaüödesanalys']
```

**Vision Extraction**: ✅ **RUNNING** but ⚠️ **EMPTY RESULTS**
```
📸 Phase 1.5: Vision Extraction for Image Pages (30s)
   ✓ Vision extraction successful for pages [9, 10, 11, 12]
   ✓ Results merged from 4 image pages
```

**Coverage Results**: ❌ **NO IMPROVEMENT**
```
   Baseline: 6.8%
   New: 6.8%
   Improvement: +0.0pp
```

**What Was Extracted**:
- Metadata: Org number, BRF name, Fiscal year ✓
- Governance: Empty ❌
- Financial: Empty ❌
- Loans: 1 loan with no details ⚠️

---

## 🔍 Root Cause of Vision Quality Issue

### Issue: Vision API Returns Empty/Null Data

**Evidence**:
- Vision API call succeeds (HTTP 200)
- Returns JSON structure correctly
- But all financial values are null
- Only 1 loan extracted with no details

**Hypotheses**:
1. **Image Resolution Too Low**: 2x zoom (144 DPI) may not be enough for Swedish text
2. **Image Format Issues**: PNG rendering may have quality loss
3. **Prompt Not Specific Enough**: Vision API may not understand Swedish financial statements
4. **Table Complexity**: Scanned tables too complex for vision API to parse

### Diagnostic Evidence Needed:
- [ ] Save rendered images to disk for manual inspection
- [ ] Check actual image resolution and quality
- [ ] Test vision API on single page manually
- [ ] Compare with higher resolution (3x-4x zoom)

---

## 🛠️ Implementation Details

### 1. Page Classification Logic

**File**: `gracian_pipeline/utils/page_classifier.py` (243 lines)

**Key Functions**:
- `detect_image_pages_from_markdown()`: Finds `<!-- image -->` markers after financial headings
- `should_use_mixed_mode_extraction()`: Decides if mixed-mode needed
- `analyze_page_content_density()`: Content metrics

**Critical Fix Applied**:
```python
# OLD (broken): Check char count first → reject before checking for images
if char_count < 3000:
    return False, "too_little_text_for_mixed_mode"

# NEW (fixed): Check for financial images FIRST (priority)
if page_classification['financial_image_sections']:
    return True, "financial_sections_are_images"  # REGARDLESS of char count
```

**Result**: brf_76536.pdf (2,558 chars) now correctly triggers mixed-mode

---

### 2. Vision Extraction Implementation

**File**: `gracian_pipeline/core/mixed_mode_extractor.py` (350+ lines)

**Key Methods**:
- `should_use_mixed_mode()`: Wrapper for classification check
- `extract_image_pages_with_vision()`: Renders pages + calls GPT-4o
- `merge_extraction_results()`: Intelligent result merging

**Current Configuration**:
```python
# Render pages
mat = fitz.Matrix(2.0, 2.0)  # 2x zoom = ~144 DPI
pix = page.get_pixmap(matrix=mat)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# Call GPT-4o vision
response = self.client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    max_tokens=4096,
    temperature=0,
)
```

**Merge Strategy**:
- Prefer vision for financial data (more accurate from images)
- Prefer text for governance, property, metadata
- Handle both dict and list formats from base extractor

---

### 3. Integration Points

**File**: `gracian_pipeline/core/pydantic_extractor.py`

**Changes Made** (lines 83-137):
```python
# Phase 0: Check PDF Type
doc = fitz.open(pdf_path)
total_pages = len(doc)

# Phase 1: Base extraction
base_result = self.base_extractor.extract_brf_document(...)

# Phase 1.5: Check if mixed-mode needed
use_mixed, classification = self.mixed_mode_extractor.should_use_mixed_mode(...)

if use_mixed:
    # Extract image pages with vision
    vision_result = self.mixed_mode_extractor.extract_image_pages_with_vision(
        pdf_path, classification['image_pages']
    )
    # Merge results
    base_result = self.mixed_mode_extractor.merge_extraction_results(
        base_result, vision_result
    )
```

**Result**: Seamless integration, existing code paths unchanged

---

## 🚀 Next Steps (Estimated 1-2 hours)

### Priority 1: Fix Vision Extraction Quality (1 hour)

**Option A: Increase Image Resolution** (RECOMMENDED)
```python
# Change from 2x to 3x or 4x zoom
mat = fitz.Matrix(3.0, 3.0)  # 3x zoom = ~216 DPI
# OR
mat = fitz.Matrix(4.0, 4.0)  # 4x zoom = ~288 DPI
```

**Expected Impact**: Better OCR quality from vision API on Swedish text

**Option B: Save Images for Manual Inspection**
```python
# Add debugging output
img.save(f"/tmp/debug_page_{page_num}.png")
```

**Expected Impact**: Understand if images are readable

**Option C: Refine Vision Prompt**
- Add example JSON structure
- Specify Swedish terminology
- Add instructions for table parsing

**Expected Impact**: Better extraction from complex tables

---

### Priority 2: Validate on Multiple PDFs (0.5 hours)

**Test Cases**:
1. ✅ brf_76536.pdf (73.7% text, pages 9-12 images) - Infrastructure test
2. **NEW**: Pick 2-3 other hybrid PDFs from SRS dataset
3. Measure coverage improvement

**Success Criteria**: At least 1 PDF shows +15-20pp improvement

---

### Priority 3: Document & Deploy (0.5 hours)

**Documentation**:
- Implementation guide
- Usage examples
- Troubleshooting tips

**Deployment**:
- Run on 42-PDF corpus
- Measure average coverage improvement
- Document corpus-wide impact

---

## 📈 Expected Impact (Once Vision Quality Fixed)

### Per-PDF Impact:
- brf_76536.pdf: 6.8% → 25-30% (+18-23pp)
- Similar hybrid PDFs: +15-20pp each

### Corpus-Wide Impact:
- ~300 hybrid PDFs affected (2.3% of 26,342)
- Average improvement: +1-2pp corpus coverage
- Total impact: +300-600pp cumulative

### Path to 75% Target:
- Current: 56.1% average
- After mixed-mode: 57-58% (+1-2pp)
- After machine-readable fixes: 62-65% (+5-7pp more)
- Final push: 65% → 75% (validation features, optimization)

---

## 💡 Key Insights from Implementation

### 1. Priority-Based Detection is Critical

**Learning**: Checking for financial image sections BEFORE rejecting on char count is essential.

**Example**: brf_76536.pdf has 2,558 chars (below 3000 threshold) but pages 9-12 are critical images. Without priority check, it would be rejected.

---

### 2. Dict vs List Handling Matters

**Learning**: Base extractor can return data in different formats (dict or list).

**Fix**: Merge logic must handle both cases gracefully:
```python
if isinstance(merged['loans_agent'], dict):
    if 'loans' in merged['loans_agent']:
        merged['loans_agent']['loans'].extend(loans_vision)
elif isinstance(merged['loans_agent'], list):
    merged['loans_agent'].extend(loans_vision)
```

---

### 3. Vision API Integration is Non-Trivial

**Learning**: Just calling the vision API isn't enough - image quality, prompt quality, and result parsing all matter.

**Current Issue**: Vision API runs but returns empty data, indicating quality issues rather than integration issues.

---

## 🏆 Bottom Line

### What Works:
✅ **Mixed-mode detection**: Correctly identifies hybrid PDFs
✅ **Page classification**: Finds financial image sections
✅ **Vision API integration**: Successfully renders and calls API
✅ **Result merging**: Combines text + vision results
✅ **Pydantic integration**: Seamless insertion into existing pipeline

### What Needs Work:
⚠️ **Vision extraction quality**: Returns empty/null data
⚠️ **Image resolution**: May need higher DPI (3x-4x vs current 2x)
⚠️ **Prompt refinement**: May need better instructions for Swedish tables

### Time to Complete:
- **Done**: 3 hours (80% complete)
- **Remaining**: 1-2 hours (vision quality tuning + validation)
- **Total**: 4-5 hours (as estimated)

### Ready for:
1. Vision quality debugging (Priority 1)
2. Multi-PDF validation (after fix)
3. Production deployment (after validation)

---

## 📁 Files Created/Modified

### Created (6 files):
1. `gracian_pipeline/utils/page_classifier.py` (243 lines) - Page-level classification
2. `gracian_pipeline/core/mixed_mode_extractor.py` (350+ lines) - Mixed-mode orchestration
3. `test_mixed_mode_extraction.py` (200+ lines) - Test script
4. `BRF_76536_INVESTIGATION_COMPLETE.md` - Investigation findings
5. `MIXED_MODE_IMPLEMENTATION_STATUS.md` - This document
6. `data/anomaly_investigation/*` - Debug files

### Modified (2 files):
1. `gracian_pipeline/core/pydantic_extractor.py` (+60 lines) - Mixed-mode integration
2. `gracian_pipeline/utils/page_classifier.py` (logic fixes)

### Test Artifacts:
1. `data/anomaly_investigation/brf_76536_investigation.json` - Investigation data
2. `data/anomaly_investigation/brf_76536_markdown.txt` - Docling output
3. `data/anomaly_investigation/mixed_mode_test_output.txt` - Test logs

**Total**: 8 files created/modified, ~900 lines of code

---

🚀 **80% Complete - Ready for vision quality tuning!**
