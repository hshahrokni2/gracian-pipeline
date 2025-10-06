#!/usr/bin/env python3
"""
Gracian Pipeline CLI - Grok-Centric BRF Extraction
"""

import argparse
import os
import sys
import glob
import json
import time
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, 'gracian_pipeline')

from prompts.agent_prompts import AGENT_PROMPTS
from core.schema import schema_prompt_block, get_types
from core.vision_qc import vision_qc_agent, json_guard, render_pdf_pages_subset, call_qwen_openrouter_vision
from core.sectionizer import sectionize_pdf, select_pages_for_agent
from core.vision_sectionizer import vision_sectionize
from core.enforce import enforce
from core.qc import numeric_qc
from core.bench import score_output, call_gemini_text, call_qwen_openrouter_text, jury_rank, call_openai_text
from core.oneshot import oneshot_extract
from core.orchestrator import orchestrate_pdf

# Best-effort: load .env if present (non-fatal if missing)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def call_grok(prompt, content):
    """Call Grok API with prompt and content"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1"
    )
    # Use OpenAI-compatible Chat Completions against xAI Grok endpoint
    model = os.getenv("XAI_MODEL", "grok-4-fast-reasoning-latest")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def extract_pdf_text(pdf_path):
    """Extract text from entire document using PyMuPDF; fallback to pdfplumber."""
    try:
        import fitz  # PyMuPDF
        text_parts = []
        doc = fitz.open(str(pdf_path))
        try:
            for i, page in enumerate(doc):
                text_parts.append(page.get_text("text"))
        finally:
            doc.close()
        if text_parts:
            return "\n\n".join(text_parts)
    except Exception:
        pass
    # Fallback: pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text_parts.append(page.extract_text() or "")
        if text_parts:
            return "\n\n".join(text_parts)
    except Exception:
        pass
    return f""

TABLE_AGENTS = {"financial_agent", "loans_agent", "reserves_agent", "cashflow_agent"}


def process_pdf(pdf_path, agents):
    """Process a single PDF with all agents"""
    # Auto-switch to vision-only if low text layer and flag enabled
    auto_vision = os.getenv("AUTO_VISION_IF_LOW_TEXT", "true").lower() == "true"
    use_vision_sectionizer = os.getenv("VISION_SECTIONIZER", "true").lower() == "true"
    if auto_vision:
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            low = 0
            total = max(doc.page_count, 1)
            for p in doc:
                txt = p.get_text("text") or ""
                if len(txt) < 500:
                    low += 1
            doc.close()
            if (low / total) >= 0.6:
                print(f"[auto-vision] Low text detected ({low}/{total} low pages). Using vision-only for {pdf_path}.")
                vis_results = {}
                vis_meta = {}
                # Use vision sectionizer to pick pages per agent
                vis_sec = vision_sectionize(str(pdf_path)) if use_vision_sectionizer else {"pages_by_agent": {}}
                pages_map = vis_sec.get("pages_by_agent", {})
                # Persist section map for auditability
                try:
                    import json as _json
                    import os as _os
                    sec_out_dir = str((Path("data") / "raw_pdfs" / "outputs" / "sections").resolve())
                    _os.makedirs(sec_out_dir, exist_ok=True)
                    base = Path(str(pdf_path)).stem + ".sections.json"
                    with open(str(Path(sec_out_dir) / base), "w") as f:
                        _json.dump(vis_sec, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                # pacing between vision calls
                try:
                    pace_ms = int(os.getenv("GEMINI_PACING_MS", "400"))
                except Exception:
                    pace_ms = 400
                for agent_id, prompt in agents.items():
                    full_prompt = f"{prompt}\n\n{schema_prompt_block(agent_id)}"
                    agent_pages = pages_map.get(agent_id) or select_pages_for_agent(str(pdf_path), agent_id)
                    print(f"  [vision] {agent_id} -> images")
                    try:
                        if pace_ms > 0:
                            time.sleep(pace_ms / 1000.0)
                        # First pass
                        best, meta = vision_qc_agent(str(pdf_path), agent_id, full_prompt, page_indices=agent_pages)
                        qcnum1 = numeric_qc(agent_id, best)
                        meta["numeric_qc_first"] = qcnum1

                        # Numeric second pass if needed (tables often need more pages)
                        need_second = agent_id in TABLE_AGENTS and not qcnum1.get("passed", False)
                        if need_second:
                            try:
                                # Expand candidate pages within section by ±2 and cap to 6
                                expanded = []
                                if agent_pages:
                                    for p in agent_pages:
                                        expanded.extend([p-2, p-1, p, p+1, p+2])
                                    expanded = sorted({i for i in expanded if i >= 0})[:6]
                                else:
                                    # Fallback: first, middle, last
                                    import fitz
                                    doc = fitz.open(str(pdf_path))
                                    n = doc.page_count
                                    doc.close()
                                    mids = [n//2-1, n//2, max(0, n-1)]
                                    expanded = sorted({0,1,*mids})
                                prev = os.environ.get("VISION_MAX_PAGES")
                                os.environ["VISION_MAX_PAGES"] = str(max(3, len(expanded)))
                                try:
                                    best2, meta2 = vision_qc_agent(str(pdf_path), agent_id, full_prompt, page_indices=expanded)
                                finally:
                                    if prev is not None:
                                        os.environ["VISION_MAX_PAGES"] = prev
                                    else:
                                        del os.environ["VISION_MAX_PAGES"]
                                qcnum2 = numeric_qc(agent_id, best2)
                                meta["numeric_qc_second"] = qcnum2
                                from core.bench import score_output as _score
                                s1 = _score(agent_id, best)
                                s2 = _score(agent_id, best2)
                                # Prefer second if QC passes or score improves
                                if qcnum2.get("passed", False) or s2 > s1:
                                    meta["second_pass_used"] = True
                                    meta["second_pass_pages"] = expanded
                                    best = best2
                                else:
                                    meta["second_pass_used"] = False
                            except Exception as _e:
                                meta["second_pass_error"] = str(_e)

                        # collect schema_extension from vision result
                        try:
                            if isinstance(best, dict) and best.get("schema_extension"):
                                import os as _os
                                from pathlib import Path as _Path
                                outdir = _Path("data")/"raw_pdfs"/"outputs"/"schema_proposals"
                                _os.makedirs(str(outdir), exist_ok=True)
                                fname = f"{_Path(str(pdf_path)).stem}__{agent_id}.schema_proposal.json"
                                with open(str(outdir/fname), "w") as f:
                                    json.dump({"agent": agent_id, "pdf": str(pdf_path), "schema_extension": best["schema_extension"]}, f, indent=2, ensure_ascii=False)
                        except Exception:
                            pass

                        # enforcement
                        best_enforced, verified, dropped = enforce(agent_id, best)
                        if verified:
                            meta["verified_fields"] = verified
                        if dropped:
                            meta["dropped_fields"] = dropped
                        vis_results[agent_id] = best_enforced
                        vis_meta[agent_id] = meta
                    except Exception as e:
                        print(f"  [vision] error {agent_id}: {e}")
                        vis_results[agent_id] = {}
                if vis_meta:
                    vis_results["_qc"] = vis_meta
                return vis_results
        except Exception:
            pass
    # Sectionize to focus each agent on relevant pages
    section_map = sectionize_pdf(str(pdf_path))
    text = extract_pdf_text(pdf_path)
    results = {}
    
    qc_meta = {}
    bench_meta = {}
    run_bench = os.getenv("BENCHMARK_MODE", "true").lower() == "true"
    text_qwen_enabled = os.getenv("TEXT_QWEN_ENABLED", "false").lower() == "true"
    table_qwen_verify = os.getenv("TABLE_QWEN_VERIFY", "true").lower() == "true"
    table_vision_qc = os.getenv("TABLE_VISION_QC", "false").lower() == "true"
    agent_items = list(agents.items())
    try:
        max_agents = int(os.getenv("BENCHMARK_MAX_AGENTS", "0"))
    except Exception:
        max_agents = 0
    if max_agents > 0:
        agent_items = agent_items[:max_agents]

    for agent_id, prompt in agent_items:
        print(f"Calling {agent_id} for {pdf_path}")
        try:
            # Build prompt with schema constraints and extension guidance
            full_prompt = f"{prompt}\n\n{schema_prompt_block(agent_id)}"
            # Gemini-only: produce Gemini baseline (clip text to section pages if available)
            agent_pages = section_map.get(agent_id, [])
            if agent_pages:
                try:
                    import fitz
                    doc = fitz.open(str(pdf_path))
                    parts = []
                    for i in agent_pages:
                        if 0 <= i < doc.page_count:
                            parts.append(doc.load_page(i).get_text("text") or "")
                    doc.close()
                    clipped_text = "\n\n".join(parts) or text
                except Exception:
                    clipped_text = text
            else:
                clipped_text = text

            # If GEMINI_ONLY=true, skip Grok/Qwen and use Gemini text only
            if os.getenv("GEMINI_ONLY", "true").lower() == "true":
                try:
                    gem_txt = call_gemini_text(full_prompt, clipped_text)
                    gem_json = json_guard(gem_txt, default={})
                except Exception as e:
                    gem_json = {}
                selected = gem_json
                # enforcement + QC
                qcnum = numeric_qc(agent_id, selected)
                selected_enforced, verified, dropped = enforce(agent_id, selected)
                results[agent_id] = selected_enforced
                if verified or dropped:
                    bench_meta.setdefault(agent_id, {})["verified_fields"] = verified
                    if dropped:
                        bench_meta[agent_id]["dropped_fields"] = dropped
                if qcnum:
                    bench_meta.setdefault(agent_id, {})["numeric_qc"] = qcnum
                continue

            # OpenAI-only path for text
            if os.getenv("OPENAI_ONLY", "false").lower() == "true":
                try:
                    # pacing
                    try:
                        pace_ms = int(os.getenv("OPENAI_PACING_MS", "1500"))
                    except Exception:
                        pace_ms = 1500
                    if pace_ms > 0:
                        time.sleep(pace_ms / 1000.0)
                    oa_txt = call_openai_text(full_prompt, clipped_text)
                    oa_json = json_guard(oa_txt, default={})
                except Exception as e:
                    oa_json = {}
                selected = oa_json
                qcnum = numeric_qc(agent_id, selected)
                selected_enforced, verified, dropped = enforce(agent_id, selected)
                results[agent_id] = selected_enforced
                if verified or dropped:
                    bench_meta.setdefault(agent_id, {})["verified_fields"] = verified
                    if dropped:
                        bench_meta[agent_id]["dropped_fields"] = dropped
                if qcnum:
                    bench_meta.setdefault(agent_id, {})["numeric_qc"] = qcnum
                continue

            grok_txt = call_grok(full_prompt, clipped_text)
            grok_json = json_guard(grok_txt, default={})

            if run_bench:
                # Compete Gemini + Qwen
                try:
                    gem_txt = call_gemini_text(prompt, clipped_text)
                    gem_json = json_guard(gem_txt, default={})
                except Exception as e:
                    gem_txt, gem_json = str(e), {}
                if text_qwen_enabled:
                    try:
                        qwen_txt = call_qwen_openrouter_text(prompt, clipped_text)
                        qwen_json = json_guard(qwen_txt, default={})
                    except Exception as e:
                        qwen_txt, qwen_json = str(e), {}
                else:
                    qwen_json = {}

                # Heuristic scoring
                scores = {
                    "grok": score_output(agent_id, grok_json),
                    "gemini": score_output(agent_id, gem_json),
                    "qwen": score_output(agent_id, qwen_json),
                }
                # Jury pick
                jury = {}
                try:
                    jury = jury_rank(agent_id, prompt, text[:12000], {
                        "grok": json.dumps(grok_json, ensure_ascii=False),
                        "gemini": json.dumps(gem_json, ensure_ascii=False),
                        "qwen": json.dumps(qwen_json, ensure_ascii=False) if qwen_json else "{}",
                    })
                except Exception as e:
                    jury = {"best": max(scores, key=scores.get), "reasons": ["jury_error: " + str(e)]}

                # Select best: prefer jury, else heuristic
                best_label = jury.get("best") if jury.get("best") in ("grok", "gemini", "qwen") else max(scores, key=scores.get)
                selected = {"grok": grok_json, "gemini": gem_json, "qwen": qwen_json}.get(best_label, grok_json)
                # enforcement
                qcnum = numeric_qc(agent_id, selected)
                selected_enforced, verified, dropped = enforce(agent_id, selected)
                results[agent_id] = selected_enforced
                if verified or dropped:
                    bench_meta.setdefault(agent_id, {})["verified_fields"] = verified
                    if dropped:
                        bench_meta[agent_id]["dropped_fields"] = dropped
                if qcnum:
                    bench_meta.setdefault(agent_id, {})["numeric_qc"] = qcnum
                bench_meta[agent_id] = {"scores": scores, "jury": jury, "chosen": best_label}
            else:
                results[agent_id] = grok_json

            # Optional legacy table vision QC (first pages only)
            if agent_id in TABLE_AGENTS and table_vision_qc:
                best, meta = vision_qc_agent(str(pdf_path), agent_id, prompt)
                qc_meta[agent_id] = meta

            # For table agents: Qwen vision verification on selected pages if suspicion (no OCR, no region detection)
            if agent_id in TABLE_AGENTS and table_qwen_verify and not table_vision_qc:
                def _num_ok(x: object) -> bool:
                    if isinstance(x, (int, float)):
                        return x != 0
                    if isinstance(x, str):
                        xs = x.replace("\u00a0", " ").replace(" ", "").replace("%", "").replace(",", ".")
                        import re
                        xs = re.sub(r"[^0-9.\-]", "", xs)
                        try:
                            return float(xs) != 0.0
                        except Exception:
                            return False
                    return False

                sel = results.get(agent_id, {})
                suspect = False
                if agent_id == "financial_agent":
                    keys = ["revenue", "expenses", "assets", "liabilities", "equity"]
                    nonempty = sum(1 for k in keys if k in sel and str(sel.get(k, "")).strip() != "")
                    nonzero = sum(1 for k in keys if _num_ok(sel.get(k)))
                    suspect = nonempty == 0 or nonzero == 0
                elif agent_id == "loans_agent":
                    suspect = not _num_ok(sel.get("outstanding_loans"))
                elif agent_id == "reserves_agent":
                    suspect = not _num_ok(sel.get("reserve_fund"))

                if suspect:
                    print(f"  [verify] Qwen vision on candidate pages for {agent_id}")
                    try:
                        import fitz
                        doc = fitz.open(str(pdf_path))
                        page_idxs = []
                        terms = [
                            "resultaträkning", "balansräkning", "not", "lån", "fond", "tillgångar", "skulder", "eget kapital",
                        ]
                        for i, page in enumerate(doc):
                            txt = page.get_text("text").lower()
                            if any(t in txt for t in terms):
                                page_idxs.append(i)
                        doc.close()
                    except Exception:
                        page_idxs = list(range(0, 3))
                    if not page_idxs:
                        page_idxs = list(range(0, 3))
                    imgs = render_pdf_pages_subset(str(pdf_path), page_idxs[:3], dpi=int(os.getenv("QC_PAGE_RENDER_DPI", "220")))
                    try:
                        verify_prompt = (
                            f"{prompt}\n\nCross-check numeric fields from these page images. "
                            f"Return STRICT minified JSON with the same keys only."
                        )
                        qv_raw = call_qwen_openrouter_vision(verify_prompt, imgs)
                        qv_json = json_guard(qv_raw, default={})
                        s_sel = score_output(agent_id, sel)
                        s_qv = score_output(agent_id, qv_json)
                        if s_qv > s_sel:
                            print(f"  [verify] Replaced with Qwen vision (score {s_qv:.1f} > {s_sel:.1f})")
                            results[agent_id] = qv_json
                        bench_meta.setdefault(agent_id, {})["qwen_verify"] = {
                            "used": s_qv > s_sel,
                            "pages_checked": page_idxs[:3],
                            "scores": {"selected": s_sel, "qwen_vision": s_qv},
                        }
                    except Exception as e:
                        print(f"  [verify] Qwen vision verification error: {e}")
        except Exception as e:
            print(f"Error with {agent_id}: {e}")
            results[agent_id] = {}
    if qc_meta:
        results["_qc"] = qc_meta
    if bench_meta:
        results["_bench"] = bench_meta
    return results

def main():
    parser = argparse.ArgumentParser(description="Gracian Pipeline CLI")
    parser.add_argument("--input-dir", required=True, help="Input directory with PDFs")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for processing")
    parser.add_argument("--simulate-scanned-first", action="store_true", help="Treat the first PDF as scanned (vision-only)")
    parser.add_argument("--max-rounds", type=int, default=5, help="Maximum rounds for extraction")
    parser.add_argument("--target-accuracy", type=float, default=0.95, help="Target accuracy")
    
    args = parser.parse_args()
    # Verbose run config
    print("=== Gracian Pipeline Start ===")
    print(f"Input: {args.input_dir} | batch={args.batch_size} | simulate_scanned_first={args.simulate_scanned_first}")
    print(f"Models: XAI_MODEL={os.getenv('XAI_MODEL','grok-4-fast-reasoning-latest')} | GEMINI_MODEL={os.getenv('GEMINI_MODEL','gemini-2.5-pro')} | OPENROUTER_QWEN_MODEL={os.getenv('OPENROUTER_QWEN_MODEL','(disabled for text)')}")
    print(f"Jury: provider={os.getenv('JURY_PROVIDER','openrouter')} | model={os.getenv('JURY_MODEL_OPENROUTER',os.getenv('JURY_MODEL','openai/gpt-5'))}")
    print(f"Benchmark mode: {os.getenv('BENCHMARK_MODE','true')} | TEXT_QWEN_ENABLED={os.getenv('TEXT_QWEN_ENABLED','false')} | TABLE_QWEN_VERIFY={os.getenv('TABLE_QWEN_VERIFY','true')} | TABLE_VISION_QC={os.getenv('TABLE_VISION_QC','false')}")
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist")
        return
    
    pdfs = [Path(p) for p in glob.glob(str(input_dir / "**/*.pdf"), recursive=True)]
    print(f"Found {len(pdfs)} PDFs")
    
    # For simplicity, process all with batch size ignored for now
    all_results = {}
    for idx, pdf in enumerate(pdfs[:args.batch_size]):  # Process only batch-size for test
        # Hybrid mode: one-shot first, then orchestrate only under-performing agents
        if os.getenv("HYBRID_MODE", "false").lower() == "true":
            print(f"[hybrid] One-shot first for {pdf}")
            oneshot = oneshot_extract(str(pdf), AGENT_PROMPTS)
            # Decide which agents need orchestration (score < target)
            try:
                target = float(os.getenv("ORCHESTRATOR_TARGET_SCORE", "95"))
            except Exception:
                target = 95.0
            needs: dict[str, str] = {}
            for aid, prompt in AGENT_PROMPTS.items():
                if aid.startswith("_"):
                    continue
                data = oneshot.get(aid, {})
                sc = score_output(aid, data)
                if sc < target:
                    needs[aid] = prompt
            print(f"[hybrid] Under target ({target}) agents: {list(needs.keys())}")
            if needs:
                print(f"[hybrid] Orchestrating {len(needs)} agent(s) for {pdf}")
                orch = orchestrate_pdf(str(pdf), needs, max_rounds=int(os.getenv("ORCHESTRATOR_MAX_ROUNDS", str(args.max_rounds))))
                # Merge: orchestrated agents replace oneshot for those keys
                for k, v in orch.items():
                    if k == "_qc":
                        continue
                    oneshot[k] = v
                # Merge qc
                if "_qc" in orch:
                    oneshot.setdefault("_qc", {}).update(orch["_qc"])  # type: ignore
            all_results[str(pdf)] = oneshot
            continue

        # One-shot mode: single GPT-5 pass produces sectionizer + all agents at once
        if os.getenv("ONESHOT", "false").lower() == "true":
            print(f"[oneshot] Single-pass extraction for {pdf}")
            results = oneshot_extract(str(pdf), AGENT_PROMPTS)
            all_results[str(pdf)] = results
            continue

        # Orchestrated mode: one OpenAI agent coaches sectionizer + agents with iterative loops
        if os.getenv("ORCHESTRATE", "false").lower() == "true":
            try:
                rounds = int(os.getenv("ORCHESTRATOR_MAX_ROUNDS", str(args.max_rounds)))
            except Exception:
                rounds = args.max_rounds
            print(f"[orchestrate] Using orchestrated extraction for {pdf} (rounds={rounds})")
            results = orchestrate_pdf(str(pdf), AGENT_PROMPTS, max_rounds=rounds)
            all_results[str(pdf)] = results
            continue
        if args.simulate_scanned_first and idx == 0:
            os.environ["VISION_MAX_PAGES"] = os.getenv("VISION_MAX_PAGES", "3")
            print(f"[simulate-scanned] Using vision-only for {pdf}")
            # Vision-only path: run all agents via vision QC
            from core.vision_qc import vision_qc_agent
            vis_results = {}
            vis_meta = {}
            for agent_id, prompt in AGENT_PROMPTS.items():
                print(f"  [vision] {agent_id} -> images")
                try:
                    full_prompt = f"{prompt}\n\n{schema_prompt_block(agent_id)}"
                    best, meta = vision_qc_agent(str(pdf), agent_id, full_prompt)
                    # numeric QC + enforcement for parity with process_pdf vision path
                    qcnum1 = numeric_qc(agent_id, best)
                    meta["numeric_qc_first"] = qcnum1
                    best_enforced, verified, dropped = enforce(agent_id, best)
                    if verified:
                        meta["verified_fields"] = verified
                    if dropped:
                        meta["dropped_fields"] = dropped
                    vis_results[agent_id] = best_enforced
                    vis_meta[agent_id] = meta
                except Exception as e:
                    print(f"  [vision] error {agent_id}: {e}")
                    vis_results[agent_id] = {}
            if vis_meta:
                vis_results["_qc"] = vis_meta
            results = vis_results
        else:
            results = process_pdf(pdf, AGENT_PROMPTS)
        all_results[str(pdf)] = results
    
    # Save results
    output_file = input_dir / "extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Results saved to {output_file}")

    # Produce a brief coverage/accuracy summary
    try:
        def _is_nonempty(v: object) -> bool:
            if v is None:
                return False
            if isinstance(v, (int, float)):
                return True
            if isinstance(v, str):
                return v.strip() != ""
            if isinstance(v, (list, dict)):
                return len(v) > 0
            return False

        summary = {}
        for pdf_path, res in all_results.items():
            pdf_sum = {"agents": {}, "evidence_ratio": 0.0}
            agents = {k: v for k, v in res.items() if not k.startswith("_")}
            ev_has = 0
            ev_total = 0
            for agent_id, data in agents.items():
                types = get_types(agent_id)
                keys = [k for k in types.keys() if k != "evidence_pages"]
                filled = sum(1 for k in keys if _is_nonempty(data.get(k)))
                coverage = 0.0 if not keys else round(100.0 * filled / len(keys), 1)
                # evidence presence
                if "evidence_pages" in types:
                    ev_total += 1
                    if _is_nonempty(data.get("evidence_pages")):
                        ev_has += 1
                # numeric qc pass if available in _qc
                qc = res.get("_qc", {}).get(agent_id, {}) if isinstance(res.get("_qc"), dict) else {}
                num_qc = qc.get("numeric_qc_first", {})
                pdf_sum["agents"][agent_id] = {
                    "coverage_pct": coverage,
                    "numeric_qc_pass": bool(num_qc.get("passed", False)),
                }
            pdf_sum["evidence_ratio"] = (round(100.0 * ev_has / ev_total, 1) if ev_total else 0.0)
            summary[pdf_path] = pdf_sum

        out_dir = input_dir / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        summary_file = out_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to {summary_file}")
    except Exception as e:
        print(f"[warn] Could not generate summary: {e}")

if __name__ == "__main__":
    main()
