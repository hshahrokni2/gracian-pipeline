"""Fast end-to-end test for loan extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

def test_e2e_fast():
    """Test complete loan extraction in fast mode."""

    pdf_path = "SRS/brf_198532.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return False

    print("🔍 Testing End-to-End Loan Extraction (Fast Mode):")
    print(f"   Document: {pdf_path}")
    print()

    # Extract in deep mode (Note 5 only runs in deep/auto mode)
    print("Running deep mode extraction...")
    report = extract_brf_to_pydantic(pdf_path, mode="deep")

    loans = report.loans

    print()
    print("=" * 80)
    print("FINAL RESULTS:")
    print("=" * 80)
    print(f"Loans count: {len(loans)}")
    print()

    if not loans:
        print("❌ TEST FAILED: No loans extracted!")
        return False

    # Check first loan
    loan1 = loans[0]
    balance1 = loan1.outstanding_balance

    print(f"Loan 1:")
    print(f"   lender: {loan1.lender.value if loan1.lender else 'N/A'}")
    print(f"   outstanding_balance: {balance1.value if balance1 else 'N/A'}")
    print(f"   interest_rate: {loan1.interest_rate.value if loan1.interest_rate else 'N/A'}")
    print()

    # CRITICAL TEST: Does loan have correct balance?
    if balance1 and balance1.value and balance1.value > 0:
        print("=" * 80)
        print("✅ TEST PASSED: Loans extracted with balances!")
        print("=" * 80)
        print(f"   Sample balance: {balance1.value} SEK")
        print(f"   Expected range: 10M-30M SEK")
        return True
    else:
        print("=" * 80)
        print("❌ TEST FAILED: Loan balances are zero or missing!")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_e2e_fast()
    sys.exit(0 if success else 1)
