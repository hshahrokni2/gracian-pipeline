import os
import json
import re
from typing import Dict, Any, Tuple
from .vertex import vertex_generate_text
from openai import OpenAI
import time


def _num(s: str) -> Tuple[bool, float | None]:
    try:
        # Normalize Swedish thousands/decimal formats
        s2 = s.replace('\u00a0', ' ').replace(' ', '')
        s2 = s2.replace('%', '')
        s2 = s2.replace(',', '.')
        # Remove any non-digit/.- except leading minus
        s2 = re.sub(r"[^0-9.\-]", "", s2)
        if s2 in ("", "-", "."):
            return False, None
        return True, float(s2)
    except Exception:
        return False, None


EXPECTED_KEYS: Dict[str, Dict[str, str]] = {
    "governance_agent": {
        "chairman": "str",
        "board_members": "list",
        "auditor_name": "str",
        "audit_firm": "str",
        "nomination_committee": "list",
    },
    "financial_agent": {
        "revenue": "num",
        "expenses": "num",
        "assets": "num",
        "liabilities": "num",
        "equity": "num",
        "surplus": "num",
    },
    "property_agent": {
        "designation": "str",
        "address": "str",
        "postal_code": "str",
        "city": "str",
        "built_year": "num",
        "apartments": "num",
        "energy_class": "str",
    },
    "notes_agent": {
        "loans_amount": "num",
        "depreciation_method": "str",
        "maintenance_plan": "str",
    },
    "events_agent": {
        "key_events": "list",
        "maintenance_budget": "num|str",
        "annual_meeting_date": "str",
    },
    "signatures_agent": {
        "signatures": "list",
    },
    "audit_agent": {
        "auditor": "str",
        "opinion": "str",
        "clean_opinion": "bool",
    },
    "loans_agent": {
        "outstanding_loans": "num",
        "interest_rate": "num",
        "amortization": "num",
    },
    "reserves_agent": {
        "reserve_fund": "num",
        "monthly_fee": "num",
    },
    "energy_agent": {
        "energy_class": "str",
        "energy_performance": "num|str",
        "inspection_date": "str",
    },
    "fees_agent": {
        "monthly_fee": "num|str",
        "planned_fee_change": "num|str",
        "fee_policy": "str",
    },
    "cashflow_agent": {
        "cash_in": "num|str",
        "cash_out": "num|str",
        "cash_change": "num|str",
    },
}


def score_output(agent_id: str, data: Dict[str, Any]) -> float:
    schema = EXPECTED_KEYS.get(agent_id, {})
    if not schema:
        # Generic: proportion of non-empty keys
        filled = sum(1 for v in data.values() if (isinstance(v, (list, dict)) and v) or (isinstance(v, str) and v.strip()) or isinstance(v, (int, float)))
        total = max(len(data), 1)
        return 50.0 * filled / total
    score = 0.0
    per_key = 100.0 / max(len(schema), 1)
    for k, t in schema.items():
        v = data.get(k, None)
        if v is None:
            continue
        ok = False
        if t == "str":
            ok = isinstance(v, str) and v.strip() != ""
        elif t == "list":
            ok = isinstance(v, list) and len(v) > 0
        elif t == "bool":
            ok = isinstance(v, bool)
        elif t == "num":
            if isinstance(v, (int, float)):
                ok = True
            elif isinstance(v, str):
                ok, _ = _num(v)
        elif t == "num|str":
            if isinstance(v, (int, float)):
                ok = True
            elif isinstance(v, str):
                ok = v.strip() != ""
        if ok:
            score += per_key
    # Clamp
    return max(0.0, min(100.0, score))


def call_gemini_text(prompt: str, content: str) -> str:
    import requests, os, time
    use_vertex = os.getenv("GEMINI_VIA_VERTEX", "true").lower() == "true"
    sa = os.getenv("VERTEX_SA_JSON")
    project = os.getenv("VERTEX_PROJECT")
    if use_vertex and sa and project:
        model = os.getenv("VERTEX_MODEL", "gemini-1.5-pro-001")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        return vertex_generate_text(sa, project, location, model, prompt, content)
    # fallback to API key path
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set and Vertex not configured")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}, {"text": content}]}]}
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, timeout=90)
            r.raise_for_status()
            out = r.json()
            try:
                return out["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                return str(out)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Gemini text call failed after retries: {last_err}")


def call_openai_text(prompt: str, content: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    last_err = None
    # Prefer Responses API for GPT-5; fallback to Chat Completions
    use_responses = os.getenv("OPENAI_RESPONSES", "true").lower() == "true"
    if use_responses:
        for attempt in range(3):
            try:
                kwargs = {
                    "model": model,
                    "input": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": prompt},
                                {"type": "input_text", "text": content},
                            ],
                        }
                    ],
                    "max_output_tokens": 1200,
                }
                if os.getenv("OPENAI_JSON_MODE", "false").lower() == "true":
                    kwargs["response_format"] = {"type": "json_object"}
                resp = client.responses.create(**kwargs)
                # New SDK returns output_text
                if getattr(resp, "output_text", None):
                    return resp.output_text
                # Fallback parse
                try:
                    return resp.choices[0].message.content[0].text  # type: ignore
                except Exception:
                    return str(resp)
            except Exception as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ],
                max_completion_tokens=1200,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OpenAI text call failed after retries: {last_err}")


def call_qwen_openrouter_text(prompt: str, content: str) -> str:
    from openai import OpenAI
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    model = os.getenv("OPENROUTER_QWEN_MODEL")
    if not model:
        raise RuntimeError("OPENROUTER_QWEN_MODEL not set")
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


def jury_rank(agent_id: str, prompt: str, content: str, cand: Dict[str, str]) -> Dict[str, Any]:
    """Pick best candidate using a jury model.
    Provider via env:
      - JURY_PROVIDER=openrouter|xai (default openrouter)
      - If openrouter: uses OPENROUTER_API_KEY and JURY_MODEL_OPENROUTER (default 'openai/gpt-5')
      - If xai: uses XAI_API_KEY and JURY_MODEL (default XAI_MODEL)
    """
    from openai import OpenAI

    provider = os.getenv("JURY_PROVIDER", "openai").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set for jury")
        model = os.getenv("JURY_MODEL_OPENAI", os.getenv("OPENAI_MODEL", "gpt-5"))
        client = OpenAI(api_key=api_key)
        use_responses = os.getenv("OPENAI_RESPONSES", "true").lower() == "true"
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set for jury")
        model = os.getenv("JURY_MODEL_OPENROUTER", "openai/gpt-5")
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    else:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise RuntimeError("XAI_API_KEY not set for xAI jury")
        model = os.getenv("JURY_MODEL", os.getenv("XAI_MODEL", "grok-4-fast-reasoning-latest"))
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    inst = (
        "You are the jury. Given a BRF agent task and 3 JSON outputs, choose the best one. "
        "Criteria: (1) matches the schema, (2) plausible values for Swedish BRF, (3) internal numeric consistency, "
        "(4) alignment with the provided document excerpt. Return STRICT JSON: {best: 'grok'|'gemini'|'qwen', reasons: []}."
    )
    user = (
        f"Agent: {agent_id}\n\nTask: {prompt}\n\nDocument excerpt (may be truncated):\n{content[:3000]}\n\n"
        f"Candidates:\nGrok: {cand.get('grok','')}\n\nGemini: {cand.get('gemini','')}\n\nQwen: {cand.get('qwen','')}\n"
    )
    if provider == "openai" and use_responses:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": inst},
                        {"type": "input_text", "text": user},
                    ],
                }
            ],
            max_output_tokens=400,
        )
        txt = getattr(resp, "output_text", None) or str(resp)
    else:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": inst},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=400,
        )
        txt = resp.choices[0].message.content
    try:
        return json.loads(txt)
    except Exception:
        return {"best": "grok", "reasons": ["fallback"]}
