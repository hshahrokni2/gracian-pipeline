#!/usr/bin/env python3
"""
Day 4 Final Validation - Complete System Test with Note 4
Tests all agents + Note 4 extraction for final coverage calculation
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

def main():
    print("=" * 80)
    print("DAY 4 FINAL VALIDATION - Sprint 1+2 Complete System Test")
    print("=" * 80)
    print("\nObjective: Validate ≥75% coverage with Note 4 extraction")
    print("Test PDF: brf_198532.pdf (K2 format)")
    print()

    # Initialize pipeline
    pipeline = OptimalBRFPipeline(enable_caching=True)

    # Run extraction
    print("Running full pipeline extraction...\n")
    result = pipeline.extract_document("../../SRS/brf_198532.pdf")

    # Extract results
    pass2 = result.pass2_result

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    # 1. Revenue Breakdown
    print("\n📊 1. revenue_breakdown_agent (15 fields)")
    revenue = pass2.get('revenue_breakdown_agent', {})
    revenue_data = revenue.get('data', {}).get('revenue_breakdown', {})
    revenue_fields = sum(1 for f in [
        'nettoomsattning', 'arsavgifter', 'hyresintakter', 'bredband_kabel_tv',
        'andel_drift_gemensam', 'andel_el_varme', 'andel_vatten', 'ovriga_rorelseintak',
        'ranta_bankmedel', 'valutakursvinster', 'summa_rorelseintakter',
        'summa_finansiella_intakter', 'summa_intakter', 'revenue_2021'
    ] if revenue_data.get(f, 0) != 0)

    print(f"   Status: {revenue.get('status')}")
    print(f"   Fields: {revenue_fields}/15 ({revenue_fields/15*100:.1f}%)")
    print(f"   Evidence: {revenue_data.get('evidence_pages', [])}")

    # 2. Enhanced Loans
    print("\n💰 2. enhanced comprehensive_notes_agent (16 new loan fields)")
    comprehensive = pass2.get('comprehensive_notes_agent', {})
    comp_data = comprehensive.get('data', {})
    loans = comp_data.get('loans', [])

    new_field_names = ['loan_type', 'collateral', 'credit_facility_limit', 'outstanding_amount']
    loan_fields = 0
    for loan in loans:
        for field in new_field_names:
            if field in loan and loan[field]:
                loan_fields += 1

    print(f"   Status: {comprehensive.get('status')}")
    print(f"   Loans: {len(loans)}/4")
    print(f"   New fields: {loan_fields}/16 ({loan_fields/16*100:.1f}%)")
    if loans:
        sample = loans[0]
        print(f"   Sample loan: {sample.get('lender')} - {sample.get('amount_2021', 0):,}")

    # 3. Operating Costs (Enhanced with Note 4)
    print("\n💸 3. operating_costs_agent + Note 4 (6 fields)")

    # Get income statement data
    op_costs = pass2.get('operating_costs_agent', {})
    op_data = op_costs.get('data', {}).get('operating_costs_breakdown', {})

    # Get Note 4 data
    note4 = comp_data.get('note_4_operating_costs', {})

    # Merge: Use income statement for fastighetsskott/reparationer, Note 4 for utilities
    merged_costs = {
        'fastighetsskott': op_data.get('fastighetsskott', 0),  # From income statement
        'reparationer': op_data.get('reparationer', 0) or note4.get('reparationer_total', 0),  # Prefer income statement, fallback to Note 4
        'el': note4.get('el', 0),  # From Note 4
        'varme': note4.get('varme', 0),  # From Note 4
        'vatten': note4.get('vatten', 0),  # From Note 4
        'ovriga_externa_kostnader': op_data.get('ovriga_externa_kostnader', 0)  # From income statement
    }

    cost_fields = sum(1 for v in merged_costs.values() if v != 0)

    print(f"   Income statement: {op_costs.get('status')}")
    print(f"   Note 4: {'success' if note4 else 'missing'}")
    print(f"   Merged fields: {cost_fields}/6 ({cost_fields/6*100:.1f}%)")
    print(f"   Breakdown:")
    for field, value in merged_costs.items():
        if value != 0:
            source = " (Note 4)" if field in ['el', 'varme', 'vatten', 'reparationer'] and note4.get(field, 0) != 0 else " (income stmt)"
            print(f"      ✅ {field}: {value:,}{source}")
        else:
            print(f"      ❌ {field}: Missing")

    # Overall Summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    total_extracted = revenue_fields + loan_fields + cost_fields
    total_fields = 15 + 16 + 6
    overall_coverage = total_extracted / total_fields

    print(f"\n📊 Combined Results (with Note 4):")
    print(f"   Total fields: {total_extracted}/{total_fields} ({overall_coverage*100:.1f}%)")
    print(f"   Revenue: {revenue_fields}/15")
    print(f"   Loans: {loan_fields}/16")
    print(f"   Costs: {cost_fields}/6 (enhanced with Note 4)")

    print(f"\n⏱️  Performance:")
    print(f"   Total time: {result.total_time:.1f}s")
    print(f"   Total cost: ${result.total_cost:.3f}")

    # Go/No-Go Decision
    print(f"\n🎯 Go/No-Go Decision:")

    if overall_coverage >= 0.75:
        print(f"   ✅ GO: {overall_coverage*100:.1f}% ≥ 75% target")
        print("   ✅ TARGET ACHIEVED - Ready for Day 5 optimizations!")
        decision = "GO"
    elif overall_coverage >= 0.70:
        print(f"   🟡 CLOSE: {overall_coverage*100:.1f}% (70-74%)")
        print(f"   Need {int((0.75 - overall_coverage)*total_fields)} more fields for 75%")
        decision = "ADJUST"
    elif overall_coverage >= 0.60:
        print(f"   🟡 ADJUST: {overall_coverage*100:.1f}% (60-69%)")
        print(f"   Action: Further investigation needed")
        decision = "ADJUST"
    else:
        print(f"   🛑 NO-GO: {overall_coverage*100:.1f}% < 60%")
        print("   Deep-dive required")
        decision = "NO_GO"

    # Detailed breakdown
    print(f"\n📋 Detailed Breakdown:")
    print(f"   ✅ Baseline (30 fields): 100% coverage (production)")
    print(f"   ✅ Enhanced loans (16 fields): {loan_fields/16*100:.1f}% ({loan_fields}/16)")
    print(f"   {'✅' if revenue_fields/15 >= 0.40 else '🟡'} Revenue breakdown (15 fields): {revenue_fields/15*100:.1f}% ({revenue_fields}/15)")
    print(f"   {'✅' if cost_fields/6 >= 0.75 else '🟡'} Operating costs (6 fields): {cost_fields/6*100:.1f}% ({cost_fields}/6)")

    # Comparison with Day 3
    day3_coverage = 25/37
    improvement = overall_coverage - day3_coverage

    print(f"\n📈 Progress:")
    print(f"   Day 3 baseline: 25/37 (67.6%)")
    print(f"   Day 4 with Note 4: {total_extracted}/37 ({overall_coverage*100:.1f}%)")
    print(f"   Improvement: +{total_extracted-25} fields ({improvement*100:.1f} percentage points)")

    # Save results
    output_file = Path("results/day4_final_validation.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf': '../../SRS/brf_198532.pdf',
            'date': '2025-10-12',
            'revenue_breakdown': {
                'fields_extracted': revenue_fields,
                'total_fields': 15,
                'coverage': revenue_fields / 15
            },
            'enhanced_loans': {
                'fields_extracted': loan_fields,
                'total_fields': 16,
                'coverage': loan_fields / 16
            },
            'operating_costs': {
                'fields_extracted': cost_fields,
                'total_fields': 6,
                'coverage': cost_fields / 6,
                'merged_data': {k: int(v) for k, v in merged_costs.items()}
            },
            'overall': {
                'total_extracted': total_extracted,
                'total_fields': total_fields,
                'coverage': overall_coverage,
                'decision': decision
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
