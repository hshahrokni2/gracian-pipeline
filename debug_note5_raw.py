"""Debug Note 5 raw extraction to see what the LLM actually returns."""

import os
import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.hierarchical_financial import HierarchicalFinancialExtractor

def debug_note5():
    """Test Note 5 extraction and print raw results."""

    # Test PDF
    pdf_path = "SRS/brf_198532.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return

    print(f"🔍 Debugging Note 5 Extraction: {pdf_path}")
    print()

    # Create extractor
    extractor = HierarchicalFinancialExtractor()

    # Extract Note 5 with typical page range
    note_pages = [9, 10, 11]  # Typical Note 5 pages

    print(f"📄 Extracting from pages: {note_pages}")
    result = extractor.extract_note_5_loans_detailed(pdf_path, note_pages)

    print()
    print("=" * 80)
    print("RAW NOTE 5 EXTRACTION RESULT:")
    print("=" * 80)

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print()
    print("=" * 80)
    print("VALIDATION ANALYSIS:")
    print("=" * 80)

    validation = result.get("_validation", {})
    print(f"Loans extracted: {validation.get('loans_extracted', 0)}")
    print(f"Loans expected: {validation.get('loans_expected', 0)}")
    print(f"All loans present: {validation.get('all_loans_present', False)}")

    missing = validation.get("missing_loan_fields", [])
    if missing:
        print()
        print(f"⚠️  Missing fields ({len(missing)}):")
        for field in missing:
            print(f"   - {field}")

    print()
    print("=" * 80)
    print("LOAN DETAILS:")
    print("=" * 80)

    loans = result.get("loans", [])
    for i, loan in enumerate(loans, 1):
        print(f"\nLoan {i}:")
        for key, value in loan.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    debug_note5()
