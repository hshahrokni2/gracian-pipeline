#!/usr/bin/env python3
"""
Simple docling test to understand the API and output structure.
"""

import json
from pathlib import Path
from docling.document_converter import DocumentConverter

def test_docling_basic():
    """Test basic docling extraction."""

    pdf_paths = [
        "SRS/brf_198532.pdf",  # Machine-readable
        "SRS/brf_276629.pdf",  # Scanned
    ]

    converter = DocumentConverter()

    for pdf_rel_path in pdf_paths:
        pdf_path = Path(__file__).parent.parent / pdf_rel_path

        if not pdf_path.exists():
            print(f"❌ Not found: {pdf_path}")
            continue

        print(f"\n{'='*80}")
        print(f"📄 {pdf_path.name}")
        print(f"{'='*80}\n")

        # Convert
        result = converter.convert(str(pdf_path))

        # Inspect result structure
        print(f"Result type: {type(result)}")
        print(f"Result attributes: {dir(result)}")

        # Get document
        doc = result.document
        print(f"\nDocument type: {type(doc)}")
        print(f"Document attributes: {[attr for attr in dir(doc) if not attr.startswith('_')]}")

        # Try to export
        try:
            markdown = doc.export_to_markdown()
            print(f"\n✅ Markdown export successful ({len(markdown)} chars)")
            print(f"\nFirst 500 chars:\n{markdown[:500]}\n")

            # Save markdown
            output_path = Path("experiments/docling_results") / f"{pdf_path.stem}_markdown.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"💾 Saved: {output_path}")

        except Exception as e:
            print(f"❌ Markdown export error: {e}")

        # Try JSON export
        try:
            json_data = doc.export_to_dict()
            print(f"\n✅ JSON export successful")
            print(f"JSON keys: {json_data.keys()}")

            # Save JSON
            output_path = Path("experiments/docling_results") / f"{pdf_path.stem}_docling.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved: {output_path}")

        except Exception as e:
            print(f"❌ JSON export error: {e}")


if __name__ == "__main__":
    test_docling_basic()
