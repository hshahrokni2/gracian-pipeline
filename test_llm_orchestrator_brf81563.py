#!/usr/bin/env python3
"""
Test LLM orchestrator on brf_81563 to validate governance fix.

Expected: Should route governance sections to chairman_agent, board_members_agent, auditor_agent
Previous behavior: 0 board members extracted (regression)
Target: 4+ board members extracted
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.vision_sectionizer import vision_sectionize


def test_brf_81563_governance():
    """Test LLM orchestrator routing on brf_81563.pdf"""

    # PDF path
    pdf_path = "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/Hjorthagen/brf_81563.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False

    print("=" * 80)
    print("Testing LLM Orchestrator on brf_81563")
    print("=" * 80)
    print(f"\nPDF: {os.path.basename(pdf_path)}")
    print("\n🔍 Running vision_sectionize with LLM orchestrator...\n")

    try:
        # Run sectionizer with LLM orchestrator
        result = vision_sectionize(pdf_path)

        # Extract results
        level_1 = result.get('level_1', [])
        level_2 = result.get('level_2', [])
        level_3 = result.get('level_3', [])
        pages_by_agent = result.get('pages_by_agent', {})

        print("\n" + "=" * 80)
        print("SECTION DETECTION RESULTS")
        print("=" * 80)
        print(f"\nLevel 1 sections: {len(level_1)}")
        for sec in level_1:
            print(f"  - {sec['title']} (pages {sec['start_page']}-{sec['end_page']})")

        print(f"\nLevel 2 sections: {len(level_2)}")
        for sec in level_2[:5]:  # Show first 5
            print(f"  - {sec['title']} under '{sec['parent']}' (pages {sec['start_page']}-{sec['end_page']})")
        if len(level_2) > 5:
            print(f"  ... and {len(level_2) - 5} more")

        print("\n" + "=" * 80)
        print("LLM ORCHESTRATOR ROUTING RESULTS")
        print("=" * 80)

        # Check governance agents specifically
        governance_agents = ['chairman_agent', 'board_members_agent', 'auditor_agent', 'governance_agent']
        governance_found = False

        print("\n📋 Governance Agents (Critical for brf_81563 regression fix):")
        for agent in governance_agents:
            pages = pages_by_agent.get(agent, [])
            if pages:
                governance_found = True
                # Convert to 1-indexed for display
                pages_display = [p + 1 for p in pages[:5]]
                suffix = "..." if len(pages) > 5 else ""
                print(f"  ✅ {agent}: {len(pages)} pages → {pages_display}{suffix}")
            else:
                print(f"  ❌ {agent}: No pages assigned")

        print("\n📊 All Agent Routing:")
        for agent, pages in sorted(pages_by_agent.items()):
            pages_display = [p + 1 for p in pages[:5]]
            suffix = "..." if len(pages) > 5 else ""
            print(f"  {agent}: {len(pages)} pages → {pages_display}{suffix}")

        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)

        if governance_found:
            print("\n✅ SUCCESS: Governance agents received page assignments!")
            print("   This should fix the brf_81563 regression (0 → 4+ board members)")
        else:
            print("\n❌ FAILURE: No governance agents received pages")
            print("   The regression may not be fixed")

        # Save results for inspection
        output_file = "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/test_llm_orchestrator_brf81563_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                'pdf': os.path.basename(pdf_path),
                'level_1_count': len(level_1),
                'level_2_count': len(level_2),
                'level_3_count': len(level_3),
                'level_1_sections': level_1,
                'level_2_sections': level_2,
                'pages_by_agent': {agent: [p + 1 for p in pages] for agent, pages in pages_by_agent.items()},
                'governance_agents_assigned': governance_found
            }, f, indent=2)

        print(f"\n💾 Results saved to: {os.path.basename(output_file)}")

        return governance_found

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_brf_81563_governance()
    sys.exit(0 if success else 1)
