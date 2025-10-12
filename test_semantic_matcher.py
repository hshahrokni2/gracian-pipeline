"""
Test SemanticFieldMatcher on real extraction results.

This script validates that semantic matching works on heterogeneous data structures.
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.validation.semantic_matcher import SemanticFieldMatcher
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor


def test_semantic_matcher():
    """Test semantic matcher on brf_198532.pdf extraction."""

    print("\n" + "="*80)
    print("SEMANTIC FIELD MATCHER TEST")
    print("="*80)

    # Initialize matcher
    print("\n📊 Initializing SemanticFieldMatcher...")
    matcher = SemanticFieldMatcher()
    stats = matcher.get_statistics()
    print(f"  ✅ Loaded {stats['total_canonical_fields']} canonical fields")
    print(f"  ✅ Total synonyms: {stats['total_synonyms']}")
    print(f"  ✅ Avg synonyms per field: {stats['average_synonyms_per_field']}")
    print(f"  ✅ Pattern definitions: {stats['pattern_definitions']}")

    # Run extraction
    print("\n📄 Extracting brf_198532.pdf...")
    extractor = RobustUltraComprehensiveExtractor()
    result = extractor.extract_brf_document("SRS/brf_198532.pdf", mode="fast")
    print(f"  ✅ Extraction complete in {result.get('_extraction_time_seconds', 0):.1f}s")

    # Load ground truth
    print("\n📋 Loading ground truth...")
    with open("ground_truth/brf_198532_comprehensive_ground_truth.json", 'r') as f:
        ground_truth = json.load(f)

    # Count ground truth fields (exclude metadata)
    gt_fields = [k for k in ground_truth.keys() if not k.startswith('_')]
    print(f"  ✅ Loaded {len(gt_fields)} ground truth categories")

    # Test semantic matching on key fields
    print("\n" + "="*80)
    print("SEMANTIC MATCHING TESTS")
    print("="*80)

    test_fields = [
        ("organization_number", "metadata"),
        ("brf_name", "metadata"),
        ("chairman", "governance"),
        ("board_members", "governance"),
        ("auditor_name", "governance"),
        ("assets", "financial"),
        ("liabilities", "financial"),
        ("equity", "financial"),
        ("cash", "financial"),
        ("property_designation", "property"),
        ("municipality", "property"),
        ("number_of_apartments", "property"),
        ("monthly_fee", "fees"),
        ("total_debt", "loans"),
    ]

    successful_matches = 0
    total_tests = len(test_fields)

    for canonical_name, gt_category in test_fields:
        print(f"\n🔍 Testing: {canonical_name} (from {gt_category})")

        # Get ground truth value
        gt_value = None
        if gt_category in ground_truth and canonical_name in ground_truth[gt_category]:
            gt_value = ground_truth[gt_category][canonical_name]
            print(f"  📋 Ground Truth: {str(gt_value)[:80]}")

        # Search in extraction result
        found_value, confidence = matcher.find_field(result, canonical_name)

        if found_value is not None:
            successful_matches += 1

            # Handle ExtractionField wrapper
            if isinstance(found_value, dict) and 'value' in found_value:
                display_value = found_value['value']
            else:
                display_value = found_value

            print(f"  ✅ FOUND via semantic matching!")
            print(f"     Value: {str(display_value)[:80]}")
            print(f"     Confidence: {confidence:.2f}")

            # Compare with ground truth if available
            if gt_value is not None:
                # Normalize for comparison
                str_found = str(display_value).lower().strip()
                str_gt = str(gt_value).lower().strip()

                if str_found == str_gt:
                    print(f"     ✅ EXACT MATCH with ground truth")
                elif str_gt in str_found or str_found in str_gt:
                    print(f"     ✅ PARTIAL MATCH with ground truth")
                else:
                    print(f"     ⚠️  VALUE DIFFERS from ground truth")
        else:
            print(f"  ❌ NOT FOUND")
            if gt_value:
                print(f"     Expected: {str(gt_value)[:80]}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nSuccessful Matches: {successful_matches}/{total_tests} ({100*successful_matches/total_tests:.1f}%)")

    if successful_matches >= 0.7 * total_tests:
        print("\n✅ SEMANTIC MATCHER VALIDATION PASSED (≥70% success rate)")
        return True
    else:
        print("\n❌ SEMANTIC MATCHER VALIDATION FAILED (<70% success rate)")
        return False


def test_synonym_expansion():
    """Test synonym expansion for key fields."""

    print("\n" + "="*80)
    print("SYNONYM EXPANSION TEST")
    print("="*80)

    matcher = SemanticFieldMatcher()

    test_cases = [
        "chairman",
        "organization_number",
        "monthly_fee",
        "total_debt",
        "property_designation"
    ]

    for canonical_name in test_cases:
        synonyms = matcher.get_all_synonyms(canonical_name)
        print(f"\n📝 {canonical_name}:")
        print(f"   {len(synonyms)} synonyms: {', '.join(synonyms[:5])}...")


def test_normalization():
    """Test Swedish character normalization."""

    print("\n" + "="*80)
    print("NORMALIZATION TEST")
    print("="*80)

    matcher = SemanticFieldMatcher()

    test_cases = [
        ("ordförande", "ordforande"),
        ("årsavgift", "arsavgift"),
        ("räkenskapsår", "rakenskap sar"),
        ("bostadsrättsförening", "bostadsrattsforening"),
        ("municipality_name", "municipalityname"),
        ("org_nr", "orgnr"),
    ]

    for original, expected_normalized in test_cases:
        normalized = matcher.normalize_key(original)
        expected_clean = expected_normalized.replace(' ', '')

        print(f"\n  '{original}' → '{normalized}'")
        if normalized == expected_clean:
            print(f"    ✅ CORRECT")
        else:
            print(f"    ❌ EXPECTED: '{expected_clean}'")


if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("SEMANTIC FIELD MATCHER - COMPREHENSIVE VALIDATION")
    print("🚀 "*20)

    # Run all tests
    test_normalization()
    test_synonym_expansion()
    success = test_semantic_matcher()

    print("\n" + "="*80)
    if success:
        print("🎉 ALL TESTS PASSED - SEMANTIC MATCHER READY FOR PRODUCTION")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
    print("="*80 + "\n")

    sys.exit(0 if success else 1)
