#!/usr/bin/env python3
"""
Test Docling extraction on Swedish BRF annual reports.

This script:
1. Runs docling on both machine-readable and scanned PDFs
2. Extracts structured data using docling's AI models
3. Maps outputs to Gracian Pipeline schema format
4. Validates results using OpenAI/Claude
5. Generates comprehensive comparison report
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

# Import Gracian pipeline components
from gracian_pipeline.core.schema import EXPECTED_TYPES, get_types
from gracian_pipeline.core.vision_qc import vision_qc_agent, call_openai_vision, render_pdf_pages_subset
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS


class DoclingExtractor:
    """Extract BRF data using Docling."""

    def __init__(self, output_dir: str = "experiments/docling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure docling pipeline with OCR for scanned docs
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def extract_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract document using docling."""
        print(f"\n🔍 Processing {Path(pdf_path).name} with Docling...")

        try:
            # Convert document
            result = self.converter.convert(pdf_path)

            # Get structured document
            doc = result.document

            # Extract text and structure
            extraction = {
                "pdf_path": pdf_path,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "num_pages": len(doc.pages),
                    "has_tables": len(list(doc.iterate_items(TableItem))) > 0,
                    "has_images": len(list(doc.iterate_items(PictureItem))) > 0,
                },
                "full_text": doc.export_to_markdown(),
                "tables": [],
                "sections": [],
            }

            # Extract tables
            for table_item in doc.iterate_items(TableItem):
                extraction["tables"].append({
                    "caption": getattr(table_item, "caption", ""),
                    "data": table_item.export_to_dataframe().to_dict() if hasattr(table_item, "export_to_dataframe") else {},
                })

            # Extract sections from document structure
            for page in doc.pages:
                for item in page.items:
                    if hasattr(item, "label") and item.label:
                        extraction["sections"].append({
                            "title": item.text[:100] if hasattr(item, "text") else "",
                            "level": getattr(item, "level", 0),
                            "page": page.page_no,
                        })

            print(f"  ✅ Extracted {extraction['metadata']['num_pages']} pages, "
                  f"{len(extraction['tables'])} tables, {len(extraction['sections'])} sections")

            return extraction

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {
                "pdf_path": pdf_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def save_raw_output(self, extraction: Dict[str, Any], pdf_name: str) -> Path:
        """Save raw docling output."""
        output_file = self.output_dir / f"{pdf_name}_docling_raw.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extraction, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved raw output: {output_file}")
        return output_file


class BRFSchemaMapper:
    """Map Docling outputs to Gracian Pipeline BRF schema."""

    def __init__(self):
        self.schema = EXPECTED_TYPES

    def map_to_brf_schema(self, docling_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map docling extraction to BRF schema format.

        Targets schema fields from gracian_pipeline/core/schema.py:
        - governance_agent: chairman, board_members, auditor_name, etc.
        - financial_agent: revenue, expenses, assets, liabilities, etc.
        - property_agent: address, construction_year, num_apartments, etc.
        """

        print(f"\n📋 Mapping to BRF schema...")

        full_text = docling_data.get("full_text", "")
        tables = docling_data.get("tables", [])

        # Use OpenAI to extract structured fields from docling's markdown output
        mapped_data = {}

        # Governance extraction
        mapped_data["governance_agent"] = self._extract_governance(full_text)

        # Financial extraction (prioritize tables)
        mapped_data["financial_agent"] = self._extract_financial(full_text, tables)

        # Property extraction
        mapped_data["property_agent"] = self._extract_property(full_text)

        return mapped_data

    def _extract_governance(self, text: str) -> Dict[str, Any]:
        """Extract governance fields using LLM on docling markdown."""

        prompt = """Extract governance information from this Swedish BRF annual report text:

Required fields (return as JSON):
- chairman (str): Name of board chairman/ordförande
- board_members (list): Names of all board members
- auditor_name (str): Name of primary auditor/revisor
- audit_firm (str): Auditing firm name
- nomination_committee (list): Names of nomination committee members
- evidence_pages (list): Page numbers where you found this info

Return ONLY valid JSON with these exact keys."""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF document parser. Extract exact names and information."},
                    {"role": "user", "content": f"{prompt}\n\nText:\n{text[:8000]}"}  # Limit context
                ],
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)
            print(f"  ✅ Governance: {result.get('chairman', 'N/A')}, {len(result.get('board_members', []))} board members")
            return result

        except Exception as e:
            print(f"  ⚠️ Governance extraction error: {e}")
            return {}

    def _extract_financial(self, text: str, tables: List[Dict]) -> Dict[str, Any]:
        """Extract financial fields, prioritizing table data."""

        # First try to extract from tables
        financial_data = {}

        for table in tables:
            # Look for balance sheet / income statement tables
            caption = table.get("caption", "").lower()
            if any(keyword in caption for keyword in ["resultat", "balans", "förvaltningsberättelse"]):
                # Try to parse table for financial figures
                pass  # TODO: Add table parsing logic

        # Fallback to LLM extraction from text
        prompt = """Extract financial information from this Swedish BRF annual report:

Required fields (return as JSON with numeric values):
- revenue (num): Total revenue/intäkter
- expenses (num): Total expenses/kostnader
- assets (num): Total assets/tillgångar
- liabilities (num): Total liabilities/skulder
- equity (num): Equity/eget kapital
- surplus (num): Surplus/överskott
- evidence_pages (list): Page numbers

Return ONLY valid JSON. Use null for missing values."""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish financial document parser. Extract exact figures."},
                    {"role": "user", "content": f"{prompt}\n\nText:\n{text[:8000]}"}
                ],
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)
            print(f"  ✅ Financial: Assets={result.get('assets', 'N/A')}, Revenue={result.get('revenue', 'N/A')}")
            return result

        except Exception as e:
            print(f"  ⚠️ Financial extraction error: {e}")
            return {}

    def _extract_property(self, text: str) -> Dict[str, Any]:
        """Extract property information."""

        prompt = """Extract property information from this Swedish BRF annual report:

Required fields (return as JSON):
- address (str): Property address
- construction_year (num): Year built
- num_apartments (num): Number of apartments
- area_sqm (num): Total area in square meters
- evidence_pages (list): Page numbers

Return ONLY valid JSON. Use null for missing values."""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Swedish property document parser."},
                    {"role": "user", "content": f"{prompt}\n\nText:\n{text[:8000]}"}
                ],
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)
            print(f"  ✅ Property: {result.get('address', 'N/A')}, {result.get('num_apartments', 'N/A')} apartments")
            return result

        except Exception as e:
            print(f"  ⚠️ Property extraction error: {e}")
            return {}


class ValidationPipeline:
    """Validate docling results against Gracian Pipeline and OpenAI."""

    def __init__(self, output_dir: str = "experiments/docling_results"):
        self.output_dir = Path(output_dir)

    def validate_document(self, pdf_path: str, docling_mapped: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run validation comparison:
        1. Docling + post-processing (already done)
        2. Gracian Pipeline (vision_qc_agent)
        3. Direct OpenAI vision extraction
        """

        print(f"\n🔬 Validating {Path(pdf_path).name}...")

        validation_results = {
            "pdf": Path(pdf_path).name,
            "docling_postprocessed": docling_mapped,
            "gracian_pipeline": {},
            "openai_direct": {},
            "comparison": {},
        }

        # Test governance agent with Gracian Pipeline
        try:
            print("  🤖 Running Gracian Pipeline (governance)...")
            governance_result, meta = vision_qc_agent(
                pdf_path,
                "governance_agent",
                AGENT_PROMPTS.get("governance_agent", "Extract governance info"),
                page_indices=[0, 1, 2]  # First 3 pages
            )
            validation_results["gracian_pipeline"]["governance_agent"] = governance_result
            print(f"    ✅ Gracian: {governance_result.get('chairman', 'N/A')}")
        except Exception as e:
            print(f"    ❌ Gracian error: {e}")
            validation_results["gracian_pipeline"]["governance_agent"] = {"error": str(e)}

        # Direct OpenAI vision extraction (baseline)
        try:
            print("  🔍 Running direct OpenAI vision...")
            images = render_pdf_pages_subset(pdf_path, [0, 1, 2], dpi=200)

            openai_prompt = """Extract from this Swedish BRF annual report:
1. Chairman name (ordförande)
2. All board members
3. Auditor name and firm

Return as JSON with keys: chairman, board_members, auditor_name, audit_firm"""

            openai_result = call_openai_vision(openai_prompt, images, page_labels=["Page 1", "Page 2", "Page 3"])

            try:
                openai_parsed = json.loads(openai_result)
                validation_results["openai_direct"] = openai_parsed
                print(f"    ✅ OpenAI: {openai_parsed.get('chairman', 'N/A')}")
            except:
                validation_results["openai_direct"] = {"raw": openai_result}

        except Exception as e:
            print(f"    ❌ OpenAI error: {e}")
            validation_results["openai_direct"] = {"error": str(e)}

        return validation_results

    def generate_comparison_report(self, all_validations: List[Dict[str, Any]]) -> str:
        """Generate markdown comparison report."""

        report_path = self.output_dir / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Docling vs Gracian Pipeline vs OpenAI - Comparison Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Documents tested**: {len(all_validations)}\n")
            f.write(f"- **Extraction methods**: Docling+GPT-4o, Gracian Pipeline, OpenAI Vision Direct\n\n")

            f.write("## Detailed Results\n\n")

            for i, validation in enumerate(all_validations, 1):
                pdf_name = validation["pdf"]
                f.write(f"### {i}. {pdf_name}\n\n")

                # Governance comparison table
                f.write("#### Governance Fields\n\n")
                f.write("| Field | Docling+Postprocessing | Gracian Pipeline | OpenAI Direct |\n")
                f.write("|-------|------------------------|------------------|---------------|\n")

                docling_gov = validation["docling_postprocessed"].get("governance_agent", {})
                gracian_gov = validation["gracian_pipeline"].get("governance_agent", {})
                openai_gov = validation["openai_direct"]

                for field in ["chairman", "auditor_name", "audit_firm"]:
                    docling_val = docling_gov.get(field, "N/A")
                    gracian_val = gracian_gov.get(field, "N/A")
                    openai_val = openai_gov.get(field, "N/A")

                    f.write(f"| {field} | {docling_val} | {gracian_val} | {openai_val} |\n")

                # Board members count
                docling_board = len(docling_gov.get("board_members", []))
                gracian_board = len(gracian_gov.get("board_members", []))
                openai_board = len(openai_gov.get("board_members", []))

                f.write(f"| board_members (count) | {docling_board} | {gracian_board} | {openai_board} |\n\n")

                # Financial comparison
                f.write("#### Financial Fields\n\n")
                f.write("| Field | Docling+Postprocessing |\n")
                f.write("|-------|------------------------|\n")

                docling_fin = validation["docling_postprocessed"].get("financial_agent", {})
                for field in ["assets", "revenue", "expenses", "equity"]:
                    val = docling_fin.get(field, "N/A")
                    f.write(f"| {field} | {val} |\n")

                f.write("\n---\n\n")

            f.write("## High-Level Statistics\n\n")

            # Calculate success rates
            successful_docling = sum(1 for v in all_validations if v["docling_postprocessed"].get("governance_agent", {}).get("chairman"))
            successful_gracian = sum(1 for v in all_validations if v["gracian_pipeline"].get("governance_agent", {}).get("chairman"))
            successful_openai = sum(1 for v in all_validations if v["openai_direct"].get("chairman"))

            total = len(all_validations)

            f.write(f"- **Docling + Postprocessing**: {successful_docling}/{total} ({successful_docling/total*100:.1f}% chairman extraction)\n")
            f.write(f"- **Gracian Pipeline**: {successful_gracian}/{total} ({successful_gracian/total*100:.1f}% chairman extraction)\n")
            f.write(f"- **OpenAI Direct**: {successful_openai}/{total} ({successful_openai/total*100:.1f}% chairman extraction)\n\n")

        print(f"\n📊 Comparison report saved: {report_path}")
        return str(report_path)


def main():
    """Main test pipeline."""

    print("=" * 80)
    print("🚀 Docling BRF Extraction Test - Gracian Pipeline")
    print("=" * 80)

    # Test PDFs
    test_pdfs = [
        "SRS/brf_198532.pdf",  # Machine-readable
        "SRS/brf_276629.pdf",  # Scanned
    ]

    # Initialize components
    docling_extractor = DoclingExtractor()
    schema_mapper = BRFSchemaMapper()
    validator = ValidationPipeline()

    all_validations = []

    for pdf_path in test_pdfs:
        full_path = str(Path(__file__).parent.parent / pdf_path)

        if not Path(full_path).exists():
            print(f"❌ PDF not found: {full_path}")
            continue

        print(f"\n{'='*80}")
        print(f"📄 Processing: {Path(pdf_path).name}")
        print(f"{'='*80}")

        # Step 1: Extract with Docling
        docling_raw = docling_extractor.extract_pdf(full_path)
        docling_extractor.save_raw_output(docling_raw, Path(pdf_path).stem)

        # Step 2: Map to BRF schema
        if "error" not in docling_raw:
            docling_mapped = schema_mapper.map_to_brf_schema(docling_raw)

            # Save mapped output
            mapped_file = docling_extractor.output_dir / f"{Path(pdf_path).stem}_mapped.json"
            with open(mapped_file, 'w', encoding='utf-8') as f:
                json.dump(docling_mapped, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved mapped output: {mapped_file}")

            # Step 3: Validate
            validation_result = validator.validate_document(full_path, docling_mapped)
            all_validations.append(validation_result)

            # Save validation
            val_file = docling_extractor.output_dir / f"{Path(pdf_path).stem}_validation.json"
            with open(val_file, 'w', encoding='utf-8') as f:
                json.dump(validation_result, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved validation: {val_file}")

    # Step 4: Generate comparison report
    if all_validations:
        report_path = validator.generate_comparison_report(all_validations)

        print("\n" + "=" * 80)
        print("✅ TESTING COMPLETE")
        print("=" * 80)
        print(f"📊 Comparison report: {report_path}")
        print(f"📁 All outputs: {docling_extractor.output_dir}")

    return all_validations


if __name__ == "__main__":
    main()
