"""
Note Data Model

Represents a note section in a BRF annual report.

Author: Claude Code
Date: 2025-10-13 (Path B Day 1)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Note:
    """
    Represents a note section in financial statements.

    Notes provide detailed explanations of line items in the balance sheet,
    income statement, and other financial statements.
    """

    number: str
    """Note number (e.g., '1', '5', '5.1')"""

    title: str
    """Note title (e.g., 'Avskrivningar', 'Låneskulder')"""

    content: str
    """Full text content of the note"""

    type: str
    """
    Note classification:
    - depreciation: Avskrivningar
    - tax: Inkomstskatter
    - maintenance: Underhåll/underhållsplan
    - loans: Låneskulder
    - reserves: Fonder/avsättningar
    - interest: Räntekostnader
    - revenue: Intäkter
    - other: Övriga
    """

    pages: List[int] = field(default_factory=list)
    """Page numbers where this note appears"""

    tables: List[Dict[str, Any]] = field(default_factory=list)
    """Tables contained within this note"""

    references_from: List[str] = field(default_factory=list)
    """
    Sections that reference this note.
    Example: ["balance_sheet:Långfristiga skulder", "income_statement:Räntekostnader"]
    """

    references_to: List[str] = field(default_factory=list)
    """
    Other notes referenced by this note.
    Example: ["7", "5.1"] (refers to Note 7 and Note 5.1)
    """

    is_multi_page: bool = False
    """True if note continues across multiple pages"""

    confidence: float = 0.0
    """Confidence score for note detection (0-1)"""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Note(number='{self.number}', title='{self.title}', type='{self.type}', pages={self.pages})"

    def __str__(self) -> str:
        """Human-readable string."""
        return f"Not {self.number} - {self.title}"


@dataclass
class NoteReference:
    """
    Represents a reference to a note from a financial statement or another note.
    """

    note_number: str
    """Number of the referenced note"""

    source: str
    """Where the reference came from (e.g., 'balance_sheet', 'income_statement', 'note_5')"""

    context: str
    """Surrounding text context (e.g., 'Långfristiga skulder: 73,500,000')"""

    line_text: str = ""
    """Full line of text containing the reference"""

    found: bool = True
    """True if the referenced note was found in the document"""

    def __repr__(self) -> str:
        """String representation."""
        return f"NoteReference(note={self.note_number}, source='{self.source}', context='{self.context[:30]}...')"
