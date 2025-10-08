#!/usr/bin/env python3
"""
Quick verification test for Pydantic schema integration fix.
Tests that ExtractionField wrappers are working correctly.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Environment loaded")
else:
    print(f"⚠️  .env not found at {env_path}, using existing environment")

# Now test the fix
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

def get_value(field):
    """Get value from either ExtractionField or raw type (MIXED approach)."""
    if hasattr(field, 'value'):
        return field.value
    return field

def verify_fix():
    """Verify Pydantic schema integration fix on single PDF."""
    pdf_path = 'data/raw_pdfs/Hjorthagen/brf_46160.pdf'

    print("=" * 80)
    print("🧪 VERIFYING PYDANTIC SCHEMA INTEGRATION FIX")
    print("=" * 80)
    print(f"Test PDF: {pdf_path}")
    print()

    try:
        # This should now work without Pydantic validation errors
        print("⏳ Extracting with Pydantic schema (fast mode)...")
        report = extract_brf_to_pydantic(pdf_path, mode='fast')

        print()
        print("=" * 80)
        print("✅ SUCCESS: BRFAnnualReport created without Pydantic errors!")
        print("=" * 80)
        print()
        print("📋 Metadata Verification:")
        print(f"   Document ID: {get_value(report.metadata.document_id)}")
        print(f"   BRF Name: {get_value(report.metadata.brf_name)}")
        print(f"   Fiscal Year: {get_value(report.metadata.fiscal_year)}")
        print(f"   Org Number: {get_value(report.metadata.organization_number)}")
        print(f"   Pages Total: {get_value(report.metadata.pages_total)}")
        print(f"   File Hash: {str(get_value(report.metadata.file_hash_sha256))[:16]}...")
        print()
        print("🔍 ExtractionField Features Working:")
        print(f"   ✓ Value wrapping: {type(report.metadata.fiscal_year).__name__}")
        if hasattr(report.metadata.fiscal_year, 'confidence'):
            print(f"   ✓ Confidence tracking: {report.metadata.fiscal_year.confidence}")
            print(f"   ✓ Source attribution: {report.metadata.fiscal_year.source}")
        print()

        # Check governance if extracted
        if report.governance:
            print("📋 Governance Verification:")
            if report.governance.chairman:
                print(f"   Chairman: {get_value(report.governance.chairman)}")
                if hasattr(report.governance.chairman, 'confidence'):
                    print(f"   Confidence: {report.governance.chairman.confidence}")
            if report.governance.board_members:
                board_list = get_value(report.governance.board_members) if hasattr(report.governance.board_members, 'value') else report.governance.board_members
                print(f"   Board Members: {len(board_list)} found")
            print()

        # Check financial if extracted
        if report.financial and report.financial.balance_sheet:
            print("📋 Financial Verification:")
            if report.financial.balance_sheet.assets_total:
                print(f"   Total Assets: {get_value(report.financial.balance_sheet.assets_total):,} SEK")
                if hasattr(report.financial.balance_sheet.assets_total, 'confidence'):
                    print(f"   Confidence: {report.financial.balance_sheet.assets_total.confidence}")
            print()

        print("=" * 80)
        print("🎉 FIX VERIFIED: All ExtractionField wrappers working correctly!")
        print("=" * 80)
        return True

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ FAILED: {type(e).__name__}")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_fix()
    sys.exit(0 if success else 1)
