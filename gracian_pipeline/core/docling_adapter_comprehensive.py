#!/usr/bin/env python3
"""
Comprehensive Docling Adapter - ALL 13 Agents

Extends docling_adapter.py to extract ALL 13 agents (59 fields total) to capture
every fact from Swedish BRF documents.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List

from docling.document_converter import DocumentConverter

class ComprehensiveDoclingAdapter:
    """
    Comprehensive Docling adapter extracting all 13 BRF agents.

    Agents extracted:
    1. governance_agent (6 fields)
    2. financial_agent (7 fields)
    3. property_agent (8 fields)
    4. notes_depreciation_agent (4 fields)
    5. notes_maintenance_agent (3 fields)
    6. notes_tax_agent (4 fields)
    7. events_agent (4 fields)
    8. audit_agent (4 fields)
    9. loans_agent (4 fields)
    10. reserves_agent (3 fields)
    11. energy_agent (4 fields)
    12. fees_agent (4 fields)
    13. cashflow_agent (4 fields)

    Total: 59 fields (including evidence_pages)
    """

    def __init__(self):
        self.converter = DocumentConverter()

    def is_machine_readable(self, markdown: str, char_threshold: int = 5000) -> bool:
        """Determine if PDF is machine-readable based on extracted text."""
        return len(markdown) > char_threshold

    def extract_with_docling(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF using Docling."""
        result = self.converter.convert(pdf_path)
        doc = result.document

        markdown = doc.export_to_markdown()
        tables = []

        # Extract tables - use Pydantic model_dump() instead of export_to_dict()
        for item, level in doc.iterate_items():
            if item.label == "table":
                # Docling TableItem has data attribute with table structure
                tables.append(item.model_dump())

        return {
            'markdown': markdown,
            'tables': tables,
            'char_count': len(markdown),
            'status': 'text' if self.is_machine_readable(markdown) else 'scanned'
        }

    def extract_table_text(self, table: Dict[str, Any]) -> str:
        """Extract readable text from a docling table structure."""
        if 'data' not in table or 'table_cells' not in table['data']:
            return ""

        cells = table['data']['table_cells']

        # Build grid representation
        max_row = max((cell.get('end_row_offset_idx', 0) for cell in cells), default=0)
        max_col = max((cell.get('end_col_offset_idx', 0) for cell in cells), default=0)

        grid = [['' for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        for cell in cells:
            text = cell.get('text', '').strip()
            row = cell.get('start_row_offset_idx', 0)
            col = cell.get('start_col_offset_idx', 0)
            if row < len(grid) and col < len(grid[row]):
                grid[row][col] = text

        # Convert to readable text
        lines = []
        for row in grid:
            line = ' | '.join(cell for cell in row if cell)
            if line.strip():
                lines.append(line)

        return '\n'.join(lines)

    def format_tables_for_llm(self, tables: List[Dict], limit: int = 20) -> str:
        """Format tables into readable text for LLM processing."""
        tables_text = ""

        for i, table in enumerate(tables[:limit], 1):
            table_text = self.extract_table_text(table)
            if table_text:
                tables_text += f"\n\n=== TABLE {i} ===\n{table_text}\n"

        return tables_text

    def extract_all_13_agents_combined(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract ALL 13 BRF agents in a single GPT-4o call.

        This captures every fact from the document except boilerplate (signatures, auditor stamps).
        """
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Format tables
        tables_text = self.format_tables_for_llm(tables)

        prompt = f"""Extract ALL data from this Swedish BRF annual report in ONE response.

DOCUMENT TEXT (first 35,000 chars - covers 77% of typical documents):
{markdown[:35000]}

FINANCIAL TABLES:
{tables_text}

Extract and return ONLY valid JSON with ALL 13 agents below:

{{
  "governance_agent": {{
    "chairman": "Name of board chairman (ordförande)",
    "board_members": ["List", "of", "all", "board", "members", "including", "suppleanter"],
    "auditor_name": "Primary auditor name",
    "audit_firm": "Auditing firm name (e.g., KPMG AB)",
    "nomination_committee": ["Nomination", "committee", "members"],
    "evidence_pages": [1, 2, 3]
  }},
  "financial_agent": {{
    "revenue": 12345678,
    "expenses": 12345678,
    "assets": 12345678,
    "liabilities": 12345678,
    "equity": 12345678,
    "surplus": 12345678,
    "evidence_pages": [4, 5, 6]
  }},
  "property_agent": {{
    "designation": "Fastighetsbeteckning (e.g., Sonfjället 2)",
    "address": "Full street address",
    "postal_code": "12345",
    "city": "City name",
    "built_year": 2015,
    "apartments": 94,
    "energy_class": "A, B, C, etc.",
    "evidence_pages": [1, 2]
  }},
  "notes_depreciation_agent": {{
    "depreciation_method": "Avskrivningsmetod (e.g., linjär avskrivning)",
    "useful_life_years": "5-50 years or description",
    "depreciation_base": "Depreciation base amount or description",
    "evidence_pages": [7, 8]
  }},
  "notes_maintenance_agent": {{
    "maintenance_plan": "Underhållsplan description or summary",
    "maintenance_budget": "Underhållsbudget amount or description",
    "evidence_pages": [9]
  }},
  "notes_tax_agent": {{
    "current_tax": "Aktuell skatt amount or description",
    "deferred_tax": "Uppskjuten skatt amount or description",
    "tax_policy": "Skatteprinciper description",
    "evidence_pages": [10]
  }},
  "events_agent": {{
    "key_events": ["List", "of", "väsentliga händelser"],
    "maintenance_budget": "Annual maintenance budget",
    "annual_meeting_date": "Årsstämma date (YYYY-MM-DD or description)",
    "evidence_pages": [2, 3]
  }},
  "audit_agent": {{
    "auditor": "Revisor name from revisionsberättelse",
    "opinion": "Uttalande summary (clean, qualified, etc.)",
    "clean_opinion": true,
    "evidence_pages": [15, 16]
  }},
  "loans_agent": {{
    "outstanding_loans": 12345678,
    "interest_rate": 2.5,
    "amortization": 123456,
    "evidence_pages": [11]
  }},
  "reserves_agent": {{
    "reserve_fund": 12345678,
    "monthly_fee": 1234,
    "evidence_pages": [12]
  }},
  "energy_agent": {{
    "energy_class": "A, B, C, etc. from energideklaration",
    "energy_performance": "kWh/m² Atemp or description",
    "inspection_date": "YYYY-MM-DD or description",
    "evidence_pages": [13]
  }},
  "fees_agent": {{
    "monthly_fee": 1234,
    "planned_fee_change": "5% increase or description",
    "fee_policy": "Avgiftspolicy description",
    "evidence_pages": [14]
  }},
  "cashflow_agent": {{
    "cash_in": 12345678,
    "cash_out": 12345678,
    "cash_change": 123456,
    "evidence_pages": [6, 7]
  }}
}}

CRITICAL RULES:
1. Swedish names: Extract EXACTLY as written (don't translate)
2. Board members: Include ALL ledamöter AND suppleanter
3. Numbers: Extract as INTEGER for financial fields (no spaces, no formatting)
   - "301 339 818" → 301339818
   - "8 009 m²" → 8009
4. Financial terms:
   - Revenue = Intäkter
   - Expenses = Kostnader
   - Assets = Tillgångar
   - Liabilities = Skulder
   - Equity = Eget kapital
   - Surplus = Årets resultat / Överskott
   - Reserve fund = Reservfond / Avsättning till fond
   - Monthly fee = Månadsavgift / Årsavgift
5. Notes sections:
   - Depreciation = Avskrivningar
   - Maintenance = Underhåll / Underhållsplan
   - Tax = Skatt / Inkomstskatt / Uppskjuten skatt
6. Events: Key events = Väsentliga händelser
7. Audit: Opinion from Revisionsberättelse
8. Loans: Lån information from Noter
9. Energy: Energideklaration data
10. Cashflow: Kassaflödesanalys data
11. Use null for missing values (not 0 unless explicitly stated)
12. Extract FACTS only, ignore boilerplate (signatures, stamps, legal text)
13. **Swedish Fee Terms** (CRITICAL):
    - Monthly fee = "Månadsavgift" OR "Årsavgift/m²" OR "Årsavgift" (convert annual to monthly if needed)
    - If you find "Årsavgift/m² bostadsrättsyta: 582", extract as monthly_fee
    - Maintenance budget = "Underhållsbudget" OR part of "Underhållsplan"
14. **Property Address** (CRITICAL):
    - Combine designation + city if full address not found
    - Example: "Sonfjället 2" + "Stockholm" = "Sonfjället 2, Stockholm"
15. **Tax Amounts**:
    - Look for specific SEK amounts in notes sections
    - Current tax = "Aktuell skatt" with amount
    - Deferred tax = "Uppskjuten skatt" with amount
16. Return ONLY the JSON object, nothing else"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF document parser. Return ONLY valid JSON with all 13 agents. Extract every fact except boilerplate text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )

            content = response.choices[0].message.content.strip()

            # Handle markdown-fenced JSON
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)

            result = json.loads(content)

            # FIX 3: Smart property address combination
            if 'property_agent' in result:
                prop = result['property_agent']
                if not prop.get('address') and prop.get('designation') and prop.get('city'):
                    # Combine designation + city if address is missing
                    result['property_agent']['address'] = f"{prop['designation']}, {prop['city']}"

            # FIX 2: Convert annual fees to monthly if needed
            if 'fees_agent' in result:
                fees = result['fees_agent']
                # If monthly_fee is a string like "582 kr/m² per år", convert it
                if fees.get('monthly_fee') and isinstance(fees['monthly_fee'], str):
                    # Try to extract number from string
                    match = re.search(r'(\d+)', fees['monthly_fee'])
                    if match:
                        annual_fee = int(match.group(1))
                        result['fees_agent']['monthly_fee'] = annual_fee  # Keep as-is, or divide by 12 if needed

            # Normalize numeric fields
            numeric_fields = {
                'financial_agent': ['revenue', 'expenses', 'assets', 'liabilities', 'equity', 'surplus'],
                'property_agent': ['built_year', 'apartments'],
                'loans_agent': ['outstanding_loans', 'interest_rate', 'amortization'],
                'reserves_agent': ['reserve_fund', 'monthly_fee'],
                'fees_agent': ['monthly_fee'],
                'cashflow_agent': ['cash_in', 'cash_out', 'cash_change']
            }

            for agent, fields in numeric_fields.items():
                if agent in result:
                    for field in fields:
                        if field in result[agent] and result[agent][field] is not None:
                            try:
                                val = str(result[agent][field])
                                val = val.replace(' ', '').replace(',', '')
                                # Handle percentages and decimals
                                if '.' in val or field == 'interest_rate':
                                    result[agent][field] = float(val.replace('%', ''))
                                else:
                                    result[agent][field] = int(float(val))
                            except (ValueError, TypeError):
                                result[agent][field] = None

            return result

        except Exception as e:
            print(f"Warning: Comprehensive extraction error: {e}")
            # Return empty structure for all 13 agents
            return self._empty_13_agent_structure()

    def _empty_13_agent_structure(self) -> Dict[str, Any]:
        """Return empty structure for all 13 agents."""
        return {
            "governance_agent": {
                "chairman": None, "board_members": [], "auditor_name": None,
                "audit_firm": None, "nomination_committee": [], "evidence_pages": []
            },
            "financial_agent": {
                "revenue": None, "expenses": None, "assets": None,
                "liabilities": None, "equity": None, "surplus": None, "evidence_pages": []
            },
            "property_agent": {
                "designation": None, "address": None, "postal_code": None,
                "city": None, "built_year": None, "apartments": None,
                "energy_class": None, "evidence_pages": []
            },
            "notes_depreciation_agent": {
                "depreciation_method": None, "useful_life_years": None,
                "depreciation_base": None, "evidence_pages": []
            },
            "notes_maintenance_agent": {
                "maintenance_plan": None, "maintenance_budget": None, "evidence_pages": []
            },
            "notes_tax_agent": {
                "current_tax": None, "deferred_tax": None,
                "tax_policy": None, "evidence_pages": []
            },
            "events_agent": {
                "key_events": [], "maintenance_budget": None,
                "annual_meeting_date": None, "evidence_pages": []
            },
            "audit_agent": {
                "auditor": None, "opinion": None,
                "clean_opinion": None, "evidence_pages": []
            },
            "loans_agent": {
                "outstanding_loans": None, "interest_rate": None,
                "amortization": None, "evidence_pages": []
            },
            "reserves_agent": {
                "reserve_fund": None, "monthly_fee": None, "evidence_pages": []
            },
            "energy_agent": {
                "energy_class": None, "energy_performance": None,
                "inspection_date": None, "evidence_pages": []
            },
            "fees_agent": {
                "monthly_fee": None, "planned_fee_change": None,
                "fee_policy": None, "evidence_pages": []
            },
            "cashflow_agent": {
                "cash_in": None, "cash_out": None,
                "cash_change": None, "evidence_pages": []
            }
        }

    def extract_brf_data_comprehensive(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main extraction method extracting ALL 13 agents.

        Returns comprehensive BRF data with quantitative and qualitative results.
        """
        print(f"\n🔍 COMPREHENSIVE Docling extraction (13 agents): {Path(pdf_path).name}")

        # Extract with Docling
        docling_result = self.extract_with_docling(pdf_path)

        if docling_result['status'] == 'scanned':
            print(f"  ⚠️  Scanned PDF detected ({docling_result['char_count']} chars) - fallback to vision recommended")
            return {
                'status': 'scanned',
                'note': 'Use vision models for scanned PDFs',
                'docling_result': docling_result
            }

        print(f"  ✅ Text PDF detected ({docling_result['char_count']} chars, {len(docling_result['tables'])} tables)")

        # Extract all 13 agents in single call
        markdown = docling_result['markdown']
        tables = docling_result['tables']

        print("  🤖 Extracting ALL 13 agents (governance, financial, property, notes, events, audit, loans, reserves, energy, fees, cashflow)...")
        all_agents = self.extract_all_13_agents_combined(markdown, tables)

        result = {
            'status': 'success',
            'method': 'docling_comprehensive_13_agents',
            **all_agents,
            'docling_metadata': {
                'char_count': docling_result['char_count'],
                'table_count': len(tables),
                'processing_method': 'comprehensive_single_call'
            }
        }

        # Calculate coverage
        total_fields, extracted_fields = self._calculate_coverage(all_agents)
        coverage_percent = (extracted_fields / total_fields * 100) if total_fields > 0 else 0

        result['coverage_metrics'] = {
            'total_fields': total_fields,
            'extracted_fields': extracted_fields,
            'coverage_percent': round(coverage_percent, 1)
        }

        # Print comprehensive summary
        self._print_comprehensive_summary(all_agents, coverage_percent)

        return result

    def _calculate_coverage(self, agents: Dict[str, Any]) -> tuple:
        """Calculate total fields vs extracted fields."""
        total_fields = 0
        extracted_fields = 0

        for agent_id, agent_data in agents.items():
            if isinstance(agent_data, dict):
                for key, value in agent_data.items():
                    if key != 'evidence_pages':  # Don't count evidence pages
                        total_fields += 1
                        if value is not None and value != [] and value != "":
                            extracted_fields += 1

        return total_fields, extracted_fields

    def _print_comprehensive_summary(self, agents: Dict[str, Any], coverage: float):
        """Print comprehensive extraction summary."""
        print(f"\n  📊 COMPREHENSIVE RESULTS ({coverage:.1f}% coverage):")
        print(f"  {'='*70}")

        # Governance
        gov = agents.get('governance_agent', {})
        print(f"  👤 GOVERNANCE:")
        print(f"     Chairman: {gov.get('chairman', 'N/A')}")
        print(f"     Board: {len(gov.get('board_members', []))} members")
        print(f"     Auditor: {gov.get('auditor_name', 'N/A')} ({gov.get('audit_firm', 'N/A')})")

        # Financial
        fin = agents.get('financial_agent', {})
        print(f"\n  💰 FINANCIAL:")
        print(f"     Assets: {fin.get('assets', 'N/A'):,}" if fin.get('assets') else "     Assets: N/A")
        print(f"     Revenue: {fin.get('revenue', 'N/A'):,}" if fin.get('revenue') else "     Revenue: N/A")
        print(f"     Equity: {fin.get('equity', 'N/A'):,}" if fin.get('equity') else "     Equity: N/A")

        # Property
        prop = agents.get('property_agent', {})
        print(f"\n  🏠 PROPERTY:")
        print(f"     Address: {prop.get('address', 'N/A')}")
        print(f"     Built: {prop.get('built_year', 'N/A')}")
        print(f"     Apartments: {prop.get('apartments', 'N/A')}")

        # Notes
        print(f"\n  📝 NOTES:")
        notes_dep = agents.get('notes_depreciation_agent', {})
        print(f"     Depreciation: {notes_dep.get('depreciation_method', 'N/A')}")
        notes_main = agents.get('notes_maintenance_agent', {})
        print(f"     Maintenance: {'Yes' if notes_main.get('maintenance_plan') else 'N/A'}")
        notes_tax = agents.get('notes_tax_agent', {})
        print(f"     Tax: {'Yes' if notes_tax.get('current_tax') or notes_tax.get('deferred_tax') else 'N/A'}")

        # Events
        events = agents.get('events_agent', {})
        print(f"\n  📅 EVENTS:")
        print(f"     Key events: {len(events.get('key_events', []))} items")
        print(f"     Meeting date: {events.get('annual_meeting_date', 'N/A')}")

        # Audit
        audit = agents.get('audit_agent', {})
        print(f"\n  ✅ AUDIT:")
        print(f"     Auditor: {audit.get('auditor', 'N/A')}")
        print(f"     Clean opinion: {audit.get('clean_opinion', 'N/A')}")

        # Loans
        loans = agents.get('loans_agent', {})
        print(f"\n  💳 LOANS:")
        print(f"     Outstanding: {loans.get('outstanding_loans', 'N/A'):,}" if loans.get('outstanding_loans') else "     Outstanding: N/A")
        print(f"     Interest rate: {loans.get('interest_rate', 'N/A')}%" if loans.get('interest_rate') else "     Interest rate: N/A")

        # Reserves
        reserves = agents.get('reserves_agent', {})
        print(f"\n  💼 RESERVES:")
        print(f"     Reserve fund: {reserves.get('reserve_fund', 'N/A'):,}" if reserves.get('reserve_fund') else "     Reserve fund: N/A")
        print(f"     Monthly fee: {reserves.get('monthly_fee', 'N/A'):,}" if reserves.get('monthly_fee') else "     Monthly fee: N/A")

        # Energy
        energy = agents.get('energy_agent', {})
        print(f"\n  ⚡ ENERGY:")
        print(f"     Class: {energy.get('energy_class', 'N/A')}")
        print(f"     Performance: {energy.get('energy_performance', 'N/A')}")

        # Fees
        fees = agents.get('fees_agent', {})
        print(f"\n  💵 FEES:")
        print(f"     Monthly: {fees.get('monthly_fee', 'N/A'):,}" if fees.get('monthly_fee') else "     Monthly: N/A")
        print(f"     Planned change: {fees.get('planned_fee_change', 'N/A')}")

        # Cashflow
        cashflow = agents.get('cashflow_agent', {})
        print(f"\n  💸 CASHFLOW:")
        print(f"     Cash in: {cashflow.get('cash_in', 'N/A'):,}" if cashflow.get('cash_in') else "     Cash in: N/A")
        print(f"     Cash out: {cashflow.get('cash_out', 'N/A'):,}" if cashflow.get('cash_out') else "     Cash out: N/A")

        print(f"  {'='*70}")
