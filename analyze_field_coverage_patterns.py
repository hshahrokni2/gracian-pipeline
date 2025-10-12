"""
Week 3 Day 5: Field-Level Coverage Analysis

Analyze existing test results to compare SRS vs Hjorthagen field extraction patterns
"""

import json
from pathlib import Path
from collections import defaultdict, Counter

# Load test results
results_dir = Path("data/week3_comprehensive_test_results")

def load_test_results():
    """Load all Week 3 Day 3 test results."""
    srs_results = []
    hjorthagen_results = []

    for json_file in results_dir.glob("*_extraction.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)

        if 'SRS_' in json_file.name:
            srs_results.append({
                'filename': json_file.name,
                'data': data
            })
        elif 'Hjorthagen_' in json_file.name:
            hjorthagen_results.append({
                'filename': json_file.name,
                'data': data
            })

    return srs_results, hjorthagen_results


def analyze_field_presence(results, dataset_name):
    """Analyze which fields are present/missing across a dataset."""
    print(f"\n📊 {dataset_name} Field Presence Analysis")
    print("=" * 80)

    field_counts = defaultdict(int)
    total_pdfs = len(results)

    for result in results:
        data = result['data']

        # Recursively find all non-null fields
        def count_fields(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('_'):
                        continue  # Skip metadata fields
                    full_key = f"{prefix}.{key}" if prefix else key
                    if value is not None and value != "" and value != []:
                        field_counts[full_key] += 1
                    if isinstance(value, (dict, list)):
                        count_fields(value, full_key)
            elif isinstance(obj, list):
                for item in obj:
                    count_fields(item, prefix)

        count_fields(data)

    # Sort by presence rate
    sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 20 Most Extracted Fields:")
    print(f"{'Field':<50} {'Count':<10} {'Rate'}")
    print("-" * 80)
    for field, count in sorted_fields[:20]:
        rate = count / total_pdfs * 100
        print(f"{field:<50} {count:<10} {rate:>6.1f}%")

    print(f"\nBottom 20 Least Extracted Fields:")
    print(f"{'Field':<50} {'Count':<10} {'Rate'}")
    print("-" * 80)
    for field, count in sorted_fields[-20:]:
        rate = count / total_pdfs * 100
        print(f"{field:<50} {count:<10} {rate:>6.1f}%")

    return field_counts


def compare_datasets(srs_fields, hjorthagen_fields, srs_count, hjorthagen_count):
    """Compare field extraction rates between datasets."""
    print("\n" + "=" * 80)
    print("🔍 DATASET COMPARISON: Fields with Largest Gaps")
    print("=" * 80)

    # Calculate rates
    srs_rates = {field: count/srs_count*100 for field, count in srs_fields.items()}
    hjorthagen_rates = {field: count/hjorthagen_count*100 for field, count in hjorthagen_fields.items()}

    # Find all unique fields
    all_fields = set(list(srs_rates.keys()) + list(hjorthagen_rates.keys()))

    # Calculate gaps
    gaps = []
    for field in all_fields:
        srs_rate = srs_rates.get(field, 0)
        hj_rate = hjorthagen_rates.get(field, 0)
        gap = hj_rate - srs_rate
        gaps.append((field, srs_rate, hj_rate, gap))

    # Sort by gap size (Hjorthagen better than SRS)
    gaps_sorted = sorted(gaps, key=lambda x: abs(x[3]), reverse=True)

    print(f"\nFields WHERE HJORTHAGEN SIGNIFICANTLY BETTER (top 15):")
    print(f"{'Field':<45} {'SRS Rate':<12} {'Hj Rate':<12} {'Gap'}")
    print("-" * 80)
    hj_better = [g for g in gaps_sorted if g[3] > 10]  # Hjorthagen better by 10%+
    for field, srs_rate, hj_rate, gap in hj_better[:15]:
        print(f"{field:<45} {srs_rate:>10.1f}% {hj_rate:>10.1f}% {gap:>+7.1f}%")

    print(f"\nFields WHERE SRS SIGNIFICANTLY BETTER (top 10):")
    print(f"{'Field':<45} {'SRS Rate':<12} {'Hj Rate':<12} {'Gap'}")
    print("-" * 80)
    srs_better = [g for g in gaps_sorted if g[3] < -10]  # SRS better by 10%+
    for field, srs_rate, hj_rate, gap in srs_better[:10]:
        print(f"{field:<45} {srs_rate:>10.1f}% {hj_rate:>10.1f}% {gap:>+7.1f}%")

    return gaps_sorted


def analyze_low_performers(srs_results):
    """Deep dive on lowest performing SRS PDFs."""
    print("\n" + "=" * 80)
    print("🔍 LOW PERFORMER ANALYSIS (Bottom 5 SRS PDFs)")
    print("=" * 80)

    # Calculate coverage for each PDF
    coverages = []
    for result in srs_results:
        data = result['data']
        coverage = data.get('_quality_metrics', {}).get('coverage_percentage', 0)
        coverage_pct = data.get('coverage_percentage', coverage)  # Try both locations
        coverages.append((result['filename'], coverage_pct, data))

    # Sort by coverage
    coverages_sorted = sorted(coverages, key=lambda x: x[1])

    print(f"\nLowest 5 Performers:")
    for filename, coverage, data in coverages_sorted[:5]:
        brf_id = filename.replace('SRS_brf_', '').replace('_extraction.json', '')
        print(f"\n  📄 {brf_id}: {coverage:.1f}% coverage")

        # Count extracted fields
        field_count = 0
        def count_non_null(obj):
            nonlocal field_count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('_'):
                        continue
                    if value is not None and value != "" and value != []:
                        field_count += 1
                    if isinstance(value, (dict, list)):
                        count_non_null(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_non_null(item)

        count_non_null(data)
        print(f"     Fields extracted: {field_count}")

        # Check for common failure patterns
        metadata = data.get('metadata', {}) or {}
        financial = data.get('financial', {}) or {}
        governance = data.get('governance', {}) or {}

        print(f"     Metadata fields: {sum(1 for v in metadata.values() if v)}")
        print(f"     Financial fields: {sum(1 for v in financial.values() if v if not isinstance(v, dict))}")
        print(f"     Governance fields: {sum(1 for v in governance.values() if v if not isinstance(v, dict))}")


def main():
    """Run field-level coverage analysis."""
    print("=" * 80)
    print("🔬 WEEK 3 DAY 5: FIELD-LEVEL COVERAGE ANALYSIS")
    print("=" * 80)

    # Load results
    print("\n📁 Loading test results...")
    srs_results, hjorthagen_results = load_test_results()

    print(f"  ✓ SRS results: {len(srs_results)} PDFs")
    print(f"  ✓ Hjorthagen results: {len(hjorthagen_results)} PDFs")

    # Analyze field presence
    srs_fields = analyze_field_presence(srs_results, "SRS")
    hjorthagen_fields = analyze_field_presence(hjorthagen_results, "HJORTHAGEN")

    # Compare datasets
    gaps = compare_datasets(srs_fields, hjorthagen_fields, len(srs_results), len(hjorthagen_results))

    # Analyze low performers
    analyze_low_performers(srs_results)

    # Save results
    analysis = {
        'srs_field_counts': dict(srs_fields),
        'hjorthagen_field_counts': dict(hjorthagen_fields),
        'gaps': [
            {'field': f, 'srs_rate': s, 'hjorthagen_rate': h, 'gap': g}
            for f, s, h, g in gaps
        ]
    }

    output_path = Path("data/field_coverage_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"\n✅ Analysis saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 80)

    hj_better = [g for g in gaps if g[3] > 10]
    print(f"\n  Fields where Hjorthagen is significantly better: {len(hj_better)}")

    if hj_better:
        print(f"\n  🔍 TOP 3 PROBLEM AREAS:")
        for field, srs_rate, hj_rate, gap in hj_better[:3]:
            print(f"     - {field}: {gap:+.1f}% gap ({srs_rate:.1f}% SRS vs {hj_rate:.1f}% Hj)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
