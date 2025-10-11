#!/usr/bin/env python3
"""
Test Integrated BRF Pipeline - All 5 Components

This script tests the complete integrated pipeline with:
- Component 1: Enhanced Structure Detector
- Component 2: Smart Context Manager
- Component 3: Cross-Agent Data Linker
- Component 4: Multi-Pass Validator
- Component 5: Swedish Financial Dictionary
"""

import sys
import json
import time
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from integrated_brf_pipeline import IntegratedBRFPipeline


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_fast_mode(pdf_path: str):
    """Test fast mode (Components 1+5 only)"""
    print_section("TESTING FAST MODE (Components 1+5)")

    print("🚀 Initializing pipeline in fast mode...")
    pipeline = IntegratedBRFPipeline(mode='fast')
    print("   ✅ Pipeline initialized")
    print()

    print(f"📄 Processing: {Path(pdf_path).name}")
    start_time = time.time()

    try:
        result = pipeline.extract_document(pdf_path)
        elapsed = time.time() - start_time

        print()
        print_section("FAST MODE RESULTS")

        # Print metrics
        print("⏱️  Performance:")
        print(f"   Total Time: {result.total_time:.2f}s")
        print(f"   Structure Detection: {result.structure_time:.2f}s")
        print(f"   Section Routing: {result.routing_time:.2f}s")
        print(f"   Extraction: {result.extraction_time:.2f}s")
        print()

        print("📊 Quality Metrics:")
        print(f"   Coverage: {result.quality_metrics.get('coverage', 0)*100:.1f}%")
        print(f"   Evidence Ratio: {result.quality_metrics.get('evidence_ratio', 0)*100:.1f}%")
        print(f"   Overall Score: {result.quality_metrics.get('overall_score', 0)*100:.1f}%")
        print(f"   Needs Coaching: {'YES' if result.quality_metrics.get('needs_coaching') else 'NO'}")
        print()

        print("🔧 Component Status:")
        m = result.integration_metrics
        print(f"   Structure Detection: {'✅' if m.structure_detection_success else '❌'}")
        print(f"   Dictionary Lookups: {m.dictionary_lookups} (hits: {m.dictionary_hits}, fuzzy: {m.dictionary_fuzzy_matches})")
        print()

        print("✅ FAST MODE TEST COMPLETE")
        return True

    except Exception as e:
        print(f"❌ FAST MODE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deep_mode(pdf_path: str):
    """Test deep mode (All 5 components)"""
    print_section("TESTING DEEP MODE (All 5 Components)")

    print("🚀 Initializing pipeline in deep mode...")
    pipeline = IntegratedBRFPipeline(mode='deep')
    print("   ✅ Pipeline initialized")
    print()

    print(f"📄 Processing: {Path(pdf_path).name}")
    start_time = time.time()

    try:
        result = pipeline.extract_document(pdf_path)
        elapsed = time.time() - start_time

        print()
        print_section("DEEP MODE RESULTS")

        # Print metrics
        print("⏱️  Performance:")
        print(f"   Total Time: {result.total_time:.2f}s")
        print(f"   Structure Detection: {result.structure_time:.2f}s")
        print(f"   Section Routing: {result.routing_time:.2f}s")
        print(f"   Extraction: {result.extraction_time:.2f}s")
        print()

        print("📊 Quality Metrics:")
        print(f"   Coverage: {result.quality_metrics.get('coverage', 0)*100:.1f}%")
        print(f"   Evidence Ratio: {result.quality_metrics.get('evidence_ratio', 0)*100:.1f}%")
        print(f"   Overall Score: {result.quality_metrics.get('overall_score', 0)*100:.1f}%")
        print(f"   Needs Coaching: {'YES' if result.quality_metrics.get('needs_coaching') else 'NO'}")
        print()

        print("🔧 Component Status:")
        m = result.integration_metrics
        print(f"   1. Structure Detection: {'✅' if m.structure_detection_success else '❌'} ({m.structure_detection_time:.2f}s)")
        print(f"   2. Context Manager: {'✅' if m.context_manager_success else '⏭️ '} ({m.context_manager_time:.2f}s)")
        print(f"      - Low Confidence Regions: {m.low_confidence_regions}")
        print(f"      - Vision API Calls: {m.vision_api_calls}")
        print(f"   3. Data Linking: {'✅' if m.data_linking_success else '⏭️ '} ({m.data_linking_time:.2f}s)")
        print(f"      - Matched Links: {m.matched_links}")
        print(f"      - Conflicts: {m.conflicts}")
        print(f"      - OCR Corrections: {m.ocr_corrections}")
        print(f"   4. Validation: {'✅' if m.validation_success else '⏭️ '} ({m.validation_time:.2f}s)")
        print(f"      - Pass Rate: {m.pass_rate*100:.1f}%")
        print(f"      - Errors: {m.errors}")
        print(f"      - Warnings: {m.warnings}")
        print(f"   5. Dictionary: {m.dictionary_lookups} lookups ({m.dictionary_hits} hits, {m.dictionary_fuzzy_matches} fuzzy)")
        print()

        # Print validation details if available
        if result.validation_report:
            print("🔍 Validation Report:")
            print(f"   {result.validation_report.summary()}")
            print()

        print("✅ DEEP MODE TEST COMPLETE")
        return True

    except Exception as e:
        print(f"❌ DEEP MODE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integrated pipeline tests"""
    print_section("INTEGRATED BRF PIPELINE - COMPREHENSIVE TEST")

    # Test PDF path
    pdf_path = "test_pdfs/brf_268882.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        print("   Please ensure test PDF is in the correct location")
        sys.exit(1)

    print(f"📄 Test Document: {pdf_path}")
    print(f"📦 Size: {Path(pdf_path).stat().st_size / 1024:.1f} KB")
    print()

    # Run tests
    fast_success = test_fast_mode(pdf_path)

    print("\n" + "="*80 + "\n")
    time.sleep(2)  # Brief pause between tests

    deep_success = test_deep_mode(pdf_path)

    # Final summary
    print()
    print_section("FINAL TEST SUMMARY")

    print("📊 Test Results:")
    print(f"   Fast Mode: {'✅ PASS' if fast_success else '❌ FAIL'}")
    print(f"   Deep Mode: {'✅ PASS' if deep_success else '❌ FAIL'}")
    print()

    if fast_success and deep_success:
        print("🎉 ALL TESTS PASSED - Integrated Pipeline Ready for Production Testing")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Review output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
