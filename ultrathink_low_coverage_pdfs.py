#!/usr/bin/env python3
"""
ULTRATHINKING ANALYSIS: 3 Low-Coverage Machine-Readable PDFs
============================================================

Deep investigation to identify specific root causes for:
- brf_83301.pdf (12.0% → 13.7% coverage)
- brf_282765.pdf (13.7% → 16.2% coverage)
- brf_57125.pdf (14.5% → 17.9% coverage)

Methodology:
1. Extract full Docling markdown + tables
2. Analyze document structure and sections detected
3. Identify what financial/governance data is actually present
4. Compare with what was extracted
5. Diagnose specific extraction failures
6. Propose targeted fixes
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import fitz
import re
from datetime import datetime

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

# Test cases
TEST_CASES = [
    {
        "name": "brf_83301.pdf",
        "path": "SRS/brf_83301.pdf",
        "baseline_coverage": 12.0,
        "new_coverage": 13.7,
        "issues": ["Low coverage despite 13,809 chars", "Has financial keywords"]
    },
    {
        "name": "brf_282765.pdf",
        "path": "SRS/brf_282765.pdf",
        "baseline_coverage": 13.7,
        "new_coverage": 16.2,
        "issues": ["No financial keywords found", "21/23 pages are low-text"]
    },
    {
        "name": "brf_57125.pdf",
        "path": "SRS/brf_57125.pdf",
        "baseline_coverage": 14.5,
        "new_coverage": 17.9,
        "issues": ["No financial keywords", "17/19 pages are low-text", "Swedish governance failed"]
    },
]

print("=" * 80)
print("ULTRATHINKING ANALYSIS: LOW-COVERAGE MACHINE-READABLE PDFs")
print("=" * 80)
print()
print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📄 Target PDFs: {len(TEST_CASES)}")
print()

# Create output directory
output_dir = Path(__file__).parent / "data" / "ultrathinking_analysis"
output_dir.mkdir(parents=True, exist_ok=True)

for i, test_case in enumerate(TEST_CASES, 1):
    print()
    print("=" * 80)
    print(f"ULTRATHINKING ANALYSIS {i}/{len(TEST_CASES)}: {test_case['name']}")
    print("=" * 80)
    print()

    pdf_path = Path(__file__).parent / test_case['path']

    if not pdf_path.exists():
        print(f"❌ ERROR: PDF not found")
        continue

    print(f"📄 PDF: {test_case['name']}")
    print(f"📊 Coverage: {test_case['baseline_coverage']}% → {test_case['new_coverage']}% ({test_case['new_coverage'] - test_case['baseline_coverage']:+.1f}pp)")
    print(f"🔍 Known Issues: {', '.join(test_case['issues'])}")
    print()

    # Phase 1: Document Structure Analysis
    print("=" * 80)
    print("PHASE 1: DOCUMENT STRUCTURE ANALYSIS")
    print("=" * 80)
    print()

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    print(f"📄 Basic Stats:")
    print(f"   Total pages: {total_pages}")

    # Analyze each page
    page_analysis = []
    total_text = ""

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        total_text += text

        # Check for keywords
        has_financial = any(kw in text for kw in ['Resultaträkning', 'Balansräkning', 'Tillgångar', 'Skulder', 'Eget kapital'])
        has_governance = any(kw in text for kw in ['Styrelse', 'Ordförande', 'Revisor', 'Styrelseledamöter'])
        has_property = any(kw in text for kw in ['Fastighet', 'Adress', 'Kommun', 'Lägenhet'])

        page_analysis.append({
            'page': page_num + 1,
            'chars': len(text),
            'has_financial': has_financial,
            'has_governance': has_governance,
            'has_property': has_property,
            'preview': text[:200] if text else ""
        })

    doc.close()

    print(f"   Total characters: {len(total_text):,}")
    print(f"   Avg chars/page: {len(total_text) / total_pages:.0f}")
    print()

    # Page-by-page summary
    print(f"📊 Page-by-Page Analysis:")
    financial_pages = [p['page'] for p in page_analysis if p['has_financial']]
    governance_pages = [p['page'] for p in page_analysis if p['has_governance']]
    property_pages = [p['page'] for p in page_analysis if p['has_property']]

    print(f"   Pages with financial keywords: {financial_pages if financial_pages else 'NONE'}")
    print(f"   Pages with governance keywords: {governance_pages if governance_pages else 'NONE'}")
    print(f"   Pages with property keywords: {property_pages if property_pages else 'NONE'}")
    print()

    # Phase 2: Docling Structure Detection
    print("=" * 80)
    print("PHASE 2: DOCLING STRUCTURE DETECTION")
    print("=" * 80)
    print()

    try:
        extractor = RobustUltraComprehensiveExtractor()
        base_result = extractor.extract_brf_document(str(pdf_path), mode="fast")

        # Extract Docling markdown
        markdown = base_result.get('_docling_markdown', '')
        docling_metadata = base_result.get('docling_metadata', {})

        # Save full markdown for inspection
        markdown_file = output_dir / f"{test_case['name'].replace('.pdf', '')}_markdown.txt"
        markdown_file.write_text(markdown)

        print(f"📝 Docling Markdown:")
        print(f"   Length: {len(markdown):,} chars")
        print(f"   Saved to: {markdown_file.name}")
        print()

        # Analyze structure
        lines = markdown.split('\n')
        headings = [line for line in lines if line.startswith('##')]
        image_markers = markdown.count('<!-- image -->')

        print(f"📊 Structure Detection:")
        print(f"   Headings found: {len(headings)}")
        if headings:
            print(f"   First 10 headings:")
            for heading in headings[:10]:
                print(f"      - {heading}")
        print(f"   Image markers: {image_markers}")
        print()

        # Check for financial sections
        financial_sections = [h for h in headings if any(kw in h for kw in ['Resultat', 'Balans', 'Kassa', 'Tillgångar', 'Skulder'])]
        governance_sections = [h for h in headings if any(kw in h for kw in ['Styrelse', 'Revisor', 'Årsstämma'])]

        print(f"📋 Section Classification:")
        print(f"   Financial sections: {len(financial_sections)}")
        if financial_sections:
            for sec in financial_sections:
                print(f"      - {sec}")
        print(f"   Governance sections: {len(governance_sections)}")
        if governance_sections:
            for sec in governance_sections:
                print(f"      - {sec}")
        print()

    except Exception as e:
        print(f"❌ Docling extraction failed: {e}")
        print()
        continue

    # Phase 3: Extraction Results Analysis
    print("=" * 80)
    print("PHASE 3: EXTRACTION RESULTS ANALYSIS")
    print("=" * 80)
    print()

    try:
        result = extract_brf_to_pydantic(str(pdf_path), mode="fast")

        # Analyze what was extracted
        extracted_summary = {
            'metadata': {},
            'governance': {},
            'financial': {},
            'property': {},
            'fees': {},
            'loans': 0
        }

        if result.metadata:
            extracted_summary['metadata'] = {
                'org_number': bool(result.metadata.organization_number and result.metadata.organization_number.value),
                'brf_name': bool(result.metadata.brf_name and result.metadata.brf_name.value),
                'fiscal_year': bool(result.metadata.fiscal_year and result.metadata.fiscal_year.value)
            }

        if result.governance:
            extracted_summary['governance'] = {
                'chairman': bool(result.governance.chairman and result.governance.chairman.value),
                'board_members': len(result.governance.board_members) if result.governance.board_members else 0,
                'auditor': bool(result.governance.primary_auditor)
            }

        if result.financial:
            if result.financial.income_statement:
                income = result.financial.income_statement
                extracted_summary['financial']['income'] = {
                    'revenue': bool(income.revenue_total and income.revenue_total.value),
                    'expenses': bool(income.expenses_total and income.expenses_total.value),
                    'net_income': bool(income.result_after_tax and income.result_after_tax.value)
                }
            if result.financial.balance_sheet:
                balance = result.financial.balance_sheet
                extracted_summary['financial']['balance'] = {
                    'assets': bool(balance.assets_total and balance.assets_total.value),
                    'liabilities': bool(balance.liabilities_total and balance.liabilities_total.value),
                    'equity': bool(balance.equity_total and balance.equity_total.value)
                }

        if result.property:
            extracted_summary['property'] = {
                'municipality': bool(result.property.municipality and result.property.municipality.value),
                'address': bool(result.property.property_designation and result.property.property_designation.value)
            }

        if result.fees:
            extracted_summary['fees'] = {
                'monthly_fee': bool(result.fees.monthly_fee_per_sqm and result.fees.monthly_fee_per_sqm.value),
                'annual_fee': bool(result.fees.annual_fee_per_sqm and result.fees.annual_fee_per_sqm.value)
            }

        if result.loans:
            extracted_summary['loans'] = len(result.loans)

        # Pretty print extraction results
        print(f"📊 Extraction Results:")
        print(f"   Coverage: {result.coverage_percentage:.1f}%")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print()

        print(f"✅ Metadata:")
        for key, value in extracted_summary['metadata'].items():
            status = "✓" if value else "✗"
            print(f"   {status} {key}")
        print()

        print(f"👔 Governance:")
        for key, value in extracted_summary['governance'].items():
            if key == 'board_members':
                print(f"   {'✓' if value > 0 else '✗'} {key}: {value}")
            else:
                status = "✓" if value else "✗"
                print(f"   {status} {key}")
        print()

        print(f"💰 Financial:")
        if 'income' in extracted_summary['financial']:
            print(f"   Income Statement:")
            for key, value in extracted_summary['financial']['income'].items():
                status = "✓" if value else "✗"
                print(f"      {status} {key}")
        if 'balance' in extracted_summary['financial']:
            print(f"   Balance Sheet:")
            for key, value in extracted_summary['financial']['balance'].items():
                status = "✓" if value else "✗"
                print(f"      {status} {key}")
        print()

        print(f"🏢 Property:")
        for key, value in extracted_summary['property'].items():
            status = "✓" if value else "✗"
            print(f"   {status} {key}")
        print()

        print(f"💳 Fees:")
        for key, value in extracted_summary['fees'].items():
            status = "✓" if value else "✗"
            print(f"   {status} {key}")
        print()

        print(f"💵 Loans: {extracted_summary['loans']} loan(s)")
        print()

        # Save detailed analysis
        analysis_file = output_dir / f"{test_case['name'].replace('.pdf', '')}_analysis.json"
        analysis_data = {
            'pdf_name': test_case['name'],
            'baseline_coverage': test_case['baseline_coverage'],
            'new_coverage': test_case['new_coverage'],
            'total_pages': total_pages,
            'total_chars': len(total_text),
            'financial_pages': financial_pages,
            'governance_pages': governance_pages,
            'property_pages': property_pages,
            'docling_headings': headings,
            'docling_image_markers': image_markers,
            'financial_sections_detected': financial_sections,
            'governance_sections_detected': governance_sections,
            'extraction_results': extracted_summary,
            'extraction_coverage': result.coverage_percentage,
            'extraction_confidence': result.confidence_score
        }
        analysis_file.write_text(json.dumps(analysis_data, indent=2, ensure_ascii=False))

        print(f"💾 Detailed analysis saved to: {analysis_file.name}")
        print()

    except Exception as e:
        print(f"❌ Extraction analysis failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        continue

    # Phase 4: Gap Analysis
    print("=" * 80)
    print("PHASE 4: GAP ANALYSIS")
    print("=" * 80)
    print()

    # Compare what's in the PDF vs what was extracted
    gaps = []

    # Financial gaps
    if financial_pages and not extracted_summary['financial']:
        gaps.append({
            'category': 'Financial',
            'issue': f'Financial keywords found on pages {financial_pages} but no financial data extracted',
            'severity': 'HIGH',
            'possible_cause': 'Section detection failure, table extraction failure, or agent routing issue'
        })
    elif financial_pages and extracted_summary['financial']:
        missing_income = []
        missing_balance = []
        if 'income' in extracted_summary['financial']:
            missing_income = [k for k, v in extracted_summary['financial']['income'].items() if not v]
        if 'balance' in extracted_summary['financial']:
            missing_balance = [k for k, v in extracted_summary['financial']['balance'].items() if not v]

        if missing_income or missing_balance:
            gaps.append({
                'category': 'Financial',
                'issue': f'Partial financial extraction: Missing {missing_income + missing_balance}',
                'severity': 'MEDIUM',
                'possible_cause': 'Incomplete table parsing or value extraction'
            })

    # Governance gaps
    if governance_pages and not any(extracted_summary['governance'].values()):
        gaps.append({
            'category': 'Governance',
            'issue': f'Governance keywords found on pages {governance_pages} but no governance data extracted',
            'severity': 'HIGH',
            'possible_cause': 'Agent routing failure or context window issues'
        })

    # Property gaps
    if property_pages and not any(extracted_summary['property'].values()):
        gaps.append({
            'category': 'Property',
            'issue': f'Property keywords found on pages {property_pages} but no property data extracted',
            'severity': 'MEDIUM',
            'possible_cause': 'Pattern matching failure or text formatting issues'
        })

    print(f"🔍 Identified Gaps: {len(gaps)}")
    print()

    if gaps:
        for gap in gaps:
            print(f"   [{gap['severity']}] {gap['category']}:")
            print(f"      Issue: {gap['issue']}")
            print(f"      Possible cause: {gap['possible_cause']}")
            print()
    else:
        print(f"   ✅ No major gaps identified")
        print()

    # Phase 5: Recommendations
    print("=" * 80)
    print("PHASE 5: RECOMMENDATIONS")
    print("=" * 80)
    print()

    recommendations = []

    # Based on gap analysis
    if any(g['category'] == 'Financial' for g in gaps):
        recommendations.append({
            'priority': 'P0',
            'action': 'Enhance financial section detection',
            'details': f'Financial data present on pages {financial_pages} but not extracted. Need better table parsing or section routing.'
        })

    if any(g['category'] == 'Governance' for g in gaps):
        recommendations.append({
            'priority': 'P1',
            'action': 'Fix governance agent context',
            'details': f'Governance data present on pages {governance_pages}. Check if agent receives correct page context.'
        })

    if image_markers > total_pages * 0.5:
        recommendations.append({
            'priority': 'P1',
            'action': 'Consider OCR enhancement',
            'details': f'{image_markers} image markers detected ({image_markers/total_pages:.0%} of pages). May need better OCR.'
        })

    if len(headings) < 5:
        recommendations.append({
            'priority': 'P1',
            'action': 'Improve structure detection',
            'details': f'Only {len(headings)} headings detected. Document may have poor structure or need better parsing.'
        })

    print(f"📋 Recommendations ({len(recommendations)}):")
    print()

    for rec in recommendations:
        print(f"   [{rec['priority']}] {rec['action']}")
        print(f"      {rec['details']}")
        print()

    # Save recommendations
    rec_file = output_dir / f"{test_case['name'].replace('.pdf', '')}_recommendations.json"
    rec_file.write_text(json.dumps({'gaps': gaps, 'recommendations': recommendations}, indent=2, ensure_ascii=False))

print()
print("=" * 80)
print("ULTRATHINKING ANALYSIS COMPLETE")
print("=" * 80)
print()

print(f"📁 All analysis files saved to: {output_dir}/")
print()
print(f"📊 Summary:")
print(f"   PDFs analyzed: {len(TEST_CASES)}")
print(f"   Output files: {len(list(output_dir.glob('*')))} files")
print()

print("🎯 Next Steps:")
print("   1. Review markdown files to understand document structure")
print("   2. Check analysis JSON for specific gap patterns")
print("   3. Implement targeted fixes based on recommendations")
print("   4. Re-test to validate improvements")
print()
