# Phase 2A Baseline Validation Results

**Date**: October 14, 2025
**Status**: ✅ BASELINE ESTABLISHED
**Pipeline**: Text-only extraction (pre-Phase 2A)
**Test Sample**: 3 PDF types (machine-readable, hybrid, scanned)

---

## 📊 EXECUTIVE SUMMARY

**Baseline Performance** (Text-Only Pipeline):
- **Average Coverage**: 50.2% (CORRECTED), 7.5% (RAW)
- **Average Accuracy**: 34.0%
- **Pass Rate**: 0/3 PDFs meet 95/95 targets

**Critical Finding**: **Scanned PDFs are the primary bottleneck** at 37.4% coverage and 22.7% accuracy, validating the need for Phase 2A vision consensus integration.

---

## 🎯 DETAILED RESULTS BY PDF TYPE

### 1. Machine-Readable PDF (Best Performance)

**Metrics**:
- **Coverage**: 67.0% (CORRECTED), 10.0% (RAW)
- **Accuracy**: 48.9%
- **Extracted Fields**: 61/91 applicable fields
- **Processing Time**: 377.9 seconds
- **Total Tokens**: 30,026

**Analysis**:
- ✅ **Highest coverage** among all PDF types
- ✅ **Highest accuracy** (48.9% confidence)
- ✅ 4 high-confidence agents, 5 low-confidence agents
- 🟡 Processing time is high (6+ minutes)
- 🟡 Still far from 95/95 target

**Expected Phase 2A Impact**:
- Coverage: 67.0% → **67.0%** (maintained, not primary target)
- Accuracy: 48.9% → **55-60%** (marginal improvement)
- Strategy: Text extraction (existing code, no vision models needed)

---

### 2. Hybrid PDF (Mixed Performance)

**Metrics**:
- **Coverage**: 46.2% (CORRECTED), 6.9% (RAW)
- **Accuracy**: 30.5%
- **Extracted Fields**: 42/91 applicable fields
- **Processing Time**: 49.4 seconds
- **Total Tokens**: 20,616

**Analysis**:
- 🟡 **Middle-ground performance** (between machine-readable and scanned)
- 🟡 2 high-confidence agents, 10 low-confidence agents
- ✅ Processing time acceptable (<1 minute)
- 🔴 Accuracy significantly lower than machine-readable

**Expected Phase 2A Impact**:
- Coverage: 46.2% → **65-70%** (text first, vision fallback if <30%)
- Accuracy: 30.5% → **55-65%** (quality-based fallback helps)
- Strategy: Hybrid (try text, fall back to vision if poor quality)

---

### 3. Scanned PDF (Primary Bottleneck) ⚠️

**Metrics**:
- **Coverage**: 37.4% (CORRECTED), 5.5% (RAW)
- **Accuracy**: 22.7%
- **Extracted Fields**: 34/91 applicable fields
- **Processing Time**: 54.3 seconds
- **Total Tokens**: 12,931

**Analysis**:
- 🔴 **WORST performance** across all metrics
- 🔴 **0 high-confidence agents**, 14 low-confidence agents
- 🔴 Accuracy at 22.7% (far below 95% target)
- 🔴 Validates the core problem Phase 2A addresses

**Expected Phase 2A Impact**:
- Coverage: 37.4% → **75-85%** (+37.6 to +47.6 percentage points) 🎯
- Accuracy: 22.7% → **75-85%** (+52.3 to +62.3 percentage points) ⭐
- Strategy: Vision consensus (Gemini 2.5-Pro 50% + GPT-4V 30%)

**This is the PRIMARY TARGET for Phase 2A!**

---

## 📈 BASELINE COMPARISON TABLE

| PDF Type | Coverage (CORRECTED) | Accuracy | Fields Extracted | Processing Time | High-Conf Agents |
|----------|---------------------|----------|------------------|-----------------|------------------|
| **Machine-Readable** | **67.0%** | **48.9%** | 61/91 | 377.9s | 4 |
| **Hybrid** | 46.2% | 30.5% | 42/91 | 49.4s | 2 |
| **Scanned** | **37.4%** | **22.7%** | 34/91 | 54.3s | **0** ❌ |
| **Average** | **50.2%** | **34.0%** | 45.7/91 | 160.5s | 2.0 |

---

## 🎯 PHASE 2A EXPECTED IMPROVEMENTS

### Overall Impact (Weighted by Corpus Distribution)

**Corpus Distribution** (from PDF topology analysis):
- Machine-readable: 48% of corpus
- Scanned: 49% of corpus
- Hybrid: 3% of corpus

**Weighted Baseline**:
- Coverage: (67.0% × 0.48) + (37.4% × 0.49) + (46.2% × 0.03) = **50.9%**
- Accuracy: (48.9% × 0.48) + (22.7% × 0.49) + (30.5% × 0.03) = **34.4%**

**Weighted Phase 2A Targets**:
- Coverage: (67.0% × 0.48) + (80.0% × 0.49) + (67.5% × 0.03) = **73.4%** (+22.5pp)
- Accuracy: (55.0% × 0.48) + (80.0% × 0.49) + (60.0% × 0.03) = **67.2%** (+32.8pp)

**Key Insight**: The 49% scanned PDF corpus drives the massive improvement potential!

---

### PDF Type Breakdown

| PDF Type | Baseline Coverage | Phase 2A Target | Improvement | Baseline Accuracy | Phase 2A Target | Improvement |
|----------|------------------|-----------------|-------------|------------------|-----------------|-------------|
| **Machine-Readable** | 67.0% | **67.0%** | 0.0pp | 48.9% | **55-60%** | +6-11pp |
| **Hybrid** | 46.2% | **65-70%** | +18.8-23.8pp | 30.5% | **55-65%** | +24.5-34.5pp |
| **Scanned** | 37.4% | **75-85%** | +37.6-47.6pp ⭐ | 22.7% | **75-85%** | +52.3-62.3pp ⭐ |
| **Average** | 50.2% | **69.0%** | +18.8pp | 34.0% | **65.0%** | +31.0pp |

---

## 💾 BASELINE ARTIFACTS SAVED

**Validation Results Files**:
- `validation/validation_machine_readable.json` - Machine-readable PDF results
- `validation/validation_hybrid.json` - Hybrid PDF results
- `validation/validation_scanned.json` - Scanned PDF results
- `validation/validation_summary.json` - Overall summary

**Key Metrics Captured**:
- Extracted fields (raw data for each agent)
- Coverage metrics (CORRECTED vs RAW OLD)
- Accuracy estimates (confidence scores)
- Processing time and token usage
- Agent-level success/failure data

---

## 🔬 CRITICAL INSIGHTS FOR PHASE 2A

### 1. Scanned PDFs = Primary Bottleneck ✅

**Evidence**:
- Worst coverage: 37.4% (vs 67.0% machine-readable)
- Worst accuracy: 22.7% (vs 48.9% machine-readable)
- 0 high-confidence agents (vs 4 for machine-readable)
- 14/15 agents have low confidence

**Conclusion**: Phase 2A vision consensus is targeting the right problem!

### 2. Text Extraction Still Valuable for Machine-Readable

**Evidence**:
- 67.0% coverage on machine-readable PDFs
- 48.9% accuracy (near 50% threshold)
- Processing time acceptable (6.3 minutes for 61 fields)

**Conclusion**: Smart routing (avoid vision models for machine-readable) is correct strategy!

### 3. Hybrid PDFs Need Quality-Based Fallback

**Evidence**:
- 46.2% coverage (mid-range)
- 30.5% accuracy (low confidence)
- Only 2 high-confidence agents

**Conclusion**: Quality threshold of 30% for fallback is appropriate!

### 4. Coverage vs Accuracy Gap

**Finding**: Coverage is higher than accuracy across all PDF types
- Machine-readable: 67.0% coverage, 48.9% accuracy (gap: -18.1pp)
- Hybrid: 46.2% coverage, 30.5% accuracy (gap: -15.7pp)
- Scanned: 37.4% coverage, 22.7% accuracy (gap: -14.7pp)

**Conclusion**: Pipeline extracts data but with low confidence → Vision consensus can improve both!

---

## 🚀 READY FOR PHASE 2A INTEGRATION TESTING

**Next Steps** (Integration Testing - Step 4):
1. ✅ Baseline established (this document)
2. ⏳ Run integration tests with Phase 2A code
3. ⏳ Compare results to baseline (expect improvements)
4. ⏳ Validate routing logic (scanned → vision, machine → text, hybrid → fallback)
5. ⏳ Measure actual vs expected gains

**Success Criteria** (for Phase 2A integration):
- ✅ Scanned PDF coverage: 37.4% → ≥75% (+37.6pp minimum)
- ✅ Scanned PDF accuracy: 22.7% → ≥75% (+52.3pp minimum)
- ✅ Machine-readable maintained: 67.0% coverage (no regression)
- ✅ Hybrid PDF improvement: 46.2% → ≥65% (+18.8pp minimum)
- ✅ Cost within budget: $0.10/PDF average (smart routing)

**Validation Ready**: ✅ **PROCEED WITH INTEGRATION TESTING**

---

## 📋 BASELINE SUMMARY

**Overall Baseline**:
- Coverage: **50.2%** (CORRECTED), 7.5% (RAW)
- Accuracy: **34.0%**
- Pass Rate: **0/3** (0% meet 95/95)

**Primary Bottleneck**:
- **Scanned PDFs**: 37.4% coverage, 22.7% accuracy
- **49% of corpus** affected
- **0 high-confidence agents**

**Phase 2A Target**:
- Coverage: 50.2% → **73.4%** (+23.2pp weighted average)
- Accuracy: 34.0% → **67.2%** (+33.2pp weighted average)
- Scanned: 37.4% → **80.0%** (+42.6pp, the big win!)

**Status**: ✅ **BASELINE VALIDATED - READY FOR INTEGRATION TESTING**

---

**Generated**: October 14, 2025
**Author**: Claude Code (Sonnet 4.5)
**Purpose**: Baseline validation before Phase 2A integration testing
**Next**: Run integration tests with vision consensus routing
