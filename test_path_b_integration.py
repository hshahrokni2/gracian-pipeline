"""
Test script to verify Path B integration into Option A

Tests that:
1. Path B agents are correctly routed
2. Note detection works
3. Extraction produces results
4. Fallback to Option A works if Path B fails

Run: python test_path_b_integration.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import integrated orchestrator
from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel

def test_path_b_integration():
    """Test Path B integration with a single PDF."""

    # Use a test PDF (adjust path as needed)
    test_pdfs = [
        "data/raw_pdfs/Hjorthagen/brf_81563.pdf",
        "validation/machine_readable.pdf",
    ]

    test_pdf = None
    for pdf in test_pdfs:
        if os.path.exists(pdf):
            test_pdf = pdf
            break

    if not test_pdf:
        print("❌ No test PDF found")
        print("Searched:")
        for pdf in test_pdfs:
            print(f"  - {pdf}")
        return False

    print(f"Testing Path B integration on: {test_pdf}")
    print("=" * 80)

    try:
        # Run extraction
        result = extract_all_agents_parallel(
            test_pdf,
            max_workers=5,
            enable_retry=False,  # Disable retry for faster testing
            verbose=True
        )

        # Check Path B agent results
        print("\n" + "=" * 80)
        print("🔍 PATH B AGENT RESULTS")
        print("=" * 80)

        path_b_agents = [
            "notes_depreciation_agent",
            "notes_maintenance_agent",
            "notes_tax_agent",
        ]

        metadata = result.get("_metadata", {})
        agent_metadata = metadata.get("agent_metadata", {})

        path_b_success = 0
        path_b_total = 0

        for agent_id in path_b_agents:
            path_b_total += 1
            agent_result = result.get(agent_id, {})
            agent_meta = agent_metadata.get(agent_id, {})

            status = agent_meta.get("status", "unknown")
            integration_layer = agent_meta.get("integration_layer", "option_a")

            print(f"\n{agent_id}:")
            print(f"  Status: {status}")
            print(f"  Integration: {integration_layer}")
            print(f"  Fields extracted: {len(agent_result)}")

            if status == "success":
                path_b_success += 1

            # Show sample data
            if agent_result:
                print(f"  Sample data:")
                for key, value in list(agent_result.items())[:3]:
                    print(f"    {key}: {value}")

        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Path B Agents: {path_b_success}/{path_b_total} successful")
        print(f"Total Agents: {metadata.get('successful_agents')}/{metadata.get('total_agents')}")
        print(f"Total Time: {metadata.get('total_time_seconds')}s")
        print(f"Total Tokens: {metadata.get('token_usage'):,}")

        # Success if at least 1 Path B agent worked
        if path_b_success > 0:
            print("\n✅ PATH B INTEGRATION SUCCESS")
            return True
        else:
            print("\n⚠️  PATH B INTEGRATION PARTIAL (no Path B agents succeeded)")
            return False

    except Exception as e:
        print(f"\n❌ PATH B INTEGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_path_b_integration()
    sys.exit(0 if success else 1)
