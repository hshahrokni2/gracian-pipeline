#!/usr/bin/env python3
"""
Test integrated Phase 2A pipeline with vision consensus routing.

Expected Results:
- Scanned PDF: Route to vision consensus (75-85% coverage vs 37.4% baseline)
- Machine-readable: Route to text extraction (67.0% maintained)
- Hybrid: Route to text, fallback to vision if <30% coverage (from 46.2% baseline)
"""

import sys
import os

# Ensure we can import from gracian_pipeline
sys.path.insert(0, '/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline')

from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel

def test_pdf(pdf_path, expected_type, expected_strategy, baseline_coverage):
    """Test single PDF and report results."""
    print("\n" + "="*80)
    print(f"Testing: {pdf_path}")
    print(f"Expected Type: {expected_type}")
    print(f"Expected Strategy: {expected_strategy}")
    print(f"Baseline Coverage: {baseline_coverage:.1%}")
    print("="*80)

    try:
        # Extract with integrated pipeline
        result = extract_all_agents_parallel(
            pdf_path,
            max_workers=3,
            verbose=True
        )

        # Analyze results
        metadata = result.get('_metadata', {})

        print("\n🎯 INTEGRATION TEST RESULTS:")
        print(f"   PDF Type: {metadata.get('pdf_type', 'unknown')}")
        print(f"   Strategy: {metadata.get('extraction_strategy', 'unknown')}")
        print(f"   Classification Confidence: {metadata.get('classification_confidence', 0):.1%}")
        print(f"   Successful Agents: {metadata.get('successful_agents', 0)}/{metadata.get('total_agents', 0)}")
        print(f"   Total Time: {metadata.get('total_time_seconds', 0):.1f}s")

        # Calculate coverage
        total_fields = 0
        populated_fields = 0

        for agent_name, agent_result in result.items():
            if agent_name.startswith('_'):
                continue

            if isinstance(agent_result, dict):
                for field, value in agent_result.items():
                    if field.startswith('_') or field in ['evidence_pages', 'extraction_method']:
                        continue
                    total_fields += 1
                    if value not in (None, '', []):
                        populated_fields += 1

        coverage = populated_fields / total_fields if total_fields > 0 else 0.0

        print(f"\n📊 COVERAGE ANALYSIS:")
        print(f"   Populated Fields: {populated_fields}/{total_fields}")
        print(f"   Coverage: {coverage:.1%}")
        print(f"   Baseline: {baseline_coverage:.1%}")
        print(f"   Improvement: {(coverage - baseline_coverage)*100:+.1f}pp")

        # Success assessment
        type_match = metadata.get('pdf_type') == expected_type
        strategy_match = metadata.get('extraction_strategy') == expected_strategy
        improvement = coverage > baseline_coverage

        print(f"\n✅ SUCCESS CRITERIA:")
        print(f"   Type Classification: {'✅' if type_match else '❌'} (expected: {expected_type})")
        print(f"   Strategy Selection: {'✅' if strategy_match else '❌'} (expected: {expected_strategy})")
        print(f"   Coverage Improvement: {'✅' if improvement else '❌'} ({coverage:.1%} vs {baseline_coverage:.1%})")

        return {
            "success": type_match and strategy_match and improvement,
            "pdf_type": metadata.get('pdf_type'),
            "strategy": metadata.get('extraction_strategy'),
            "coverage": coverage,
            "baseline": baseline_coverage,
            "improvement": coverage - baseline_coverage
        }

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """Run integration tests on all 3 PDF types."""
    print("\n" + "="*80)
    print("PHASE 2A INTEGRATION VALIDATION")
    print("="*80)
    print("\nTesting integrated pipeline with vision consensus routing...")
    print("Expected: Scanned PDFs route to vision, machine-readable to text\n")

    # Test cases (from ACTUAL baseline validation results - Oct 14, 2025)
    test_cases = [
        {
            "pdf_path": "validation/test_pdfs/scanned.pdf",
            "expected_type": "scanned",
            "expected_strategy": "vision_consensus",
            "baseline_coverage": 0.374  # 37.4% from baseline (CORRECTED)
        },
        {
            "pdf_path": "validation/test_pdfs/machine_readable.pdf",
            "expected_type": "machine_readable",
            "expected_strategy": "text",
            "baseline_coverage": 0.670  # 67.0% from baseline (CORRECTED)
        },
        {
            "pdf_path": "validation/test_pdfs/hybrid.pdf",
            "expected_type": "hybrid",
            "expected_strategy": "text",  # Will fallback to vision if <30%
            "baseline_coverage": 0.462  # 46.2% from baseline (CORRECTED)
        }
    ]

    results = []

    for test_case in test_cases:
        result = test_pdf(**test_case)
        results.append(result)

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    successful_tests = sum(1 for r in results if r.get("success", False))

    print(f"\n📊 Overall Results:")
    print(f"   Tests Passed: {successful_tests}/{len(results)}")

    print(f"\n📈 Coverage Improvements:")
    for i, (test_case, result) in enumerate(zip(test_cases, results), 1):
        if "coverage" in result:
            pdf_name = test_case["pdf_path"].split("/")[-1]
            improvement = result.get("improvement", 0)
            print(f"   {i}. {pdf_name}: {result['baseline']:.1%} → {result['coverage']:.1%} ({improvement*100:+.1f}pp)")

    if successful_tests == len(results):
        print("\n✅ ALL TESTS PASSED - Integration successful!")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS - {successful_tests}/{len(results)} tests passed")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
