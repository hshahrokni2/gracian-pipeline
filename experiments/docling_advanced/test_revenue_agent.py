#!/usr/bin/env python3
"""Test revenue_breakdown_agent on brf_198532"""

import sys
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
    print("🧪 Testing revenue_breakdown_agent on brf_198532...\n")

    # Initialize pipeline
    pipeline = OptimalBRFPipeline(enable_caching=True)

    # Run extraction
    result = pipeline.extract_document("../../SRS/brf_198532.pdf")

    # Check revenue_breakdown_agent results
    if 'revenue_breakdown_agent' in result.pass2_result:
        agent_result = result.pass2_result['revenue_breakdown_agent']
        print(f"\n📊 Revenue Breakdown Agent Results:")
        print(f"   Status: {agent_result.get('status')}")
        print(f"   Evidence pages: {agent_result.get('evidence_pages', [])}")

        if agent_result.get('status') == 'success':
            data = agent_result.get('data', {})
            rb = data.get('revenue_breakdown', {})

            # Count extracted fields
            extracted_fields = sum(1 for v in rb.values() if v and v != 0)
            total_fields = len(rb)
            print(f"   Extracted fields: {extracted_fields}/{total_fields}")
            print(f"\n   Revenue breakdown details:")
            for key, value in sorted(rb.items()):
                if key != 'evidence_pages':
                    if isinstance(value, (int, float)) and value != 0:
                        print(f"     {key}: {value:,}")
                    elif key == 'evidence_pages' or (isinstance(value, list) and value):
                        print(f"     {key}: {value}")
        else:
            print(f"   Error: {agent_result.get('error', 'Unknown error')}")
    else:
        print("❌ revenue_breakdown_agent not found in results")

    pipeline.close()

    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
