#!/usr/bin/env python3
"""
Tests for Schema V7.0 ExtractionField enhancements.

Tests the 6 new fields added in v7.0:
- evidence_pages: List[int]
- extraction_method: Optional[str]
- model_used: Optional[str]
- validation_status: Optional[str]
- alternative_values: List[Any]
- extraction_timestamp: Optional[datetime]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from schema_v7 import (
    ExtractionField,
    StringField,
    NumberField,
    IntegerField,
    BooleanField,
    DateField,
    ListField,
    DictField
)


# ============================================================
# Test ExtractionField Basic Functionality
# ============================================================

def test_extraction_field_basic():
    """Test basic ExtractionField creation with core fields"""
    field = ExtractionField(
        value="Test Value",
        confidence=0.95,
        source="Page 1"
    )
    assert field.value == "Test Value"
    assert field.confidence == 0.95
    assert field.source == "Page 1"
    assert field.evidence_pages == []  # Default empty list
    assert field.extraction_method is None
    assert field.model_used is None


def test_extraction_field_with_evidence_pages():
    """Test evidence_pages field"""
    field = ExtractionField(
        value="Test",
        evidence_pages=[1, 2, 3]
    )
    assert field.evidence_pages == [1, 2, 3]
    assert len(field.evidence_pages) == 3


def test_extraction_field_with_extraction_method():
    """Test extraction_method field"""
    methods = ["table_extraction", "text_extraction", "calculated", "manual"]

    for method in methods:
        field = ExtractionField(value="Test", extraction_method=method)
        assert field.extraction_method == method


def test_extraction_field_with_model_used():
    """Test model_used field"""
    models = ["gpt-4o", "gpt-4o-mini", "docling", "gemini-2.5-pro", "manual"]

    for model in models:
        field = ExtractionField(value="Test", model_used=model)
        assert field.model_used == model


def test_extraction_field_with_validation_status():
    """Test validation_status field"""
    statuses = ["valid", "warning", "error", "unknown"]

    for status in statuses:
        field = ExtractionField(value="Test", validation_status=status)
        assert field.validation_status == status


def test_extraction_field_with_alternative_values():
    """Test alternative_values field"""
    field = ExtractionField(
        value="Primary Value",
        alternative_values=["Alt 1", "Alt 2", "Alt 3"]
    )
    assert field.value == "Primary Value"
    assert field.alternative_values == ["Alt 1", "Alt 2", "Alt 3"]
    assert len(field.alternative_values) == 3


def test_extraction_field_with_timestamp():
    """Test extraction_timestamp field"""
    now = datetime.utcnow()
    field = ExtractionField(value="Test", extraction_timestamp=now)
    assert field.extraction_timestamp == now
    assert isinstance(field.extraction_timestamp, datetime)


def test_extraction_field_all_enhancements():
    """Test ExtractionField with all v7.0 enhancements"""
    now = datetime.utcnow()
    field = ExtractionField(
        value="Complete Test",
        confidence=0.92,
        source="Page 5, Table 2",
        evidence_pages=[5, 6],
        extraction_method="table_extraction",
        model_used="gpt-4o",
        validation_status="valid",
        alternative_values=["Alt1", "Alt2"],
        extraction_timestamp=now
    )

    # Core fields
    assert field.value == "Complete Test"
    assert field.confidence == 0.92
    assert field.source == "Page 5, Table 2"

    # Enhanced fields
    assert field.evidence_pages == [5, 6]
    assert field.extraction_method == "table_extraction"
    assert field.model_used == "gpt-4o"
    assert field.validation_status == "valid"
    assert field.alternative_values == ["Alt1", "Alt2"]
    assert field.extraction_timestamp == now


# ============================================================
# Test Typed Field Classes
# ============================================================

def test_string_field_inheritance():
    """Test StringField inherits all ExtractionField enhancements"""
    field = StringField(
        value="Test String",
        confidence=0.88,
        evidence_pages=[1],
        extraction_method="text_extraction",
        model_used="gpt-4o-mini"
    )
    assert field.value == "Test String"
    assert field.confidence == 0.88
    assert field.evidence_pages == [1]
    assert field.extraction_method == "text_extraction"
    assert field.model_used == "gpt-4o-mini"


def test_number_field_inheritance():
    """Test NumberField inherits all ExtractionField enhancements"""
    field = NumberField(
        value=12345.67,
        confidence=0.95,
        evidence_pages=[2, 3],
        extraction_method="table_extraction",
        validation_status="valid"
    )
    assert field.value == 12345.67
    assert field.confidence == 0.95
    assert field.evidence_pages == [2, 3]
    assert field.validation_status == "valid"


def test_integer_field_inheritance():
    """Test IntegerField inherits all ExtractionField enhancements"""
    field = IntegerField(
        value=42,
        evidence_pages=[7],
        extraction_method="calculated",
        model_used="manual"
    )
    assert field.value == 42
    assert field.evidence_pages == [7]
    assert field.extraction_method == "calculated"


def test_boolean_field_inheritance():
    """Test BooleanField inherits all ExtractionField enhancements"""
    field = BooleanField(
        value=True,
        confidence=1.0,
        evidence_pages=[10],
        validation_status="valid"
    )
    assert field.value is True
    assert field.confidence == 1.0
    assert field.evidence_pages == [10]


def test_date_field_inheritance():
    """Test DateField inherits all ExtractionField enhancements"""
    field = DateField(
        value="2024-10-13",
        confidence=0.90,
        evidence_pages=[1],
        extraction_method="text_extraction"
    )
    assert field.value == "2024-10-13"
    assert field.confidence == 0.90
    assert field.evidence_pages == [1]


def test_list_field_inheritance():
    """Test ListField inherits all ExtractionField enhancements"""
    field = ListField(
        value=["item1", "item2", "item3"],
        confidence=0.85,
        evidence_pages=[3, 4],
        extraction_method="text_extraction"
    )
    assert field.value == ["item1", "item2", "item3"]
    assert len(field.value) == 3
    assert field.evidence_pages == [3, 4]


def test_dict_field_inheritance():
    """Test DictField inherits all ExtractionField enhancements"""
    field = DictField(
        value={"key1": "value1", "key2": "value2"},
        confidence=0.92,
        evidence_pages=[5],
        extraction_method="table_extraction"
    )
    assert field.value == {"key1": "value1", "key2": "value2"}
    assert field.evidence_pages == [5]


# ============================================================
# Test Edge Cases
# ============================================================

def test_confidence_bounds():
    """Test confidence field respects 0.0-1.0 bounds"""
    # Valid confidence
    field = ExtractionField(value="Test", confidence=0.5)
    assert field.confidence == 0.5

    # Edge cases
    field_min = ExtractionField(value="Test", confidence=0.0)
    assert field_min.confidence == 0.0

    field_max = ExtractionField(value="Test", confidence=1.0)
    assert field_max.confidence == 1.0

    # Invalid confidence should raise ValidationError
    with pytest.raises(Exception):  # Pydantic ValidationError
        ExtractionField(value="Test", confidence=1.5)

    with pytest.raises(Exception):
        ExtractionField(value="Test", confidence=-0.1)


def test_empty_alternative_values():
    """Test alternative_values defaults to empty list"""
    field = ExtractionField(value="Test")
    assert field.alternative_values == []
    assert isinstance(field.alternative_values, list)


def test_none_timestamp():
    """Test extraction_timestamp can be None"""
    field = ExtractionField(value="Test")
    assert field.extraction_timestamp is None


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
