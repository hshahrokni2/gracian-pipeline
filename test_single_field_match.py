#!/usr/bin/env python3
"""
Test semantic matcher Strategy 1 fix - single field verification.
This tests that Strategy 1 now searches nested dictionaries correctly.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gracian_pipeline.validation.semantic_matcher import SemanticFieldMatcher

def test_nested_field_matching():
    """Test that Strategy 1 finds fields in nested structures."""

    matcher = SemanticFieldMatcher()

    # Test Case 1: Chairman in governance_agent
    extraction = {
        "governance_agent": {"chairman": "Elvy Maria Löfvenberg"}
    }

    value, confidence = matcher.find_field(extraction, "chairman")

    print("Test 1: Chairman in nested structure")
    print(f"  Search for: 'chairman'")
    print(f"  Structure: {extraction}")
    print(f"  Found value: {value}")
    print(f"  Confidence: {confidence}")
    print(f"  Expected: 'Elvy Maria Löfvenberg' with confidence 1.0")

    assert value == "Elvy Maria Löfvenberg", f"Expected 'Elvy Maria Löfvenberg', got {value}"
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"
    print("  ✅ PASS\n")

    # Test Case 2: Apartments in property_agent
    extraction2 = {
        "property_agent": {"apartments": 94}
    }

    value2, confidence2 = matcher.find_field(extraction2, "apartments")

    print("Test 2: Apartments in nested structure")
    print(f"  Search for: 'apartments'")
    print(f"  Structure: {extraction2}")
    print(f"  Found value: {value2}")
    print(f"  Confidence: {confidence2}")
    print(f"  Expected: 94 with confidence 1.0")

    assert value2 == 94, f"Expected 94, got {value2}"
    assert confidence2 == 1.0, f"Expected confidence 1.0, got {confidence2}"
    print("  ✅ PASS\n")

    # Test Case 3: Deep nesting (3 levels)
    extraction3 = {
        "level1": {
            "level2": {
                "revenue": 7451585
            }
        }
    }

    value3, confidence3 = matcher.find_field(extraction3, "revenue")

    print("Test 3: Deep nesting (3 levels)")
    print(f"  Search for: 'revenue'")
    print(f"  Structure: {extraction3}")
    print(f"  Found value: {value3}")
    print(f"  Confidence: {confidence3}")
    print(f"  Expected: 7451585 with confidence 1.0")

    assert value3 == 7451585, f"Expected 7451585, got {value3}"
    assert confidence3 == 1.0, f"Expected confidence 1.0, got {confidence3}"
    print("  ✅ PASS\n")

    # Test Case 4: Field in list of dicts
    extraction4 = {
        "governance_agent": {
            "board_members": [
                {"name": "Elvy Maria Löfvenberg", "role": "Ordförande"},
                {"name": "Torbjörn Andersson", "role": "Ledamot"}
            ]
        }
    }

    value4, confidence4 = matcher.find_field(extraction4, "board_members")

    print("Test 4: Field containing list")
    print(f"  Search for: 'board_members'")
    print(f"  Found value: {value4}")
    print(f"  Confidence: {confidence4}")
    print(f"  Expected: list with 2 members, confidence 1.0")

    assert isinstance(value4, list), f"Expected list, got {type(value4)}"
    assert len(value4) == 2, f"Expected 2 members, got {len(value4)}"
    assert confidence4 == 1.0, f"Expected confidence 1.0, got {confidence4}"
    print("  ✅ PASS\n")

    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
    print("\nStrategy 1 fix is working correctly:")
    print("  - Searches nested dictionaries recursively")
    print("  - Finds fields at any nesting depth")
    print("  - Returns confidence 1.0 for exact field name matches")
    print("  - Path-agnostic matching confirmed")

if __name__ == "__main__":
    test_nested_field_matching()
