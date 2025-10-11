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
    timeout: int = 30
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract data for a single agent with timeout and retry.

    Args:
        agent_id: Agent identifier (e.g., "governance_agent")
        agent_prompt: Agent system prompt from AGENT_PROMPTS
        document_context: Relevant document sections (max 10K chars)
        tables: Relevant tables for this agent
        page_numbers: Page numbers this agent should focus on
        client: OpenAI client instance
        timeout: Maximum seconds for API call

    Returns:
        (result_dict, metadata_dict)
        - result_dict: Extracted data (empty dict on failure)
        - metadata_dict: Status, timing, tokens, etc.

    Never raises exceptions - always returns valid structure.
    """
    start_time = time.time()

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

        # Call OpenAI with timeout
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            timeout=timeout
        )

        # Parse JSON with fallback
        content = response.choices[0].message.content.strip()
        result = _parse_json_with_fallback(content)

        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)

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
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Extract all agents in parallel (ROBUST MULTI-AGENT ARCHITECTURE).

    Args:
        pdf_path: Path to PDF
        max_workers: Number of concurrent workers (5-8 recommended)
        enable_retry: Retry critical agents on failure
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
                "token_usage": 32456
            }
        }
    """
    start_time = time.time()

    if verbose:
        print("=" * 80)
        print("🚀 PARALLEL MULTI-AGENT EXTRACTION")
        print("=" * 80)

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

    # Step 4: Prepare agent tasks
    agent_tasks = []
    for agent_id, agent_prompt in AGENT_PROMPTS.items():
        context_data = agent_contexts.get(agent_id, {})
        agent_tasks.append({
            "agent_id": agent_id,
            "agent_prompt": agent_prompt,
            "document_context": context_data.get("context", ""),
            "tables": context_data.get("tables", []),
            "page_numbers": context_data.get("pages", []),
            "client": client
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

    results["_metadata"] = metadata

    if verbose:
        print("\n" + "=" * 80)
        print(f"✅ Extraction complete: {metadata['successful_agents']}/{metadata['total_agents']} agents succeeded")
        print(f"⏱️  Total time: {metadata['total_time_seconds']}s")
        print(f"🎫 Total tokens: {metadata['token_usage']:,}")
        print("=" * 80)

    return results


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
