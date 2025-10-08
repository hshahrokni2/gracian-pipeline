"""
Week 2 Day 2-3: Synonym Mapping Test Suite

Tests for Swedish→English term mapping system with 200+ synonyms.

Test Coverage:
1. Category-specific mappings (financial, governance, property, fees, loans, organization)
2. Fuzzy matching and normalization
3. Search functionality
4. Statistics and coverage
5. Integration with extraction pipeline

Run: python test_synonyms.py
"""

import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.synonyms import (
    FINANCIAL_SYNONYMS,
    GOVERNANCE_SYNONYMS,
    PROPERTY_SYNONYMS,
    FEE_SYNONYMS,
    LOAN_SYNONYMS,
    ORGANIZATION_SYNONYMS,
    SYNONYM_MAPPING,
    normalize_swedish_term,
    map_to_canonical_field,
    get_all_synonyms_for_field,
    get_synonym_categories,
    search_synonyms,
    get_synonym_stats,
)


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def test_financial_synonyms():
    """Test 1: Financial metrics synonyms."""
    print_section("TEST 1: Financial Metrics Synonyms")

    test_cases = [
        ("nettoomsättning", "net_revenue_tkr", "Revenue synonym"),
        ("summa rörelseintäkter", "net_revenue_tkr", "Total operating income"),
        ("årets resultat", "net_income_tkr", "Net income"),
        ("rörelseresultat", "operating_surplus_tkr", "Operating result"),
        ("summa tillgångar", "total_assets_tkr", "Total assets"),
        ("eget kapital", "equity_tkr", "Equity"),
        ("soliditet", "solidarity_percent", "Solidarity"),
        ("lån, kr/m²", "debt_per_sqm", "Debt per sqm"),
        ("kassa och bank", "cash_tkr", "Cash and bank"),
        ("långfristiga skulder", "long_term_debt", "Long-term debt"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nFinancial synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_governance_synonyms():
    """Test 2: Governance role synonyms."""
    print_section("TEST 2: Governance Role Synonyms")

    test_cases = [
        ("ordförande", "chairman", "Chairman"),
        ("ordf", "chairman", "Chairman abbreviation"),
        ("vice ordförande", "vice_chairman", "Vice chairman"),
        ("kassör", "treasurer", "Treasurer"),
        ("sekreterare", "secretary", "Secretary"),
        ("styrelseledamot", "board_member", "Board member"),
        ("suppleant", "deputy", "Deputy"),
        ("revisor", "auditor", "Auditor"),
        ("auktoriserad revisor", "authorized_auditor", "Authorized auditor"),
        ("valberedning", "nomination_committee", "Nomination committee"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nGovernance synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_property_synonyms():
    """Test 3: Property detail synonyms."""
    print_section("TEST 3: Property Detail Synonyms")

    test_cases = [
        ("fastighetsbeteckning", "property_designation", "Property designation"),
        ("byggår", "built_year", "Built year"),
        ("byggnaden uppfördes", "built_year", "Building was built"),
        ("total bostadsarea", "residential_area_sqm", "Residential area"),
        ("boarea", "residential_area_sqm", "Living area"),
        ("antal lägenheter", "total_apartments", "Total apartments"),
        ("antal lokaler", "number_of_commercial_units", "Commercial units"),
        ("taxeringsvärde", "tax_value", "Tax value"),
        ("friköpt tomt", "property_tenure_freehold", "Freehold"),
        ("tomträtt", "property_tenure_leasehold", "Leasehold"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nProperty synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_fee_synonyms():
    """Test 4: Fee-related synonyms."""
    print_section("TEST 4: Fee-Related Synonyms")

    test_cases = [
        ("månadsavgift", "monthly_fee", "Monthly fee"),
        ("avgift per månad", "monthly_fee", "Fee per month"),
        ("årsavgift", "annual_fee", "Annual fee"),
        ("avgift per m²", "fee_per_sqm", "Fee per sqm"),
        ("avgift kr/kvm", "fee_per_sqm", "Fee kr/sqm"),
        ("årsavgift per m²", "annual_fee_per_sqm", "Annual fee per sqm"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nFee synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_loan_synonyms():
    """Test 5: Loan-related synonyms."""
    print_section("TEST 5: Loan-Related Synonyms")

    test_cases = [
        ("långivare", "loan_lender", "Lender"),
        ("kreditinstitut", "loan_lender", "Credit institution"),
        ("lånebelopp", "loan_amount", "Loan amount"),
        ("utgående skuld", "loan_amount_current_year", "Current year debt"),
        ("ingående skuld", "loan_amount_previous_year", "Previous year debt"),
        ("räntesats", "loan_interest_rate", "Interest rate"),
        ("ränta %", "loan_interest_rate", "Interest %"),
        ("förfallodag", "loan_maturity_date", "Maturity date"),
        ("amortering", "loan_amortization", "Amortization"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nLoan synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_organization_synonyms():
    """Test 6: Organization-related synonyms."""
    print_section("TEST 6: Organization-Related Synonyms")

    test_cases = [
        ("organisationsnummer", "organization_number", "Organization number"),
        ("org.nr", "organization_number", "Org number abbreviation"),
        ("föreningens namn", "brf_name", "BRF name"),
        ("bostadsrättsförening", "brf_name", "Housing cooperative"),
        ("säte", "registered_office", "Registered office"),
        ("antal medlemmar", "number_of_members", "Number of members"),
        ("antal anställda", "number_of_employees", "Number of employees"),
        ("årsstämma", "agm_date", "AGM date"),
    ]

    passed = 0
    for swedish_term, expected_canonical, description in test_cases:
        result = map_to_canonical_field(swedish_term)
        if result == expected_canonical:
            print(f"✅ {description}: '{swedish_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{swedish_term}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nOrganization synonyms: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_normalization():
    """Test 7: Term normalization."""
    print_section("TEST 7: Term Normalization")

    test_cases = [
        ("  Nettoomsättning (tkr)  ", "nettoomsättning", "Remove units and whitespace"),
        ("Ordf.", "ordf", "Remove periods"),
        ("Soliditet %", "soliditet", "Remove percentage sign"),
        ("Lån, kr/m²", "lån, kr/m²", "Preserve kr/m² notation"),
        ("SUMMA TILLGÅNGAR (tkr)", "summa tillgångar", "Uppercase and units"),
    ]

    passed = 0
    for raw_term, expected_normalized, description in test_cases:
        result = normalize_swedish_term(raw_term)
        if result == expected_normalized:
            print(f"✅ {description}: '{raw_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{raw_term}' → Expected '{expected_normalized}', got '{result}'")

    print(f"\nNormalization: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_fuzzy_matching():
    """Test 8: Fuzzy matching with variations."""
    print_section("TEST 8: Fuzzy Matching")

    test_cases = [
        ("Nettoomsättning (tkr)", "net_revenue_tkr", "With units"),
        ("NETTOOMSÄTTNING", "net_revenue_tkr", "Uppercase"),
        ("  nettoomsättning  ", "net_revenue_tkr", "Extra whitespace"),
        ("Ordf.", "chairman", "With period"),
        ("ordf", "chairman", "Without period"),
        ("Soliditet %", "solidarity_percent", "With % sign"),
    ]

    passed = 0
    for variant, expected_canonical, description in test_cases:
        result = map_to_canonical_field(variant)
        if result == expected_canonical:
            print(f"✅ {description}: '{variant}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{variant}' → Expected '{expected_canonical}', got '{result}'")

    print(f"\nFuzzy matching: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_reverse_lookup():
    """Test 9: Reverse lookup (canonical → Swedish)."""
    print_section("TEST 9: Reverse Lookup")

    test_cases = [
        ("chairman", ["ordförande", "ordf", "ordf."]),
        ("net_revenue_tkr", ["nettoomsättning", "nettooms", "rörelseintäkter", "summa rörelseintäkter", "totala intäkter", "intäkter", "verksamhetens intäkter"]),
        ("solidarity_percent", ["soliditet", "soliditet %", "soliditet, %"]),
    ]

    passed = 0
    for canonical_field, expected_synonyms_subset in test_cases:
        result = get_all_synonyms_for_field(canonical_field)
        # Check if expected synonyms are in result
        if all(syn in result for syn in expected_synonyms_subset):
            print(f"✅ {canonical_field}: Found {len(result)} synonyms (including {expected_synonyms_subset[0]})")
            passed += 1
        else:
            print(f"❌ {canonical_field}: Missing expected synonyms")
            print(f"   Expected: {expected_synonyms_subset}")
            print(f"   Found: {result}")

    print(f"\nReverse lookup: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_search_functionality():
    """Test 10: Search functionality."""
    print_section("TEST 10: Search Functionality")

    test_cases = [
        ("resultat", ["årets resultat", "resultat", "rörelseresultat"], "Search for 'resultat'"),
        ("avgift", ["månadsavgift", "avgift per månad", "årsavgift"], "Search for 'avgift'"),
        ("skuld", ["skuld", "utgående skuld", "ingående skuld"], "Search for 'skuld'"),
    ]

    passed = 0
    for query, expected_terms_subset, description in test_cases:
        results = search_synonyms(query, max_results=20)
        result_terms = [term for term, _ in results]

        if all(term in result_terms for term in expected_terms_subset):
            print(f"✅ {description}: Found {len(results)} results")
            for term, canonical in results[:3]:
                print(f"   - '{term}' → '{canonical}'")
            passed += 1
        else:
            print(f"❌ {description}: Missing expected terms")
            print(f"   Expected: {expected_terms_subset}")
            print(f"   Found: {result_terms[:5]}")

    print(f"\nSearch functionality: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_statistics():
    """Test 11: Statistics and coverage."""
    print_section("TEST 11: Statistics and Coverage")

    stats = get_synonym_stats()

    print(f"Total synonyms: {stats['total_synonyms']}")
    print(f"Financial synonyms: {stats['financial_synonyms']}")
    print(f"Governance synonyms: {stats['governance_synonyms']}")
    print(f"Property synonyms: {stats['property_synonyms']}")
    print(f"Fee synonyms: {stats['fee_synonyms']}")
    print(f"Loan synonyms: {stats['loan_synonyms']}")
    print(f"Organization synonyms: {stats['organization_synonyms']}")
    print(f"Unique canonical fields: {stats['unique_canonical_fields']}")

    # Validate expected counts
    expected_checks = [
        (stats['total_synonyms'] >= 150, "Total synonyms >= 150"),
        (stats['financial_synonyms'] >= 40, "Financial synonyms >= 40"),
        (stats['governance_synonyms'] >= 15, "Governance synonyms >= 15"),
        (stats['property_synonyms'] >= 20, "Property synonyms >= 20"),
        (stats['fee_synonyms'] >= 5, "Fee synonyms >= 5"),
        (stats['loan_synonyms'] >= 15, "Loan synonyms >= 15"),
        (stats['organization_synonyms'] >= 10, "Organization synonyms >= 10"),
        (stats['unique_canonical_fields'] >= 50, "Unique fields >= 50"),
    ]

    passed = 0
    for check, description in expected_checks:
        if check:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")

    print(f"\nStatistics checks: {passed}/{len(expected_checks)} passed")
    return passed == len(expected_checks)


def test_category_organization():
    """Test 12: Category organization."""
    print_section("TEST 12: Category Organization")

    categories = get_synonym_categories()

    expected_categories = ["financial", "governance", "property", "fees", "loans", "organization"]

    passed = 0
    for category in expected_categories:
        if category in categories:
            fields = categories[category]
            print(f"✅ {category}: {len(fields)} unique canonical fields")
            print(f"   Examples: {fields[:3]}")
            passed += 1
        else:
            print(f"❌ {category}: Not found in categories")

    print(f"\nCategory organization: {passed}/{len(expected_categories)} passed")
    return passed == len(expected_categories)


def test_edge_cases():
    """Test 13: Edge cases and error handling."""
    print_section("TEST 13: Edge Cases")

    test_cases = [
        (None, None, "None input"),
        ("", None, "Empty string"),
        ("unknown_term_xyz", None, "Unknown term"),
        ("   ", None, "Whitespace only"),
    ]

    passed = 0
    for input_term, expected_result, description in test_cases:
        result = map_to_canonical_field(input_term)
        if result == expected_result:
            print(f"✅ {description}: '{input_term}' → {result}")
            passed += 1
        else:
            print(f"❌ {description}: '{input_term}' → Expected {expected_result}, got {result}")

    # Test normalization edge cases
    edge_cases = [
        (None, "", "None normalization"),
        ("", "", "Empty normalization"),
    ]

    for input_term, expected_result, description in edge_cases:
        result = normalize_swedish_term(input_term)
        if result == expected_result:
            print(f"✅ {description}: '{input_term}' → '{result}'")
            passed += 1
        else:
            print(f"❌ {description}: '{input_term}' → Expected '{expected_result}', got '{result}'")

    total_tests = len(test_cases) + len(edge_cases)
    print(f"\nEdge cases: {passed}/{total_tests} passed")
    return passed == total_tests


def main():
    """Run all synonym mapping tests."""
    print("\n" + "=" * 70)
    print("WEEK 2 DAY 2-3: SYNONYM MAPPING TEST SUITE")
    print("=" * 70)

    tests = [
        ("test_financial_synonyms", test_financial_synonyms),
        ("test_governance_synonyms", test_governance_synonyms),
        ("test_property_synonyms", test_property_synonyms),
        ("test_fee_synonyms", test_fee_synonyms),
        ("test_loan_synonyms", test_loan_synonyms),
        ("test_organization_synonyms", test_organization_synonyms),
        ("test_normalization", test_normalization),
        ("test_fuzzy_matching", test_fuzzy_matching),
        ("test_reverse_lookup", test_reverse_lookup),
        ("test_search_functionality", test_search_functionality),
        ("test_statistics", test_statistics),
        ("test_category_organization", test_category_organization),
        ("test_edge_cases", test_edge_cases),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            results[test_name] = False

    # Summary
    print_section("TEST SUMMARY")

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    pass_rate = (passed_tests / total_tests) * 100

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Week 2 Day 2-3 Synonym Mapping COMPLETE!\n")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review output above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
