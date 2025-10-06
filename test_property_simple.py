#!/usr/bin/env python3
"""
Simple test: Extract property designation from PDF using docling markdown.
This tests the property designation extractor without running the full pipeline.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.property_designation import PropertyDesignationExtractor
from docling.document_converter import DocumentConverter

def test_pdf_property_designation():
    """Test property designation extraction on real PDF."""

    pdf_path = "SRS/brf_198532.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False

    print("Testing property designation extraction on real PDF...")
    print(f"  PDF: {pdf_path}")

    # Extract markdown using docling
    print("  → Converting PDF with docling...")
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    markdown = result.document.export_to_markdown()

    print(f"  → Extracted {len(markdown)} characters of markdown")

    # Extract property designation
    extractor = PropertyDesignationExtractor()
    property_designation = extractor.extract_property_designation(markdown)

    print(f"\n  Extracted: {property_designation}")
    print(f"  Expected: Sonfjället 2")

    if property_designation == "Sonfjället 2":
        print("  ✅ TEST PASSED - Property designation correctly extracted!")
        return True
    else:
        print("  ❌ TEST FAILED - Unexpected value")
        # Debug: show context around property designation
        if "Fastighetsbeteckning" in markdown:
            idx = markdown.index("Fastighetsbeteckning")
            context = markdown[max(0, idx-50):min(len(markdown), idx+100)]
            print(f"\n  Debug - Context from markdown:")
            print(f"  {context}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Simple Property Designation Test")
    print("="*60)
    print()

    success = test_pdf_property_designation()

    print("\n" + "="*60)
    print(f"RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    print("="*60)

    sys.exit(0 if success else 1)
