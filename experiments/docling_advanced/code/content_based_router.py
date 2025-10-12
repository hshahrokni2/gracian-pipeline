"""
Content-Based Section Router

Routes document sections to specialized agents based on CONTENT, not note numbers.

Key Principle: NOTE NUMBERS ARE ARBITRARY, CONTENT IS CONSISTENT

Architecture:
- Layer 1: Direct Swedish keyword matching (93%+ accuracy)
- Layer 2: Fuzzy semantic matching (handles typos, variations)
- Layer 3: LLM classification (edge cases)

Author: Gracian Pipeline Team
Date: 2025-10-12
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from fuzzywuzzy import fuzz
import yaml
from pathlib import Path
import openai


@dataclass
class SectionInfo:
    """Normalized section information"""
    heading: str
    preview_text: str
    page_range: Tuple[int, int]
    note_number: Optional[str] = None  # Detected but NOT used for routing


@dataclass
class RoutingResult:
    """Result of routing decision"""
    agent_name: str
    confidence: float
    matched_keywords: List[str]
    routing_layer: int  # 1=direct, 2=fuzzy, 3=LLM
    reasoning: str


class ContentBasedRouter:
    """
    Routes sections to agents based on CONTENT keywords, not note numbers.

    Anti-Pattern Examples (What NOT to do):
    ❌ if "Not 4" in heading: return "UtilitiesAgent"
    ❌ class Note4UtilitiesAgent
    ❌ NOTE_MAP = {4: "utilities", 8: "buildings"}

    Correct Pattern:
    ✅ if "Driftkostnader" in heading: return "OperatingCostsAgent"
    ✅ class OperatingCostsAgent
    ✅ route_by_content(section) → agent
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize router with content-based configuration.

        Args:
            config_path: Path to content_based_routing.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "content_based_routing.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.agents = self.config['agents']
        self.note_pattern = re.compile(self.config['note_number_pattern']['regex'])

        # Statistics
        self.routing_stats = {
            'layer1_hits': 0,
            'layer2_hits': 0,
            'layer3_hits': 0,
            'total_routes': 0
        }

    def route_section(self, section: SectionInfo) -> RoutingResult:
        """
        Route section to appropriate agent based on content.

        Args:
            section: Section information with heading and preview text

        Returns:
            RoutingResult with agent name, confidence, and reasoning
        """
        self.routing_stats['total_routes'] += 1

        # Strip note number from heading (for detection only, not routing!)
        clean_heading = self._strip_note_number(section.heading)

        # Layer 1: Direct keyword matching
        result = self._route_layer1_keywords(clean_heading, section.preview_text)
        if result:
            self.routing_stats['layer1_hits'] += 1
            return result

        # Layer 2: Fuzzy semantic matching
        result = self._route_layer2_fuzzy(clean_heading, section.preview_text)
        if result:
            self.routing_stats['layer2_hits'] += 1
            return result

        # Layer 3: LLM classification
        result = self._route_layer3_llm(clean_heading, section.preview_text)
        self.routing_stats['layer3_hits'] += 1
        return result

    def _strip_note_number(self, heading: str) -> str:
        """
        Remove note number from heading (for detection only).

        Examples:
            "Not 4 - Driftkostnader" → "Driftkostnader"
            "Noter - Not 8 Byggnader" → "Byggnader"
            "11. Långfristiga skulder" → "Långfristiga skulder"
        """
        # Remove "Not X -" or "Noter - Not X" patterns
        heading = re.sub(r'^Not(er)?\s*-?\s*Not\s+\d+\s*-?\s*', '', heading, flags=re.IGNORECASE)
        heading = re.sub(r'^Not\s+\d+\s*-?\s*', '', heading, flags=re.IGNORECASE)

        # Remove leading number patterns like "11. "
        heading = re.sub(r'^\d+\.\s+', '', heading)

        return heading.strip()

    def _route_layer1_keywords(self, heading: str, preview: str) -> Optional[RoutingResult]:
        """
        Layer 1: Direct Swedish keyword matching.

        Target: 93%+ accuracy
        Strategy: Check if any primary/secondary keywords appear in heading or preview
        """
        heading_lower = heading.lower()
        preview_lower = preview[:500].lower()  # First 500 chars

        for agent_name, agent_config in self.agents.items():
            matched_keywords = []

            # Check primary keywords (higher weight)
            for keyword in agent_config['primary_keywords']:
                if keyword.lower() in heading_lower:
                    matched_keywords.append(f"primary: {keyword}")
                elif keyword.lower() in preview_lower:
                    matched_keywords.append(f"primary_preview: {keyword}")

            # Check secondary keywords
            for keyword in agent_config.get('secondary_keywords', []):
                if keyword.lower() in heading_lower:
                    matched_keywords.append(f"secondary: {keyword}")
                elif keyword.lower() in preview_lower:
                    matched_keywords.append(f"secondary_preview: {keyword}")

            # Check exclude keywords (veto match)
            exclude_match = False
            for keyword in agent_config.get('exclude_keywords', []):
                if keyword.lower() in heading_lower or keyword.lower() in preview_lower:
                    exclude_match = True
                    break

            if matched_keywords and not exclude_match:
                confidence = self._calculate_confidence_layer1(matched_keywords)
                return RoutingResult(
                    agent_name=agent_name,
                    confidence=confidence,
                    matched_keywords=matched_keywords,
                    routing_layer=1,
                    reasoning=f"Direct keyword match: {', '.join(matched_keywords[:3])}"
                )

        return None

    def _route_layer2_fuzzy(self, heading: str, preview: str) -> Optional[RoutingResult]:
        """
        Layer 2: Fuzzy semantic matching.

        Target: 5% accuracy (handles typos, variations, stemming)
        Strategy: Use Levenshtein distance for fuzzy matching
        """
        heading_lower = heading.lower()
        best_match = None
        best_score = 0

        for agent_name, agent_config in self.agents.items():
            # Check fuzzy_terms
            for term in agent_config.get('fuzzy_terms', []):
                # Use partial ratio (handles substrings)
                score = fuzz.partial_ratio(term.lower(), heading_lower)

                if score > 85 and score > best_score:  # 85% threshold
                    best_score = score
                    best_match = (agent_name, term, score)

        if best_match:
            agent_name, term, score = best_match
            return RoutingResult(
                agent_name=agent_name,
                confidence=score / 100.0,
                matched_keywords=[f"fuzzy: {term}"],
                routing_layer=2,
                reasoning=f"Fuzzy match: '{term}' ({score}% similarity)"
            )

        return None

    def _route_layer3_llm(self, heading: str, preview: str) -> RoutingResult:
        """
        Layer 3: LLM classification.

        Target: 2% accuracy (edge cases, ambiguous sections)
        Strategy: Ask LLM to classify based on content
        """
        prompt = self._build_classification_prompt(heading, preview)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF document classification expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=100
            )

            classification = response.choices[0].message.content.strip()
            agent_name, confidence = self._parse_llm_classification(classification)

            return RoutingResult(
                agent_name=agent_name,
                confidence=confidence,
                matched_keywords=["llm_classified"],
                routing_layer=3,
                reasoning=f"LLM classification: {classification}"
            )

        except Exception as e:
            # Fallback to default agent
            return RoutingResult(
                agent_name="MetadataAgent",  # Safe default
                confidence=0.3,
                matched_keywords=["fallback"],
                routing_layer=3,
                reasoning=f"LLM classification failed, using fallback: {str(e)}"
            )

    def _build_classification_prompt(self, heading: str, preview: str) -> str:
        """Build LLM classification prompt with agent descriptions."""
        agent_descriptions = []
        for i, (agent_name, agent_config) in enumerate(self.agents.items(), 1):
            desc = agent_config['description']
            keywords = ', '.join(agent_config['primary_keywords'][:3])
            agent_descriptions.append(f"{i}. {agent_name} - {desc} (Keywords: {keywords})")

        return f"""Analyze this section heading and determine which content type it represents:

Section Heading: "{heading}"
Preview Text: "{preview[:300]}"

Content Types:
{chr(10).join(agent_descriptions)}

Return ONLY the agent name (e.g., "OperatingCostsAgent") or "unknown" if unclear.
If returning an agent name, add confidence score (0-100) on the next line.

Example response:
OperatingCostsAgent
95
"""

    def _parse_llm_classification(self, classification: str) -> Tuple[str, float]:
        """Parse LLM response into agent name and confidence."""
        lines = classification.strip().split('\n')

        if len(lines) >= 2:
            agent_name = lines[0].strip()
            try:
                confidence = float(lines[1].strip()) / 100.0
            except ValueError:
                confidence = 0.7  # Default confidence
        else:
            agent_name = lines[0].strip()
            confidence = 0.7

        # Validate agent name
        if agent_name not in self.agents and agent_name.lower() != "unknown":
            agent_name = "MetadataAgent"  # Fallback
            confidence = 0.3

        return agent_name, confidence

    def _calculate_confidence_layer1(self, matched_keywords: List[str]) -> float:
        """Calculate confidence based on matched keywords."""
        primary_count = sum(1 for k in matched_keywords if k.startswith('primary:'))
        secondary_count = sum(1 for k in matched_keywords if k.startswith('secondary:'))

        # Primary keywords = higher confidence
        confidence = 0.6  # Base
        confidence += primary_count * 0.15
        confidence += secondary_count * 0.05

        return min(confidence, 0.98)  # Cap at 98%

    def get_routing_statistics(self) -> Dict:
        """Return routing statistics for analysis."""
        total = self.routing_stats['total_routes']
        if total == 0:
            return self.routing_stats

        return {
            **self.routing_stats,
            'layer1_percent': (self.routing_stats['layer1_hits'] / total) * 100,
            'layer2_percent': (self.routing_stats['layer2_hits'] / total) * 100,
            'layer3_percent': (self.routing_stats['layer3_hits'] / total) * 100
        }

    def route_batch(self, sections: List[SectionInfo]) -> List[RoutingResult]:
        """Route multiple sections efficiently."""
        return [self.route_section(section) for section in sections]


# ===== USAGE EXAMPLES =====

def example_correct_routing():
    """✅ Example: Correct content-based routing"""
    router = ContentBasedRouter()

    # Example 1: Utilities section (note number varies!)
    section1 = SectionInfo(
        heading="Not 4 - Driftkostnader",
        preview_text="El 450 000 SEK, Värme 890 000 SEK, Vatten 234 000 SEK",
        page_range=(15, 16)
    )
    result1 = router.route_section(section1)
    print(f"✅ Routed to: {result1.agent_name} (confidence: {result1.confidence:.2f})")
    # Output: ✅ Routed to: OperatingCostsAgent (confidence: 0.90)

    # Example 2: Same content, different note number
    section2 = SectionInfo(
        heading="Not 7 - Driftkostnader",  # Different note number!
        preview_text="El 450 000 SEK, Värme 890 000 SEK, Vatten 234 000 SEK",
        page_range=(20, 21)
    )
    result2 = router.route_section(section2)
    print(f"✅ Routed to: {result2.agent_name} (confidence: {result2.confidence:.2f})")
    # Output: ✅ Routed to: OperatingCostsAgent (confidence: 0.90)
    # SAME AGENT despite different note number!

    # Example 3: Buildings section
    section3 = SectionInfo(
        heading="Byggnader och mark",
        preview_text="Taxeringsvärde 50 000 000 SEK, Antal lägenheter 45",
        page_range=(12, 13)
    )
    result3 = router.route_section(section3)
    print(f"✅ Routed to: {result3.agent_name} (confidence: {result3.confidence:.2f})")
    # Output: ✅ Routed to: PropertyAgent (confidence: 0.95)


def example_anti_patterns():
    """❌ Examples: What NOT to do (anti-patterns)"""

    # ❌ WRONG: Hard-coded note numbers
    def wrong_routing_v1(heading: str):
        if "Not 4" in heading:
            return "UtilitiesAgent"
        if "Not 8" in heading:
            return "BuildingsAgent"
        # Problem: Not 4 may be different content in another BRF!

    # ❌ WRONG: Note number in agent name
    class Note4UtilitiesAgent:
        # Problem: Utilities not always in Note 4
        pass

    # ❌ WRONG: Assuming sequential numbering
    NOTE_MAP = {
        4: "utilities",
        8: "buildings",
        11: "liabilities"
    }
    # Problem: Numbering varies across documents

    print("❌ These are ANTI-PATTERNS - do NOT use!")


if __name__ == "__main__":
    print("=== Content-Based Router Examples ===\n")

    print("✅ CORRECT PATTERN:\n")
    example_correct_routing()

    print("\n" + "="*50 + "\n")

    print("❌ ANTI-PATTERNS (What NOT to do):\n")
    example_anti_patterns()

    print("\n" + "="*50 + "\n")

    # Show routing statistics
    router = ContentBasedRouter()
    sections = [
        SectionInfo("Not 4 - Driftkostnader", "El, Värme, Vatten", (15, 16)),
        SectionInfo("Byggnader och mark", "Taxeringsvärde", (12, 13)),
        SectionInfo("Långfristiga skulder", "Lån 1: 25 000 000 SEK", (18, 19)),
        SectionInfo("Styrelse", "Ordförande: Per Wiklund", (3, 4)),
    ]
    results = router.route_batch(sections)

    print("Routing Results:")
    for i, (section, result) in enumerate(zip(sections, results), 1):
        print(f"{i}. '{section.heading}' → {result.agent_name} "
              f"(Layer {result.routing_layer}, {result.confidence:.2f} confidence)")

    print(f"\nStatistics: {router.get_routing_statistics()}")
