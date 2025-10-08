"""
Base field classes for extraction with confidence tracking.

This module provides the foundational ExtractionField classes that enable:
- Per-field confidence scoring (0.0-1.0)
- Source tracking (which extraction method was used)
- Evidence tracking (which PDF pages contained the data)
- Multi-source aggregation (when multiple methods extract the same field)
- Validation status tracking (valid/warning/error)

Design Philosophy:
- NEVER null data due to validation failures
- Preserve both extracted and calculated values
- Track all extraction attempts and methods
- Enable tolerant validation with warnings instead of rejections
"""

from __future__ import annotations

from typing import Any, Optional, List, Dict, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from decimal import Decimal


class ExtractionField(BaseModel):
    """
    Base class for all extracted fields with confidence tracking.

    This is the foundation for tolerant validation - we track confidence,
    source, and evidence for every field, allowing us to preserve data
    even when validation warnings occur.

    Attributes:
        value: The extracted value (type-specific in subclasses)
        confidence: Confidence score 0.0-1.0 (0.0 = not found, 1.0 = perfect)
        source: Extraction method used ("structured_table"|"regex"|"vision_llm"|"calculated")
        evidence_pages: List of PDF pages where data was found
        extraction_method: Detailed method name (e.g., "hierarchical_table_parser")
        model_used: For LLM extractions, which model (e.g., "gpt-4o", "gemini-2.5-pro")
        validation_status: Validation result ("valid"|"warning"|"error"|"unknown")
        alternative_values: List of other extractions for this field (multi-source)
        extraction_timestamp: When this field was extracted
    """

    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")

    # Provenance tracking
    source: Optional[str] = Field(
        None,
        description="Extraction method: structured_table|regex|vision_llm|calculated|not_found"
    )
    evidence_pages: List[int] = Field(
        default_factory=list,
        description="PDF pages where data was found (1-indexed)"
    )

    # Detailed metadata
    extraction_method: Optional[str] = Field(
        None,
        description="Detailed method name (e.g., hierarchical_table_parser, swedish_regex)"
    )
    model_used: Optional[str] = Field(
        None,
        description="For LLM extractions: gpt-4o|gemini-2.5-pro|qwen-2.5-vl|etc"
    )

    # Validation tracking
    validation_status: Optional[str] = Field(
        None,
        description="Validation result: valid|warning|error|unknown"
    )

    # Multi-source tracking
    alternative_values: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Other extractions for this field: [{value, confidence, source}, ...]"
    )

    # Timestamp
    extraction_timestamp: Optional[datetime] = Field(
        None,
        description="When this field was extracted"
    )

    def add_alternative(self, value: Any, confidence: float, source: str, **kwargs) -> None:
        """
        Track an alternative extraction for this field.

        Used when multiple extraction methods return different values for the same field.
        Enables multi-source aggregation and consensus-building.

        Args:
            value: The alternative extracted value
            confidence: Confidence score for this alternative
            source: Extraction method that produced this alternative
            **kwargs: Additional metadata (extraction_method, model_used, etc.)
        """
        alternative = {
            "value": value,
            "confidence": confidence,
            "source": source,
            **kwargs
        }
        self.alternative_values.append(alternative)

    def resolve_best_value(self) -> None:
        """
        Resolve best value from multiple extractions.

        Strategy:
        - If all values agree: Use highest confidence
        - If values disagree: Use weighted vote, apply disagreement penalty

        This method updates self.value, self.confidence, and self.source
        based on aggregation of all alternatives.
        """
        if not self.alternative_values:
            return

        # Collect all extractions (current + alternatives)
        all_extractions = [
            {
                "value": self.value,
                "confidence": self.confidence,
                "source": self.source
            }
        ] + self.alternative_values

        # Check if all agree
        values = [e["value"] for e in all_extractions]
        if self._all_values_agree(values):
            # Agreement: Use highest confidence, boost for consensus
            best = max(all_extractions, key=lambda x: x["confidence"])
            num_sources = len(all_extractions)
            boost = min(0.10, num_sources * 0.03)  # +3% per source, max +10%

            self.value = best["value"]
            self.confidence = min(1.0, best["confidence"] + boost)
            self.source = "multi_source_consensus"
        else:
            # Disagreement: Weighted vote
            weighted_sum = 0.0
            total_weight = 0.0

            for extraction in all_extractions:
                weight = extraction["confidence"]
                # Convert value to numeric if possible for weighted average
                try:
                    numeric_value = float(extraction["value"])
                    weighted_sum += numeric_value * weight
                    total_weight += weight
                except (TypeError, ValueError):
                    # Non-numeric value, use highest confidence value
                    pass

            if total_weight > 0:
                # Numeric weighted average
                self.value = weighted_sum / total_weight
                self.confidence = total_weight / len(all_extractions)
                # Apply disagreement penalty
                self.confidence = max(0.0, self.confidence - 0.15)
                self.source = "multi_source_weighted"
            else:
                # Non-numeric, use highest confidence
                best = max(all_extractions, key=lambda x: x["confidence"])
                self.value = best["value"]
                self.confidence = best["confidence"] - 0.15  # Disagreement penalty
                self.source = "multi_source_disagreement"

    def _all_values_agree(self, values: List[Any]) -> bool:
        """Check if all values in list are effectively equal."""
        if not values:
            return True

        # Handle numeric values with tolerance
        try:
            numeric_values = [float(v) for v in values if v is not None]
            if len(numeric_values) < 2:
                return True

            # Check if all within 1% of each other
            mean = sum(numeric_values) / len(numeric_values)
            tolerance = abs(mean * 0.01)
            return all(abs(v - mean) <= tolerance for v in numeric_values)
        except (TypeError, ValueError):
            # Non-numeric: strict equality
            first = values[0]
            return all(v == first for v in values)

    class Config:
        arbitrary_types_allowed = True


class StringField(ExtractionField):
    """String-valued extraction field."""
    value: Optional[str] = None

    @field_validator('value')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from strings."""
        if v is not None and isinstance(v, str):
            return v.strip()
        return v


class NumberField(ExtractionField):
    """
    Numeric extraction field (float/int/Decimal).

    Supports:
    - Swedish number formatting (space as thousands separator, comma as decimal)
    - Automatic conversion to float
    - Preservation of original string representation
    - Tolerant parsing with fallback
    """
    value: Optional[Union[float, int, Decimal]] = None
    original_string: Optional[str] = Field(
        None,
        description="Original string representation before parsing"
    )

    @field_validator('value', mode='before')
    @classmethod
    def parse_number(cls, v: Any) -> Optional[Union[float, int, Decimal]]:
        """
        Parse number from various formats.

        Handles:
        - Swedish format: "1 234 567,89" → 1234567.89
        - Standard format: "1,234,567.89" → 1234567.89
        - Already numeric: pass through
        """
        if v is None:
            return None

        if isinstance(v, (int, float, Decimal)):
            return v

        if isinstance(v, str):
            # Remove whitespace and common separators
            cleaned = v.replace(' ', '').replace('\xa0', '')  # \xa0 = non-breaking space

            # Try Swedish format first (comma as decimal)
            if ',' in cleaned and '.' not in cleaned:
                try:
                    return float(cleaned.replace(',', '.'))
                except ValueError:
                    pass

            # Try standard format (period as decimal)
            try:
                # Remove thousand separators
                cleaned = cleaned.replace(',', '')
                return float(cleaned)
            except ValueError:
                pass

        return None


class ListField(ExtractionField):
    """List-valued extraction field (for board members, apartments, etc)."""
    value: List[Any] = Field(default_factory=list)

    @field_validator('value', mode='before')
    @classmethod
    def ensure_list(cls, v: Any) -> List[Any]:
        """Ensure value is a list."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # Convert single value to list
        return [v]


class BooleanField(ExtractionField):
    """Boolean extraction field."""
    value: Optional[bool] = None

    @field_validator('value', mode='before')
    @classmethod
    def parse_boolean(cls, v: Any) -> Optional[bool]:
        """Parse boolean from various formats (ja/nej, yes/no, true/false, 1/0)."""
        if v is None:
            return None

        if isinstance(v, bool):
            return v

        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ('ja', 'yes', 'true', '1', 'sant'):
                return True
            if v_lower in ('nej', 'no', 'false', '0', 'falskt'):
                return False

        if isinstance(v, (int, float)):
            return bool(v)

        return None


class DateField(ExtractionField):
    """Date extraction field."""
    value: Optional[datetime] = None
    date_format: Optional[str] = Field(
        None,
        description="Format string used to parse date (e.g., '%Y-%m-%d')"
    )

    @field_validator('value', mode='before')
    @classmethod
    def parse_date(cls, v: Any) -> Optional[datetime]:
        """
        Parse date from various formats.

        Tries:
        - ISO format: 2024-03-15
        - Swedish format: 2024-03-15, 15/3/2024, 15 mars 2024
        - Already datetime: pass through
        """
        if v is None:
            return None

        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            # Try common formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%d.%m.%Y',
                '%Y.%m.%d',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue

        return None


class DictField(ExtractionField):
    """Dictionary-valued extraction field (for complex nested data)."""
    value: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator('value', mode='before')
    @classmethod
    def ensure_dict(cls, v: Any) -> Optional[Dict[str, Any]]:
        """Ensure value is a dictionary."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        return {}


# Convenience type aliases for common field types
TextField = StringField
IntegerField = NumberField
FloatField = NumberField
DecimalField = NumberField
ArrayField = ListField
ObjectField = DictField
