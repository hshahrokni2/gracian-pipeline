#!/usr/bin/env python3
"""
Comprehensive Ground Truth Validation for Optimal BRF Pipeline.

Compares extraction results against human-verified ground truth to calculate:
- TRUE Coverage: % of required fields extracted
- TRUE Accuracy: % of extracted values that are correct
- Field-by-field gap analysis
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from decimal import Decimal

def load_json(path: str) -> Dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_value(val: Any) -> Any:
    """Normalize value for comparison."""
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip().lower()
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, list):
        return [normalize_value(v) for v in val]
    if isinstance(val, dict):
        return {k: normalize_value(v) for k, v in val.items()}
    return val

def compare_values(extracted: Any, ground_truth: Any, tolerance: float = 0.05) -> Tuple[bool, str]:
    """
    Compare two values with tolerance for numeric values.
    Returns (is_match, reason)
    """
    # Both None/empty
    if not extracted and not ground_truth:
        return True, "both_empty"

    # One is None/empty
    if not extracted:
        return False, "missing_extraction"
    if not ground_truth:
        return False, "unexpected_extraction"

    # Numeric comparison with tolerance
    if isinstance(ground_truth, (int, float)) and isinstance(extracted, (int, float)):
        diff = abs(float(extracted) - float(ground_truth))
        threshold = abs(float(ground_truth)) * tolerance
        if diff <= threshold:
            return True, "numeric_match_within_tolerance"
        else:
            return False, f"numeric_mismatch: {extracted} vs {ground_truth} (diff: {diff:.2f})"

    # String comparison (case-insensitive)
    if isinstance(ground_truth, str) and isinstance(extracted, str):
        if normalize_value(extracted) == normalize_value(ground_truth):
            return True, "exact_match"
        else:
            return False, f"string_mismatch: '{extracted}' vs '{ground_truth}'"

    # List comparison
    if isinstance(ground_truth, list) and isinstance(extracted, list):
        if len(extracted) != len(ground_truth):
            return False, f"list_length_mismatch: {len(extracted)} vs {len(ground_truth)}"
        # Check if all items match
        matches = all(compare_values(e, g)[0] for e, g in zip(extracted, ground_truth))
        return matches, "list_match" if matches else "list_content_mismatch"

    # Direct comparison
    if extracted == ground_truth:
        return True, "exact_match"

    return False, f"type_mismatch: {type(extracted)} vs {type(ground_truth)}"

def flatten_dict(d: Dict, parent_key: str = '') -> Dict:
    """Flatten nested dictionary for easier comparison, handling lists of dicts."""
    items = []

    # Handle case where d is actually a list (shouldn't happen at root, but for safety)
    if isinstance(d, list):
        return {parent_key: d}

    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k

        # Handle list of dictionaries (e.g., loans, board_members)
        if isinstance(v, list):
            # Store the entire list as a single value for comparison
            items.append((new_key, v))
        # Handle nested dictionary (recurse)
        elif isinstance(v, dict) and not any(isinstance(vv, (list, dict)) for vv in v.values()):
            items.extend(flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))

    return dict(items)

def main():
    """Run comprehensive validation."""

    print("="*80)
    print("COMPREHENSIVE GROUND TRUTH VALIDATION")
    print("="*80)

    # Paths (absolute from Gracian Pipeline root)
    gracian_root = Path(__file__).parent.parent.parent.parent
    ground_truth_path = gracian_root / "ground_truth" / "brf_198532_comprehensive_ground_truth.json"
    extraction_path = Path(__file__).parent.parent / "results" / "optimal_pipeline_refactored" / "brf_198532_optimal_result.json"

    if not ground_truth_path.exists():
        print(f"❌ Ground truth not found: {ground_truth_path}")
        return

    if not extraction_path.exists():
        print(f"❌ Extraction results not found: {extraction_path}")
        return

    # Load data
    print(f"\n📄 Loading ground truth...")
    ground_truth = load_json(str(ground_truth_path))

    print(f"📄 Loading extraction results...")
    extraction = load_json(str(extraction_path))

    # Count total ground truth fields
    flattened_gt = flatten_dict(ground_truth)
    total_gt_fields = len([k for k in flattened_gt.keys() if not k.startswith('_') and k != 'source_pages'])

    print(f"\n📊 Ground Truth Statistics:")
    print(f"   • Total fields: {total_gt_fields}")
    print(f"   • Sections: {len(ground_truth.keys())}")

    # Analyze extraction results
    agent_results = extraction.get('agent_results', {})
    print(f"\n📊 Extraction Statistics:")
    print(f"   • Agents run: {len(agent_results)}")

    # Count extracted fields
    extracted_fields = 0
    correct_fields = 0
    incorrect_fields = 0
    missing_fields = 0

    detailed_results = {}

    # Compare each section
    print(f"\n{'='*80}")
    print("FIELD-BY-FIELD COMPARISON")
    print(f"{'='*80}\n")

    # Define mappings from ground truth sections to agent IDs
    section_mapping = {
        'governance': 'governance_agent',
        'financial': 'financial_agent',
        'property': 'property_agent',
        'apartments': 'operations_agent',
        'loans': 'notes_accounting_agent',
        'fees': 'operations_agent'
    }

    for gt_section, agent_id in section_mapping.items():
        if gt_section not in ground_truth or gt_section.startswith('_'):
            continue

        print(f"\n{'─'*80}")
        print(f"📋 Section: {gt_section.upper()} → Agent: {agent_id}")
        print(f"{'─'*80}")

        gt_data = ground_truth[gt_section]
        agent_data = agent_results.get(agent_id, {}).get('data', {}) if agent_results.get(agent_id) else {}

        # Flatten for comparison
        gt_flat = flatten_dict(gt_data)

        section_results = {
            'extracted': 0,
            'correct': 0,
            'incorrect': 0,
            'missing': 0,
            'details': []
        }

        for field_path, gt_value in gt_flat.items():
            if field_path == 'source_pages':
                continue

            # Try to find corresponding field in extraction
            extracted_value = agent_data.get(field_path) if isinstance(agent_data, dict) else None

            if extracted_value is not None:
                section_results['extracted'] += 1
                is_correct, reason = compare_values(extracted_value, gt_value)

                if is_correct:
                    section_results['correct'] += 1
                    status = "✅"
                else:
                    section_results['incorrect'] += 1
                    status = "❌"

                print(f"  {status} {field_path}: {extracted_value} {'==' if is_correct else '!='} {gt_value}")
                if not is_correct:
                    print(f"     Reason: {reason}")

                section_results['details'].append({
                    'field': field_path,
                    'extracted': extracted_value,
                    'ground_truth': gt_value,
                    'correct': is_correct,
                    'reason': reason
                })
            else:
                section_results['missing'] += 1
                print(f"  ⚠️  {field_path}: MISSING (GT: {gt_value})")

                section_results['details'].append({
                    'field': field_path,
                    'extracted': None,
                    'ground_truth': gt_value,
                    'correct': False,
                    'reason': 'not_extracted'
                })

        # Section summary
        total_in_section = len(gt_flat) - (1 if 'source_pages' in gt_flat else 0)
        section_coverage = (section_results['extracted'] / total_in_section * 100) if total_in_section > 0 else 0
        section_accuracy = (section_results['correct'] / section_results['extracted'] * 100) if section_results['extracted'] > 0 else 0

        print(f"\n  📊 Section Summary:")
        print(f"     Coverage:  {section_results['extracted']}/{total_in_section} = {section_coverage:.1f}%")
        print(f"     Accuracy:  {section_results['correct']}/{section_results['extracted']} = {section_accuracy:.1f}%" if section_results['extracted'] > 0 else "     Accuracy:  N/A (no fields extracted)")

        detailed_results[gt_section] = section_results

        # Update totals
        extracted_fields += section_results['extracted']
        correct_fields += section_results['correct']
        incorrect_fields += section_results['incorrect']
        missing_fields += section_results['missing']

    # Overall summary
    print(f"\n{'='*80}")
    print("FINAL VALIDATION RESULTS")
    print(f"{'='*80}\n")

    overall_coverage = (extracted_fields / total_gt_fields * 100) if total_gt_fields > 0 else 0
    overall_accuracy = (correct_fields / extracted_fields * 100) if extracted_fields > 0 else 0

    print(f"📊 Overall Metrics:")
    print(f"   • Total Ground Truth Fields: {total_gt_fields}")
    print(f"   • Fields Extracted: {extracted_fields}")
    print(f"   • Fields Correct: {correct_fields}")
    print(f"   • Fields Incorrect: {incorrect_fields}")
    print(f"   • Fields Missing: {missing_fields}")
    print(f"")
    print(f"   🎯 TRUE COVERAGE:  {overall_coverage:.1f}%  (Target: 100%)")
    print(f"   🎯 TRUE ACCURACY:  {overall_accuracy:.1f}%  (Target: 100%)")
    print(f"")

    # Success criteria
    print(f"{'='*80}")
    print("VALIDATION CRITERIA")
    print(f"{'='*80}\n")

    criteria = {
        "Coverage ≥ 90%": overall_coverage >= 90,
        "Accuracy ≥ 95%": overall_accuracy >= 95,
        "At least 80% of GT fields extracted": (extracted_fields / total_gt_fields) >= 0.8
    }

    for criterion, passed in criteria.items():
        status = "✅" if passed else "❌"
        print(f"{status} {criterion}")

    all_pass = all(criteria.values())

    if all_pass:
        print(f"\n🎉 ALL VALIDATION CRITERIA PASSED!")
    else:
        print(f"\n⚠️  VALIDATION INCOMPLETE - See gaps above")

    # Save detailed results
    output_file = Path(__file__).parent.parent / "results" / "optimal_pipeline_refactored" / "ground_truth_validation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_gt_fields': total_gt_fields,
                'extracted_fields': extracted_fields,
                'correct_fields': correct_fields,
                'incorrect_fields': incorrect_fields,
                'missing_fields': missing_fields,
                'coverage_percent': round(overall_coverage, 2),
                'accuracy_percent': round(overall_accuracy, 2)
            },
            'by_section': detailed_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == '__main__':
    main()
