#!/usr/bin/env python3
"""
Test Parallel Orchestrator on brf_81563 (Regression Case)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import parallel orchestrator
from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel

def main():
    """Test parallel orchestrator on brf_81563.pdf"""

    # Test PDF path
    test_pdf = "Hjorthagen/brf_81563.pdf"

    print("=" * 80)
    print("🧪 PARALLEL ORCHESTRATOR TEST")
    print("=" * 80)
    print(f"Testing on: {test_pdf}")
    print(f"Expected: Extract >= 4 board members (fix regression)")
    print()

    # Run parallel extraction
    try:
        result = extract_all_agents_parallel(
            test_pdf,
            max_workers=5,
            enable_retry=True,
            verbose=True
        )

        print("\n" + "=" * 80)
        print("📊 RESULTS ANALYSIS")
        print("=" * 80)

        # Check metadata
        metadata = result.get("_metadata", {})
        print(f"Total agents: {metadata.get('total_agents', 0)}")
        print(f"Successful agents: {metadata.get('successful_agents', 0)}")
        print(f"Failed agents: {metadata.get('failed_agents', [])}")
        print(f"Total time: {metadata.get('total_time_seconds', 0):.1f}s")
        print(f"Token usage: {metadata.get('token_usage', 0):,}")

        # Check governance results
        print("\n" + "=" * 80)
        print("👥 GOVERNANCE EXTRACTION")
        print("=" * 80)

        governance = result.get("governance_agent", {})
        if governance:
            chairman = governance.get("chairman", "NOT_FOUND")
            board_members = governance.get("board_members", [])
            auditor = governance.get("auditor_name", "NOT_FOUND")

            print(f"Chairman: {chairman}")
            print(f"Board members count: {len(board_members)}")
            print(f"Auditor: {auditor}")

            if board_members:
                print("\nBoard members:")
                for i, member in enumerate(board_members, 1):
                    if isinstance(member, dict):
                        name = member.get("name", "UNKNOWN")
                        role = member.get("role", "UNKNOWN")
                        print(f"  {i}. {name} - {role}")
                    else:
                        print(f"  {i}. {member}")

            # Regression check
            print("\n" + "=" * 80)
            if len(board_members) >= 4:
                print("✅ SUCCESS: Extracted >= 4 board members")
                print("   Regression fixed!")
            else:
                print("❌ FAILURE: Still not extracting enough board members")
                print(f"   Expected: >= 4, Got: {len(board_members)}")
        else:
            print("❌ FAILURE: governance_agent returned no data")

        # Save results
        output_path = Path("data/parallel_orchestrator_test_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Full results saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
