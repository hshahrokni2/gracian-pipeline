#!/usr/bin/env python3
"""
Quick metadata validation - just check if it's working now
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

print("🔬 QUICK METADATA VALIDATION")
print("="*80)
print()

pdf_path = "SRS/brf_198532.pdf"

try:
    report = extract_brf_to_pydantic(pdf_path, mode="fast")

    print()
    print("="*80)
    print("📊 METADATA RESULTS:")
    print("="*80)

    meta = report.metadata

    print(f"   Organization Number: {meta.organization_number.value}")
    print(f"   BRF Name: {meta.brf_name.value}")
    print(f"   Fiscal Year: {meta.fiscal_year.value}")
    print()

    # Compare against ground truth
    print("✅ COMPARISON:")
    org_match = meta.organization_number.value == "769629-0134"
    year_match = meta.fiscal_year.value == 2021
    name_partial = "Björk och Plaza" in meta.brf_name.value or "Bj\u00f6rk och Plaza" in meta.brf_name.value

    print(f"   Org Number: {'✅ CORRECT' if org_match else '❌ WRONG'} ({meta.organization_number.value} vs 769629-0134)")
    print(f"   Fiscal Year: {'✅ CORRECT' if year_match else '❌ WRONG'} ({meta.fiscal_year.value} vs 2021)")
    print(f"   BRF Name: {'⚠️ PARTIAL' if name_partial else '❌ WRONG'} ({meta.brf_name.value})")
    print()

    if org_match and year_match:
        print("🎉 METADATA EXTRACTION IS WORKING!")
        print("   Issue #1 (metadata) is FIXED ✅")
    else:
        print("❌ Metadata extraction still has issues")

except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
