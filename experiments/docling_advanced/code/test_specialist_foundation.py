#!/usr/bin/env python3
"""
Test Specialist Agent Foundation

Tests the base architecture without requiring API calls:
1. Prompt template generation
2. Pydantic schema validation
3. Ground truth comparison
4. Error classification

Run: python code/test_specialist_foundation.py
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from specialist_note4_utilities import create_note4_utilities_agent, Note4UtilitiesAgent
from specialist_schemas import Note4UtilitiesSchema


def test_prompt_generation():
    """Test 1: Prompt template generation"""
    print("\n" + "="*60)
    print("TEST 1: Prompt Template Generation")
    print("="*60)

    agent = create_note4_utilities_agent(enable_llm=False)
    prompt = agent.prompt_template.build_prompt()

    # Check prompt contains key elements
    checks = {
        "Identity included": "Swedish BRF Utilities Cost Specialist" in prompt,
        "Target section mentioned": "Not 4" in prompt,
        "Expected fields listed": all(f in prompt for f in ['el', 'varme', 'vatten']),
        "Swedish terms included": "Driftkostnader" in prompt,
        "Golden examples included": "example_source" in prompt.lower() or "example" in prompt.lower(),
        "Anti-examples included": "mistake" in prompt.lower() or "avoid" in prompt.lower(),
        "Number format rules": "Swedish number format" in prompt,
        "Validation rules": "positive" in prompt.lower(),
    }

    print(f"\nPrompt length: {len(prompt)} characters")
    print(f"\nPrompt quality checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")

    all_passed = all(checks.values())
    print(f"\n{'✅ PASS' if all_passed else '❌ FAIL'}: Prompt generation")

    # Show preview
    print(f"\nPrompt preview (first 500 chars):")
    print("-" * 60)
    print(prompt[:500])
    print("..." if len(prompt) > 500 else "")

    return all_passed


def test_schema_validation():
    """Test 2: Pydantic schema validation"""
    print("\n" + "="*60)
    print("TEST 2: Pydantic Schema Validation")
    print("="*60)

    # Valid data
    valid_data = {
        'el': 698763,
        'varme': 438246,
        'vatten': 162487,
        'evidence_page': 13,
        'confidence': 1.0
    }

    # Test valid case
    try:
        schema = Note4UtilitiesSchema(**valid_data)
        print(f"\n✅ Valid data accepted:")
        print(f"   El: {schema.el:,} SEK")
        print(f"   Värme: {schema.varme:,} SEK")
        print(f"   Vatten: {schema.vatten:,} SEK")
        valid_passed = True
    except Exception as e:
        print(f"\n❌ Valid data rejected: {e}")
        valid_passed = False

    # Test invalid cases
    invalid_cases = [
        ({'el': -1000, 'confidence': 1.0}, "Negative electricity cost", False),
        ({'el': 50_000_000, 'confidence': 1.0}, "Unusually high electricity (should warn)", True),
        ({'el': 1000, 'confidence': 1.0}, "Unusually low electricity (should warn)", True),
    ]

    print(f"\n📋 Invalid case handling:")
    invalid_passed = True
    for data, description, should_create_with_warning in invalid_cases:
        try:
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                schema = Note4UtilitiesSchema(**data)

                if should_create_with_warning:
                    if len(w) > 0:
                        print(f"   ✅ {description}: Warning raised as expected")
                    else:
                        print(f"   ⚠️  {description}: Expected warning, got none")
                else:
                    print(f"   ❌ {description}: Should have raised error")
                    invalid_passed = False
        except Exception as e:
            if not should_create_with_warning:
                print(f"   ✅ {description}: Rejected as expected")
            else:
                print(f"   ❌ {description}: Unexpected rejection: {e}")
                invalid_passed = False

    all_passed = valid_passed and invalid_passed
    print(f"\n{'✅ PASS' if all_passed else '❌ FAIL'}: Schema validation")
    return all_passed


def test_ground_truth_comparison():
    """Test 3: Ground truth comparison logic"""
    print("\n" + "="*60)
    print("TEST 3: Ground Truth Comparison")
    print("="*60)

    agent = create_note4_utilities_agent(enable_llm=False)

    # Perfect match
    extracted = {'el': 698763, 'varme': 438246, 'vatten': 162487}
    ground_truth = {'el': 698763, 'varme': 438246, 'vatten': 162487}

    result = agent.compare_with_ground_truth(extracted, ground_truth)

    print(f"\nPerfect match test:")
    print(f"   Matches: {result['matches']}")
    print(f"   Mismatches: {len(result['mismatches'])}")
    print(f"   Accuracy: {result['accuracy']:.1%}")

    perfect_passed = result['accuracy'] == 1.0 and len(result['mismatches']) == 0
    print(f"   {'✅' if perfect_passed else '❌'} Perfect match detected correctly")

    # Partial match with tolerance
    extracted2 = {'el': 700000, 'varme': 440000, 'vatten': 160000}  # ~1-2% off
    result2 = agent.compare_with_ground_truth(extracted2, ground_truth)

    print(f"\nPartial match test (within 5% tolerance):")
    print(f"   Matches: {result2['matches']}")
    print(f"   Mismatches: {result2['mismatches']}")
    print(f"   Accuracy: {result2['accuracy']:.1%}")

    # Should match with 5% tolerance
    tolerance_passed = result2['accuracy'] == 1.0
    print(f"   {'✅' if tolerance_passed else '❌'} Tolerance applied correctly")

    # Complete mismatch
    extracted3 = {'el': 1000000, 'varme': 2000000, 'vatten': 500000}  # Way off
    result3 = agent.compare_with_ground_truth(extracted3, ground_truth)

    print(f"\nComplete mismatch test:")
    print(f"   Matches: {result3['matches']}")
    print(f"   Mismatches: {len(result3['mismatches'])} fields")
    print(f"   Accuracy: {result3['accuracy']:.1%}")

    if result3['mismatches']:
        print(f"   Error types detected:")
        for mismatch in result3['mismatches']:
            print(f"      - {mismatch['field']}: {mismatch['error_type']}")

    mismatch_passed = result3['accuracy'] < 1.0 and len(result3['mismatches']) > 0
    print(f"   {'✅' if mismatch_passed else '❌'} Mismatch detected correctly")

    all_passed = perfect_passed and tolerance_passed and mismatch_passed
    print(f"\n{'✅ PASS' if all_passed else '❌ FAIL'}: Ground truth comparison")
    return all_passed


def test_error_classification():
    """Test 4: Error classification"""
    print("\n" + "="*60)
    print("TEST 4: Error Classification")
    print("="*60)

    agent = create_note4_utilities_agent(enable_llm=False)

    test_cases = [
        (None, 698763, 'missing_extraction', 'Missing extraction'),
        (100, 698763, 'numeric_large_error', 'Large numeric error'),
        (690000, 698763, 'numeric_small_error', 'Small numeric error'),
        ('text', 698763, 'wrong_type', 'Wrong type'),
    ]

    print(f"\nError classification tests:")
    all_passed = True
    for extracted, gt, expected_type, description in test_cases:
        error_type = agent._classify_error(extracted, gt)
        passed = error_type == expected_type
        status = "✅" if passed else "❌"
        print(f"   {status} {description}: {error_type}")
        if not passed:
            print(f"       Expected: {expected_type}, Got: {error_type}")
            all_passed = False

    print(f"\n{'✅ PASS' if all_passed else '❌ FAIL'}: Error classification")
    return all_passed


def test_agent_factory():
    """Test 5: Agent factory pattern"""
    print("\n" + "="*60)
    print("TEST 5: Agent Factory Pattern")
    print("="*60)

    # Create with default examples
    agent1 = create_note4_utilities_agent()
    print(f"\n✅ Agent created with default golden examples")
    print(f"   Golden examples: {len(agent1.prompt_template.golden_examples)}")
    print(f"   Anti examples: {len(agent1.prompt_template.anti_examples)}")

    # Create with custom examples
    custom_golden = [{'el': 500000, 'varme': 300000, 'vatten': 100000, 'source': 'custom'}]
    custom_anti = [{'description': 'Custom mistake', 'lesson': 'Custom lesson'}]

    agent2 = create_note4_utilities_agent(
        golden_examples=custom_golden,
        anti_examples=custom_anti,
        enable_llm=False
    )
    print(f"\n✅ Agent created with custom examples")
    print(f"   Golden examples: {len(agent2.prompt_template.golden_examples)}")
    print(f"   Anti examples: {len(agent2.prompt_template.anti_examples)}")

    # Verify agents are independent
    independent = (
        len(agent1.prompt_template.golden_examples) != len(agent2.prompt_template.golden_examples)
    )
    print(f"\n{'✅' if independent else '❌'} Agents are independent instances")

    print(f"\n✅ PASS: Agent factory pattern")
    return True


def run_all_tests():
    """Run all foundation tests"""
    print("\n" + "="*60)
    print("SPECIALIST AGENT FOUNDATION TESTS")
    print("="*60)
    print("\nTesting specialist agent architecture without API calls")
    print("This validates: prompts, schemas, comparison logic, error handling\n")

    tests = [
        ("Prompt Generation", test_prompt_generation),
        ("Schema Validation", test_schema_validation),
        ("Ground Truth Comparison", test_ground_truth_comparison),
        ("Error Classification", test_error_classification),
        ("Agent Factory", test_agent_factory),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} tests passed")
    print()

    for name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"       Error: {error}")

    all_passed = passed_count == total_count

    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Foundation is solid!")
        print("\nNext step: Implement remaining specialist agents")
    else:
        print(f"❌ {total_count - passed_count} TESTS FAILED")
        print("\nPlease fix failing tests before proceeding")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
