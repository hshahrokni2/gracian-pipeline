#!/usr/bin/env python3
"""
Test Mixed-Mode Extraction on brf_76536.pdf
============================================

Expected Results:
- Detect financial pages (9-12) as images
- Use vision extraction for those pages
- Coverage improves from 6.8% to 25-30% (+18-23pp)

This test validates the Option A solution for hybrid PDFs.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

PDF_PATH = "SRS/brf_76536.pdf"

print("=" * 80)
print("MIXED-MODE EXTRACTION TEST: brf_76536.pdf")
print("=" * 80)
print("\n🎯 Expected: Pages 9-12 extracted with vision API")
print("🎯 Target: Coverage 6.8% → 25-30% (+18-23pp improvement)\n")
print("=" * 80)

pdf_path = Path(__file__).parent / PDF_PATH

if not pdf_path.exists():
    print(f"\n❌ ERROR: PDF not found at {PDF_PATH}")
    sys.exit(1)

print(f"\n📄 Testing: {pdf_path.name}")

try:
    # Run extraction with mixed-mode support
    result = extract_brf_to_pydantic(str(pdf_path), mode="fast")

    # Display results
    print(f"\n\n{'=' * 80}")
    print("EXTRACTION RESULTS")
    print("=" * 80)

    print(f"\n📊 Overall Metrics:")
    print(f"   Coverage: {result.coverage_percentage:.1f}%")
    print(f"   Confidence: {result.confidence_score:.2f}")

    # Check what was extracted
    print(f"\n📋 Extracted Data:")

    # Metadata
    if result.metadata:
        print(f"\n   Metadata:")
        print(f"      Org number: {result.metadata.organization_number.value if result.metadata.organization_number else 'None'}")
        print(f"      BRF name: {result.metadata.brf_name.value if result.metadata.brf_name else 'None'}")
        print(f"      Fiscal year: {result.metadata.fiscal_year.value if result.metadata.fiscal_year else 'None'}")

    # Governance
    if result.governance:
        print(f"\n   Governance:")
        print(f"      Chairman: {result.governance.chairman.value if result.governance.chairman else 'None'}")
        print(f"      Board members: {len(result.governance.board_members) if result.governance.board_members else 0}")
        if result.governance.primary_auditor:
            print(f"      Auditor: {result.governance.primary_auditor.name.value}")
    else:
        print(f"\n   Governance: None ❌")

    # Financial
    if result.financial:
        financial = result.financial
        print(f"\n   Financial:")

        if financial.income_statement:
            income = financial.income_statement
            print(f"      Income Statement:")
            print(f"         Revenue: {income.revenue_total.value if income.revenue_total else 'None'}")
            print(f"         Expenses: {income.expenses_total.value if income.expenses_total else 'None'}")
            print(f"         Net Income: {income.result_after_tax.value if income.result_after_tax else 'None'}")

        if financial.balance_sheet:
            balance = financial.balance_sheet
            print(f"      Balance Sheet:")
            print(f"         Assets: {balance.assets_total.value if balance.assets_total else 'None'}")
            print(f"         Liabilities: {balance.liabilities_total.value if balance.liabilities_total else 'None'}")
            print(f"         Equity: {balance.equity_total.value if balance.equity_total else 'None'}")
    else:
        print(f"\n   Financial: None ❌")

    # Property
    if result.property:
        print(f"\n   Property:")
        print(f"      Municipality: {result.property.municipality.value if result.property.municipality else 'None'}")
        print(f"      Address: {result.property.property_designation.value if result.property.property_designation else 'None'}")
    else:
        print(f"\n   Property: None")

    # Fees
    if result.fees:
        print(f"\n   Fees:")
        print(f"      Annual fee/sqm: {result.fees.annual_fee_per_sqm.value if result.fees.annual_fee_per_sqm else 'None'}")
    else:
        print(f"\n   Fees: None")

    # Loans
    if result.loans:
        print(f"\n   Loans: {len(result.loans)} loan(s)")
        for i, loan in enumerate(result.loans, 1):
            print(f"      Loan {i}: {loan.lender.value} - {loan.outstanding_balance.value if loan.outstanding_balance else 'N/A'}")
    else:
        print(f"\n   Loans: None")

    # Analysis
    print(f"\n\n{'=' * 80}")
    print("ANALYSIS")
    print("=" * 80)

    # Check if mixed-mode was used
    if hasattr(result, '_extraction_metadata') and result._extraction_metadata:
        metadata = result._extraction_metadata
        if metadata.get('mode') == 'mixed':
            print(f"\n✅ Mixed-mode extraction USED")
            print(f"   Vision pages: {metadata.get('vision_pages', [])}")
            print(f"   Text extraction: {metadata.get('text_extraction', 'unknown')}")
            print(f"   Vision extraction: {metadata.get('vision_extraction', 'unknown')}")
        else:
            print(f"\n⚠️  Mixed-mode NOT used (mode: {metadata.get('mode', 'unknown')})")
    else:
        print(f"\n⚠️  No extraction metadata available")

    # Compare with baseline
    baseline_coverage = 6.8
    improvement = result.coverage_percentage - baseline_coverage

    print(f"\n📊 Coverage Comparison:")
    print(f"   Baseline: {baseline_coverage}%")
    print(f"   New: {result.coverage_percentage:.1f}%")
    print(f"   Improvement: {improvement:+.1f}pp")

    if improvement >= 18:
        print(f"\n🎉 SUCCESS: Improvement ≥18pp (target achieved!)")
    elif improvement >= 10:
        print(f"\n✅ GOOD: Improvement ≥10pp (significant progress)")
    elif improvement >= 5:
        print(f"\n⚠️  PARTIAL: Improvement 5-10pp (some progress)")
    else:
        print(f"\n❌ FAILED: Improvement <5pp (mixed-mode may not be working)")

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ EXTRACTION FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
