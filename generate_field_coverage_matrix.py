#!/usr/bin/env python3
"""
Field Coverage Matrix Generator
Analyzes all extraction JSONs to identify which fields are missing across PDFs
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
import sys

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Recursively flatten nested dictionary into dot-notation keys"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # For lists, check if any item exists
            if v:  # Non-empty list
                items.append((new_key, True))
                # If list contains dicts, flatten first item as representative
                if v and isinstance(v[0], dict):
                    items.extend(flatten_dict(v[0], f"{new_key}[0]", sep=sep).items())
            else:
                items.append((new_key, False))
        else:
            # Field has value if not None and not empty string
            has_value = v is not None and v != ""
            items.append((new_key, has_value))

    return dict(items)

def analyze_extraction_file(filepath: Path) -> Dict[str, bool]:
    """Analyze single extraction JSON and return field presence map"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Flatten the data structure
        flat_data = flatten_dict(data)

        return flat_data
    except Exception as e:
        print(f"⚠️  Error reading {filepath.name}: {e}", file=sys.stderr)
        return {}

def generate_coverage_matrix():
    """Generate complete field coverage matrix across all extraction JSONs"""

    results_dir = Path("data/week3_comprehensive_test_results")

    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return

    # Get all JSON files (excluding comprehensive_test_summary.json)
    json_files = [f for f in results_dir.glob("*.json")
                  if f.name != "comprehensive_test_summary.json"]

    if not json_files:
        print(f"❌ No extraction JSON files found in {results_dir}")
        return

    print(f"📁 Found {len(json_files)} extraction files")
    print(f"🔍 Analyzing field coverage...\n")

    # Collect all field data
    field_coverage: Dict[str, List[bool]] = defaultdict(list)
    pdf_names: List[str] = []
    all_fields: Set[str] = set()

    for json_file in sorted(json_files):
        pdf_name = json_file.stem.replace("_extraction", "")
        pdf_names.append(pdf_name)

        field_map = analyze_extraction_file(json_file)

        # Collect all unique fields
        all_fields.update(field_map.keys())

        # Store coverage for this PDF
        for field, has_value in field_map.items():
            field_coverage[field].append(has_value)

    # Normalize: ensure all fields have entries for all PDFs
    for field in all_fields:
        while len(field_coverage[field]) < len(pdf_names):
            field_coverage[field].append(False)

    # Calculate statistics
    field_stats = []
    for field, coverage_list in field_coverage.items():
        total_pdfs = len(coverage_list)
        filled_count = sum(coverage_list)
        coverage_pct = (filled_count / total_pdfs * 100) if total_pdfs > 0 else 0

        field_stats.append({
            'field': field,
            'filled': filled_count,
            'total': total_pdfs,
            'coverage': coverage_pct,
            'missing': total_pdfs - filled_count
        })

    # Sort by coverage (ascending) to show most-missing fields first
    field_stats.sort(key=lambda x: (x['coverage'], x['field']))

    # Generate report
    report_lines = [
        "# Field Coverage Matrix Report",
        "",
        f"**Generated**: {Path.cwd().name}",
        f"**Total PDFs Analyzed**: {len(pdf_names)}",
        f"**Total Unique Fields**: {len(all_fields)}",
        "",
        "---",
        "",
        "## 📊 Summary Statistics",
        "",
        f"- **Fields with 100% coverage**: {sum(1 for s in field_stats if s['coverage'] == 100)}",
        f"- **Fields with 80-99% coverage**: {sum(1 for s in field_stats if 80 <= s['coverage'] < 100)}",
        f"- **Fields with 50-79% coverage**: {sum(1 for s in field_stats if 50 <= s['coverage'] < 80)}",
        f"- **Fields with 1-49% coverage**: {sum(1 for s in field_stats if 0 < s['coverage'] < 50)}",
        f"- **Fields with 0% coverage**: {sum(1 for s in field_stats if s['coverage'] == 0)}",
        "",
        "---",
        "",
        "## 🎯 Top 30 Most Missing Fields (Prioritized for Fixing)",
        "",
        "| Rank | Field | Coverage | Filled | Missing | Fix Priority |",
        "|------|-------|----------|--------|---------|--------------|"
    ]

    # Top 30 most missing fields
    for idx, stat in enumerate(field_stats[:30], 1):
        # Determine fix priority based on field name patterns
        field_name = stat['field']

        if any(kw in field_name.lower() for kw in ['metadata', 'document_id', 'fiscal_year', 'brf_name']):
            priority = "🔴 CRITICAL"
        elif any(kw in field_name.lower() for kw in ['governance', 'board', 'chairman', 'auditor']):
            priority = "🟠 HIGH"
        elif any(kw in field_name.lower() for kw in ['financial', 'balance', 'income', 'equity']):
            priority = "🟡 MEDIUM"
        elif any(kw in field_name.lower() for kw in ['_quality', 'extraction_metadata']):
            priority = "🔵 LOW (System)"
        else:
            priority = "⚪ STANDARD"

        report_lines.append(
            f"| {idx:2d} | `{field_name[:60]}` | {stat['coverage']:.1f}% | "
            f"{stat['filled']}/{stat['total']} | {stat['missing']} | {priority} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 📈 Fields by Coverage Range",
        "",
        "### 100% Coverage (Always Present)",
        ""
    ])

    perfect_fields = [s for s in field_stats if s['coverage'] == 100]
    if perfect_fields:
        report_lines.append("| Field | Filled |")
        report_lines.append("|-------|--------|")
        for stat in perfect_fields:
            report_lines.append(f"| `{stat['field']}` | {stat['filled']}/{stat['total']} |")
    else:
        report_lines.append("*No fields with 100% coverage*")

    report_lines.extend([
        "",
        "### 80-99% Coverage (Nearly Complete)",
        ""
    ])

    high_fields = [s for s in field_stats if 80 <= s['coverage'] < 100]
    if high_fields:
        report_lines.append("| Field | Coverage | Filled | Missing |")
        report_lines.append("|-------|----------|--------|---------|")
        for stat in high_fields:
            report_lines.append(
                f"| `{stat['field'][:50]}` | {stat['coverage']:.1f}% | "
                f"{stat['filled']}/{stat['total']} | {stat['missing']} |"
            )
    else:
        report_lines.append("*No fields in this range*")

    report_lines.extend([
        "",
        "### 0% Coverage (Never Present)",
        ""
    ])

    zero_fields = [s for s in field_stats if s['coverage'] == 0]
    if zero_fields:
        report_lines.append("| Field | Status |")
        report_lines.append("|-------|--------|")
        for stat in zero_fields[:20]:  # Limit to 20 for readability
            report_lines.append(f"| `{stat['field'][:60]}` | Never extracted |")
        if len(zero_fields) > 20:
            report_lines.append(f"| ... and {len(zero_fields) - 20} more | ... |")
    else:
        report_lines.append("*No fields with 0% coverage*")

    report_lines.extend([
        "",
        "---",
        "",
        "## 🔧 Fix Strategy Recommendations",
        "",
        "### Tier 1: Quick Wins (Estimated 2-3 hours)",
        "**Target**: Fields with 50-80% coverage (likely prompt/extraction logic issues)",
        "",
        "```python",
        "# Example fix categories:",
        "# 1. Add missing synonyms to Swedish term dictionaries",
        "# 2. Adjust confidence thresholds for semantic matching",
        "# 3. Add fallback patterns for common field locations",
        "```",
        "",
        "### Tier 2: Moderate Improvements (Estimated 4-5 hours)",
        "**Target**: Fields with 20-50% coverage (may need new extraction strategies)",
        "",
        "```python",
        "# Example fix categories:",
        "# 1. Implement cross-page aggregation for fragmented data",
        "# 2. Add specialized extractors for nested structures",
        "# 3. Enhance table parsing for specific field types",
        "```",
        "",
        "### Tier 3: Deep Fixes (Estimated 6-8 hours)",
        "**Target**: Fields with 0-20% coverage (architectural changes needed)",
        "",
        "```python",
        "# Example fix categories:",
        "# 1. Add new agent specialists for complex extractions",
        "# 2. Implement document structure analysis",
        "# 3. Add multi-pass refinement for difficult fields",
        "```",
        "",
        "---",
        "",
        "## 💡 Key Insights",
        ""
    ])

    # Calculate key insights
    total_fields = len(field_stats)
    avg_coverage = sum(s['coverage'] for s in field_stats) / total_fields if total_fields > 0 else 0

    # Find most common missing patterns
    missing_patterns = defaultdict(int)
    for stat in field_stats[:50]:  # Top 50 missing
        field_parts = stat['field'].split('.')
        if len(field_parts) >= 2:
            pattern = '.'.join(field_parts[:2])
            missing_patterns[pattern] += 1

    top_patterns = sorted(missing_patterns.items(), key=lambda x: x[1], reverse=True)[:5]

    report_lines.extend([
        f"1. **Average Field Coverage**: {avg_coverage:.1f}%",
        f"2. **Coverage Gap to 95% Target**: {95 - avg_coverage:.1f} percentage points",
        f"3. **Most Problematic Sections**:",
    ])

    for pattern, count in top_patterns:
        report_lines.append(f"   - `{pattern}.*`: {count} missing fields")

    report_lines.extend([
        "",
        "4. **Recommended Focus**: Start with Tier 1 fields (50-80% coverage) for maximum ROI",
        "5. **Expected Impact**: Fixing top 20 missing fields could add 15-25 percentage points to average coverage",
        "",
        "---",
        "",
        f"**Report Generated**: 2025-10-11",
        f"**Next Step**: Review top 30 missing fields and categorize by fix difficulty"
    ])

    # Write report
    report_path = Path("FIELD_COVERAGE_MATRIX_REPORT.md")
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')

    # Also write raw CSV for detailed analysis
    csv_lines = ["field,coverage_pct,filled,total,missing"]
    for stat in field_stats:
        csv_lines.append(
            f"\"{stat['field']}\",{stat['coverage']:.2f},"
            f"{stat['filled']},{stat['total']},{stat['missing']}"
        )

    csv_path = Path("field_coverage_matrix.csv")
    csv_path.write_text('\n'.join(csv_lines), encoding='utf-8')

    # Print summary
    print("=" * 80)
    print("FIELD COVERAGE MATRIX ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"✅ Analyzed {len(pdf_names)} PDFs")
    print(f"✅ Found {len(all_fields)} unique fields")
    print(f"✅ Average field coverage: {avg_coverage:.1f}%")
    print(f"✅ Fields with 0% coverage: {len(zero_fields)}")
    print(f"✅ Fields with 100% coverage: {len(perfect_fields)}")
    print()
    print(f"📄 Report saved to: {report_path}")
    print(f"📊 CSV saved to: {csv_path}")
    print()
    print("🎯 Top 5 Most Missing Fields:")
    for idx, stat in enumerate(field_stats[:5], 1):
        print(f"   {idx}. {stat['field'][:60]} - {stat['coverage']:.1f}% coverage")
    print()
    print("=" * 80)

if __name__ == "__main__":
    generate_coverage_matrix()
