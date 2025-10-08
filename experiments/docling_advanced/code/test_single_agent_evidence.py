#!/usr/bin/env python3
"""
Experiment: Single-Agent Evidence Tracking Test
Run ONLY governance_agent to diagnose evidence_pages issue with full logging
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
gracian_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")

# Add to path
sys.path.insert(0, str(gracian_root))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from optimal_brf_pipeline import OptimalBRFPipeline

def main():
    """Run single governance agent extraction with full diagnostics"""

    pdf_path = "test_pdfs/brf_268882.pdf"

    print("\n" + "="*70)
    print("🔬 EXPERIMENT: Single-Agent Evidence Tracking Test")
    print("="*70)
    print(f"PDF: {pdf_path}")
    print(f"Agent: governance_agent (the one that supposedly works)")
    print("="*70 + "\n")

    # Create pipeline
    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/experiment",
        enable_caching=True
    )

    try:
        # Stage 1: Topology
        print("📊 STAGE 1: PDF Topology Detection")
        topology = pipeline.analyze_topology(pdf_path)
        print(f"   Classification: {topology.classification}")
        print(f"   Total pages: {topology.total_pages}\n")

        # Stage 2: Structure Detection
        print("🔍 STAGE 2: Structure Detection (Docling)")
        structure = pipeline.detect_structure(pdf_path, topology)
        print(f"   Sections detected: {structure.num_sections}")
        print(f"   Method: {structure.method}\n")

        # Stage 3: Routing
        print("🧭 STAGE 3: Section Routing")
        routing = pipeline.route_sections(structure)
        print(f"   Governance sections: {len(routing.main_sections.get('governance_agent', []))}")

        # Print the actual sections for governance
        gov_sections = routing.main_sections.get('governance_agent', [])
        if gov_sections:
            print(f"   Sections: {gov_sections}\n")
        else:
            print(f"   ⚠️ No sections found for governance_agent!\n")

        # Stage 4: Extract ONLY governance_agent
        print("🎯 STAGE 4: Single-Agent Extraction (governance_agent)")
        print("-" * 70)

        result = pipeline._extract_agent(
            pdf_path=pdf_path,
            agent_id='governance_agent',
            section_headings=gov_sections if gov_sections else ['Styrelse', 'Förvaltning'],
            context={}
        )

        print("\n" + "-" * 70)
        print("📋 EXTRACTION RESULT:")
        print(f"   Status: {result.get('status')}")
        print(f"   Extracted keys: {list(result.get('data', {}).keys())}")
        print(f"   Evidence pages: {result.get('evidence_pages', [])}")
        print(f"   Evidence verified: {result.get('evidence_verified', False)}")
        print(f"   Pages rendered: {result.get('pages_rendered', [])}")
        print(f"   Extraction time: {result.get('extraction_time', 0):.1f}s")

        # Detailed data inspection
        data = result.get('data', {})
        if data:
            print(f"\n   📊 EXTRACTED DATA:")
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"      {key}: {len(value)} items")
                elif isinstance(value, str):
                    preview = value[:50] if len(value) > 50 else value
                    print(f"      {key}: {preview}...")
                else:
                    print(f"      {key}: {value}")

        print("\n" + "="*70)
        print("✅ EXPERIMENT COMPLETE")
        print("="*70)

        # Final analysis
        print("\n🔍 ANALYSIS:")
        if result.get('evidence_pages'):
            print(f"   ✅ SUCCESS: evidence_pages found: {result['evidence_pages']}")
        else:
            print(f"   ❌ FAILURE: evidence_pages MISSING or empty")

        if result.get('status') == 'success':
            print(f"   ✅ Extraction succeeded")
        else:
            print(f"   ❌ Extraction failed: {result.get('error', 'Unknown error')}")

    finally:
        pipeline.close()

if __name__ == "__main__":
    main()
