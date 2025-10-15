#!/usr/bin/env python3
"""
Test Two-LLM Ground Truth System on Seed PDFs

Date: 2025-10-15
Purpose: Validate two-LLM verification system performance vs manual verification
Expected: 23 min manual → 8 min with two-LLM (65% reduction)

Usage:
    python test_two_llm_system.py
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ground_truth.scripts.create_two_llm_ground_truth import TwoLLMGroundTruthCreator


def test_seed_pdf(pdf_path: str, manual_verification_time: int) -> Dict:
    """
    Test two-LLM system on a single seed PDF and compare with manual verification.

    Args:
        pdf_path: Path to PDF
        manual_verification_time: Time (minutes) it took for manual verification

    Returns:
        Dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing: {Path(pdf_path).name}")
    print(f"Manual verification time: {manual_verification_time} minutes")
    print(f"{'='*80}\n")

    start_time = time.time()

    try:
        # Run two-LLM pipeline
        creator = TwoLLMGroundTruthCreator(pdf_path)
        consensus_gt, human_needed = creator.run_full_pipeline()

        elapsed_minutes = (time.time() - start_time) / 60

        # Calculate expected human time (1 min per disagreement)
        expected_human_time = len(human_needed)
        total_time = elapsed_minutes + expected_human_time

        # Calculate time savings
        time_saved = manual_verification_time - expected_human_time
        time_saved_pct = (time_saved / manual_verification_time * 100) if manual_verification_time > 0 else 0

        results = {
            'pdf_name': Path(pdf_path).name,
            'manual_verification_time_min': manual_verification_time,
            'llm_processing_time_min': round(elapsed_minutes, 2),
            'fields_flagged_by_claude': len(creator.gpt_results) if creator.gpt_results else 0,
            'fields_auto_resolved': len(creator.gpt_results) - len(human_needed) if creator.gpt_results else 0,
            'fields_need_human': len(human_needed),
            'expected_human_time_min': expected_human_time,
            'total_time_min': round(total_time, 2),
            'time_saved_min': time_saved,
            'time_saved_pct': round(time_saved_pct, 1),
            'success': True
        }

        print(f"\n📊 Results for {Path(pdf_path).name}:")
        print(f"   Manual verification: {manual_verification_time} min")
        print(f"   LLM processing: {results['llm_processing_time_min']} min")
        print(f"   Fields flagged: {results['fields_flagged_by_claude']}")
        print(f"   Auto-resolved: {results['fields_auto_resolved']}")
        print(f"   Need human: {results['fields_need_human']} → {expected_human_time} min")
        print(f"   Time saved: {time_saved} min ({time_saved_pct:.1f}%)")

        return results

    except Exception as e:
        print(f"❌ Error testing {Path(pdf_path).name}: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'pdf_name': Path(pdf_path).name,
            'success': False,
            'error': str(e)
        }


def main():
    """
    Test two-LLM system on all 3 seed PDFs.
    """
    print("🚀 Two-LLM Ground Truth System Validation")
    print("="*80)

    # Define seed PDFs with their manual verification times
    seed_pdfs = [
        {
            'path': str(project_root / 'ground_truth' / 'seed_pdfs' / 'brf_268882.pdf'),
            'manual_time': 5  # minutes
        },
        {
            'path': str(project_root / 'ground_truth' / 'seed_pdfs' / 'brf_81563.pdf'),
            'manual_time': 3  # minutes
        },
        {
            'path': str(project_root / 'ground_truth' / 'seed_pdfs' / 'brf_76536.pdf'),
            'manual_time': 15  # minutes
        }
    ]

    # Test each seed PDF
    results = []
    for seed in seed_pdfs:
        if not Path(seed['path']).exists():
            print(f"⚠️  Skipping {Path(seed['path']).name} - file not found")
            continue

        result = test_seed_pdf(seed['path'], seed['manual_time'])
        results.append(result)

    # Aggregate results
    print(f"\n{'='*80}")
    print("📈 AGGREGATE RESULTS")
    print(f"{'='*80}\n")

    successful_tests = [r for r in results if r.get('success')]

    if successful_tests:
        total_manual_time = sum(r['manual_verification_time_min'] for r in successful_tests)
        total_expected_human_time = sum(r['expected_human_time_min'] for r in successful_tests)
        total_time_saved = total_manual_time - total_expected_human_time
        total_time_saved_pct = (total_time_saved / total_manual_time * 100) if total_manual_time > 0 else 0

        print(f"✅ Successfully tested: {len(successful_tests)}/3 PDFs\n")
        print(f"Manual verification time (baseline): {total_manual_time} min")
        print(f"Two-LLM expected human time: {total_expected_human_time} min")
        print(f"Time saved: {total_time_saved} min ({total_time_saved_pct:.1f}%)\n")

        print("Per-PDF Breakdown:")
        for r in successful_tests:
            print(f"  - {r['pdf_name']}: {r['manual_verification_time_min']} min → {r['expected_human_time_min']} min ({r['time_saved_pct']:.1f}% saved)")

        # Check if we hit target
        if total_time_saved_pct >= 60:
            print(f"\n🎉 SUCCESS! Achieved {total_time_saved_pct:.1f}% time reduction (target: ≥60%)")
        else:
            print(f"\n⚠️  Below target: {total_time_saved_pct:.1f}% reduction (target: ≥60%)")

    else:
        print("❌ No successful tests")

    # Save results to JSON
    output_path = project_root / 'ground_truth' / 'two_llm_results' / 'test_results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'results': results,
            'summary': {
                'successful_tests': len(successful_tests),
                'total_manual_time_min': sum(r['manual_verification_time_min'] for r in successful_tests) if successful_tests else 0,
                'total_expected_human_time_min': sum(r['expected_human_time_min'] for r in successful_tests) if successful_tests else 0,
                'total_time_saved_min': sum(r['time_saved_min'] for r in successful_tests) if successful_tests else 0,
                'time_saved_pct': (sum(r['time_saved_min'] for r in successful_tests) / sum(r['manual_verification_time_min'] for r in successful_tests) * 100) if successful_tests else 0
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Test results saved: {output_path}")


if __name__ == "__main__":
    main()
