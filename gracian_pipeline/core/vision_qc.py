import base64
import io
import os
from typing import List, Dict, Any, Tuple
from .vertex import vertex_generate_vision
from openai import OpenAI
from .bench import score_output
import time


def _b64_png(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def render_pdf_pages(pdf_path: str, max_pages: int = 2, dpi: int = 200) -> List[bytes]:
    """Render first N pages of a PDF to PNG bytes using PyMuPDF (fitz)."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    images: List[bytes] = []
    try:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            # scale factor for DPI: 72 dpi base, so zoom = dpi/72
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def render_pdf_pages_subset(pdf_path: str, page_indices: List[int], dpi: int = 200) -> List[bytes]:
    """Render specific pages (0-based indices) to PNG bytes using PyMuPDF.
    Pages out of bounds are ignored.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    images: List[bytes] = []
    try:
        for idx in sorted(set(page_indices)):
            if idx < 0 or idx >= doc.page_count:
                continue
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            page = doc.load_page(idx)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def json_guard(text: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Attempt to coerce model output into JSON dict.
    - Strips code fences
    - Finds first {...} block
    - Falls back to default or {}
    """
    import json, re
    s = text.strip()
    # strip ``` blocks
    if s.startswith("```"):
        s = "\n".join([line for line in s.splitlines() if not line.strip().startswith("```")])
    # try direct
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # find first JSON object
    m = re.search(r"\{[\s\S]*\}", s)
    if m:
        frag = m.group(0)
        try:
            obj = json.loads(frag)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {} if default is None else default


def call_grok_vision(prompt: str, images_png: List[bytes]) -> str:
    """Call xAI Grok (OpenAI-compatible) with image(s) and prompt; return text content."""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    model = os.getenv("XAI_MODEL", "grok-4-fast-reasoning-latest")

    # Build message with embedded data URLs
    user_parts = [{"type": "text", "text": prompt}]
    for data in images_png:
        b64 = _b64_png(data)
        user_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            }
        )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You extract data from BRF tables. Return minified JSON only."},
            {"role": "user", "content": user_parts},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


def call_gemini_vision(prompt: str, images_png: List[bytes]) -> str:
    """Call Gemini 2.5 Pro via REST with inline images; return text content. Retries on transient errors."""
    import requests, time

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    parts = [{"text": prompt}]
    for data in images_png:
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/png",
                    "data": _b64_png(data),
                }
            }
        )

    payload = {"contents": [{"role": "user", "parts": parts}]}
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
    raise RuntimeError(f"Gemini vision call failed after retries: {last_err}")


def call_qwen_openrouter_vision(prompt: str, images_png: List[bytes]) -> str:
    """Call Qwen vision via OpenRouter (OpenAI-compatible chat)."""
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    model = os.getenv("OPENROUTER_QWEN_MODEL")
    if not model:
        # Demand explicit model slug to avoid mismatches
        raise RuntimeError("OPENROUTER_QWEN_MODEL not set (e.g., qwen/qwen-3-vl-235b-instruct)")

    user_parts = [{"type": "text", "text": prompt}]
    for data in images_png:
        b64 = _b64_png(data)
        user_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            }
        )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You extract data from BRF tables. Return minified JSON only."},
            {"role": "user", "content": user_parts},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


def has_signal(d: Dict[str, Any]) -> bool:
    """True if any non-empty value present."""
    for v in d.values():
        if isinstance(v, (list, dict)) and v:
            return True
        if isinstance(v, str) and v.strip():
            return True
        if isinstance(v, (int, float)):
            return True
    return False

def call_openai_vision(prompt: str, images_png: List[bytes], page_labels: List[str] | None = None) -> str:
    """Call OpenAI Chat Completions with vision (image_url parts). Retries on transient errors."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    user_parts = [{"type": "text", "text": prompt}]
    # Optionally interleave a short label before each image to help page referencing
    inject_labels = os.getenv("PASS_PAGE_LABELS", "true").lower() == "true"
    for idx, data in enumerate(images_png):
        if inject_labels:
            label = page_labels[idx] if page_labels and idx < len(page_labels) else f"Image {idx+1}/{len(images_png)}"
            user_parts.append({"type": "text", "text": label})
        b64 = _b64_png(data)
        user_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    last_err = None
    use_json_mode = os.getenv("OPENAI_JSON_MODE", "true").lower() == "true"
    for attempt in range(3):
        try:
            kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You extract BRF data. Return strict minified JSON only."},
                    {"role": "user", "content": user_parts},
                ],
                "max_completion_tokens": 1200,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OpenAI vision call failed after retries: {last_err}")


def call_openai_responses_vision(prompt: str, images_png: List[bytes], page_labels: List[str] | None = None) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-5")
    user_parts = [{"type": "input_text", "text": prompt}]
    # Optionally interleave a short label before each image to help page referencing
    inject_labels = os.getenv("PASS_PAGE_LABELS", "true").lower() == "true"
    for idx, data in enumerate(images_png):
        if inject_labels:
            label = page_labels[idx] if page_labels and idx < len(page_labels) else f"Image {idx+1}/{len(images_png)}"
            user_parts.append({"type": "input_text", "text": label})
        b64 = _b64_png(data)
        user_parts.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})
    last_err = None
    use_json_mode = os.getenv("OPENAI_JSON_MODE", "false").lower() == "true"
    try:
        max_out = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "3000") or "3000")
    except Exception:
        max_out = 3000
    for attempt in range(3):
        try:
            kwargs = {
                "model": model,
                "input": [{"role": "user", "content": user_parts}],
                "max_output_tokens": max_out,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.responses.create(**kwargs)
            if getattr(resp, "output_text", None):
                return resp.output_text
            try:
                return resp.choices[0].message.content[0].text  # type: ignore
            except Exception:
                return str(resp)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OpenAI Responses vision failed after retries: {last_err}")

def vision_qc_agent(pdf_path: str, agent_id: str, prompt: str, page_indices: List[int] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run Grok (+ optional Gemini, Qwen via OpenRouter) on first pages, JSON-guard, and pick a result.
    Returns (best_result, qc_meta)
    """
    try:
        max_pages = int(os.getenv("VISION_MAX_PAGES", "2"))
    except Exception:
        max_pages = 2
    dpi = int(os.getenv("QC_PAGE_RENDER_DPI", "220"))
    used_indices: List[int] | None = None
    if page_indices:
        exact = os.getenv("EXACT_PAGE_LIST", "true").lower() == "true"
        use = page_indices if exact else page_indices[:max_pages]
        used_indices = list(use)
        images = render_pdf_pages_subset(str(pdf_path), use, dpi=dpi)
    else:
        # default to first N pages (0-based indices 0..max_pages-1)
        used_indices = list(range(max_pages))
        images = render_pdf_pages(str(pdf_path), max_pages=max_pages, dpi=dpi)
    qc_meta: Dict[str, Any] = {"model": "multi", "grok_ok": False, "gemini_ok": False, "qwen_ok": False, "disagreement": False}

    # Encourage strict JSON
    final_prompt = (
        f"{prompt}\n\nYou are given images from the BRF report. "
        f"Extract ONLY the JSON specified above. Return STRICT minified JSON without comments or extra text."
    )

    grok_raw = ""
    gem_raw = ""
    grok = {}
    gem = {}

    # Gemini-only fast path (optionally via Vertex)
    if os.getenv("GEMINI_ONLY", "false").lower() == "true":
        try:
            use_vertex = os.getenv("GEMINI_VIA_VERTEX", "true").lower() == "true"
            if use_vertex and os.getenv("VERTEX_SA_JSON") and os.getenv("VERTEX_PROJECT"):
                sa = os.getenv("VERTEX_SA_JSON")
                project = os.getenv("VERTEX_PROJECT")
                location = os.getenv("VERTEX_LOCATION", "us-central1")
                model = os.getenv("VERTEX_MODEL", "gemini-1.5-pro-001")
                txt = vertex_generate_vision(sa, project, location, model, final_prompt, images)
            else:
                txt = call_gemini_vision(final_prompt, images)
            gem = json_guard(txt)
            qc_meta["gemini_ok"] = has_signal(gem)
            qc_meta["gemini_out"] = gem
            return gem, qc_meta
        except Exception as e:
            qc_meta["gemini_error"] = str(e)
            return {}, qc_meta

    # OpenAI-only fast path (supports chunking large page lists)
    if os.getenv("OPENAI_ONLY", "false").lower() == "true":
        try:
            # If we have many pages, split into chunks and choose best-scoring chunk
            chunk_size = int(os.getenv("VISION_PAGES_PER_CALL", "10") or "10")
            verbose = os.getenv("VERBOSE_VISION", "false").lower() == "true"
            if used_indices is not None and len(used_indices) > chunk_size:
                try:
                    import fitz  # type: ignore
                    doc = fitz.open(str(pdf_path))
                    total = max(doc.page_count, 1)
                    doc.close()
                except Exception:
                    total = None
                chunks: List[List[int]] = [used_indices[i:i+chunk_size] for i in range(0, len(used_indices), chunk_size)]
                best_js: Dict[str, Any] = {}
                best_score = -1.0
                chunk_meta: List[Dict[str, Any]] = []
                use_responses = os.getenv("OPENAI_RESPONSES", "true").lower() == "true"
                for ch in chunks:
                    imgs = render_pdf_pages_subset(str(pdf_path), ch, dpi=dpi)
                    page_labels: List[str] | None = None
                    if os.getenv("PASS_PAGE_LABELS", "true").lower() == "true":
                        page_labels = [(f"Page {i+1}/{total}" if total else f"Page {i+1}") for i in ch]
                    if verbose:
                        print(f"[vision] {agent_id}: chunk {len(ch)} pages -> {ch}")
                    if use_responses:
                        txt = call_openai_responses_vision(final_prompt, imgs, page_labels)
                    else:
                        txt = call_openai_vision(final_prompt, imgs, page_labels)
                    js = json_guard(txt)
                    sc = score_output(agent_id, js)
                    chunk_meta.append({"pages": ch, "score": sc})
                    if sc > best_score:
                        best_score = sc
                        best_js = js
                qc_meta["openai_ok"] = has_signal(best_js)
                qc_meta["openai_out"] = best_js
                qc_meta["openai_chunks"] = chunk_meta
                return best_js, qc_meta
            else:
                # Single call path (few pages)
                if os.getenv("OPENAI_RESPONSES", "true").lower() == "true":
                    # Build optional page labels for better evidence referencing
                    page_labels: List[str] | None = None
                    if os.getenv("PASS_PAGE_LABELS", "true").lower() == "true":
                        try:
                            import fitz  # type: ignore
                            doc = fitz.open(str(pdf_path))
                            total = max(doc.page_count, 1)
                            doc.close()
                        except Exception:
                            total = None
                        if used_indices is not None:
                            page_labels = [
                                (f"Page {i+1}/{total}" if total else f"Page {i+1}") for i in used_indices[:len(images)]
                            ]
                    txt = call_openai_responses_vision(final_prompt, images, page_labels)
                else:
                    page_labels: List[str] | None = None
                    if os.getenv("PASS_PAGE_LABELS", "true").lower() == "true":
                        try:
                            import fitz  # type: ignore
                            doc = fitz.open(str(pdf_path))
                            total = max(doc.page_count, 1)
                            doc.close()
                        except Exception:
                            total = None
                        if used_indices is not None:
                            page_labels = [
                                (f"Page {i+1}/{total}" if total else f"Page {i+1}") for i in used_indices[:len(images)]
                            ]
                    txt = call_openai_vision(final_prompt, images, page_labels)
                js = json_guard(txt)
                qc_meta["openai_ok"] = has_signal(js)
                qc_meta["openai_out"] = js
                return js, qc_meta
        except Exception as e:
            qc_meta["openai_error"] = str(e)
            return {}, qc_meta

    # Grok first
    try:
        grok_raw = call_grok_vision(final_prompt, images)
        grok = json_guard(grok_raw)
        qc_meta["grok_ok"] = has_signal(grok)
        qc_meta["grok_out"] = grok
    except Exception as e:
        qc_meta["grok_error"] = str(e)

    # Optionally Gemini (default enabled)
    use_gemini = os.getenv("DUAL_VISION_QC", "true").lower() == "true"
    use_qwen = os.getenv("QWEN_VISION_QC", "true").lower() == "true" and bool(os.getenv("OPENROUTER_API_KEY"))
    if use_gemini:
        try:
            gem_raw = call_gemini_vision(final_prompt, images)
            gem = json_guard(gem_raw)
            qc_meta["gemini_ok"] = has_signal(gem)
            qc_meta["gemini_out"] = gem
        except Exception as e:
            qc_meta["gemini_error"] = str(e)

    # Qwen via OpenRouter
    qwen_raw = ""
    qwen = {}
    if use_qwen:
        try:
            qwen_raw = call_qwen_openrouter_vision(final_prompt, images)
            qwen = json_guard(qwen_raw)
            qc_meta["qwen_ok"] = has_signal(qwen)
            qc_meta["qwen_out"] = qwen
        except Exception as e:
            qc_meta["qwen_error"] = str(e)

    # Select winner: prefer Grok; else Gemini; else Qwen; else empty
    best = (
        grok if has_signal(grok) else (
            gem if has_signal(gem) else (
                qwen if has_signal(qwen) else {}
            )
        )
    )

    # Basic disagreement flag if both have signal but differ
    # Disagreement if any two with signal differ
    candidates = [("grok", grok, grok_raw), ("gemini", gem, gem_raw)]
    if use_qwen:
        candidates.append(("qwen", qwen, qwen_raw))
    with_signal = [(n, d, r) for n, d, r in candidates if has_signal(d)]
    if len(with_signal) >= 2:
        for i in range(len(with_signal)):
            for j in range(i + 1, len(with_signal)):
                if with_signal[i][1] != with_signal[j][1]:
                    qc_meta["disagreement"] = True
                    qc_meta[with_signal[i][0] + "_raw"] = (with_signal[i][2] or "")[:500]
                    qc_meta[with_signal[j][0] + "_raw"] = (with_signal[j][2] or "")[:500]
                    break

    return best, qc_meta
