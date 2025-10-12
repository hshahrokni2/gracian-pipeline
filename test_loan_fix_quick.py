"""Quick test to verify loan field name fix."""

import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_field_name_fix():
    """Test that loan extraction uses correct field name (amount_2021 not outstanding_balance)."""

    # Simulate what Note 5 extractor returns
    mock_base_result = {
        "financial_agent": {
            "loans": [
                {
                    "loan_number": "1",
                    "lender": "SEB",
                    "amount_2021": 30000000.0,  # NOTE: Key name is amount_2021
                    "amount_2020": 28000000.0,
                    "interest_rate": 0.015,
                    "maturity_date": "2030-12-31",
                    "amortization_free": True,
                    "notes": "Fixed rate"
                }
            ]
        }
    }

    print("🔍 Testing Loan Field Name Fix:")
    print()

    # Import after path setup
    from gracian_pipeline.core.pydantic_extractor import UltraComprehensivePydanticExtractor

    # Create extractor
    extractor = UltraComprehensivePydanticExtractor()

    # Call _extract_loans_enhanced with mock data
    loans = extractor._extract_loans_enhanced(mock_base_result)

    print("=" * 80)
    print("EXTRACTION RESULTS:")
    print("=" * 80)
    print(f"Loans extracted: {len(loans)}")
    print()

    if loans:
        loan = loans[0]
        lender_field = loan.lender
        balance_field = loan.outstanding_balance

        print(f"Loan 1:")
        print(f"   lender: {lender_field.value if lender_field else 'N/A'}")
        print(f"   outstanding_balance: {balance_field.value if balance_field else 'N/A'}")
        print(f"   outstanding_balance (raw): {balance_field}")
        print()

        # CRITICAL TEST: Does outstanding_balance have the value from amount_2021?
        if balance_field and balance_field.value == 30000000.0:
            print("=" * 80)
            print("✅ TEST PASSED: Field name fix works!")
            print("=" * 80)
            print(f"   Expected: 30000000.0")
            print(f"   Got:      {balance_field.value}")
            return True
        else:
            print("=" * 80)
            print("❌ TEST FAILED: Field name fix not working!")
            print("=" * 80)
            print(f"   Expected: 30000000.0")
            print(f"   Got:      {balance_field.value if balance_field else 'None'}")
            return False
    else:
        print("=" * 80)
        print("❌ TEST FAILED: No loans extracted!")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_field_name_fix()
    sys.exit(0 if success else 1)
