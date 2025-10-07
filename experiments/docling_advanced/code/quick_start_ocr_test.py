#!/usr/bin/env python3
"""
Quick Start: OCR Engine Test for Scanned Swedish BRF PDFs

Run this first to compare EasyOCR vs Tesseract on Swedish text.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add main pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TesseractOcrOptions,
)

# Start with smallest PDF for fast iteration
TEST_PDF = "test_pdfs/brf_268882.pdf"

def test_easyocr():
    """Test EasyOCR with Swedish language support."""
    print("\n" + "="*60)
    print("TESTING: EasyOCR (Swedish + English)")
    print("="*60)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = EasyOcrOptions(
        force_full_page_ocr=True,
        lang=["sv", "en"]  # Swedish and English
    )

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start = datetime.now()
    result = converter.convert(TEST_PDF)
    elapsed = (datetime.now() - start).total_seconds()

    markdown = result.document.export_to_markdown()

    # Quality metrics
    char_count = len(markdown)
    word_count = len(markdown.split())
    swedish_chars = sum(1 for c in markdown if c in 'åäöÅÄÖ')

    # Check for common Swedish BRF terms
    swedish_terms = ['styrelse', 'ordförande', 'resultaträkning', 'balansräkning',
                     'tillgångar', 'skulder', 'eget kapital']
    terms_found = sum(1 for term in swedish_terms if term.lower() in markdown.lower())

    print(f"✓ Completed in {elapsed:.1f}s")
    print(f"  Characters: {char_count:,}")
    print(f"  Words: {word_count:,}")
    print(f"  Swedish chars (å,ä,ö): {swedish_chars}")
    print(f"  BRF terms found: {terms_found}/{len(swedish_terms)}")

    print(f"\nFirst 300 characters:")
    print("-" * 60)
    print(markdown[:300])
    print("-" * 60)

    return {
        "engine": "EasyOCR",
        "languages": ["sv", "en"],
        "elapsed_seconds": elapsed,
        "char_count": char_count,
        "word_count": word_count,
        "swedish_chars": swedish_chars,
        "brf_terms_found": terms_found,
        "markdown_sample": markdown[:500]
    }


def test_tesseract():
    """Test Tesseract OCR with Swedish language support."""
    print("\n" + "="*60)
    print("TESTING: Tesseract (Swedish + English)")
    print("="*60)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = TesseractOcrOptions(
        force_full_page_ocr=True,
        lang=["swe", "eng"]  # Note: Tesseract uses 'swe', not 'sv'
    )

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    try:
        start = datetime.now()
        result = converter.convert(TEST_PDF)
        elapsed = (datetime.now() - start).total_seconds()

        markdown = result.document.export_to_markdown()

        char_count = len(markdown)
        word_count = len(markdown.split())
        swedish_chars = sum(1 for c in markdown if c in 'åäöÅÄÖ')

        swedish_terms = ['styrelse', 'ordförande', 'resultaträkning', 'balansräkning',
                         'tillgångar', 'skulder', 'eget kapital']
        terms_found = sum(1 for term in swedish_terms if term.lower() in markdown.lower())

        print(f"✓ Completed in {elapsed:.1f}s")
        print(f"  Characters: {char_count:,}")
        print(f"  Words: {word_count:,}")
        print(f"  Swedish chars (å,ä,ö): {swedish_chars}")
        print(f"  BRF terms found: {terms_found}/{len(swedish_terms)}")

        print(f"\nFirst 300 characters:")
        print("-" * 60)
        print(markdown[:300])
        print("-" * 60)

        return {
            "engine": "Tesseract",
            "languages": ["swe", "eng"],
            "elapsed_seconds": elapsed,
            "char_count": char_count,
            "word_count": word_count,
            "swedish_chars": swedish_chars,
            "brf_terms_found": terms_found,
            "markdown_sample": markdown[:500]
        }

    except Exception as e:
        print(f"❌ Tesseract failed: {e}")
        print("   (Tesseract may not be installed or Swedish language pack missing)")
        return {
            "engine": "Tesseract",
            "error": str(e)
        }


def main():
    print("="*60)
    print("OCR ENGINE QUICK START TEST")
    print("="*60)
    print(f"PDF: {TEST_PDF}")
    print(f"Purpose: Compare OCR quality for Swedish BRF documents")
    print()

    if not Path(TEST_PDF).exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        print("   Run from: experiments/docling_advanced/")
        return

    results = []

    # Test EasyOCR (most likely to work out of the box)
    try:
        result = test_easyocr()
        results.append(result)
    except Exception as e:
        print(f"❌ EasyOCR failed: {e}")
        import traceback
        traceback.print_exc()

    # Test Tesseract (may require installation)
    try:
        result = test_tesseract()
        results.append(result)
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")

    # Save results
    output_file = f"results/quick_ocr_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "pdf": TEST_PDF,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    if len(results) >= 2:
        print(f"{'Metric':<25} {'EasyOCR':<15} {'Tesseract':<15}")
        print("-"*60)
        print(f"{'Processing Time (s)':<25} {results[0]['elapsed_seconds']:<15.1f} {results[1].get('elapsed_seconds', 'N/A')}")
        print(f"{'Words Extracted':<25} {results[0]['word_count']:<15,} {results[1].get('word_count', 'N/A')}")
        print(f"{'Swedish Characters':<25} {results[0]['swedish_chars']:<15} {results[1].get('swedish_chars', 'N/A')}")
        print(f"{'BRF Terms Found':<25} {results[0]['brf_terms_found']:<15} {results[1].get('brf_terms_found', 'N/A')}")

        # Recommendation
        print("\n📊 Recommendation:")
        if results[0]['brf_terms_found'] >= results[1].get('brf_terms_found', 0):
            print("   ✅ EasyOCR performs better for Swedish BRF terminology")
        else:
            print("   ✅ Tesseract performs better for Swedish BRF terminology")

    print(f"\n💾 Full results saved to: {output_file}")
    print("\n✅ Quick start test complete!")
    print("\nNext steps:")
    print("1. Review results in results/ directory")
    print("2. Run full comparison: python code/test_ocr_engines.py")
    print("3. Test table extraction: python code/test_table_extraction.py")


if __name__ == "__main__":
    main()
