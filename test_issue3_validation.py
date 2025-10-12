#!/usr/bin/env python3
"""
Issue #3 Validation Test - Board Members with Suppleant Role
Tests the updated prompt and parsing logic with debug logging.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.integrated_brf_pipeline import process_single_pdf

def test_board_members_extraction():
    """Test board member extraction with debug logging."""

    # Test on brf_198532.pdf (the one with ground truth)
    pdf_path = project_root / "data" / "test_pdfs" / "brf_198532.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    print("🔍 Testing Board Members Extraction (Issue #3)")
    print("=" * 60)
    print(f"📄 PDF: {pdf_path.name}")
    print(f"🎯 Expected: 7 members (1 Ordförande + 4 Ledamot + 2 Suppleant)")
    print()

    # Run extraction in fast mode
    try:
        result = process_single_pdf(
            pdf_path=str(pdf_path),
            mode="fast",
            cache_dir=project_root / ".cache_test_issue3"  # Use separate cache
        )

        if not result or not result.governance:
            print("❌ No governance data extracted")
            return

        gov = result.governance

        # Display results
        print(f"✅ Board Members Extracted: {len(gov.board_members)} members")
        print()

        if len(gov.board_members) == 0:
            print("⚠️  WARNING: 0 members extracted!")
            print("   This suggests LLM didn't return board_members data")
            return

        # Show each member with role
        role_counts = {"ordforande": 0, "ledamot": 0, "suppleant": 0, "revisor": 0}

        for i, member in enumerate(gov.board_members, 1):
            name = member.full_name.value if member.full_name else "Unknown"
            role = member.role
            role_counts[role] = role_counts.get(role, 0) + 1

            # Translate role for display
            role_display = {
                "ordforande": "Ordförande (Chairman)",
                "ledamot": "Ledamot (Member)",
                "suppleant": "Suppleant (Deputy)",
                "revisor": "Revisor (Auditor)"
            }.get(role, role)

            print(f"  {i}. {name}")
            print(f"     Role: {role_display}")
            print()

        # Summary
        print("📊 Role Distribution:")
        print(f"   Ordförande: {role_counts['ordforande']}")
        print(f"   Ledamot: {role_counts['ledamot']}")
        print(f"   Suppleant: {role_counts['suppleant']}")
        print(f"   Revisor: {role_counts['revisor']}")
        print()

        # Validation
        if len(gov.board_members) == 7 and role_counts['suppleant'] == 2:
            print("✅ SUCCESS: All 7 members extracted with 2 Suppleants!")
        elif role_counts['suppleant'] == 0:
            print("❌ FAIL: No Suppleant roles extracted (Issue #3 not fixed)")
        elif len(gov.board_members) != 7:
            print(f"⚠️  PARTIAL: Expected 7 members, got {len(gov.board_members)}")
        else:
            print(f"⚠️  PARTIAL: Expected 2 Suppleants, got {role_counts['suppleant']}")

    except Exception as e:
        print(f"❌ Extraction FAILED: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_board_members_extraction()
