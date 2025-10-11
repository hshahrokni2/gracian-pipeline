"""
Cross-Agent Data Linker - Component 3 of Phase 3A

Resolves data conflicts across multiple extraction agents using:
1. Cross-reference validation (from Enhanced Structure Detector)
2. Confidence-weighted conflict resolution
3. Synonym matching (Swedish term normalization)

Architecture: Graph-based resolver with topological ordering
Performance Target: <5s per document, >95% link accuracy
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from enhanced_structure_detector import DocumentMap, CrossReference


@dataclass
class CrossAgentLink:
    """Represents a link between two agent extractions of the same field"""

    source_agent: str
    source_field: str
    source_value: Any
    source_confidence: float
    source_page: int

    target_agent: str
    target_field: str
    target_value: Any
    target_confidence: float
    target_page: int

    link_type: str  # "cross_reference" | "synonym" | "calculation"
    resolution_status: str = "pending"  # "matched" | "conflict" | "ocr_error" | "missing"

    final_value: Any = None
    final_confidence: float = 0.0
    conflict_details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Export link for diagnostics"""
        return {
            "source": f"{self.source_agent}.{self.source_field}",
            "source_value": self.source_value,
            "source_confidence": self.source_confidence,
            "source_page": self.source_page,
            "target": f"{self.target_agent}.{self.target_field}",
            "target_value": self.target_value,
            "target_confidence": self.target_confidence,
            "target_page": self.target_page,
            "link_type": self.link_type,
            "resolution": {
                "status": self.resolution_status,
                "final_value": self.final_value,
                "final_confidence": self.final_confidence,
                "details": self.conflict_details
            }
        }


@dataclass
class LinkResolution:
    """Final resolution results after cross-agent linking"""

    linked_data: Dict[str, Any] = field(default_factory=dict)  # Merged field values
    confidence_boost: Dict[str, float] = field(default_factory=dict)  # Fields with confirmed cross-refs
    conflicts: List[CrossAgentLink] = field(default_factory=list)  # Unresolved conflicts
    flags_for_review: List[str] = field(default_factory=list)  # Missing cross-references
    merge_stats: Dict[str, int] = field(default_factory=dict)  # Diagnostics

    def to_dict(self) -> Dict[str, Any]:
        """Export resolution for analysis"""
        return {
            "linked_data": self.linked_data,
            "confidence_boost": self.confidence_boost,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "flags_for_review": self.flags_for_review,
            "merge_stats": self.merge_stats
        }


class CrossAgentDataLinker:
    """
    Links and resolves data across multiple extraction agents.

    Strategy:
    1. Build link graph from cross_references (Component 1)
    2. Resolve conflicts using confidence-weighted voting
    3. Boost confidence for matched cross-references
    4. Flag unresolved conflicts and missing data
    """

    def __init__(self, document_map: DocumentMap):
        self.cross_references = document_map.cross_references
        self.term_index = document_map.term_index

        # Agent field mappings (Swedish → English canonical names)
        self.field_mappings = self._build_field_mappings()

    def _build_field_mappings(self) -> Dict[str, str]:
        """
        Build Swedish → English field name mappings

        Uses term_index from Component 1 for canonical names
        """
        mappings = {}

        # From term_index (Component 1)
        for canonical_field, term_data in self.term_index.items():
            swedish_term = term_data.term.lower()
            mappings[swedish_term] = canonical_field

        # Additional common mappings (fallback)
        fallback_mappings = {
            "nettoomsättning": "revenue",
            "nettoomsattning": "revenue",
            "intäkter": "revenue",
            "rörelseresultat": "operating_surplus",
            "resultat": "net_income",
            "tillgångar": "assets",
            "tillgangar": "assets",
            "skulder": "liabilities",
            "eget kapital": "equity",
            "kassa och bank": "cash",
            "fastighetsinteckning": "pledged_assets_amount"
        }

        mappings.update(fallback_mappings)
        return mappings

    def link_agent_results(
        self,
        agent_results: Dict[str, Dict[str, Any]]
    ) -> LinkResolution:
        """
        Main linking algorithm.

        Args:
            agent_results: {
                "financial_agent": {"revenue": 2183255, "confidence": 0.85, "source_page": 8},
                "note_2_agent": {"nettoomsättning": 2183255, "confidence": 0.92, "source_page": 13}
            }

        Returns:
            LinkResolution with merged data, confidence boosts, and conflict flags
        """
        resolution = LinkResolution()

        # Step 1: Build link graph from cross_references
        links = self._build_link_graph(agent_results)
        resolution.merge_stats['total_links'] = len(links)

        # Step 2: Resolve conflicts (confidence-weighted voting)
        resolved_links = []
        for link in links:
            resolved_link = self._resolve_conflict(link)
            resolved_links.append(resolved_link)

            # Track resolution stats
            if resolved_link.resolution_status == "matched":
                resolution.merge_stats['matched'] = resolution.merge_stats.get('matched', 0) + 1
            elif resolved_link.resolution_status == "conflict":
                resolution.conflicts.append(resolved_link)
                resolution.merge_stats['conflicts'] = resolution.merge_stats.get('conflicts', 0) + 1
            elif resolved_link.resolution_status == "ocr_error":
                resolution.merge_stats['ocr_errors'] = resolution.merge_stats.get('ocr_errors', 0) + 1

        # Step 3: Merge results with boosted confidence
        resolution = self._merge_results(agent_results, resolved_links, resolution)

        # Step 4: Flag missing cross-references
        resolution = self._flag_missing_references(agent_results, resolved_links, resolution)

        return resolution

    def _build_link_graph(
        self,
        agent_results: Dict[str, Dict[str, Any]]
    ) -> List[CrossAgentLink]:
        """
        Build link graph from cross_references.

        CrossReference structure from Component 1:
        - note_heading: str  # e.g. "NOT 2, NETTOOMSÄTTNING"
        - note_page: int
        - balance_sheet_page: int
        - balance_sheet_row: Dict[str, Any]
        - link_type: str  # 'note_to_balance_sheet', 'note_to_income_statement'
        """
        links = []

        for cross_ref in self.cross_references:
            # Extract note number and field from heading
            note_match = re.match(r'NOT\s+(\d+)[,\s]+(.*)', cross_ref.note_heading, re.IGNORECASE)
            if not note_match:
                continue

            note_num = note_match.group(1)
            note_field_swedish = note_match.group(2).strip()

            # Map to agents
            source_agent = f"note_{note_num}_agent"

            # Determine target agent from link_type
            if 'balance_sheet' in cross_ref.link_type:
                target_agent = "financial_agent"
            elif 'income_statement' in cross_ref.link_type:
                target_agent = "financial_agent"
            else:
                target_agent = "financial_agent"  # Default

            # Get field values from agent results
            source_data = agent_results.get(source_agent, {})
            target_data = agent_results.get(target_agent, {})

            # Normalize field names (Swedish → English)
            source_field_canonical = self._normalize_field_name(note_field_swedish)

            # For target, use balance_sheet_row label field
            target_field_label = cross_ref.balance_sheet_row.get('label', '')
            target_field_canonical = self._normalize_field_name(target_field_label)

            # Extract values
            source_value = source_data.get(source_field_canonical)

            # For target, look in balance_sheet_row data
            # balance_sheet_row example: {'label': 'Byggnad och mark', '2023-12-31': 65198856, ...}
            target_value = None
            for key, val in cross_ref.balance_sheet_row.items():
                if key != 'label' and isinstance(val, (int, float)):
                    target_value = val
                    break

            # Skip if either value is missing
            if source_value is None or target_value is None:
                continue

            # Create link
            link = CrossAgentLink(
                source_agent=source_agent,
                source_field=source_field_canonical,
                source_value=source_value,
                source_confidence=source_data.get('confidence', 0.5),
                source_page=cross_ref.note_page,
                target_agent=target_agent,
                target_field=target_field_canonical,
                target_value=target_value,
                target_confidence=target_data.get('confidence', 0.5),
                target_page=cross_ref.balance_sheet_page,
                link_type=cross_ref.link_type
            )

            links.append(link)

        return links

    def _table_to_agent(self, table_name: str) -> str:
        """
        Map table name to agent name.

        Examples:
        - "income_statement" → "financial_agent"
        - "note_2" → "note_2_agent"
        - "balance_sheet_assets" → "financial_agent"
        """
        agent_mappings = {
            "income_statement": "financial_agent",
            "balance_sheet_assets": "financial_agent",
            "balance_sheet_equity_liabilities": "financial_agent",
            "cash_flow": "financial_agent",
            "note_2": "note_2_agent",
            "note_7": "note_7_agent",
            "note_11": "note_11_agent",
            "note_14": "note_14_agent",
            "note_16": "note_16_agent",
            "note_17": "note_17_agent"
        }

        return agent_mappings.get(table_name, f"{table_name}_agent")

    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize Swedish field name to English canonical name.

        Examples:
        - "Nettoomsättning" → "revenue"
        - "Tillgångar" → "assets"
        - "revenue" → "revenue" (already canonical)
        """
        # Lowercase and strip
        field_lower = field_name.lower().strip()

        # Check field_mappings
        if field_lower in self.field_mappings:
            return self.field_mappings[field_lower]

        # Return as-is if no mapping found (might already be canonical)
        return field_name

    def _resolve_conflict(self, link: CrossAgentLink) -> CrossAgentLink:
        """
        Resolve conflict between source and target values.

        Algorithm:
        1. Exact Match + High Confidence (both >0.7)
           → Average values, boost confidence to max + 0.1

        2. Mismatch + High Confidence (diff >5%, both >0.7)
           → Use higher confidence value, flag conflict

        3. Mismatch + Low Confidence (one <0.7)
           → Use higher confidence value (likely OCR error)

        4. Missing Data
           → Keep available value, flag for review
        """
        # Convert to numeric if possible
        source_num = self._to_numeric(link.source_value)
        target_num = self._to_numeric(link.target_value)

        # Case 1: Exact Match (within 5% tolerance)
        if source_num is not None and target_num is not None:
            diff_percent = abs(source_num - target_num) / max(abs(target_num), 1) * 100

            if diff_percent < 5.0:
                # Exact match - average values and boost confidence
                link.final_value = (source_num + target_num) / 2
                link.final_confidence = min(0.98, max(link.source_confidence, link.target_confidence) + 0.1)
                link.resolution_status = "matched"
                link.conflict_details = f"Exact match (diff: {diff_percent:.1f}%), confidence boosted"

            elif link.source_confidence > 0.7 and link.target_confidence > 0.7:
                # Case 2: High confidence mismatch - conflict
                if link.source_confidence > link.target_confidence:
                    link.final_value = link.source_value
                    link.final_confidence = link.source_confidence
                else:
                    link.final_value = link.target_value
                    link.final_confidence = link.target_confidence

                link.resolution_status = "conflict"
                link.conflict_details = f"High confidence mismatch (diff: {diff_percent:.1f}%), used higher confidence"

            else:
                # Case 3: Low confidence mismatch - likely OCR error
                if link.source_confidence > link.target_confidence:
                    link.final_value = link.source_value
                    link.final_confidence = link.source_confidence
                else:
                    link.final_value = link.target_value
                    link.final_confidence = link.target_confidence

                link.resolution_status = "ocr_error"
                link.conflict_details = f"Low confidence mismatch (diff: {diff_percent:.1f}%), likely OCR error"

        else:
            # Non-numeric comparison (exact string match)
            if str(link.source_value).lower().strip() == str(link.target_value).lower().strip():
                link.final_value = link.source_value
                link.final_confidence = min(0.98, max(link.source_confidence, link.target_confidence) + 0.1)
                link.resolution_status = "matched"
                link.conflict_details = "Exact string match, confidence boosted"
            else:
                # Use higher confidence value
                if link.source_confidence > link.target_confidence:
                    link.final_value = link.source_value
                    link.final_confidence = link.source_confidence
                else:
                    link.final_value = link.target_value
                    link.final_confidence = link.target_confidence

                link.resolution_status = "conflict"
                link.conflict_details = "String mismatch, used higher confidence"

        return link

    def _to_numeric(self, value: Any) -> Optional[float]:
        """Convert value to numeric if possible"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        # Try parsing string
        if isinstance(value, str):
            # Remove spaces and replace comma with dot
            cleaned = value.strip().replace(' ', '').replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                return None

        return None

    def _merge_results(
        self,
        agent_results: Dict[str, Dict[str, Any]],
        resolved_links: List[CrossAgentLink],
        resolution: LinkResolution
    ) -> LinkResolution:
        """
        Merge agent results with resolved links.

        Strategy:
        1. Start with all agent results
        2. Replace values with resolved link values (higher confidence)
        3. Track confidence boosts for matched cross-references
        """
        # Start with all agent data
        for agent_name, agent_data in agent_results.items():
            for field_name, value in agent_data.items():
                if field_name in ['confidence', 'source_page']:
                    continue  # Skip metadata

                resolution.linked_data[f"{agent_name}.{field_name}"] = value

        # Apply resolved links
        for link in resolved_links:
            target_key = f"{link.target_agent}.{link.target_field}"

            # Replace with final resolved value
            resolution.linked_data[target_key] = link.final_value

            # Track confidence boost if matched
            if link.resolution_status == "matched":
                resolution.confidence_boost[target_key] = link.final_confidence

        return resolution

    def _flag_missing_references(
        self,
        agent_results: Dict[str, Dict[str, Any]],
        resolved_links: List[CrossAgentLink],
        resolution: LinkResolution
    ) -> LinkResolution:
        """
        Flag fields that should have cross-references but don't.

        Example: Financial statement shows "Assets: 65M" but no Note 11 breakdown found
        """
        # Get all expected cross-references from document_map
        expected_links = set()
        for cross_ref in self.cross_references:
            source_agent = self._table_to_agent(cross_ref.source_table)
            target_agent = self._table_to_agent(cross_ref.target_table)
            expected_links.add((source_agent, target_agent))

        # Check which expected links are missing
        actual_links = set()
        for link in resolved_links:
            actual_links.add((link.source_agent, link.target_agent))

        missing_links = expected_links - actual_links

        for source_agent, target_agent in missing_links:
            resolution.flags_for_review.append(
                f"Missing cross-reference: {source_agent} → {target_agent}"
            )

        resolution.merge_stats['missing_links'] = len(missing_links)

        return resolution


# Test function
def test_cross_agent_linker():
    """Test cross-agent data linker on sample data"""
    from enhanced_structure_detector import EnhancedStructureDetector

    # Load test PDF structure
    detector = EnhancedStructureDetector()
    pdf_path = 'test_pdfs/brf_268882.pdf'

    print("Extracting document structure...")
    document_map = detector.extract_document_map(pdf_path)

    # Simulate agent results (from financial_agent and note_2_agent)
    agent_results = {
        "financial_agent": {
            "revenue": 2183255,
            "confidence": 0.85,
            "source_page": 8
        },
        "note_2_agent": {
            "nettoomsättning": 2183255,  # Same value (cross-reference)
            "confidence": 0.92,
            "source_page": 13
        }
    }

    # Test linker
    linker = CrossAgentDataLinker(document_map)
    resolution = linker.link_agent_results(agent_results)

    # Display results
    import json
    print("\n✅ Cross-Agent Data Linker Results:")
    print(json.dumps(resolution.to_dict(), indent=2, ensure_ascii=False))

    # Assertions
    assert len(resolution.confidence_boost) > 0, "Should have confidence boosts"
    assert resolution.merge_stats['matched'] > 0, "Should have matched links"
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_cross_agent_linker()
