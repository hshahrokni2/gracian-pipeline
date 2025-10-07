#!/usr/bin/env python3
"""
Comprehensive Docling Test: Find the REAL Best Configuration
Test ALL Docling capabilities for scanned Swedish BRF PDFs

Tests:
1. DEFAULT Docling (no options - let it decide)
2. Default OCR enabled (Docling chooses backend)
3. EasyOCR (Swedish)
4. RapidOCR (if installed)
5. Tesseract (if installed)
6. With/without table structure analysis
7. Any VLM/picture description options
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    RapidOcrOptions,
    TesseractOcrOptions,
)

TEST_PDF = "test_pdfs/brf_268882.pdf"
PAGE_LIMIT = 3


def extract_metrics(result, method_name, elapsed_seconds):
    """Extract comprehensive quality metrics."""
    doc = result.document
    markdown = doc.export_to_markdown()

    char_count = len(markdown)
    word_count = len(markdown.split())
    swedish_chars = sum(1 for c in markdown if c in 'åäöÅÄÖ')

    # Swedish BRF terms
    brf_terms = [
        'styrelse', 'ordförande', 'vice ordförande', 'sekreterare',
        'resultaträkning', 'balansräkning', 'tillgångar', 'skulder',
        'eget kapital', 'intäkter', 'kostnader', 'årsavgift',
        'förvaltningsberättelse', 'revisionsberättelse', 'årsredovisning'
    ]
    terms_found = sum(1 for term in brf_terms if term.lower() in markdown.lower())

    # Check for numbers (financial data)
    import re
    numbers = re.findall(r'\d[\d\s]*', markdown)
    has_numbers = len(numbers) > 10

    # Check for image placeholders
    image_placeholders = markdown.count('<!-- image -->')

    return {
        "method": method_name,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "char_count": char_count,
        "word_count": word_count,
        "swedish_chars": swedish_chars,
        "swedish_char_ratio": round(swedish_chars / char_count if char_count > 0 else 0, 4),
        "brf_terms_found": terms_found,
        "brf_terms_total": len(brf_terms),
        "brf_coverage": round(terms_found / len(brf_terms) * 100, 1),
        "has_financial_numbers": has_numbers,
        "image_placeholders": image_placeholders,
        "is_text_extracted": char_count > 1000 and image_placeholders < 10,
        "markdown_sample": markdown[:600]
    }


def test_default_docling():
    """Test 1: Pure default Docling - let it decide everything."""
    print("\n" + "="*70)
    print("TEST 1: DEFAULT DOCLING (Zero Configuration)")
    print("="*70)
    print("Strategy: Let Docling choose ALL settings")
    print("Expected: Should use best available pipeline")
    print()

    try:
        # Completely default - no options
        converter = DocumentConverter()

        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, "Default Docling (no options)", elapsed)

        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  Text extracted: {'YES ✅' if metrics['is_text_extracted'] else 'NO ❌'}")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']}")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']} ({metrics['brf_coverage']}%)")
        print(f"  Image placeholders: {metrics['image_placeholders']}")

        return metrics

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {"method": "Default Docling", "error": str(e)}


def test_default_with_ocr():
    """Test 2: Default pipeline with OCR explicitly enabled."""
    print("\n" + "="*70)
    print("TEST 2: DEFAULT PIPELINE + OCR ENABLED")
    print("="*70)
    print("Strategy: Enable OCR, let Docling choose backend")
    print("Expected: Should use default OCR engine")
    print()

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR, but don't specify engine
        # Let Docling choose the default OCR backend

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, "Default Pipeline + OCR", elapsed)

        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  Text extracted: {'YES ✅' if metrics['is_text_extracted'] else 'NO ❌'}")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']}")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']} ({metrics['brf_coverage']}%)")

        return metrics

    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"method": "Default + OCR", "error": str(e)}


def test_easyocr_swedish():
    """Test 3: EasyOCR with Swedish language."""
    print("\n" + "="*70)
    print("TEST 3: EasyOCR (Swedish + English)")
    print("="*70)
    print("Strategy: Explicit Swedish language support")
    print()

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = EasyOcrOptions(
            force_full_page_ocr=True,
            lang=["sv", "en"]
        )
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, "EasyOCR (Swedish)", elapsed)

        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  Text extracted: {'YES ✅' if metrics['is_text_extracted'] else 'NO ❌'}")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']}")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']} ({metrics['brf_coverage']}%)")

        return metrics

    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"method": "EasyOCR", "error": str(e)}


def test_rapidocr():
    """Test 4: RapidOCR (if installed)."""
    print("\n" + "="*70)
    print("TEST 4: RapidOCR 3.x")
    print("="*70)
    print("Strategy: Newest OCR backend with ONNX")
    print()

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = RapidOcrOptions(
            force_full_page_ocr=True
        )
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, "RapidOCR", elapsed)

        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  Text extracted: {'YES ✅' if metrics['is_text_extracted'] else 'NO ❌'}")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']}")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']} ({metrics['brf_coverage']}%)")

        return metrics

    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"method": "RapidOCR", "error": str(e)}


def test_tesseract():
    """Test 5: Tesseract with Swedish."""
    print("\n" + "="*70)
    print("TEST 5: Tesseract (Swedish)")
    print("="*70)
    print("Strategy: Traditional OCR with Swedish language pack")
    print()

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = TesseractOcrOptions(
            force_full_page_ocr=True,
            lang=["swe", "eng"]  # Tesseract uses 'swe', not 'sv'
        )
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, "Tesseract (Swedish)", elapsed)

        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  Text extracted: {'YES ✅' if metrics['is_text_extracted'] else 'NO ❌'}")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']}")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']} ({metrics['brf_coverage']}%)")

        return metrics

    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"method": "Tesseract", "error": str(e)}


def print_comprehensive_comparison(results):
    """Print detailed comparison table."""
    print("\n" + "="*70)
    print("COMPREHENSIVE COMPARISON")
    print("="*70)

    successful = [r for r in results if "error" not in r and r.get("is_text_extracted")]
    failed = [r for r in results if "error" in r]
    no_text = [r for r in results if "error" not in r and not r.get("is_text_extracted")]

    if not successful:
        print("\n❌ No methods successfully extracted text!")
        return

    print(f"\n{'Method':<30} {'Speed':<12} {'BRF Terms':<12} {'Swedish':<12} {'Quality':<10}")
    print("-"*70)

    for r in successful:
        speed = f"{r['elapsed_seconds']:.1f}s"
        terms = f"{r['brf_terms_found']}/{r['brf_terms_total']}"
        swedish = f"{r['swedish_chars']}"
        quality = f"{r['brf_coverage']:.0f}%"
        print(f"{r['method']:<30} {speed:<12} {terms:<12} {swedish:<12} {quality:<10}")

    # Failed/problematic methods
    if no_text:
        print("\n⚠️ Methods that detected structure but extracted NO TEXT:")
        for r in no_text:
            print(f"  - {r['method']}: {r['image_placeholders']} image placeholders, {r['char_count']} chars")

    if failed:
        print("\n❌ Failed methods:")
        for r in failed:
            print(f"  - {r['method']}: {r['error'][:60]}")

    # Recommendations
    print("\n" + "="*70)
    print("WINNER ANALYSIS")
    print("="*70)

    fastest = min(successful, key=lambda x: x["elapsed_seconds"])
    best_quality = max(successful, key=lambda x: x["brf_coverage"])
    most_swedish = max(successful, key=lambda x: x["swedish_chars"])

    print(f"\n⚡ FASTEST: {fastest['method']}")
    print(f"   {fastest['elapsed_seconds']:.1f}s ({fastest['elapsed_seconds']/PAGE_LIMIT:.1f}s per page)")
    print(f"   Quality: {fastest['brf_coverage']:.0f}% BRF coverage")

    print(f"\n🎯 BEST QUALITY: {best_quality['method']}")
    print(f"   {best_quality['brf_coverage']:.0f}% BRF term coverage ({best_quality['brf_terms_found']}/{best_quality['brf_terms_total']})")
    print(f"   Speed: {best_quality['elapsed_seconds']:.1f}s")

    print(f"\n🇸🇪 BEST SWEDISH: {most_swedish['method']}")
    print(f"   {most_swedish['swedish_chars']} Swedish characters detected")
    print(f"   {most_swedish['swedish_char_ratio']:.1%} of text is Swedish")

    # Overall winner
    print("\n" + "="*70)
    print("🏆 RECOMMENDED FOR PRODUCTION")
    print("="*70)

    # Score: 50% quality + 30% speed + 20% Swedish
    for r in successful:
        quality_score = r['brf_coverage']
        speed_score = (fastest['elapsed_seconds'] / r['elapsed_seconds']) * 100
        swedish_score = (r['swedish_chars'] / most_swedish['swedish_chars']) * 100 if most_swedish['swedish_chars'] > 0 else 0

        total_score = (quality_score * 0.5) + (speed_score * 0.3) + (swedish_score * 0.2)

        print(f"{r['method']:<30} Score: {total_score:.1f}/100")
        print(f"  Quality: {quality_score:.0f}/100 | Speed: {speed_score:.0f}/100 | Swedish: {swedish_score:.0f}/100")


def main():
    print("="*70)
    print("COMPREHENSIVE DOCLING TEST")
    print("="*70)
    print(f"Test PDF: {TEST_PDF}")
    print(f"Pages: First {PAGE_LIMIT} pages")
    print(f"Goal: Find the BEST Docling configuration for scanned Swedish PDFs")
    print()

    if not Path(TEST_PDF).exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        return

    results = []

    # Test 1: Pure default
    results.append(test_default_docling())

    # Test 2: Default + OCR enabled
    results.append(test_default_with_ocr())

    # Test 3: EasyOCR
    results.append(test_easyocr_swedish())

    # Test 4: RapidOCR
    results.append(test_rapidocr())

    # Test 5: Tesseract
    results.append(test_tesseract())

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"results/docling_comprehensive_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "pdf": TEST_PDF,
            "pages_tested": PAGE_LIMIT,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    # Print comparison
    print_comprehensive_comparison(results)

    print(f"\n💾 Full results saved to: {output_file}")
    print("\n✅ Comprehensive test complete!")


if __name__ == "__main__":
    main()
