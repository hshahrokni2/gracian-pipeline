# Parallel Docling Experimentation Guide

**Purpose**: Test advanced Docling features on image-based PDFs while Week 3 comprehensive testing runs in parallel.

**Target Agent**: Any Claude Code instance or coding agent (not the main Week 3 testing agent)

---

## 🎯 Mission

Experiment with Docling's advanced features on **scanned/image-based** Swedish BRF PDFs to discover:
1. OCR quality improvements
2. Table extraction from images
3. Layout analysis optimizations
4. Alternative processing pipelines

**Report back findings** to improve main extraction pipeline.

---

## 📁 Experimental Setup

### Directory Structure

Create isolated experimental workspace:

```bash
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"

# Create experimental directory
mkdir -p experiments/docling_advanced
cd experiments/docling_advanced

# Create subdirectories
mkdir -p {test_pdfs,results,code,logs}
```

### Copy Test PDFs (Image-Based)

Based on PDF topology analysis, these are **scanned/image-based** PDFs (~49% of corpus):

```bash
# From Hjorthagen (15 total, ~7 are scanned)
cp ../../Hjorthagen/brf_268882.pdf test_pdfs/  # Scanned, 21 pages
cp ../../Hjorthagen/brf_271852.pdf test_pdfs/  # Scanned, 15 pages
cp ../../Hjorthagen/brf_48574.pdf test_pdfs/   # Scanned, 42 pages

# From SRS (27 total, ~13 are scanned)
cp ../../SRS/brf_276507.pdf test_pdfs/         # Large scanned, 52 pages
cp ../../SRS/brf_282765.pdf test_pdfs/         # Large scanned, 151 pages
cp ../../SRS/brf_53107.pdf test_pdfs/          # Extra large, 209 pages

# Start with 1-2 smaller PDFs for faster iteration
```

---

## 🧪 Experiments to Run

### Experiment 1: OCR Engine Comparison

**Goal**: Compare different OCR backends for Swedish text quality

**Code** (`code/test_ocr_engines.py`):

```python
#!/usr/bin/env python3
"""
Compare OCR engines for Swedish BRF documents.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add main pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TesseractOcrOptions,
)

# Test PDFs
TEST_PDFS = [
    "test_pdfs/brf_268882.pdf",  # Small scanned
    "test_pdfs/brf_271852.pdf",  # Medium scanned
]

# OCR engines to test
OCR_CONFIGS = {
    "easyocr": EasyOcrOptions(force_full_page_ocr=True, lang=["sv", "en"]),
    "tesseract": TesseractOcrOptions(force_full_page_ocr=True, lang=["swe", "eng"]),
    # Add others: ocrmac, rapidocr
}


def test_ocr_engine(pdf_path: str, engine_name: str, ocr_options):
    """Test single OCR engine on PDF."""
    print(f"\n{'='*60}")
    print(f"Testing {engine_name} on {Path(pdf_path).name}")
    print('='*60)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = ocr_options

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = datetime.now()
    result = converter.convert(pdf_path)
    elapsed = (datetime.now() - start_time).total_seconds()

    # Extract metrics
    markdown = result.document.export_to_markdown()
    char_count = len(markdown)
    word_count = len(markdown.split())

    # Check for Swedish characters (å, ä, ö)
    swedish_chars = sum(1 for c in markdown if c in 'åäöÅÄÖ')

    print(f"✓ Completed in {elapsed:.1f}s")
    print(f"  Characters: {char_count:,}")
    print(f"  Words: {word_count:,}")
    print(f"  Swedish chars: {swedish_chars}")
    print(f"  Chars/word: {char_count/word_count:.1f}")

    return {
        "pdf": Path(pdf_path).name,
        "engine": engine_name,
        "elapsed_seconds": elapsed,
        "char_count": char_count,
        "word_count": word_count,
        "swedish_chars": swedish_chars,
        "avg_word_length": char_count / word_count if word_count > 0 else 0,
        "markdown_sample": markdown[:500]  # First 500 chars
    }


def main():
    results = []

    for pdf_path in TEST_PDFS:
        if not Path(pdf_path).exists():
            print(f"⚠️ PDF not found: {pdf_path}")
            continue

        for engine_name, ocr_options in OCR_CONFIGS.items():
            try:
                result = test_ocr_engine(pdf_path, engine_name, ocr_options)
                results.append(result)
            except Exception as e:
                print(f"❌ Error with {engine_name}: {e}")
                results.append({
                    "pdf": Path(pdf_path).name,
                    "engine": engine_name,
                    "error": str(e)
                })

    # Save results
    output_file = f"results/ocr_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {output_file}")

    # Print comparison table
    print("\n" + "="*80)
    print("OCR ENGINE COMPARISON")
    print("="*80)
    print(f"{'PDF':<20} {'Engine':<15} {'Time (s)':<10} {'Words':<10} {'Swedish':<10}")
    print("-"*80)

    for r in results:
        if 'error' not in r:
            print(f"{r['pdf']:<20} {r['engine']:<15} {r['elapsed_seconds']:<10.1f} "
                  f"{r['word_count']:<10,} {r['swedish_chars']:<10}")


if __name__ == "__main__":
    main()
```

**Run**:
```bash
cd experiments/docling_advanced
python code/test_ocr_engines.py > logs/ocr_comparison.log 2>&1
```

---

### Experiment 2: Table Extraction Quality

**Goal**: Test table detection and extraction accuracy on scanned documents

**Code** (`code/test_table_extraction.py`):

```python
#!/usr/bin/env python3
"""
Test table extraction quality on scanned PDFs.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling_core.types.doc import TableItem


TEST_PDFS = [
    "test_pdfs/brf_268882.pdf",
    "test_pdfs/brf_271852.pdf",
]


def analyze_tables(pdf_path: str):
    """Extract and analyze all tables from PDF."""
    print(f"\n{'='*60}")
    print(f"Analyzing tables in {Path(pdf_path).name}")
    print('='*60)

    # Configure for table extraction
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = EasyOcrOptions(
        force_full_page_ocr=True,
        lang=["sv", "en"]
    )
    pipeline_options.do_table_structure = True  # Enable table structure analysis

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(pdf_path)
    doc = result.document

    # Find all tables
    tables = []
    for item, level in doc.iterate_items():
        if isinstance(item, TableItem):
            tables.append(item)

    print(f"Found {len(tables)} tables")

    table_data = []
    for i, table in enumerate(tables, 1):
        print(f"\nTable {i}:")

        # Try to export to dataframe
        try:
            df = table.export_to_dataframe()
            rows, cols = df.shape

            print(f"  Dimensions: {rows} rows × {cols} columns")
            print(f"  Sample data:")
            print(df.head(3).to_string(index=False))

            # Check for Swedish financial terms
            text = df.to_string()
            has_financial = any(term in text.lower() for term in
                ['tillgångar', 'skulder', 'eget kapital', 'intäkter', 'kostnader'])

            table_data.append({
                "table_number": i,
                "rows": rows,
                "columns": cols,
                "has_financial_terms": has_financial,
                "sample_data": df.head(2).to_dict()
            })

        except Exception as e:
            print(f"  ⚠️ Could not export to dataframe: {e}")
            table_data.append({
                "table_number": i,
                "error": str(e)
            })

    return {
        "pdf": Path(pdf_path).name,
        "table_count": len(tables),
        "tables": table_data
    }


def main():
    results = []

    for pdf_path in TEST_PDFS:
        if not Path(pdf_path).exists():
            print(f"⚠️ PDF not found: {pdf_path}")
            continue

        try:
            result = analyze_tables(pdf_path)
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_file = f"results/table_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {output_file}")


if __name__ == "__main__":
    main()
```

---

### Experiment 3: Layout Analysis Deep Dive

**Goal**: Understand document structure detection quality

**Code** (`code/test_layout_analysis.py`):

```python
#!/usr/bin/env python3
"""
Analyze layout detection on scanned PDFs.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel


TEST_PDF = "test_pdfs/brf_268882.pdf"  # Start with smallest


def analyze_layout(pdf_path: str):
    """Analyze document layout structure."""
    print(f"Analyzing layout in {Path(pdf_path).name}")

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    # Count item types
    item_counts = {}
    for item, level in doc.iterate_items():
        label = item.label
        item_counts[label] = item_counts.get(label, 0) + 1

    print(f"\nDocument Structure:")
    for label, count in sorted(item_counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count}")

    # Find headings (important for section detection)
    headings = []
    for item, level in doc.iterate_items():
        if item.label in [DocItemLabel.SECTION_HEADER, DocItemLabel.TITLE]:
            headings.append({
                "level": level,
                "text": item.text[:100] if hasattr(item, 'text') else "",
                "label": str(item.label)
            })

    print(f"\nFound {len(headings)} headings:")
    for h in headings[:10]:  # Show first 10
        print(f"  Level {h['level']}: {h['text']}")

    return {
        "pdf": Path(pdf_path).name,
        "item_counts": item_counts,
        "heading_count": len(headings),
        "headings_sample": headings[:20]
    }


def main():
    if not Path(TEST_PDF).exists():
        print(f"❌ PDF not found: {TEST_PDF}")
        return

    result = analyze_layout(TEST_PDF)

    output_file = f"results/layout_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {output_file}")


if __name__ == "__main__":
    main()
```

---

## 🚀 Quick Start Commands

```bash
# 1. Setup
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"
mkdir -p experiments/docling_advanced/{test_pdfs,results,code,logs}

# 2. Copy a small scanned PDF for testing
cp Hjorthagen/brf_268882.pdf experiments/docling_advanced/test_pdfs/

# 3. Create experiment scripts (copy code from above sections)
# Save to: code/test_ocr_engines.py, code/test_table_extraction.py, etc.

# 4. Run experiments
cd experiments/docling_advanced
python code/test_ocr_engines.py > logs/ocr_$(date +%Y%m%d_%H%M%S).log 2>&1
python code/test_table_extraction.py > logs/tables_$(date +%Y%m%d_%H%M%S).log 2>&1
python code/test_layout_analysis.py > logs/layout_$(date +%Y%m%d_%H%M%S).log 2>&1

# 5. Review results
ls -lh results/
cat results/ocr_comparison_*.json | jq '.'
```

---

## 📊 What to Report Back

Create a file: `experiments/docling_advanced/FINDINGS.md`

Include:

### 1. OCR Quality
- Which engine worked best for Swedish text?
- Character recognition accuracy (especially å, ä, ö)
- Processing speed comparison
- Any errors encountered

### 2. Table Extraction
- How many tables were detected vs actual tables?
- Were financial tables (assets, liabilities) extracted correctly?
- Any missing or malformed tables?

### 3. Layout Analysis
- Were section headers correctly identified?
- Did it find "Styrelse", "Resultaträkning", "Balansräkning"?
- Any layout misdetection issues?

### 4. Recommendations
- Should we change default OCR engine?
- Any pipeline parameter tweaks to suggest?
- Performance optimization opportunities?

---

## 🎯 Success Criteria

**Minimum**: Run at least 1 experiment on 1 scanned PDF
**Good**: Run all 3 experiments on 2-3 scanned PDFs
**Excellent**: Compare results across multiple engines/configurations

**Time Estimate**: 1-2 hours for comprehensive experiments

---

## 🔗 Integration Plan

Once you have findings:

1. **Share results** via `FINDINGS.md`
2. Main agent will **review during Week 3 Day 3** (ground truth validation phase)
3. **Integrate improvements** into main pipeline if validated
4. **Update documentation** with best practices

---

## ⚠️ Important Notes

1. **Don't modify main pipeline code** - work only in `experiments/docling_advanced/`
2. **Use .env from main directory** - Docling needs no API keys, but experiments might
3. **Log everything** - redirect output to log files for review
4. **Small PDFs first** - test on brf_268882.pdf (21 pages) before large ones
5. **Safe to run in parallel** - won't interfere with Week 3 comprehensive testing

---

## 📚 Docling Documentation References

- **Official Docs**: https://ds4sd.github.io/docling/
- **OCR Options**: https://ds4sd.github.io/docling/examples/ocr/
- **Table Extraction**: https://ds4sd.github.io/docling/examples/table_structure/
- **Pipeline Options**: https://ds4sd.github.io/docling/examples/custom_convert/

---

## 🤖 Message to Parallel Agent

Hi! You're running **parallel docling experiments** while the main agent tests the full pipeline.

**Your mission**: Help improve OCR and table extraction for scanned Swedish BRF PDFs.

**What you need to know**:
- Main testing is running on `test_comprehensive_sample.py` (don't touch)
- Your workspace: `experiments/docling_advanced/`
- Test PDFs are scanned/image-based (the hard ones!)
- Goal: Find best docling configuration for Swedish text

**Quick Start**:
```bash
cd experiments/docling_advanced
python code/test_ocr_engines.py  # Start here!
```

**Report findings** in `FINDINGS.md` when done. Main agent will integrate during Week 3 Day 3.

Happy experimenting! 🧪
