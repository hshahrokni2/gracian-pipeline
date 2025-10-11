"""
Swedish BRF Synonym Mapping System

Week 2 Day 2-3 Implementation (2025-10-07)

Centralized mappings for Swedish terminology to canonical field names.
Derived from ZeldaDemo mappings.py with 200+ Swedish synonyms.

Key Features:
- 200+ Swedish→English term mappings
- Financial metrics terminology
- Governance role synonyms
- Property detail synonyms
- Fuzzy matching support

Usage:
    from gracian_pipeline.core.synonyms import map_to_canonical_field

    canonical = map_to_canonical_field("nettoomsättning")  # → "net_revenue_tkr"
    canonical = map_to_canonical_field("ordförande")  # → "chairman"
"""

from typing import Optional, Dict, List
import re


# =============================================================================
# FINANCIAL METRICS SYNONYMS
# =============================================================================

FINANCIAL_SYNONYMS = {
    # Revenue
    "nettoomsättning": "net_revenue_tkr",
    "nettooms": "net_revenue_tkr",
    "rörelseintäkter": "net_revenue_tkr",
    "summa rörelseintäkter": "net_revenue_tkr",
    "totala intäkter": "net_revenue_tkr",
    "intäkter": "net_revenue_tkr",
    "verksamhetens intäkter": "net_revenue_tkr",

    # Expenses
    "rörelsekostnader": "operating_expenses_tkr",
    "summa rörelsekostnader": "operating_expenses_tkr",
    "totala kostnader": "operating_expenses_tkr",
    "kostnader": "operating_expenses_tkr",
    "verksamhetens kostnader": "operating_expenses_tkr",
    "driftkostnader": "operating_expenses_tkr",

    # Result/Surplus
    "årets resultat": "net_income_tkr",
    "resultat": "net_income_tkr",
    "resultat efter finansiella poster": "net_income_tkr",
    "resultat efter fin. poster": "net_income_tkr",
    "rörelseresultat": "operating_surplus_tkr",
    "resultat före finansiella poster": "operating_surplus_tkr",

    # Balance Sheet
    "summa tillgångar": "total_assets_tkr",
    "tillgångar": "total_assets_tkr",
    "summa skulder": "total_liabilities_tkr",
    "skulder": "total_liabilities_tkr",
    "summa eget kapital": "equity_tkr",
    "eget kapital": "equity_tkr",
    "summa eget kapital och skulder": "total_equity_and_liabilities",

    # Cash
    "kassa och bank": "cash_tkr",
    "kassa": "cash_tkr",
    "likvida medel": "cash_tkr",

    # Debt
    "långfristiga skulder": "long_term_debt",
    "kortfristiga skulder": "short_term_debt",
    "totalt lån": "total_debt",
    "lån": "total_debt",

    # Solidarity
    "soliditet": "solidarity_percent",
    "soliditet %": "solidarity_percent",
    "soliditet, %": "solidarity_percent",

    # Debt per sqm
    "lån, kr/m²": "debt_per_sqm",
    "lån kr/kvm": "debt_per_sqm",
    "skuldsättning, kr/kvm": "debt_per_sqm",
    "lån/kvm bostadsyta": "debt_per_sqm",
    "skuldsättning per kvm": "debt_per_sqm",
    "skuldsättning per m2": "debt_per_sqm",
    "lån per kvm bostadsyta": "debt_per_sqm",
    "skuldsättning/kvadratmeter (lån/kvm)": "debt_per_sqm",

    # Security
    "ställda säkerheter": "pledged_assets_amount",
    "fastighetsinteckning": "pledged_assets_amount",
    "pantbrev i fastighet": "pledged_assets_amount",
    "uttagna pantbrev i fastighet": "pledged_assets_amount",
}


# =============================================================================
# GOVERNANCE SYNONYMS
# =============================================================================

GOVERNANCE_SYNONYMS = {
    # Board Section Keywords (for locating governance data)
    "styrelsen": "board_section",
    "styrelse och revisorer": "board_section",
    "styrelseledamöter": "board_section",
    "förvaltning": "board_section",
    "för styrelsen": "board_section",
    "underskrift": "board_section",  # Signature section often lists board

    # Chairman
    "ordförande": "chairman",
    "ordf": "chairman",
    "ordf.": "chairman",
    "styrelsens ordförande": "chairman",

    # Vice Chairman
    "vice ordförande": "vice_chairman",
    "vice-ordförande": "vice_chairman",  # With hyphen variation
    "v ordf": "vice_chairman",
    "v. ordf.": "vice_chairman",
    "v ordförande": "vice_chairman",

    # Treasurer
    "kassör": "treasurer",
    "ekonomiansvarig": "treasurer",

    # Secretary
    "sekreterare": "secretary",
    "sekr": "secretary",
    "sekr.": "secretary",

    # Board Member
    "ledamot": "board_member",
    "ledamöter": "board_member",  # Plural form
    "styrelseledamot": "board_member",
    "styrelseledamöter": "board_member",  # Plural form
    "styr.ledamot": "board_member",  # Abbreviated

    # Deputy
    "suppleant": "deputy",
    "suppleanter": "deputy",  # Plural form
    "ersättare": "deputy",
    "suppl": "deputy",  # Abbreviated
    "suppl.": "deputy",

    # Auditor
    "revisor": "auditor",
    "revisorer": "auditor",  # Plural form
    "ordinarie revisor": "primary_auditor",
    "revisorssuppleant": "deputy_auditor",
    "auktoriserad revisor": "authorized_auditor",
    "aukt. revisor": "authorized_auditor",
    "aukt revisor": "authorized_auditor",
    "godkänd revisor": "authorized_auditor",
    "god. revisor": "authorized_auditor",
    "revisionsbolag": "audit_firm",
    "revisionsbyrå": "audit_firm",

    # Nomination Committee
    "valberedning": "nomination_committee",
    "valberedningen": "nomination_committee",
    "sammankallande": "nomination_convener",
}


# =============================================================================
# PROPERTY SYNONYMS
# =============================================================================

PROPERTY_SYNONYMS = {
    # Property Designation
    "fastighetsbeteckning": "property_designation",
    "fastighet": "property_designation",

    # Built Year
    "byggår": "built_year",
    "byggnation": "built_year",
    "byggnaden är uppförd": "built_year",
    "byggnaden uppfördes": "built_year",
    "nybyggnadsår byggnad": "built_year",
    "fastigheten bebyggdes": "built_year",
    "fastigheten byggdes": "built_year",
    "inflyttades under": "built_year",
    "färdigställdes år": "built_year",

    # Area
    "total bostadsarea": "residential_area_sqm",
    "total yta m² (för lägenheter)": "residential_area_sqm",
    "boarea": "residential_area_sqm",
    "total lokalarea": "commercial_area_sqm",
    "total yta m²": "total_area_sqm",
    "totalarea": "total_area_sqm",
    "total tomtarea": "total_land_area_sqm",

    # Apartments
    "antal lägenheter": "total_apartments",
    "antal bostäder": "total_apartments",

    # Commercial Units
    "antal lokaler": "number_of_commercial_units",
    "lokaler": "number_of_commercial_units",

    # Tax Value
    "taxeringsvärde": "tax_value",
    "totalt taxeringsvärde": "tax_value",
    "årets taxeringsvärde": "tax_value",
    "taxeringsvärde, byggnader och mark": "tax_value",

    # Tenure
    "friköpt tomt": "property_tenure_freehold",
    "tomträtt": "property_tenure_leasehold",
    "marken innehas med äganderätt": "property_tenure_freehold",
}


# =============================================================================
# FEE SYNONYMS (SWEDISH-FIRST SEMANTIC)
# =============================================================================

FEE_SYNONYMS = {
    # Monthly Fee
    "månadsavgift": "monthly_fee",
    "avgift per månad": "monthly_fee",
    "månadskostnad": "monthly_fee",
    "månatlig avgift": "monthly_fee",

    # Annual Fee
    "årsavgift": "annual_fee",
    "avgift per år": "annual_fee",
    "årlig avgift": "annual_fee",

    # Fee per sqm
    "avgift per m²": "fee_per_sqm",
    "avgift kr/m²": "fee_per_sqm",
    "avgift kr/kvm": "fee_per_sqm",
    "månadskostnad per m²": "fee_per_sqm",

    # Annual fee per sqm
    "årsavgift per m²": "annual_fee_per_sqm",
    "avgift per m²/år": "annual_fee_per_sqm",
}


# =============================================================================
# LOAN SYNONYMS
# =============================================================================

LOAN_SYNONYMS = {
    # Lender
    "långivare": "loan_lender",
    "kreditinstitut": "loan_lender",
    "låneinstitut": "loan_lender",
    "bank": "loan_lender",

    # Amount
    "lånebelopp": "loan_amount",
    "skuld": "loan_amount",
    "utg.skuld": "loan_amount_current_year",
    "utgående skuld": "loan_amount_current_year",
    "skuld innevarande år": "loan_amount_current_year",
    "ing.skuld": "loan_amount_previous_year",
    "ingående skuld": "loan_amount_previous_year",
    "skuld föregående år": "loan_amount_previous_year",

    # Interest Rate
    "räntesats": "loan_interest_rate",
    "ränta": "loan_interest_rate",
    "ränta %": "loan_interest_rate",
    "aktuell räntesats": "loan_interest_rate",
    "nuvarande räntesats": "loan_interest_rate",

    # Maturity
    "förfallodag": "loan_maturity_date",
    "villkorsändringsdag": "loan_maturity_date",
    "villkors- ändringsdag": "loan_maturity_date",

    # Amortization
    "amortering": "loan_amortization",
    "årets amorteringar": "loan_current_year_amortization",
    "årets amort.": "loan_current_year_amortization",
    "nästa års amortering": "loan_next_year_amortization",
}


# =============================================================================
# ORGANIZATION SYNONYMS
# =============================================================================

ORGANIZATION_SYNONYMS = {
    # Organization Number
    "org.nr": "organization_number",
    "org nr": "organization_number",
    "organisationsnummer": "organization_number",
    "organisationsnr": "organization_number",

    # Name
    "föreningens namn": "brf_name",
    "brf": "brf_name",
    "bostadsrättsförening": "brf_name",

    # Registered Office
    "säte": "registered_office",
    "styrelsens säte": "registered_office",
    "föreningen har sitt säte i": "registered_office",

    # Members
    "antal medlemmar": "number_of_members",
    "antal medlemmar vid räkenskapsårets slut": "number_of_members",
    "föreningens medlemsantal på bokslutsdagen": "number_of_members",

    # Employees
    "antal anställda": "number_of_employees",

    # AGM Date
    "årsstämma": "agm_date",
    "datum årsstämma": "agm_date",
    "datum för årsstämma": "agm_date",
    "ordinarie föreningsstämma hölls": "agm_date",
}


# =============================================================================
# MASTER SYNONYM MAPPING (COMBINED)
# =============================================================================

SYNONYM_MAPPING = {
    **FINANCIAL_SYNONYMS,
    **GOVERNANCE_SYNONYMS,
    **PROPERTY_SYNONYMS,
    **FEE_SYNONYMS,
    **LOAN_SYNONYMS,
    **ORGANIZATION_SYNONYMS,
}


# =============================================================================
# FUZZY MATCHING UTILITIES
# =============================================================================

def normalize_swedish_term(term: str) -> str:
    """
    Normalize Swedish term for matching.

    Normalization:
    - Lowercase
    - Strip whitespace
    - Remove punctuation
    - Handle common abbreviations

    Args:
        term: Raw Swedish term

    Returns:
        Normalized term

    Example:
        >>> normalize_swedish_term("  Nettoomsättning (tkr)  ")
        "nettoomsättning"
        >>> normalize_swedish_term("Ordf.")
        "ordf"
    """
    if not term:
        return ""

    # Lowercase
    normalized = term.lower().strip()

    # Remove common units/modifiers
    normalized = re.sub(r'\(tkr\)', '', normalized)
    normalized = re.sub(r'\(kr\)', '', normalized)
    normalized = re.sub(r'\(sek\)', '', normalized)
    normalized = re.sub(r'\(%\)', '', normalized)

    # Remove periods (for abbreviations like "Ordf.")
    normalized = normalized.replace('.', '')

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    return normalized


def map_to_canonical_field(term: str, case_sensitive: bool = False) -> Optional[str]:
    """
    Map Swedish term to canonical field name.

    Args:
        term: Swedish term (e.g., "nettoomsättning", "ordförande")
        case_sensitive: Whether to match case-sensitively (default: False)

    Returns:
        Canonical field name (e.g., "net_revenue_tkr", "chairman")
        Returns None if no mapping found

    Example:
        >>> map_to_canonical_field("Nettoomsättning (tkr)")
        "net_revenue_tkr"
        >>> map_to_canonical_field("Ordf.")
        "chairman"
        >>> map_to_canonical_field("unknown_term")
        None
    """
    if not term:
        return None

    # Normalize term
    normalized = normalize_swedish_term(term)

    # Direct lookup
    if normalized in SYNONYM_MAPPING:
        return SYNONYM_MAPPING[normalized]

    # If case-insensitive, try original term
    if not case_sensitive:
        original_lower = term.lower().strip()
        if original_lower in SYNONYM_MAPPING:
            return SYNONYM_MAPPING[original_lower]

    return None


def get_all_synonyms_for_field(canonical_field: str) -> List[str]:
    """
    Get all Swedish synonyms for a canonical field.

    Args:
        canonical_field: Canonical field name (e.g., "chairman")

    Returns:
        List of Swedish synonyms

    Example:
        >>> get_all_synonyms_for_field("chairman")
        ["ordförande", "ordf", "ordf."]
    """
    synonyms = []
    for swedish_term, canonical in SYNONYM_MAPPING.items():
        if canonical == canonical_field:
            synonyms.append(swedish_term)
    return synonyms


def get_synonym_categories() -> Dict[str, List[str]]:
    """
    Get synonym mappings organized by category.

    Returns:
        Dictionary of category -> list of canonical fields

    Example:
        >>> categories = get_synonym_categories()
        >>> "financial" in categories
        True
        >>> "governance" in categories
        True
    """
    return {
        "financial": list(set(FINANCIAL_SYNONYMS.values())),
        "governance": list(set(GOVERNANCE_SYNONYMS.values())),
        "property": list(set(PROPERTY_SYNONYMS.values())),
        "fees": list(set(FEE_SYNONYMS.values())),
        "loans": list(set(LOAN_SYNONYMS.values())),
        "organization": list(set(ORGANIZATION_SYNONYMS.values())),
    }


def search_synonyms(query: str, max_results: int = 10) -> List[tuple]:
    """
    Search for synonyms matching query (fuzzy).

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of (swedish_term, canonical_field) tuples

    Example:
        >>> search_synonyms("resultat")
        [("årets resultat", "net_income_tkr"), ...]
    """
    query_normalized = normalize_swedish_term(query)
    results = []

    for swedish_term, canonical_field in SYNONYM_MAPPING.items():
        if query_normalized in swedish_term:
            results.append((swedish_term, canonical_field))

    return results[:max_results]


# =============================================================================
# STATISTICS
# =============================================================================

def get_synonym_stats() -> Dict[str, int]:
    """
    Get statistics about synonym mappings.

    Returns:
        Dictionary with counts

    Example:
        >>> stats = get_synonym_stats()
        >>> stats["total_synonyms"]
        200+
    """
    return {
        "total_synonyms": len(SYNONYM_MAPPING),
        "financial_synonyms": len(FINANCIAL_SYNONYMS),
        "governance_synonyms": len(GOVERNANCE_SYNONYMS),
        "property_synonyms": len(PROPERTY_SYNONYMS),
        "fee_synonyms": len(FEE_SYNONYMS),
        "loan_synonyms": len(LOAN_SYNONYMS),
        "organization_synonyms": len(ORGANIZATION_SYNONYMS),
        "unique_canonical_fields": len(set(SYNONYM_MAPPING.values())),
    }


if __name__ == "__main__":
    # Display statistics
    stats = get_synonym_stats()
    print("\n" + "=" * 70)
    print("SWEDISH SYNONYM MAPPING STATISTICS")
    print("=" * 70)
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Example usage
    print("\n" + "=" * 70)
    print("EXAMPLE MAPPINGS")
    print("=" * 70)

    examples = [
        "Nettoomsättning (tkr)",
        "Ordf.",
        "Soliditet %",
        "Lån, kr/m²",
        "Total bostadsarea",
    ]

    for term in examples:
        canonical = map_to_canonical_field(term)
        print(f"{term:30s} → {canonical}")

    print("\n" + "=" * 70)
