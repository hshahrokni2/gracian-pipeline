"""
Week 2 Day 5: Validation Threshold Testing Suite

Tests validation thresholds for calculated financial metrics.

Test Coverage:
1. Dynamic tolerance threshold calibration
2. Validation pass rate measurement
3. False positive rate (warnings when data is correct)
4. False negative rate (passes when data is wrong)
5. Data loss rate (nulling data incorrectly)
6. Threshold recommendations

Run: python test_validation_thresholds.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.models.brf_schema import (
    CalculatedFinancialMetrics,
    FeeStructure,
    YearlyFinancialData
)
from gracian_pipeline.models.base_fields import NumberField


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


# =============================================================================
# TEST DATA: Real-world scenarios from Swedish BRF documents
# =============================================================================

REAL_WORLD_DEBT_PER_SQM_SCENARIOS = [
    # (debt_tkr, area_sqm, extracted_debt_per_sqm, expected_status, description)
    # Sjöstaden 2: calc = 19,907.6 kr/m², tolerance = 1,990.8 kr, 2x = 3,981.5 kr
    (99538.124, 5000, 19900, "valid", "Sjöstaden 2 - exact match"),
    (99538.124, 5000, 19908, "valid", "Sjöstaden 2 - tiny rounding error"),
    (99538.124, 5000, 20000, "valid", "Sjöstaden 2 - 100 kr difference"),
    (99538.124, 5000, 21000, "valid", "Sjöstaden 2 - 1092 kr diff < tolerance (1991)"),
    (99538.124, 5000, 25000, "error", "Sjöstaden 2 - 5092 kr diff > 2x tolerance"),

    # Small BRF: calc = 10,000 kr/m², tolerance = 1,000 kr, 2x = 2,000 kr
    (5000.0, 500, 10000, "valid", "Small BRF - exact match"),
    (5000.0, 500, 10500, "valid", "Small BRF - 500 kr difference (5%)"),
    (5000.0, 500, 11500, "warning", "Small BRF - 1500 kr difference (15%)"),
    (5000.0, 500, 13000, "error", "Small BRF - 3000 kr difference (30%)"),

    # Large BRF: calc = 50,000 kr/m², tolerance = 5,000 kr, 2x = 10,000 kr
    (500000.0, 10000, 50000, "valid", "Large BRF - exact match"),
    (500000.0, 10000, 52500, "valid", "Large BRF - 2500 kr difference (5%)"),
    (500000.0, 10000, 55000, "valid", "Large BRF - 5000 kr diff = tolerance (inclusive)"),
    (500000.0, 10000, 60000, "warning", "Large BRF - 10000 kr diff = 2x tolerance (inclusive)"),
]

REAL_WORLD_SOLIDARITY_SCENARIOS = [
    # (equity_tkr, assets_tkr, extracted_solidarity, expected_status, description)
    # Tolerance = 2 pp (valid), 2x = 4 pp (warning threshold)
    (201801.694, 301339.818, 67.0, "valid", "Sjöstaden 2 - exact match"),
    (201801.694, 301339.818, 68.0, "valid", "Sjöstaden 2 - 1 pp difference"),
    (201801.694, 301339.818, 70.0, "warning", "Sjöstaden 2 - 3 pp difference"),
    (201801.694, 301339.818, 75.0, "error", "Sjöstaden 2 - 8 pp difference"),

    # High solidarity scenarios
    (90000.0, 100000.0, 90.0, "valid", "High solidarity - exact match"),
    (90000.0, 100000.0, 88.0, "valid", "High solidarity - 2 pp difference"),
    (90000.0, 100000.0, 85.0, "error", "High solidarity - 5 pp diff > 2x tolerance (4 pp)"),
    (90000.0, 100000.0, 80.0, "error", "High solidarity - 10 pp difference"),

    # Low solidarity scenarios
    (10000.0, 100000.0, 10.0, "valid", "Low solidarity - exact match"),
    (10000.0, 100000.0, 11.0, "valid", "Low solidarity - 1 pp difference"),
    (10000.0, 100000.0, 13.0, "warning", "Low solidarity - 3 pp difference"),
    (10000.0, 100000.0, 16.0, "error", "Low solidarity - 6 pp difference"),
]

REAL_WORLD_FEE_PER_SQM_SCENARIOS = [
    # (monthly_fee, area_sqm, extracted_annual_fee, expected_status, description)
    # Standard: calc = 600 kr/m²/år, tolerance = 100 kr, 2x = 200 kr
    (5000.0, 100, 600.0, "valid", "Standard apartment - exact monthly*12"),
    (5000.0, 100, 610.0, "valid", "Standard apartment - 10 kr/m² difference"),
    (5000.0, 100, 650.0, "valid", "Standard apartment - 50 kr diff < tolerance (100)"),
    (5000.0, 100, 750.0, "warning", "Standard apartment - 150 kr diff < 2x tolerance (200)"),

    # High-end: calc = 1200 kr/m²/år, tolerance = 120 kr, 2x = 240 kr
    (15000.0, 150, 1200.0, "valid", "High-end apartment - exact match"),
    (15000.0, 150, 1250.0, "valid", "High-end apartment - 50 kr/m² difference"),
    (15000.0, 150, 1350.0, "warning", "High-end apartment - 150 kr/m² difference"),
    (15000.0, 150, 1500.0, "error", "High-end apartment - 300 kr diff > 2x tolerance"),

    # Small studio: calc = 1200 kr/m²/år, tolerance = 120 kr, 2x = 240 kr
    (3000.0, 30, 1200.0, "valid", "Small studio - exact match"),
    (3000.0, 30, 1250.0, "valid", "Small studio - 50 kr/m² difference"),
    (3000.0, 30, 1350.0, "warning", "Small studio - 150 kr/m² difference"),
    (3000.0, 30, 1500.0, "error", "Small studio - 300 kr diff > 2x tolerance"),
]


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_debt_per_sqm_thresholds():
    """Test 1: Debt per sqm validation thresholds."""
    print_section("TEST 1: Debt per sqm Validation Thresholds")

    results = {"valid": 0, "warning": 0, "error": 0, "incorrect": 0}

    for debt, area, extracted_debt_per_sqm, expected_status, description in REAL_WORLD_DEBT_PER_SQM_SCENARIOS:
        metrics = CalculatedFinancialMetrics(
            total_debt_extracted=NumberField(value=debt, confidence=0.95),
            total_area_sqm_extracted=NumberField(value=area, confidence=0.95),
            debt_per_sqm_extracted=NumberField(value=extracted_debt_per_sqm, confidence=0.90)
        )

        actual_status = metrics.debt_per_sqm_status

        if actual_status == expected_status:
            results[expected_status] += 1
            status_symbol = "✅"
        else:
            results["incorrect"] += 1
            status_symbol = "❌"

        calculated = metrics.debt_per_sqm_calculated if metrics.debt_per_sqm_calculated else 0
        diff = abs(extracted_debt_per_sqm - calculated) if calculated else 0

        print(f"{status_symbol} {description}")
        print(f"   Extracted: {extracted_debt_per_sqm:,.0f} kr/m² | Calculated: {calculated:,.0f} kr/m²")
        print(f"   Difference: {diff:,.0f} kr/m² | Expected: {expected_status} | Got: {actual_status}")

    total = len(REAL_WORLD_DEBT_PER_SQM_SCENARIOS)
    correct = total - results["incorrect"]
    pass_rate = (correct / total) * 100

    print(f"\n📊 Results:")
    print(f"   Total scenarios: {total}")
    print(f"   Correct classifications: {correct} ({pass_rate:.1f}%)")
    print(f"   Valid: {results['valid']} | Warning: {results['warning']} | Error: {results['error']}")
    print(f"   Incorrect: {results['incorrect']}")

    return pass_rate >= 90.0  # 90% threshold accuracy required


def test_solidarity_percent_thresholds():
    """Test 2: Solidarity percentage validation thresholds."""
    print_section("TEST 2: Solidarity Percentage Validation Thresholds")

    results = {"valid": 0, "warning": 0, "error": 0, "incorrect": 0}

    for equity, assets, extracted_solidarity, expected_status, description in REAL_WORLD_SOLIDARITY_SCENARIOS:
        metrics = CalculatedFinancialMetrics(
            equity_extracted=NumberField(value=equity, confidence=0.95),
            assets_extracted=NumberField(value=assets, confidence=0.95),
            solidarity_percent_extracted=NumberField(value=extracted_solidarity, confidence=0.90)
        )

        actual_status = metrics.solidarity_percent_status

        if actual_status == expected_status:
            results[expected_status] += 1
            status_symbol = "✅"
        else:
            results["incorrect"] += 1
            status_symbol = "❌"

        calculated = metrics.solidarity_percent_calculated if metrics.solidarity_percent_calculated else 0
        diff = abs(extracted_solidarity - calculated) if calculated else 0

        print(f"{status_symbol} {description}")
        print(f"   Extracted: {extracted_solidarity:.1f}% | Calculated: {calculated:.1f}%")
        print(f"   Difference: {diff:.1f} pp | Expected: {expected_status} | Got: {actual_status}")

    total = len(REAL_WORLD_SOLIDARITY_SCENARIOS)
    correct = total - results["incorrect"]
    pass_rate = (correct / total) * 100

    print(f"\n📊 Results:")
    print(f"   Total scenarios: {total}")
    print(f"   Correct classifications: {correct} ({pass_rate:.1f}%)")
    print(f"   Valid: {results['valid']} | Warning: {results['warning']} | Error: {results['error']}")
    print(f"   Incorrect: {results['incorrect']}")

    return pass_rate >= 90.0


def test_fee_per_sqm_thresholds():
    """Test 3: Fee per sqm validation thresholds."""
    print_section("TEST 3: Fee per sqm Validation Thresholds")

    results = {"valid": 0, "warning": 0, "error": 0, "incorrect": 0}

    for monthly_fee, area, extracted_annual, expected_status, description in REAL_WORLD_FEE_PER_SQM_SCENARIOS:
        metrics = CalculatedFinancialMetrics(
            monthly_fee_extracted=NumberField(value=monthly_fee, confidence=0.90),
            apartment_area_extracted=NumberField(value=area, confidence=0.95),
            fee_per_sqm_annual_extracted=NumberField(value=extracted_annual, confidence=0.85)
        )

        actual_status = metrics.fee_per_sqm_status

        if actual_status == expected_status:
            results[expected_status] += 1
            status_symbol = "✅"
        else:
            results["incorrect"] += 1
            status_symbol = "❌"

        calculated = metrics.fee_per_sqm_annual_calculated if metrics.fee_per_sqm_annual_calculated else 0
        diff = abs(extracted_annual - calculated) if calculated else 0

        print(f"{status_symbol} {description}")
        print(f"   Extracted: {extracted_annual:,.0f} kr/m²/år | Calculated: {calculated:,.0f} kr/m²/år")
        print(f"   Difference: {diff:,.0f} kr/m²/år | Expected: {expected_status} | Got: {actual_status}")

    total = len(REAL_WORLD_FEE_PER_SQM_SCENARIOS)
    correct = total - results["incorrect"]
    pass_rate = (correct / total) * 100

    print(f"\n📊 Results:")
    print(f"   Total scenarios: {total}")
    print(f"   Correct classifications: {correct} ({pass_rate:.1f}%)")
    print(f"   Valid: {results['valid']} | Warning: {results['warning']} | Error: {results['error']}")
    print(f"   Incorrect: {results['incorrect']}")

    return pass_rate >= 90.0


def test_data_preservation():
    """Test 4: Data preservation - never null policy."""
    print_section("TEST 4: Data Preservation (Never Null Policy)")

    scenarios = [
        ("valid", 99538.124, 5000, 19908),
        ("warning", 201801.694, 301339.818, 70.0),
        ("error", 5000.0, 100, 750.0),
    ]

    all_preserved = True

    for status, value1, value2, extracted in scenarios:
        metrics = CalculatedFinancialMetrics(
            total_debt_extracted=NumberField(value=value1, confidence=0.95),
            total_area_sqm_extracted=NumberField(value=value2, confidence=0.95),
            debt_per_sqm_extracted=NumberField(value=extracted, confidence=0.90)
        )

        # Check all fields are preserved
        preserved = (
            metrics.total_debt_extracted is not None and
            metrics.total_area_sqm_extracted is not None and
            metrics.debt_per_sqm_extracted is not None and
            metrics.debt_per_sqm_calculated is not None
        )

        if preserved:
            print(f"✅ {status.upper()}: All data preserved")
            print(f"   Extracted: {extracted} | Calculated: {metrics.debt_per_sqm_calculated}")
        else:
            print(f"❌ {status.upper()}: Data loss detected!")
            all_preserved = False

    if all_preserved:
        print("\n✅ PASS: All data preserved across all validation tiers")
    else:
        print("\n❌ FAIL: Data loss detected in some scenarios")

    return all_preserved


def test_false_positive_rate():
    """Test 5: False positive rate (warnings when data is actually correct)."""
    print_section("TEST 5: False Positive Rate Analysis")

    # Test scenarios (each using correct fields for metric type)
    test_cases = [
        # Debt per sqm: debt, area, extracted_debt_per_sqm
        {
            "type": "debt",
            "metrics": CalculatedFinancialMetrics(
                total_debt_extracted=NumberField(value=99538.124, confidence=0.95),
                total_area_sqm_extracted=NumberField(value=5000, confidence=0.95),
                debt_per_sqm_extracted=NumberField(value=19907.6248, confidence=0.90)
            ),
            "status_field": "debt_per_sqm_status"
        },
        # Solidarity %: equity, assets, extracted_solidarity
        {
            "type": "solidarity",
            "metrics": CalculatedFinancialMetrics(
                equity_extracted=NumberField(value=201801.694, confidence=0.98),
                assets_extracted=NumberField(value=301339.818, confidence=0.98),
                solidarity_percent_extracted=NumberField(value=66.97, confidence=0.90)
            ),
            "status_field": "solidarity_percent_status"
        },
        # Fee per sqm: monthly_fee, area, extracted_fee_annual
        {
            "type": "fee",
            "metrics": CalculatedFinancialMetrics(
                monthly_fee_extracted=NumberField(value=5000.0, confidence=0.90),
                apartment_area_extracted=NumberField(value=100, confidence=0.95),
                fee_per_sqm_annual_extracted=NumberField(value=600.0, confidence=0.90)
            ),
            "status_field": "fee_per_sqm_status"
        },
    ]

    false_positives = 0
    total = len(test_cases)

    for case in test_cases:
        status = getattr(case["metrics"], case["status_field"])
        if status != "valid":
            false_positives += 1
            print(f"❌ FALSE POSITIVE: {case['type']} exact match marked as {status}")
        else:
            print(f"✅ Correct: {case['type']} exact match correctly classified as valid")

    false_positive_rate = (false_positives / total) * 100

    print(f"\n📊 False Positive Rate: {false_positive_rate:.1f}%")
    print(f"   Target: <5% (excellent), <10% (acceptable)")

    return false_positive_rate < 10.0


def test_false_negative_rate():
    """Test 6: False negative rate (passes when data is clearly wrong)."""
    print_section("TEST 6: False Negative Rate Analysis")

    # Test scenarios with large errors (each using correct fields for metric type)
    test_cases = [
        # Debt per sqm: 50% error (should be error or warning, not valid)
        {
            "type": "debt",
            "description": "30000 vs 19908 - 50% error",
            "metrics": CalculatedFinancialMetrics(
                total_debt_extracted=NumberField(value=99538.124, confidence=0.95),
                total_area_sqm_extracted=NumberField(value=5000, confidence=0.95),
                debt_per_sqm_extracted=NumberField(value=30000, confidence=0.90)
            ),
            "status_field": "debt_per_sqm_status"
        },
        # Solidarity %: 23 pp error (should be error, not valid)
        {
            "type": "solidarity",
            "description": "90% vs 67% - 23 pp error",
            "metrics": CalculatedFinancialMetrics(
                equity_extracted=NumberField(value=201801.694, confidence=0.98),
                assets_extracted=NumberField(value=301339.818, confidence=0.98),
                solidarity_percent_extracted=NumberField(value=90.0, confidence=0.90)
            ),
            "status_field": "solidarity_percent_status"
        },
        # Fee per sqm: 67% error (should be error, not valid)
        {
            "type": "fee",
            "description": "1000 vs 600 - 67% error",
            "metrics": CalculatedFinancialMetrics(
                monthly_fee_extracted=NumberField(value=5000.0, confidence=0.90),
                apartment_area_extracted=NumberField(value=100, confidence=0.95),
                fee_per_sqm_annual_extracted=NumberField(value=1000.0, confidence=0.90)
            ),
            "status_field": "fee_per_sqm_status"
        },
    ]

    false_negatives = 0
    total = len(test_cases)

    for case in test_cases:
        status = getattr(case["metrics"], case["status_field"])
        if status == "valid":
            false_negatives += 1
            print(f"❌ FALSE NEGATIVE: {case['type']} {case['description']} marked as valid")
        else:
            print(f"✅ Correct: {case['type']} {case['description']} correctly flagged as {status}")

    false_negative_rate = (false_negatives / total) * 100

    print(f"\n📊 False Negative Rate: {false_negative_rate:.1f}%")
    print(f"   Target: 0% (no large errors should pass)")

    return false_negative_rate == 0.0


def generate_threshold_report(results: Dict[str, bool]):
    """Generate comprehensive threshold calibration report."""
    print_section("THRESHOLD CALIBRATION REPORT")

    print("📊 Test Results Summary:")
    print(f"   Debt per sqm thresholds: {'✅ PASS' if results['debt_per_sqm'] else '❌ FAIL'}")
    print(f"   Solidarity % thresholds: {'✅ PASS' if results['solidarity'] else '❌ FAIL'}")
    print(f"   Fee per sqm thresholds: {'✅ PASS' if results['fee_per_sqm'] else '❌ FAIL'}")
    print(f"   Data preservation: {'✅ PASS' if results['data_preservation'] else '❌ FAIL'}")
    print(f"   False positive rate: {'✅ PASS' if results['false_positive'] else '❌ FAIL'}")
    print(f"   False negative rate: {'✅ PASS' if results['false_negative'] else '❌ FAIL'}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    pass_rate = (passed / total) * 100

    print(f"\n🎯 Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")

    if pass_rate == 100.0:
        print("\n✅ RECOMMENDATION: Current thresholds are well-calibrated")
        print("   - 90%+ classification accuracy across all metrics")
        print("   - <10% false positive rate")
        print("   - 0% false negative rate")
        print("   - 100% data preservation")
    elif pass_rate >= 80.0:
        print("\n⚠️ RECOMMENDATION: Minor threshold adjustments needed")
        print("   - Review failed test categories")
        print("   - Consider tightening tolerances for false positives")
        print("   - Or loosening tolerances for false negatives")
    else:
        print("\n❌ RECOMMENDATION: Significant threshold recalibration required")
        print("   - Review tolerance formulas")
        print("   - Analyze real-world data distribution")
        print("   - Consider Swedish BRF-specific adjustments")

    return pass_rate >= 90.0


def main():
    """Run all validation threshold tests."""
    print("\n" + "=" * 70)
    print("WEEK 2 DAY 5: VALIDATION THRESHOLD TESTING SUITE")
    print("=" * 70)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing on real-world Swedish BRF scenarios")

    results = {}

    try:
        results['debt_per_sqm'] = test_debt_per_sqm_thresholds()
    except Exception as e:
        print(f"\n❌ test_debt_per_sqm_thresholds FAILED: {e}")
        results['debt_per_sqm'] = False

    try:
        results['solidarity'] = test_solidarity_percent_thresholds()
    except Exception as e:
        print(f"\n❌ test_solidarity_percent_thresholds FAILED: {e}")
        results['solidarity'] = False

    try:
        results['fee_per_sqm'] = test_fee_per_sqm_thresholds()
    except Exception as e:
        print(f"\n❌ test_fee_per_sqm_thresholds FAILED: {e}")
        results['fee_per_sqm'] = False

    try:
        results['data_preservation'] = test_data_preservation()
    except Exception as e:
        print(f"\n❌ test_data_preservation FAILED: {e}")
        results['data_preservation'] = False

    try:
        results['false_positive'] = test_false_positive_rate()
    except Exception as e:
        print(f"\n❌ test_false_positive_rate FAILED: {e}")
        results['false_positive'] = False

    try:
        results['false_negative'] = test_false_negative_rate()
    except Exception as e:
        print(f"\n❌ test_false_negative_rate FAILED: {e}")
        results['false_negative'] = False

    # Generate report
    overall_pass = generate_threshold_report(results)

    print("\n" + "=" * 70)

    if overall_pass:
        print("🎉 ALL TESTS PASSED! Week 2 Day 5 Validation Thresholds COMPLETE!")
        print("=" * 70 + "\n")
        return 0
    else:
        print("⚠️ Some tests failed. Review recommendations above.")
        print("=" * 70 + "\n")
        return 1


if __name__ == "__main__":
    exit(main())
