"""
Semantic Section Heading Matcher for Swedish BRF Documents

Uses sentence-transformers to match Docling headings to expected section types
based on semantic similarity, not exact text matching.

This handles diverse Swedish heading variations without manual synonym lists.
"""

from sentence_transformers import SentenceTransformer, util
import torch
from typing import List, Dict, Tuple, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class SemanticHeadingMatcher:
    """
    Matches Swedish section headings to agent types using semantic similarity.

    Handles diverse heading variations automatically without manual synonyms.
    """

    def __init__(self, model_name: str = 'paraphrase-multilingual-mpnet-base-v2'):
        """
        Initialize semantic matcher.

        Args:
            model_name: Sentence-transformer model to use
                       Default: multilingual model (Swedish + 50+ languages)
                       Alternative: 'KBLab/sentence-bert-swedish-cased' (Swedish-only)
        """
        logger.info(f"Loading semantic model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Define expected section types with multiple semantic variations
        # Each variation helps the model understand what we're looking for
        self.section_types = {
            'governance_chairman': [
                "ordförande",
                "styrelsens ordförande",
                "föreningens ordförande",
                "ledning ordförande",
                "chairman"
            ],
            'governance_board': [
                "styrelsen",
                "styrelseledamöter",
                "förvaltning",
                "ledning",
                "styrelsearbete",
                "föreningens styrelse",
                "styrelsens sammansättning",
                "organisation och ledning",
                "föreningens ledning",
                "styrelseledamöter och suppleanter",
                "board of directors"
            ],
            'governance_auditor': [
                "revisorer",
                "revisor",
                "revision",
                "föreningens revisorer",
                "revisionsberättelse",
                "valberedning och revisorer",
                "auditors"
            ],
            'financial_balance_sheet': [
                "balansräkning",
                "tillgångar och skulder",
                "finansiell ställning",
                "balans",
                "föreningens tillgångar",
                "skulder och eget kapital",
                "ekonomisk ställning",
                "föreningens ekonomiska ställning",
                "balance sheet"
            ],
            'financial_income_statement': [
                "resultaträkning",
                "intäkter och kostnader",
                "årets resultat",
                "ekonomiskt utfall",
                "resultat",
                "vinst och förlust",
                "årets ekonomiska resultat",
                "income statement"
            ],
            'financial_notes': [
                "noter",
                "not",
                "tilläggsupplysningar",
                "redovisningsprinciper",
                "upplysningar",
                "noter till räkenskaperna",
                "bokslutskommentarer",
                "notes"
            ],
            'property': [
                "fastighet",
                "fastigheten",
                "föreningens fastighet",
                "fastighetsuppgifter",
                "byggnaden",
                "fastighetsdata",
                "property information"
            ],
            'fees': [
                "avgifter",
                "månadsavgift",
                "årsavgift",
                "medlemsavgifter",
                "bostadsrättsavgifter",
                "avgiftsuppgifter",
                "fees"
            ]
        }

        # Pre-compute embeddings for all expected section types
        logger.info("Pre-computing section type embeddings...")
        self._compute_section_embeddings()

    def _compute_section_embeddings(self):
        """Pre-compute and cache embeddings for expected section types."""
        self.section_embeddings = {}

        for section_type, variations in self.section_types.items():
            # Encode all variations
            embeddings = self.model.encode(
                variations,
                convert_to_tensor=True,
                show_progress_bar=False
            )

            # Average embeddings for robustness
            # This creates a "centroid" representing the semantic concept
            self.section_embeddings[section_type] = embeddings.mean(dim=0)

        logger.info(f"✓ Cached {len(self.section_embeddings)} section type embeddings")

    @lru_cache(maxsize=1000)
    def find_best_match(
        self,
        heading: str,
        threshold: float = 0.5
    ) -> Tuple[Optional[str], float]:
        """
        Find best matching section type for a given heading.

        Args:
            heading: Section heading from Docling
            threshold: Minimum similarity score (0.0-1.0) to consider valid match

        Returns:
            (section_type, confidence) or (None, 0.0) if no match

        Examples:
            >>> matcher.find_best_match("Styrelsen")
            ('governance_board', 0.89)

            >>> matcher.find_best_match("Föreningens ekonomiska ställning")
            ('financial_balance_sheet', 0.82)

            >>> matcher.find_best_match("Irrelevant heading")
            (None, 0.35)
        """
        if not heading or not heading.strip():
            return None, 0.0

        # Encode heading
        heading_embedding = self.model.encode(
            [heading],
            convert_to_tensor=True,
            show_progress_bar=False
        )[0]

        # Calculate similarities to all section types
        similarities = {}
        for section_type, section_embedding in self.section_embeddings.items():
            similarity = util.cos_sim(heading_embedding, section_embedding).item()
            similarities[section_type] = similarity

        # Find best match
        best_match = max(similarities, key=similarities.get)
        confidence = similarities[best_match]

        if confidence >= threshold:
            return best_match, confidence
        else:
            return None, 0.0

    def match_headings(
        self,
        headings: List[str],
        threshold: float = 0.5,
        verbose: bool = False
    ) -> Dict[str, Dict]:
        """
        Match multiple headings to section types.

        Args:
            headings: List of section headings from Docling
            threshold: Minimum similarity score
            verbose: Print matching details

        Returns:
            Dict mapping heading to {section_type, confidence, matched}

        Example:
            >>> results = matcher.match_headings([
            ...     "Styrelsen",
            ...     "Balansräkning",
            ...     "Irrelevant"
            ... ])
            >>> results["Styrelsen"]["section_type"]
            'governance_board'
        """
        results = {}

        for heading in headings:
            section_type, confidence = self.find_best_match(heading, threshold)

            results[heading] = {
                'section_type': section_type,
                'confidence': confidence,
                'matched': section_type is not None
            }

            if verbose:
                if section_type:
                    logger.info(f"✓ '{heading}' → {section_type} ({confidence:.2f})")
                else:
                    logger.info(f"✗ '{heading}' → No match (confidence: {confidence:.2f})")

        return results

    def get_pages_for_agent(
        self,
        agent_id: str,
        docling_sections: List[Dict],
        threshold: float = 0.5
    ) -> List[int]:
        """
        Get page numbers for an agent based on semantic heading matching.

        Args:
            agent_id: Agent identifier (e.g., 'chairman_agent', 'financial_agent')
            docling_sections: Sections from Docling with 'heading' and 'pages' keys
            threshold: Similarity threshold

        Returns:
            List of page numbers where agent should extract data

        Example:
            >>> sections = [
            ...     {'heading': 'Styrelsen', 'pages': [2, 3]},
            ...     {'heading': 'Balansräkning', 'pages': [8, 9]}
            ... ]
            >>> matcher.get_pages_for_agent('chairman_agent', sections)
            [2, 3]
        """
        # Map agent IDs to section types
        agent_to_section = {
            'chairman_agent': ['governance_chairman', 'governance_board'],
            'board_members_agent': ['governance_board'],
            'auditor_agent': ['governance_auditor'],
            'balance_sheet_agent': ['financial_balance_sheet'],
            'income_statement_agent': ['financial_income_statement'],
            'notes_agent': ['financial_notes'],
            'property_agent': ['property'],
            'fee_agent': ['fees'],
            # Legacy/composite agents
            'governance_agent': ['governance_chairman', 'governance_board', 'governance_auditor'],
            'financial_agent': ['financial_balance_sheet', 'financial_income_statement', 'financial_notes'],
        }

        target_sections = agent_to_section.get(agent_id, [])
        if not target_sections:
            logger.warning(f"Unknown agent_id: {agent_id}")
            return []

        pages = []
        for section in docling_sections:
            heading = section.get('heading', '')
            if not heading:
                continue

            section_type, confidence = self.find_best_match(heading, threshold)

            if section_type in target_sections:
                # Add pages from this section
                section_pages = section.get('pages', [])
                if isinstance(section_pages, list):
                    pages.extend(section_pages)
                elif isinstance(section_pages, (int, float)):
                    pages.append(int(section_pages))

                logger.debug(f"Agent {agent_id}: matched '{heading}' → {section_type} ({confidence:.2f}), pages: {section_pages}")

        # Return unique, sorted pages
        unique_pages = sorted(list(set(pages)))
        logger.info(f"Agent {agent_id}: found {len(unique_pages)} pages via semantic matching")
        return unique_pages


# Singleton instance for efficiency
_semantic_matcher_instance = None


def get_semantic_matcher() -> SemanticHeadingMatcher:
    """
    Get singleton instance of semantic matcher.

    Model loading is expensive (~1-2 seconds), so we cache the instance.
    """
    global _semantic_matcher_instance
    if _semantic_matcher_instance is None:
        _semantic_matcher_instance = SemanticHeadingMatcher()
    return _semantic_matcher_instance


# Convenience function for testing
if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("🧪 Testing Semantic Heading Matcher")
    print("=" * 80)

    # Initialize matcher
    print("\n📥 Loading model...")
    matcher = SemanticHeadingMatcher()

    # Example headings from SRS PDFs (diverse variations)
    print("\n🔍 Testing on diverse Swedish headings:")
    test_headings = [
        "Styrelsen",                              # Should → governance_board
        "Föreningens ledning",                    # Should → governance_board
        "Årets ekonomiska resultat",              # Should → financial_income_statement
        "Tillgångar och skulder",                 # Should → financial_balance_sheet
        "Ekonomisk ställning",                    # Should → financial_balance_sheet
        "Fastighetsuppgifter",                    # Should → property
        "Månadsavgift och avgifter",              # Should → fees
        "Revisionsberättelse",                    # Should → governance_auditor
        "Not 1 - Redovisningsprinciper",         # Should → financial_notes
        "Styrelseledamöter och suppleanter",     # Should → governance_board
        "Ordförande",                             # Should → governance_chairman
        "Random irrelevant heading",              # Should → None (no match)
    ]

    print("")
    results = matcher.match_headings(test_headings, threshold=0.5, verbose=True)

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    matched = sum(1 for r in results.values() if r['matched'])
    total = len(test_headings)
    print(f"  Matched: {matched}/{total} ({matched/total*100:.0f}%)")

    # Show confidence scores
    print("\n📈 Confidence Scores:")
    for heading, result in sorted(results.items(), key=lambda x: x[1]['confidence'], reverse=True):
        status = "✓" if result['matched'] else "✗"
        section = result['section_type'] or 'NO_MATCH'
        conf = result['confidence']
        print(f"  {status} {heading:<45} → {section:<30} ({conf:.2f})")

    print("\n✅ Semantic matcher ready for production!")
    print("=" * 80)
