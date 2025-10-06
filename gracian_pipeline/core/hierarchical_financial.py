"""
Hierarchical Financial Extractor for Swedish BRF Documents

Specialized extractor for nested Swedish BRF financial tables.
Handles Note 4, 8, 9, 10 with full line-item preservation.

Solves: Current extraction only gets 4 summary totals instead of 50+ line items from Note 4.
"""

import os
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Docling imports
from docling.document_converter import DocumentConverter

# OpenAI for LLM extraction
from openai import OpenAI


class HierarchicalFinancialExtractor:
    """
    Specialized extractor for nested Swedish BRF financial tables.
    Handles Note 4, 8, 9, 10 with full line-item preservation.
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.note_patterns = {
            "note_4": {
                "name": "DRIFTKOSTNADER",
                "categories": [
                    "Fastighetskostnader",
                    "Reparationer",
                    "Periodiskt underhåll",
                    "Taxebundna kostnader",
                    "Övriga driftkostnader"
                ],
                "expected_items": 50,
                "page_hint": "typically pages 7-9",
                "extraction_type": "hierarchical"
            },
            "note_8": {
                "name": "BYGGNADER",
                "fields": [
                    "ackumulerade_anskaffningsvarden",
                    "arets_avskrivningar",
                    "planenligt_restvarde",
                    "taxeringsvarde_byggnad",
                    "taxeringsvarde_mark"
                ],
                "expected_items": 5,
                "page_hint": "typically pages 8-10",
                "extraction_type": "building_details"
            },
            "note_9": {
                "name": "ÖVRIGA FORDRINGAR",
                "fields": [
                    "skattekonto",
                    "momsavrakning",
                    "klientmedel",
                    "fordringar",
                    "avrakning_ovrigt"
                ],
                "expected_items": 5,
                "page_hint": "typically pages 10-12",
                "extraction_type": "receivables_breakdown"
            }
        }

    def extract_note_4_detailed(self, pdf_path: str, note_pages: List[int]) -> Dict[str, Any]:
        """
        Extract complete Note 4 with all 50+ line items.

        Uses 4-stage process:
        1. Extract markdown + tables for just note pages
        2. Build specialized prompt for hierarchical structure
        3. Extract with high token limit for full detail
        4. Validate structure and subtotals

        Args:
            pdf_path: Path to PDF document
            note_pages: List of page indices containing Note 4 (0-based)

        Returns:
            Dictionary with hierarchical breakdown and validation metadata
        """

        # Stage 1: Extract markdown for just note pages
        note_markdown, note_tables = self.extract_note_section(pdf_path, note_pages)

        # Stage 2: Use specialized prompt for hierarchical structure
        prompt = self.build_hierarchical_prompt(
            note_id="note_4",
            markdown=note_markdown,
            tables=note_tables,
            page_indices=note_pages
        )

        # Stage 3: Extract with high token limit for full detail
        result = self.call_gpt4o_extended(
            prompt=prompt,
            max_tokens=12000,  # Increased for 50+ items
            temperature=0
        )

        # Stage 4: Validate structure
        validated = self.validate_hierarchical_structure(
            result,
            expected_categories=self.note_patterns["note_4"]["categories"],
            expected_min_items=self.note_patterns["note_4"]["expected_items"]
        )

        return validated

    def extract_note_8_detailed(self, pdf_path: str, note_pages: List[int]) -> Dict[str, Any]:
        """
        Extract Note 8 (BYGGNADER - Building Details).

        Extracts building depreciation schedule with 5 key fields:
        - Accumulated acquisition values
        - Annual depreciation
        - Planned residual value
        - Tax assessment (building)
        - Tax assessment (land)

        Args:
            pdf_path: Path to PDF document
            note_pages: List of page indices containing Note 8 (0-based)

        Returns:
            Dictionary with building details and validation metadata
        """
        note_markdown, note_tables = self.extract_note_section(pdf_path, note_pages)

        pattern = self.note_patterns["note_8"]

        prompt = f"""
Extract COMPLETE building details from Note 8 ({pattern["name"]}).

CRITICAL FIELDS TO EXTRACT (all 5 required):
1. ackumulerade_anskaffningsvarden - Accumulated acquisition values (SEK)
2. arets_avskrivningar - Annual depreciation for current year (SEK)
3. planenligt_restvarde - Planned residual value (SEK)
4. taxeringsvarde_byggnad - Tax assessment value for building (SEK)
5. taxeringsvarde_mark - Tax assessment value for land (SEK)

OUTPUT SCHEMA:
{{
  "ackumulerade_anskaffningsvarden": number,
  "arets_avskrivningar": number,
  "planenligt_restvarde": number,
  "taxeringsvarde_byggnad": number,
  "taxeringsvarde_mark": number,
  "_source_note": "note_8",
  "_fields_found": list_of_field_names
}}

DOCUMENT TEXT (pages {note_pages}):
{note_markdown}

TABLES:
{self.format_tables_hierarchical(note_tables)}

INSTRUCTIONS:
- Extract ALL 5 fields if present
- Return numbers without spaces or formatting (e.g., 12500000 not "12 500 000")
- If a field is missing, set to null
- Swedish terms may vary (e.g., "Ackumulerade anskaffningsvärden", "Ingående anskaffningsvärde")
"""

        result = self.call_gpt4o_extended(prompt=prompt, max_tokens=4000, temperature=0)

        # Validate presence of required fields
        validation = {
            "fields_extracted": len([k for k, v in result.items() if not k.startswith("_") and v is not None]),
            "fields_expected": len(pattern["fields"]),
            "all_fields_present": True,
            "missing_fields": []
        }

        for field in pattern["fields"]:
            if field not in result or result[field] is None:
                validation["all_fields_present"] = False
                validation["missing_fields"].append(field)

        result["_validation"] = validation
        return result

    def extract_note_9_detailed(self, pdf_path: str, note_pages: List[int]) -> Dict[str, Any]:
        """
        Extract Note 9 (ÖVRIGA FORDRINGAR - Other Receivables).

        Extracts detailed receivables breakdown with 5 key fields:
        - Tax account balance
        - VAT settlement
        - Client funds
        - General receivables
        - Other settlements

        Args:
            pdf_path: Path to PDF document
            note_pages: List of page indices containing Note 9 (0-based)

        Returns:
            Dictionary with receivables details and validation metadata
        """
        note_markdown, note_tables = self.extract_note_section(pdf_path, note_pages)

        pattern = self.note_patterns["note_9"]

        prompt = f"""
Extract COMPLETE receivables breakdown from Note 9 ({pattern["name"]}).

CRITICAL FIELDS TO EXTRACT (all 5 required):
1. skattekonto - Tax account balance (SEK)
2. momsavrakning - VAT settlement amount (SEK)
3. klientmedel - Client funds held (SEK)
4. fordringar - General receivables (SEK)
5. avrakning_ovrigt - Other settlements/clearing amounts (SEK)

OUTPUT SCHEMA:
{{
  "skattekonto": number,
  "momsavrakning": number,
  "klientmedel": number,
  "fordringar": number,
  "avrakning_ovrigt": number,
  "_source_note": "note_9",
  "_fields_found": list_of_field_names
}}

DOCUMENT TEXT (pages {note_pages}):
{note_markdown}

TABLES:
{self.format_tables_hierarchical(note_tables)}

INSTRUCTIONS:
- Extract ALL 5 fields if present in the document
- Return numbers without spaces or formatting (e.g., 125000 not "125 000")
- If a field is missing, set to null
- Swedish terms may vary (e.g., "Momsavräkning", "Moms", "Skattekonto", "Kortfristiga fordringar")
- This section may be called "Övriga kortfristiga fordringar" or similar
"""

        result = self.call_gpt4o_extended(prompt=prompt, max_tokens=4000, temperature=0)

        # Validate presence of required fields
        validation = {
            "fields_extracted": len([k for k, v in result.items() if not k.startswith("_") and v is not None]),
            "fields_expected": len(pattern["fields"]),
            "all_fields_present": True,
            "missing_fields": []
        }

        for field in pattern["fields"]:
            if field not in result or result[field] is None:
                validation["all_fields_present"] = False
                validation["missing_fields"].append(field)

        result["_validation"] = validation
        return result

    def build_hierarchical_prompt(
        self,
        note_id: str,
        markdown: str,
        tables: List[Dict],
        page_indices: List[int]
    ) -> str:
        """
        Build specialized prompt for hierarchical table extraction.

        Args:
            note_id: ID of note to extract (e.g., "note_4")
            markdown: Docling markdown for note pages
            tables: List of docling table structures
            page_indices: Page numbers for context

        Returns:
            Extraction prompt with schema and rules
        """

        pattern = self.note_patterns[note_id]

        return f"""
Extract COMPLETE hierarchical breakdown from {pattern["name"]}.

CRITICAL STRUCTURE RULES:
1. This is a NESTED table with category headers and line items
2. Extract ALL categories: {", ".join(pattern["categories"])}
3. Under each category, extract EVERY line item (not just first few)
4. Each line item must have both years: 2021 and 2020
5. Each category must have a subtotal
6. Minimum expected items: {pattern["expected_items"]}

OUTPUT SCHEMA:
{{
  "category_name": {{
    "items": [
      {{"name": "Line item name", "2021": number, "2020": number}},
      // ... ALL items under this category
    ],
    "subtotal": {{"2021": number, "2020": number}}
  }},
  // ... repeat for ALL categories
}}

VALIDATION:
- Count items extracted: Must be ≥ {pattern["expected_items"]}
- All categories present: {len(pattern["categories"])}
- Subtotals mathematically correct

DOCUMENT TEXT (pages {page_indices}):
{markdown}

TABLES:
{self.format_tables_hierarchical(tables)}

REMEMBER: Extract EVERY line item, not summaries. This is for detailed financial analysis.
"""

    def validate_hierarchical_structure(
        self,
        extraction: Dict,
        expected_categories: List[str],
        expected_min_items: int
    ) -> Dict[str, Any]:
        """
        Validate extracted hierarchical structure.
        Returns extraction + validation metadata.

        Args:
            extraction: Extracted financial breakdown
            expected_categories: List of expected category names
            expected_min_items: Minimum total items expected

        Returns:
            Extraction with _validation metadata added
        """

        validation = {
            "categories_found": len(extraction),
            "categories_expected": len(expected_categories),
            "total_items_extracted": 0,
            "subtotals_validated": True,
            "warnings": []
        }

        # Check all categories present
        for expected_cat in expected_categories:
            if expected_cat not in extraction:
                validation["warnings"].append(f"Missing category: {expected_cat}")

        # Count total items and validate subtotals
        for category, data in extraction.items():
            if category.startswith("_"):  # Skip metadata fields
                continue

            items = data.get("items", [])
            subtotal = data.get("subtotal", {})

            validation["total_items_extracted"] += len(items)

            # Validate subtotal matches sum of items
            if items and subtotal:
                calculated_2021 = sum(item.get("2021", 0) for item in items)
                claimed_2021 = subtotal.get("2021", 0)

                if abs(calculated_2021 - claimed_2021) > 1:  # Allow rounding error
                    validation["subtotals_validated"] = False
                    validation["warnings"].append(
                        f"{category}: Subtotal mismatch (items sum: {calculated_2021}, "
                        f"claimed: {claimed_2021})"
                    )

        # Check minimum item count
        if validation["total_items_extracted"] < expected_min_items:
            validation["warnings"].append(
                f"Low item count: {validation['total_items_extracted']} < {expected_min_items} expected"
            )

        # Add validation metadata to extraction
        extraction["_validation"] = validation

        return extraction

    def extract_note_section(self, pdf_path: str, page_indices: List[int]) -> Tuple[str, List[Dict]]:
        """
        Extract markdown + tables for specific pages only.
        Increases context focus on target section.

        Args:
            pdf_path: Path to PDF document
            page_indices: 0-based page indices to extract

        Returns:
            Tuple of (filtered_markdown, filtered_tables)
        """
        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        # Get full markdown
        full_markdown = result.document.export_to_markdown()

        # Filter to just target pages (simplified - in production use more robust page filtering)
        # For now, we'll use the full markdown since docling doesn't provide easy page-level filtering
        filtered_markdown = full_markdown

        # Filter tables to just target pages
        filtered_tables = []
        for table in result.document.tables:
            # Docling tables have page numbers (convert to 0-based if needed)
            if hasattr(table, 'prov') and table.prov:
                for prov_item in table.prov:
                    if hasattr(prov_item, 'page_no') and (prov_item.page_no - 1) in page_indices:
                        filtered_tables.append({
                            "data": table.export_to_dataframe() if hasattr(table, 'export_to_dataframe') else {},
                            "page": prov_item.page_no - 1
                        })
                        break

        return filtered_markdown, filtered_tables

    def format_tables_hierarchical(self, tables: List[Dict]) -> str:
        """
        Format tables into readable text for LLM processing.

        Args:
            tables: List of table dictionaries from docling

        Returns:
            Formatted string representation of tables
        """
        if not tables:
            return "(No tables found in section)"

        formatted = []
        for i, table in enumerate(tables, 1):
            formatted.append(f"\n=== TABLE {i} (Page {table.get('page', '?')}) ===")

            # Extract table data
            data = table.get("data", {})
            if hasattr(data, 'to_markdown'):
                formatted.append(data.to_markdown())
            elif hasattr(data, 'to_string'):
                formatted.append(data.to_string())
            else:
                formatted.append(str(data))

        return "\n".join(formatted)

    def call_gpt4o_extended(self, prompt: str, max_tokens: int = 12000, temperature: float = 0) -> Dict[str, Any]:
        """
        Call GPT-4o with extended context for hierarchical extraction.

        Args:
            prompt: Extraction prompt
            max_tokens: Maximum tokens for response
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Parsed JSON response
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial data extraction specialist for Swedish BRF documents. Extract complete hierarchical table data with 100% accuracy. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"Error in GPT-4o extraction: {e}")
            return {}

    def extract_all_notes(self, pdf_path: str, notes: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract multiple financial notes from a document.

        Args:
            pdf_path: Path to PDF document
            notes: List of note IDs to extract (default: ["note_4"])

        Returns:
            Dictionary mapping note_id -> extracted data
        """
        if notes is None:
            notes = ["note_4"]

        results = {}

        for note_id in notes:
            if note_id not in self.note_patterns:
                print(f"Warning: Unknown note ID: {note_id}")
                continue

            print(f"Extracting {note_id}: {self.note_patterns[note_id]['name']}...")

            # Determine page ranges (heuristic - in production use sectionizer)
            if note_id == "note_4":
                page_range = [6, 7, 8]  # Typical Note 4 pages (0-based)
            elif note_id == "note_8":
                page_range = [7, 8, 9]  # Typical Note 8 pages
            elif note_id == "note_9":
                page_range = [9, 10, 11]  # Typical Note 9 pages
            else:
                page_range = [6, 7, 8, 9, 10, 11]  # Wide range as fallback

            try:
                # Call appropriate extraction method based on note type
                if note_id == "note_4":
                    extracted = self.extract_note_4_detailed(pdf_path, page_range)
                elif note_id == "note_8":
                    extracted = self.extract_note_8_detailed(pdf_path, page_range)
                elif note_id == "note_9":
                    extracted = self.extract_note_9_detailed(pdf_path, page_range)
                else:
                    # Fallback to Note 4 method for unknown notes
                    extracted = self.extract_note_4_detailed(pdf_path, page_range)

                results[note_id] = extracted
            except Exception as e:
                print(f"Error extracting {note_id}: {e}")
                results[note_id] = {"_error": str(e)}

        return results


# Test function
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Test on brf_198532.pdf
    test_pdf = "SRS/brf_198532.pdf"

    if not Path(test_pdf).exists():
        print(f"Test PDF not found: {test_pdf}")
        print("Please provide path to test PDF as argument")
        if len(sys.argv) > 1:
            test_pdf = sys.argv[1]
        else:
            sys.exit(1)

    print(f"Testing HierarchicalFinancialExtractor on {test_pdf}...")

    extractor = HierarchicalFinancialExtractor()

    # Extract Note 4
    print("\nExtracting Note 4 (DRIFTKOSTNADER)...")
    result = extractor.extract_note_4_detailed(test_pdf, note_pages=[7, 8, 9])

    # Print validation summary
    validation = result.get("_validation", {})
    print(f"\n✅ VALIDATION RESULTS:")
    print(f"   Categories found: {validation.get('categories_found', 0)} / {validation.get('categories_expected', 0)}")
    print(f"   Total items extracted: {validation.get('total_items_extracted', 0)}")
    print(f"   Subtotals validated: {validation.get('subtotals_validated', False)}")

    if validation.get("warnings"):
        print(f"\n⚠️  WARNINGS:")
        for warning in validation["warnings"]:
            print(f"   - {warning}")

    # Print sample of extracted data
    print(f"\n📊 SAMPLE EXTRACTED DATA:")
    for category, data in result.items():
        if category.startswith("_"):
            continue
        items = data.get("items", [])
        print(f"\n{category}: {len(items)} items")
        if items:
            print(f"   First item: {items[0]}")

    # Save full result
    output_file = "hierarchical_extraction_test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Full results saved to: {output_file}")

    # Success criteria check
    if validation.get("total_items_extracted", 0) >= 50:
        print(f"\n🎉 SUCCESS: Extracted {validation['total_items_extracted']} items (≥50 target)")
    else:
        print(f"\n❌ NEEDS IMPROVEMENT: Only {validation.get('total_items_extracted', 0)} items (target: 50+)")
