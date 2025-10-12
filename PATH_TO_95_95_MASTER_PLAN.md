# Path to 95/95 Accuracy - Master Plan

**Target**: Achieve **95% coverage and 95% accuracy** across all 42 test PDFs
**Current State**: 55.9% average coverage (33/42 PDFs tested)
**Gap**: **39.1 percentage points** to close

**Generated**: 2025-10-10 17:00:00
**Status**: Week 3 Day 3 - Planning Phase

---

## 🎯 Current State Analysis

### Test Progress
- **PDFs Tested**: 33/42 (78.6% complete)
- **Success Rate**: 90.9% (30/33 successful, 3 failures)
- **Average Coverage**: 55.9%
- **Average Confidence**: 0.64

### Performance Distribution
| Coverage Range | Count | % | Status |
|----------------|-------|---|--------|
| **80-100%** | 4 | 12.1% | ✅ Excellent |
| **60-79%** | 21 | 63.6% | ✅ Good |
| **1-19%** | 5 | 15.2% | ⚠️ Needs improvement |
| **0%** | 3 | 9.1% | ❌ Critical failures |

### Top Performers (Benchmark Targets)
1. `brf_198532`: 82.1% coverage, 0.85 confidence ⭐
2. `brf_48663`: 82.1% coverage, 0.85 confidence ⭐
3. `brf_271949`: 80.3% coverage, 0.85 confidence ⭐

### Critical Failures (Priority Fixes)
1. `Hjorthagen_brf_78906`: 0% coverage (scanned PDF)
2. `SRS_brf_276629`: 0% coverage (scanned PDF)
3. `SRS_brf_76536`: 0% coverage (scanned PDF)

---

## 📊 Gap Analysis: 55.9% → 95%

### The 39.1 Percentage Point Gap

To achieve 95% average coverage, we need to close a **39.1 percentage point gap**.

### Three-Tier Problem

**Tier 1: Critical Failures (3 PDFs at 0%)**
- Impact: Pulling average down by ~7-9 percentage points
- Fix difficulty: Medium (vision extraction issues)
- Priority: **CRITICAL** (must reach 100% success rate)

**Tier 2: Low Performers (5 PDFs at 1-19%)**
- Impact: Pulling average down by ~5-7 percentage points
- Fix difficulty: Medium-High (partial extraction failures)
- Priority: **HIGH**

**Tier 3: General Coverage Gap (All PDFs)**
- Impact: Remaining ~25 percentage points
- Fix difficulty: High (requires expanding extraction)
- Priority: **MEDIUM** (broad improvement needed)

---

## 🗺️ Master Plan: 4-Week Roadmap

### Week 3 Day 3-5: Discovery & Root Cause Analysis

**Objectives**:
1. Complete 42-PDF test suite
2. Identify root causes of all failures
3. Create comprehensive field coverage matrix
4. Prioritize fixes by impact

**Deliverables**:
- ✅ 42-PDF complete analysis report
- ✅ Failed PDF root cause analysis
- ✅ Field coverage matrix (all 42 PDFs)
- ✅ Top 20 missing fields identified
- ✅ Week 4 implementation plan

**Time**: 2-3 days

---

### Week 4 Day 1-2: Fix Critical Failures (Tier 1)

**Objective**: Achieve **100% success rate** (0 failures)

**Tasks**:
1. Debug vision extraction on 3 failed scanned PDFs
2. Identify OCR quality issues
3. Implement fallback extraction strategies
4. Add robust error handling
5. Test fix on all scanned PDFs

**Target**:
- Before: 3/33 failures (9.1%)
- After: 0/42 failures (0%)
- Impact: +7-9 percentage points to average

**Time**: 1-2 days

---

### Week 4 Day 3-4: Fix Low Performers (Tier 2)

**Objective**: Bring all PDFs to **minimum 40% coverage**

**Tasks**:
1. Analyze 5 low-performing PDFs (1-19% coverage)
2. Identify common missing field patterns
3. Expand agent prompts for those patterns
4. Add targeted extractors
5. Re-test low performers

**Target**:
- Before: 5 PDFs at 1-19% coverage
- After: 5 PDFs at 40%+ coverage
- Impact: +5-7 percentage points to average

**Time**: 1-2 days

---

### Week 4 Day 5-7: Close General Coverage Gap (Tier 3)

**Objective**: Improve **all PDFs** to approach 95% coverage

**Strategy**: Three-pronged approach

#### Prong 1: Expand Agent Prompts (Quick Wins)
- Add top 10 most-missing fields to existing agent prompts
- Improve field name consistency (semantic matching)
- Enhance extraction instructions with examples
- **Expected Impact**: +10-15 percentage points

#### Prong 2: Add Specialized Extractors (Medium Effort)
- Implement metadata extractor (org number, BRF name, fiscal year)
- Implement detailed financial extractor (income statement, balance sheet breakdowns)
- Implement enhanced property extractor (construction year, tax value)
- **Expected Impact**: +10-15 percentage points

#### Prong 3: Hierarchical Extraction (High Effort, High Reward)
- Two-pass extraction for complex sections (Notes 8, 9)
- Deep-dive extraction for tables and nested structures
- Cross-reference validation
- **Expected Impact**: +5-10 percentage points

**Total Expected Improvement**: +25-40 percentage points

**Time**: 2-3 days

---

### Week 4 Day 8-10: Validation & Iteration

**Objective**: Measure improvement and iterate to 95%

**Tasks**:
1. Run full 42-PDF test suite with all improvements
2. Measure new average coverage
3. Identify remaining gaps
4. Iterate on biggest remaining gaps
5. Re-run until 95% achieved

**Target**:
- Current: 55.9% average coverage
- After Tier 1 fixes: ~63-65%
- After Tier 2 fixes: ~68-72%
- After Tier 3 fixes: ~93-105% (target: 95%)

**Time**: 2-3 days

---

## 📋 Detailed Task Lists

### Week 3 Day 3 Tasks (IMMEDIATE)

#### Task 1: Complete 42-PDF Test Suite
```bash
# Resume test from checkpoint
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"
python3 test_comprehensive_42_pdfs.py --resume
```

**Expected Output**:
- 9 additional extraction result JSONs
- Updated `WEEK3_DAY3_COMPLETE_RESULTS.md`

#### Task 2: Investigate 3 Failed PDFs
```bash
# Debug failed PDFs individually
python3 debug_failed_pdf.py --pdf data/raw_pdfs/Hjorthagen/brf_78906.pdf
python3 debug_failed_pdf.py --pdf data/raw_pdfs/SRS/brf_276629.pdf
python3 debug_failed_pdf.py --pdf data/raw_pdfs/SRS/brf_76536.pdf
```

**Analysis Checklist**:
- [ ] Check if PDF is actually scanned or corrupted
- [ ] Verify OCR extraction quality
- [ ] Test vision extraction manually
- [ ] Identify root cause (OCR failure, vision API error, etc.)
- [ ] Document findings in `FAILED_PDF_ROOT_CAUSE_ANALYSIS.md`

#### Task 3: Analyze Component Tests
```bash
# Aggregate component test results
python3 analyze_component_tests.py --results-dir data/week3_comprehensive_test_results
```

**Component Tests to Analyze**:
1. **ExtractionField Functionality**: How many PDFs passed?
2. **Synonym Mapping**: Coverage of Swedish term variants
3. **Swedish-First Semantic Fields**: Fee/financial field sync
4. **Calculated Metrics Validation**: Tolerance threshold performance

#### Task 4: Create Field Coverage Matrix
```bash
# Generate field-by-field coverage across all PDFs
python3 generate_field_coverage_matrix.py --input data/week3_comprehensive_test_results --output FIELD_COVERAGE_MATRIX.md
```

**Matrix Structure**:
| Field Name | PDFs with Field | Coverage % | Priority |
|------------|----------------|------------|----------|
| chairman   | 40/42          | 95.2%      | ✅ Good   |
| org_number | 2/42           | 4.8%       | ❌ Critical |
| ...        | ...            | ...        | ...      |

---

### Week 4 Day 1-2 Tasks (Fix Critical Failures)

#### Task 5: Debug Vision Extraction
**File to Create**: `fix_vision_extraction.py`

**Steps**:
1. Test vision extraction on failed PDFs with verbose logging
2. Check DPI settings (current: 220, try 250, 300)
3. Test different vision models (GPT-4o vs Gemini vs Qwen)
4. Implement fallback strategy (OCR → Vision → Pattern matching)

**Success Criteria**:
- All 3 failed PDFs achieve >40% coverage
- 100% success rate on all 42 PDFs

#### Task 6: Add Robust Error Handling
**File to Modify**: `gracian_pipeline/core/pydantic_extractor.py`

**Improvements**:
1. Try multiple vision models on failure
2. Increase timeout for scanned PDFs
3. Add retry logic with exponential backoff
4. Return partial results instead of complete failure

---

### Week 4 Day 3-4 Tasks (Fix Low Performers)

#### Task 7: Analyze Low-Performing PDFs
**Create**: `analyze_low_performers.py`

**Analysis**:
1. Load 5 low-performing PDFs (1-19% coverage)
2. Compare to ground truth or high performers
3. Identify missing field patterns
4. Document in `LOW_PERFORMER_ANALYSIS.md`

#### Task 8: Expand Agent Prompts
**Files to Modify**: `gracian_pipeline/prompts/agent_prompts.py`

**Expansion Strategy**:
- Add top 5 most-missing fields to each agent
- Add examples of Swedish terminology variants
- Strengthen extraction instructions

---

### Week 4 Day 5-7 Tasks (Close General Gap)

#### Task 9: Implement Metadata Extractor
**Create**: `gracian_pipeline/core/metadata_extractor.py`

**Fields to Extract**:
- organization_number (org nr, organisationsnummer)
- brf_name (föreningens namn)
- fiscal_year (räkenskapsår)
- document_date (datum)

**Expected Impact**: +3-5 percentage points

#### Task 10: Implement Detailed Financial Extractor
**Create**: `gracian_pipeline/core/detailed_financial_extractor.py`

**Fields to Extract**:
- income_statement (nested structure with all line items)
- balance_sheet (nested structure with assets/liabilities breakdown)
- cash_flow_statement (detailed inflows/outflows)

**Expected Impact**: +5-8 percentage points

#### Task 11: Implement Enhanced Property Extractor
**Modify**: `gracian_pipeline/core/pydantic_extractor.py`

**Fields to Add**:
- construction_year (byggår, byggnadsår)
- renovation_year (renoveringsår)
- tax_value (taxeringsvärde)
- land_area (tomtarea)

**Expected Impact**: +2-4 percentage points

#### Task 12: Hierarchical Extraction for Notes
**Create**: `gracian_pipeline/core/hierarchical_notes_extractor.py`

**Approach**:
1. First pass: Identify all note sections
2. Second pass: Deep-dive into each note for details
3. Cross-reference values across notes

**Expected Impact**: +5-10 percentage points

---

## 📊 Success Metrics & Milestones

### Milestone 1: Week 3 Day 3 Complete
✅ **Criteria**:
- All 42 PDFs tested
- Root cause analysis for failures documented
- Field coverage matrix created
- Top 20 missing fields identified

### Milestone 2: Week 4 Day 2 Complete
✅ **Criteria**:
- 100% success rate (0 failures)
- Average coverage: 63-65%
- All scanned PDFs extracting data

### Milestone 3: Week 4 Day 4 Complete
✅ **Criteria**:
- No PDFs below 40% coverage
- Average coverage: 68-72%
- Low performers improved

### Milestone 4: Week 4 Day 7 Complete
✅ **Criteria**:
- Average coverage: 90-95%
- Top performers: 95%+ coverage
- All major field categories covered

### Milestone 5: Week 4 Day 10 Complete (GOAL)
🎯 **CRITERIA**:
- **Average coverage: ≥95%**
- **Minimum coverage: ≥80%** (all PDFs)
- **Success rate: 100%** (0 failures)
- **Top 20 critical fields: ≥95% coverage**

---

## 🛡️ Amnesia Protection Documents

### Documents to Create Before Compaction

1. **`WEEK3_DAY3_COMPLETE_RESULTS.md`** ✅
   - Complete 42-PDF test results
   - Coverage distribution
   - Component test results

2. **`FAILED_PDF_ROOT_CAUSE_ANALYSIS.md`**
   - Detailed analysis of 3 failed PDFs
   - Root causes identified
   - Fix recommendations

3. **`FIELD_COVERAGE_MATRIX.md`**
   - Field-by-field coverage across all 42 PDFs
   - Missing field prioritization
   - Top 20 targets for improvement

4. **`LOW_PERFORMER_ANALYSIS.md`**
   - Analysis of 5 low-performing PDFs
   - Common patterns identified
   - Fix strategies

5. **`WEEK4_IMPLEMENTATION_PLAN.md`**
   - Detailed task breakdown
   - Code files to create/modify
   - Expected impact estimates

6. **`95_95_ACHIEVEMENT_VALIDATION.md`** (Week 4 end)
   - Final validation results
   - Before/after comparison
   - Lessons learned

---

## 🚀 Quick Start: Next Immediate Actions

### Action 1: Resume 42-PDF Test (30 minutes)
```bash
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"
python3 test_comprehensive_42_pdfs.py --resume
```

### Action 2: Analyze Results (1 hour)
```bash
python3 analyze_week3_day3_results.py  # Re-run with all 42
python3 analyze_component_tests.py
```

### Action 3: Investigate Failures (2 hours)
```bash
# Create debug script
python3 debug_failed_pdfs.py
```

### Action 4: Create Field Coverage Matrix (1 hour)
```bash
python3 generate_field_coverage_matrix.py
```

---

## 📈 Expected Improvement Timeline

| Week | Task | Current Coverage | Target Coverage | Gain |
|------|------|-----------------|-----------------|------|
| **W3D3** | Complete testing | 55.9% (33 PDFs) | 55.9% (42 PDFs) | +0% (baseline) |
| **W4D2** | Fix critical failures | 55.9% | 63-65% | +7-9% |
| **W4D4** | Fix low performers | 63-65% | 68-72% | +5-7% |
| **W4D7** | Close general gap | 68-72% | 90-95% | +22-23% |
| **W4D10** | Validation & iteration | 90-95% | **95%+** | +0-5% |

**Total Expected Gain**: **+39.1 percentage points** (55.9% → 95%)

---

## ⚠️ Risk Mitigation

### Risk 1: Scanned PDF Failures Cannot Be Fixed
**Likelihood**: Low
**Impact**: High (-7-9 percentage points)
**Mitigation**:
- Test multiple OCR engines (EasyOCR, Tesseract, Docling)
- Implement multi-model vision approach
- Accept partial results instead of complete failure

### Risk 2: General Gap Too Large (Can't Reach 95%)
**Likelihood**: Medium
**Impact**: High (miss target)
**Mitigation**:
- Re-evaluate target (maybe 85% is acceptable?)
- Focus on critical fields only (95% on top 50 fields)
- Implement hierarchical extraction for biggest gaps

### Risk 3: Time Overrun (Takes Longer Than 10 Days)
**Likelihood**: Medium
**Impact**: Medium (project delay)
**Mitigation**:
- Prioritize high-impact fixes (Pareto principle)
- Parallelize work where possible
- Accept 90% coverage as interim milestone

---

**Last Updated**: 2025-10-10 17:00:00
**Status**: Master plan created, ready for execution
**Next Action**: Resume 42-PDF test completion
