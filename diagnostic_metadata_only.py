#!/usr/bin/env python3
"""
Quick diagnostic script to test metadata extraction in isolation
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Import base extractor
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

print("🔬 METADATA EXTRACTION DIAGNOSTIC")
print("="*80)
print()

pdf_path = "SRS/brf_198532.pdf"

# Run base extraction (this saves markdown to base_result)
print("📊 Step 1: Running base extraction...")
extractor = RobustUltraComprehensiveExtractor()
base_result = extractor.extract_brf_document(pdf_path, mode="fast")

print(f"✅ Base extraction complete")
print()

# Check what keys are in base_result
print("📋 Keys in base_result:")
for key in base_result.keys():
    if key.startswith('_'):
        print(f"   {key}: {len(str(base_result[key]))} chars")
print()

# Check markdown specifically
markdown = base_result.get("_docling_markdown", "")
print(f"🔍 Markdown Analysis:")
print(f"   Length: {len(markdown)} chars")
print(f"   Present: {bool(markdown)}")

if markdown:
    print(f"   First 300 chars:")
    print(f"   {repr(markdown[:300])}")
    print()
    print(f"   Search for '769629-0134': {'FOUND' if '769629-0134' in markdown else 'NOT FOUND'}")
    print(f"   Search for 'Bostadsrättsföreningen': {'FOUND' if 'Bostadsrättsföreningen' in markdown else 'NOT FOUND'}")
    print(f"   Search for '2021': {'FOUND' if '2021' in markdown else 'NOT FOUND'}")
else:
    print(f"   ❌ MARKDOWN IS EMPTY!")
    print(f"   This confirms Issue #1 root cause")

print()
print("="*80)
print("✅ DIAGNOSTIC COMPLETE")
