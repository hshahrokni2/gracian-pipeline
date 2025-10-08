#!/usr/bin/env python3
"""
Debug script to inspect actual extraction results from Phase 2B test.
Shows what data was extracted and identifies the section-to-LLM disconnect.
"""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
gracian_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from optimal_brf_pipeline import OptimalBRFPipeline

def main():
    """Run extraction and dump detailed results"""

    pdf_path = "test_pdfs/brf_268882.pdf"

    print("🔍 Running extraction with detailed logging...\n")

    # Create pipeline
    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/debug",
        enable_caching=True
    )

    try:
        # Run extraction
        result = pipeline.extract_document(pdf_path)

        print("\n" + "="*70)
        print("📊 DETAILED EXTRACTION RESULTS")
        print("="*70)

        # Pass 1 results
        print("\n🎯 PASS 1 RESULTS (Governance, Property):")
        print("-" * 70)
        for agent_id, agent_result in result.pass1_result.items():
            print(f"\n📌 {agent_id}:")
            print(f"   Status: {agent_result.get('status', 'unknown')}")
            print(f"   Sections: {agent_result.get('section_headings', [])}")
            print(f"   Pages rendered: {agent_result.get('pages_rendered', [])}")
            print(f"   Evidence pages: {agent_result.get('evidence_pages', [])}")
            print(f"   Evidence verified: {agent_result.get('evidence_verified', False)}")
            print(f"   Time: {agent_result.get('extraction_time', 0):.1f}s")

            # Show extracted data
            data = agent_result.get('data', {})
            if data:
                print(f"   Extracted fields: {list(data.keys())}")
                print(f"   Sample data: {json.dumps(data, indent=6, ensure_ascii=False)[:500]}...")
            else:
                print(f"   ⚠️ No data extracted!")

        # Pass 2 results
        print("\n\n🎯 PASS 2 RESULTS (Financial + Notes):")
        print("-" * 70)
        for agent_id, agent_result in result.pass2_result.items():
            print(f"\n📌 {agent_id}:")
            print(f"   Status: {agent_result.get('status', 'unknown')}")
            print(f"   Sections: {agent_result.get('section_headings', [])}")
            print(f"   Pages rendered: {agent_result.get('pages_rendered', [])}")
            print(f"   Evidence pages: {agent_result.get('evidence_pages', [])}")
            print(f"   Evidence verified: {agent_result.get('evidence_verified', False)}")
            print(f"   Time: {agent_result.get('extraction_time', 0):.1f}s")

            # Show extracted data
            data = agent_result.get('data', {})
            if data:
                print(f"   Extracted fields: {list(data.keys())}")
                print(f"   Sample data: {json.dumps(data, indent=6, ensure_ascii=False)[:500]}...")
            else:
                print(f"   ⚠️ No data extracted!")

        # Quality analysis
        print("\n\n📈 QUALITY ANALYSIS:")
        print("-" * 70)
        total_agents = len(result.pass1_result) + len(result.pass2_result)
        agents_with_evidence = 0
        agents_with_data = 0

        all_results = {**result.pass1_result, **result.pass2_result}
        for agent_id, agent_result in all_results.items():
            if agent_result.get('data'):
                agents_with_data += 1
            if agent_result.get('evidence_pages'):
                agents_with_evidence += 1

        print(f"Total agents: {total_agents}")
        print(f"Agents with extracted data: {agents_with_data} ({agents_with_data/total_agents*100:.1f}%)")
        print(f"Agents with evidence_pages: {agents_with_evidence} ({agents_with_evidence/total_agents*100:.1f}%)")
        print(f"\n⚠️ Evidence gap: {total_agents - agents_with_evidence} agents missing evidence_pages")

        # Root cause analysis
        print("\n\n🔍 ROOT CAUSE ANALYSIS:")
        print("-" * 70)
        print("\nAgents WITHOUT evidence_pages:")
        for agent_id, agent_result in all_results.items():
            if not agent_result.get('evidence_pages'):
                data = agent_result.get('data', {})
                print(f"  • {agent_id}")
                print(f"    - Has data: {bool(data)}")
                print(f"    - Data keys: {list(data.keys()) if data else 'None'}")
                print(f"    - Status: {agent_result.get('status')}")

        print("\nAgents WITH evidence_pages:")
        for agent_id, agent_result in all_results.items():
            if agent_result.get('evidence_pages'):
                data = agent_result.get('data', {})
                print(f"  ✅ {agent_id}")
                print(f"     - Evidence: {agent_result.get('evidence_pages')}")
                print(f"     - Data keys: {list(data.keys())}")

    finally:
        pipeline.close()

if __name__ == "__main__":
    main()
