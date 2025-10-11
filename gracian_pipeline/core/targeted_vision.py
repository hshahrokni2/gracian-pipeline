"""
Targeted Vision Extraction System
Extracts specific missing fields using vision LLM with field-specific prompts.

Designed for recovery after validation failures - targets specific fields that
failed extraction or validation in the base pipeline.
"""

import os
import json
import base64
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from openai import OpenAI


class TargetedVisionExtractor:
    """
    Extract missing/failed fields with vision LLM.

    Uses field-specific heuristics for page selection and custom prompts
    optimized for each field type.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Field-to-page heuristics (Swedish BRF structure)
        self.FIELD_HEURISTICS = {
            # Property fields (usually in first 3-5 pages)
            "property_designation": [1, 2, 3],
            "built_year": [2, 3, 4, 5],
            "total_area_sqm": [2, 3, 4, 5],
            "property_address": [1, 2, 3],
            "plot_area_sqm": [3, 4, 5],

            # Fee fields (usually pages 3-6)
            "fee_1_rok": [3, 4, 5, 6],
            "fee_2_rok": [3, 4, 5, 6],
            "fee_3_rok": [3, 4, 5, 6],
            "fee_4_rok": [3, 4, 5, 6],
            "fee_5_rok": [3, 4, 5, 6],
            "monthly_fee_per_sqm": [3, 4, 5, 6],
            "annual_fee_total": [3, 4, 5, 6],

            # Loan fields (Note 5, usually pages 8-15)
            "loans": [8, 9, 10, 11, 12, 13, 14, 15],

            # Governance fields (pages 2-4)
            "chairman": [2, 3, 4],
            "board_members": [2, 3, 4],
            "auditor_name": [2, 3, 4],
            "audit_firm": [2, 3, 4],

            # Building details (Note 8, usually pages 10-14)
            "building_details": [10, 11, 12, 13, 14],

            # Apartment breakdown (usually pages 4-8)
            "apartment_breakdown": [4, 5, 6, 7, 8],
        }

        # Field-specific prompts
        self.FIELD_PROMPTS = {
            "loans": """Extract ALL loans from Note 5 (Noter - Långfristiga skulder) in this Swedish BRF annual report.

For EACH loan, extract:
- Lender name (bank name, e.g., "SEB", "Swedbank", "Handelsbanken")
- Outstanding balance in SEK (amount remaining on loan)
- Interest rate (as percentage)
- Loan amount (original loan amount)
- Maturity date or year

Return JSON array:
{
  "loans": [
    {
      "lender": "SEB",
      "outstanding_balance": 30000000,
      "interest_rate": 2.5,
      "amount_2021": 30000000,
      "maturity_date": "2025-12-31"
    }
  ]
}

CRITICAL: Extract ALL loans shown in the table. If balance is shown, it CANNOT be zero for an active loan.""",

            "property_designation": """Extract the property designation (fastighetsbeteckning) from this Swedish BRF document.

Look for patterns like:
- "Gustavsberg 2:123"
- "Stockholm Södermalm 1:45"
- Format: [Municipality] [District] [Number]:[Number]

Return JSON:
{
  "property_designation": "exact designation as shown"
}""",

            "apartment_breakdown": """Extract the apartment distribution (lägenhetsfördel

ning) from this Swedish BRF document.

Look for a table showing apartment counts by room size (e.g., "1 rok", "2 rok", "3 rok").

Return JSON:
{
  "apartment_breakdown": {
    "1_rok": 10,
    "2_rok": 25,
    "3_rok": 15,
    "4_rok": 5,
    "5_rok": 2
  }
}""",

            "fee_structure": """Extract the monthly fees (årsavgifter/månadsavgifter) by apartment size from this Swedish BRF document.

Look for fee table showing costs per apartment type.

Return JSON:
{
  "fee_1_rok": 2500,
  "fee_2_rok": 3800,
  "fee_3_rok": 5200,
  "fee_4_rok": 6500,
  "fee_5_rok": 7800
}""",

            "building_details": """Extract building details from Note 8 (Byggnader) in this Swedish BRF annual report.

Extract:
- Purchase value (Anskaffningsvärde)
- Accumulated depreciation (Ackumulerade avskrivningar)
- Book value (Bokfört värde)
- Depreciation percentage (Avskrivningsprocent)
- Useful life (Nyttjandeperiod)

Return JSON:
{
  "purchase_value": 150000000,
  "accumulated_depreciation": -25000000,
  "book_value": 125000000,
  "depreciation_percent": 2.0,
  "useful_life_years": 50
}"""
        }

    def extract_missing_fields(
        self,
        pdf_path: str,
        base_result: Dict[str, Any],
        failed_fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract missing/failed fields using targeted vision extraction.

        Args:
            pdf_path: Path to PDF
            base_result: Base extraction result
            failed_fields: List of validation issues (from ValidationEngine)

        Returns:
            Updated extraction result with recovered fields
        """
        print(f"\n🎯 Targeted Vision Extraction")
        print(f"   Failed fields: {len(failed_fields)}")

        # Group failed fields by category for batch extraction
        field_groups = self._group_failed_fields(failed_fields)

        for group_name, fields in field_groups.items():
            print(f"\n   → Extracting {group_name} ({len(fields)} fields)...")

            # Get optimal pages for this group
            pages = self._get_group_pages(group_name, pdf_path)

            # Render pages to images
            images = self._render_pages(pdf_path, pages, dpi=200)

            # Get field-specific prompt
            prompt = self._get_field_prompt(group_name)

            # Extract with vision LLM
            extraction_result = self._call_vision_llm(prompt, images, pages)

            if extraction_result:
                # Update base result with extracted data
                base_result = self._update_result(
                    base_result,
                    group_name,
                    extraction_result,
                    evidence_pages=pages
                )
                print(f"      ✓ Extracted {group_name}")
            else:
                print(f"      ✗ Failed to extract {group_name}")

        return base_result

    def _group_failed_fields(self, failed_fields: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Group failed fields by extraction category."""
        groups = {}

        for issue in failed_fields:
            field = issue.get("field", "")

            # Determine group based on field name
            if "loans" in field:
                group = "loans"
            elif "property_designation" in field:
                group = "property_designation"
            elif "apartment" in field:
                group = "apartment_breakdown"
            elif "fee" in field or "avgift" in field:
                group = "fee_structure"
            elif "building" in field or "byggnader" in field:
                group = "building_details"
            else:
                group = "other"

            if group not in groups:
                groups[group] = []
            groups[group].append(field)

        return groups

    def _get_group_pages(self, group_name: str, pdf_path: str) -> List[int]:
        """Get optimal pages for field group."""
        # Use heuristics or default to middle pages
        pages = self.FIELD_HEURISTICS.get(group_name, [5, 6, 7, 8, 9, 10])

        # Ensure pages are within document bounds
        doc = fitz.open(pdf_path)
        max_page = doc.page_count - 1
        doc.close()

        valid_pages = [p for p in pages if 0 <= p <= max_page]

        # Limit to 8 pages max to prevent token overflow
        return valid_pages[:8]

    def _render_pages(self, pdf_path: str, page_indices: List[int], dpi: int = 200) -> List[bytes]:
        """Render PDF pages to PNG images."""
        doc = fitz.open(pdf_path)
        images = []

        for page_idx in page_indices:
            page = doc.load_page(page_idx)

            # Render at high DPI for Swedish text clarity
            pix = page.get_pixmap(dpi=dpi)

            # Convert to PNG bytes
            img_bytes = pix.pil_tobytes(format="PNG")
            images.append(img_bytes)

        doc.close()
        return images

    def _get_field_prompt(self, group_name: str) -> str:
        """Get field-specific extraction prompt."""
        return self.FIELD_PROMPTS.get(group_name, f"Extract {group_name} from this Swedish BRF document.")

    def _call_vision_llm(
        self,
        prompt: str,
        images: List[bytes],
        page_labels: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Call vision LLM with images and prompt.

        Args:
            prompt: Field-specific extraction prompt
            images: List of PNG image bytes
            page_labels: Page numbers for evidence tracking

        Returns:
            Extracted data as dict, or None if extraction failed
        """
        # Build messages with interleaved images and page labels
        messages_content = [{"type": "text", "text": prompt}]

        for idx, img_bytes in enumerate(images):
            # Add page label
            page_num = page_labels[idx] + 1  # 1-indexed for display
            messages_content.append({
                "type": "text",
                "text": f"\n--- Page {page_num} ---"
            })

            # Add image
            b64_img = base64.b64encode(img_bytes).decode('utf-8')
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_img}"}
            })

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": messages_content}],
                max_tokens=2000,
                temperature=0
            )

            content = response.choices[0].message.content

            # Parse JSON from response
            result = self._parse_json(content)
            return result

        except Exception as e:
            print(f"      Error calling vision LLM: {e}")
            return None

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling code fences."""
        # Remove markdown code fences
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"      JSON parse error: {e}")
            return None

    def _update_result(
        self,
        base_result: Dict[str, Any],
        group_name: str,
        extraction_result: Dict[str, Any],
        evidence_pages: List[int]
    ) -> Dict[str, Any]:
        """Update base result with targeted extraction data."""

        # Map group to agent
        agent_map = {
            "loans": "financial_agent",
            "property_designation": "property_agent",
            "apartment_breakdown": "property_agent",
            "fee_structure": "fees_agent",
            "building_details": "financial_agent",
        }

        agent_key = agent_map.get(group_name, "other_agent")

        # Ensure agent exists in result
        if agent_key not in base_result:
            base_result[agent_key] = {}

        # Update fields from extraction
        for field, value in extraction_result.items():
            base_result[agent_key][field] = value

            # Add evidence pages metadata
            if f"{field}_evidence_pages" not in base_result[agent_key]:
                base_result[agent_key][f"{field}_evidence_pages"] = evidence_pages

        # Mark as vision-extracted
        base_result[agent_key][f"_{group_name}_vision_extracted"] = True

        return base_result


# Test function
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Test on a PDF with known failures
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "Hjorthagen/brf_198532.pdf"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    # Simulate failed fields from validation
    failed_fields = [
        {"field": "loans[0].outstanding_balance", "value": 0},
        {"field": "loans[1].outstanding_balance", "value": 0},
        {"field": "loans[2].outstanding_balance", "value": 0},
        {"field": "property_designation", "value": None},
    ]

    extractor = TargetedVisionExtractor()

    # Mock base result
    base_result = {
        "financial_agent": {},
        "property_agent": {}
    }

    # Extract missing fields
    updated_result = extractor.extract_missing_fields(pdf_path, base_result, failed_fields)

    # Print results
    print(f"\n{'='*60}")
    print(f"TARGETED EXTRACTION RESULTS")
    print(f"{'='*60}\n")
    print(json.dumps(updated_result, indent=2, ensure_ascii=False))
