"""
Test Issue #2 Enhancement: Liabilities Breakdown Extraction

Validates that long_term_liabilities and short_term_liabilities are correctly extracted
from Balance Sheet (Balansräkning).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic
import traceback

# Load environment variables
load_dotenv()


def test_liabilities_extraction():
    """Test liabilities breakdown on brf_198532.pdf in fast mode."""

    pdf_path = "experiments/docling_advanced/test_pdfs/brf_198532.pdf"

    print("=" * 80)
    print("LIABILITIES BREAKDOWN EXTRACTION TEST")
    print("=" * 80)
    print(f"\nTest Document: {pdf_path}")
    print("Mode: fast (no vision)")
    print("\nExpected Ground Truth Values:")
    print("  - long_term_liabilities: 114,480 tkr (Note 5: Långfristiga låneskulder)")
    print("  - short_term_liabilities: 5,137 tkr (Kortfristiga skulder)")
    print("  - Total liabilities: 119,617 tkr")
    print("\n" + "=" * 80)

    try:
        # Run extraction in fast mode
        print("\n🔄 Running extraction (fast mode)...\n")
        report = extract_brf_to_pydantic(pdf_path, mode="fast")

        # Access financial data
        financial = report.financial

        if financial and financial.balance_sheet:
            balance_sheet = financial.balance_sheet

            print("=" * 80)
            print("EXTRACTION RESULTS")
            print("=" * 80)

            # Total liabilities
            total_liabilities = None
            if balance_sheet.liabilities_total:
                total_liabilities = balance_sheet.liabilities_total.value
                print(f"\n✓ Total Liabilities: {total_liabilities:,.0f} kr")
            else:
                print("\n✗ Total Liabilities: NOT EXTRACTED")

            # Long-term liabilities
            long_term = None
            if balance_sheet.long_term_liabilities:
                long_term = balance_sheet.long_term_liabilities.value
                print(f"✓ Long-term Liabilities: {long_term:,.0f} kr")
            else:
                print("✗ Long-term Liabilities: NOT EXTRACTED")

            # Short-term liabilities
            short_term = None
            if balance_sheet.short_term_liabilities:
                short_term = balance_sheet.short_term_liabilities.value
                print(f"✓ Short-term Liabilities: {short_term:,.0f} kr")
            else:
                print("✗ Short-term Liabilities: NOT EXTRACTED")

            # Validation
            print("\n" + "=" * 80)
            print("VALIDATION RESULTS")
            print("=" * 80)

            ground_truth = {
                "long_term_liabilities": 114_480_000,  # 114,480 tkr
                "short_term_liabilities": 5_137_000,   # 5,137 tkr
                "total_liabilities": 119_617_000        # 119,617 tkr
            }

            results = []

            # Validate long-term liabilities
            if long_term:
                tolerance = ground_truth["long_term_liabilities"] * 0.05  # 5% tolerance
                diff = abs(long_term - ground_truth["long_term_liabilities"])
                if diff <= tolerance:
                    print(f"✅ Long-term Liabilities: MATCH (within 5% tolerance)")
                    print(f"   Expected: {ground_truth['long_term_liabilities']:,.0f} kr")
                    print(f"   Extracted: {long_term:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['long_term_liabilities']*100):.2f}%)")
                    results.append(True)
                else:
                    print(f"⚠️  Long-term Liabilities: MISMATCH (exceeds 5% tolerance)")
                    print(f"   Expected: {ground_truth['long_term_liabilities']:,.0f} kr")
                    print(f"   Extracted: {long_term:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['long_term_liabilities']*100):.2f}%)")
                    results.append(False)
            else:
                print("❌ Long-term Liabilities: NOT EXTRACTED")
                results.append(False)

            # Validate short-term liabilities
            if short_term:
                tolerance = ground_truth["short_term_liabilities"] * 0.05  # 5% tolerance
                diff = abs(short_term - ground_truth["short_term_liabilities"])
                if diff <= tolerance:
                    print(f"\n✅ Short-term Liabilities: MATCH (within 5% tolerance)")
                    print(f"   Expected: {ground_truth['short_term_liabilities']:,.0f} kr")
                    print(f"   Extracted: {short_term:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['short_term_liabilities']*100):.2f}%)")
                    results.append(True)
                else:
                    print(f"\n⚠️  Short-term Liabilities: MISMATCH (exceeds 5% tolerance)")
                    print(f"   Expected: {ground_truth['short_term_liabilities']:,.0f} kr")
                    print(f"   Extracted: {short_term:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['short_term_liabilities']*100):.2f}%)")
                    results.append(False)
            else:
                print("\n❌ Short-term Liabilities: NOT EXTRACTED")
                results.append(False)

            # Validate total (for completeness)
            if total_liabilities:
                tolerance = ground_truth["total_liabilities"] * 0.05  # 5% tolerance
                diff = abs(total_liabilities - ground_truth["total_liabilities"])
                if diff <= tolerance:
                    print(f"\n✅ Total Liabilities: MATCH (within 5% tolerance)")
                    print(f"   Expected: {ground_truth['total_liabilities']:,.0f} kr")
                    print(f"   Extracted: {total_liabilities:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['total_liabilities']*100):.2f}%)")
                else:
                    print(f"\n⚠️  Total Liabilities: MISMATCH (exceeds 5% tolerance)")
                    print(f"   Expected: {ground_truth['total_liabilities']:,.0f} kr")
                    print(f"   Extracted: {total_liabilities:,.0f} kr")
                    print(f"   Difference: {diff:,.0f} kr ({(diff/ground_truth['total_liabilities']*100):.2f}%)")

            # Final verdict
            print("\n" + "=" * 80)
            print("FINAL VERDICT")
            print("=" * 80)

            if all(results):
                print("\n🎉 SUCCESS: All liabilities breakdown fields extracted correctly!")
                print("✅ Issue #2 Enhancement: VALIDATED")
                return True
            else:
                passed = sum(results)
                total = len(results)
                print(f"\n⚠️  PARTIAL SUCCESS: {passed}/{total} fields extracted correctly")
                print("🔧 Issue #2 Enhancement: NEEDS INVESTIGATION")
                return False

        else:
            print("\n❌ ERROR: No financial data extracted")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_liabilities_extraction()
    sys.exit(0 if success else 1)
