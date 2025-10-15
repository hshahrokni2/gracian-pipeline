#!/usr/bin/env python3
"""
Quick PDF Classification for Phase 2B Test Selection

Classifies 20 candidate PDFs to select 7 diverse test cases across:
- Financial validation (balance sheet, cross-agent)
- Governance validation (chairman, dates)
- Property validation (building year, address)
- Conflict potential (hybrid PDFs with agent disagreement)

Date: 2025-10-14
Phase: Phase 2B Hour 2 - Test Corpus Curation
"""

import sys
import json
from pathlib import Path
from gracian_pipeline.core.pdf_classifier import classify_pdf

# Candidates from available datasets
CANDIDATES = [
    # Already tested (baseline)
    "experiments/docling_advanced/test_pdfs/brf_198532.pdf",
    "experiments/docling_advanced/test_pdfs/brf_268882.pdf",
    "SRS/brf_53546.pdf",

    # Hjorthagen candidates (15 PDFs)
    "Hjorthagen/brf_266956.pdf",
    "Hjorthagen/brf_268411.pdf",
    "Hjorthagen/brf_271852.pdf",
    "Hjorthagen/brf_271949.pdf",
    "Hjorthagen/brf_44232.pdf",
    "Hjorthagen/brf_46160.pdf",
    "Hjorthagen/brf_48574.pdf",
    "Hjorthagen/brf_48893.pdf",
    "Hjorthagen/brf_49369.pdf",
    "Hjorthagen/brf_58306.pdf",
    "Hjorthagen/brf_78906.pdf",
    "Hjorthagen/brf_79568.pdf",
    "Hjorthagen/brf_81563.pdf",
    "Hjorthagen/brf_82841.pdf",

    # SRS candidates (17 PDFs)
    "SRS/brf_275608.pdf",
    "SRS/brf_276507.pdf",
    "SRS/brf_276629.pdf",
    "SRS/brf_276796.pdf",
    "SRS/brf_280938.pdf",
    "SRS/brf_282765.pdf",
    "SRS/brf_43334.pdf",
    "SRS/brf_47809.pdf",
    "SRS/brf_47903.pdf",
    "SRS/brf_48663.pdf",
    "SRS/brf_52576.pdf",
    "SRS/brf_53107.pdf",
    "SRS/brf_54015.pdf",
    "SRS/brf_57125.pdf",
    "SRS/brf_58256.pdf",
    "SRS/brf_76536.pdf",
    "SRS/brf_77241.pdf",
]


def quick_classify():
    """Quick classification of candidate PDFs"""

    results = {
        "machine_readable": [],
        "scanned": [],
        "hybrid": [],
        "errors": []
    }

    print("🔍 Quick Classification Starting...")
    print(f"📄 Analyzing {len(CANDIDATES)} candidate PDFs\n")

    for i, pdf_path in enumerate(CANDIDATES, 1):
        full_path = Path(pdf_path)

        if not full_path.exists():
            print(f"{i:2d}. ❌ {pdf_path} - NOT FOUND")
            results["errors"].append(pdf_path)
            continue

        try:
            # Classify PDF
            classification = classify_pdf(str(full_path))
            pdf_type = classification.pdf_type  # "machine_readable", "scanned", or "hybrid"
            text_chars = classification.details.get("total_text_chars", 0)
            image_ratio = classification.image_ratio
            total_pages = classification.page_count

            # Categorize
            if pdf_type == "machine_readable":
                category = "machine_readable"
                emoji = "📝"
            elif pdf_type == "scanned":
                category = "scanned"
                emoji = "🖼️"
            elif pdf_type == "hybrid":
                category = "hybrid"
                emoji = "🔀"
            else:
                category = "errors"
                emoji = "❓"

            results[category].append({
                "path": pdf_path,
                "type": pdf_type,
                "pages": total_pages,
                "text_chars": text_chars,
                "image_ratio": image_ratio
            })

            print(f"{i:2d}. {emoji} {Path(pdf_path).name:30s} - {pdf_type:15s} "
                  f"({total_pages}p, {text_chars:,} chars, {image_ratio:.1%} img)")

        except Exception as e:
            print(f"{i:2d}. ❌ {pdf_path} - ERROR: {e}")
            results["errors"].append(pdf_path)

    # Summary
    print("\n" + "="*80)
    print("📊 CLASSIFICATION SUMMARY\n")
    print(f"Machine-Readable: {len(results['machine_readable'])} PDFs")
    print(f"Scanned:          {len(results['scanned'])} PDFs")
    print(f"Hybrid:           {len(results['hybrid'])} PDFs")
    print(f"Errors:           {len(results['errors'])} PDFs")
    print("="*80 + "\n")

    return results


def select_diverse_samples(results):
    """
    Select 7 diverse PDFs for comprehensive testing

    Strategy:
    - 2 Financial PDFs (complex balance sheets, cross-agent validation)
    - 2 Governance PDFs (chairman, board, dates)
    - 1 Property PDF (building year, address)
    - 2 Conflict PDFs (hybrid with potential agent disagreement)
    """

    selected = {
        "financial": [],
        "governance": [],
        "property": [],
        "conflict": []
    }

    # Category A: Financial (2 PDFs - prefer machine-readable for accurate tables)
    # Pick PDFs with >10 pages (complex financials) and high text content
    financial_candidates = [
        pdf for pdf in results["machine_readable"]
        if pdf["pages"] > 10 and pdf["text_chars"] > 50000
    ]
    if len(financial_candidates) >= 2:
        selected["financial"] = financial_candidates[:2]
    else:
        selected["financial"] = results["machine_readable"][:2]

    # Category B: Governance (2 PDFs - prefer machine-readable for text extraction)
    # Pick PDFs with moderate pages (governance in first 5 pages typically)
    governance_candidates = [
        pdf for pdf in results["machine_readable"]
        if 8 <= pdf["pages"] <= 15 and pdf not in selected["financial"]
    ]
    if len(governance_candidates) >= 2:
        selected["governance"] = governance_candidates[:2]
    else:
        # Fallback to any machine-readable
        remaining = [pdf for pdf in results["machine_readable"] if pdf not in selected["financial"]]
        selected["governance"] = remaining[:2]

    # Category C: Property (1 PDF - can be any type)
    # Pick scanned PDF to test vision extraction on property data
    if results["scanned"]:
        selected["property"] = [results["scanned"][0]]
    elif results["hybrid"]:
        selected["property"] = [results["hybrid"][0]]
    else:
        # Fallback to machine-readable
        remaining = [pdf for pdf in results["machine_readable"]
                    if pdf not in selected["financial"] and pdf not in selected["governance"]]
        selected["property"] = remaining[:1] if remaining else []

    # Category D: Conflict (2 PDFs - hybrid preferred for agent disagreement)
    if len(results["hybrid"]) >= 2:
        selected["conflict"] = results["hybrid"][:2]
    elif len(results["hybrid"]) == 1:
        # 1 hybrid + 1 scanned
        selected["conflict"] = [results["hybrid"][0]]
        if results["scanned"] and results["scanned"][0] not in selected["property"]:
            selected["conflict"].append(results["scanned"][0])
        elif len(results["scanned"]) > 1:
            selected["conflict"].append(results["scanned"][1])
    else:
        # Fallback to scanned PDFs (vision path vs text path potential conflicts)
        conflict_candidates = [pdf for pdf in results["scanned"] if pdf not in selected["property"]]
        selected["conflict"] = conflict_candidates[:2]

    return selected


def main():
    """Main execution"""

    # Step 1: Quick classification
    results = quick_classify()

    # Step 2: Select diverse samples
    print("🎯 SELECTING 7 DIVERSE TEST SAMPLES\n")
    selected = select_diverse_samples(results)

    # Step 3: Display selection
    print("="*80)
    print("📋 SELECTED TEST CORPUS (7 PDFs)")
    print("="*80 + "\n")

    total_selected = 0
    all_paths = []

    for category, pdfs in selected.items():
        print(f"Category: {category.upper()} ({len(pdfs)} PDFs)")
        for pdf in pdfs:
            print(f"  ✅ {pdf['path']}")
            print(f"     Type: {pdf['type']}, Pages: {pdf['pages']}, "
                  f"Text: {pdf['text_chars']:,} chars, Images: {pdf['image_ratio']:.1%}")
            all_paths.append(pdf['path'])
            total_selected += 1
        print()

    print("="*80)
    print(f"TOTAL SELECTED: {total_selected} PDFs")
    print("="*80 + "\n")

    # Step 4: Save to file for batch testing
    output = {
        "selected_pdfs": all_paths,
        "categories": selected,
        "total": total_selected,
        "timestamp": "2025-10-14T21:20:00Z"
    }

    output_path = Path("test_corpus_selection.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"💾 Selection saved to: {output_path}")
    print(f"\n✅ Test corpus curation complete!")
    print(f"📊 Ready for batch testing with {total_selected} diverse PDFs")

    return output


if __name__ == "__main__":
    main()
