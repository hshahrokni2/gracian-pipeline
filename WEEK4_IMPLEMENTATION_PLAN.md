# Week 4 Implementation Plan: Path to 95% Coverage

**Generated**: 2025-10-11
**Based on**: Field Coverage Matrix Analysis (43 PDFs, 406 unique fields)
**Current State**: 55.6% document-level coverage, 19.7% field-level coverage
**Target**: 95% coverage (39.4 percentage point gap)

---

## 🎯 Executive Summary

**Key Discovery from Field Coverage Analysis**:
- **406 unique fields** discovered (due to ExtractionField nested structure)
- **296 fields (73%)** have 0% coverage (mostly metadata properties)
- **36 fields** have 80-99% coverage (nearly complete - quick wins)
- **62 fields** have 50-79% coverage (partially working - medium fixes)

**Core Strategy**: Focus on **data fields** (not ExtractionField metadata) using data-driven prioritization from field coverage matrix.

---

## 📊 Field Coverage Matrix Analysis

### Top-Level Statistics
- **Total PDFs Analyzed**: 43
- **Successful Extractions**: 41/43 (95.3%)
- **Average Document Coverage**: 55.6%
- **Average Field-Level Coverage**: 19.7%
- **Fields with 100% coverage**: 0
- **Fields with 0% coverage**: 296

### Critical Missing Fields (Priority Fixes)

#### 🔴 **Tier 1: HIGH PRIORITY** (0% coverage, critical business data)
1. `auditor_report` - 0/43 (Complete auditor report text)
2. `board_report` - 0/43 (Board's management report)
3. `chairman_statement` - 0/43 (Chairman's address)

These are **structured text fields** that require document section extraction enhancement.

#### 🟠 **Tier 2: MEDIUM PRIORITY** (0% coverage, fee details)
4. `fees.annual_fee_per_sqm` - 0/43 + 8 nested ExtractionField properties
5. `fees.arsavgift_per_sqm_total` - 0/43 + 8 nested ExtractionField properties
6. `fees.fee_1_rok` through `fees.fee_5_rok` - 0/43 (Fee breakdown by room count)
7. `fees.fee_calculation_basis` - 0/43
8. `fees.fee_excludes` - 0/43

These are **fee structure details** that may require table parsing enhancement.

#### 🟡 **Tier 3: LOW PRIORITY** (0% coverage, optional fields)
9. `environmental` - 0/43 (Environmental initiatives)
10. `events` - 0/43 (Significant events during fiscal year)

---

## 📋 Week 4 Day-by-Day Plan

### **Week 4 Day 1-2: Tier 1 Quick Wins (50-80% Coverage Fields)**
**Estimated Time**: 8-12 hours
**Target**: Improve 62 fields from 50-79% to 85%+ coverage

#### Task Card #1: Governance Fields Enhancement (4 hours)
**Problem**: Board members showing 81.4% coverage (35/43 PDFs)
- **Root Cause**: 8 PDFs missing board member extraction
- **Fix Strategy**:
  1. Analyze failed PDFs to identify common patterns
  2. Add fallback synonyms for Swedish board member terminology
  3. Improve section detection for governance pages

**Files to Modify**:
- `gracian_pipeline/prompts/agent_prompts.py` (governance_agent prompt)
- `gracian_pipeline/core/synonyms.py` (add board member variations)

**Success Criteria**: Board members coverage 85%+ (37/43 PDFs)

#### Task Card #2: Metadata Completeness (2 hours)
**Problem**: `metadata.organization_number.evidence_pages` at 81.4% (35/43)
- **Root Cause**: Evidence pages not being tracked for organization number
- **Fix Strategy**:
  1. Update metadata extraction to capture source pages
  2. Ensure ExtractionField objects properly populate evidence_pages

**Files to Modify**:
- `gracian_pipeline/core/pydantic_extractor.py` (_extract_metadata method)

**Success Criteria**: Metadata evidence tracking at 95%+ (41/43 PDFs)

#### Task Card #3: Auditor Information (2 hours)
**Problem**: `governance.primary_auditor` at 88.4% (38/43)
- **Root Cause**: 5 PDFs missing auditor extraction
- **Fix Strategy**:
  1. Review failed PDFs for auditor placement variations
  2. Add Swedish auditor title synonyms (revisor, auktoriserad revisor, etc.)
  3. Improve fuzzy matching for auditor names

**Files to Modify**:
- `gracian_pipeline/core/synonyms.py` (auditor title variations)
- `gracian_pipeline/prompts/agent_prompts.py` (governance_agent prompt)

**Success Criteria**: Auditor information at 93%+ (40/43 PDFs)

---

### **Week 4 Day 3-4: Tier 2 Structured Text Extraction (Critical Business Data)**
**Estimated Time**: 12-16 hours
**Target**: Extract 3 critical 0% fields (auditor_report, board_report, chairman_statement)

#### Task Card #4: Document Section Text Extraction (8 hours)
**Problem**: Structured text sections (reports, statements) not being extracted at all
- **Root Cause**: No dedicated text extraction beyond field-level data
- **Fix Strategy**:
  1. Create new extraction agent: `structured_text_agent`
  2. Implement section-to-text mapping using Docling markdown output
  3. Store complete section text in ExtractionField.value with page references

**Implementation Steps**:
1. **Create structured_text_agent** (2 hours)
   - Add to `agent_prompts.py`
   - Define schema in `schema_comprehensive.py`
   - Prompt should extract: auditor_report, board_report, chairman_statement

2. **Enhance Docling Adapter** (4 hours)
   - Modify `docling_adapter_ultra_v2.py` to preserve section text
   - Map Docling sections to schema fields
   - Implement text boundary detection (page start/end)

3. **Integration Testing** (2 hours)
   - Test on 5-PDF sample
   - Validate text completeness and accuracy
   - Check page reference accuracy

**Files to Modify**:
- `gracian_pipeline/prompts/agent_prompts.py` (add structured_text_agent)
- `gracian_pipeline/core/schema_comprehensive.py` (add text fields to schema)
- `gracian_pipeline/core/docling_adapter_ultra_v2.py` (section text extraction)

**Success Criteria**:
- Auditor report extracted: 35/43+ PDFs (80%+)
- Board report extracted: 35/43+ PDFs (80%+)
- Chairman statement extracted: 30/43+ PDFs (70%+)

---

### **Week 4 Day 5: Tier 3 Fee Structure Deep Dive (Medium Priority)**
**Estimated Time**: 6-8 hours
**Target**: Improve fee field coverage from 0% to 60%+

#### Task Card #5: Fee Table Parsing Enhancement (6 hours)
**Problem**: Fee breakdown fields completely missing (0% coverage)
- **Root Cause**: Fee tables not being parsed or data not mapped to schema
- **Fix Strategy**:
  1. Analyze fee table structures across PDFs
  2. Enhance Docling table parsing for fee-specific patterns
  3. Map parsed fee data to schema fields

**Implementation Steps**:
1. **Fee Table Analysis** (2 hours)
   - Sample 10 PDFs with fee tables
   - Document common table structures
   - Identify Swedish fee terminology patterns

2. **Enhanced Fee Extraction** (3 hours)
   - Create dedicated fee table parser
   - Map to schema fields: annual_fee_per_sqm, fee_1_rok-5_rok, etc.
   - Handle Swedish number formats

3. **Testing & Validation** (1 hour)
   - Test on 5-PDF sample
   - Validate numeric accuracy
   - Check unit conversions (kr vs tkr vs million)

**Files to Modify**:
- `gracian_pipeline/core/docling_adapter_ultra_v2.py` (fee table parsing)
- `gracian_pipeline/core/synonyms.py` (fee terminology)
- `gracian_pipeline/models/brf_schema.py` (fee field validation)

**Success Criteria**: Fee structure coverage at 60%+ (26/43 PDFs)

---

## 🎯 Expected Impact by End of Week 4

### Coverage Improvement Projections

| Tier | Fields Targeted | Current Coverage | Target Coverage | Expected Gain |
|------|----------------|------------------|-----------------|---------------|
| **Tier 1** | 62 fields (50-79%) | 50-79% | 85%+ | +10-35 percentage points per field |
| **Tier 2** | 3 fields (0%) | 0% | 80%+ | +80 percentage points per field |
| **Tier 3** | 10 fee fields (0%) | 0% | 60%+ | +60 percentage points per field |

### Overall Impact
- **Before Week 4**: 55.6% document-level coverage
- **After Week 4 (Conservative)**: **72-78% document-level coverage**
- **After Week 4 (Optimistic)**: **78-85% document-level coverage**
- **Remaining Gap to 95%**: 10-23 percentage points

---

## 🔬 Data-Driven Approach: Why This Works

### Evidence from Field Coverage Matrix
1. **36 fields at 80-99% coverage** → Small tweaks yield high ROI
2. **62 fields at 50-79% coverage** → Partially working, just need refinement
3. **296 fields at 0% coverage** → Mostly ExtractionField metadata (not business data)

### Key Insight
The 19.7% field-level coverage is **artificially low** because it includes ExtractionField metadata properties (`extraction_timestamp`, `model_used`, `validation_status`, etc.) which are intentionally null in many cases.

**Actual data field coverage is much higher** (55.6% document-level), and focusing on the **Top 75 missing data fields** will bridge most of the gap to 95%.

---

## 🚨 Risk Mitigation

### Risk #1: Scope Creep
**Mitigation**: Strict focus on Top 75 fields only. Defer remaining 221 low-priority fields to Week 5+.

### Risk #2: PDF Variability
**Mitigation**: Test fixes on diverse PDFs (Hjorthagen + SRS datasets) to ensure robustness.

### Risk #3: Schema Breaking Changes
**Mitigation**: All changes must pass existing validation tests (test_base_fields.py, test_pydantic_extraction.py).

---

## 📝 Implementation Checklist

### Pre-Week 4 (Preparation)
- [x] Generate field coverage matrix
- [x] Analyze top 30 missing fields
- [x] Create Week 4 implementation plan
- [ ] Review current extraction pipeline architecture
- [ ] Set up test harness for rapid iteration

### Week 4 Day 1-2
- [ ] Task Card #1: Governance fields enhancement
- [ ] Task Card #2: Metadata completeness
- [ ] Task Card #3: Auditor information
- [ ] Run 5-PDF smoke test after each task
- [ ] Document changes in git commits

### Week 4 Day 3-4
- [ ] Task Card #4: Structured text extraction (3 sub-tasks)
- [ ] Run 10-PDF validation test
- [ ] Update CLAUDE.md with new agent documentation

### Week 4 Day 5
- [ ] Task Card #5: Fee table parsing enhancement
- [ ] Run comprehensive 42-PDF test suite
- [ ] Generate Week 4 completion report
- [ ] Create Week 5 plan based on remaining gaps

---

## 📊 Success Metrics (End of Week 4)

### Quantitative Targets
- **Document-Level Coverage**: 72%+ (from 55.6%)
- **Field-Level Coverage**: 35%+ (from 19.7%)
- **Critical Business Data**: 80%+ (auditor_report, board_report, chairman_statement)
- **Fee Structure Data**: 60%+ (fee breakdown fields)

### Qualitative Targets
- All 43 PDFs pass validation engine checks (no critical errors)
- Test suite passes 100% (no regressions)
- Code coverage >80% for new modules
- Documentation updated for all new features

---

## 🔄 Next Steps After Week 4

### Week 5: Environmental & Events Fields (Optional Fields)
- Target remaining 0% coverage fields (environmental, events)
- Enhance multi-year financial comparison
- Implement calculated metrics validation

### Week 6: Production Hardening
- Performance optimization (reduce processing time)
- Error recovery and retry logic
- Monitoring and alerting setup
- Production deployment on 26,342-PDF corpus

---

**Plan Generated**: 2025-10-11
**Based on**: FIELD_COVERAGE_MATRIX_REPORT.md
**Next Review**: End of Week 4 Day 2 (re-assess progress and adjust)
