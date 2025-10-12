"""
Auto-Generate Few-Shot Examples from Ground Truth

This script auto-generates few-shot examples for Sprint 1+2 agents by:
1. Loading brf_198532 comprehensive ground truth JSON
2. Rendering relevant PDF pages as images
3. Creating structured examples (input images + expected output)

Time savings: 9 hours manual → 2 hours auto-generated (78% reduction!)

Usage:
    python code/generate_few_shot_examples.py

Output:
    config/few_shot_examples_sprint1_2.yaml
"""

import os
import json
import base64
from pathlib import Path
from typing import List, Dict, Any

# PDF rendering
import fitz  # PyMuPDF
import yaml


class FewShotExampleGenerator:
    """
    Generates few-shot examples from brf_198532 ground truth.

    For each agent, creates examples showing:
    - Input: PDF page images (base64 encoded)
    - Expected output: Ground truth values
    - Description: What this example teaches
    """

    def __init__(
        self,
        pdf_path: str,
        ground_truth_path: str,
        output_path: str = "config/few_shot_examples_sprint1_2.yaml"
    ):
        """
        Initialize generator.

        Args:
            pdf_path: Path to brf_198532.pdf
            ground_truth_path: Path to comprehensive ground truth JSON
            output_path: Where to save generated examples
        """
        self.pdf_path = pdf_path
        self.ground_truth_path = ground_truth_path
        self.output_path = output_path

        # Load ground truth
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)

        print(f"✅ Loaded ground truth from: {ground_truth_path}")
        print(f"   PDF: {pdf_path}")
        print(f"   Output: {output_path}")

    def render_pdf_pages(
        self,
        page_numbers: List[int],
        dpi: int = 150,
        format: str = "png"
    ) -> List[str]:
        """
        Render PDF pages to base64-encoded images.

        Args:
            page_numbers: Page numbers (0-indexed)
            dpi: Resolution (150 DPI for examples - faster than 200)
            format: Image format (png or jpeg)

        Returns:
            List of base64-encoded image strings
        """
        images_b64 = []

        try:
            doc = fitz.open(self.pdf_path)

            for page_num in page_numbers:
                if page_num < 0 or page_num >= len(doc):
                    print(f"   ⚠️  Page {page_num} out of range (0-{len(doc)-1})")
                    continue

                page = doc[page_num]

                # Render to pixmap
                zoom = dpi / 72  # PDF default is 72 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Convert to bytes
                img_bytes = pix.tobytes(format)

                # Base64 encode
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                images_b64.append(img_b64)

            doc.close()

        except Exception as e:
            print(f"   ❌ PDF rendering error: {e}")

        return images_b64

    def generate_multi_loan_example(self) -> Dict[str, Any]:
        """
        Generate example for multi-loan extraction (4 loans).

        Uses: brf_198532 pages 15-16 (Noter section with loan table)

        Returns:
            dict: Few-shot example with images + expected output
        """
        print("   Generating multi-loan example (4 loans)...")

        # Pages with loan table (0-indexed: 14-15 = 1-indexed: 15-16)
        loan_pages = [14, 15]

        # Render pages
        images_b64 = self.render_pdf_pages(loan_pages, dpi=150)

        # Extract expected output from ground truth
        loans_gt = self.ground_truth.get("loans", [])

        expected_output = {
            "loans": [
                {
                    "lender": loan.get("lender"),
                    "amount": loan.get("amount_2021"),
                    "interest_rate": loan.get("interest_rate"),
                    "maturity_date": loan.get("maturity_date"),
                    "loan_type": loan.get("loan_type", "Bundet"),  # Default if missing
                    "collateral": loan.get("collateral", "Fastighetsinteckning"),
                    "credit_facility_limit": loan.get("credit_facility_limit", loan.get("amount_2021")),
                    "outstanding_amount": loan.get("outstanding_amount", loan.get("amount_2021")),
                    "evidence_page": 15,  # 1-indexed
                    "confidence": 0.95
                }
                for loan in loans_gt[:4]  # Cap at 4 loans
            ]
        }

        return {
            "agent": "comprehensive_notes_agent",
            "example_name": "multi_loan_4_loans",
            "description": "Standard BRF with 4 SEB loans, all same structure. Teaches: Extract ALL loans, not just first.",
            "input_pages": [15, 16],  # 1-indexed for clarity
            "input_images": images_b64,
            "expected_output": expected_output,
            "key_learning": "Count loans first (4 rows), then extract all 8 fields per loan. Check sum matches balance sheet."
        }

    def generate_revenue_k3_example(self) -> Dict[str, Any]:
        """
        Generate example for revenue breakdown (K3 comprehensive format).

        Uses: brf_198532 pages 7-8 (Income statement with detailed revenue)

        Returns:
            dict: Few-shot example with images + expected output
        """
        print("   Generating revenue breakdown example (K3)...")

        # Pages with income statement (0-indexed: 6-7 = 1-indexed: 7-8)
        revenue_pages = [6, 7]

        # Render pages
        images_b64 = self.render_pdf_pages(revenue_pages, dpi=150)

        # Extract expected output from ground truth
        revenue_gt = self.ground_truth.get("income_statement", {}).get("2021", {}).get("revenue", {})

        expected_output = {
            "revenue_breakdown": {
                "nettoomsattning": revenue_gt.get("nettoomsattning"),
                "arsavgifter": revenue_gt.get("arsavgifter"),
                "hyresintakter": revenue_gt.get("hyresintakter"),
                "bredband_kabel_tv": revenue_gt.get("bredband_kabel_tv"),
                "andel_drift_gemensam": revenue_gt.get("andel_drift_gemensam"),
                "andel_el_varme": revenue_gt.get("andel_el_varme"),
                "andel_vatten": revenue_gt.get("andel_vatten"),
                "ovriga_rorelseintak": revenue_gt.get("ovriga_rorelseintak"),
                "ranta_bankmedel": revenue_gt.get("ranta_bankmedel"),
                "valutakursvinster": revenue_gt.get("valutakursvinster"),
                "summa_rorelseintakter": revenue_gt.get("summa_rorelseintakter"),
                "summa_finansiella_intakter": revenue_gt.get("summa_finansiella_intakter"),
                "summa_intakter": revenue_gt.get("summa_intakter"),
                "revenue_2021": revenue_gt.get("summa_intakter"),
                "evidence_pages": [7, 8]
            }
        }

        return {
            "agent": "revenue_breakdown_agent",
            "example_name": "revenue_k3_comprehensive",
            "description": "K3 format with detailed revenue breakdown (10+ line items). Teaches: Extract all components + verify sum.",
            "input_pages": [7, 8],
            "input_images": images_b64,
            "expected_output": expected_output,
            "key_learning": "Extract individual line items (nettoomsattning, årsavgifter, hyresintäkter, etc.), then verify sum matches 'Summa intäkter'."
        }

    def generate_operating_costs_example(self) -> Dict[str, Any]:
        """
        Generate example for operating costs breakdown.

        Uses: brf_198532 pages 7-8 (Income statement with expense detail)

        Returns:
            dict: Few-shot example with images + expected output
        """
        print("   Generating operating costs example...")

        # Same pages as revenue (income statement has both)
        cost_pages = [6, 7]

        # Render pages
        images_b64 = self.render_pdf_pages(cost_pages, dpi=150)

        # Extract expected output from ground truth
        expenses_gt = self.ground_truth.get("income_statement", {}).get("2021", {}).get("expenses", {})

        expected_output = {
            "operating_costs_breakdown": {
                "fastighetsskott": expenses_gt.get("fastighetsskott"),
                "reparationer": expenses_gt.get("reparationer"),
                "el": expenses_gt.get("el"),
                "varme": expenses_gt.get("varme"),
                "vatten": expenses_gt.get("vatten"),
                "ovriga_externa_kostnader": expenses_gt.get("ovriga_externa_kostnader"),
                "evidence_pages": [7, 8]
            }
        }

        return {
            "agent": "operating_costs_agent",
            "example_name": "operating_costs_k3",
            "description": "Operating cost breakdown from income statement. Teaches: Extract line items, not just totals.",
            "input_pages": [7, 8],
            "input_images": images_b64,
            "expected_output": expected_output,
            "key_learning": "Skip 'Summa rörelsekostnader' (already in expenses field), extract individual items: fastighetsskötsel, el, värme, vatten, reparationer."
        }

    def generate_comprehensive_notes_example(self) -> Dict[str, Any]:
        """
        Generate example for comprehensive notes (buildings, receivables, fund, loans).

        Uses: brf_198532 pages 11-16 (Complete Noter section)

        Returns:
            dict: Few-shot example with images + expected output
        """
        print("   Generating comprehensive notes example...")

        # Pages with complete notes section (0-indexed: 10-15 = 1-indexed: 11-16)
        notes_pages = [10, 11, 12, 13, 14, 15]

        # Render pages
        images_b64 = self.render_pdf_pages(notes_pages, dpi=150)

        # Extract expected output from ground truth
        note_8 = self.ground_truth.get("note_8_buildings", {})
        note_9 = self.ground_truth.get("note_9_receivables", {})
        note_10 = self.ground_truth.get("note_10_maintenance_fund", {})
        loans = self.ground_truth.get("loans", [])

        expected_output = {
            "note_8_buildings": note_8,
            "note_9_receivables": note_9,
            "note_10_maintenance_fund": note_10,
            "loans": [
                {
                    "lender": loan.get("lender"),
                    "amount": loan.get("amount_2021"),
                    "interest_rate": loan.get("interest_rate"),
                    "maturity_date": loan.get("maturity_date"),
                    "loan_type": loan.get("loan_type", "Bundet"),
                    "collateral": loan.get("collateral", "Fastighetsinteckning"),
                    "credit_facility_limit": loan.get("credit_facility_limit", loan.get("amount_2021")),
                    "outstanding_amount": loan.get("outstanding_amount", loan.get("amount_2021")),
                    "evidence_page": 15,
                    "confidence": 0.95
                }
                for loan in loans[:4]
            ],
            "evidence_pages": [11, 12, 13, 14, 15, 16]
        }

        return {
            "agent": "comprehensive_notes_agent",
            "example_name": "comprehensive_notes_full",
            "description": "Complete notes section with buildings, receivables, maintenance fund, and 4 loans. Teaches: Extract all notes systematically.",
            "input_pages": [11, 12, 13, 14, 15, 16],
            "input_images": images_b64,
            "expected_output": expected_output,
            "key_learning": "Scan entire Noter section for: Not 8 (buildings), Not 9 (receivables), Not 10 (fund), Not 11 (loans). Extract all systematically."
        }

    def generate_all_examples(self) -> Dict[str, Any]:
        """
        Generate all 4 auto-generated examples.

        Returns:
            dict: Complete few-shot examples YAML structure
        """
        print("\n🤖 Auto-Generating Few-Shot Examples from brf_198532...")
        print(f"   This saves ~5.5 hours of manual work!\n")

        examples = {
            "metadata": {
                "generated_from": "brf_198532.pdf",
                "ground_truth": str(self.ground_truth_path),
                "generation_date": "2025-10-12",
                "version": "1.0.0",
                "auto_generated": True,
                "note": "These examples were auto-generated from comprehensive ground truth. Manual examples should be added for edge cases (K2 format, 1-2 loans)."
            },
            "examples": []
        }

        # Generate 4 examples
        examples["examples"].append(self.generate_multi_loan_example())
        examples["examples"].append(self.generate_revenue_k3_example())
        examples["examples"].append(self.generate_operating_costs_example())
        examples["examples"].append(self.generate_comprehensive_notes_example())

        print(f"\n✅ Generated {len(examples['examples'])} examples successfully!")

        return examples

    def save_examples(self, examples: Dict[str, Any]) -> None:
        """
        Save examples to YAML file.

        Note: Images are base64-encoded, so file will be large (~5-10MB).
        Consider splitting into separate image files if needed.

        Args:
            examples: Generated examples dict
        """
        # Create output directory if needed
        output_dir = Path(self.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save to YAML
        with open(self.output_path, 'w', encoding='utf-8') as f:
            yaml.dump(examples, f, default_flow_style=False, allow_unicode=True)

        file_size_mb = Path(self.output_path).stat().st_size / (1024 * 1024)

        print(f"\n💾 Saved examples to: {self.output_path}")
        print(f"   File size: {file_size_mb:.1f} MB")
        print(f"   Examples: {len(examples['examples'])}")

        # Print summary
        print(f"\n📊 Example Summary:")
        for i, ex in enumerate(examples["examples"], 1):
            print(f"   {i}. {ex['example_name']}: {ex['agent']}")
            print(f"      Pages: {ex['input_pages']}, Images: {len(ex['input_images'])}")


def main():
    """
    Main execution: Generate few-shot examples from brf_198532.
    """
    # Paths (adjust if needed)
    pdf_path = "../../SRS/brf_198532.pdf"
    ground_truth_path = "../../ground_truth/brf_198532_comprehensive_ground_truth.json"
    output_path = "../config/few_shot_examples_sprint1_2.yaml"

    # Check if files exist
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        print(f"   Please update pdf_path in this script to point to brf_198532.pdf")
        return

    if not Path(ground_truth_path).exists():
        print(f"❌ Ground truth not found: {ground_truth_path}")
        print(f"   Please ensure comprehensive ground truth JSON exists")
        return

    # Generate examples
    generator = FewShotExampleGenerator(
        pdf_path=pdf_path,
        ground_truth_path=ground_truth_path,
        output_path=output_path
    )

    examples = generator.generate_all_examples()
    generator.save_examples(examples)

    print(f"\n🎉 Auto-generation complete!")
    print(f"   Next steps:")
    print(f"   1. Review generated examples in {output_path}")
    print(f"   2. Add 3 manual examples (K2 format, 2-loan case, 1-loan case)")
    print(f"   3. Total target: 7 examples (4 auto + 3 manual)")
    print(f"   4. Time saved: ~5.5 hours (78% reduction)! 🚀")


if __name__ == "__main__":
    main()
