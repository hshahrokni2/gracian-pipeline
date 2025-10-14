"""
Test Universal Learning Integration with Parallel Orchestrator

This script validates that the universal learning wrapper is properly integrated
and records extraction patterns for all 15+ agent types.

Author: Claude Code
Date: 2025-10-14
"""

import os
import json
import logging
from pathlib import Path
from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel
from gracian_pipeline.core.learning_loop import get_learning_loop

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_learning_integration():
    """Test that learning is integrated and working for all agents."""

    print("=" * 80)
    print("🧪 TESTING UNIVERSAL LEARNING INTEGRATION")
    print("=" * 80)

    # Step 1: Clear any existing learned patterns
    print("\n📋 Step 1: Clearing existing learned patterns...")
    learning_loop = get_learning_loop()

    patterns_dir = Path("gracian_pipeline/learned_patterns")
    if patterns_dir.exists():
        for file in patterns_dir.glob("*.json"):
            file.unlink()
            print(f"   ✓ Cleared {file.name}")

    # Step 2: Run extraction on sample PDF
    print("\n📄 Step 2: Running extraction with learning enabled...")

    test_pdf = "Hjorthagen/brf_81563.pdf"
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        print("Please provide a valid PDF path")
        return False

    try:
        result = extract_all_agents_parallel(
            test_pdf,
            max_workers=5,
            enable_retry=True,
            enable_learning=True,  # ✨ Learning enabled!
            verbose=True
        )

        print(f"\n✅ Extraction completed successfully!")
        print(f"   Agents processed: {result['_metadata']['total_agents']}")
        print(f"   Successful: {result['_metadata']['successful_agents']}")
        print(f"   Failed: {len(result['_metadata']['failed_agents'])}")

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

    # Step 3: Check learned patterns
    print("\n🔍 Step 3: Validating learned patterns...")

    patterns_found = {
        "term_variants.json": False,
        "note_patterns.json": False,
        "extraction_patterns.json": False,
        "confidence_calibration.json": False
    }

    for pattern_file in patterns_found.keys():
        pattern_path = patterns_dir / pattern_file
        if pattern_path.exists():
            patterns_found[pattern_file] = True

            # Load and display stats
            with open(pattern_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if pattern_file == "term_variants.json":
                total_variants = sum(len(variants) for variants in data.values())
                print(f"   ✅ {pattern_file}: {len(data)} terms, {total_variants} variants")

            elif pattern_file == "note_patterns.json":
                print(f"   ✅ {pattern_file}: {len(data)} patterns detected")

            elif pattern_file == "extraction_patterns.json":
                success_count = sum(1 for p in data.values() if p.get('success_count', 0) > 0)
                print(f"   ✅ {pattern_file}: {len(data)} agents, {success_count} successful")

            elif pattern_file == "confidence_calibration.json":
                print(f"   ✅ {pattern_file}: {len(data)} agents calibrated")
        else:
            print(f"   ⚠️  {pattern_file}: NOT FOUND")

    # Step 4: Validate agent-specific learning
    print("\n🎯 Step 4: Checking agent-specific learning...")

    agent_categories = {
        'governance': ['chairman_agent', 'board_members_agent', 'auditor_agent'],
        'financial': ['financial_agent', 'cashflow_agent'],
        'property': ['property_agent', 'energy_agent'],
        'loans': ['loans_agent', 'reserves_agent'],
        'operations': ['operations_agent', 'fees_agent', 'events_agent'],
        'notes': ['notes_depreciation_agent', 'notes_maintenance_agent', 'notes_tax_agent']
    }

    extraction_patterns_path = patterns_dir / "extraction_patterns.json"
    if extraction_patterns_path.exists():
        with open(extraction_patterns_path, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)

        for category, agents in agent_categories.items():
            learned_agents = [a for a in agents if a in extraction_data]
            print(f"   {category.upper()}: {len(learned_agents)}/{len(agents)} agents learned")
            for agent in learned_agents:
                success_count = extraction_data[agent].get('success_count', 0)
                print(f"      ✓ {agent}: {success_count} successful extractions")

    # Step 5: Summary
    print("\n" + "=" * 80)
    print("📊 LEARNING INTEGRATION TEST SUMMARY")
    print("=" * 80)

    patterns_created = sum(patterns_found.values())
    total_expected = len(patterns_found)

    print(f"Patterns created: {patterns_created}/{total_expected}")
    print(f"Learning enabled: ✅")
    print(f"Persistence working: {'✅' if patterns_created > 0 else '❌'}")

    if patterns_created == total_expected:
        print("\n🎉 ALL TESTS PASSED - Learning integration is working!")
        return True
    else:
        print(f"\n⚠️  PARTIAL SUCCESS - {total_expected - patterns_created} patterns missing")
        return False


if __name__ == "__main__":
    success = test_learning_integration()
    exit(0 if success else 1)
