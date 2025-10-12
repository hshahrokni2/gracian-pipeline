#!/usr/bin/env python3
"""
Debug script to check what base_result actually contains
"""

import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

print('=' * 80)
print('DEBUGGING BASE_RESULT TABLES')
print('=' * 80)

# Initialize extractor (same as pydantic_extractor)
extractor = RobustUltraComprehensiveExtractor()

# Extract document (same call as pydantic_extractor)
print('\n[Step 1] Running base extraction (same as pydantic_extractor)...')
base_result = extractor.extract_brf_document('SRS/brf_83301.pdf', mode='fast')

# Check what keys are in base_result
print(f'\n[Step 2] Checking base_result keys...')
print(f'   Keys in base_result: {list(base_result.keys())}')

# Check for _docling keys
has_markdown = '_docling_markdown' in base_result
has_tables = '_docling_tables' in base_result

print(f'   Has _docling_markdown: {has_markdown}')
print(f'   Has _docling_tables: {has_tables}')

if has_markdown:
    markdown = base_result.get('_docling_markdown', '')
    print(f'   Markdown length: {len(markdown):,} chars')
else:
    print('   ❌ _docling_markdown NOT FOUND')

if has_tables:
    tables = base_result.get('_docling_tables', [])
    print(f'   Tables detected: {len(tables)}')

    # Analyze table structures
    if len(tables) > 0:
        print(f'\n[Step 3] Analyzing first 5 tables...')
        empty_count = 0
        for i, table in enumerate(tables[:5], 1):
            data = table.get('data', [])
            col_count = 0
            if data and len(data) > 0:
                first_row = data[0] if isinstance(data, list) else []
                col_count = len(first_row) if isinstance(first_row, list) else 0

            is_empty = col_count == 0
            if is_empty:
                empty_count += 1

            print(f'   Table {i}: {col_count} columns' + (' ✗ EMPTY' if is_empty else ''))

        total_empty = sum(1 for t in tables if (t.get('data', []) and len(t.get('data', [])[0] if isinstance(t.get('data', []), list) and len(t.get('data', [])) > 0 else []) == 0))
        empty_ratio = total_empty / len(tables) if len(tables) > 0 else 0
        print(f'\n   Total: {total_empty}/{len(tables)} empty ({empty_ratio*100:.1f}%)')
        print(f'   Meets criteria (>50% empty, ≥5 tables): {empty_ratio > 0.5 and len(tables) >= 5}')
else:
    print('   ❌ _docling_tables NOT FOUND')

# Test the mixed-mode detection with what we have
if has_markdown and has_tables:
    print(f'\n[Step 4] Testing mixed-mode detection...')
    from gracian_pipeline.utils.page_classifier import should_use_mixed_mode_extraction
    import fitz

    doc = fitz.open('SRS/brf_83301.pdf')
    total_pages = len(doc)
    doc.close()

    markdown = base_result['_docling_markdown']
    tables = base_result['_docling_tables']

    should_trigger, reason = should_use_mixed_mode_extraction(
        markdown,
        total_pages,
        tables=tables
    )

    print(f'   Should trigger: {should_trigger}')
    print(f'   Reason: {reason}')

print('\n' + '=' * 80)
