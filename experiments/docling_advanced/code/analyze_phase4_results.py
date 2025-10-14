#!/usr/bin/env python3
"""Analyze Phase 4 results from optimal_result.json files"""
import json
import os
from pathlib import Path

# Validated PDFs
COMPLETED_PDFS = [
    "brf_268882",
    "brf_81563",
    "brf_53546",
    "brf_47903",
    "brf_57125",
    "brf_282765",
    "brf_54015",
]

results_dir = "results/phase4_validation"

print("="*80)
print("PHASE 4 RESULTS ANALYSIS (7/10 PDFs)")
print("="*80)

for pdf_name in COMPLETED_PDFS:
    result_file = os.path.join(results_dir, f"{pdf_name}_optimal_result.json")

    if not os.path.exists(result_file):
        print(f"\n❌ {pdf_name}: File not found")
        continue

    with open(result_file, 'r') as f:
        result = json.load(f)

    # Count populated fields
    populated = 0
    total = 0
    agent_results = result.get("agent_results", {})

    for agent_name, agent_data in agent_results.items():
        if isinstance(agent_data, dict) and agent_data.get("status") == "success":
            data = agent_data.get("data", {})
            for key, value in data.items():
                total += 1
                if value and value != "" and value != [] and value != {}:
                    populated += 1

    coverage = (populated / total * 100) if total > 0 else 0

    # Check for cross-agent fallback
    has_fallback = False
    if "✅ SCANNED PDF" in result.get("extraction_notes", ""):
        has_fallback = True

    print(f"\n{pdf_name}:")
    print(f"  Coverage: {populated}/{total} ({coverage:.1f}%)")
    print(f"  Agents: {len([a for a in agent_results.values() if isinstance(a, dict) and a.get('status') == 'success'])}")
    print(f"  Topology: {result.get('topology', {}).get('classification', 'unknown')}")
    if has_fallback:
        print(f"  🔄 Cross-agent fallback activated")

print("\n" + "="*80)
print(f"SUMMARY: {len(COMPLETED_PDFS)}/10 PDFs completed successfully")
print("="*80)
