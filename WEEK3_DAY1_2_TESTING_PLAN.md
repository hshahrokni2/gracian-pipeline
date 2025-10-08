# Week 3 Day 1-2: Comprehensive Testing Plan

## 🎯 Objectives

Test integrated schema on real-world Swedish BRF annual reports to validate:
1. **ExtractionField Functionality**: Multi-source aggregation, confidence tracking, validation status
2. **Synonym Mapping**: Real Swedish BRF terminology recognition
3. **Swedish-First Semantic Fields**: Primary Swedish fields with English aliases
4. **Calculated Metrics**: Tolerant validation with dynamic thresholds

## 📊 Test Strategy

### Phase 1: Strategic Sample Testing (5 PDFs) ✅ IN PROGRESS

**Purpose**: Validate system integration and estimate full test duration

**Sample Selection**:
- `Hjorthagen/brf_46160.pdf` - Small, well-tested baseline
- `Hjorthagen/brf_266956.pdf` - Medium complexity
- `SRS/brf_198532.pdf` - Well-documented reference case
- `SRS/brf_52576.pdf` - Different structural patterns
- `SRS/brf_276507.pdf` - Large document stress test

**Test Script**: `test_comprehensive_sample.py`

**Metrics Tracked**:
- Extraction coverage (% of fields populated)
- Confidence scores (0.0-1.0)
- Processing time per PDF
- Component test pass rates

### Phase 2: Full Test Suite (42 PDFs) - PLANNED

**Scope**:
- Hjorthagen: 15 PDFs (various BRF structures)
- SRS: 27 PDFs (diverse document types)
- **Total**: 42 real-world Swedish BRF annual reports

**Test Script**: `test_comprehensive_42_pdfs.py`

**Estimated Duration**: 3-7 hours (based on sample results)

**Execution Strategy**:
```bash
# Background execution with logging
python test_comprehensive_42_pdfs.py > week3_full_test.log 2>&1 &

# Monitor progress
tail -f week3_full_test.log
```

## 🧪 Component Tests

### 1. ExtractionField Functionality Tests

**Test Cases**:
- ✅ **Confidence Scores Present**: All extractions include confidence scores (0.0-1.0)
- ✅ **Source Pages Tracked**: `all_source_pages` populated with evidence
- ⚠️ **Multi-Source Aggregation**: Fields with alternatives from multiple sources
- ✅ **Validation Status Tracking**: Calculated metrics include status (valid/warning/error)

**Target**: ≥90% pass rate across all documents

### 2. Synonym Mapping Tests

**Test Cases**:
- ✅ **Swedish Governance Terms**: Chairman, board members extracted correctly
- ✅ **Swedish Financial Terms**: Assets, liabilities, equity recognized
- ⚠️ **Synonym Metadata**: `_terminology_found` fields populated (if implemented)

**Target**: ≥95% recognition rate for standard Swedish BRF terminology

### 3. Swedish-First Semantic Fields Tests

**Test Cases**:
- ✅ **Fee Structure Swedish Primary**: `arsavgift_kr_per_kvm`, `manadsavgift_kr` as primary
- ✅ **Financial Swedish Primary**: Swedish field names prioritized
- ✅ **Swedish-English Alias Sync**: Both Swedish primary and English alias populated

**Target**: 100% Swedish-first implementation across all semantic fields

### 4. Calculated Metrics Validation Tests

**Test Cases**:
- ✅ **Calculated Metrics Present**: `CalculatedFinancialMetrics` model populated
- ✅ **Validation Thresholds Applied**: Status in `['valid', 'warning', 'error']`
- ✅ **Tolerant Validation**: 3-tier system (≤tolerance, ≤2x, >2x) working
- ✅ **Data Preservation**: "Never null" policy enforced (extracted values preserved)

**Target**: 100% validation logic correctness (validated in Week 2 Day 5)

## 📁 Output Structure

### Sample Test Results
```
data/week3_sample_test_results/
├── sample_test_results_YYYYMMDD_HHMMSS.json
└── [individual_extraction_files.json]
```

### Full Test Results
```
data/week3_comprehensive_test_results/
├── comprehensive_test_results.json     # Detailed per-PDF results
├── comprehensive_test_summary.json     # Aggregated statistics
└── [dataset]_[pdf_name]_extraction.json  # Individual extractions
```

## 📊 Success Criteria

### Minimum Viable Criteria (Must Pass)
- ✅ Sample test: ≥80% successful extractions (4/5 PDFs)
- ✅ Average coverage: ≥60% (real-world documents are challenging)
- ✅ Component tests: ≥70% pass rate across all test categories

### Production-Ready Criteria (Target)
- 🎯 Full test: ≥90% successful extractions (38/42 PDFs)
- 🎯 Average coverage: ≥75%
- 🎯 Average confidence: ≥0.85
- 🎯 Component tests: ≥90% pass rate
- 🎯 Processing time: <10 minutes per PDF

## 🚀 Execution Plan

### Week 3 Day 1: Sample Testing & Analysis
1. ✅ Run strategic sample test (5 PDFs)
2. 📊 Analyze sample results
3. 🐛 Address critical failures (if any)
4. 📝 Document findings

### Week 3 Day 2: Full Suite Execution
1. 🔄 Run full 42-PDF test suite (if sample passes)
2. 📊 Generate comprehensive reports
3. 📈 Analyze coverage and confidence metrics
4. 🎯 Identify patterns in successful vs failed extractions
5. 📝 Create detailed findings report

## 🔍 Known Considerations

### Processing Time
- **Deep Mode**: 3-5 minutes per PDF (docling + LLM extraction)
- **Full 42-PDF Suite**: Estimated 3-7 hours
- **Recommendation**: Run overnight or in dedicated session

### Expected Challenges
1. **Scanned PDFs**: Lower text extraction quality
2. **Diverse Structures**: Swedish BRF reports vary significantly
3. **API Rate Limits**: May require retry logic
4. **Memory Usage**: Large PDF batch processing

### Mitigation Strategies
- ✅ Robust error handling with detailed logging
- ✅ Retry logic for API calls
- ✅ Individual result saving (checkpoint recovery)
- ✅ Progress tracking with time estimates

## 📈 Monitoring Commands

### Check Background Process
```bash
# View recent output
tail -100 week3_full_test.log

# Monitor live
tail -f week3_full_test.log

# Check if still running
ps aux | grep test_comprehensive
```

### Partial Results Analysis
```bash
# Count completed extractions
ls data/week3_comprehensive_test_results/*.json | wc -l

# View summary (if generated)
cat data/week3_comprehensive_test_results/comprehensive_test_summary.json | jq '.'
```

## 🎯 Deliverables

### Expected Outputs
1. ✅ `test_comprehensive_sample.py` - Strategic sample test runner
2. ✅ `test_comprehensive_42_pdfs.py` - Full suite test runner
3. ✅ `WEEK3_DAY1_2_TESTING_PLAN.md` - This document
4. 📊 `WEEK3_DAY1_2_RESULTS.md` - Findings report (post-execution)
5. 📊 JSON results files with detailed metrics

### Next Steps (Week 3 Day 3)
- Ground truth creation for validation
- Manual verification of sample extractions
- Accuracy assessment against human-validated data
- Refinement of extraction pipeline based on findings

---

**Status**: Week 3 Day 1 - Sample Testing IN PROGRESS
**Last Updated**: 2025-10-07
**Next Milestone**: Sample results analysis & full suite execution decision
