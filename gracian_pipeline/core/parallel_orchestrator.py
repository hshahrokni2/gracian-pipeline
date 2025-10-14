"""
Parallel Multi-Agent Orchestrator
Robust, scalable architecture for extracting 13 BRF agents in parallel.

Key Features:
- Independent API calls per agent (no cognitive overload)
- Context optimization (5K chars per agent, not 40K)
- Parallel execution with ThreadPoolExecutor (4x speedup)
- Graceful degradation (isolated failures)
- Retry logic for critical agents
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from openai import OpenAI

from .docling_adapter_ultra import UltraComprehensiveDoclingAdapter
from .sectionizer import sectionize_pdf
from .schema_comprehensive import COMPREHENSIVE_TYPES, schema_comprehensive_prompt_block
from ..prompts.agent_prompts import AGENT_PROMPTS
from .llm_retry_wrapper import call_llm_with_retry, RetryConfig
from .agent_confidence import add_confidence_to_result
from .path_b_integration import is_path_b_agent, extract_with_path_b_agent
from .universal_learning_wrapper import UniversalLearningWrapper

logger = logging.getLogger(__name__)


# ============================================================================
# Component 1: Single-Agent Extraction with Robust Error Handling
# ============================================================================

def extract_single_agent(
    agent_id: str,
    agent_prompt: str,
    document_context: str,
    tables: List[Dict],
    page_numbers: List[int],
    client: OpenAI,
    timeout: int = 30,
    markdown: str = None,  # Added for Path B integration
    enable_learning: bool = True  # Enable adaptive learning
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract data for a single agent with timeout and retry.

    INTEGRATION: Routes note agents to Path B implementation for enhanced extraction.
    LEARNING: Records extraction patterns for adaptive improvement.

    Args:
        agent_id: Agent identifier (e.g., "governance_agent")
        agent_prompt: Agent system prompt from AGENT_PROMPTS
        document_context: Relevant document sections (max 10K chars)
        tables: Relevant tables for this agent
        page_numbers: Page numbers this agent should focus on
        client: OpenAI client instance
        timeout: Maximum seconds for API call
        markdown: Full document markdown (for Path B note detection)
        enable_learning: Enable adaptive learning (default: True)

    Returns:
        (result_dict, metadata_dict)
        - result_dict: Extracted data (empty dict on failure)
        - metadata_dict: Status, timing, tokens, etc.

    Never raises exceptions - always returns valid structure.
    """
    start_time = time.time()

    # Initialize learning wrapper if enabled
    learning_wrapper = UniversalLearningWrapper(agent_id, enable_learning) if enable_learning else None

    # ✨ PATH B INTEGRATION: Route note agents to Path B implementation
    if is_path_b_agent(agent_id) and markdown:
        try:
            logger.info(f"🎯 Routing {agent_id} to Path B (TDD production-grade agent)")
            return extract_with_path_b_agent(agent_id, markdown, tables, page_numbers)
        except Exception as e:
            logger.warning(f"Path B extraction failed for {agent_id}: {e}, falling back to Option A")
            # Fall through to Option A extraction

    try:
        # Format tables for this agent (max 3 tables to reduce context)
        tables_text = _format_tables_for_agent(tables[:3])

        # Build focused prompt
        prompt = f"""Extract data from this Swedish BRF annual report section.

DOCUMENT SECTION (relevant to {agent_id}):
{document_context[:10000]}

{tables_text}

INSTRUCTIONS: Extract ONLY the fields below. Return valid JSON.

{schema_comprehensive_prompt_block(agent_id)}

FOCUS ON PAGES: {page_numbers}

Return ONLY valid JSON matching the schema above. Use null for missing data."""

        # Call OpenAI with retry logic and timeout
        response = call_llm_with_retry(
            client=client,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            timeout=timeout,
            config=RetryConfig(max_retries=3, base_delay=1.0),
            context={"agent_id": agent_id, "pages": page_numbers}
        )

        # Parse JSON with fallback
        content = response.choices[0].message.content.strip()
        result = _parse_json_with_fallback(content)

        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Add evidence pages to result for learning
        if result and page_numbers and 'evidence_pages' not in result:
            result['evidence_pages'] = page_numbers

        # 🎓 LEARNING: Record extraction for adaptive improvement
        if learning_wrapper and result:
            try:
                learning_wrapper._record_extraction(result)
                logger.debug(f"✅ Learning recorded for {agent_id}")
            except Exception as e:
                logger.warning(f"Learning recording failed for {agent_id}: {e}")
                # Don't fail extraction if learning fails

        # Return with success metadata
        return result, {
            "status": "success",
            "agent_id": agent_id,
            "token_count": response.usage.total_tokens,
            "latency_ms": elapsed_ms,
            "pages_used": page_numbers
        }

    except TimeoutError:
        logger.warning(f"Agent {agent_id} timed out after {timeout}s")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {}, {
            "status": "timeout",
            "agent_id": agent_id,
            "latency_ms": elapsed_ms
        }

    except Exception as e:
        logger.error(f"Agent {agent_id} failed: {e}")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {}, {
            "status": "failed",
            "agent_id": agent_id,
            "error": str(e),
            "latency_ms": elapsed_ms
        }


def _format_tables_for_agent(tables: List[Dict]) -> str:
    """Format tables for agent context (compact version)."""
    if not tables:
        return "No tables available for this section."

    formatted = f"TABLES ({len(tables)} available):\n\n"
    for i, table in enumerate(tables, 1):
        # Extract basic table structure (first 5 rows only)
        cells = table.get('data', {}).get('table_cells', [])[:20]  # Limit cells
        if cells:
            formatted += f"Table {i}:\n"
            for cell in cells:
                text = cell.get('text', '').strip()
                if text:
                    formatted += f"  {text}\n"
            formatted += "\n"

    return formatted[:2000]  # Limit total table context to 2K chars


def _parse_json_with_fallback(content: str) -> Dict[str, Any]:
    """Parse JSON with multiple fallback strategies."""
    # Remove markdown fences if present
    if content.startswith("```"):
        import re
        content = re.sub(r'^```(?:json)?\n', '', content)
        content = re.sub(r'\n```$', '', content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in content
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except:
            pass

        # Return empty dict on failure
        logger.warning(f"Failed to parse JSON, returning empty dict")
        return {}


# ============================================================================
# Component 2: Context Router (Section-Based Optimization)
# ============================================================================

def build_agent_context_map(
    pdf_path: str,
    markdown: str,
    tables: List[Dict],
    section_map: Optional[Dict[str, List[int]]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Build minimal context for each agent (token optimization).

    Args:
        pdf_path: Path to PDF
        markdown: Full document markdown (from Docling)
        tables: All tables from document
        section_map: Optional section mapping from sectionizer

    Returns:
        {
            "governance_agent": {
                "context": "...",  # Relevant sections only (~5K chars)
                "tables": [...],    # Relevant tables only (max 3)
                "pages": [1, 2, 3]  # Page numbers
            },
            ...
        }
    """
    # Agent to section keyword mapping (Swedish BRF terminology)
    AGENT_SECTION_MAP = {
        # Governance agents (split into specialized agents)
        "chairman_agent": ["Styrelsen", "Styrelsens ordförande", "Ordförande"],
        "board_members_agent": ["Styrelsen", "Styrelseledamöter", "Ledamöter"],
        "auditor_agent": ["Revisorer", "Revisor", "Vald av"],
        # Financial agent
        "financial_agent": ["Resultaträkning", "Balansräkning", "Kassaflöde"],
        # Property agent
        "property_agent": ["Förvaltningsberättelse", "Fastigheten", "Byggnaden", "Grundfakta"],
        # Fees agent
        "fees_agent": ["Årsavgift", "Avgift", "Månadsavgift"],
        # Loans agent
        "loans_agent": ["Not 5", "Låneskulder", "Kreditinstitut"],
        # Notes agents
        "notes_depreciation_agent": ["Not 1", "Avskrivningar"],
        "notes_maintenance_agent": ["Not", "Underhåll", "Underhållsplan"],
        "notes_tax_agent": ["Not", "Skatt", "Inkomstskatt"],
        # Events agent
        "events_agent": ["Väsentliga händelser", "Händelser"],
        # Audit agent
        "audit_agent": ["Revisionsberättelse"],
        # Reserves agent
        "reserves_agent": ["Fond", "Avsättning"],
        # Energy agent
        "energy_agent": ["Energideklaration", "Energiklass"],
        # Cashflow agent
        "cashflow_agent": ["Kassaflödesanalys", "Kassaflöde"]
    }

    agent_contexts = {}

    for agent_id, section_keywords in AGENT_SECTION_MAP.items():
        # Find relevant pages for this agent
        pages = _find_pages_by_keywords(markdown, section_keywords, section_map)

        if not pages:
            # Fallback: use first 5 pages if no specific pages found
            pages = list(range(1, 6))

        # Extract relevant sections from markdown
        context = _extract_sections_from_pages(markdown, pages, section_keywords)

        # Filter relevant tables (only tables mentioned in context)
        relevant_tables = _filter_relevant_tables(tables, context, pages)

        agent_contexts[agent_id] = {
            "context": context[:10000],  # Limit to 10K chars per agent
            "tables": relevant_tables[:3],  # Max 3 tables per agent
            "pages": pages[:5]  # Max 5 pages per agent
        }

    return agent_contexts


def _find_pages_by_keywords(
    markdown: str,
    keywords: List[str],
    section_map: Optional[Dict[str, List[int]]]
) -> List[int]:
    """Find pages containing any of the keywords."""
    pages = set()

    # Try section map first (if available)
    if section_map:
        for agent_id, agent_pages in section_map.items():
            if any(kw.lower() in agent_id.lower() for kw in keywords):
                pages.update(agent_pages)

    # If no pages found, scan markdown for keywords
    if not pages:
        lines = markdown.split('\n')
        for i, line in enumerate(lines):
            if any(kw.lower() in line.lower() for kw in keywords):
                # Estimate page number (rough heuristic: 50 lines per page)
                page_num = (i // 50) + 1
                pages.add(page_num)

    return sorted(list(pages))[:5]  # Return max 5 pages


def _extract_sections_from_pages(
    markdown: str,
    pages: List[int],
    keywords: List[str]
) -> str:
    """Extract relevant sections from markdown based on keywords."""
    lines = markdown.split('\n')
    relevant_lines = []

    # Estimate lines per page (rough heuristic)
    lines_per_page = len(lines) // max(1, len(pages))

    for page in pages:
        # Calculate line range for this page
        start_line = max(0, (page - 1) * lines_per_page)
        end_line = min(len(lines), page * lines_per_page)

        # Extract lines from this page
        page_lines = lines[start_line:end_line]

        # Filter lines containing keywords (with context window)
        for i, line in enumerate(page_lines):
            if any(kw.lower() in line.lower() for kw in keywords):
                # Include surrounding context (5 lines before, 10 lines after)
                context_start = max(0, i - 5)
                context_end = min(len(page_lines), i + 10)
                relevant_lines.extend(page_lines[context_start:context_end])

    return '\n'.join(relevant_lines)


def _filter_relevant_tables(
    tables: List[Dict],
    context: str,
    pages: List[int]
) -> List[Dict]:
    """Filter tables that are relevant to this agent's context."""
    relevant_tables = []

    for table in tables:
        # Check if table contains keywords from context
        table_text = _extract_table_preview(table)

        # Simple relevance check: does table text appear in context?
        if any(word in context for word in table_text.split()[:10]):
            relevant_tables.append(table)

    return relevant_tables


def _extract_table_preview(table: Dict) -> str:
    """Extract first few cells from table as preview."""
    cells = table.get('data', {}).get('table_cells', [])[:10]
    return ' '.join([cell.get('text', '') for cell in cells])


# ============================================================================
# Component 3: Parallel Orchestrator
# ============================================================================

def extract_all_agents_parallel(
    pdf_path: str,
    max_workers: int = 5,
    enable_retry: bool = True,
    enable_learning: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Extract all agents in parallel (ROBUST MULTI-AGENT ARCHITECTURE).

    ENHANCED with automatic PDF type detection and intelligent routing:
    - Machine-readable PDFs → Text extraction (fast, cheap)
    - Scanned PDFs → Vision consensus (accurate, necessary)
    - Hybrid PDFs → Text with vision fallback (optimal)

    Args:
        pdf_path: Path to PDF
        max_workers: Number of concurrent workers (5-8 recommended)
        enable_retry: Retry critical agents on failure
        enable_learning: Enable adaptive learning (default: True)
        verbose: Print progress messages

    Returns:
        {
            "governance_agent": {...},
            "financial_agent": {...},
            ...
            "_metadata": {
                "total_agents": 13,
                "successful_agents": 12,
                "failed_agents": ["notes_tax_agent"],
                "total_time_seconds": 25.3,
                "token_usage": 32456,
                "pdf_type": "scanned",
                "extraction_strategy": "vision_consensus"
            }
        }
    """
    start_time = time.time()

    if verbose:
        print("=" * 80)
        print("🚀 PARALLEL MULTI-AGENT EXTRACTION")
        print("=" * 80)

    # ============================================================================
    # STEP 0: PDF TYPE CLASSIFICATION (NEW - Phase 2A)
    # ============================================================================

    if verbose:
        print("\n📋 Step 0: Classifying PDF type...")

    from .pdf_classifier import classify_pdf

    classification = classify_pdf(pdf_path)

    if verbose:
        print(f"   Type: {classification.pdf_type}")
        print(f"   Strategy: {classification.strategy}")
        print(f"   Confidence: {classification.confidence:.1%}")
        print(f"   Text Density: {classification.text_density:.0f} chars/page")
        print(f"   Image Ratio: {classification.image_ratio:.1%}")

    # Route based on classification
    if classification.pdf_type == "scanned" and classification.confidence > 0.7:
        # High-confidence scanned → Vision consensus (slow, accurate)
        logger.info(f"🎨 Routing to vision consensus extraction (scanned PDF)")
        return _extract_with_vision_consensus(
            pdf_path,
            max_workers,
            classification,
            enable_retry,
            enable_learning,
            verbose
        )

    elif classification.pdf_type == "machine_readable":
        # Machine-readable → Text extraction (fast, cheap)
        logger.info(f"📝 Routing to text extraction (machine-readable PDF)")
        # Continue with existing text extraction below
        # (No return - fall through to existing code)

    else:
        # Hybrid or low-confidence → Try text, fall back to vision if poor
        logger.info(f"🔀 Using hybrid strategy (text with vision fallback)")
        # Continue with text extraction, will check quality at end
        # (No return - fall through to existing code)

    # Store classification for metadata
    _pdf_classification = classification

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Step 1: Extract with Docling
    if verbose:
        print("\n📄 Step 1: Extracting document structure...")

    adapter = UltraComprehensiveDoclingAdapter()
    docling_result = adapter.extract_with_docling(pdf_path)
    markdown = docling_result['markdown']
    tables = docling_result['tables']

    if verbose:
        print(f"   ✓ Extracted {len(markdown)} chars, {len(tables)} tables")

    # Step 2: Run sectionizer (optional - can skip for speed)
    if verbose:
        print("\n🗺️  Step 2: Detecting sections...")

    try:
        section_map = sectionize_pdf(pdf_path)
        if verbose:
            print(f"   ✓ Detected {len(section_map)} sections")
    except Exception as e:
        logger.warning(f"Sectionizer failed: {e}, continuing without section map")
        section_map = None

    # Step 3: Build agent contexts
    if verbose:
        print("\n🔍 Step 3: Building agent contexts...")

    agent_contexts = build_agent_context_map(pdf_path, markdown, tables, section_map)

    if verbose:
        total_chars = sum(len(ctx["context"]) for ctx in agent_contexts.values())
        print(f"   ✓ Built contexts for {len(agent_contexts)} agents ({total_chars:,} total chars)")

    # Step 4: Prepare agent tasks (with markdown for Path B integration)
    agent_tasks = []
    for agent_id, agent_prompt in AGENT_PROMPTS.items():
        context_data = agent_contexts.get(agent_id, {})
        agent_tasks.append({
            "agent_id": agent_id,
            "agent_prompt": agent_prompt,
            "document_context": context_data.get("context", ""),
            "tables": context_data.get("tables", []),
            "page_numbers": context_data.get("pages", []),
            "client": client,
            "markdown": markdown,  # ✨ Added for Path B integration
            "enable_learning": enable_learning  # 🎓 Enable adaptive learning
        })

    # Step 5: Execute in parallel
    if verbose:
        print(f"\n⚡ Step 4: Extracting {len(agent_tasks)} agents in parallel (workers={max_workers})...")

    results = {}
    metadata = {
        "total_agents": len(agent_tasks),
        "successful_agents": 0,
        "failed_agents": [],
        "agent_metadata": {}
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(extract_single_agent, **task): task["agent_id"]
            for task in agent_tasks
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_agent):
            agent_id = future_to_agent[future]
            completed += 1

            try:
                result, agent_metadata = future.result(timeout=35)  # 30s + 5s buffer

                results[agent_id] = result
                metadata["agent_metadata"][agent_id] = agent_metadata

                if agent_metadata["status"] == "success":
                    metadata["successful_agents"] += 1
                    if verbose:
                        print(f"   ✅ [{completed}/{len(agent_tasks)}] {agent_id}: {agent_metadata['token_count']} tokens, {agent_metadata['latency_ms']}ms")
                else:
                    metadata["failed_agents"].append(agent_id)
                    if verbose:
                        print(f"   ❌ [{completed}/{len(agent_tasks)}] {agent_id}: {agent_metadata['status']}")

            except TimeoutError:
                logger.error(f"Agent {agent_id} exceeded 35s timeout")
                results[agent_id] = {}
                metadata["failed_agents"].append(agent_id)
                if verbose:
                    print(f"   ⏱️  [{completed}/{len(agent_tasks)}] {agent_id}: timeout")

    # Step 6: Retry critical agents if enabled
    if enable_retry:
        critical_agents = ["governance_agent", "financial_agent", "property_agent"]
        failed_critical = [a for a in critical_agents if a in metadata["failed_agents"]]

        if failed_critical:
            if verbose:
                print(f"\n🔄 Step 5: Retrying {len(failed_critical)} critical agents...")

            for agent_id in failed_critical:
                time.sleep(2)  # Brief pause before retry
                task = next(t for t in agent_tasks if t["agent_id"] == agent_id)
                result, agent_metadata = extract_single_agent(**task)

                if agent_metadata["status"] == "success":
                    results[agent_id] = result
                    metadata["successful_agents"] += 1
                    metadata["failed_agents"].remove(agent_id)
                    metadata["agent_metadata"][agent_id] = agent_metadata
                    if verbose:
                        print(f"   ✅ {agent_id}: retry succeeded")
                else:
                    if verbose:
                        print(f"   ❌ {agent_id}: retry failed")

    # Step 7: Calculate final metrics
    metadata["total_time_seconds"] = round(time.time() - start_time, 1)
    metadata["token_usage"] = sum(
        m.get("token_count", 0)
        for m in metadata["agent_metadata"].values()
    )

    # Add PDF classification metadata (Phase 2A)
    if '_pdf_classification' in locals():
        metadata["pdf_type"] = _pdf_classification.pdf_type
        metadata["extraction_strategy"] = "text"  # Since we're in text extraction path
        metadata["classification_confidence"] = _pdf_classification.confidence

    # Step 7.5: Check if hybrid/low-confidence PDF needs vision fallback
    if '_pdf_classification' in locals() and (_pdf_classification.pdf_type == "hybrid" or _pdf_classification.confidence < 0.7):
        # Calculate extraction quality
        quality = _check_extraction_quality(results)

        if verbose:
            print(f"\n🔍 Quality check: {quality:.1%} coverage")

        if quality < 0.30:  # <30% coverage = poor extraction
            if verbose:
                print(f"   ⚠️  Text extraction poor ({quality:.1%} coverage)")
                print(f"   🎨 Falling back to vision consensus...")

            # Fall back to vision consensus
            vision_results = _extract_with_vision_consensus(
                pdf_path,
                max_workers,
                _pdf_classification,
                enable_retry,
                enable_learning,
                verbose
            )

            # Return vision results instead
            return vision_results

    results["_metadata"] = metadata

    # ============================================================================
    # NEW: Phase 2B - Cross-Agent Validation & Consensus Resolution
    # ============================================================================

    # Step 7.6: Cross-agent validation (hallucination detection, consistency checks)
    if verbose:
        print("\n🔍 Step 7: Running cross-agent validation...")

    from ..validation import CrossValidator, HallucinationDetector, ConsensusResolver

    # Run validation rules
    validator = CrossValidator()
    validation_warnings = validator.validate(results)

    # Run hallucination detection
    hallucination_detector = HallucinationDetector()
    hallucination_warnings = hallucination_detector.detect(results)

    # Combine all warnings
    all_warnings = validation_warnings + hallucination_warnings

    if verbose:
        if all_warnings:
            summary = validator.get_summary(all_warnings)
            print(f"   ⚠️  Found {summary['total_warnings']} validation warnings:")
            print(f"      High severity: {summary['high_severity']}")
            print(f"      Medium severity: {summary['medium_severity']}")
            print(f"      Low severity: {summary['low_severity']}")
            print(f"      Affected agents: {', '.join(summary['affected_agents'][:5])}")
        else:
            print(f"   ✅ No validation warnings")

    # Step 7.7: Consensus resolution (resolve conflicts between agents)
    if verbose:
        print("\n🤝 Step 8: Resolving conflicts...")

    resolver = ConsensusResolver()
    results = resolver.resolve_conflicts(results, all_warnings)

    if verbose:
        if resolver.conflicts_resolved_count > 0:
            print(f"   ✅ Resolved {resolver.conflicts_resolved_count} conflicts")
            # Show first few conflict resolutions
            for log_entry in resolver.resolution_log[:3]:
                print(f"      - {log_entry['field']}: {log_entry['strategy']} "
                     f"(confidence: {log_entry['confidence']:.1%})")
        else:
            print(f"   ✅ No conflicts to resolve")

    # Add validation metadata to results
    results['_validation'] = {
        'warnings': [w.to_dict() for w in all_warnings],
        'warnings_count': len(all_warnings),
        'high_severity_count': sum(1 for w in all_warnings if w.severity == 'high'),
        'rules_triggered': list(set(w.rule for w in all_warnings)),
        'conflicts_resolved': resolver.conflicts_resolved_count
    }

    # Step 8: Add confidence scores
    if verbose:
        print("\n📊 Step 9: Calculating confidence scores...")

    results = add_confidence_to_result(results)

    if verbose and "extraction_quality" in results:
        confidence_score = results["extraction_quality"].get("confidence_score", 0)
        high_conf = results["extraction_quality"].get("high_confidence_agents", 0)
        low_conf = results["extraction_quality"].get("low_confidence_agents", 0)
        print(f"   ✓ Overall confidence: {confidence_score:.1%}")
        print(f"   ✓ High confidence agents: {high_conf}")
        print(f"   ✓ Low confidence agents: {low_conf}")

    if verbose:
        print("\n" + "=" * 80)
        print(f"✅ Extraction complete: {metadata['successful_agents']}/{metadata['total_agents']} agents succeeded")
        print(f"⏱️  Total time: {metadata['total_time_seconds']}s")
        print(f"🎫 Total tokens: {metadata['token_usage']:,}")
        print("=" * 80)

    return results


# ============================================================================
# Component 4: Vision Consensus Extraction (Phase 2A)
# ============================================================================

def _extract_with_vision_consensus(
    pdf_path: str,
    max_workers: int,
    classification: any,  # PDFClassification object
    enable_retry: bool,
    enable_learning: bool,
    verbose: bool
) -> Dict[str, Any]:
    """
    Extract using multi-model vision consensus for scanned PDFs.

    Returns same structure as text extraction for validation compatibility.
    """
    from .image_preprocessor import preprocess_pdf, PreprocessingPresets
    from .vision_consensus import VisionConsensusExtractor

    start_time = time.time()

    if verbose:
        print("\n🎨 VISION CONSENSUS EXTRACTION MODE")
        print("=" * 80)

    # Step 1: Preprocess all pages to images
    if verbose:
        print("\n📸 Step 1: Preprocessing PDF to images (200 DPI, color preserved)...")

    config = PreprocessingPresets.vision_model_optimal()
    all_images = preprocess_pdf(pdf_path, config=config)

    # Build image map
    image_map = {page_num: img for page_num, img in all_images}

    if verbose:
        print(f"   ✓ Preprocessed {len(image_map)} pages")

    # Step 2: Initialize vision extractor (reuse across agents)
    vision_extractor = VisionConsensusExtractor()

    # Step 3: Extract agents in parallel
    agent_names = list(AGENT_PROMPTS.keys())

    if verbose:
        print(f"\n⚡ Step 2: Extracting {len(agent_names)} agents with vision consensus "
              f"(workers={max_workers})...")

    results = {}
    metadata = {
        "total_agents": len(agent_names),
        "successful_agents": 0,
        "failed_agents": [],
        "agent_metadata": {},
        "pdf_type": classification.pdf_type,
        "extraction_strategy": "vision_consensus",
        "classification_confidence": classification.confidence
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for agent_name in agent_names:
            # Get pages for this agent
            page_numbers = _get_pages_for_agent(agent_name, pdf_path)
            agent_images = [(pn, image_map[pn]) for pn in page_numbers
                           if pn in image_map]

            if not agent_images:
                logger.warning(f"   ⚠️  No images for {agent_name}, skipping")
                continue

            # Submit vision extraction
            future = executor.submit(
                _extract_single_agent_vision,
                agent_name,
                agent_images,
                AGENT_PROMPTS[agent_name],
                vision_extractor
            )
            futures[future] = agent_name

        # Collect results
        completed = 0
        for future in as_completed(futures):
            agent_name = futures[future]
            completed += 1

            try:
                result = future.result(timeout=60)  # Vision models are slower

                results[agent_name] = result.get("extracted_data", {})
                metadata["agent_metadata"][agent_name] = {
                    "status": "success" if "error" not in result else "failed",
                    "confidence": result.get("confidence", 0.0),
                    "agreement_ratio": result.get("agreement_ratio", 0.0),
                    "primary_model": result.get("primary_model", "unknown"),
                    "pages_used": result.get("evidence_pages", [])
                }

                if "error" not in result:
                    metadata["successful_agents"] += 1
                    if verbose:
                        print(f"   ✅ [{completed}/{len(futures)}] {agent_name}: "
                             f"confidence={result.get('confidence', 0):.1%}, "
                             f"agreement={result.get('agreement_ratio', 0):.1%}")
                else:
                    metadata["failed_agents"].append(agent_name)
                    if verbose:
                        print(f"   ❌ [{completed}/{len(futures)}] {agent_name}: "
                             f"{result['error']}")

            except TimeoutError:
                logger.error(f"Agent {agent_name} exceeded 60s timeout")
                results[agent_name] = {}
                metadata["failed_agents"].append(agent_name)
                if verbose:
                    print(f"   ⏱️  [{completed}/{len(futures)}] {agent_name}: timeout")

    # Calculate final metrics
    metadata["total_time_seconds"] = round(time.time() - start_time, 1)

    results["_metadata"] = metadata

    # Add confidence scores
    if verbose:
        print("\n📊 Step 3: Calculating overall confidence...")

    results = add_confidence_to_result(results)

    # =========================================================================
    # NEW: Phase 2B - Cross-Agent Validation & Consensus Resolution (Vision Mode)
    # =========================================================================

    if verbose:
        print("\n🔍 Step 7: Running cross-agent validation...")

    from ..validation import CrossValidator, HallucinationDetector, ConsensusResolver

    # Run validation rules
    validator = CrossValidator()
    validation_warnings = validator.validate(results)

    # Run hallucination detection
    hallucination_detector = HallucinationDetector()
    hallucination_warnings = hallucination_detector.detect(results)

    # Combine all warnings
    all_warnings = validation_warnings + hallucination_warnings

    if verbose:
        if all_warnings:
            summary = validator.get_summary(all_warnings)
            print(f"   ⚠️  Found {summary['total_warnings']} validation warnings:")
            print(f"      High severity: {summary['high_severity']}")
            print(f"      Medium severity: {summary['medium_severity']}")
            print(f"      Low severity: {summary['low_severity']}")
            print(f"      Affected agents: {', '.join(summary['affected_agents'][:5])}")
        else:
            print(f"   ✅ No validation warnings")

    # Consensus resolution
    if verbose:
        print("\n🤝 Step 8: Resolving conflicts...")

    resolver = ConsensusResolver()
    results = resolver.resolve_conflicts(results, all_warnings)

    if verbose:
        if resolver.conflicts_resolved_count > 0:
            print(f"   ✅ Resolved {resolver.conflicts_resolved_count} conflicts")
            # Show first few conflict resolutions
            for log_entry in resolver.resolution_log[:3]:
                print(f"      - {log_entry['field']}: {log_entry['strategy']} "
                     f"(confidence: {log_entry['confidence']:.1%})")
        else:
            print(f"   ✅ No conflicts to resolve")

    # Add validation metadata to results
    results['_validation'] = {
        'warnings': [w.to_dict() for w in all_warnings],
        'warnings_count': len(all_warnings),
        'high_severity_count': sum(1 for w in all_warnings if w.severity == 'high'),
        'rules_triggered': list(set(w.rule for w in all_warnings)),
        'conflicts_resolved': resolver.conflicts_resolved_count
    }

    # Final output
    if verbose:
        print("\n" + "=" * 80)
        print(f"✅ Vision extraction complete: {metadata['successful_agents']}/{metadata['total_agents']} agents succeeded")
        print(f"⏱️  Total time: {metadata['total_time_seconds']}s")
        print("=" * 80)

    return results


def _extract_single_agent_vision(
    agent_name: str,
    images: List[Tuple[int, any]],  # List of (page_num, PIL.Image)
    agent_prompt: str,
    vision_extractor: any  # VisionConsensusExtractor
) -> dict:
    """
    Extract single agent using vision consensus.

    Returns same structure as text extraction for compatibility.
    """
    if not images:
        return {"error": "No images provided", "extraction_method": "vision_consensus"}

    try:
        # Call vision consensus
        consensus_result = vision_extractor.extract_from_images(
            images=images,
            extraction_prompt=agent_prompt,
            agent_name=agent_name
        )

        # Format to match text extraction structure
        return {
            "extracted_data": consensus_result.extracted_data,
            "confidence": consensus_result.confidence,
            "agreement_ratio": consensus_result.agreement_ratio,
            "primary_model": consensus_result.primary_model,
            "evidence_pages": [pn for pn, _ in images],
            "extraction_method": "vision_consensus",
            "fallback_used": consensus_result.fallback_used
        }

    except Exception as e:
        logger.error(f"Vision extraction error for {agent_name}: {e}")
        return {"error": str(e), "extraction_method": "vision_consensus"}


def _check_extraction_quality(results: dict) -> float:
    """
    Calculate coverage ratio from extraction results.

    Used to decide if vision fallback needed for hybrid PDFs.

    Returns:
        Coverage ratio (0.0-1.0)
    """
    total_fields = 0
    populated_fields = 0

    for agent_name, agent_result in results.items():
        # Skip metadata
        if agent_name.startswith("_"):
            continue

        if isinstance(agent_result, dict):
            for field, value in agent_result.items():
                # Skip metadata fields
                if field.startswith("_") or field in ["evidence_pages", "extraction_method"]:
                    continue

                total_fields += 1

                # Check if field is populated (not null, empty string, or empty list)
                if value is not None and value != "" and value != []:
                    populated_fields += 1

    return populated_fields / total_fields if total_fields > 0 else 0.0


def _get_pages_for_agent(agent_name: str, pdf_path: str) -> List[int]:
    """
    Determine which pages an agent needs.

    Uses heuristics based on Swedish BRF document structure.
    Falls back to safe defaults if section detection unavailable.

    Args:
        agent_name: Name of agent
        pdf_path: Path to PDF (for future section detection integration)

    Returns:
        List of page numbers (1-indexed)
    """
    # Agent categories (from agent_prompts.py)
    governance_agents = ["chairman_agent", "board_members_agent", "auditor_agent"]
    financial_agents = ["financial_agent", "cashflow_agent"]
    notes_agents = [
        "notes_depreciation_agent",
        "notes_maintenance_agent",
        "notes_tax_agent"
    ]
    property_agents = ["property_agent", "energy_agent"]
    loans_agents = ["loans_agent", "reserves_agent"]

    # Page allocation heuristics (based on Swedish BRF document structure)
    if agent_name in governance_agents:
        return [1, 2, 3, 4, 5]  # Governance: Pages 1-5
    elif agent_name in financial_agents:
        return [4, 5, 6, 7, 8, 9, 10]  # Financials: Pages 4-10
    elif agent_name in notes_agents:
        return [8, 9, 10, 11, 12, 13, 14, 15]  # Notes: Pages 8-15
    elif agent_name in property_agents:
        return [1, 2, 3]  # Property: Pages 1-3
    elif agent_name in loans_agents:
        return [8, 9, 10, 11, 12]  # Loans/Reserves: Pages 8-12
    else:
        return [1, 2, 3, 4, 5]  # Default: First 5 pages


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    # Test on brf_81563 (the regression case)
    test_pdf = "Hjorthagen/brf_81563.pdf"

    if not os.path.exists(test_pdf):
        print(f"Test PDF not found: {test_pdf}")
        sys.exit(1)

    print("Testing parallel orchestrator on brf_81563 (regression case)")
    print(f"Expected: Extract >= 4 board members\n")

    result = extract_all_agents_parallel(test_pdf, max_workers=5, verbose=True)

    # Check governance results
    governance = result.get("governance_agent", {})
    board_members = governance.get("board_members", [])

    print(f"\n🎯 GOVERNANCE RESULTS:")
    print(f"   Chairman: {governance.get('chairman')}")
    print(f"   Board members: {len(board_members)}")
    if board_members:
        for i, member in enumerate(board_members, 1):
            print(f"      {i}. {member}")
    print(f"   Auditor: {governance.get('auditor_name')}")

    # Success criteria
    if len(board_members) >= 4:
        print(f"\n✅ SUCCESS: Extracted {len(board_members)} board members (>= 4 expected)")
        print("   Regression fixed!")
    else:
        print(f"\n⚠️  PARTIAL: Only {len(board_members)} board members extracted")
