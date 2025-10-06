"""
Ultra-Comprehensive Docling Adapter
Extracts ALL 13 agents with expanded comprehensive_details fields.

Based on human validation findings - captures the ~70% of information
that exists in documents but wasn't in the base 46-field schema.

Total fields: ~80+ (46 base + 30-40 comprehensive additions)
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List

from docling.document_converter import DocumentConverter
from openai import OpenAI

from .schema_comprehensive import (
    get_comprehensive_types,
    schema_comprehensive_prompt_block,
    get_field_counts
)


class UltraComprehensiveDoclingAdapter:
    """
    Ultra-comprehensive extraction adapter.

    Extracts:
    - All 46 base schema fields
    - 30-40 comprehensive detail fields
    - Suppliers, contracts, apartment breakdowns, etc.
    - Complete financial note details
    """

    def __init__(self):
        self.converter = DocumentConverter()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def is_machine_readable(self, markdown: str, char_threshold: int = 5000) -> bool:
        """Determine if PDF is machine-readable based on extracted text."""
        return len(markdown.strip()) >= char_threshold

    def extract_with_docling(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF using Docling."""
        result = self.converter.convert(pdf_path)
        markdown = result.document.export_to_markdown()

        # Get tables using model_dump() (new Docling API)
        tables = []
        for item in result.document.tables:
            tables.append(item.model_dump())

        is_readable = self.is_machine_readable(markdown)

        return {
            'status': 'text' if is_readable else 'scanned',
            'markdown': markdown,
            'tables': tables,
            'char_count': len(markdown)
        }

    def extract_table_text(self, table: Dict[str, Any]) -> str:
        """Extract readable text from a docling table structure."""
        if not table or 'data' not in table:
            return ""

        cells = table['data'].get('table_cells', [])
        if not cells:
            return ""

        # Build grid from cell positions
        max_row = max((cell.get('end_row_offset_idx', 0) for cell in cells), default=0)
        max_col = max((cell.get('end_col_offset_idx', 0) for cell in cells), default=0)

        grid = [['' for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        for cell in cells:
            start_row = cell.get('start_row_offset_idx', 0)
            start_col = cell.get('start_col_offset_idx', 0)
            text = cell.get('text', '').strip()
            if text:
                grid[start_row][start_col] = text

        # Convert grid to readable text
        lines = []
        for row in grid:
            row_text = ' | '.join([cell if cell else '' for cell in row])
            if row_text.strip():
                lines.append(row_text)

        return '\n'.join(lines)

    def format_tables_for_llm(self, tables: List[Dict], limit: int = 25) -> str:
        """
        Format tables into readable text for LLM processing.
        INCREASED LIMIT to 25 to capture more financial notes.
        """
        if not tables:
            return "No tables detected."

        formatted = f"TABLES DETECTED: {len(tables)} total\n\n"

        for i, table in enumerate(tables[:limit], 1):
            table_text = self.extract_table_text(table)
            if table_text:
                formatted += f"--- TABLE {i} ---\n{table_text}\n\n"

        if len(tables) > limit:
            formatted += f"(Note: {len(tables) - limit} additional tables not shown due to space)\n"

        return formatted

    def extract_all_ultra_comprehensive(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract ALL 13 agents with ultra-comprehensive details in ONE GPT-4o call.

        Targets:
        - 46 base fields (from original schema)
        - 30-40 comprehensive detail fields
        - Total: ~80+ fields extracted
        """

        # Format tables for LLM
        tables_text = self.format_tables_for_llm(tables, limit=25)

        # Get field statistics
        stats = get_field_counts()
        total_base = sum(s['base_fields'] for s in stats.values())
        total_comprehensive = sum(s['comprehensive_fields'] for s in stats.values())

        # Build comprehensive prompt for ALL 13 agents
        prompt = f"""Extract ALL data from this Swedish BRF annual report in ONE response.

EXTRACTION MODE: ULTRA-COMPREHENSIVE
- Base schema fields: {total_base}
- Comprehensive detail fields: {total_comprehensive}
- TOTAL FIELDS: {total_comprehensive} fields across 13 agents

DOCUMENT TEXT (first 40,000 chars to capture more notes sections):
{markdown[:40000]}

{tables_text}

CRITICAL INSTRUCTIONS:

1. **Extract EVERY PIECE OF INFORMATION** - not just summary totals
2. **Suppliers & Contracts**: Extract complete list from "Förvaltning" section
3. **Apartment Breakdown**: Extract full distribution (1 rok, 2 rok, 3 rok, etc.)
4. **Financial Notes Details**: Extract complete line items from all notes tables
5. **Commercial Tenants**: Extract ALL tenants with lease terms
6. **Common Areas**: Extract all gemeensamma utrymmen
7. **Samfällighet**: Extract ownership percentage and what it manages
8. **Planned Maintenance**: Extract all planned actions with years
9. **Loan Details**: Extract provider, number, term, conditions
10. **Insurance**: Extract provider and full coverage description

AGENT SCHEMAS (with comprehensive fields):

**GOVERNANCE AGENT**
{schema_comprehensive_prompt_block('governance_agent')}

**FINANCIAL AGENT** (CRITICAL - Extract detailed breakdowns from notes)
{schema_comprehensive_prompt_block('financial_agent')}

**PROPERTY AGENT** (CRITICAL - Extract apartment breakdown, commercial tenants, common areas, samfällighet)
{schema_comprehensive_prompt_block('property_agent')}

**NOTES: DEPRECIATION AGENT**
{schema_comprehensive_prompt_block('notes_depreciation_agent')}

**NOTES: MAINTENANCE AGENT** (CRITICAL - Extract suppliers, planned actions, service contracts)
{schema_comprehensive_prompt_block('notes_maintenance_agent')}

**NOTES: TAX AGENT**
{schema_comprehensive_prompt_block('notes_tax_agent')}

**EVENTS AGENT**
{schema_comprehensive_prompt_block('events_agent')}

**AUDIT AGENT**
{schema_comprehensive_prompt_block('audit_agent')}

**LOANS AGENT** (CRITICAL - Extract provider, loan number, term, restructuring details)
{schema_comprehensive_prompt_block('loans_agent')}

**RESERVES AGENT**
{schema_comprehensive_prompt_block('reserves_agent')}

**ENERGY AGENT**
{schema_comprehensive_prompt_block('energy_agent')}

**FEES AGENT**
{schema_comprehensive_prompt_block('fees_agent')}

**CASHFLOW AGENT**
{schema_comprehensive_prompt_block('cashflow_agent')}

RETURN FORMAT:
{{
  "governance_agent": {{...all fields...}},
  "financial_agent": {{...all fields including detailed breakdowns...}},
  "property_agent": {{...all fields including apartment_breakdown, commercial_tenants, common_areas, samfällighet...}},
  "notes_depreciation_agent": {{...all fields...}},
  "notes_maintenance_agent": {{...all fields including suppliers, planned_actions, service_contracts...}},
  "notes_tax_agent": {{...all fields...}},
  "events_agent": {{...all fields...}},
  "audit_agent": {{...all fields...}},
  "loans_agent": {{...all fields including loan_provider, loan_number, loan_term...}},
  "reserves_agent": {{...all fields...}},
  "energy_agent": {{...all fields...}},
  "fees_agent": {{...all fields...}},
  "cashflow_agent": {{...all fields including activity breakdowns...}}
}}

IMPORTANT: Return ONLY valid JSON. Extract EVERYTHING visible in the document."""

        # Call GPT-4o with extended context
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from Swedish BRF documents. Extract EVERY piece of information available, not just summary fields."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=8000  # Increased for comprehensive extraction
        )

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown fences if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\n', '', content)
            content = re.sub(r'\n```$', '', content)

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Content: {content[:500]}")
            result = {}

        # Add metadata
        result['docling_metadata'] = {
            'char_count': len(markdown),
            'table_count': len(tables),
            'processing_method': 'ultra_comprehensive_single_call',
            'schema_version': 'comprehensive_v1',
            'total_fields_target': total_comprehensive
        }

        # Calculate comprehensive coverage
        from .schema_comprehensive import COMPREHENSIVE_TYPES
        extracted_count = 0
        for agent_id in COMPREHENSIVE_TYPES.keys():
            agent_data = result.get(agent_id, {})
            expected_fields = get_comprehensive_types(agent_id)
            for field in expected_fields.keys():
                if field != 'evidence_pages' and agent_data.get(field) is not None:
                    extracted_count += 1

        result['coverage_metrics'] = {
            'total_fields': total_comprehensive,
            'extracted_fields': extracted_count,
            'coverage_percent': round((extracted_count / total_comprehensive) * 100, 1)
        }

        return result

    def extract_brf_data_ultra(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main entry point for ultra-comprehensive BRF extraction.

        Returns dictionary with:
        - All 13 agent results (with comprehensive details)
        - Metadata (char_count, table_count, etc.)
        - Coverage metrics
        """
        # Extract with Docling
        docling_result = self.extract_with_docling(pdf_path)

        if docling_result['status'] == 'scanned':
            return {
                'status': 'scanned',
                'message': 'PDF appears to be scanned (low text content). Consider using vision models.',
                'char_count': docling_result['char_count']
            }

        # Extract all data with ultra-comprehensive schema
        result = self.extract_all_ultra_comprehensive(
            docling_result['markdown'],
            docling_result['tables']
        )

        result['status'] = 'success'
        result['pdf_path'] = pdf_path

        # Store docling markdown and tables for downstream processing (e.g., vision extraction)
        result['_docling_markdown'] = docling_result['markdown']
        result['_docling_tables'] = docling_result['tables']

        return result


if __name__ == "__main__":
    # Test the ultra-comprehensive adapter
    import sys
    from datetime import datetime
    from dotenv import load_dotenv

    load_dotenv()

    test_pdf = "SRS/brf_198532.pdf"

    if not os.path.exists(test_pdf):
        print(f"Test PDF not found: {test_pdf}")
        sys.exit(1)

    print("=" * 80)
    print("ULTRA-COMPREHENSIVE DOCLING EXTRACTION TEST")
    print("=" * 80)
    print(f"\nTest document: {test_pdf}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Show schema statistics
    print("Schema Statistics:")
    print("-" * 80)
    stats = get_field_counts()
    for agent_id, counts in stats.items():
        expansion_pct = ((counts['comprehensive_fields'] / counts['base_fields'] - 1) * 100)
        print(f"{agent_id:30} {counts['base_fields']:2d} → {counts['comprehensive_fields']:2d} (+{expansion_pct:5.1f}%)")

    total_base = sum(s['base_fields'] for s in stats.values())
    total_comp = sum(s['comprehensive_fields'] for s in stats.values())
    print("-" * 80)
    print(f"{'TOTAL':30} {total_base:2d} → {total_comp:2d} (+{((total_comp/total_base-1)*100):.1f}%)")
    print()

    # Run extraction
    adapter = UltraComprehensiveDoclingAdapter()

    import time
    start = time.time()
    result = adapter.extract_brf_data_ultra(test_pdf)
    elapsed = time.time() - start

    print(f"✅ Extraction complete in {elapsed:.1f}s\n")

    # Show results
    print("=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)

    if result.get('status') == 'success':
        coverage = result.get('coverage_metrics', {})
        print(f"Coverage: {coverage.get('coverage_percent', 0)}% ({coverage.get('extracted_fields', 0)}/{coverage.get('total_fields', 0)} fields)")
        print()

        # Show field counts per agent
        from .schema_comprehensive import COMPREHENSIVE_TYPES
        print("Results by Agent:")
        print("-" * 80)
        for agent_id in COMPREHENSIVE_TYPES.keys():
            agent_data = result.get(agent_id, {})
            field_count = sum(1 for k, v in agent_data.items() if k != 'evidence_pages' and v is not None)
            expected = len(get_comprehensive_types(agent_id)) - 1  # Exclude evidence_pages
            pct = (field_count / expected * 100) if expected > 0 else 0
            print(f"{agent_id:30} {field_count:2d}/{expected:2d} ({pct:5.1f}%)")

        # Save results
        output_file = f"experiments/comparison_results/ultra_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("experiments/comparison_results", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Results saved to: {output_file}")
    else:
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
