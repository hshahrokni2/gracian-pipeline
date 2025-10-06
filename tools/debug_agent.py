#!/usr/bin/env python3
"""
Debug a single specialized agent on a single PDF using exact pages.

- Picks pages from orchestrated sections if present, else vision sectionizer.
- Splits pages into chunks (<= N), calls GPT-5 Responses vision with page labels.
- Saves raw outputs + parsed/enforced JSON + per-chunk scores for inspection.
- Prints a concise, followable log to stdout.

Usage:
  python tools/debug_agent.py --pdf data/raw_pdfs/Hjorthagen/brf_46160.pdf --agent property_agent \
    --chunk-size 10 --dpi 200

Optional:
  --pages 1,2,3   (1-based explicit pages)
  --no-responses  (use Chat Completions vision fallback)
  --out-dir data/raw_pdfs/outputs/agent_debug

Requires OPENAI_API_KEY and the repo deps. Respects .env if present.
"""

from __future__ import annotations

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"gracian_pipeline"))

from prompts.agent_prompts import AGENT_PROMPTS
from core.schema import schema_prompt_block
from core.vision_qc import render_pdf_pages_subset, call_openai_responses_vision, call_openai_vision, json_guard
from core.qc import numeric_qc
from core.enforce import enforce
from core.bench import score_output
from core.vision_sectionizer import vision_sectionize


def load_orchestrated_pages(pdf_path: str, agent_id: str) -> List[int]:
    base = Path(pdf_path).stem
    sec_dir = Path("data")/"raw_pdfs"/"outputs"/"sections"
    # Prefer orchestrated; fall back to sections.json
    for name in (f"{base}.orchestrated.sections.json", f"{base}.sections.json", f"{base}.oneshot.sections.json"):
        p = sec_dir/name
        if p.exists():
            try:
                obj = json.loads(p.read_text())
                # handle different top-level shapes
                if "outline" in obj and isinstance(obj["outline"], dict):
                    return obj["outline"].get("pages_by_agent", {}).get(agent_id, [])
                if "pages_by_agent" in obj:
                    return obj.get("pages_by_agent", {}).get(agent_id, [])
            except Exception:
                pass
    return []


def parse_pages_arg(p: str) -> List[int]:
    parts = [x.strip() for x in p.split(",") if x.strip() != ""]
    idxs = []
    for x in parts:
        try:
            v = int(x)
            if v > 0:
                idxs.append(v-1)  # to 0-based
        except Exception:
            pass
    return sorted(set(idxs))


def chunk(seq: List[int], size: int) -> List[List[int]]:
    return [seq[i:i+size] for i in range(0, len(seq), size)]


def main() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Debug a single agent with exact pages")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--pages", default="", help="1-based comma-separated override pages")
    ap.add_argument("--chunk-size", type=int, default=int(os.getenv("DEBUG_CHUNK_SIZE", "10") or "10"))
    ap.add_argument("--dpi", type=int, default=int(os.getenv("DEBUG_DPI", "200") or "200"))
    ap.add_argument("--no-responses", action="store_true")
    ap.add_argument("--out-dir", default=str(Path("data")/"raw_pdfs"/"outputs"/"agent_debug"))
    ap.add_argument("--no-fallback", action="store_true", help="Do NOT call any sectionizer; require --pages or precomputed sections")
    args = ap.parse_args()

    pdf_path = args.pdf
    agent_id = args.agent
    out_dir = Path(args.out_dir)/Path(pdf_path).stem/agent_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve pages
    page_idxs: List[int] = []
    if args.pages:
        page_idxs = parse_pages_arg(args.pages)
    if not page_idxs:
        page_idxs = load_orchestrated_pages(pdf_path, agent_id)
    if not page_idxs:
        if args.no_fallback:
            print("[debug] No pages provided and no precomputed sections. Aborting (--no-fallback).")
            return
        print("[debug] No precomputed pages. Running vision sectionizer quickly to guess.")
        sec = vision_sectionize(pdf_path)
        page_idxs = sec.get("pages_by_agent", {}).get(agent_id, [])
    if not page_idxs:
        print("[debug] No pages found for this agent.")
        return

    prompt = AGENT_PROMPTS.get(agent_id, "Default prompt: Extract BRF data in JSON.")
    full_prompt = f"{prompt}\n\n{schema_prompt_block(agent_id)}"

    print(f"[debug] pdf={pdf_path}")
    print(f"[debug] agent={agent_id}")
    print(f"[debug] pages(0-based)={page_idxs}")
    print(f"[debug] chunk_size={args.chunk_size} dpi={args.dpi} responses={not args.no_responses}")

    chunks = chunk(page_idxs, max(1, args.chunk_size))
    best_score = -1.0
    best_json: Dict[str, Any] = {}
    summary: List[Dict[str, Any]] = []

    for ci, ch in enumerate(chunks, start=1):
        imgs = render_pdf_pages_subset(pdf_path, ch, dpi=args.dpi)
        labels = [f"Page {i+1}" for i in ch]
        if args.no_responses:
            raw = call_openai_vision(full_prompt, imgs, page_labels=labels)
        else:
            raw = call_openai_responses_vision(full_prompt, imgs, page_labels=labels)
        (out_dir/f"chunk_{ci}.raw.txt").write_text(raw)
        js = json_guard(raw, default={})
        (out_dir/f"chunk_{ci}.json").write_text(json.dumps(js, indent=2, ensure_ascii=False))
        qc = numeric_qc(agent_id, js)
        enforced, verified, dropped = enforce(agent_id, js)
        sc = score_output(agent_id, enforced)
        summary.append({
            "chunk": ci,
            "pages": ch,
            "score": sc,
            "numeric_qc": qc,
            "verified_fields": verified,
            "dropped_fields": dropped,
        })
        print(f"[debug] chunk {ci}/{len(chunks)} pages={ch} score={sc:.1f}")
        if sc > best_score:
            best_score = sc
            best_json = enforced

    (out_dir/"summary.json").write_text(json.dumps({
        "pdf": pdf_path,
        "agent": agent_id,
        "pages": page_idxs,
        "best_score": best_score,
        "best_json": best_json,
        "chunks": summary,
    }, indent=2, ensure_ascii=False))

    print("[debug] Done. Inspect:")
    print(f"  {out_dir}/summary.json")
    for ci in range(1, len(chunks)+1):
        print(f"  {out_dir}/chunk_{ci}.raw.txt  {out_dir}/chunk_{ci}.json")


if __name__ == "__main__":
    main()
