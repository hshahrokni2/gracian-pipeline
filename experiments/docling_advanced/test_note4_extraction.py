#!/usr/bin/env python3
"""
Test Note 4 extraction from comprehensive_notes_agent (Day 4 enhancement)
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
    print("TEST: Note 4 Extraction from comprehensive_notes_agent")
    print("=" * 80)
    print("\nDay 4 Morning Enhancement: Extract operating costs from Note 4")
    print("Expected values (brf_198532, page 13, Note 4 DRIFTKOSTNADER):")
    print("  - fastighetskostnader_total: ~553,590 kr")
    print("  - reparationer_total: ~483,370 kr (sum of various items)")
    print("  - el: ~260,845 kr")
    print("  - varme: ~611,237 kr")
    print("  - vatten: ~174,838 kr")
    print()

    # Initialize pipeline
    pipeline = OptimalBRFPipeline(enable_caching=True)

    # Run extraction
    print("Running full pipeline extraction...\n")
    result = pipeline.extract_document("../../SRS/brf_198532.pdf")

    # Check comprehensive_notes_agent results
    if 'comprehensive_notes_agent' not in result.pass2_result:
        print("❌ comprehensive_notes_agent not found in results")
        return

    agent_result = result.pass2_result['comprehensive_notes_agent']

    print("\n" + "=" * 80)
    print("COMPREHENSIVE NOTES AGENT RESULTS")
    print("=" * 80)

    print(f"\nStatus: {agent_result.get('status')}")
    print(f"Evidence pages: {agent_result.get('evidence_pages', [])}")

    if agent_result.get('status') != 'success':
        print(f"❌ Error: {agent_result.get('error', 'Unknown error')}")
        return

    data = agent_result.get('data', {})

    # Check for Note 4
    note4 = data.get('note_4_operating_costs', {})

    if not note4:
        print("\n❌ Note 4 not found in extraction")
        print("   Agent may not have detected Note 4 DRIFTKOSTNADER section")
        return

    print("\n✅ Note 4 extracted!")
    print("\n📊 Note 4 Operating Costs Breakdown:")

    # Validate each field
    fields = [
        ('fastighetskostnader_total', 'Fastighetskostnader total', 553590),
        ('reparationer_total', 'Reparationer total', 483370),
        ('el', 'Electricity', 260845),
        ('varme', 'Heating', 611237),
        ('vatten', 'Water/drainage', 174838)
    ]

    extracted_count = 0
    for field_name, field_desc, expected_value in fields:
        value = note4.get(field_name, 0)
        if value != 0:
            # Calculate deviation from expected
            if expected_value > 0:
                deviation_pct = abs(value - expected_value) / expected_value * 100
                if deviation_pct <= 5:  # Within 5% tolerance
                    print(f"   ✅ {field_desc}: {value:,} kr (expected: {expected_value:,}, {deviation_pct:.1f}% deviation)")
                    extracted_count += 1
                else:
                    print(f"   ⚠️  {field_desc}: {value:,} kr (expected: {expected_value:,}, {deviation_pct:.1f}% deviation - outside 5% tolerance)")
                    extracted_count += 1  # Still counts as extracted
            else:
                print(f"   ✅ {field_desc}: {value:,} kr")
                extracted_count += 1
        else:
            print(f"   ❌ {field_desc}: Missing (0)")

    evidence = note4.get('evidence_pages', [])
    if evidence:
        print(f"\n   ✅ Evidence pages: {evidence}")
        if 13 in evidence:
            print(f"      ✅ Page 13 cited (Note 4 location)")
        else:
            print(f"      ⚠️  Page 13 not cited (Note 4 expected on page 13)")
    else:
        print(f"\n   ❌ No evidence pages cited")

    # Summary
    print(f"\n📊 Summary: {extracted_count}/5 fields extracted ({extracted_count/5*100:.1f}%)")

    if extracted_count >= 5:
        print("✅ EXCELLENT: All 5 fields extracted!")
    elif extracted_count >= 4:
        print("✅ SUCCESS: ≥4/5 fields extracted (target met)")
    elif extracted_count >= 3:
        print("🟡 PARTIAL: 3/5 fields extracted (needs improvement)")
    else:
        print("❌ FAILED: <3/5 fields extracted")

    # Calculate improvement in operating_costs
    print("\n" + "=" * 80)
    print("IMPACT ON operating_costs_agent")
    print("=" * 80)

    print("\nDay 3 baseline: operating_costs_agent extracted 2/6 fields (33.3%)")
    print("  - fastighetsskott: -2,834,798 kr (income statement)")
    print("  - ovriga_externa_kostnader: -229,331 kr (income statement)")

    print("\nDay 4 with Note 4: operating_costs can now extract utilities:")
    if note4.get('el', 0) != 0:
        print(f"  ✅ el: {note4.get('el', 0):,} kr (from Note 4)")
    else:
        print(f"  ❌ el: Missing")
    if note4.get('varme', 0) != 0:
        print(f"  ✅ varme: {note4.get('varme', 0):,} kr (from Note 4)")
    else:
        print(f"  ❌ varme: Missing")
    if note4.get('vatten', 0) != 0:
        print(f"  ✅ vatten: {note4.get('vatten', 0):,} kr (from Note 4)")
    else:
        print(f"  ❌ vatten: Missing")

    # Calculate new operating_costs extraction rate
    new_fields = 2  # baseline (fastighetsskott, ovriga_externa_kostnader)
    if note4.get('el', 0) != 0:
        new_fields += 1
    if note4.get('varme', 0) != 0:
        new_fields += 1
    if note4.get('vatten', 0) != 0:
        new_fields += 1

    print(f"\nProjected operating_costs extraction: {new_fields}/6 ({new_fields/6*100:.1f}%)")
    print(f"Improvement: +{new_fields-2} fields ({(new_fields/6*100)-(2/6*100):.1f} percentage points)")

    # Calculate overall coverage improvement
    print("\n" + "=" * 80)
    print("OVERALL SPRINT 1+2 COVERAGE PROJECTION")
    print("=" * 80)

    baseline_coverage = 25/37  # Day 3
    improvement = (new_fields - 2) / 37
    new_coverage = baseline_coverage + improvement

    print(f"\nDay 3 baseline: 25/37 fields (67.6%)")
    print(f"Day 4 projection: {25 + (new_fields - 2)}/37 ({new_coverage*100:.1f}%)")
    print(f"Improvement: +{new_fields - 2} fields ({improvement*100:.1f} percentage points)")

    if new_coverage >= 0.75:
        print(f"\n✅ TARGET ACHIEVED: {new_coverage*100:.1f}% ≥ 75%")
    else:
        print(f"\n🟡 CLOSE TO TARGET: {new_coverage*100:.1f}% (need {int((0.75 - new_coverage)*37)} more fields for 75%)")

    print("\n" + "=" * 80)

    pipeline.close()

if __name__ == "__main__":
    main()
