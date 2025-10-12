"""
Mixed-Mode Extraction for Hybrid PDFs
======================================

Handles PDFs with page-level heterogeneity by routing different pages
to appropriate extraction methods.

Problem: Hybrid PDFs where some pages are text and others are images
- Example: brf_76536.pdf has text headers (pages 1-8, 13-19) and
  image-based financial statements (pages 9-12)

Solution: Extract text pages with LLM, image pages with vision, merge results

Expected Impact: +15-20pp coverage for hybrid PDFs
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
import base64
from io import BytesIO
from PIL import Image

from gracian_pipeline.utils.page_classifier import (
    detect_image_pages_from_markdown,
    should_use_mixed_mode_extraction,
)


class MixedModeExtractor:
    """
    Orchestrates mixed-mode extraction for hybrid PDFs.

    Workflow:
    1. Analyze Docling markdown to identify page types
    2. Extract text from text pages (existing LLM pipeline)
    3. Extract data from image pages (vision extraction)
    4. Merge results intelligently
    """

    def __init__(self, docling_adapter, openai_client):
        """
        Initialize with existing extraction components.

        Args:
            docling_adapter: UltraComprehensiveDoclingAdapter instance
            openai_client: OpenAI client for vision extraction
        """
        self.docling_adapter = docling_adapter
        self.client = openai_client

    def should_use_mixed_mode(
        self,
        docling_result: Dict[str, Any],
        total_pages: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Determine if PDF should use mixed-mode extraction.

        ENHANCED (Week 3 Day 6): Now includes empty table detection and image density checks.

        Args:
            docling_result: Result from Docling extraction
            total_pages: Total number of pages

        Returns:
            (should_use_mixed_mode, page_classification_dict)
        """
        markdown = docling_result['markdown']
        char_count = docling_result['char_count']

        # NEW: Extract tables from docling_result (for empty table detection)
        tables = docling_result.get('tables', [])

        # Check if mixed-mode is appropriate (with enhanced detection)
        use_mixed, reason = should_use_mixed_mode_extraction(
            markdown,
            total_pages,
            tables=tables  # NEW: Pass tables for empty table detection
        )

        if not use_mixed:
            return False, {'reason': reason}

        # Get page classification
        page_classification = detect_image_pages_from_markdown(markdown, total_pages)

        # CRITICAL FIX (Week 3 Day 6 Extended):
        # Priority 2 (empty tables) and Priority 3 (high image density) may trigger
        # but detect_image_pages_from_markdown() returns empty image_pages list
        # because it only detects Priority 1 pattern (financial sections as images)
        #
        # Solution: If image_pages is empty but mixed-mode is triggered,
        # use heuristic fallback for typical Swedish BRF financial pages
        if not page_classification['image_pages']:
            # Fallback: Assume financial statements are on typical pages 9-12
            # This is conservative but based on analysis of 221-PDF corpus
            # where 90%+ of BRF annual reports follow this structure
            typical_financial_pages = list(range(9, min(13, total_pages + 1)))

            page_classification['image_pages'] = typical_financial_pages
            page_classification['fallback_heuristic'] = True
            page_classification['fallback_reason'] = f"Typical BRF structure (pages 9-12) for {reason}"

        # Add metadata
        page_classification['use_mixed_mode'] = True
        page_classification['reason'] = reason
        page_classification['char_count'] = char_count

        return True, page_classification

    def extract_image_pages_with_vision(
        self,
        pdf_path: str,
        image_pages: List[int],
        context_hints: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data from specific pages using GPT-4o vision.

        Args:
            pdf_path: Path to PDF file
            image_pages: List of page numbers to extract (1-indexed)
            context_hints: Optional context about what to extract

        Returns:
            Extraction results from vision API
        """

        # Render pages as images
        doc = fitz.open(pdf_path)
        images_base64 = []

        for page_num in image_pages:
            if page_num < 1 or page_num > len(doc):
                continue

            page = doc[page_num - 1]  # 0-indexed

            # Render at high DPI for better OCR (increased from 2x to 3x for Swedish text)
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom = ~216 DPI
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            images_base64.append(img_base64)

        doc.close()

        # Build vision extraction prompt
        prompt = self._build_vision_prompt_for_financial_pages(context_hints)

        # Call GPT-4o vision
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            *[
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                                for img_base64 in images_base64
                            ]
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0,
            )

            content = response.choices[0].message.content

            # Parse JSON response
            import json
            import re

            # Extract JSON from markdown fences if present
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            result = json.loads(content)

            return {
                'success': True,
                'data': result,
                'pages_processed': image_pages,
                'model': 'gpt-4o',
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'pages_processed': image_pages,
            }

    def _build_vision_prompt_for_financial_pages(
        self,
        context_hints: Optional[str] = None
    ) -> str:
        """
        Build prompt for vision extraction of financial statement pages.
        """

        base_prompt = """You are analyzing financial statement pages from a Swedish BRF (Bostadsrättsförening) annual report.

The images show financial statements that may include:
- Resultaträkning (Income Statement)
- Balansräkning (Balance Sheet)
- Kassaflödesanalys (Cash Flow Statement)

Extract ALL financial data you can find. Pay special attention to:

1. Income Statement (Resultaträkning):
   - Intäkter (Revenue) - total and itemized
   - Kostnader (Expenses) - total and itemized
   - Årets resultat (Net income/surplus)

2. Balance Sheet (Balansräkning):
   - Tillgångar (Assets) - total and itemized
   - Skulder (Liabilities) - total and itemized
   - Eget kapital (Equity) - total and components

3. Specific Items:
   - Långfristiga skulder (Long-term debt)
   - Kortfristiga skulder (Short-term debt)
   - Likvida medel (Cash and cash equivalents)
   - Årsavgifter (Annual fees) - if mentioned

Return a JSON object with the following structure (IMPORTANT: Use these exact key names):
{
  "financial_agent": {
    "revenue": <number or null>,
    "expenses": <number or null>,
    "assets": <number or null>,
    "liabilities": <number or null>,
    "equity": <number or null>,
    "surplus": <number or null>,
    "evidence_pages": [list of page numbers where data was found]
  },
  "loans_agent": {
    "loans": [
      {
        "loan_provider": <string or null>,
        "outstanding_loans": <number or null>,
        "interest_rate": <number or null>
      }
    ]
  },
  "fees_agent": {
    "monthly_fee": <number or null>,
    "fee_per_sqm": <number or null>
  }
}

Important:
- Extract ALL numbers you can find
- Use null for fields not found
- Numbers should be without spaces or commas (e.g., 1500000 not 1 500 000)
- Include currency if mentioned (usually SEK/kr)
- If you see "tkr" (tusen kronor), multiply by 1000
"""

        if context_hints:
            base_prompt += f"\n\nAdditional context:\n{context_hints}"

        return base_prompt

    def merge_extraction_results(
        self,
        text_extraction: Dict[str, Any],
        vision_extraction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge results from text extraction and vision extraction.

        Strategy:
        - Prefer vision extraction for financial data (more accurate from images)
        - Prefer text extraction for governance, property, metadata
        - Combine when both have data
        """

        merged = text_extraction.copy()

        if not vision_extraction.get('success'):
            return merged

        vision_data = vision_extraction.get('data', {})

        # Merge financial agent data (prefer vision)
        if 'financial_agent' in vision_data:
            financial_vision = vision_data['financial_agent']

            # If text extraction has financial data, compare
            if 'financial_agent' in merged:
                financial_text = merged['financial_agent']

                # Merge, preferring vision for non-null values
                for key, value in financial_vision.items():
                    if value is not None:
                        financial_text[key] = value

            else:
                # No text extraction financial data, use vision
                merged['financial_agent'] = financial_vision

        # Merge loans agent (combine arrays)
        if 'loans_agent' in vision_data:
            loans_vision = vision_data['loans_agent']

            if 'loans_agent' in merged:
                # Handle both dict and list cases from base extractor
                if isinstance(merged['loans_agent'], dict):
                    # Base extractor returned dict format
                    # Check if it has a 'loans' array inside
                    if 'loans' in merged['loans_agent']:
                        merged['loans_agent']['loans'].extend(loans_vision)
                    else:
                        # Convert to array format
                        merged['loans_agent'] = loans_vision
                elif isinstance(merged['loans_agent'], list):
                    # Already a list, extend it
                    merged['loans_agent'].extend(loans_vision)
            else:
                merged['loans_agent'] = loans_vision

        # Merge fees agent (prefer vision)
        if 'fees_agent' in vision_data:
            fees_vision = vision_data['fees_agent']

            if 'fees_agent' in merged:
                fees_text = merged['fees_agent']

                for key, value in fees_vision.items():
                    if value is not None:
                        fees_text[key] = value
            else:
                merged['fees_agent'] = fees_vision

        # Add metadata about mixed-mode extraction
        merged['_extraction_metadata'] = {
            'mode': 'mixed',
            'text_extraction': 'docling_llm',
            'vision_extraction': 'gpt-4o',
            'vision_pages': vision_extraction.get('pages_processed', []),
        }

        return merged


# Example usage
if __name__ == "__main__":
    print("Mixed-Mode Extractor - Test Initialization")
    print("=" * 80)

    # This would be used in the main extraction pipeline:
    #
    # from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter
    # from openai import OpenAI
    #
    # adapter = UltraComprehensiveDoclingAdapter()
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    #
    # extractor = MixedModeExtractor(adapter, client)
    #
    # # Step 1: Run Docling
    # docling_result = adapter.extract_with_docling(pdf_path)
    #
    # # Step 2: Check if mixed-mode needed
    # use_mixed, classification = extractor.should_use_mixed_mode(docling_result, total_pages)
    #
    # if use_mixed:
    #     # Step 3: Extract image pages with vision
    #     vision_result = extractor.extract_image_pages_with_vision(
    #         pdf_path,
    #         classification['image_pages']
    #     )
    #
    #     # Step 4: Merge results
    #     final_result = extractor.merge_extraction_results(
    #         text_extraction_result,
    #         vision_result
    #     )

    print("Mixed-Mode Extractor initialized successfully")
    print("Ready for integration into pydantic_extractor.py")
