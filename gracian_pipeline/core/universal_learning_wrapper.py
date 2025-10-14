"""
Universal Learning Wrapper for ALL Extraction Agents

Wraps ANY agent (governance, financial, property, loans, etc.) with adaptive learning.
Works with both Option A (LLM-based) and Path B (TDD-based) agents.

Author: Claude Code
Date: 2025-10-14
"""

from typing import Dict, Any, Optional, Callable
import logging
from functools import wraps

from ..core.learning_loop import get_learning_loop

logger = logging.getLogger(__name__)


class UniversalLearningWrapper:
    """
    Universal wrapper that adds adaptive learning to ANY extraction agent.

    Supports:
    - Governance agents (chairman, board_members, auditor)
    - Financial agents (financial, cashflow)
    - Property agents (property, energy)
    - Loans agents (loans, reserves)
    - Operations agents (operations, fees)
    - Notes agents (depreciation, maintenance, tax)
    - All other extraction agents
    """

    def __init__(self, agent_id: str, enable_learning: bool = True):
        """
        Initialize universal learning wrapper.

        Args:
            agent_id: Agent identifier (e.g., "chairman_agent", "financial_agent")
            enable_learning: Whether to enable learning (default: True)
        """
        self.agent_id = agent_id
        self.enable_learning = enable_learning
        self.learning_loop = get_learning_loop() if enable_learning else None

        # Map agent types to their data categories
        self.agent_categories = {
            # Governance
            'chairman_agent': 'governance',
            'board_members_agent': 'governance',
            'auditor_agent': 'governance',

            # Financial
            'financial_agent': 'financial',
            'cashflow_agent': 'financial',

            # Property
            'property_agent': 'property',
            'energy_agent': 'property',

            # Loans & Reserves
            'loans_agent': 'loans',
            'reserves_agent': 'loans',

            # Operations
            'operations_agent': 'operations',
            'fees_agent': 'operations',
            'events_agent': 'operations',

            # Notes (Path B agents)
            'notes_depreciation_agent': 'notes',
            'notes_maintenance_agent': 'notes',
            'notes_tax_agent': 'notes',

            # Audit
            'audit_agent': 'audit',
        }

    def wrap_extraction(self, extraction_func: Callable) -> Callable:
        """
        Wrap an extraction function with learning capabilities.

        Args:
            extraction_func: Original extraction function

        Returns:
            Wrapped function with learning integrated
        """
        @wraps(extraction_func)
        def wrapped_with_learning(*args, **kwargs):
            # Step 1: Call original extraction function
            result = extraction_func(*args, **kwargs)

            # Step 2: Record extraction for learning (if enabled)
            if self.enable_learning and self.learning_loop:
                try:
                    self._record_extraction(result)
                except Exception as e:
                    logger.warning(f"Learning recording failed for {self.agent_id}: {e}")
                    # Don't fail extraction if learning fails

            return result

        return wrapped_with_learning

    def _record_extraction(self, result: Dict[str, Any]) -> None:
        """
        Record extraction result for learning.

        Args:
            result: Extraction result dict
        """
        if not isinstance(result, dict):
            return

        # Extract evidence pages (if available)
        evidence_pages = result.get('evidence_pages', [])

        # Calculate confidence (heuristic based on filled fields)
        confidence = self._calculate_confidence(result)

        # Record each extracted field
        for field_name, field_value in result.items():
            # Skip metadata fields
            if field_name in ['evidence_pages', 'confidence']:
                continue

            # Determine if extraction was successful
            validation_passed = self._is_field_valid(field_value) and confidence > 0.7

            # Build evidence dict
            evidence = {
                "pages": evidence_pages,
                "quotes": self._extract_quotes(field_value)
            }

            # Record extraction
            self.learning_loop.record_extraction(
                agent_id=self.agent_id,
                field_name=field_name,
                value=field_value,
                confidence=confidence,
                evidence=evidence,
                validation_passed=validation_passed
            )

        # Record section detection pattern (if applicable)
        self._record_section_pattern(result)

    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on filled fields.

        Args:
            result: Extraction result dict

        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Count non-metadata fields
        all_fields = [k for k in result.keys() if k not in ['evidence_pages', 'confidence']]
        filled_fields = [k for k in all_fields if self._is_field_valid(result[k])]

        if not all_fields:
            return 0.5

        # Calculate completeness ratio
        completeness = len(filled_fields) / len(all_fields)

        # Factor in evidence pages
        evidence_bonus = 0.1 if result.get('evidence_pages') else 0.0

        return min(1.0, 0.5 + (completeness * 0.4) + evidence_bonus)

    def _is_field_valid(self, value: Any) -> bool:
        """
        Check if field value is valid (not null/empty).

        Args:
            value: Field value to check

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    def _extract_quotes(self, value: Any) -> list:
        """
        Extract representative quotes from field value.

        Args:
            value: Field value

        Returns:
            List of quote strings
        """
        if isinstance(value, str) and len(value) > 0:
            # Return first 100 chars as quote
            return [value[:100]]
        return []

    def _record_section_pattern(self, result: Dict[str, Any]) -> None:
        """
        Record section/heading pattern for future detection.

        Args:
            result: Extraction result dict
        """
        # Get agent category
        category = self.agent_categories.get(self.agent_id, 'unknown')

        # If governance agent extracted chairman, record pattern
        if self.agent_id == 'chairman_agent' and result.get('chairman'):
            confidence = self._calculate_confidence(result)
            self.learning_loop.record_note_detection(
                heading="Styrelsen / Ordförande",
                note_type=category,
                detection_confidence=confidence
            )

        # If financial agent extracted revenue, record pattern
        elif self.agent_id == 'financial_agent' and result.get('revenue'):
            confidence = self._calculate_confidence(result)
            self.learning_loop.record_note_detection(
                heading="Resultaträkning / Balansräkning",
                note_type=category,
                detection_confidence=confidence
            )

        # If loans agent extracted loans list, record pattern
        elif self.agent_id == 'loans_agent' and result.get('loans'):
            confidence = self._calculate_confidence(result)
            self.learning_loop.record_note_detection(
                heading="Not 5 - Låneskulder",
                note_type=category,
                detection_confidence=confidence
            )

        # Add more patterns for other agents as needed


def with_learning(agent_id: str, enable_learning: bool = True):
    """
    Decorator to add learning to any extraction function.

    Usage:
        @with_learning('financial_agent')
        def extract_financial_data(pdf_path):
            # ... extraction logic ...
            return {"revenue": 1000000, "evidence_pages": [5, 6]}

    Args:
        agent_id: Agent identifier
        enable_learning: Whether to enable learning

    Returns:
        Decorator function
    """
    def decorator(func):
        wrapper = UniversalLearningWrapper(agent_id, enable_learning)
        return wrapper.wrap_extraction(func)
    return decorator


# Export for easy imports
__all__ = ['UniversalLearningWrapper', 'with_learning']
