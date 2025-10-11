#!/usr/bin/env python3
"""
Test script to validate OptimalBRFPipeline after refactoring to inherit from BaseExtractor.

This test ensures that:
1. Inheritance works correctly
2. Coverage is maintained (should be similar to pre-refactoring)
3. All inherited methods are accessible
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST (before any other imports that might need them)
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from optimal_brf_pipeline import OptimalBRFPipeline


def test_refactored_optimal_pipeline():
    """Test the refactored optimal pipeline."""

    # Test document
    test_pdf = Path(__file__).parent.parent / "test_pdfs" / "brf_198532.pdf"

    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return

    print("="*80)
    print("TESTING REFACTORED OPTIMAL PIPELINE")
    print("="*80)
    print(f"\n📄 Test Document: {test_pdf.name}")

    # Initialize pipeline
    print("\n1️⃣ Initializing OptimalBRFPipeline...")
    try:
        pipeline = OptimalBRFPipeline(
            cache_dir="results/cache",
            output_dir="results/optimal_pipeline_refactored",
            enable_caching=True
        )
        print("   ✅ Pipeline initialized successfully")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify inherited methods are accessible
    print("\n2️⃣ Verifying inherited methods...")
    methods_to_check = [
        '_render_pdf_pages',
        '_parse_json_with_fallback',
        '_extract_agent',
        '_get_pages_for_sections'
    ]

    for method_name in methods_to_check:
        if hasattr(pipeline, method_name):
            method = getattr(pipeline, method_name)
            if callable(method):
                print(f"   ✅ {method_name} is accessible and callable")
            else:
                print(f"   ⚠️ {method_name} exists but is not callable")
        else:
            print(f"   ❌ {method_name} not found")

    # Check that we're using the base class implementation (not local duplicates)
    print("\n3️⃣ Verifying BaseExtractor inheritance...")
    from base_brf_extractor import BaseExtractor

    if isinstance(pipeline, BaseExtractor):
        print("   ✅ Pipeline correctly inherits from BaseExtractor")
    else:
        print("   ❌ Pipeline does not inherit from BaseExtractor")

    # Check AGENT_PROMPTS from base class
    if hasattr(pipeline, 'AGENT_PROMPTS'):
        num_prompts = len(pipeline.AGENT_PROMPTS)
        print(f"   ✅ AGENT_PROMPTS inherited: {num_prompts} agents")
    else:
        print("   ❌ AGENT_PROMPTS not inherited")

    # Run extraction
    print("\n4️⃣ Running extraction...")
    try:
        result = pipeline.extract_document(str(test_pdf))
        print(f"   ✅ Extraction completed")

        # Display results
        print("\n" + "="*80)
        print("EXTRACTION RESULTS")
        print("="*80)

        # Load the saved JSON file (pipeline saves it automatically)
        output_file = Path("results/optimal_pipeline_refactored") / f"{test_pdf.stem}_optimal_result.json"

        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                extraction_data = json.load(f)

            # Overall metrics
            overall_score = extraction_data.get('quality_metrics', {}).get('overall_score', 0) * 100
            overall_coverage = extraction_data.get('quality_metrics', {}).get('coverage', 0) * 100

            print(f"\n📊 Overall Metrics:")
            print(f"   • Overall Score: {overall_score:.1f}%")
            print(f"   • Coverage: {overall_coverage:.1f}%")

            # Agent results
            agent_results = extraction_data.get('agent_results', {})
            print(f"\n🤖 Agent Results:")
            for agent_id, agent_data in agent_results.items():
                extracted_fields = len([v for v in agent_data.get('data', {}).values() if v])
                status = "✅" if extracted_fields > 0 else "⚠️"
                print(f"   {status} {agent_id}: {extracted_fields} fields extracted")

            # Evidence tracking
            evidence_ratio = extraction_data.get('quality_metrics', {}).get('evidence_ratio', 0) * 100
            print(f"\n📄 Evidence Tracking:")
            print(f"   • Evidence Ratio: {evidence_ratio:.1f}%")

            # Performance
            total_time = extraction_data.get('total_time', 0)
            print(f"\n⏱️ Performance:")
            print(f"   • Total Time: {total_time:.1f}s")

            print(f"\n💾 Results saved to: {output_file}")

            # Success criteria
            print("\n" + "="*80)
            print("VALIDATION SUMMARY")
            print("="*80)

            success_criteria = {
                "Coverage > 50%": overall_coverage > 50,
                "At least 5 agents extracting": len([a for a in agent_results.values() if len([v for v in a.get('data', {}).values() if v]) > 0]) >= 5,
                "Evidence ratio > 50%": evidence_ratio > 50,
                "Extraction completed": True
            }

            all_pass = all(success_criteria.values())

            for criterion, passed in success_criteria.items():
                status = "✅" if passed else "❌"
                print(f"{status} {criterion}")

            if all_pass:
                print("\n🎉 ALL VALIDATION CRITERIA PASSED!")
            else:
                print("\n⚠️ Some validation criteria failed")
        else:
            print(f"   ❌ Results file not found: {output_file}")

    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_refactored_optimal_pipeline()
