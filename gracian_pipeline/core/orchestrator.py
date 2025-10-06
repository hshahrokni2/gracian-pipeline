from __future__ import annotations

import os
import json as _json
import hashlib
import threading
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .vision_sectionizer import vision_sectionize, render_all_pages
from .vision_qc import json_guard, render_pdf_pages_subset, call_openai_responses_vision
from .schema import get_types, schema_prompt_block
from .qc import numeric_qc
from .enforce import enforce
from .bench import score_output
from .sectionizer import select_pages_for_agent


def _score_threshold(agent_id: str) -> float:
    # Target score can be globally set for 95/95 runs
    try:
        target = float(os.getenv("ORCHESTRATOR_TARGET_SCORE", "95"))
    except Exception:
        target = 95.0
    return target


def _distinct_ints(seq: List[int]) -> List[int]:
    return sorted({int(x) for x in seq if isinstance(x, int) and x >= 0})


def _coach_sectionizer_once(pdf_path: str, outline: Dict[str, Any]) -> Dict[str, Any]:
    """Ask GPT-5 (Responses) to review sectionizer output and propose corrected pages_by_agent.
    Sends all page images with labels so the model can reason globally.
    Returns a dict {pages_by_agent: {agent:[indices]}, notes: str, added_agents: []}
    """
    # Render all pages (PNG) – capped via env if needed
    max_pages_cap = int(os.getenv("ORCH_MAX_PAGES", "0") or "0")
    images = render_all_pages(pdf_path, dpi=int(os.getenv("SECTIONIZER_DPI", "170")))
    if max_pages_cap and len(images) > max_pages_cap:
        images = images[:max_pages_cap]
    page_labels = [f"Page {i+1}/{len(images)}" for i in range(len(images))]

    prompt = (
        "You are Orchestrator for a Swedish BRF document.\n"
        "You will coach the sectionizer to map each agent to exact 1-based page ranges.\n"
        "Agents include: governance_agent, property_agent, events_agent, audit_agent, "
        "financial_agent, loans_agent, reserves_agent, notes_depreciation_agent, "
        "notes_maintenance_agent, notes_tax_agent.\n"
        "Instructions: ONLY use visible headings and content in the provided page images.\n"
        "Return STRICT minified JSON: {pages_by_agent: {agent:[zero_based_page_indices]}, added_agents: [], notes: ''}.\n"
        "Do NOT guess; if unsure leave the agent list empty. Indices must be 0-based."
    )
    # Provide current outline to improve correction quality
    import json as _json
    outline_text = _json.dumps({k: outline.get(k, {}) for k in ("level_1", "level_2", "level_3", "pages_by_agent")}, ensure_ascii=False)

    # Include outline JSON inside the prompt so the model can compare and correct
    prompt_full = (
        prompt
        + "\nCurrent outline JSON (may be imperfect):\n"
        + outline_text
        + "\nPlease correct pages_by_agent based on the images."
    )
    raw = call_openai_responses_vision(prompt_full, images, page_labels=page_labels)
    coached = json_guard(raw, default={"pages_by_agent": outline.get("pages_by_agent", {}), "added_agents": [], "notes": ""})
    # Normalize pages_by_agent indices
    pmap = coached.get("pages_by_agent", {}) or {}
    norm = {a: _distinct_ints(v if isinstance(v, list) else []) for a, v in pmap.items()}
    coached["pages_by_agent"] = norm
    return coached


def _coach_agent_once(pdf_path: str, agent_id: str, pages: List[int], last_json: Dict[str, Any]) -> Dict[str, Any]:
    """Ask GPT-5 to refine the page list for a specific agent by looking at the images for those pages ±1 around.
    Returns dict {ok: bool, revised_pages: [ints], hints: ''}
    """
    # Expand small window around suggested pages to give the model local context
    extra = int(os.getenv("ORCH_AGENT_PAGE_PAD", "1") or "1")
    window: List[int] = []
    for p in pages or []:
        for d in range(-extra, extra + 1):
            window.append(p + d)
    window = _distinct_ints(window)
    if not window:
        window = [0, 1, 2]
    dpi = int(os.getenv("QC_PAGE_RENDER_DPI", "220"))
    imgs = render_pdf_pages_subset(pdf_path, window, dpi=dpi)
    plabels = [f"Page {i+1}" for i in window]

    schema = get_types(agent_id)
    import json as _json
    prompt = (
        "You are Orchestrator. Coach the agent to pick the right pages for extraction.\n"
        f"Agent: {agent_id}. Expected keys: {list(schema.keys())}.\n"
        "Given page images and the agent's last JSON, decide if pages are correct.\n"
        "Return STRICT minified JSON: {ok: true|false, revised_pages: [zero_based_indices], hints: ''}.\n"
        "If pages are wrong or incomplete, propose a better 0-based list limited to <=6 pages."
    )
    last_json_text = _json.dumps(last_json, ensure_ascii=False)
    # Include the last JSON as leading text before images
    raw = call_openai_responses_vision(prompt + "\nLast JSON:" + last_json_text, imgs, page_labels=plabels)
    out = json_guard(raw, default={"ok": False, "revised_pages": pages, "hints": ""})
    out["revised_pages"] = _distinct_ints(out.get("revised_pages", pages))[:6]
    out["ok"] = bool(out.get("ok", False))
    return out


def _global_pick_pages_for_agent(pdf_path: str, agent_id: str) -> List[int]:
    """As a last resort, sample pages across the whole document and ask GPT-5 to pick the best <=6 pages for this agent."""
    try:
        import fitz  # type: ignore
        doc = fitz.open(pdf_path)
        n = doc.page_count
        doc.close()
    except Exception:
        n = 0
    if n <= 0:
        return []
    max_samples = int(os.getenv("ORCH_GLOBAL_SAMPLE_PAGES", "18") or "18")
    stride = max(1, n // max(1, max_samples))
    sample_idxs = list(range(0, n, stride))[:max_samples]
    imgs = render_pdf_pages_subset(pdf_path, sample_idxs, dpi=int(os.getenv("SECTIONIZER_DPI", "150")))
    labels = [f"Page {i+1}/{n}" for i in sample_idxs]
    prompt = (
        "You are Orchestrator. Given sampled page images across the report, choose up to 6 0-based page indices "
        f"most relevant for agent '{agent_id}'. Return STRICT minified JSON: {{pages:[ints]}}."
    )
    raw = call_openai_responses_vision(prompt, imgs, page_labels=labels)
    out = json_guard(raw, default={"pages": []})
    pages = out.get("pages", [])
    try:
        pages = [int(x) for x in pages]
    except Exception:
        pages = []
    # Keep only those actually sampled to avoid hallucinated indices
    keep = [p for p in pages if p in sample_idxs]
    return sorted(set(keep))[:6]


def orchestrate_pdf(pdf_path: str, agents: Dict[str, str], max_rounds: int = 5) -> Dict[str, Any]:
    """High-level loop: sectionize, extract per agent, coach iteratively until acceptance or rounds exhausted.
    Returns results dict like the standard pipeline.
    """
    # Optionally limit number of agents for quick validation runs
    try:
        limit = int(os.getenv("ORCHESTRATOR_MAX_AGENTS", "0") or "0")
    except Exception:
        limit = 0
    agent_items = list(agents.items())[: limit or None]

    # 1) Initial outline via vision sectionizer (full doc)
    verbose = os.getenv("VERBOSE_ORCHESTRATOR", "true").lower() == "true"
    if verbose:
        print(f"[orchestrator] agents={list(agents.keys())}")
        print(f"[orchestrator] concurrency={os.getenv('ORCHESTRATOR_CONCURRENCY','2')} chunksize={os.getenv('VISION_PAGES_PER_CALL','10')}")
    outline = vision_sectionize(pdf_path)

    # 2) Coach sectionizer once (optional)
    try:
        coached = _coach_sectionizer_once(pdf_path, outline)
        if isinstance(coached, dict) and coached.get("pages_by_agent"):
            outline["pages_by_agent"] = coached["pages_by_agent"]
        added_agents = coached.get("added_agents") or []
        if added_agents:
            # Only act on agents we know prompts for; persist the rest
            for a in added_agents:
                if a in agents and a not in outline["pages_by_agent"]:
                    outline["pages_by_agent"][a] = []
        # Persist orchestrated section map for auditability
        try:
            import json as _json
            from pathlib import Path as _Path
            out_dir = _Path("data")/"raw_pdfs"/"outputs"/"sections"
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = _Path(pdf_path).stem + ".orchestrated.sections.json"
            with open(str(out_dir/fname), "w") as f:
                _json.dump({"coached": coached, "outline": outline}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    except Exception:
        pass

    pages_map: Dict[str, List[int]] = outline.get("pages_by_agent", {})
    results: Dict[str, Any] = {}
    qc_meta: Dict[str, Any] = {"_orchestrator": {"pages_by_agent": pages_map, "added_agents": (locals().get("added_agents") or [])}}

    # History logging (simple JSONL file)
    _hist_lock = threading.Lock()
    hist_path = os.getenv("COACH_HISTORY_PATH", "data/raw_pdfs/outputs/coach_history/coach_log.jsonl")
    try:
        os.makedirs(os.path.dirname(hist_path), exist_ok=True)
    except Exception:
        pass
    if verbose:
        print(f"[orchestrator] history -> {hist_path}")

    def _hash_str(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    def _append_history(entry: Dict[str, Any]):
        try:
            with _hist_lock:
                with open(hist_path, "a") as f:
                    f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    from .vision_qc import vision_qc_agent

    # 3) For each agent, loop up to max_rounds with coaching
    def _process_single(agent_id: str, base_prompt: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        full_prompt = f"{base_prompt}\n\n{schema_prompt_block(agent_id)}"
        cur_pages = pages_map.get(agent_id, [])
        # Seed empty page lists using text sectionizer first, then global pick
        if not cur_pages:
            try:
                cur_pages = select_pages_for_agent(pdf_path, agent_id) or []
            except Exception:
                cur_pages = []
            if not cur_pages:
                try:
                    cur_pages = _global_pick_pages_for_agent(pdf_path, agent_id) or []
                except Exception:
                    cur_pages = []
        best_json: Dict[str, Any] = {}
        best_score = -1.0
        meta_store: Dict[str, Any] = {}
        coach_accept = float(os.getenv("COACH_ACCEPT_SCORE", "85") or "85")
        phash = _hash_str(full_prompt)
        for round_idx in range(max_rounds):
            print(f"[orchestrator] {agent_id} round {round_idx+1}/{max_rounds} pages={cur_pages}")
            try:
                vis_json, vis_meta = vision_qc_agent(str(pdf_path), agent_id, full_prompt, page_indices=cur_pages)
            except Exception as e:
                vis_json, vis_meta = {}, {"error": str(e)}
            qc_first = numeric_qc(agent_id, vis_json)
            vis_meta["numeric_qc_first"] = qc_first
            enforced, verified, dropped = enforce(agent_id, vis_json)
            sc = score_output(agent_id, enforced)
            print(f"[orchestrator] {agent_id} round {round_idx+1} score={sc:.1f}")
            if sc > best_score:
                best_score = sc
                best_json = enforced
            meta_store.setdefault("rounds", []).append({
                "round": round_idx + 1,
                "pages": list(cur_pages),
                "score": sc,
                "numeric_qc": qc_first,
                "verified_fields": verified,
                "dropped_fields": dropped,
            })
            _append_history({
                "pdf": pdf_path,
                "agent": agent_id,
                "round": round_idx + 1,
                "pages": list(cur_pages),
                "score": sc,
                "prompt_hash": phash,
            })
            if sc >= _score_threshold(agent_id):
                break
            try:
                advice = _coach_agent_once(pdf_path, agent_id, cur_pages, enforced)
                cur_pages = advice.get("revised_pages", cur_pages) or cur_pages
                meta_store.setdefault("coaching", []).append({
                    "round": round_idx + 1,
                    "advice": advice,
                })
                # If coach signals OK and score is decent, accept early
                if advice.get("ok") and sc >= coach_accept:
                    if verbose:
                        print(f"[orchestrator] {agent_id} coach-ok accepted at round {round_idx+1} (score={sc:.1f})")
                    break
            except Exception as e:
                meta_store.setdefault("coaching_errors", []).append({"round": round_idx + 1, "error": str(e)})
                if cur_pages:
                    pad = 1
                    exp = []
                    for p in cur_pages:
                        exp.extend([p - pad, p, p + pad])
                    cur_pages = _distinct_ints(exp)[:6]
        if best_score < _score_threshold(agent_id):
            try:
                global_pages = _global_pick_pages_for_agent(pdf_path, agent_id)
                if global_pages:
                    print(f"[orchestrator] {agent_id} global page pick -> {global_pages}")
                    vis_json, vis_meta = vision_qc_agent(str(pdf_path), agent_id, full_prompt, page_indices=global_pages)
                    qc_first = numeric_qc(agent_id, vis_json)
                    enforced, verified, dropped = enforce(agent_id, vis_json)
                    sc = score_output(agent_id, enforced)
                    meta_store.setdefault("rounds", []).append({
                        "round": max_rounds + 1,
                        "pages": list(global_pages),
                        "score": sc,
                        "numeric_qc": qc_first,
                        "verified_fields": verified,
                        "dropped_fields": dropped,
                        "global_pick": True,
                    })
                    if sc > best_score:
                        best_score = sc
                        best_json = enforced
            except Exception as e:
                meta_store.setdefault("coaching_errors", []).append({"round": max_rounds + 1, "error": str(e)})
        return agent_id, best_json, meta_store

    # Concurrency control
    try:
        concurrency = int(os.getenv("ORCHESTRATOR_CONCURRENCY", "2") or "2")
    except Exception:
        concurrency = 2

    if concurrency <= 1 or len(agent_items) <= 1:
        for aid, prompt in agent_items:
            a, r, m = _process_single(aid, prompt)
            results[a] = r
            qc_meta[a] = m
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = {ex.submit(_process_single, aid, prompt): aid for aid, prompt in agent_items}
            for fut in as_completed(futs):
                try:
                    a, r, m = fut.result()
                    results[a] = r
                    qc_meta[a] = m
                except Exception as e:
                    a = futs[fut]
                    results[a] = {}
                    qc_meta[a] = {"error": str(e)}

    if qc_meta:
        results["_qc"] = qc_meta
    return results
