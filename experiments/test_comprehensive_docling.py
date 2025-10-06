#!/usr/bin/env python3
"""
Test Comprehensive Docling Extraction (All 13 Agents)

Validates extraction of ALL 59 fields across 13 agents to capture every fact
from Swedish BRF documents.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from gracian_pipeline.core.docling_adapter_comprehensive import ComprehensiveDoclingAdapter


def test_comprehensive_extraction():
    """Test comprehensive extraction on test document."""

    # Test document
    test_pdf = "SRS/brf_198532.pdf"

    print("="*80)
    print("🔬 COMPREHENSIVE DOCLING EXTRACTION TEST - ALL 13 AGENTS")
    print("="*80)
    print(f"\n📄 Test Document: {test_pdf}")
    print(f"🎯 Target: Extract ALL 13 agents (59 total fields)")
    print(f"📊 Goal: 95%+ coverage, capture every fact except boilerplate\n")

    # Initialize adapter
    adapter = ComprehensiveDoclingAdapter()

    # Run extraction
    start_time = time.time()
    result = adapter.extract_brf_data_comprehensive(test_pdf)
    elapsed = time.time() - start_time

    if result['status'] == 'scanned':
        print("\n⚠️  SCANNED PDF - Cannot test comprehensive extraction")
        return

    # Generate detailed report
    print("\n" + "="*80)
    print("📋 DETAILED EXTRACTION RESULTS")
    print("="*80)

    report = generate_detailed_report(result, elapsed)

    # Save results
    output_dir = Path("experiments/comparison_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"comprehensive_docling_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'pdf': test_pdf,
            'elapsed_seconds': round(elapsed, 1),
            'coverage': result['coverage_metrics'],
            'results': result
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved: {output_file}")

    # Generate markdown report
    report_file = output_dir / f"COMPREHENSIVE_REPORT_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 Report: {report_file}")

    return result


def generate_detailed_report(result: Dict[str, Any], elapsed: float) -> str:
    """Generate comprehensive markdown report."""

    coverage = result['coverage_metrics']
    agents = {k: v for k, v in result.items() if k.endswith('_agent')}

    report = f"""# Comprehensive Docling Extraction - All 13 Agents

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Document**: brf_198532.pdf (BRF Björk och Plaza)
**Method**: Docling + GPT-4o (Single Combined Call)

---

## 📊 **Coverage Summary**

| Metric | Value | Status |
|--------|-------|--------|
| **Total Fields** | {coverage['total_fields']} | - |
| **Extracted Fields** | {coverage['extracted_fields']} | - |
| **Coverage** | **{coverage['coverage_percent']}%** | {'✅ EXCEEDS 95%' if coverage['coverage_percent'] >= 95 else '🟡 APPROACHING 95%' if coverage['coverage_percent'] >= 85 else '🔴 BELOW TARGET'} |
| **Processing Time** | {elapsed:.1f}s | {'✅ <60s' if elapsed < 60 else '⚠️ >60s'} |

---

## 🔍 **Detailed Results by Agent**

"""

    # Agent details
    agent_details = {
        'governance_agent': ('👤 GOVERNANCE AGENT', [
            ('chairman', 'Chairman'),
            ('board_members', 'Board Members'),
            ('auditor_name', 'Auditor Name'),
            ('audit_firm', 'Audit Firm'),
            ('nomination_committee', 'Nomination Committee'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'financial_agent': ('💰 FINANCIAL AGENT', [
            ('revenue', 'Revenue (SEK)'),
            ('expenses', 'Expenses (SEK)'),
            ('assets', 'Assets (SEK)'),
            ('liabilities', 'Liabilities (SEK)'),
            ('equity', 'Equity (SEK)'),
            ('surplus', 'Surplus (SEK)'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'property_agent': ('🏠 PROPERTY AGENT', [
            ('designation', 'Designation'),
            ('address', 'Address'),
            ('postal_code', 'Postal Code'),
            ('city', 'City'),
            ('built_year', 'Built Year'),
            ('apartments', 'Apartments'),
            ('energy_class', 'Energy Class'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'notes_depreciation_agent': ('📝 NOTES: DEPRECIATION', [
            ('depreciation_method', 'Method'),
            ('useful_life_years', 'Useful Life'),
            ('depreciation_base', 'Base'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'notes_maintenance_agent': ('📝 NOTES: MAINTENANCE', [
            ('maintenance_plan', 'Plan'),
            ('maintenance_budget', 'Budget'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'notes_tax_agent': ('📝 NOTES: TAX', [
            ('current_tax', 'Current Tax'),
            ('deferred_tax', 'Deferred Tax'),
            ('tax_policy', 'Tax Policy'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'events_agent': ('📅 EVENTS AGENT', [
            ('key_events', 'Key Events'),
            ('maintenance_budget', 'Maintenance Budget'),
            ('annual_meeting_date', 'Annual Meeting Date'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'audit_agent': ('✅ AUDIT AGENT', [
            ('auditor', 'Auditor'),
            ('opinion', 'Opinion'),
            ('clean_opinion', 'Clean Opinion'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'loans_agent': ('💳 LOANS AGENT', [
            ('outstanding_loans', 'Outstanding Loans (SEK)'),
            ('interest_rate', 'Interest Rate (%)'),
            ('amortization', 'Amortization (SEK)'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'reserves_agent': ('💼 RESERVES AGENT', [
            ('reserve_fund', 'Reserve Fund (SEK)'),
            ('monthly_fee', 'Monthly Fee (SEK)'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'energy_agent': ('⚡ ENERGY AGENT', [
            ('energy_class', 'Energy Class'),
            ('energy_performance', 'Performance'),
            ('inspection_date', 'Inspection Date'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'fees_agent': ('💵 FEES AGENT', [
            ('monthly_fee', 'Monthly Fee (SEK)'),
            ('planned_fee_change', 'Planned Change'),
            ('fee_policy', 'Fee Policy'),
            ('evidence_pages', 'Evidence Pages')
        ]),
        'cashflow_agent': ('💸 CASHFLOW AGENT', [
            ('cash_in', 'Cash In (SEK)'),
            ('cash_out', 'Cash Out (SEK)'),
            ('cash_change', 'Cash Change (SEK)'),
            ('evidence_pages', 'Evidence Pages')
        ])
    }

    for agent_id, (title, fields) in agent_details.items():
        agent_data = result.get(agent_id, {})

        extracted_count = sum(1 for field, _ in fields if field != 'evidence_pages' and
                             agent_data.get(field) is not None and
                             agent_data.get(field) != [] and
                             agent_data.get(field) != "")

        total_count = len([f for f, _ in fields if f != 'evidence_pages'])
        status = '✅' if extracted_count == total_count else '⚠️' if extracted_count > 0 else '❌'

        report += f"\n### {title}\n\n"
        report += f"**Coverage**: {extracted_count}/{total_count} fields {status}\n\n"
        report += "| Field | Value | Status |\n"
        report += "|-------|-------|--------|\n"

        for field, label in fields:
            value = agent_data.get(field)

            # Format value
            if value is None:
                formatted_value = "null"
                field_status = "❌"
            elif value == [] or value == "":
                formatted_value = "empty"
                field_status = "❌"
            elif isinstance(value, list):
                if field == 'evidence_pages':
                    formatted_value = f"{value}"
                    field_status = "📍"
                elif len(value) > 0:
                    formatted_value = f"{len(value)} items: {', '.join(str(v) for v in value[:3])}"
                    if len(value) > 3:
                        formatted_value += "..."
                    field_status = "✅"
                else:
                    formatted_value = "empty list"
                    field_status = "❌"
            elif isinstance(value, (int, float)):
                formatted_value = f"{value:,}" if isinstance(value, int) else f"{value}"
                field_status = "✅"
            elif isinstance(value, bool):
                formatted_value = "Yes" if value else "No"
                field_status = "✅"
            else:
                formatted_value = str(value)
                field_status = "✅" if value else "❌"

            report += f"| {label} | {formatted_value} | {field_status} |\n"

        report += "\n"

    # Summary
    report += "\n---\n\n## 📈 **Analysis**\n\n"

    if coverage['coverage_percent'] >= 95:
        report += f"✅ **EXCELLENT**: Achieved {coverage['coverage_percent']}% coverage, exceeding 95% target.\n\n"
    elif coverage['coverage_percent'] >= 85:
        report += f"🟡 **GOOD**: Achieved {coverage['coverage_percent']}% coverage, approaching 95% target.\n\n"
    else:
        report += f"🔴 **NEEDS IMPROVEMENT**: {coverage['coverage_percent']}% coverage below 95% target.\n\n"

    report += "### **Strengths**:\n"
    report += "- Single combined GPT-4o call captures all agents\n"
    report += "- Docling's native table detection extracts financial data\n"
    report += "- Swedish-specific prompting preserves exact names\n"
    report += "- Evidence pages provided for verification\n\n"

    report += "### **Next Steps**:\n"
    report += "1. Validate extracted values against ground truth\n"
    report += "2. Test on additional documents (SRS corpus)\n"
    report += "3. Identify patterns in missing fields\n"
    report += "4. Fine-tune prompts for notes sections\n\n"

    return report


if __name__ == "__main__":
    test_comprehensive_extraction()
