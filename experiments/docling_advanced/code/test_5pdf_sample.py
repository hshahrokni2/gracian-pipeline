#!/usr/bin/env python3
"""
Test integrated pipeline on 5-PDF sample (strategic sample mixing machine-readable and scanned).

Test Documents (from existing test_pdfs):
- brf_268882.pdf (28 pages, scanned, 11 tables)
- brf_271852.pdf
- brf_276507.pdf

Usage:
    python3 code/test_5pdf_sample.py
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from integrated_brf_pipeline import IntegratedBRFPipeline, EnhancedExtractionResult


def print_section(title: str):
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def test_pdf(pipeline: IntegratedBRFPipeline, pdf_path: str, test_num: int) -> Dict[str, Any]:
    """Test a single PDF and return metrics"""
    print_section(f"TEST {test_num}: {Path(pdf_path).name}")

    try:
        start_time = time.time()
        result = pipeline.extract_document(pdf_path)
        elapsed = time.time() - start_time

        # Print summary
        print(f"\n✅ Extraction completed in {elapsed:.1f}s")
        print(f"   Total Pipeline Time: {result.total_time:.1f}s")
        print(f"   Total Cost: ${result.total_cost:.4f}")
        print(f"   Coverage: {result.quality_metrics.get('coverage', 0)*100:.1f}%")
        print(f"   Overall Score: {result.quality_metrics.get('overall_score', 0)*100:.1f}%")

        # Component status
        m = result.integration_metrics
        print(f"\n🔧 Component Status:")
        print(f"   1. Structure Detection: {'✅' if m.structure_detection_success else '❌'}")
        print(f"   2. Context Manager: {'✅' if m.context_manager_success else '⏭️  Skipped'}")
        print(f"   3. Data Linking: {'✅' if m.data_linking_success else '⏭️  Skipped'}")
        print(f"   4. Validation: {'✅' if m.validation_success else '⏭️  Skipped'}")
        print(f"   5. Dictionary: {m.dictionary_lookups} lookups, {m.dictionary_hits} hits")

        return {
            "pdf": Path(pdf_path).name,
            "success": True,
            "total_time": result.total_time,
            "total_cost": result.total_cost,
            "coverage": result.quality_metrics.get('coverage', 0),
            "overall_score": result.quality_metrics.get('overall_score', 0),
            "components": {
                "structure_detection": m.structure_detection_success,
                "context_manager": m.context_manager_success,
                "data_linking": m.data_linking_success,
                "validation": m.validation_success
            },
            "sections_detected": getattr(result, 'structure_sections', 0),
            "tables_detected": getattr(result, 'structure_tables', 0),
            "agents_used": len(getattr(result, 'agents_used', []))
        }

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "pdf": Path(pdf_path).name,
            "success": False,
            "error": str(e)
        }


def main():
    """Run 5-PDF sample test"""
    print_section("5-PDF SAMPLE TEST - INTEGRATED BRF PIPELINE")

    # Test PDFs (3 available, will test all 3)
    test_pdfs = [
        "test_pdfs/brf_268882.pdf",  # Already tested: 28 pages, scanned, 11 tables
        "test_pdfs/brf_271852.pdf",  # Unknown topology
        "test_pdfs/brf_276507.pdf",  # Unknown topology
    ]

    # Initialize pipeline (fast mode for speed)
    print("\n🚀 Initializing IntegratedBRFPipeline (fast mode)")
    pipeline = IntegratedBRFPipeline(mode='fast')

    # Test each PDF
    results = []
    total_start_time = time.time()

    for i, pdf_path in enumerate(test_pdfs, 1):
        if not Path(pdf_path).exists():
            print(f"\n⚠️  PDF {i} not found: {pdf_path}")
            continue

        result = test_pdf(pipeline, pdf_path, i)
        results.append(result)

        # Small delay between tests
        if i < len(test_pdfs):
            time.sleep(2)

    total_elapsed = time.time() - total_start_time

    # Aggregate results
    print_section("AGGREGATE RESULTS")

    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', True)]

    print(f"\n📊 Summary:")
    print(f"   Total PDFs: {len(results)}")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed: {len(failed)}")
    print(f"   Total Time: {total_elapsed:.1f}s")
    print(f"   Avg Time per PDF: {total_elapsed/len(results):.1f}s")

    if successful:
        avg_coverage = sum(r['coverage'] for r in successful) / len(successful)
        avg_score = sum(r['overall_score'] for r in successful) / len(successful)
        avg_cost = sum(r['total_cost'] for r in successful) / len(successful)

        print(f"\n📈 Quality Metrics (Successful Extractions):")
        print(f"   Avg Coverage: {avg_coverage*100:.1f}%")
        print(f"   Avg Overall Score: {avg_score*100:.1f}%")
        print(f"   Avg Cost: ${avg_cost:.4f}")

        # Component success rates
        structure_success = sum(1 for r in successful if r['components']['structure_detection'])
        context_success = sum(1 for r in successful if r['components']['context_manager'])
        linking_success = sum(1 for r in successful if r['components']['data_linking'])
        validation_success = sum(1 for r in successful if r['components']['validation'])

        print(f"\n🔧 Component Success Rates:")
        print(f"   Structure Detection: {structure_success}/{len(successful)} ({structure_success/len(successful)*100:.0f}%)")
        print(f"   Context Manager: {context_success}/{len(successful)} ({context_success/len(successful)*100:.0f}%)")
        print(f"   Data Linking: {linking_success}/{len(successful)} ({linking_success/len(successful)*100:.0f}%)")
        print(f"   Validation: {validation_success}/{len(successful)} ({validation_success/len(successful)*100:.0f}%)")

    # Save results
    output_dir = Path("results/5pdf_sample")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"5pdf_sample_results_{timestamp}.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "mode": "fast",
            "total_pdfs": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_time": total_elapsed,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to: {results_file}")

    print_section("TEST COMPLETE")

    # Exit with appropriate code
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
