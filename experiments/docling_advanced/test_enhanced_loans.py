#!/usr/bin/env python3
"""Test enhanced comprehensive_notes_agent with 8-field loan schema"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
gracian_root = Path(__file__).resolve().parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}\n")

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent / "code"))

from optimal_brf_pipeline import OptimalBRFPipeline

def main():
    print("🧪 Testing enhanced comprehensive_notes_agent (8-field loans)...\n")

    # Initialize pipeline
    pipeline = OptimalBRFPipeline(enable_caching=False)  # Disable cache to force fresh extraction

    # Run extraction
    result = pipeline.extract_document("../../SRS/brf_198532.pdf")

    # Check comprehensive_notes_agent results
    if 'comprehensive_notes_agent' in result.pass2_result:
        agent_result = result.pass2_result['comprehensive_notes_agent']
        print(f"\n📊 Comprehensive Notes Agent Results:")
        print(f"   Status: {agent_result.get('status')}")
        print(f"   Evidence pages: {agent_result.get('evidence_pages', [])}")

        if agent_result.get('status') == 'success':
            data = agent_result.get('data', {})
            loans = data.get('loans', [])

            print(f"\n   Loans extracted: {len(loans)}/4 expected")

            if loans:
                print(f"\n   Enhanced Loan Details (8 fields per loan):")
                for i, loan in enumerate(loans, 1):
                    print(f"\n   Loan {i}:")
                    print(f"     Lender: {loan.get('lender')}")
                    print(f"     Amount: {loan.get('amount_2021'):,} kr")
                    print(f"     Interest rate: {loan.get('interest_rate')*100:.2f}%")
                    print(f"     Maturity date: {loan.get('maturity_date')}")
                    print(f"     Amortization free: {loan.get('amortization_free')}")

                    # NEW FIELDS (Sprint 1+2)
                    print(f"     🆕 Loan type: {loan.get('loan_type', 'NOT EXTRACTED')}")
                    print(f"     🆕 Collateral: {loan.get('collateral', 'NOT EXTRACTED')}")
                    print(f"     🆕 Credit limit: {loan.get('credit_facility_limit', 'NOT EXTRACTED')}")
                    print(f"     🆕 Outstanding: {loan.get('outstanding_amount', 'NOT EXTRACTED')}")

                # Count fields per loan
                if loans:
                    sample_loan = loans[0]
                    fields_extracted = sum(1 for v in sample_loan.values() if v is not None and v != 'NOT EXTRACTED')
                    print(f"\n   Fields per loan: {fields_extracted}/9 (8 data + evidence)")
            else:
                print("   ⚠️ No loans extracted")
        else:
            print(f"   Error: {agent_result.get('error', 'Unknown error')}")
    else:
        print("❌ comprehensive_notes_agent not found in results")

    pipeline.close()

    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
