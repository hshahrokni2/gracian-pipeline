from __future__ import annotations

import os
import json
from typing import Dict, Any, List, Tuple

from .vision_sectionizer import render_all_pages
from .vision_qc import call_openai_responses_vision, json_guard, render_pdf_pages_subset
from .schema import get_types, schema_prompt_block
from .enforce import enforce
from .qc import numeric_qc
from .bench import score_output
from .sectionizer import sectionize_pdf


def _sample_pages(pdf_path: str, max_pages: int) -> Tuple[List[int], List[bytes]]:
    """Select up to max_pages spanning the document; return (indices, images)."""
    try:
        import fitz  # type: ignore
        doc = fitz.open(pdf_path)
        n = doc.page_count
        doc.close()
    except Exception:
        n = 0
    if n <= 0:
        return [], []
    if max_pages >= n:
        idxs = list(range(n))
    else:
        stride = max(1, n // max_pages)
        idxs = list(range(0, n, stride))[:max_pages]
    dpi = int(os.getenv("ONESHOT_DPI", "170") or "170")
    imgs = render_pdf_pages_subset(pdf_path, idxs, dpi=dpi)
    return idxs, imgs


def _build_schema_block(agent_ids: List[str]) -> str:
    schema: Dict[str, Dict[str, str]] = {}
    for a in agent_ids:
        schema[a] = get_types(a)
    return json.dumps(schema, ensure_ascii=False)


def oneshot_extract(pdf_path: str, agents: Dict[str, str]) -> Dict[str, Any]:
    """One-shot GPT-5 pass: sectionize + extract all agents in a single Responses vision call.
    Returns a dict shaped like per-agent results for compatibility, plus _qc and saves a sections file.
    """
    # Page selection: prefer fast text sectionizer union if enabled
    max_pages = int(os.getenv("ONESHOT_MAX_PAGES", "12") or "12")
    use_text_sec = os.getenv("ONESHOT_USE_TEXT_SECTIONIZER", "true").lower() == "true"
    if use_text_sec:
        sec = sectionize_pdf(pdf_path)
        union: List[int] = sorted({p for pages in sec.values() for p in pages})
        if union:
            idxs = union[:max_pages]
            images = render_pdf_pages_subset(pdf_path, idxs, dpi=int(os.getenv("ONESHOT_DPI", "170") or "170"))
        else:
            idxs, images = _sample_pages(pdf_path, max_pages)
    else:
        idxs, images = _sample_pages(pdf_path, max_pages)
    if not images:
        return {}
    labels = [f"Page {i+1}" for i in idxs]

    # Compose prompt
    agent_ids = list(agents.keys())
    schema_all = _build_schema_block(agent_ids)
    guidance = (
        "You are OneShot Orchestrator for a Swedish BRF report. Perform BOTH: (A) Sectionization and (B) Extraction.\n"
        "A) Sectionization: Detect level_1/2/3 with 1-based page ranges and propose pages_by_agent mapping using the provided images.\n"
        "B) Extraction: For EACH agent listed, produce JSON strictly following the schema types and include evidence_pages (1-based).\n"
        "Rules: Only use visible content. Never invent numbers or return 0 unless printed. Leave fields empty when not visible.\n"
        "Return STRICT minified JSON only: {sectionizer:{level_1:[], level_2:[], level_3:[], pages_by_agent:{}}, agents:{<agent_id>:{...}}}.\n"
        "Schema per agent (key:type): " + schema_all
    )

    raw = call_openai_responses_vision(guidance, images, page_labels=labels)
    out = json_guard(raw, default={"sectionizer": {}, "agents": {}})

    # Persist sectionizer map for audit
    try:
        from pathlib import Path
        outdir = Path("data")/"raw_pdfs"/"outputs"/"sections"
        outdir.mkdir(parents=True, exist_ok=True)
        with open(str(outdir/(Path(pdf_path).stem + ".oneshot.sections.json")), "w") as f:
            json.dump(out.get("sectionizer", {}), f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Flatten agents to top-level results; run enforcement + QC
    results: Dict[str, Any] = {}
    qc_meta: Dict[str, Any] = {"_oneshot": {"pages_sampled": idxs}}
    agents_out: Dict[str, Any] = out.get("agents", {}) if isinstance(out.get("agents", {}), dict) else {}
    for agent_id in agents.keys():
        data = agents_out.get(agent_id, {}) if isinstance(agents_out, dict) else {}
        qc_first = numeric_qc(agent_id, data)
        enforced, verified, dropped = enforce(agent_id, data)
        results[agent_id] = enforced
        qc_meta[agent_id] = {
            "score": score_output(agent_id, enforced),
            "numeric_qc": qc_first,
            "verified_fields": verified,
            "dropped_fields": dropped,
        }

    if qc_meta:
        results["_qc"] = qc_meta
    return results
