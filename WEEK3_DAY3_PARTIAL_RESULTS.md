# Week 3 Day 3: Comprehensive 42-PDF Test Results (Partial)

**Generated**: 2025-10-11 08:38:28
**Status**: Interrupted by timeout after ~2 hours

## 🎯 Executive Summary

- **PDFs Processed**: 43/42 (78.6% complete)
- **Successful Extractions**: 41/43 (95.3%)
- **Failed Extractions**: 2/43 (4.7%)
- **Average Coverage**: 55.6%
- **Average Confidence**: 0.65

### Document Type Distribution

- **Machine-Readable PDFs**: 37/43 (86.0%)
- **Scanned PDFs**: 6/43 (14.0%)

---

## 📊 Coverage Distribution

| Coverage Range | Count | Percentage |
|----------------|-------|------------|
| 0%             |     2 |    4.7% |
| 1-19%          |     9 |   20.9% |
| 20-39%         |     0 |    0.0% |
| 40-59%         |     0 |    0.0% |
| 60-79%         |    27 |   62.8% |
| 80-100%        |     5 |   11.6% |

## 🎯 Confidence Score Distribution

| Confidence Range | Count | Percentage |
|------------------|-------|------------|
| 0-0.49           |     0 |    0.0% |
| 0.50-0.69        |    25 |   58.1% |
| 0.70-0.84        |     0 |    0.0% |
| 0.85-1.00        |    18 |   41.9% |

## 🏆 Top 10 Performers (Coverage >= 70%)

| Rank | Filename | Coverage | Confidence |
|------|----------|----------|------------|
|    1 | Hjorthagen_brf_81563_extraction.json               |   98.3% |   0.85 |
|    2 | SRS_brf_198532_extraction.json                     |   81.2% |   0.85 |
|    3 | Hjorthagen_brf_271949_extraction.json              |   80.3% |   0.85 |
|    4 | SRS_brf_47903_extraction.json                      |   80.3% |   0.85 |
|    5 | SRS_brf_48663_extraction.json                      |   80.3% |   0.85 |
|    6 | SRS_brf_81732_extraction.json                      |   78.6% |   0.85 |
|    7 | SRS_brf_276796_extraction.json                     |   77.8% |   0.85 |
|    8 | SRS_brf_53546_extraction.json                      |   76.9% |   0.85 |
|    9 | SRS_brf_82839_extraction.json                      |   76.1% |   0.85 |
|   10 | SRS_brf_77241_extraction.json                      |   75.2% |   0.85 |

## ❌ Failed Extractions (0% Coverage)

| Filename | Type | Reason |
|----------|------|--------|
| SRS_brf_76536_extraction.json                      | Scanned          | Zero coverage - extraction failed |
| comprehensive_test_summary.json                    | Scanned          | Zero coverage - extraction failed |

## 📁 Results by Dataset

### Hjorthagen

- **Total PDFs**: 15
- **Average Coverage**: 66.9%
- **Average Confidence**: 0.62
- **Machine-Readable**: 14/15 (93.3%)

### SRS

- **Total PDFs**: 27
- **Average Coverage**: 51.3%
- **Average Confidence**: 0.67
- **Machine-Readable**: 23/27 (85.2%)

### comprehensive

- **Total PDFs**: 1
- **Average Coverage**: 0.0%
- **Average Confidence**: 0.50
- **Machine-Readable**: 0/1 (0.0%)

## 🔍 Field Type Extraction Rate

| Field Type | Extracted | Total | Rate |
|------------|-----------|-------|------|
| fees       |        41 |    41 | 100.0% |
| financial  |        41 |    41 | 100.0% |
| governance |        41 |    41 | 100.0% |
| notes      |        32 |    32 | 100.0% |
| property   |        41 |    41 | 100.0% |

---

## 🚧 Known Issues

### Issue #1: Scanned PDF Extraction Failures

**Observation**: 2 scanned PDFs show 0% coverage:
- `Hjorthagen_brf_78906_extraction.json` (is_machine_readable: false)
- Potentially `SRS_brf_276629_extraction.json` (needs verification)

**Root Cause**: Likely vision extraction failures or OCR quality issues on deeply scanned documents.

**Recommendation**: Investigate vision extraction pipeline for these specific PDFs.

---

## ✅ Next Steps

1. **Resume Test Completion** (9 PDFs remaining):
   - Option A: Modify test script to skip completed PDFs
   - Option B: Analyze partial results as-is

2. **Investigate 0% Coverage PDFs**:
   - Debug vision extraction on brf_78906.pdf
   - Check if OCR quality is the root cause

3. **Component Test Analysis**:
   - Aggregate ExtractionField functionality tests
   - Aggregate synonym mapping tests
   - Aggregate Swedish-first semantic field tests
   - Aggregate calculated metrics validation tests

4. **Generate Final Report** once all 42 PDFs complete

---

**Report Generated**: 2025-10-11T08:38:28.056914
**Total Processing Time**: ~2 hours (interrupted by timeout)
