#!/usr/bin/env python3
"""
Validate Pydantic extraction against Pydantic-aligned ground truth.

This script tests Phase 2B: Pydantic-Aligned Ground Truth validation.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.pydantic_extractor import UltraComprehensivePydanticExtractor
from gracian_pipeline.models.brf_schema import BRFAnnualReport

load_dotenv()


def load_json(path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_value(field: Any) -> Any:
    """Recursively extract values from ExtractionField objects (MIXED approach)."""
    # Check if it's an ExtractionField dict (from model_dump())
    if isinstance(field, dict) and 'value' in field and 'confidence' in field:
        # This is an ExtractionField serialized as dict - extract the value
        return get_value(field['value'])
    elif isinstance(field, dict):
        # Regular dict - recursively unwrap values
        return {k: get_value(v) for k, v in field.items()}
    elif isinstance(field, list):
        # Recursively unwrap list elements
        return [get_value(item) for item in field]
    else:
        return field


def normalize_value(val: Any) -> Any:
    """Normalize value for comparison (handles Swedish numbers, decimals, etc.)."""
    if val is None:
        return None

    # Handle string representations of numbers
    if isinstance(val, str):
        # Remove Swedish thousand separator (space) and replace comma with dot
        normalized = val.strip().replace(' ', '').replace(',', '.')

        # Try to convert to number
        try:
            if '.' in normalized:
                return float(normalized)
            else:
                return int(normalized)
        except ValueError:
            # Return normalized string if not a number
            return normalized.lower().strip()

    # Handle numeric types
    if isinstance(val, (int, float, Decimal)):
        return float(val) if isinstance(val, (float, Decimal)) else val

    # Handle lists
    if isinstance(val, list):
        return [normalize_value(v) for v in val]

    # Handle dicts
    if isinstance(val, dict):
        return {k: normalize_value(v) for k, v in val.items()}

    return val


def compare_values(extracted: Any, ground_truth: Any, tolerance: float = 0.05) -> Tuple[bool, str]:
    """
    Compare extracted value with ground truth value.

    Args:
        extracted: Value from extraction
        ground_truth: Expected value from ground truth
        tolerance: Tolerance for numeric comparisons (default 5%)

    Returns:
        Tuple of (match: bool, reason: str)
    """
    # Normalize both values
    norm_extracted = normalize_value(extracted)
    norm_ground_truth = normalize_value(ground_truth)

    # Handle None cases
    if norm_ground_truth is None and norm_extracted is None:
        return True, "Both null (match)"
    if norm_ground_truth is None:
        return False, "Ground truth is null, extracted has value"
    if norm_extracted is None:
        return False, "Extracted is null, ground truth has value"

    # Type mismatch check
    if type(norm_extracted) != type(norm_ground_truth):
        return False, f"Type mismatch: extracted={type(norm_extracted).__name__}, ground_truth={type(norm_ground_truth).__name__}"

    # Numeric comparison with tolerance
    if isinstance(norm_ground_truth, (int, float)):
        if isinstance(norm_extracted, (int, float)):
            # Use absolute tolerance for large numbers (±tolerance * value or minimum 5000 SEK)
            abs_tolerance = max(abs(norm_ground_truth) * tolerance, 5000)

            if abs(norm_ground_truth - norm_extracted) <= abs_tolerance:
                return True, f"Numeric match within {tolerance*100}% tolerance"
            else:
                diff = abs(norm_ground_truth - norm_extracted)
                return False, f"Numeric mismatch: diff={diff:.0f} (tolerance={abs_tolerance:.0f})"

    # String comparison (case-insensitive)
    if isinstance(norm_ground_truth, str):
        if isinstance(norm_extracted, str):
            if norm_extracted == norm_ground_truth:
                return True, "Exact string match"
            else:
                # Fuzzy match for Swedish names
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, norm_extracted, norm_ground_truth).ratio()
                if similarity >= 0.85:
                    return True, f"Fuzzy match (similarity={similarity:.2%})"
                else:
                    return False, f"String mismatch: '{norm_extracted}' != '{norm_ground_truth}' (similarity={similarity:.2%})"

    # List comparison
    if isinstance(norm_ground_truth, list):
        if len(norm_ground_truth) != len(norm_extracted):
            return False, f"List length mismatch: {len(norm_extracted)} != {len(norm_ground_truth)}"

        # Element-wise comparison
        mismatches = []
        for i, (ext_val, gt_val) in enumerate(zip(norm_extracted, norm_ground_truth)):
            match, reason = compare_values(ext_val, gt_val, tolerance)
            if not match:
                mismatches.append(f"Index {i}: {reason}")

        if mismatches:
            return False, f"List element mismatches: {'; '.join(mismatches)}"
        return True, "List elements match"

    # Dict comparison (recursive)
    if isinstance(norm_ground_truth, dict):
        mismatches = []
        for key in norm_ground_truth.keys():
            if key not in norm_extracted:
                mismatches.append(f"Missing key: {key}")
            else:
                match, reason = compare_values(norm_extracted[key], norm_ground_truth[key], tolerance)
                if not match:
                    mismatches.append(f"{key}: {reason}")

        if mismatches:
            return False, f"Dict mismatches: {'; '.join(mismatches)}"
        return True, "Dict values match"

    # Fallback: direct equality
    if norm_extracted == norm_ground_truth:
        return True, "Direct equality match"
    else:
        return False, f"Value mismatch: {norm_extracted} != {norm_ground_truth}"


def main():
    """Run Pydantic-aligned validation."""

    # Paths
    pdf_path = "SRS/brf_198532.pdf"
    gt_path = "ground_truth/brf_198532_pydantic_ground_truth.json"

    if not Path(gt_path).exists():
        print(f"❌ Ground truth file not found: {gt_path}")
        sys.exit(1)

    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print("PYDANTIC-ALIGNED VALIDATION (Phase 2B)")
    print("=" * 80)

    # Load ground truth
    print(f"\n📂 Loading Pydantic-aligned ground truth from: {gt_path}")
    ground_truth = load_json(gt_path)
    print(f"   ✓ Loaded ground truth with {len(ground_truth)} top-level keys")

    # Run extraction
    print(f"\n🔬 Running Pydantic extraction on: {pdf_path}")
    extractor = UltraComprehensivePydanticExtractor()
    result = extractor.extract_brf_comprehensive(pdf_path, mode="fast")
    print(f"   ✓ Extraction complete")
    print(f"   Type: {type(result).__name__}")
    print(f"   Is BRFAnnualReport: {isinstance(result, BRFAnnualReport)}")

    # Convert to dict for comparison
    result_dict = result.model_dump()

    # Debug: Check what we actually have
    print(f"\n🔍 DEBUG: Type of result_dict['metadata']: {type(result_dict.get('metadata'))}")
    if 'metadata' in result_dict:
        print(f"   metadata.organization_number type: {type(result_dict['metadata'].get('organization_number'))}")
        print(f"   metadata.organization_number value: {result_dict['metadata'].get('organization_number')}")

    # Recursively unwrap ALL ExtractionField objects
    result_dict = get_value(result_dict)

    print(f"\n🔍 AFTER UNWRAP: Type of result_dict['metadata']: {type(result_dict.get('metadata'))}")
    if 'metadata' in result_dict:
        print(f"   metadata.organization_number type: {type(result_dict['metadata'].get('organization_number'))}")
        print(f"   metadata.organization_number value: {result_dict['metadata'].get('organization_number')}")

    # Validation
    print("\n📊 Running validation...\n")

    total_fields = 0
    matched_fields = 0
    field_results = []

    # Iterate through ground truth fields and compare with extraction
    def validate_nested_dict(gt_dict: Dict, ext_dict: Dict, prefix: str = ""):
        """Recursively validate nested dictionary fields."""
        nonlocal total_fields, matched_fields

        for key, gt_value in gt_dict.items():
            field_path = f"{prefix}.{key}" if prefix else key

            # Skip metadata fields
            if key.startswith('_'):
                continue

            total_fields += 1

            # Get extracted value
            ext_value = ext_dict.get(key) if isinstance(ext_dict, dict) else None

            # Extract from ExtractionField if needed
            if ext_value is not None:
                ext_value = get_value(ext_value)

            if ext_value is not None:
                # Compare values
                match, reason = compare_values(ext_value, gt_value)

                if match:
                    matched_fields += 1
                    status = "✓ MATCH"
                else:
                    status = f"✗ MISMATCH ({reason})"

                field_results.append({
                    "field": field_path,
                    "status": status,
                    "extracted": ext_value,
                    "ground_truth": gt_value,
                    "match": match
                })

                print(f"{status:20} | {field_path:40}")
            else:
                field_results.append({
                    "field": field_path,
                    "status": "✗ NOT FOUND",
                    "extracted": None,
                    "ground_truth": gt_value,
                    "match": False
                })
                print(f"{'✗ NOT FOUND':20} | {field_path:40}")

            # Recurse for nested dicts
            if isinstance(gt_value, dict) and isinstance(ext_value, dict):
                validate_nested_dict(gt_value, ext_value, field_path)

    validate_nested_dict(ground_truth, result_dict)

    # Calculate metrics
    coverage = (total_fields / total_fields * 100) if total_fields > 0 else 0
    accuracy = (matched_fields / total_fields * 100) if total_fields > 0 else 0

    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"\n📊 METRICS:")
    print(f"   • Total ground truth fields: {total_fields}")
    print(f"   • Fields found (coverage): {matched_fields}/{total_fields} = {coverage:.1f}%")
    print(f"   • Fields matched (accuracy): {matched_fields}/{total_fields} = {accuracy:.1f}%")

    # Save results
    output_path = "week3_day5_phase2b_validation_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metrics": {
                "total_fields": total_fields,
                "matched_fields": matched_fields,
                "coverage_percent": coverage,
                "accuracy_percent": accuracy
            },
            "field_results": field_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
