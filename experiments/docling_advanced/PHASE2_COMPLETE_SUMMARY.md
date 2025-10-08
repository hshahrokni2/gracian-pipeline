# Phase 2 Complete Summary - Provenance-Based Routing

**Date**: 2025-10-08
**Status**: ⚠️ IMPLEMENTATION COMPLETE, TESTING IN PROGRESS

---

## 🎯 Achievement Summary

### Phase 2A-2D: Problem Diagnosis Journey ✅

**Phase 2A**: Initial hierarchical extraction with placeholders
**Phase 2B**: Real LLM integration (OpenAI GPT-4o vision)
**Phase 2C**: Evidence tracking fixes (page labels + prompt strengthening)
**Phase 2D**: Keyword search enhancement (failed on scanned PDFs)

### Phase 2E: Provenance-Based Routing Implementation ✅

**Key Insight (User Feedback)**:
> "No, option A is not good for image based if docling works, try to use docling to identify page elements in scanned pages, then an orchestrator that looks at those parts and sends them to the right agent. lets try learn to use the power of docling ultrathink"

**Paradigm Shift**:
- ❌ **Wrong**: Search PDF text for pages → fails on scanned PDFs
- ✅ **Right**: Use Docling provenance metadata → works on scanned PDFs

---

## 🔬 Root Cause Analysis (Confirmed)

### Evidence Ratio Problem
- **Current**: 12.5% (1/8 agents provide evidence_pages)
- **Target**: ≥75% (6-7/8 agents)
- **Root Cause**: Agents receive wrong pages → Can't find data → Return empty

### Why Text Search Failed
1. **PyMuPDF on Scanned PDFs**: `get_text()` returns `""` for scanned pages
2. **Keyword Search Limitation**: Searching empty string → finds nothing
3. **Wrong Page Routing**: Falls back to heading-based pages [1,2,4,5]
4. **Financial Data Elsewhere**: Actual tables on different pages (not seen by LLM)

### Diagnostic Evidence

**Test Document**: `brf_268882.pdf` (scanned)

**Provenance Data (Verified via `debug_docling_pages.py`)**:
```
Section #1: Välkommen... → prov[0].page_no: 2
Section #3: Förvaltningsberättelse → prov[0].page_no: 3
Section #4: Resultaträkning → prov[0].page_no: 3
Section #5: Balansräkning → prov[0].page_no: 3
```

**Current Behavior**:
- governance_agent: receives pages [1,2,4,5] → returns evidence_pages [4,5] ✅
- financial_agent: receives pages [1,2,4,5] → returns evidence_pages [] ❌

---

## 💡 Phase 2E Implementation Details

### Enhancement #1: Provenance Extraction in `detect_structure()`

**File**: `optimal_brf_pipeline.py:368-385`

**BEFORE** (attributes, doesn't work):
```python
section_info = {
    "heading": item.text,
    "level": level,
    "page": getattr(item, 'page', None),  # Always None
}
```

**AFTER** (provenance, works):
```python
# Extract page from provenance metadata
page_no = None
if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
    page_no = getattr(item.prov[0], 'page_no', None)
    if page_no is not None:
        provenance_pages_found += 1

section_info = {
    "heading": item.text,
    "level": level,
    "page": page_no,  # ✅ Now from provenance
}
```

### Enhancement #2: Provenance-First Routing in `_get_pages_for_sections()`

**File**: `optimal_brf_pipeline.py:519-575`

**Priority Order**:
1. ✅ Docling provenance page numbers (works on scanned PDFs)
2. ✅ Add context pages for multi-page sections (e.g., financial +1, +2)
3. ⚠️ Keyword search fallback (machine-readable PDFs only - skip on scanned)
4. ⚠️ First N pages (last resort)

**Code Enhancement**:
```python
# Method 1: Use provenance pages
if hasattr(self, 'structure_cache') and self.structure_cache:
    for heading in section_headings:
        for section in self.structure_cache.sections:
            if section['heading'] == heading and section.get('page') is not None:
                page = section['page']
                pages.append(page)

                # Add nearby pages for context (financial sections span 2-3 pages)
                if agent_id == 'financial_agent':
                    if page + 1 < total_pages:
                        pages.append(page + 1)
                    if page + 2 < total_pages:
                        pages.append(page + 2)

# Method 2-3: SKIP text/keyword search on scanned PDFs
if hasattr(self, 'topology') and self.topology.classification == "machine_readable":
    # ... fallback methods only for machine-readable PDFs
```

### Enhancement #3: Topology Storage

**File**: `optimal_brf_pipeline.py:1138-1139`

```python
# Store topology for access by _get_pages_for_sections()
self.topology = topology
```

---

## 📊 Expected Improvements (Projected)

| Metric | Before (Phase 2D) | After (Phase 2E) | Reasoning |
|--------|-------------------|------------------|--------------|
| **Evidence Ratio** | 12.5% | ≥75% | Agents get correct pages with data |
| **Page Detection** | Text search (fails scanned) | Provenance (works scanned) | Docling OCR provides page metadata |
| **Financial Agent** | Pages [1,2,4,5] (no data) | Pages [3,4,5] (has tables) | Correct page numbers from structure |
| **Overall Score** | 56.2% | ≥87.5% | (100% coverage + 75% evidence) / 2 |

---

## 🧪 Testing Status

### Test #1: Phase 2E Provenance Implementation (In Progress)

**Command**:
```bash
# Clear cache and run fresh test
python3 -c "import sqlite3; conn = sqlite3.connect('results/cache/pipeline_cache.db'); cursor = conn.cursor(); cursor.execute('DELETE FROM structure_cache'); cursor.execute('DELETE FROM topology_cache'); conn.commit(); conn.close()"

timeout 300 python3 code/optimal_brf_pipeline.py test_pdfs/brf_268882.pdf
```

**Status**: ⏳ Running (OCR processing ~90s)

**Expected Diagnostic Output**:
```
STAGE 2: Structure Detection (Docling)
   📄 Converting PDF with Docling (OCR: True)...
   ✅ Structure detected (50 sections, 94.3s)
   Provenance pages: 50/50 (100%)  # ← Verify this appears
```

---

## 🎯 Success Criteria

**Phase 2E Complete When**:
1. ✅ Provenance extraction verified (diagnostic shows `prov[0].page_no`)
2. ✅ `detect_structure()` captures page numbers from provenance
3. ✅ `_get_pages_for_sections()` uses provenance-based routing
4. ⏳ Evidence ratio improves to ≥50% (testing in progress)
5. ⏳ financial_agent returns populated evidence_pages (testing)

---

## 📋 Next Steps

1. **Complete Current Test** (~5 min remaining for OCR)
2. **Analyze Results**: Check if financial_agent now gets correct pages
3. **Verify Page Indexing**: Confirm Docling page_no is 0-indexed or 1-indexed
4. **Document Findings**: Create Phase 2E completion report
5. **Create Documentation**: ULTRATHINKING analysis document

---

## 🔍 Open Questions

### Q1: Page Indexing (CRITICAL)
- **Question**: Is Docling `prov[0].page_no` 0-indexed or 1-indexed?
- **Evidence**: Diagnostic shows `page_no: 2, 3, 3, 3...` (looks 1-indexed)
- **Impact**: If 1-indexed, need to subtract 1 before passing to PyMuPDF
- **Next Step**: Verify with test results

### Q2: Context Page Expansion Strategy
- **Current**: financial_agent gets +1, +2 pages for context
- **Question**: Should other agents also get context pages?
- **Next Step**: Tune based on test results

### Q3: Fallback Strategy for Scanned PDFs
- **Current**: Skip text/keyword search entirely on scanned PDFs
- **Alternative**: Could search Docling OCR markdown instead
- **Trade-off**: More complex vs cleaner implementation
- **Decision**: Keep simple for now, optimize later if needed

---

## 💭 Lessons Learned

### User's Critical Insight
The user redirected from "fix keyword search" to "use Docling's power". This paradigm shift was the breakthrough:
- **Before**: Trying to work around Docling's limitations
- **After**: Leveraging Docling's strengths (provenance metadata)

### Caching Complications
Cache persistence caused test confusion:
- Structure cached from earlier test runs
- SQLite database persists across runs
- Solution: Explicit cache clearing before fresh tests

### Text Search Fundamentals
PyMuPDF `get_text()` returns empty string for scanned pages - this is the fundamental limitation that required the pivot to provenance-based routing.

---

**Status**: Implementation complete, test in progress, analysis pending.
