#!/usr/bin/env python3
"""
Experiment 3A: Structure Detection Validation
Test if Docling can reliably detect sections on scanned Swedish BRF PDFs

Critical Question: Can we map document sections to agents WITHOUT full OCR?
Success Criteria: ≥80% of expected sections detected with identifiable headings
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling_core.types.doc import DoclingDocument, SectionHeaderItem, TextItem

TEST_PDF = "test_pdfs/brf_268882.pdf"

# Expected sections in a Swedish BRF annual report
EXPECTED_SECTIONS = [
    "Förvaltningsberättelse",  # Management report
    "Styrelse",                 # Board
    "Resultaträkning",          # Income statement
    "Balansräkning",            # Balance sheet
    "Kassaflödesanalys",        # Cash flow
    "Noter",                    # Notes
    "Revisionsberättelse",      # Audit report
]


class StructureDetectionTester:
    """Test Docling's ability to detect document structure"""

    def __init__(self):
        self.detected_sections = []
        self.section_headings = []

    def extract_structure(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract document structure using Docling with EasyOCR
        Returns structure metadata and headings
        """
        print("Step 1: Extracting document structure with Docling + EasyOCR...")

        # Use EasyOCR for Swedish text recognition
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = EasyOcrOptions(
            force_full_page_ocr=True,
            lang=["sv", "en"]
        )
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        import time
        start = time.time()
        result = converter.convert(pdf_path)
        elapsed = time.time() - start

        doc: DoclingDocument = result.document

        print(f"✓ Structure extraction complete in {elapsed:.1f}s")
        print()

        # Extract sections from the document
        sections = []
        section_headings = []

        # Iterate through document items
        for item, level in doc.iterate_items():
            if isinstance(item, SectionHeaderItem):
                section_info = {
                    "heading": item.text,
                    "level": level,
                    "page": getattr(item, 'page', None),
                }
                sections.append(section_info)
                section_headings.append(item.text.lower())

                print(f"📑 Found section: \"{item.text}\" (level {level})")

        print()
        print(f"Total sections detected: {len(sections)}")
        print()

        self.detected_sections = sections
        self.section_headings = section_headings

        return {
            "extraction_time": elapsed,
            "num_sections": len(sections),
            "sections": sections,
            "markdown": doc.export_to_markdown()[:2000],  # First 2000 chars
        }

    def evaluate_section_detection(self) -> Dict[str, Any]:
        """
        Evaluate if detected sections match expected BRF structure
        """
        print("=" * 70)
        print("SECTION DETECTION EVALUATION")
        print("=" * 70)
        print()

        matches = []

        for expected in EXPECTED_SECTIONS:
            found = False
            matched_section = None

            # Check if any detected heading contains the expected term
            for i, heading in enumerate(self.section_headings):
                if expected.lower() in heading:
                    found = True
                    matched_section = self.detected_sections[i]
                    break

            status = "✅" if found else "❌"
            matches.append({
                "expected": expected,
                "found": found,
                "matched_heading": matched_section['heading'] if matched_section else None
            })

            if found:
                print(f"  {status} {expected}: Found as \"{matched_section['heading']}\"")
            else:
                print(f"  {status} {expected}: NOT FOUND")

        print()

        detection_rate = sum(1 for m in matches if m['found']) / len(EXPECTED_SECTIONS)

        print(f"Detection Rate: {detection_rate:.1%} ({sum(1 for m in matches if m['found'])}/{len(EXPECTED_SECTIONS)})")
        print()

        if detection_rate >= 0.80:
            print("✅ SUCCESS: ≥80% sections detected")
            print("   → Structure detection is RELIABLE for section-based routing")
        elif detection_rate >= 0.60:
            print("⚠️ PARTIAL: 60-80% sections detected")
            print("   → May work with robust fallback strategy")
        else:
            print("❌ FAILURE: <60% sections detected")
            print("   → Fall back to strategic page sampling")

        print()

        return {
            "expected_sections": EXPECTED_SECTIONS,
            "matches": matches,
            "detection_rate": detection_rate,
            "success": detection_rate >= 0.80
        }

    def analyze_for_agent_routing(self) -> Dict[str, List[int]]:
        """
        Analyze detected sections to create agent routing map
        """
        print("=" * 70)
        print("AGENT ROUTING ANALYSIS")
        print("=" * 70)
        print()

        # Define mapping rules (Swedish terms → agent IDs)
        ROUTING_RULES = {
            "governance_agent": [
                "förvaltningsberättelse", "styrelse", "ordförande",
                "ledamot", "valberedning", "revisionsberättelse"
            ],
            "financial_agent": [
                "resultaträkning", "balansräkning", "kassaflödesanalys",
                "finansiell", "ekonomisk"
            ],
            "notes_agent": [
                "noter", "not ", "tilläggsupplysningar"
            ],
            "property_agent": [
                "fastighet", "byggnader", "mark", "lokaler"
            ],
            "fees_agent": [
                "avgift", "årsavgift", "månadsavgift"
            ],
        }

        agent_map = {}

        for agent_id, keywords in ROUTING_RULES.items():
            matching_pages = set()

            for section in self.detected_sections:
                heading_lower = section['heading'].lower()

                # Check if any keyword matches
                if any(kw in heading_lower for kw in keywords):
                    # Estimate page range (would need more sophisticated logic)
                    page = section.get('page')
                    if page is None:
                        # If page info not available, use section index as proxy
                        page = self.detected_sections.index(section) + 1
                    # Add page and surrounding pages (rough estimate)
                    matching_pages.update(range(max(1, page), page + 3))

            if matching_pages:
                agent_map[agent_id] = sorted(list(matching_pages))
                print(f"📌 {agent_id}: pages {agent_map[agent_id]}")

        print()

        if len(agent_map) >= 3:
            print("✅ SUCCESS: Sufficient sections mapped for routing")
        else:
            print("⚠️ WARNING: Limited section mapping - may need fallback")

        print()

        return agent_map

    def estimate_cost_savings(self, agent_map: Dict[str, List[int]]) -> Dict[str, float]:
        """
        Estimate cost savings from section-based routing vs naive approach
        """
        print("=" * 70)
        print("COST SAVINGS ESTIMATE")
        print("=" * 70)
        print()

        # Assume 13 agents total, 20 pages per document
        num_agents = 13
        total_pages = 20
        cost_per_page_agent = 0.005  # $0.005 per page per agent

        # Naive approach: all agents process all pages
        naive_cost = num_agents * total_pages * cost_per_page_agent

        # Section-aware: agents only process relevant pages
        total_page_agent_calls = 0
        for agent_id, pages in agent_map.items():
            total_page_agent_calls += len(pages)

        # Estimate unmapped agents (use fallback: 5 pages each)
        unmapped_agents = num_agents - len(agent_map)
        total_page_agent_calls += unmapped_agents * 5  # Conservative fallback

        section_aware_cost = total_page_agent_calls * cost_per_page_agent

        savings = naive_cost - section_aware_cost
        savings_pct = (savings / naive_cost) * 100 if naive_cost > 0 else 0

        print(f"Naive Approach:")
        print(f"  {num_agents} agents × {total_pages} pages = {num_agents * total_pages} page-agent calls")
        print(f"  Cost: ${naive_cost:.2f}")
        print()

        print(f"Section-Aware Approach:")
        print(f"  {len(agent_map)} mapped agents, {total_page_agent_calls} total page-agent calls")
        print(f"  Cost: ${section_aware_cost:.2f}")
        print()

        print(f"💰 Savings: ${savings:.2f} ({savings_pct:.0f}% reduction)")
        print()

        return {
            "naive_cost": naive_cost,
            "section_aware_cost": section_aware_cost,
            "savings_usd": savings,
            "savings_percent": savings_pct
        }


def run_experiment_3a():
    """Run Experiment 3A: Structure detection validation"""

    print("=" * 70)
    print("EXPERIMENT 3A: Structure Detection Validation")
    print("=" * 70)
    print(f"Test PDF: {TEST_PDF}")
    print(f"Goal: Validate section detection for routing optimization")
    print(f"Success Criteria: ≥80% expected sections detected")
    print()

    if not Path(TEST_PDF).exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        return

    tester = StructureDetectionTester()

    # Step 1: Extract structure
    structure_data = tester.extract_structure(TEST_PDF)

    # Step 2: Evaluate detection
    evaluation = tester.evaluate_section_detection()

    # Step 3: Analyze for routing
    agent_map = tester.analyze_for_agent_routing()

    # Step 4: Estimate savings
    cost_analysis = tester.estimate_cost_savings(agent_map)

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"results/exp3a_structure_detection_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "experiment": "Experiment 3A: Structure Detection Validation",
            "test_date": datetime.now().isoformat(),
            "pdf": TEST_PDF,
            "structure_data": structure_data,
            "evaluation": evaluation,
            "agent_routing_map": {k: v for k, v in agent_map.items()},
            "cost_analysis": cost_analysis,
            "recommendation": {
                "use_section_routing": evaluation['success'],
                "expected_savings": cost_analysis['savings_percent'],
                "confidence": "high" if evaluation['success'] else "medium"
            }
        }, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print("FINAL RECOMMENDATION")
    print("=" * 70)
    print()

    if evaluation['success']:
        print("✅ RECOMMENDATION: Use section-based routing")
        print(f"   Expected savings: {cost_analysis['savings_percent']:.0f}%")
        print(f"   Confidence: HIGH")
        print()
        print("Next steps:")
        print("1. Implement section-aware extraction pipeline")
        print("2. Test on 5-10 additional documents")
        print("3. Deploy to production with monitoring")
    else:
        print("⚠️ RECOMMENDATION: Use strategic page sampling fallback")
        print(f"   Reason: Only {evaluation['detection_rate']:.0%} sections detected")
        print()
        print("Next steps:")
        print("1. Implement fallback with BRF conventions")
        print("2. Consider manual section tagging for difficult documents")
        print("3. Re-evaluate with different PDF samples")

    print()
    print(f"💾 Results saved to: {output_file}")
    print()
    print("✅ Experiment 3A complete!")


if __name__ == "__main__":
    run_experiment_3a()
