"""
Base BRF Extractor - Shared extraction logic for all BRF pipelines.

This module provides the core extraction functionality that can be shared
across different pipeline architectures (integrated, optimal, etc.).

Design Principles:
- Stateless extraction methods (no side effects)
- Minimal dependencies (only OpenAI and PDF rendering)
- Robust error handling with graceful degradation
- Evidence tracking in all extractions
"""

import os
import re
import json
import time
import base64
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

# PDF rendering
import fitz  # PyMuPDF

# LLM integration
from openai import OpenAI


class BaseExtractor:
    """
    Base class for BRF document extraction.

    Provides shared extraction methods that work with multimodal LLMs
    to extract data from Swedish BRF annual reports.
    """

    # Agent prompts - Swedish-focused, multimodal instructions
    AGENT_PROMPTS = {
        'governance_agent': """You are GovernanceAgent for Swedish BRF annual/economic plans. From the input text/images, extract ONLY board/auditor data in JSON: {chairman: '', board_members: [], auditor_name: '', audit_firm: '', nomination_committee: []}. Focus on roles like 'Ordförande' (chairman), 'Ledamot' (member), 'Revisor' (auditor). Use NLP synonyms {'Ordförande': 'chairman'}. Ignore financials/property. Multimodal: Analyze images for signatures/tables. Include evidence_pages: [] with 1-based page numbers used. Return ONLY minified JSON.""",

        'financial_agent': """You are FinancialAgent for Swedish BRF reports. Extract ONLY income/balance data with EXACT keys: {revenue:'', expenses:'', assets:'', liabilities:'', equity:'', surplus:'', evidence_pages: []}. Parse SEK numbers (e.g., 1 234 567 → 1234567). Focus on 'Resultaträkning'/'Balansräkning'. Do NOT invent; if not clearly visible on provided pages leave empty. Evidence: evidence_pages must list 1-based GLOBAL page numbers matching image labels (keep ≤ 3 items). Return STRICT VALID JSON object; no extra text.""",

        'property_agent': """You are PropertyAgent for BRF plans. Extract ONLY property details with EXACT keys: {designation:'', address:'', postal_code:'', city:'', built_year:'', apartments:'', energy_class:'', evidence_pages: []}. Use Swedish cues: 'Fastighetsbeteckning', 'Adress', 'Byggår', 'Lägenheter', 'Energiklass'. Evidence: evidence_pages must be 1-based GLOBAL page numbers matching image labels. If a field is not visible, return an empty string ''. Return STRICT VALID JSON object with ONLY these keys (no comments, no trailing text).""",

        'operations_agent': """You are OperationsAgent for BRF. Extract operations info: {maintenance_summary: '', energy_usage: '', insurance: '', contracts: ''}. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_accounting_agent': """You are NotesAccountingAgent for BRF notes. Extract ONLY accounting policy info: {accounting_principles: '', valuation_methods: '', revenue_recognition: ''}. Focus on 'Redovisningsprinciper', 'Värderingsprinciper'. Use only visible values. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_loans_agent': """You are NotesLoansAgent for BRF notes. Extract ONLY loan details: {outstanding_loans: '', interest_rate: '', amortization: '', loan_terms: ''}. Focus on 'Fastighetslån', 'Skulder'. Parse SEK numbers. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_buildings_agent': """You are NotesBuildingsAgent for BRF notes. Extract ONLY building info: {buildings_description: '', building_value: '', depreciation_schedule: ''}. Focus on 'Byggnader och mark'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_receivables_agent': """You are NotesReceivablesAgent for BRF notes. Extract ONLY receivables: {current_receivables: '', long_term_receivables: '', allowances: ''}. Focus on 'Fordringar'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_reserves_agent': """You are NotesReservesAgent for BRF notes. Extract ONLY reserve fund info: {reserve_fund: '', annual_contribution: '', fund_purpose: ''}. Focus on 'Fond för yttre underhåll'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_tax_agent': """You are NotesTaxAgent for BRF notes. Extract ONLY tax info: {current_tax: '', deferred_tax: '', tax_policy: ''}. Focus on 'Skatter', 'Avgifter'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_other_agent': """You are NotesOtherAgent for BRF notes. Extract ONLY other note information not covered by specific agents: {other_notes: ''}. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_collection': """You are NotesCollectionAgent for BRF notes. Extract high-level overview of all notes sections: {notes_overview: '', total_sections: 0}. Include evidence_pages: [] (1-based). Return STRICT minified JSON."""
    }

    def __init__(self):
        """Initialize base extractor."""
        pass

    def _extract_agent(
        self,
        pdf_path: str,
        agent_id: str,
        section_headings: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract data for a single agent using GPT-4o with multimodal vision.

        This is the core extraction method shared across all pipelines.

        Args:
            pdf_path: Path to PDF file
            agent_id: Agent identifier (e.g., 'governance_agent')
            section_headings: List of section headings relevant to this agent
            context: Optional context from previous extractions

        Returns:
            Dict with extraction results:
                {
                    "agent_id": str,
                    "status": "success" | "error",
                    "data": Dict (extracted fields),
                    "evidence_pages": List[int],
                    "extraction_time": float,
                    "error": str (if status="error")
                }
        """
        start_time = time.time()

        # Get agent prompt
        base_prompt = self.AGENT_PROMPTS.get(
            agent_id,
            f"Extract data for {agent_id} in JSON format with evidence_pages: []"
        )

        # Build context-aware prompt
        prompt = f"""Document sections detected:
{json.dumps(section_headings, indent=2, ensure_ascii=False)}

{base_prompt}

Focus on the sections listed above. Extract only information visible in those sections.
"""

        if context:
            prompt += f"\n\nContext from previous extraction:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"

        # Add mandatory evidence instruction
        prompt += """
⚠️ MANDATORY REQUIREMENT:
Your JSON response MUST include 'evidence_pages': [page_numbers].
List ALL page numbers (1-based, from image labels below) used for extraction.
If you used images labeled "Page 5", "Page 7", "Page 8", return: 'evidence_pages': [5, 7, 8]
If no relevant information found, return 'evidence_pages': []
"""

        # Step 1: Get pages for sections
        pages = self._get_pages_for_sections(pdf_path, section_headings, fallback_pages=5, agent_id=agent_id)

        # Step 2: Adaptive page selection (max 4 pages to prevent token overflow)
        if len(pages) > 4:
            selected_pages = [
                pages[0],                    # Start
                pages[len(pages)//3],        # Early-middle
                pages[2*len(pages)//3],      # Late-middle
                pages[-1]                    # End
            ]
            pages = sorted(set(selected_pages))

        # Step 3: Render pages to images
        images, page_labels = self._render_pdf_pages(pdf_path, pages, dpi=200)

        if not images:
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": "No images rendered",
                "extraction_time": time.time() - start_time,
                "evidence_pages": []
            }

        # Step 4: Build multimodal message with interleaved page labels
        content = [{"type": "text", "text": prompt}]

        for img_bytes, label in zip(images, page_labels):
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            # Add text label before each image so LLM knows which page is which
            content.append({"type": "text", "text": f"\n--- {label} ---"})
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })

        messages = [{"role": "user", "content": content}]

        # Step 5: Call OpenAI API with retry logic
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

                response = client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0
                )

                raw_content = response.choices[0].message.content

                # Step 6: Parse JSON with fallback
                extracted_data = self._parse_json_with_fallback(raw_content)

                if extracted_data is None:
                    raise ValueError(f"Failed to parse JSON from response: {raw_content[:200]}")

                # Step 7: Validate evidence_pages exist
                evidence_pages = extracted_data.get('evidence_pages', [])
                if not evidence_pages:
                    # Validation: Check that evidence_pages exists
                    print(f"   ⚠️  {agent_id}: No evidence_pages returned (may be empty list)")

                # Step 8: Return result
                return {
                    "agent_id": agent_id,
                    "status": "success",
                    "data": extracted_data,
                    "section_headings": section_headings,
                    "pages_rendered": [p + 1 for p in pages],  # 1-based
                    "num_images": len(images),
                    "evidence_pages": evidence_pages,
                    "extraction_time": time.time() - start_time,
                    "model": "gpt-4o-2024-11-20",
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s
                    time.sleep(wait_time)
                continue

        # All retries failed
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(last_error),
            "extraction_time": time.time() - start_time,
            "evidence_pages": []
        }

    def _get_pages_for_sections(
        self,
        pdf_path: str,
        section_headings: List[str],
        fallback_pages: int = 5,
        agent_id: str = None
    ) -> List[int]:
        """
        Get page numbers (0-indexed) for given section headings.

        Uses hybrid strategy:
        1. Search PDF text for section headings
        2. Fallback to content keywords if no headings found
        3. Final fallback to document-wide sampling

        Args:
            pdf_path: Path to PDF
            section_headings: List of section titles to find
            fallback_pages: Number of pages to sample if no sections found
            agent_id: Optional agent ID for content-based fallback

        Returns:
            List of page indices (0-based)
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            found_pages = set()

            # Strategy 1: Search for section headings in PDF text
            for heading in section_headings:
                for page_num in range(total_pages):
                    page = doc[page_num]
                    text = page.get_text()
                    # Normalize and search
                    normalized_heading = re.sub(r'\s+', ' ', heading.lower().strip())
                    normalized_text = re.sub(r'\s+', ' ', text.lower())

                    if normalized_heading in normalized_text:
                        found_pages.add(page_num)
                        # Also add next 2 pages for context
                        if page_num + 1 < total_pages:
                            found_pages.add(page_num + 1)
                        if page_num + 2 < total_pages:
                            found_pages.add(page_num + 2)

            doc.close()

            if found_pages:
                return sorted(list(found_pages))[:10]  # Max 10 pages

            # Strategy 2: Content-based keyword fallback
            if agent_id:
                content_pages = self._find_pages_by_content_keywords(pdf_path, agent_id)
                if content_pages:
                    return content_pages[:fallback_pages]

            # Strategy 3: Document-wide sampling (last resort)
            if total_pages <= fallback_pages:
                return list(range(total_pages))
            else:
                # Sample evenly across document
                step = total_pages / fallback_pages
                return [int(i * step) for i in range(fallback_pages)]

        except Exception as e:
            print(f"   ⚠️  Page selection error: {e}")
            # Emergency fallback: first N pages
            return list(range(min(fallback_pages, 10)))

    def _find_pages_by_content_keywords(self, pdf_path: str, agent_id: str) -> List[int]:
        """
        Find pages by content keywords specific to each agent.

        Args:
            pdf_path: Path to PDF
            agent_id: Agent identifier

        Returns:
            List of page indices (0-based)
        """
        # Agent-specific keywords (Swedish)
        AGENT_KEYWORDS = {
            'governance_agent': ['styrelse', 'ordförande', 'revisor', 'valberedning'],
            'financial_agent': ['resultaträkning', 'balansräkning', 'intäkter', 'kostnader', 'tillgångar', 'skulder'],
            'property_agent': ['fastighetsbeteckning', 'adress', 'byggår', 'lägenheter'],
            'operations_agent': ['underhåll', 'energi', 'försäkring', 'avtal'],
            'notes_accounting_agent': ['redovisningsprinciper', 'värderingsprinciper'],
            'notes_loans_agent': ['lån', 'skulder', 'ränta'],
            'notes_buildings_agent': ['byggnader', 'mark', 'avskrivningar'],
            'notes_receivables_agent': ['fordringar'],
            'notes_reserves_agent': ['fond', 'underhåll'],
            'notes_tax_agent': ['skatt', 'avgift'],
        }

        keywords = AGENT_KEYWORDS.get(agent_id, [])
        if not keywords:
            return []

        try:
            doc = fitz.open(pdf_path)
            scored_pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()

                # Count keyword matches
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    scored_pages.append((page_num, score))

            doc.close()

            # Sort by score descending
            scored_pages.sort(key=lambda x: x[1], reverse=True)

            # Return top pages
            return [page_num for page_num, score in scored_pages[:5]]

        except Exception as e:
            print(f"   ⚠️  Content keyword search error: {e}")
            return []

    def _render_pdf_pages(
        self,
        pdf_path: str,
        page_numbers: List[int],
        dpi: int = 200
    ) -> Tuple[List[bytes], List[str]]:
        """
        Render PDF pages to PNG images.

        Args:
            pdf_path: Path to PDF
            page_numbers: List of page indices (0-based)
            dpi: Resolution for rendering

        Returns:
            Tuple of (image_bytes_list, page_labels_list)
        """
        images = []
        labels = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in page_numbers:
                if page_num < 0 or page_num >= len(doc):
                    continue

                page = doc[page_num]

                # Render to pixmap
                zoom = dpi / 72  # PDF default is 72 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PNG bytes
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
                labels.append(f"Page {page_num + 1}")  # 1-based labels

            doc.close()

        except Exception as e:
            print(f"   ⚠️  PDF rendering error: {e}")

        return images, labels

    def _parse_json_with_fallback(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from text with multiple fallback strategies.

        Handles:
        - Clean JSON
        - Markdown code fences (```json ... ```)
        - Trailing text after JSON

        Args:
            text: Raw text possibly containing JSON

        Returns:
            Parsed dict or None if parsing fails
        """
        if not text:
            return None

        # Strategy 1: Direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code fence
        json_fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_fence_match:
            try:
                return json.loads(json_fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find first '{' and last '}' (handles trailing text)
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        return None
