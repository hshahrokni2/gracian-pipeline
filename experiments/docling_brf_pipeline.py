#!/usr/bin/env python3
"""
Docling BRF Extraction Pipeline with Validation

Compares:
1. Docling + GPT-4o post-processing
2. Gracian Pipeline (vision_qc)
3. OpenAI Vision Direct

Goal: Achieve 95% coverage and 95% accuracy for BRF extraction.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from docling.document_converter import DocumentConverter
from gracian_pipeline.core.schema import EXPECTED_TYPES
from gracian_pipeline.core.vision_qc import vision_qc_agent, call_openai_vision, render_pdf_pages_subset
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS


class DoclingBRFExtractor:
    """Extract BRF data using Docling + LLM post-processing."""

    def __init__(self, output_dir: str = "experiments/docling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converter = DocumentConverter()

    def extract(self, pdf_path: str) -> Dict[str, Any]:
        """Extract with docling and map to BRF schema."""

        print(f"\n{'='*80}")
        print(f"📄 DOCLING EXTRACTION: {Path(pdf_path).name}")
        print(f"{'='*80}\n")

        # Convert PDF
        result = self.converter.convert(pdf_path)
        doc = result.document

        # Export to markdown (best for LLM processing)
        markdown = doc.export_to_markdown()
        json_export = doc.export_to_dict()

        print(f"✅ Docling extracted: {len(markdown)} chars, {len(json_export.get('tables', []))} tables")

        # If mostly images (scanned PDF), use note
        if len(markdown) < 500 and markdown.count("<!-- image -->") > 5:
            print("⚠️  Scanned PDF detected - docling extracted minimal text")
            return {
                "status": "scanned_pdf",
                "markdown": markdown,
                "note": "Docling doesn't OCR scanned PDFs effectively - use vision LLM instead"
            }

        # Use GPT-4o to extract structured BRF data from markdown
        brf_data = self._extract_brf_from_markdown(markdown, json_export)

        # Save outputs
        self._save_outputs(pdf_path, markdown, json_export, brf_data)

        return brf_data

    def _extract_brf_from_markdown(self, markdown: str, json_export: Dict) -> Dict[str, Any]:
        """Use GPT-4o to extract structured BRF fields from docling markdown."""

        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Comprehensive extraction prompt targeting all schema fields
        prompt = f"""You are extracting data from a Swedish BRF (housing cooperative) annual report.

DOCLING MARKDOWN OUTPUT:
{markdown[:12000]}

EXTRACT THE FOLLOWING (return as JSON):

**GOVERNANCE** (governance_agent):
- chairman: Name of board chairman (ordförande)
- board_members: List of all board member names
- auditor_name: Primary auditor name
- audit_firm: Auditing firm name
- nomination_committee: Nomination committee member names
- evidence_pages: Page numbers where found

**FINANCIAL** (financial_agent):
- revenue: Total revenue/intäkter (number)
- expenses: Total expenses/kostnader (number)
- assets: Total assets/tillgångar (number)
- liabilities: Total liabilities/skulder (number)
- equity: Equity/eget kapital (number)
- surplus: Surplus/överskott (number)
- evidence_pages: Page numbers

**PROPERTY** (property_agent):
- address: Property address
- construction_year: Year built (number)
- num_apartments: Number of apartments (number)
- area_sqm: Total area in square meters (number)
- evidence_pages: Page numbers

**NOTES** (notes_agent):
- revenue_notes: Revenue breakdown notes
- expense_notes: Expense breakdown notes
- other_notes: Other financial notes

Return ONLY valid JSON with this exact structure:
{{
  "governance_agent": {{}},
  "financial_agent": {{}},
  "property_agent": {{}},
  "notes_agent": {{}}
}}

Use null for missing values. Extract exact names and numbers."""

        try:
            print("🤖 Running GPT-4o extraction on docling markdown...")

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF document extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)

            # Print summary
            gov = result.get("governance_agent", {})
            fin = result.get("financial_agent", {})
            prop = result.get("property_agent", {})

            print(f"  ✅ Governance: Chairman={gov.get('chairman', 'N/A')}, Board={len(gov.get('board_members', []))} members")
            print(f"  ✅ Financial: Assets={fin.get('assets', 'N/A')}, Revenue={fin.get('revenue', 'N/A')}")
            print(f"  ✅ Property: {prop.get('address', 'N/A')}, {prop.get('num_apartments', 'N/A')} apartments")

            return result

        except Exception as e:
            print(f"  ❌ GPT-4o extraction error: {e}")
            return {
                "error": str(e),
                "governance_agent": {},
                "financial_agent": {},
                "property_agent": {},
                "notes_agent": {}
            }

    def _save_outputs(self, pdf_path: str, markdown: str, json_export: Dict, brf_data: Dict):
        """Save all extraction outputs."""

        pdf_name = Path(pdf_path).stem

        # Save markdown
        md_file = self.output_dir / f"{pdf_name}_docling.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        # Save raw JSON
        json_file = self.output_dir / f"{pdf_name}_docling_raw.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_export, f, indent=2, ensure_ascii=False)

        # Save BRF extraction
        brf_file = self.output_dir / f"{pdf_name}_docling_brf.json"
        with open(brf_file, 'w', encoding='utf-8') as f:
            json.dump(brf_data, f, indent=2, ensure_ascii=False)

        print(f"  💾 Saved: {md_file}, {json_file}, {brf_file}")


class ComparisonValidator:
    """Compare Docling vs Gracian Pipeline vs OpenAI Vision Direct."""

    def __init__(self, output_dir: str = "experiments/docling_results"):
        self.output_dir = Path(output_dir)

    def validate(self, pdf_path: str, docling_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run all three extraction methods and compare."""

        print(f"\n{'='*80}")
        print(f"🔬 VALIDATION: {Path(pdf_path).name}")
        print(f"{'='*80}\n")

        comparison = {
            "pdf": Path(pdf_path).name,
            "timestamp": datetime.now().isoformat(),
            "docling_postprocessed": docling_result,
            "gracian_pipeline": {},
            "openai_direct": {},
        }

        # Method 2: Gracian Pipeline
        print("🤖 Method 2: Gracian Pipeline (vision_qc_agent)...")
        try:
            gov_result, meta = vision_qc_agent(
                pdf_path,
                "governance_agent",
                AGENT_PROMPTS.get("governance_agent", "Extract governance"),
                page_indices=[0, 1, 2, 3]  # First 4 pages
            )
            comparison["gracian_pipeline"]["governance_agent"] = gov_result
            print(f"  ✅ Chairman: {gov_result.get('chairman', 'N/A')}, Board: {len(gov_result.get('board_members', []))} members")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            comparison["gracian_pipeline"]["governance_agent"] = {"error": str(e)}

        # Method 3: OpenAI Vision Direct
        print("\n🔍 Method 3: OpenAI Vision Direct...")
        try:
            images = render_pdf_pages_subset(pdf_path, [0, 1, 2, 3], dpi=220)

            vision_prompt = """Extract from this Swedish BRF annual report:

GOVERNANCE:
- Chairman name (ordförande)
- All board members (styrelseledamöter)
- Auditor name and firm (revisor)

FINANCIAL (if visible):
- Total assets (tillgångar)
- Total revenue (intäkter)
- Total expenses (kostnader)

PROPERTY (if visible):
- Address
- Number of apartments

Return as JSON with keys: chairman, board_members, auditor_name, audit_firm, assets, revenue, expenses, address, num_apartments"""

            openai_result = call_openai_vision(vision_prompt, images, page_labels=["Page 1", "Page 2", "Page 3", "Page 4"])

            try:
                openai_parsed = json.loads(openai_result)
                comparison["openai_direct"] = openai_parsed
                print(f"  ✅ Chairman: {openai_parsed.get('chairman', 'N/A')}, Assets: {openai_parsed.get('assets', 'N/A')}")
            except:
                comparison["openai_direct"] = {"raw": openai_result}

        except Exception as e:
            print(f"  ❌ Error: {e}")
            comparison["openai_direct"] = {"error": str(e)}

        # Save comparison
        comp_file = self.output_dir / f"{Path(pdf_path).stem}_comparison.json"
        with open(comp_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Comparison saved: {comp_file}")

        return comparison


class ReportGenerator:
    """Generate comprehensive comparison report."""

    def __init__(self, output_dir: str = "experiments/docling_results"):
        self.output_dir = Path(output_dir)

    def generate(self, all_comparisons: List[Dict[str, Any]]) -> str:
        """Generate markdown report."""

        report_path = self.output_dir / f"DOCLING_VALIDATION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            self._write_header(f, all_comparisons)
            self._write_summary(f, all_comparisons)
            self._write_detailed_comparison(f, all_comparisons)
            self._write_recommendations(f, all_comparisons)

        print(f"\n{'='*80}")
        print(f"📊 FINAL REPORT: {report_path}")
        print(f"{'='*80}\n")

        return str(report_path)

    def _write_header(self, f, comparisons):
        f.write("# Docling BRF Extraction - Validation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Test Documents**: {len(comparisons)}\n")
        f.write(f"- **Extraction Methods Compared**: 3 (Docling+GPT-4o, Gracian Pipeline, OpenAI Vision Direct)\n")
        f.write(f"- **Target**: 95% coverage, 95% accuracy\n\n")

    def _write_summary(self, f, comparisons):
        f.write("## High-Level Performance\n\n")

        # Calculate success rates
        metrics = {
            "docling": {"chairman": 0, "board_count": 0, "assets": 0, "total": len(comparisons)},
            "gracian": {"chairman": 0, "board_count": 0, "total": len(comparisons)},
            "openai": {"chairman": 0, "assets": 0, "total": len(comparisons)}
        }

        for comp in comparisons:
            # Docling metrics
            docling_gov = comp.get("docling_postprocessed", {}).get("governance_agent", {})
            if docling_gov.get("chairman"):
                metrics["docling"]["chairman"] += 1
            if len(docling_gov.get("board_members", [])) > 0:
                metrics["docling"]["board_count"] += 1

            docling_fin = comp.get("docling_postprocessed", {}).get("financial_agent", {})
            if docling_fin.get("assets"):
                metrics["docling"]["assets"] += 1

            # Gracian metrics
            gracian_gov = comp.get("gracian_pipeline", {}).get("governance_agent", {})
            if gracian_gov.get("chairman"):
                metrics["gracian"]["chairman"] += 1
            if len(gracian_gov.get("board_members", [])) > 0:
                metrics["gracian"]["board_count"] += 1

            # OpenAI metrics
            openai = comp.get("openai_direct", {})
            if openai.get("chairman"):
                metrics["openai"]["chairman"] += 1
            if openai.get("assets"):
                metrics["openai"]["assets"] += 1

        total = len(comparisons) if comparisons else 1  # Avoid division by zero

        f.write("| Method | Chairman Extracted | Board Members Found | Assets Extracted |\n")
        f.write("|--------|-------------------|---------------------|------------------|\n")
        f.write(f"| **Docling + GPT-4o** | {metrics['docling']['chairman']}/{total} ({metrics['docling']['chairman']/total*100:.0f}%) | {metrics['docling']['board_count']}/{total} ({metrics['docling']['board_count']/total*100:.0f}%) | {metrics['docling']['assets']}/{total} ({metrics['docling']['assets']/total*100:.0f}%) |\n")
        f.write(f"| **Gracian Pipeline** | {metrics['gracian']['chairman']}/{total} ({metrics['gracian']['chairman']/total*100:.0f}%) | {metrics['gracian']['board_count']}/{total} ({metrics['gracian']['board_count']/total*100:.0f}%) | N/A |\n")
        f.write(f"| **OpenAI Direct** | {metrics['openai']['chairman']}/{total} ({metrics['openai']['chairman']/total*100:.0f}%) | N/A | {metrics['openai']['assets']}/{total} ({metrics['openai']['assets']/total*100:.0f}%) |\n\n")

    def _write_detailed_comparison(self, f, comparisons):
        f.write("## Detailed Results\n\n")

        for i, comp in enumerate(comparisons, 1):
            pdf_name = comp["pdf"]
            f.write(f"### {i}. {pdf_name}\n\n")

            # Governance table
            f.write("#### Governance Fields\n\n")
            f.write("| Field | Docling+GPT-4o | Gracian Pipeline | OpenAI Direct |\n")
            f.write("|-------|----------------|------------------|---------------|\n")

            docling_gov = comp.get("docling_postprocessed", {}).get("governance_agent", {})
            gracian_gov = comp.get("gracian_pipeline", {}).get("governance_agent", {})
            openai_data = comp.get("openai_direct", {})

            for field in ["chairman", "auditor_name", "audit_firm"]:
                d_val = docling_gov.get(field, "N/A") or "N/A"
                g_val = gracian_gov.get(field, "N/A") or "N/A"
                o_val = openai_data.get(field, "N/A") or "N/A"
                f.write(f"| {field} | {d_val} | {g_val} | {o_val} |\n")

            # Board members count
            d_board = len(docling_gov.get("board_members", []))
            g_board = len(gracian_gov.get("board_members", []))
            o_board = len(openai_data.get("board_members", [])) if isinstance(openai_data.get("board_members"), list) else 0
            f.write(f"| board_members (count) | {d_board} | {g_board} | {o_board} |\n\n")

            # Financial fields (Docling + OpenAI only)
            f.write("#### Financial Fields\n\n")
            f.write("| Field | Docling+GPT-4o | OpenAI Direct |\n")
            f.write("|-------|----------------|---------------|\n")

            docling_fin = comp.get("docling_postprocessed", {}).get("financial_agent", {})
            for field in ["assets", "revenue", "expenses", "equity"]:
                d_val = docling_fin.get(field, "N/A") or "N/A"
                o_val = openai_data.get(field, "N/A") or "N/A"
                f.write(f"| {field} | {d_val} | {o_val} |\n")

            f.write("\n---\n\n")

    def _write_recommendations(self, f, comparisons):
        f.write("## Recommendations for 95/95 Target\n\n")

        # Analyze which method performed best
        f.write("### Key Findings\n\n")
        f.write("1. **Docling + GPT-4o**: Best for machine-readable PDFs with good structure\n")
        f.write("   - Pros: Extracts tables, handles multi-page documents well\n")
        f.write("   - Cons: Doesn't OCR scanned PDFs effectively\n\n")

        f.write("2. **Gracian Pipeline**: Good for governance extraction\n")
        f.write("   - Pros: Uses vision models, works on both scanned and text PDFs\n")
        f.write("   - Cons: Limited to configured agents\n\n")

        f.write("3. **OpenAI Vision Direct**: Baseline for validation\n")
        f.write("   - Pros: Simple, works on all PDF types\n")
        f.write("   - Cons: No table extraction, limited context\n\n")

        f.write("### Proposed Hybrid Pipeline\n\n")
        f.write("```python\n")
        f.write("def hybrid_extraction(pdf_path):\n")
        f.write("    # 1. Try Docling first (fast for text PDFs)\n")
        f.write("    docling_result = docling_extract(pdf_path)\n")
        f.write("    \n")
        f.write("    if is_text_pdf(docling_result):\n")
        f.write("        # Use Docling + GPT-4o for structured extraction\n")
        f.write("        return docling_to_brf_schema(docling_result)\n")
        f.write("    else:\n")
        f.write("        # Fall back to Gracian Pipeline for scanned PDFs\n")
        f.write("        return gracian_vision_extraction(pdf_path)\n")
        f.write("```\n\n")

        f.write("### Schema Mapping Integration\n\n")
        f.write("- Add `mappings.py` to convert docling tables to BRF financial schema\n")
        f.write("- Use regex patterns for Swedish number parsing (\"301 339 818\" → 301339818)\n")
        f.write("- Implement confidence scoring for each extracted field\n")
        f.write("- Add cross-validation between methods\n\n")


def main():
    """Main pipeline."""

    print("\n" + "="*80)
    print("🚀 DOCLING BRF EXTRACTION VALIDATION PIPELINE")
    print("="*80)

    # Test PDFs
    test_pdfs = [
        "SRS/brf_198532.pdf",  # Machine-readable
        # "SRS/brf_276629.pdf",  # Scanned (skip for now - docling doesn't OCR well)
    ]

    # Initialize components
    docling_extractor = DoclingBRFExtractor()
    validator = ComparisonValidator()
    report_gen = ReportGenerator()

    all_comparisons = []

    for pdf_rel_path in test_pdfs:
        pdf_path = str(Path(__file__).parent.parent / pdf_rel_path)

        if not Path(pdf_path).exists():
            print(f"❌ Not found: {pdf_path}")
            continue

        # Step 1: Extract with Docling
        docling_result = docling_extractor.extract(pdf_path)

        # Step 2: Validate against other methods
        if docling_result.get("status") != "scanned_pdf":
            comparison = validator.validate(pdf_path, docling_result)
            all_comparisons.append(comparison)

    # Step 3: Generate report
    if all_comparisons:
        report_path = report_gen.generate(all_comparisons)
        print(f"✅ Validation complete! Report: {report_path}")

    return all_comparisons


if __name__ == "__main__":
    main()
