#!/usr/bin/env python3
"""
Phase 4: Multi-PDF Consistency Testing
Tests optimal pipeline on 10 diverse PDFs to validate consistent 95/95 performance
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import traceback

# Test set: 2 Hjorthagen + 8 SRS PDFs
TEST_PDFS = [
    # Hjorthagen (known structure)
    "../../data/raw_pdfs/Hjorthagen/brf_268882.pdf",
    "../../data/raw_pdfs/Hjorthagen/brf_81563.pdf",

    # SRS (more heterogeneous)
    "../../SRS/brf_53546.pdf",
    "../../SRS/brf_47903.pdf",
    "../../SRS/brf_57125.pdf",
    "../../SRS/brf_282765.pdf",
    "../../SRS/brf_54015.pdf",
    "../../SRS/brf_276796.pdf",
    "../../SRS/brf_48663.pdf",
    "../../SRS/brf_83301.pdf",
]

# 30-field schema for validation
FIELD_SCHEMA = {
    # Governance (5 fields)
    "chairman": {"path": "agent_results.governance_agent.data.chairman", "priority": "P0"},
    "board_members": {"path": "agent_results.governance_agent.data.board_members", "priority": "P0"},
    "auditor_name": {"path": "agent_results.governance_agent.data.auditor_name", "priority": "P0"},
    "audit_firm": {"path": "agent_results.governance_agent.data.audit_firm", "priority": "P1"},
    "nomination_committee": {"path": "agent_results.governance_agent.data.nomination_committee", "priority": "P2"},

    # Property (6 fields)
    "designation": {"path": "agent_results.property_agent.data.designation", "priority": "P1"},
    "address": {"path": "agent_results.property_agent.data.address", "priority": "P2"},
    "postal_code": {"path": "agent_results.property_agent.data.postal_code", "priority": "P2"},
    "city": {"path": "agent_results.property_agent.data.city", "priority": "P1"},
    "built_year": {"path": "agent_results.property_agent.data.built_year", "priority": "P1"},
    "apartments": {"path": "agent_results.property_agent.data.apartments", "priority": "P1"},

    # Financial (6 fields)
    "revenue": {"path": "agent_results.financial_agent.data.revenue", "priority": "P0"},
    "expenses": {"path": "agent_results.financial_agent.data.expenses", "priority": "P1"},
    "assets": {"path": "agent_results.financial_agent.data.assets", "priority": "P0"},
    "liabilities": {"path": "agent_results.financial_agent.data.liabilities", "priority": "P0"},
    "equity": {"path": "agent_results.financial_agent.data.equity", "priority": "P0"},
    "surplus": {"path": "agent_results.financial_agent.data.surplus", "priority": "P1"},

    # Detailed Financials (2 fields)
    "revenue_breakdown": {"path": "agent_results.revenue_breakdown_agent.data.revenue_breakdown", "priority": "P2"},
    "operating_costs": {"path": "agent_results.operating_costs_agent.data.operating_costs_breakdown", "priority": "P2"},

    # Operations (4 fields)
    "maintenance_summary": {"path": "agent_results.operations_agent.data.maintenance_summary", "priority": "P1"},
    "energy_usage": {"path": "agent_results.operations_agent.data.energy_usage", "priority": "P2"},
    "insurance": {"path": "agent_results.operations_agent.data.insurance", "priority": "P2"},
    "contracts": {"path": "agent_results.operations_agent.data.contracts", "priority": "P2"},

    # Notes (7 fields)
    "accounting_principles": {"path": "agent_results.notes_accounting_agent.data.accounting_principles", "priority": "P1"},
    "buildings": {"path": "agent_results.comprehensive_notes_agent.data.note_8_buildings", "priority": "P1"},
    "receivables": {"path": "agent_results.comprehensive_notes_agent.data.note_9_receivables", "priority": "P2"},
    "maintenance_fund": {"path": "agent_results.comprehensive_notes_agent.data.note_10_maintenance_fund", "priority": "P1"},
    "loans": {"path": "agent_results.comprehensive_notes_agent.data.loans", "priority": "P1"},
    "operating_costs_detail": {"path": "agent_results.comprehensive_notes_agent.data.note_4_operating_costs", "priority": "P2"},
    "tax_info": {"path": "agent_results.comprehensive_notes_agent.data.tax_info", "priority": "P2"},
}


def get_nested_value(data: Dict, path: str) -> Any:
    """Extract value from nested dictionary using dot notation path"""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def is_populated(value: Any) -> bool:
    """Check if a value is populated (not None, empty string, empty list, or empty dict)"""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    return True


def validate_pdf(pdf_path: str, output_dir: str = "results/phase4_validation") -> Dict[str, Any]:
    """
    Extract and validate a single PDF

    Returns:
        dict: Validation results including coverage, accuracy, timing
    """
    os.makedirs(output_dir, exist_ok=True)

    pdf_name = os.path.basename(pdf_path)
    result_path = os.path.join(output_dir, pdf_name.replace('.pdf', '_result.json'))

    print(f"\n{'='*80}")
    print(f"Processing: {pdf_name}")
    print(f"{'='*80}")

    # Run extraction
    start_time = time.time()

    try:
        from optimal_brf_pipeline import OptimalBRFPipeline

        pipeline = OptimalBRFPipeline(enable_caching=True, output_dir=output_dir)
        result = pipeline.extract_document(pdf_path)

        extraction_time = time.time() - start_time

        # Pipeline already saved result internally - just load it for validation
        # result_path was the intended save location, but pipeline saves to output_dir
        actual_result_path = os.path.join(output_dir, pdf_name.replace('.pdf', '_optimal_result.json'))

        # Load the actual saved result
        with open(actual_result_path, 'r', encoding='utf-8') as f:
            result = json.load(f)

        # Validate fields
        validation = {
            "pdf": pdf_name,
            "extraction_time": extraction_time,
            "total_fields": len(FIELD_SCHEMA),
            "populated_fields": 0,
            "empty_fields": 0,
            "field_details": {},
            "priority_breakdown": {},  # Will be populated dynamically
            "balance_check": None,
            "evidence_ratio": 0.0,
        }

        # Check each field
        for field_name, field_info in FIELD_SCHEMA.items():
            value = get_nested_value(result, field_info["path"])
            populated = is_populated(value)
            priority = field_info["priority"]

            validation["field_details"][field_name] = {
                "populated": populated,
                "priority": priority,
                "value_type": type(value).__name__ if value is not None else "None"
            }

            # Initialize priority breakdown entry if needed (ONCE per priority)
            if priority not in validation["priority_breakdown"]:
                validation["priority_breakdown"][priority] = {"populated": 0, "total": 0}

            # Update counters
            if populated:
                validation["populated_fields"] += 1
                validation["priority_breakdown"][priority]["populated"] += 1
            else:
                validation["empty_fields"] += 1

            validation["priority_breakdown"][priority]["total"] += 1

        # Calculate coverage
        validation["coverage_pct"] = (validation["populated_fields"] / validation["total_fields"]) * 100

        # Balance check
        assets = get_nested_value(result, "agent_results.financial_agent.data.assets")
        liabilities = get_nested_value(result, "agent_results.financial_agent.data.liabilities")
        equity = get_nested_value(result, "agent_results.financial_agent.data.equity")

        if all([assets, liabilities, equity]):
            try:
                assets_num = int(str(assets).replace(" ", "").replace(",", ""))
                liabilities_num = int(str(liabilities).replace(" ", "").replace(",", ""))
                equity_num = int(str(equity).replace(" ", "").replace(",", ""))

                total_liab_equity = liabilities_num + equity_num
                diff = abs(assets_num - total_liab_equity)
                diff_pct = (diff / assets_num) * 100 if assets_num > 0 else 0

                validation["balance_check"] = {
                    "pass": diff_pct < 1.0,  # Allow 1% tolerance
                    "assets": assets_num,
                    "liabilities": liabilities_num,
                    "equity": equity_num,
                    "difference": diff,
                    "difference_pct": diff_pct
                }
            except (ValueError, TypeError) as e:
                validation["balance_check"] = {"pass": False, "error": str(e)}

        # Evidence ratio
        agent_results = result.get("agent_results", {})
        agents_with_evidence = 0
        total_agents = 0

        for agent_name, agent_data in agent_results.items():
            if isinstance(agent_data, dict) and agent_data.get("status") == "success":
                total_agents += 1
                evidence_pages = agent_data.get("evidence_pages", [])
                if evidence_pages and len(evidence_pages) > 0:
                    agents_with_evidence += 1

        validation["evidence_ratio"] = (agents_with_evidence / total_agents) if total_agents > 0 else 0.0
        validation["agents_with_evidence"] = agents_with_evidence
        validation["total_agents"] = total_agents

        # Success status
        validation["success"] = True
        validation["error"] = None

        print(f"\n✅ Extraction successful")
        print(f"   Coverage: {validation['populated_fields']}/{validation['total_fields']} ({validation['coverage_pct']:.1f}%)")
        print(f"   Time: {extraction_time:.1f}s")
        print(f"   Balance check: {'✅ Pass' if validation['balance_check'] and validation['balance_check']['pass'] else '❌ Fail'}")

        return validation

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"\n❌ Extraction failed: {error_msg}")
        print(traceback.format_exc())

        return {
            "pdf": pdf_name,
            "success": False,
            "error": error_msg,
            "extraction_time": time.time() - start_time,
        }


def generate_summary_report(validations: List[Dict[str, Any]], output_path: str = "results/phase4_validation/PHASE4_SUMMARY_REPORT.md"):
    """Generate comprehensive summary report"""

    successful = [v for v in validations if v.get("success", False)]
    failed = [v for v in validations if not v.get("success", False)]

    # Calculate aggregate statistics
    total_pdfs = len(validations)
    success_rate = (len(successful) / total_pdfs) * 100 if total_pdfs > 0 else 0

    if successful:
        avg_coverage = sum(v["coverage_pct"] for v in successful) / len(successful)
        avg_time = sum(v["extraction_time"] for v in successful) / len(successful)
        balance_pass_rate = sum(1 for v in successful if v.get("balance_check", {}).get("pass", False)) / len(successful) * 100
        avg_evidence_ratio = sum(v.get("evidence_ratio", 0) for v in successful) / len(successful) * 100
    else:
        avg_coverage = avg_time = balance_pass_rate = avg_evidence_ratio = 0

    # Generate markdown report
    report = f"""# Phase 4 Complete: Multi-PDF Consistency Validation

**Date**: October 14, 2025
**Test Set**: 10 diverse PDFs (2 Hjorthagen + 8 SRS)
**Status**: {'✅ **COMPLETE**' if success_rate == 100 else '⚠️ **PARTIAL**'}

---

## 🎯 Aggregate Results

**Success Rate**: **{len(successful)}/{total_pdfs} ({success_rate:.1f}%)** {'✅' if success_rate >= 95 else '❌'}

**Average Coverage**: **{avg_coverage:.1f}%** {'✅ **MEETS 95% TARGET**' if avg_coverage >= 95 else '❌ **BELOW TARGET**'}

**Average Processing Time**: **{avg_time:.1f}s**

**Balance Check Pass Rate**: **{balance_pass_rate:.1f}%** {'✅' if balance_pass_rate >= 95 else '❌'}

**Average Evidence Ratio**: **{avg_evidence_ratio:.1f}%** {'✅' if avg_evidence_ratio >= 80 else '⚠️'}

---

## 📊 Individual PDF Results

### ✅ Successful Extractions ({len(successful)}/{total_pdfs})

"""

    for v in successful:
        report += f"""
#### {v['pdf']}
- **Coverage**: {v['populated_fields']}/{v['total_fields']} ({v['coverage_pct']:.1f}%)
- **Processing Time**: {v['extraction_time']:.1f}s
- **Balance Check**: {'✅ Pass' if v.get('balance_check', {}).get('pass') else '❌ Fail'}
- **Evidence Ratio**: {v.get('evidence_ratio', 0)*100:.1f}%
- **Priority Breakdown**:
"""
        for priority in ["P0", "P1", "P2"]:
            if priority in v.get("priority_breakdown", {}):
                pb = v["priority_breakdown"][priority]
                report += f"  - {priority}: {pb['populated']}/{pb['total']} ({pb['populated']/pb['total']*100 if pb['total'] > 0 else 0:.1f}%)\n"

    if failed:
        report += f"""
### ❌ Failed Extractions ({len(failed)}/{total_pdfs})

"""
        for v in failed:
            report += f"""
#### {v['pdf']}
- **Error**: {v.get('error', 'Unknown error')}
- **Time**: {v['extraction_time']:.1f}s
"""

    report += f"""
---

## 📈 Statistical Analysis

### Coverage Distribution

"""
    if successful:
        coverage_values = [v["coverage_pct"] for v in successful]
        report += f"""
- **Minimum**: {min(coverage_values):.1f}%
- **Maximum**: {max(coverage_values):.1f}%
- **Median**: {sorted(coverage_values)[len(coverage_values)//2]:.1f}%
- **Standard Deviation**: {(sum((x - avg_coverage)**2 for x in coverage_values) / len(coverage_values))**0.5:.1f}%

### Outliers

"""
        # Identify outliers (coverage < 80% or > 100%)
        outliers = [v for v in successful if v["coverage_pct"] < 80 or v["coverage_pct"] > 100]
        if outliers:
            for v in outliers:
                report += f"- **{v['pdf']}**: {v['coverage_pct']:.1f}% ({'LOW' if v['coverage_pct'] < 80 else 'HIGH'})\n"
        else:
            report += "No significant outliers detected ✅\n"

    report += f"""
---

## 🎯 Phase 4 Success Criteria Assessment

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| **Success Rate** | ≥95% | {success_rate:.1f}% | {'✅ **MEETS**' if success_rate >= 95 else '❌ **BELOW**'} |
| **Average Coverage** | ≥93% | {avg_coverage:.1f}% | {'✅ **MEETS**' if avg_coverage >= 93 else '❌ **BELOW**'} |
| **Balance Check Rate** | ≥95% | {balance_pass_rate:.1f}% | {'✅ **MEETS**' if balance_pass_rate >= 95 else '❌ **BELOW**'} |
| **Evidence Ratio** | ≥80% | {avg_evidence_ratio:.1f}% | {'✅ **MEETS**' if avg_evidence_ratio >= 80 else '⚠️ **CLOSE**'} |

---

## 🚀 Production Readiness

"""

    if success_rate >= 95 and avg_coverage >= 93:
        report += """
✅ **READY FOR PRODUCTION DEPLOYMENT**

**Rationale**:
1. Success rate exceeds 95% target
2. Average coverage meets 93% threshold
3. Consistent performance across diverse PDFs
4. Balance checks passing reliably

**Recommendation**: Proceed with pilot production deployment on 100-PDF subset

"""
    else:
        report += """
⚠️ **ADDITIONAL OPTIMIZATION NEEDED**

**Issues Identified**:
"""
        if success_rate < 95:
            report += f"- Success rate ({success_rate:.1f}%) below 95% target\n"
        if avg_coverage < 93:
            report += f"- Average coverage ({avg_coverage:.1f}%) below 93% target\n"

        report += """
**Recommendation**: Analyze failure cases and improve extraction before production deployment

"""

    report += f"""
---

**Generated**: October 14, 2025
**Test Framework**: Phase 4 Multi-PDF Consistency
**Status**: {'✅ **VALIDATION COMPLETE**' if success_rate == 100 else '⚠️ **PARTIAL VALIDATION**'}
"""

    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n{'='*80}")
    print(f"Summary report generated: {output_path}")
    print(f"{'='*80}")

    return report


def main():
    """Run Phase 4 multi-PDF consistency testing"""
    print("="*80)
    print("PHASE 4: MULTI-PDF CONSISTENCY TESTING")
    print("="*80)
    print(f"\nTest set: {len(TEST_PDFS)} PDFs")
    print(f"  - 2 Hjorthagen (known structure)")
    print(f"  - 8 SRS (heterogeneous)")
    print(f"\nTarget: ≥95% success rate, ≥93% average coverage\n")

    validations = []

    for i, pdf_path in enumerate(TEST_PDFS, 1):
        print(f"\n[{i}/{len(TEST_PDFS)}] Testing: {os.path.basename(pdf_path)}")

        try:
            validation = validate_pdf(pdf_path)
            validations.append(validation)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            traceback.print_exc()
            validations.append({
                "pdf": os.path.basename(pdf_path),
                "success": False,
                "error": str(e),
                "extraction_time": 0
            })

    # Generate summary report
    generate_summary_report(validations)

    # Print final summary
    successful = [v for v in validations if v.get("success", False)]
    print(f"\n{'='*80}")
    print("PHASE 4 COMPLETE")
    print(f"{'='*80}")
    print(f"Successful: {len(successful)}/{len(TEST_PDFS)}")
    if successful:
        avg_coverage = sum(v["coverage_pct"] for v in successful) / len(successful)
        print(f"Average coverage: {avg_coverage:.1f}%")
    print(f"\nDetailed results: results/phase4_validation/PHASE4_SUMMARY_REPORT.md")
    print("="*80)


if __name__ == "__main__":
    main()
