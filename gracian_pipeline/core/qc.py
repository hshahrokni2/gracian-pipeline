from __future__ import annotations

import math
import re
from typing import Dict, Any, Tuple


def _to_float(x: Any) -> Tuple[bool, float | None]:
    if isinstance(x, (int, float)):
        return True, float(x)
    if not isinstance(x, str):
        return False, None
    s = x.replace("\u00a0", " ").replace(" ", "").replace(",", ".").replace("%", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return True, float(s)
    except Exception:
        return False, None


def qc_financial(d: Dict[str, Any], tol: float = 0.06) -> Dict[str, Any]:
    ok = {}
    checks = {}
    rev_ok, rev = _to_float(d.get("revenue"))
    exp_ok, exp = _to_float(d.get("expenses"))
    sur_ok, sur = _to_float(d.get("surplus"))
    if rev_ok and exp_ok and sur_ok:
        diff = (rev - exp) - sur
        denom = max(1.0, abs(rev) + abs(exp))
        pass_sur = abs(diff) / denom <= tol
        checks["surplus_balance"] = {"ok": pass_sur, "diff": diff}
        ok["surplus_balance"] = pass_sur

    a_ok, a = _to_float(d.get("assets"))
    l_ok, l = _to_float(d.get("liabilities"))
    e_ok, e = _to_float(d.get("equity"))
    if a_ok and l_ok and e_ok:
        diff = a - (l + e)
        denom = max(1.0, abs(a))
        pass_bs = abs(diff) / denom <= tol
        checks["balance_sheet"] = {"ok": pass_bs, "diff": diff}
        ok["balance_sheet"] = pass_bs

    passed = any(ok.values()) if ok else False
    return {"passed": passed, "checks": checks}


def qc_loans(d: Dict[str, Any]) -> Dict[str, Any]:
    ok = {}
    amt_ok, amt = _to_float(d.get("outstanding_loans"))
    if amt_ok:
        ok["amount_nonnegative"] = (amt is not None and amt >= 0)
    ir_ok, ir = _to_float(d.get("interest_rate"))
    if ir_ok:
        ok["interest_rate_range"] = (0.0 <= (ir or 0.0) <= 20.0)
    am_ok, am = _to_float(d.get("amortization"))
    if am_ok:
        ok["amortization_nonnegative"] = (am is not None and am >= 0)
    passed = any(ok.values()) if ok else False
    return {"passed": passed, "checks": ok}


def qc_reserves(d: Dict[str, Any]) -> Dict[str, Any]:
    ok = {}
    rf_ok, rf = _to_float(d.get("reserve_fund"))
    if rf_ok:
        ok["reserve_nonnegative"] = (rf is not None and rf >= 0)
    mf_ok, mf = _to_float(d.get("monthly_fee"))
    if mf_ok:
        ok["monthly_fee_nonnegative"] = (mf is not None and mf >= 0)
    passed = any(ok.values()) if ok else False
    return {"passed": passed, "checks": ok}


def numeric_qc(agent_id: str, d: Dict[str, Any]) -> Dict[str, Any]:
    if agent_id == "financial_agent":
        return qc_financial(d)
    if agent_id == "loans_agent":
        return qc_loans(d)
    if agent_id == "reserves_agent":
        return qc_reserves(d)
    return {"passed": True, "checks": {}}

