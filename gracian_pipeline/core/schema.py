from __future__ import annotations

from typing import Dict, Any


# Base expected types per agent. Types: 'str', 'num', 'bool', 'list', 'num|str'
EXPECTED_TYPES: Dict[str, Dict[str, str]] = {
    "metadata_agent": {
        "brf_name": "str",
        "org_number": "str",
        "report_year": "num",
        "accounting_standard": "str",  # "K2"|"K3"
        "pages": "num",
        "evidence_pages": "list",
    },
    "governance_agent": {
        "chairman": "str",
        "board_members": "list",
        "auditor_name": "str",
        "audit_firm": "str",
        "nomination_committee": "list",
        "evidence_pages": "list",
    },
    "financial_agent": {
        "revenue": "num",
        "expenses": "num",
        "assets": "num",
        "liabilities": "num",
        "equity": "num",
        "surplus": "num",
        "consecutive_loss_years": "num",  # Count of consecutive loss years
        "multi_year_metrics": "list",  # Flerårsöversikt data
        "evidence_pages": "list",
    },
    "property_agent": {
        "designation": "str",
        "address": "str",
        "postal_code": "str",
        "city": "str",
        "built_year": "num|str",
        "apartments": "num|str",
        "energy_class": "str",
        "evidence_pages": "list",
    },
    "notes_depreciation_agent": {
        "depreciation_method": "str",
        "useful_life_years": "num|str",
        "depreciation_base": "num|str",
        "evidence_pages": "list",
    },
    "notes_maintenance_agent": {
        "maintenance_plan": "str",
        "maintenance_budget": "num|str",
        "major_project": "str",
        "expensing_strategy": "str",  # "capitalized"|"expensed_directly"|"mixed"
        "evidence_pages": "list",
    },
    "notes_tax_agent": {
        "current_tax": "num|str",
        "deferred_tax": "num|str",
        "tax_policy": "str",
        "evidence_pages": "list",
    },
    "events_agent": {
        "key_events": "list",
        "maintenance_budget": "num|str",
        "annual_meeting_date": "str",
        "evidence_pages": "list",
    },
    "audit_agent": {
        "auditor": "str",
        "opinion": "str",
        "clean_opinion": "bool",
        "evidence_pages": "list",
    },
    "loans_agent": {
        "loans": "list",  # List of loan objects with maturity classification
        "outstanding_loans": "num",
        "interest_rate": "num",
        "amortization": "num",
        "evidence_pages": "list",
    },
    "reserves_agent": {
        "reserve_fund": "num",
        "monthly_fee": "num",
        "evidence_pages": "list",
    },
    "energy_agent": {
        "energy_class": "str",
        "energy_performance": "num|str",
        "inspection_date": "str",
        "evidence_pages": "list",
    },
    "fees_agent": {
        "monthly_fee": "num|str",
        "planned_fee_change": "num|str",
        "fee_policy": "str",
        "evidence_pages": "list",
    },
    "cashflow_agent": {
        "cash_in": "num|str",
        "cash_out": "num|str",
        "cash_change": "num|str",
        "evidence_pages": "list",
    },
}


def get_types(agent_id: str) -> Dict[str, str]:
    return EXPECTED_TYPES.get(agent_id, {})


def schema_prompt_block(agent_id: str) -> str:
    t = get_types(agent_id)
    if not t:
        return ""
    # Render as key:type pairs for clarity in the prompt
    pairs = ", ".join([f"{k}:{v}" for k, v in t.items()])
    guidance = (
        "Use this schema strictly. If a field is not visible in provided pages, leave it empty or []. "
        "Never invent numbers or return 0 unless 0 is explicitly printed. "
        "Always include evidence_pages with 1-based page numbers you used. "
        "If the schema is inadequate, add a top-level key 'schema_extension' with suggested {key:type} additions, "
        "and still return the flat JSON with both existing and new fields filled when visible."
    )
    return f"Schema keys: {{{pairs}}}. {guidance}"
