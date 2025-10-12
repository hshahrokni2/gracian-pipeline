#!/usr/bin/env python3
"""
Comprehensive Extraction Validation Script
Compares extraction results against comprehensive ground truth
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from decimal import Decimal

def load_json(path: str) -> Dict:
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_value(obj, path: str) -> Any:
    """Get nested value using dot notation, handles ExtractionField.value pattern"""
    parts = path.split('.')
    current = obj

    for part in parts:
        if current is None:
            return None

        # Handle list index access
        if '[' in part:
            key = part[:part.index('[')]
            idx = int(part[part.index('[')+1:part.index(']')])
            current = current.get(key, [])
            if isinstance(current, list) and len(current) > idx:
                current = current[idx]
            else:
                return None
        else:
            current = current.get(part) if isinstance(current, dict) else None

    # Unwrap ExtractionField pattern {value: X, confidence: Y, ...}
    if isinstance(current, dict) and 'value' in current and 'confidence' in current:
        return current['value']

    return current

def format_value(val: Any) -> str:
    """Format value for display"""
    if val is None:
        return "❌ NOT FOUND"
    if isinstance(val, bool):
        return "✅ TRUE" if val else "❌ FALSE"
    if isinstance(val, (int, float)):
        # Format numbers with thousand separators
        if val > 1000:
            return f"{val:,.0f}"
        return str(val)
    if isinstance(val, list):
        return f"[{len(val)} items]" if val else "[]"
    if isinstance(val, dict):
        return f"{{{len(val)} keys}}"
    return str(val)

def compare_field(field_name: str, extracted: Any, ground_truth: Any) -> Dict[str, Any]:
    """Compare a single field"""
    result = {
        'field': field_name,
        'extracted': extracted,
        'ground_truth': ground_truth,
        'status': None,
        'note': None
    }

    # Both missing
    if extracted is None and ground_truth is None:
        result['status'] = 'both_none'
        result['note'] = 'Not in either document'
        return result

    # Ground truth present, extraction missing
    if extracted is None and ground_truth is not None:
        result['status'] = 'missing'
        result['note'] = f'MISSING: Should be "{ground_truth}"'
        return result

    # Extraction present, no ground truth (suspicious)
    if extracted is not None and ground_truth is None:
        result['status'] = 'extra'
        result['note'] = f'EXTRA: Extracted "{extracted}" but no ground truth'
        return result

    # Both present - compare
    if isinstance(ground_truth, (int, float)) and isinstance(extracted, (int, float, str)):
        # Numeric comparison
        try:
            ext_num = float(str(extracted).replace(',', '').replace(' ', ''))
            gt_num = float(ground_truth)
            diff = abs(ext_num - gt_num)
            pct_diff = (diff / gt_num * 100) if gt_num != 0 else 0

            if diff < 0.01:
                result['status'] = 'correct'
                result['note'] = '✅ Exact match'
            elif pct_diff < 1:
                result['status'] = 'correct'
                result['note'] = f'✅ Close match (<1% diff)'
            else:
                result['status'] = 'wrong'
                result['note'] = f'❌ WRONG: {pct_diff:.1f}% difference'
        except:
            result['status'] = 'wrong'
            result['note'] = f'❌ Type mismatch: extracted={type(extracted).__name__}, gt={type(ground_truth).__name__}'
    elif isinstance(ground_truth, str) and isinstance(extracted, str):
        # String comparison (case-insensitive)
        if extracted.lower().strip() == ground_truth.lower().strip():
            result['status'] = 'correct'
            result['note'] = '✅ Exact match'
        elif extracted.lower().strip() in ground_truth.lower().strip() or ground_truth.lower().strip() in extracted.lower().strip():
            result['status'] = 'partial'
            result['note'] = '⚠️ Partial match'
        else:
            result['status'] = 'wrong'
            result['note'] = f'❌ WRONG: extracted="{extracted}", gt="{ground_truth}"'
    elif isinstance(ground_truth, list) and isinstance(extracted, list):
        # List comparison
        if len(extracted) == len(ground_truth):
            result['status'] = 'correct'
            result['note'] = f'✅ Same count ({len(extracted)})'
        else:
            result['status'] = 'partial'
            result['note'] = f'⚠️ Count mismatch: extracted={len(extracted)}, gt={len(ground_truth)}'
    else:
        # Generic comparison
        if str(extracted).strip() == str(ground_truth).strip():
            result['status'] = 'correct'
            result['note'] = '✅ Match'
        else:
            result['status'] = 'wrong'
            result['note'] = f'❌ WRONG'

    return result

def validate_comprehensive():
    """Run comprehensive validation"""
    print("=" * 80)
    print("COMPREHENSIVE EXTRACTION VALIDATION")
    print("=" * 80)
    print()

    # Load files
    extraction = load_json('validation_extraction_brf_198532.json')
    ground_truth = load_json('ground_truth/brf_198532_comprehensive_ground_truth.json')

    # Define critical fields to validate
    critical_fields = {
        # METADATA
        'Metadata': [
            ('metadata.organization_number', 'metadata.organization_number'),
            ('metadata.brf_name', 'metadata.brf_name'),
            ('metadata.fiscal_year', 'metadata.fiscal_year'),
            ('metadata.municipality', 'metadata.municipality'),
        ],

        # GOVERNANCE
        'Governance': [
            ('governance.chairman', 'governance.board_members[0].name'),  # Chairman is first board member
            ('governance.board_members', 'governance.board_members'),  # Count comparison
            ('governance.primary_auditor.name', 'governance.auditors[0].name'),
            ('governance.primary_auditor.firm', 'governance.auditors[0].firm'),
            ('governance.nomination_committee', 'governance.nomination_committee'),
        ],

        # FINANCIAL - Balance Sheet
        'Financial (Balance Sheet)': [
            ('financial.balance_sheet.assets_total', 'financial.balance_sheet.2021.assets.total_assets'),
            ('financial.balance_sheet.liabilities_total', 'financial.balance_sheet.2021.equity_liabilities.short_term_liabilities.total'),
            ('financial.balance_sheet.equity_total', 'financial.balance_sheet.2021.equity_liabilities.equity.total_equity'),
        ],

        # FINANCIAL - Income Statement
        'Financial (Income)': [
            ('financial.income_statement.revenue_total', 'financial.income_statement.2021.revenue.total'),
            ('financial.income_statement.expenses_total', 'financial.income_statement.2021.operating_expenses.total'),
            ('financial.income_statement.result_after_tax', 'financial.income_statement.2021.result_after_financial'),
        ],

        # PROPERTY
        'Property': [
            ('property.municipality', 'property.properties[0].municipality'),
            ('property.total_apartments', 'apartments.total_count'),
            ('property.apartment_distribution', 'apartments.breakdown'),
        ],

        # FEES
        'Fees': [
            ('fees.annual_fee_per_sqm', 'key_ratios.2021.annual_fee_per_sqm'),
        ],

        # LOANS
        'Loans': [
            ('loans', 'loans'),  # Count comparison
        ],
    }

    # Run validation by category
    results_by_category = {}
    total_correct = 0
    total_checked = 0

    for category, fields in critical_fields.items():
        print(f"\n📊 {category}")
        print("-" * 80)

        category_results = []
        for ext_path, gt_path in fields:
            extracted = get_value(extraction, ext_path)
            gt_value = get_value(ground_truth, gt_path)

            result = compare_field(ext_path, extracted, gt_value)
            category_results.append(result)

            # Print result
            status_icon = {
                'correct': '✅',
                'partial': '⚠️',
                'wrong': '❌',
                'missing': '❌',
                'extra': '❓',
                'both_none': '⚪'
            }.get(result['status'], '❓')

            print(f"{status_icon} {result['field']}")
            print(f"   Extracted: {format_value(extracted)}")
            print(f"   Ground Truth: {format_value(gt_value)}")
            print(f"   {result['note']}")
            print()

            if result['status'] in ['correct', 'partial']:
                total_correct += 1
            if result['status'] != 'both_none':
                total_checked += 1

        results_by_category[category] = category_results

    # Summary
    print("=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)

    for category, results in results_by_category.items():
        correct = sum(1 for r in results if r['status'] in ['correct', 'partial'])
        total = sum(1 for r in results if r['status'] != 'both_none')
        pct = (correct / total * 100) if total > 0 else 0

        status_icon = '✅' if pct == 100 else '⚠️' if pct >= 50 else '❌'
        print(f"{status_icon} {category}: {correct}/{total} ({pct:.1f}%)")

    print()
    print(f"🎯 OVERALL ACCURACY: {total_correct}/{total_checked} ({total_correct/total_checked*100:.1f}%)")
    print()

    # Critical findings
    print("🔴 CRITICAL GAPS IDENTIFIED:")
    print("-" * 80)
    for category, results in results_by_category.items():
        missing = [r for r in results if r['status'] == 'missing']
        if missing:
            print(f"\n{category}:")
            for r in missing:
                print(f"  ❌ {r['field']}: {r['note']}")

    # Save detailed results
    output = {
        'summary': {
            'total_correct': total_correct,
            'total_checked': total_checked,
            'accuracy_percentage': round(total_correct/total_checked*100, 2) if total_checked > 0 else 0
        },
        'by_category': results_by_category,
        'timestamp': '2025-10-09'
    }

    with open('validation_detailed_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    print("\n💾 Detailed results saved to: validation_detailed_results.json")

if __name__ == '__main__':
    validate_comprehensive()
