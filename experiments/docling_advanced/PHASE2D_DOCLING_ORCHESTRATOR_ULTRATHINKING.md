# Phase 2D: Docling-Based Orchestrator - ULTRATHINKING Analysis

**Date**: 2025-10-08
**Status**: 🧠 ULTRATHINKING IN PROGRESS

---

## 🎯 The Paradigm Shift

### What We Were Doing Wrong:
```python
# ❌ WRONG: Search PDF text for sections, then search again for keywords
1. Docling extracts structure → Get section headings
2. Search PDF raw text for headings → Get pages (FAILS on scanned PDFs)
3. Search PDF raw text for keywords → Get pages (FAILS on scanned PDFs)
4. Pass pages to LLM
```

### What We Should Do (User's Insight):
```python
# ✅ RIGHT: Use Docling's structure metadata directly
1. Docling extracts structure → Get sections WITH PAGE NUMBERS
2. Map section headings → agents (semantic routing)
3. Use Docling's page metadata → Pass correct pages to LLM
```

---

## 🔬 Root Cause Analysis (Confirmed)

### Evidence Ratio Problem:
- **Current**: 12.5% (1/8 agents provide evidence_pages)
- **Target**: ≥75% (6-7/8 agents)
- **Root Cause**: Agents receive wrong pages → Can't find data → Return empty

### Why Page Detection Failed:
1. **PyMuPDF Search Fails on Scanned PDFs**:
   - `fitz.open(pdf).page.get_text()` → Returns `""`  for scanned pages
   - Keyword search in empty string → Finds nothing
   - Falls back to heading-based pages [1,2,4,5]

2. **Financial Data on Different Pages**:
   - Heading "Resultaträkning" might be on page 4
   - Actual financial TABLE might be on pages 7-8
   - LLM gets pages [1,2,4,5], doesn't see pages 7-8
   - Returns `evidence_pages: []`

---

## 💡 ULTRATHINKING Solution: Docling Orchestrator

### Key Insight from Docling:
Docling **already** provides page information via:
1. **Provenance metadata**: `item.prov[0].page_no`
2. **Section ranges**: Start/end page for each section
3. **OCR text**: Full text from all pages (not just headings)

### Architecture Redesign:

```python
class DoclingOrchestrator:
    """
    Intelligent orchestrator that uses Docling structure metadata
    instead of searching raw PDF text.
    """

    def route_sections_to_agents(self, doc: DoclingDocument) -> Dict[str, List[int]]:
        """
        Map sections → agents → pages using Docling provenance.

        BEFORE (Text Search):
        - Search PDF text for "Resultaträkning" → page 4
        - Pass page 4 to financial_agent

        AFTER (Provenance-Based):
        - Get section "Resultaträkning" from Docling
        - Extract prov[0].page_no → page 4
        - Get section content span → pages 4-7
        - Pass pages 4-7 to financial_agent
        """
        agent_page_map = {}

        for item, level in doc.iterate_items():
            if isinstance(item, SectionHeaderItem):
                # Get page from provenance (not text search!)
                page_no = item.prov[0].page_no if item.prov else None

                # Map heading to agent
                agent_id = self.semantic_router.classify(item.text)

                # Collect pages for agent
                if agent_id not in agent_page_map:
                    agent_page_map[agent_id] = []
                if page_no is not None:
                    agent_page_map[agent_id].append(page_no)

        return agent_page_map
```

---

## 🔧 Implementation Strategy

### Phase 1: Extract Provenance Data (15 minutes)
**Goal**: Verify Docling provides `prov[0].page_no` for sections

**Current Diagnostic Running**:
```bash
python3 code/debug_docling_pages.py
# Will show: item.prov[0].page_no for each section
```

**Expected Output**:
```
Section #1: Förvaltningsberättelse
  ✅ prov[0].page_no: 1

Section #2: Resultaträkning
  ✅ prov[0].page_no: 7

Section #3: Balansräkning
  ✅ prov[0].page_no: 8
```

### Phase 2: Update detect_structure() (10 minutes)
**Goal**: Preserve provenance page numbers in structure cache

```python
def detect_structure(self, pdf_path: str, topology: PDFTopology) -> StructureDetectionResult:
    # ... existing code ...

    for item, level in doc.iterate_items():
        if isinstance(item, SectionHeaderItem):
            # ENHANCEMENT: Extract page from provenance
            page_no = None
            if item.prov and len(item.prov) > 0:
                page_no = getattr(item.prov[0], 'page_no', None)

            section_info = {
                "heading": item.text,
                "level": level,
                "page": page_no,  # ✅ Now from provenance, not attribute
                "text_preview": item.text[:200] if hasattr(item, 'text') else ""
            }
            sections.append(section_info)
```

### Phase 3: Update _get_pages_for_sections() (15 minutes)
**Goal**: Use provenance data FIRST, text search as fallback

```python
def _get_pages_for_sections(
    self,
    pdf_path: str,
    section_headings: List[str],
    fallback_pages: int = 5,
    agent_id: str = None
) -> List[int]:
    """
    ENHANCED: Use Docling provenance first, then fallbacks.

    Priority:
    1. Docling provenance page numbers (✅ Works on scanned PDFs)
    2. Expand to nearby pages (context around heading)
    3. Text search fallback (machine-readable PDFs only)
    4. First N pages (last resort)
    """
    pages = []

    # Method 1: Use Docling provenance (PRIORITY)
    if hasattr(self, 'structure_cache') and self.structure_cache:
        for heading in section_headings:
            for section in self.structure_cache.sections:
                if section['heading'] == heading and section.get('page') is not None:
                    page = section['page']
                    pages.append(page)

                    # ✅ ENHANCEMENT: Add nearby pages for context
                    # Financial sections often span 2-3 pages
                    if agent_id == 'financial_agent':
                        pages.extend([page+1, page+2])

                    break

    # Method 2: Text search fallback (for machine-readable PDFs)
    if not pages and self.topology.classification == "machine_readable":
        # ... existing text search code ...

    # Method 3: Last resort
    if not pages:
        pages = list(range(min(fallback_pages, self._get_pdf_page_count(pdf_path))))

    return sorted(set(pages))
```

---

## 📊 Expected Improvements

| Metric | Before (Phase 2C) | After (Phase 2D) | Reasoning |
|--------|-------------------|------------------|-----------|
| **Evidence Ratio** | 12.5% | ≥75% | Agents get correct pages with data |
| **Page Detection** | Text search (fails on scanned) | Provenance (works on scanned) | Docling OCR provides page metadata |
| **Financial Agent** | Pages [1,2,4,5], no data | Pages [7,8,9], has tables | Correct page numbers from structure |
| **Overall Score** | 56.2% | ≥87.5% | (100% coverage + 75% evidence) / 2 |

---

## ✅ Success Criteria

**Phase 2D Complete When**:
1. ✅ Provenance extraction verified (diagnostic shows `prov[0].page_no`)
2. ✅ `detect_structure()` captures page numbers from provenance
3. ✅ `_get_pages_for_sections()` uses provenance-based routing
4. ✅ Evidence ratio ≥75% on test document
5. ✅ financial_agent returns populated evidence_pages

---

**Next Action**: Wait for diagnostic (~2 min), then implement provenance-based routing.
