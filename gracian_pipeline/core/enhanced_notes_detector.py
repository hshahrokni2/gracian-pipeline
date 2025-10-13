"""
Enhanced Notes Detector for Swedish BRF Annual Reports

Detects and parses notes sections with Swedish terminology awareness.
Handles multiple note numbering formats and multi-page continuations.

Author: Claude Code
Date: 2025-10-13 (Path B Day 2)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..models.note import Note, NoteReference


class EnhancedNotesDetector:
    """
    Detect and parse notes sections in Swedish BRF documents.

    Features:
    - Multi-pattern recognition (Not, NOTE, Tillägg, etc.)
    - Case-insensitive with whitespace tolerance
    - Type classification (depreciation, tax, maintenance, loans)
    - Multi-page note merging
    - Cross-reference extraction
    """

    def __init__(self):
        """Initialize with all Swedish BRF note patterns (Step 3)."""
        # Compile patterns in order of specificity (most specific first)
        # IMPORTANT: Use ^ to match only at start of line (not inline references)
        self.note_patterns = [
            # Pattern 1: "Not till punkt X" (most specific)
            (re.compile(r'^\s*Not\s+till\s+punkt\s+(\d+)', re.IGNORECASE), 'note_to_point'),

            # Pattern 2: Standard "Not X" or "NOTE X" (E is optional)
            (re.compile(r'^\s*NOTE?\s+(\d+)', re.IGNORECASE), 'standard'),

            # Pattern 3: "Tillägg X" (supplement)
            (re.compile(r'^\s*Tillägg\s+(\d+)', re.IGNORECASE), 'supplement'),
        ]

        # Patterns for reference extraction (in parentheses or inline)
        self.reference_patterns = [
            # Pattern: "(Not 5)" or "(Not 5, Not 7)"
            re.compile(r'\(Not\s+(\d+(?:,\s*Not\s+\d+)*)\)', re.IGNORECASE),

            # Pattern: "se Not 5" or "enligt Not 7"
            re.compile(r'(?:se|enligt|jfr)\s+Not\s+(\d+)', re.IGNORECASE),
        ]

        self.note_type_keywords = {}  # Will populate in Step 5

    def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
        """
        Detect all notes with multi-page continuation support (Step 4).

        Args:
            markdown: Document text in markdown format
            tables: Optional list of tables from Docling

        Returns:
            List of Note objects with detected notes
        """
        notes = []
        lines = markdown.split('\n')

        for i, line in enumerate(lines):
            # Skip if line contains a parenthesized reference like "(Not 1)"
            # These are NOT note headers, they are references
            if re.search(r'\(\s*Not\s+\d+\s*\)', line, re.IGNORECASE):
                continue

            # Check for continuation marker first (Step 4)
            continuation_match = re.search(r'Not\s+(\d+)\s*\(forts\.?\)', line, re.IGNORECASE)
            if continuation_match:
                note_number = continuation_match.group(1)

                # Find existing note with this number
                existing_note = next((n for n in notes if n.number == note_number), None)
                if existing_note:
                    # Merge content
                    continuation_content = self._extract_content(lines, i)
                    existing_note.content += '\n\n' + continuation_content
                    existing_note.is_multi_page = True
                    continue

            # Regular note detection
            for pattern, pattern_name in self.note_patterns:
                match = pattern.search(line)
                if match:
                    note_number = match.group(1)

                    # Check if note already exists (duplicate detection)
                    if any(n.number == note_number for n in notes):
                        continue

                    # Extract title (text after dash or colon)
                    title = self._extract_title(line, match.end())

                    # Extract content (lines following note header)
                    content = self._extract_content(lines, i)

                    # Classify note type
                    note_type = self._classify_note_type(title, content)

                    # Create Note object
                    note = Note(
                        number=note_number,
                        title=title,
                        content=content,
                        type=note_type,
                        pages=[],
                        is_multi_page=False
                    )
                    notes.append(note)
                    break  # Found match, don't check other patterns

        return notes

    def _extract_title(self, line: str, start_pos: int) -> str:
        """Extract note title from header line."""
        # Look for title after dash or colon
        title_match = re.search(r'[-:]\s*(.+)', line[start_pos:])
        if title_match:
            return title_match.group(1).strip()
        return ""

    def _extract_content(self, lines: List[str], start_index: int) -> str:
        """Extract content lines following note header."""
        content_lines = []

        # Start from line after header
        for i in range(start_index + 1, len(lines)):
            line = lines[i].strip()

            # Stop if we hit another note header
            if self._is_note_header(line):
                break

            # Stop if we hit a major section header (e.g., "BALANSRÄKNING")
            # But NOT bullet points like "- SEB: 30,000,000 SEK"
            if line.isupper() and len(line) > 10 and not line.startswith(('-', '•', '*', '·')):
                break

            # Add non-empty lines to content
            if line:
                content_lines.append(line)

        return '\n'.join(content_lines)

    def _is_note_header(self, line: str) -> bool:
        """Check if line is a note header."""
        for pattern, _ in self.note_patterns:
            if pattern.search(line):
                return True
        return False

    def _classify_note_type(self, title: str, content: str) -> str:
        """
        Classify note type based on keywords (basic version for Step 2).

        Will be enhanced in Step 5 with comprehensive keywords.
        """
        text = (title + " " + content).lower()

        # Simple keyword matching for now
        if "avskrivning" in text:
            return "depreciation"
        elif "skatt" in text:
            return "tax"
        elif "underhåll" in text:
            return "maintenance"
        elif "lån" in text or "kredit" in text:
            return "loans"
        elif "fond" in text or "avsättning" in text:
            return "reserves"
        elif "ränt" in text:
            return "interest"
        elif "intäkt" in text:
            return "revenue"
        else:
            return "other"

    def extract_references(self, text: str) -> List[NoteReference]:
        """
        Extract note references from text (Step 3).

        Args:
            text: Text to scan for references (e.g., balance sheet)

        Returns:
            List of NoteReference objects
        """
        references = []

        for pattern in self.reference_patterns:
            for match in pattern.finditer(text):
                # Extract note numbers (handle comma-separated lists)
                note_numbers_str = match.group(1)
                note_numbers = re.findall(r'\d+', note_numbers_str)

                # Extract smart context: field name before the reference
                # Look for the start of the line or sentence
                line_start = text.rfind('\n', 0, match.start()) + 1
                line_before_ref = text[line_start:match.start()]

                # Extract field name (text before colon and numbers)
                # E.g., "Långfristiga skulder: 10,500,000 (Not 5)" -> "Långfristiga skulder"
                context_match = re.search(r'([A-Za-zÅÄÖåäö\s]+):\s*[\d,]+', line_before_ref)
                if context_match:
                    context = context_match.group(1).strip()
                else:
                    # Fallback: extract all Swedish text at end of line
                    context_match2 = re.search(r'([A-Za-zÅÄÖåäö\s]+)\s*$', line_before_ref)
                    if context_match2:
                        context = context_match2.group(1).strip()
                    else:
                        context = line_before_ref.strip()

                # Create NoteReference for each number
                for num in note_numbers:
                    ref = NoteReference(
                        note_number=num,
                        source="unknown",  # Will be set by caller
                        context=context,
                        line_text=text[match.start():match.end()]
                    )
                    references.append(ref)

        return references
