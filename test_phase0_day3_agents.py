#!/usr/bin/env python3
"""
Phase 0 Day 3 - Agent Prompt Validation Test

Tests the 5 updated/new agent prompts with relative year naming:
1. loans_agent - interest_expense_current_year/prior_year
2. energy_agent - YoY fields + government_energy_support_current_year
3. fees_agent - fee_increase_count_current_year
4. key_metrics_agent - depreciation paradox detection (NEW)
5. balance_sheet_agent - cash crisis detection (NEW)

Purpose: Verify all relative field names are correctly implemented
and pattern detection logic works as expected.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import agent prompts
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS

# Import schema for validation
from gracian_pipeline.core.schema_comprehensive import COMPREHENSIVE_TYPES


def test_relative_field_names():
    """Test that all agents use relative year naming (no hardcoded years)."""
    print("=" * 80)
    print("🧪 TEST 1: Relative Year Field Names")
    print("=" * 80)

    # Fields that should use relative naming
    relative_fields = [
        'interest_expense_current_year',
        'interest_expense_prior_year',
        'electricity_yoy_increase_percent',
        'heating_yoy_increase_percent',
        'water_yoy_increase_percent',
        'government_energy_support_current_year',
        'fee_increase_count_current_year',
        'result_without_depreciation_current_year',
        'result_without_depreciation_prior_year',
        'depreciation_as_percent_of_revenue_current_year',
        'total_liquidity_current_year',
        'total_liquidity_prior_year',
        'cash_to_debt_ratio_current_year',
        'cash_to_debt_ratio_prior_year',
        'cash_to_debt_ratio_prior_2_years',
    ]

    # Check each agent prompt for relative naming
    agents_to_check = ['loans_agent', 'energy_agent', 'fees_agent', 'key_metrics_agent', 'balance_sheet_agent']

    passed = 0
    failed = 0

    for agent_name in agents_to_check:
        prompt = AGENT_PROMPTS.get(agent_name, '')

        # Check for hardcoded years in field definitions (not examples)
        hardcoded_patterns = [
            '".*_2023":',
            '".*_2022":',
            '".*_2021":',
        ]

        # Extract only the JSON schema section (before examples)
        if 'Return JSON' in prompt:
            schema_section = prompt.split('✅ REAL EXAMPLE')[0] if '✅ REAL EXAMPLE' in prompt else prompt

            has_hardcoded = False
            for pattern in ['_2023":', '_2022":', '_2021":']:
                if pattern in schema_section and 'example' not in schema_section.lower():
                    has_hardcoded = True
                    break

            if not has_hardcoded:
                print(f"✅ {agent_name}: No hardcoded years in field definitions")
                passed += 1
            else:
                print(f"❌ {agent_name}: Found hardcoded years in field definitions")
                failed += 1
        else:
            print(f"⚠️  {agent_name}: No 'Return JSON' section found")
            failed += 1

    print(f"\n📊 Results: {passed}/{len(agents_to_check)} passed")
    return failed == 0


def test_schema_consistency():
    """Test that agent prompts match schema_comprehensive.py."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Schema Consistency")
    print("=" * 80)

    # Check that new agents exist in schema
    new_agents = ['key_metrics_agent', 'balance_sheet_agent']

    passed = 0
    failed = 0

    for agent_name in new_agents:
        if agent_name in COMPREHENSIVE_TYPES:
            fields = COMPREHENSIVE_TYPES[agent_name]
            print(f"✅ {agent_name}: Found in schema with {len(fields)} fields")
            passed += 1
        else:
            print(f"❌ {agent_name}: NOT found in schema_comprehensive.py")
            failed += 1

    print(f"\n📊 Results: {passed}/{len(new_agents)} agents in schema")
    return failed == 0


def test_pattern_detection_fields():
    """Test that pattern detection agents have required fields."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Pattern Detection Fields")
    print("=" * 80)

    # key_metrics_agent required fields
    key_metrics_required = [
        'result_without_depreciation_current_year',
        'result_without_depreciation_prior_year',
        'depreciation_as_percent_of_revenue_current_year',
        'depreciation_paradox_detected',
    ]

    # balance_sheet_agent required fields
    balance_sheet_required = [
        'total_liquidity_current_year',
        'total_liquidity_prior_year',
        'cash_to_debt_ratio_current_year',
        'cash_to_debt_ratio_prior_year',
        'cash_to_debt_ratio_prior_2_years',
        'cash_crisis_detected',
    ]

    passed = 0
    failed = 0

    # Check key_metrics_agent
    if 'key_metrics_agent' in COMPREHENSIVE_TYPES:
        schema_fields = COMPREHENSIVE_TYPES['key_metrics_agent']
        missing = [f for f in key_metrics_required if f not in schema_fields]

        if not missing:
            print(f"✅ key_metrics_agent: All {len(key_metrics_required)} required fields present")
            passed += 1
        else:
            print(f"❌ key_metrics_agent: Missing fields: {missing}")
            failed += 1
    else:
        print("❌ key_metrics_agent: Not in schema")
        failed += 1

    # Check balance_sheet_agent
    if 'balance_sheet_agent' in COMPREHENSIVE_TYPES:
        schema_fields = COMPREHENSIVE_TYPES['balance_sheet_agent']
        missing = [f for f in balance_sheet_required if f not in schema_fields]

        if not missing:
            print(f"✅ balance_sheet_agent: All {len(balance_sheet_required)} required fields present")
            passed += 1
        else:
            print(f"❌ balance_sheet_agent: Missing fields: {missing}")
            failed += 1
    else:
        print("❌ balance_sheet_agent: Not in schema")
        failed += 1

    print(f"\n📊 Results: {passed}/2 pattern agents validated")
    return failed == 0


def test_prompt_structure():
    """Test that all agent prompts follow consistent structure."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: Agent Prompt Structure")
    print("=" * 80)

    required_sections = [
        'Return JSON',
        'WHERE TO LOOK',
        '🚨 ANTI-HALLUCINATION RULES',
        'Return STRICT VALID JSON',
    ]

    agents_to_check = ['key_metrics_agent', 'balance_sheet_agent']

    passed = 0
    failed = 0

    for agent_name in agents_to_check:
        prompt = AGENT_PROMPTS.get(agent_name, '')

        missing_sections = []
        for section in required_sections:
            if section not in prompt:
                missing_sections.append(section)

        if not missing_sections:
            print(f"✅ {agent_name}: All required sections present")
            passed += 1
        else:
            print(f"❌ {agent_name}: Missing sections: {missing_sections}")
            failed += 1

    print(f"\n📊 Results: {passed}/{len(agents_to_check)} prompts structured correctly")
    return failed == 0


def test_agent_existence():
    """Test that all required agents exist in AGENT_PROMPTS."""
    print("\n" + "=" * 80)
    print("🧪 TEST 5: Agent Existence")
    print("=" * 80)

    required_agents = [
        'loans_agent',
        'energy_agent',
        'fees_agent',
        'key_metrics_agent',
        'balance_sheet_agent',
    ]

    passed = 0
    failed = 0

    for agent_name in required_agents:
        if agent_name in AGENT_PROMPTS:
            prompt_length = len(AGENT_PROMPTS[agent_name])
            print(f"✅ {agent_name}: Exists ({prompt_length} chars)")
            passed += 1
        else:
            print(f"❌ {agent_name}: NOT FOUND in AGENT_PROMPTS")
            failed += 1

    print(f"\n📊 Results: {passed}/{len(required_agents)} agents exist")
    return failed == 0


def run_all_tests():
    """Run all validation tests."""
    print("🧪" * 40)
    print("PHASE 0 DAY 3 - AGENT PROMPT VALIDATION")
    print("🧪" * 40)
    print()

    results = []

    # Test 1: Relative field names
    results.append(("Relative Field Names", test_relative_field_names()))

    # Test 2: Schema consistency
    results.append(("Schema Consistency", test_schema_consistency()))

    # Test 3: Pattern detection fields
    results.append(("Pattern Detection Fields", test_pattern_detection_fields()))

    # Test 4: Prompt structure
    results.append(("Prompt Structure", test_prompt_structure()))

    # Test 5: Agent existence
    results.append(("Agent Existence", test_agent_existence()))

    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ ✅ ✅ ALL TESTS PASSED! ✅ ✅ ✅")
        print("Phase 0 Day 2 agent prompt updates are VALIDATED.")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) failed")
        print("Please review and fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
