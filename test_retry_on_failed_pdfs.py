"""
Test Retry Logic on 5 Failed PDFs from Week 3 Day 3

These 5 PDFs failed with "Connection error" in the baseline test.
This script validates that the retry logic implementation recovers from transient failures.
"""

import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify API key is loaded
if not os.getenv('OPENAI_API_KEY'):
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    print(f"   Checked: {env_path}")
    sys.exit(1)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

# 5 PDFs that failed in Week 3 Day 3 baseline test (all connection errors)
FAILED_PDFS = [
    "SRS/brf_47809.pdf",
    "SRS/brf_47903.pdf",
    "SRS/brf_48663.pdf",
    "SRS/brf_52576.pdf",
    "SRS/brf_53107.pdf"
]

def test_retry_logic():
    """Test retry logic on failed PDFs."""
    print("🧪 WEEK 3 DAY 4: Retry Logic Validation Test")
    print("=" * 70)
    print("\nTesting 5 PDFs that failed with connection errors in baseline test")
    print("Expected: Retry logic should recover from transient failures\n")
    print("=" * 70)

    results = []
    start_time = time.time()

    for i, pdf_path in enumerate(FAILED_PDFS, 1):
        print(f"\n[{i}/5] Testing: {pdf_path}")
        print("-" * 70)

        pdf_start = time.time()

        try:
            # Extract with retry logic (mode='fast' for quicker testing)
            result = extract_brf_to_pydantic(pdf_path, mode='fast')

            pdf_time = time.time() - pdf_start

            # Check if extraction was successful
            if result and hasattr(result, 'coverage_percentage'):
                coverage = result.coverage_percentage
                confidence = result.confidence_score

                print(f"  ✅ SUCCESS")
                print(f"     Coverage: {coverage:.1f}%")
                print(f"     Confidence: {confidence:.2f}")
                print(f"     Extraction Time: {pdf_time:.1f}s")

                results.append({
                    'pdf': pdf_path,
                    'status': 'success',
                    'coverage': coverage,
                    'confidence': confidence,
                    'time': pdf_time
                })
            else:
                print(f"  ⚠️  PARTIAL: Extraction returned but missing metrics")
                results.append({
                    'pdf': pdf_path,
                    'status': 'partial',
                    'time': pdf_time
                })

        except Exception as e:
            pdf_time = time.time() - pdf_start
            print(f"  ❌ FAILED: {type(e).__name__}: {e}")
            print(f"     Time to failure: {pdf_time:.1f}s")

            results.append({
                'pdf': pdf_path,
                'status': 'failed',
                'error': str(e),
                'time': pdf_time
            })

    # Summary
    total_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("📊 RETRY LOGIC VALIDATION SUMMARY")
    print("=" * 70)

    successes = [r for r in results if r['status'] == 'success']
    failures = [r for r in results if r['status'] == 'failed']
    partials = [r for r in results if r['status'] == 'partial']

    print(f"\n✅ Successful: {len(successes)}/5 ({len(successes)/5*100:.0f}%)")
    print(f"❌ Failed: {len(failures)}/5 ({len(failures)/5*100:.0f}%)")
    if partials:
        print(f"⚠️  Partial: {len(partials)}/5 ({len(partials)/5*100:.0f}%)")

    if successes:
        avg_coverage = sum(r['coverage'] for r in successes) / len(successes)
        avg_confidence = sum(r['confidence'] for r in successes) / len(successes)
        avg_time = sum(r['time'] for r in successes) / len(successes)

        print(f"\n📈 Success Metrics:")
        print(f"   Average Coverage: {avg_coverage:.1f}%")
        print(f"   Average Confidence: {avg_confidence:.2f}")
        print(f"   Average Time: {avg_time:.1f}s")

    print(f"\n⏱️  Total Test Time: {total_time:.1f}s")

    # Comparison with Week 3 Day 3 baseline
    print("\n" + "=" * 70)
    print("📊 COMPARISON WITH WEEK 3 DAY 3 BASELINE")
    print("=" * 70)
    print(f"\nBaseline (WITHOUT retry logic):")
    print(f"  - Success Rate: 0/5 (0%)")
    print(f"  - All failed with: Connection error")

    print(f"\nDay 4 (WITH retry logic):")
    print(f"  - Success Rate: {len(successes)}/5 ({len(successes)/5*100:.0f}%)")

    if len(successes) == 5:
        print(f"\n🎉 VALIDATION SUCCESSFUL!")
        print(f"   ✅ 100% recovery rate (5/5 PDFs)")
        print(f"   ✅ Retry logic is working as expected")
        print(f"   ✅ Ready to proceed to Phase 2: Partial Extraction Mode")
    elif len(successes) >= 3:
        print(f"\n✅ VALIDATION MOSTLY SUCCESSFUL")
        print(f"   ✅ {len(successes)/5*100:.0f}% recovery rate ({len(successes)}/5 PDFs)")
        print(f"   ⚠️  Some failures may indicate non-transient issues")
        print(f"   ✅ Retry logic is helping, proceed to Phase 2")
    elif len(successes) >= 1:
        print(f"\n⚠️  PARTIAL VALIDATION")
        print(f"   ⚠️  {len(successes)/5*100:.0f}% recovery rate ({len(successes)}/5 PDFs)")
        print(f"   ⚠️  Consider investigating remaining failures")
    else:
        print(f"\n❌ VALIDATION FAILED")
        print(f"   ❌ 0% recovery rate (0/5 PDFs)")
        print(f"   ❌ Retry logic may not be working or API is still down")
        print(f"   ⚠️  Consider implementing Circuit Breaker pattern")

    print("\n" + "=" * 70)

    return results


if __name__ == "__main__":
    results = test_retry_logic()
