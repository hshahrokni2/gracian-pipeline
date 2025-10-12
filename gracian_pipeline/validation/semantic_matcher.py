"""
Semantic Field Matcher - Finds fields by meaning rather than exact path.

This module enables validation to work with heterogeneous PDFs by matching fields
through semantic equivalence instead of requiring exact structural alignment.

Key Features:
- Synonym-based matching (100+ field variations)
- Fuzzy string matching (handles typos, abbreviations)
- Swedish character normalization (å→a, ä→a, ö→o)
- Pattern-based matching for typed fields (org numbers, amounts, etc.)
- Confidence scoring for all matches
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Set
from difflib import SequenceMatcher
from dataclasses import dataclass


@dataclass
class FieldMatch:
    """Result of a semantic field search."""
    canonical_name: str
    value: Any
    confidence: float  # 0.0-1.0
    match_strategy: str  # "direct", "synonym", "fuzzy", "pattern"
    matched_path: str  # Actual path where value was found
    notes: str = ""


class SemanticFieldMatcher:
    """
    Finds fields by semantic meaning, not exact path.

    Handles heterogeneity via:
    1. Fuzzy path matching
    2. Synonym expansion
    3. Multiple search strategies
    4. Confidence scoring
    """

    def __init__(self):
        """Initialize with comprehensive synonym dictionary."""

        # Comprehensive synonym dictionary (100+ fields)
        self.field_synonyms = {
            # Metadata fields
            "organization_number": [
                "organization_number", "org_nr", "org.nr", "organisationsnummer",
                "orgnr", "reg_nr", "registreringsnummer", "org_number", "org-nr",
                "foreningsnummer", "registration_number"
            ],
            "brf_name": [
                "brf_name", "foreningsnamn", "föreningsnamn", "name", "foreningens_namn",
                "association_name", "bostadsrattsforeningens_namn", "brf", "br", "förening"
            ],
            "fiscal_year": [
                "fiscal_year", "rakenskapsår", "räkenskapsår", "year", "ar", "år",
                "verksamhetsår", "fiscal", "räkenskapsperiod", "period"
            ],

            # Governance fields
            "chairman": [
                "chairman", "ordförande", "ordforande", "ordf.", "ordf", "styrelseordförande",
                "styrelseordf", "chair", "vd", "styrelsens_ordförande", "ordforand"
            ],
            "board_members": [
                "board_members", "styrelseledamoter", "styrelseledamot", "ledamoter", "ledamöter",
                "board", "styrelse", "styrelsemedlemmar", "ledamot", "suppleanter", "suppleant"
            ],
            "auditor_name": [
                "auditor_name", "revisor", "auktoriserad_revisor", "revisorsnamn",
                "auditor", "auditors", "revisorns_namn", "huvudrevisor", "revisorerna"
            ],
            "audit_firm": [
                "audit_firm", "revisionsbyra", "revisionsbyrå", "byrå", "byra",
                "audit_company", "revision", "revisionsfirma", "granskande_firma"
            ],
            "nomination_committee": [
                "nomination_committee", "valberedning", "valberedningen", "nomineringskommitte",
                "nomination", "valbered", "val", "nominating_committee"
            ],

            # Financial fields - Income Statement
            "revenue": [
                "revenue", "intakter", "intakt", "inkomster", "inkomst", "revenues",
                "total_intakter", "summa_intakter", "sales", "income"
            ],
            "expenses": [
                "expenses", "kostnader", "utgifter", "kostnad", "utgift", "costs",
                "expense", "totala_kostnader", "summa_kostnader", "operating_costs"
            ],
            "surplus": [
                "surplus", "resultat", "arets_resultat", "årets_resultat", "överskott",
                "overskott", "profit", "net_result", "nettoresultat", "vinst"
            ],

            # Financial fields - Balance Sheet
            "assets": [
                "assets", "tillgangar", "tillgångar", "totala_tillgangar", "totala_tillgångar",
                "total_assets", "summa_tillgangar", "summa_tillgångar", "balansomslutning"
            ],
            "liabilities": [
                "liabilities", "skulder", "skuld", "total_skulder", "totala_skulder",
                "total_liabilities", "summa_skulder", "lån_och_skulder", "forpliktelser"
            ],
            "equity": [
                "equity", "eget_kapital", "kapital", "totalt_eget_kapital",
                "shareholders_equity", "foreningenskapital", "föreningens_kapital",
                "medlemskapital", "insatskapital"
            ],
            "cash": [
                "cash", "kassa", "kassamedel", "likvida_medel", "kontanter",
                "cash_equivalents", "bank", "banktillgodohavanden", "kassa_bank"
            ],

            # Property fields
            "property_designation": [
                "property_designation", "fastighetsbeteckning", "fastighet", "property",
                "beteckning", "fastighetens_beteckning", "property_name", "fastighetsnamn"
            ],
            "municipality": [
                "municipality", "kommun", "municipalities", "stad", "city",
                "location", "ort", "kommunnamn", "municipality_name"
            ],
            "address": [
                "address", "adress", "gata", "street", "postadress", "besoksadress",
                "besöksadress", "street_address", "postal_address", "gatuadress"
            ],
            "building_year": [
                "building_year", "byggnadsår", "byggår", "byggar", "construction_year",
                "byggnadsår", "arbyggd", "år_byggd", "built", "uppfört_år"
            ],
            "total_area": [
                "total_area", "total_yta", "yta", "area", "bostadsyta", "lokalyta",
                "total_sqm", "areal", "kvadratmeter", "total_area_sqm", "totala_ytan"
            ],

            # Apartment/Unit fields
            "number_of_apartments": [
                "number_of_apartments", "antal_lagenheter", "antal_lägenheter",
                "lagenheter", "lägenheter", "apartments", "units", "antal_bostader",
                "bostadsratter", "bostadsrätter", "total_apartments"
            ],
            "rooms_distribution": [
                "rooms_distribution", "rumsfordelning", "rumsfördelning", "rooms",
                "rumsdistribution", "lagenhetsstorlekar", "lägenhetsstorlekar",
                "apartment_sizes", "unit_mix", "fordelning"
            ],

            # Fee fields
            "monthly_fee": [
                "monthly_fee", "avgift", "månadsavgift", "manadsavgift", "manad",
                "monthly", "avg", "avgifter", "medlemsavgift", "hyra", "avgift_per_manad"
            ],
            "annual_fee": [
                "annual_fee", "arsavgift", "årsavgift", "annual", "ar", "år",
                "total_avgift", "avgift_per_ar", "avgift_per_år", "totala_avgifter"
            ],
            "fee_per_sqm": [
                "fee_per_sqm", "avgift_per_kvm", "avgift_per_m2", "avgift_per_kvadratmeter",
                "fee_sqm", "kr_per_kvm", "kr_per_m2", "avgift_kvadrat"
            ],

            # Loan fields
            "total_debt": [
                "total_debt", "skulder", "lan", "lån", "total_lan", "totala_lan",
                "totala_lån", "debt", "borrowing", "summa_skulder", "summa_lån"
            ],
            "lender_name": [
                "lender_name", "långivare", "langivare", "bank", "lender", "långivarens_namn",
                "kreditgivare", "banknamn", "lanegivare", "långiv", "långivare"
            ],
            "interest_rate": [
                "interest_rate", "ranta", "ränta", "rate", "rantesats", "räntesats",
                "interest", "procent", "%", "ranteniva", "räntenivå"
            ],
            "loan_amount": [
                "loan_amount", "lanbelopp", "lånebelopp", "amount", "belopp", "kapital",
                "principal", "lansum", "lånesumma", "ursprungligt_belopp"
            ],

            # Note fields
            "depreciation_schedule": [
                "depreciation_schedule", "avskrivningar", "avskrivning", "depreciation",
                "avskriv", "planenlig_avskrivning", "avskrivningsplan", "nedskrivningar"
            ],
            "maintenance_plan": [
                "maintenance_plan", "underhallsplan", "underhållsplan", "maintenance",
                "underhall", "underhåll", "reparationer", "repairs", "planerat_underhall"
            ],
            "tax_information": [
                "tax_information", "skatt", "skatter", "tax", "skatteinfo",
                "deklaration", "skattedeklaration", "beskattning", "taxering"
            ],

            # Operations fields
            "suppliers": [
                "suppliers", "leverantorer", "leverantor", "supplier", "lev",
                "leverantorsnamn", "leverantorsregister", "vendors", "tjansteleverantorer"
            ],
            "service_contracts": [
                "service_contracts", "avtal", "serviceavtal", "contracts", "kontrakt",
                "avtalsregister", "service", "underhallsavtal", "underhållsavtal"
            ],

            # Additional semantic variations
            "commercial_tenants": [
                "commercial_tenants", "lokalhyresgaster", "lokalhyresgäster", "kommersiella",
                "commercial", "hyresgaster", "hyresgäster", "tenant", "tenants", "lokaler"
            ],
            "common_areas": [
                "common_areas", "gemensamhetsutrymmen", "gemensamma_ytor", "common",
                "gemensam", "gemensamheter", "shared_spaces", "allmanningar", "allmänningar"
            ],

            # ========================================
            # ADDED 2025-10-10: Field name variations
            # discovered from validation analysis
            # ========================================

            # Building/Note 8 field variations
            "acquisition_value": [
                "opening_acquisition_value",
                "closing_acquisition_value",
                "anskaffningsvärde"
            ],
            "accumulated_depreciation": [
                "opening_depreciation",
                "closing_depreciation",
                "ackumulerad_avskrivning"
            ],
            "book_value": [
                "net_book_value",
                "carrying_amount",
                "bokfört_värde"
            ],
            "depreciation": [
                "depreciation_for_year",
                "årets_avskrivning"
            ],

            # Cash flow variations
            "liquid_assets": [
                "cash_and_bank",
                "cash_and_cash_equivalents",
                "likvida_medel",
                "kassa_och_bank"
            ],
            "liquid_assets_beginning": [
                "opening_liquid_assets",
                "beginning_of_year",
                "ingående_likvida_medel"
            ],
            "liquid_assets_end": [
                "closing_liquid_assets",
                "end_of_year",
                "utgående_likvida_medel"
            ],
            "change_in_liquid_assets": [
                "liquid_assets_change",
                "årets_förändring"
            ],

            # Governance variations
            "auditors": [
                "primary_auditor",
                "deputy_auditor",
                "audit_firm",
                "revisor",
                "revisorer"
            ],
            "primary_auditor": [
                "auditor_name",
                "ordinarie_revisor"
            ],
            "deputy_auditor": [
                "suppleant",
                "ersättare"
            ],
            "board_meetings_count": [
                "number_of_board_meetings",
                "antal_styrelsemöten"
            ],

            # Financial statement variations
            "operating_income": [
                "income_from_operations",
                "rörelseintäkter",
                "nettoomsättning"
            ],
            "operating_costs": [
                "operating_expenses",
                "rörelsekostnader"
            ],
            "financial_income": [
                "interest_income",
                "ränteintäkter",
                "finansiella_intäkter"
            ],
            "financial_costs": [
                "interest_costs",
                "räntekostnader",
                "finansiella_kostnader"
            ],

            # Property/Apartment variations
            "total_apartments": [
                "total_count",
                "number_of_apartments",
                "antal_lägenheter"
            ],
            "apartment_distribution": [
                "apartment_breakdown",
                "breakdown",
                "lägenhetsfördelning"
            ],
            "living_area_sqm": [
                "total_area_sqm",
                "boarea",
                "totalarea"
            ],

            # Fee variations (WITH per_sqm compounds - critical for validation!)
            "annual_fee_per_sqm": [
                "arsavgift_per_sqm_total",
                "arsavgift_per_sqm",
                "annual_fee_sqm",
                "avgift_per_kvm_ar",
                "yearly_fee_per_sqm"
            ],
            "monthly_fee_per_sqm": [
                "manadsavgift_per_sqm",
                "monthly_fee_sqm",
                "avgift_per_kvm_manad",
                "monthly_fee_per_m2"
            ],
            "monthly_fee_average": [
                "manadsavgift_per_apartment_avg",
                "average_monthly_fee",
                "genomsnittlig_månadsavgift"
            ],
            "annual_fee_average": [
                "arsavgift_per_apartment_avg",
                "average_annual_fee",
                "genomsnittlig_årsavgift"
            ],

            # Revenue and cost breakdown variations (critical for Note validation!)
            "revenue_breakdown": [
                "revenue_breakdown_2021",
                "revenue_breakdown_2020",
                "intaktsfordelning",
                "intakter_specifikation"
            ],
            "operating_costs": [
                "operating_costs_2021",
                "operating_costs_2020",
                "driftkostnader",
                "rörelsekostnader"
            ],
            "other_operating_income": [
                "other_operating_income_2021",
                "other_operating_income_2020",
                "ovriga_rorelsein täkter"
            ],

            # Multi-year data mappings
            "total_loans": [
                "total_loans_2021",
                "total_loans_2020",
                "totala_lan",
                "summa_skulder"
            ],

            # Note-specific variations
            "note_8_buildings": [
                "building_details",
                "buildings_and_land",
                "byggnader"
            ],
            "note_9_receivables": [
                "receivables_breakdown",
                "kortfristiga_fordringar"
            ],
            "note_5_financial_items": [
                "financial_income_and_costs",
                "finansiella_poster"
            ],
        }

        # Regex patterns for typed fields
        self.field_patterns = {
            "organization_number": r'\d{6}-\d{4}',  # Swedish org number format
            "fiscal_year": r'20\d{2}',  # Year format (2000-2099)
            "swedish_amount": r'[\d\s]+(?:kr|SEK|kronor|tkr)?',  # Swedish amounts
            "interest_rate": r'\d+[.,]\d+\s*%?',  # Interest rates
            "property_designation": r'[A-ZÅÄÖ][a-zåäö]+\s+\d+:\d+',  # Property format
        }

    def normalize_key(self, key: str) -> str:
        """
        Normalize a field name for comparison.

        Handles:
        - Swedish characters (å→a, ä→a, ö→o)
        - Case insensitivity
        - Special characters (underscore, hyphen, etc.)
        """
        # Convert to lowercase
        normalized = key.lower()

        # Remove underscores and hyphens
        normalized = normalized.replace('_', '').replace('-', '').replace('.', '')

        # Swedish character normalization
        swedish_map = {'å': 'a', 'ä': 'a', 'ö': 'o'}
        for sv, en in swedish_map.items():
            normalized = normalized.replace(sv, en)

        # Remove all non-alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', normalized)

        return normalized

    def _normalize_field_name_with_year(self, field_name: str) -> Tuple[str, Optional[str]]:
        """
        Extract year suffix from field name.

        Ground truth often has year suffixes like '_2021', '_2020', etc.
        Extraction typically doesn't (extracts current year only).

        Examples:
            "annual_fee_per_sqm_2021" → ("annual_fee_per_sqm", "2021")
            "acquisition_value_2020" → ("acquisition_value", "2020")
            "chairman" → ("chairman", None)

        Returns:
            Tuple[base_name, year_suffix]
        """
        year_pattern = r"_(\d{4})$"
        match = re.search(year_pattern, field_name)
        if match:
            year = match.group(1)
            base_name = field_name[:match.start()]
            return (base_name, year)
        return (field_name, None)

    def find_field(self, data: Dict, canonical_field_name: str) -> Tuple[Optional[Any], float]:
        """
        Find field value by semantic meaning. Returns (value, confidence).

        Searches using 4 strategies in order:
        1. Direct match (confidence = 1.0)
        2. Synonym match (confidence = 0.95)
        3. Fuzzy path matching (confidence = 0.8-0.9 based on similarity)
        4. Pattern-based search (confidence = 0.75)
        """
        # NEW: Strip year suffix from field name before searching
        base_field_name, year = self._normalize_field_name_with_year(canonical_field_name)

        # Build comprehensive search list: canonical field + all synonyms
        # This ensures we search ALL possible names in nested structures
        search_terms = [base_field_name]
        synonyms = self.field_synonyms.get(base_field_name, [])
        search_terms.extend(synonyms)

        # Strategy 1+2 COMBINED: Search for canonical field AND all synonyms in nested structure
        # This fixes the issue where nested fields weren't found even with synonyms defined
        for i, term in enumerate(search_terms):
            value, conf = self._search_nested_dict(data, term)
            if value is not None:
                # First term is canonical (confidence 1.0), rest are synonyms (confidence 0.95)
                confidence = 1.0 if i == 0 else 0.95
                return value, confidence

        # Strategy 3: Fuzzy path matching (fallback if no exact/synonym match)
        fuzzy_matches = self._fuzzy_path_search(data, base_field_name)
        if fuzzy_matches:
            best_match = max(fuzzy_matches, key=lambda x: x[1])
            if best_match[1] > 0.75:  # Threshold for fuzzy matches
                return best_match[0], best_match[1]

        # Strategy 4: Pattern-based (for typed fields)
        if base_field_name in self.field_patterns:
            pattern_match = self._pattern_search(data, self.field_patterns[base_field_name])
            if pattern_match:
                return pattern_match, 0.75

        return None, 0.0

    def _search_nested_dict(self, data: Dict, search_key: str, parent_path: str = "") -> Tuple[Optional[Any], float]:
        """
        Recursively search nested dictionary for a key.

        Returns (value, confidence) tuple.
        """
        normalized_search = self.normalize_key(search_key)

        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            normalized_key = self.normalize_key(key)

            # Direct match
            if normalized_key == normalized_search:
                return value, 1.0

            # Recursive search if value is dict
            if isinstance(value, dict):
                result, conf = self._search_nested_dict(value, search_key, current_path)
                if result is not None:
                    return result, conf

            # Search in lists of dicts
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result, conf = self._search_nested_dict(item, search_key, f"{current_path}[{i}]")
                        if result is not None:
                            return result, conf

        return None, 0.0

    def _fuzzy_path_search(self, data: Dict, canonical_name: str) -> List[Tuple[Any, float]]:
        """
        Search using fuzzy string matching on field paths.

        Returns list of (value, confidence_score) tuples.
        """
        matches = []
        normalized_canonical = self.normalize_key(canonical_name)

        def _traverse(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                normalized_key = self.normalize_key(key)

                # Calculate similarity
                similarity = SequenceMatcher(None, normalized_canonical, normalized_key).ratio()

                if similarity > 0.75:  # Threshold for fuzzy matching
                    confidence = min(0.9, similarity)  # Cap at 0.9 for fuzzy matches
                    matches.append((value, confidence))

                # Recursive search
                if isinstance(value, dict):
                    _traverse(value, current_path)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            _traverse(item, f"{current_path}[{i}]")

        _traverse(data)
        return matches

    def _pattern_search(self, data: Dict, pattern: str) -> Optional[Any]:
        """
        Search for values matching a regex pattern.

        Used for typed fields like organization numbers, dates, etc.
        """
        def _search_values(d: Dict) -> Optional[Any]:
            for key, value in d.items():
                # Check if value matches pattern
                if isinstance(value, str) and re.search(pattern, value):
                    return value

                # Recursive search
                if isinstance(value, dict):
                    result = _search_values(value)
                    if result:
                        return result
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result = _search_values(item)
                            if result:
                                return result
                        elif isinstance(item, str) and re.search(pattern, item):
                            return item
            return None

        return _search_values(data)

    def get_all_synonyms(self, canonical_name: str) -> List[str]:
        """Get all known synonyms for a canonical field name."""
        return self.field_synonyms.get(canonical_name, [canonical_name])

    def get_statistics(self) -> Dict[str, int]:
        """Get matcher statistics."""
        total_fields = len(self.field_synonyms)
        total_synonyms = sum(len(syns) for syns in self.field_synonyms.values())
        avg_synonyms = total_synonyms / total_fields if total_fields > 0 else 0

        return {
            "total_canonical_fields": total_fields,
            "total_synonyms": total_synonyms,
            "average_synonyms_per_field": round(avg_synonyms, 1),
            "pattern_definitions": len(self.field_patterns)
        }
