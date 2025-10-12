#!/usr/bin/env python3
"""
Debug script to see what OCR actually extracts from scanned PDFs.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("⚠️  Warning: .env file not found, API key may be missing")

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter

# Test PDFs
test_pdfs = [
    "SRS/brf_276629.pdf",  # Pure scanned (0% text)
    "SRS/brf_43334.pdf",   # Mostly scanned (10.5% text)
]

print("=" * 80)
print("OCR EXTRACTION DEBUG - Check what EasyOCR actually extracts")
print("=" * 80)

adapter = UltraComprehensiveDoclingAdapter()

for pdf_path in test_pdfs:
    full_path = Path(__file__).parent / pdf_path

    if not full_path.exists():
        print(f"\n❌ PDF not found: {pdf_path}")
        continue

    print(f"\n{'=' * 80}")
    print(f"PDF: {pdf_path}")
    print("=" * 80)

    # Extract with Docling (OCR enabled)
    result = adapter.extract_with_docling(str(full_path))

    # Show results
    markdown = result['markdown']
    char_count = result['char_count']
    status = result['status']

    print(f"\n📊 OCR Extraction Results:")
    print(f"   Status: {status}")
    print(f"   Character count: {char_count:,}")
    print(f"   Exceeds 1000 char threshold: {'✓' if char_count >= 1000 else '✗'}")

    if char_count > 0:
        print(f"\n📝 First 500 chars of OCR text:")
        print("-" * 80)
        print(markdown[:500])
        print("-" * 80)

        # Count how many pages have text
        lines = markdown.split('\n')
        print(f"\n📄 Text distribution:")
        print(f"   Total lines: {len(lines)}")
        print(f"   Non-empty lines: {sum(1 for line in lines if line.strip())}")

        # Check for Swedish keywords
        swedish_keywords = [
            'Styrelse', 'Ordförande', 'Revisor', 'Årsredovisning',
            'Balansräkning', 'Resultaträkning', 'Noter', 'Bostadsrättsförening'
        ]
        found_keywords = [kw for kw in swedish_keywords if kw in markdown]
        print(f"\n🔍 Swedish keywords found: {len(found_keywords)}/{len(swedish_keywords)}")
        if found_keywords:
            print(f"   Found: {', '.join(found_keywords)}")
    else:
        print("\n⚠️  OCR extracted 0 characters (complete failure)")

print(f"\n\n{'=' * 80}")
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
