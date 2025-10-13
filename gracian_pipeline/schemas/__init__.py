"""
Pydantic schemas for Swedish BRF data extraction.

Provides type-safe schemas with validation for extracted financial data.

Author: Claude Code
Date: 2025-10-13 (Path B Day 3)
"""

from .notes_schemas import (
    BaseNoteData,
    DepreciationData,
    MaintenanceData,
    TaxData,
)

__all__ = [
    'BaseNoteData',
    'DepreciationData',
    'MaintenanceData',
    'TaxData',
]
