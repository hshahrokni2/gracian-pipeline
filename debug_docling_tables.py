#!/usr/bin/env python3
"""
Debug Docling Tables - Where is the financial data?
====================================================

Investigation: brf_83301.pdf has financial keywords but no extractable text.
Hypothesis: Financial data is in Docling tables, not plain text.
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

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

# Test PDF
TEST_PDF = "SRS/brf_83301.pdf"

print("=" * 80)
print("DOCLING TABLES INVESTIGATION - brf_83301.pdf")
print("=" * 80)
print()

pdf_path = Path(__file__).parent / TEST_PDF

if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {TEST_PDF}")
    sys.exit(1)

# Extract with Docling
extractor = RobustUltraComprehensiveExtractor()
base_result = extractor.extract_brf_document(str(pdf_path), mode="fast")

tables = base_result.get('_docling_tables', [])

print(f"📊 Total tables detected: {len(tables)}")
print()

if len(tables) == 0:
    print("❌ NO TABLES FOUND - Financial data may be in images or complex layouts")
    sys.exit(0)

# Analyze each table
financial_keywords = [
    'Intäkter', 'Nettoomsättning', 'Rörelsens intäkter',
    'Kostnader', 'Rörelsekostnader',
    'Årets resultat', 'Resultat efter skatt',
    'Tillgångar', 'Summa tillgångar',
    'Skulder', 'Summa skulder',
    'Eget kapital'
]

print("🔍 Analyzing tables for financial data:")
print()

financial_tables = []

for i, table in enumerate(tables, 1):
    print(f"📋 Table {i}:")
    print(f"   Type: {table.get('table_type', 'unknown')}")

    data = table.get('data', [])
    print(f"   Rows: {len(data)}")

    # Get column count safely
    col_count = 0
    if data and len(data) > 0:
        first_row = data[0] if isinstance(data, list) else []
        col_count = len(first_row) if isinstance(first_row, list) else 0
    print(f"   Columns: {col_count}")

    # Convert table data to text for keyword search
    table_text = json.dumps(table.get('data', []), ensure_ascii=False)

    # Check for financial keywords
    keywords_found = []
    for keyword in financial_keywords:
        if keyword in table_text:
            keywords_found.append(keyword)

    if keywords_found:
        print(f"   ✅ Financial keywords: {', '.join(keywords_found[:5])}")
        financial_tables.append((i, table, keywords_found))
    else:
        print(f"   ⚠️ No financial keywords")

    # Show table preview (first 3 rows)
    if data and isinstance(data, list):
        print(f"   Preview (first 3 rows):")
        for row_idx, row in enumerate(data[:3], 1):
            print(f"      Row {row_idx}: {row[:5] if len(row) > 5 else row}")

    print()

# Deep dive into financial tables
if financial_tables:
    print("=" * 80)
    print("FINANCIAL TABLES DETAIL")
    print("=" * 80)
    print()

    for table_num, table, keywords in financial_tables:
        print(f"📊 Table {table_num} - Financial Data Found!")
        print(f"   Keywords: {', '.join(keywords)}")
        print()

        # Show full table data
        data = table.get('data', [])
        print(f"   Full table ({len(data)} rows × {len(data[0]) if data else 0} columns):")
        print()

        for row_idx, row in enumerate(data, 1):
            print(f"      {row_idx:2d}. {row}")

        print()

        # Try to extract specific values
        print(f"   🔍 Extraction Attempt:")

        # Look for revenue
        revenue_keywords = ['Intäkter', 'Nettoomsättning', 'Rörelsens intäkter']
        for row in data:
            for cell in row:
                if any(kw in str(cell) for kw in revenue_keywords):
                    print(f"      Revenue row found: {row}")
                    # Try to extract numeric value from next cell
                    row_idx = data.index(row)
                    if len(row) > 1:
                        print(f"         → Value candidates: {row[1:]}")

        # Look for assets
        asset_keywords = ['Tillgångar', 'Summa tillgångar']
        for row in data:
            for cell in row:
                if any(kw in str(cell) for kw in asset_keywords):
                    print(f"      Assets row found: {row}")
                    if len(row) > 1:
                        print(f"         → Value candidates: {row[1:]}")

        print()
else:
    print("❌ NO FINANCIAL TABLES FOUND")
    print("   Root cause: Financial data likely in images or non-table format")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print(f"📊 Tables analyzed: {len(tables)}")
print(f"📊 Financial tables found: {len(financial_tables)}")
print()

if financial_tables:
    print("✅ FINANCIAL DATA IS IN TABLES!")
    print()
    print("💡 Recommendation:")
    print("   1. Fix context routing to pass Docling tables to financial agents")
    print("   2. Ensure agents can parse Swedish table structures")
    print("   3. Tables contain the missing financial data")
else:
    print("❌ FINANCIAL DATA NOT IN TABLES")
    print()
    print("💡 Recommendation:")
    print("   1. Check if pages are images (use mixed-mode extraction)")
    print("   2. Investigate alternative data formats")
    print("   3. Manual PDF inspection required")

print()
print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
