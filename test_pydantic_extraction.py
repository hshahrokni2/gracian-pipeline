#!/usr/bin/env python3
"""
Test ultra-comprehensive Pydantic extraction on sample document.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

load_dotenv()


def test_pydantic_extraction():
    """Test Pydantic extraction on test document."""

    # Test document
    pdf_path = "SRS/brf_198532.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ Test document not found: {pdf_path}")
        return False

    print("="*80)
    print("🧪 Ultra-Comprehensive Pydantic Extraction Test")
    print("="*80)

    try:
        # Run extraction
        report = extract_brf_to_pydantic(pdf_path, mode="deep")

        # Save JSON output
        output_path = "pydantic_extraction_test.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✅ Extraction Complete - Saved to {output_path}")

        # Display summary
        print("\n" + "="*80)
        print("📊 EXTRACTION SUMMARY")
        print("="*80)

        print(f"\n📋 Document Metadata:")
        print(f"   BRF Name: {report.metadata.brf_name}")
        print(f"   Org Number: {report.metadata.organization_number}")
        print(f"   Fiscal Year: {report.metadata.fiscal_year}")
        print(f"   Pages: {report.metadata.pages_total}")
        print(f"   Machine Readable: {report.metadata.is_machine_readable}")

        print(f"\n👥 Governance:")
        if report.governance:
            print(f"   Chairman: {report.governance.chairman}")
            print(f"   Board Members: {len(report.governance.board_members)}")
            if report.governance.primary_auditor:
                print(f"   Auditor: {report.governance.primary_auditor.name}")
                if report.governance.primary_auditor.firm:
                    print(f"   Audit Firm: {report.governance.primary_auditor.firm}")
        else:
            print("   ❌ No governance data extracted")

        print(f"\n💰 Financial:")
        if report.financial and report.financial.income_statement:
            is_stmt = report.financial.income_statement
            print(f"   Revenue: {is_stmt.revenue_total:,.0f} SEK" if is_stmt.revenue_total else "   Revenue: N/A")
            print(f"   Expenses: {is_stmt.expenses_total:,.0f} SEK" if is_stmt.expenses_total else "   Expenses: N/A")
            print(f"   Result: {is_stmt.result_after_tax:,.0f} SEK" if is_stmt.result_after_tax else "   Result: N/A")

        if report.financial and report.financial.balance_sheet:
            bs = report.financial.balance_sheet
            print(f"   Assets: {bs.assets_total:,.0f} SEK" if bs.assets_total else "   Assets: N/A")
            print(f"   Liabilities: {bs.liabilities_total:,.0f} SEK" if bs.liabilities_total else "   Liabilities: N/A")
            print(f"   Equity: {bs.equity_total:,.0f} SEK" if bs.equity_total else "   Equity: N/A")

        print(f"\n📝 Notes:")
        if report.notes:
            if report.notes.note_8_buildings:
                print(f"   ✅ Note 8 (Building Details) - Extracted")
            if report.notes.note_9_receivables:
                print(f"   ✅ Note 9 (Receivables) - Extracted")
        else:
            print("   ❌ No notes extracted")

        print(f"\n🏠 Property:")
        if report.property:
            print(f"   Designation: {report.property.property_designation or 'N/A'}")
            print(f"   Municipality: {report.property.municipality or 'N/A'}")
            if report.property.apartment_distribution:
                apt_dist = report.property.apartment_distribution
                print(f"   Total Apartments: {apt_dist.total_apartments}")
                print(f"     1 room: {apt_dist.one_room}")
                print(f"     2 rooms: {apt_dist.two_rooms}")
                print(f"     3 rooms: {apt_dist.three_rooms}")
                print(f"     4 rooms: {apt_dist.four_rooms}")
                print(f"     5 rooms: {apt_dist.five_rooms}")
            print(f"   Commercial Tenants: {len(report.property.commercial_tenants)}")
            print(f"   Common Areas: {len(report.property.common_areas)}")
        else:
            print("   ❌ No property data extracted")

        print(f"\n💵 Fees:")
        if report.fees:
            print(f"   Annual Fee/sqm: {report.fees.annual_fee_per_sqm} SEK" if report.fees.annual_fee_per_sqm else "   Annual Fee/sqm: N/A")
        else:
            print("   ❌ No fee data extracted")

        print(f"\n🏦 Loans:")
        print(f"   Total Loans: {len(report.loans)}")

        print(f"\n🔧 Operations:")
        if report.operations:
            print(f"   Suppliers: {len(report.operations.suppliers)}")
            print(f"   Planned Maintenance Items: {len(report.operations.planned_maintenance)}")
        else:
            print("   ❌ No operations data extracted")

        print(f"\n📅 Events:")
        print(f"   Total Events: {len(report.events)}")

        print(f"\n📜 Policies:")
        print(f"   Total Policies: {len(report.policies)}")

        print(f"\n✅ Quality Metrics:")
        print(f"   Coverage: {report.coverage_percentage:.1f}%")
        print(f"   Confidence: {report.confidence_score:.2f}")
        print(f"   Source Pages: {len(report.all_source_pages)}")

        # Detailed field count
        total_fields = sum([
            1 if report.governance else 0,
            1 if report.financial else 0,
            1 if report.notes else 0,
            1 if report.property else 0,
            1 if report.fees else 0,
            len(report.loans),
            1 if report.operations else 0,
            len(report.events),
            len(report.policies),
        ])

        print(f"\n📊 Populated Sections: {total_fields}")

        print("\n" + "="*80)
        print("✅ TEST COMPLETE")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pydantic_extraction()
    sys.exit(0 if success else 1)
