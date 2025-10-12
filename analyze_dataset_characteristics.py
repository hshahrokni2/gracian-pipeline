#!/usr/bin/env python3
"""
Phase 1.1: Document Characteristics Comparison
Analyzes Hjorthagen vs SRS dataset differences to identify root cause of 18-point coverage gap.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Data directory
DATA_DIR = Path("data/week3_comprehensive_test_results")

def load_all_extractions():
    """Load all extraction results from Week 3 Day 4 test."""
    hjorthagen_results = []
    srs_results = []

    for json_file in DATA_DIR.glob("*_extraction.json"):
        with open(json_file) as f:
            data = json.load(f)

        if json_file.name.startswith("Hjorthagen_"):
            hjorthagen_results.append(data)
        elif json_file.name.startswith("SRS_"):
            srs_results.append(data)

    return hjorthagen_results, srs_results

def analyze_coverage_distribution(results: List[Dict], dataset_name: str):
    """Analyze coverage distribution patterns."""
    coverages = []
    for r in results:
        # Real structure has coverage_percentage at top level
        coverage = r.get("coverage_percentage", 0)
        if coverage > 0:
            coverages.append(coverage)

    if not coverages:
        return None

    coverages.sort()

    return {
        "dataset": dataset_name,
        "count": len(coverages),
        "min": min(coverages),
        "max": max(coverages),
        "avg": sum(coverages) / len(coverages),
        "median": coverages[len(coverages) // 2],
        "q1": coverages[len(coverages) // 4],
        "q3": coverages[(3 * len(coverages)) // 4],
        "below_50": sum(1 for c in coverages if c < 50),
        "below_30": sum(1 for c in coverages if c < 30),
        "above_70": sum(1 for c in coverages if c >= 70),
        "distribution": coverages
    }

def analyze_field_extraction_patterns(results: List[Dict], dataset_name: str):
    """Analyze which fields succeed/fail per dataset."""
    field_stats = defaultdict(lambda: {"found": 0, "total": 0})

    def get_field_value(obj):
        """Extract value from nested structure."""
        if obj is None:
            return None
        if isinstance(obj, dict) and "value" in obj:
            return obj["value"]
        return obj

    for r in results:
        # Check key fields with real structure
        # Safe navigation for nested dicts
        governance = r.get("governance", {}) or {}
        financial = r.get("financial", {}) or {}
        balance_sheet = financial.get("balance_sheet", {}) or {}
        income_statement = financial.get("income_statement", {}) or {}
        property_data = r.get("property", {}) or {}
        fees = r.get("fees", {}) or {}
        metadata = r.get("metadata", {}) or {}
        primary_auditor = governance.get("primary_auditor", {}) or {}

        fields_to_check = {
            # Governance
            "chairman": get_field_value(governance.get("chairman")),
            "board_members": governance.get("board_members"),
            "auditor": get_field_value(primary_auditor.get("name")),

            # Financial
            "total_assets": get_field_value(balance_sheet.get("assets_total")),
            "total_liabilities": get_field_value(balance_sheet.get("liabilities_total")),
            "revenue": get_field_value(income_statement.get("revenue_total")),
            "net_result": get_field_value(income_statement.get("result_after_tax")),

            # Property
            "municipality": get_field_value(property_data.get("municipality")),
            "property_designation": get_field_value(property_data.get("property_designation")),

            # Fees
            "annual_fee_per_sqm": get_field_value(fees.get("annual_fee_per_sqm")),

            # Metadata
            "organization_number": get_field_value(metadata.get("organization_number")),
            "fiscal_year": get_field_value(metadata.get("fiscal_year")),
        }

        for field_name, value in fields_to_check.items():
            field_stats[field_name]["total"] += 1
            if value is not None and value != "" and value != [] and value != "000000-0000" and value != 0:
                field_stats[field_name]["found"] += 1

    # Calculate success rates
    field_success_rates = {}
    for field_name, stats in field_stats.items():
        if stats["total"] > 0:
            success_rate = (stats["found"] / stats["total"]) * 100
            field_success_rates[field_name] = {
                "success_rate": success_rate,
                "found": stats["found"],
                "total": stats["total"]
            }

    return field_success_rates

def analyze_failures(results: List[Dict], dataset_name: str):
    """Analyze failed extractions."""
    failures = []

    for r in results:
        # Get file path for PDF name
        pdf_path = r.get("metadata", {}).get("file_path", "unknown")
        pdf_name = Path(pdf_path).name if pdf_path != "unknown" else "unknown"

        coverage = r.get("coverage_percentage", 0)

        if coverage < 20:
            # Very low coverage (potential extraction failure)
            failures.append({
                "pdf": pdf_name,
                "coverage": coverage,
                "reason": "Very low coverage (<20%)"
            })

    return failures

def compare_agent_performance(hjorthagen: List[Dict], srs: List[Dict]):
    """Compare how individual agents perform across datasets."""
    def get_field_value(obj):
        """Extract value from nested structure."""
        if obj is None:
            return None
        if isinstance(obj, dict) and "value" in obj:
            return obj["value"]
        return obj

    def get_agent_stats(results):
        agent_stats = defaultdict(lambda: {"success": 0, "total": 0, "avg_confidence": []})

        for r in results:
            # Check governance agent
            gov = r.get("governance", {})
            if gov:
                agent_stats["governance_agent"]["total"] += 1
                chairman = get_field_value(gov.get("chairman"))
                board = gov.get("board_members", [])
                if chairman or board:
                    agent_stats["governance_agent"]["success"] += 1

            # Check financial agent
            fin = r.get("financial", {})
            if fin:
                agent_stats["financial_agent"]["total"] += 1
                assets = get_field_value(fin.get("balance_sheet", {}).get("assets_total"))
                revenue = get_field_value(fin.get("income_statement", {}).get("revenue_total"))
                if assets or revenue:
                    agent_stats["financial_agent"]["success"] += 1

            # Check property agent
            prop = r.get("property", {})
            if prop:
                agent_stats["property_agent"]["total"] += 1
                muni = get_field_value(prop.get("municipality"))
                prop_des = get_field_value(prop.get("property_designation"))
                if muni or prop_des:
                    agent_stats["property_agent"]["success"] += 1

            # Check fees agent
            fees = r.get("fees", {})
            if fees:
                agent_stats["fees_agent"]["total"] += 1
                annual_fee = get_field_value(fees.get("annual_fee_per_sqm"))
                if annual_fee:
                    agent_stats["fees_agent"]["success"] += 1

        # Calculate averages
        for agent, stats in agent_stats.items():
            if stats["total"] > 0:
                stats["success_rate"] = (stats["success"] / stats["total"]) * 100
            else:
                stats["success_rate"] = 0

        return agent_stats

    hjorthagen_agents = get_agent_stats(hjorthagen)
    srs_agents = get_agent_stats(srs)

    # Compare
    comparison = {}
    all_agents = set(hjorthagen_agents.keys()) | set(srs_agents.keys())

    for agent in all_agents:
        h_stats = hjorthagen_agents.get(agent, {"success_rate": 0})
        s_stats = srs_agents.get(agent, {"success_rate": 0})

        comparison[agent] = {
            "hjorthagen_success_rate": h_stats["success_rate"],
            "srs_success_rate": s_stats["success_rate"],
            "success_rate_delta": h_stats["success_rate"] - s_stats["success_rate"]
        }

    return comparison

def main():
    print("=" * 80)
    print("PHASE 1.1: DATASET CHARACTERISTICS COMPARISON")
    print("=" * 80)
    print()

    # Load data
    print("Loading extraction results...")
    hjorthagen, srs = load_all_extractions()
    print(f"  Hjorthagen: {len(hjorthagen)} PDFs")
    print(f"  SRS: {len(srs)} PDFs")
    print()

    # Analyze coverage distributions
    print("1. COVERAGE DISTRIBUTION ANALYSIS")
    print("-" * 80)
    h_dist = analyze_coverage_distribution(hjorthagen, "Hjorthagen")
    s_dist = analyze_coverage_distribution(srs, "SRS")

    if h_dist and s_dist:
        print(f"\nHjorthagen Coverage:")
        print(f"  Average: {h_dist['avg']:.1f}%")
        print(f"  Median: {h_dist['median']:.1f}%")
        print(f"  Range: {h_dist['min']:.1f}% - {h_dist['max']:.1f}%")
        print(f"  Q1: {h_dist['q1']:.1f}%, Q3: {h_dist['q3']:.1f}%")
        print(f"  Below 50%: {h_dist['below_50']}/{h_dist['count']} ({(h_dist['below_50']/h_dist['count'])*100:.1f}%)")
        print(f"  Below 30%: {h_dist['below_30']}/{h_dist['count']} ({(h_dist['below_30']/h_dist['count'])*100:.1f}%)")
        print(f"  Above 70%: {h_dist['above_70']}/{h_dist['count']} ({(h_dist['above_70']/h_dist['count'])*100:.1f}%)")

        print(f"\nSRS Coverage:")
        print(f"  Average: {s_dist['avg']:.1f}%")
        print(f"  Median: {s_dist['median']:.1f}%")
        print(f"  Range: {s_dist['min']:.1f}% - {s_dist['max']:.1f}%")
        print(f"  Q1: {s_dist['q1']:.1f}%, Q3: {s_dist['q3']:.1f}%")
        print(f"  Below 50%: {s_dist['below_50']}/{s_dist['count']} ({(s_dist['below_50']/s_dist['count'])*100:.1f}%)")
        print(f"  Below 30%: {s_dist['below_30']}/{s_dist['count']} ({(s_dist['below_30']/s_dist['count'])*100:.1f}%)")
        print(f"  Above 70%: {s_dist['above_70']}/{s_dist['count']} ({(s_dist['above_70']/s_dist['count'])*100:.1f}%)")

        print(f"\n  🔍 KEY FINDING: Coverage Gap = {h_dist['avg'] - s_dist['avg']:.1f} percentage points")
        print(f"  🔍 SRS has {s_dist['below_50']} low performers vs {h_dist['below_50']} in Hjorthagen")
    print()

    # Analyze field-level patterns
    print("2. FIELD-LEVEL EXTRACTION PATTERNS")
    print("-" * 80)
    h_fields = analyze_field_extraction_patterns(hjorthagen, "Hjorthagen")
    s_fields = analyze_field_extraction_patterns(srs, "SRS")

    print(f"\n{'Field':<25} {'Hjorthagen':<15} {'SRS':<15} {'Delta':<10}")
    print("-" * 70)

    all_fields = sorted(set(h_fields.keys()) | set(s_fields.keys()))

    biggest_gaps = []
    for field in all_fields:
        h_rate = h_fields.get(field, {}).get("success_rate", 0)
        s_rate = s_fields.get(field, {}).get("success_rate", 0)
        delta = h_rate - s_rate

        biggest_gaps.append((field, delta, h_rate, s_rate))

        print(f"{field:<25} {h_rate:>6.1f}%        {s_rate:>6.1f}%        {delta:>+6.1f}pp")

    # Sort by delta
    biggest_gaps.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"\n  🔍 BIGGEST FIELD GAPS (Hjorthagen vs SRS):")
    for i, (field, delta, h_rate, s_rate) in enumerate(biggest_gaps[:5], 1):
        print(f"     {i}. {field}: {delta:+.1f}pp gap ({h_rate:.1f}% vs {s_rate:.1f}%)")
    print()

    # Analyze failures
    print("3. FAILURE ANALYSIS")
    print("-" * 80)
    h_failures = analyze_failures(hjorthagen, "Hjorthagen")
    s_failures = analyze_failures(srs, "SRS")

    print(f"\nHjorthagen Failures: {len(h_failures)}")
    for f in h_failures:
        print(f"  - {f['pdf']}: {f.get('error', '')} {f.get('reason', '')} (coverage: {f.get('coverage', 'N/A')})")

    print(f"\nSRS Failures: {len(s_failures)}")
    for f in s_failures:
        print(f"  - {f['pdf']}: {f.get('error', '')} {f.get('reason', '')} (coverage: {f.get('coverage', 'N/A')})")

    print(f"\n  🔍 SRS has {len(s_failures)} failures vs {len(h_failures)} in Hjorthagen")
    print()

    # Compare agent performance
    print("4. AGENT PERFORMANCE COMPARISON")
    print("-" * 80)
    agent_comparison = compare_agent_performance(hjorthagen, srs)

    print(f"\n{'Agent':<20} {'Hjorthagen':<15} {'SRS':<15} {'Delta':<10}")
    print("-" * 65)

    for agent, stats in sorted(agent_comparison.items()):
        h_rate = stats["hjorthagen_success_rate"]
        s_rate = stats["srs_success_rate"]
        delta = stats["success_rate_delta"]

        print(f"{agent:<20} {h_rate:>6.1f}%        {s_rate:>6.1f}%        {delta:>+6.1f}pp")

    print(f"\n  🔍 AGENT PERFORMANCE GAPS:")
    sorted_agents = sorted(agent_comparison.items(), key=lambda x: abs(x[1]["success_rate_delta"]), reverse=True)
    for i, (agent, stats) in enumerate(sorted_agents, 1):
        delta = stats["success_rate_delta"]
        if abs(delta) > 5:  # Only show significant gaps
            print(f"     {i}. {agent}: {delta:+.1f}pp gap")
    print()

    # Save detailed results
    results = {
        "hjorthagen_distribution": h_dist,
        "srs_distribution": s_dist,
        "hjorthagen_field_patterns": h_fields,
        "srs_field_patterns": s_fields,
        "hjorthagen_failures": h_failures,
        "srs_failures": s_failures,
        "agent_performance_comparison": agent_comparison,
        "key_findings": {
            "coverage_gap": h_dist['avg'] - s_dist['avg'] if h_dist and s_dist else 0,
            "failure_rate_hjorthagen": len(h_failures) / len(hjorthagen) * 100 if hjorthagen else 0,
            "failure_rate_srs": len(s_failures) / len(srs) * 100 if srs else 0,
            "biggest_field_gaps": [
                {"field": field, "delta": delta, "hjorthagen_rate": h_rate, "srs_rate": s_rate}
                for field, delta, h_rate, s_rate in biggest_gaps[:10]
            ]
        }
    }

    output_file = "data/dataset_characteristics_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 80)
    print(f"Detailed results saved to: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
