# Week 3 Day 5: SRS Dataset Coverage Gap - Ultrathinking Strategy

**Date**: October 11, 2025
**Current Status**: Week 3 Day 4 complete (retry logic validated), Day 5 planning phase
**Objective**: Strategic analysis of SRS dataset coverage gap and path to 75% target

---

## 🧠 **ULTRATHINKING: Root Cause Analysis**

### **Problem Statement**

**SRS Dataset Coverage Gap**: 48.8% vs 66.9% Hjorthagen (18 percentage point gap)

**Why This Matters**:
1. **Scalability**: SRS corpus is part of 26,342 PDF citywide target
2. **Production Readiness**: Can't ship with 30% lower coverage on major dataset
3. **75% Target**: Need 65%+ SRS coverage to average 75% across full corpus
4. **User Impact**: SRS documents are real-world annual reports used by stakeholders

---

## 📊 **Current State Analysis**

### **Dataset Comparison**

| Metric | Hjorthagen (n=15) | SRS (n=27) | Gap | Analysis |
|--------|-------------------|------------|-----|----------|
| **Success Rate** | 100% (15/15) | 81.5% (22/27) | -18.5% | ✅ **SOLVED** with retry logic |
| **Average Coverage** | 66.9% | 48.8% | **-18.1%** | 🔴 **P0 BLOCKER** |
| **Average Confidence** | 0.62 | 0.66 | +0.04 | ✅ SRS slightly higher |
| **Processing Time** | 43-211s | Similar | ~0 | ✅ No performance issue |

**Key Insight**: Confidence scores are **higher** in SRS (0.66 vs 0.62), but coverage is **lower** (48.8% vs 66.9%). This suggests:
- LLM extraction quality is fine (high confidence)
- Problem is likely **missing data** or **routing issues** (not extraction failures)

---

## 🔬 **Hypothesis Generation**

### **Hypothesis 1: Document Structure Differences** (MOST LIKELY)

**Theory**: SRS PDFs have different section structures/headings than Hjorthagen

**Evidence**:
- Hjorthagen: Homogeneous dataset (same neighborhood, similar templates)
- SRS: Diverse citywide corpus (multiple municipalities, varying templates)
- Swedish term mapping: 97.3% overall (good), but may miss SRS-specific headings

**Test**:
```python
# Compare Docling section headings between datasets
hjorthagen_headings = analyze_docling_headings('Hjorthagen/*.pdf')
srs_headings = analyze_docling_headings('SRS/*.pdf')
unique_to_srs = srs_headings - hjorthagen_headings
```

**Expected Findings**:
- SRS may use different Swedish terms for same concepts
- Section order/nesting may differ
- Some agents may route to wrong pages

**Fix Impact**: +5-10 percentage points if correct

---

### **Hypothesis 2: Scanned vs Machine-Readable Ratio** (MEDIUM LIKELIHOOD)

**Theory**: SRS dataset has more scanned PDFs requiring OCR

**Evidence**:
- PDF topology analysis: 49.3% scanned overall
- Scanned PDFs are slower and less accurate for text extraction
- Docling OCR quality may vary by document

**Test**:
```python
# Check PDF topology per dataset
hjorthagen_scanned_pct = count_scanned('Hjorthagen/*.pdf')
srs_scanned_pct = count_scanned('SRS/*.pdf')
correlation_coverage = analyze_scanned_vs_coverage()
```

**Expected Findings**:
- If SRS has 60%+ scanned (vs 40% Hjorthagen), OCR is the issue
- Low performers (brf_76536: 0.0%, brf_43334: 6.8%) likely scanned

**Fix Impact**: +3-7 percentage points if OCR improved

---

### **Hypothesis 3: Missing Validation Features** (CONFIRMED)

**Theory**: SRS needs multi-source aggregation more than Hjorthagen

**Evidence** (from Week 3 Day 3 validation):
- Multi-source aggregation: **0%** implemented (0/37 PDFs)
- Validation thresholds: **0%** implemented
- Calculated metrics: **0%** implemented
- Data preservation: 97.3% (working)

**SRS-Specific Need**:
- SRS documents may spread data across multiple sections
- Hjorthagen may be more "template-like" with data in expected locations
- Without multi-source aggregation, SRS loses 10-15% coverage

**Test**:
```python
# Check field sources per dataset
hjorthagen_multi_source_fields = count_multi_source('Hjorthagen/*.pdf')
srs_multi_source_fields = count_multi_source('SRS/*.pdf')
```

**Expected Findings**:
- SRS requires cross-section aggregation more frequently
- Example: Fee data in both "Avgifter" section AND balance sheet notes

**Fix Impact**: +10-15 percentage points (HIGHEST POTENTIAL)

---

### **Hypothesis 4: Low Performers Skewing Average** (STATISTICAL)

**Theory**: A few extreme outliers drag down SRS average

**Evidence**:
- **5 lowest SRS performers**:
  - brf_76536: 0.0% coverage (zero extraction)
  - brf_43334: 6.8% coverage
  - brf_78906: 6.0% coverage
  - brf_53107: 14.5% coverage (also tested with retry: 17.9%)
  - brf_280938: 19.7% coverage
- **Average of 5 lowest**: 9.4%
- **Average of remaining 22**: 56.7% (closer to Hjorthagen!)

**Test**:
```python
# Calculate SRS coverage without 5 lowest
srs_all_coverage = [c for c in srs_coverage_list]
srs_excluding_lowest_5 = sorted(srs_all_coverage)[5:]  # Remove bottom 5
avg_excluding_outliers = mean(srs_excluding_lowest_5)
```

**Expected Findings**:
- SRS without outliers: ~56-58% coverage
- Gap narrows: 66.9% vs 56-58% = 8-10 point gap (vs 18 points)

**Fix Impact**: +8-10 percentage points if outliers fixed

---

## 🎯 **Recommended Investigation Strategy**

### **Phase 1: Quick Diagnostic** (30 minutes) - **START HERE**

**Objective**: Rapid triage to identify primary root cause

**Actions**:
1. **Manual PDF Review** (15 min)
   - Open 3 lowest SRS performers in PDF viewer
   - Open 3 highest Hjorthagen performers
   - Compare:
     - Document structure (sections, headings, order)
     - Visual quality (scanned vs text-based)
     - Data presentation (tables, lists, narrative)

2. **Docling Heading Analysis** (10 min)
   ```python
   # Quick script to compare section headings
   python -c "
   from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter

   adapter = UltraComprehensiveDoclingAdapter()

   # Analyze 2 low SRS + 2 high Hjorthagen
   for pdf in ['SRS/brf_76536.pdf', 'SRS/brf_43334.pdf',
               'Hjorthagen/brf_81563.pdf', 'Hjorthagen/brf_268411.pdf']:
       result = adapter.extract_with_docling(pdf)
       print(f'\n{pdf}:')
       print(f'  Sections detected: {len(result.get(\"sections\", []))}')
       print(f'  First 5 headings: {[s[\"heading\"] for s in result.get(\"sections\", [])[:5]]}')
   "
   ```

3. **Coverage Pattern Analysis** (5 min)
   ```python
   # Load Week 3 Day 3 results and analyze field-level patterns
   python analyze_week3_day3_results.py  # Already exists
   ```

**Decision Point After Phase 1**:
- If **structure differs**: → Hypothesis 1 (fix agent routing)
- If **more scanned**: → Hypothesis 2 (improve OCR)
- If **multi-source needed**: → Hypothesis 3 (implement aggregation)
- If **outliers skewing**: → Hypothesis 4 (fix specific PDFs)

---

### **Phase 2: Targeted Fix** (1-2 hours)

Based on Phase 1 diagnosis, implement ONE high-impact fix:

#### **Fix A: Agent Routing Improvements** (if Hypothesis 1 confirmed)

**Implementation**:
```python
# Update synonyms.py with SRS-specific heading variations
GOVERNANCE_HEADINGS_SRS = [
    "Styrelse",
    "Styrelsens sammansättning",
    "Förvaltning",  # SRS-specific
    "Ledning",  # SRS-specific
    # ... add more based on Phase 1 findings
]

# Update agent routing logic to handle variations
def get_governance_context_with_fallback(docling_result):
    # Try primary headings
    context = find_sections(GOVERNANCE_HEADINGS_PRIMARY)
    if not context:
        # Fallback to SRS-specific headings
        context = find_sections(GOVERNANCE_HEADINGS_SRS)
    return context
```

**Expected Impact**: +5-10 percentage points
**Time**: 1 hour

#### **Fix B: Multi-Source Aggregation** (if Hypothesis 3 confirmed)

**Implementation** (already partially designed in Week 3 plans):
```python
# Enable cross-section data merging
from gracian_pipeline.validation.semantic_matcher import merge_from_multiple_sources

# For fee fields: Aggregate from both sections
fee_data = merge_from_multiple_sources(
    sources=[
        extract_from_section("Avgifter"),
        extract_from_section("Not 1", field="månadsavgift"),
        extract_from_section("Balansräkning", field="avgiftsskulder")
    ],
    field="arsavgift",
    strategy="highest_confidence"  # Take most confident source
)
```

**Expected Impact**: +10-15 percentage points (HIGHEST)
**Time**: 1-2 hours

#### **Fix C: OCR Quality Improvements** (if Hypothesis 2 confirmed)

**Implementation**:
```python
# Switch to higher-quality OCR for scanned PDFs
from docling.backend.ocr_backend import EasyOCR  # Better Swedish support

# Detect if PDF is scanned
if is_scanned_pdf(pdf_path):
    # Use EasyOCR instead of default
    pipeline = DocumentConverter(
        ocr_backend=EasyOCR(lang=['sv', 'en']),
        ocr_quality='high'  # Slower but more accurate
    )
```

**Expected Impact**: +3-7 percentage points
**Time**: 30 minutes

#### **Fix D: Outlier-Specific Fixes** (if Hypothesis 4 confirmed)

**Implementation**:
```python
# Manual investigation of 5 lowest performers
for pdf in ['brf_76536', 'brf_43334', 'brf_78906', 'brf_53107', 'brf_280938']:
    # Extract and inspect
    result = extract_brf_to_pydantic(f'SRS/{pdf}.pdf', mode='deep')

    # Identify specific failure patterns
    missing_fields = [f for f in expected_fields if not result.get(f)]
    print(f'{pdf}: Missing {len(missing_fields)} fields')
    print(f'  Top missing: {missing_fields[:5]}')

    # Create targeted fixes
    # ...
```

**Expected Impact**: +8-10 percentage points
**Time**: 2 hours

---

### **Phase 3: Validation** (30 minutes)

**Test on SRS Subset**:
```python
# Re-test 10 representative SRS PDFs with fix applied
srs_test_subset = [
    'SRS/brf_76536.pdf',  # 0.0% baseline (worst)
    'SRS/brf_43334.pdf',  # 6.8% baseline
    'SRS/brf_53107.pdf',  # 14.5% baseline
    'SRS/brf_198532.pdf', # Mid-range
    'SRS/brf_275608.pdf', # Mid-range
    # ... 5 more
]

results = []
for pdf in srs_test_subset:
    result = extract_brf_to_pydantic(pdf, mode='fast')
    results.append({
        'pdf': pdf,
        'coverage': result.coverage_percentage,
        'confidence': result.confidence_score
    })

avg_coverage = mean([r['coverage'] for r in results])
improvement = avg_coverage - 48.8  # SRS baseline
print(f'SRS subset coverage: {avg_coverage:.1f}% (+{improvement:.1f} points)')
```

**Success Criteria**:
- **Minimum**: SRS subset average ≥ 55% (+6 points)
- **Target**: SRS subset average ≥ 60% (+11 points)
- **Stretch**: SRS subset average ≥ 65% (+16 points)

---

## 🎯 **Estimated Impact Matrix**

| Fix | Complexity | Time | Expected Impact | Risk |
|-----|------------|------|-----------------|------|
| **Multi-Source Aggregation** | ⭐⭐⭐ MEDIUM | 1-2 hours | **+10-15 points** | LOW (already designed) |
| **Agent Routing Improvements** | ⭐⭐ LOW | 1 hour | **+5-10 points** | VERY LOW (synonym updates) |
| **Outlier-Specific Fixes** | ⭐⭐⭐ MEDIUM | 2 hours | **+8-10 points** | LOW (targeted approach) |
| **OCR Quality** | ⭐ VERY LOW | 30 min | **+3-7 points** | VERY LOW (config change) |

**Combined Potential**: +15-25 percentage points if multiple fixes applied

**Realistic Target**: +10-15 points (60-63% SRS coverage) with 1-2 key fixes

---

## 📋 **Recommended Task Breakdown**

### **Week 3 Day 5 Tasks** (Prioritized)

#### **IMMEDIATE (Next 30 Minutes)**:
1. ✅ **COMPLETE**: Week 3 Day 4 retry logic validated
2. 🔄 **NEXT**: Phase 1 Diagnostic (manual review + heading analysis)
   - Open 6 PDFs (3 low SRS, 3 high Hjorthagen)
   - Run Docling heading comparison script
   - Run field coverage pattern analysis
   - Document findings in `WEEK3_DAY5_DIAGNOSTIC_RESULTS.md`

#### **SHORT-TERM (Next 2 Hours)**:
3. 🔄 Implement Phase 2 Targeted Fix (based on Phase 1 diagnosis)
   - **If routing issue**: Update synonyms.py
   - **If multi-source needed**: Implement aggregation
   - **If scanned PDFs**: Improve OCR quality
   - **If outliers**: Manual fixes

4. 🔄 Phase 3 Validation (re-test 10 SRS PDFs with fix)
   - Measure improvement (+6 to +16 points expected)
   - Document results

5. 🔄 Create `WEEK3_DAY5_COMPLETE.md` summary
   - Root cause identified
   - Fix implemented and validated
   - Impact measured
   - Next steps outlined

#### **MEDIUM-TERM (Week 3 Day 6+)**:
6. ⏭️ Full 42-PDF regression test WITH Day 4 retry logic + Day 5 fixes
7. ⏭️ Compare: Baseline (56.1%) → Day 4 (retry) → Day 5 (SRS fix) → Combined
8. ⏭️ If SRS gap persists, implement secondary fixes
9. ⏭️ Scale to 100-PDF test for production validation

---

## 🧪 **Testing Strategy**

### **Incremental Validation**

**Step 1**: Baseline confirmation
- Re-check Week 3 Day 3 results for SRS: 48.8% avg coverage

**Step 2**: Single-fix validation
- Apply ONE fix (e.g., multi-source aggregation)
- Test on 10 SRS PDFs
- Measure improvement

**Step 3**: Multi-fix validation (if needed)
- Apply SECOND fix (e.g., agent routing)
- Re-test same 10 PDFs
- Measure cumulative improvement

**Step 4**: Full regression
- Test all 27 SRS PDFs with all fixes
- Compare: 48.8% baseline → X% with fixes
- Target: ≥60% (ideally 65%+)

---

## 💡 **Key Insights**

### **1. SRS Is Not "Broken" - It's Different**
- **Evidence**: 0.66 confidence (higher than Hjorthagen's 0.62)
- **Implication**: LLM extraction quality is fine
- **Problem**: Missing data OR routing issues (not extraction failures)

### **2. Multi-Source Aggregation Is Likely the Highest-Impact Fix**
- **Reason**: 0% implementation (untested potential)
- **SRS Context**: Diverse templates likely scatter data across sections
- **Expected Impact**: +10-15 points (biggest gain)

### **3. Outliers Significantly Skew Average**
- **Evidence**: Bottom 5 average 9.4%, top 22 average 56.7%
- **Implication**: Fixing 5 PDFs = +8-10 point improvement
- **Strategy**: Targeted fixes may be faster than systemic changes

### **4. Hjorthagen Is Homogeneous, SRS Is Diverse**
- **Hjorthagen**: Same neighborhood, likely similar templates
- **SRS**: Citywide corpus, multiple municipalities/vendors
- **Implication**: SRS requires more robust routing (not template-specific)

---

## 🚀 **Success Metrics**

### **Week 3 Day 5 Complete When**:
✅ Phase 1 diagnostic complete (root cause identified)
✅ Phase 2 targeted fix implemented
✅ Phase 3 validation shows +6 to +16 point improvement
✅ Documentation created (`WEEK3_DAY5_COMPLETE.md`)

### **SRS Dataset Fixed When**:
✅ SRS average coverage ≥ 60% (+11 points from 48.8%)
✅ Gap narrowed: Hjorthagen 66.9% vs SRS 60%+ = <7 point gap
✅ Full 42-PDF test shows overall coverage ≥ 60% (vs 56.1% baseline)

### **Production Ready When**:
✅ Overall coverage ≥ 65% (closer to 75% target)
✅ Success rate ≥ 95% (retry logic validated)
✅ SRS coverage within 5 points of Hjorthagen
✅ 100-PDF scale test successful

---

## 📊 **Estimated Timeline**

| Task | Time | Cumulative |
|------|------|------------|
| **Phase 1: Diagnostic** | 30 min | 30 min |
| **Phase 2: Implement Fix** | 1-2 hours | 2.5 hours |
| **Phase 3: Validate Fix** | 30 min | 3 hours |
| **Documentation** | 30 min | 3.5 hours |
| **TOTAL: Week 3 Day 5** | **3-4 hours** | - |

---

## 🎯 **Final Recommendation**

**START WITH**: Phase 1 Diagnostic (30 minutes)
1. Manual review of 6 PDFs (3 low SRS, 3 high Hjorthagen)
2. Docling heading comparison
3. Field coverage pattern analysis

**THEN**: Implement multi-source aggregation (MOST LIKELY FIX)
- Highest impact potential: +10-15 points
- Already designed in Week 3 plans
- Low risk, well-understood solution

**VALIDATE**: Re-test 10 SRS PDFs
- Measure improvement
- If ≥+10 points → DONE
- If <+10 points → Add secondary fix (routing or OCR)

**TARGET**: SRS coverage ≥ 60% by end of Day 5
**STRETCH**: SRS coverage ≥ 65% (matching Hjorthagen)

---

**Status**: ✅ **Ready to Begin Phase 1 Diagnostic**
**Next Action**: Manual PDF review + heading analysis script
**Expected Outcome**: Root cause identified within 30 minutes
