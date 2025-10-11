#!/usr/bin/env python3
"""
Pydantic Extraction Validation - Handles ExtractionField structure.

Validates Pydantic extraction results against comprehensive ground truth.
Handles:
- ExtractionField objects with .value property
- Field name mappings (full_name → name)
- Role normalization (ordforande → Ordförande)
- Optional fields (term_expires_at_next_meeting)
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


def extract_value(field: Any) -> Any:
    """
    Extract value from ExtractionField or return raw value.

    ExtractionField structure:
    {
        "value": "actual_value",
        "confidence": 0.9,
        "source": "llm_extraction",
        "evidence_pages": [1, 2, 3]
    }
    """
    if isinstance(field, dict) and 'value' in field:
        return field['value']
    return field


def normalize_role(role: str) -> str:
    """Normalize Swedish roles to match ground truth format."""
    role_map = {
        "ordforande": "Ordförande",
        "vice_ordforande": "Vice ordförande",
        "ledamot": "Ledamot",
        "suppleant": "Suppleant"
    }
    if isinstance(role, str):
        return role_map.get(role.lower(), role)
    return role


def normalize_board_member(member: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Pydantic board member to ground truth format.

    Pydantic: {full_name: {value: "..."}, role: "ordforande", ...}
    Ground Truth: {name: "...", role: "Ordförande", term_expires_at_next_meeting: true}
    """
    normalized = {}

    # Map full_name → name
    if 'full_name' in member:
        normalized['name'] = extract_value(member['full_name'])
    elif 'name' in member:
        normalized['name'] = extract_value(member['name'])

    # Normalize role
    if 'role' in member:
        normalized['role'] = normalize_role(member['role'])

    # Add term_expires_at_next_meeting if missing (not critical for validation)
    # Ground truth has this, but Pydantic schema doesn't extract it

    return normalized


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

    # List comparison (special handling for board_members)
    if isinstance(ground_truth, list) and isinstance(extracted, list):
        if len(extracted) != len(ground_truth):
            return False, f"list_length_mismatch: {len(extracted)} vs {len(ground_truth)}"

        # For board members, compare normalized versions
        if extracted and isinstance(extracted[0], dict) and 'full_name' in extracted[0]:
            norm_extracted = [normalize_board_member(m) for m in extracted]
            norm_gt = [normalize_board_member(m) for m in ground_truth]

            # Compare names and roles only (ignore term_expires_at_next_meeting for now)
            for e, g in zip(norm_extracted, norm_gt):
                if e.get('name', '').lower() != g.get('name', '').lower():
                    return False, f"board_member_name_mismatch: {e.get('name')} vs {g.get('name')}"
                if e.get('role', '').lower() != g.get('role', '').lower():
                    return False, f"board_member_role_mismatch: {e.get('role')} vs {g.get('role')}"

            return True, "board_members_match"

        # Generic list comparison
        matches = all(compare_values(e, g)[0] for e, g in zip(extracted, ground_truth))
        return matches, "list_match" if matches else "list_content_mismatch"

    # Direct comparison
    if extracted == ground_truth:
        return True, "exact_match"

    return False, f"type_mismatch: {type(extracted)} vs {type(ground_truth)}"


def flatten_dict(d: Dict, parent_key: str = '') -> Dict:
    """Flatten nested dictionary, handling ExtractionField objects."""
    items = []

    if isinstance(d, list):
        return {parent_key: d}

    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k

        # Extract value from ExtractionField
        value = extract_value(v)

        # Handle list of dictionaries
        if isinstance(value, list):
            items.append((new_key, value))
        # Handle nested dictionary
        elif isinstance(value, dict) and not any(isinstance(vv, (list, dict)) for vv in value.values()):
            items.extend(flatten_dict(value, new_key).items())
        else:
            items.append((new_key, value))

    return dict(items)


def main():
    """Run comprehensive validation."""

    print("="*80)
    print("PYDANTIC EXTRACTION VALIDATION")
    print("="*80)

    # Paths
    gracian_root = Path(__file__).parent.parent.parent.parent
    ground_truth_path = gracian_root / "ground_truth" / "brf_198532_comprehensive_ground_truth.json"
    pydantic_extraction_path = gracian_root / "pydantic_extraction_test.json"

    if not ground_truth_path.exists():
        print(f"❌ Ground truth not found: {ground_truth_path}")
        return

    if not pydantic_extraction_path.exists():
        print(f"❌ Pydantic extraction not found: {pydantic_extraction_path}")
        return

    # Load data
    print(f"\n📄 Loading ground truth: {ground_truth_path.name}")
    ground_truth = load_json(str(ground_truth_path))

    print(f"📄 Loading Pydantic extraction: {pydantic_extraction_path.name}")
    pydantic_result = load_json(str(pydantic_extraction_path))

    # Count total ground truth fields
    flattened_gt = flatten_dict(ground_truth)
    total_gt_fields = len([k for k in flattened_gt.keys() if not k.startswith('_') and k != 'source_pages'])

    print(f"\n📊 Ground Truth Statistics:")
    print(f"   • Total fields: {total_gt_fields}")
    print(f"   • Sections: {len(ground_truth.keys())}")

    # Pydantic extraction has top-level sections: governance, financial, property, etc.
    print(f"\n📊 Pydantic Extraction Structure:")
    print(f"   • Top-level sections: {list(pydantic_result.keys())}")

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

    # Define mappings from ground truth sections to Pydantic sections
    section_mapping = {
        'governance': 'governance',
        'financial': 'financial',
        'property': 'property',
        'apartments': 'apartments',
        'loans': 'loans',
        'fees': 'fees'
    }

    for gt_section, pydantic_section in section_mapping.items():
        if gt_section not in ground_truth or gt_section.startswith('_'):
            continue

        print(f"\n{'─'*80}")
        print(f"📋 Section: {gt_section.upper()} → Pydantic: {pydantic_section}")
        print(f"{'─'*80}")

        gt_data = ground_truth[gt_section]
        pydantic_data = pydantic_result.get(pydantic_section, {})

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

            # Try to find corresponding field in Pydantic extraction
            # Handle case where pydantic_data itself might be a list or non-dict
            if not isinstance(pydantic_data, dict):
                pydantic_value = None
            else:
                pydantic_value = pydantic_data.get(field_path)

            # Extract value from ExtractionField if needed
            pydantic_value = extract_value(pydantic_value)

            if pydantic_value is not None:
                section_results['extracted'] += 1
                is_correct, reason = compare_values(pydantic_value, gt_value)

                if is_correct:
                    section_results['correct'] += 1
                    status = "✅"
                else:
                    section_results['incorrect'] += 1
                    status = "❌"

                print(f"  {status} {field_path}: {pydantic_value} {'==' if is_correct else '!='} {gt_value}")
                if not is_correct:
                    print(f"     Reason: {reason}")

                section_results['details'].append({
                    'field': field_path,
                    'extracted': pydantic_value,
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
    output_file = Path(__file__).parent.parent / "results" / "pydantic_extraction_validation.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

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
