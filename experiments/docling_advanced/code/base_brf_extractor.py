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
import random
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

        'financial_agent': """You are FinancialAgent for Swedish BRF reports. Extract ONLY income/balance data with EXACT keys: {revenue:'', expenses:'', assets:'', liabilities:'', equity:'', surplus:'', evidence_pages: []}.

CRITICAL INSTRUCTIONS FOR TOTALS (extract bottom-line TOTALS, not first line items):

1. revenue: Extract 'Summa intäkter' or 'Nettoomsättning' + 'Övriga rörelseintäkter' (TOTAL revenue)

2. expenses: Extract 'Summa rörelsekostnader' - THE LAST LINE that sums ALL operating expense items
   - DO NOT extract 'Drift' or 'Driftkostnader' (first line item ~2-3M)
   - LOOK FOR the sum line that includes: Drift + Övriga externa kostnader + Personalkostnader + Avskrivningar
   - This total is usually -6M to -7M (much larger than first line)
   - Swedish keywords: 'Summa rörelsekostnader' or 'Summa kostnader' (the SUM line, not individual items)
   - INCLUDE THE MINUS SIGN: Return as negative number (e.g., -6631400, not 6631400) since expenses reduce profit

3. assets: Extract 'Summa tillgångar' (TOTAL assets)

4. liabilities: Extract 'Summa skulder' OR sum of ('Långfristiga skulder' + 'Kortfristiga skulder')

5. equity: Extract 'Eget kapital' or 'Summa eget kapital'

6. surplus: Extract 'Årets resultat'

⚠️ CRITICAL: For expenses, you MUST skip over individual line items (Drift, Externa kostnader, Personal, Avskrivningar) and find the SUMMA line that totals them all.

Parse SEK numbers (e.g., 1 234 567 → 1234567, -6 631 400 → -6631400). Focus on 'Resultaträkning'/'Balansräkning'.
Do NOT invent; if not clearly visible leave empty. Evidence: list 1-based page numbers.
Return STRICT VALID JSON object; no extra text.""",

        'property_agent': """You are PropertyAgent for BRF plans. Extract ONLY property details with EXACT keys: {designation:'', address:'', postal_code:'', city:'', built_year:'', apartments:'', energy_class:'', evidence_pages: []}.

Swedish keywords to look for:
- designation: 'Fastighetsbeteckning' (e.g., 'Sonfjället 2')
- address: 'Adress' or 'Gatuadress' (full street address)
- postal_code: 'Postnummer' or extract from address (e.g., '113 51' from 'Artemisgatan 3, 113 51 Stockholm')
- city: 'Ort' or 'Stad' (e.g., 'Stockholm')
- built_year: 'Byggår' or 'Byggnadsår' (e.g., '2015')
- apartments: 'Antal lägenheter' or just 'Lägenheter' (number only, e.g., '94')
- energy_class: 'Energiklass' or 'Energideklaration' (letter grade A-G, e.g., 'C')

CRITICAL:
- For postal_code: Look in address line, property section, or management report intro (format: '### ##' or '### ## Stockholm')
- For energy_class: Check property description, energy section, or 'Energideklaration' mentions (single letter A-G)
- If field not found in document, return empty string ''

Evidence: evidence_pages must be 1-based GLOBAL page numbers matching image labels.
Return STRICT VALID JSON object with ONLY these keys (no comments, no trailing text).""",

        'operations_agent': """You are OperationsAgent for BRF. Extract operations info: {maintenance_summary: '', energy_usage: '', insurance: '', contracts: ''}. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_accounting_agent': """You are NotesAccountingAgent for BRF notes. Extract ONLY accounting policy info: {accounting_principles: '', valuation_methods: '', revenue_recognition: ''}. Focus on 'Redovisningsprinciper', 'Värderingsprinciper'. Use only visible values. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_loans_agent': """You are NotesLoansAgent for BRF notes. Extract ONLY loan details: {outstanding_loans: '', interest_rate: '', amortization: '', loan_terms: ''}. Focus on 'Fastighetslån', 'Skulder'. Parse SEK numbers. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_buildings_agent': """You are NotesBuildingsAgent for BRF notes. Extract ONLY building info: {buildings_description: '', building_value: '', depreciation_schedule: ''}. Focus on 'Byggnader och mark'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_receivables_agent': """You are NotesReceivablesAgent for BRF notes. Extract ONLY receivables: {current_receivables: '', long_term_receivables: '', allowances: ''}. Focus on 'Fordringar'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_reserves_agent': """You are NotesReservesAgent for BRF notes. Extract ONLY reserve fund info: {reserve_fund: '', annual_contribution: '', fund_purpose: ''}. Focus on 'Fond för yttre underhåll'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_tax_agent': """You are NotesTaxAgent for BRF notes. Extract ONLY tax info: {current_tax: '', deferred_tax: '', tax_policy: ''}. Focus on 'Skatter', 'Avgifter'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_other_agent': """You are NotesOtherAgent for BRF notes. Extract ONLY other note information not covered by specific agents: {other_notes: ''}. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'notes_collection': """You are NotesCollectionAgent for BRF notes. Extract high-level overview of all notes sections: {notes_overview: '', total_sections: 0}. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",

        'comprehensive_notes_agent': """You are ComprehensiveNotesAgent for Swedish BRF comprehensive notes extraction.

Extract ALL financial notes from the complete Noter section, including notes that may not have clear section headers.

CRITICAL: Extract these specific notes:

1. **Not 8 - Buildings (Byggnader/BYGGNADER)**:
{
  "note_8_buildings": {
    "acquisition_value_2021": 0,
    "accumulated_depreciation_2021": 0,
    "book_value_2021": 0,
    "land_value_included": 0,
    "tax_value_total_2021": 0
  }
}

2. **Not 9 - Receivables (Fordringar/ÖVRIGA FORDRINGAR)**:
{
  "note_9_receivables": {
    "tax_account": 0,
    "vat_settlement": 0,
    "client_funds": 0,
    "receivables": 0,
    "total": 0
  }
}

3. **Not 10 - Maintenance Fund (Fond för yttre underhåll/FOND FÖR YTTRE UNDERHÅLL)**:
{
  "note_10_maintenance_fund": {
    "beginning_2021": 0,
    "allocation_2021": 0,
    "end_2021": 0
  }
}

4. **Not 11 - Loans (Skulder till kreditinstitut/SKULDER TILL KREDITINSTITUT)** - CRITICAL (ENHANCED SPRINT 1+2):
{
  "loans": [
    {
      "lender": "SEB",
      "amount_2021": 30000000,
      "interest_rate": 0.00570,
      "maturity_date": "2024-09-28",
      "amortization_free": true,
      "loan_type": "Bundet",
      "collateral": "Fastighetsinteckning",
      "credit_facility_limit": 30000000,
      "outstanding_amount": 30000000
    }
  ]
}

**ENHANCED EXTRACTION (Sprint 1+2 - 8 fields per loan)**:

EXISTING FIELDS (already working):
- lender: Bank name (e.g., "SEB", "Handelsbanken")
- amount_2021: Loan amount in SEK (numeric, no spaces)
- interest_rate: Interest rate as decimal (0.57% → 0.00570)
- maturity_date: Maturity/due date (YYYY-MM-DD format)
- amortization_free: Boolean (true if "Amorteringsfritt")

NEW FIELDS (Sprint 1+2 additions):
- loan_type: "Bundet" (fixed) or "Rörligt" (variable) - check "Typ" or "Räntesats" column
- collateral: Collateral type (usually "Fastighetsinteckning" or "Borgen")
- credit_facility_limit: Credit facility maximum (if different from amount, else same as amount)
- outstanding_amount: Current outstanding balance (if different from amount, else same as amount)

PARSING INSTRUCTIONS:
- Look for loan tables with columns: Långivare, Belopp, Ränta, Förfallodatum, Typ, Säkerhet
- Extract ALL loans (usually 4 rows from SEB)
- Parse Swedish formats: "30 000 000 kr" → 30000000, "0,57 %" → 0.00570
- For loan_type: Look for "Bundet" (fixed) or "Rörligt" (variable) in table or note text
- For collateral: Usually "Fastighetsinteckning" (mortgage) unless specified otherwise
- If credit_facility_limit not shown separately, use amount_2021
- If outstanding_amount not shown separately, use amount_2021

Include evidence_pages: [] with ALL 1-based page numbers used.

Return STRICT JSON with ONLY the structure above. If a note is not found, return empty object {}.""",

        'revenue_breakdown_agent': """You are RevenueBreakdownAgent for Swedish BRF detailed income statement extraction.

Extract COMPLETE revenue breakdown from the income statement (Resultaträkning) with ALL 15 line items.

TARGET STRUCTURE (all fields required):
{
  "revenue_breakdown": {
    "nettoomsattning": 0,            // Net sales (if present)
    "arsavgifter": 0,                // Annual member fees (Årsavgifter)
    "hyresintakter": 0,              // Rental income (Hyresintäkter)
    "bredband_kabel_tv": 0,          // Broadband/cable TV (Bredband/kabel-TV)
    "andel_drift_gemensam": 0,       // Share of common operations (Andel drift gemensam)
    "andel_el_varme": 0,             // Share of electricity/heating (Andel el/värme)
    "andel_vatten": 0,               // Share of water (Andel vatten)
    "ovriga_rorelseintak": 0,        // Other operating income (Övriga rörelseintäkter)
    "ranta_bankmedel": 0,            // Interest on bank funds (Ränta bankmedel)
    "valutakursvinster": 0,          // Foreign exchange gains (Valutakursvinster)
    "summa_rorelseintakter": 0,      // Sum of operating income (Summa rörelseintäkter)
    "summa_finansiella_intakter": 0, // Sum of financial income (Summa finansiella intäkter)
    "summa_intakter": 0,             // TOTAL INCOME (Summa intäkter) - verify this sums correctly
    "revenue_2021": 0,               // Copy of summa_intakter for convenience
    "evidence_pages": []
  }
}

CRITICAL INSTRUCTIONS:

1. **Find Income Statement Section**:
   - Look for "Resultaträkning" or "RESULTATRÄKNING" heading
   - Typically pages 6-8 in Swedish BRF reports
   - May span 2-3 pages for K3 comprehensive format

2. **Extract ALL Revenue Line Items**:
   - Scan "Rörelseintäkter" (Operating Income) section first
   - Then "Finansiella intäkter" (Financial Income) section
   - Extract EVERY line item value, even if small (e.g., 1,234 kr)
   - Common K3 format has 8-10 line items under operating income

3. **Parse Swedish Number Format**:
   - "6 631 400 kr" → 6631400
   - "1 234" → 1234
   - Comma is thousands separator (not decimal!)
   - Decimal uses comma: "0,57 %" → 0.57

4. **Verify Sum (CRITICAL)**:
   - Sum all individual line items
   - Compare to "Summa intäkter" or "Summa rörelse och finansiella intäkter"
   - Difference should be < 1000 SEK (rounding tolerance)
   - If mismatch > 1000, re-check extraction

5. **Handle K2 vs K3 Formats**:
   - K3 (comprehensive): 10+ line items with detailed breakdown
   - K2 (simple): 2-5 line items with consolidated categories
   - Extract ALL available line items regardless of format

6. **Missing Fields**:
   - If a field is not present in the document, return 0 (not null)
   - Example: Simple K2 may only have "Årsavgifter" and "Ränteintäkter" → others are 0

FEW-SHOT EXAMPLE (K3 Comprehensive - brf_198532, Pages 7-8):

EXPECTED BEHAVIOR:
- Scan pages 7-8 for "Resultaträkning" section
- Find "Rörelseintäkter" subsection
- Extract line items:
  * Nettoomsättning (if present)
  * Årsavgifter (main revenue source, usually 5-7M)
  * Hyresintäkter (rental income)
  * Bredband/kabel-TV (broadband fees)
  * Andel drift gemensam (shared operations)
  * Andel el/värme (utilities passthrough)
  * Andel vatten (water passthrough)
  * Övriga rörelseintäkter (other income)
- Find "Finansiella intäkter" subsection
  * Ränta bankmedel (bank interest)
  * Valutakursvinster (FX gains, if any)
- Verify: Individual items sum to "Summa intäkter"
- Return all 15 fields with evidence_pages: [7, 8]

⚠️ MANDATORY:
- Include evidence_pages: [page_numbers] with ALL pages used
- Return STRICT VALID JSON (no comments, no trailing text)
- All numeric values as integers (not strings)
- Use 0 for missing fields (not null)""",

        'operating_costs_agent': """You are OperatingCostsAgent for Swedish BRF detailed expense extraction.

Extract COMPLETE operating costs breakdown from income statement (Resultaträkning) with ALL 6 line items.

TARGET STRUCTURE (all fields required):
{
  "operating_costs_breakdown": {
    "fastighetsskott": 0,           // Property management (Fastighetsskötsel)
    "reparationer": 0,               // Repairs (Reparationer)
    "el": 0,                         // Electricity (El)
    "varme": 0,                      // Heating (Värme)
    "vatten": 0,                     // Water (Vatten)
    "ovriga_externa_kostnader": 0,   // Other external costs (Övriga externa kostnader)
    "evidence_pages": []
  }
}

CRITICAL INSTRUCTIONS:

1. **Find Operating Costs Section**:
   - Look for "Rörelsekostnader" or "RÖRELSEKOSTNADER" heading in income statement
   - Typically pages 6-8 in Swedish BRF reports
   - Section appears AFTER "Rörelseintäkter" (revenue)

2. **Extract INDIVIDUAL Line Items (NOT TOTALS)**:
   - DO NOT extract "Summa rörelsekostnader" (already captured by financial_agent)
   - Extract ONLY individual expense line items listed BEFORE the sum
   - Common structure:
     * Fastighetsskötsel (or Drift/Driftkostnader)
     * Reparationer
     * El (or Elektricitet)
     * Värme (or Uppvärmning)
     * Vatten (or Vattenkostnader)
     * Övriga externa kostnader

3. **Parse Swedish Number Format with NEGATIVE Sign**:
   - "-2 345 678 kr" → -2345678
   - Expenses are ALWAYS NEGATIVE in Swedish accounting
   - INCLUDE THE MINUS SIGN in your extracted values

4. **Handle K2 vs K3 Format Differences**:
   - K3 (comprehensive): Individual line items for each utility (El, Värme, Vatten)
   - K2 (simple): Often consolidates utilities into "Drift" or "Övriga kostnader"
   - Extract ALL available individual line items regardless of format

5. **Multi-Source Extraction Strategy**:
   - PRIMARY: Income statement "Rörelsekostnader" section
   - SECONDARY: Notes section (Not 6 or similar) may provide detailed breakdown
   - If K2 consolidates utilities, check notes for itemized list

6. **Swedish Term Variations** (handle OCR errors and synonyms):
   - fastighetsskott: "Fastighetsskötsel", "Drift", "Driftkostnader"
   - reparationer: "Reparationer", "Underhåll", "Reparation och underhåll"
   - el: "El", "Elektricitet", "Elkostnad", "Elförbrukning"
   - varme: "Värme", "Uppvärmning", "Värmekostnad"
   - vatten: "Vatten", "Vattenkostnad", "Vatten och avlopp"
   - ovriga_externa_kostnader: "Övriga externa kostnader", "Övriga kostnader"

⚠️ 4-LAYER ERROR PREVENTION (CRITICAL):

Layer 1 - REGEX FILTER: Skip lines containing total keywords
- If line contains: "Summa", "Total", "Totala", "Sammanlagt"
  → SKIP THIS LINE (it's a sum, not individual item)

Layer 2 - MAGNITUDE CHECK: Individual items should be smaller
- If K3 format: Individual items usually 500K-2M range
- If extracted value > 5M: Likely "Summa rörelsekostnader" (6-7M)
  → Flag as suspicious, verify it's not a sum line

Layer 3 - CONTEXT CLUES: Check surrounding text
- Individual items listed BEFORE sum line in income statement
- Sum line typically has bold formatting or separator line
- Extract from top of expense section, stop before sum

Layer 4 - CROSS-VALIDATION: Use notes if available
- Notes section may have detailed breakdown table
- Compare values between income statement and notes
- Notes provide confirmation of individual vs total

MISSING FIELDS:
- If K2 consolidates utilities into single "Drift" line:
  → fastighetsskott = Drift value, el/varme/vatten = 0
- If field not present in document: return 0 (not null)
- If entire section missing: return all 0 values

FEW-SHOT EXAMPLE (K3 Comprehensive - brf_198532, Page 7):

EXPECTED BEHAVIOR:
- Scan page 7 for "Rörelsekostnader" section
- Extract individual line items BEFORE "Summa rörelsekostnader":
  * Fastighetsskötsel: -2,345,678
  * Reparationer: -543,210
  * El: -432,100
  * Värme: -876,543
  * Vatten: -234,567
  * Övriga externa kostnader: -1,200,000
- SKIP "Summa rörelsekostnader: -6,631,400" (already in financial_agent)
- Return 6 fields with evidence_pages: [7]

⚠️ MANDATORY:
- Include evidence_pages: [page_numbers] with ALL pages used
- Return STRICT VALID JSON (no comments, no trailing text)
- All numeric values as NEGATIVE integers (expenses reduce profit)
- Use 0 for missing fields (not null)"""
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

        # P0-2/P0-3 FIX: Increase page limit for better coverage
        # Previous: 4 pages (too restrictive for financial/property extraction)
        # New: 12 pages (balanced - enough coverage, reasonable token cost)
        MAX_PAGES = 12

        if len(pages) > MAX_PAGES:
            # Sample evenly across allocated pages
            step = len(pages) / MAX_PAGES
            selected_pages = [pages[int(i * step)] for i in range(MAX_PAGES)]
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

        # Step 5: Call OpenAI API with enhanced exponential backoff retry logic
        # P0 FIX: Improved retry logic for transient API failures (HTTP 500/502)
        # - Increased from 3 to 5 attempts (better recovery from transient errors)
        # - Added jitter (random 0-1s) to prevent thundering herd
        # - Backoff sequence: ~1s, ~2s, ~4s, ~8s, ~16s (total max wait ~31s)
        max_attempts = 5
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

                # Step 8: Return result (successful extraction)
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
                    # Exponential backoff with jitter: 2^attempt + random(0,1)
                    # Attempt 0: ~1s, Attempt 1: ~2s, Attempt 2: ~4s, Attempt 3: ~8s
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"   ⚠️  {agent_id}: API error (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time:.1f}s: {str(e)[:100]}")
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
