#!/usr/bin/env python3
"""
Test metadata extraction directly with known good markdown
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from gracian_pipeline.core.pydantic_extractor import UltraComprehensivePydanticExtractor
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

print("🔬 DIRECT METADATA EXTRACTION TEST")
print("="*80)
print()

pdf_path = "SRS/brf_198532.pdf"

# Get base_result with known good markdown
print("Step 1: Get base_result with markdown...")
extractor_base = RobustUltraComprehensiveExtractor()
base_result = extractor_base.extract_brf_document(pdf_path, mode="fast")

markdown = base_result.get("_docling_markdown", "")
print(f"✅ Markdown retrieved: {len(markdown)} chars")
print()

# Now test metadata extraction
print("Step 2: Extract metadata from base_result...")
extractor_pydantic = UltraComprehensivePydanticExtractor()
metadata = extractor_pydantic._extract_metadata(pdf_path, base_result)

print()
print("📊 METADATA EXTRACTION RESULTS:")
print(f"   organization_number: {metadata.organization_number.value}")
print(f"   brf_name: {metadata.brf_name.value}")
print(f"   fiscal_year: {metadata.fiscal_year.value}")
print()

# Check if they match ground truth
ground_truth = {
    'organization_number': '769629-0134',
    'brf_name': 'Bostadsrättsföreningen Björk och Plaza',
    'fiscal_year': 2021
}

print("✅ COMPARISON AGAINST GROUND TRUTH:")
print(f"   Org Number: {'✅' if metadata.organization_number.value == ground_truth['organization_number'] else '❌'} {metadata.organization_number.value} vs {ground_truth['organization_number']}")
print(f"   BRF Name: {'✅' if ground_truth['brf_name'] in metadata.brf_name.value else '❌'} {metadata.brf_name.value} vs {ground_truth['brf_name']}")
print(f"   Fiscal Year: {'✅' if metadata.fiscal_year.value == ground_truth['fiscal_year'] else '❌'} {metadata.fiscal_year.value} vs {ground_truth['fiscal_year']}")

print()
print("="*80)
print("✅ TEST COMPLETE")
