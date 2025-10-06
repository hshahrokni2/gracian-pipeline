import os
import json
import time
from typing import List, Dict, Any, Tuple

from .vision_qc import _b64_png  # reuse encoding helper


def render_all_pages(pdf_path: str, dpi: int = 170) -> List[bytes]:
    import fitz
    doc = fitz.open(pdf_path)
    images: List[bytes] = []
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def _call_openai_compatible_vision(base_url: str, api_key: str, model: str, prompt: str, images: List[bytes]) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for data in images:
        parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64_png(data)}"}})
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise BRF sectionizer. Return strict minified JSON only."},
            {"role": "user", "content": parts},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


def _json_guard(text: str, default: Any) -> Any:
    try:
        return json.loads(text)
    except Exception:
        # attempt to extract first JSON object/array
        import re
        s = text.strip()
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return default
        return default


ROUND1_PROMPT = (
    "Task: From these BRF report page images, detect ALL top-level (level 1) sections that are actually visible. "
    "Use Swedish headings and layout cues. Typical L1: Förvaltningsberättelse, Resultaträkning, Balansräkning, Kassaflödesanalys, Noter/Tilläggsupplysningar, Revisionsberättelse, Underskrifter, Stadgar. "
    "Requirements: (1) Use 1-based GLOBAL page numbers from the provided listing, (2) Do NOT invent titles or pages, (3) If a section spans multiple pages, set start_page and end_page accordingly, (4) If uncertain, omit. "
    "Return strict minified JSON only: {level_1:[{title,start_page,end_page}]}."
)


ROUND2_PROMPT = (
    "Task: For the given L1 section pages, identify visible level 2 and 3 subheadings with exact page ranges. "
    "Examples: Under Noter: 'Not 1 Lån', 'Not 2 Avskrivningar', etc.; under Förvaltningsberättelse: governance/property subheads. "
    "Requirements: (1) Use 1-based GLOBAL page numbers, (2) Derive ranges only from visible headings, (3) Do NOT infer or guess, (4) If none, return empty arrays. "
    "Return strict minified JSON only: {level_2:[{parent,title,start_page,end_page}], level_3:[{parent,title,start_page,end_page}]}."
)


def _batch_indices(n: int, size: int) -> List[Tuple[int, int]]:
    i = 0
    out = []
    while i < n:
        j = min(n, i + size)
        out.append((i, j))
        i = j
    return out


def _choose_sectionizer_provider() -> Tuple[str, str, str]:
    # returns (base_url, api_key, model)
    provider = os.getenv("SECTIONIZER_PROVIDER", "openrouter").lower()
    if provider == "xai":
        return (
            "https://api.x.ai/v1",
            os.getenv("XAI_API_KEY", ""),
            os.getenv("SECTIONIZER_MODEL_XAI", os.getenv("XAI_MODEL", "grok-4-fast-reasoning-latest")),
        )
    # default openrouter
    return (
        "https://openrouter.ai/api/v1",
        os.getenv("OPENROUTER_API_KEY", ""),
        os.getenv("SECTIONIZER_MODEL_OPENROUTER", os.getenv("OPENROUTER_QWEN_MODEL", "qwen/qwen3-vl-235b-a22b-instruct")),
    )


def vision_sectionize(pdf_path: str) -> Dict[str, Any]:
    """Two-round vision sectionizer. Returns a dict with level_1, level_2, level_3 and pages_by_agent."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        doc.close()
    except Exception:
        page_count = 0

    base_url, api_key, model = _choose_sectionizer_provider()
    if not api_key:
        raise RuntimeError("Sectionizer API key missing")

    # Round 1: identify level 1 sections
    batch_size = int(os.getenv("SECTIONIZER_PAGES_PER_CALL", "8"))
    dpi = int(os.getenv("SECTIONIZER_DPI", "170"))
    level_1_items: List[Dict[str, Any]] = []
    pace_ms = int(os.getenv("SECTIONIZER_PACE_MS", "300") or "300")
    verbose = os.getenv("VERBOSE_SECTIONIZER", "false").lower() == "true"
    for start, end in _batch_indices(page_count, batch_size):
        # render this slice
        import fitz
        doc = fitz.open(pdf_path)
        imgs: List[bytes] = []
        try:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for i in range(start, end):
                pix = doc.load_page(i).get_pixmap(matrix=mat, alpha=False)
                imgs.append(pix.tobytes("png"))
        finally:
            doc.close()
        listing = "; ".join([f"page {i+1}" for i in range(start, end)])
        prompt = (
            ROUND1_PROMPT
            + f"\nGlobal page listing for the images in order: {listing}. \nReturn only JSON."
        )
        if verbose:
            print(f"[sectionizer] round1 batch pages {start+1}-{end}")
        # retry with backoff to survive rate limits (429)
        txt = ""
        last_err = None
        for attempt in range(5):
            try:
                txt = _call_openai_compatible_vision(base_url, api_key, model, prompt, imgs)
                break
            except Exception as e:
                last_err = e
                # backoff 0.8s, 1.6s, 2.4s, ...
                time.sleep(0.8 * (attempt + 1))
        if not txt and last_err:
            # skip this batch but continue others
            continue
        out = _json_guard(txt, {"level_1": []})
        items = out.get("level_1", []) if isinstance(out, dict) else []
        # keep only items within [start+1, end]
        for it in items:
            try:
                sp, ep = int(it.get("start_page", 0)), int(it.get("end_page", 0))
                title = str(it.get("title", "")).strip()
                if title and (start + 1) <= sp <= page_count and (start + 1) <= ep <= page_count:
                    level_1_items.append({"title": title, "start_page": sp, "end_page": ep})
            except Exception:
                continue

    # Merge overlapping/adjacent level 1 items with same normalized title
    def norm_title(t: str) -> str:
        return " ".join(t.lower().split())
    merged: Dict[str, List[Tuple[int, int]]] = {}
    for it in level_1_items:
        t = norm_title(it["title"])
        merged.setdefault(t, []).append((it["start_page"], it["end_page"]))
    level_1: List[Dict[str, Any]] = []
    for t, ranges in merged.items():
        ranges.sort()
        cur_s, cur_e = ranges[0]
        for s, e in ranges[1:]:
            if s <= cur_e + 1:
                cur_e = max(cur_e, e)
            else:
                level_1.append({"title": t, "start_page": cur_s, "end_page": cur_e})
                cur_s, cur_e = s, e
        level_1.append({"title": t, "start_page": cur_s, "end_page": cur_e})

    # Round 2: for each L1 region, detect level 2/3
    level_2: List[Dict[str, Any]] = []
    level_3: List[Dict[str, Any]] = []
    for sec in level_1:
        sp, ep = sec["start_page"], sec["end_page"]
        if ep < sp:
            continue
        # render this range
        import fitz
        doc = fitz.open(pdf_path)
        imgs: List[bytes] = []
        try:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for i in range(sp - 1, ep):
                pix = doc.load_page(i).get_pixmap(matrix=mat, alpha=False)
                imgs.append(pix.tobytes("png"))
        finally:
            doc.close()
        listing = "; ".join([f"page {i}" for i in range(sp, ep + 1)])
        prompt = (
            ROUND2_PROMPT
            + f"\nLevel 1 section: {sec['title']} ({sp}–{ep}). Global pages in order: {listing}. Return only JSON."
        )
        if verbose:
            print(f"[sectionizer] round2 L1 '{sec['title']}' {sp}-{ep} ({len(imgs)} pages)")
        txt = ""
        last_err = None
        for attempt in range(5):
            try:
                txt = _call_openai_compatible_vision(base_url, api_key, model, prompt, imgs)
                break
            except Exception as e:
                last_err = e
                time.sleep(0.8 * (attempt + 1))
        if not txt and last_err:
            continue
        out = _json_guard(txt, {"level_2": [], "level_3": []})
        for lv, store in ("level_2", level_2), ("level_3", level_3):
            items = out.get(lv, []) if isinstance(out, dict) else []
            for it in items:
                try:
                    title = str(it.get("title", "")).strip()
                    p = str(it.get("parent", sec["title"]))
                    s, e = int(it.get("start_page", sp)), int(it.get("end_page", sp))
                    if title:
                        store.append({"parent": p, "title": title, "start_page": s, "end_page": e})
                except Exception:
                    continue

    # Heuristic mapping to agents → pages
    pages_by_agent: Dict[str, List[int]] = {}
    def add_pages(agent: str, s: int, e: int):
        pages_by_agent.setdefault(agent, [])
        for i in range(s - 1, e):
            if i not in pages_by_agent[agent]:
                pages_by_agent[agent].append(i)

    def contains(t: str, needles: List[str]) -> bool:
        t2 = t.lower()
        return any(n in t2 for n in needles)

    for sec in level_1:
        t = sec["title"]
        if contains(t, ["resultaträkning", "balansräkning", "kassaflöde"]):
            add_pages("financial_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["kassaflöde", "kassaflödesanalys"]):
            add_pages("cashflow_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["revisionsberättelse", "revisorernas"]):
            add_pages("audit_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["underskrifter", "undertecknat"]):
            add_pages("signatures_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["not", "tilläggsupplysningar"]):
            # generic notes span; specific detection follows below
            add_pages("notes_depreciation_agent", sec["start_page"], sec["end_page"])
            add_pages("notes_maintenance_agent", sec["start_page"], sec["end_page"])
            add_pages("notes_tax_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["förvaltningsberättelse"]):
            add_pages("governance_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["fastighet", "lägenheter", "byggår"]):
            add_pages("property_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["energideklaration", "energiklass", "energieffektiv", "primärenergi"]):
            add_pages("energy_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["fond", "avsättning", "underhållsfond"]):
            add_pages("reserves_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["lån", "kredit"]):
            add_pages("loans_agent", sec["start_page"], sec["end_page"])
        if contains(t, ["avgift", "avgifter", "årsavgift", "månadsavgift"]):
            add_pages("fees_agent", sec["start_page"], sec["end_page"])

    # Also use level 2/3 titles to add more precise pages
    for it in level_2 + level_3:
        t = it["title"]
        s, e = it["start_page"], it["end_page"]
        if contains(t, ["lån", "ränta", "amortering"]):
            add_pages("loans_agent", s, e)
        if contains(t, ["fond", "avsättning"]):
            add_pages("reserves_agent", s, e)
        if contains(t, ["avskrivning"]):
            add_pages("notes_depreciation_agent", s, e)
        if contains(t, ["underhåll"]):
            add_pages("notes_maintenance_agent", s, e)
        if contains(t, ["skatt", "uppskjuten"]):
            add_pages("notes_tax_agent", s, e)
        if contains(t, ["energideklaration", "energiklass", "energieffektiv", "primärenergi"]):
            add_pages("energy_agent", s, e)
        if contains(t, ["avgift", "avgifter", "årsavgift", "månadsavgift"]):
            add_pages("fees_agent", s, e)
        if contains(t, ["kassaflöde", "kassaflödesanalys"]):
            add_pages("cashflow_agent", s, e)

    for a in list(pages_by_agent.keys()):
        pages_by_agent[a] = sorted(pages_by_agent[a])

    return {
        "level_1": level_1,
        "level_2": level_2,
        "level_3": level_3,
        "pages_by_agent": pages_by_agent,
    }
