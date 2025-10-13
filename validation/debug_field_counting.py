"""
Debug Field Counting - Diagnostic Tool

This script extracts from a PDF and prints the complete structure to understand
what's being counted as "fields" and why we're getting >100% coverage.

Usage:
    python debug_field_counting.py

Author: Claude Code
Date: 2025-10-13
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel
import json
from typing import Any, Dict


def count_recursive(obj: Any, path: str = "", depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """
    Recursively analyze structure and categorize fields.

    Returns:
        Dict with categorized field counts
    """
    stats = {
        "total_keys": 0,
        "data_fields": 0,
        "metadata_fields": 0,
        "private_fields": 0,
        "nested_dicts": 0,
        "lists": 0,
        "null_values": 0,
        "field_paths": []
    }

    if depth > max_depth:
        return stats

    # Metadata field patterns
    METADATA_FIELDS = {
        "confidence", "source", "evidence_pages", "extraction_method",
        "model_used", "validation_status", "alternative_values",
        "extraction_timestamp", "original_string", "quality_score",
        "agent_name", "processing_time_ms", "tokens_used"
    }

    if isinstance(obj, dict):
        for key, value in obj.items():
            stats["total_keys"] += 1
            field_path = f"{path}.{key}" if path else key

            # Categorize field
            is_metadata = key in METADATA_FIELDS
            is_private = key.startswith("_")
            is_null = value is None or value == "" or value == [] or value == {}

            if is_metadata:
                stats["metadata_fields"] += 1
                category = "METADATA"
            elif is_private:
                stats["private_fields"] += 1
                category = "PRIVATE"
            elif is_null:
                stats["null_values"] += 1
                category = "NULL"
            else:
                stats["data_fields"] += 1
                category = "DATA"

            # Type analysis
            value_type = type(value).__name__
            if isinstance(value, dict):
                stats["nested_dicts"] += 1
                # Check if it's an ExtractionField (has 'value' key)
                is_extraction_field = "value" in value
                if is_extraction_field:
                    value_type = "ExtractionField"
            elif isinstance(value, list):
                stats["lists"] += 1
                value_type = f"list[{len(value)}]"

            # Record field
            field_info = {
                "path": field_path,
                "type": value_type,
                "category": category,
                "depth": depth
            }
            stats["field_paths"].append(field_info)

            # Print with indentation
            indent = "  " * depth
            print(f"{indent}{field_path}")
            print(f"{indent}  → Type: {value_type}, Category: {category}")

            # Recurse into nested structures
            if isinstance(value, dict) and depth < max_depth:
                # Don't recurse into ExtractionField metadata
                if "value" not in value or category == "DATA":
                    nested_stats = count_recursive(value, field_path, depth + 1, max_depth)
                    # Merge stats
                    for k in ["total_keys", "data_fields", "metadata_fields",
                             "private_fields", "nested_dicts", "lists", "null_values"]:
                        stats[k] += nested_stats[k]
                    stats["field_paths"].extend(nested_stats["field_paths"])

            elif isinstance(value, list) and depth < max_depth:
                # Recurse into first item only (to avoid huge output)
                if len(value) > 0 and isinstance(value[0], dict):
                    print(f"{indent}  → [Recursing into first list item...]")
                    nested_stats = count_recursive(value[0], f"{field_path}[0]", depth + 1, max_depth)
                    # Multiply by list length for total count estimate
                    for k in ["total_keys", "data_fields", "metadata_fields",
                             "private_fields", "nested_dicts", "lists", "null_values"]:
                        stats[k] += nested_stats[k] * len(value)
                    # Don't multiply field_paths (just show one example)
                    stats["field_paths"].extend(nested_stats["field_paths"])

    return stats


def diagnose_extraction(pdf_path: str):
    """Extract and analyze field counting."""

    print(f"{'='*80}")
    print(f"FIELD COUNTING DIAGNOSTIC")
    print(f"{'='*80}")
    print(f"PDF: {Path(pdf_path).name}\n")

    # Extract
    print("🔄 Extracting...")
    result = extract_all_agents_parallel(pdf_path)
    print("   ✅ Extraction complete\n")

    # 1. Top-level structure
    print(f"{'='*80}")
    print(f"TOP-LEVEL KEYS")
    print(f"{'='*80}")
    for i, key in enumerate(result.keys(), 1):
        value = result[key]
        value_type = type(value).__name__
        if isinstance(value, dict):
            value_type = f"dict[{len(value)} keys]"
        elif isinstance(value, list):
            value_type = f"list[{len(value)} items]"

        is_private = key.startswith("_")
        print(f"{i:2d}. {key:30s} {value_type:20s} {'[PRIVATE]' if is_private else ''}")

    # 2. Detailed field analysis
    print(f"\n{'='*80}")
    print(f"DETAILED FIELD STRUCTURE")
    print(f"{'='*80}\n")

    stats = count_recursive(result, max_depth=2)  # Limit depth for readability

    # 3. Summary statistics
    print(f"\n{'='*80}")
    print(f"FIELD COUNTING SUMMARY")
    print(f"{'='*80}")
    print(f"Total Keys: {stats['total_keys']}")
    print(f"  DATA Fields: {stats['data_fields']} ← SHOULD BE COUNTED")
    print(f"  METADATA Fields: {stats['metadata_fields']} ← SHOULD BE EXCLUDED")
    print(f"  PRIVATE Fields: {stats['private_fields']} ← SHOULD BE EXCLUDED")
    print(f"  NULL Values: {stats['null_values']} ← SHOULD BE EXCLUDED")
    print(f"Nested Dicts: {stats['nested_dicts']}")
    print(f"Lists: {stats['lists']}")

    # 4. Field breakdown by depth
    print(f"\n{'='*80}")
    print(f"FIELDS BY DEPTH")
    print(f"{'='*80}")
    fields_by_depth = {}
    for field in stats["field_paths"]:
        depth = field["depth"]
        if depth not in fields_by_depth:
            fields_by_depth[depth] = {"DATA": 0, "METADATA": 0, "PRIVATE": 0, "NULL": 0}
        fields_by_depth[depth][field["category"]] += 1

    for depth in sorted(fields_by_depth.keys()):
        counts = fields_by_depth[depth]
        print(f"Depth {depth}: DATA={counts['DATA']}, "
              f"METADATA={counts['METADATA']}, "
              f"PRIVATE={counts['PRIVATE']}, "
              f"NULL={counts['NULL']}")

    # 5. Save full result
    output_file = Path(__file__).parent / "debug_extraction_full.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n✅ Full extraction saved to: {output_file.name}")

    # 6. Current vs expected count
    print(f"\n{'='*80}")
    print(f"COUNTING ANALYSIS")
    print(f"{'='*80}")
    print(f"Current validation shows: 113 fields extracted")
    print(f"Applicable fields detected: 91 fields")
    print(f"Coverage: 113/91 = 124.2% (IMPOSSIBLE!)")
    print(f"\nDiagnostic found:")
    print(f"  DATA fields: {stats['data_fields']}")
    print(f"  (If we only count DATA fields, coverage would be: {stats['data_fields']}/91 = "
          f"{stats['data_fields']/91*100:.1f}%)")

    # 7. Recommendations
    print(f"\n{'='*80}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*80}")

    if stats["metadata_fields"] > 0:
        print(f"⚠️  Found {stats['metadata_fields']} METADATA fields being counted")
        print(f"   → Ensure count_extracted_fields() excludes these")

    if stats["private_fields"] > 0:
        print(f"⚠️  Found {stats['private_fields']} PRIVATE fields (starting with _)")
        print(f"   → Add check: if key.startswith('_'): continue")

    if stats["null_values"] > 0:
        print(f"ℹ️  Found {stats['null_values']} NULL values (correctly excluded)")

    if stats["data_fields"] > 91:
        print(f"⚠️  DATA fields ({stats['data_fields']}) > Applicable (91)")
        print(f"   → Either: 1) Core fields list too conservative")
        print(f"   →     OR: 2) Some DATA fields are actually optional")

    print(f"\n{'='*80}")
    print(f"NEXT STEPS")
    print(f"{'='*80}")
    print(f"1. Review debug_extraction_full.json to see all fields")
    print(f"2. Update count_extracted_fields() to exclude METADATA and PRIVATE")
    print(f"3. Update ApplicableFieldsDetector core fields if needed")
    print(f"4. Re-run validation to verify fix")


if __name__ == "__main__":
    pdf_path = Path(__file__).parent / "test_pdfs" / "machine_readable.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    # Set API key
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY=your_key")
        sys.exit(1)

    diagnose_extraction(str(pdf_path))
