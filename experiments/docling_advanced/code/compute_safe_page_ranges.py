#!/usr/bin/env python3
"""
Safe Page Ranges Computation - Day 5 Pre-Flight Tool #4

Pre-computes minimum safe MAX_PAGES values per agent based on Day 4 successful extractions.
These values act as "floor" to prevent coverage regression when optimizing MAX_PAGES.

Usage:
    python code/compute_safe_page_ranges.py
    python code/compute_safe_page_ranges.py --pdfs brf_198532.pdf brf_268882.pdf brf_271852.pdf

Output:
    results/safe_page_ranges.json
    {
        "governance_agent": {
            "min_pages": 6,
            "recommended_pages": 8,
            "rationale": "Governance data found on pages 1-3, 17. Need first 3 + signature page."
        },
        "financial_agent": {
            "min_pages": 12,
            "recommended_pages": 16,
            "rationale": "Balance sheet spans pages 9-11, need context pages."
        },
        ...
    }

Day 5 Usage:
    When reducing MAX_PAGES, never go below min_pages to avoid regression.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from dataclasses import dataclass

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))

from optimal_brf_pipeline import OptimalBRFPipeline


@dataclass
class AgentPageAnalysis:
    """Analysis of pages needed by an agent"""
    agent_id: str
    pages_used: List[int]
    pages_with_extractions: List[int]
    min_page: int
    max_page: int
    min_pages_needed: int
    recommended_pages: int
    rationale: str
    confidence: float


def analyze_agent_pages(
    agent_id: str,
    agent_results: List[Dict],
    pdf_page_counts: List[int]
) -> AgentPageAnalysis:
    """
    Analyze minimum pages needed for an agent across multiple PDFs.

    Args:
        agent_id: Agent identifier
        agent_results: List of agent results from different PDFs
        pdf_page_counts: Page counts of analyzed PDFs

    Returns:
        AgentPageAnalysis with safe page ranges
    """
    all_pages = set()
    extraction_pages = set()

    # Aggregate pages across all PDFs
    for result in agent_results:
        if result.get('status') == 'success' and result.get('data'):
            pages_rendered = result.get('pages_rendered', [])
            all_pages.update(pages_rendered)

            # Identify pages that contributed to successful extractions
            evidence_pages = result.get('evidence_pages', [])
            if evidence_pages:
                extraction_pages.update(evidence_pages)

    if not all_pages:
        # No successful extractions - use conservative defaults
        return AgentPageAnalysis(
            agent_id=agent_id,
            pages_used=[],
            pages_with_extractions=[],
            min_page=0,
            max_page=0,
            min_pages_needed=8,  # Conservative default
            recommended_pages=12,
            rationale="No successful extractions - using conservative defaults",
            confidence=0.3
        )

    # Calculate minimum pages needed
    min_page = min(all_pages) if all_pages else 1
    max_page = max(all_pages) if all_pages else 1
    page_range = max_page - min_page + 1

    # Add buffer for context (empirically 20-30% buffer is safe)
    buffer = max(2, int(page_range * 0.25))
    recommended_pages = page_range + buffer

    # Generate rationale
    if extraction_pages:
        page_list = sorted(extraction_pages)[:5]  # Show first 5
        rationale = f"Successful extractions from pages {page_list}. Range: {min_page}-{max_page}. Buffer: +{buffer} pages."
        confidence = 0.9
    else:
        rationale = f"Agent used pages {min_page}-{max_page}. No evidence pages tracked. Conservative estimate."
        confidence = 0.6

    return AgentPageAnalysis(
        agent_id=agent_id,
        pages_used=sorted(all_pages),
        pages_with_extractions=sorted(extraction_pages),
        min_page=min_page,
        max_page=max_page,
        min_pages_needed=page_range,
        recommended_pages=recommended_pages,
        rationale=rationale,
        confidence=confidence
    )


def compute_safe_ranges(pdf_paths: List[str]) -> Dict[str, Any]:
    """
    Compute safe page ranges across multiple PDFs.

    Args:
        pdf_paths: List of PDF paths to analyze

    Returns:
        Dict with safe page ranges per agent
    """
    print(f"\n{'='*80}")
    print(f"COMPUTING SAFE PAGE RANGES")
    print(f"Analyzing {len(pdf_paths)} PDFs")
    print(f"{'='*80}\n")

    # Run extraction on all PDFs
    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/safe_page_analysis",
        enable_caching=True
    )

    agent_results = defaultdict(list)
    pdf_page_counts = []

    for pdf_path in pdf_paths:
        print(f"📄 Analyzing {Path(pdf_path).name}...")

        try:
            result = pipeline.extract_document(pdf_path)
            pdf_page_counts.append(result.topology.total_pages)

            # Collect agent results
            all_agents = {**result.pass1_result, **result.pass2_result}
            for agent_id, agent_result in all_agents.items():
                agent_results[agent_id].append(agent_result)

            print(f"   ✅ Extracted ({result.quality_metrics.get('coverage', 0):.1%} coverage)")

        except Exception as e:
            print(f"   ⚠️ Error: {e}")

    pipeline.close()

    print(f"\n{'─'*80}")
    print(f"ANALYZING AGENT PAGE REQUIREMENTS")
    print(f"{'─'*80}\n")

    # Analyze each agent
    safe_ranges = {}

    for agent_id, results in agent_results.items():
        analysis = analyze_agent_pages(agent_id, results, pdf_page_counts)

        safe_ranges[agent_id] = {
            'min_pages': analysis.min_pages_needed,
            'recommended_pages': analysis.recommended_pages,
            'pages_with_evidence': analysis.pages_with_extractions,
            'page_range': f"{analysis.min_page}-{analysis.max_page}",
            'rationale': analysis.rationale,
            'confidence': analysis.confidence
        }

        # Print summary
        conf_emoji = "🟢" if analysis.confidence >= 0.8 else "🟡" if analysis.confidence >= 0.6 else "🔴"
        print(f"{conf_emoji} {agent_id}:")
        print(f"   • Min pages: {analysis.min_pages_needed}")
        print(f"   • Recommended: {analysis.recommended_pages}")
        print(f"   • Page range: {analysis.min_page}-{analysis.max_page}")
        print(f"   • Evidence pages: {len(analysis.pages_with_extractions)}")
        print(f"   • Confidence: {analysis.confidence:.0%}")
        print(f"   • Rationale: {analysis.rationale}\n")

    # Generate Day 5 optimization guidance
    print(f"{'='*80}")
    print(f"DAY 5 OPTIMIZATION GUIDANCE")
    print(f"{'='*80}\n")

    print("When optimizing MAX_PAGES on Day 5:\n")
    print("1. **Floor Values** (Never go below these):")
    for agent_id, ranges in sorted(safe_ranges.items()):
        print(f"   • {agent_id}: ≥{ranges['min_pages']} pages")

    print("\n2. **Recommended Starting Points** (Safe to test):")
    for agent_id, ranges in sorted(safe_ranges.items()):
        print(f"   • {agent_id}: {ranges['recommended_pages']} pages")

    print("\n3. **High-Confidence Optimizations** (Confidence ≥80%):")
    high_conf = [(a, r) for a, r in safe_ranges.items() if r['confidence'] >= 0.8]
    if high_conf:
        for agent_id, ranges in high_conf:
            print(f"   • {agent_id}: {ranges['min_pages']}-{ranges['recommended_pages']} pages (safe to optimize)")
    else:
        print("   • None - use conservative approach")

    print("\n4. **Caution Required** (Confidence <60%):")
    low_conf = [(a, r) for a, r in safe_ranges.items() if r['confidence'] < 0.6]
    if low_conf:
        for agent_id, ranges in low_conf:
            print(f"   • {agent_id}: Limited data - keep at {ranges['recommended_pages']}+ pages")
    else:
        print("   • None - all agents have good data")

    # Save results
    output_file = Path("results/safe_page_ranges.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'pdfs_analyzed': len(pdf_paths),
                'timestamp': str(Path(__file__).parent.parent / "DAY4_COMPLETE_SPRINT1_2.md"),
                'day4_baseline_coverage': 0.784
            },
            'safe_ranges': safe_ranges,
            'optimization_strategy': {
                'phase1_targets': {  # Day 5 Phase 1: Safe reductions
                    agent_id: max(ranges['min_pages'], ranges['recommended_pages'] - 2)
                    for agent_id, ranges in safe_ranges.items()
                    if ranges['confidence'] >= 0.8
                },
                'phase2_targets': {  # Day 5 Phase 2: Aggressive optimization
                    agent_id: ranges['min_pages']
                    for agent_id, ranges in safe_ranges.items()
                    if ranges['confidence'] >= 0.8
                }
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Safe page ranges saved to: {output_file}")
    print(f"\nUse these values on Day 5 to prevent coverage regression!")

    return safe_ranges


def main():
    parser = argparse.ArgumentParser(description='Compute safe page ranges for Day 5 optimization')
    parser.add_argument('--pdfs', nargs='+', help='PDF files to analyze')
    parser.add_argument('--baseline', action='store_true', help='Analyze Day 4 baseline PDFs')

    args = parser.parse_args()

    # Determine PDFs to analyze
    if args.baseline or not args.pdfs:
        # Day 4 baseline PDFs
        pdfs = [
            "../../SRS/brf_198532.pdf",      # Day 4 validation PDF (78.4% coverage)
            "test_pdfs/brf_268882.pdf",      # Day 4 test PDF
            "test_pdfs/brf_271852.pdf"       # Additional test PDF
        ]
    else:
        pdfs = args.pdfs

    # Verify PDFs exist
    valid_pdfs = []
    for pdf_path in pdfs:
        if Path(pdf_path).exists():
            valid_pdfs.append(pdf_path)
        else:
            print(f"⚠️  Warning: PDF not found: {pdf_path}")

    if not valid_pdfs:
        print("❌ Error: No valid PDFs found")
        sys.exit(1)

    # Compute safe ranges
    safe_ranges = compute_safe_ranges(valid_pdfs)

    print(f"\n✅ Safe page ranges computed successfully!")
    print(f"   Ready for Day 5 MAX_PAGES optimization")


if __name__ == '__main__':
    main()
