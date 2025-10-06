#!/usr/bin/env python3
"""
Test property designation extraction on brf_198532.pdf
Expected result: "Sonfjället 2"
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.property_designation import PropertyDesignationExtractor

def test_property_designation_extraction():
    """Test property designation extraction from markdown."""

    # Sample markdown text from brf_198532.pdf (page 2)
    test_markdown = """
    ÅRSREDOVISNING
    Bostadsrättsföreningen Björk och Plaza

    FÖRVALTNINGSBERÄTTELSE

    Styrelsen för Bostadsrättsföreningen Björk och Plaza får härmed avge
    årsredovisning för 2023.

    ALLMÄNT OM VERKSAMHETEN

    Organisationsnummer: 716433-6651
    Säte: Stockholm
    Fastighetsbeteckning: Sonfjället 2

    Föreningens ändamål är att främja medlemmarnas ekonomiska intressen genom
    att i föreningens hus upplåta lägenheter under bostadsrätt.
    """

    extractor = PropertyDesignationExtractor()
    result = extractor.extract_property_designation(test_markdown)

    print("Testing property designation extraction...")
    print(f"  Input text snippet: 'Fastighetsbeteckning: Sonfjället 2'")
    print(f"  Extracted: {result}")
    print(f"  Expected: Sonfjället 2")

    if result == "Sonfjället 2":
        print("  ✅ TEST PASSED")
        return True
    else:
        print("  ❌ TEST FAILED")
        return False

def test_full_pipeline():
    """Test full extraction pipeline with property designation."""

    from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

    pdf_path = "SRS/brf_198532.pdf"

    if not os.path.exists(pdf_path):
        print(f"⚠️ Test PDF not found: {pdf_path}")
        print("Skipping full pipeline test")
        return None

    print("\nTesting full extraction pipeline...")
    print(f"  PDF: {pdf_path}")

    extractor = RobustUltraComprehensiveExtractor()
    result = extractor.extract_brf_document(pdf_path, mode="deep")

    property_designation = result.get("property_agent", {}).get("property_designation")

    print(f"\n  Property designation extracted: {property_designation}")
    print(f"  Expected: Sonfjället 2")

    if property_designation == "Sonfjället 2":
        print("  ✅ FULL PIPELINE TEST PASSED")
        return True
    else:
        print("  ❌ FULL PIPELINE TEST FAILED")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Property Designation Extraction Test")
    print("="*60)
    print()

    # Test 1: Standalone extractor
    test1_passed = test_property_designation_extraction()

    # Test 2: Full pipeline (if PDF available)
    test2_passed = test_full_pipeline()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  Standalone extractor: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    if test2_passed is not None:
        print(f"  Full pipeline: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    else:
        print(f"  Full pipeline: ⊘ SKIPPED (PDF not found)")
    print("="*60)

    sys.exit(0 if test1_passed else 1)
