#!/usr/bin/env python3
"""
ULTRATHINKING INVESTIGATION: brf_76536.pdf Anomaly
=====================================================

CRITICAL BUG: 73.7% text percentage but 0.0% coverage

This is the highest-priority investigation because it represents a complete
extraction failure on a PDF that SHOULD be machine-readable.

Expected Impact: +15-20pp coverage if fixed

Investigation Plan:
1. Verify PDF properties (pages, size, text percentage)
2. Extract raw text to see what's actually in the PDF
3. Run full extraction pipeline to observe failure mode
4. Analyze Docling structure detection
5. Check agent routing and context allocation
6. Identify root cause and propose fix

Target: Understand WHY 73.7% text leads to 0% extraction
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.utils.pdf_classifier import classify_pdf
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic
import fitz  # PyMuPDF

# PDF to investigate
PDF_PATH = "SRS/brf_76536.pdf"

print("=" * 80)
print("ULTRATHINKING INVESTIGATION: brf_76536.pdf Anomaly")
print("=" * 80)
print("\n🎯 CRITICAL BUG: 73.7% text but 0.0% coverage")
print("Expected Impact: +15-20pp if fixed\n")
print("=" * 80)

pdf_path = Path(__file__).parent / PDF_PATH

if not pdf_path.exists():
    print(f"\n❌ ERROR: PDF not found at {PDF_PATH}")
    print("Available SRS PDFs:")
    srs_dir = Path(__file__).parent / "SRS"
    if srs_dir.exists():
        for pdf in sorted(srs_dir.glob("brf_76536*.pdf")):
            print(f"  - {pdf.name}")
    sys.exit(1)

# ============================================================================
# PHASE 1: Basic PDF Properties
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 1: Basic PDF Properties")
print("=" * 80)

doc = fitz.open(pdf_path)
num_pages = len(doc)
file_size = pdf_path.stat().st_size / 1024  # KB

print(f"\n📄 PDF Information:")
print(f"   File: {pdf_path.name}")
print(f"   Size: {file_size:.1f} KB")
print(f"   Pages: {num_pages}")

# ============================================================================
# PHASE 2: Text Percentage Classification
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 2: Text Percentage Classification")
print("=" * 80)

classification = classify_pdf(str(pdf_path), verbose=True)

print(f"\n📊 Classification Results:")
print(f"   Classification: {classification['classification']}")
print(f"   Text percentage: {classification['text_percentage']:.1f}%")
print(f"   Pages with text: {classification['pages_with_text']}/{classification['total_pages']}")
print(f"   Machine-readable: {classification['is_machine_readable']}")

if classification['text_percentage'] < 70 or classification['text_percentage'] > 80:
    print(f"\n⚠️  WARNING: Text percentage {classification['text_percentage']:.1f}% differs from expected 73.7%")

# ============================================================================
# PHASE 3: Raw Text Extraction Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 3: Raw Text Extraction Analysis")
print("=" * 80)

pages_with_text_list = []
total_chars = 0
swedish_keywords = ['Styrelse', 'Ordförande', 'Revisor', 'Årsredovisning',
                   'Balansräkning', 'Resultaträkning', 'Noter', 'Bostadsrättsförening']

print(f"\n📖 Page-by-Page Text Analysis:")

for page_num, page in enumerate(doc, 1):
    text = page.get_text()
    char_count = len(text)
    total_chars += char_count

    has_text = char_count > 100
    if has_text:
        pages_with_text_list.append(page_num)

    # Check for Swedish keywords
    keywords_found = [kw for kw in swedish_keywords if kw in text]

    status = "✓ HAS TEXT" if has_text else "✗ Minimal/No text"
    print(f"   Page {page_num:2d}: {char_count:6,} chars - {status}", end="")

    if keywords_found:
        print(f" - Keywords: {', '.join(keywords_found)}")
    else:
        print()

    # Show first 200 chars of pages with text
    if has_text and page_num <= 5:  # First 5 pages with text
        print(f"      Preview: {text[:200].strip()[:150]}...")

doc.close()

print(f"\n📊 Text Distribution Summary:")
print(f"   Total characters: {total_chars:,}")
print(f"   Pages with text: {len(pages_with_text_list)}/{num_pages}")
print(f"   Text percentage: {len(pages_with_text_list)/num_pages*100:.1f}%")
print(f"   Pages with text: {pages_with_text_list}")

# ============================================================================
# PHASE 4: Full Extraction Pipeline Test
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 4: Full Extraction Pipeline Test")
print("=" * 80)

print(f"\n🔧 Running extraction pipeline (fast mode)...")

try:
    result = extract_brf_to_pydantic(str(pdf_path), mode="fast")

    # Extract results
    coverage = result.coverage_percentage
    confidence = result.confidence_score

    print(f"\n✓ Extraction completed")
    print(f"\n📊 Extraction Results:")
    print(f"   Coverage: {coverage:.1f}%")
    print(f"   Confidence: {confidence:.2f}")

    # Analyze what was extracted
    print(f"\n📋 Field Extraction Details:")

    # Governance
    governance = result.governance
    if governance:
        print(f"\n   Governance:")
        print(f"      Chairman: {governance.chairman if governance.chairman else 'None'}")
        print(f"      Board members: {len(governance.board_members) if governance.board_members else 0}")
        if governance.board_members:
            for member in governance.board_members[:3]:
                print(f"         - {member.name} ({member.role})")
        print(f"      Auditor: {governance.primary_auditor.name if governance.primary_auditor else 'None'}")
    else:
        print(f"   Governance: None ❌")

    # Financial
    financial = result.financial
    if financial:
        print(f"\n   Financial:")
        if financial.income_statement:
            print(f"      Revenue: {financial.income_statement.revenue_total or 'None'}")
            print(f"      Expenses: {financial.income_statement.expenses_total or 'None'}")
        if financial.balance_sheet:
            print(f"      Assets: {financial.balance_sheet.assets_total or 'None'}")
            print(f"      Liabilities: {financial.balance_sheet.liabilities_total or 'None'}")
            print(f"      Equity: {financial.balance_sheet.equity_total or 'None'}")
    else:
        print(f"   Financial: None ❌")

    # Property
    property_info = result.property
    if property_info:
        print(f"\n   Property:")
        print(f"      Municipality: {property_info.municipality or 'None'}")
        print(f"      Address: {property_info.address or 'None'}")
        print(f"      Built year: {property_info.built_year or 'None'}")
    else:
        print(f"   Property: None ❌")

    # Metadata
    metadata = result.metadata
    if metadata:
        print(f"\n   Metadata:")
        print(f"      Org number: {metadata.organization_number or 'None'}")
        print(f"      BRF name: {metadata.brf_name or 'None'}")
        print(f"      Report year: {metadata.report_year or 'None'}")
    else:
        print(f"   Metadata: None ❌")

    # Quality metrics
    quality = result._quality_metrics
    if quality:
        print(f"\n   Quality Metrics:")
        print(f"      Coverage: {quality.get('coverage_percentage', 0):.1f}%")
        print(f"      Filled fields: {quality.get('fields_filled', 0)}/{quality.get('total_fields', 0)}")
        print(f"      Evidence ratio: {quality.get('evidence_ratio', 0):.1f}%")

    # Critical Analysis
    print(f"\n" + "=" * 80)
    print("CRITICAL ANALYSIS")
    print("=" * 80)

    if coverage == 0.0:
        print("\n❌ CONFIRMED: 0% coverage despite 73.7% text percentage")
        print("\n🔍 Root Cause Hypotheses:")
        print("   1. Agent routing failure (text exists but not passed to agents)")
        print("   2. Text format issues (text extracted but unreadable by LLM)")
        print("   3. Section detection failure (can't find sections in document)")
        print("   4. Context building failure (text not organized into extractable context)")
        print("   5. LLM extraction failure (LLM can't extract from provided context)")

        print("\n📋 Next Steps:")
        print("   1. Check Docling structure detection (see what markdown it generates)")
        print("   2. Inspect agent context allocation (see what text each agent gets)")
        print("   3. Review LLM prompts and responses (see why extraction fails)")
        print("   4. Compare with successful PDFs (what's different?)")
    else:
        print(f"\n⚠️  UNEXPECTED: Got {coverage:.1f}% coverage (not 0%)")
        print("   Original report may be outdated or extraction improved")

except Exception as e:
    print(f"\n❌ EXTRACTION FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

    print(f"\n🔍 Error Analysis:")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error indicates: Likely system failure, not data issue")

# ============================================================================
# PHASE 5: Save Investigation Results
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 5: Save Investigation Results")
print("=" * 80)

output_dir = Path(__file__).parent / "data" / "anomaly_investigation"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "brf_76536_investigation.json"

investigation_data = {
    "pdf": PDF_PATH,
    "file_size_kb": file_size,
    "num_pages": num_pages,
    "classification": classification,
    "total_chars": total_chars,
    "pages_with_text": pages_with_text_list,
    "text_percentage_calculated": len(pages_with_text_list)/num_pages*100,
}

if 'result' in locals():
    investigation_data["extraction_result"] = {
        "coverage": coverage,
        "confidence": confidence,
        "governance_extracted": governance is not None,
        "financial_extracted": financial is not None,
        "property_extracted": property_info is not None,
        "metadata_extracted": metadata is not None,
    }

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(investigation_data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Investigation results saved to: {output_file}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)

print(f"\n📊 Summary:")
print(f"   PDF: {pdf_path.name}")
print(f"   Text percentage: {classification['text_percentage']:.1f}%")
print(f"   Pages with text: {len(pages_with_text_list)}/{num_pages}")

if 'result' in locals():
    print(f"   Extraction coverage: {coverage:.1f}%")
    print(f"   Status: {'❌ ANOMALY CONFIRMED' if coverage == 0 else '⚠️ DIFFERENT THAN EXPECTED'}")
else:
    print(f"   Extraction: FAILED")
    print(f"   Status: ❌ SYSTEM ERROR")

print("\n🔍 Next: Analyze Docling structure detection and agent context allocation")
print("=" * 80)
