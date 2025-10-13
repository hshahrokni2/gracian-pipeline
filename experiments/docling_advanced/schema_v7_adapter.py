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
    # Revenue fields (raw totals)
    'annual_revenue': 'nettoomsättning_tkr',
    'net_revenue': 'nettoomsättning_tkr',
    'revenue': 'nettoomsättning_tkr',
    'total_revenue': 'nettoomsättning_tkr',
    'nettoomsattning': 'nettoomsättning_tkr',  # Direct Swedish

    # Raw financial totals (NEW in Phase 1)
    'assets': 'tillgångar_tkr',
    'total_assets': 'tillgångar_tkr',
    'liabilities': 'skulder_tkr',
    'total_liabilities': 'skulder_tkr',
    'equity': 'eget_kapital_tkr',
    'total_equity': 'eget_kapital_tkr',
    'expenses': 'kostnader_tkr',
    'total_expenses': 'kostnader_tkr',
    'surplus': 'resultat_efter_finansiella_tkr',

    # Result fields
    'result_after_financial': 'resultat_efter_finansiella_tkr',
    'net_income': 'resultat_efter_finansiella_tkr',

    # Property/building data (NEW in Phase 1)
    'apartments': 'antal_lägenheter',
    'number_of_apartments': 'antal_lägenheter',
    'num_apartments': 'antal_lägenheter',
    'built_year': 'byggår',
    'year_built': 'byggår',
    'construction_year': 'byggår',
    'designation': 'fastighet_beteckning',
    'property_designation': 'fastighet_beteckning',
    'total_area_sqm': 'total_area_sqm',
    'residential_area_sqm': 'boyta_sqm',
    'boyta_sqm': 'boyta_sqm',
    'address': 'adress',
    'street_address': 'adress',
    'city': 'stad',
    'town': 'stad',

    # Equity ratio (calculated metric)
    'equity_ratio': 'soliditet_procent',
    'solidarity': 'soliditet_procent',
    'solidarity_percent': 'soliditet_procent',

    # Annual fees (per-sqm metric)
    'annual_fee_per_sqm': 'årsavgift_per_kvm',
    'fee_per_sqm': 'årsavgift_per_kvm',
    'monthly_fee_per_sqm': 'årsavgift_per_kvm',  # Convert monthly → annual

    # Debt (per-sqm metrics)
    'debt_per_sqm': 'skuld_per_kvm_total',
    'debt_per_total_sqm': 'skuld_per_kvm_total',
    'debt_per_residential_sqm': 'skuld_per_kvm_boyta',

    # Energy (per-sqm metric)
    'energy_cost_per_sqm': 'energikostnad_per_kvm',

    # Interest sensitivity
    'interest_sensitivity': 'räntekänslighet_procent',

    # Savings (per-sqm metric)
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


def calculate_derived_metrics(year_data: YearlyFinancialData) -> YearlyFinancialData:
    """
    Calculate derived metrics from raw totals (Option 1 feature).

    Calculates:
    - soliditet_procent: (eget_kapital / tillgångar) * 100
    - skuld_per_kvm_total: skulder / total_area_sqm
    - skuld_per_kvm_boyta: skulder / boyta_sqm

    Args:
        year_data: YearlyFinancialData with raw fields populated

    Returns:
        YearlyFinancialData with calculated metrics added
    """
    # Calculate equity ratio (soliditet) if both equity and assets are available
    if year_data.eget_kapital_tkr and year_data.tillgångar_tkr and year_data.tillgångar_tkr > 0:
        year_data.soliditet_procent = round((year_data.eget_kapital_tkr / year_data.tillgångar_tkr) * 100, 1)

    # Calculate debt per sqm (total area) if both debt and area are available
    if year_data.skulder_tkr and year_data.total_area_sqm and year_data.total_area_sqm > 0:
        year_data.skuld_per_kvm_total = round(year_data.skulder_tkr / year_data.total_area_sqm, 0)

    # Calculate debt per sqm (residential area) if both debt and boyta are available
    if year_data.skulder_tkr and year_data.boyta_sqm and year_data.boyta_sqm > 0:
        year_data.skuld_per_kvm_boyta = round(year_data.skulder_tkr / year_data.boyta_sqm, 0)

    return year_data


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

    # Calculate derived metrics (Option 1 feature)
    year_data = calculate_derived_metrics(year_data)

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


def generate_insights_worked(year_data: YearlyFinancialData, quality: Dict[str, float]) -> str:
    """Generate 'what worked' section"""
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


def generate_insights_issues(
    pipeline_result: Dict[str, Any],
    year_data: YearlyFinancialData,
    quality: Dict[str, float]
) -> str:
    """Generate 'issues found' section"""
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


def generate_recommendations(quality: Dict[str, float]) -> str:
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

    # Count schema v7 fields populated (including NEW fields from Phase 1 + Option 2)
    swedish_fields = [
        # Raw totals
        'nettoomsättning_tkr', 'tillgångar_tkr', 'skulder_tkr', 'eget_kapital_tkr',
        'kostnader_tkr', 'resultat_efter_finansiella_tkr',
        # Property/building
        'antal_lägenheter', 'byggår', 'fastighet_beteckning', 'total_area_sqm', 'boyta_sqm',
        'adress', 'stad',
        # Per-sqm metrics
        'soliditet_procent', 'årsavgift_per_kvm', 'skuld_per_kvm_total', 'skuld_per_kvm_boyta',
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
{generate_insights_worked(year_data, quality)}

### Issues Found:
{generate_insights_issues(pipeline_result, year_data, quality)}

### Recommendations:
{generate_recommendations(quality)}

---

**Generated by**: schema_v7_adapter.py (Phase 2 integration test)
"""

    return report


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
