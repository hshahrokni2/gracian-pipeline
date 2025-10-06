"""
Swedish-First BRF Schema with Semantic Clarity
Version 2.0 - Multi-lingual field naming

Solves: Fee field semantics mismatch where Swedish "årsavgift/m²" was mapped to "monthly_fee".
Now uses semantic Swedish-first fields that match actual BRF terminology.
"""

from __future__ import annotations
from typing import Dict
from gracian_pipeline.core.schema_comprehensive import COMPREHENSIVE_TYPES


# SEMANTIC FEE SCHEMA (Swedish-First)
COMPREHENSIVE_TYPES_V2: Dict[str, Dict[str, str]] = {
    **COMPREHENSIVE_TYPES,  # Inherit all base comprehensive fields

    # Override fees_agent with v2 semantic fields
    "fees_agent": {
        # SWEDISH BRF STANDARD FIELDS (Primary)
        "arsavgift_per_sqm": "num",           # Årsavgift/m² bostadsrättsyta (MOST COMMON)
        "arsavgift_per_apartment": "num",     # Årsavgift per lägenhet (rare)
        "manadsavgift_per_sqm": "num",        # Månadsavgift/m² (very rare)
        "manadsavgift_per_apartment": "num",  # Månadsavgift per lägenhet (uncommon)

        # FEE CHANGE INFORMATION
        "planned_fee_change": "str",          # E.g., "Oförändrade närmaste året"
        "fee_calculation_basis": "str",       # E.g., "självkostnadsprincipen"
        "fee_policy": "str",

        # METADATA (for validation and migration)
        "_fee_terminology_found": "str",      # Original Swedish term in PDF
        "_fee_unit_verified": "str",          # "per_sqm" | "per_apartment"
        "_fee_period_verified": "str",        # "annual" | "monthly"

        # LEGACY FIELDS (deprecated but maintained for backwards compatibility)
        "monthly_fee": "num",    # DEPRECATED: Use specific fields above
        "fee_per_sqm": "num",    # DEPRECATED: Time unit ambiguous
        "fee_unit": "str",       # DEPRECATED: Separate unit field not needed

        "evidence_pages": "list"
    }
}


# EXTRACTION GUIDANCE
FEE_EXTRACTION_GUIDE = """
FEE EXTRACTION RULES (Swedish BRF Documents):

STEP 1: Find exact Swedish terminology in document
Look for phrases:
- "Årsavgift/m² bostadsrättsyta: X"
- "Månadsavgift per lägenhet: Y"
- "Avgift per m² och år: Z"

STEP 2: Map to correct semantic field

Swedish Term                          → Field Name
"Årsavgift/m²"                        → arsavgift_per_sqm
"Årsavgift per lägenhet"              → arsavgift_per_apartment
"Månadsavgift/m²"                     → manadsavgift_per_sqm
"Månadsavgift per lägenhet"           → manadsavgift_per_apartment

STEP 3: Extract value and store metadata

Example:
PDF says: "Årsavgift/m² bostadsrättsyta: 582 kr"

Correct extraction:
{
  "arsavgift_per_sqm": 582,
  "_fee_terminology_found": "Årsavgift/m² bostadsrättsyta",
  "_fee_unit_verified": "per_sqm",
  "_fee_period_verified": "annual"
}

CRITICAL: Do NOT use legacy fields (monthly_fee, fee_per_sqm, fee_unit).
Use semantic Swedish-first fields.
"""


def get_comprehensive_types_v2(agent_id: str) -> Dict[str, str]:
    """
    Get comprehensive v2 types for an agent (Swedish-first semantic fields).

    Args:
        agent_id: Agent identifier (e.g., "fees_agent")

    Returns:
        Dictionary of field names to types
    """
    return COMPREHENSIVE_TYPES_V2.get(agent_id, {})


def schema_comprehensive_prompt_block_v2(agent_id: str) -> str:
    """
    Enhanced prompt for v2 schema with fee guidance.

    Args:
        agent_id: Agent identifier

    Returns:
        Formatted schema prompt for extraction
    """
    types = get_comprehensive_types_v2(agent_id)

    if agent_id == "fees_agent":
        # Special prompt for fees with extraction guide
        lines = [
            "FEES AGENT SCHEMA (v2 - Swedish-First Semantic Fields):",
            "",
            FEE_EXTRACTION_GUIDE,
            "",
            "OUTPUT SCHEMA:",
            "{"
        ]

        for field, typ in types.items():
            if field.startswith("_"):
                comment = "// Metadata field"
            elif field in ["monthly_fee", "fee_per_sqm", "fee_unit"]:
                comment = "// DEPRECATED - do not use"
            elif field.startswith("arsavgift"):
                comment = "// If 'Årsavgift' found"
            elif field.startswith("manadsavgift"):
                comment = "// If 'Månadsavgift' found"
            else:
                comment = ""

            type_hint = "number" if typ == "num" else "string" if typ == "str" else f"[{typ}]" if typ == "list" else "{...}"
            lines.append(f'  "{field}": {type_hint},  {comment}')

        lines.append("}")
        lines.append("")
        lines.append("CRITICAL: Extract exact Swedish terminology. Use semantic v2 fields only.")

        return "\n".join(lines)

    else:
        # Standard prompt for other agents
        lines = [f"AGENT: {agent_id}", "OUTPUT JSON with these fields:"]
        for field, typ in types.items():
            type_hint = "number" if typ == "num" else "string" if typ == "str" else f"array" if typ == "list" else "object"
            lines.append(f'  "{field}": {type_hint}')
        return "\n".join(lines)


def get_field_counts_v2() -> Dict[str, Dict[str, int]]:
    """
    Return field counts for base vs comprehensive v2 schema.

    Returns:
        Dictionary with comprehensive_v2 field counts per agent
    """
    counts = {}
    for agent_id, fields in COMPREHENSIVE_TYPES_V2.items():
        counts[agent_id] = len(fields)
    return {"comprehensive_v2": counts}


# Migration utilities will be in separate file (fee_field_migrator.py)
