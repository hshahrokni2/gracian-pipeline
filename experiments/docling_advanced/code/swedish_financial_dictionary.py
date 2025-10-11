#!/usr/bin/env python3
"""
Swedish Financial Dictionary - Component 5

Purpose: Map Swedish BRF terminology to canonical field names with intelligent matching:
- Swedish character normalization (å/a, ä/a, ö/o)
- Fuzzy matching for OCR errors
- Context-aware term resolution
- Unit detection and conversion (tkr → kr)
- High-performance caching
"""

import os
import re
import yaml
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class TermMatch:
    """Result of term matching"""
    canonical_term: str
    english_field: str
    category: str
    confidence: float  # 0.0-1.0
    match_type: str  # exact, normalized, fuzzy, synonym
    context: List[str]


@dataclass
class UnitConversion:
    """Result of unit detection and conversion"""
    value: float
    original_unit: str
    converted_value: float  # Always in kr
    multiplier: int


class SwedishFinancialDictionary:
    """
    Intelligent Swedish financial term dictionary with:
    - Multi-level synonym mapping
    - Swedish character normalization
    - Fuzzy matching for OCR errors
    - Context-aware resolution
    - Unit detection & conversion
    """

    def __init__(self, config_path: str = "config/swedish_financial_terms.yaml"):
        """
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Build fast lookup indexes
        self._build_indexes()

        # Match cache for performance
        self._match_cache: Dict[str, TermMatch] = {}
        self._unit_cache: Dict[str, UnitConversion] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _build_indexes(self):
        """Build fast lookup indexes for matching"""
        self.canonical_to_field: Dict[str, Tuple[str, str]] = {}  # canonical → (category, field)
        self.synonym_to_field: Dict[str, Tuple[str, str]] = {}   # synonym → (category, field)
        self.normalized_to_canonical: Dict[str, str] = {}        # normalized → canonical

        # Index all terms
        for category in ['balance_sheet', 'income_statement', 'notes', 'governance', 'property']:
            if category not in self.config:
                continue

            for field, data in self.config[category].items():
                canonical = data['canonical']
                english = data['english']

                # Index canonical term
                self.canonical_to_field[canonical] = (category, english)
                self.canonical_to_field[self.normalize_swedish(canonical)] = (category, english)

                # Index synonyms
                for synonym in data.get('synonyms', []):
                    self.synonym_to_field[synonym] = (category, english)
                    self.synonym_to_field[self.normalize_swedish(synonym)] = (category, english)

                    # Build normalization map
                    self.normalized_to_canonical[self.normalize_swedish(synonym)] = canonical

        # Index section header patterns (for section-level routing)
        if 'special_patterns' in self.config and 'section_headers' in self.config['special_patterns']:
            for category, patterns in self.config['special_patterns']['section_headers'].items():
                for pattern in patterns:
                    # Map section header to category (use category name as "field" for section headers)
                    self.synonym_to_field[pattern] = (category, f"{category}_section")
                    self.synonym_to_field[self.normalize_swedish(pattern)] = (category, f"{category}_section")
                    self.normalized_to_canonical[self.normalize_swedish(pattern)] = pattern

    @staticmethod
    def normalize_swedish(text: str) -> str:
        """
        Normalize Swedish text for matching:
        - Remove diacritics (å→a, ä→a, ö→o)
        - Lowercase
        - Strip whitespace
        - Remove special characters

        Examples:
            "Tillgångar" → "tillgangar"
            "Årets Resultat" → "arets resultat"
            "Eget Kapital" → "eget kapital"
        """
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Remove diacritics (å→a, ä→a, ö→o)
        # NFD = Canonical Decomposition (separate base char + diacritic)
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Strip extra whitespace
        text = ' '.join(text.split())

        return text

    def fuzzy_match_score(self, term1: str, term2: str) -> float:
        """
        Calculate fuzzy match score using Levenshtein-based similarity.

        Returns:
            Similarity score 0.0-1.0
        """
        # Normalize both terms
        norm1 = self.normalize_swedish(term1)
        norm2 = self.normalize_swedish(term2)

        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def match_term(
        self,
        term: str,
        context: Optional[str] = None,
        fuzzy_threshold: float = 0.85
    ) -> Optional[TermMatch]:
        """
        Match Swedish term to canonical field with intelligent matching.

        Args:
            term: Swedish term to match (e.g., "Tillgångar", "Summa skulder")
            context: Optional context (e.g., "balansräkning", "not 8")
            fuzzy_threshold: Minimum similarity for fuzzy matching (0.0-1.0)

        Returns:
            TermMatch object with canonical term, English field, and confidence

        Examples:
            match_term("Tillgångar") → assets, confidence=1.0
            match_term("Tillgangar") → assets, confidence=0.95 (normalized)
            match_term("Tillganager") → assets, confidence=0.85 (fuzzy)
        """
        # Check cache
        cache_key = f"{term}|{context or ''}"
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        # Normalize term
        normalized_term = self.normalize_swedish(term)

        # 1. Try exact canonical match
        if term in self.canonical_to_field:
            category, english = self.canonical_to_field[term]
            match = TermMatch(
                canonical_term=term,
                english_field=english,
                category=category,
                confidence=1.0,
                match_type="exact",
                context=self._get_context(category, english)
            )
            self._match_cache[cache_key] = match
            return match

        # 2. Try normalized canonical match
        if normalized_term in self.canonical_to_field:
            category, english = self.canonical_to_field[normalized_term]
            canonical = self.normalized_to_canonical.get(normalized_term, normalized_term)
            match = TermMatch(
                canonical_term=canonical,
                english_field=english,
                category=category,
                confidence=0.95,
                match_type="normalized",
                context=self._get_context(category, english)
            )
            self._match_cache[cache_key] = match
            return match

        # 3. Try exact synonym match
        if term in self.synonym_to_field:
            category, english = self.synonym_to_field[term]
            canonical = self._get_canonical_term(category, english)
            match = TermMatch(
                canonical_term=canonical,
                english_field=english,
                category=category,
                confidence=0.98,
                match_type="synonym",
                context=self._get_context(category, english)
            )
            self._match_cache[cache_key] = match
            return match

        # 4. Try normalized synonym match
        if normalized_term in self.synonym_to_field:
            category, english = self.synonym_to_field[normalized_term]
            canonical = self._get_canonical_term(category, english)
            match = TermMatch(
                canonical_term=canonical,
                english_field=english,
                category=category,
                confidence=0.93,
                match_type="synonym_normalized",
                context=self._get_context(category, english)
            )
            self._match_cache[cache_key] = match
            return match

        # 5. Try fuzzy matching (OCR errors)
        best_match = None
        best_score = 0.0

        # Check against all canonical terms
        for canonical, (category, english) in self.canonical_to_field.items():
            score = self.fuzzy_match_score(term, canonical)
            if score >= fuzzy_threshold and score > best_score:
                best_score = score
                best_match = TermMatch(
                    canonical_term=canonical,
                    english_field=english,
                    category=category,
                    confidence=score * 0.9,  # Reduce confidence for fuzzy matches
                    match_type="fuzzy",
                    context=self._get_context(category, english)
                )

        # Check against synonyms
        for synonym, (category, english) in self.synonym_to_field.items():
            score = self.fuzzy_match_score(term, synonym)
            if score >= fuzzy_threshold and score > best_score:
                best_score = score
                canonical = self._get_canonical_term(category, english)
                best_match = TermMatch(
                    canonical_term=canonical,
                    english_field=english,
                    category=category,
                    confidence=score * 0.85,  # Lower confidence for fuzzy synonym
                    match_type="fuzzy_synonym",
                    context=self._get_context(category, english)
                )

        if best_match:
            self._match_cache[cache_key] = best_match
            return best_match

        # No match found
        return None

    def detect_unit(self, text: str) -> Optional[UnitConversion]:
        """
        Detect unit in text and return conversion info.

        Args:
            text: Text containing value and unit (e.g., "1 234 tkr", "2,5 mkr")

        Returns:
            UnitConversion object with value and converted amount

        Examples:
            detect_unit("1 234 tkr") → 1234.0, tkr, 1234000.0 kr
            detect_unit("2,5 mkr") → 2.5, mkr, 2500000.0 kr
            detect_unit("500 kr") → 500.0, kr, 500.0 kr
        """
        # Check cache
        if text in self._unit_cache:
            return self._unit_cache[text]

        if 'units' not in self.config:
            return None

        # Pattern: number + optional unit
        # Swedish format: "1 234,56" or "1234,56" or "1 234"
        pattern = r'([\d\s]+(?:,\d+)?)\s*([a-zåäö]+)?'
        match = re.search(pattern, text.lower())

        if not match:
            return None

        value_str, unit_str = match.groups()

        # Parse Swedish number format
        # Remove spaces, replace comma with dot
        value_str = value_str.replace(' ', '').replace(',', '.')
        try:
            value = float(value_str)
        except ValueError:
            return None

        # Default to kr if no unit specified
        if not unit_str:
            unit_str = 'kr'

        # Find unit multiplier
        multiplier = 1
        canonical_unit = unit_str

        for unit_type, unit_data in self.config['units'].items():
            if unit_str in unit_data['synonyms'] or unit_str == unit_data['canonical']:
                multiplier = unit_data['multiplier']
                canonical_unit = unit_data['canonical']
                break

        conversion = UnitConversion(
            value=value,
            original_unit=canonical_unit,
            converted_value=value * multiplier,
            multiplier=multiplier
        )

        self._unit_cache[text] = conversion
        return conversion

    def _get_canonical_term(self, category: str, english_field: str) -> str:
        """Get canonical Swedish term for a field"""
        if category in self.config and english_field in self.config[category]:
            for field, data in self.config[category].items():
                if data['english'] == english_field:
                    return data['canonical']
        return english_field

    def _get_context(self, category: str, english_field: str) -> List[str]:
        """Get context list for a field"""
        if category in self.config:
            for field, data in self.config[category].items():
                if data['english'] == english_field:
                    return data.get('context', [])
        return []

    def get_category_terms(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all terms in a category.

        Args:
            category: One of: balance_sheet, income_statement, notes, governance, property

        Returns:
            List of term dictionaries with canonical, english, synonyms
        """
        if category not in self.config:
            return []

        terms = []
        for field, data in self.config[category].items():
            terms.append({
                'field': field,
                'canonical': data['canonical'],
                'english': data['english'],
                'synonyms': data.get('synonyms', []),
                'context': data.get('context', [])
            })

        return terms

    def get_statistics(self) -> Dict[str, Any]:
        """Get dictionary statistics"""
        stats = {
            'version': self.config.get('version', 'unknown'),
            'updated': self.config.get('updated', 'unknown'),
            'categories': {},
            'total_terms': 0,
            'total_synonyms': 0,
            'cache_hits': len(self._match_cache),
            'cache_size': len(self._match_cache) + len(self._unit_cache)
        }

        for category in ['balance_sheet', 'income_statement', 'notes', 'governance', 'property']:
            if category in self.config:
                terms = self.config[category]
                synonym_count = sum(len(data.get('synonyms', [])) for data in terms.values())

                stats['categories'][category] = {
                    'terms': len(terms),
                    'synonyms': synonym_count
                }

                stats['total_terms'] += len(terms)
                stats['total_synonyms'] += synonym_count

        return stats


def main():
    """Test Swedish Financial Dictionary"""
    print("=" * 80)
    print("SWEDISH FINANCIAL DICTIONARY - Component 5 Test")
    print("=" * 80)
    print()

    # Initialize dictionary
    config_path = Path(__file__).parent.parent / "config" / "swedish_financial_terms.yaml"
    dictionary = SwedishFinancialDictionary(str(config_path))

    # Print statistics
    stats = dictionary.get_statistics()
    print("📊 DICTIONARY STATISTICS:")
    print(f"   Version: {stats['version']}")
    print(f"   Updated: {stats['updated']}")
    print(f"   Total Terms: {stats['total_terms']}")
    print(f"   Total Synonyms: {stats['total_synonyms']}")
    print()

    print("📚 TERMS BY CATEGORY:")
    for category, data in stats['categories'].items():
        print(f"   • {category}: {data['terms']} terms, {data['synonyms']} synonyms")
    print()

    # Test matching
    print("🔍 TERM MATCHING TESTS:")
    print()

    test_terms = [
        # Exact matches
        ("tillgångar", None, "Exact canonical"),
        ("skulder", None, "Exact canonical"),

        # Normalized matches (no Swedish chars)
        ("Tillgangar", None, "Normalized (no å)"),
        ("Eget Kapital", None, "Normalized (no å, ä, ö)"),

        # Synonym matches
        ("summa tillgångar", None, "Synonym"),
        ("balansomslutning", None, "Synonym"),

        # Fuzzy matches (OCR errors)
        ("Tillganager", None, "Fuzzy (OCR error)"),
        ("skuldder", None, "Fuzzy (typo)"),

        # Unit detection
        ("1 234 tkr", None, "Unit: thousands"),
        ("2,5 mkr", None, "Unit: millions"),
        ("500 kr", None, "Unit: kronor"),
    ]

    for term, context, description in test_terms:
        # Try term matching
        match = dictionary.match_term(term, context)

        if match:
            print(f"✅ '{term}' ({description}):")
            print(f"   → {match.english_field} (canonical: {match.canonical_term})")
            print(f"   → Confidence: {match.confidence:.2f}, Type: {match.match_type}")
        else:
            # Try unit detection
            unit = dictionary.detect_unit(term)
            if unit:
                print(f"✅ '{term}' ({description}):")
                print(f"   → Value: {unit.value}, Unit: {unit.original_unit}")
                print(f"   → Converted: {unit.converted_value:,.0f} kr (×{unit.multiplier})")
            else:
                print(f"❌ '{term}' ({description}): No match")

        print()

    print("=" * 80)
    print("✅ DICTIONARY TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
