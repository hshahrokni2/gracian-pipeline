# Week 1 Day 4 - CrossReferenceLinker Ultrathinking Strategy

**Date**: 2025-10-13
**Target**: Build CrossReferenceLinker to pass 7 cross-reference tests (15/29 → 22/29)
**Time Budget**: 6 hours
**Current Status**: 15/29 tests passing (52%), ready to implement linking layer

---

## 🎯 Strategic Overview

### The Big Picture

Day 4 is about **connecting the dots** between different sections of the document:
- Notes reference balance sheet items (e.g., "Not 1: Byggnader och mark")
- Balance sheet references notes (e.g., "Byggnader och mark₁")
- Notes reference each other (e.g., "Enligt not 5...")
- Income statement references notes (e.g., "Avskrivningar₃")

**Core Insight**: We're building a **graph of references** that enriches extraction context.

**Why This Matters**:
- Agents need context from MULTIPLE sections to extract accurately
- Example: LoansAgent needs balance sheet data + note text + income statement interest
- Without linking: Agents work in isolation, miss cross-validation opportunities
- With linking: Agents get enriched context, confidence scores improve by 0.1-0.2

---

## 📊 Test Analysis: What We Need to Pass

### Test Breakdown (7 tests, 0/7 currently passing)

#### **Category 1: Basic Linking (2 tests)**

**1. test_balance_sheet_to_note_linking**
- **Assertion**: Extract "Byggnader och mark₁" → detect reference to Note 1
- **Input**: Balance sheet snippet with superscript/subscript note markers
- **Expected Output**: `{"line": "Byggnader och mark", "note_refs": [1]}`
- **Complexity**: 🟢 LOW - Pattern matching for note markers

**2. test_income_statement_to_note_linking**
- **Assertion**: Extract "Avskrivningar₃" → detect reference to Note 3
- **Input**: Income statement snippet
- **Expected Output**: `{"line": "Avskrivningar", "note_refs": [3]}`
- **Complexity**: 🟢 LOW - Similar to test 1

#### **Category 2: Cross-Document Linking (1 test)**

**3. test_note_to_note_reference**
- **Assertion**: Extract "Enligt not 5..." from Note 3 → detect reference to Note 5
- **Input**: Note text with Swedish reference patterns
- **Expected Output**: `{"note_id": 3, "references": [5]}`
- **Complexity**: 🟡 MEDIUM - Swedish phrase patterns ("enligt not", "se not", "jfr not")

#### **Category 3: Context Building (1 test)**

**4. test_build_enriched_context_for_loans_agent**
- **Assertion**: Given Note 8 (loans), return enriched context with:
  - Note text
  - Referenced balance sheet snippets (Långfristiga skulder)
  - Referenced income statement snippets (Räntekostnader)
  - Related notes (if Note 8 references Note 3)
- **Input**: Note metadata, all sections data
- **Expected Output**: `{"note_text": "...", "balance_sheet_context": "...", "income_statement_context": "...", "related_notes": [...]}`
- **Complexity**: 🔴 HIGH - Integration of all reference extraction + context building

#### **Category 4: Edge Cases (3 tests)**

**5. test_circular_reference_handling**
- **Assertion**: Note 3 → Note 5 → Note 3 (circular) should not crash
- **Expected**: Detect cycle, return both notes but mark as circular
- **Complexity**: 🟡 MEDIUM - Graph cycle detection

**6. test_missing_note_reference_handling**
- **Assertion**: "Se not 99" where Note 99 doesn't exist → graceful handling
- **Expected**: Return reference but mark as unresolved
- **Complexity**: 🟢 LOW - Error handling

**7. test_multiple_references_same_line**
- **Assertion**: "Byggnader₁ och inventarier₂" → detect both [1, 2]
- **Expected**: `{"line": "Byggnader och inventarier", "note_refs": [1, 2]}`
- **Complexity**: 🟢 LOW - Multiple pattern matches

---

## 🏗️ Architecture Design

### Key Design Decision: Leverage Existing Code

**Critical Insight from Day 3 Complete Doc**:
> "Use EnhancedNotesDetector's `extract_references()` method (already implemented!)"

Let me verify what's already available:

**EnhancedNotesDetector** (Day 2 implementation):
- Already has `extract_references()` method
- Already detects note patterns in Swedish documents
- **We can reuse this!** 🎯

### Proposed Architecture

```python
class CrossReferenceLinker:
    """
    Builds a graph of cross-references between document sections.

    Architecture Pattern: Builder + Graph
    - Builder: Incrementally construct reference graph
    - Graph: Nodes = sections, Edges = references
    """

    def __init__(self, notes_detector: EnhancedNotesDetector):
        """Inject EnhancedNotesDetector for code reuse."""
        self.notes_detector = notes_detector
        self.reference_graph = {}  # {section_id: [referenced_section_ids]}

    # === Phase 1: Reference Extraction (Tests 1-3, 6-7) ===

    def extract_balance_sheet_references(
        self,
        balance_sheet: Dict[str, Any]
    ) -> List[Dict]:
        """
        Extract note references from balance sheet lines.
        Pattern: "Text₁" or "Text¹" or "Text (not 1)"
        """
        pass

    def extract_income_statement_references(
        self,
        income_statement: Dict[str, Any]
    ) -> List[Dict]:
        """
        Extract note references from income statement lines.
        Same patterns as balance sheet.
        """
        pass

    def extract_note_to_note_references(
        self,
        note: Note
    ) -> List[int]:
        """
        Extract note-to-note references.
        Swedish patterns: "enligt not X", "se not X", "jfr not X"

        **REUSE**: Call self.notes_detector.extract_references()
        """
        pass

    # === Phase 2: Graph Building (Tests 4-5) ===

    def build_reference_graph(
        self,
        balance_sheet: Dict,
        income_statement: Dict,
        notes: List[Note]
    ) -> Dict[str, List[str]]:
        """
        Build complete reference graph.

        Returns:
            {
                "balance_sheet_line_1": ["note_1"],
                "note_1": ["note_5", "balance_sheet_line_3"],
                "note_5": ["note_1"]  # circular
            }
        """
        pass

    def detect_circular_references(self) -> List[Tuple[str, str]]:
        """
        Detect cycles in reference graph.
        Algorithm: DFS with visited tracking
        """
        pass

    # === Phase 3: Context Building (Test 4) ===

    def build_enriched_context(
        self,
        note: Note,
        balance_sheet: Dict,
        income_statement: Dict,
        all_notes: List[Note]
    ) -> Dict[str, Any]:
        """
        Build enriched context for agent extraction.

        Returns:
            {
                "note_text": note.content,
                "note_metadata": {...},
                "balance_sheet_context": "Relevant BS snippets",
                "income_statement_context": "Relevant IS snippets",
                "related_notes": [Note(...), Note(...)],
                "reference_metadata": {
                    "total_references": 3,
                    "circular_references": [],
                    "unresolved_references": []
                }
            }
        """
        pass

    # === Helper Methods ===

    def _extract_note_markers(self, text: str) -> List[int]:
        """
        Extract note numbers from markers.
        Patterns:
        - Superscript: ₁ ² ³ ⁴ ⁵
        - Subscript: ₁ ₂ ₃ ₄ ₅
        - Parentheses: (not 1) (Not 1) (NOT 1)
        """
        pass

    def _find_section_by_reference(
        self,
        ref: int,
        all_notes: List[Note]
    ) -> Optional[Note]:
        """Find note by number, return None if not found."""
        pass
```

**Why This Architecture Works**:

1. **Code Reuse**: Leverages Day 2's `EnhancedNotesDetector.extract_references()`
2. **Clear Separation**: 3 phases (extraction → graph → context) match test categories
3. **Testable**: Each method maps to 1-2 specific tests
4. **Maintainable**: Helper methods for pattern matching can be tested independently
5. **Extensible**: Easy to add new reference types (e.g., footnotes, appendices)

---

## ⏱️ Time Allocation Strategy (6 hours total)

### Hour 1: Foundation & Setup (60 min)
**Goal**: Get basic structure working, first test passing

**Tasks**:
- Create `gracian_pipeline/core/cross_reference_linker.py` file
- Implement `__init__()` and `_extract_note_markers()` helper
- Implement `extract_balance_sheet_references()` (simplest method)
- **Run test**: `pytest tests/test_notes_extraction.py::TestCrossReferenceLinking::test_balance_sheet_to_note_linking`
- **Success Criteria**: 1/7 tests passing (16/29 overall)

**Why Start Here**:
- Balance sheet references are simplest (just pattern matching)
- Gets momentum going
- Validates architecture quickly

### Hour 2: Basic Reference Extraction (60 min)
**Goal**: Complete all basic reference extraction methods

**Tasks**:
- Implement `extract_income_statement_references()` (similar to balance sheet)
- Implement `extract_note_to_note_references()` (reuse `notes_detector.extract_references()`)
- Implement `_find_section_by_reference()` helper
- **Run tests**: Tests 1, 2, 3
- **Success Criteria**: 3/7 tests passing (18/29 overall)

**Expected Challenges**:
- Swedish phrase patterns ("enligt not", "se not", "jfr not")
- Multiple variations of note markers (superscript, subscript, parentheses)

**Mitigation**:
- Start with most common pattern (superscript numbers)
- Add variations incrementally
- Use regex with fallback to string search

### Hour 3: Edge Case Handling (60 min)
**Goal**: Pass edge case tests before complex integration

**Tasks**:
- Implement `test_missing_note_reference_handling` (graceful failure)
- Implement `test_multiple_references_same_line` (multiple regex matches)
- Add comprehensive error handling to all extraction methods
- **Run tests**: Tests 6, 7
- **Success Criteria**: 5/7 tests passing (20/29 overall)

**Why Do Edge Cases Now**:
- Easier to debug edge cases in isolation than in complex integration
- Builds robust foundation for graph building
- Quick wins to maintain momentum

### Hour 4: Graph Building (60 min)
**Goal**: Build reference graph and detect circular references

**Tasks**:
- Implement `build_reference_graph()` method
  - Call all extraction methods
  - Populate `self.reference_graph` dictionary
- Implement `detect_circular_references()` using DFS
- **Run test**: `test_circular_reference_handling`
- **Success Criteria**: 6/7 tests passing (21/29 overall)

**Algorithm: DFS Cycle Detection**
```python
def detect_circular_references(self) -> List[Tuple[str, str]]:
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in self.reference_graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path + [node]):
                    cycles.append((node, neighbor))
            elif neighbor in rec_stack:
                # Found cycle
                cycles.append((node, neighbor))

        rec_stack.remove(node)
        return False

    for node in self.reference_graph:
        if node not in visited:
            dfs(node, [])

    return cycles
```

### Hour 5: Context Building (75 min)
**Goal**: Implement `build_enriched_context()` - the most complex method

**Tasks**:
- Implement `build_enriched_context()` method
  - Extract note text
  - Find all references from note
  - Collect balance sheet snippets for referenced items
  - Collect income statement snippets for referenced items
  - Recursively collect related notes (with cycle detection)
- **Run test**: `test_build_enriched_context_for_loans_agent`
- **Success Criteria**: 7/7 tests passing (22/29 overall) 🎯

**Context Building Algorithm**:
```python
def build_enriched_context(self, note, balance_sheet, income_statement, all_notes):
    context = {
        "note_text": note.content,
        "note_metadata": {
            "note_id": note.id,
            "pages": note.pages,
            "type": note.type
        },
        "balance_sheet_context": "",
        "income_statement_context": "",
        "related_notes": [],
        "reference_metadata": {}
    }

    # Step 1: Extract all references from this note
    note_refs = self.extract_note_to_note_references(note)

    # Step 2: Find what balance sheet items reference this note
    bs_refs = [
        line for line in balance_sheet.get("lines", [])
        if note.id in line.get("note_refs", [])
    ]
    context["balance_sheet_context"] = "\n".join([
        f"{line['text']}: {line['value']}"
        for line in bs_refs
    ])

    # Step 3: Find what income statement items reference this note
    is_refs = [
        line for line in income_statement.get("lines", [])
        if note.id in line.get("note_refs", [])
    ]
    context["income_statement_context"] = "\n".join([
        f"{line['text']}: {line['value']}"
        for line in is_refs
    ])

    # Step 4: Collect related notes (with cycle detection)
    visited = {note.id}
    for ref_id in note_refs:
        related_note = self._find_section_by_reference(ref_id, all_notes)
        if related_note and related_note.id not in visited:
            context["related_notes"].append(related_note)
            visited.add(related_note.id)

    # Step 5: Add metadata
    context["reference_metadata"] = {
        "total_references": len(note_refs),
        "circular_references": self._find_cycles_involving(note.id),
        "unresolved_references": [
            ref for ref in note_refs
            if not self._find_section_by_reference(ref, all_notes)
        ]
    }

    return context
```

**Why This Takes 75 Minutes**:
- Most complex logic
- Multiple data sources to integrate
- Recursive note collection with cycle prevention
- Comprehensive error handling needed

### Hour 6: Testing & Refinement (45 min)
**Goal**: Ensure all 7 tests pass reliably, fix any issues

**Tasks**:
- Run full test suite: `pytest tests/test_notes_extraction.py -k TestCrossReferenceLinking -v`
- Debug any failures
- Add docstrings and comments
- Verify all edge cases handled
- **Success Criteria**: 7/7 tests passing, all with confidence

**Testing Strategy**:
```bash
# Run individual tests first
pytest tests/test_notes_extraction.py::TestCrossReferenceLinking::test_balance_sheet_to_note_linking -v
pytest tests/test_notes_extraction.py::TestCrossReferenceLinking::test_income_statement_to_note_linking -v
# ... etc

# Then run full category
pytest tests/test_notes_extraction.py::TestCrossReferenceLinking -v

# Finally, run entire suite to verify no regressions
pytest tests/test_notes_extraction.py -v
```

---

## 🎯 Implementation Order (Optimal Path)

### Phase 1: Quick Wins (Hours 1-2)
1. ✅ Basic pattern matching for note markers
2. ✅ Balance sheet reference extraction (Test 1)
3. ✅ Income statement reference extraction (Test 2)
4. ✅ Note-to-note reference extraction (Test 3)
**Result**: 3/7 tests passing

### Phase 2: Edge Cases (Hour 3)
5. ✅ Missing note handling (Test 6)
6. ✅ Multiple references per line (Test 7)
**Result**: 5/7 tests passing

### Phase 3: Graph Logic (Hour 4)
7. ✅ Build reference graph
8. ✅ Circular reference detection (Test 5)
**Result**: 6/7 tests passing

### Phase 4: Integration (Hour 5)
9. ✅ Context building with all data sources (Test 4)
**Result**: 7/7 tests passing 🎯

### Phase 5: Polish (Hour 6)
10. ✅ Debug and verify all tests pass
11. ✅ Add documentation
**Result**: 22/29 tests passing (76% of total suite)

---

## 🚨 Risk Analysis & Mitigation

### Risk 1: EnhancedNotesDetector.extract_references() Doesn't Exist
**Probability**: 🟡 MEDIUM (30%)
**Impact**: 🔴 HIGH (would need to implement from scratch)

**Mitigation**:
- **Hour 1 First Task**: Verify method exists
```python
from gracian_pipeline.core.enhanced_notes_detector import EnhancedNotesDetector
detector = EnhancedNotesDetector()
# Check if method exists
assert hasattr(detector, 'extract_references'), "Method missing!"
```
- **Fallback**: If missing, implement basic regex pattern matching (30 min)

### Risk 2: Test Data Doesn't Match Real Document Patterns
**Probability**: 🟢 LOW (20%)
**Impact**: 🟡 MEDIUM (tests pass but real extractions fail)

**Mitigation**:
- Use same Swedish terminology patterns as Day 2 and Day 3
- Validate patterns against real BRF documents in `data/raw_pdfs/`
- Add manual validation test at end of Hour 6

### Risk 3: Circular Reference Detection is Complex
**Probability**: 🟢 LOW (20%)
**Impact**: 🟡 MEDIUM (might take longer than 1 hour)

**Mitigation**:
- Use standard DFS algorithm (proven approach)
- Implement simplest version first (detect cycles, don't worry about reporting all paths)
- Can optimize later if needed

### Risk 4: Context Building Takes Longer Than Expected
**Probability**: 🟡 MEDIUM (40%)
**Impact**: 🟡 MEDIUM (might need 90 min instead of 75 min)

**Mitigation**:
- Build incrementally: note text → BS context → IS context → related notes
- Test after each piece is added
- If running over time, defer "reference_metadata" to Hour 6

### Risk 5: Tests Have Bugs or Unclear Assertions
**Probability**: 🟢 LOW (15%)
**Impact**: 🟢 LOW (can fix test or clarify with user)

**Mitigation**:
- Read test file carefully in Hour 1
- Understand expected output format before coding
- Ask user for clarification if test is ambiguous

---

## 💡 Key Success Factors

### 1. **Reuse Day 2 Code Aggressively**
- Don't reimplement what exists
- EnhancedNotesDetector is 225 lines - USE IT
- Pattern matching for Swedish terms - already validated

### 2. **Test Early, Test Often**
- Don't code for 2 hours then test
- Test after each method implementation
- Fix issues immediately while context is fresh

### 3. **Start Simple, Add Complexity**
- Basic pattern → Edge cases → Integration
- Get 1 test passing in Hour 1 (motivation boost)
- Build confidence before tackling hard problems

### 4. **Use TDD Properly**
- Tests already written (green phase)
- Focus on making tests pass, not over-engineering
- Only implement what tests require

### 5. **Time Box Ruthlessly**
- Set timer for each hour
- If stuck >20 min, move to next task and return later
- Better to have 6/7 tests passing than 0/7 from perfectionism

---

## 📝 Code Skeleton to Start

```python
"""
Cross-reference linking for Swedish BRF document sections.

Builds a graph of references between notes, balance sheet, and income statement
to provide enriched context for agent extraction.

Author: Claude Code
Date: 2025-10-13 (Path B Day 4)
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import re
from ..models.note import Note
from .enhanced_notes_detector import EnhancedNotesDetector


class CrossReferenceLinker:
    """
    Cross-reference linker for Swedish BRF documents.

    Extracts and links references between:
    - Balance sheet → Notes (e.g., "Byggnader₁")
    - Income statement → Notes (e.g., "Avskrivningar₃")
    - Notes → Notes (e.g., "Enligt not 5...")

    Architecture:
    - Phase 1: Extract references from each section type
    - Phase 2: Build directed graph of references
    - Phase 3: Detect cycles and unresolved references
    - Phase 4: Build enriched context for agent extraction
    """

    def __init__(self, notes_detector: Optional[EnhancedNotesDetector] = None):
        """
        Initialize cross-reference linker.

        Args:
            notes_detector: Optional EnhancedNotesDetector for code reuse.
                           If not provided, creates new instance.
        """
        self.notes_detector = notes_detector or EnhancedNotesDetector()
        self.reference_graph: Dict[str, List[str]] = {}

    # === Phase 1: Reference Extraction ===

    def extract_balance_sheet_references(
        self,
        balance_sheet: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract note references from balance sheet lines.

        Swedish BRF balance sheets use:
        - Superscript: "Byggnader₁" or "Byggnader¹"
        - Parentheses: "Byggnader (not 1)"
        - Combined: "Byggnader och mark₁˒₂"

        Args:
            balance_sheet: Balance sheet data with "lines" list

        Returns:
            List of dicts:
            [
                {
                    "line": "Byggnader och mark",
                    "note_refs": [1],
                    "line_value": 15000000.0
                },
                ...
            ]
        """
        # TODO: Implement in Hour 1
        pass

    def extract_income_statement_references(
        self,
        income_statement: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract note references from income statement lines.

        Similar to balance sheet, but income statement lines.

        Args:
            income_statement: Income statement data with "lines" list

        Returns:
            List of dicts (same format as balance sheet)
        """
        # TODO: Implement in Hour 2
        pass

    def extract_note_to_note_references(
        self,
        note: Note
    ) -> List[int]:
        """
        Extract note-to-note references.

        Swedish patterns:
        - "enligt not X" (according to note X)
        - "se not X" (see note X)
        - "jfr not X" (compare note X)
        - "not X" (note X)

        Args:
            note: Note object with content

        Returns:
            List of referenced note IDs: [3, 5, 7]
        """
        # TODO: Implement in Hour 2
        # HINT: Reuse self.notes_detector.extract_references(note.content)
        pass

    # === Phase 2: Graph Building ===

    def build_reference_graph(
        self,
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any],
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
            balance_sheet: Balance sheet data
            income_statement: Income statement data
            notes: List of all notes

        Returns:
            Reference graph dictionary
        """
        # TODO: Implement in Hour 4
        pass

    def detect_circular_references(self) -> List[Tuple[str, str]]:
        """
        Detect circular references in graph.

        Uses DFS with recursion stack to find cycles.

        Returns:
            List of (node1, node2) tuples representing cycles
        """
        # TODO: Implement in Hour 4
        pass

    # === Phase 3: Context Building ===

    def build_enriched_context(
        self,
        note: Note,
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any],
        all_notes: List[Note]
    ) -> Dict[str, Any]:
        """
        Build enriched context for agent extraction.

        Collects:
        1. Note text and metadata
        2. Balance sheet lines that reference this note
        3. Income statement lines that reference this note
        4. Related notes (notes referenced by this note)
        5. Reference metadata (counts, cycles, unresolved)

        Args:
            note: Target note to build context for
            balance_sheet: Balance sheet data
            income_statement: Income statement data
            all_notes: All notes in document

        Returns:
            {
                "note_text": str,
                "note_metadata": {...},
                "balance_sheet_context": str,
                "income_statement_context": str,
                "related_notes": [Note, ...],
                "reference_metadata": {...}
            }
        """
        # TODO: Implement in Hour 5
        pass

    # === Helper Methods ===

    def _extract_note_markers(self, text: str) -> List[int]:
        """
        Extract note numbers from text using multiple patterns.

        Patterns:
        - Superscript: ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹
        - Subscript: ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉
        - Parentheses: (not 1) (Not 1) (NOT 1)
        - Combined: ₁˒₂ (notes 1 and 2)

        Args:
            text: Text to search for note markers

        Returns:
            List of note numbers: [1, 2, 3]
        """
        # TODO: Implement in Hour 1
        pass

    def _find_section_by_reference(
        self,
        ref: int,
        all_notes: List[Note]
    ) -> Optional[Note]:
        """
        Find note by number.

        Args:
            ref: Note number to find
            all_notes: List of all notes

        Returns:
            Note object if found, None otherwise
        """
        # TODO: Implement in Hour 2
        pass

    def _find_cycles_involving(self, node_id: str) -> List[Tuple[str, str]]:
        """
        Find all cycles involving a specific node.

        Args:
            node_id: Node to check for cycles

        Returns:
            List of cycles as (node1, node2) tuples
        """
        # TODO: Implement in Hour 5
        pass


# Export
__all__ = ['CrossReferenceLinker']
```

---

## 🎯 Success Criteria

### Hour 1 Success
- [ ] File created: `gracian_pipeline/core/cross_reference_linker.py`
- [ ] Basic structure working
- [ ] 1/7 tests passing (test_balance_sheet_to_note_linking)
- [ ] 16/29 total tests passing

### Hour 3 Success (Checkpoint)
- [ ] 5/7 cross-reference tests passing
- [ ] All edge cases handled
- [ ] 20/29 total tests passing

### Hour 6 Success (Final)
- [ ] **7/7 cross-reference tests passing** ✅
- [ ] **22/29 total tests passing (76%)** ✅
- [ ] Code documented with docstrings
- [ ] No regressions (Day 2 and Day 3 tests still pass)

---

## 📚 Reference Materials

### Read Before Starting
1. **Day 2 Implementation**: `gracian_pipeline/core/enhanced_notes_detector.py`
   - Check if `extract_references()` method exists
   - Understand Swedish pattern matching approach
   - Reuse code patterns

2. **Test File**: `tests/test_notes_extraction.py`
   - Lines ~400-550: TestCrossReferenceLinking class
   - Understand expected input/output formats
   - Note any Swedish test data patterns

3. **Note Model**: `gracian_pipeline/models/note.py`
   - Understand Note class structure
   - Fields: id, type, content, pages, references

### During Implementation
- **Regex Cheat Sheet**: Swedish number patterns
  - Superscript: `[¹²³⁴⁵⁶⁷⁸⁹]`
  - Subscript: `[₁₂₃₄₅₆₇₈₉]`
  - Swedish phrases: `(?:enligt|se|jfr)?\s*not\s*(\d+)`

---

## 🚀 Day 4 Execution Checklist

### Pre-Flight (5 min)
- [ ] Read WEEK1_DAY3_COMPLETE.md (understand where we are)
- [ ] Read test_notes_extraction.py lines 400-550 (understand requirements)
- [ ] Check EnhancedNotesDetector has extract_references() method
- [ ] Set 6-hour timer

### Hour 1: Foundation
- [ ] Create cross_reference_linker.py file
- [ ] Copy code skeleton from this document
- [ ] Implement _extract_note_markers() helper
- [ ] Implement extract_balance_sheet_references()
- [ ] Run test 1
- [ ] **Checkpoint**: 1 test passing

### Hour 2: Basic Extraction
- [ ] Implement extract_income_statement_references()
- [ ] Implement extract_note_to_note_references()
- [ ] Implement _find_section_by_reference() helper
- [ ] Run tests 1, 2, 3
- [ ] **Checkpoint**: 3 tests passing

### Hour 3: Edge Cases
- [ ] Add error handling for missing notes
- [ ] Handle multiple references per line
- [ ] Run tests 6, 7
- [ ] **Checkpoint**: 5 tests passing

### Hour 4: Graph Building
- [ ] Implement build_reference_graph()
- [ ] Implement detect_circular_references() using DFS
- [ ] Run test 5
- [ ] **Checkpoint**: 6 tests passing

### Hour 5: Context Building
- [ ] Implement build_enriched_context()
- [ ] Handle all 5 context components
- [ ] Run test 4
- [ ] **Checkpoint**: 7 tests passing

### Hour 6: Testing & Polish
- [ ] Run all 7 tests together
- [ ] Fix any failures
- [ ] Add docstrings
- [ ] Verify no regressions
- [ ] **Final Checkpoint**: 22/29 tests passing

---

## 🎓 TDD Principles for Day 4

1. **Tests Already Written** ✅
   - All 7 tests exist
   - We're in green phase (make tests pass)

2. **Incremental Progress**
   - Target 1 test per hour (roughly)
   - Don't try to pass all 7 at once

3. **Test After Every Method**
   - Implement method → Run relevant test → Fix → Continue
   - Don't accumulate failures

4. **No Over-Engineering**
   - Implement minimal code to pass tests
   - Fancy optimizations can wait for refactoring phase

5. **Verify No Regressions**
   - After each hour, run full test suite
   - Ensure Days 2 and 3 tests still pass

---

**Status**: ✅ **READY TO BEGIN DAY 4**
**Estimated Completion**: 6 hours with this strategy
**Confidence**: High (clear plan, proven TDD approach, code reuse opportunities)
