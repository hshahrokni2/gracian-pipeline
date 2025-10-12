"""Test complete loan data flow from Note 5 → Pydantic."""

import os
import sys
import json
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor
from gracian_pipeline.core.pydantic_extractor import UltraComprehensivePydanticExtractor

def test_loan_integration():
    """Test loan extraction end-to-end."""

    pdf_path = "SRS/brf_198532.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return

    print("🔍 Testing Loan Integration:")
    print(f"   Document: {pdf_path}")
    print()

    # Step 1: Base extraction
    print("Step 1: Base extraction (RobustUltraComprehensiveExtractor)...")
    extractor = RobustUltraComprehensiveExtractor()
    base_result = extractor.extract_brf_document(pdf_path, mode="deep")

    # Check base extraction has loans
    print()
    print("=" * 80)
    print("BASE EXTRACTION - Financial Agent Loans:")
    print("=" * 80)

    fin_data = base_result.get("financial_agent", {})
    loans_in_base = fin_data.get("loans", [])

    print(f"Loans count: {len(loans_in_base)}")
    print()

    for i, loan in enumerate(loans_in_base[:2], 1):  # Show first 2
        print(f"Loan {i}:")
        print(f"   lender: {loan.get('lender', 'N/A')}")
        print(f"   amount_2021: {loan.get('amount_2021', 'N/A')}")
        print(f"   interest_rate: {loan.get('interest_rate', 'N/A')}")
        print()

    # Step 2: Pydantic extraction
    print("=" * 80)
    print("Step 2: Pydantic extraction...")
    print("=" * 80)

    pydantic_extractor = UltraComprehensivePydanticExtractor()

    # DIRECT TEST: Call _extract_loans_enhanced with base_result
    loans_pydantic = pydantic_extractor._extract_loans_enhanced(base_result)

    print(f"Pydantic loans count: {len(loans_pydantic)}")
    print()

    for i, loan in enumerate(loans_pydantic[:2], 1):  # Show first 2
        lender_field = loan.lender
        balance_field = loan.outstanding_balance
        rate_field = loan.interest_rate

        print(f"Loan {i}:")
        print(f"   lender: {lender_field.value if lender_field else 'N/A'}")
        print(f"   outstanding_balance: {balance_field.value if balance_field else 'N/A'}")
        print(f"   interest_rate: {rate_field.value if rate_field else 'N/A'}")
        print()

    # Step 3: Full integration test
    print("=" * 80)
    print("Step 3: Full Pydantic model creation...")
    print("=" * 80)

    report = pydantic_extractor.extract_brf_comprehensive(pdf_path, mode="fast")

    loans_final = report.loans
    print(f"Final loans count: {len(loans_final)}")
    print()

    for i, loan in enumerate(loans_final[:2], 1):
        lender_field = loan.lender
        balance_field = loan.outstanding_balance
        rate_field = loan.interest_rate

        print(f"Loan {i}:")
        print(f"   lender: {lender_field.value if lender_field else 'N/A'}")
        print(f"   outstanding_balance: {balance_field.value if balance_field else 'N/A'} (EXPECTED: 30M, 25M...)")
        print(f"   interest_rate: {rate_field.value if rate_field else 'N/A'}")
        print()

    print("=" * 80)
    print("✅ Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_loan_integration()
