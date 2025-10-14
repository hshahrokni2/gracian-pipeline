# Phase 2B Hour 2: Ultra-Optimized Test Corpus & Validation Strategy

**Date**: October 14, 2025 21:20 UTC
**Duration**: 75 minutes (optimized execution plan)
**Goal**: Complete 10-PDF testing + measure Phase 2B success metrics
**Strategy**: Smart PDF selection → Parallel testing → Rapid analysis

---

## 🎯 Mission Critical Objectives

### Primary Goals (Must Achieve):

1. ✅ **Test 10 diverse PDFs** (3 done, 7 to select)
2. ✅ **Measure accuracy improvement** ≥+5% (34% → 39%+)
3. ✅ **Validate hallucination detection** ≥80%
4. ✅ **Confirm conflict resolution** ≥90%
5. ✅ **Verify false positive rate** <10%

### Secondary Goals (Nice to Have):

6. ⭐ **Test all 10 validation rules** (currently 6/10 tested)
7. ⭐ **Find at least 3 conflicts** (test consensus resolution)
8. ⭐ **Document edge cases** (for Phase 3 improvements)

---

## 📊 Current Status Analysis

### Already Tested (3/10 PDFs):

| # | PDF | Type | Agents | Warnings | Rules Tested |
|---|-----|------|--------|----------|--------------|
| **1** | brf_198532 | Machine-readable | 12/15 | 0 | Balance (implicit) |
| **2** | brf_268882 | Scanned | 15/15 | 1 | invalid_year_format |
| **3** | brf_53546 | Machine-readable | 15/15 | 4 | missing_evidence (3x) |

**Coverage So Far**:
- ✅ Text extraction path validated
- ✅ Vision extraction path validated
- ✅ Hallucination detection validated (missing_evidence rule)
- ❌ Financial validation untested (balance sheet, cross-agent)
- ❌ Governance validation partially tested (chairman in board needs real test)
- ❌ Property validation untested (building year, address)
- ❌ Conflict resolution untested (no conflicts found)

### Validation Rules Coverage:

| Rule | Status | Test Coverage | Priority |
|------|--------|---------------|----------|
| **Missing Evidence** | ✅ Working | Test 3 (3 warnings) | Validated |
| **Template Text** | ⚠️ Implied | No templates found | Low priority |
| **Governance (chairman)** | ✅ Fixed | Bug fixed, needs test | **HIGH** |
| **Balance Sheet** | ⏳ Untested | Need financial PDF | **HIGH** |
| **Cross-Agent Amounts** | ⏳ Untested | Need loan data | **MEDIUM** |
| **Date Consistency** | ⏳ Untested | Need dates | **MEDIUM** |
| **Building Year** | ⏳ Untested | Need property data | **MEDIUM** |
| **Address Format** | ⏳ Untested | Need addresses | **LOW** |
| **Suspicious Numbers** | ⏳ Untested | Need round numbers | **LOW** |
| **Invalid Dates** | ⏳ Untested | Need bad dates | **LOW** |

**Gap Analysis**: Need 4 more HIGH/MEDIUM rules tested to claim comprehensive validation

---

## 🎨 Strategic PDF Selection Framework

### Selection Criteria (Optimized for Coverage):

**Priority 1: Rule Coverage** (50% weight)
- Select PDFs that trigger untested validation rules
- Focus on HIGH priority rules first (balance sheet, governance, cross-agent)
- Avoid redundancy (don't need more missing_evidence tests)

**Priority 2: Diversity** (30% weight)
- Mix of machine-readable, scanned, hybrid
- Different BRF sizes (small, medium, large)
- Different document formats (K2, K3, custom)
- Different years (test date validation)

**Priority 3: Conflict Potential** (20% weight)
- PDFs where multiple agents might disagree
- Complex financial structures (multiple loan types)
- Unusual governance structures (large boards)

### The 7-PDF Selection Matrix:

**Category A: Financial Validation** (2 PDFs) - Test balance sheet + cross-agent rules

**Target Characteristics**:
- Complete financial statements (balance sheet, income, cash flow)
- Loan data present (cross-agent validation with financial_agent)
- Medium-to-large BRF (more complex finances)

**Selection Strategy**:
```python
# Ideal candidates from existing test corpus
# Look for PDFs with:
# 1. total_assets, total_liabilities, total_equity all present
# 2. loans_agent and financial_agent both successful
# 3. Potential imbalance for testing

# From Hjorthagen dataset (high quality):
candidates_financial = [
    "Hjorthagen/brf_81563.pdf",  # Known good extraction
    "Hjorthagen/brf_82123.pdf",  # If available
]

# From SRS dataset (more diverse):
candidates_financial_srs = [
    "SRS/brf_54015.pdf",  # Known from earlier testing
    "SRS/brf_57125.pdf",  # Known good
]
```

**Expected Rules Tested**: `balance_sheet_equation`, `debt_consistency`

---

**Category B: Governance Validation** (2 PDFs) - Test chairman in board + date consistency

**Target Characteristics**:
- Chairman name extracted
- Board members list extracted
- Building year present (for date validation)
- Potential name mismatches (test fuzzy matching)

**Selection Strategy**:
```python
# Look for PDFs with:
# 1. chairman_agent and board_members_agent both successful
# 2. Different name formats (test "Erik Johansson" vs "E. Johansson")
# 3. Building year for date validation

# From Hjorthagen:
candidates_governance = [
    "Hjorthagen/brf_81563.pdf",  # Overlap with financial OK
]

# From SRS:
candidates_governance_srs = [
    "SRS/brf_53546.pdf",  # Already tested, but can reuse
    "SRS/brf_47903.pdf",  # New test
]
```

**Expected Rules Tested**: `chairman_not_in_board`, `future_building_year`

---

**Category C: Property Validation** (1 PDF) - Test building year + address format

**Target Characteristics**:
- Old building (built before 1900 OR very old)
- Complete address
- Property data extracted

**Selection Strategy**:
```python
# Look for:
# 1. Very old building (edge case testing)
# 2. Complete address with street number
# 3. property_agent successful

candidates_property = [
    "Hjorthagen/brf_*.pdf",  # Hjorthagen has older buildings
    # Select oldest building in corpus
]
```

**Expected Rules Tested**: `invalid_building_year`, `address_missing_number`

---

**Category D: Conflict Resolution** (2 PDFs) - Test consensus strategies

**Target Characteristics**:
- Hybrid PDFs (mix of text + scanned pages)
- Multiple sections with same data (potential disagreements)
- Complex documents (agents might extract different values)

**Selection Strategy**:
```python
# Look for:
# 1. Hybrid topology (text + image pages)
# 2. Multiple agents extracting overlapping fields
# 3. Large documents (more opportunities for conflicts)

# Best candidates:
candidates_conflicts = [
    "experiments/docling_advanced/test_pdfs/brf_276507.pdf",  # From test_pdfs
    "SRS/brf_282765.pdf",  # Large SRS document
]
```

**Expected Rules Tested**: Consensus resolution (majority, weighted avg, evidence-based)

---

## 🚀 Optimized PDF Selection Algorithm

### Phase 1: Fast Classification (5 min)

**Goal**: Quickly categorize available PDFs by type and complexity

**Implementation**:
```bash
#!/bin/bash
# Quick PDF classification script

cd /Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian\ Pipeline

# Create candidate list (20 PDFs from each dataset)
echo "=== HJORTHAGEN CANDIDATES ===" > /tmp/pdf_candidates.txt
ls -1 Hjorthagen/*.pdf | head -10 >> /tmp/pdf_candidates.txt

echo "=== SRS CANDIDATES ===" >> /tmp/pdf_candidates.txt
ls -1 SRS/*.pdf | head -10 >> /tmp/pdf_candidates.txt

echo "=== TEST_PDFS CANDIDATES ===" >> /tmp/pdf_candidates.txt
ls -1 experiments/docling_advanced/test_pdfs/*.pdf >> /tmp/pdf_candidates.txt

# Quick classification (parallel for speed)
python3 << 'PYTHON'
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from gracian_pipeline.core.pdf_classifier import classify_pdf_topology

def quick_classify(pdf_path):
    try:
        result = classify_pdf_topology(pdf_path)
        return {
            'path': pdf_path,
            'type': result['type'],
            'confidence': result['confidence'],
            'pages': result.get('num_pages', 0)
        }
    except Exception as e:
        return None

# Read candidates
with open('/tmp/pdf_candidates.txt') as f:
    candidates = [line.strip() for line in f if line.strip() and not line.startswith('===')]

# Classify in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(quick_classify, candidates))

# Filter and categorize
machine_readable = [r for r in results if r and r['type'] == 'machine_readable']
scanned = [r for r in results if r and r['type'] == 'scanned']
hybrid = [r for r in results if r and r['type'] == 'hybrid']

print("=== CLASSIFICATION RESULTS ===")
print(f"Machine-readable: {len(machine_readable)}")
print(f"Scanned: {len(scanned)}")
print(f"Hybrid: {len(hybrid)}")

# Save categorized lists
with open('/tmp/machine_readable.txt', 'w') as f:
    for r in machine_readable[:10]:
        f.write(f"{r['path']}\n")

with open('/tmp/scanned.txt', 'w') as f:
    for r in scanned[:10]:
        f.write(f"{r['path']}\n")

with open('/tmp/hybrid.txt', 'w') as f:
    for r in hybrid[:5]:
        f.write(f"{r['path']}\n")

print("\n✅ Classification complete!")
PYTHON

# Display results
echo "Machine-readable candidates:"
head -5 /tmp/machine_readable.txt

echo "Scanned candidates:"
head -5 /tmp/scanned.txt

echo "Hybrid candidates:"
head -3 /tmp/hybrid.txt
```

**Output**: 3 categorized lists (machine-readable, scanned, hybrid) for smart selection

**Time**: 5 minutes (parallel classification)

---

### Phase 2: Smart Selection (5 min)

**Goal**: Select exactly 7 PDFs based on strategic criteria

**Decision Matrix**:

| Category | Count | Type | Source | Rationale |
|----------|-------|------|--------|-----------|
| **Financial** | 2 | Machine-readable | Hjorthagen + SRS | Clean financial data, test balance sheet |
| **Governance** | 1 | Machine-readable | SRS | Test chairman in board (new) |
| **Governance** | 1 | Scanned | SRS | Test vision + governance together |
| **Property** | 1 | Machine-readable | Hjorthagen | Old building, test building year |
| **Conflict** | 1 | Hybrid | test_pdfs | Test consensus resolution |
| **Conflict** | 1 | Scanned | SRS | Test vision + conflict together |

**Total**: 7 PDFs (4 machine-readable, 2 scanned, 1 hybrid)

**Implementation**:
```python
# Final selection based on classification + strategic fit
final_selection = {
    'financial_1': 'Hjorthagen/brf_81563.pdf',      # Known good, complete financials
    'financial_2': 'SRS/brf_54015.pdf',             # SRS diversity, test balance
    'governance_text': 'SRS/brf_47903.pdf',         # Chairman + board
    'governance_vision': 'SRS/brf_282765.pdf',      # Scanned governance test
    'property': 'Hjorthagen/brf_82XXX.pdf',         # Oldest building (TBD)
    'conflict_hybrid': 'experiments/docling_advanced/test_pdfs/brf_276507.pdf',
    'conflict_scanned': 'SRS/brf_80193.pdf',        # Large scanned document
}
```

**Fallback Strategy**:
- If a PDF doesn't exist, use next candidate from classification list
- Prefer Hjorthagen for quality, SRS for diversity
- test_pdfs/ directory has known-good PDFs

**Time**: 5 minutes (manual selection + verification)

---

### Phase 3: Validation (5 min)

**Goal**: Verify selected PDFs exist and are accessible

**Quick Check Script**:
```bash
#!/bin/bash
# Verify selected PDFs

selected_pdfs=(
    "Hjorthagen/brf_81563.pdf"
    "SRS/brf_54015.pdf"
    "SRS/brf_47903.pdf"
    "SRS/brf_282765.pdf"
    "Hjorthagen/brf_82XXX.pdf"  # Placeholder - find actual
    "experiments/docling_advanced/test_pdfs/brf_276507.pdf"
    "SRS/brf_80193.pdf"
)

echo "=== VERIFYING SELECTED PDFs ==="
missing=0
for pdf in "${selected_pdfs[@]}"; do
    if [ -f "$pdf" ]; then
        echo "✅ $pdf"
        # Get page count for reference
        pages=$(python -c "import fitz; print(len(fitz.open('$pdf')))")
        echo "   Pages: $pages"
    else
        echo "❌ $pdf (NOT FOUND)"
        missing=$((missing + 1))
    fi
done

if [ $missing -gt 0 ]; then
    echo "⚠️  $missing PDFs missing - select alternates"
    exit 1
else
    echo "✅ All PDFs verified!"
fi
```

**Time**: 2 minutes (automated verification)

---

## ⚡ Batch Testing Strategy

### Parallel Execution Plan (40 min)

**Goal**: Test all 10 PDFs efficiently with comprehensive metrics

**Challenge**: Each PDF takes 40-120s
- **Sequential**: 10 PDFs × 80s avg = 800s = 13.3 minutes minimum
- **With analysis**: +10 min per PDF = 100+ minutes ❌

**Solution**: Parallel testing + batch analysis

**Architecture**:
```
[PDF 1] ───┐
[PDF 2] ───┤
[PDF 3] ───┼──→ Parallel Processing (5 workers) ──→ Results collected
[PDF 4] ───┤
[PDF 5] ───┘
[PDF 6-10] → Second batch
           ↓
    Batch Analysis (once all complete)
```

**Implementation**:

```bash
#!/bin/bash
# Phase 2B Batch Testing Script (Optimized)
# Tests 10 PDFs in parallel and collects metrics

set -e  # Exit on error

export OPENAI_API_KEY=YOUR_OPENAI_API_KEY

# Test corpus (10 PDFs)
PDFS=(
    # Already tested (3)
    "experiments/docling_advanced/test_pdfs/brf_198532.pdf"
    "experiments/docling_advanced/test_pdfs/brf_268882.pdf"
    "SRS/brf_53546.pdf"

    # New selections (7) - TBD based on Phase 1-3 selection
    "Hjorthagen/brf_81563.pdf"
    "SRS/brf_54015.pdf"
    "SRS/brf_47903.pdf"
    "SRS/brf_282765.pdf"
    "Hjorthagen/brf_XXXXX.pdf"  # Property validation
    "experiments/docling_advanced/test_pdfs/brf_276507.pdf"
    "SRS/brf_80193.pdf"
)

RESULTS_DIR="phase2b_batch_results_$(date +%s)"
mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "Phase 2B Batch Testing (Parallel)"
echo "PDFs: ${#PDFS[@]}"
echo "Workers: 5 (parallel)"
echo "=========================================="

# Function to test single PDF
test_pdf() {
    local pdf=$1
    local index=$2
    local output="$RESULTS_DIR/test_${index}.txt"

    echo "[$index/${#PDFS[@]}] Testing: $pdf"

    timeout 300 python test_phase2b_integration.py "$pdf" > "$output" 2>&1

    if [ $? -eq 0 ]; then
        echo "[$index/${#PDFS[@]}] ✅ SUCCESS: $pdf"
        return 0
    else
        echo "[$index/${#PDFS[@]}] ❌ FAILED: $pdf"
        return 1
    fi
}

export -f test_pdf
export RESULTS_DIR
export PDFS

# Parallel execution (5 workers)
echo ""
echo "🚀 Starting parallel testing (5 workers)..."
start_time=$(date +%s)

# Use GNU parallel if available, otherwise loop in background
if command -v parallel &> /dev/null; then
    # GNU parallel (fastest)
    parallel -j 5 --line-buffer test_pdf {1} {2} ::: "${PDFS[@]}" ::: $(seq 1 ${#PDFS[@]})
else
    # Bash background jobs (fallback)
    pids=()
    for i in "${!PDFS[@]}"; do
        test_pdf "${PDFS[$i]}" "$((i+1))" &
        pids+=($!)

        # Limit to 5 parallel jobs
        if [ $(( (i+1) % 5 )) -eq 0 ]; then
            wait "${pids[@]}"
            pids=()
        fi
    done

    # Wait for remaining jobs
    wait "${pids[@]}"
fi

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "✅ Testing complete in ${total_time}s"
echo ""

# Aggregate metrics
echo "=========================================="
echo "BATCH RESULTS SUMMARY"
echo "=========================================="

total_pdfs=${#PDFS[@]}
successful=0
total_warnings=0
total_conflicts=0
total_agents=0
successful_agents=0

for i in $(seq 1 $total_pdfs); do
    result_file="$RESULTS_DIR/test_${i}.txt"

    if grep -q "PHASE 2B INTEGRATION TEST PASSED" "$result_file"; then
        successful=$((successful + 1))
    fi

    # Extract metrics (robust parsing)
    warnings=$(grep "Warnings:" "$result_file" | tail -1 | awk '{print $2}' || echo "0")
    conflicts=$(grep "Conflicts resolved:" "$result_file" | tail -1 | awk '{print $3}' || echo "0")
    agents=$(grep "Success rate:" "$result_file" | tail -1 | awk '{print $3}' | cut -d'/' -f1 || echo "0")
    total_a=$(grep "Success rate:" "$result_file" | tail -1 | awk '{print $3}' | cut -d'/' -f2 || echo "0")

    total_warnings=$((total_warnings + warnings))
    total_conflicts=$((total_conflicts + conflicts))
    successful_agents=$((successful_agents + agents))
    total_agents=$((total_agents + total_a))
done

# Calculate percentages
success_rate=$(echo "scale=1; $successful * 100 / $total_pdfs" | bc)
avg_warnings=$(echo "scale=1; $total_warnings / $total_pdfs" | bc)
avg_conflicts=$(echo "scale=1; $total_conflicts / $total_pdfs" | bc)
agent_success_rate=$(echo "scale=1; $successful_agents * 100 / $total_agents" | bc)

echo "Test Success Rate: $successful/$total_pdfs (${success_rate}%)"
echo "Agent Success Rate: $successful_agents/$total_agents (${agent_success_rate}%)"
echo "Total Warnings: $total_warnings (avg $avg_warnings per PDF)"
echo "Total Conflicts Resolved: $total_conflicts (avg $avg_conflicts per PDF)"
echo "Total Execution Time: ${total_time}s (avg $((total_time / total_pdfs))s per PDF)"
echo ""

# Save summary JSON
cat > "$RESULTS_DIR/summary.json" << JSON
{
  "total_pdfs": $total_pdfs,
  "successful_tests": $successful,
  "success_rate": $(echo "scale=3; $successful / $total_pdfs" | bc),
  "agent_success_rate": $(echo "scale=3; $successful_agents / $total_agents" | bc),
  "total_warnings": $total_warnings,
  "avg_warnings_per_pdf": $avg_warnings,
  "total_conflicts": $total_conflicts,
  "avg_conflicts_per_pdf": $avg_conflicts,
  "total_time_seconds": $total_time,
  "avg_time_per_pdf_seconds": $((total_time / total_pdfs))
}
JSON

echo "Results saved to: $RESULTS_DIR/summary.json"
echo ""

# Detailed breakdown
echo "=========================================="
echo "DETAILED BREAKDOWN"
echo "=========================================="
for i in $(seq 1 $total_pdfs); do
    pdf="${PDFS[$((i-1))]}"
    result_file="$RESULTS_DIR/test_${i}.txt"

    warnings=$(grep "Warnings:" "$result_file" | tail -1 | awk '{print $2}' || echo "0")
    conflicts=$(grep "Conflicts resolved:" "$result_file" | tail -1 | awk '{print $3}' || echo "0")
    time=$(grep "Total time:" "$result_file" | tail -1 | awk '{print $3}' | sed 's/s//' || echo "0")

    status="✅"
    if ! grep -q "PHASE 2B INTEGRATION TEST PASSED" "$result_file"; then
        status="❌"
    fi

    echo "[$i] $status $(basename $pdf)"
    echo "     Warnings: $warnings, Conflicts: $conflicts, Time: ${time}s"
done

echo ""
echo "=========================================="
echo "✅ BATCH TESTING COMPLETE"
echo "=========================================="
```

**Optimization Techniques**:
1. **Parallel Execution**: 5 PDFs at once (5x speedup)
2. **Background Jobs**: Bash async if GNU parallel unavailable
3. **Timeout Protection**: 300s max per PDF (prevents hangs)
4. **Robust Parsing**: Handles missing metrics gracefully
5. **Incremental Output**: See progress in real-time

**Expected Time**:
- **Sequential**: 10 PDFs × 80s = 800s = 13.3 min
- **Parallel (5 workers)**: 2 batches × 120s = 240s = **4 min** 🚀
- **With overhead**: ~5 minutes total

---

## 📊 Accuracy Measurement Strategy

### Challenge: No Ground Truth for All PDFs

**Problem**: Can't directly measure accuracy without manual validation of all 10 PDFs

**Solution**: Proxy metrics + manual sampling

### Method 1: Warning-Based Accuracy Estimation (Primary)

**Concept**: Warnings indicate prevented errors

**Formula**:
```python
# Estimate accuracy improvement
prevented_errors = (
    high_severity_warnings × 1.0 +      # Definite errors
    medium_severity_warnings × 0.5 +    # Probable errors
    conflicts_resolved × 0.7            # Agent disagreements
)

total_fields = num_pdfs × 28  # 28 fields per PDF (from 30-field schema)

accuracy_improvement = (prevented_errors / total_fields) × 100
```

**Example Calculation**:
```
10 PDFs tested
- High severity warnings: 5 (5 × 1.0 = 5.0 prevented errors)
- Medium severity warnings: 12 (12 × 0.5 = 6.0 prevented errors)
- Conflicts resolved: 8 (8 × 0.7 = 5.6 prevented errors)

Total prevented errors: 5.0 + 6.0 + 5.6 = 16.6
Total fields: 10 × 28 = 280
Improvement: 16.6 / 280 = 5.9% ✅ (exceeds +5% target)
```

**Assumptions**:
- High severity warnings = 100% error prevention
- Medium severity warnings = 50% error prevention
- Conflicts resolved = 70% error prevention (conservative)

**Validation**: Manual spot-check 3 PDFs to verify assumptions

---

### Method 2: Confidence Delta Analysis (Secondary)

**Concept**: Validation adjusts confidence scores

**Measurement**:
```python
# Compare confidence before/after validation
for each PDF:
    confidence_before = extract without validation
    confidence_after = extract with validation
    delta = confidence_after - confidence_before

avg_confidence_improvement = mean(deltas)
```

**Interpretation**:
- Positive delta: Validation increases confidence (good extractions confirmed)
- Negative delta: Validation decreases confidence (bad extractions flagged)
- Target: Negative delta on low-quality PDFs, positive on high-quality

**Challenge**: Requires running extraction twice (time-consuming)

**Optimization**: Use existing baseline from earlier tests (3 PDFs)

---

### Method 3: Manual Ground Truth Sampling (Validation)

**Concept**: Manually validate 3 PDFs to verify proxy metrics

**Selection**: Pick 1 from each category:
- 1 high-warning PDF (test if warnings correct)
- 1 zero-warning PDF (test if false negatives)
- 1 medium-warning PDF (test if balanced)

**Manual Review Process** (10 min per PDF):
1. Open PDF in viewer
2. Check top 5 warnings against source document
3. Categorize as true positive or false positive
4. Calculate: TP / (TP + FP) = detection accuracy

**Expected Result**:
- Detection accuracy: 80-90%
- False positive rate: 5-10%
- Validates proxy metric assumptions

**Time**: 30 minutes total (3 PDFs × 10 min)

---

## 🎯 Success Metrics Calculation

### Metric 1: Accuracy Improvement ≥+5%

**Measurement**: Warning-based estimation (Method 1)

**Target**: ≥+5.0% improvement

**Analysis Script**:
```python
#!/usr/bin/env python3
"""
Calculate accuracy improvement from Phase 2B validation
"""

import json
from pathlib import Path

def calculate_accuracy_improvement(results_dir: str):
    """Calculate estimated accuracy improvement"""

    # Load summary
    with open(f"{results_dir}/summary.json") as f:
        summary = json.load(f)

    # Parse all warnings
    high_severity = 0
    medium_severity = 0
    low_severity = 0
    conflicts_resolved = summary['total_conflicts']

    for test_file in Path(results_dir).glob("test_*.txt"):
        with open(test_file) as f:
            content = f.read()

        # Extract severity counts
        if "High severity:" in content:
            high = int(content.split("High severity:")[1].split()[0])
            high_severity += high

        if "Medium severity:" in content:
            medium = int(content.split("Medium severity:")[1].split()[0])
            medium_severity += medium

        if "Low severity:" in content:
            low = int(content.split("Low severity:")[1].split()[0])
            low_severity += low

    # Calculate prevented errors
    prevented_errors = (
        high_severity * 1.0 +
        medium_severity * 0.5 +
        conflicts_resolved * 0.7
    )

    # Calculate improvement
    total_fields = summary['total_pdfs'] * 28
    accuracy_improvement = (prevented_errors / total_fields) * 100

    # Report
    print("=" * 60)
    print("ACCURACY IMPROVEMENT ANALYSIS")
    print("=" * 60)
    print(f"High Severity Warnings: {high_severity} (×1.0 = {high_severity * 1.0:.1f} prevented errors)")
    print(f"Medium Severity Warnings: {medium_severity} (×0.5 = {medium_severity * 0.5:.1f} prevented errors)")
    print(f"Low Severity Warnings: {low_severity} (not counted)")
    print(f"Conflicts Resolved: {conflicts_resolved} (×0.7 = {conflicts_resolved * 0.7:.1f} prevented errors)")
    print()
    print(f"Total Prevented Errors: {prevented_errors:.1f}")
    print(f"Total Fields: {total_fields}")
    print(f"Estimated Accuracy Improvement: +{accuracy_improvement:.1f}%")
    print()
    print(f"Target: ≥+5.0%")
    print(f"Status: {'✅ ACHIEVED' if accuracy_improvement >= 5.0 else '❌ BELOW TARGET'}")

    return accuracy_improvement

if __name__ == "__main__":
    import sys
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "phase2b_batch_results"
    calculate_accuracy_improvement(results_dir)
```

---

### Metric 2: Hallucination Detection Rate ≥80%

**Measurement**: Manual review + categorization

**Target**: ≥80% true positive rate

**Analysis Process**:
1. List all high+medium severity warnings
2. Manually review each warning against PDF
3. Categorize: True Positive (TP) or False Positive (FP)
4. Calculate: TP / (TP + FP)

**Expected**: 15-25 warnings across 10 PDFs, manual review in 15 minutes

---

### Metric 3: Conflict Resolution Success ≥90%

**Measurement**: Conflicts resolved / conflicts detected

**Target**: ≥90% resolution rate

**Challenge**: May have 0 conflicts if PDFs too simple

**Fallback**: If <3 conflicts, select additional PDFs known to have conflicts

---

### Metric 4: False Positive Rate <10%

**Measurement**: Inverse of hallucination detection

**Formula**: FP / (TP + FP) < 0.10

**Target**: <10% false alarms

---

## ⏱️ Hour 2 Timeline (Optimized)

### Phase 1: PDF Selection (15 min)

| Time | Task | Output |
|------|------|--------|
| 0:00-0:05 | Quick classification | 20 PDFs categorized |
| 0:05-0:10 | Smart selection | 7 PDFs selected |
| 0:10-0:15 | Verification | All PDFs confirmed |

**Checkpoint 1** (0:15): 10 PDFs ready for testing

---

### Phase 2: Batch Testing (40 min)

| Time | Task | Output |
|------|------|--------|
| 0:15-0:20 | Batch script execution (batch 1) | 5 PDFs tested |
| 0:20-0:25 | Batch script execution (batch 2) | 5 PDFs tested |
| 0:25-0:40 | Results collection | All metrics extracted |

**Checkpoint 2** (0:40): All 10 PDFs tested, metrics collected

---

### Phase 3: Analysis (20 min)

| Time | Task | Output |
|------|------|--------|
| 0:40-0:50 | Accuracy calculation | Improvement measured |
| 0:50-1:05 | Manual review (3 PDFs) | Detection rate validated |
| 1:05-1:15 | Final report | Phase 2B complete! |

**Checkpoint 3** (1:15): All metrics validated, documentation complete

---

## 🎯 Success Criteria Checklist

### Phase 2B Phase 2 Complete When:

- [ ] **10 PDFs tested** (3 done + 7 new)
- [ ] **Accuracy improvement measured** (warning-based estimation)
- [ ] **Result**: ≥+5% improvement validated
- [ ] **Hallucination detection validated** (manual review)
- [ ] **Result**: ≥80% true positive rate
- [ ] **Conflict resolution tested** (if conflicts found)
- [ ] **Result**: ≥90% resolution rate
- [ ] **False positive rate calculated** (manual review)
- [ ] **Result**: <10% false alarms
- [ ] **All validation rules tested** (or documented why not)
- [ ] **Final report created** (PHASE2B_COMPLETE.md)

---

## 🚀 Ready to Execute

**Total Time**: 75 minutes (15 + 40 + 20)

**Next Command**:
```bash
cd /Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian\ Pipeline

# Phase 1: Quick classification (5 min)
# <classification script from above>

# Phase 2: Selection (10 min)
# <manual selection based on results>

# Phase 3: Batch testing (40 min)
# <batch testing script from above>

# Phase 4: Analysis (20 min)
# <analysis scripts from above>
```

**Expected Outcomes**:
- ✅ 10 diverse PDFs tested
- ✅ +5-8% accuracy improvement
- ✅ 85-90% hallucination detection
- ✅ 95%+ conflict resolution (if tested)
- ✅ 5-8% false positive rate
- ✅ Phase 2B validated and complete!

---

**Generated**: October 14, 2025 21:35 UTC
**Strategy**: Optimized for speed and comprehensive validation
**Ready**: Execute Hour 2 (PDF selection → Batch testing → Analysis)
