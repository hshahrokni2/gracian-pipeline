#!/usr/bin/env python3
"""
Analyze Failed Board Member Extractions
Task Card #1 Step 1.1: Identify which PDFs are missing board_members and why.

Expected: 8 PDFs failing (43 total - 35 successful = 8 failures)
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter


def load_extraction_results(results_dir: Path) -> List[Dict[str, Any]]:
    """Load all extraction result JSON files."""
    results = []
    for result_file in results_dir.glob("*.json"):
        try:
            with open(result_file) as f:
                data = json.load(f)
                data['_result_file'] = result_file.name
                results.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {result_file.name}: {e}")
    return results


def extract_board_members(result: Dict) -> List[Dict]:
    """Extract board_members from result (handles nested structure)."""
    # Try governance.board_members path
    if 'governance' in result:
        gov = result['governance']
        if isinstance(gov, dict) and 'board_members' in gov:
            members = gov['board_members']
            if isinstance(members, list):
                return members

    # Try top-level board_members
    if 'board_members' in result:
        members = result['board_members']
        if isinstance(members, list):
            return members

    return []


def analyze_failed_extractions(results: List[Dict]) -> Dict[str, Any]:
    """Analyze which PDFs are missing board_members and why."""
    analysis = {
        'total_pdfs': len(results),
        'successful': [],
        'failed': [],
        'success_rate': 0.0,
        'failure_patterns': Counter(),
        'pdf_type_distribution': Counter(),
        'coverage_distribution': []
    }

    for result in results:
        pdf_name = result.get('metadata', {}).get('file_path', result.get('_result_file', 'unknown'))
        if isinstance(pdf_name, str):
            pdf_name = Path(pdf_name).stem

        board_members = extract_board_members(result)
        coverage = result.get('coverage_percentage', result.get('extraction_quality', {}).get('coverage_percentage', 0))

        # Determine PDF type
        is_machine_readable = result.get('metadata', {}).get('is_machine_readable', None)
        pdf_type = 'machine-readable' if is_machine_readable else 'scanned' if is_machine_readable is False else 'unknown'
        analysis['pdf_type_distribution'][pdf_type] += 1

        if board_members and len(board_members) > 0:
            analysis['successful'].append({
                'pdf': pdf_name,
                'member_count': len(board_members),
                'coverage': coverage,
                'pdf_type': pdf_type
            })
        else:
            # Identify failure reason
            reason = 'unknown'
            if coverage == 0:
                reason = 'complete_extraction_failure'
            elif 'governance' not in result:
                reason = 'governance_section_missing'
            elif isinstance(result.get('governance'), dict) and 'board_members' in result['governance']:
                if result['governance']['board_members'] is None:
                    reason = 'board_members_null'
                elif result['governance']['board_members'] == []:
                    reason = 'board_members_empty_list'
            else:
                reason = 'board_members_field_missing'

            analysis['failure_patterns'][reason] += 1
            analysis['failed'].append({
                'pdf': pdf_name,
                'reason': reason,
                'coverage': coverage,
                'pdf_type': pdf_type
            })

    analysis['success_rate'] = len(analysis['successful']) / len(results) * 100 if results else 0
    analysis['coverage_distribution'] = [r.get('coverage', 0) for r in results]

    return analysis


def print_analysis_report(analysis: Dict[str, Any]):
    """Print comprehensive analysis report."""
    print("\n" + "="*80)
    print("📊 BOARD MEMBERS EXTRACTION ANALYSIS")
    print("="*80)

    print(f"\n🎯 Overall Summary:")
    print(f"   Total PDFs: {analysis['total_pdfs']}")
    print(f"   Successful: {len(analysis['successful'])} ({analysis['success_rate']:.1f}%)")
    print(f"   Failed: {len(analysis['failed'])} ({100-analysis['success_rate']:.1f}%)")

    print(f"\n📈 PDF Type Distribution:")
    for pdf_type, count in analysis['pdf_type_distribution'].items():
        pct = count / analysis['total_pdfs'] * 100
        print(f"   {pdf_type}: {count} ({pct:.1f}%)")

    print(f"\n❌ Failure Patterns:")
    for reason, count in analysis['failure_patterns'].most_common():
        pct = count / len(analysis['failed']) * 100 if analysis['failed'] else 0
        print(f"   {reason}: {count} ({pct:.1f}%)")

    print(f"\n🔴 Failed PDFs (Detail):")
    for failure in analysis['failed']:
        print(f"   • {failure['pdf']}")
        print(f"     - Reason: {failure['reason']}")
        print(f"     - Coverage: {failure['coverage']:.1f}%")
        print(f"     - Type: {failure['pdf_type']}")

    print(f"\n✅ Successful PDFs (Sample - First 5):")
    for success in analysis['successful'][:5]:
        print(f"   • {success['pdf']}: {success['member_count']} members, {success['coverage']:.1f}% coverage ({success['pdf_type']})")

    if len(analysis['successful']) > 5:
        print(f"   ... and {len(analysis['successful']) - 5} more")

    print("\n" + "="*80)
    print("📝 RECOMMENDATIONS")
    print("="*80)

    # Generate recommendations based on failure patterns
    if 'complete_extraction_failure' in analysis['failure_patterns']:
        print("\n⚠️  Complete Extraction Failures:")
        print("   - These PDFs have 0% coverage (not just board_members)")
        print("   - Root cause: Likely scanned PDFs with OCR issues")
        print("   - Fix: Improve vision extraction or OCR preprocessing")

    if 'board_members_field_missing' in analysis['failure_patterns']:
        print("\n⚠️  Board Members Field Missing:")
        print("   - Governance section exists but board_members field is absent")
        print("   - Root cause: Schema mismatch or prompt not requesting board_members")
        print("   - Fix: Update governance_agent prompt to explicitly request board_members list")

    if 'board_members_empty_list' in analysis['failure_patterns']:
        print("\n⚠️  Board Members Empty List:")
        print("   - Field exists but contains no members []")
        print("   - Root cause: Extraction found nothing or failed to parse")
        print("   - Fix: Add fallback synonyms (styrelsen, styrelseledamöter, etc.)")

    print("\n" + "="*80)


def main():
    """Main execution."""
    results_dir = Path("data/week3_comprehensive_test_results")

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    print("📂 Loading extraction results...")
    results = load_extraction_results(results_dir)

    if not results:
        print("❌ Error: No results found")
        sys.exit(1)

    print(f"✅ Loaded {len(results)} results")

    print("\n🔍 Analyzing board member extractions...")
    analysis = analyze_failed_extractions(results)

    print_analysis_report(analysis)

    # Save detailed analysis to JSON
    output_file = Path("data/board_members_failure_analysis.json")
    with open(output_file, 'w') as f:
        # Convert Counter objects to dicts for JSON serialization
        analysis_json = {
            **analysis,
            'failure_patterns': dict(analysis['failure_patterns']),
            'pdf_type_distribution': dict(analysis['pdf_type_distribution'])
        }
        json.dump(analysis_json, f, indent=2)

    print(f"\n💾 Detailed analysis saved to: {output_file}")

    # Exit code based on expected failure count (8 expected)
    expected_failures = 8
    actual_failures = len(analysis['failed'])
    if actual_failures == expected_failures:
        print(f"\n✅ Success: Found expected {expected_failures} failures")
        return 0
    else:
        print(f"\n⚠️  Warning: Expected {expected_failures} failures, found {actual_failures}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
