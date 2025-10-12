#!/usr/bin/env python3
"""
Debug metadata extraction - inspect Docling markdown to find org number
"""

import sys
import re
sys.path.insert(0, '/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline')

from scripts.run_prod import extract_brf_to_pydantic

# Extract the PDF
pdf_path = "SRS/brf_198532.pdf"
print(f"🔍 Debugging metadata extraction for: {pdf_path}\n")

result = extract_brf_to_pydantic(pdf_path, mode="fast")

# Get the base_result (before Pydantic conversion)
from gracian_pipeline.core.pydantic_extractor import PydanticBRFExtractor
extractor = PydanticBRFExtractor()

# Re-run extraction to get base_result
from gracian_pipeline.core.orchestrator import GracianOrchestrator
orchestrator = GracianOrchestrator()
base_result = orchestrator.process_document(pdf_path, mode="fast")

# Get Docling markdown
markdown = base_result.get("_docling_markdown", "")

print("=" * 80)
print("📄 FIRST 2000 CHARACTERS OF DOCLING MARKDOWN:")
print("=" * 80)
print(markdown[:2000])
print("\n")

print("=" * 80)
print("🔍 SEARCHING FOR ORGANIZATION NUMBER PATTERN:")
print("=" * 80)

# Test different search windows
for window_size in [500, 1000, 2000, 5000]:
    pattern = r'(\d{6}-\d{4})'
    match = re.search(pattern, markdown[:window_size])
    status = "✅ FOUND" if match else "❌ NOT FOUND"
    value = match.group(1) if match else "N/A"
    print(f"Window {window_size:5d} chars: {status:12s} → {value}")

print("\n")

# Search for the specific number
print("=" * 80)
print("🎯 SEARCHING FOR '769629-0134' SPECIFICALLY:")
print("=" * 80)

if "769629-0134" in markdown:
    position = markdown.index("769629-0134")
    print(f"✅ FOUND at position {position}")
    print(f"\nContext (50 chars before and after):")
    start = max(0, position - 50)
    end = min(len(markdown), position + 50)
    print(markdown[start:end])
    print("\n")
else:
    print("❌ NOT FOUND in entire markdown")
    print("\nChecking if it appears in any form:")
    if "769629" in markdown:
        print("✅ Found '769629' (first part)")
        pos = markdown.index("769629")
        print(f"   At position {pos}: {markdown[pos:pos+20]}")
    if "0134" in markdown:
        print("✅ Found '0134' (second part)")
        pos = markdown.index("0134")
        print(f"   At position {pos}: {markdown[pos-10:pos+10]}")

print("\n")

# Check what the current extraction returns
print("=" * 80)
print("📊 CURRENT EXTRACTION RESULTS:")
print("=" * 80)
print(f"Organization Number: {result.metadata.organization_number.value}")
print(f"   Confidence: {result.metadata.organization_number.confidence}")
print(f"   Source: {result.metadata.organization_number.source}")
print(f"\nBRF Name: {result.metadata.brf_name.value}")
print(f"   Confidence: {result.metadata.brf_name.confidence}")
print(f"\nFiscal Year: {result.metadata.fiscal_year.value}")
print(f"   Confidence: {result.metadata.fiscal_year.confidence}")
