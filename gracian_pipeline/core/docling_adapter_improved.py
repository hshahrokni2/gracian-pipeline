#!/usr/bin/env python3
"""
Improved Docling Adapter with Fixed Financial Table Parsing

Key improvements:
1. Better table extraction from docling's data structure
2. Swedish number parsing (handles "301 339 818" format)
3. Combined extraction (single GPT-4o call instead of 3)
4. Improved error handling and logging
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from docling.document_converter import DocumentConverter


class ImprovedDoclingAdapter:
    """Enhanced adapter with optimized table parsing."""

    def __init__(self):
        self.converter = DocumentConverter()

    def is_machine_readable(self, markdown: str, char_threshold: int = 5000) -> bool:
        """Determine if PDF is machine-readable based on extracted text."""
        text_only = re.sub(r'<!--\s*image\s*-->', '', markdown).strip()
        return len(text_only) > char_threshold

    def extract_with_docling(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF using Docling."""
        result = self.converter.convert(pdf_path)
        doc = result.document

        markdown = doc.export_to_markdown()
        json_export = doc.export_to_dict()

        # Determine if text or scanned
        is_text = self.is_machine_readable(markdown)

        return {
            'status': 'text' if is_text else 'scanned',
            'markdown': markdown,
            'tables': json_export.get('tables', []),
            'char_count': len(markdown),
            'json_export': json_export,
            'pdf_path': pdf_path
        }

    def extract_table_text(self, table: Dict[str, Any]) -> str:
        """
        Extract readable text from a docling table structure.

        Docling tables have structure:
        {
            'data': {
                'table_cells': [
                    {'text': 'cell_value', 'start_row_offset_idx': 0, 'start_col_offset_idx': 0, ...},
                    ...
                ]
            },
            'captions': [...],
            ...
        }
        """
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

        # Add caption if available
        table_text = '\n'.join(lines)
        if 'captions' in table and table['captions']:
            caption = ' '.join(cap.get('text', '') for cap in table['captions'])
            table_text = f"[{caption}]\n{table_text}"

        return table_text

    def format_tables_for_llm(self, tables: List[Dict], limit: int = 15) -> str:
        """Format tables into readable text for LLM processing."""
        tables_text = ""

        for i, table in enumerate(tables[:limit], 1):
            table_text = self.extract_table_text(table)
            if table_text:
                tables_text += f"\n\n=== TABLE {i} ===\n{table_text}\n"

        return tables_text

    def extract_all_brf_fields_combined(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract ALL BRF fields in a single GPT-4o call for better speed and context.

        This replaces the 3 separate calls (governance, financial, property) with one optimized call.
        """
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Format tables
        tables_text = self.format_tables_for_llm(tables)

        prompt = f"""Extract ALL data from this Swedish BRF annual report in ONE response.

DOCUMENT TEXT (first 12,000 chars):
{markdown[:12000]}

FINANCIAL TABLES:
{tables_text}

Extract and return ONLY valid JSON with ALL fields below:

{{
  "governance_agent": {{
    "chairman": "Name of board chairman (ordförande)",
    "board_members": ["List", "of", "all", "board", "members", "including", "suppleanter"],
    "auditor_name": "Primary auditor name",
    "audit_firm": "Auditing firm name",
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
    "address": "Full property address",
    "construction_year": 2015,
    "num_apartments": 94,
    "area_sqm": 8009,
    "evidence_pages": [1, 2]
  }}
}}

CRITICAL RULES:
1. Swedish names: Extract EXACTLY as written (don't translate)
2. Board members: Include ALL ledamöter AND suppleanter
3. Numbers: Extract as INTEGER (no spaces, no formatting)
   - "301 339 818" → 301339818
   - "8 009 m²" → 8009
4. Financial terms:
   - Revenue = Intäkter
   - Expenses = Kostnader
   - Assets = Tillgångar
   - Liabilities = Skulder
   - Equity = Eget kapital
   - Surplus = Årets resultat / Överskott
5. Use null for missing values (not 0)
6. Return ONLY the JSON object, nothing else"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF document parser. Return ONLY valid JSON with numeric values as integers."},
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

            # Ensure numeric types for financial fields
            if 'financial_agent' in result:
                for key in ['revenue', 'expenses', 'assets', 'liabilities', 'equity', 'surplus']:
                    if key in result['financial_agent'] and result['financial_agent'][key] is not None:
                        try:
                            # Convert string numbers with spaces to integers
                            val = str(result['financial_agent'][key])
                            val = val.replace(' ', '').replace(',', '')
                            result['financial_agent'][key] = int(float(val))
                        except (ValueError, TypeError):
                            result['financial_agent'][key] = None

            # Ensure numeric types for property fields
            if 'property_agent' in result:
                for key in ['construction_year', 'num_apartments', 'area_sqm']:
                    if key in result['property_agent'] and result['property_agent'][key] is not None:
                        try:
                            val = str(result['property_agent'][key])
                            val = val.replace(' ', '').replace(',', '')
                            result['property_agent'][key] = int(float(val))
                        except (ValueError, TypeError):
                            result['property_agent'][key] = None

            return result

        except Exception as e:
            print(f"Warning: Combined extraction error: {e}")
            return {
                "governance_agent": {
                    "chairman": None,
                    "board_members": [],
                    "auditor_name": None,
                    "audit_firm": None,
                    "nomination_committee": [],
                    "evidence_pages": []
                },
                "financial_agent": {
                    "revenue": None,
                    "expenses": None,
                    "assets": None,
                    "liabilities": None,
                    "equity": None,
                    "surplus": None,
                    "evidence_pages": []
                },
                "property_agent": {
                    "address": None,
                    "construction_year": None,
                    "num_apartments": None,
                    "area_sqm": None,
                    "evidence_pages": []
                }
            }

    def extract_brf_data(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main extraction method using Docling with improved table parsing.

        Now uses single combined extraction for better performance.
        """
        print(f"\n🔍 Improved Docling extraction: {Path(pdf_path).name}")

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

        # Extract all fields in single call
        markdown = docling_result['markdown']
        tables = docling_result['tables']

        print("  🤖 Extracting ALL fields (governance + financial + property)...")
        all_fields = self.extract_all_brf_fields_combined(markdown, tables)

        result = {
            'status': 'success',
            'method': 'docling_improved',
            'governance_agent': all_fields.get('governance_agent', {}),
            'financial_agent': all_fields.get('financial_agent', {}),
            'property_agent': all_fields.get('property_agent', {}),
            'notes_agent': {},
            'docling_metadata': {
                'char_count': docling_result['char_count'],
                'table_count': len(tables),
                'processing_method': 'docling_combined_extraction'
            }
        }

        # Print summary
        gov = result['governance_agent']
        fin = result['financial_agent']
        prop = result['property_agent']

        print(f"  📊 Results:")
        print(f"     Chairman: {gov.get('chairman', 'N/A')}")
        print(f"     Board: {len(gov.get('board_members', []))} members")
        print(f"     Assets: {fin.get('assets', 'N/A')}")
        print(f"     Revenue: {fin.get('revenue', 'N/A')}")
        print(f"     Apartments: {prop.get('num_apartments', 'N/A')}")

        return result
