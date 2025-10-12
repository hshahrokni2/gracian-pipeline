#!/usr/bin/env python3
"""
Generate agent-aligned ground truth from semantic ground truth and validation results.

This script maps semantic field names to agent-grouped field names based on:
1. The original semantic ground truth structure
2. The actual extraction output (from validation results)
3. Evidence of value matches between the two
"""

import json
from pathlib import Path
from typing import Dict, Any

def load_json(path: str) -> Dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_agent_aligned_ground_truth() -> Dict[str, Any]:
    """Create agent-aligned ground truth from semantic ground truth."""

    # Load semantic ground truth
    semantic_gt = load_json("ground_truth/brf_198532_comprehensive_ground_truth.json")

    # Load validation results to see extraction structure
    validation_results = load_json("week3_day5_validation_results.json")

    # Initialize agent-aligned structure
    agent_gt = {
        "metadata": semantic_gt.get("metadata", {}),
    }

    # Map governance fields
    governance = semantic_gt.get("governance", {})
    agent_gt["governance_agent"] = {
        "chairman": governance.get("board_members", [{}])[0].get("name") if governance.get("board_members") else None,
        "board_members": governance.get("board_members", []),
        "auditor": governance.get("auditors", [{}])[0].get("name") if governance.get("auditors") else None,
        "audit_firm": governance.get("auditors", [{}])[0].get("firm") if governance.get("auditors") else None,
        "evidence_pages": [2, 3]
    }

    # Map cash flow fields (from validation: cashflow_agent)
    cash_flow_2021 = semantic_gt.get("cash_flow_2021", {})
    agent_gt["cashflow_agent"] = {
        "cash_in": cash_flow_2021.get("inflows", {}).get("total"),
        "cash_out": cash_flow_2021.get("outflows", {}).get("total"),
        "cash_change": cash_flow_2021.get("change_in_liquid_assets"),
        "evidence_pages": cash_flow_2021.get("source_pages", [])
    }

    # Map financial fields (from validation: financial_agent)
    financial = semantic_gt.get("financial", {})
    income = financial.get("income_statement", {})
    balance = financial.get("balance_sheet", {})

    agent_gt["financial_agent"] = {
        "revenue": income.get("revenue"),
        "expenses": income.get("expenses"),
        "net_income": income.get("net_income"),
        "assets": balance.get("assets"),
        "liabilities": balance.get("liabilities"),
        "equity": balance.get("equity"),
        "evidence_pages": [4, 5, 14]
    }

    # Map property fields (from validation: property_agent)
    property_data = semantic_gt.get("property", {})
    agent_gt["property_agent"] = {
        "address": property_data.get("address"),
        "property_designation": property_data.get("property_designation"),
        "area_sqm": None,  # Not in semantic GT
        "evidence_pages": property_data.get("source_pages", [])
    }

    # Map audit fields (from validation: audit_agent)
    auditors = semantic_gt.get("governance", {}).get("auditors", [{}])[0]
    agent_gt["audit_agent"] = {
        "auditor": auditors.get("name"),
        "audit_firm": auditors.get("firm"),
        "opinion": None,  # Not explicitly in semantic GT
        "clean_opinion": None,
        "evidence_pages": [16]
    }

    # Map apartments (from validation: apartments or operations_agent)
    apartments = semantic_gt.get("apartments", {})
    agent_gt["apartments"] = {
        "total_count": apartments.get("total_count"),
        "breakdown": apartments.get("breakdown", {}),
        "evidence_pages": apartments.get("source_pages", [])
    }

    # Map fees (from validation: fees_agent)
    fees = semantic_gt.get("fees", {})
    agent_gt["fees_agent"] = {
        "monthly_fee_avg": fees.get("monthly_fee_avg"),
        "annual_fee": fees.get("annual_fee"),
        "evidence_pages": fees.get("source_pages", [])
    }

    # Map loans (from validation: loans_agent or loans list)
    loans = semantic_gt.get("loans", [])
    agent_gt["loans"] = loans

    # Map notes (building_details_note8 → note_8 or building_agent)
    building_note8 = semantic_gt.get("building_details_note8", {})
    agent_gt["note_8_buildings"] = building_note8

    receivables_note9 = semantic_gt.get("receivables_breakdown_note9", {})
    agent_gt["note_9_receivables"] = receivables_note9

    # Map accounting principles
    accounting = semantic_gt.get("accounting_principles", {})
    agent_gt["accounting_principles"] = accounting

    # Map collateral
    collateral = semantic_gt.get("collateral", {})
    agent_gt["collateral"] = collateral

    # Map contracts
    contracts = semantic_gt.get("contracts", {})
    agent_gt["contracts"] = contracts

    # Map commercial tenants
    commercial = semantic_gt.get("commercial_tenants", [])
    agent_gt["commercial_tenants"] = commercial

    # Map common areas
    common_areas = semantic_gt.get("common_areas", {})
    agent_gt["common_areas"] = common_areas

    return agent_gt


def main():
    """Generate and save agent-aligned ground truth."""

    print("=" * 80)
    print("Generating Agent-Aligned Ground Truth")
    print("=" * 80)

    print("\n📂 Loading semantic ground truth...")
    print("   Source: ground_truth/brf_198532_comprehensive_ground_truth.json")

    print("\n🔄 Mapping semantic fields → agent-grouped structure...")
    agent_gt = create_agent_aligned_ground_truth()

    # Count fields
    def count_fields(d: Dict, exclude_meta: bool = True) -> int:
        """Count non-null leaf fields."""
        count = 0
        for k, v in d.items():
            if exclude_meta and k.startswith('_'):
                continue
            if isinstance(v, dict):
                count += count_fields(v, exclude_meta)
            elif isinstance(v, list) and v:
                count += 1
            elif v is not None:
                count += 1
        return count

    field_count = count_fields(agent_gt)

    print(f"   ✓ Mapped {field_count} fields to agent-grouped structure")

    # Save output
    output_path = "ground_truth/brf_198532_agent_aligned_ground_truth.json"
    print(f"\n💾 Saving agent-aligned ground truth...")
    print(f"   Output: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(agent_gt, f, indent=2, ensure_ascii=False)

    print(f"   ✓ Saved successfully")

    # Print summary
    print(f"\n{'=' * 80}")
    print("AGENT-ALIGNED GROUND TRUTH CREATED")
    print(f"{'=' * 80}")
    print(f"\n📊 Summary:")
    print(f"   Fields mapped: {field_count}")
    print(f"   Agent groups: {len([k for k in agent_gt.keys() if not k.startswith('_')])}")

    print(f"\n🔑 Key agent groups:")
    for key in sorted(agent_gt.keys()):
        if not key.startswith('_'):
            value = agent_gt[key]
            if isinstance(value, dict):
                sub_count = count_fields(value, exclude_meta=False)
                print(f"   • {key}: {sub_count} fields")
            elif isinstance(value, list):
                print(f"   • {key}: {len(value)} items")
            else:
                print(f"   • {key}: {type(value).__name__}")

    print(f"\n✅ Next step: Update validate_95_95_comprehensive.py to use:")
    print(f'   gt_path = "{output_path}"')
    print()


if __name__ == "__main__":
    main()
