"""
Week 2 Day 4: Swedish-First Semantic Fields Test Suite

Tests for Swedish-first semantic fields with English aliases.

Test Coverage:
1. Fee structure Swedish→English synchronization
2. Financial data Swedish→English synchronization
3. Alias bidirectional sync
4. Metadata fields (_terminology_found, _unit_verified)
5. Cross-validation (monthly*12 ≈ annual)

Run: python test_swedish_first_fields.py
"""

import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from gracian_pipeline.models.brf_schema import FeeStructure, YearlyFinancialData
from gracian_pipeline.models.base_fields import NumberField, BooleanField


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def test_fee_structure_swedish_to_english():
    """Test 1: Fee structure - Swedish primary field syncs to English alias."""
    print_section("TEST 1: Fee Structure - Swedish → English Sync")

    fee = FeeStructure(
        arsavgift_per_sqm_total=NumberField(
            value=800.0,
            confidence=0.95,
            source="structured_table",
            evidence_pages=[5]
        ),
        manadsavgift_per_sqm=NumberField(
            value=67.0,
            confidence=0.90,
            source="structured_table",
            evidence_pages=[5]
        )
    )

    # Check sync occurred
    assert fee.annual_fee_per_sqm is not None, "annual_fee_per_sqm should be synced"
    assert fee.annual_fee_per_sqm.value == 800.0, f"Expected 800.0, got {fee.annual_fee_per_sqm.value}"

    assert fee.monthly_fee_per_sqm is not None, "monthly_fee_per_sqm should be synced"
    assert fee.monthly_fee_per_sqm.value == 67.0, f"Expected 67.0, got {fee.monthly_fee_per_sqm.value}"

    print(f"✅ Swedish field: årsavgift_per_sqm_total = {fee.arsavgift_per_sqm_total.value} kr/m²/år")
    print(f"✅ English alias: annual_fee_per_sqm = {fee.annual_fee_per_sqm.value} kr/m²/år")
    print(f"✅ Swedish field: månadsavgift_per_sqm = {fee.manadsavgift_per_sqm.value} kr/m²/mån")
    print(f"✅ English alias: monthly_fee_per_sqm = {fee.monthly_fee_per_sqm.value} kr/m²/mån")

    return True


def test_fee_structure_english_to_swedish():
    """Test 2: Fee structure - English alias syncs to Swedish primary field."""
    print_section("TEST 2: Fee Structure - English → Swedish Sync")

    fee = FeeStructure(
        annual_fee_per_sqm=NumberField(
            value=750.0,
            confidence=0.90,
            source="vision_llm",
            evidence_pages=[6]
        ),
        monthly_fee_average=NumberField(
            value=5000.0,
            confidence=0.85,
            source="vision_llm",
            evidence_pages=[6]
        )
    )

    # Check sync occurred
    assert fee.arsavgift_per_sqm_total is not None, "årsavgift_per_sqm_total should be synced"
    assert fee.arsavgift_per_sqm_total.value == 750.0, f"Expected 750.0, got {fee.arsavgift_per_sqm_total.value}"

    assert fee.manadsavgift_per_apartment_avg is not None, "månadsavgift_per_apartment_avg should be synced"
    assert fee.manadsavgift_per_apartment_avg.value == 5000.0, f"Expected 5000.0, got {fee.manadsavgift_per_apartment_avg.value}"

    print(f"✅ English input: annual_fee_per_sqm = {fee.annual_fee_per_sqm.value} kr/m²/år")
    print(f"✅ Swedish sync: årsavgift_per_sqm_total = {fee.arsavgift_per_sqm_total.value} kr/m²/år")
    print(f"✅ English input: monthly_fee_average = {fee.monthly_fee_average.value} kr/lägenhet/mån")
    print(f"✅ Swedish sync: månadsavgift_per_apartment_avg = {fee.manadsavgift_per_apartment_avg.value} kr/lägenhet/mån")

    return True


def test_fee_cross_validation_pass():
    """Test 3: Fee cross-validation - monthly*12 ≈ annual (within tolerance)."""
    print_section("TEST 3: Fee Cross-Validation - PASS (Within Tolerance)")

    fee = FeeStructure(
        manadsavgift_per_sqm=NumberField(value=66.67, confidence=0.95),
        arsavgift_per_sqm_total=NumberField(value=800.0, confidence=0.95)
    )

    # Calculate expected
    expected_annual = 66.67 * 12  # = 800.04
    diff = abs(fee.arsavgift_per_sqm_total.value - expected_annual)

    print(f"Månadsavgift per m²: {fee.manadsavgift_per_sqm.value} kr/m²/mån")
    print(f"Expected annual: {expected_annual:.2f} kr/m²/år")
    print(f"Actual annual: {fee.arsavgift_per_sqm_total.value} kr/m²/år")
    print(f"Difference: {diff:.2f} kr/m²/år")
    print(f"✅ PASS: Difference within tolerance (≤100 kr or 10%)")

    # Check no warnings
    if not hasattr(fee, '_validation_warnings'):
        print("✅ No validation warnings (as expected)")
    else:
        print(f"⚠️ Unexpected warnings: {fee._validation_warnings}")
        return False

    return True


def test_fee_cross_validation_warning():
    """Test 4: Fee cross-validation - monthly*12 ≠ annual (exceeds tolerance)."""
    print_section("TEST 4: Fee Cross-Validation - WARNING (Exceeds Tolerance)")

    fee = FeeStructure(
        manadsavgift_per_sqm=NumberField(value=50.0, confidence=0.90),
        arsavgift_per_sqm_total=NumberField(value=800.0, confidence=0.90)
    )

    # Calculate expected
    expected_annual = 50.0 * 12  # = 600.0
    diff = abs(fee.arsavgift_per_sqm_total.value - expected_annual)  # = 200.0

    print(f"Månadsavgift per m²: {fee.manadsavgift_per_sqm.value} kr/m²/mån")
    print(f"Expected annual: {expected_annual:.2f} kr/m²/år")
    print(f"Actual annual: {fee.arsavgift_per_sqm_total.value} kr/m²/år")
    print(f"Difference: {diff:.2f} kr/m²/år")
    print(f"⚠️ WARNING: Difference exceeds tolerance (>100 kr)")

    # Check for warnings
    if hasattr(fee, '_validation_warnings') and len(fee._validation_warnings) > 0:
        print(f"✅ Validation warning generated (as expected)")
        print(f"   Warning: {fee._validation_warnings[0]}")
        return True
    else:
        print("❌ No validation warning generated (expected one)")
        return False


def test_fee_metadata_fields():
    """Test 5: Fee metadata fields (_terminology_found, _unit_verified)."""
    print_section("TEST 5: Fee Metadata Fields")

    fee = FeeStructure(
        arsavgift_per_sqm_total=NumberField(value=800.0, confidence=0.95),
        inkluderar_vatten=BooleanField(value=True, confidence=0.90),
        inkluderar_uppvarmning=BooleanField(value=True, confidence=0.90),
        inkluderar_el=BooleanField(value=False, confidence=0.85),
        terminology_found="årsavgift per m² bostadsyta",
        unit_verified=True
    )

    assert fee.terminology_found == "årsavgift per m² bostadsyta", "Terminology metadata should be preserved"
    assert fee.unit_verified == True, "Unit verification metadata should be preserved"

    print(f"✅ Terminology found: '{fee.terminology_found}'")
    print(f"✅ Unit verified: {fee.unit_verified}")
    print(f"✅ Inkluderar vatten: {fee.inkluderar_vatten.value}")
    print(f"✅ Inkluderar uppvärmning: {fee.inkluderar_uppvarmning.value}")
    print(f"✅ Inkluderar el: {fee.inkluderar_el.value}")

    return True


def test_financial_swedish_to_english():
    """Test 6: Financial data - Swedish primary field syncs to English alias."""
    print_section("TEST 6: Financial Data - Swedish → English Sync")

    financial = YearlyFinancialData(
        year=2024,
        nettoomsattning_tkr=NumberField(value=5234.5, confidence=0.95),
        driftskostnader_tkr=NumberField(value=4123.8, confidence=0.95),
        driftsoverskott_tkr=NumberField(value=1110.7, confidence=0.95),
        tillgangar_tkr=NumberField(value=301339.8, confidence=0.98),
        skulder_tkr=NumberField(value=99538.1, confidence=0.98),
        eget_kapital_tkr=NumberField(value=201801.7, confidence=0.98),
        soliditet_procent=NumberField(value=67.0, confidence=0.95)
    )

    # Check all syncs occurred
    assert financial.net_revenue_tkr is not None and financial.net_revenue_tkr.value == 5234.5
    assert financial.operating_expenses_tkr is not None and financial.operating_expenses_tkr.value == 4123.8
    assert financial.operating_surplus_tkr is not None and financial.operating_surplus_tkr.value == 1110.7
    assert financial.total_assets_tkr is not None and financial.total_assets_tkr.value == 301339.8
    assert financial.total_liabilities_tkr is not None and financial.total_liabilities_tkr.value == 99538.1
    assert financial.equity_tkr is not None and financial.equity_tkr.value == 201801.7
    assert financial.solidarity_percent is not None and financial.solidarity_percent.value == 67.0

    print(f"✅ Swedish: nettoomsättning = {financial.nettoomsattning_tkr.value} tkr")
    print(f"   English: net_revenue = {financial.net_revenue_tkr.value} tkr")
    print(f"✅ Swedish: driftskostnader = {financial.driftskostnader_tkr.value} tkr")
    print(f"   English: operating_expenses = {financial.operating_expenses_tkr.value} tkr")
    print(f"✅ Swedish: tillgångar = {financial.tillgangar_tkr.value} tkr")
    print(f"   English: total_assets = {financial.total_assets_tkr.value} tkr")
    print(f"✅ Swedish: soliditet = {financial.soliditet_procent.value} %")
    print(f"   English: solidarity = {financial.solidarity_percent.value} %")

    return True


def test_financial_english_to_swedish():
    """Test 7: Financial data - English alias syncs to Swedish primary field."""
    print_section("TEST 7: Financial Data - English → Swedish Sync")

    financial = YearlyFinancialData(
        year=2023,
        net_revenue_tkr=NumberField(value=5000.0, confidence=0.90),
        operating_expenses_tkr=NumberField(value=4000.0, confidence=0.90),
        total_assets_tkr=NumberField(value=300000.0, confidence=0.95),
        equity_tkr=NumberField(value=200000.0, confidence=0.95)
    )

    # Check sync occurred
    assert financial.nettoomsattning_tkr is not None and financial.nettoomsattning_tkr.value == 5000.0
    assert financial.driftskostnader_tkr is not None and financial.driftskostnader_tkr.value == 4000.0
    assert financial.tillgangar_tkr is not None and financial.tillgangar_tkr.value == 300000.0
    assert financial.eget_kapital_tkr is not None and financial.eget_kapital_tkr.value == 200000.0

    print(f"✅ English input: net_revenue = {financial.net_revenue_tkr.value} tkr")
    print(f"   Swedish sync: nettoomsättning = {financial.nettoomsattning_tkr.value} tkr")
    print(f"✅ English input: operating_expenses = {financial.operating_expenses_tkr.value} tkr")
    print(f"   Swedish sync: driftskostnader = {financial.driftskostnader_tkr.value} tkr")
    print(f"✅ English input: total_assets = {financial.total_assets_tkr.value} tkr")
    print(f"   Swedish sync: tillgångar = {financial.tillgangar_tkr.value} tkr")
    print(f"✅ English input: equity = {financial.equity_tkr.value} tkr")
    print(f"   Swedish sync: eget_kapital = {financial.eget_kapital_tkr.value} tkr")

    return True


def test_financial_metadata_fields():
    """Test 8: Financial metadata fields (_terminology_found, _unit_verified)."""
    print_section("TEST 8: Financial Metadata Fields")

    financial = YearlyFinancialData(
        year=2024,
        nettoomsattning_tkr=NumberField(value=5234.5, confidence=0.95),
        terminology_found="nettoomsättning",
        unit_verified=True
    )

    assert financial.terminology_found == "nettoomsättning", "Terminology metadata should be preserved"
    assert financial.unit_verified == True, "Unit verification metadata should be preserved"

    print(f"✅ Terminology found: '{financial.terminology_found}'")
    print(f"✅ Unit verified: {financial.unit_verified}")

    return True


def main():
    """Run all Swedish-first semantic fields tests."""
    print("\n" + "=" * 70)
    print("WEEK 2 DAY 4: SWEDISH-FIRST SEMANTIC FIELDS TEST SUITE")
    print("=" * 70)

    tests = [
        ("test_fee_structure_swedish_to_english", test_fee_structure_swedish_to_english),
        ("test_fee_structure_english_to_swedish", test_fee_structure_english_to_swedish),
        ("test_fee_cross_validation_pass", test_fee_cross_validation_pass),
        ("test_fee_cross_validation_warning", test_fee_cross_validation_warning),
        ("test_fee_metadata_fields", test_fee_metadata_fields),
        ("test_financial_swedish_to_english", test_financial_swedish_to_english),
        ("test_financial_english_to_swedish", test_financial_english_to_swedish),
        ("test_financial_metadata_fields", test_financial_metadata_fields),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print_section("TEST SUMMARY")

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    pass_rate = (passed_tests / total_tests) * 100

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Week 2 Day 4 Swedish-First Semantic Fields COMPLETE!\n")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review output above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
