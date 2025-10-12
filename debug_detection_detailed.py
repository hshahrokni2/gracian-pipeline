#!/usr/bin/env python3
"""
Detailed debug of detection logic with actual table data
"""

import sys
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

print('=' * 80)
print('DETAILED DETECTION LOGIC DEBUG')
print('=' * 80)

# Get base_result
extractor = RobustUltraComprehensiveExtractor()
base_result = extractor.extract_brf_document('SRS/brf_83301.pdf', mode='fast')

markdown = base_result['_docling_markdown']
tables = base_result['_docling_tables']

print(f'\n[Input Data]')
print(f'   Markdown length: {len(markdown):,} chars')
print(f'   Tables count: {len(tables)}')

# Manually execute Priority 2 logic with detailed logging
print(f'\n[Priority 2 Logic Execution]')
if len(tables) > 0:
    empty_table_count = 0

    for i, table in enumerate(tables, 1):
        data = table.get('data', [])

        print(f'\n   Table {i}:')
        print(f'      data type: {type(data)}')
        print(f'      data value: {data}')
        print(f'      len(data): {len(data) if data else 0}')

        # Check if table has no data
        if not data or len(data) == 0:
            print(f'      ✅ Empty (no data or len==0)')
            empty_table_count += 1
            continue

        # Check if first row is empty (malformed table)
        if isinstance(data, list) and len(data) > 0:
            first_row = data[0] if isinstance(data, list) else []
            print(f'      first_row type: {type(first_row)}')
            print(f'      first_row value: {first_row}')
            print(f'      first_row len: {len(first_row) if first_row else 0}')

            if not first_row or len(first_row) == 0:
                print(f'      ✅ Empty (first row empty)')
                empty_table_count += 1
            else:
                print(f'      ❌ Not empty (has {len(first_row)} columns)')

    empty_ratio = empty_table_count / len(tables) if len(tables) > 0 else 0

    print(f'\n[Results]')
    print(f'   Empty tables: {empty_table_count}/{len(tables)}')
    print(f'   Empty ratio: {empty_ratio*100:.1f}%')
    print(f'   Threshold check:')
    print(f'      empty_ratio > 0.5: {empty_ratio > 0.5}')
    print(f'      len(tables) >= 5: {len(tables) >= 5}')
    print(f'      SHOULD TRIGGER: {empty_ratio > 0.5 and len(tables) >= 5}')

print('\n' + '=' * 80)
