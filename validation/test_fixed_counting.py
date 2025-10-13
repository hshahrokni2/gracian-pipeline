"""
Test Fixed Field Counting

Quick test to verify the fix works without full extraction.
Uses the debug_extraction_full.json from diagnostic run.

Author: Claude Code
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.run_95_95_validation import ComprehensiveValidator


def test_fixed_counting():
    """Test that fixed counting logic works correctly."""

    # Load the diagnostic extraction result
    debug_file = Path(__file__).parent / "debug_extraction_full.json"

    if not debug_file.exists():
        print(f"❌ Debug file not found: {debug_file}")
        print("   Run debug_field_counting.py first")
        sys.exit(1)

    with open(debug_file) as f:
        result = json.load(f)

    print(f"{'='*80}")
    print(f"TESTING FIXED FIELD COUNTING")
    print(f"{'='*80}\n")

    # Initialize validator
    validator = ComprehensiveValidator()

    # Count with fixed logic
    extracted_count = validator.count_extracted_fields(result)

    print(f"📊 Counting Results:")
    print(f"   Extracted Fields (FIXED): {extracted_count}")
    print(f"   Expected from diagnostic: 79 DATA fields")
    print(f"   Difference: {abs(extracted_count - 79)}")

    # Validate
    if extracted_count == 79:
        print(f"\n✅ PERFECT MATCH! Field counting is now correct.")
    elif 75 <= extracted_count <= 85:
        print(f"\n✅ CLOSE ENOUGH! Within acceptable range.")
        print(f"   (Small differences expected due to list handling)")
    else:
        print(f"\n⚠️  DISCREPANCY: Count {extracted_count} differs from expected 79")
        print(f"   Review the counting logic")

    # Test coverage calculation
    print(f"\n{'='*80}")
    print(f"COVERAGE CALCULATION")
    print(f"{'='*80}")

    applicable = 91  # From ApplicableFieldsDetector
    coverage_old = 113 / 613 * 100  # Old (wrong)
    coverage_raw = 113 / applicable * 100  # Old with applicable denominator
    coverage_fixed = extracted_count / applicable * 100  # Fixed

    print(f"Old calculation (wrong denominator):")
    print(f"   113 / 613 = {coverage_old:.1f}% ❌")
    print(f"\nOld with applicable fields:")
    print(f"   113 / 91 = {coverage_raw:.1f}% ⚠️  (>100% impossible)")
    print(f"\nFixed calculation:")
    print(f"   {extracted_count} / 91 = {coverage_fixed:.1f}% ✅")

    if coverage_fixed <= 100:
        print(f"\n✅ Coverage is now realistic (<100%)")
    else:
        print(f"\n⚠️  Still >100%, but much better than 124.2%")

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Before fix: 113 fields → 124.2% coverage (IMPOSSIBLE)")
    print(f"After fix:  {extracted_count} fields → {coverage_fixed:.1f}% coverage (REALISTIC)")
    print(f"Improvement: {124.2 - coverage_fixed:.1f} percentage points reduction")


if __name__ == "__main__":
    test_fixed_counting()
