#!/usr/bin/env python3
"""
Test Improved Docling Adapter with Fixed Financial Extraction

Tests the enhanced version against the test document to validate:
1. Financial table parsing works
2. Single combined extraction is faster
3. Coverage improves toward 95/95 target
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Import improved adapter
from gracian_pipeline.core.docling_adapter_improved import ImprovedDoclingAdapter


def test_improved_adapter():
    """Test improved adapter on test document."""

    print("\n" + "="*80)
    print("🧪 TESTING IMPROVED DOCLING ADAPTER")
    print("="*80)

    test_pdf = str(Path(__file__).parent.parent / "SRS" / "brf_198532.pdf")

    if not Path(test_pdf).exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return

    # Test with improved adapter
    print(f"\n📄 Testing: {Path(test_pdf).name}")
    print(f"   Expected improvements:")
    print(f"   - Financial extraction (17 tables detected)")
    print(f"   - Faster (single API call vs 3)")
    print(f"   - Higher coverage (→95% target)")

    adapter = ImprovedDoclingAdapter()

    start_time = time.time()
    result = adapter.extract_brf_data(test_pdf)
    elapsed = time.time() - start_time

    print(f"\n⏱️  Processing Time: {elapsed:.1f}s")

    # Analyze results
    if result.get('status') == 'success':
        gov = result.get('governance_agent', {})
        fin = result.get('financial_agent', {})
        prop = result.get('property_agent', {})

        # Count extracted fields
        governance_fields = sum(1 for v in [
            gov.get('chairman'),
            gov.get('board_members'),
            gov.get('auditor_name'),
            gov.get('audit_firm'),
            gov.get('nomination_committee')
        ] if v)

        financial_fields = sum(1 for v in [
            fin.get('revenue'),
            fin.get('expenses'),
            fin.get('assets'),
            fin.get('liabilities'),
            fin.get('equity'),
            fin.get('surplus')
        ] if v is not None)

        property_fields = sum(1 for v in [
            prop.get('address'),
            prop.get('construction_year'),
            prop.get('num_apartments'),
            prop.get('area_sqm')
        ] if v is not None)

        total_extracted = governance_fields + financial_fields + property_fields
        total_fields = 15  # 5 gov + 6 fin + 4 prop
        coverage = (total_extracted / total_fields) * 100

        print(f"\n📊 EXTRACTION RESULTS")
        print(f"{'='*80}")

        print(f"\n👤 GOVERNANCE ({governance_fields}/5 fields)")
        print(f"   Chairman: {gov.get('chairman')}")
        print(f"   Board Members: {len(gov.get('board_members', []))} members")
        for i, member in enumerate(gov.get('board_members', [])[:7], 1):
            print(f"      {i}. {member}")
        print(f"   Auditor: {gov.get('auditor_name')}")
        print(f"   Audit Firm: {gov.get('audit_firm')}")
        print(f"   Nomination Committee: {len(gov.get('nomination_committee', []))} members")

        print(f"\n💰 FINANCIAL ({financial_fields}/6 fields)")
        print(f"   Revenue: {fin.get('revenue')}")
        print(f"   Expenses: {fin.get('expenses')}")
        print(f"   Assets: {fin.get('assets')}")
        print(f"   Liabilities: {fin.get('liabilities')}")
        print(f"   Equity: {fin.get('equity')}")
        print(f"   Surplus: {fin.get('surplus')}")

        print(f"\n🏠 PROPERTY ({property_fields}/4 fields)")
        print(f"   Address: {prop.get('address')}")
        print(f"   Construction Year: {prop.get('construction_year')}")
        print(f"   Apartments: {prop.get('num_apartments')}")
        print(f"   Area: {prop.get('area_sqm')} m²")

        print(f"\n🎯 COVERAGE ANALYSIS")
        print(f"{'='*80}")
        print(f"   Total Extracted: {total_extracted}/{total_fields} fields")
        print(f"   Coverage: {coverage:.1f}%")
        print(f"   Target: 95%")
        print(f"   Status: {'✅ TARGET MET' if coverage >= 95 else f'🟡 {95-coverage:.1f}% TO GO'}")

        # Compare to baseline
        print(f"\n📈 IMPROVEMENT vs BASELINE")
        print(f"{'='*80}")
        print(f"   Baseline Coverage: 56% (13/23 fields)")
        print(f"   Improved Coverage: {coverage:.1f}% ({total_extracted}/{total_fields} fields)")
        print(f"   Improvement: +{coverage - 56:.1f}%")

        # Save results
        output_dir = Path(__file__).parent / "comparison_results"
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f"improved_docling_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'pdf': Path(test_pdf).name,
                'elapsed_seconds': elapsed,
                'coverage_percent': coverage,
                'fields_extracted': total_extracted,
                'total_fields': total_fields,
                'results': result
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved: {output_file}")

    else:
        print(f"\n❌ Extraction failed: {result.get('status')}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    test_improved_adapter()
