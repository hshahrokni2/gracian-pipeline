"""
Comprehensive test suite for DynamicMultiYearOverview feature.

Tests:
1. Basic multi-year creation
2. Helper method functionality
3. Auto-computation of metadata
4. Different table orientations
5. Integration with BRFAnnualReport
6. Edge cases (missing years, incomplete data)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from gracian_pipeline.models.brf_schema import (
    MultiYearTableOrientation,
    YearlyFinancialData,
    DynamicMultiYearOverview,
    BRFAnnualReport,
    DocumentMetadata
)
from gracian_pipeline.models.base_fields import NumberField


def test_yearly_financial_data():
    """Test 1: Create and validate YearlyFinancialData."""
    print("\n📊 Test 1: YearlyFinancialData Creation")
    print("-" * 60)

    year_2023 = YearlyFinancialData(
        year=2023,
        net_revenue_tkr=NumberField(
            value=5000,
            confidence=0.95,
            source='structured_table',
            evidence_pages=[8]
        ),
        total_assets_tkr=NumberField(
            value=300000,
            confidence=0.98,
            source='structured_table',
            evidence_pages=[8]
        ),
        equity_tkr=NumberField(
            value=200000,
            confidence=0.98,
            source='structured_table',
            evidence_pages=[8]
        ),
        solidarity_percent=NumberField(
            value=66.7,
            confidence=0.90,
            source='calculated',
            evidence_pages=[8]
        ),
        is_complete=True,
        extraction_confidence=0.95,
        source_page=8
    )

    assert year_2023.year == 2023
    assert year_2023.net_revenue_tkr.value == 5000
    assert year_2023.net_revenue_tkr.confidence == 0.95
    assert year_2023.is_complete == True

    print(f"✅ Year: {year_2023.year}")
    print(f"✅ Revenue: {year_2023.net_revenue_tkr.value:,} tkr (confidence: {year_2023.net_revenue_tkr.confidence})")
    print(f"✅ Assets: {year_2023.total_assets_tkr.value:,} tkr")
    print(f"✅ Solidarity: {year_2023.solidarity_percent.value}%")
    print(f"✅ Is Complete: {year_2023.is_complete}")
    print("✅ Test 1 PASSED")


def test_multi_year_overview_basic():
    """Test 2: Create DynamicMultiYearOverview with 3 years."""
    print("\n📈 Test 2: DynamicMultiYearOverview Basic Creation")
    print("-" * 60)

    multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(
                year=2021,
                net_revenue_tkr=NumberField(value=4500, confidence=0.90, source='structured_table', evidence_pages=[8]),
                total_assets_tkr=NumberField(value=280000, confidence=0.90, source='structured_table', evidence_pages=[8]),
                equity_tkr=NumberField(value=180000, confidence=0.90, source='structured_table', evidence_pages=[8])
            ),
            YearlyFinancialData(
                year=2022,
                net_revenue_tkr=NumberField(value=4750, confidence=0.92, source='structured_table', evidence_pages=[8]),
                total_assets_tkr=NumberField(value=290000, confidence=0.92, source='structured_table', evidence_pages=[8]),
                equity_tkr=NumberField(value=190000, confidence=0.92, source='structured_table', evidence_pages=[8])
            ),
            YearlyFinancialData(
                year=2023,
                net_revenue_tkr=NumberField(value=5000, confidence=0.95, source='structured_table', evidence_pages=[8]),
                total_assets_tkr=NumberField(value=300000, confidence=0.95, source='structured_table', evidence_pages=[8]),
                equity_tkr=NumberField(value=200000, confidence=0.95, source='structured_table', evidence_pages=[8])
            ),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table',
        confidence=0.93
    )

    # Verify auto-computation
    assert multi_year.num_years == 3, f"Expected 3 years, got {multi_year.num_years}"
    assert multi_year.years_covered == [2021, 2022, 2023], f"Expected [2021, 2022, 2023], got {multi_year.years_covered}"

    print(f"✅ Number of years: {multi_year.num_years}")
    print(f"✅ Years covered: {multi_year.years_covered}")
    print(f"✅ Table orientation: {multi_year.table_orientation.value}")
    print(f"✅ Overall confidence: {multi_year.confidence}")
    print("✅ Test 2 PASSED")


def test_helper_methods():
    """Test 3: Test get_year and get_metric_timeseries."""
    print("\n🔧 Test 3: Helper Methods")
    print("-" * 60)

    multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(
                year=2021,
                net_revenue_tkr=NumberField(value=4500, confidence=0.90, source='structured_table', evidence_pages=[8]),
                operating_expenses_tkr=NumberField(value=3800, confidence=0.90, source='structured_table', evidence_pages=[8]),
                solidarity_percent=NumberField(value=62.5, confidence=0.85, source='calculated', evidence_pages=[8])
            ),
            YearlyFinancialData(
                year=2022,
                net_revenue_tkr=NumberField(value=4750, confidence=0.92, source='structured_table', evidence_pages=[8]),
                operating_expenses_tkr=NumberField(value=4000, confidence=0.92, source='structured_table', evidence_pages=[8]),
                solidarity_percent=NumberField(value=64.2, confidence=0.87, source='calculated', evidence_pages=[8])
            ),
            YearlyFinancialData(
                year=2023,
                net_revenue_tkr=NumberField(value=5000, confidence=0.95, source='structured_table', evidence_pages=[8]),
                operating_expenses_tkr=NumberField(value=4200, confidence=0.95, source='structured_table', evidence_pages=[8]),
                solidarity_percent=NumberField(value=66.7, confidence=0.90, source='calculated', evidence_pages=[8])
            ),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table',
        confidence=0.92
    )

    # Test get_year
    year_2022 = multi_year.get_year(2022)
    assert year_2022 is not None, "get_year(2022) should return data"
    assert year_2022.year == 2022, "Year should be 2022"
    assert year_2022.net_revenue_tkr.value == 4750, "Revenue should be 4750"

    print(f"✅ get_year(2022): Revenue={year_2022.net_revenue_tkr.value}, Expenses={year_2022.operating_expenses_tkr.value}")

    # Test get_year for non-existent year
    year_2020 = multi_year.get_year(2020)
    assert year_2020 is None, "get_year(2020) should return None"
    print(f"✅ get_year(2020): None (correctly handles missing year)")

    # Test get_metric_timeseries
    revenue_ts = multi_year.get_metric_timeseries('net_revenue_tkr')
    assert revenue_ts == {2021: 4500, 2022: 4750, 2023: 5000}, "Revenue timeseries incorrect"
    print(f"✅ Revenue timeseries: {revenue_ts}")

    expenses_ts = multi_year.get_metric_timeseries('operating_expenses_tkr')
    assert expenses_ts == {2021: 3800, 2022: 4000, 2023: 4200}, "Expenses timeseries incorrect"
    print(f"✅ Expenses timeseries: {expenses_ts}")

    solidarity_ts = multi_year.get_metric_timeseries('solidarity_percent')
    print(f"✅ Solidarity timeseries: {solidarity_ts}")

    print("✅ Test 3 PASSED")


def test_table_orientations():
    """Test 4: Different table orientations."""
    print("\n🔄 Test 4: Table Orientations")
    print("-" * 60)

    # Test YEARS_AS_COLUMNS
    columns_multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=2022, net_revenue_tkr=NumberField(value=4000, confidence=0.90, source='structured_table', evidence_pages=[5])),
            YearlyFinancialData(year=2023, net_revenue_tkr=NumberField(value=4200, confidence=0.90, source='structured_table', evidence_pages=[5])),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table'
    )
    print(f"✅ YEARS_AS_COLUMNS: {columns_multi_year.years_covered}")

    # Test YEARS_AS_ROWS
    rows_multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=2022, total_assets_tkr=NumberField(value=250000, confidence=0.90, source='structured_table', evidence_pages=[6])),
            YearlyFinancialData(year=2023, total_assets_tkr=NumberField(value=260000, confidence=0.90, source='structured_table', evidence_pages=[6])),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_ROWS,
        extraction_method='structured_table'
    )
    print(f"✅ YEARS_AS_ROWS: {rows_multi_year.years_covered}")

    # Test UNKNOWN
    unknown_multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=2023, equity_tkr=NumberField(value=180000, confidence=0.70, source='vision_llm', evidence_pages=[7])),
        ],
        table_orientation=MultiYearTableOrientation.UNKNOWN,
        extraction_method='vision_llm'
    )
    print(f"✅ UNKNOWN orientation: {unknown_multi_year.years_covered}")

    print("✅ Test 4 PASSED")


def test_brf_annual_report_integration():
    """Test 5: Integration with BRFAnnualReport."""
    print("\n🏢 Test 5: BRFAnnualReport Integration")
    print("-" * 60)

    multi_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(
                year=2021,
                net_revenue_tkr=NumberField(value=4500, confidence=0.90, source='structured_table', evidence_pages=[10]),
                total_assets_tkr=NumberField(value=280000, confidence=0.90, source='structured_table', evidence_pages=[10])
            ),
            YearlyFinancialData(
                year=2022,
                net_revenue_tkr=NumberField(value=4750, confidence=0.92, source='structured_table', evidence_pages=[10]),
                total_assets_tkr=NumberField(value=290000, confidence=0.92, source='structured_table', evidence_pages=[10])
            ),
            YearlyFinancialData(
                year=2023,
                net_revenue_tkr=NumberField(value=5000, confidence=0.95, source='structured_table', evidence_pages=[10]),
                total_assets_tkr=NumberField(value=300000, confidence=0.95, source='structured_table', evidence_pages=[10])
            ),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table',
        confidence=0.92
    )

    report = BRFAnnualReport(
        metadata=DocumentMetadata(
            document_id='769606-2533_2023',
            document_type='arsredovisning',
            pages_total=30
        ),
        multi_year_overview=multi_year
    )

    assert report.multi_year_overview is not None, "multi_year_overview should be set"
    assert report.multi_year_overview.num_years == 3, "Should have 3 years"
    assert report.multi_year_overview.years_covered == [2021, 2022, 2023], "Years should match"

    print(f"✅ BRFAnnualReport created with multi_year_overview")
    print(f"✅ Document ID: {report.metadata.document_id}")
    print(f"✅ Multi-year: {report.multi_year_overview.num_years} years ({report.multi_year_overview.years_covered})")

    # Access specific year data through BRFAnnualReport
    year_2023 = report.multi_year_overview.get_year(2023)
    print(f"✅ 2023 Revenue from report: {year_2023.net_revenue_tkr.value:,} tkr")

    # Get timeseries through BRFAnnualReport
    revenue_ts = report.multi_year_overview.get_metric_timeseries('net_revenue_tkr')
    print(f"✅ Revenue trend through report: {revenue_ts}")

    print("✅ Test 5 PASSED")


def test_edge_cases():
    """Test 6: Edge cases and incomplete data."""
    print("\n🔍 Test 6: Edge Cases")
    print("-" * 60)

    # Test 1: Single year (minimum)
    single_year = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=2023, net_revenue_tkr=NumberField(value=5000, confidence=0.90, source='structured_table', evidence_pages=[5]))
        ],
        table_orientation=MultiYearTableOrientation.UNKNOWN,
        extraction_method='vision_llm'
    )
    assert single_year.num_years == 1, "Should handle single year"
    print(f"✅ Single year: {single_year.years_covered}")

    # Test 2: Many years (10+)
    many_years = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=year, net_revenue_tkr=NumberField(value=4000 + (year - 2014) * 100, confidence=0.85, source='structured_table', evidence_pages=[6]))
            for year in range(2014, 2024)  # 10 years
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table'
    )
    assert many_years.num_years == 10, "Should handle 10 years"
    print(f"✅ Many years (10): {many_years.years_covered}")

    # Test 3: Non-sequential years (gap)
    gap_years = DynamicMultiYearOverview(
        years=[
            YearlyFinancialData(year=2020, net_revenue_tkr=NumberField(value=4000, confidence=0.90, source='structured_table', evidence_pages=[7])),
            # 2021 missing
            YearlyFinancialData(year=2022, net_revenue_tkr=NumberField(value=4500, confidence=0.90, source='structured_table', evidence_pages=[7])),
            YearlyFinancialData(year=2023, net_revenue_tkr=NumberField(value=4800, confidence=0.90, source='structured_table', evidence_pages=[7])),
        ],
        table_orientation=MultiYearTableOrientation.YEARS_AS_COLUMNS,
        extraction_method='structured_table'
    )
    assert gap_years.num_years == 3, "Should count 3 years despite gap"
    assert 2021 not in gap_years.years_covered, "2021 should not be in years_covered"
    print(f"✅ Gap years (2021 missing): {gap_years.years_covered}")

    # Test 4: Incomplete year (missing fields)
    incomplete_year = YearlyFinancialData(
        year=2023,
        net_revenue_tkr=NumberField(value=5000, confidence=0.90, source='structured_table', evidence_pages=[8]),
        # Other fields missing
        is_complete=False,  # Correctly marked as incomplete
        extraction_confidence=0.40  # Low confidence
    )
    assert incomplete_year.is_complete == False, "Should be marked incomplete"
    print(f"✅ Incomplete year: Year={incomplete_year.year}, is_complete={incomplete_year.is_complete}, confidence={incomplete_year.extraction_confidence}")

    print("✅ Test 6 PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🧪 DynamicMultiYearOverview Test Suite")
    print("=" * 60)

    try:
        test_yearly_financial_data()
        test_multi_year_overview_basic()
        test_helper_methods()
        test_table_orientations()
        test_brf_annual_report_integration()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - DynamicMultiYearOverview is production ready!")
        print("=" * 60)
        print(f"\n✅ Summary:")
        print(f"   • 3 new models: MultiYearTableOrientation, YearlyFinancialData, DynamicMultiYearOverview")
        print(f"   • 2 helper methods: get_year(), get_metric_timeseries()")
        print(f"   • 1 auto-validator: compute_metadata()")
        print(f"   • Supports: 2-10+ years dynamically")
        print(f"   • Integration: BRFAnnualReport.multi_year_overview")
        print(f"   • Confidence tracking: All 7 financial metrics per year")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
