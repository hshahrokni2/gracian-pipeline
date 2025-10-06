#!/usr/bin/env python3
"""
Ground Truth Validation Script
Compares extraction results against manually verified ground truth.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_field(field_path: str, extracted_value: Any, ground_truth_value: Any) -> Tuple[str, str]:
    """
    Compare a single field.
    Returns: (status, message)
    Status: CORRECT, INCORRECT, MISSING, EXTRA
    """
    # Skip internal metadata fields
    if field_path.startswith('_'):
        return "SKIP", "Metadata field"

    # Handle missing values
    if ground_truth_value in [None, "NEED_TO_VERIFY", "NOT_IN_DOCUMENT", "PRESENT_IN_DOCUMENT_BUT_NOT_EXTRACTED"]:
        if extracted_value in [None, [], {}, ""]:
            return "EXPECTED_MISSING", f"Field not in document or extraction expected to fail"
        else:
            return "UNEXPECTED_EXTRACTION", f"Extracted '{extracted_value}' but ground truth says field is missing"

    if extracted_value in [None, [], {}, ""] and ground_truth_value not in [None, [], {}, ""]:
        return "MISSING", f"Expected '{ground_truth_value}' but got null/empty"

    # Compare values
    if str(extracted_value) == str(ground_truth_value):
        return "CORRECT", f"✓ {extracted_value}"
    else:
        # Check if numeric values are within 1 SEK tolerance (rounding)
        if isinstance(extracted_value, (int, float)) and isinstance(ground_truth_value, (int, float)):
            if abs(extracted_value - ground_truth_value) <= 1:
                return "CORRECT_ROUNDED", f"✓ {extracted_value} (±1 SEK from {ground_truth_value})"

        return "INCORRECT", f"✗ Got '{extracted_value}', expected '{ground_truth_value}'"

def flatten_dict(d: Dict, parent_key: str = '') -> Dict[str, Any]:
    """Flatten nested dictionary for easier comparison."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k

        # Skip metadata fields
        if k.startswith('_'):
            continue

        if isinstance(v, dict) and not k.startswith('_'):
            items.extend(flatten_dict(v, new_key).items())
        elif isinstance(v, list):
            # For lists, convert to string for comparison
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def validate_extraction(extraction_path: str, ground_truth_path: str) -> Dict[str, Any]:
    """
    Compare extraction against manual ground truth.
    Returns comprehensive validation report.
    """
    extraction = load_json(extraction_path)
    ground_truth = load_json(ground_truth_path)

    # Flatten both dictionaries
    ext_flat = flatten_dict(extraction)
    gt_flat = flatten_dict(ground_truth)

    results = {
        "total_fields": 0,
        "correct": 0,
        "correct_rounded": 0,
        "incorrect": 0,
        "missing": 0,
        "expected_missing": 0,
        "unexpected_extraction": 0,
        "accuracy_percent": 0.0,
        "coverage_percent": 0.0,
        "errors": [],
        "successes": [],
        "missing_fields": [],
        "unexpected_fields": []
    }

    # Compare all ground truth fields
    all_fields = set(gt_flat.keys()) | set(ext_flat.keys())

    for field_path in sorted(all_fields):
        ext_value = ext_flat.get(field_path)
        gt_value = gt_flat.get(field_path)

        results["total_fields"] += 1

        status, message = compare_field(field_path, ext_value, gt_value)

        if status == "CORRECT":
            results["correct"] += 1
            results["successes"].append({
                "field": field_path,
                "value": ext_value,
                "status": "correct"
            })
        elif status == "CORRECT_ROUNDED":
            results["correct_rounded"] += 1
            results["successes"].append({
                "field": field_path,
                "value": ext_value,
                "ground_truth": gt_value,
                "status": "correct_rounded"
            })
        elif status == "INCORRECT":
            results["incorrect"] += 1
            results["errors"].append({
                "field": field_path,
                "extracted": ext_value,
                "ground_truth": gt_value,
                "error": "value_mismatch",
                "message": message
            })
        elif status == "MISSING":
            results["missing"] += 1
            results["missing_fields"].append({
                "field": field_path,
                "expected_value": gt_value,
                "error": "extraction_failed",
                "message": message
            })
        elif status == "EXPECTED_MISSING":
            results["expected_missing"] += 1
        elif status == "UNEXPECTED_EXTRACTION":
            results["unexpected_extraction"] += 1
            results["unexpected_fields"].append({
                "field": field_path,
                "extracted": ext_value,
                "message": message
            })

    # Calculate metrics
    validated_fields = results["correct"] + results["correct_rounded"] + results["incorrect"] + results["missing"]
    if validated_fields > 0:
        results["accuracy_percent"] = ((results["correct"] + results["correct_rounded"]) / validated_fields) * 100

    extractable_fields = results["total_fields"] - results["expected_missing"]
    if extractable_fields > 0:
        results["coverage_percent"] = ((results["correct"] + results["correct_rounded"] + results["incorrect"]) / extractable_fields) * 100

    return results

def generate_markdown_report(results: Dict[str, Any], output_path: str):
    """Generate detailed markdown validation report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Ground Truth Validation Report\n\n")
        f.write(f"**Date**: {Path(__file__).stat().st_mtime}\n\n")

        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Fields Validated**: {results['total_fields']}\n")
        f.write(f"- **Accuracy**: {results['accuracy_percent']:.1f}% ({results['correct'] + results['correct_rounded']}/{results['total_fields'] - results['expected_missing']} fields correct)\n")
        f.write(f"- **Coverage**: {results['coverage_percent']:.1f}% ({results['correct'] + results['correct_rounded'] + results['incorrect']}/{results['total_fields'] - results['expected_missing']} fields extracted)\n\n")

        f.write("### Breakdown\n\n")
        f.write(f"- ✅ **Correct**: {results['correct']} fields\n")
        f.write(f"- ≈ **Correct (rounded)**: {results['correct_rounded']} fields\n")
        f.write(f"- ❌ **Incorrect**: {results['incorrect']} fields\n")
        f.write(f"- ⚠️ **Missing**: {results['missing']} fields (present in PDF but not extracted)\n")
        f.write(f"- ℹ️ **Expected Missing**: {results['expected_missing']} fields (not in PDF)\n")
        f.write(f"- 🔍 **Unexpected**: {results['unexpected_extraction']} fields (extracted but shouldn't be)\n\n")

        if results['errors']:
            f.write("## ❌ Incorrect Extractions\n\n")
            for error in results['errors']:
                f.write(f"### {error['field']}\n")
                f.write(f"- **Extracted**: `{error['extracted']}`\n")
                f.write(f"- **Expected**: `{error['ground_truth']}`\n")
                f.write(f"- **Error**: {error['error']}\n\n")

        if results['missing_fields']:
            f.write("## ⚠️ Missing Extractions (Data Present in PDF)\n\n")
            for missing in results['missing_fields']:
                f.write(f"### {missing['field']}\n")
                f.write(f"- **Expected Value**: `{missing['expected_value']}`\n")
                f.write(f"- **Status**: {missing['error']}\n")
                f.write(f"- **Message**: {missing['message']}\n\n")

        if results['successes'][:20]:  # Show first 20 successes
            f.write("## ✅ Sample Successful Extractions\n\n")
            for success in results['successes'][:20]:
                f.write(f"- **{success['field']}**: `{success['value']}` ({success['status']})\n")

        f.write("\n---\n\n")
        f.write("**Conclusion**: ")
        if results['accuracy_percent'] >= 95:
            f.write("✅ **PRODUCTION READY** - Accuracy meets 95% target\n")
        elif results['accuracy_percent'] >= 90:
            f.write("⚠️ **NEAR TARGET** - Accuracy close to 95% target, minor fixes needed\n")
        else:
            f.write("❌ **NEEDS IMPROVEMENT** - Accuracy below 90%, significant fixes required\n")

if __name__ == "__main__":
    # File paths
    extraction_file = "deep_mode_full_test_notes_4_8_9.json"
    ground_truth_file = "ground_truth/brf_198532_ground_truth.json"
    output_report = "GROUND_TRUTH_VALIDATION_REPORT.md"

    print("🔍 Validating extraction against ground truth...")
    print(f"   Extraction: {extraction_file}")
    print(f"   Ground Truth: {ground_truth_file}")
    print()

    # Run validation
    results = validate_extraction(extraction_file, ground_truth_file)

    # Print summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Fields: {results['total_fields']}")
    print(f"Accuracy: {results['accuracy_percent']:.1f}%")
    print(f"Coverage: {results['coverage_percent']:.1f}%")
    print()
    print(f"✅ Correct: {results['correct']}")
    print(f"≈ Correct (rounded): {results['correct_rounded']}")
    print(f"❌ Incorrect: {results['incorrect']}")
    print(f"⚠️ Missing: {results['missing']}")
    print(f"ℹ️ Expected Missing: {results['expected_missing']}")
    print(f"🔍 Unexpected: {results['unexpected_extraction']}")
    print("=" * 80)

    # Generate report
    generate_markdown_report(results, output_report)
    print(f"\n✅ Detailed report saved to: {output_report}")

    # Save JSON results
    json_output = output_report.replace('.md', '.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON results saved to: {json_output}")
