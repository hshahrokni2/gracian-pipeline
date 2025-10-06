from __future__ import annotations

import re
from typing import Dict, List, Tuple, Set


# Anchor keywords per agent (Swedish + common variants)
AGENT_ANCHORS: Dict[str, List[str]] = {
    "governance_agent": [
        "styrelse", "ordförande", "ledamot", "revisor", "valberedning",
        "förvaltningsberättelse",
    ],
    "financial_agent": [
        "resultaträkning", "balansräkning", "intäkter", "kostnader",
    ],
    "property_agent": [
        "fastighetsbeteckning", "fastighet", "adress", "lägenheter",
        "byggår", "energideklaration",
    ],
    "notes_depreciation_agent": [
        "avskrivning", "avskrivningar",
    ],
    "notes_maintenance_agent": [
        "underhåll", "underhållsplan",
    ],
    "notes_tax_agent": [
        "skatt", "inkomstskatt", "uppskjuten skatt",
    ],
    "events_agent": [
        "väsentliga händelser", "underhållsplan", "åtgärdsplan",
    ],
    "audit_agent": [
        "revisionsberättelse", "revisorernas berättelse",
    ],
    "loans_agent": [
        "lån ", "låne", "ränta", "amortering", "kredit", "skuld",
    ],
    "reserves_agent": [
        "fond", "avsättning", "yttre underhållsfond", "underhållsfond",
    ],
}


def _normalize_text(t: str) -> str:
    # Lowercase and collapse whitespace
    return re.sub(r"\s+", " ", t.lower()).strip()


def _scan_pages_for_anchors(pdf_path: str) -> Dict[int, Set[str]]:
    """Return mapping page_index -> matched agent_ids (by text anchors)."""
    import fitz  # PyMuPDF

    page_hits: Dict[int, Set[str]] = {}
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc):
            txt = _normalize_text(page.get_text("text") or "")
            hits: Set[str] = set()
            if not txt:
                continue
            for agent_id, anchors in AGENT_ANCHORS.items():
                for a in anchors:
                    if a in txt:
                        hits.add(agent_id)
                        break
            if hits:
                page_hits[i] = hits
    finally:
        doc.close()
    return page_hits


def _group_consecutive(pages: List[int]) -> List[Tuple[int, int]]:
    if not pages:
        return []
    pages = sorted(set(pages))
    ranges: List[Tuple[int, int]] = []
    start = pages[0]
    prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        ranges.append((start, prev))
        start = p
        prev = p
    ranges.append((start, prev))
    return ranges


def sectionize_pdf(pdf_path: str) -> Dict[str, List[int]]:
    """Best-effort sectionization using ToC if present, else anchor scan.
    Returns mapping agent_id -> list of page indices likely relevant.
    """
    pages_for_agent: Dict[str, Set[int]] = {k: set() for k in AGENT_ANCHORS}

    # 1) Try TOC/bookmarks first
    try:
        import fitz
        doc = fitz.open(pdf_path)
        toc = doc.get_toc(simple=True)  # list of (level, title, page)
        if toc:
            # Map toc titles to agents by anchor keywords
            for level, title, page1 in toc:
                t = _normalize_text(title)
                page_idx = max(0, (page1 or 1) - 1)
                for agent_id, anchors in AGENT_ANCHORS.items():
                    for a in anchors:
                        if a in t:
                            pages_for_agent[agent_id].add(page_idx)
                            break
        doc.close()
    except Exception:
        pass

    # 2) Anchor scan per page (adds to pages_for_agent)
    try:
        per_page = _scan_pages_for_anchors(pdf_path)
        for idx, agents in per_page.items():
            for agent_id in agents:
                pages_for_agent[agent_id].add(idx)
    except Exception:
        pass

    # 3) Expand a bit around hits (±1 page) to capture spreads
    try:
        import fitz
        doc = fitz.open(pdf_path)
        n = doc.page_count
        doc.close()
    except Exception:
        n = 0
    for agent_id, s in pages_for_agent.items():
        expanded: Set[int] = set()
        for p in s:
            expanded.add(p)
            if p - 1 >= 0:
                expanded.add(p - 1)
            if n and p + 1 < n:
                expanded.add(p + 1)
        pages_for_agent[agent_id] = expanded or s

    # Final: dedupe and sort
    return {k: sorted(v) for k, v in pages_for_agent.items() if v}


def select_pages_for_agent(pdf_path: str, agent_id: str) -> List[int]:
    """Helper to get page indices for a single agent."""
    mp = sectionize_pdf(pdf_path)
    return mp.get(agent_id, [])
