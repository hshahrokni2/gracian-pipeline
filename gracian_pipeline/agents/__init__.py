"""
Notes extraction agents for Swedish BRF documents.

Provides specialized agents for extracting information from different
types of notes sections in annual reports.

Author: Claude Code
Date: 2025-10-13 (Path B Day 3)
"""

from .base_note_agent import BaseNoteAgent
from .notes_agents import (
    DepreciationNoteAgent,
    MaintenanceNoteAgent,
    TaxNoteAgent,
)

__all__ = [
    'BaseNoteAgent',
    'DepreciationNoteAgent',
    'MaintenanceNoteAgent',
    'TaxNoteAgent',
]
