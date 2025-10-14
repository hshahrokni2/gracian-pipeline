"""
Agent Confidence Calculator

Calculates confidence scores for agent extractions based on:
1. Evidence quality (strength of evidence_pages citations)
2. Completeness (proportion of expected fields extracted)
3. Validation status (data quality checks)
4. Context relevance (whether agent examined relevant pages)

Author: Claude Code
Date: 2025-10-13
"""

from typing import Dict, Any, List, Optional
import statistics


class AgentConfidenceCalculator:
    """Calculates confidence scores for agent extractions."""

    # Expected field counts per agent (based on schema)
    EXPECTED_FIELDS = {
        "auditor_agent": 3,
        "chairman_agent": 1,
        "notes_depreciation_agent": 3,
        "financial_agent": 7,
        "notes_maintenance_agent": 2,
        "board_members_agent": 1,  # board_members list
        "notes_tax_agent": 3,
        "property_agent": 13,
        "events_agent": 3,
        "energy_agent": 3,
        "audit_agent": 6,
        "cashflow_agent": 3,
        "loans_agent": 5,  # includes loans list
        "fees_agent": 14,
        "reserves_agent": 4,
    }

    # Critical pages for each agent (where we expect to find their data)
    EXPECTED_PAGE_RANGES = {
        "auditor_agent": (13, 16),  # Audit report typically at end
        "chairman_agent": (1, 3),   # Governance at front
        "notes_depreciation_agent": (5, 12),  # Notes section
        "financial_agent": (1, 7),  # Financial statements early
        "notes_maintenance_agent": (5, 12),
        "board_members_agent": (1, 3),
        "notes_tax_agent": (5, 12),
        "property_agent": (1, 5),  # Property info typically early
        "events_agent": (1, 16),  # Can appear anywhere
        "energy_agent": (1, 16),  # Energy info varies
        "audit_agent": (13, 16),
        "cashflow_agent": (5, 10),  # Usually in financial statements
        "loans_agent": (8, 14),  # Typically in notes
        "fees_agent": (1, 10),  # Fee info varies
        "reserves_agent": (5, 10),  # Reserve fund in notes
    }

    def calculate_agent_confidence(
        self,
        agent_name: str,
        agent_result: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a single agent's extraction.

        Returns:
            Float between 0.0 and 1.0
        """
        # Handle None result (agent failed to extract)
        if agent_result is None:
            return 0.0

        # Factor 1: Evidence quality (0-0.3)
        evidence_score = self._calculate_evidence_score(agent_result)

        # Factor 2: Completeness (0-0.4)
        completeness_score = self._calculate_completeness_score(agent_name, agent_result)

        # Factor 3: Validation status (0-0.2)
        validation_score = self._calculate_validation_score(agent_name, agent_result)

        # Factor 4: Context relevance (0-0.1)
        context_score = self._calculate_context_relevance(agent_name, agent_result)

        # Total weighted score
        total_score = evidence_score + completeness_score + validation_score + context_score

        return min(1.0, max(0.0, total_score))

    def _calculate_evidence_score(self, agent_result: Dict[str, Any]) -> float:
        """
        Calculate evidence quality score (0-0.3).

        Based on:
        - Number of evidence pages cited
        - Whether evidence pages are non-empty
        """
        evidence_pages = agent_result.get("evidence_pages", [])

        if not evidence_pages:
            return 0.0

        # More evidence pages = higher confidence (up to 5 pages)
        num_pages = len(evidence_pages)
        page_score = min(num_pages / 5.0, 1.0)

        return page_score * 0.3

    def _calculate_completeness_score(
        self,
        agent_name: str,
        agent_result: Dict[str, Any]
    ) -> float:
        """
        Calculate completeness score (0-0.4).

        Based on:
        - Proportion of expected fields that have values
        """
        expected_count = self.EXPECTED_FIELDS.get(agent_name, 5)

        # Count non-null fields (excluding evidence_pages and metadata)
        extracted_count = 0
        for key, value in agent_result.items():
            if key == "evidence_pages":
                continue

            # Check if field has meaningful value
            if value is not None and value != "" and value != [] and value != {}:
                extracted_count += 1

        # Calculate proportion
        if expected_count == 0:
            return 0.4  # Full score if no fields expected

        proportion = extracted_count / expected_count

        # Cap at 1.0 (can extract more than expected)
        proportion = min(proportion, 1.0)

        return proportion * 0.4

    def _calculate_validation_score(
        self,
        agent_name: str,
        agent_result: Dict[str, Any]
    ) -> float:
        """
        Calculate validation score (0-0.2).

        Based on:
        - Data type checks
        - Value range checks
        - Format validation
        """
        score = 0.2  # Start with full score

        # Check for common validation issues
        for key, value in agent_result.items():
            if key == "evidence_pages":
                continue

            # Skip null values
            if value is None or value == "" or value == [] or value == {}:
                continue

            # Type-specific validation
            if "date" in key.lower():
                # Check date format (basic check)
                if isinstance(value, str) and len(value) < 6:
                    score -= 0.05  # Suspicious date format

            elif "year" in key.lower():
                # Check year range
                if isinstance(value, int) and (value < 1900 or value > 2100):
                    score -= 0.05

            elif "rate" in key.lower() or "percentage" in key.lower():
                # Check percentage/rate range
                if isinstance(value, (int, float)) and (value < 0 or value > 100):
                    score -= 0.05

            elif "amount" in key.lower() or "balance" in key.lower():
                # Check negative amounts (suspicious for assets/equity)
                if isinstance(value, (int, float)) and value < 0:
                    if "liabilities" not in key.lower() and "debt" not in key.lower():
                        score -= 0.05

        return max(0.0, score)

    def _calculate_context_relevance(
        self,
        agent_name: str,
        agent_result: Dict[str, Any]
    ) -> float:
        """
        Calculate context relevance score (0-0.1).

        Based on:
        - Whether agent examined pages in expected range
        """
        evidence_pages = agent_result.get("evidence_pages", [])

        if not evidence_pages:
            return 0.0

        expected_range = self.EXPECTED_PAGE_RANGES.get(agent_name)
        if not expected_range:
            return 0.1  # Full score if no expected range defined

        min_page, max_page = expected_range

        # Check if any evidence page is in expected range
        in_range = any(min_page <= page <= max_page for page in evidence_pages)

        if in_range:
            return 0.1
        else:
            # Partial score if pages are close to expected range
            closest_distance = min(
                abs(page - min_page) if page < min_page else abs(page - max_page)
                for page in evidence_pages
            )

            if closest_distance <= 3:
                return 0.05  # Close enough
            else:
                return 0.0

    def calculate_overall_confidence(
        self,
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence for entire extraction.

        Returns:
            Dict with:
            - confidence_score: Weighted average confidence (0-1)
            - agent_confidences: Dict of per-agent scores
            - high_confidence_count: Number of agents with >0.7 confidence
            - low_confidence_count: Number of agents with <0.3 confidence
        """
        agent_confidences = {}

        # Calculate confidence for each agent
        for agent_name, agent_result in extraction_result.items():
            # Skip metadata fields
            if agent_name.startswith("_"):
                continue

            # Skip non-agent fields
            if not agent_name.endswith("_agent"):
                continue

            # Skip None results (failed agents) - will get 0.0 confidence
            # Note: calculate_agent_confidence handles None, but we document it here

            # Calculate confidence
            confidence = self.calculate_agent_confidence(agent_name, agent_result)
            agent_confidences[agent_name] = confidence

        # Calculate weighted average
        if not agent_confidences:
            overall_confidence = 0.0
        else:
            # Weight by expected field count (agents with more fields matter more)
            total_weight = 0
            weighted_sum = 0

            for agent_name, confidence in agent_confidences.items():
                weight = self.EXPECTED_FIELDS.get(agent_name, 5)
                weighted_sum += confidence * weight
                total_weight += weight

            overall_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Count high/low confidence agents
        high_confidence_count = sum(1 for c in agent_confidences.values() if c > 0.7)
        low_confidence_count = sum(1 for c in agent_confidences.values() if c < 0.3)

        return {
            "confidence_score": overall_confidence,
            "agent_confidences": agent_confidences,
            "high_confidence_count": high_confidence_count,
            "low_confidence_count": low_confidence_count,
            "total_agents": len(agent_confidences),
        }


def add_confidence_to_result(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add confidence scores to extraction result.

    This is the main function to call from the orchestrator.

    Args:
        extraction_result: Result dict from extract_all_agents_parallel()

    Returns:
        Same dict with added extraction_quality section
    """
    calculator = AgentConfidenceCalculator()
    confidence_data = calculator.calculate_overall_confidence(extraction_result)

    # Add to result
    extraction_result["extraction_quality"] = {
        "confidence_score": confidence_data["confidence_score"],
        "high_confidence_agents": confidence_data["high_confidence_count"],
        "low_confidence_agents": confidence_data["low_confidence_count"],
        "total_agents_evaluated": confidence_data["total_agents"],
        "agent_confidence_breakdown": confidence_data["agent_confidences"],
    }

    return extraction_result
