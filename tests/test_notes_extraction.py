"""
Test Suite for Enhanced Notes Extraction

This test suite follows TDD principles:
1. Write tests FIRST (red phase)
2. Implement features to pass tests (green phase)
3. Refactor for quality (refactor phase)

Test Categories:
- Pattern Recognition: Detect Swedish note variants
- Content Extraction: Extract depreciation, maintenance, tax details
- Cross-Reference Linking: Link balance sheet → notes

Author: Claude Code
Date: 2025-10-13 (Path B Day 1)
"""

import pytest
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Note model (already exists)
from gracian_pipeline.models.note import Note, NoteReference

# Import agents and detector (Day 2-3 implementations)
from gracian_pipeline.core.enhanced_notes_detector import EnhancedNotesDetector
from gracian_pipeline.agents.notes_agents import (
    DepreciationNoteAgent,
    MaintenanceNoteAgent,
    TaxNoteAgent
)

# CrossReferenceLinker not yet implemented (Day 4)
try:
    from gracian_pipeline.core.cross_reference_linker import CrossReferenceLinker
except ImportError:
    CrossReferenceLinker = None  # Will be implemented in Day 4


# ==============================================================================
# Category 1: Note Pattern Recognition (8 tests)
# ==============================================================================

class TestNotePatternRecognition:
    """Test detection of Swedish note numbering variants."""

    def test_standard_note_pattern(self):
        """Test standard 'Not 1' pattern."""
        markdown = """
        Not 1 - Avskrivningar

        Avskrivningar enligt plan sker linjärt över tillgångarnas
        beräknade nyttjandeperiod.
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 1
        assert notes[0].number == "1"
        assert "Avskrivningar" in notes[0].title
        assert notes[0].type == "depreciation"

    def test_uppercase_note_pattern(self):
        """Test uppercase 'NOTE 1' pattern."""
        markdown = """
        NOTE 2 - Inkomstskatter

        Föreningen är ett privatbostadsföretag enligt inkomstskattelagen.
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 1
        assert notes[0].number == "2"
        assert "Inkomstskatter" in notes[0].title
        assert notes[0].type == "tax"

    def test_alternative_tillagg_pattern(self):
        """Test 'Tillägg' (supplement) pattern."""
        markdown = """
        Tillägg 3 - Underhållsplan

        Underhållsplan upprättades 2020 och sträcker sig till 2040.
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 1
        assert notes[0].number == "3"
        assert "Underhållsplan" in notes[0].title
        assert notes[0].type == "maintenance"

    def test_note_to_point_pattern(self):
        """Test 'Not till punkt X' pattern."""
        markdown = """
        Not till punkt 5 - Låneskulder

        Föreningen har följande låneskulder till kreditinstitut.
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 1
        assert notes[0].number == "5"
        assert "Låneskulder" in notes[0].title
        assert notes[0].type == "loans"

    def test_parenthesized_reference(self):
        """Test '(Not 5)' reference style detection."""
        markdown = """
        Långfristiga skulder: 10,500,000 (Not 5)
        """

        detector = EnhancedNotesDetector()
        references = detector.extract_references(markdown)

        assert len(references) == 1
        assert references[0].note_number == "5"
        assert references[0].context == "Långfristiga skulder"

    def test_multiple_notes_detection(self):
        """Test detection of multiple notes in same document."""
        markdown = """
        Not 1 - Avskrivningar
        Avskrivningar enligt plan...

        Not 2 - Inkomstskatter
        Föreningen är privatbostadsföretag...

        NOTE 3 Underhåll
        Underhållsplan finns...

        Tillägg 4 - Låneskulder
        Lån hos SEB och SBAB...
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 4
        assert [n.number for n in notes] == ["1", "2", "3", "4"]
        assert [n.type for n in notes] == ["depreciation", "tax", "maintenance", "loans"]

    def test_multi_page_note_continuation(self):
        """Test detection of multi-page notes with (forts.) marker."""
        markdown = """
        Not 5 - Låneskulder

        Föreningen har följande lån:
        - SEB: 30,000,000 SEK

        Not 5 (forts.)

        - SBAB: 28,500,000 SEK
        - Handelsbanken: 15,000,000 SEK
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 1  # Should merge continuations
        assert notes[0].number == "5"
        assert notes[0].is_multi_page == True
        assert "SEB" in notes[0].content
        assert "SBAB" in notes[0].content
        assert "Handelsbanken" in notes[0].content

    def test_mixed_case_whitespace_tolerance(self):
        """Test tolerance for mixed case and extra whitespace."""
        markdown = """
        not  1    -   Avskrivningar

        NOTE   2  Inkomstskatter

        Not    3-Underhåll
        """

        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(markdown)

        assert len(notes) == 3
        assert notes[0].number == "1"
        assert notes[1].number == "2"
        assert notes[2].number == "3"


# ==============================================================================
# Category 2: Content Extraction (10 tests)
# ==============================================================================

class TestNotesContentExtraction:
    """Test extraction of specific data from notes."""

    def test_depreciation_method_extraction(self):
        """Test extraction of depreciation method."""
        note_content = """
        Not 1 - Avskrivningar

        Avskrivningar enligt plan sker linjärt över tillgångarnas
        beräknade nyttjandeperiod med följande procentsatser:

        Byggnader: 2% (50 år)
        Markanläggningar: 5% (20 år)
        Inventarier: 20% (5 år)
        """

        note = Note(number="1", title="Avskrivningar", content=note_content, type="depreciation")
        agent = DepreciationNoteAgent()
        result = agent.extract(note, context={})

        assert result["depreciation_method"] == "linjär avskrivning"
        assert result["useful_life_years"] is not None
        assert "50" in str(result["useful_life_years"])  # Buildings: 50 years

    def test_useful_life_years_extraction(self):
        """Test extraction of useful life years for different asset types."""
        note_content = """
        Not 1 - Avskrivningar

        Byggnader skrivs av över 50 år
        Inventarier skrivs av över 5 år
        """

        note = Note(number="1", title="Avskrivningar", content=note_content, type="depreciation")
        agent = DepreciationNoteAgent()
        result = agent.extract(note, context={})

        assert "useful_life_years" in result
        useful_life = result["useful_life_years"]

        # Should extract building life (primary asset)
        assert "50" in str(useful_life) or useful_life == 50

    def test_depreciation_base_extraction(self):
        """Test extraction of depreciation calculation base."""
        note_content = """
        Not 1 - Avskrivningar

        Avskrivning beräknas på anskaffningsvärdet minskat med
        beräknat restvärde. Linjär avskrivning tillämpas.
        """

        note = Note(number="1", title="Avskrivningar", content=note_content, type="depreciation")
        agent = DepreciationNoteAgent()
        result = agent.extract(note, context={})

        assert result["depreciation_base"] is not None
        assert "anskaffningsvärde" in result["depreciation_base"].lower()

    def test_maintenance_plan_extraction(self):
        """Test extraction of maintenance plan details."""
        note_content = """
        Not 3 - Underhållsplan

        Föreningen följer en underhållsplan som upprättades 2015
        och sträcker sig fram till 2035. Planen omfattar:

        - Fasadrenovering 2025: 5,000,000 SEK
        - Takomläggning 2028: 3,500,000 SEK
        - Stambyten 2030: 8,000,000 SEK
        """

        note = Note(number="3", title="Underhållsplan", content=note_content, type="maintenance")
        agent = MaintenanceNoteAgent()
        result = agent.extract(note, context={})

        assert result["maintenance_plan"] is not None
        assert "2015" in result["maintenance_plan"]
        assert "2035" in result["maintenance_plan"]

    def test_maintenance_budget_extraction(self):
        """Test extraction of annual maintenance budget."""
        note_content = """
        Not 3 - Underhåll

        Årlig budget för löpande underhåll: 500,000 SEK
        Avsättning till underhållsfond: 300,000 SEK/år
        """

        note = Note(number="3", title="Underhåll", content=note_content, type="maintenance")
        agent = MaintenanceNoteAgent()
        result = agent.extract(note, context={})

        assert result["maintenance_budget"] is not None
        assert 500000 <= result["maintenance_budget"] <= 800000

    def test_tax_policy_extraction(self):
        """Test extraction of tax policy."""
        note_content = """
        Not 2 - Inkomstskatter

        Föreningen är ett privatbostadsföretag enligt inkomstskattelagen
        (1999:1229) och utgör därmed en äkta bostadsrättsförening.
        Detta innebär att föreningen inte är skattskyldig för
        överskott från fastighetsförvaltning.
        """

        note = Note(number="2", title="Inkomstskatter", content=note_content, type="tax")
        agent = TaxNoteAgent()
        result = agent.extract(note, context={})

        assert result["tax_policy"] is not None
        assert "privatbostadsföretag" in result["tax_policy"].lower()

    def test_current_tax_extraction(self):
        """Test extraction of current year tax."""
        note_content = """
        Not 2 - Skatter

        Aktuell skatt för räkenskapsåret: 0 SEK
        Uppskjuten skatt: 0 SEK

        Föreningen är privatbostadsföretag och därmed skattebefriad.
        """

        note = Note(number="2", title="Skatter", content=note_content, type="tax")
        agent = TaxNoteAgent()
        result = agent.extract(note, context={})

        assert result["current_tax"] == 0 or result["current_tax"] is None

    def test_deferred_tax_extraction(self):
        """Test extraction of deferred tax."""
        note_content = """
        Not 2 - Skatter

        Uppskjuten skattefordran: 250,000 SEK
        Avser temporära skillnader i värdering av fastighet.
        """

        note = Note(number="2", title="Skatter", content=note_content, type="tax")
        agent = TaxNoteAgent()
        result = agent.extract(note, context={})

        assert result["deferred_tax"] is not None
        assert 200000 <= result["deferred_tax"] <= 300000

    def test_extraction_with_cross_validation(self):
        """Test extraction with cross-validation against balance sheet."""
        note_content = """
        Not 1 - Avskrivningar

        Ackumulerade avskrivningar: 15,000,000 SEK
        Årets avskrivningar: 750,000 SEK
        """

        context = {
            "balance_sheet": {
                "accumulated_depreciation": 15000000,
                "fixed_assets": 30000000
            }
        }

        note = Note(number="1", title="Avskrivningar", content=note_content, type="depreciation")
        agent = DepreciationNoteAgent()
        result = agent.extract(note, context=context)

        # Should have high confidence due to cross-validation
        assert result.get("confidence", 0) > 0.7

    def test_empty_note_handling(self):
        """Test handling of empty or minimal notes."""
        note_content = """
        Not 1 - Avskrivningar

        Ej tillämpligt.
        """

        note = Note(number="1", title="Avskrivningar", content=note_content, type="depreciation")
        agent = DepreciationNoteAgent()
        result = agent.extract(note, context={})

        # Should return structure with nulls, not fail
        assert result["depreciation_method"] is None
        assert result["useful_life_years"] is None
        assert result.get("confidence", 1.0) < 0.3  # Low confidence


# ==============================================================================
# Category 3: Cross-Reference Linking (7 tests)
# ==============================================================================

class TestCrossReferenceLinking:
    """Test linking between financial statements and notes."""

    def test_balance_sheet_to_note_linking(self):
        """Test detection of note references in balance sheet."""
        balance_sheet_text = """
        TILLGÅNGAR

        Anläggningstillgångar
        Byggnader och mark: 50,000,000 (Not 1)

        SKULDER

        Långfristiga skulder
        Låneskulder till kreditinstitut: 73,500,000 (Not 5)

        EGET KAPITAL

        Fond för yttre underhåll: 2,500,000 (Not 8)
        """

        linker = CrossReferenceLinker()
        references = linker.extract_balance_sheet_references(balance_sheet_text)

        assert len(references) >= 3
        assert "1" in [ref.note_number for ref in references]
        assert "5" in [ref.note_number for ref in references]
        assert "8" in [ref.note_number for ref in references]

    def test_income_statement_to_note_linking(self):
        """Test detection of note references in income statement."""
        income_statement_text = """
        RÖRELSENS INTÄKTER

        Årsavgifter: 8,500,000
        Övriga intäkter: 250,000 (Not 6)

        RÖRELSENS KOSTNADER

        Räntekostnader: -2,100,000 (Not 7)
        Avskrivningar: -750,000 (Not 1)
        """

        linker = CrossReferenceLinker()
        references = linker.extract_income_statement_references(income_statement_text)

        assert len(references) >= 3
        note_numbers = [ref.note_number for ref in references]
        assert "1" in note_numbers  # Depreciation
        assert "6" in note_numbers  # Other income
        assert "7" in note_numbers  # Interest

    def test_note_to_note_reference(self):
        """Test detection of references between notes."""
        note_text = """
        Not 5 - Låneskulder

        För information om ränteintäkter och räntekostnader, se Not 7.
        Amorteringsplan finns i Not 5.1.
        """

        linker = CrossReferenceLinker()
        references = linker.extract_note_references(note_text, source_note="5")

        assert len(references) >= 2
        assert "7" in [ref.note_number for ref in references]
        assert "5.1" in [ref.note_number for ref in references]

    def test_build_enriched_context_for_loans_agent(self):
        """Test building enriched context for loans agent."""
        notes = [
            Note(number="5", title="Låneskulder", content="Lån hos SEB: 30M, SBAB: 28.5M", type="loans")
        ]

        financial_statements = {
            "balance_sheet": "Långfristiga skulder: 73,500,000 (Not 5)",
            "income_statement": "Räntekostnader: -2,100,000 (Not 7)"
        }

        references = {
            "loans": ["5"],
            "interest": ["7"]
        }

        linker = CrossReferenceLinker()
        context = linker.build_agent_context(
            agent_id="loans_agent",
            notes=notes,
            financial_statements=financial_statements,
            references=references
        )

        # Context should include:
        # 1. Note 5 content
        # 2. Balance sheet long-term liabilities line
        # 3. Income statement interest expense
        assert "30M" in context or "30,000,000" in context
        assert "73,500,000" in context
        assert "2,100,000" in context or "-2,100,000" in context

    def test_circular_reference_handling(self):
        """Test handling of circular references between notes."""
        notes = [
            Note(number="5", title="Låneskulder", content="Se Not 7 för räntekostnader", type="loans"),
            Note(number="7", title="Räntekostnader", content="Se Not 5 för låneuppgifter", type="interest")
        ]

        linker = CrossReferenceLinker()
        # Should detect circular reference and handle gracefully (no infinite loop)
        context = linker.build_agent_context(
            agent_id="loans_agent",
            notes=notes,
            financial_statements={},
            references={"loans": ["5"], "interest": ["7"]}
        )

        # Should still build context without crashing
        assert context is not None
        assert len(context) > 0

    def test_missing_note_reference_handling(self):
        """Test handling when referenced note doesn't exist."""
        balance_sheet_text = """
        Långfristiga skulder: 73,500,000 (Not 5)
        """

        notes = []  # Note 5 doesn't exist

        linker = CrossReferenceLinker()
        references = linker.extract_balance_sheet_references(balance_sheet_text)

        # Should detect reference even if note missing
        assert len(references) == 1
        assert references[0].note_number == "5"
        assert references[0].found == False  # Mark as not found

    def test_multiple_references_same_line(self):
        """Test detection of multiple note references on same line."""
        text = """
        Resultat före skatt: 1,500,000 (Not 2, Not 7, Not 9)
        """

        linker = CrossReferenceLinker()
        references = linker.extract_references(text)

        assert len(references) == 3
        note_numbers = sorted([ref.note_number for ref in references])
        assert note_numbers == ["2", "7", "9"]


# ==============================================================================
# Fixtures & Test Data
# ==============================================================================

@pytest.fixture
def sample_markdown_with_notes():
    """Sample markdown with multiple notes for integration testing."""
    return """
    BOSTADSRÄTTSFÖRENINGEN SOLSIDAN
    Årsredovisning 2023

    RESULTATRÄKNING

    Årsavgifter: 8,500,000
    Räntekostnader: -2,100,000 (Not 7)
    Avskrivningar: -750,000 (Not 1)
    Årets resultat: 1,500,000

    BALANSRÄKNING

    TILLGÅNGAR
    Byggnader och mark: 50,000,000 (Not 1)

    SKULDER
    Långfristiga skulder: 73,500,000 (Not 5)

    EGET KAPITAL
    Fond för underhåll: 2,500,000 (Not 8)

    NOTER

    Not 1 - Avskrivningar

    Avskrivningar enligt plan sker linjärt över tillgångarnas
    beräknade nyttjandeperiod med 2% för byggnader (50 år).

    Ackumulerade avskrivningar: 15,000,000 SEK
    Årets avskrivningar: 750,000 SEK

    Not 5 - Låneskulder till kreditinstitut

    Lån hos SEB: 30,000,000 SEK, ränta 2.5%
    Lån hos SBAB: 28,500,000 SEK, ränta 2.8%
    Lån hos Handelsbanken: 15,000,000 SEK, ränta 3.1%

    Totala låneskulder: 73,500,000 SEK

    Not 7 - Räntekostnader

    Ränta på lån hos kreditinstitut: 2,100,000 SEK
    Varav SEB: 750,000 SEK
    Varav SBAB: 798,000 SEK
    Varav Handelsbanken: 465,000 SEK

    Not 8 - Fond för yttre underhåll

    Ingående balans: 2,200,000 SEK
    Årets avsättning: 300,000 SEK
    Utgående balans: 2,500,000 SEK
    """


@pytest.fixture
def sample_notes():
    """Sample Note objects for testing."""
    return [
        Note(
            number="1",
            title="Avskrivningar",
            content="Linjär avskrivning över 50 år för byggnader",
            type="depreciation",
            pages=[8, 9]
        ),
        Note(
            number="5",
            title="Låneskulder",
            content="Lån hos SEB, SBAB, Handelsbanken",
            type="loans",
            pages=[11, 12]
        ),
        Note(
            number="8",
            title="Underhållsfond",
            content="Fond för yttre underhåll",
            type="reserves",
            pages=[13]
        )
    ]


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestNotesExtractionIntegration:
    """Integration tests for full notes extraction pipeline."""

    def test_end_to_end_notes_extraction(self, sample_markdown_with_notes):
        """Test complete notes extraction pipeline."""
        # 1. Detect notes
        detector = EnhancedNotesDetector()
        notes = detector.detect_notes(sample_markdown_with_notes)

        assert len(notes) >= 4  # Should find Not 1, 5, 7, 8

        # 2. Extract cross-references
        linker = CrossReferenceLinker()
        references = linker.extract_all_references(sample_markdown_with_notes)

        assert len(references) >= 4

        # 3. Link notes to financial statements
        linked_notes = linker.link_cross_references(notes, sample_markdown_with_notes)

        # Note 1 should be linked from balance sheet and income statement
        note_1 = next(n for n in linked_notes if n.number == "1")
        assert len(note_1.references_from) >= 2

        # 4. Extract with specialized agents
        note_1 = next(n for n in notes if n.number == "1")
        agent = DepreciationNoteAgent()
        result = agent.extract(note_1, context={"balance_sheet": sample_markdown_with_notes})

        # Should extract depreciation method
        assert result["depreciation_method"] is not None
        assert "linjär" in result["depreciation_method"].lower()

        # Should have high confidence due to cross-validation
        assert result.get("confidence", 0) > 0.6

    def test_confidence_improves_with_cross_validation(self, sample_notes):
        """Test that confidence scores improve when cross-validation succeeds."""
        note = sample_notes[0]  # Depreciation note
        agent = DepreciationNoteAgent()

        # Extract without context
        result_no_context = agent.extract(note, context={})
        confidence_no_context = result_no_context.get("confidence", 0)

        # Extract with context
        context = {
            "balance_sheet": {
                "fixed_assets": 50000000,
                "accumulated_depreciation": 15000000
            }
        }
        result_with_context = agent.extract(note, context=context)
        confidence_with_context = result_with_context.get("confidence", 0)

        # Confidence should be higher with cross-validation
        assert confidence_with_context > confidence_no_context


# ==============================================================================
# Performance Tests
# ==============================================================================

class TestNotesExtractionPerformance:
    """Test performance characteristics of notes extraction."""

    def test_detection_performance(self, sample_markdown_with_notes):
        """Test that detection completes in reasonable time."""
        import time

        detector = EnhancedNotesDetector()

        start = time.time()
        notes = detector.detect_notes(sample_markdown_with_notes)
        elapsed = time.time() - start

        # Should complete in <100ms for typical document
        assert elapsed < 0.1
        assert len(notes) >= 4

    def test_cross_reference_linking_performance(self, sample_markdown_with_notes, sample_notes):
        """Test that cross-reference linking completes quickly."""
        import time

        linker = CrossReferenceLinker()

        start = time.time()
        linked = linker.link_cross_references(sample_notes, sample_markdown_with_notes)
        elapsed = time.time() - start

        # Should complete in <50ms
        assert elapsed < 0.05
        assert len(linked) == len(sample_notes)


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    # Run all tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
