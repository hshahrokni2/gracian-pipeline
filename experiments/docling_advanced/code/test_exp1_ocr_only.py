#!/usr/bin/env python3
"""
Experiment 1: OCR-Only Baseline with Pattern Matching
Test what percentage of BRF fields can be extracted WITHOUT LLM calls

Goal: Establish floor performance (accuracy & coverage with $0 cost)
Expected: 60-70% coverage, 85-90% accuracy on matched fields
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions

TEST_PDF = "test_pdfs/brf_268882.pdf"


class BRFPatternExtractor:
    """Extract BRF fields using only regex patterns (no LLM)"""

    def __init__(self):
        # Comprehensive Swedish BRF patterns
        self.patterns = {
            # Governance
            "chairman": [
                r"Ordförande[:\s]+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
                r"Styrelseordförande[:\s]+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
            ],
            "board_members": [
                r"Styrelseledamöter?[:\s]+(.{1,300})",
                r"Ledamöter?[:\s]+(.{1,200})",
            ],
            "auditor_name": [
                r"(?:Auktoriserad\s+)?Revisor[:\s]+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
                r"Ordinarie\s+revisor[:\s]+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
            ],
            "audit_firm": [
                r"Revisionsbyrå[:\s]+([A-ZÅÄÖ][^\n]{10,80})",
                r"Revisionsbolag[:\s]+([A-ZÅÄÖ][^\n]{10,80})",
            ],

            # Property
            "org_number": [
                r"(?:Org\.?\s*(?:nr|nummer)|Organisationsnummer)[:\s]+(\d{6}-\d{4})",
            ],
            "address": [
                r"(?:Postadress|Adress|Besöksadress)[:\s]+([A-ZÅÄÖ][^\n]{10,100})",
            ],
            "property_designation": [
                r"Fastighetsbeteckning[:\s]+([A-ZÅÄÖ][^\n]{10,80})",
                r"Fastighet[:\s]+([A-ZÅÄÖ][a-zåäö]+\s+\d+:\d+)",
            ],
            "sqm_total": [
                r"(?:Total\s+)?(?:Yta|Area)[:\s]+(\d[\d\s]+)\s*(?:m²|m2|kvm)",
                r"Bostadsarea[:\s]+(\d[\d\s]+)\s*(?:m²|m2|kvm)",
            ],
            "num_apartments": [
                r"Antal\s+(?:bostadsrätter|lägenheter)[:\s]+(\d+)",
            ],

            # Financial (key numbers only)
            "revenue": [
                r"(?:Intäkter|Nettoomsättning|Årsavgifter).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
            ],
            "expenses": [
                r"(?:Kostnader|Driftskostnader).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
            ],
            "assets": [
                r"(?:Tillgångar|Summa tillgångar).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
            ],
            "liabilities": [
                r"(?:Skulder|Summa skulder).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
            ],
            "equity": [
                r"(?:Eget kapital|Summa eget kapital).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
            ],

            # Fees
            "monthly_fee_avg": [
                r"(?:Genomsnittlig\s+)?(?:Månadsavgift|Årsavgift/12)[:\s]+(\d[\d\s]*\d)\s*(?:kr|SEK)",
            ],
        }

    def extract_with_confidence(self, markdown: str, field_name: str) -> Tuple[Optional[Any], float]:
        """
        Extract field value with confidence score
        Returns: (value, confidence) where confidence = 0.0-1.0
        """
        if field_name not in self.patterns:
            return None, 0.0

        patterns = self.patterns[field_name]
        matches = []

        for pattern in patterns:
            found = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE)
            if found:
                value = found.group(1).strip()

                # Clean numeric values
                if field_name in ["sqm_total", "num_apartments", "revenue", "expenses",
                                  "assets", "liabilities", "equity", "monthly_fee_avg"]:
                    value = self._parse_number(value)

                # Confidence based on pattern strength
                if found.group(0).count(":") > 0:  # Explicit label
                    confidence = 0.90
                else:
                    confidence = 0.70

                matches.append((value, confidence))

        if len(matches) == 0:
            return None, 0.0

        # If multiple matches agree, high confidence
        if len(matches) > 1 and matches[0][0] == matches[1][0]:
            return matches[0][0], 0.95

        # Return first match
        return matches[0]

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse Swedish number format"""
        # Remove spaces (thousands separator in Swedish)
        text = text.replace(" ", "")
        # Replace comma with dot (decimal separator)
        text = text.replace(",", ".")

        try:
            return float(text)
        except ValueError:
            return None

    def extract_all_fields(self, markdown: str) -> Dict[str, Any]:
        """Extract all fields with confidence scores"""
        results = {}
        confidence_scores = {}

        for field_name in self.patterns.keys():
            value, confidence = self.extract_with_confidence(markdown, field_name)
            results[field_name] = value
            confidence_scores[field_name] = confidence

        return {
            "extracted_fields": results,
            "confidence_scores": confidence_scores,
            "num_extracted": sum(1 for v in results.values() if v is not None),
            "total_fields": len(self.patterns),
            "coverage": sum(1 for v in results.values() if v is not None) / len(self.patterns)
        }


def run_experiment_1():
    """Run Experiment 1: OCR-only baseline"""

    print("=" * 70)
    print("EXPERIMENT 1: OCR-Only Baseline with Pattern Matching")
    print("=" * 70)
    print(f"Test PDF: {TEST_PDF}")
    print(f"Goal: Establish floor performance WITHOUT LLM calls")
    print(f"Expected: 60-70% coverage, 85-90% accuracy")
    print()

    if not Path(TEST_PDF).exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        return

    # Step 1: Extract with Docling + EasyOCR (Swedish)
    print("Step 1: Extracting with Docling + EasyOCR (Swedish)...")

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
    result = converter.convert(TEST_PDF)
    elapsed = time.time() - start

    markdown = result.document.export_to_markdown()

    print(f"✓ Extraction complete in {elapsed:.1f}s")
    print(f"  Characters: {len(markdown):,}")
    print(f"  Words: {len(markdown.split()):,}")
    print()

    # Step 2: Pattern-based extraction
    print("Step 2: Attempting pattern-based extraction...")

    extractor = BRFPatternExtractor()
    extraction_results = extractor.extract_all_fields(markdown)

    print(f"✓ Pattern extraction complete")
    print(f"  Fields extracted: {extraction_results['num_extracted']}/{extraction_results['total_fields']}")
    print(f"  Coverage: {extraction_results['coverage']:.1%}")
    print()

    # Step 3: Display results
    print("=" * 70)
    print("EXTRACTION RESULTS (OCR + Patterns Only)")
    print("=" * 70)
    print()

    extracted = extraction_results['extracted_fields']
    confidence = extraction_results['confidence_scores']

    # Group by category
    categories = {
        "Governance": ["chairman", "board_members", "auditor_name", "audit_firm"],
        "Property": ["org_number", "address", "property_designation", "sqm_total", "num_apartments"],
        "Financial": ["revenue", "expenses", "assets", "liabilities", "equity"],
        "Fees": ["monthly_fee_avg"],
    }

    for category, fields in categories.items():
        print(f"📊 {category.upper()}")
        print("-" * 70)

        for field in fields:
            value = extracted.get(field)
            conf = confidence.get(field, 0.0)

            if value is not None:
                status = "✅" if conf >= 0.80 else "⚠️"
                print(f"  {status} {field}: {value} (confidence: {conf:.0%})")
            else:
                print(f"  ❌ {field}: NOT FOUND")

        print()

    # Step 4: Analysis
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()

    high_conf_fields = sum(1 for c in confidence.values() if c >= 0.80)
    low_conf_fields = sum(1 for c in confidence.values() if 0.0 < c < 0.80)
    missing_fields = sum(1 for v in extracted.values() if v is None)

    print(f"High Confidence (≥80%): {high_conf_fields} fields")
    print(f"Low Confidence (<80%): {low_conf_fields} fields")
    print(f"Missing: {missing_fields} fields")
    print()

    print(f"💰 Cost: $0.00 (no LLM calls)")
    print(f"⚡ Speed: {elapsed:.1f}s (OCR only)")
    print()

    # Step 5: LLM fallback recommendation
    print("=" * 70)
    print("LLM FALLBACK RECOMMENDATION")
    print("=" * 70)
    print()

    low_conf_or_missing = [
        field for field, conf in confidence.items()
        if conf < 0.80
    ]

    if len(low_conf_or_missing) > 0:
        print(f"⚠️ {len(low_conf_or_missing)} fields need LLM fallback:")
        for field in low_conf_or_missing[:10]:  # Show first 10
            print(f"  - {field}")

        llm_cost_estimate = len(low_conf_or_missing) * 0.05  # $0.05 per field
        print()
        print(f"Estimated LLM cost: ${llm_cost_estimate:.2f}")
        print(f"Total cost (OCR + LLM): ${llm_cost_estimate:.2f}")
    else:
        print("✅ All fields extracted with high confidence!")
        print("No LLM fallback needed.")

    print()

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"results/exp1_ocr_only_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "experiment": "Experiment 1: OCR-Only Baseline",
            "test_date": datetime.now().isoformat(),
            "pdf": TEST_PDF,
            "ocr_time_seconds": elapsed,
            "markdown_chars": len(markdown),
            "extraction_results": extraction_results,
            "extracted_fields": {k: str(v) if v is not None else None for k, v in extracted.items()},
            "confidence_scores": confidence,
            "llm_fallback_needed": low_conf_or_missing,
            "cost_breakdown": {
                "ocr_cost": 0.0,
                "llm_cost_estimate": len(low_conf_or_missing) * 0.05,
                "total_cost": len(low_conf_or_missing) * 0.05
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Results saved to: {output_file}")
    print()
    print("✅ Experiment 1 complete!")
    print()
    print("Next steps:")
    print("1. Review which fields patterns handle well (→ skip LLM)")
    print("2. Review which fields need LLM (→ use confidence threshold)")
    print("3. Run Experiment 3 (section-aware routing) for optimal hybrid")


if __name__ == "__main__":
    run_experiment_1()
