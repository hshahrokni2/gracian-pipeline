#!/usr/bin/env python3
"""
Debug script to inspect Docling section page information
"""
import sys
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling_core.types.doc import SectionHeaderItem, DoclingDocument

# Load test PDF
pdf_path = "test_pdfs/brf_268882.pdf"

# Configure Docling with OCR (exact pattern from test_exp3a)
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

print("Converting document...")
result = converter.convert(pdf_path)
doc: DoclingDocument = result.document

print("\n" + "="*70)
print("SECTION INSPECTION")
print("="*70)

count = 0
for item, level in doc.iterate_items():
    if isinstance(item, SectionHeaderItem):
        count += 1
        if count > 5:  # Only show first 5 sections
            break

        print(f"\nSection #{count}: {item.text}")
        print(f"  Level: {level}")

        # Check different ways to get page number
        print(f"  hasattr(item, 'page'): {hasattr(item, 'page')}")
        print(f"  getattr(item, 'page', None): {getattr(item, 'page', None)}")

        # Check provenance
        if hasattr(item, 'prov') and item.prov:
            print(f"  item.prov type: {type(item.prov)}")
            print(f"  item.prov length: {len(item.prov)}")
            if len(item.prov) > 0:
                prov_item = item.prov[0]
                print(f"  prov[0] type: {type(prov_item)}")
                print(f"  prov[0] attributes: {[a for a in dir(prov_item) if not a.startswith('_')][:10]}")
                if hasattr(prov_item, 'page_no'):
                    print(f"  ✅ prov[0].page_no: {prov_item.page_no}")
                if hasattr(prov_item, 'bbox'):
                    print(f"  prov[0].bbox: {prov_item.bbox}")

print(f"\n\nTotal sections found: {count}")
