"""
Base agent for Swedish BRF notes extraction.

Implements Template Method Pattern for consistent extraction flow across
all note-specific agents. Provides 4-factor confidence scoring and robust
error handling with graceful degradation.

Author: Claude Code
Date: 2025-10-13 (Path B Day 3)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import json
import os
from openai import OpenAI

from ..models.note import Note
from ..schemas.notes_schemas import BaseNoteData
from ..core.learning_loop import get_learning_loop


class BaseNoteAgent(ABC):
    """
    Abstract base class for all note-specific agents.

    Implements Template Method Pattern:
    1. Pre-validation (check empty notes)
    2. Build extraction prompt (subclass-specific)
    3. Call LLM with structured output
    4. Parse with Pydantic
    5. Cross-validate with context
    6. Calculate confidence (4-factor model)
    7. Return dict

    Subclasses must implement:
    - _build_extraction_prompt(): Create agent-specific prompt
    - _cross_validate(): Validate extracted data with context
    - _get_schema_class(): Return Pydantic schema class
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0, enable_learning: bool = True):
        """
        Initialize base agent.

        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
            temperature: Temperature for generation (default: 0.0 for deterministic)
            enable_learning: Whether to enable adaptive learning loop (default: True)
        """
        self.model = model
        self.temperature = temperature
        self.enable_learning = enable_learning

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)

        # Initialize learning loop
        if self.enable_learning:
            self.learning_loop = get_learning_loop()
        else:
            self.learning_loop = None

    def extract(self, note: Note, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction flow (Template Method).

        This method defines the skeleton of the extraction algorithm.
        Subclasses customize specific steps via abstract methods.

        Args:
            note: Note object with content to extract from
            context: Context dict with balance sheet, income statement data

        Returns:
            Dict with extracted fields and confidence score
        """
        # Step 1: Pre-validation
        if self._is_empty_note(note):
            return self._empty_response()

        # Step 2: Build extraction prompt (subclass-specific)
        try:
            prompt = self._build_extraction_prompt(note, context)
        except Exception as e:
            print(f"Error building prompt: {e}")
            return self._empty_response()

        # Step 3: Call LLM with structured output
        try:
            raw_result = self._call_llm(prompt)
        except Exception as e:
            print(f"LLM error: {e}")
            return self._empty_response()

        # Step 4: Parse with Pydantic
        try:
            parsed = self._parse_result(raw_result)
        except Exception as e:
            print(f"Parsing error: {e}")
            return self._empty_response()

        # Step 5: Cross-validate with context (subclass-specific)
        try:
            validated = self._cross_validate(parsed, context)
        except Exception as e:
            print(f"Cross-validation error: {e}")
            validated = parsed

        # Step 6: Calculate confidence (4-factor model)
        try:
            final = self._add_confidence(validated, note, context)
        except Exception as e:
            print(f"Confidence calculation error: {e}")
            final = validated

        # Step 7: Record extraction for learning (if enabled)
        if self.enable_learning and self.learning_loop:
            try:
                self._record_extraction_for_learning(final, note, context)
            except Exception as e:
                print(f"Learning loop recording error: {e}")

        # Step 8: Return dict
        return final.dict()

    def _is_empty_note(self, note: Note) -> bool:
        """
        Check if note is empty or has insufficient content.

        Args:
            note: Note object to check

        Returns:
            True if note is empty or too short
        """
        if not note or not note.content:
            return True

        # Check if content is just whitespace or very short
        content_stripped = note.content.strip()
        if len(content_stripped) < 10:
            return True

        return False

    def _empty_response(self) -> Dict[str, Any]:
        """
        Return empty response with null values and low confidence.

        Returns:
            Dict with all fields set to None and confidence 0.0
        """
        schema_class = self._get_schema_class()
        empty_instance = schema_class(
            confidence=0.0,
            evidence_pages=[],
            evidence_quotes=[]
        )
        return empty_instance.dict()

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API with error handling.

        Args:
            prompt: Extraction prompt

        Returns:
            Dict with extracted data

        Raises:
            Exception: If API call fails after retries
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Swedish BRF financial document extraction expert. Extract information accurately from Swedish text and return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            return result

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {content}")
            raise
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise

    def _parse_result(self, raw_result: Dict[str, Any]) -> BaseNoteData:
        """
        Parse LLM result with Pydantic validation.

        Args:
            raw_result: Raw dict from LLM

        Returns:
            Validated Pydantic model instance

        Raises:
            Exception: If parsing or validation fails
        """
        schema_class = self._get_schema_class()

        try:
            # Parse with Pydantic
            instance = schema_class(**raw_result)
            return instance
        except Exception as e:
            print(f"Pydantic validation error: {e}")
            print(f"Raw result: {raw_result}")
            raise

    def _add_confidence(
        self,
        data: BaseNoteData,
        note: Note,
        context: Dict[str, Any]
    ) -> BaseNoteData:
        """
        Calculate 4-factor confidence score.

        4-Factor Confidence Model (from Option A success):
        1. Evidence Factor (0-0.3): Based on evidence_quotes and evidence_pages
        2. Completeness Factor (0-0.4): Based on non-null fields
        3. Validation Factor (0-0.2): Based on cross-validation with context
        4. Context Factor (0-0.1): Based on note type matching expected content

        Args:
            data: Pydantic model instance
            note: Original note object
            context: Context dict

        Returns:
            Model instance with updated confidence score
        """
        confidence = 0.0

        # Factor 1: Evidence Factor (0-0.3)
        if data.evidence_quotes:
            # More quotes = higher confidence (max at 2 quotes)
            confidence += 0.15 * min(len(data.evidence_quotes) / 2.0, 1.0)

        if data.evidence_pages:
            # More pages cited = higher confidence (max at 2 pages)
            confidence += 0.15 * min(len(data.evidence_pages) / 2.0, 1.0)

        # Factor 2: Completeness Factor (0-0.4)
        # Count non-metadata fields
        all_fields = list(data.dict().keys())
        metadata_fields = {'evidence_pages', 'evidence_quotes', 'confidence'}
        data_fields = [f for f in all_fields if f not in metadata_fields]

        # Count how many data fields are filled
        filled_fields = [
            f for f in data_fields
            if getattr(data, f) is not None
        ]

        if data_fields:
            completeness_ratio = len(filled_fields) / len(data_fields)
            confidence += 0.4 * completeness_ratio

        # Factor 3: Validation Factor (0-0.2)
        # This is added by subclass in _cross_validate()
        # If data.confidence was already set by cross-validation, preserve it
        if data.confidence > 0:
            confidence += data.confidence  # Add validation bonus

        # Factor 4: Context Factor (0-0.1)
        # Check if note type matches expected content
        expected_types = {
            'depreciation': ['depreciation', 'avskrivning'],
            'tax': ['tax', 'skatt'],
            'maintenance': ['maintenance', 'underhåll']
        }

        note_type = note.type.lower() if note.type else ''
        note_content_lower = note.content.lower()

        for expected_type, keywords in expected_types.items():
            if note_type == expected_type or any(kw in note_content_lower for kw in keywords):
                confidence += 0.1
                break

        # Cap confidence at 1.0
        data.confidence = min(confidence, 1.0)

        return data

    def _record_extraction_for_learning(
        self,
        data: BaseNoteData,
        note: Note,
        context: Dict[str, Any]
    ) -> None:
        """
        Record extraction for learning loop.

        This method teaches the system from each extraction:
        - Learn Swedish term variants from evidence
        - Record extraction patterns (successful/failed)
        - Calibrate confidence scoring
        - Learn note heading patterns

        Args:
            data: Extracted data with confidence
            note: Original note object
            context: Context dict used for extraction
        """
        if not self.learning_loop:
            return

        # Get agent ID for learning
        agent_id = self.__class__.__name__

        # Record each extracted field
        data_dict = data.dict()
        metadata_fields = {'evidence_pages', 'evidence_quotes', 'confidence'}

        for field_name, value in data_dict.items():
            if field_name in metadata_fields:
                continue

            # Determine if validation passed (high confidence = passed)
            validation_passed = data.confidence > 0.7 and value is not None

            # Record extraction
            self.learning_loop.record_extraction(
                agent_id=agent_id,
                field_name=field_name,
                value=value,
                confidence=data.confidence,
                evidence={
                    "quotes": data.evidence_quotes if hasattr(data, 'evidence_quotes') else [],
                    "pages": data.evidence_pages if hasattr(data, 'evidence_pages') else []
                },
                validation_passed=validation_passed
            )

        # Record note detection pattern
        if note.title:
            note_type = self._get_note_type()
            self.learning_loop.record_note_detection(
                heading=note.title,
                note_type=note_type,
                detection_confidence=data.confidence
            )

    def _get_note_type(self) -> str:
        """
        Get note type for this agent.

        Returns:
            Note type string (depreciation, maintenance, tax)
        """
        agent_name = self.__class__.__name__.lower()
        if 'depreciation' in agent_name:
            return 'depreciation'
        elif 'maintenance' in agent_name:
            return 'maintenance'
        elif 'tax' in agent_name:
            return 'tax'
        else:
            return 'unknown'

    # Abstract methods that subclasses must implement

    @abstractmethod
    def _build_extraction_prompt(
        self,
        note: Note,
        context: Dict[str, Any]
    ) -> str:
        """
        Build extraction prompt for this specific note type.

        Subclasses implement this to create agent-specific prompts
        with relevant Swedish terminology and extraction instructions.

        Args:
            note: Note object with content to extract from
            context: Context dict with balance sheet, income statement data

        Returns:
            Formatted prompt string for LLM
        """
        pass

    @abstractmethod
    def _cross_validate(
        self,
        data: BaseNoteData,
        context: Dict[str, Any]
    ) -> BaseNoteData:
        """
        Cross-validate extracted data with context.

        Subclasses implement this to validate extracted data against
        balance sheet, income statement, or other contextual information.

        Args:
            data: Parsed Pydantic model instance
            context: Context dict

        Returns:
            Validated model instance (may modify confidence or field values)
        """
        pass

    @abstractmethod
    def _get_schema_class(self) -> Type[BaseNoteData]:
        """
        Return the Pydantic schema class for this agent.

        Subclasses implement this to specify which schema to use
        for parsing and validation.

        Returns:
            Pydantic schema class (e.g., DepreciationData)
        """
        pass


# Export base agent
__all__ = ['BaseNoteAgent']
