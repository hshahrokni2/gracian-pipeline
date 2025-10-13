"""
Path B Integration Layer for Option A

Integrates Path B's production-grade note agents into Option A's parallel orchestrator.
Provides adapter between Option A's generic extraction and Path B's Note-based API.

Author: Claude Code
Date: 2025-10-13 (Integration Day)
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import time

from ..agents.notes_agents import DepreciationNoteAgent, MaintenanceNoteAgent, TaxNoteAgent
from ..core.enhanced_notes_detector import EnhancedNotesDetector
from ..core.cross_reference_linker import CrossReferenceLinker
from ..models.note import Note

logger = logging.getLogger(__name__)


# Agent registry: Maps agent_id → Path B agent class
PATH_B_AGENTS = {
    "notes_depreciation_agent": DepreciationNoteAgent,
    "notes_maintenance_agent": MaintenanceNoteAgent,
    "notes_tax_agent": TaxNoteAgent,
}


def is_path_b_agent(agent_id: str) -> bool:
    """
    Check if agent should use Path B implementation.

    Args:
        agent_id: Agent identifier (e.g., "notes_depreciation_agent")

    Returns:
        True if agent is a Path B note agent
    """
    return agent_id in PATH_B_AGENTS


def extract_with_path_b_agent(
    agent_id: str,
    markdown: str,
    tables: List[Dict],
    page_numbers: List[int]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract using Path B note agent.

    This adapter bridges Option A's context-based extraction with
    Path B's Note-based API.

    Args:
        agent_id: Agent identifier (must be in PATH_B_AGENTS)
        markdown: Document markdown from Docling
        tables: All tables from document
        page_numbers: Pages this agent should focus on

    Returns:
        (result_dict, metadata_dict) same format as Option A's extract_single_agent()
    """
    start_time = time.time()

    try:
        # Step 1: Detect notes in document
        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown, tables)

        if not notes:
            logger.warning(f"{agent_id}: No notes detected in document")
            return _empty_result(agent_id, start_time, "no_notes_detected")

        # Step 2: Link notes with cross-references
        linker = CrossReferenceLinker()
        notes = linker.link_cross_references(notes, markdown)

        # Step 3: Find relevant note for this agent
        note_type_map = {
            "notes_depreciation_agent": "depreciation",
            "notes_maintenance_agent": "maintenance",
            "notes_tax_agent": "tax",
        }

        target_note_type = note_type_map.get(agent_id)
        relevant_note = _find_relevant_note(notes, target_note_type, agent_id)

        if not relevant_note:
            logger.info(f"{agent_id}: No relevant note found (searched for type={target_note_type})")
            return _empty_result(agent_id, start_time, "no_relevant_note")

        # Step 4: Build context for Path B agent
        context = _build_path_b_context(markdown, tables, relevant_note)

        # Step 5: Initialize Path B agent
        agent_class = PATH_B_AGENTS[agent_id]
        agent = agent_class()

        # Step 6: Extract with Path B agent
        result = agent.extract(relevant_note, context)

        # Step 7: Calculate metadata
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Count tokens (rough estimate based on content length)
        token_count = len(relevant_note.content) // 4 + 200  # Rough estimate

        metadata = {
            "status": "success",
            "agent_id": agent_id,
            "token_count": token_count,
            "latency_ms": elapsed_ms,
            "pages_used": page_numbers,
            "note_number": relevant_note.number,
            "note_type": relevant_note.type,
            "integration_layer": "path_b",
        }

        return result, metadata

    except Exception as e:
        logger.error(f"{agent_id} Path B extraction failed: {e}")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return _empty_result(agent_id, start_time, f"error: {str(e)}")


def _find_relevant_note(notes: List[Note], target_type: str, agent_id: str) -> Optional[Note]:
    """
    Find note relevant to this agent.

    Strategy:
    1. Exact match on note type
    2. Keyword match on note title
    3. Keyword match on note content
    4. Fallback: First note with substantial content

    Args:
        notes: List of detected notes
        target_type: Expected note type (e.g., "depreciation")
        agent_id: Agent identifier for fallback keywords

    Returns:
        Most relevant Note or None if no match
    """
    # Strategy 1: Exact type match
    for note in notes:
        if note.type == target_type:
            return note

    # Strategy 2: Title keyword match
    keywords_map = {
        "depreciation": ["avskrivning", "depreciation"],
        "maintenance": ["underhåll", "maintenance", "underhållsplan"],
        "tax": ["skatt", "tax", "inkomstskatt"],
    }

    keywords = keywords_map.get(target_type, [])

    for note in notes:
        if note.title:
            title_lower = note.title.lower()
            if any(kw in title_lower for kw in keywords):
                logger.info(f"{agent_id}: Found note by title match: {note.title}")
                return note

    # Strategy 3: Content keyword match
    for note in notes:
        content_lower = note.content.lower()
        if any(kw in content_lower for kw in keywords):
            logger.info(f"{agent_id}: Found note by content keyword match")
            return note

    # Strategy 4: Fallback to first substantial note
    for note in notes:
        if len(note.content) > 100:  # Has substantial content
            logger.warning(f"{agent_id}: Using fallback note (no type/keyword match)")
            return note

    return None


def _build_path_b_context(
    markdown: str,
    tables: List[Dict],
    note: Note
) -> Dict[str, Any]:
    """
    Build context dict for Path B agent.

    Extracts relevant sections from markdown to provide:
    - balance_sheet_snippet: For depreciation/tax cross-validation
    - income_statement_snippet: For tax cross-validation
    - balance_sheet_data: Structured data if available

    Args:
        markdown: Full document markdown
        tables: All tables
        note: The note being processed

    Returns:
        Context dict for Path B agent
    """
    context = {
        "balance_sheet_snippet": _extract_section(markdown, ["BALANSRÄKNING", "Balance Sheet"]),
        "income_statement_snippet": _extract_section(markdown, ["RESULTATRÄKNING", "Income Statement"]),
        "balance_sheet_data": {},  # Could extract from tables in future
        "income_statement_data": {},  # Could extract from tables in future
        "references_from": note.references_from if hasattr(note, 'references_from') else [],
        "references_to": note.references_to if hasattr(note, 'references_to') else [],
    }

    return context


def _extract_section(markdown: str, section_headings: List[str]) -> str:
    """
    Extract section from markdown by heading.

    Args:
        markdown: Full markdown text
        section_headings: List of possible section headings (Swedish + English)

    Returns:
        Section content (max 2000 chars) or "Not found"
    """
    lines = markdown.split('\n')

    # Find section start
    start_idx = None
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if any(heading.upper() in line_upper for heading in section_headings):
            start_idx = i
            break

    if start_idx is None:
        return "Not found"

    # Extract next 50 lines (roughly 1-2 pages)
    section_lines = lines[start_idx:start_idx + 50]
    section_text = '\n'.join(section_lines)

    # Limit to 2000 chars
    return section_text[:2000]


def _empty_result(agent_id: str, start_time: float, reason: str) -> Tuple[Dict, Dict]:
    """
    Return empty result with metadata.

    Args:
        agent_id: Agent identifier
        start_time: When extraction started
        reason: Why empty result (for logging)

    Returns:
        (empty_dict, metadata_dict)
    """
    elapsed_ms = int((time.time() - start_time) * 1000)

    return {}, {
        "status": "empty",
        "agent_id": agent_id,
        "token_count": 0,
        "latency_ms": elapsed_ms,
        "pages_used": [],
        "reason": reason,
        "integration_layer": "path_b",
    }


# Export public API
__all__ = [
    'is_path_b_agent',
    'extract_with_path_b_agent',
    'PATH_B_AGENTS',
]
