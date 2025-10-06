"""
Apartment Breakdown Extractor for Swedish BRF Documents

Intelligent apartment breakdown extraction with fallback levels.
Tries detailed table first, falls back to summary if not found.

Solves: Current extraction gets summary totals instead of detailed breakdown by room type.
"""

import os
import json
from typing import Dict, List, Optional, Any

# OpenAI for LLM extraction
from openai import OpenAI


class ApartmentBreakdownExtractor:
    """
    Intelligent apartment breakdown extraction with fallback levels.
    Tries detailed table first, falls back to summary if not found.
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_apartment_breakdown(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract apartment breakdown with progressive detail levels.

        Priority:
        1. Detailed table (1 rok, 2 rok, etc.) - BEST
        2. Summary counts (total lägenheter, lokaler) - ACCEPTABLE
        3. Null with warning - DOCUMENTED FAILURE

        Args:
            markdown: Docling markdown of document
            tables: List of docling table structures

        Returns:
            Dictionary with breakdown, granularity, and source metadata
        """

        # Try Level 1: Detailed table extraction
        detailed = self.try_extract_detailed_breakdown(markdown, tables)
        if detailed:
            return {
                "granularity": "detailed",
                "breakdown": detailed,
                "source": "table_extraction"
            }

        # Try Level 2: Summary extraction
        summary = self.try_extract_summary_breakdown(markdown)
        if summary:
            return {
                "granularity": "summary",
                "breakdown": summary,
                "source": "text_extraction",
                "_warning": "Detailed breakdown table not found, using summary counts"
            }

        # Level 3: Failed extraction
        return {
            "granularity": "none",
            "breakdown": None,
            "source": "failed",
            "_error": "No apartment count information found in document"
        }

    def try_extract_detailed_breakdown(self, markdown: str, tables: List[Dict]) -> Optional[Dict[str, int]]:
        """
        Attempt to extract detailed breakdown table.

        Table patterns to match:
        - Headers: "Lägenhetsstorlek", "Antal rum", "Typ", "Storlek"
        - Rows: "1 rok", "2 rok", "3 rok", "4 rok", "5 rok", "Lokaler"

        Args:
            markdown: Document markdown
            tables: List of table structures

        Returns:
            Dict mapping room types to counts, or None if not found
        """

        prompt = f"""
Search for a DETAILED apartment breakdown table in this document.

TARGET TABLE CHARACTERISTICS:
- Has rows for different apartment sizes: "1 rok", "2 rok", "3 rok", etc.
- Has a count/antal column
- May include "Lokaler" or "Kommersiella lokaler" row
- Common headers: "Lägenhetsstorlek", "Antal rum", "Typ", "Antal"

CRITICAL: Only extract if you find a DETAILED TABLE with multiple room types.
DO NOT extract if you only see summary text like "94 lägenheter".

OUTPUT FORMAT (only if detailed table found):
{{
  "1_rok": 10,
  "2_rok": 24,
  "3_rok": 30,
  "4_rok": 20,
  "5_rok": 10,
  "lokaler": 2
}}

If no detailed table found, return: {{"_not_found": true}}

DOCUMENT:
{markdown[:15000]}

TABLES:
{self.format_tables(tables)}
"""

        result = self.call_gpt4o(prompt)

        # Validate it's actually detailed (has multiple rok types)
        if result and not result.get("_not_found"):
            rok_keys = [k for k in result.keys() if "rok" in k]
            if len(rok_keys) >= 3:  # At least 3 room types
                return result

        return None

    def try_extract_summary_breakdown(self, markdown: str) -> Optional[Dict[str, int]]:
        """
        Fallback: Extract summary apartment counts from text.

        Common patterns:
        - "Föreningen består av 94 lägenheter och 2 lokaler"
        - "Totalt antal lägenheter: 94"
        - "Lägenheter: 94, Lokaler: 2"

        Args:
            markdown: Document markdown

        Returns:
            Dict with total counts, or None if not found
        """

        prompt = f"""
Extract summary apartment counts from text.

Look for phrases like:
- "X lägenheter" / "X apartments"
- "Y lokaler" / "Y commercial units"
- Total counts mentioned in text

OUTPUT:
{{
  "total_apartments": X,
  "commercial_units": Y
}}

If no counts found, return: {{"_not_found": true}}

DOCUMENT:
{markdown[:10000]}
"""

        result = self.call_gpt4o(prompt)

        if result and not result.get("_not_found"):
            return result

        return None

    def format_tables(self, tables: List[Dict]) -> str:
        """
        Format tables into readable text for LLM processing.

        Args:
            tables: List of table dictionaries from docling

        Returns:
            Formatted string representation of tables
        """
        if not tables:
            return "(No tables found)"

        formatted = []
        for i, table in enumerate(tables[:10], 1):  # Limit to first 10 tables
            formatted.append(f"\n=== TABLE {i} ===")

            # Extract table data
            data = table.get("data", {})
            if hasattr(data, 'to_markdown'):
                formatted.append(data.to_markdown())
            elif hasattr(data, 'to_string'):
                formatted.append(data.to_string())
            else:
                formatted.append(str(data)[:500])  # Truncate large tables

        return "\n".join(formatted)

    def call_gpt4o(self, prompt: str) -> Dict[str, Any]:
        """
        Call GPT-4o for apartment breakdown extraction.

        Args:
            prompt: Extraction prompt

        Returns:
            Parsed JSON response
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction specialist for Swedish BRF documents. Extract apartment breakdown data accurately. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"Error in GPT-4o extraction: {e}")
            return {"_not_found": True}


# Test function
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from docling.document_converter import DocumentConverter

    # Test on brf_198532.pdf
    test_pdf = "SRS/brf_198532.pdf"

    if not Path(test_pdf).exists():
        print(f"Test PDF not found: {test_pdf}")
        print("Please provide path to test PDF as argument")
        if len(sys.argv) > 1:
            test_pdf = sys.argv[1]
        else:
            sys.exit(1)

    print(f"Testing ApartmentBreakdownExtractor on {test_pdf}...")

    # Extract document with docling first
    print("\nExtracting document with docling...")
    converter = DocumentConverter()
    docling_result = converter.convert(test_pdf)
    markdown = docling_result.document.export_to_markdown()

    # Get tables
    tables = []
    for table in docling_result.document.tables:
        tables.append({
            "data": table.export_to_dataframe() if hasattr(table, 'export_to_dataframe') else {}
        })

    # Test apartment breakdown extraction
    print(f"\nTesting apartment breakdown extraction...")
    extractor = ApartmentBreakdownExtractor()
    result = extractor.extract_apartment_breakdown(markdown, tables)

    # Print results
    print(f"\n✅ EXTRACTION RESULTS:")
    print(f"   Granularity: {result['granularity']}")
    print(f"   Source: {result['source']}")

    if result.get('_warning'):
        print(f"\n⚠️  WARNING: {result['_warning']}")

    if result.get('_error'):
        print(f"\n❌ ERROR: {result['_error']}")

    if result.get('breakdown'):
        print(f"\n📊 BREAKDOWN:")
        for key, value in result['breakdown'].items():
            if not key.startswith('_'):
                print(f"   {key}: {value}")

    # Save result
    output_file = "apartment_breakdown_test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Full results saved to: {output_file}")

    # Success criteria
    if result['granularity'] == 'detailed':
        print(f"\n🎉 SUCCESS: Extracted detailed breakdown with {len([k for k in result['breakdown'].keys() if 'rok' in k])} room types")
    elif result['granularity'] == 'summary':
        print(f"\n✅ ACCEPTABLE: Extracted summary breakdown (detailed table not found in document)")
    else:
        print(f"\n❌ FAILED: No apartment breakdown information found")
