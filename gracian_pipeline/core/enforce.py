from __future__ import annotations

import os
import re
from typing import Dict, Any, Tuple
from .schema import EXPECTED_TYPES


## Expected types imported from core.schema


def _parse_num(s: Any) -> Tuple[bool, float | None]:
    if isinstance(s, (int, float)):
        return True, float(s)
    if not isinstance(s, str):
        return False, None
    s2 = s.replace("\u00a0", " ").replace(" ", "").replace("%", "").replace(",", ".")
    s2 = re.sub(r"[^0-9.\-]", "", s2)
    if s2 in ("", "-", "."):
        return False, None
    try:
        return True, float(s2)
    except Exception:
        return False, None


def enforce(agent_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Return (possibly modified data, verification_meta, dropped_fields).
    Modes:
      ENFORCE_VERIFICATION: soft|strict (default soft)
      STRICT_NEEDS_EVIDENCE: true|false (default false) — if true, numeric fields require evidence_pages to be kept
    """
    mode = os.getenv("ENFORCE_VERIFICATION", "soft").lower()
    needs_evidence = os.getenv("STRICT_NEEDS_EVIDENCE", "false").lower() == "true"
    # Only gate numerics by evidence for numeric-heavy agents (default true)
    numeric_agents_only = os.getenv("STRICT_NUMERIC_AGENTS_ONLY", "true").lower() == "true"
    NUMERIC_AGENTS = {"financial_agent", "loans_agent", "reserves_agent", "cashflow_agent"}

    schema = EXPECTED_TYPES.get(agent_id, {})
    verified: Dict[str, Any] = {}
    dropped: Dict[str, Any] = {}

    evidence_pages = data.get("evidence_pages", [])
    has_evidence = isinstance(evidence_pages, list) and len(evidence_pages) > 0

    out = dict(data)
    for k, t in schema.items():
        v = out.get(k)
        ok = False
        reason = ""
        if t == "str":
            ok = isinstance(v, str) and v.strip() != ""
            reason = "non-empty string" if ok else "empty or not string"
        elif t == "list":
            ok = isinstance(v, list) and len(v) > 0
            reason = "non-empty list" if ok else "empty or not list"
        elif t == "bool":
            ok = isinstance(v, bool)
            reason = "bool" if ok else "not bool"
        elif t in ("num", "num|str"):
            if isinstance(v, (int, float)):
                ok = True
                reason = "numeric"
            else:
                ok, num = _parse_num(v)
                reason = "parsed numeric" if ok else "not numeric"
            if needs_evidence and (not numeric_agents_only or agent_id in NUMERIC_AGENTS) and not has_evidence:
                verified[k] = {"verified": False, "reason": "missing evidence_pages"}
                if mode == "strict":
                    dropped[k] = v
                    out[k] = ""
                continue
        else:
            ok = v is not None
            reason = "present" if ok else "missing"

        verified[k] = {"verified": ok, "reason": reason}
        if mode == "strict" and not ok:
            dropped[k] = v
            # set to empty of appropriate shape
            if t == "list":
                out[k] = []
            elif t == "bool":
                out[k] = False
            else:
                out[k] = ""

    return out, verified, dropped
