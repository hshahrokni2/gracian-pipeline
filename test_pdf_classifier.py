#!/usr/bin/env python3
"""Test PDF classifier on sample PDFs."""

import sys
sys.path.insert(0, '/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline')

from gracian_pipeline.core.pdf_classifier import classify_pdf

# Test on 3 diverse PDFs
test_pdfs = [
    "Hjorthagen/brf_268882.pdf",  # Known machine-readable
    "SRS/brf_78906.pdf",          # Known low performer (likely scanned)
    "SRS/brf_198532.pdf",         # Ground truth PDF
]

print("\n" + "="*70)
print("PDF CLASSIFIER TEST RESULTS")
print("="*70)

for pdf_path in test_pdfs:
    try:
        result = classify_pdf(pdf_path)
        print(f"\n📄 {pdf_path}")
        print(f"   Type: {result.pdf_type}")
        print(f"   Strategy: {result.strategy}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Text Density: {result.text_density:.1f} chars/page")
        print(f"   Image Ratio: {result.image_ratio:.1%}")
        print(f"   Pages Analyzed: {result.sample_pages}/{result.page_count}")
    except Exception as e:
        print(f"\n❌ {pdf_path}")
        print(f"   Error: {e}")

print("\n" + "="*70 + "\n")
