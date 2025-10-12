#!/usr/bin/env python3
"""
Quick test of multi-agent governance architecture on brf_81563 PDF.
This PDF had the regression: 4 board members → 0 members with comprehensive prompt.
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

def test_brf_81563():
    """Test the critical regression case with multi-agent architecture."""

    pdf_path = Path("Hjorthagen/brf_81563.pdf")

    print("=" * 80)
    print("🧪 Testing Multi-Agent Governance Architecture")
    print("=" * 80)
    print(f"\n📄 PDF: {pdf_path}")
    print(f"🎯 Expected: Board members should be extracted (4+ members)")
    print(f"❌ Before Fix: 0 members (LLM cognitive overload)")
    print(f"✅ After Fix: Using 3 specialized agents\n")

    print("🚀 Running extraction...")
    result = extract_brf_to_pydantic(str(pdf_path), mode="fast")

    # Extract governance data
    governance = result.governance if hasattr(result, 'governance') else None

    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)

    if governance:
        chairman = governance.chairman.value if governance.chairman else None
        board_members = governance.board_members if governance.board_members else []
        auditor = governance.primary_auditor.name.value if governance.primary_auditor else None

        print(f"✅ Governance data extracted: YES")
        print(f"   Chairman: {chairman}")
        print(f"   Board members: {len(board_members)} found")

        if board_members:
            print("\n   📋 Board Member Details:")
            for i, member in enumerate(board_members, 1):
                name = member.full_name.value if hasattr(member.full_name, 'value') else member.full_name
                role = member.role if hasattr(member, 'role') else "unknown"
                print(f"      {i}. {name} ({role})")

        print(f"\n   Auditor: {auditor}")

        # Success criteria
        if len(board_members) >= 4:
            print("\n✅ SUCCESS: Multi-agent architecture fixed the regression!")
            print(f"   Board members extracted: {len(board_members)} (≥4 expected)")
            return True
        else:
            print(f"\n⚠️  PARTIAL: Only {len(board_members)} members (expected ≥4)")
            return False
    else:
        print("❌ FAILURE: Governance data is None")
        print("   The multi-agent architecture did not extract governance data")
        return False

if __name__ == "__main__":
    try:
        success = test_brf_81563()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
