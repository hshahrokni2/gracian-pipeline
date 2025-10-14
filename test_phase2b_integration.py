"""
Phase 2B Integration Test

Tests the integrated cross-validation, hallucination detection,
and consensus resolution system.

Usage:
    python test_phase2b_integration.py <pdf_path>

Author: Claude Code
Date: 2025-10-14
"""

import sys
import os
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel


def test_phase2b_integration(pdf_path: str):
    """
    Test Phase 2B integration on a single PDF.

    Expected behavior:
    1. All agents extract in parallel (Phase 1)
    2. Cross-validation runs (Phase 2B)
    3. Hallucination detection runs (Phase 2B)
    4. Consensus resolution runs (Phase 2B)
    5. Confidence scores calculated
    6. Validation metadata included in results
    """
    print("=" * 80)
    print("🧪 PHASE 2B INTEGRATION TEST")
    print("=" * 80)
    print(f"\nTest PDF: {pdf_path}")
    print()

    # Run extraction with Phase 2B validation
    results = extract_all_agents_parallel(
        pdf_path=pdf_path,
        max_workers=5,
        enable_retry=True,
        enable_learning=True,
        verbose=True
    )

    # Verify Phase 2B components are present
    print("\n" + "=" * 80)
    print("🔍 PHASE 2B VALIDATION RESULTS")
    print("=" * 80)

    # Check validation metadata
    if '_validation' in results:
        validation = results['_validation']
        print(f"\n✅ Validation metadata present")
        print(f"   Warnings: {validation['warnings_count']}")
        print(f"   High severity: {validation['high_severity_count']}")
        print(f"   Rules triggered: {', '.join(validation['rules_triggered'][:5])}")
        print(f"   Conflicts resolved: {validation['conflicts_resolved']}")

        # Show warnings
        if validation['warnings_count'] > 0:
            print(f"\n⚠️  Top warnings:")
            for warning in validation['warnings'][:5]:
                print(f"   - [{warning['severity']}] {warning['rule']}: {warning['message'][:80]}")
    else:
        print(f"\n❌ Validation metadata missing!")
        return False

    # Check consensus resolution
    if '_consensus' in results:
        consensus = results['_consensus']
        print(f"\n🤝 Consensus resolution results:")
        for field, resolution in list(consensus.items())[:5]:
            print(f"   - {field}: {resolution['strategy']} "
                 f"(confidence: {resolution['confidence']:.1%}, "
                 f"sources: {len(resolution['sources'])} agents)")
    else:
        print(f"\n✅ No conflicts needed resolution")

    # Check confidence scores
    if 'extraction_quality' in results:
        quality = results['extraction_quality']
        print(f"\n📊 Extraction quality:")
        print(f"   Overall confidence: {quality['confidence_score']:.1%}")
        print(f"   High confidence agents: {quality['high_confidence_agents']}")
        print(f"   Low confidence agents: {quality['low_confidence_agents']}")
    else:
        print(f"\n❌ Extraction quality missing!")
        return False

    # Final summary
    print("\n" + "=" * 80)
    print("✅ PHASE 2B INTEGRATION TEST PASSED")
    print("=" * 80)

    metadata = results['_metadata']
    print(f"\nExtraction summary:")
    print(f"   Success rate: {metadata['successful_agents']}/{metadata['total_agents']} agents")
    print(f"   Total time: {metadata['total_time_seconds']}s")
    print(f"   Tokens: {metadata['token_usage']:,}")

    validation = results['_validation']
    print(f"\nValidation summary:")
    print(f"   Warnings: {validation['warnings_count']}")
    print(f"   Conflicts resolved: {validation['conflicts_resolved']}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_phase2b_integration.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    success = test_phase2b_integration(pdf_path)
    sys.exit(0 if success else 1)
