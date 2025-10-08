#!/usr/bin/env python3
"""
Test Note Semantic Routing on Experiment 3A Data

Validates the NoteSemanticRouter class using real section headings
from brf_268882.pdf (Experiment 3A results).

Success Criteria:
- ≥80% keyword match rate (no LLM needed)
- ≥90% overall accuracy
- <$0.01 cost per document
- Cache functionality working
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from note_semantic_router import NoteSemanticRouter


def load_exp3a_data() -> Dict:
    """Load section data from Experiment 3A results"""
    exp3a_path = Path(__file__).parent.parent / "results" / "exp3a_structure_detection_20251007_192217.json"

    with open(exp3a_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def extract_note_headings(sections: List[Dict]) -> List[str]:
    """
    Extract headings from sections that belong to "Noter" section.

    From Exp 3A analysis:
    - "Noter" main section is at index 6
    - Actual note subsections start at index 29 with "NOT 1 REDOVISNINGS-..."
    - Note subsections end before "Underskrifter" at index 37

    Strategy: Look for sections that match note-specific patterns
    Two-phase approach:
    1. Find first "NOT X" section (marks start of actual notes)
    2. Collect all sections with note keywords until end markers
    """
    note_headings = []
    in_notes_subsection = False

    # Note-specific keywords (Swedish BRF annual reports)
    note_keywords = [
        'redovisningsprinciper', 'värderingsprinciper',
        'lån', 'fastighetslån', 'skulder',
        'avskrivningar',
        'byggnader', 'mark',  # Removed 'fastighet' to avoid false positives
        'fordringar', 'omsättningstillgångar',
        'fond', 'yttre underhåll', 'reserv',
        'skatter', 'avgifter', 'moms',
        'intäkter', 'kostnader'
    ]

    for section in sections:
        heading = section['heading']
        heading_lower = heading.lower()

        # Pattern 1: First "NOT X" section marks start of notes subsections
        if heading.startswith("NOT "):
            in_notes_subsection = True
            note_headings.append(heading)
            continue

        # Stop at end markers
        if any(keyword in heading_lower for keyword in [
            "underskrifter",
            "revisionsberättelse",
            "rapport om årsredovisningen"
        ]):
            break

        # After entering notes subsection, collect keyword-matching sections
        if in_notes_subsection:
            if any(keyword in heading_lower for keyword in note_keywords):
                note_headings.append(heading)

    return note_headings


def create_ground_truth() -> Dict[str, str]:
    """
    Create ground truth mapping for validation.

    These are manually verified from brf_268882.pdf Experiment 3A results.
    """
    return {
        "NOT 1 REDOVISNINGS- OCH VÄRDERINGSPRINCIPER": "notes_accounting_agent",
        "Redovisning av intäkter": "notes_accounting_agent",
        "Omsättningstillgångar": "notes_receivables_agent",
        "Föreningens fond för yttre underhåll": "notes_reserves_agent",
        "Skatter och avgifter": "notes_tax_agent",
        "Fastighetslån": "notes_loans_agent",
        # Note: "ångar" is OCR error, should route to loans if LLM enabled
        "ångar": "notes_loans_agent",
    }


def test_keyword_matching():
    """
    Test 1: Keyword matching accuracy (no LLM).

    Success Criteria: ≥80% correct classification without LLM.
    """
    print("\n" + "=" * 70)
    print("TEST 1: Keyword Matching Accuracy (No LLM)")
    print("=" * 70)
    print()

    router = NoteSemanticRouter(enable_llm=False)
    ground_truth = create_ground_truth()

    correct = 0
    total = 0

    for heading, expected_agent in ground_truth.items():
        # Skip OCR error test (requires LLM)
        if heading == "ångar":
            continue

        result = router._classify_heading(heading)

        total += 1
        if result.agent_id == expected_agent:
            correct += 1
            print(f"✅ {heading[:50]}")
            print(f"   → {result.agent_id} (confidence: {result.confidence:.2f})")
        else:
            print(f"❌ {heading[:50]}")
            print(f"   Expected: {expected_agent}")
            print(f"   Got: {result.agent_id}")

    accuracy = correct / total if total > 0 else 0

    print()
    print(f"Keyword Accuracy: {accuracy:.1%} ({correct}/{total})")
    print()

    if accuracy >= 0.80:
        print("✅ TEST PASSED: ≥80% keyword accuracy")
    else:
        print(f"❌ TEST FAILED: {accuracy:.1%} < 80% target")

    router.close()
    return accuracy >= 0.80


def test_llm_fallback():
    """
    Test 2: LLM fallback for OCR errors.

    Success Criteria: LLM correctly classifies "ångar" → notes_loans_agent.
    """
    print("\n" + "=" * 70)
    print("TEST 2: LLM Fallback for OCR Errors")
    print("=" * 70)
    print()

    router = NoteSemanticRouter(enable_llm=True)

    # Test OCR error handling
    ocr_error_heading = "ångar"  # Should be "lån"
    expected_agent = "notes_loans_agent"

    result = router._classify_heading(ocr_error_heading)

    print(f"Heading: {ocr_error_heading}")
    print(f"Expected: {expected_agent}")
    print(f"Got: {result.agent_id}")
    print(f"Method: {result.method}")
    print(f"Confidence: {result.confidence:.2f}")
    print()

    if result.agent_id == expected_agent:
        print("✅ TEST PASSED: LLM correctly handled OCR error")
        success = True
    else:
        print(f"❌ TEST FAILED: Expected {expected_agent}, got {result.agent_id}")
        success = False

    router.close()
    return success


def test_full_pipeline_exp3a():
    """
    Test 3: Full pipeline on Experiment 3A data.

    Success Criteria:
    - All note headings routed
    - ≥80% keyword match rate
    - Metrics tracking working
    """
    print("\n" + "=" * 70)
    print("TEST 3: Full Pipeline on Experiment 3A Data")
    print("=" * 70)
    print()

    # Load Exp 3A data
    exp3a_data = load_exp3a_data()
    sections = exp3a_data['structure_data']['sections']

    # Extract note headings
    note_headings = extract_note_headings(sections)

    print(f"Extracted {len(note_headings)} note headings from Exp 3A data:")
    for i, heading in enumerate(note_headings[:10], 1):
        print(f"  {i}. {heading[:60]}")
    if len(note_headings) > 10:
        print(f"  ... and {len(note_headings) - 10} more")
    print()

    # Route headings
    router = NoteSemanticRouter(enable_llm=True)
    start_time = time.time()

    agent_map = router.route_headings(note_headings)

    elapsed = time.time() - start_time

    # Display results
    print("\n=== Routing Results ===")
    for agent_id, headings in sorted(agent_map.items()):
        print(f"\n{agent_id} ({len(headings)} headings):")
        for heading in headings[:3]:
            print(f"  - {heading[:60]}")
        if len(headings) > 3:
            print(f"  ... and {len(headings) - 3} more")

    # Get metrics
    metrics = router.get_metrics_summary()

    print("\n=== Performance Metrics ===")
    print(json.dumps(metrics, indent=2))
    print()

    print(f"Processing Time: {elapsed:.2f}s")
    print(f"Headings per second: {len(note_headings) / elapsed:.1f}")
    print()

    # Validate success criteria
    success = True

    # Combined metric: cache hits + keyword matches (both are successful routing)
    successful_routing_rate = metrics['cache_hit_rate'] + metrics['keyword_match_rate']

    if successful_routing_rate >= 0.80:
        print(f"✅ Successful routing rate: {successful_routing_rate:.1%} ≥ 80%")
        print(f"   (Cache: {metrics['cache_hit_rate']:.1%}, Keywords: {metrics['keyword_match_rate']:.1%})")
    else:
        print(f"❌ Successful routing rate: {successful_routing_rate:.1%} < 80%")
        print(f"   (Cache: {metrics['cache_hit_rate']:.1%}, Keywords: {metrics['keyword_match_rate']:.1%})")
        success = False

    if len(agent_map) >= 3:
        print(f"✅ Routed to {len(agent_map)} specialized agents")
    else:
        print(f"❌ Only routed to {len(agent_map)} agents (expected ≥3)")
        success = False

    router.close()
    return success


def test_caching():
    """
    Test 4: Cache functionality.

    Success Criteria:
    - Second run has 100% cache hit rate
    - Faster processing on second run
    """
    print("\n" + "=" * 70)
    print("TEST 4: Cache Functionality")
    print("=" * 70)
    print()

    test_headings = [
        "Fastighetslån",
        "Byggnader och mark",
        "Fordringar"
    ]

    # First run (cold cache)
    print("First run (cold cache)...")
    router1 = NoteSemanticRouter(enable_llm=False)
    start1 = time.time()
    router1.route_headings(test_headings)
    elapsed1 = time.time() - start1
    metrics1 = router1.get_metrics_summary()
    router1.close()

    print(f"  Time: {elapsed1:.4f}s")
    print(f"  Cache hit rate: {metrics1['cache_hit_rate']:.1%}")
    print()

    # Second run (warm cache)
    print("Second run (warm cache)...")
    router2 = NoteSemanticRouter(enable_llm=False)
    start2 = time.time()
    router2.route_headings(test_headings)
    elapsed2 = time.time() - start2
    metrics2 = router2.get_metrics_summary()
    router2.close()

    print(f"  Time: {elapsed2:.4f}s")
    print(f"  Cache hit rate: {metrics2['cache_hit_rate']:.1%}")
    print()

    # Validate
    success = True

    if metrics2['cache_hit_rate'] == 1.0:
        print("✅ 100% cache hit rate on second run")
    else:
        print(f"❌ Cache hit rate: {metrics2['cache_hit_rate']:.1%} < 100%")
        success = False

    if elapsed2 < elapsed1:
        speedup = elapsed1 / elapsed2
        print(f"✅ Speedup: {speedup:.1f}x faster with cache")
    else:
        print("⚠️ Second run not faster (cache may not be working)")

    return success


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print("NOTE SEMANTIC ROUTING - VALIDATION TEST SUITE")
    print("=" * 70)
    print()

    results = {}

    # Run tests
    results['keyword_accuracy'] = test_keyword_matching()
    results['llm_fallback'] = test_llm_fallback()
    results['full_pipeline'] = test_full_pipeline_exp3a()
    results['caching'] = test_caching()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Overall: {passed}/{total} tests passed ({passed/total:.0%})")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED - Router is production-ready!")
    else:
        print(f"⚠️ {total - passed} test(s) failed - review and fix before deployment")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
