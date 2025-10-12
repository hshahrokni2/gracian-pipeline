#!/usr/bin/env python3
"""
Debug Merge Logic - Check Base Extractor Structure
====================================================

Checks what structure the base extractor returns and validates the merge logic.
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

PDF_PATH = "SRS/brf_76536.pdf"

print("=" * 80)
print("MERGE LOGIC DEBUG: Base Extractor Structure")
print("=" * 80)
print()

pdf_path = Path(__file__).parent / PDF_PATH

if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {PDF_PATH}")
    sys.exit(1)

print(f"📄 PDF: {pdf_path.name}")
print()

# Run base extraction
print("🔍 Running base extraction...")
extractor = RobustUltraComprehensiveExtractor()
result = extractor.extract_brf_document(str(pdf_path), mode="fast")

print(f"   ✓ Extraction complete")
print()

# Check structure
print("📊 Base Result Structure:")
print("-" * 80)
print()

# Show top-level keys
print("Top-level keys:")
for key in sorted(result.keys()):
    if key.startswith('_'):
        continue  # Skip internal keys
    value = result[key]
    value_type = type(value).__name__
    print(f"  - {key}: {value_type}")
print()

# Check for financial_agent key
if 'financial_agent' in result:
    print("✓ Has 'financial_agent' key")
    financial = result['financial_agent']
    print(f"  Type: {type(financial).__name__}")
    if isinstance(financial, dict):
        print(f"  Keys: {list(financial.keys())}")
    print()
else:
    print("✗ NO 'financial_agent' key")
    print()

# Check for other relevant keys
relevant_keys = [
    'metadata_agent',
    'governance_agent',
    'property_agent',
    'loans_agent',
    'fees_agent',
    'buildings_agent',
    'chairman_agent',
]

print("Relevant agent keys:")
for key in relevant_keys:
    if key in result:
        value = result[key]
        value_type = type(value).__name__
        print(f"  ✓ {key}: {value_type}")
        if isinstance(value, dict) and len(value) <= 10:
            print(f"     Keys: {list(value.keys())}")
        elif isinstance(value, list):
            print(f"     Length: {len(value)}")
    else:
        print(f"  ✗ {key}: NOT FOUND")
print()

# Show sample of financial data structure (if exists)
if 'income_statement' in result:
    print("📈 Income Statement Structure:")
    income = result['income_statement']
    print(f"  Type: {type(income).__name__}")
    if isinstance(income, dict):
        for key, value in list(income.items())[:5]:
            print(f"    - {key}: {value}")
    print()

if 'balance_sheet' in result:
    print("💰 Balance Sheet Structure:")
    balance = result['balance_sheet']
    print(f"  Type: {type(balance).__name__}")
    if isinstance(balance, dict):
        for key, value in list(balance.items())[:5]:
            print(f"    - {key}: {value}")
    print()

# Save full structure for inspection
output_path = Path(__file__).parent / "data" / "anomaly_investigation" / "vision_debug" / "base_extractor_structure.json"

# Create a simplified view (remove large fields)
simplified = {}
for key, value in result.items():
    if key.startswith('_') and key in ['_docling_markdown', '_raw_text']:
        simplified[key] = f"<{len(str(value))} chars>"
    elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
        simplified[key] = value
    else:
        simplified[key] = str(type(value))

output_path.write_text(json.dumps(simplified, indent=2, ensure_ascii=False))
print(f"💾 Full structure saved to: {output_path.name}")
print()

print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
print()
print("🔍 Analysis:")
print("   1. Check if base extractor has 'financial_agent' key")
print("   2. If not, vision data needs to be added as new key")
print("   3. If yes, check structure matches vision data format")
print("   4. Verify merge logic handles the actual structure")
