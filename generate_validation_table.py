#!/usr/bin/env python3
"""
Generate human-readable validation table comparing extraction results vs ground truth.
"""

import json
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_nested_value(data, path):
    """Get value from nested dictionary using dot notation."""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return None
        else:
            return None
    return value

def format_value(value):
    """Format value for display."""
    if value is None:
        return "❌ NULL"
    elif isinstance(value, list):
        if len(value) == 0:
            return "❌ []"
        return f"✅ {value}"
    elif isinstance(value, str) and value == "":
        return "❌ (empty)"
    elif isinstance(value, dict):
        return f"✅ {json.dumps(value, ensure_ascii=False)[:100]}..."
    else:
        return f"✅ {value}"

def generate_validation_table():
    """Generate comprehensive validation table."""

    # Load files
    extraction = load_json("deep_mode_full_test_vision_complete.json")
    ground_truth = load_json("ground_truth/brf_198532_ground_truth.json")

    print("# 🔍 HUMAN VALIDATION TABLE - Ground Truth vs Extraction")
    print()
    print("**Document**: brf_198532.pdf (BRF Björk och Plaza)")
    print("**Extraction File**: deep_mode_full_test_vision_complete.json")
    print("**Ground Truth File**: ground_truth/brf_198532_ground_truth.json")
    print()
    print("---")
    print()

    # Define all fields to validate (from ground truth)
    fields_to_check = [
        # Governance
        ("governance_agent.chairman", "Chairman"),
        ("governance_agent.board_members", "Board Members"),
        ("governance_agent.auditor_name", "Auditor Name"),
        ("governance_agent.audit_firm", "Audit Firm"),
        ("governance_agent.nomination_committee", "Nomination Committee"),

        # Financial
        ("financial_agent.revenue", "Revenue"),
        ("financial_agent.expenses", "Expenses"),
        ("financial_agent.assets", "Assets"),
        ("financial_agent.liabilities", "Liabilities"),
        ("financial_agent.equity", "Equity"),
        ("financial_agent.surplus", "Surplus/Deficit"),

        # Financial - Building Details (Note 8)
        ("financial_agent.building_details.ackumulerade_anskaffningsvarden", "Building: Accumulated Acquisition Value"),
        ("financial_agent.building_details.arets_avskrivningar", "Building: Year's Depreciation"),
        ("financial_agent.building_details.planenligt_restvarde", "Building: Planned Residual Value"),
        ("financial_agent.building_details.taxeringsvarde_byggnad", "Building: Tax Assessment Value"),
        ("financial_agent.building_details.taxeringsvarde_mark", "Land: Tax Assessment Value"),

        # Financial - Receivables (Note 9)
        ("financial_agent.receivables_breakdown.skattekonto", "Receivables: Tax Account"),
        ("financial_agent.receivables_breakdown.momsavrakning", "Receivables: VAT Deduction"),
        ("financial_agent.receivables_breakdown.klientmedel", "Receivables: Client Funds"),
        ("financial_agent.receivables_breakdown.fordringar", "Receivables: Receivables"),
        ("financial_agent.receivables_breakdown.avrakning_ovrigt", "Receivables: Other Deductions"),

        # Property
        ("property_agent.property_designation", "Property Designation"),
        ("property_agent.municipality", "Municipality"),

        # Property - Apartment Breakdown
        ("property_agent.apartment_breakdown.1_rok", "Apartments: 1 room"),
        ("property_agent.apartment_breakdown.2_rok", "Apartments: 2 rooms"),
        ("property_agent.apartment_breakdown.3_rok", "Apartments: 3 rooms"),
        ("property_agent.apartment_breakdown.4_rok", "Apartments: 4 rooms"),
        ("property_agent.apartment_breakdown.5_rok", "Apartments: 5 rooms"),
        ("property_agent.apartment_breakdown.>5_rok", "Apartments: >5 rooms"),

        # Fees
        ("fees_agent.arsavgift_per_sqm", "Annual Fee per sqm"),
    ]

    # Generate table
    print("## 📊 Field-by-Field Comparison")
    print()
    print("| # | Field | Ground Truth | Extracted | Match |")
    print("|---|-------|--------------|-----------|-------|")

    total_fields = 0
    correct_fields = 0
    missing_fields = 0
    incorrect_fields = 0

    for i, (field_path, field_name) in enumerate(fields_to_check, 1):
        gt_value = get_nested_value(ground_truth, field_path)
        ext_value = get_nested_value(extraction, field_path)

        # Skip fields marked as NOT_IN_DOCUMENT or NEED_TO_VERIFY in ground truth
        if gt_value in ["NOT_IN_DOCUMENT", "NEED_TO_VERIFY", "PRESENT_IN_DOCUMENT_BUT_NOT_EXTRACTED"]:
            continue

        total_fields += 1

        # Format values
        gt_display = str(gt_value) if gt_value is not None else "❌ NULL"
        ext_display = format_value(ext_value)

        # Check match
        if ext_value is None:
            match = "❌ MISSING"
            missing_fields += 1
        elif str(ext_value) == str(gt_value):
            match = "✅ EXACT"
            correct_fields += 1
        elif isinstance(ext_value, (int, float)) and isinstance(gt_value, (int, float)):
            # Check numeric tolerance (±1 for rounding)
            if abs(ext_value - gt_value) <= 1:
                match = "✅ ROUNDED"
                correct_fields += 1
            else:
                match = f"❌ DIFF ({ext_value} vs {gt_value})"
                incorrect_fields += 1
        else:
            match = f"⚠️ MISMATCH"
            incorrect_fields += 1

        # Print row
        print(f"| {i} | {field_name} | `{gt_display}` | `{ext_display}` | {match} |")

    print()
    print("---")
    print()
    print("## 📈 Summary Statistics")
    print()
    print(f"- **Total Fields Validated**: {total_fields}")
    print(f"- **✅ Correct**: {correct_fields}")
    print(f"- **❌ Missing**: {missing_fields}")
    print(f"- **⚠️ Incorrect**: {incorrect_fields}")
    print()

    accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 0
    print(f"### 🎯 Accuracy: **{accuracy:.1f}%** ({correct_fields}/{total_fields})")
    print()

    if accuracy >= 100:
        print("✅ **PERFECT SCORE - 100% ACCURACY ACHIEVED!**")
    elif accuracy >= 95:
        print("✅ **PRODUCTION READY - Exceeds 95% Target**")
    elif accuracy >= 90:
        print("⚠️ **NEAR TARGET - Minor fixes needed**")
    else:
        print("❌ **NEEDS IMPROVEMENT - Below 90%**")

    print()
    print("---")
    print()
    print("*Generated for human validation review*")

if __name__ == "__main__":
    generate_validation_table()
