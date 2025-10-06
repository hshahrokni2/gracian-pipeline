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

    def extract_apartment_breakdown(self, markdown: str, tables: List[Dict], pdf_path: str = None) -> Dict[str, Any]:
        """
        Extract apartment breakdown with progressive detail levels.

        Priority:
        1. Detailed table (1 rok, 2 rok, etc.) - BEST
        2. Vision-based chart extraction - VERY GOOD
        3. Summary counts (total lägenheter, lokaler) - ACCEPTABLE
        4. Null with warning - DOCUMENTED FAILURE

        Args:
            markdown: Docling markdown of document
            tables: List of docling table structures
            pdf_path: Path to PDF (required for vision extraction)

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

        # Try Level 2: Vision-based chart extraction
        if pdf_path and "<!-- image -->" in markdown and "Lägenhetsfördelning" in markdown:
            print("  → Detected chart placeholder, attempting vision extraction...")
            vision_result = self.try_extract_chart_with_vision(pdf_path, markdown)
            if vision_result:
                print(f"    ✓ Vision extraction successful: {len(vision_result)} fields")
                return {
                    "granularity": "detailed",
                    "breakdown": vision_result,
                    "source": "vision_chart_extraction"
                }
            else:
                print("    ⚠ Vision extraction returned no results")

        # Try Level 3: Summary extraction
        summary = self.try_extract_summary_breakdown(markdown)
        if summary:
            return {
                "granularity": "summary",
                "breakdown": summary,
                "source": "text_extraction",
                "_warning": "Detailed breakdown table not found, using summary counts"
            }

        # Level 4: Failed extraction
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

    def try_extract_chart_with_vision(self, pdf_path: str, markdown: str) -> Optional[Dict[str, int]]:
        """
        Extract apartment breakdown from bar chart/image using GPT-4o Vision.

        Args:
            pdf_path: Path to PDF file
            markdown: Document markdown (used to find page with chart)

        Returns:
            Dict mapping room types to counts, or None if extraction fails
        """
        try:
            import fitz  # PyMuPDF
            import base64
            from io import BytesIO
            from PIL import Image

            # Find the page containing "Lägenhetsfördelning" by searching the PDF
            doc = fitz.open(pdf_path)
            target_page = None

            # Look specifically for "Lägenhetsfördelning" (the section header)
            for page_num in range(min(10, len(doc))):  # Check first 10 pages
                page = doc[page_num]
                text = page.get_text()
                # Be specific - look for the section header, not just mentions of apartments
                if "Lägenhetsfördelning" in text:
                    target_page = page_num
                    print(f"    → Found 'Lägenhetsfördelning' on page {page_num + 1}")
                    break

            if target_page is None:
                # Fallback: search markdown for page hint
                print("    → 'Lägenhetsfördelning' not found in PDF text, defaulting to page 2")
                target_page = 1  # Default to page 2 (index 1)

            # Render the page to image (high DPI for chart readability)
            page = doc[target_page]
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")

            # Convert to base64
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            doc.close()

            # Call GPT-4o Vision
            vision_prompt = """
Extract apartment distribution data from this Swedish BRF document page.

Look for a bar chart or table showing "Lägenhetsfördelning" (apartment distribution by room count).

EXPECTED DATA FORMAT:
- 1 rok (1 room): [count]
- 2 rok (2 rooms): [count]
- 3 rok (3 rooms): [count]
- 4 rok (4 rooms): [count]
- 5 rok (5 rooms): [count]
- >5 rok (more than 5 rooms): [count]

Return ONLY valid JSON in this exact format:
{
  "1_rok": <number>,
  "2_rok": <number>,
  "3_rok": <number>,
  "4_rok": <number>,
  "5_rok": <number>,
  ">5_rok": <number>
}

If you cannot find apartment distribution data, return: {"_not_found": true}
"""

            print(f"    → Calling GPT-4o Vision on page {target_page + 1}...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            print(f"    → GPT-4o returned: {result}")

            # Validate result
            if result and not result.get("_not_found"):
                rok_keys = [k for k in result.keys() if "rok" in k]
                if len(rok_keys) >= 3:  # At least 3 room types
                    print(f"    ✓ Valid detailed breakdown with {len(rok_keys)} room types")
                    return result
                else:
                    print(f"    ⚠ Only found {len(rok_keys)} room types, need at least 3")

        except Exception as e:
            print(f"    ✗ Vision extraction error: {e}")
            import traceback
            traceback.print_exc()

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

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

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
    result = extractor.extract_apartment_breakdown(markdown, tables, pdf_path=test_pdf)

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
