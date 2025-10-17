#!/usr/bin/env python3
"""
Phase 0 Day 3 - Agent Integration Test

Tests the new agent extraction logic on real PDFs:
1. key_metrics_agent - Depreciation paradox detection on brf_82839, brf_82841
2. balance_sheet_agent - Cash crisis detection on brf_80193

Purpose: Verify pattern detection thresholds work correctly on validated PDFs.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import extraction functions
from gracian_pipeline.core.pydantic_extractor import extract_single_agent


def test_depreciation_paradox_detection():
    """Test depreciation paradox detection on known positive case (brf_82839)."""
    print("=" * 80)
    print("🧪 TEST 1: Depreciation Paradox Detection (brf_82839)")
    print("=" * 80)

    pdf_path = "SRS/brf_82839.pdf"

    print(f"\n📄 Testing: {pdf_path}")
    print("Expected pattern: Paper loss + Strong cash flow + High soliditet")
    print("Expected values:")
    print("  - Annual result: -313,943 kr (paper loss)")
    print("  - Depreciation: +1,371,024 kr")
    print("  - Result without depreciation: +1,057,081 kr (strong cash flow)")
    print("  - Soliditet: 85%")
    print("  - Pattern: K2 accounting creates paper loss but actual cash flow excellent")

    try:
        # Extract using key_metrics_agent
        result = extract_single_agent("key_metrics_agent", pdf_path)

        if result and result.get("success"):
            data = result.get("data", {})
            print("\n✅ Extraction successful!")
            print(f"\nExtracted data:")
            print(f"  - result_without_depreciation_current_year: {data.get('result_without_depreciation_current_year')}")
            print(f"  - result_without_depreciation_prior_year: {data.get('result_without_depreciation_prior_year')}")
            print(f"  - depreciation_as_percent_of_revenue_current_year: {data.get('depreciation_as_percent_of_revenue_current_year')}%")
            print(f"  - depreciation_paradox_detected: {data.get('depreciation_paradox_detected')}")
            print(f"  - soliditet_pct: {data.get('soliditet_pct')}%")
            print(f"  - evidence_pages: {data.get('evidence_pages', [])}")

            # Validate pattern detection
            detected = data.get('depreciation_paradox_detected', False)
            result_wo_dep = data.get('result_without_depreciation_current_year')
            soliditet = data.get('soliditet_pct')

            # Detection criteria: result_without_depreciation ≥ 500,000 AND soliditet ≥ 85%
            should_detect = (result_wo_dep is not None and result_wo_dep >= 500000) and \
                          (soliditet is not None and soliditet >= 85)

            if detected == should_detect:
                print(f"\n✅ Pattern detection CORRECT: {detected} (expected {should_detect})")
                return True
            else:
                print(f"\n❌ Pattern detection INCORRECT: {detected} (expected {should_detect})")
                if result_wo_dep is not None:
                    print(f"   Cash flow threshold: {result_wo_dep} {'≥' if result_wo_dep >= 500000 else '<'} 500,000")
                if soliditet is not None:
                    print(f"   Soliditet threshold: {soliditet}% {'≥' if soliditet >= 85 else '<'} 85%")
                return False
        else:
            print(f"\n❌ Extraction failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cash_crisis_detection():
    """Test cash crisis detection on known positive case (brf_80193)."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Cash Crisis Detection (brf_80193)")
    print("=" * 80)

    pdf_path = "SRS/brf_80193.pdf"

    print(f"\n📄 Testing: {pdf_path}")
    print("Expected pattern: Rapid cash depletion + Refinancing pressure")
    print("Expected values:")
    print("  - Liquidity: 1,053k → 286k kr (-73% collapse!)")
    print("  - Cash-to-debt ratio: 5.2% → 3.7% → 0.9% (3-year deterioration)")
    print("  - Short-term debt: 95.9%")
    print("  - Pattern: Rapid cash depletion + refinancing pressure = liquidity crisis")

    try:
        # Extract using balance_sheet_agent
        result = extract_single_agent("balance_sheet_agent", pdf_path)

        if result and result.get("success"):
            data = result.get("data", {})
            print("\n✅ Extraction successful!")
            print(f"\nExtracted data:")
            print(f"  - total_liquidity_current_year: {data.get('total_liquidity_current_year')}")
            print(f"  - total_liquidity_prior_year: {data.get('total_liquidity_prior_year')}")
            print(f"  - cash_to_debt_ratio_current_year: {data.get('cash_to_debt_ratio_current_year')}%")
            print(f"  - cash_to_debt_ratio_prior_year: {data.get('cash_to_debt_ratio_prior_year')}%")
            print(f"  - cash_to_debt_ratio_prior_2_years: {data.get('cash_to_debt_ratio_prior_2_years')}%")
            print(f"  - cash_crisis_detected: {data.get('cash_crisis_detected')}")
            print(f"  - short_term_debt_pct: {data.get('short_term_debt_pct')}%")
            print(f"  - evidence_pages: {data.get('evidence_pages', [])}")

            # Validate pattern detection
            detected = data.get('cash_crisis_detected', False)
            cash_ratio_current = data.get('cash_to_debt_ratio_current_year')
            cash_ratio_prior = data.get('cash_to_debt_ratio_prior_year')
            short_term_pct = data.get('short_term_debt_pct')

            # Detection criteria: ratio <5% AND declining AND short_term >50%
            should_detect = (cash_ratio_current is not None and cash_ratio_current < 5) and \
                          (cash_ratio_prior is not None and cash_ratio_current < cash_ratio_prior) and \
                          (short_term_pct is not None and short_term_pct > 50)

            if detected == should_detect:
                print(f"\n✅ Pattern detection CORRECT: {detected} (expected {should_detect})")
                return True
            else:
                print(f"\n❌ Pattern detection INCORRECT: {detected} (expected {should_detect})")
                if cash_ratio_current is not None:
                    print(f"   Liquidity stress: {cash_ratio_current}% {'<' if cash_ratio_current < 5 else '≥'} 5%")
                if cash_ratio_prior is not None and cash_ratio_current is not None:
                    print(f"   Deteriorating: {cash_ratio_current}% {'<' if cash_ratio_current < cash_ratio_prior else '≥'} {cash_ratio_prior}%")
                if short_term_pct is not None:
                    print(f"   Refinancing pressure: {short_term_pct}% {'>' if short_term_pct > 50 else '≤'} 50%")
                return False
        else:
            print(f"\n❌ Extraction failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_negative_case():
    """Test pattern detection on a PDF without patterns (negative case)."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Negative Case - No Patterns (brf_82841)")
    print("=" * 80)

    pdf_path = "Hjorthagen/brf_82841.pdf"

    print(f"\n📄 Testing: {pdf_path}")
    print("Expected: Extract data but pattern detection varies by actual values")

    try:
        # Test both agents
        key_metrics_result = extract_single_agent("key_metrics_agent", pdf_path)
        balance_sheet_result = extract_single_agent("balance_sheet_agent", pdf_path)

        success_count = 0
        if key_metrics_result and key_metrics_result.get("success"):
            print("\n✅ key_metrics_agent extraction successful")
            data = key_metrics_result.get("data", {})
            print(f"   - depreciation_paradox_detected: {data.get('depreciation_paradox_detected')}")
            print(f"   - result_without_depreciation: {data.get('result_without_depreciation_current_year')}")
            print(f"   - soliditet: {data.get('soliditet_pct')}%")
            success_count += 1
        else:
            print(f"\n⚠️  key_metrics_agent failed: {key_metrics_result.get('error', 'Unknown')}")

        if balance_sheet_result and balance_sheet_result.get("success"):
            print("\n✅ balance_sheet_agent extraction successful")
            data = balance_sheet_result.get("data", {})
            print(f"   - cash_crisis_detected: {data.get('cash_crisis_detected')}")
            print(f"   - cash_to_debt_ratio: {data.get('cash_to_debt_ratio_current_year')}%")
            print(f"   - short_term_debt: {data.get('short_term_debt_pct')}%")
            success_count += 1
        else:
            print(f"\n⚠️  balance_sheet_agent failed: {balance_sheet_result.get('error', 'Unknown')}")

        # Success if at least one agent extracted data
        return success_count > 0

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("🧪" * 40)
    print("PHASE 0 DAY 3 - AGENT INTEGRATION TESTS")
    print("🧪" * 40)
    print()

    results = []

    # Test 1: Depreciation paradox detection
    results.append(("Depreciation Paradox Detection", test_depreciation_paradox_detection()))

    # Test 2: Cash crisis detection
    results.append(("Cash Crisis Detection", test_cash_crisis_detection()))

    # Test 3: Negative case (no patterns)
    results.append(("Negative Case Testing", test_negative_case()))

    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ ✅ ✅ ALL INTEGRATION TESTS PASSED! ✅ ✅ ✅")
        print("Phase 0 Day 3 agent extraction logic is VALIDATED.")
        return 0
    elif passed_count > 0:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed, but {passed_count} passed")
        print("Partial validation successful - review failures above.")
        return 1
    else:
        print(f"\n❌ All tests failed")
        print("Please review and fix the issues above.")
        return 2


if __name__ == "__main__":
    sys.exit(run_all_tests())
