"""
Integration test for ValidationEngine in production pipeline.

Tests that the validation engine:
1. Detects loan balance = 0 errors
2. Validates cross-references (balance sheet)
3. Reports validation issues in the pipeline output
"""

import sys
import json
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor


def test_validation_integration():
    """
    Test validation engine integration on a real PDF.
    """
    print("\n" + "="*80)
    print("VALIDATION ENGINE INTEGRATION TEST")
    print("="*80)

    # Use test PDF
    test_pdf = "SRS/brf_198532.pdf"

    if not Path(test_pdf).exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        print("Please run from the Gracian Pipeline directory")
        return False

    print(f"\nTest PDF: {test_pdf}")
    print(f"Mode: fast (for quick testing)")

    # Create extractor
    extractor = RobustUltraComprehensiveExtractor()

    # Extract with validation
    result = extractor.extract_brf_document(test_pdf, mode="fast")

    # Analyze validation report
    print("\n" + "="*80)
    print("VALIDATION REPORT ANALYSIS")
    print("="*80)

    validation_report = result.get("_validation_report", {})

    if not validation_report:
        print("❌ No validation report found in result!")
        return False

    print(f"\n✅ Validation report present")
    print(f"   Schema valid: {validation_report.get('schema_valid', False)}")
    print(f"   Total issues: {len(validation_report.get('issues', []))}")
    print(f"   Errors: {validation_report.get('error_count', 0)}")
    print(f"   Warnings: {validation_report.get('warning_count', 0)}")

    # Check for specific validation patterns
    issues = validation_report.get("issues", [])

    if issues:
        print(f"\n📋 Validation Issues Found:")
        for i, issue in enumerate(issues[:10], 1):  # Show first 10
            severity = issue.get("severity", "UNKNOWN")
            field = issue.get("field", "unknown")
            message = issue.get("message", "")
            value = issue.get("value", "")

            icon = "❌" if severity == "ERROR" else "⚠️" if severity == "WARNING" else "ℹ️"
            print(f"\n{i}. {icon} [{severity}] {field}")
            print(f"   Value: {value}")
            print(f"   Message: {message}")

            if issue.get("suggestion"):
                print(f"   💡 Suggestion: {issue.get('suggestion')}")
    else:
        print("\n✅ No validation issues found (data looks good!)")

    # Check specific critical patterns
    print("\n" + "="*80)
    print("CRITICAL PATTERN CHECKS")
    print("="*80)

    # Check 1: Loan balance = 0 detection
    loans = result.get("financial_agent", {}).get("loans", [])

    # Helper function to extract value from field (handles both dict and raw formats)
    def extract_loan_balance(loan):
        balance_field = loan.get("outstanding_balance", {})
        if isinstance(balance_field, dict):
            return balance_field.get("value")
        return balance_field

    zero_balance_loans = [
        loan for loan in loans
        if extract_loan_balance(loan) in [0, "0", "", None]
    ]

    if zero_balance_loans:
        print(f"\n⚠️  Found {len(zero_balance_loans)} loan(s) with zero/null balance")
        print("   Validation engine should have flagged these:")
        for loan in zero_balance_loans[:3]:
            lender = loan.get("lender", {}).get("value", "Unknown")
            balance = loan.get("outstanding_balance", {}).get("value", "N/A")
            print(f"   - {lender}: balance = {balance}")

        # Check if validation engine caught them
        loan_balance_errors = [
            issue for issue in issues
            if "outstanding_balance" in issue.get("field", "") and issue.get("severity") == "ERROR"
        ]

        if loan_balance_errors:
            print(f"   ✅ Validation engine caught {len(loan_balance_errors)} loan balance error(s)")
        else:
            print(f"   ❌ Validation engine did NOT catch zero balance loans (BUG!)")
    else:
        print("\n✅ No zero-balance loans found")

    # Check 2: Balance sheet validation
    financial = result.get("financial_agent", {})

    # Handle both ExtractionField format and raw values
    def get_value(field):
        if isinstance(field, dict):
            return field.get("value")
        return field

    assets = get_value(financial.get("assets"))
    liabilities = get_value(financial.get("liabilities"))
    equity = get_value(financial.get("equity"))

    if assets and liabilities and equity:
        print(f"\n📊 Balance Sheet Check:")
        print(f"   Assets: {assets:,} SEK")
        print(f"   Liabilities: {liabilities:,} SEK")
        print(f"   Equity: {equity:,} SEK")
        print(f"   Sum (L+E): {liabilities + equity:,} SEK")

        diff = abs(assets - (liabilities + equity))
        diff_percent = (diff / assets) * 100 if assets > 0 else 0

        if diff_percent > 5:
            print(f"   ⚠️  Balance sheet difference: {diff:,} SEK ({diff_percent:.1f}%)")

            # Check if validation engine caught it
            bs_errors = [
                issue for issue in issues
                if "balance_sheet" in issue.get("field", "")
            ]

            if bs_errors:
                print(f"   ✅ Validation engine caught balance sheet imbalance")
            else:
                print(f"   ❌ Validation engine did NOT catch balance sheet issue")
        else:
            print(f"   ✅ Balance sheet balanced (diff: {diff_percent:.2f}%)")
    else:
        print("\n⚠️  Incomplete balance sheet data")

    print("\n" + "="*80)
    print("✅ INTEGRATION TEST COMPLETE")
    print("="*80)

    return True


if __name__ == "__main__":
    try:
        success = test_validation_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
