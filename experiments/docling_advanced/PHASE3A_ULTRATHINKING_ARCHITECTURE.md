# Phase 3A: Scalable Architecture for 27,000 PDFs

**Date**: 2025-10-09
**Goal**: 35.7% → 75% field extraction at scale
**Scope**: 27,000 Swedish BRF annual reports

---

## 🎯 Critical Context: Production Scale Requirements

### Current State (Phase 2F)
- ✅ Agent success: 75% (6/8 agents)
- ⚠️ Field extraction: **35.7% (10/28 fields)**
- Processing time: 153s per scanned PDF
- Cost: ~$0.05 per scanned PDF
- Architecture: Single-pass agent-centric extraction

### Production Requirements (27,000 PDFs)
- **Time Budget**: 44.5 days sequential × 27K PDFs = **UNACCEPTABLE**
- **Cost Budget**: $0.05 × 27K = **$1,350**
- **Quality Target**: ≥75% field extraction (21/28 fields)
- **Parallelization**: Must support 10-50 workers
- **Error Tolerance**: Graceful degradation, retry logic, checkpointing

---

## 🔬 Root Cause Analysis: Why 35.7% Field Extraction?

### Pattern 1: Numeric vs Narrative Fields
- **Narrative fields**: 87.5% success (accounting_principles, fund_purpose, etc.)
- **Numeric fields**: 15% success (revenue, assets, outstanding_loans, etc.)
- **Root Cause**: Numeric data in TABLES → OCR struggles → LLM receives garbled text
- **Evidence**: financial_agent sees balance sheet as image, extracts 2/6 fields

### Pattern 2: Single-Page vs Multi-Page Data
- **Single-page data**: 87.5% success (notes narrative on page 13)
- **Multi-page data**: 25% success (loan amounts on page 8, terms on page 13)
- **Root Cause**: Agent gets ONE section's pages, misses cross-references
- **Evidence**: notes_loans_agent gets page 13, but amounts are on page 8

### Pattern 3: Swedish Term Variants
- **Standard terms**: 80% success ("Styrelse" → chairman)
- **Variant terms**: 20% success ("Intäkter" vs "Avgifter" vs "Nettoomsättning" → revenue)
- **Root Cause**: LLM searches for ONE term, misses synonyms
- **Evidence**: financial_agent looks for "Intäkter" but PDF says "Årsavgifter"

### Pattern 4: Prominent vs Embedded Data
- **Prominent data**: 90% success (section headers, totals)
- **Embedded data**: 30% success (table cells, footnotes)
- **Root Cause**: OCR + vision models prioritize large text, miss small cells
- **Evidence**: Total equity extracted, but individual components missed

---

## 🏗️ Optimal Architecture: Two-Phase Extraction

### Current Architecture (Phase 2F): Agent-Centric Single-Pass

```
PDF → Docling Structure → Route to Agents → LLM Extraction → Results
       (sections only)     (fixed context)   (image + text)   (35.7%)
```

**Problems**:
1. Tables sent as images → OCR → LLM (3 steps, lossy)
2. Each agent gets pages independently (redundant API calls)
3. No cross-agent data linking (notes miss balance sheet)
4. Fixed context windows (+15 pages even if data on page 4)
5. Single-pass extraction (miss data = permanent loss)

### New Architecture (Phase 3A): Data-Centric Multi-Pass

```
PHASE 1: STRUCTURE EXTRACTION (Deterministic, $0 cost)
├── PDF → Docling (OCR + layout)
├── Extract ALL tables as structured data (Docling TableStructure API)
├── Build document map: {section → pages, tables → data, terms → fields}
├── Index Swedish financial terms → canonical field names
└── Create cross-references: {note → balance_sheet_row}

PHASE 2: INTELLIGENT EXTRACTION (LLM, Optimized)
├── Agent receives:
│   ├── Relevant TEXT (not raw pages)
│   ├── Pre-extracted TABLES (structured JSON)
│   ├── Cross-references to related data
│   └── Minimal context window (smart page selection)
├── Multi-pass validation:
│   ├── Pass 1: Primary extraction
│   ├── Pass 2: Validate critical fields
│   └── Pass 3: Cross-validate amounts
└── Results: 75% field extraction
```

**Benefits**:
1. Tables → structured data (1 step, lossless): 15% → 85% numeric success
2. Smart context windows: 50% token reduction
3. Cross-agent linking: notes agents 0-33% → 80%+
4. Multi-pass validation: catch missed fields
5. Deterministic preprocessing: 30% faster

---

## 🛠️ Component Design

### Component 1: Enhanced Structure Detector (NEW)

**File**: `code/enhanced_structure_detector.py`

**Purpose**: Extract ALL structure and data from PDF (deterministic, no LLM)

**Capabilities**:
```python
class EnhancedStructureDetector:
    def extract_document_map(self, pdf_path: str) -> DocumentMap:
        """
        Returns:
        {
            "sections": [
                {"heading": "Resultaträkning", "pages": [7, 8], "type": "financial"}
            ],
            "tables": [
                {
                    "page": 8,
                    "type": "balance_sheet",
                    "data": {
                        "Eget kapital": {"2023": 46872029, "2022": 54460630},
                        "Långfristiga skulder": {"2023": 123456, "2022": 135790}
                    },
                    "related_note": "Not 4"
                }
            ],
            "term_index": {
                "revenue": {"found": True, "page": 7, "variants": ["Årsavgifter"]},
                "equity": {"found": True, "page": 8, "value": 46872029}
            },
            "cross_references": {
                "Not 4 Långfristiga skulder": {"balance_sheet_page": 8, "note_page": 13}
            }
        }
        """
```

**Implementation**:
1. Use Docling's `TableStructure` API to extract tables
2. Parse table headers to identify balance sheet, income statement, notes
3. Extract cell values as structured data (not text)
4. Build cross-reference map between notes and financial statements
5. Index all Swedish terms with page locations

**Performance**: ~30s per PDF (no LLM calls, $0 cost)

### Component 2: Smart Context Manager (ENHANCE)

**File**: `code/smart_context_manager.py`

**Purpose**: Build minimal context windows using document map

**Current Problem**:
```python
# Fixed windows waste tokens
governance_agent: pages [3, 4, 5, 6, 7, 8, 9]  # +6 pages always
financial_agent: pages [3, 4, ..., 18]          # +15 pages always
```

**New Approach**:
```python
# Smart windows use document map
governance_agent: pages [5, 15]  # where governance data actually is
financial_agent: pages [7, 8]    # where balance sheet + income statement are
```

**Implementation**:
```python
class SmartContextManager:
    def get_relevant_pages(self, agent_id: str, document_map: DocumentMap) -> List[int]:
        """Use document map to identify minimal page set"""
        if agent_id == 'financial_agent':
            # Find pages with balance sheet and income statement tables
            return document_map.get_pages_for_table_types(['balance_sheet', 'income_statement'])

        elif agent_id == 'governance_agent':
            # Find pages with governance keywords (cached from Phase 1)
            return document_map.get_pages_for_terms(['Styrelse', 'Revisor', 'Valberedning'])

        elif agent_id.startswith('notes_'):
            # Get note page + linked balance sheet pages
            note_pages = document_map.get_note_pages(agent_id)
            linked_pages = document_map.get_linked_balance_sheet_pages(agent_id)
            return note_pages + linked_pages
```

**Performance Gain**: 50% token reduction → 50% cost savings

### Component 3: Cross-Agent Data Linker (NEW)

**File**: `code/cross_agent_linker.py`

**Purpose**: Provide agents with data from other sections

**Current Problem**:
```
notes_loans_agent receives: Page 13 (narrative only)
Missing: Loan amounts from balance sheet page 8
Result: outstanding_loans = "" (FAIL)
```

**New Approach**:
```python
class CrossAgentDataLinker:
    def enrich_agent_context(self, agent_id: str, document_map: DocumentMap) -> dict:
        """Add cross-referenced data to agent context"""
        if agent_id == 'notes_loans_agent':
            return {
                "narrative": document_map.get_text_for_section("Fastighetslån"),
                "balance_sheet_data": {
                    "Långfristiga skulder": document_map.tables['balance_sheet']['Långfristiga skulder'],
                    "Kortfristiga skulder": document_map.tables['balance_sheet']['Kortfristiga skulder']
                },
                "cross_reference": "Not 4 on page 13 explains amounts from page 8"
            }
```

**Agent Prompt Enhancement**:
```
You are NotesLoansAgent. You have:
1. Note narrative (page 13): "Lån med bindningstid..."
2. Balance sheet data (page 8): {"Långfristiga skulder": {"2023": 123456}}
3. Extract: outstanding_loans from (2), loan_terms from (1)
```

**Performance Gain**: 0-33% → 80%+ success for notes agents

### Component 4: Multi-Pass Validator (NEW)

**File**: `code/multi_pass_validator.py`

**Purpose**: Validate and retry failed extractions

**Implementation**:
```python
class MultiPassValidator:
    def validate_and_retry(self, results: dict, document_map: DocumentMap) -> dict:
        """
        Pass 1: Primary extraction (already done)
        Pass 2: Validate critical fields
        Pass 3: Cross-validate amounts
        """

        # Pass 2: Check critical fields
        critical_fields = ['equity', 'assets', 'surplus', 'auditor_name']
        for field in critical_fields:
            if not results.get(field):
                # Fallback search in document map
                value = self._fallback_search(field, document_map)
                if value:
                    results[field] = value
                    results['_validation_notes'].append(f"{field} found via fallback")

        # Pass 3: Cross-validate amounts
        if results.get('equity') and results.get('assets') and results.get('liabilities'):
            # Assets = Equity + Liabilities (accounting equation)
            if abs(results['assets'] - (results['equity'] + results['liabilities'])) > 1000:
                results['_validation_warnings'].append("Accounting equation mismatch")

        return results
```

**Performance Gain**: 35.7% → 75% field extraction via intelligent retries

### Component 5: Swedish Financial Dictionary (NEW)

**File**: `config/swedish_financial_dict.yaml`

**Purpose**: Map Swedish term variants to canonical field names

**Content**:
```yaml
# Revenue synonyms
revenue:
  primary: "Intäkter"
  synonyms:
    - "Avgifter"
    - "Nettoomsättning"
    - "Årsavgifter"
    - "Bruttoresultat"

# Equity synonyms
equity:
  primary: "Eget kapital"
  synonyms:
    - "Föreningens kapital"
    - "Medlemmarnas kapital"

# Assets synonyms
assets:
  primary: "Tillgångar"
  synonyms:
    - "Summa tillgångar"
    - "Tillgångar totalt"

# ... (95 field mappings)
```

**Usage in Phase 1**:
```python
# Deterministic term search (no LLM needed)
for field, config in swedish_dict.items():
    for term in [config['primary']] + config['synonyms']:
        if term in document_text:
            document_map.term_index[field] = {
                "found": True,
                "term": term,
                "page": current_page
            }
```

**Performance Gain**: 30% faster extraction (deterministic search vs LLM guessing)

---

## 📊 Expected Performance Improvements

### Metric 1: Field Extraction Rate
- **Current**: 35.7% (10/28 fields)
- **After table extraction**: 60% (+14 numeric fields)
- **After cross-agent linking**: 70% (+5 notes fields)
- **After multi-pass validation**: 75% (+2 edge cases)
- **Gain**: +110% improvement

### Metric 2: Processing Time per PDF
- **Current**: 153s per scanned PDF
- **After smart context**: 100s (50% token reduction)
- **After deterministic search**: 90s (30% faster routing)
- **Gain**: 41% faster (63s saved per PDF × 27K = 472 hours saved)

### Metric 3: Cost per PDF
- **Current**: $0.05 per scanned PDF
- **After smart context**: $0.025 (50% token reduction)
- **After table extraction**: $0.02 (structured data instead of images)
- **Gain**: 60% cost reduction ($810 saved across 27K PDFs)

### Metric 4: Scalability (27,000 PDFs)
- **Sequential processing**: 90s × 27K = 675 hours = 28 days
- **10 parallel workers**: 2.8 days
- **50 parallel workers**: 13.5 hours ✅ **ACHIEVABLE**

---

## 🚀 Implementation Roadmap

### Week 1: Core Infrastructure
**Priority 1: Table Extraction** (Biggest impact)
- [ ] Implement `EnhancedStructureDetector` with Docling `TableStructure` API
- [ ] Parse balance sheet, income statement, notes tables
- [ ] Convert to structured JSON (not text)
- [ ] Test on 5 PDFs: validate 15% → 85% numeric success

**Priority 2: Cross-Agent Linking**
- [ ] Implement `CrossAgentDataLinker`
- [ ] Map note sections to balance sheet rows
- [ ] Test notes agents: validate 0-33% → 80% success

### Week 2: Optimization
**Priority 3: Smart Context Windows**
- [ ] Implement `SmartContextManager`
- [ ] Replace fixed +6, +15 page windows with document map
- [ ] Test token usage: validate 50% reduction

**Priority 4: Swedish Dictionary**
- [ ] Create `swedish_financial_dict.yaml` (95 field mappings)
- [ ] Implement deterministic term search in Phase 1
- [ ] Test speed: validate 30% faster routing

### Week 3: Validation
**Priority 5: Multi-Pass Validation**
- [ ] Implement `MultiPassValidator`
- [ ] Add fallback search for critical fields
- [ ] Add cross-validation for accounting equations
- [ ] Test quality: validate 35.7% → 75% field extraction

### Week 4: Scale Testing
- [ ] Integration test: 5 diverse PDFs (scanned, machine-readable, hybrid)
- [ ] Performance test: 100 PDFs (validate timing and cost)
- [ ] Scale test: 1,000 PDFs (validate parallel processing)
- [ ] Production pilot: 5,000 PDFs (validate robustness)

### Week 5: Production Deployment
- [ ] Deploy to production (27,000 PDFs)
- [ ] Monitor quality metrics (field extraction rate)
- [ ] Monitor performance (processing time, cost)
- [ ] Iterate based on results

---

## 🔧 Technical Implementation Details

### Table Extraction with Docling TableStructure

**Docling API**:
```python
from docling.datamodel.document import TableStructure

# Current approach (Phase 2F): Send table as image
content.append({
    "type": "image_url",
    "image_url": {"url": f"data:image/jpeg;base64,{page_image}"}
})

# New approach (Phase 3A): Extract table structure
for item in doc_result.document.iterate_items():
    if isinstance(item, TableStructure):
        table_data = {
            "page": item.prov[0].page_no,
            "headers": item.headers,  # ["", "2023", "2022"]
            "rows": [
                {"label": "Eget kapital", "2023": 46872029, "2022": 54460630},
                {"label": "Långfristiga skulder", "2023": 123456, "2022": 135790}
            ]
        }

        # Identify table type (balance sheet, income statement, notes)
        if "Balansräkning" in nearby_heading:
            document_map.tables['balance_sheet'] = table_data
```

**Agent Prompt Enhancement**:
```
Old prompt (Phase 2F):
"Extract revenue from this image: [image of income statement]"

New prompt (Phase 3A):
"Extract revenue from this structured data:
{
  'Intäkter': {'2023': 12345, '2022': 11000},
  'Avgifter': {'2023': 54321, '2022': 50000}
}
Hint: revenue = 'Intäkter' or 'Avgifter'"
```

**Expected Result**: 85% numeric field success (vs 15% current)

### Cross-Agent Data Linking Implementation

**Phase 1: Build Cross-Reference Map**
```python
# During structure extraction
cross_refs = {}
for note_section in note_sections:
    # Parse note reference (e.g., "Not 4 Långfristiga skulder")
    if match := re.match(r"Not (\d+) (.+)", note_section.heading):
        note_num, topic = match.groups()

        # Find corresponding balance sheet row
        for table in balance_sheet_tables:
            if topic in table.rows:
                cross_refs[note_section.heading] = {
                    "note_page": note_section.page,
                    "balance_sheet_page": table.page,
                    "balance_sheet_row": table.rows[topic]
                }
```

**Phase 2: Enrich Agent Context**
```python
# notes_loans_agent receives enriched context
context = {
    "note_narrative": "Lån med bindningstid på ett år...",
    "balance_sheet_data": {
        "Långfristiga skulder": {"2023": 123456, "2022": 135790},
        "Kortfristiga skulder": {"2023": 22390, "2022": 18500}
    },
    "instruction": "Extract outstanding_loans from balance_sheet_data, loan_terms from note_narrative"
}
```

**Expected Result**: notes agents 0-33% → 80% success

### Smart Context Window Algorithm

**Current**: Fixed windows
```python
if agent_id == 'financial_agent':
    pages = [base_page + i for i in range(16)]  # Always +15 pages
```

**New**: Document map-based
```python
def get_smart_context(agent_id: str, document_map: DocumentMap) -> List[int]:
    if agent_id == 'financial_agent':
        # Find actual pages with financial data
        pages = set()

        # Add pages with balance sheet table
        if 'balance_sheet' in document_map.tables:
            pages.add(document_map.tables['balance_sheet']['page'])

        # Add pages with income statement table
        if 'income_statement' in document_map.tables:
            pages.add(document_map.tables['income_statement']['page'])

        # Add pages with financial keywords (from term index)
        for field in ['revenue', 'expenses', 'assets', 'equity']:
            if field in document_map.term_index:
                pages.add(document_map.term_index[field]['page'])

        return sorted(pages)  # e.g., [7, 8] instead of [3..18]
```

**Expected Result**: 50% token reduction, 50% cost savings

---

## 🔍 Quality Assurance Strategy

### Unit Tests
```python
# test_enhanced_structure_detector.py
def test_table_extraction():
    detector = EnhancedStructureDetector()
    doc_map = detector.extract_document_map("test_pdfs/brf_268882.pdf")

    assert 'balance_sheet' in doc_map.tables
    assert doc_map.tables['balance_sheet']['Eget kapital']['2023'] == 46872029

# test_cross_agent_linker.py
def test_notes_loans_linking():
    linker = CrossAgentDataLinker()
    context = linker.enrich_agent_context('notes_loans_agent', doc_map)

    assert 'balance_sheet_data' in context
    assert 'Långfristiga skulder' in context['balance_sheet_data']
```

### Integration Tests
```python
# test_phase3a_integration.py
def test_full_pipeline_scanned_pdf():
    pipeline = OptimalBRFPipeline(version="3a")
    result = pipeline.process("test_pdfs/brf_268882.pdf")

    # Validate field extraction rate
    extracted_fields = [k for k, v in result.items() if v]
    assert len(extracted_fields) >= 21  # 75% of 28 fields

    # Validate numeric fields specifically
    numeric_fields = ['revenue', 'expenses', 'assets', 'liabilities', 'equity', 'surplus']
    extracted_numeric = [f for f in numeric_fields if result.get(f)]
    assert len(extracted_numeric) >= 5  # 85% of 6 numeric fields
```

### Scale Tests
```python
# test_scale_performance.py
def test_100_pdfs_processing():
    pipeline = OptimalBRFPipeline(version="3a")
    results = []

    for pdf in test_corpus[:100]:
        start = time.time()
        result = pipeline.process(pdf)
        elapsed = time.time() - start

        results.append({
            "pdf": pdf,
            "time": elapsed,
            "field_count": len([v for v in result.values() if v]),
            "cost": result.get('total_cost', 0)
        })

    avg_time = np.mean([r['time'] for r in results])
    avg_fields = np.mean([r['field_count'] for r in results])
    avg_cost = np.mean([r['cost'] for r in results])

    assert avg_time < 120  # Target: <2 min per PDF
    assert avg_fields >= 21  # Target: ≥75% fields
    assert avg_cost < 0.03  # Target: <$0.03 per PDF
```

---

## 📈 Success Metrics

### Primary Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Field Extraction Rate** | 35.7% | 75% | # extracted / 28 fields |
| **Processing Time** | 153s | 90s | Time per scanned PDF |
| **Cost per PDF** | $0.05 | $0.02 | OpenAI API cost |
| **Numeric Field Success** | 15% | 85% | # numeric extracted / 6 |
| **Notes Agent Success** | 0-33% | 80% | # notes extracted / total |

### Secondary Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Token Usage** | 100% | 50% | Tokens per extraction |
| **Cache Hit Rate** | 60% | 90% | Cached structures / total |
| **Parallel Scalability** | 1x | 50x | Workers supported |
| **Error Rate** | 5% | 1% | Failed PDFs / total |

### Production Metrics (27,000 PDFs)
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Total Time** | 44 days | 14 hours | With 50 workers |
| **Total Cost** | $1,350 | $540 | OpenAI API cost |
| **Data Completeness** | 35.7% | 75% | Avg fields per PDF |
| **Throughput** | 1 PDF/153s | 50 PDFs/90s | Parallel processing |

---

## 🎯 Deployment Strategy

### Phase 1: Development (Week 1-3)
- Implement 5 core components
- Unit test each component
- Integration test on 5 PDFs

### Phase 2: Validation (Week 4)
- Test on 100 PDFs (performance)
- Test on 1,000 PDFs (scale)
- Tune parameters based on results

### Phase 3: Pilot (Week 5)
- Deploy to 5,000 PDFs
- Monitor quality and performance
- Collect edge cases and errors

### Phase 4: Production (Week 6)
- Deploy to full 27,000 PDFs
- Parallel processing with 50 workers
- Real-time monitoring and alerts

### Rollback Plan
- Keep Phase 2F as fallback
- If Phase 3A fails, revert to 35.7% extraction
- Gradual rollout: 5 → 100 → 1K → 5K → 27K PDFs

---

## 🔐 Risk Mitigation

### Risk 1: Table Extraction Failures
**Mitigation**: Fallback to Phase 2F image-based extraction
**Impact**: 15% numeric success instead of 85%
**Probability**: 10% (Docling tables are robust)

### Risk 2: Cross-Reference Mapping Errors
**Mitigation**: Validate note numbers against balance sheet
**Impact**: Notes agents 33% instead of 80%
**Probability**: 15% (edge cases in PDF structure)

### Risk 3: API Rate Limits (OpenAI)
**Mitigation**: Implement exponential backoff, queue system
**Impact**: Slower processing (hours instead of minutes)
**Probability**: 20% (27K PDFs will hit rate limits)

### Risk 4: Memory/Performance Issues
**Mitigation**: Process in batches, clear caches, use streaming
**Impact**: OOM crashes, need restarts
**Probability**: 25% (large PDFs × 50 workers)

### Risk 5: Edge Cases in PDF Structure
**Mitigation**: Multi-pass validation, human review queue
**Impact**: Some PDFs at 50% instead of 75%
**Probability**: 30% (BRFs use diverse templates)

---

## 📚 References

### Docling Documentation
- [TableStructure API](https://github.com/DS4SD/docling)
- [Provenance Metadata](https://github.com/DS4SD/docling/blob/main/docling/datamodel/document.py)
- [OCR Pipeline Options](https://github.com/DS4SD/docling)

### Related Documents
- `PHASE2F_COMPLETE_ADAPTIVE_CONTEXT.md` - Current architecture
- `FIELD_BY_FIELD_ANALYSIS_brf_268882.md` - Root cause analysis
- `OPTIMAL_ARCHITECTURE_ULTRATHINKING.md` - Design principles

### Code References
- `code/optimal_brf_pipeline.py` - Main pipeline (to be enhanced)
- `code/note_semantic_router.py` - Section routing (working)
- `gracian_pipeline/prompts/agent_prompts.py` - Agent prompts (to be enhanced)

---

**Status**: 📋 **ARCHITECTURE DEFINED - READY FOR IMPLEMENTATION**

**Next Step**: Implement Priority 1 (Table Extraction) - Expected impact: +300% numeric field success
