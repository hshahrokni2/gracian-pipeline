"""
Cross-reference linking for Swedish BRF document sections.

Builds a graph of references between notes, balance sheet, and income statement
to provide enriched context for agent extraction.

Author: Claude Code
Date: 2025-10-13 (Path B Day 4)
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import re
from ..models.note import Note, NoteReference


class CrossReferenceLinker:
    """
    Cross-reference linker for Swedish BRF documents.

    Extracts and links references between:
    - Balance sheet → Notes (e.g., "Byggnader (Not 1)")
    - Income statement → Notes (e.g., "Räntekostnader (Not 7)")
    - Notes → Notes (e.g., "se Not 5")

    Architecture:
    - Phase 1: Extract references from each section type
    - Phase 2: Build directed graph of references
    - Phase 3: Detect cycles and unresolved references
    - Phase 4: Build enriched context for agent extraction
    """

    def __init__(self):
        """Initialize cross-reference linker."""
        self.reference_graph: Dict[str, List[str]] = {}

        # Regex patterns for note references
        self.patterns = {
            # Primary pattern: (Not 5) or (Not 5.1)
            'parentheses': re.compile(r'\(Not\s+(\d+(?:\.\d+)?)\)', re.IGNORECASE),
            # Multiple refs: (Not 2, Not 7, Not 9)
            'multiple': re.compile(r'\(Not\s+(\d+(?:\.\d+)?(?:\s*,\s*Not\s+\d+(?:\.\d+)?)*)\)', re.IGNORECASE),
            # Swedish phrases: "se Not 7", "enligt Not 5"
            'swedish_ref': re.compile(r'(?:se|enligt|jfr)\s+Not\s+(\d+(?:\.\d+)?)', re.IGNORECASE),
            # Plain: "Not 5" or "Not 5.1" (with word boundary or period/comma)
            'plain': re.compile(r'\bNot\s+(\d+(?:\.\d+)?)(?:\b|\.)', re.IGNORECASE),
            # In-text: "i Not 5.1" (within sentence)
            'in_text': re.compile(r'\s+Not\s+(\d+(?:\.\d+)?)\.?(?:\s|$)', re.IGNORECASE),
        }

    # === Phase 1: Reference Extraction ===

    def extract_balance_sheet_references(
        self,
        balance_sheet_text: str,
        notes: Optional[List[Note]] = None
    ) -> List[NoteReference]:
        """
        Extract note references from balance sheet lines.

        Swedish BRF balance sheets use:
        - Parentheses: "Byggnader (Not 1)"
        - Multiple: "(Not 1, Not 2)"

        Args:
            balance_sheet_text: Balance sheet text
            notes: Optional list of notes to validate against

        Returns:
            List of NoteReference objects
        """
        references = self._extract_references_from_text(
            balance_sheet_text,
            source="balance_sheet"
        )

        # Validate against actual notes if provided
        if notes is not None:
            references = self._validate_references(references, notes)

        return references

    def extract_income_statement_references(
        self,
        income_statement_text: str
    ) -> List[NoteReference]:
        """
        Extract note references from income statement lines.

        Args:
            income_statement_text: Income statement text

        Returns:
            List of NoteReference objects
        """
        return self._extract_references_from_text(
            income_statement_text,
            source="income_statement"
        )

    def extract_note_references(
        self,
        note_text: str,
        source_note: str = "unknown"
    ) -> List[NoteReference]:
        """
        Extract references to other notes from a note's content.

        Swedish patterns:
        - "se Not 7" (see note 7)
        - "enligt Not 5" (according to note 5)
        - "jfr Not 3" (compare note 3)

        Args:
            note_text: Note content text
            source_note: Number of the source note

        Returns:
            List of referenced note numbers
        """
        return self._extract_references_from_text(
            note_text,
            source=f"note_{source_note}"
        )

    def extract_references(self, text: str) -> List[NoteReference]:
        """
        Generic reference extraction from any text.

        Args:
            text: Text to search for references

        Returns:
            List of NoteReference objects
        """
        return self._extract_references_from_text(text, source="unknown")

    def extract_all_references(self, markdown: str) -> List[NoteReference]:
        """
        Extract ALL references from entire document (integration method).

        Args:
            markdown: Full document markdown

        Returns:
            List of all NoteReference objects found
        """
        return self._extract_references_from_text(markdown, source="document")

    def link_cross_references(
        self,
        notes: List[Note],
        markdown: str
    ) -> List[Note]:
        """
        Link notes with their cross-references (integration method).

        Updates notes' references_from and references_to lists.

        Args:
            notes: List of Note objects to link
            markdown: Full document markdown

        Returns:
            List of Note objects with updated reference lists
        """
        # Try to split markdown into sections
        # Simple heuristic: look for RESULTATRÄKNING and BALANSRÄKNING
        balance_sheet_text = ""
        income_statement_text = ""

        if "BALANSRÄKNING" in markdown.upper():
            # Find balance sheet section
            bs_start = markdown.upper().find("BALANSRÄKNING")
            bs_end = markdown.upper().find("NOTER", bs_start)
            if bs_end == -1:
                bs_end = len(markdown)
            balance_sheet_text = markdown[bs_start:bs_end]

        if "RESULTATRÄKNING" in markdown.upper():
            # Find income statement section
            is_start = markdown.upper().find("RESULTATRÄKNING")
            is_end = markdown.upper().find("BALANSRÄKNING", is_start)
            if is_end == -1:
                is_end = markdown.upper().find("NOTER", is_start)
            if is_end == -1:
                is_end = len(markdown)
            income_statement_text = markdown[is_start:is_end]

        # Extract references from each section
        bs_refs = self.extract_balance_sheet_references(balance_sheet_text) if balance_sheet_text else []
        is_refs = self.extract_income_statement_references(income_statement_text) if income_statement_text else []

        # Build map of note number → references pointing to it
        refs_by_target: Dict[str, List[str]] = {}
        for ref in bs_refs:
            refs_by_target.setdefault(ref.note_number, []).append("balance_sheet")
        for ref in is_refs:
            refs_by_target.setdefault(ref.note_number, []).append("income_statement")

        # Update each note's references_from list
        for note in notes:
            note.references_from = list(set(refs_by_target.get(note.number, [])))

            # Extract references FROM this note TO other notes
            note_refs = self.extract_note_references(note.content, source_note=note.number)
            note.references_to = [ref.note_number for ref in note_refs]

        return notes

    # === Phase 2: Graph Building ===

    def build_reference_graph(
        self,
        balance_sheet_text: str,
        income_statement_text: str,
        notes: List[Note]
    ) -> Dict[str, List[str]]:
        """
        Build complete reference graph.

        Graph structure:
        {
            "balance_sheet:line_5": ["note_1"],
            "note_1": ["note_3", "balance_sheet:line_7"],
            "note_3": ["note_1"],  # circular
            "income_statement:line_10": ["note_5"]
        }

        Args:
            balance_sheet_text: Balance sheet text
            income_statement_text: Income statement text
            notes: List of all notes

        Returns:
            Reference graph dictionary
        """
        self.reference_graph = {}

        # Extract all references
        bs_refs = self.extract_balance_sheet_references(balance_sheet_text)
        is_refs = self.extract_income_statement_references(income_statement_text)

        # Add balance sheet → note edges
        for ref in bs_refs:
            key = f"balance_sheet:ref_{ref.note_number}"
            self.reference_graph.setdefault(key, []).append(f"note_{ref.note_number}")

        # Add income statement → note edges
        for ref in is_refs:
            key = f"income_statement:ref_{ref.note_number}"
            self.reference_graph.setdefault(key, []).append(f"note_{ref.note_number}")

        # Add note → note edges
        for note in notes:
            note_refs = self.extract_note_references(note.content, source_note=note.number)
            if note_refs:
                key = f"note_{note.number}"
                self.reference_graph.setdefault(key, []).extend(
                    [f"note_{ref.note_number}" for ref in note_refs]
                )

        return self.reference_graph

    def detect_circular_references(self) -> List[Tuple[str, str]]:
        """
        Detect circular references in graph.

        Uses DFS with recursion stack to find cycles.

        Returns:
            List of (node1, node2) tuples representing cycles
        """
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.reference_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [node])
                elif neighbor in rec_stack:
                    # Found cycle
                    cycles.append((node, neighbor))

            rec_stack.remove(node)

        # Run DFS from each node
        for node in self.reference_graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    # === Phase 3: Context Building ===

    def build_agent_context(
        self,
        agent_id: str,
        notes: List[Note],
        financial_statements: Dict[str, str],
        references: Dict[str, List[str]]
    ) -> str:
        """
        Build enriched context for agent extraction.

        Collects:
        1. Relevant note content
        2. Balance sheet lines referencing the notes
        3. Income statement lines referencing the notes
        4. Related notes (with cycle detection)

        Args:
            agent_id: Agent identifier (e.g., "loans_agent")
            notes: List of all notes
            financial_statements: Dict with "balance_sheet" and "income_statement" keys
            references: Dict mapping categories to note numbers

        Returns:
            Combined context string
        """
        context_parts = []

        # Get relevant notes for this agent
        relevant_note_numbers = []
        for category, note_nums in references.items():
            relevant_note_numbers.extend(note_nums)

        # Add note content
        visited_notes = set()
        for note_num in relevant_note_numbers:
            note = self._find_note_by_number(note_num, notes)
            if note and note.number not in visited_notes:
                context_parts.append(f"=== Not {note.number} - {note.title} ===")
                context_parts.append(note.content)
                visited_notes.add(note.number)

                # Add related notes (with cycle detection)
                related_refs = self.extract_note_references(note.content, source_note=note.number)
                for ref in related_refs:
                    if ref.note_number not in visited_notes:
                        related_note = self._find_note_by_number(ref.note_number, notes)
                        if related_note:
                            context_parts.append(f"\n=== Not {related_note.number} - {related_note.title} (Referenced) ===")
                            context_parts.append(related_note.content)
                            visited_notes.add(related_note.number)

        # Add relevant balance sheet lines
        balance_sheet = financial_statements.get("balance_sheet", "")
        if balance_sheet:
            bs_refs = self.extract_balance_sheet_references(balance_sheet)
            for ref in bs_refs:
                if ref.note_number in relevant_note_numbers:
                    context_parts.append(f"\n=== Balance Sheet Reference ===")
                    context_parts.append(ref.context)

        # Add relevant income statement lines
        income_statement = financial_statements.get("income_statement", "")
        if income_statement:
            is_refs = self.extract_income_statement_references(income_statement)
            for ref in is_refs:
                if ref.note_number in relevant_note_numbers or any(
                    cat in ['interest', 'revenue'] for cat in references.keys()
                ):
                    context_parts.append(f"\n=== Income Statement Reference ===")
                    context_parts.append(ref.context)

        return "\n".join(context_parts)

    # === Helper Methods ===

    def _extract_references_from_text(
        self,
        text: str,
        source: str
    ) -> List[NoteReference]:
        """
        Extract all note references from text using multiple patterns.

        Args:
            text: Text to search
            source: Source identifier (e.g., "balance_sheet", "note_5")

        Returns:
            List of NoteReference objects
        """
        references = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try multiple pattern: (Not 2, Not 7, Not 9)
            multiple_match = self.patterns['multiple'].search(line)
            if multiple_match:
                # Extract all numbers from the match
                numbers_text = multiple_match.group(1)
                numbers = re.findall(r'(\d+(?:\.\d+)?)', numbers_text)
                for num in numbers:
                    references.append(NoteReference(
                        note_number=num,
                        source=source,
                        context=line[:60],  # First 60 chars for context
                        line_text=line,
                        found=False  # Will be updated later if we check against actual notes
                    ))
                continue

            # Try standard parentheses pattern: (Not 5)
            paren_match = self.patterns['parentheses'].search(line)
            if paren_match:
                note_num = paren_match.group(1)
                # Extract context (text before the reference)
                context_end = paren_match.start()
                context = line[:context_end].strip()
                if not context:
                    context = line[:60]

                references.append(NoteReference(
                    note_number=note_num,
                    source=source,
                    context=context,
                    line_text=line,
                    found=False
                ))
                continue

            # Try Swedish reference patterns
            swedish_match = self.patterns['swedish_ref'].search(line)
            if swedish_match:
                note_num = swedish_match.group(1)
                references.append(NoteReference(
                    note_number=note_num,
                    source=source,
                    context=line[:60],
                    line_text=line,
                    found=False
                ))
                continue

            # Try in-text pattern for decimal notes like "i Not 5.1"
            in_text_match = self.patterns['in_text'].search(line)
            if in_text_match:
                note_num = in_text_match.group(1)
                references.append(NoteReference(
                    note_number=note_num,
                    source=source,
                    context=line[:60],
                    line_text=line,
                    found=False
                ))

        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_refs = []
        for ref in references:
            key = (ref.note_number, ref.source)
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)

        return unique_refs

    def _find_note_by_number(
        self,
        note_number: str,
        notes: List[Note]
    ) -> Optional[Note]:
        """
        Find note by number.

        Args:
            note_number: Note number to find
            notes: List of all notes

        Returns:
            Note object if found, None otherwise
        """
        for note in notes:
            if note.number == note_number:
                return note
        return None

    def _find_cycles_involving(self, node_id: str) -> List[Tuple[str, str]]:
        """
        Find all cycles involving a specific node.

        Args:
            node_id: Node to check for cycles

        Returns:
            List of cycles as (node1, node2) tuples
        """
        all_cycles = self.detect_circular_references()
        return [cycle for cycle in all_cycles if node_id in cycle]

    def _validate_references(
        self,
        references: List[NoteReference],
        notes: List[Note]
    ) -> List[NoteReference]:
        """
        Validate references against actual notes and mark found status.

        Args:
            references: List of references to validate
            notes: List of actual notes in document

        Returns:
            Updated references with found status
        """
        note_numbers = {note.number for note in notes}

        for ref in references:
            ref.found = ref.note_number in note_numbers

        return references


# Export
__all__ = ['CrossReferenceLinker']
