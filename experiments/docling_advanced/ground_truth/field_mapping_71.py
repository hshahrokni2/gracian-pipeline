"""
71-Field Ground Truth Mapping

Maps our 71-field schema to brf_198532 comprehensive ground truth JSON.

This enables automated validation by translating:
- Our field names → Ground truth JSON paths
- Handles nested structures (revenue_breakdown.nettoomsattning → income_statement.2021.revenue.nettoomsattning)
- Supports multi-instance data (loan_1_amount → loans[0].amount)

Usage:
    gt = json.load("brf_198532_comprehensive_ground_truth.json")
    extracted = {...}  # Our 71-field extraction

    for our_field, gt_path in FIELD_MAPPING_71.items():
        expected = get_nested_value(gt, gt_path)
        actual = get_nested_value(extracted, our_field)
        compare(expected, actual)
"""

from typing import Any, Optional


# ============================================================================
# FIELD MAPPING: 71 Fields → Ground Truth Paths
# ============================================================================

FIELD_MAPPING_71 = {
    # ========================================================================
    # EXISTING 30 FIELDS (Base Schema)
    # ========================================================================

    # Governance (7 fields)
    "chairman": "governance.chairman",
    "board_members": "governance.board_members",  # List comparison
    "auditor_name": "governance.auditor_name",
    "audit_firm": "governance.audit_firm",
    "nomination_committee": "governance.nomination_committee",  # List comparison

    # Property (7 fields)
    "designation": "property.designation",
    "address": "property.address",
    "postal_code": "property.postal_code",
    "city": "property.city",
    "built_year": "property.built_year",
    "apartments": "property.apartments",
    "energy_class": "property.energy_class",

    # Financial totals (6 fields)
    "revenue": "income_statement.2021.revenue.summa_intakter",  # Total revenue
    "expenses": "income_statement.2021.expenses.summa_rörelsekostnader",  # Total expenses (negative)
    "assets": "balance_sheet.2021.assets.total",  # Total assets
    "liabilities": "balance_sheet.2021.liabilities.total",  # Total liabilities
    "equity": "balance_sheet.2021.equity.total",  # Total equity
    "surplus": "income_statement.2021.surplus.årets_resultat",  # Surplus/deficit

    # Notes summaries (10 fields - high-level)
    "accounting_principles": "notes.accounting.accounting_principles",
    "valuation_methods": "notes.accounting.valuation_methods",
    "revenue_recognition": "notes.accounting.revenue_recognition",
    "outstanding_loans": "notes.loans.summary",  # Summary string
    "interest_rate": "notes.loans.average_rate",  # Summary string
    "amortization": "notes.loans.amortization_policy",
    "loan_terms": "notes.loans.terms",
    "reserve_fund": "notes.reserves.fund_description",
    "annual_contribution": "notes.reserves.annual_contribution",
    "fund_purpose": "notes.reserves.purpose",

    # ========================================================================
    # NEW: Revenue Breakdown (15 fields)
    # ========================================================================

    # Revenue components
    "revenue_breakdown.nettoomsattning": "income_statement.2021.revenue.nettoomsattning",
    "revenue_breakdown.arsavgifter": "income_statement.2021.revenue.arsavgifter",
    "revenue_breakdown.hyresintakter": "income_statement.2021.revenue.hyresintakter",
    "revenue_breakdown.bredband_kabel_tv": "income_statement.2021.revenue.bredband_kabel_tv",
    "revenue_breakdown.andel_drift_gemensam": "income_statement.2021.revenue.andel_drift_gemensam",
    "revenue_breakdown.andel_el_varme": "income_statement.2021.revenue.andel_el_varme",
    "revenue_breakdown.andel_vatten": "income_statement.2021.revenue.andel_vatten",
    "revenue_breakdown.ovriga_rorelseintak": "income_statement.2021.revenue.ovriga_rorelseintak",
    "revenue_breakdown.ranta_bankmedel": "income_statement.2021.revenue.ranta_bankmedel",
    "revenue_breakdown.valutakursvinster": "income_statement.2021.revenue.valutakursvinster",

    # Revenue totals
    "revenue_breakdown.summa_rorelseintakter": "income_statement.2021.revenue.summa_rorelseintakter",
    "revenue_breakdown.summa_finansiella_intakter": "income_statement.2021.revenue.summa_finansiella_intakter",
    "revenue_breakdown.summa_intakter": "income_statement.2021.revenue.summa_intakter",

    # Multi-year
    "revenue_breakdown.revenue_2021": "income_statement.2021.revenue.summa_intakter",
    "revenue_breakdown.revenue_2020": "income_statement.2020.revenue.summa_intakter",

    # ========================================================================
    # NEW: Multi-Loan (4 loans × 8 fields = 32 fields)
    # ========================================================================

    # Loan 1 (8 fields)
    "loan_1_lender": "loans[0].lender",
    "loan_1_amount": "loans[0].amount_2021",  # Note: GT uses "amount_2021"
    "loan_1_interest_rate": "loans[0].interest_rate",
    "loan_1_maturity_date": "loans[0].maturity_date",
    "loan_1_loan_type": "loans[0].loan_type",  # NEW: May not exist in GT
    "loan_1_collateral": "loans[0].collateral",  # NEW: May not exist in GT
    "loan_1_credit_facility_limit": "loans[0].credit_facility_limit",  # NEW: May not exist in GT
    "loan_1_outstanding_amount": "loans[0].outstanding_amount",  # NEW: May not exist in GT

    # Loan 2 (8 fields)
    "loan_2_lender": "loans[1].lender",
    "loan_2_amount": "loans[1].amount_2021",
    "loan_2_interest_rate": "loans[1].interest_rate",
    "loan_2_maturity_date": "loans[1].maturity_date",
    "loan_2_loan_type": "loans[1].loan_type",
    "loan_2_collateral": "loans[1].collateral",
    "loan_2_credit_facility_limit": "loans[1].credit_facility_limit",
    "loan_2_outstanding_amount": "loans[1].outstanding_amount",

    # Loan 3 (8 fields)
    "loan_3_lender": "loans[2].lender",
    "loan_3_amount": "loans[2].amount_2021",
    "loan_3_interest_rate": "loans[2].interest_rate",
    "loan_3_maturity_date": "loans[2].maturity_date",
    "loan_3_loan_type": "loans[2].loan_type",
    "loan_3_collateral": "loans[2].collateral",
    "loan_3_credit_facility_limit": "loans[2].credit_facility_limit",
    "loan_3_outstanding_amount": "loans[2].outstanding_amount",

    # Loan 4 (8 fields)
    "loan_4_lender": "loans[3].lender",
    "loan_4_amount": "loans[3].amount_2021",
    "loan_4_interest_rate": "loans[3].interest_rate",
    "loan_4_maturity_date": "loans[3].maturity_date",
    "loan_4_loan_type": "loans[3].loan_type",
    "loan_4_collateral": "loans[3].collateral",
    "loan_4_credit_facility_limit": "loans[3].credit_facility_limit",
    "loan_4_outstanding_amount": "loans[3].outstanding_amount",

    # ========================================================================
    # NEW: Operating Costs (6 fields)
    # ========================================================================

    "operating_costs_breakdown.fastighetsskott": "income_statement.2021.expenses.fastighetsskott",
    "operating_costs_breakdown.reparationer": "income_statement.2021.expenses.reparationer",
    "operating_costs_breakdown.el": "income_statement.2021.expenses.el",
    "operating_costs_breakdown.varme": "income_statement.2021.expenses.varme",
    "operating_costs_breakdown.vatten": "income_statement.2021.expenses.vatten",
    "operating_costs_breakdown.ovriga_externa_kostnader": "income_statement.2021.expenses.ovriga_externa_kostnader",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_nested_value(data: dict, path: str) -> Any:
    """
    Get value from nested dictionary using dot notation path.

    Supports:
    - Dot notation: "income_statement.2021.revenue.summa_intakter"
    - Array indexing: "loans[0].lender"

    Args:
        data: Dictionary (typically ground truth JSON)
        path: Dot notation path with optional array indexing

    Returns:
        Value at path, or None if path doesn't exist

    Examples:
        >>> data = {"income_statement": {"2021": {"revenue": {"total": 1000}}}}
        >>> get_nested_value(data, "income_statement.2021.revenue.total")
        1000

        >>> data = {"loans": [{"lender": "SEB", "amount": 30000000}]}
        >>> get_nested_value(data, "loans[0].lender")
        "SEB"
    """
    if not path:
        return None

    try:
        # Handle array indexing: "loans[0].lender"
        parts = path.replace('[', '.').replace(']', '').split('.')
        current = data

        for part in parts:
            if part.isdigit():
                # Array index
                current = current[int(part)]
            else:
                # Dictionary key
                current = current[part]

        return current

    except (KeyError, IndexError, TypeError):
        return None


def set_nested_value(data: dict, path: str, value: Any) -> None:
    """
    Set value in nested dictionary using dot notation path.

    Args:
        data: Dictionary to modify
        path: Dot notation path
        value: Value to set

    Examples:
        >>> data = {}
        >>> set_nested_value(data, "revenue_breakdown.nettoomsattning", 7393591)
        >>> data
        {"revenue_breakdown": {"nettoomsattning": 7393591}}
    """
    parts = path.split('.')
    current = data

    for i, part in enumerate(parts[:-1]):
        if part not in current:
            # Check if next part is array index
            next_part = parts[i + 1]
            if next_part.isdigit():
                current[part] = []
            else:
                current[part] = {}
        current = current[part]

    # Set final value
    final_key = parts[-1]
    current[final_key] = value


def compare_values(extracted: Any, expected: Any, tolerance: float = 0.05) -> dict:
    """
    Compare extracted value vs expected (ground truth) with tolerance.

    Handles:
    - Numeric comparison with tolerance (±5% by default)
    - String comparison (case-insensitive, normalized whitespace)
    - List comparison (order-independent for board members)
    - None/null handling

    Args:
        extracted: Our extraction value
        expected: Ground truth value
        tolerance: Numeric tolerance (0.05 = ±5%)

    Returns:
        dict: {status: "CORRECT"|"INCORRECT"|"MISSING"|"PARTIAL", details: str}
    """
    # Both None - field doesn't exist in document
    if extracted is None and expected is None:
        return {"status": "CORRECT", "details": "Both null (field doesn't exist)"}

    # Extracted is None but expected exists
    if extracted is None:
        return {"status": "MISSING", "details": f"Expected: {expected}"}

    # Expected is None but extracted exists (may be hallucination)
    if expected is None:
        return {"status": "PARTIAL", "details": f"Extracted: {extracted} (no ground truth)"}

    # Numeric comparison
    if isinstance(extracted, (int, float)) and isinstance(expected, (int, float)):
        if expected == 0:
            # Avoid division by zero
            diff = abs(extracted - expected)
            if diff < 1:  # Within 1 unit for zero values
                return {"status": "CORRECT", "details": f"Match: {extracted}"}
            else:
                return {"status": "INCORRECT", "details": f"Expected: {expected}, Got: {extracted}"}
        else:
            pct_diff = abs(extracted - expected) / abs(expected)
            if pct_diff <= tolerance:
                return {"status": "CORRECT", "details": f"Match: {extracted} (within {tolerance*100}%)"}
            else:
                return {"status": "INCORRECT", "details": f"Expected: {expected}, Got: {extracted} ({pct_diff*100:.1f}% diff)"}

    # String comparison
    if isinstance(extracted, str) and isinstance(expected, str):
        # Normalize
        extracted_norm = extracted.lower().strip()
        expected_norm = expected.lower().strip()

        if extracted_norm == expected_norm:
            return {"status": "CORRECT", "details": f"Match: {extracted}"}
        elif expected_norm in extracted_norm or extracted_norm in expected_norm:
            return {"status": "PARTIAL", "details": f"Partial match: {extracted} vs {expected}"}
        else:
            return {"status": "INCORRECT", "details": f"Expected: {expected}, Got: {extracted}"}

    # List comparison (e.g., board_members)
    if isinstance(extracted, list) and isinstance(expected, list):
        extracted_set = set(str(x).lower().strip() for x in extracted)
        expected_set = set(str(x).lower().strip() for x in expected)

        if extracted_set == expected_set:
            return {"status": "CORRECT", "details": f"Match: {len(extracted)} members"}
        else:
            missing = expected_set - extracted_set
            extra = extracted_set - expected_set
            overlap = len(extracted_set & expected_set)
            total = len(expected_set)

            if overlap == total:
                return {"status": "CORRECT", "details": f"Match: {overlap}/{total} members"}
            elif overlap > 0:
                return {"status": "PARTIAL", "details": f"Partial: {overlap}/{total} members (missing: {missing}, extra: {extra})"}
            else:
                return {"status": "INCORRECT", "details": f"No overlap: expected {expected}, got {extracted}"}

    # Fallback: Direct equality
    if extracted == expected:
        return {"status": "CORRECT", "details": f"Match: {extracted}"}
    else:
        return {"status": "INCORRECT", "details": f"Expected: {expected}, Got: {extracted}"}


# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_71_fields_automated(
    extracted: dict,
    ground_truth: dict,
    tolerance: float = 0.05
) -> dict:
    """
    Automated validation of 71-field extraction against ground truth.

    Args:
        extracted: Our extraction result (flat or nested dict)
        ground_truth: Comprehensive ground truth JSON
        tolerance: Numeric tolerance for comparison (default ±5%)

    Returns:
        dict: {
            "total_fields": 71,
            "correct": N,
            "incorrect": N,
            "missing": N,
            "partial": N,
            "accuracy": float,
            "coverage": float,
            "field_results": List[dict]
        }
    """
    results = {
        "total_fields": len(FIELD_MAPPING_71),
        "correct": 0,
        "incorrect": 0,
        "missing": 0,
        "partial": 0,
        "field_results": []
    }

    for our_field, gt_path in FIELD_MAPPING_71.items():
        # Get values
        expected = get_nested_value(ground_truth, gt_path)
        actual = get_nested_value(extracted, our_field)

        # Compare
        comparison = compare_values(actual, expected, tolerance)

        # Update counters
        if comparison["status"] == "CORRECT":
            results["correct"] += 1
        elif comparison["status"] == "INCORRECT":
            results["incorrect"] += 1
        elif comparison["status"] == "MISSING":
            results["missing"] += 1
        elif comparison["status"] == "PARTIAL":
            results["partial"] += 1

        # Store detailed result
        results["field_results"].append({
            "field": our_field,
            "ground_truth_path": gt_path,
            "status": comparison["status"],
            "details": comparison["details"],
            "extracted": actual,
            "expected": expected
        })

    # Calculate metrics
    results["accuracy"] = results["correct"] / results["total_fields"] if results["total_fields"] > 0 else 0
    results["coverage"] = (results["correct"] + results["incorrect"] + results["partial"]) / results["total_fields"] if results["total_fields"] > 0 else 0

    return results


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import json

    # Example: Load ground truth
    # gt = json.load(open("brf_198532_comprehensive_ground_truth.json"))

    # Example: Mock ground truth
    gt = {
        "governance": {
            "chairman": "Elvy Svensson",
            "board_members": ["Member 1", "Member 2"]
        },
        "income_statement": {
            "2021": {
                "revenue": {
                    "nettoomsattning": 7393591,
                    "arsavgifter": 5264131,
                    "summa_intakter": 8033323
                },
                "expenses": {
                    "summa_rörelsekostnader": -6631400,
                    "fastighetsskott": 553590
                }
            }
        },
        "loans": [
            {"lender": "SEB", "amount_2021": 30000000, "interest_rate": 0.0057},
            {"lender": "SEB", "amount_2021": 30000000, "interest_rate": 0.0059}
        ]
    }

    # Example: Mock extraction
    extracted = {
        "chairman": "Elvy Svensson",
        "board_members": ["Member 1", "Member 2"],
        "revenue_breakdown": {
            "nettoomsattning": 7393591,
            "arsavgifter": 5264131
        },
        "loan_1_lender": "SEB",
        "loan_1_amount": 30000000
    }

    # Validate
    results = validate_71_fields_automated(extracted, gt)

    print(f"✅ Validation Results:")
    print(f"   Accuracy: {results['accuracy']*100:.1f}%")
    print(f"   Coverage: {results['coverage']*100:.1f}%")
    print(f"   Correct: {results['correct']}")
    print(f"   Incorrect: {results['incorrect']}")
    print(f"   Missing: {results['missing']}")
    print(f"   Partial: {results['partial']}")

    # Show first 5 errors
    errors = [r for r in results['field_results'] if r['status'] != 'CORRECT']
    print(f"\n❌ First 5 errors:")
    for error in errors[:5]:
        print(f"   {error['field']}: {error['status']} - {error['details']}")
