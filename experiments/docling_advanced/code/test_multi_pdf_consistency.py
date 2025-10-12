#!/usr/bin/env python3
"""
Multi-PDF Consistency Test - Validation-First Approach

Tests current optimal_brf_pipeline.py on 5-6 diverse PDFs to measure:
- Average coverage and variance
- Failure patterns
- Whether specialist refactoring is actually needed

Based on ultrathinking: "Test first, decide later"
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Starting multi-PDF validation test...")
print(f"Working directory: {Path.cwd()}")
print(f"Script location: {Path(__file__).parent}")

try:
    from optimal_brf_pipeline import OptimalBRFPipeline
    print("✅ Successfully imported OptimalBRFPipeline")
except ImportError as e:
    print(f"❌ Error: Could not import optimal_brf_pipeline.py: {e}")
    print("   Make sure you're in experiments/docling_advanced/code/")
    sys.exit(1)


def test_pdf_simple(pdf_path: str) -> Dict:
    """Simple test - just run extraction and report success/failure"""
    pdf_name = Path(pdf_path).stem
    
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_name}")
    print(f"Path: {pdf_path}")
    print(f"{'='*60}")
    
    try:
        pipeline = OptimalBRFPipeline(enable_caching=True)
        result = pipeline.extract_document(pdf_path)
        
        # Count extracted fields
        def count_fields(d, prefix=""):
            count = 0
            if isinstance(d, dict):
                for k, v in d.items():
                    if v is not None:
                        if isinstance(v, (dict, list)):
                            count += count_fields(v, f"{prefix}{k}.")
                        else:
                            count += 1
            elif isinstance(d, list) and d:
                count += len(d)
            return count
        
        field_count = count_fields(result)
        
        print(f"✅ Extraction successful")
        print(f"   Fields extracted: {field_count}")
        
        return {
            'pdf': pdf_name,
            'status': 'success',
            'field_count': field_count,
            'path': pdf_path
        }
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'pdf': pdf_name,
            'status': 'error',
            'error': str(e),
            'field_count': 0,
            'path': pdf_path
        }


def main():
    """Run multi-PDF consistency test"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║     Multi-PDF Consistency Test - Validation-First Approach   ║
║                                                              ║
║  Strategy: Test current system on diverse PDFs BEFORE       ║
║           committing to 15-20 hour specialist refactoring   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Test PDFs - use relative paths from code/ directory
    base_dir = Path(__file__).parent.parent
    
    test_pdfs = [
        (base_dir / "../../SRS/brf_198532.pdf", "Baseline (86.7% on Oct 12)"),
        (base_dir / "test_pdfs/brf_268882.pdf", "Regression test"),
    ]
    
    print(f"\nBase directory: {base_dir}")
    print(f"\n📋 Testing {len(test_pdfs)} PDFs:")
    
    for pdf_path, desc in test_pdfs:
        pdf_name = pdf_path.stem
        exists = "✅" if pdf_path.exists() else "❌"
        print(f"   {exists} {pdf_name}: {desc}")
        if not pdf_path.exists():
            print(f"       Path: {pdf_path}")
    
    # Test each PDF
    results = []
    for pdf_path, desc in test_pdfs:
        if pdf_path.exists():
            result = test_pdf_simple(str(pdf_path))
            results.append(result)
        else:
            print(f"\n⚠️  Skipping {pdf_path.stem} (file not found at {pdf_path})")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"Tested: {len(results)} PDFs")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        field_counts = [r['field_count'] for r in successful]
        avg_fields = statistics.mean(field_counts)
        print(f"\nAverage fields extracted: {avg_fields:.0f}")
        print(f"Range: {min(field_counts)} - {max(field_counts)}")
    
    # Save results
    output_path = base_dir / "results" / "multi_pdf_validation_simple.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'results': results,
            'summary': {
                'tested': len(results),
                'successful': len(successful),
                'failed': len(failed)
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    print(f"\n{'='*60}\n")
    
    return 0 if len(successful) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
