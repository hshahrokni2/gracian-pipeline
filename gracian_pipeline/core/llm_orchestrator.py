"""
LLM-Based Orchestrator for Dynamic Section-to-Agent Routing

Replaces hard-coded keyword matching with intelligent LLM-based routing.
Handles heterogeneous section names across 30,000+ PDFs.

Architecture:
  Input: Section map from vision_sectionizer (level_1, level_2, level_3)
  Process: LLM analyzes section titles and routes to appropriate agents
  Output: pages_by_agent dictionary (agent_id → list of page numbers)
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from openai import OpenAI


# Agent descriptions for routing (concise)
AGENT_ROUTING_DESCRIPTIONS = {
    "chairman_agent": "Chairman/Ordförande name extraction",
    "board_members_agent": "Board members/Styrelseledamöter list extraction",
    "auditor_agent": "Auditor/Revisor information extraction",
    "financial_agent": "Financial statements: Resultaträkning (income), Balansräkning (balance sheet)",
    "property_agent": "Property details: address, built year, area, heating, energy class, apartments",
    "notes_depreciation_agent": "Depreciation method from notes (Avskrivningar)",
    "notes_maintenance_agent": "Maintenance plan from notes (Underhållsplan)",
    "notes_tax_agent": "Tax information from notes (Skatt, Inkomstskatt)",
    "events_agent": "Key events, annual meeting (Väsentliga händelser)",
    "audit_agent": "Audit report (Revisionsberättelse)",
    "loans_agent": "Loan details from Note 5 (Låneskulder)",
    "reserves_agent": "Reserve funds (Avsättning till fond)",
    "energy_agent": "Energy declaration (Energideklaration)",
    "fees_agent": "Fee structure: årsavgift, månadsavgift, room-specific fees",
    "cashflow_agent": "Cash flow statement (Kassaflödesanalys)",
}


def llm_orchestrate_sections(
    section_map: Dict[str, Any],
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
    verbose: bool = False
) -> Dict[str, List[int]]:
    """
    Use LLM to dynamically route sections to agents.

    Args:
        section_map: Output from vision_sectionizer() with level_1, level_2, level_3
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: Model to use for routing decisions
        verbose: Print routing decisions

    Returns:
        pages_by_agent: Dict[agent_id, List[page_numbers]]
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key required for LLM orchestration")

    client = OpenAI(api_key=api_key)

    # Build prompt with section information
    prompt = _build_routing_prompt(section_map)

    if verbose:
        print("[LLM Orchestrator] Routing sections to agents...")
        print(f"[LLM Orchestrator] Found {len(section_map.get('level_1', []))} level 1 sections")

    try:
        # Call LLM with routing task
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a document routing expert for Swedish BRF (housing cooperative) annual reports. Your job is to intelligently map document sections to specialized extraction agents."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        # Parse routing decisions
        content = response.choices[0].message.content
        routing = json.loads(content)

        # Convert to pages_by_agent format
        pages_by_agent = _convert_routing_to_pages(routing, verbose=verbose)

        if verbose:
            print(f"[LLM Orchestrator] Routed to {len(pages_by_agent)} agents")
            for agent_id, pages in pages_by_agent.items():
                print(f"  {agent_id}: {len(pages)} pages")

        return pages_by_agent

    except Exception as e:
        print(f"[LLM Orchestrator] Error: {e}")
        # Fallback to empty routing if LLM fails
        return {}


def _build_routing_prompt(section_map: Dict[str, Any]) -> str:
    """Build prompt for LLM routing task."""

    # Extract sections
    level_1 = section_map.get("level_1", [])
    level_2 = section_map.get("level_2", [])
    level_3 = section_map.get("level_3", [])

    # Format sections for prompt
    sections_text = "DOCUMENT SECTIONS DETECTED:\n\n"

    # Level 1 sections
    sections_text += "Level 1 (Main Sections):\n"
    for i, sec in enumerate(level_1, 1):
        title = sec.get("title", "")
        start = sec.get("start_page", 0)
        end = sec.get("end_page", 0)
        sections_text += f"{i}. \"{title}\" (pages {start}-{end})\n"

    sections_text += "\n"

    # Level 2 sections (subsections)
    if level_2:
        sections_text += "Level 2 (Subsections):\n"
        for i, sec in enumerate(level_2, 1):
            title = sec.get("title", "")
            parent = sec.get("parent", "")
            start = sec.get("start_page", 0)
            end = sec.get("end_page", 0)
            sections_text += f"{i}. \"{title}\" under \"{parent}\" (pages {start}-{end})\n"
        sections_text += "\n"

    # Level 3 sections (detailed subsections)
    if level_3:
        sections_text += "Level 3 (Detailed Subsections):\n"
        for i, sec in enumerate(level_3[:10], 1):  # Limit to first 10 to avoid token overflow
            title = sec.get("title", "")
            parent = sec.get("parent", "")
            start = sec.get("start_page", 0)
            end = sec.get("end_page", 0)
            sections_text += f"{i}. \"{title}\" under \"{parent}\" (pages {start}-{end})\n"
        if len(level_3) > 10:
            sections_text += f"... and {len(level_3) - 10} more level 3 sections\n"
        sections_text += "\n"

    # Agent descriptions
    agents_text = "AVAILABLE AGENTS:\n\n"
    for agent_id, description in AGENT_ROUTING_DESCRIPTIONS.items():
        agents_text += f"- {agent_id}: {description}\n"

    # Instructions
    instructions = """
TASK: Route each section to the most appropriate agent(s).

RULES:
1. One section can be routed to MULTIPLE agents if it contains relevant data for them
2. Consider both main sections and subsections
3. Use semantic understanding, not just keyword matching
   - "Styrelsen" → chairman_agent, board_members_agent, auditor_agent
   - "Förvaltningsberättelse" → property_agent, events_agent
   - "Resultaträkning" → financial_agent
   - "Balansräkning" → financial_agent
   - "Noter" / "Tilläggsupplysningar" → notes_* agents, loans_agent
   - "Not 5" or "Låneskulder" → loans_agent
   - "Revisionsberättelse" → audit_agent
   - "Kassaflödesanalys" → cashflow_agent
   - "Energideklaration" → energy_agent
   - "Avgift" sections → fees_agent
4. Return JSON with structure:
   {
     "agent_id": [
       {"section_name": "...", "start_page": N, "end_page": M},
       ...
     ],
     ...
   }

IMPORTANT:
- Include ALL page numbers from start_page to end_page for each section
- If a section could be relevant to multiple agents, include it for all of them
- Use actual section names from the document (don't invent)
- If uncertain, include the section (better to over-route than under-route)

Return ONLY valid JSON, no extra text.
"""

    return sections_text + "\n" + agents_text + "\n" + instructions


def _convert_routing_to_pages(
    routing: Dict[str, List[Dict]],
    verbose: bool = False
) -> Dict[str, List[int]]:
    """
    Convert LLM routing decisions to pages_by_agent format.

    Input format:
    {
      "agent_id": [
        {"section_name": "...", "start_page": N, "end_page": M},
        ...
      ]
    }

    Output format:
    {
      "agent_id": [page1, page2, page3, ...],
      ...
    }
    """
    pages_by_agent = {}

    for agent_id, sections in routing.items():
        if not isinstance(sections, list):
            continue

        pages = []
        for section in sections:
            if not isinstance(section, dict):
                continue

            start_page = section.get("start_page", 0)
            end_page = section.get("end_page", 0)

            if start_page > 0 and end_page > 0:
                # Add all pages in range (convert to 0-indexed for internal use)
                for page in range(start_page - 1, end_page):
                    if page not in pages:
                        pages.append(page)

        if pages:
            pages_by_agent[agent_id] = sorted(pages)

            if verbose:
                print(f"  [LLM Orchestrator] {agent_id}: pages {[p+1 for p in pages[:5]]}{'...' if len(pages) > 5 else ''}")

    return pages_by_agent


def test_llm_orchestrator():
    """Test LLM orchestrator with sample section map."""

    # Sample section map (simulating vision_sectionizer output)
    section_map = {
        "level_1": [
            {"title": "förvaltningsberättelse", "start_page": 1, "end_page": 5},
            {"title": "resultaträkning", "start_page": 6, "end_page": 7},
            {"title": "balansräkning", "start_page": 8, "end_page": 9},
            {"title": "noter", "start_page": 10, "end_page": 15},
            {"title": "revisionsberättelse", "start_page": 16, "end_page": 17},
        ],
        "level_2": [
            {"parent": "förvaltningsberättelse", "title": "styrelsen", "start_page": 2, "end_page": 3},
            {"parent": "noter", "title": "not 5 långfristiga skulder", "start_page": 12, "end_page": 13},
        ],
        "level_3": []
    }

    print("=" * 80)
    print("LLM ORCHESTRATOR TEST")
    print("=" * 80)

    try:
        pages_by_agent = llm_orchestrate_sections(section_map, verbose=True)

        print("\n" + "=" * 80)
        print("ROUTING RESULTS")
        print("=" * 80)

        for agent_id, pages in pages_by_agent.items():
            print(f"\n{agent_id}:")
            print(f"  Pages (0-indexed): {pages}")
            print(f"  Pages (1-indexed): {[p+1 for p in pages]}")

        print("\n✅ Test completed successfully")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_orchestrator()
