"""
Concrete note agents for Swedish BRF document extraction.

Implements specialized agents for different note types:
- DepreciationNoteAgent: Extracts depreciation information
- MaintenanceNoteAgent: Extracts maintenance plan details
- TaxNoteAgent: Extracts tax policy and amounts

Author: Claude Code
Date: 2025-10-13 (Path B Day 3)
"""

from typing import Dict, Any, Type

from .base_note_agent import BaseNoteAgent
from ..models.note import Note
from ..schemas.notes_schemas import (
    BaseNoteData,
    DepreciationData,
    MaintenanceData,
    TaxData
)


class DepreciationNoteAgent(BaseNoteAgent):
    """
    Agent for extracting depreciation information from Swedish BRF notes.

    Extracts:
    - Depreciation method (linjär, rak, etc.)
    - Useful life in years
    - Assets being depreciated

    Swedish Terminology:
    - avskrivning = depreciation
    - avskrivningsmetod = depreciation method
    - nyttjandeperiod / ekonomisk livslängd = useful life
    - byggnader = buildings
    - inventarier = equipment
    """

    def _get_schema_class(self) -> Type[BaseNoteData]:
        """Return DepreciationData schema."""
        return DepreciationData

    def _build_extraction_prompt(
        self,
        note: Note,
        context: Dict[str, Any]
    ) -> str:
        """
        Build depreciation extraction prompt with Swedish terminology.

        Uses 3-layer terminology approach:
        - Layer 1: Swedish term → English concept
        - Layer 2: Synonyms and variations
        - Layer 3: Context hints from surrounding text
        """
        # Extract balance sheet context if available
        balance_sheet_snippet = context.get('balance_sheet_snippet', 'Not available')

        # Build comprehensive prompt
        prompt = f"""Extract depreciation information from this Swedish BRF note.

**Note Content:**
{note.content}

**Balance Sheet Context (for cross-validation):**
{balance_sheet_snippet}

**Task:**
Extract the following information accurately:

1. **depreciation_method**: The method used for depreciation
   - Swedish terms: "linjär avskrivning", "rak avskrivning", "degressiv avskrivning"
   - Look for: "avskrivningsmetod", "metod för avskrivning", "avskrivning sker enligt"

2. **useful_life_years**: Number of years assets are depreciated over
   - Swedish terms: "nyttjandeperiod", "ekonomisk livslängd", "avskrivningstid"
   - Look for: Numbers followed by "år" (years)
   - Typical values: Buildings 50-100 years, Equipment 5-20 years

3. **depreciation_base**: What assets are being depreciated
   - Swedish terms: "byggnader", "inventarier", "maskiner och inventarier"
   - Look for: Asset types mentioned in depreciation context

**Important Instructions:**
- Extract ONLY information that is explicitly stated in the text
- If information is not found, return null for that field
- Cite the page number in evidence_pages (use note.pages if known)
- Include relevant quotes in evidence_quotes (Swedish text is fine)
- Return valid JSON matching the schema below

**Required JSON Schema:**
{{
    "depreciation_method": "string or null (e.g., 'linjär avskrivning')",
    "useful_life_years": "integer or null (e.g., 50)",
    "depreciation_base": "string or null (e.g., 'byggnader')",
    "evidence_pages": [list of page numbers],
    "evidence_quotes": ["list of relevant quotes from the text"]
}}

**Example Output:**
{{
    "depreciation_method": "linjär avskrivning",
    "useful_life_years": 50,
    "depreciation_base": "byggnader",
    "evidence_pages": [10],
    "evidence_quotes": [
        "Avskrivningar sker enligt linjär avskrivningsmetod",
        "Byggnader skrivs av över en beräknad nyttjandeperiod om 50 år"
    ]
}}
"""
        return prompt

    def _cross_validate(
        self,
        data: DepreciationData,
        context: Dict[str, Any]
    ) -> DepreciationData:
        """
        Cross-validate depreciation data with balance sheet.

        Checks:
        1. If balance sheet has accumulated depreciation, boost confidence
        2. Validate useful_life_years is in reasonable range
        3. Check if depreciation_base matches balance sheet asset types
        """
        # Get balance sheet data if available
        balance_sheet = context.get('balance_sheet_data', {})

        # Check 1: Validate accumulated depreciation exists
        if balance_sheet.get('accumulated_depreciation'):
            # Balance sheet confirms depreciation is tracked
            data.confidence += 0.1

        # Check 2: Validate useful_life_years range
        if data.useful_life_years:
            # Buildings: 50-100 years
            # Equipment: 5-20 years
            # If outside range, reduce confidence but keep value
            if data.useful_life_years < 5 or data.useful_life_years > 100:
                data.confidence -= 0.1

        # Check 3: Validate depreciation_base matches assets
        if data.depreciation_base and balance_sheet.get('fixed_assets'):
            # If we have fixed assets in balance sheet, boost confidence
            data.confidence += 0.05

        return data


class MaintenanceNoteAgent(BaseNoteAgent):
    """
    Agent for extracting maintenance plan information from Swedish BRF notes.

    Extracts:
    - Maintenance plan description
    - Plan start and end dates
    - Budget allocation

    Swedish Terminology:
    - underhåll = maintenance
    - underhållsplan = maintenance plan
    - planerat underhåll = planned maintenance
    - underhållsfond = maintenance fund
    """

    def _get_schema_class(self) -> Type[BaseNoteData]:
        """Return MaintenanceData schema."""
        return MaintenanceData

    def _build_extraction_prompt(
        self,
        note: Note,
        context: Dict[str, Any]
    ) -> str:
        """Build maintenance plan extraction prompt."""
        prompt = f"""Extract maintenance plan information from this Swedish BRF note.

**Note Content:**
{note.content}

**Task:**
Extract the following information:

1. **maintenance_plan**: Description of the maintenance plan
   - Swedish terms: "underhållsplan", "plan för underhåll", "planerat underhåll"
   - Look for: "10-årig underhållsplan", "långsiktig underhållsplan"

2. **plan_start_date**: Start year of the plan
   - Look for: Year (e.g., "2020") when plan begins
   - Format: Return as string "YYYY"

3. **plan_end_date**: End year of the plan
   - Look for: Year when plan ends (e.g., "2030")
   - Format: Return as string "YYYY"

4. **maintenance_budget**: Total budget allocated
   - Swedish terms: "underhållsbudget", "avsatta medel"
   - Look for: Amounts in SEK (e.g., "15 miljoner kr", "15,000,000 SEK")
   - Return as float (e.g., 15000000.0)

**Required JSON Schema:**
{{
    "maintenance_plan": "string or null",
    "plan_start_date": "string (YYYY) or null",
    "plan_end_date": "string (YYYY) or null",
    "maintenance_budget": "float or null",
    "evidence_pages": [list of page numbers],
    "evidence_quotes": ["list of relevant quotes"]
}}
"""
        return prompt

    def _cross_validate(
        self,
        data: MaintenanceData,
        context: Dict[str, Any]
    ) -> MaintenanceData:
        """
        Cross-validate maintenance data.

        Checks:
        1. Date range is reasonable (5-20 years typical)
        2. Budget is reasonable for BRF size
        """
        # Validate date range
        if data.plan_start_date and data.plan_end_date:
            try:
                start_year = int(data.plan_start_date)
                end_year = int(data.plan_end_date)

                # Check valid range
                if end_year > start_year:
                    plan_length = end_year - start_year
                    # Typical BRF plans: 5-20 years
                    if 5 <= plan_length <= 20:
                        data.confidence += 0.1
                    else:
                        data.confidence -= 0.05
            except (ValueError, TypeError):
                pass

        # Validate budget if available
        if data.maintenance_budget:
            # Typical range: 1M-100M SEK for BRF maintenance plans
            if 1_000_000 <= data.maintenance_budget <= 100_000_000:
                data.confidence += 0.05

        return data


class TaxNoteAgent(BaseNoteAgent):
    """
    Agent for extracting tax information from Swedish BRF notes.

    Extracts:
    - Tax accounting policy
    - Current year tax
    - Deferred tax

    Swedish Terminology:
    - skatt = tax
    - inkomstskatt = income tax
    - skattepolicy = tax policy
    - aktuell skatt = current tax
    - uppskjuten skatt = deferred tax
    """

    def _get_schema_class(self) -> Type[BaseNoteData]:
        """Return TaxData schema."""
        return TaxData

    def _build_extraction_prompt(
        self,
        note: Note,
        context: Dict[str, Any]
    ) -> str:
        """Build tax extraction prompt."""
        # Extract income statement context if available
        income_statement_snippet = context.get('income_statement_snippet', 'Not available')

        prompt = f"""Extract tax information from this Swedish BRF note.

**Note Content:**
{note.content}

**Income Statement Context (for cross-validation):**
{income_statement_snippet}

**Task:**
Extract the following information:

1. **tax_policy**: Tax accounting method or policy
   - Swedish terms: "skattepolicy", "redovisningsprinciper för skatt"
   - Look for: "bokföringsmässiga grunder", "skattemässiga grunder"

2. **current_tax**: Current year tax amount
   - Swedish terms: "aktuell skatt", "inkomstskatt", "skatt för året"
   - Look for: Amounts in SEK (e.g., "250,000 SEK", "250 tkr")
   - Return as float (e.g., 250000.0)

3. **deferred_tax**: Deferred tax amount
   - Swedish terms: "uppskjuten skatt", "uppskjuten skattefordran"
   - May be negative (tax asset) or positive (tax liability)
   - Return as float (e.g., -50000.0 for tax asset)

**Required JSON Schema:**
{{
    "tax_policy": "string or null",
    "current_tax": "float or null",
    "deferred_tax": "float or null",
    "evidence_pages": [list of page numbers],
    "evidence_quotes": ["list of relevant quotes"]
}}
"""
        return prompt

    def _cross_validate(
        self,
        data: TaxData,
        context: Dict[str, Any]
    ) -> TaxData:
        """
        Cross-validate tax data with income statement.

        Checks:
        1. Compare current_tax with income statement tax expense
        2. Validate amounts are reasonable
        """
        # Get income statement data
        income_statement = context.get('income_statement_data', {})

        # Check 1: Cross-validate with income statement tax
        if income_statement.get('tax_expense') and data.current_tax:
            income_tax = abs(income_statement['tax_expense'])
            extracted_tax = abs(data.current_tax)

            # Check if values are reasonably close (within 20%)
            if income_tax > 0:
                diff_ratio = abs(income_tax - extracted_tax) / income_tax
                if diff_ratio < 0.2:
                    # Values match closely, boost confidence
                    data.confidence += 0.15
                elif diff_ratio > 0.5:
                    # Large discrepancy, reduce confidence
                    data.confidence -= 0.1

        # Check 2: Validate amounts are reasonable for BRF
        if data.current_tax:
            # BRF typically have tax expenses from 0 to a few million SEK
            if abs(data.current_tax) > 50_000_000:  # 50M SEK sanity check
                data.confidence -= 0.1

        if data.deferred_tax:
            # Deferred tax typically smaller than current tax
            if abs(data.deferred_tax) > 20_000_000:  # 20M SEK sanity check
                data.confidence -= 0.05

        return data


# Export all agents
__all__ = [
    'DepreciationNoteAgent',
    'MaintenanceNoteAgent',
    'TaxNoteAgent',
]
