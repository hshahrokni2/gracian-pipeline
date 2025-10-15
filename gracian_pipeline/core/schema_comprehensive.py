"""
Comprehensive Expanded Schema for BRF Extraction
Extends base schema.py with comprehensive_details for each agent.

This captures the ~70% of information that exists in documents but isn't in the base schema.
Based on human validation findings from HUMAN_VALIDATION_GUIDE.md.
"""

from __future__ import annotations
from typing import Dict, Any

# Import base schema
try:
    from .schema import EXPECTED_TYPES as BASE_TYPES
except ImportError:
    # Standalone execution
    from schema import EXPECTED_TYPES as BASE_TYPES

# MEGA-EXPANDED TYPES - Keeps all base fields + adds comprehensive_details
COMPREHENSIVE_TYPES: Dict[str, Dict[str, str]] = {
    "governance_agent": {
        # Base fields (keep as-is, BUT board_members is STRUCTURED format)
        # CRITICAL: board_members is [{name: str, role: str}], not simple string list
        # Roles: "Ordförande" (chairman), "Ledamot" (member), "Suppleant" (deputy), "Revisor" (auditor)
        **BASE_TYPES["governance_agent"],
        # NEW: Comprehensive details
        "internal_auditor": "str",  # Ordinarie Intern Internrevisor
        "board_meeting_frequency": "str",  # E.g., "månadsvis"
    },

    "financial_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["financial_agent"],
        # NEW: Detailed breakdowns from notes
        "operating_costs_breakdown": "dict",  # Note 4: Driftkostnader line items
        "building_details": "dict",  # Note 8: Byggnader depreciation schedule
        "other_receivables": "dict",  # Note 9: Övriga fordringar
        "reserve_fund_movements": "dict",  # Note 10: Fond för yttre underhåll
        "income_breakdown": "dict",  # Intäkter line items
        "tax_details": "dict",  # Skatter details if available
    },

    "property_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["property_agent"],
        # NEW: Comprehensive property details
        "acquisition_date": "str",  # Förvärv date
        "municipality": "str",  # Kommun
        "heating_system": "str",  # Uppvärmning (e.g., "Fjärrvärme")
        "insurance_provider": "str",  # E.g., "Brandkontoret"
        "insurance_details": "str",  # Full insurance description
        "apartment_breakdown": "dict",  # {"1_rok": 10, "2_rok": 24, ...}
        "commercial_tenants": "list",  # [{"name": str, "area": str, "lease": str}]
        "common_areas": "list",  # [{"type": str, "count": int, "notes": str}]
        "samfallighet": "dict",  # {"name": str, "ownership_percent": num, "manages": str}
        "registration_dates": "dict",  # Economic plan, bylaws registration
        "tax_assessment": "dict",  # Taxeringsvärde breakdown
    },

    "notes_depreciation_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["notes_depreciation_agent"],
        # Already comprehensive at base level
    },

    "notes_maintenance_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["notes_maintenance_agent"],
        # NEW: Maintenance details
        "planned_actions": "list",  # [{"action": str, "year": str, "comment": str}]
        "technical_status": "str",  # Teknisk status description
        "suppliers": "list",  # [{"service": str, "supplier": str}]
        "service_contracts": "dict",  # All förvaltning contracts
    },

    "notes_tax_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["notes_tax_agent"],
        # NEW: Tax details
        "tax_type": "str",  # E.g., "privatbostadsföretag"
        "tax_law_reference": "str",  # E.g., "inkomstskattelagen (1999:1229)"
    },

    "events_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["events_agent"],
        # NEW: Event details
        "warranty_claims": "str",  # A-anmärkningar från garantibesiktning
        "tenant_changes": "str",  # Changes in commercial tenants
        "loan_restructuring": "str",  # Loan modifications
        "rental_activity": "str",  # Andrahandsuthyrningar count
        # NEW from brf_48574: Technical management changes
        "technical_management_change": "dict",  # {"new_provider": str, "start_date": str, "previous_provider": str}
    },

    "audit_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["audit_agent"],
        # NEW: Audit details
        "audit_date": "str",
        "audit_location": "str",
        "qualifications": "str",  # Any qualifications or remarks
    },

    "loans_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["loans_agent"],
        # NEW: Loan details
        "loan_provider": "str",  # E.g., "SEB"
        "loan_number": "str",  # E.g., "41431520"
        "loan_term": "str",  # E.g., "3 år"
        "amortization_schedule": "str",  # E.g., "amorteringsfria"
        "loan_changes": "str",  # Villkorsändringar
        # NEW from brf_48574: Risk indicators
        "all_loans_mature_within_12_months": "bool",  # True if ALL loans mature < 1 year (refinancing risk)
        "refinancing_year": "int",  # Year when all loans mature (if applicable)
        "credit_facility_previous_year": "num",  # Previous year's credit facility for comparison
    },

    "reserves_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["reserves_agent"],
        # NEW: Reserve details
        "reserve_policy": "str",  # Avsättningspolicy
        "fund_name": "str",  # E.g., "Fond för yttre underhåll"
        "annual_allocation": "num",  # Årlig avsättning
    },

    "energy_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["energy_agent"],
        # Energy data typically in separate documents
        "energy_source": "str",  # If mentioned in årsredovisning
        # NEW from brf_48574: Energy crisis impact tracking
        "electricity_increase_percent_2021_2022": "float",  # % increase electricity cost
        "heating_increase_percent_2021_2022": "float",  # % increase heating cost
        "water_increase_percent_2021_2022": "float",  # % increase water cost
    },

    "fees_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["fees_agent"],
        # NEW: Fee details
        "fee_calculation_basis": "str",  # E.g., "självkostnadsprincipen"
        "fee_per_sqm": "num",  # If different from monthly_fee
        "fee_unit": "str",  # E.g., "SEK/m² per year"
    },

    "insurance_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES.get("insurance_agent", {}),
        # NEW from brf_48574: Insurance cost tracking
        "insurance_increase_percent": "float",  # Year-over-year % increase
    },

    "tax_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES.get("tax_agent", {}),
        # NEW from brf_48574: Tax assessment tracking
        "tax_assessment_increase_percent": "float",  # Year-over-year % increase in taxeringsvärde
    },

    "cashflow_agent": {
        # Base fields (keep as-is)
        **BASE_TYPES["cashflow_agent"],
        # NEW: Cashflow details
        "operating_activities": "num",  # Kassaflöde från den löpande verksamheten
        "investing_activities": "num",  # Investeringsverksamheten
        "financing_activities": "num",  # Finansieringsverksamheten
    },

    "operating_costs_agent": {
        # THE MOST CRITICAL AGENT - Operating costs breakdown from Note 4
        "el": "num",  # Electricity
        "värme": "num",  # Heating
        "vatten": "num",  # Water
        "avlopp": "num",  # Sewage/drainage
        "värme_och_vatten": "num",  # Combined heating+water (MOST COMMON!)
        "underhåll_och_reparationer": "num",  # Maintenance & repairs (OFTEN LARGEST!)
        "fastighetsskötsel": "num",  # Property management services
        "försäkringar": "num",  # Insurance
        "fastighetsskatt": "num",  # Property tax
        "hiss": "num",  # Elevator maintenance
        "sotning_och_ventilationskontroll": "num",  # Chimney sweep & ventilation
        "trädgård": "num",  # Garden/landscaping
        "snöröjning": "num",  # Snow removal
        "sophämtning": "num",  # Garbage collection
        "övriga_driftkostnader": "num",  # Other operating costs (catchall)
        "total_driftkostnader": "num",  # Total operating costs
        "note_number": "str",  # Which note (e.g., "Not 4")
        "evidence_pages": "list",  # Page numbers where data found
    },
}


def get_comprehensive_types(agent_id: str) -> Dict[str, str]:
    """Get comprehensive types for an agent (includes base + expanded fields)."""
    return COMPREHENSIVE_TYPES.get(agent_id, {})


def schema_comprehensive_prompt_block(agent_id: str) -> str:
    """
    Generate prompt block for comprehensive extraction.
    Emphasizes extracting ALL available information, not just base schema fields.
    """
    t = get_comprehensive_types(agent_id)
    if not t:
        return ""

    # Render as key:type pairs
    pairs = ", ".join([f"{k}:{v}" for k, v in t.items()])

    guidance = (
        "COMPREHENSIVE EXTRACTION MODE: Extract ALL information available in the document. "
        "This schema includes both REQUIRED base fields and OPTIONAL comprehensive details. "
        "\n\n"
        "RULES:\n"
        "1. REQUIRED fields (from base schema): Extract if visible in provided pages\n"
        "2. COMPREHENSIVE fields (expanded details): Extract if available, use null if not found\n"
        "3. NEVER invent data - if not in document, use null or []\n"
        "4. For lists/dicts: Capture ALL instances, not just first\n"
        "5. Always include evidence_pages with 1-based page numbers\n"
        "6. For financial breakdowns: Extract complete line items from notes tables\n"
        "7. For suppliers/contracts: Extract complete list with all details\n"
        "8. For apartment breakdown: Extract full distribution (1 rok, 2 rok, 3 rok, etc.)\n"
        "\n"
        "If you find additional structured information not in this schema, "
        "add a top-level key 'additional_facts' with a list of discovered facts."
    )

    # Add agent-specific instructions
    if agent_id == "governance_agent":
        governance_instruction = (
            "\n\n"
            "**CRITICAL GOVERNANCE INSTRUCTION:**\n"
            "board_members MUST be structured format: [{\"name\": \"Full Name\", \"role\": \"role_type\"}]\n"
            "role_type options: \"Ordförande\" (chairman), \"Ledamot\" (member), \"Suppleant\" (deputy), \"Revisor\" (auditor)\n"
            "Extract ALL board members including deputies (Suppleanter). Do NOT use simple string list.\n"
            "\n"
            "Example:\n"
            "board_members: [\n"
            "  {\"name\": \"Elvy Maria Löfvenberg\", \"role\": \"Ordförande\"},\n"
            "  {\"name\": \"Torbjörn Andersson\", \"role\": \"Ledamot\"},\n"
            "  {\"name\": \"Lisa Lind\", \"role\": \"Suppleant\"},\n"
            "  {\"name\": \"Daniel Wetter\", \"role\": \"Suppleant\"}\n"
            "]"
        )
        guidance += governance_instruction

    if agent_id == "loans_agent":
        loans_instruction = (
            "\n\n"
            "**CRITICAL LOANS INSTRUCTION:**\n"
            "loans MUST be structured format: [{\"lender\": \"Bank Name\", \"loan_number\": \"Number\", \"outstanding_balance\": amount, \"interest_rate\": rate, \"maturity_date\": \"YYYY-MM-DD\", \"amortization_schedule\": \"Description\"}]\n"
            "Extract ALL individual loans from Note 5 (Låneskulder till kreditinstitut). Return a list of loan objects.\n"
            "Do NOT return single total - extract each loan separately with all available details.\n"
            "\n"
            "Example:\n"
            "loans: [\n"
            "  {\"lender\": \"SEB\", \"loan_number\": \"41431520\", \"outstanding_balance\": 30000000, \"interest_rate\": 0.0057, \"maturity_date\": \"2024-09-28\", \"amortization_schedule\": \"amorteringsfria\"},\n"
            "  {\"lender\": \"SBAB\", \"loan_number\": \"12345\", \"outstanding_balance\": 28500000, \"interest_rate\": 0.0045, \"maturity_date\": \"2022-03-23\", \"amortization_schedule\": \"amorteringsfria\"}\n"
            "]\n"
            "Also include: outstanding_loans (total), interest_rate (average), amortization (if applicable)\n"
        )
        guidance += loans_instruction

    if agent_id == "financial_agent":
        financial_instruction = (
            "\n\n"
            "**CRITICAL FINANCIAL INSTRUCTION:**\n"
            "Extract liabilities breakdown from Balance Sheet (Balansräkning):\n"
            "- liabilities: Total liabilities (Summa skulder och eget kapital)\n"
            "- long_term_liabilities: Långfristiga skulder (typically from Note 5: Loans)\n"
            "- short_term_liabilities: Kortfristiga skulder\n"
            "\n"
            "Swedish terms to look for:\n"
            "- \"Långfristiga skulder\" = long-term liabilities\n"
            "- \"Kortfristiga skulder\" = short-term liabilities\n"
            "- \"Låneskulder till kreditinstitut\" = loans (usually long-term)\n"
            "\n"
            "Example:\n"
            "{\n"
            "  \"liabilities\": 119617000,\n"
            "  \"long_term_liabilities\": 114480000,\n"
            "  \"short_term_liabilities\": 5137000\n"
            "}\n"
        )
        guidance += financial_instruction

    return f"COMPREHENSIVE SCHEMA: {{{pairs}}}\n\n{guidance}"


# Helper function to get field count statistics
def get_field_counts() -> Dict[str, Dict[str, int]]:
    """Return field counts for base vs comprehensive schema."""
    stats = {}
    for agent_id in COMPREHENSIVE_TYPES.keys():
        base_count = len(BASE_TYPES.get(agent_id, {}))
        comprehensive_count = len(COMPREHENSIVE_TYPES[agent_id])
        stats[agent_id] = {
            "base_fields": base_count,
            "comprehensive_fields": comprehensive_count,
            "added_fields": comprehensive_count - base_count
        }
    return stats


# Print schema expansion statistics when imported
if __name__ == "__main__":
    print("Schema Expansion Statistics:")
    print("-" * 60)
    stats = get_field_counts()
    total_base = 0
    total_comprehensive = 0
    for agent_id, counts in stats.items():
        total_base += counts["base_fields"]
        total_comprehensive += counts["comprehensive_fields"]
        print(f"{agent_id:30} {counts['base_fields']:2d} → {counts['comprehensive_fields']:2d} (+{counts['added_fields']:2d})")
    print("-" * 60)
    print(f"{'TOTAL':30} {total_base:2d} → {total_comprehensive:2d} (+{total_comprehensive - total_base:2d})")
    print(f"\nExpansion: {((total_comprehensive / total_base - 1) * 100):.1f}% more fields")
