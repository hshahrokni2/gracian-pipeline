"""
Week 3 Day 5: Comprehensive 95/95 Validation Test
Validates extraction against comprehensive ground truth with validation engine integration.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import production pipeline components
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor
from gracian_pipeline.core.validation_engine import ValidationEngine, ValidationSeverity


def load_ground_truth(path: str) -> Dict[str, Any]:
    """Load ground truth data from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_value(field: Any) -> Any:
    """Extract value from ExtractionField or raw type (MIXED approach)."""
    if hasattr(field, 'value'):
        return field.value
    return field


def normalize_value(val: Any) -> Any:
    """Normalize value for comparison (handles Swedish numbers, decimals, etc.)."""
    if val is None:
        return None

    # Handle Decimal
    if isinstance(val, Decimal):
        return float(val)

    # Handle ExtractionField wrapper
    if hasattr(val, 'value'):
        return normalize_value(val.value)

    # Handle strings
    if isinstance(val, str):
        val = val.strip()
        # Try to convert Swedish number format
        if val and any(c.isdigit() for c in val):
            # Remove spaces and convert comma to dot
            normalized = val.replace(' ', '').replace(',', '.')
            try:
                return float(normalized)
            except ValueError:
                return val

    # Handle lists
    if isinstance(val, list):
        return [normalize_value(v) for v in val]

    # Handle dicts
    if isinstance(val, dict):
        return {k: normalize_value(v) for k, v in val.items()}

    return val


def compare_values(extracted: Any, ground_truth: Any, tolerance: float = 0.05) -> Tuple[bool, str]:
    """
    Compare extracted value with ground truth.
    Returns (match: bool, details: str).
    """
    ext_norm = normalize_value(extracted)
    gt_norm = normalize_value(ground_truth)

    # Both None
    if ext_norm is None and gt_norm is None:
        return True, "Both None (MATCH)"

    # One None
    if ext_norm is None:
        return False, f"Missing extraction (GT: {gt_norm})"
    if gt_norm is None:
        return False, f"Unexpected extraction (Extracted: {ext_norm})"

    # Numeric comparison with tolerance
    if isinstance(ext_norm, (int, float)) and isinstance(gt_norm, (int, float)):
        if abs(ext_norm - gt_norm) / max(abs(gt_norm), 1) <= tolerance:
            return True, f"Numeric match within {tolerance*100}% (Extracted: {ext_norm}, GT: {gt_norm})"
        else:
            return False, f"Numeric mismatch (Extracted: {ext_norm}, GT: {gt_norm})"

    # String comparison (case-insensitive)
    if isinstance(ext_norm, str) and isinstance(gt_norm, str):
        if ext_norm.lower() == gt_norm.lower():
            return True, f"String match (case-insensitive)"
        else:
            return False, f"String mismatch (Extracted: '{ext_norm}', GT: '{gt_norm}')"

    # Direct equality for other types
    if ext_norm == gt_norm:
        return True, f"Direct match"

    return False, f"Type/value mismatch (Extracted: {type(ext_norm).__name__} = {ext_norm}, GT: {type(gt_norm).__name__} = {gt_norm})"


def flatten_dict(d: Dict, parent_key: str = '', exclude_metadata: bool = False) -> Dict[str, Any]:
    """Flatten nested dictionary for easier comparison.

    Args:
        exclude_metadata: If True, skip keys starting with underscore (internal metadata)
    """
    items = []
    for k, v in d.items():
        # Skip metadata fields (those starting with _) if requested
        if exclude_metadata and k.startswith('_'):
            continue

        new_key = f"{parent_key}.{k}" if parent_key else k

        if isinstance(v, dict) and not any(isinstance(val, list) for val in v.values()):
            # Recurse for nested dicts (unless they contain lists)
            items.extend(flatten_dict(v, new_key, exclude_metadata).items())
        else:
            items.append((new_key, v))

    return dict(items)


def calculate_metrics(
    extraction: Dict[str, Any],
    ground_truth: Dict[str, Any],
    validation_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate 95/95 metrics:
    - Coverage: % of GT fields extracted
    - Accuracy: % of extracted fields correct
    - Validation engine precision/recall
    """

    # Flatten both dicts for field-level comparison
    # CRITICAL: Exclude metadata fields (starting with _) from extraction
    ext_flat = flatten_dict(extraction, exclude_metadata=True)
    gt_flat = flatten_dict(ground_truth, exclude_metadata=True)

    # Field-level analysis
    results = []
    all_fields = set(gt_flat.keys()) | set(ext_flat.keys())

    for field in sorted(all_fields):
        ext_val = ext_flat.get(field)
        gt_val = gt_flat.get(field)

        match, details = compare_values(ext_val, gt_val)

        results.append({
            'field': field,
            'extracted': ext_val,
            'ground_truth': gt_val,
            'match': match,
            'details': details,
            'in_gt': field in gt_flat,
            'in_extraction': field in ext_flat
        })

    # Calculate coverage (% of GT fields extracted)
    gt_fields = [r for r in results if r['in_gt']]
    extracted_fields = [r for r in results if r['in_extraction'] and r['extracted'] is not None]
    coverage = len(extracted_fields) / len(gt_fields) * 100 if gt_fields else 0

    # Calculate accuracy (% of extracted fields correct)
    correct_fields = [r for r in extracted_fields if r['match']]
    accuracy = len(correct_fields) / len(extracted_fields) * 100 if extracted_fields else 0

    # Validation engine analysis
    val_issues = validation_report.get('issues', [])
    val_errors = [iss for iss in val_issues if iss['severity'] == 'ERROR']
    val_warnings = [iss for iss in val_issues if iss['severity'] == 'WARNING']

    # True positives: Validation errors that match GT mismatches
    tp_errors = 0
    for err in val_errors:
        err_field = err['field']
        # Check if this field is actually wrong in GT comparison
        matching_result = next((r for r in results if err_field in r['field']), None)
        if matching_result and not matching_result['match']:
            tp_errors += 1

    # False positives: Validation errors for fields that match GT
    fp_errors = len(val_errors) - tp_errors

    # Precision/Recall for validation engine
    precision = tp_errors / len(val_errors) * 100 if val_errors else 0
    recall = tp_errors / len([r for r in results if not r['match'] and r['in_gt']]) * 100 if any(not r['match'] and r['in_gt'] for r in results) else 0

    return {
        'coverage_percent': round(coverage, 1),
        'accuracy_percent': round(accuracy, 1),
        'total_gt_fields': len(gt_fields),
        'total_extracted_fields': len(extracted_fields),
        'correct_fields': len(correct_fields),
        'incorrect_fields': len(extracted_fields) - len(correct_fields),
        'missing_fields': len(gt_fields) - len(extracted_fields),
        'validation_engine': {
            'total_errors': len(val_errors),
            'total_warnings': len(val_warnings),
            'true_positive_errors': tp_errors,
            'false_positive_errors': fp_errors,
            'precision_percent': round(precision, 1),
            'recall_percent': round(recall, 1)
        },
        'field_results': results
    }


def generate_report(metrics: Dict[str, Any], output_path: str):
    """Generate comprehensive markdown validation report."""

    md = f"""# Week 3 Day 5: Comprehensive 95/95 Validation Report

## 🎯 EXECUTIVE SUMMARY

**Coverage**: {metrics['coverage_percent']}% ({metrics['total_extracted_fields']}/{metrics['total_gt_fields']} fields)
**Accuracy**: {metrics['accuracy_percent']}% ({metrics['correct_fields']}/{metrics['total_extracted_fields']} correct)

**95/95 Target Status**:
- Coverage ≥95%: {'✅ PASS' if metrics['coverage_percent'] >= 95 else '❌ FAIL'}
- Accuracy ≥95%: {'✅ PASS' if metrics['accuracy_percent'] >= 95 else '❌ FAIL'}

---

## 🔍 VALIDATION ENGINE PERFORMANCE

**Error Detection**:
- Total Errors Detected: {metrics['validation_engine']['total_errors']}
- True Positives: {metrics['validation_engine']['true_positive_errors']} (correctly flagged errors)
- False Positives: {metrics['validation_engine']['false_positive_errors']} (incorrect flags)
- Warnings: {metrics['validation_engine']['total_warnings']}

**Metrics**:
- Precision: {metrics['validation_engine']['precision_percent']}% (accuracy of error detection)
- Recall: {metrics['validation_engine']['recall_percent']}% (% of actual errors detected)

---

## 📊 FIELD-BY-FIELD ANALYSIS

### ✅ CORRECT EXTRACTIONS ({len([r for r in metrics['field_results'] if r['match']])} fields)

"""

    # Correct fields
    for result in [r for r in metrics['field_results'] if r['match']]:
        md += f"- **{result['field']}**: {result['details']}\n"

    md += f"\n### ❌ INCORRECT EXTRACTIONS ({len([r for r in metrics['field_results'] if r['in_extraction'] and not r['match']])} fields)\n\n"

    # Incorrect fields
    for result in [r for r in metrics['field_results'] if r['in_extraction'] and not r['match']]:
        md += f"- **{result['field']}**: {result['details']}\n"

    md += f"\n### 🔴 MISSING EXTRACTIONS ({metrics['missing_fields']} fields)\n\n"

    # Missing fields
    for result in [r for r in metrics['field_results'] if r['in_gt'] and not r['in_extraction']]:
        md += f"- **{result['field']}**: Not extracted (GT: {result['ground_truth']})\n"

    md += """
---

## 🎯 GAP ANALYSIS

### Root Causes for < 95/95 (if applicable)

"""

    if metrics['coverage_percent'] < 95:
        md += f"**Coverage Gap**: {95 - metrics['coverage_percent']:.1f}% below target\n"
        md += f"- Missing {metrics['missing_fields']} fields from ground truth\n"
        md += "- Likely causes: Agent prompt gaps, section routing errors, LLM extraction failures\n\n"

    if metrics['accuracy_percent'] < 95:
        md += f"**Accuracy Gap**: {95 - metrics['accuracy_percent']:.1f}% below target\n"
        md += f"- {metrics['incorrect_fields']} incorrect extractions\n"
        md += "- Likely causes: Validation logic issues, Swedish number parsing, field mapping errors\n\n"

    md += "---\n\n**Generated**: Week 3 Day 5 - Integration & Testing Phase\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"✅ Report saved to: {output_path}")


def main():
    """Run comprehensive 95/95 validation test."""

    # Paths
    pdf_path = "SRS/brf_198532.pdf"
    gt_path = "ground_truth/brf_198532_agent_aligned_ground_truth.json"

    if not Path(gt_path).exists():
        print(f"❌ Ground truth file not found: {gt_path}")
        sys.exit(1)

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print("Week 3 Day 5: Comprehensive 95/95 Validation Test")
    print("=" * 80)

    # Load ground truth
    print(f"\n📂 Loading ground truth from: {gt_path}")
    ground_truth = load_ground_truth(gt_path)
    print(f"   ✓ Loaded {len(flatten_dict(ground_truth, exclude_metadata=True))} ground truth fields")

    # Run extraction with validation engine
    print(f"\n🔬 Running extraction on: {pdf_path}")
    print("   Mode: deep (with validation engine + targeted vision)")

    extractor = RobustUltraComprehensiveExtractor()
    result = extractor.extract_brf_document(pdf_path, mode="deep")

    # Get validation report
    validation_report = result.get('_validation_report', {})
    validation_report_post = result.get('_validation_report_post_recovery', {})

    print(f"\n   ✓ Extraction complete")
    print(f"   → Validation errors (before recovery): {validation_report.get('error_count', 0)}")
    print(f"   → Validation errors (after recovery): {validation_report_post.get('error_count', 0)}")

    # Calculate metrics
    print(f"\n📊 Calculating 95/95 metrics...")

    # Use post-recovery validation report if available
    final_validation = validation_report_post if validation_report_post else validation_report

    metrics = calculate_metrics(result, ground_truth, final_validation)

    # Print summary
    print(f"\n{'=' * 80}")
    print(f"VALIDATION RESULTS")
    print(f"{'=' * 80}")
    print(f"\n✅ Coverage: {metrics['coverage_percent']}% ({metrics['total_extracted_fields']}/{metrics['total_gt_fields']} fields)")
    print(f"✅ Accuracy: {metrics['accuracy_percent']}% ({metrics['correct_fields']}/{metrics['total_extracted_fields']} correct)")
    print(f"\n🎯 95/95 Target:")
    print(f"   Coverage ≥95%: {'✅ PASS' if metrics['coverage_percent'] >= 95 else '❌ FAIL'}")
    print(f"   Accuracy ≥95%: {'✅ PASS' if metrics['accuracy_percent'] >= 95 else '❌ FAIL'}")

    print(f"\n🔍 Validation Engine Performance:")
    print(f"   Precision: {metrics['validation_engine']['precision_percent']}%")
    print(f"   Recall: {metrics['validation_engine']['recall_percent']}%")

    # Generate report
    report_path = "WEEK3_DAY5_95_95_VALIDATION_REPORT.md"
    print(f"\n📝 Generating comprehensive report...")
    generate_report(metrics, report_path)

    # Save detailed results to JSON
    results_path = "week3_day5_validation_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Detailed results saved to: {results_path}")

    print(f"\n{'=' * 80}")
    print("Week 3 Day 5 Validation Complete")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
