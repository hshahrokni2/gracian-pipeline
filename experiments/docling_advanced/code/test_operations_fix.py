#!/usr/bin/env python3
"""
Test operations_agent fix on brf_198532.pdf

Validates that operations_agent is now being called.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
gracian_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import pipeline
from optimal_brf_pipeline import OptimalBRFPipeline

def test_operations_agent_fix():
    """Test that operations_agent is now called"""

    print("🧪 Testing operations_agent fix...")
    print("=" * 70)

    # Test PDF (known to have operations content)
    pdf_path = "../../SRS/brf_198532.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False

    # Run pipeline
    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/optimal_pipeline",
        enable_caching=True
    )

    try:
        result = pipeline.extract_document(pdf_path)

        # Check if operations_agent was called
        agent_results = {}
        agent_results.update(result.pass1_result)
        agent_results.update(result.pass2_result)

        print("\n📊 Agent Results:")
        print(f"   Total agents: {len(agent_results)}")

        # Check operations_agent
        if 'operations_agent' in agent_results:
            ops_result = agent_results['operations_agent']
            print(f"\n✅ operations_agent WAS CALLED!")
            print(f"   Status: {ops_result.get('status')}")
            print(f"   Data keys: {list(ops_result.get('data', {}).keys())}")
            print(f"   Evidence pages: {ops_result.get('evidence_pages', [])}")
            return True
        else:
            print(f"\n❌ operations_agent NOT CALLED (bug still present)")
            print(f"\n   Agents called: {list(agent_results.keys())}")
            return False

    finally:
        pipeline.close()

if __name__ == "__main__":
    success = test_operations_agent_fix()
    sys.exit(0 if success else 1)
