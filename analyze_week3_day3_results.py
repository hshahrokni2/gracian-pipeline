#!/usr/bin/env python3
"""
Analyze Week 3 Day 3 Comprehensive Test Results
Aggregates results from 33 PDF extractions and generates summary report.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime

def load_extraction_results(results_dir: Path) -> List[Dict]:
    """Load all extraction result JSON files."""
    results = []
    for json_file in sorted(results_dir.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_filename'] = json_file.name
                results.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}", file=sys.stderr)
    return results

def analyze_results(results: List[Dict]) -> Dict[str, Any]:
    """Analyze extraction results and generate statistics."""

    stats = {
        'total_pdfs': len(results),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'coverage_distribution': defaultdict(int),
        'confidence_distribution': defaultdict(int),
        'machine_readable_count': 0,
        'scanned_count': 0,
        'by_dataset': defaultdict(list),
        'component_tests': {
            'extraction_field': {'total': 0, 'passed': 0},
            'synonym_mapping': {'total': 0, 'passed': 0},
            'swedish_first_fields': {'total': 0, 'passed': 0},
            'calculated_metrics': {'total': 0, 'passed': 0}
        },
        'validation_errors': [],
        'top_performers': [],
        'failures': [],
        'coverage_by_field_type': defaultdict(lambda: {'total': 0, 'extracted': 0})
    }

    for result in results:
        # Get metadata
        metadata = result.get('metadata', {})
        quality = result.get('extraction_quality', {})
        coverage = quality.get('coverage_percentage', 0.0)
        confidence = quality.get('confidence_score', 0.5)
        is_readable = metadata.get('is_machine_readable', False)
        file_name = result['_filename']
        dataset = file_name.split('_')[0]  # Hjorthagen or SRS

        # Track by dataset
        stats['by_dataset'][dataset].append({
            'filename': file_name,
            'coverage': coverage,
            'confidence': confidence,
            'is_readable': is_readable
        })

        # Machine readable vs scanned
        if is_readable:
            stats['machine_readable_count'] += 1
        else:
            stats['scanned_count'] += 1

        # Success/failure classification
        if coverage > 0:
            stats['successful_extractions'] += 1
        else:
            stats['failed_extractions'] += 1
            stats['failures'].append({
                'filename': file_name,
                'is_readable': is_readable,
                'reason': 'Zero coverage - extraction failed'
            })

        # Coverage distribution (buckets)
        if coverage == 0:
            bucket = '0%'
        elif coverage < 20:
            bucket = '1-19%'
        elif coverage < 40:
            bucket = '20-39%'
        elif coverage < 60:
            bucket = '40-59%'
        elif coverage < 80:
            bucket = '60-79%'
        else:
            bucket = '80-100%'
        stats['coverage_distribution'][bucket] += 1

        # Confidence distribution
        if confidence < 0.5:
            conf_bucket = '0-0.49'
        elif confidence < 0.7:
            conf_bucket = '0.50-0.69'
        elif confidence < 0.85:
            conf_bucket = '0.70-0.84'
        else:
            conf_bucket = '0.85-1.00'
        stats['confidence_distribution'][conf_bucket] += 1

        # Top performers (coverage >= 70%)
        if coverage >= 70:
            stats['top_performers'].append({
                'filename': file_name,
                'coverage': coverage,
                'confidence': confidence
            })

        # Field-level analysis
        for section_name in ['governance', 'financial', 'property', 'fees', 'operations', 'notes']:
            section_data = result.get(section_name)
            if section_data is not None:
                # Count extracted vs total fields
                stats['coverage_by_field_type'][section_name]['total'] += 1
                if section_data:  # Non-empty section
                    stats['coverage_by_field_type'][section_name]['extracted'] += 1

    # Sort top performers
    stats['top_performers'] = sorted(stats['top_performers'], key=lambda x: x['coverage'], reverse=True)[:10]

    # Calculate averages
    if results:
        total_coverage = sum(r.get('extraction_quality', {}).get('coverage_percentage', 0) for r in results)
        total_confidence = sum(r.get('extraction_quality', {}).get('confidence_score', 0.5) for r in results)
        stats['avg_coverage'] = total_coverage / len(results)
        stats['avg_confidence'] = total_confidence / len(results)

    return stats

def generate_report(stats: Dict[str, Any], output_path: Path):
    """Generate comprehensive markdown report."""

    report = [
        "# Week 3 Day 3: Comprehensive 42-PDF Test Results (Partial)",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Status**: Interrupted by timeout after ~2 hours",
        "",
        "## 🎯 Executive Summary",
        "",
        f"- **PDFs Processed**: {stats['total_pdfs']}/42 (78.6% complete)",
        f"- **Successful Extractions**: {stats['successful_extractions']}/{stats['total_pdfs']} ({stats['successful_extractions']/stats['total_pdfs']*100:.1f}%)",
        f"- **Failed Extractions**: {stats['failed_extractions']}/{stats['total_pdfs']} ({stats['failed_extractions']/stats['total_pdfs']*100:.1f}%)",
        f"- **Average Coverage**: {stats['avg_coverage']:.1f}%",
        f"- **Average Confidence**: {stats['avg_confidence']:.2f}",
        "",
        "### Document Type Distribution",
        "",
        f"- **Machine-Readable PDFs**: {stats['machine_readable_count']}/{stats['total_pdfs']} ({stats['machine_readable_count']/stats['total_pdfs']*100:.1f}%)",
        f"- **Scanned PDFs**: {stats['scanned_count']}/{stats['total_pdfs']} ({stats['scanned_count']/stats['total_pdfs']*100:.1f}%)",
        "",
        "---",
        "",
        "## 📊 Coverage Distribution",
        "",
        "| Coverage Range | Count | Percentage |",
        "|----------------|-------|------------|"
    ]

    for bucket in ['0%', '1-19%', '20-39%', '40-59%', '60-79%', '80-100%']:
        count = stats['coverage_distribution'][bucket]
        pct = (count / stats['total_pdfs'] * 100) if stats['total_pdfs'] > 0 else 0
        report.append(f"| {bucket:14} | {count:5} | {pct:6.1f}% |")

    report.extend([
        "",
        "## 🎯 Confidence Score Distribution",
        "",
        "| Confidence Range | Count | Percentage |",
        "|------------------|-------|------------|"
    ])

    for bucket in ['0-0.49', '0.50-0.69', '0.70-0.84', '0.85-1.00']:
        count = stats['confidence_distribution'][bucket]
        pct = (count / stats['total_pdfs'] * 100) if stats['total_pdfs'] > 0 else 0
        report.append(f"| {bucket:16} | {count:5} | {pct:6.1f}% |")

    report.extend([
        "",
        "## 🏆 Top 10 Performers (Coverage >= 70%)",
        "",
        "| Rank | Filename | Coverage | Confidence |",
        "|------|----------|----------|------------|"
    ])

    for i, perf in enumerate(stats['top_performers'], 1):
        report.append(f"| {i:4} | {perf['filename']:50} | {perf['coverage']:6.1f}% | {perf['confidence']:6.2f} |")

    report.extend([
        "",
        "## ❌ Failed Extractions (0% Coverage)",
        "",
        "| Filename | Type | Reason |",
        "|----------|------|--------|"
    ])

    for failure in stats['failures']:
        doc_type = "Machine-Readable" if failure['is_readable'] else "Scanned"
        report.append(f"| {failure['filename']:50} | {doc_type:16} | {failure['reason']} |")

    report.extend([
        "",
        "## 📁 Results by Dataset",
        ""
    ])

    for dataset, pdfs in sorted(stats['by_dataset'].items()):
        total = len(pdfs)
        avg_coverage = sum(p['coverage'] for p in pdfs) / total if total > 0 else 0
        avg_confidence = sum(p['confidence'] for p in pdfs) / total if total > 0 else 0
        machine_readable = sum(1 for p in pdfs if p['is_readable'])

        report.extend([
            f"### {dataset}",
            "",
            f"- **Total PDFs**: {total}",
            f"- **Average Coverage**: {avg_coverage:.1f}%",
            f"- **Average Confidence**: {avg_confidence:.2f}",
            f"- **Machine-Readable**: {machine_readable}/{total} ({machine_readable/total*100:.1f}%)",
            ""
        ])

    report.extend([
        "## 🔍 Field Type Extraction Rate",
        "",
        "| Field Type | Extracted | Total | Rate |",
        "|------------|-----------|-------|------|"
    ])

    for field_type, counts in sorted(stats['coverage_by_field_type'].items()):
        if counts['total'] > 0:
            rate = counts['extracted'] / counts['total'] * 100
            report.append(f"| {field_type:10} | {counts['extracted']:9} | {counts['total']:5} | {rate:5.1f}% |")

    report.extend([
        "",
        "---",
        "",
        "## 🚧 Known Issues",
        "",
        "### Issue #1: Scanned PDF Extraction Failures",
        "",
        "**Observation**: 2 scanned PDFs show 0% coverage:",
        f"- `Hjorthagen_brf_78906_extraction.json` (is_machine_readable: false)",
        f"- Potentially `SRS_brf_276629_extraction.json` (needs verification)",
        "",
        "**Root Cause**: Likely vision extraction failures or OCR quality issues on deeply scanned documents.",
        "",
        "**Recommendation**: Investigate vision extraction pipeline for these specific PDFs.",
        "",
        "---",
        "",
        "## ✅ Next Steps",
        "",
        "1. **Resume Test Completion** (9 PDFs remaining):",
        "   - Option A: Modify test script to skip completed PDFs",
        "   - Option B: Analyze partial results as-is",
        "",
        "2. **Investigate 0% Coverage PDFs**:",
        "   - Debug vision extraction on brf_78906.pdf",
        "   - Check if OCR quality is the root cause",
        "",
        "3. **Component Test Analysis**:",
        "   - Aggregate ExtractionField functionality tests",
        "   - Aggregate synonym mapping tests",
        "   - Aggregate Swedish-first semantic field tests",
        "   - Aggregate calculated metrics validation tests",
        "",
        f"4. **Generate Final Report** once all 42 PDFs complete",
        "",
        "---",
        "",
        f"**Report Generated**: {datetime.now().isoformat()}",
        f"**Total Processing Time**: ~2 hours (interrupted by timeout)",
        ""
    ])

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"✅ Report generated: {output_path}")

def main():
    """Main execution."""
    results_dir = Path("data/week3_comprehensive_test_results")

    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        sys.exit(1)

    print("📂 Loading extraction results...")
    results = load_extraction_results(results_dir)
    print(f"   ✓ Loaded {len(results)} extraction results")

    print("\n📊 Analyzing results...")
    stats = analyze_results(results)
    print(f"   ✓ Analysis complete")

    print("\n📝 Generating report...")
    output_path = Path("WEEK3_DAY3_PARTIAL_RESULTS.md")
    generate_report(stats, output_path)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total PDFs Processed: {stats['total_pdfs']}/42")
    print(f"Successful: {stats['successful_extractions']} | Failed: {stats['failed_extractions']}")
    print(f"Avg Coverage: {stats['avg_coverage']:.1f}% | Avg Confidence: {stats['avg_confidence']:.2f}")
    print(f"Machine-Readable: {stats['machine_readable_count']} | Scanned: {stats['scanned_count']}")
    print("="*80)

if __name__ == "__main__":
    main()
