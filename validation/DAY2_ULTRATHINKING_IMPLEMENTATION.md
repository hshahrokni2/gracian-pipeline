# Day 2 Ultrathinking: Perfect EnhancedNotesDetector Implementation

**Date**: 2025-10-13 (preparing for execution)
**Objective**: Build EnhancedNotesDetector to pass 8 pattern recognition tests
**Time Budget**: 8 hours
**Approach**: Incremental TDD with continuous validation

---

## 🎯 Core Philosophy: Incremental Perfection

### Implementation Sequence (8 steps)

**Hour 1-2**: Basic structure + simplest pattern
**Hour 3-4**: All pattern variants + normalization
**Hour 5-6**: Type classification + multi-page merging
**Hour 7-8**: Edge cases + performance optimization

**Key Principle**: **Test after EVERY feature addition**
- Write feature → Run tests → Fix failures → Commit
- Never add 2 features without testing
- Maintain "tests passing" state as much as possible

---

## 📋 Step-by-Step Implementation Plan

### Step 1: Project Structure Setup (15 minutes)

**Create file structure**:
```
gracian_pipeline/
├── core/
│   ├── enhanced_notes_detector.py    # NEW - Main implementation
│   └── __init__.py                    # Update imports
├── models/
│   └── note.py                        # Already exists ✅
└── tests/
    └── test_notes_extraction.py       # Already exists ✅
```

**Create skeleton file**:
```python
# gracian_pipeline/core/enhanced_notes_detector.py

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
        """Initialize detector with Swedish BRF patterns."""
        self.note_patterns = []  # Will populate in Step 2
        self.note_type_keywords = {}  # Will populate in Step 5

    def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
        """
        Detect all notes in document.

        Args:
            markdown: Document text in markdown format
            tables: Optional list of tables from Docling

        Returns:
            List of Note objects with detected notes
        """
        # Implementation will be built incrementally
        pass

    def extract_references(self, text: str) -> List[NoteReference]:
        """
        Extract note references from text.

        Args:
            text: Text to scan for references (e.g., balance sheet)

        Returns:
            List of NoteReference objects
        """
        # Implementation in Step 4
        pass
```

**Test after Step 1**: File imports correctly
```bash
python -c "from gracian_pipeline.core.enhanced_notes_detector import EnhancedNotesDetector; print('✅ Import successful')"
```

---

### Step 2: Simplest Pattern Implementation (30 minutes)

**Goal**: Make test_standard_note_pattern pass

**Add basic regex pattern**:
```python
class EnhancedNotesDetector:
    def __init__(self):
        # Start with SIMPLEST pattern only
        self.note_patterns = [
            (re.compile(r'Not\s+(\d+)', re.IGNORECASE), 'standard')
        ]

    def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
        """Detect all notes in document."""
        notes = []
        lines = markdown.split('\n')

        for i, line in enumerate(lines):
            # Try each pattern
            for pattern, pattern_name in self.note_patterns:
                match = pattern.search(line)
                if match:
                    note_number = match.group(1)

                    # Extract title (text after dash or colon)
                    title = self._extract_title(line, match.end())

                    # Extract content (lines following note header)
                    content = self._extract_content(lines, i)

                    # Create Note object
                    note = Note(
                        number=note_number,
                        title=title,
                        content=content,
                        type="unknown",  # Will classify in Step 5
                        pages=[]  # Will populate if page info available
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
            if line.isupper() and len(line) > 10:
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
```

**Test after Step 2**: Run single test
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition::test_standard_note_pattern -v
```

**Expected**: ✅ 1/29 tests passing (3.4%)

**If failing**: Debug by printing detected notes
```python
# Add to test:
print(f"Detected notes: {notes}")
for note in notes:
    print(f"  - {note.number}: {note.title}")
```

---

### Step 3: Add All Pattern Variants (45 minutes)

**Goal**: Make tests 1-5 pass (standard, uppercase, tillägg, note_to_point, parenthesized)

**Add all Swedish patterns**:
```python
def __init__(self):
    """Initialize with all Swedish BRF note patterns."""
    # Compile patterns in order of specificity (most specific first)
    self.note_patterns = [
        # Pattern 1: "Not till punkt X" (most specific)
        (re.compile(r'Not\s+till\s+punkt\s+(\d+)', re.IGNORECASE), 'note_to_point'),

        # Pattern 2: Standard "Not X" or "NOTE X"
        (re.compile(r'NOT\s+(\d+)', re.IGNORECASE), 'standard'),

        # Pattern 3: "Tillägg X" (supplement)
        (re.compile(r'Tillägg\s+(\d+)', re.IGNORECASE), 'supplement'),
    ]

    # Patterns for reference extraction (in parentheses or inline)
    self.reference_patterns = [
        # Pattern: "(Not 5)" or "(Not 5, Not 7)"
        re.compile(r'\(Not\s+(\d+(?:,\s*Not\s+\d+)*)\)', re.IGNORECASE),

        # Pattern: "se Not 5" or "enligt Not 7"
        re.compile(r'(?:se|enligt|jfr)\s+Not\s+(\d+)', re.IGNORECASE),
    ]

def extract_references(self, text: str) -> List[NoteReference]:
    """Extract note references from text."""
    references = []

    for pattern in self.reference_patterns:
        for match in pattern.finditer(text):
            # Extract note numbers (handle comma-separated lists)
            note_numbers_str = match.group(1)
            note_numbers = re.findall(r'\d+', note_numbers_str)

            # Get context (20 chars before and after)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()

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
```

**Test after Step 3**: Run tests 1-5
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition -k "standard or uppercase or tillagg or point or parenthesized" -v
```

**Expected**: ✅ 5/29 tests passing (17%)

---

### Step 4: Add Multi-Page Merging (45 minutes)

**Goal**: Make test_multi_page_note_continuation pass

**Challenge**: Detect "Not 5 (forts.)" and merge with previous "Not 5"

**Implementation**:
```python
def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Detect all notes with multi-page continuation support."""
    notes = []
    lines = markdown.split('\n')

    for i, line in enumerate(lines):
        # Check for continuation marker first
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

                title = self._extract_title(line, match.end())
                content = self._extract_content(lines, i)

                note = Note(
                    number=note_number,
                    title=title,
                    content=content,
                    type="unknown",
                    pages=[],
                    is_multi_page=False
                )
                notes.append(note)
                break

    return notes
```

**Test after Step 4**: Run multi-page test
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition::test_multi_page_note_continuation -v
```

**Expected**: ✅ 6/29 tests passing (21%)

---

### Step 5: Type Classification (60 minutes)

**Goal**: Automatically classify notes by content

**Build keyword-based classifier**:
```python
def __init__(self):
    """Initialize with patterns and type classifier."""
    # ... patterns from before ...

    # Build note type classifier
    self.note_type_keywords = {
        "depreciation": [
            "avskrivning", "avskriv", "nyttjandeperiod", "linjär",
            "degressiv", "anskaffningsvärde", "restvärde"
        ],
        "tax": [
            "skatt", "inkomstskatt", "privatbostadsföretag",
            "uppskjuten skatt", "aktuell skatt", "skattemässig"
        ],
        "maintenance": [
            "underhåll", "underhållsplan", "planerat underhåll",
            "stambyten", "fasadrenovering", "takomläggning"
        ],
        "loans": [
            "låneskuld", "kreditinstitut", "lån hos", "ränta",
            "amortering", "bindningstid", "kreditavtal"
        ],
        "reserves": [
            "fond", "avsättning", "reserv", "yttre underhåll",
            "innre underhåll", "dispositionsfond"
        ],
        "interest": [
            "räntekostnad", "ränteintäkt", "finansiell kostnad",
            "ränta på lån", "räntesats"
        ],
        "revenue": [
            "intäkt", "årsavgift", "hyresintäkt", "övriga intäkter",
            "periodiseringsfond"
        ]
    }

def _classify_note_type(self, title: str, content: str) -> str:
    """
    Classify note type based on keywords in title and content.

    Returns:
        Note type (depreciation, tax, maintenance, etc.) or "other"
    """
    # Combine title and first 200 chars of content (weighted towards title)
    text = (title * 3 + " " + content[:200]).lower()

    # Score each type by keyword matches
    scores = {}
    for note_type, keywords in self.note_type_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scores[note_type] = score

    # Return type with highest score
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    else:
        return "other"

def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Detect all notes with type classification."""
    # ... previous implementation ...

    # After creating note, classify it
    note = Note(
        number=note_number,
        title=title,
        content=content,
        type=self._classify_note_type(title, content),  # NEW: Classify
        pages=[],
        is_multi_page=False
    )
```

**Test after Step 5**: Run all 8 pattern tests
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition -v
```

**Expected**: ✅ 8/29 tests passing (28%) - **PRIMARY GOAL ACHIEVED**

---

### Step 6: Whitespace & Case Tolerance (30 minutes)

**Goal**: Make test_mixed_case_whitespace_tolerance pass

**Add normalization**:
```python
def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Detect notes with robust whitespace handling."""
    notes = []

    # Normalize whitespace in markdown (multiple spaces → single space)
    normalized_lines = []
    for line in markdown.split('\n'):
        # Normalize internal whitespace while preserving line structure
        normalized = re.sub(r'\s+', ' ', line)
        normalized_lines.append(normalized)

    # Use normalized lines for detection
    for i, line in enumerate(normalized_lines):
        # ... rest of implementation ...
```

**Test after Step 6**: Run whitespace test
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition::test_mixed_case_whitespace_tolerance -v
```

**Expected**: Already passing (due to re.IGNORECASE and \s+ in patterns)

---

### Step 7: Multiple Notes Detection (15 minutes)

**Goal**: Ensure test_multiple_notes_detection passes

**This should already work** if previous steps are correct. Test to verify:

```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition::test_multiple_notes_detection -v
```

**If failing**: Check for issues:
1. Are notes being deduplicated incorrectly?
2. Is pattern ordering preventing matches?
3. Are all 4 notes being found?

**Debug**:
```python
# Add logging to detect_notes():
print(f"Found {len(notes)} notes: {[n.number for n in notes]}")
```

---

### Step 8: Edge Cases & Performance (60 minutes)

**Edge Case 1: Duplicate note numbers**
```python
def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Detect notes with duplicate handling."""
    notes = []
    seen_numbers = set()

    for i, line in enumerate(lines):
        # ... pattern matching ...

        if match:
            note_number = match.group(1)

            # Skip if already seen (unless it's a continuation)
            if note_number in seen_numbers:
                # Check if this is a continuation
                if '(forts' not in line.lower():
                    continue

            seen_numbers.add(note_number)
            # ... create note ...
```

**Edge Case 2: Note headers in table cells**
```python
def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Detect notes while avoiding false positives in tables."""
    # Skip lines that are likely table cells (start with |)
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            continue  # Skip table rows

        # ... pattern matching ...
```

**Performance Optimization**:
```python
def detect_notes(self, markdown: str, tables: List[Dict] = None) -> List[Note]:
    """Optimized note detection."""
    notes = []
    lines = markdown.split('\n')

    # Pre-compile expensive operations
    seen_numbers = set()

    # Use enumerate with early exit on major sections
    for i, line in enumerate(lines):
        # Skip empty lines early
        if not line.strip():
            continue

        # ... rest of implementation ...

    return notes
```

**Performance Test**:
```bash
pytest tests/test_notes_extraction.py::TestNotesExtractionPerformance::test_detection_performance -v
```

**Target**: Complete in <100ms per document

---

## 🔧 Common Pitfalls & Solutions

### Pitfall 1: Pattern Order Matters

**Problem**: "Not till punkt 5" matched by "Not 5" pattern first
**Solution**: Order patterns from most specific to least specific

```python
# ❌ WRONG ORDER
self.note_patterns = [
    (re.compile(r'NOT\s+(\d+)'), 'standard'),           # Matches "Not till punkt"
    (re.compile(r'Not\s+till\s+punkt\s+(\d+)'), 'specific'),  # Never reached!
]

# ✅ CORRECT ORDER
self.note_patterns = [
    (re.compile(r'Not\s+till\s+punkt\s+(\d+)'), 'specific'),  # Check specific first
    (re.compile(r'NOT\s+(\d+)'), 'standard'),                  # Check general after
]
```

### Pitfall 2: Greedy Content Extraction

**Problem**: Note content includes next note's header
**Solution**: Check for note headers before adding content

```python
def _extract_content(self, lines: List[str], start_index: int) -> str:
    """Extract content with proper boundary detection."""
    content_lines = []

    for i in range(start_index + 1, len(lines)):
        line = lines[i].strip()

        # ✅ CRITICAL: Check if this is next note's header
        if self._is_note_header(line):
            break

        # ✅ CRITICAL: Check if this is major section
        if line.isupper() and len(line) > 10:
            break

        if line:
            content_lines.append(line)

    return '\n'.join(content_lines)
```

### Pitfall 3: Continuation Merging Bug

**Problem**: Continuation content replaces original instead of appending
**Solution**: Use += for string concatenation

```python
# ❌ WRONG: Replaces content
existing_note.content = continuation_content

# ✅ CORRECT: Appends content
existing_note.content += '\n\n' + continuation_content
```

### Pitfall 4: Case Sensitivity Issues

**Problem**: "not 1" not matched by r'Not\s+(\d+)'
**Solution**: Always use re.IGNORECASE flag

```python
# ❌ WRONG: Case-sensitive
pattern = re.compile(r'Not\s+(\d+)')

# ✅ CORRECT: Case-insensitive
pattern = re.compile(r'Not\s+(\d+)', re.IGNORECASE)
```

### Pitfall 5: Memory Leaks with Large Documents

**Problem**: Storing entire markdown in memory multiple times
**Solution**: Process line-by-line, don't duplicate strings

```python
# ❌ WRONG: Creates many copies
normalized = markdown.replace('  ', ' ').replace('   ', ' ')

# ✅ CORRECT: Single-pass normalization
lines = [re.sub(r'\s+', ' ', line) for line in markdown.split('\n')]
```

---

## 🧪 Testing Strategy

### Incremental Testing (After Each Step)

**Step 2**: Run single test
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition::test_standard_note_pattern -v
```

**Step 3**: Run tests 1-5
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition -k "standard or uppercase or tillagg or point or parenthesized" -v
```

**Step 5**: Run all 8 pattern tests
```bash
pytest tests/test_notes_extraction.py::TestNotePatternRecognition -v
```

**Final**: Run full test suite
```bash
pytest tests/test_notes_extraction.py -v --tb=short
```

### Debugging Failed Tests

**Print detected notes**:
```python
def test_standard_note_pattern(self):
    detector = EnhancedNotesDetector()
    notes = detector.detect_notes(markdown)

    # DEBUG: Print what was detected
    print(f"\nDetected {len(notes)} notes:")
    for note in notes:
        print(f"  - Note {note.number}: {note.title}")
        print(f"    Type: {note.type}")
        print(f"    Content: {note.content[:50]}...")

    # Then run assertions
    assert len(notes) == 1
    assert notes[0].number == "1"
```

**Check regex matches**:
```python
# Test pattern directly
pattern = re.compile(r'Not\s+(\d+)', re.IGNORECASE)
test_text = "Not 1 - Avskrivningar"
match = pattern.search(test_text)

print(f"Pattern matched: {match is not None}")
if match:
    print(f"Note number: {match.group(1)}")
```

---

## 📊 Success Criteria for Day 2

### Must-Pass Tests (8/29 = 28%)
- [x] test_standard_note_pattern
- [x] test_uppercase_note_pattern
- [x] test_alternative_tillagg_pattern
- [x] test_note_to_point_pattern
- [x] test_parenthesized_reference
- [x] test_multiple_notes_detection
- [x] test_multi_page_note_continuation
- [x] test_mixed_case_whitespace_tolerance

### Code Quality
- [x] All functions documented
- [x] No code duplication
- [x] Proper error handling
- [x] Performance <100ms per document

### Git Commit Readiness
- [x] Tests passing
- [x] Code formatted
- [x] No debug print statements
- [x] Commit message ready

---

## ⏱️ Time Breakdown (8 hours)

| Step | Duration | Cumulative | Task |
|------|----------|------------|------|
| 1 | 15 min | 0:15 | Project structure setup |
| 2 | 30 min | 0:45 | Simplest pattern (1 test passing) |
| 3 | 45 min | 1:30 | All patterns (5 tests passing) |
| 4 | 45 min | 2:15 | Multi-page merging (6 tests) |
| 5 | 60 min | 3:15 | Type classification (8 tests) ✅ PRIMARY GOAL |
| 6 | 30 min | 3:45 | Whitespace tolerance |
| 7 | 15 min | 4:00 | Multiple notes verification |
| 8 | 60 min | 5:00 | Edge cases + performance |
| **Buffer** | **180 min** | **8:00** | **Debugging, testing, documentation** |

**Actual Expected**: 5-6 hours (3-hour buffer for unexpected issues)

---

## 🎯 Exit Criteria

**Day 2 is complete when**:
1. ✅ 8/29 tests passing (pattern recognition category)
2. ✅ Type classification ≥80% accurate on manual spot-check
3. ✅ Performance <100ms per document (on 10-page PDF)
4. ✅ Code reviewed and documented
5. ✅ Git commit ready with clear message

**Ready for Day 3** when:
- EnhancedNotesDetector fully functional
- Can detect all Swedish note variants
- Classifies notes by type correctly
- Ready to build note-specific agents

---

## 📝 Implementation Checklist

### Before Starting
- [ ] Review all 8 test cases
- [ ] Understand expected behavior
- [ ] Set up test runner (pytest -v)
- [ ] Clear plan for each step

### During Implementation
- [ ] Step 1: Structure setup ✅
- [ ] Step 2: Simplest pattern → 1 test passing
- [ ] Step 3: All patterns → 5 tests passing
- [ ] Step 4: Multi-page → 6 tests passing
- [ ] Step 5: Type classification → 8 tests passing ✅ GOAL
- [ ] Step 6: Whitespace tolerance → verified
- [ ] Step 7: Multiple notes → verified
- [ ] Step 8: Edge cases + performance → optimized

### After Completion
- [ ] All 8 tests passing
- [ ] Performance benchmark met
- [ ] Code documented
- [ ] Git commit created
- [ ] DAY2_COMPLETE.md written
- [ ] Ready for Day 3

---

## 🚀 Next Steps After Day 2

**Day 3 Goal**: Create note-specific agents (DepreciationNoteAgent, MaintenanceNoteAgent, TaxNoteAgent)
**Target**: Make 10 content extraction tests pass (18/29 = 62% total)

**But first**: Complete Day 2 with 8/29 tests passing! 🎯

---

**Ready to execute Day 2? Let's build the EnhancedNotesDetector!** 🏗️
