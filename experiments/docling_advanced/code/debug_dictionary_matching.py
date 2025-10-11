#!/usr/bin/env python3
"""
Comprehensive Dictionary Matching Diagnostic Tool

Purpose: Diagnose why 0% of Docling sections are matching to agents

Outputs:
1. All raw section headings from Docling
2. Preprocessing results (stripped numbering, normalized)
3. Match attempts with each layer and scores
4. Patterns identified (language, case, numbering, OCR errors)
5. Recommended fixes with code snippets
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling_core.types.doc import SectionHeaderItem


def preprocess_section_heading(heading: str) -> Dict[str, str]:
    """
    Apply multiple preprocessing strategies to section headings.

    Returns dict with different preprocessing strategies for comparison.
    """
    strategies = {}

    # Original
    strategies['original'] = heading

    # Strip whitespace
    strategies['stripped'] = heading.strip()

    # Lowercase
    strategies['lowercase'] = heading.lower()

    # Remove numbering patterns
    # Match: "1.", "1.1", "3.2.1", "(1)", "[1]"
    cleaned = heading.strip()
    cleaned = re.sub(r'^[\[\(]?\d+[\.\)\]]\s*', '', cleaned)  # 1. or (1) or [1]
    cleaned = re.sub(r'^\d+\.\d+\s*', '', cleaned)  # 1.1
    cleaned = re.sub(r'^\d+\.\d+\.\d+\s*', '', cleaned)  # 1.2.3
    strategies['no_numbering'] = cleaned

    # Remove section labels
    cleaned = strategies['no_numbering']
    cleaned = re.sub(r'^(avsnitt|section|not|note|kapitel|chapter)\s*:?\s*', '', cleaned, flags=re.IGNORECASE)
    strategies['no_labels'] = cleaned

    # Remove special characters at start
    cleaned = strategies['no_labels']
    cleaned = re.sub(r'^[\-–—:]+\s*', '', cleaned)
    strategies['no_special_chars'] = cleaned

    # Normalize Swedish characters (å→a, ä→a, ö→o)
    import unicodedata
    text = strategies['no_special_chars'].lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    strategies['normalized_swedish'] = text

    # Final cleaned version
    strategies['final'] = ' '.join(strategies['normalized_swedish'].split())

    return strategies


def extract_sections_from_docling(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract section headings using Docling"""
    print("🔍 Extracting sections from Docling...")

    # Use OCR for scanned PDFs
    pipeline_options = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=EasyOcrOptions(lang=["sv", "en"])
    )

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(pdf_path)
    doc = result.document

    sections = []
    for item, level in doc.iterate_items():
        if isinstance(item, SectionHeaderItem):
            # Get page from provenance
            page_no = None
            if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                docling_page = getattr(item.prov[0], 'page_no', None)
                if docling_page is not None:
                    page_no = docling_page - 1  # Convert to 0-indexed

            sections.append({
                "heading": item.text,
                "level": level,
                "page": page_no
            })

    print(f"   Found {len(sections)} sections")
    return sections


def load_main_section_keywords() -> Dict[str, List[str]]:
    """Load keyword routing map from optimal_brf_pipeline.py"""
    return {
        "governance_agent": [
            "förvaltningsberättelse", "styrelse", "board", "governance",
            "föreningsstämma", "annual meeting", "giltighet", "validity"
        ],
        "financial_agent": [
            "resultaträkning", "income statement", "balansräkning", "balance sheet",
            "kassaflödesanalys", "cash flow", "ekonomi", "financial"
        ],
        "property_agent": [
            "fastighet", "property", "building", "byggnadsår", "construction year",
            "ytor", "area", "lokaler", "premises"
        ],
        "operations_agent": [
            "verksamhet", "operations", "avtal", "contracts", "leverantörer", "suppliers"
        ]
    }


def load_dictionary_patterns() -> Dict[str, List[str]]:
    """Load section header patterns from Swedish Financial Dictionary YAML"""
    # These come from config/swedish_financial_terms.yaml special_patterns.section_headers
    return {
        "balance_sheet": [
            "balansräkning", "balansrakning", "balans"
        ],
        "income_statement": [
            "resultaträkning", "resultatrakning", "resultat"
        ],
        "notes": [
            "noter", "not", "tilläggsupplysningar", "tillaggsupplysningar"
        ],
        "governance": [
            "förvaltningsberättelse", "forvaltningsberattelse", "styrelse"
        ],
        "audit": [
            "revisionsberättelse", "revisionsberattelse", "revision"
        ]
    }


def match_layer1_substring(heading: str, keywords: List[str]) -> Optional[float]:
    """
    Layer 1: Substring matching (current implementation)
    Returns confidence score if match found
    """
    heading_lower = heading.lower()
    for keyword in keywords:
        if keyword.lower() in heading_lower:
            # Score based on how much of heading is matched
            score = len(keyword) / len(heading_lower)
            return min(score, 1.0)
    return None


def match_layer2_preprocessed(heading_preprocessed: Dict[str, str], keywords: List[str]) -> Optional[float]:
    """
    Layer 2: Preprocessed substring matching
    Try multiple preprocessing strategies
    """
    best_score = None

    for strategy, processed_heading in heading_preprocessed.items():
        if strategy == 'original':
            continue  # Already tried in Layer 1

        processed_lower = processed_heading.lower()
        for keyword in keywords:
            if keyword.lower() in processed_lower:
                # Higher confidence for cleaner preprocessing strategies
                base_score = len(keyword) / len(processed_lower) if processed_lower else 0

                # Bonus for better preprocessing
                strategy_bonus = {
                    'stripped': 0.05,
                    'lowercase': 0.05,
                    'no_numbering': 0.10,
                    'no_labels': 0.15,
                    'no_special_chars': 0.15,
                    'normalized_swedish': 0.20,
                    'final': 0.20
                }.get(strategy, 0)

                score = min(base_score + strategy_bonus, 1.0)
                if best_score is None or score > best_score:
                    best_score = score

    return best_score


def match_layer3_fuzzy(heading: str, keywords: List[str], threshold: float = 0.70) -> Optional[float]:
    """
    Layer 3: Fuzzy string matching using difflib
    Returns score if above threshold
    """
    from difflib import SequenceMatcher
    import unicodedata

    # Normalize both heading and keywords
    def normalize(text):
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        return text

    heading_norm = normalize(heading)
    best_score = 0.0

    for keyword in keywords:
        keyword_norm = normalize(keyword)
        score = SequenceMatcher(None, heading_norm, keyword_norm).ratio()
        if score > best_score:
            best_score = score

    return best_score if best_score >= threshold else None


def diagnose_dictionary_matching(pdf_path: str, output_path: str = "results/dictionary_diagnostic.txt"):
    """
    Comprehensive diagnostic for dictionary matching issues
    """
    print("=" * 80)
    print("DICTIONARY MATCHING DIAGNOSTIC")
    print("=" * 80)
    print()

    # Step 1: Extract sections from Docling
    sections = extract_sections_from_docling(pdf_path)

    if not sections:
        print("❌ No sections found! Docling may have failed.")
        return

    print()
    print("=" * 80)
    print("STEP 1: RAW SECTION HEADINGS FROM DOCLING")
    print("=" * 80)
    print()
    print(f"Total sections: {len(sections)}")
    print()
    print("First 10 section headings:")
    for i, section in enumerate(sections[:10], 1):
        print(f"{i:2}. Page {section['page']:2} | Level {section['level']} | {section['heading'][:70]}")
    print()

    # Step 2: Load routing configurations
    main_keywords = load_main_section_keywords()
    dict_patterns = load_dictionary_patterns()

    print("=" * 80)
    print("STEP 2: ROUTING CONFIGURATIONS LOADED")
    print("=" * 80)
    print()
    print(f"Main section keywords: {len(main_keywords)} agent types")
    for agent, keywords in main_keywords.items():
        print(f"   • {agent}: {len(keywords)} keywords")
    print()
    print(f"Dictionary patterns: {len(dict_patterns)} categories")
    for category, patterns in dict_patterns.items():
        print(f"   • {category}: {len(patterns)} patterns")
    print()

    # Step 3: Match analysis
    print("=" * 80)
    print("STEP 3: MULTI-LAYER MATCHING ANALYSIS")
    print("=" * 80)
    print()

    results = []
    layer_stats = defaultdict(int)

    for section in sections:
        heading = section['heading']
        preprocessed = preprocess_section_heading(heading)

        match_result = {
            "heading": heading,
            "page": section['page'],
            "level": section['level'],
            "preprocessed": preprocessed,
            "matches": {}
        }

        # Try Layer 1: Main keywords substring
        for agent_id, keywords in main_keywords.items():
            score = match_layer1_substring(heading, keywords)
            if score:
                match_result["matches"][f"layer1_{agent_id}"] = {
                    "layer": 1,
                    "agent": agent_id,
                    "score": score,
                    "method": "substring"
                }
                layer_stats["layer1"] += 1

        # Try Layer 2: Preprocessed substring
        for agent_id, keywords in main_keywords.items():
            score = match_layer2_preprocessed(preprocessed, keywords)
            if score and f"layer1_{agent_id}" not in match_result["matches"]:
                match_result["matches"][f"layer2_{agent_id}"] = {
                    "layer": 2,
                    "agent": agent_id,
                    "score": score,
                    "method": "preprocessed_substring"
                }
                layer_stats["layer2"] += 1

        # Try Layer 3: Dictionary fuzzy matching
        for category, patterns in dict_patterns.items():
            score = match_layer3_fuzzy(heading, patterns, threshold=0.70)
            if score and f"dict_{category}" not in match_result["matches"]:
                match_result["matches"][f"layer3_{category}"] = {
                    "layer": 3,
                    "category": category,
                    "score": score,
                    "method": "fuzzy"
                }
                layer_stats["layer3"] += 1

        results.append(match_result)

    # Step 4: Statistics
    print("📊 MATCHING STATISTICS:")
    print()
    total_sections = len(sections)
    matched_sections = sum(1 for r in results if r["matches"])
    print(f"   Total sections: {total_sections}")
    print(f"   Matched sections: {matched_sections} ({100*matched_sections//total_sections}%)")
    print(f"   Unmatched sections: {total_sections - matched_sections}")
    print()
    print("   Layer Performance:")
    print(f"      Layer 1 (substring): {layer_stats['layer1']} matches")
    print(f"      Layer 2 (preprocessed): {layer_stats['layer2']} matches")
    print(f"      Layer 3 (fuzzy): {layer_stats['layer3']} matches")
    print()

    # Step 5: Sample matches and mismatches
    print("=" * 80)
    print("STEP 4: SAMPLE MATCHES")
    print("=" * 80)
    print()

    matched_samples = [r for r in results if r["matches"]][:10]
    if matched_samples:
        for result in matched_samples:
            best_match = max(result["matches"].values(), key=lambda m: m["score"])
            print(f"✅ '{result['heading'][:60]}'")
            print(f"   → {best_match['method']} match")
            print(f"   → Agent/Category: {best_match.get('agent') or best_match.get('category')}")
            print(f"   → Score: {best_match['score']:.2f}")
            print()
    else:
        print("❌ No matches found!")
        print()

    print("=" * 80)
    print("STEP 5: SAMPLE MISMATCHES (First 10)")
    print("=" * 80)
    print()

    unmatched_samples = [r for r in results if not r["matches"]][:10]
    if unmatched_samples:
        for result in unmatched_samples:
            print(f"❌ Page {result['page']:2} | {result['heading'][:70]}")
            print(f"   Preprocessed (final): '{result['preprocessed']['final'][:60]}'")
            print()
    else:
        print("✅ All sections matched!")
        print()

    # Step 6: Pattern analysis
    print("=" * 80)
    print("STEP 6: PATTERN ANALYSIS")
    print("=" * 80)
    print()

    patterns_found = []

    # Check for numbering
    numbered_sections = sum(1 for s in sections if re.match(r'^\d+', s['heading']))
    if numbered_sections > 0:
        patterns_found.append({
            "type": "Numbering",
            "count": numbered_sections,
            "percentage": 100 * numbered_sections // total_sections,
            "description": "Sections start with numbers (e.g., '1.', '1.1', '3.2.1')",
            "fix": "Preprocessing Layer 2 strips numbering"
        })

    # Check for case variations
    uppercase_sections = sum(1 for s in sections if s['heading'].isupper())
    if uppercase_sections > 0:
        patterns_found.append({
            "type": "Uppercase",
            "count": uppercase_sections,
            "percentage": 100 * uppercase_sections // total_sections,
            "description": "Sections in ALL CAPS",
            "fix": "Preprocessing normalizes case"
        })

    # Check for Swedish characters
    swedish_chars = sum(1 for s in sections if any(c in s['heading'] for c in 'åäöÅÄÖ'))
    if swedish_chars > 0:
        patterns_found.append({
            "type": "Swedish Characters",
            "count": swedish_chars,
            "percentage": 100 * swedish_chars // total_sections,
            "description": "Sections contain Swedish characters (å, ä, ö)",
            "fix": "Preprocessing normalizes to ASCII"
        })

    # Check for generic labels
    generic_sections = sum(1 for s in sections if any(word in s['heading'].lower() for word in ['section', 'avsnitt', 'kapitel']))
    if generic_sections > 0:
        patterns_found.append({
            "type": "Generic Labels",
            "count": generic_sections,
            "percentage": 100 * generic_sections // total_sections,
            "description": "Sections use generic labels (Section X, Avsnitt Y)",
            "fix": "Layer 3 fuzzy matching or LLM fallback needed"
        })

    print("Patterns identified:")
    for pattern in patterns_found:
        print(f"   • {pattern['type']}: {pattern['count']}/{total_sections} ({pattern['percentage']}%)")
        print(f"      → {pattern['description']}")
        print(f"      → Fix: {pattern['fix']}")
        print()

    # Step 7: Recommendations
    print("=" * 80)
    print("STEP 7: RECOMMENDATIONS")
    print("=" * 80)
    print()

    recommendations = []

    if matched_sections == 0:
        recommendations.append("🚨 CRITICAL: 0% match rate - investigate section heading format")
        recommendations.append("   → Run this diagnostic to see actual Docling output")
        recommendations.append("   → Check if Docling is outputting generic labels")

    if numbered_sections > total_sections * 0.5:
        recommendations.append("📝 Implement numbering strip preprocessing (Layer 2)")
        recommendations.append("   → Most sections have numbering that blocks matches")

    if layer_stats["layer2"] > layer_stats["layer1"]:
        recommendations.append("✅ Preprocessing is helping! Integrate into production pipeline")

    if layer_stats["layer3"] > 0:
        recommendations.append("✅ Fuzzy matching catching edge cases - keep Layer 3")

    if matched_sections < total_sections * 0.80:
        recommendations.append("🔄 Add LLM classification fallback (Layer 4) for remaining sections")
        recommendations.append("   → ~${:.2f} cost for LLM classification".format(
            (total_sections - matched_sections) * 0.001  # Rough estimate
        ))

    if not recommendations:
        recommendations.append("✅ Routing is working well! No major issues found.")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    print()
    print("=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

    # Save detailed results to JSON
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    json_output = output_path.replace('.txt', '.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({
            "pdf": pdf_path,
            "total_sections": total_sections,
            "matched_sections": matched_sections,
            "match_rate": matched_sections / total_sections if total_sections else 0,
            "layer_stats": dict(layer_stats),
            "patterns": patterns_found,
            "recommendations": recommendations,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Detailed results saved to:")
    print(f"   • {json_output}")
    print(f"   • {output_path}")


def main():
    import sys
    from dotenv import load_dotenv

    # Load environment
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    if len(sys.argv) < 2:
        print("Usage: python debug_dictionary_matching.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    diagnose_dictionary_matching(pdf_path)


if __name__ == "__main__":
    main()
