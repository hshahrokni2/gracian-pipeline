#!/usr/bin/env python3
"""
Sprint 1+2 Integration Test - All 3 New Agents
Tests revenue_breakdown, enhanced_loans, and operating_costs together
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
gracian_root = Path(__file__).resolve().parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}\n")

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent / "code"))

from optimal_brf_pipeline import OptimalBRFPipeline

def validate_revenue_breakdown(result):
    """Validate revenue_breakdown_agent results"""
    if 'revenue_breakdown_agent' not in result.pass2_result:
        return {"status": "missing", "fields_extracted": 0, "total_fields": 15}

    agent_result = result.pass2_result['revenue_breakdown_agent']

    if agent_result.get('status') != 'success':
        return {"status": "error", "fields_extracted": 0, "total_fields": 15, "error": agent_result.get('error')}

    data = agent_result.get('data', {}).get('revenue_breakdown', {})

    # Count non-zero fields (K2 format expected: 8/15)
    fields = [
        'nettoomsattning', 'arsavgifter', 'hyresintakter', 'bredband_kabel_tv',
        'andel_drift_gemensam', 'andel_el_varme', 'andel_vatten', 'ovriga_rorelseintak',
        'ranta_bankmedel', 'valutakursvinster', 'summa_rorelseintakter',
        'summa_finansiella_intakter', 'summa_intakter', 'revenue_2021'
    ]

    extracted = sum(1 for f in fields if data.get(f, 0) != 0)

    return {
        "status": "success",
        "fields_extracted": extracted,
        "total_fields": 15,
        "coverage": extracted / 15,
        "evidence_pages": data.get('evidence_pages', []),
        "data": data
    }

def validate_enhanced_loans(result):
    """Validate enhanced comprehensive_notes_agent results (4 new loan fields)"""
    if 'comprehensive_notes_agent' not in result.pass2_result:
        return {"status": "missing", "fields_extracted": 0, "total_fields": 16}

    agent_result = result.pass2_result['comprehensive_notes_agent']

    if agent_result.get('status') != 'success':
        return {"status": "error", "fields_extracted": 0, "total_fields": 16, "error": agent_result.get('error')}

    data = agent_result.get('data', {})
    loans = data.get('loans', [])

    if not loans:
        return {"status": "no_loans", "fields_extracted": 0, "total_fields": 16}

    # Count NEW fields (loan_type, collateral, credit_facility_limit, outstanding_amount)
    # Expected: 4 new fields × 4 loans = 16 new fields
    new_field_names = ['loan_type', 'collateral', 'credit_facility_limit', 'outstanding_amount']

    extracted_count = 0
    for loan in loans:
        for field in new_field_names:
            if field in loan and loan[field]:
                extracted_count += 1

    return {
        "status": "success",
        "loans_count": len(loans),
        "fields_extracted": extracted_count,
        "total_fields": 16,  # 4 new fields × 4 loans
        "coverage": extracted_count / 16,
        "evidence_pages": data.get('evidence_pages', []),
        "sample_loan": loans[0] if loans else None
    }

def validate_operating_costs(result):
    """Validate operating_costs_agent results"""
    if 'operating_costs_agent' not in result.pass2_result:
        return {"status": "missing", "fields_extracted": 0, "total_fields": 6}

    agent_result = result.pass2_result['operating_costs_agent']

    if agent_result.get('status') != 'success':
        return {"status": "error", "fields_extracted": 0, "total_fields": 6, "error": agent_result.get('error')}

    data = agent_result.get('data', {}).get('operating_costs_breakdown', {})

    # Count non-zero fields
    fields = ['fastighetsskott', 'reparationer', 'el', 'varme', 'vatten', 'ovriga_externa_kostnader']

    extracted = sum(1 for f in fields if data.get(f, 0) != 0)

    return {
        "status": "success",
        "fields_extracted": extracted,
        "total_fields": 6,
        "coverage": extracted / 6,
        "evidence_pages": data.get('evidence_pages', []),
        "data": data
    }

def main():
    print("=" * 80)
    print("SPRINT 1+2 INTEGRATION TEST - All 3 New Agents")
    print("=" * 80)
    print("\nTesting PDF: brf_198532.pdf")
    print("Agents: revenue_breakdown, enhanced_loans, operating_costs")
    print("\nExpected:")
    print("  - Revenue: 8/15 fields (K2 format)")
    print("  - Enhanced loans: 16/16 fields (4 new × 4 loans)")
    print("  - Operating costs: 2/6 fields (current, improve to 4+)")
    print("  - COMBINED TARGET: ≥70% (≥23/37 fields)\n")

    # Initialize pipeline
    pipeline = OptimalBRFPipeline(enable_caching=True)

    # Run extraction
    print("Running full pipeline extraction...\n")
    result = pipeline.extract_document("../../SRS/brf_198532.pdf")

    # Validate each agent
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    # 1. Revenue Breakdown
    print("\n📊 1. revenue_breakdown_agent (15 fields)")
    revenue = validate_revenue_breakdown(result)
    print(f"   Status: {revenue['status']}")
    print(f"   Fields: {revenue['fields_extracted']}/{revenue['total_fields']} ({revenue['fields_extracted']/revenue['total_fields']*100:.1f}%)")
    if revenue.get('evidence_pages'):
        print(f"   Evidence: {revenue['evidence_pages']}")

    # 2. Enhanced Loans
    print("\n💰 2. enhanced comprehensive_notes_agent (16 new loan fields)")
    loans = validate_enhanced_loans(result)
    print(f"   Status: {loans['status']}")
    print(f"   Loans: {loans.get('loans_count', 0)}/4 expected")
    print(f"   New fields: {loans['fields_extracted']}/{loans['total_fields']} ({loans['fields_extracted']/loans['total_fields']*100:.1f}%)")
    if loans.get('evidence_pages'):
        print(f"   Evidence: {loans['evidence_pages']}")
    if loans.get('sample_loan'):
        sample = loans['sample_loan']
        print(f"   Sample loan 1:")
        print(f"     - Lender: {sample.get('lender')}")
        print(f"     - Amount: {sample.get('amount_2021', 0):,}")
        print(f"     - NEW loan_type: {sample.get('loan_type', 'MISSING')}")
        print(f"     - NEW collateral: {sample.get('collateral', 'MISSING')}")
        print(f"     - NEW credit_limit: {sample.get('credit_facility_limit', 'MISSING')}")
        print(f"     - NEW outstanding: {sample.get('outstanding_amount', 'MISSING')}")

    # 3. Operating Costs
    print("\n💸 3. operating_costs_agent (6 fields)")
    costs = validate_operating_costs(result)
    print(f"   Status: {costs['status']}")
    print(f"   Fields: {costs['fields_extracted']}/{costs['total_fields']} ({costs['fields_extracted']/costs['total_fields']*100:.1f}%)")
    if costs.get('evidence_pages'):
        print(f"   Evidence: {costs['evidence_pages']}")

    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    total_extracted = (
        revenue['fields_extracted'] +
        loans['fields_extracted'] +
        costs['fields_extracted']
    )
    total_fields = (
        revenue['total_fields'] +
        loans['total_fields'] +
        costs['total_fields']
    )

    overall_coverage = total_extracted / total_fields if total_fields > 0 else 0

    print(f"\n📊 Combined Results:")
    print(f"   Total fields: {total_extracted}/{total_fields} ({overall_coverage*100:.1f}%)")
    print(f"   Revenue: {revenue['fields_extracted']}/{revenue['total_fields']}")
    print(f"   Loans: {loans['fields_extracted']}/{loans['total_fields']}")
    print(f"   Costs: {costs['fields_extracted']}/{costs['total_fields']}")

    print(f"\n⏱️  Performance:")
    print(f"   Total time: {result.total_time:.1f}s")
    print(f"   Total cost: ${result.total_cost:.3f}")

    # Go/No-Go Decision
    print(f"\n🎯 Go/No-Go Decision:")

    if overall_coverage >= 0.70:
        print(f"   ✅ GO: {overall_coverage*100:.1f}% ≥ 70% target")
        print("   Ready for Day 4 full system validation")
    elif overall_coverage >= 0.60:
        print(f"   🟡 ADJUST: {overall_coverage*100:.1f}% (60-69%)")
        print("   Action: Add Note 4 extraction for operating costs")
        print("   Expected improvement: +15-20 percentage points")
    else:
        print(f"   🛑 NO-GO: {overall_coverage*100:.1f}% < 60%")
        print("   Deep-dive required on failed agents")

    # Save results
    output_file = Path("results/sprint1_2_integration_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf': '../../SRS/brf_198532.pdf',
            'revenue_breakdown': revenue,
            'enhanced_loans': loans,
            'operating_costs': costs,
            'overall': {
                'total_extracted': total_extracted,
                'total_fields': total_fields,
                'coverage': overall_coverage
            },
            'performance': {
                'total_time': result.total_time,
                'total_cost': result.total_cost
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved: {output_file}")
    print("\n" + "=" * 80)

    pipeline.close()

if __name__ == "__main__":
    main()
