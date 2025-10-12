#!/usr/bin/env python3
"""
Test Governance Fix - Task Card #1 Step 1.4
Run extraction on 5-PDF sample to validate governance improvements.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic


def load_sample_pdfs(sample_file: Path) -> List[str]:
    """Load PDF IDs from sample file."""
    pdf_ids = []
    with open(sample_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                pdf_ids.append(line)
    return pdf_ids


def find_pdf_path(pdf_id: str) -> Path:
    """Find PDF path in test directories."""
    # Try Hjorthagen (root-level directory)
    hjorthagen_path = Path(f"Hjorthagen/{pdf_id}.pdf")
    if hjorthagen_path.exists():
        return hjorthagen_path

    # Try SRS (root-level directory)
    srs_path = Path(f"SRS/{pdf_id}.pdf")
    if srs_path.exists():
        return srs_path

    raise FileNotFoundError(f"PDF not found: {pdf_id}")


def load_original_result(pdf_id: str, original_dir: Path) -> Dict[str, Any]:
    """Load original extraction result from Week 3 comprehensive test."""
    # Search for file matching pattern *{pdf_id}*extraction.json
    matches = list(original_dir.glob(f"*{pdf_id}*extraction.json"))
    if matches:
        with open(matches[0]) as f:
            return json.load(f)

    return None


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


def compare_results(pdf_id: str, original: Dict, new: Dict) -> Dict[str, Any]:
    """Compare original vs new extraction results."""
    comparison = {
        'pdf_id': pdf_id,
        'original': {},
        'new': {},
        'improvement': {}
    }

    # Extract board members
    original_members = extract_board_members(original) if original else []
    new_members = extract_board_members(new)

    comparison['original']['board_member_count'] = len(original_members)
    comparison['new']['board_member_count'] = len(new_members)
    comparison['improvement']['member_count_delta'] = len(new_members) - len(original_members)

    # Coverage
    original_coverage = original.get('coverage_percentage', 0) if original else 0
    new_coverage = new.get('coverage_percentage', 0)

    comparison['original']['coverage'] = original_coverage
    comparison['new']['coverage'] = new_coverage
    comparison['improvement']['coverage_delta'] = new_coverage - original_coverage

    # Status
    original_status = 'success' if len(original_members) > 0 else 'failed'
    new_status = 'success' if len(new_members) > 0 else 'failed'

    comparison['original']['status'] = original_status
    comparison['new']['status'] = new_status
    comparison['improvement']['fixed'] = (original_status == 'failed' and new_status == 'success')

    return comparison


def main():
    """Main execution."""
    print("=" * 80)
    print("🔧 GOVERNANCE FIX VALIDATION TEST")
    print("=" * 80)

    # Load sample PDFs
    sample_file = Path("data/test_sample_governance.txt")
    if not sample_file.exists():
        print(f"❌ Error: Sample file not found: {sample_file}")
        sys.exit(1)

    pdf_ids = load_sample_pdfs(sample_file)
    print(f"\n📂 Loaded {len(pdf_ids)} PDFs from sample file")
    print(f"   PDFs: {', '.join(pdf_ids)}")

    # Original results directory
    original_dir = Path("data/week3_comprehensive_test_results")

    # New results directory
    new_dir = Path("data/governance_fix_test_results")
    new_dir.mkdir(exist_ok=True)

    # Run extractions
    results = []
    for i, pdf_id in enumerate(pdf_ids, 1):
        print(f"\n{'='*80}")
        print(f"📄 Processing {i}/{len(pdf_ids)}: {pdf_id}")
        print(f"{'='*80}")

        try:
            # Find PDF path
            pdf_path = find_pdf_path(pdf_id)
            print(f"   Found: {pdf_path}")

            # Load original result
            original = load_original_result(pdf_id, original_dir)
            if original:
                orig_members = extract_board_members(original)
                print(f"   Original: {len(orig_members)} board members, {original.get('coverage_percentage', 0):.1f}% coverage")
            else:
                print(f"   Original: No result found")

            # Run new extraction (fast mode for speed)
            print(f"   Running new extraction...")
            report = extract_brf_to_pydantic(str(pdf_path), mode="fast")

            # Save new result
            result_dict = report.model_dump()
            result_file = new_dir / f"{pdf_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)

            # Compare
            comparison = compare_results(pdf_id, original, result_dict)
            results.append(comparison)

            # Print summary
            new_members = extract_board_members(result_dict)
            print(f"   New:      {len(new_members)} board members, {result_dict.get('coverage_percentage', 0):.1f}% coverage")
            print(f"   Status:   {comparison['improvement']['fixed'] and '✅ FIXED!' or (comparison['new']['status'] == 'success' and '✅ Still working' or '❌ Still failing')}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'pdf_id': pdf_id,
                'error': str(e)
            })

    # Generate summary report
    print(f"\n{'='*80}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*80}")

    fixed_count = sum(1 for r in results if r.get('improvement', {}).get('fixed', False))
    success_count = sum(1 for r in results if r.get('new', {}).get('status') == 'success')

    print(f"\n✅ Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print(f"🔧 Fixed PDFs: {fixed_count}/{len(results)}")

    print(f"\n📋 Detailed Results:")
    for r in results:
        if 'error' in r:
            print(f"   ❌ {r['pdf_id']}: ERROR - {r['error']}")
        else:
            status_icon = '✅' if r['improvement']['fixed'] else ('✅' if r['new']['status'] == 'success' else '❌')
            delta = r['improvement']['member_count_delta']
            print(f"   {status_icon} {r['pdf_id']}: {r['original']['board_member_count']} → {r['new']['board_member_count']} members ({delta:+d})")

    # Save summary
    summary_file = new_dir / "validation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_pdfs': len(results),
            'success_count': success_count,
            'fixed_count': fixed_count,
            'results': results
        }, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {new_dir}/")
    print(f"   - Individual results: {len(results)} JSON files")
    print(f"   - Summary: validation_summary.json")

    print(f"\n{'='*80}")

    # Exit code
    return 0 if fixed_count >= 1 else 1  # Success if at least 1 PDF fixed


if __name__ == "__main__":
    sys.exit(main())
