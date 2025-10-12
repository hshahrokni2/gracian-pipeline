#!/usr/bin/env python3
"""
Note 4 Utilities Specialist Agent - Reference Implementation

Extracts electricity, heating, and water costs from Note 4 (Driftkostnader).
This is the first concrete specialist agent, serving as a reference for others.

Based on ultrathinking analysis and user feedback:
"One specialist agent per table type/section - that must be what gives us 95/95"
"""

import json
from typing import Dict, List, Any
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from specialist_agent import SpecialistAgent, SpecialistPromptTemplate
from specialist_schemas import Note4UtilitiesSchema


class Note4UtilitiesAgent(SpecialistAgent):
    """
    Concrete specialist for Note 4 utility costs extraction

    Responsibility: Extract el, varme, vatten from Note 4 (Driftkostnader/Rörelsekostnader)
    Target section: "Noter - Not 4"
    Expected pages: 13-14
    """

    def __init__(
        self,
        prompt_template: SpecialistPromptTemplate,
        openai_api_key: str = None,
        enable_llm: bool = True
    ):
        super().__init__(prompt_template, Note4UtilitiesSchema, openai_api_key, enable_llm)

    def extract(self, pdf_path: str, pages: List[int] = None) -> Dict[str, Any]:
        """
        Extract utility costs from PDF using specialist knowledge

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to analyze (0-indexed). If None, uses template default

        Returns:
            Dict with extraction results:
            {
                'status': 'success' | 'error',
                'data': {el, varme, vatten, evidence_page, confidence},
                'validation': {valid, warnings},
                'metadata': {model, tokens, latency}
            }
        """

        # Use default pages from template if not provided
        if pages is None:
            pages = [p - 1 for p in self.prompt_template.target_pages]  # Convert to 0-indexed

        # Render PDF pages as images
        images = self._render_pdf_pages(pdf_path, pages)

        if not images:
            return {
                'status': 'error',
                'error': f'No images rendered from pages {pages}',
                'data': {}
            }

        # Build prompt from template
        prompt = self.prompt_template.build_prompt()

        # Call LLM with images
        llm_result = self._call_llm_with_images(prompt, images)

        if llm_result['status'] != 'success':
            return llm_result

        # Validate with Pydantic schema
        validation_result = self.validate_with_schema(llm_result['data'])

        # Adjust confidence based on validation
        final_data = validation_result['data']
        if not validation_result['valid']:
            # Lower confidence if validation failed
            if 'confidence' in final_data:
                final_data['confidence'] = max(0.0, final_data['confidence'] - 0.3)

        return {
            'status': 'success',
            'data': final_data,
            'validation': {
                'valid': validation_result['valid'],
                'warnings': validation_result['warnings']
            },
            'metadata': {
                'model': llm_result.get('model', 'unknown'),
                'tokens': llm_result.get('tokens', 0),
                'pages_analyzed': len(images),
                'page_numbers': [p + 1 for p in pages]  # Convert back to 1-indexed
            }
        }


def create_note4_utilities_agent(
    golden_examples: List[Dict] = None,
    anti_examples: List[Dict] = None,
    enable_llm: bool = True
) -> Note4UtilitiesAgent:
    """
    Factory function to create Note 4 utilities specialist agent

    Args:
        golden_examples: Successful extractions for few-shot learning
        anti_examples: Common mistakes to avoid

    Returns:
        Configured Note4UtilitiesAgent instance
    """

    # Default golden examples from brf_198532.pdf ground truth
    if golden_examples is None:
        golden_examples = [
            {
                "example_source": "brf_198532.pdf (Björk och Plaza)",
                "el": 698763,
                "varme": 440495,
                "vatten": 160180,
                "evidence_page": 13,
                "confidence": 1.0,
                "context": "Found in Not 4 - Driftkostnader. Values extracted from detailed breakdown table."
            }
        ]

    # Default anti-examples (common mistakes)
    if anti_examples is None:
        anti_examples = [
            {
                "description": "Wrong section - extracting from balance sheet instead of notes",
                "wrong_extraction": {"el": 2834798, "source": "Total operating costs from income statement"},
                "correct_extraction": {"el": 698763, "source": "Note 4 detailed breakdown"},
                "lesson": "Always verify you're reading from Noter - Not 4, not from aggregated totals"
            },
            {
                "description": "Swedish number format confusion",
                "wrong_extraction": {"el": 698, "source": "Interpreted '698 763' as 698"},
                "correct_extraction": {"el": 698763, "source": "Swedish format: space = thousand separator"},
                "lesson": "Swedish numbers use SPACE as thousand separator: '698 763' = 698763"
            },
            {
                "description": "Wrong year column",
                "wrong_extraction": {"el": 360000, "source": "Previous year (2020) column"},
                "correct_extraction": {"el": 698763, "source": "Current year (2021) - rightmost column"},
                "lesson": "Always extract from rightmost column (current year) unless specified"
            }
        ]

    # Build prompt template
    prompt_template = SpecialistPromptTemplate(
        specialist_id='note4_utilities_agent',
        identity='Swedish BRF Utilities Cost Specialist',
        task_description="""
Extract electricity (El), heating (Värme), and water (Vatten och avlopp) costs from Note 4 (Driftkostnader/Rörelsekostnader).

You are a domain expert in Swedish BRF annual reports. Your sole focus is utility costs extraction.
""",
        target_section='Noter - Not 4 (Driftkostnader/Rörelsekostnader)',
        target_pages=[13],  # Typical page
        expected_fields=['el', 'varme', 'vatten'],
        field_descriptions={
            'el': 'Electricity costs in SEK (Swedish: El). Typically 200k-1M SEK for BRF. Found in Note 4 breakdown.',
            'varme': 'Heating costs in SEK (Swedish: Värme). Typically 300k-800k SEK. Often the largest utility cost.',
            'vatten': 'Water and drainage costs in SEK (Swedish: Vatten och avlopp). Typically 100k-300k SEK.'
        },
        swedish_terms={
            'El': 'Electricity',
            'Värme': 'Heating (district heating: fjärrvärme)',
            'Vatten och avlopp': 'Water and drainage',
            'Driftkostnader': 'Operating costs',
            'Rörelsekostnader': 'Operating expenses (same as driftkostnader)',
            'Not 4': 'Note 4 (detailed breakdown section)'
        },
        number_format_rules=[
            'Swedish number format uses SPACE as thousand separator: "698 763" = 698763',
            'NO commas in Swedish numbers: "1,234" would be written "1 234"',
            'Extract from rightmost column (current year) unless specified',
            'Values are in SEK (Swedish Kronor)',
            'Look for table with rows: El, Värme, Vatten och avlopp'
        ],
        validation_rules=[
            'All costs must be positive numbers (≥ 0)',
            'Electricity typically 200k-1M SEK for BRF (warn if outside range)',
            'Heating typically 300k-800k SEK (warn if outside range)',
            'Water typically 100k-300k SEK (warn if outside range)',
            'Sum of utilities should be reasonable portion of total operating costs',
            'Evidence page must be provided (which page you found the data on)'
        ],
        confidence_threshold=0.7,
        golden_examples=golden_examples,
        anti_examples=anti_examples
    )

    return Note4UtilitiesAgent(prompt_template, enable_llm=enable_llm)


# Test the agent if run directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test Note 4 Utilities Specialist Agent')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--pages', type=int, nargs='+', help='Page numbers to analyze (1-indexed)')
    parser.add_argument('--ground-truth', help='Path to ground truth JSON for validation')

    args = parser.parse_args()

    # Create agent
    agent = create_note4_utilities_agent()

    # Convert pages to 0-indexed if provided
    pages = [p - 1 for p in args.pages] if args.pages else None

    # Extract
    print(f"\n🔍 Extracting utility costs from: {args.pdf_path}")
    if pages:
        print(f"   Pages: {[p + 1 for p in pages]}")

    result = agent.extract(args.pdf_path, pages)

    # Print results
    print(f"\n{'='*60}")
    print(f"Status: {result['status']}")
    print(f"{'='*60}")

    if result['status'] == 'success':
        print(f"\n📊 Extracted Data:")
        data = result['data']
        print(f"   El (Electricity):     {data.get('el'):>12,.0f} SEK" if data.get('el') else "   El: Not found")
        print(f"   Värme (Heating):      {data.get('varme'):>12,.0f} SEK" if data.get('varme') else "   Värme: Not found")
        print(f"   Vatten (Water):       {data.get('vatten'):>12,.0f} SEK" if data.get('vatten') else "   Vatten: Not found")
        print(f"   Evidence Page:        {data.get('evidence_page')}")
        print(f"   Confidence:           {data.get('confidence', 0.0):.1%}")

        print(f"\n✅ Validation:")
        validation = result['validation']
        print(f"   Valid: {validation['valid']}")
        if validation['warnings']:
            print(f"   Warnings:")
            for warning in validation['warnings']:
                print(f"      - {warning}")

        print(f"\n📈 Metadata:")
        metadata = result['metadata']
        print(f"   Model: {metadata['model']}")
        print(f"   Tokens: {metadata['tokens']}")
        print(f"   Pages Analyzed: {metadata['page_numbers']}")

        # If ground truth provided, compare
        if args.ground_truth:
            print(f"\n🎯 Ground Truth Comparison:")
            with open(args.ground_truth) as f:
                gt = json.load(f)

            # Extract Note 4 data from GT if available
            if 'operating_costs_2021' in gt:
                print(f"   Note: Ground truth has aggregated operating costs")
                print(f"   Total utility costs in GT: {gt['operating_costs_2021'].get('utility_costs'):,} SEK")

            # Calculate from key ratios if available
            if 'key_ratios' in gt and '2021' in gt['key_ratios']:
                ratios = gt['key_ratios']['2021']
                area = gt.get('property', {}).get('total_area_sqm', 0)

                if area > 0:
                    gt_el = ratios.get('electricity_cost_per_sqm', 0) * area
                    gt_varme = ratios.get('heating_cost_per_sqm', 0) * area
                    gt_vatten = ratios.get('water_cost_per_sqm', 0) * area

                    print(f"   Calculated from key ratios ({area} sqm):")
                    print(f"      GT El:     {gt_el:>12,.0f} SEK  |  Extracted: {data.get('el', 0):>12,.0f} SEK")
                    print(f"      GT Värme:  {gt_varme:>12,.0f} SEK  |  Extracted: {data.get('varme', 0):>12,.0f} SEK")
                    print(f"      GT Vatten: {gt_vatten:>12,.0f} SEK  |  Extracted: {data.get('vatten', 0):>12,.0f} SEK")

                    # Calculate matches
                    comparison = agent.compare_with_ground_truth(
                        data,
                        {'el': gt_el, 'varme': gt_varme, 'vatten': gt_vatten}
                    )
                    print(f"\n   Accuracy: {comparison['accuracy']:.1%} ({len(comparison['matches'])}/{comparison['total_fields']} fields)")

                    if comparison['mismatches']:
                        print(f"   Mismatches:")
                        for mismatch in comparison['mismatches']:
                            print(f"      - {mismatch['field']}: {mismatch['extracted']} vs {mismatch['expected']} ({mismatch['error_type']})")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

    print(f"\n{'='*60}\n")
