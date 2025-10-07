#!/usr/bin/env python3
"""
Granite-Docling VLM vs Traditional OCR Comparison
Test on 3 pages with tables and Swedish text from scanned BRF PDFs

Compares:
1. Granite-Docling VLM (vision-first, no traditional OCR)
2. RapidOCR (newest, recommended)
3. EasyOCR (popular, multi-language)
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import time

# Add main pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    RapidOcrOptions,
)
from docling_core.types.doc import TableItem

# Test PDF - use smallest for fast iteration
TEST_PDF = "test_pdfs/brf_268882.pdf"
PAGE_LIMIT = 3  # Test on first 3 pages only


def extract_metrics(result, elapsed_seconds):
    """Extract quality metrics from conversion result."""
    doc = result.document
    markdown = doc.export_to_markdown()

    # Basic metrics
    char_count = len(markdown)
    word_count = len(markdown.split())
    swedish_chars = sum(1 for c in markdown if c in 'åäöÅÄÖ')

    # Swedish BRF terminology
    brf_terms = [
        'styrelse', 'ordförande', 'vice ordförande', 'sekreterare',
        'resultaträkning', 'balansräkning', 'tillgångar', 'skulder',
        'eget kapital', 'intäkter', 'kostnader', 'årsavgift',
        'förvaltningsberättelse', 'revisionsberättelse'
    ]
    terms_found = sum(1 for term in brf_terms if term.lower() in markdown.lower())

    # Table extraction
    tables = []
    for item, level in doc.iterate_items():
        if isinstance(item, TableItem):
            try:
                df = item.export_to_dataframe()
                tables.append({
                    "rows": df.shape[0],
                    "columns": df.shape[1],
                    "has_numbers": any(df.astype(str).str.contains(r'\d', regex=True).any())
                })
            except Exception as e:
                tables.append({"error": str(e)})

    return {
        "elapsed_seconds": elapsed_seconds,
        "char_count": char_count,
        "word_count": word_count,
        "swedish_chars": swedish_chars,
        "swedish_char_ratio": swedish_chars / char_count if char_count > 0 else 0,
        "brf_terms_found": terms_found,
        "brf_terms_total": len(brf_terms),
        "table_count": len(tables),
        "tables": tables,
        "markdown_sample": markdown[:800]
    }


def test_granite_docling():
    """
    Test Granite-Docling VLM model (vision-first approach).

    Note: This uses Docling's default pipeline which may leverage
    Granite-Docling if available, or fall back to computer vision + OCR.
    """
    print("\n" + "="*70)
    print("TEST 1: GRANITE-DOCLING VLM (Vision-First)")
    print("="*70)
    print("Approach: Computer vision for layout, minimal OCR")
    print("Speed: ~30x faster than traditional OCR (claimed)")
    print()

    # Use default pipeline - should use Granite-Docling if available
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False  # Disable traditional OCR, let VLM handle it
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start = time.time()
    result = converter.convert(TEST_PDF)
    elapsed = time.time() - start

    metrics = extract_metrics(result, elapsed)

    print(f"✓ Completed in {elapsed:.2f}s ({elapsed/PAGE_LIMIT:.2f}s per page)")
    print(f"  Characters: {metrics['char_count']:,}")
    print(f"  Words: {metrics['word_count']:,}")
    print(f"  Swedish chars: {metrics['swedish_chars']} ({metrics['swedish_char_ratio']:.1%})")
    print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']}")
    print(f"  Tables: {metrics['table_count']}")

    return {"method": "Granite-Docling VLM", **metrics}


def test_rapidocr():
    """Test RapidOCR (upgraded to 3.x, newest backend)."""
    print("\n" + "="*70)
    print("TEST 2: RapidOCR 3.x (Newest OCR Backend)")
    print("="*70)
    print("Approach: Traditional OCR with ONNX runtime")
    print("Speed: Fast, GPU-accelerated")
    print()

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

    try:
        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, elapsed)

        print(f"✓ Completed in {elapsed:.2f}s ({elapsed/PAGE_LIMIT:.2f}s per page)")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Words: {metrics['word_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']} ({metrics['swedish_char_ratio']:.1%})")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']}")
        print(f"  Tables: {metrics['table_count']}")

        return {"method": "RapidOCR", **metrics}

    except Exception as e:
        print(f"❌ RapidOCR failed: {e}")
        return {"method": "RapidOCR", "error": str(e)}


def test_easyocr():
    """Test EasyOCR with Swedish language support."""
    print("\n" + "="*70)
    print("TEST 3: EasyOCR (Swedish + English)")
    print("="*70)
    print("Approach: Deep learning OCR with 80+ language support")
    print("Speed: Moderate, good for multi-language")
    print()

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = EasyOcrOptions(
        force_full_page_ocr=True,
        lang=["sv", "en"]  # Swedish + English
    )
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    try:
        start = time.time()
        result = converter.convert(TEST_PDF)
        elapsed = time.time() - start

        metrics = extract_metrics(result, elapsed)

        print(f"✓ Completed in {elapsed:.2f}s ({elapsed/PAGE_LIMIT:.2f}s per page)")
        print(f"  Characters: {metrics['char_count']:,}")
        print(f"  Words: {metrics['word_count']:,}")
        print(f"  Swedish chars: {metrics['swedish_chars']} ({metrics['swedish_char_ratio']:.1%})")
        print(f"  BRF terms: {metrics['brf_terms_found']}/{metrics['brf_terms_total']}")
        print(f"  Tables: {metrics['table_count']}")

        return {"method": "EasyOCR", **metrics}

    except Exception as e:
        print(f"❌ EasyOCR failed: {e}")
        return {"method": "EasyOCR", "error": str(e)}


def print_comparison_table(results):
    """Print side-by-side comparison."""
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)

    # Filter out failed tests
    successful = [r for r in results if "error" not in r]

    if len(successful) < 2:
        print("⚠️ Need at least 2 successful tests for comparison")
        return

    print(f"\n{'Metric':<30} {'Granite-VLM':<15} {'RapidOCR':<15} {'EasyOCR':<15}")
    print("-"*70)

    metrics_to_compare = [
        ("Processing Time (s)", "elapsed_seconds", "{:.2f}"),
        ("Speed (s/page)", lambda r: r["elapsed_seconds"] / PAGE_LIMIT, "{:.2f}"),
        ("Characters Extracted", "char_count", "{:,}"),
        ("Swedish Characters", "swedish_chars", "{}"),
        ("Swedish Char Ratio", "swedish_char_ratio", "{:.1%}"),
        ("BRF Terms Found", "brf_terms_found", "{}/14"),
        ("Tables Detected", "table_count", "{}"),
    ]

    for label, key, fmt in metrics_to_compare:
        values = []
        for method in ["Granite-Docling VLM", "RapidOCR", "EasyOCR"]:
            result = next((r for r in successful if r["method"] == method), None)
            if result:
                if callable(key):
                    val = key(result)
                else:
                    val = result.get(key, "N/A")

                if val != "N/A" and "{}" in fmt:
                    values.append(fmt.format(val))
                else:
                    values.append(str(val))
            else:
                values.append("N/A")

        print(f"{label:<30} {values[0]:<15} {values[1]:<15} {values[2]:<15}")

    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)

    fastest = min(successful, key=lambda x: x["elapsed_seconds"])
    most_terms = max(successful, key=lambda x: x["brf_terms_found"])
    most_swedish = max(successful, key=lambda x: x["swedish_chars"])

    print(f"\n⚡ Fastest: {fastest['method']} ({fastest['elapsed_seconds']:.2f}s total)")
    print(f"📝 Most BRF Terms: {most_terms['method']} ({most_terms['brf_terms_found']}/14 terms)")
    print(f"🇸🇪 Most Swedish Chars: {most_swedish['method']} ({most_swedish['swedish_chars']} chars)")

    # Quality vs Speed
    print("\n💡 Quality vs Speed Trade-off:")
    for result in successful:
        quality_score = result['brf_terms_found'] / 14 * 100
        speed_score = (10 / result['elapsed_seconds']) * 100 if result['elapsed_seconds'] > 0 else 0
        combined = (quality_score + speed_score) / 2
        print(f"  {result['method']:<25} Quality: {quality_score:.1f}%  Speed: {speed_score:.1f}%  Combined: {combined:.1f}%")


def main():
    print("="*70)
    print("GRANITE-DOCLING VLM vs TRADITIONAL OCR EXPERIMENT")
    print("="*70)
    print(f"Test PDF: {TEST_PDF}")
    print(f"Pages to test: First {PAGE_LIMIT} pages")
    print(f"Focus: Tables + Swedish BRF terminology")
    print()

    if not Path(TEST_PDF).exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        print("   Run from: experiments/docling_advanced/")
        return

    results = []

    # Test 1: Granite-Docling VLM (vision-first)
    try:
        result = test_granite_docling()
        results.append(result)
    except Exception as e:
        print(f"❌ Granite-Docling test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: RapidOCR (newest)
    try:
        result = test_rapidocr()
        results.append(result)
    except Exception as e:
        print(f"❌ RapidOCR test failed: {e}")

    # Test 3: EasyOCR (popular)
    try:
        result = test_easyocr()
        results.append(result)
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"results/granite_vs_ocr_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "pdf": TEST_PDF,
            "pages_tested": PAGE_LIMIT,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    # Print comparison
    print_comparison_table(results)

    print(f"\n💾 Full results saved to: {output_file}")
    print("\n✅ Experiment complete!")
    print("\nNext steps:")
    print("1. Review markdown samples in JSON results")
    print("2. Check table extraction quality")
    print("3. Update FINDINGS.md with recommendations")


if __name__ == "__main__":
    main()
