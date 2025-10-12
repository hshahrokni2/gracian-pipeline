"""
Debug script to check what financial_agent is actually returning.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

load_dotenv()

# Test with the same PDF
pdf_path = "experiments/docling_advanced/test_pdfs/brf_198532.pdf"

print("=" * 80)
print("FINANCIAL AGENT RAW RESPONSE DEBUG")
print("=" * 80)
print(f"\nPDF: {pdf_path}\n")

# Extract using the base extractor
extractor = RobustUltraComprehensiveExtractor()
print("Running base extraction...")
result = extractor.extract_brf_document(pdf_path, mode="fast")

# Check what financial_agent returned
if "financial_agent" in result:
    print("\n" + "=" * 80)
    print("FINANCIAL_AGENT RAW RESPONSE")
    print("=" * 80)
    print(json.dumps(result["financial_agent"], indent=2, ensure_ascii=False))

    # Check for our target fields
    print("\n" + "=" * 80)
    print("TARGET FIELDS CHECK")
    print("=" * 80)

    fin = result["financial_agent"]
    print(f"✓ Contains 'liabilities': {('liabilities' in fin)}")
    print(f"✗ Contains 'long_term_liabilities': {('long_term_liabilities' in fin)}")
    print(f"✗ Contains 'short_term_liabilities': {('short_term_liabilities' in fin)}")

    if 'liabilities' in fin:
        print(f"\n  liabilities value: {fin['liabilities']}")
    if 'long_term_liabilities' in fin:
        print(f"  long_term_liabilities value: {fin['long_term_liabilities']}")
    if 'short_term_liabilities' in fin:
        print(f"  short_term_liabilities value: {fin['short_term_liabilities']}")

else:
    print("\n❌ ERROR: No financial_agent in result")
    print("\nAvailable agents:")
    for key in result.keys():
        print(f"  - {key}")
