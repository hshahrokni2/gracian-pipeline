"""
Week 3 Day 5: SRS Dataset Coverage Gap Analysis

Phase 1 Diagnostic: Compare SRS vs Hjorthagen PDFs
- Docling heading analysis
- Field coverage patterns
- Document structure comparison
"""

import sys
import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify API key
if not os.getenv('OPENAI_API_KEY'):
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter

# PDFs to analyze (3 low SRS + 3 high Hjorthagen)
LOW_SRS_PDFS = [
    "SRS/brf_76536.pdf",   # 0.0% coverage (worst)
    "SRS/brf_43334.pdf",   # 6.8% coverage
    "SRS/brf_78906.pdf",   # 6.0% coverage
]

HIGH_HJORTHAGEN_PDFS = [
    "Hjorthagen/brf_81563.pdf",  # 98.3% coverage (best)
    "Hjorthagen/brf_268411.pdf", # 70.1% coverage
    "Hjorthagen/brf_271949.pdf", # 81.2% coverage
]

def analyze_pdf_structure(pdf_path: str) -> dict:
    """Extract Docling structure from a PDF."""
    print(f"\n📄 Analyzing: {Path(pdf_path).name}")

    adapter = UltraComprehensiveDoclingAdapter()

    try:
        result = adapter.extract_with_docling(pdf_path)

        # Extract sections
        sections = result.get('sections', [])
        section_headings = [s.get('heading', '') for s in sections if s.get('heading')]

        # Extract tables
        tables = result.get('tables', [])

        # Count pages
        num_pages = result.get('num_pages', 0)

        # Get markdown length as proxy for content
        markdown_length = len(result.get('markdown', ''))

        analysis = {
            'pdf': Path(pdf_path).name,
            'num_sections': len(sections),
            'section_headings': section_headings[:20],  # First 20 headings
            'num_tables': len(tables),
            'num_pages': num_pages,
            'markdown_length': markdown_length,
            'avg_section_length': markdown_length / len(sections) if sections else 0
        }

        print(f"  ✓ Sections: {len(sections)}")
        print(f"  ✓ Tables: {len(tables)}")
        print(f"  ✓ Pages: {num_pages}")
        print(f"  ✓ First 5 headings:")
        for i, heading in enumerate(section_headings[:5], 1):
            print(f"    {i}. {heading}")

        return analysis

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            'pdf': Path(pdf_path).name,
            'error': str(e)
        }


def compare_heading_patterns(srs_analyses: list, hjorthagen_analyses: list):
    """Compare section heading patterns between datasets."""
    print("\n" + "=" * 80)
    print("📊 HEADING PATTERN COMPARISON")
    print("=" * 80)

    # Collect all headings
    srs_headings = []
    hjorthagen_headings = []

    for analysis in srs_analyses:
        if 'section_headings' in analysis:
            srs_headings.extend(analysis['section_headings'])

    for analysis in hjorthagen_analyses:
        if 'section_headings' in analysis:
            hjorthagen_headings.extend(analysis['section_headings'])

    # Count frequencies
    srs_counter = Counter(srs_headings)
    hjorthagen_counter = Counter(hjorthagen_headings)

    print(f"\n🔴 SRS Most Common Headings (top 15):")
    for heading, count in srs_counter.most_common(15):
        print(f"  {count}x: {heading}")

    print(f"\n🟢 Hjorthagen Most Common Headings (top 15):")
    for heading, count in hjorthagen_counter.most_common(15):
        print(f"  {count}x: {heading}")

    # Find unique headings
    srs_unique = set(srs_headings) - set(hjorthagen_headings)
    hjorthagen_unique = set(hjorthagen_headings) - set(srs_headings)

    print(f"\n⚠️  Headings UNIQUE to SRS ({len(srs_unique)}):")
    for heading in sorted(list(srs_unique))[:10]:
        print(f"  - {heading}")

    print(f"\n⚠️  Headings UNIQUE to Hjorthagen ({len(hjorthagen_unique)}):")
    for heading in sorted(list(hjorthagen_unique))[:10]:
        print(f"  - {heading}")

    # Calculate overlap
    overlap = set(srs_headings) & set(hjorthagen_headings)
    overlap_pct = len(overlap) / len(set(srs_headings + hjorthagen_headings)) * 100

    print(f"\n📊 Heading Overlap: {len(overlap)} headings ({overlap_pct:.1f}%)")

    return {
        'srs_headings': srs_counter,
        'hjorthagen_headings': hjorthagen_counter,
        'srs_unique': list(srs_unique),
        'hjorthagen_unique': list(hjorthagen_unique),
        'overlap': list(overlap),
        'overlap_percentage': overlap_pct
    }


def analyze_structure_metrics(srs_analyses: list, hjorthagen_analyses: list):
    """Compare structural metrics between datasets."""
    print("\n" + "=" * 80)
    print("📊 STRUCTURAL METRICS COMPARISON")
    print("=" * 80)

    # Calculate averages
    srs_sections = [a['num_sections'] for a in srs_analyses if 'num_sections' in a]
    srs_tables = [a['num_tables'] for a in srs_analyses if 'num_tables' in a]
    srs_pages = [a['num_pages'] for a in srs_analyses if 'num_pages' in a]

    hjorthagen_sections = [a['num_sections'] for a in hjorthagen_analyses if 'num_sections' in a]
    hjorthagen_tables = [a['num_tables'] for a in hjorthagen_analyses if 'num_tables' in a]
    hjorthagen_pages = [a['num_pages'] for a in hjorthagen_analyses if 'num_pages' in a]

    print(f"\n{'Metric':<20} {'SRS (low)':<15} {'Hjorthagen (high)':<20} {'Difference'}")
    print("-" * 80)

    if srs_sections and hjorthagen_sections:
        srs_avg_sections = sum(srs_sections) / len(srs_sections)
        hj_avg_sections = sum(hjorthagen_sections) / len(hjorthagen_sections)
        diff_sections = hj_avg_sections - srs_avg_sections
        print(f"{'Sections/PDF':<20} {srs_avg_sections:<15.1f} {hj_avg_sections:<20.1f} {diff_sections:+.1f}")

    if srs_tables and hjorthagen_tables:
        srs_avg_tables = sum(srs_tables) / len(srs_tables)
        hj_avg_tables = sum(hjorthagen_tables) / len(hjorthagen_tables)
        diff_tables = hj_avg_tables - srs_avg_tables
        print(f"{'Tables/PDF':<20} {srs_avg_tables:<15.1f} {hj_avg_tables:<20.1f} {diff_tables:+.1f}")

    if srs_pages and hjorthagen_pages:
        srs_avg_pages = sum(srs_pages) / len(srs_pages)
        hj_avg_pages = sum(hjorthagen_pages) / len(hjorthagen_pages)
        diff_pages = hj_avg_pages - srs_avg_pages
        print(f"{'Pages/PDF':<20} {srs_avg_pages:<15.1f} {hj_avg_pages:<20.1f} {diff_pages:+.1f}")

    return {
        'srs_avg_sections': sum(srs_sections) / len(srs_sections) if srs_sections else 0,
        'hjorthagen_avg_sections': sum(hjorthagen_sections) / len(hjorthagen_sections) if hjorthagen_sections else 0,
        'srs_avg_tables': sum(srs_tables) / len(srs_tables) if srs_tables else 0,
        'hjorthagen_avg_tables': sum(hjorthagen_tables) / len(hjorthagen_tables) if hjorthagen_tables else 0,
    }


def load_coverage_data():
    """Load Week 3 Day 3 test results to compare field coverage."""
    print("\n" + "=" * 80)
    print("📊 FIELD COVERAGE ANALYSIS")
    print("=" * 80)

    summary_path = Path("data/week3_comprehensive_test_results/comprehensive_test_summary.json")

    if not summary_path.exists():
        print("  ⚠️  Summary file not found")
        return None

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    print(f"\n🔴 SRS Dataset:")
    print(f"  PDFs: {summary['by_dataset']['SRS']['count']}")
    print(f"  Success: {summary['by_dataset']['SRS']['successful']}/{summary['by_dataset']['SRS']['count']}")
    print(f"  Avg Coverage: {summary['by_dataset']['SRS']['avg_coverage']:.1f}%")
    print(f"  Avg Confidence: {summary['by_dataset']['SRS']['avg_confidence']:.2f}")

    print(f"\n🟢 Hjorthagen Dataset:")
    print(f"  PDFs: {summary['by_dataset']['Hjorthagen']['count']}")
    print(f"  Success: {summary['by_dataset']['Hjorthagen']['successful']}/{summary['by_dataset']['Hjorthagen']['count']}")
    print(f"  Avg Coverage: {summary['by_dataset']['Hjorthagen']['avg_coverage']:.1f}%")
    print(f"  Avg Confidence: {summary['by_dataset']['Hjorthagen']['avg_confidence']:.2f}")

    gap = summary['by_dataset']['Hjorthagen']['avg_coverage'] - summary['by_dataset']['SRS']['avg_coverage']
    print(f"\n⚠️  Coverage Gap: {gap:.1f} percentage points")

    return summary


def main():
    """Run Phase 1 diagnostic analysis."""
    print("=" * 80)
    print("🔬 WEEK 3 DAY 5: PHASE 1 DIAGNOSTIC")
    print("SRS Dataset Coverage Gap Analysis")
    print("=" * 80)

    # Step 1: Analyze low SRS PDFs
    print("\n" + "=" * 80)
    print("🔴 ANALYZING LOW-PERFORMING SRS PDFs")
    print("=" * 80)

    srs_analyses = []
    for pdf in LOW_SRS_PDFS:
        analysis = analyze_pdf_structure(pdf)
        srs_analyses.append(analysis)

    # Step 2: Analyze high Hjorthagen PDFs
    print("\n" + "=" * 80)
    print("🟢 ANALYZING HIGH-PERFORMING HJORTHAGEN PDFs")
    print("=" * 80)

    hjorthagen_analyses = []
    for pdf in HIGH_HJORTHAGEN_PDFS:
        analysis = analyze_pdf_structure(pdf)
        hjorthagen_analyses.append(analysis)

    # Step 3: Compare heading patterns
    heading_comparison = compare_heading_patterns(srs_analyses, hjorthagen_analyses)

    # Step 4: Compare structural metrics
    structure_metrics = analyze_structure_metrics(srs_analyses, hjorthagen_analyses)

    # Step 5: Load coverage data
    coverage_data = load_coverage_data()

    # Step 6: Generate diagnostic report
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 80)

    # Save full results
    results = {
        'srs_analyses': srs_analyses,
        'hjorthagen_analyses': hjorthagen_analyses,
        'heading_comparison': {
            'srs_unique': heading_comparison['srs_unique'],
            'hjorthagen_unique': heading_comparison['hjorthagen_unique'],
            'overlap_percentage': heading_comparison['overlap_percentage']
        },
        'structure_metrics': structure_metrics,
        'coverage_summary': coverage_data
    }

    output_path = Path("data/srs_diagnostic_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Full results saved to: {output_path}")

    # Print key findings
    print("\n🔍 KEY FINDINGS:")
    print(f"  1. Heading overlap: {heading_comparison['overlap_percentage']:.1f}%")
    print(f"  2. SRS unique headings: {len(heading_comparison['srs_unique'])}")
    print(f"  3. Hjorthagen unique headings: {len(heading_comparison['hjorthagen_unique'])}")
    print(f"  4. Coverage gap: {gap:.1f} percentage points" if coverage_data else "")

    print("\n🎯 NEXT STEPS:")
    if heading_comparison['overlap_percentage'] < 70:
        print("  ⚠️  LOW HEADING OVERLAP → Hypothesis 1: Document structure differences")
        print("  → Recommended fix: Update agent routing with SRS-specific headings")
    elif len(heading_comparison['srs_unique']) > 20:
        print("  ⚠️  MANY SRS-SPECIFIC HEADINGS → Hypothesis 1: Routing mismatch")
        print("  → Recommended fix: Expand synonym mapping for SRS terms")
    else:
        print("  ✅ HEADING OVERLAP ACCEPTABLE")
        print("  → Likely Hypothesis 3: Multi-source aggregation needed")
        print("  → Recommended fix: Implement cross-section field merging")

    print("\n" + "=" * 80)
    print("✅ PHASE 1 DIAGNOSTIC COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    results = main()
