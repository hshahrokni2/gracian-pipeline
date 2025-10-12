#!/usr/bin/env python3
"""Direct test of enhanced comprehensive_notes_agent (skip full pipeline)"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
gracian_root = Path(__file__).resolve().parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent / "code"))

from base_brf_extractor import BaseExtractor

def main():
    print("🧪 Direct Test: Enhanced comprehensive_notes_agent (8-field loans)\n")

    # Initialize extractor
    extractor = BaseExtractor()

    # Test on Noter pages directly (pages 11-16, 0-indexed: 10-15)
    pdf_path = "../../SRS/brf_198532.pdf"

    # Noter section headings (simplified)
    section_headings = ["Noter", "Not 11 Skulder till kreditinstitut"]

    print("Extracting from Noter section (pages 11-16)...")
    print("Expected: 4 loans with 8 fields each\n")

    # Call extraction directly
    result = extractor._extract_agent(
        pdf_path=pdf_path,
        agent_id="comprehensive_notes_agent",
        section_headings=section_headings,
        context=None
    )

    # Display results
    print(f"Status: {result.get('status')}")
    print(f"Extraction time: {result.get('extraction_time', 0):.1f}s")
    print(f"Evidence pages: {result.get('evidence_pages', [])}")

    if result.get('status') == 'success':
        data = result.get('data', {})
        loans = data.get('loans', [])

        print(f"\nLoans extracted: {len(loans)}/4")

        if loans:
            for i, loan in enumerate(loans, 1):
                print(f"\n🔹 Loan {i}:")
                print(f"   Lender: {loan.get('lender', 'MISSING')}")
                print(f"   Amount: {loan.get('amount_2021', 0):,}")
                print(f"   Interest: {loan.get('interest_rate', 0)*100:.2f}%")
                print(f"   Maturity: {loan.get('maturity_date', 'MISSING')}")

                # Check NEW fields
                new_fields_status = []
                if 'loan_type' in loan and loan['loan_type']:
                    print(f"   ✅ Loan type: {loan['loan_type']}")
                    new_fields_status.append(True)
                else:
                    print(f"   ❌ Loan type: MISSING")
                    new_fields_status.append(False)

                if 'collateral' in loan and loan['collateral']:
                    print(f"   ✅ Collateral: {loan['collateral']}")
                    new_fields_status.append(True)
                else:
                    print(f"   ❌ Collateral: MISSING")
                    new_fields_status.append(False)

                if 'credit_facility_limit' in loan and loan['credit_facility_limit']:
                    print(f"   ✅ Credit limit: {loan['credit_facility_limit']:,}")
                    new_fields_status.append(True)
                else:
                    print(f"   ❌ Credit limit: MISSING")
                    new_fields_status.append(False)

                if 'outstanding_amount' in loan and loan['outstanding_amount']:
                    print(f"   ✅ Outstanding: {loan['outstanding_amount']:,}")
                    new_fields_status.append(True)
                else:
                    print(f"   ❌ Outstanding: MISSING")
                    new_fields_status.append(False)

            # Summary
            if loans:
                sample_loan = loans[0]
                new_fields_extracted = sum(1 for f in ['loan_type', 'collateral', 'credit_facility_limit', 'outstanding_amount'] if f in sample_loan and sample_loan[f])
                print(f"\n📊 Summary: {new_fields_extracted}/4 new fields extracted per loan")

                if new_fields_extracted == 4:
                    print("✅ SUCCESS: All 4 new fields extracted!")
                elif new_fields_extracted > 0:
                    print(f"⚠️ PARTIAL: {new_fields_extracted}/4 new fields extracted")
                else:
                    print("❌ FAILED: No new fields extracted (using old 5-field schema)")
        else:
            print("❌ No loans extracted")
    else:
        print(f"\n❌ Extraction failed: {result.get('error', 'Unknown error')}")

    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
