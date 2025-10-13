# Ultrathinking: Phase 2 Perfect Integration Strategy

**Date**: October 13, 2025
**Context**: Days 1-3 complete (80 tests passing), Proof-of-Concept validated
**Goal**: Integrate schema_v7.py with optimal_brf_pipeline.py for real-world extraction testing

---

## 🎯 Phase 2 Objectives (from ULTRATHINKING_NEXT_STEP_STRATEGY.md)

**What Phase 2 Delivers** (2-3 hours):
1. Create integration adapter (converts pipeline output → schema_v7 format)
2. Test on brf_268882.pdf (regression test)
3. Validate quality metrics on real data
4. Identify gaps or issues early
5. Generate real quality metrics

**Expected Outcome**:
- Real-world validation of schema_v7.0 architecture
- Quality metrics on actual BRF PDF extraction
- Clear decision on whether to continue with Days 4-5 or scale Swedish-first pattern

---

## 📊 Current State Analysis

### **What We Have**:

#### **Schema V7.0** (Days 1-3):
- `schema_v7.py` - ValidationResult enum + YearlyFinancialData with Swedish-first pattern
- `schema_v7_validation.py` - Tolerant comparison + quality scoring (520 lines)
- 80 tests passing (100% pass rate)
- Proof-of-concept demo validated

#### **Optimal BRF Pipeline** (October 12 breakthrough):
- `optimal_brf_pipeline.py` - Complete extraction pipeline (1,387 lines)
- **86.7% coverage, 92% accuracy** on brf_198532.pdf (Oct 12)
- Outputs JSON with `agent_results` dict:
  ```json
  {
    "agent_results": {
      "property_agent": {"status": "success", "data": {...}, "evidence_pages": [...]},
      "governance_agent": {"status": "success", "data": {...}, "evidence_pages": [...]},
      "financial_agent": {"status": "success", "data": {...}, "evidence_pages": [...]}
    }
  }
  ```

### **The Gap**:
- Pipeline outputs `agent_results` dict with agent-specific data
- Schema v7 expects `YearlyFinancialData` model with Swedish-first fields
- **Need**: Adapter to convert pipeline output → schema_v7 format

---

## 🤔 Integration Strategy Options

### **Option A: Modify Pipeline Directly** ❌ NOT RECOMMENDED

**What**:
- Modify `optimal_brf_pipeline.py` to output `YearlyFinancialData` directly
- Replace JSON dict with Pydantic model

**Pros**:
- Clean integration
- Pipeline natively uses v7 schema

**Cons**:
- ❌ **HIGH RISK**: Breaks existing pipeline (used in production)
- ❌ **TIME-CONSUMING**: Need to refactor 1,387 lines
- ❌ **BLOCKS TESTING**: Can't test until refactor complete
- ❌ **NO ROLLBACK**: Hard to revert if issues found

**Risk**: **HIGH** - Don't break working code

---

### **Option B: Create Adapter Wrapper** ⭐ **RECOMMENDED**

**What**:
- Create `schema_v7_adapter.py` that:
  1. Takes pipeline JSON output as input
  2. Extracts relevant fields from `agent_results`
  3. Maps to `YearlyFinancialData` model
  4. Calculates quality metrics using `schema_v7_validation.py`
  5. Generates comparison report

**Pros**:
- ✅ **ZERO RISK**: Doesn't modify working pipeline
- ✅ **FAST**: ~200 lines of adapter code
- ✅ **TESTABLE**: Can test immediately on existing results
- ✅ **REVERSIBLE**: Easy to iterate or discard
- ✅ **ADDITIVE**: Adds v7 validation without breaking existing code

**Cons**:
- ⚠️ Requires maintaining adapter layer (temporary)
- ⚠️ Not "native" integration (can refactor later)

**Risk**: **LOW** - Adapter is isolated, easy to fix if issues

---

### **Option C: Create New Extraction Script** ❌ NOT RECOMMENDED FOR PHASE 2

**What**:
- Create `schema_v7_extraction_pipeline.py` from scratch
- Use schema_v7 natively from the start
- Reimplement all extraction logic

**Pros**:
- Clean architecture
- Native v7 integration

**Cons**:
- ❌ **TIME-CONSUMING**: 8-10 hours to reimplement
- ❌ **DUPLICATES CODE**: Need to copy working extraction logic
- ❌ **NOT PHASE 2 GOAL**: Phase 2 is about validation, not reimplementation
- ❌ **PREMATURE**: Should validate architecture before building new pipeline

**Risk**: **HIGH** - Too much work for validation phase

---

## ✅ Recommended Strategy: Option B (Adapter Wrapper)

### **Why Option B is Optimal**:

1. **Validates Architecture** (Phase 2 goal)
   - Tests schema_v7 with real extraction data
   - Validates quality scoring on real PDFs
   - Identifies gaps without risk

2. **Fast Implementation** (2-3 hours)
   - 200 lines of adapter code
   - Reuses existing pipeline (86.7% coverage proven)
   - No refactoring needed

3. **Zero Risk**
   - Doesn't modify working pipeline
   - Easy to iterate
   - Can discard if approach doesn't work

4. **Practical Feedback**
   - Real quality metrics on actual data
   - Reveals integration issues early
   - Informs decision on Days 4-5 vs scaling

---

## 📋 Implementation Plan: Adapter Wrapper (Option B)

### **Phase 2A: Create Adapter** (1 hour)

**File**: `schema_v7_adapter.py` (~200 lines)

**What It Does**:
```python
# Input: optimal_brf_pipeline.py JSON output
pipeline_result = {
    "agent_results": {
        "financial_agent": {
            "status": "success",
            "data": {
                "annual_revenue": 12345.67,
                "equity_ratio": 45.8,
                "annual_fee_per_sqm": 125.50
            },
            "evidence_pages": [5, 6, 7]
        }
    }
}

# Output: schema_v7 YearlyFinancialData + quality metrics
year_data = YearlyFinancialData(
    year=2024,
    nettoomsättning_tkr=12345.67,      # Swedish primary
    soliditet_procent=45.8,             # Swedish primary
    årsavgift_per_kvm=125.50,           # Swedish primary
    data_source="financial_agent",
    extraction_confidence=0.92
)

quality = calculate_extraction_quality(year_data)
# → {'coverage': 0.48, 'overall': 0.14, ...}
```

**Key Functions**:
1. `load_pipeline_result(json_path)` - Load pipeline JSON
2. `extract_financial_year(agent_results)` - Extract yearly financial data
3. `map_to_swedish_fields(data_dict)` - Map English → Swedish field names
4. `calculate_v7_quality(year_data)` - Calculate schema_v7 quality metrics
5. `generate_comparison_report(pipeline_result, v7_result)` - Compare old vs new

**Field Mapping** (English → Swedish):
```python
FIELD_MAPPING = {
    # Financial fields
    'annual_revenue': 'nettoomsättning_tkr',
    'net_revenue': 'nettoomsättning_tkr',
    'revenue': 'nettoomsättning_tkr',

    # Ratios
    'equity_ratio': 'soliditet_procent',
    'solidarity_percent': 'soliditet_procent',

    # Fees
    'annual_fee_per_sqm': 'årsavgift_per_kvm',
    'fee_per_sqm': 'årsavgift_per_kvm',

    # ... more mappings
}
```

---

### **Phase 2B: Test on Regression PDF** (30 min)

**Goal**: Run adapter on brf_268882.pdf results

**Steps**:
1. Run `optimal_brf_pipeline.py` on brf_268882.pdf (if not already done)
2. Run adapter on pipeline output JSON
3. Generate v7 quality report
4. Compare with Oct 12 results (86.7% coverage baseline)

**Expected Output**:
```
📊 Schema V7.0 Quality Report - brf_268882.pdf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pipeline Extraction:
  ✅ Status: success
  📄 Sections detected: 50
  🎯 Agents run: 10
  📊 Agent success rate: 80% (8/10)

Schema V7.0 Conversion:
  📅 Year: 2024
  🇸🇪 Swedish fields populated: 12/20 (60%)
  🏴󠁧󠁢󠁥󠁮󠁧󠁿 English aliases synced: 12/20 (100%)
  📄 Data source: "financial_agent, property_agent"
  💪 Extraction confidence: 0.85

Quality Metrics (schema_v7_validation.py):
  Coverage:    60.0% (12/20 fields)
  Validation:  85.0% (VALID: 10, WARNING: 2, ERROR: 0)
  Confidence:  85.0% (avg extraction confidence)
  Evidence:    90.0% (9/10 agents cited evidence_pages)
  Overall:     80.0% ✅ (weighted average)

Comparison with Oct 12 Results:
  Pipeline: 86.7% coverage, 92% accuracy
  Schema v7: 60.0% coverage, 85% confidence
  Gap: Schema v7 expects 20 Swedish-first fields, pipeline extracts different fields
```

---

### **Phase 2C: Validate Quality Metrics** (30 min)

**Goal**: Verify schema_v7_validation.py works on real data

**Tests**:
1. **Tolerant Float Comparison**:
   - Pipeline: `annual_revenue = 12345.67`
   - Ground truth: `annual_revenue = 12400.00`
   - Test: `tolerant_float_compare(12345.67, 12400.00)` → `(True, 0.0044)` ✅

2. **Quality Scoring**:
   - Test: `calculate_extraction_quality(year_data)`
   - Verify: All 4 metrics (coverage, validation, confidence, evidence) calculated
   - Check: Overall score is weighted average

3. **Multi-Source Validation**:
   - If multiple agents extract same field (e.g., financial_agent + notes_agent)
   - Test: `compare_multi_source_values([value1, value2, value3])`
   - Verify: Consensus logic works (2/3 → WARNING)

---

### **Phase 2D: Document Issues & Next Steps** (30 min)

**Goal**: Identify gaps and recommend next action

**Analysis Questions**:
1. **Does schema_v7 architecture work on real data?** (YES/NO + evidence)
2. **Are quality metrics informative?** (coverage, validation, confidence, evidence)
3. **What fields are missing?** (pipeline extracts X, schema expects Y)
4. **Is Swedish-first pattern practical?** (mapping difficulty, edge cases)
5. **What integration issues were found?** (type mismatches, missing fields, etc.)

**Decision Matrix**:
| Finding | Next Action |
|---------|-------------|
| ✅ Architecture works, metrics informative | Continue with Days 4-5 OR scale Swedish-first |
| ⚠️ Minor issues found (field mapping, types) | Fix issues (30-60 min), then decide |
| ❌ Major issues found (architecture doesn't fit) | Refactor schema_v7 (2-3 hours), then retry |

---

## 🎯 Implementation: Adapter Code Structure

### **File**: `schema_v7_adapter.py`

```python
#!/usr/bin/env python3
"""
Schema V7.0 Adapter - Converts optimal_brf_pipeline.py output to schema_v7 format.

Purpose: Validate schema_v7 architecture with real extraction data (Phase 2).

Usage:
    python schema_v7_adapter.py results/optimal_pipeline/brf_268882_optimal_result.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from schema_v7 import YearlyFinancialData, ValidationResult
from schema_v7_validation import (
    calculate_extraction_quality,
    tolerant_float_compare,
    validate_with_tolerance
)


# ============================================================
# Field Mapping Configuration
# ============================================================

# Maps pipeline field names (English) → schema_v7 field names (Swedish)
FIELD_MAPPING = {
    # Revenue fields
    'annual_revenue': 'nettoomsättning_tkr',
    'net_revenue': 'nettoomsättning_tkr',
    'revenue': 'nettoomsättning_tkr',
    'total_revenue': 'nettoomsättning_tkr',

    # Result fields
    'result_after_financial': 'resultat_efter_finansiella_tkr',
    'net_income': 'resultat_efter_finansiella_tkr',

    # Equity ratio
    'equity_ratio': 'soliditet_procent',
    'solidarity': 'soliditet_procent',
    'solidarity_percent': 'soliditet_procent',

    # Annual fees
    'annual_fee_per_sqm': 'årsavgift_per_kvm',
    'fee_per_sqm': 'årsavgift_per_kvm',
    'monthly_fee_per_sqm': 'årsavgift_per_kvm',  # Convert monthly → annual

    # Debt
    'debt_per_sqm': 'skuld_per_kvm_total',
    'debt_per_total_sqm': 'skuld_per_kvm_total',
    'debt_per_residential_sqm': 'skuld_per_kvm_boyta',

    # Energy
    'energy_cost_per_sqm': 'energikostnad_per_kvm',

    # Interest sensitivity
    'interest_sensitivity': 'räntekänslighet_procent',

    # Savings
    'savings_per_sqm': 'avsättning_per_kvm',

    # Fee percentage
    'annual_fees_percent_of_revenue': 'årsavgift_andel_intäkter_procent'
}


# ============================================================
# Core Adapter Functions
# ============================================================

def load_pipeline_result(json_path: str) -> Dict[str, Any]:
    """Load optimal_brf_pipeline.py JSON output."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_year_from_filename(filename: str) -> Optional[int]:
    """
    Extract year from PDF filename or metadata.

    Examples:
        "brf_268882.pdf" → 2024 (default to current year)
        "brf_268882_2023.pdf" → 2023
    """
    # Try to extract from filename
    import re
    match = re.search(r'_(\d{4})\.pdf', filename)
    if match:
        return int(match.group(1))

    # Default to current year
    return datetime.now().year


def map_to_swedish_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map English field names to Swedish field names.

    Args:
        data: Dict with English field names (from pipeline)

    Returns:
        Dict with Swedish field names (for schema_v7)
    """
    mapped = {}

    for english_key, value in data.items():
        # Look up Swedish equivalent
        swedish_key = FIELD_MAPPING.get(english_key.lower(), english_key)

        # Special handling for monthly → annual conversion
        if english_key.lower() == 'monthly_fee_per_sqm' and isinstance(value, (int, float)):
            value = value * 12  # Convert monthly to annual

        mapped[swedish_key] = value

    return mapped


def extract_financial_year(
    agent_results: Dict[str, Dict],
    year: int
) -> YearlyFinancialData:
    """
    Extract YearlyFinancialData from agent_results.

    Args:
        agent_results: Dict of agent extraction results
        year: Fiscal year

    Returns:
        YearlyFinancialData instance
    """
    # Combine data from all agents
    combined_data = {}
    evidence_pages = []
    data_sources = []
    confidence_scores = []

    for agent_id, result in agent_results.items():
        if result.get('status') == 'success' and 'data' in result:
            # Extract data
            agent_data = result['data']
            combined_data.update(agent_data)

            # Track metadata
            if result.get('evidence_pages'):
                evidence_pages.extend(result['evidence_pages'])
            data_sources.append(agent_id)

            # Extract confidence if available
            if 'confidence' in result:
                confidence_scores.append(result['confidence'])

    # Map English → Swedish
    swedish_data = map_to_swedish_fields(combined_data)

    # Calculate average confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

    # Create YearlyFinancialData
    year_data = YearlyFinancialData(
        year=year,
        **swedish_data,
        data_source=", ".join(data_sources),
        extraction_confidence=avg_confidence
    )

    return year_data


def calculate_v7_quality(year_data: YearlyFinancialData) -> Dict[str, float]:
    """
    Calculate schema_v7 quality metrics.

    Uses schema_v7_validation.py functions to calculate:
    - Coverage: % fields populated
    - Validation: % passing validation
    - Confidence: avg extraction confidence
    - Evidence: % with evidence tracking
    - Overall: weighted average
    """
    return calculate_extraction_quality(year_data)


def generate_comparison_report(
    pipeline_result: Dict[str, Any],
    year_data: YearlyFinancialData,
    quality: Dict[str, float]
) -> str:
    """
    Generate comparison report: pipeline results vs schema_v7.

    Returns markdown report.
    """
    pdf_name = Path(pipeline_result['pdf']).name

    # Extract pipeline stats
    agent_results = pipeline_result.get('agent_results', {})
    total_agents = len(agent_results)
    successful_agents = sum(1 for r in agent_results.values() if r.get('status') == 'success')
    pipeline_coverage = successful_agents / total_agents if total_agents > 0 else 0.0

    # Count schema v7 fields populated
    swedish_fields = [
        'nettoomsättning_tkr', 'resultat_efter_finansiella_tkr', 'soliditet_procent',
        'årsavgift_per_kvm', 'skuld_per_kvm_total', 'skuld_per_kvm_boyta',
        'räntekänslighet_procent', 'energikostnad_per_kvm', 'avsättning_per_kvm',
        'årsavgift_andel_intäkter_procent'
    ]
    swedish_populated = sum(1 for field in swedish_fields if getattr(year_data, field, None) is not None)

    # Generate report
    report = f"""
# Schema V7.0 Quality Report - {pdf_name}

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Pipeline Extraction (optimal_brf_pipeline.py)

- **Status**: {"✅ success" if pipeline_coverage > 0.5 else "❌ failed"}
- **Sections detected**: {pipeline_result.get('structure', {}).get('num_sections', 0)}
- **Agents run**: {total_agents}
- **Agent success rate**: {pipeline_coverage:.1%} ({successful_agents}/{total_agents})
- **Total time**: {pipeline_result.get('total_time', 0):.1f}s
- **Total cost**: ${pipeline_result.get('total_cost', 0):.2f}

## 🇸🇪 Schema V7.0 Conversion

- **Year**: {year_data.year}
- **Swedish fields populated**: {swedish_populated}/{len(swedish_fields)} ({swedish_populated/len(swedish_fields):.1%})
- **English aliases synced**: {swedish_populated}/{len(swedish_fields)} (100% - automatic)
- **Data source**: "{year_data.data_source or 'unknown'}"
- **Extraction confidence**: {year_data.extraction_confidence or 0.0:.1%}

### Populated Fields:

"""

    # List populated Swedish fields
    for field in swedish_fields:
        value = getattr(year_data, field, None)
        if value is not None:
            report += f"- **{field}**: {value}\n"

    report += f"""

## ✅ Quality Metrics (schema_v7_validation.py)

| Metric | Score | Status |
|--------|-------|--------|
| **Coverage** | {quality['coverage']:.1%} | {'✅' if quality['coverage'] >= 0.75 else '⚠️'} |
| **Validation** | {quality['validation']:.1%} | {'✅' if quality['validation'] >= 0.85 else '⚠️'} |
| **Confidence** | {quality['confidence']:.1%} | {'✅' if quality['confidence'] >= 0.80 else '⚠️'} |
| **Evidence** | {quality['evidence']:.1%} | {'✅' if quality['evidence'] >= 0.90 else '⚠️'} |
| **Overall** | {quality['overall']:.1%} | {'✅' if quality['overall'] >= 0.75 else '⚠️'} |

## 📈 Comparison

| Metric | Pipeline | Schema V7 | Gap |
|--------|----------|-----------|-----|
| **Coverage** | {pipeline_coverage:.1%} (agents) | {quality['coverage']:.1%} (fields) | {abs(pipeline_coverage - quality['coverage']):.1%} |
| **Success Rate** | {pipeline_coverage:.1%} | {quality['overall']:.1%} | {abs(pipeline_coverage - quality['overall']):.1%} |

## 🎓 Insights

### What Worked:
{self._generate_insights_worked(year_data, quality)}

### Issues Found:
{self._generate_insights_issues(pipeline_result, year_data, quality)}

### Recommendations:
{self._generate_recommendations(quality)}

---

**Generated by**: schema_v7_adapter.py (Phase 2 integration test)
"""

    return report


def _generate_insights_worked(year_data, quality) -> str:
    """Generate "what worked" section"""
    insights = []

    if quality['overall'] >= 0.75:
        insights.append("✅ Overall quality score ≥75% - architecture validates well")

    if year_data.nettoomsättning_tkr and year_data.net_revenue_tkr == year_data.nettoomsättning_tkr:
        insights.append("✅ Swedish-first pattern working - bidirectional sync automatic")

    if quality['evidence'] >= 0.90:
        insights.append("✅ Evidence tracking strong - 90%+ agents cite source pages")

    if not insights:
        insights.append("⚠️ Limited validation - need more extraction data")

    return "\n".join(insights)


def _generate_insights_issues(pipeline_result, year_data, quality) -> str:
    """Generate "issues found" section"""
    issues = []

    if quality['coverage'] < 0.50:
        issues.append("⚠️ Low field coverage (<50%) - many Swedish fields not populated")

    if quality['validation'] == 0.0:
        issues.append("⚠️ No validation data - fields don't have validation_status set")

    if quality['confidence'] == 0.0:
        issues.append("⚠️ No confidence scores - pipeline doesn't track extraction confidence")

    # Check for field mapping mismatches
    agent_results = pipeline_result.get('agent_results', {})
    unmapped_fields = set()
    for result in agent_results.values():
        if result.get('status') == 'success' and 'data' in result:
            for key in result['data'].keys():
                if key.lower() not in FIELD_MAPPING and key not in ['year', 'confidence', 'evidence_pages']:
                    unmapped_fields.add(key)

    if unmapped_fields:
        issues.append(f"⚠️ Unmapped fields found: {', '.join(list(unmapped_fields)[:5])}")

    if not issues:
        issues.append("✅ No major issues found")

    return "\n".join(issues)


def _generate_recommendations(quality) -> str:
    """Generate recommendations section"""
    recs = []

    if quality['overall'] >= 0.75:
        recs.append("✅ **RECOMMEND**: Continue with Days 4-5 OR scale Swedish-first to more models")
        recs.append("   Architecture validated successfully, ready to expand")
    elif quality['overall'] >= 0.50:
        recs.append("⚠️ **RECOMMEND**: Fix minor issues (field mapping, confidence tracking), then retry")
        recs.append("   Architecture shows promise, needs refinement")
    else:
        recs.append("❌ **RECOMMEND**: Review schema design, may need refactoring")
        recs.append("   Low quality scores indicate architecture mismatch with pipeline")

    return "\n".join(recs)


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Main entry point for adapter"""
    if len(sys.argv) < 2:
        print("Usage: python schema_v7_adapter.py <pipeline_result.json>")
        print()
        print("Example:")
        print("  python schema_v7_adapter.py results/optimal_pipeline/brf_268882_optimal_result.json")
        sys.exit(1)

    json_path = sys.argv[1]

    if not Path(json_path).exists():
        print(f"❌ Error: File not found: {json_path}")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"SCHEMA V7.0 ADAPTER - Phase 2 Integration Test")
    print(f"{'='*70}\n")

    # Load pipeline result
    print(f"📂 Loading pipeline result: {json_path}")
    pipeline_result = load_pipeline_result(json_path)

    # Extract year
    year = extract_year_from_filename(pipeline_result['pdf'])
    print(f"📅 Fiscal year: {year}")

    # Extract financial data
    print(f"🇸🇪 Converting to schema_v7 format...")
    agent_results = pipeline_result.get('agent_results', {})
    year_data = extract_financial_year(agent_results, year)

    # Calculate quality metrics
    print(f"✅ Calculating quality metrics...")
    quality = calculate_v7_quality(year_data)

    # Generate report
    print(f"📊 Generating comparison report...")
    report = generate_comparison_report(pipeline_result, year_data, quality)

    # Save report
    output_path = Path(json_path).parent / f"{Path(json_path).stem}_v7_report.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    # Print summary
    print(f"\n{'='*70}")
    print(f"✅ ADAPTER COMPLETE")
    print(f"{'='*70}\n")
    print(f"Schema V7 Quality:")
    print(f"  Coverage:    {quality['coverage']:.1%}")
    print(f"  Validation:  {quality['validation']:.1%}")
    print(f"  Confidence:  {quality['confidence']:.1%}")
    print(f"  Evidence:    {quality['evidence']:.1%}")
    print(f"  Overall:     {quality['overall']:.1%} {'✅' if quality['overall'] >= 0.75 else '⚠️'}")
    print(f"\n📄 Report saved: {output_path}\n")

    # Also print report to console
    print(report)


if __name__ == "__main__":
    main()
```

---

## 📊 Expected Timeline

| Phase | Task | Time | Output |
|-------|------|------|--------|
| **2A** | Create adapter | 1h | `schema_v7_adapter.py` (200 lines) |
| **2B** | Test on brf_268882.pdf | 30m | Quality report JSON + MD |
| **2C** | Validate quality metrics | 30m | Validation test results |
| **2D** | Document & decide | 30m | Decision: Days 4-5 or scale |

**Total**: 2.5 hours (within 2-3 hour target ✅)

---

## ✅ Success Criteria

**Phase 2 Success** if:
1. ✅ Adapter converts pipeline output → schema_v7 format
2. ✅ Quality metrics calculated on real data
3. ✅ Report generated comparing pipeline vs v7
4. ✅ Clear recommendation for next step (Days 4-5 or scale)

**Architecture Validated** if:
1. ✅ Overall quality ≥75%
2. ✅ Swedish-first pattern works on real data
3. ✅ Tolerant validation practical
4. ✅ No major integration issues

---

## 🎯 Decision Matrix (After Phase 2)

| Quality Score | Recommendation | Next Action |
|---------------|----------------|-------------|
| **≥75%** | ✅ **VALIDATED** | Continue with Days 4-5 OR scale Swedish-first |
| **50-75%** | ⚠️ **PROMISING** | Fix minor issues (30-60 min), then decide |
| **<50%** | ❌ **NEEDS WORK** | Review schema design (2-3 hours), refactor |

---

**Created**: October 13, 2025
**Purpose**: Perfect Phase 2 integration strategy
**Recommended**: Option B (Adapter Wrapper) - 2.5 hours, low risk, high value
**Output**: Validated schema_v7 architecture on real BRF extraction data

**🎯 Test early, validate often, nail it perfectly! 🚀**
