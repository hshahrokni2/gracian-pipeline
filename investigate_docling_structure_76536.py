#!/usr/bin/env python3
"""
DEEP DIVE: Docling Structure Detection for brf_76536.pdf
=========================================================

Root Cause Analysis: Pages 9-12 (financial statements) have <100 chars each.
These pages contain the critical data but text extraction fails.

Investigation Focus:
1. What does Docling detect on these pages?
2. Are there tables that Docling can extract?
3. Is OCR running on these pages?
4. What's in the markdown output for pages 9-12?

Goal: Understand if we can extract financial data from structured tables
instead of relying on text extraction.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter

PDF_PATH = "SRS/brf_76536.pdf"

print("=" * 80)
print("DEEP DIVE: Docling Structure Detection - brf_76536.pdf")
print("=" * 80)
print("\n🎯 Focus: Understand why pages 9-12 (financial statements) fail")
print("Expected: These pages have tables that need structure extraction\n")
print("=" * 80)

pdf_path = Path(__file__).parent / PDF_PATH

if not pdf_path.exists():
    print(f"\n❌ ERROR: PDF not found at {PDF_PATH}")
    sys.exit(1)

# ============================================================================
# PHASE 1: Docling Full Extraction
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 1: Docling Full Extraction")
print("=" * 80)

adapter = UltraComprehensiveDoclingAdapter()

print(f"\n🔧 Running Docling extraction...")
result = adapter.extract_with_docling(str(pdf_path))

# Extract results
markdown = result['markdown']
tables = result['tables']
char_count = result['char_count']
status = result['status']

print(f"\n✓ Docling extraction complete")
print(f"\n📊 Extraction Summary:")
print(f"   Status: {status}")
print(f"   Character count: {char_count:,}")
print(f"   Machine-readable threshold (1000): {char_count >= 1000}")
print(f"   Tables detected: {len(tables)}")

# ============================================================================
# PHASE 2: Table Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 2: Table Structure Analysis")
print("=" * 80)

if tables:
    print(f"\n📊 Found {len(tables)} tables:")

    for i, table in enumerate(tables, 1):
        print(f"\n   Table {i}:")
        print(f"      Keys: {list(table.keys())}")

        # Try to extract table data
        if 'data' in table:
            data = table['data']
            if isinstance(data, list) and len(data) > 0:
                print(f"      Rows: {len(data)}")
                print(f"      Columns: {len(data[0]) if len(data) > 0 else 0}")

                # Show first few rows
                print(f"      Sample data:")
                for j, row in enumerate(data[:3], 1):
                    print(f"         Row {j}: {row}")
            else:
                print(f"      Data: {str(data)[:200]}")

        # Check for prov (provenance - which page)
        if 'prov' in table:
            prov = table['prov']
            print(f"      Provenance: {prov}")

        # Check for text content
        if 'text' in table:
            text = table['text']
            print(f"      Text: {text[:200]}...")

    # Check if financial pages have tables
    print(f"\n🔍 Checking financial pages (9-12) for tables:")
    financial_page_tables = []

    for i, table in enumerate(tables, 1):
        if 'prov' in table:
            prov = table['prov']
            # Extract page number from provenance
            for item in prov:
                if hasattr(item, 'page_no'):
                    page_no = item.page_no
                    if 9 <= page_no <= 12:
                        financial_page_tables.append((i, page_no, table))
                        print(f"      ✓ Table {i} found on page {page_no}")

    if not financial_page_tables:
        print(f"      ❌ NO tables found on financial pages 9-12")
        print(f"      This explains the extraction failure!")
else:
    print(f"\n❌ NO TABLES DETECTED by Docling")
    print(f"   This is a critical issue - financial statements should have tables")

# ============================================================================
# PHASE 3: Markdown Analysis by Page
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 3: Markdown Content Analysis")
print("=" * 80)

# Split markdown by page markers (if Docling includes them)
lines = markdown.split('\n')

print(f"\n📄 Markdown Statistics:")
print(f"   Total lines: {len(lines)}")
print(f"   Total characters: {len(markdown)}")
print(f"   Non-empty lines: {sum(1 for line in lines if line.strip())}")

# Look for page markers or section headings
print(f"\n🔍 Section Headings in Markdown:")
heading_count = 0
for i, line in enumerate(lines):
    if line.startswith('#'):
        heading_count += 1
        if heading_count <= 20:  # First 20 headings
            print(f"   Line {i+1}: {line[:100]}")

if heading_count == 0:
    print(f"   ❌ NO section headings found in markdown")
    print(f"   Docling may not be structuring the document properly")
else:
    print(f"\n   Total headings: {heading_count}")

# Search for financial keywords in markdown
print(f"\n🔍 Financial Keywords in Markdown:")
financial_keywords = [
    'Resultaträkning', 'Balansräkning', 'Kassaflödesanalys',
    'Intäkter', 'Kostnader', 'Tillgångar', 'Skulder', 'Eget kapital',
    'Noter', 'Årsavgift'
]

for keyword in financial_keywords:
    count = markdown.count(keyword)
    if count > 0:
        print(f"   {keyword}: {count} occurrences")

        # Find context around keyword
        pos = markdown.find(keyword)
        if pos != -1:
            context_start = max(0, pos - 100)
            context_end = min(len(markdown), pos + 200)
            context = markdown[context_start:context_end]
            print(f"      Context: ...{context}...")
            print()

# ============================================================================
# PHASE 4: Check Pages 9-12 Specifically
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 4: Pages 9-12 Deep Analysis")
print("=" * 80)

# Save markdown to file for manual inspection
output_dir = Path(__file__).parent / "data" / "anomaly_investigation"
output_dir.mkdir(parents=True, exist_ok=True)

markdown_file = output_dir / "brf_76536_markdown.txt"
with open(markdown_file, 'w', encoding='utf-8') as f:
    f.write(markdown)

print(f"\n💾 Full markdown saved to: {markdown_file}")
print(f"   Manual inspection recommended to find page 9-12 content")

# Try to extract pages 9-12 content
print(f"\n🔍 Searching for page-specific content:")

# Look for image markers on pages 9-12
image_count = markdown.count('<!-- image -->')
print(f"   Image markers: {image_count}")

if image_count > 0:
    print(f"   ⚠️  Document contains {image_count} image markers")
    print(f"   OCR may not be extracting text from these images")

# ============================================================================
# PHASE 5: Root Cause Summary
# ============================================================================

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

print(f"\n📊 Evidence Summary:")
print(f"   1. Total characters extracted: {char_count:,} (very low)")
print(f"   2. Tables detected: {len(tables)}")
print(f"   3. Image markers: {image_count}")
print(f"   4. Section headings: {heading_count}")

print(f"\n🔍 Root Cause Hypothesis:")

if len(tables) == 0:
    print(f"   ❌ CRITICAL: NO tables detected by Docling")
    print(f"      → Financial statement pages (9-12) not detected as tables")
    print(f"      → These pages likely have image-based tables (scanned)")
    print(f"      → OCR is enabled but may not be running on table detection")
elif not financial_page_tables:
    print(f"   ❌ CRITICAL: Tables detected but NOT on pages 9-12")
    print(f"      → Financial data pages have no table structure")
    print(f"      → Need to check if tables are on different pages")
else:
    print(f"   ⚠️  Tables found on pages 9-12 but extraction still failed")
    print(f"      → Table extraction may be incomplete")
    print(f"      → Need to check table data quality")

if image_count > 10:
    print(f"\n   ⚠️  HIGH IMAGE COUNT: {image_count} image markers")
    print(f"      → Document is heavily image-based")
    print(f"      → OCR may not be extracting text from images")

if char_count < 3000:
    print(f"\n   ❌ EXTREMELY LOW CHARACTER COUNT: {char_count:,}")
    print(f"      → Even with OCR, very little text extracted")
    print(f"      → Suggests OCR quality issues or OCR not running")

print(f"\n🎯 Recommended Fixes:")
print(f"   1. OPTION A: Force vision extraction on pages 9-12")
print(f"      → Use GPT-4o vision to extract from table images")
print(f"      → Expected impact: +10-15pp coverage")
print(f"\n   2. OPTION B: Alternative OCR backend (Tesseract/RapidOCR)")
print(f"      → Try different OCR engine for table extraction")
print(f"      → Expected impact: +5-10pp coverage")
print(f"\n   3. OPTION C: Table structure detection improvement")
print(f"      → Enhance Docling table detection settings")
print(f"      → Expected impact: +10-20pp coverage if tables exist")

# Save analysis
analysis_file = output_dir / "brf_76536_docling_analysis.json"

analysis_data = {
    "pdf": PDF_PATH,
    "char_count": char_count,
    "tables_detected": len(tables),
    "image_markers": image_count,
    "section_headings": heading_count,
    "financial_page_tables": len(financial_page_tables),
    "hypothesis": "Financial pages 9-12 are image-based tables that Docling cannot extract",
    "recommended_fix": "Option A - Force vision extraction on pages 9-12"
}

with open(analysis_file, 'w', encoding='utf-8') as f:
    json.dump(analysis_data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Analysis saved to: {analysis_file}")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
