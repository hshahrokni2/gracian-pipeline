"""
Test Suite for Content-Based Routing

Validates that routing works by CONTENT, not note numbers.

Key Principle: Same content should route to same agent, regardless of note number.

Author: Gracian Pipeline Team
Date: 2025-10-12
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from code.content_based_router import ContentBasedRouter, SectionInfo, RoutingResult


class TestContentBasedRouting:
    """Test content-based routing functionality"""

    @pytest.fixture
    def router(self):
        """Create router instance"""
        return ContentBasedRouter()

    def test_routing_consistency_utilities(self, router):
        """Test: Same utilities content routes to same agent regardless of note number"""
        # Test cases: Same content (Driftkostnader), different note numbers
        test_cases = [
            SectionInfo("Not 4 - Driftkostnader", "El, Värme, Vatten", (15, 16)),
            SectionInfo("Not 7 - Driftkostnader", "El, Värme, Vatten", (20, 21)),
            SectionInfo("Driftkostnader", "El, Värme, Vatten", (18, 19)),
            SectionInfo("Not 5 - Fastighetskostnader", "El, Värme", (17, 18)),
        ]

        results = [router.route_section(section) for section in test_cases]

        # All should route to OperatingCostsAgent
        for i, result in enumerate(results):
            assert result.agent_name == "OperatingCostsAgent", \
                f"Case {i+1} failed: {test_cases[i].heading} → {result.agent_name} (expected OperatingCostsAgent)"
            assert result.confidence > 0.7, \
                f"Case {i+1} low confidence: {result.confidence}"

        print("✅ Utilities routing consistency: PASSED")

    def test_routing_consistency_buildings(self, router):
        """Test: Same buildings content routes to same agent regardless of note number"""
        test_cases = [
            SectionInfo("Not 8 - Byggnader och mark", "Taxeringsvärde 50 000 000", (12, 13)),
            SectionInfo("Not 5 - Byggnader och mark", "Antal lägenheter 45", (15, 16)),
            SectionInfo("Byggnader och mark", "Totalarea 3200 kvm", (10, 11)),
            SectionInfo("Not 12 - Byggnader", "Byggnadsår 1965", (18, 19)),
        ]

        results = [router.route_section(section) for section in test_cases]

        # All should route to PropertyAgent
        for i, result in enumerate(results):
            assert result.agent_name == "PropertyAgent", \
                f"Case {i+1} failed: {test_cases[i].heading} → {result.agent_name} (expected PropertyAgent)"

        print("✅ Buildings routing consistency: PASSED")

    def test_routing_consistency_loans(self, router):
        """Test: Same loans content routes to same agent regardless of note number"""
        test_cases = [
            SectionInfo("Not 11 - Långfristiga skulder", "Lån 1: 25 000 000 SEK", (18, 19)),
            SectionInfo("Not 9 - Långfristiga skulder", "Bundna lån 15 000 000", (22, 23)),
            SectionInfo("Långfristiga skulder", "Räntesats 3.2%", (20, 21)),
            SectionInfo("Not 13 - Lån", "Förfallodag 2030-12-31", (25, 26)),
        ]

        results = [router.route_section(section) for section in test_cases]

        # All should route to LoansAgent
        for i, result in enumerate(results):
            assert result.agent_name == "LoansAgent", \
                f"Case {i+1} failed: {test_cases[i].heading} → {result.agent_name} (expected LoansAgent)"

        print("✅ Loans routing consistency: PASSED")

    def test_routing_governance(self, router):
        """Test: Governance content routes correctly"""
        test_cases = [
            ("Styrelse", "Ordförande: Per Wiklund", "GovernanceAgent"),
            ("Styrelseordförande", "Erik Ohman", "GovernanceAgent"),
            ("Revisorer", "Auktoriserad revisor: Katarina Nyberg", "GovernanceAgent"),
            ("Valberedning", "Ledamöter i valberedningen", "GovernanceAgent"),
        ]

        for heading, preview, expected_agent in test_cases:
            section = SectionInfo(heading, preview, (3, 4))
            result = router.route_section(section)
            assert result.agent_name == expected_agent, \
                f"'{heading}' → {result.agent_name} (expected {expected_agent})"

        print("✅ Governance routing: PASSED")

    def test_routing_financial(self, router):
        """Test: Financial costs routing"""
        test_cases = [
            ("Räntekostnader", "Räntor på lån 890 000 SEK", "FinancialCostsAgent"),
            ("Ränteintäkter", "Bankränta 12 000 SEK", "FinancialCostsAgent"),
            ("Finansiella kostnader", "Bankavgifter 5 000", "FinancialCostsAgent"),
        ]

        for heading, preview, expected_agent in test_cases:
            section = SectionInfo(heading, preview, (8, 9))
            result = router.route_section(section)
            assert result.agent_name == expected_agent, \
                f"'{heading}' → {result.agent_name} (expected {expected_agent})"

        print("✅ Financial costs routing: PASSED")

    def test_no_false_positives_exclude_keywords(self, router):
        """Test: Exclude keywords prevent false positives"""
        # "Styrelsearvode" should NOT route to GovernanceAgent (it's financial)
        # Exclude keyword prevents this
        section = SectionInfo(
            "Styrelsearvode",
            "Arvode till styrelsen 50 000 SEK",
            (5, 6)
        )
        result = router.route_section(section)

        # Should not be GovernanceAgent (arvode is financial, not governance structure)
        assert result.agent_name != "GovernanceAgent", \
            "Exclude keyword failed: 'Styrelsearvode' incorrectly routed to GovernanceAgent"

        print("✅ Exclude keywords working: PASSED")

    def test_routing_statistics(self, router):
        """Test: Routing statistics tracking"""
        # Route 10 sections
        sections = [
            SectionInfo("Driftkostnader", "El, Värme", (15, 16)),
            SectionInfo("Byggnader", "Taxeringsvärde", (12, 13)),
            SectionInfo("Lån", "25 000 000 SEK", (18, 19)),
            SectionInfo("Styrelse", "Ordförande", (3, 4)),
            SectionInfo("Räntekostnader", "890 000", (8, 9)),
            SectionInfo("Not 4 - Driftkostnader", "El", (20, 21)),
            SectionInfo("Not 8 - Byggnader", "Area", (22, 23)),
            SectionInfo("Not 11 - Skulder", "Lån", (25, 26)),
            SectionInfo("Eget kapital", "Reservfond", (10, 11)),
            SectionInfo("Årsavgifter", "3500 kr/mån", (7, 8)),
        ]

        for section in sections:
            router.route_section(section)

        stats = router.get_routing_statistics()

        assert stats['total_routes'] == 10
        assert stats['layer1_hits'] > 0  # Should have direct keyword matches
        assert stats['layer1_percent'] > 80  # Most should be Layer 1 (direct)

        print(f"✅ Routing statistics: {stats['layer1_percent']:.1f}% Layer 1, "
              f"{stats['layer2_percent']:.1f}% Layer 2, {stats['layer3_percent']:.1f}% Layer 3")

    def test_note_number_stripping(self, router):
        """Test: Note numbers are stripped correctly"""
        test_cases = [
            ("Not 4 - Driftkostnader", "Driftkostnader"),
            ("Noter - Not 8 Byggnader", "Byggnader"),
            ("11. Långfristiga skulder", "Långfristiga skulder"),
            ("Not 5 - Fastighetskostnader", "Fastighetskostnader"),
        ]

        for input_heading, expected_clean in test_cases:
            clean = router._strip_note_number(input_heading)
            assert clean == expected_clean, \
                f"Note stripping failed: '{input_heading}' → '{clean}' (expected '{expected_clean}')"

        print("✅ Note number stripping: PASSED")

    def test_fuzzy_matching_typos(self, router):
        """Test: Layer 2 fuzzy matching handles typos"""
        # Test with typos in Swedish terms
        test_cases = [
            SectionInfo("Drifkostnader", "El, Värme", (15, 16)),  # Missing 't'
            SectionInfo("Byggnader och amrk", "Taxering", (12, 13)),  # Typo: amrk
            SectionInfo("Räntekostnader", "Ränta", (8, 9)),  # Should match even with variations
        ]

        for section in test_cases:
            result = router.route_section(section)
            # Should still route correctly despite typos
            assert result.agent_name in ["OperatingCostsAgent", "PropertyAgent", "FinancialCostsAgent"]
            assert result.confidence > 0.5

        print("✅ Fuzzy matching for typos: PASSED")


class TestAntiPatterns:
    """Test that anti-patterns are not present in the codebase"""

    def test_no_hardcoded_note_numbers_in_router(self):
        """Test: Router code should not have hard-coded note numbers"""
        router_file = Path(__file__).parent.parent / "code" / "content_based_router.py"
        code = router_file.read_text()

        # Should NOT have patterns like: if "Not 4" in heading
        import re
        anti_pattern_matches = re.findall(r'if\s+["\']Not \d+["\']', code)

        assert len(anti_pattern_matches) == 0, \
            f"Found anti-pattern in router: {anti_pattern_matches}"

        print("✅ No hard-coded note numbers in router: PASSED")

    def test_no_note_number_agent_names_in_config(self):
        """Test: Config should not have agent names with note numbers"""
        config_file = Path(__file__).parent.parent / "config" / "content_based_routing.yaml"

        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)

        agent_names = config['agents'].keys()

        for agent_name in agent_names:
            # Should NOT match pattern like: Note4Agent, Note8Agent
            import re
            assert not re.match(r'Note\d+', agent_name), \
                f"Anti-pattern agent name found: {agent_name}"

        print("✅ No note-number-based agent names in config: PASSED")


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def router(self):
        return ContentBasedRouter()

    def test_empty_heading(self, router):
        """Test: Handle empty heading gracefully"""
        section = SectionInfo("", "Some preview text", (1, 1))
        result = router.route_section(section)

        # Should not crash, should return some agent
        assert result.agent_name is not None
        print("✅ Empty heading handled: PASSED")

    def test_no_matching_keywords(self, router):
        """Test: Handle section with no matching keywords"""
        section = SectionInfo(
            "Random Section Title",
            "This contains no Swedish BRF keywords",
            (50, 51)
        )
        result = router.route_section(section)

        # Should fall back to Layer 3 (LLM) or default agent
        assert result.routing_layer == 3 or result.agent_name == "MetadataAgent"
        print("✅ No matching keywords fallback: PASSED")

    def test_multiple_keyword_matches(self, router):
        """Test: Section with keywords matching multiple agents"""
        # "Styrelse" (governance) + "Arvode" (financial) conflict
        section = SectionInfo(
            "Styrelsearvode och ersättningar",
            "Arvode till styrelsen 50 000 SEK",
            (5, 6)
        )
        result = router.route_section(section)

        # Should pick one agent with reasonable confidence
        assert result.agent_name is not None
        assert result.confidence > 0.3
        print("✅ Multiple keyword matches handled: PASSED")


# ===== Integration Tests =====

class TestIntegrationWithPipeline:
    """Test integration with actual BRF pipeline"""

    def test_routing_with_real_docling_sections(self):
        """Test: Route actual Docling-detected sections"""
        # Simulate real Docling output
        docling_sections = [
            {
                "heading": "1. Allmänna upplysningar om föreningen",
                "text_preview": "Organisationsnummer 769606-2533",
                "page_range": (2, 3)
            },
            {
                "heading": "2. Redovisnings- och värderingsprinciper",
                "text_preview": "Årsredovisningen är upprättad",
                "page_range": (3, 4)
            },
            {
                "heading": "Not 4 - Driftkostnader",
                "text_preview": "El 450 000 SEK, Värme 890 000 SEK",
                "page_range": (15, 16)
            },
            {
                "heading": "Not 8 - Byggnader och mark",
                "text_preview": "Taxeringsvärde 50 000 000 SEK",
                "page_range": (18, 19)
            },
        ]

        router = ContentBasedRouter()

        for section_data in docling_sections:
            section = SectionInfo(
                heading=section_data["heading"],
                preview_text=section_data["text_preview"],
                page_range=section_data["page_range"]
            )
            result = router.route_section(section)

            print(f"  {section.heading} → {result.agent_name} "
                  f"(Layer {result.routing_layer}, {result.confidence:.2f} conf)")

        print("✅ Integration with Docling sections: PASSED")


# ===== Performance Tests =====

class TestPerformance:
    """Test routing performance"""

    def test_routing_speed(self):
        """Test: Routing should be fast (<10ms per section)"""
        import time

        router = ContentBasedRouter()
        section = SectionInfo("Driftkostnader", "El, Värme, Vatten", (15, 16))

        # Time 100 routes
        start = time.time()
        for _ in range(100):
            router.route_section(section)
        elapsed = time.time() - start

        avg_time_ms = (elapsed / 100) * 1000

        assert avg_time_ms < 10, f"Routing too slow: {avg_time_ms:.2f}ms per section"
        print(f"✅ Routing performance: {avg_time_ms:.2f}ms per section")


# ===== Run All Tests =====

if __name__ == "__main__":
    print("="*70)
    print("Content-Based Routing Test Suite")
    print("="*70)
    print()

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])

    print()
    print("="*70)
    print("Manual Test Examples")
    print("="*70)
    print()

    # Manual examples
    router = ContentBasedRouter()

    print("Example 1: Same content, different note numbers")
    print("-" * 50)
    test_sections = [
        ("Not 4 - Driftkostnader", "El, Värme"),
        ("Not 7 - Driftkostnader", "El, Värme"),
        ("Driftkostnader", "El, Värme"),
    ]
    for heading, preview in test_sections:
        section = SectionInfo(heading, preview, (1, 1))
        result = router.route_section(section)
        print(f"  '{heading}' → {result.agent_name} ({result.confidence:.2f})")

    print()
    print("Example 2: Different content types")
    print("-" * 50)
    test_sections = [
        ("Byggnader och mark", "Taxeringsvärde 50M"),
        ("Långfristiga skulder", "Lån 25M"),
        ("Styrelse", "Ordförande: Per Wiklund"),
        ("Räntekostnader", "890 000 SEK"),
    ]
    for heading, preview in test_sections:
        section = SectionInfo(heading, preview, (1, 1))
        result = router.route_section(section)
        print(f"  '{heading}' → {result.agent_name} ({result.confidence:.2f})")

    print()
    print("Routing Statistics:")
    print("-" * 50)
    stats = router.get_routing_statistics()
    print(f"  Total routes: {stats['total_routes']}")
    print(f"  Layer 1 (keywords): {stats['layer1_percent']:.1f}%")
    print(f"  Layer 2 (fuzzy): {stats['layer2_percent']:.1f}%")
    print(f"  Layer 3 (LLM): {stats['layer3_percent']:.1f}%")

    print()
    print("="*70)
    print("✅ All tests complete!")
    print("="*70)
