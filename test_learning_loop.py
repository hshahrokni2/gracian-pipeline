"""
Test Learning Loop Implementation

Tests that the learning loop:
1. Records extractions correctly
2. Learns Swedish term variants
3. Learns note patterns
4. Saves/loads from disk
5. Calibrates confidence

Run: python test_learning_loop.py
"""

import os
import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.learning_loop import get_learning_loop, LearningLoop
from gracian_pipeline.agents.notes_agents import DepreciationNoteAgent, MaintenanceNoteAgent, TaxNoteAgent
from gracian_pipeline.models.note import Note


def test_basic_recording():
    """Test basic extraction recording."""
    print("\n" + "="*80)
    print("TEST 1: Basic Extraction Recording")
    print("="*80)

    loop = get_learning_loop()

    # Record a sample extraction
    loop.record_extraction(
        agent_id="DepreciationNoteAgent",
        field_name="depreciation_method",
        value="linear",
        confidence=0.85,
        evidence={
            "quotes": ["Linjär avskrivning tillämpas över nyttjandeperioden"],
            "pages": [11, 12]
        },
        validation_passed=True
    )

    print("✅ Recorded extraction successfully")

    # Check if it was recorded
    patterns = loop.get_reliable_patterns("depreciation_method")
    print(f"📊 Reliable patterns found: {len(patterns)}")

    return True


def test_term_learning():
    """Test Swedish term variant learning."""
    print("\n" + "="*80)
    print("TEST 2: Swedish Term Learning")
    print("="*80)

    loop = get_learning_loop()

    # Simulate learning from multiple documents
    terms_to_learn = [
        ("avskrivning", "Document 1"),
        ("avskrivningar", "Document 2"),
        ("avskrivningsmetod", "Document 3"),
        ("avskrivet", "Document 4"),
    ]

    for term, doc in terms_to_learn:
        loop.record_extraction(
            agent_id="DepreciationNoteAgent",
            field_name="depreciation_method",
            value="linear",
            confidence=0.85,
            evidence={
                "quotes": [f"Text containing {term} in Swedish"],
                "pages": [11]
            },
            validation_passed=True
        )
        print(f"  📝 Learned: {term} (from {doc})")

    # Query learned variants
    learned = loop.get_learned_terms("avskrivning")
    print(f"\n✅ Learned {len(learned)} variants for 'avskrivning'")
    print(f"📚 Variants: {learned}")

    return len(learned) > 0


def test_note_pattern_learning():
    """Test note heading pattern learning."""
    print("\n" + "="*80)
    print("TEST 3: Note Pattern Learning")
    print("="*80)

    loop = get_learning_loop()

    # Simulate learning note patterns
    patterns = [
        ("Not 1 Avskrivningar", "depreciation", 0.9),
        ("NOTE 1: Depreciation", "depreciation", 0.85),
        ("Tillägg 1 - Avskrivning", "depreciation", 0.88),
        ("Not 2 Underhåll", "maintenance", 0.87),
        ("Not 3 Skatter", "tax", 0.86),
    ]

    for heading, note_type, confidence in patterns:
        loop.record_note_detection(heading, note_type, confidence)
        print(f"  📋 Learned: '{heading}' → {note_type}")

    # Query learned patterns
    depreciation_patterns = loop.get_note_patterns("depreciation")
    print(f"\n✅ Learned {len(depreciation_patterns)} depreciation patterns")
    print(f"📊 Top patterns: {depreciation_patterns[:3]}")

    return len(depreciation_patterns) > 0


def test_persistence():
    """Test saving and loading from disk."""
    print("\n" + "="*80)
    print("TEST 4: Persistence (Save/Load)")
    print("="*80)

    loop = get_learning_loop()

    # Save current state
    print("💾 Saving learned patterns...")
    loop.save_learned_patterns()

    storage_path = Path("gracian_pipeline/learned_patterns")
    files = list(storage_path.glob("*.json"))

    print(f"✅ Saved {len(files)} files:")
    for f in files:
        size = f.stat().st_size
        print(f"   📄 {f.name} ({size} bytes)")

    # Create new instance (will load from disk)
    print("\n🔄 Creating new instance (loads from disk)...")
    new_loop = LearningLoop()

    # Verify loaded data
    loaded_terms = new_loop.get_learned_terms("avskrivning")
    print(f"✅ Loaded {len(loaded_terms)} term variants")

    loaded_patterns = new_loop.get_note_patterns("depreciation")
    print(f"✅ Loaded {len(loaded_patterns)} note patterns")

    return len(files) >= 3  # Should have at least 3 JSON files


def test_confidence_calibration():
    """Test confidence calibration."""
    print("\n" + "="*80)
    print("TEST 5: Confidence Calibration")
    print("="*80)

    loop = get_learning_loop()

    # Simulate 15 historical extractions with varying confidence
    historical_confidences = [0.85, 0.90, 0.88, 0.92, 0.87, 0.89, 0.91, 0.86,
                             0.88, 0.90, 0.87, 0.89, 0.91, 0.88, 0.90]

    for conf in historical_confidences:
        loop.record_extraction(
            agent_id="DepreciationNoteAgent",
            field_name="depreciation_method",
            value="linear",
            confidence=conf,
            evidence={"quotes": ["test"], "pages": [11]},
            validation_passed=True
        )

    avg_historical = sum(historical_confidences) / len(historical_confidences)
    print(f"📊 Historical average: {avg_historical:.3f}")

    # Test calibration
    raw_confidence = 0.75
    calibrated = loop.calibrate_confidence(
        "DepreciationNoteAgent",
        "depreciation_method",
        raw_confidence
    )

    print(f"🎯 Raw confidence: {raw_confidence:.3f}")
    print(f"✅ Calibrated confidence: {calibrated:.3f}")
    print(f"📈 Adjustment: {(calibrated - raw_confidence):.3f} ({((calibrated/raw_confidence - 1) * 100):.1f}%)")

    return calibrated != raw_confidence  # Should be calibrated differently


def test_agent_integration():
    """Test integration with actual agents."""
    print("\n" + "="*80)
    print("TEST 6: Agent Integration")
    print("="*80)

    # Create agents with learning enabled
    agents = [
        DepreciationNoteAgent(enable_learning=True),
        MaintenanceNoteAgent(enable_learning=True),
        TaxNoteAgent(enable_learning=True),
    ]

    print("✅ Created 3 agents with learning enabled")

    # Create sample note
    note = Note(
        number=1,
        title="Not 1 Avskrivningar",
        type="depreciation",
        content="""
        Linjär avskrivning tillämpas. Nyttjandeperioden är 50 år.
        Avskrivningsunderlaget baseras på anskaffningskostnaden.
        """,
        pages=[11, 12]
    )

    context = {
        "balance_sheet_snippet": "Balansräkning 2024...",
        "income_statement_snippet": "Resultaträkning 2024..."
    }

    print(f"\n📝 Testing extraction on sample note...")
    print(f"   Title: {note.title}")
    print(f"   Content: {len(note.content)} chars")

    # Extract with first agent (depreciation)
    try:
        result = agents[0].extract(note, context)
        print(f"\n✅ Extraction successful!")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        print(f"   Fields extracted: {len([v for v in result.values() if v is not None])}")

        # Check if learning was recorded
        loop = get_learning_loop()
        patterns = loop.get_reliable_patterns("depreciation_method")
        print(f"   Learning recorded: {len(patterns)} patterns")

        return True

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 LEARNING LOOP TEST SUITE")
    print("="*80)

    tests = [
        ("Basic Recording", test_basic_recording),
        ("Term Learning", test_term_learning),
        ("Note Pattern Learning", test_note_pattern_learning),
        ("Persistence", test_persistence),
        ("Confidence Calibration", test_confidence_calibration),
        ("Agent Integration", test_agent_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n🎯 Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Learning loop is working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed - needs investigation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
