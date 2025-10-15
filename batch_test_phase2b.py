#!/usr/bin/env python3
"""
Batch Test Script for Phase 2B - 10 PDF Comprehensive Validation

Tests Phase 2B validation system on 10 diverse PDFs:
- 3 baseline PDFs (already tested individually)
- 7 newly selected PDFs (diverse categories)

Metrics Collected:
- Validation warnings (high/medium/low severity)
- Conflicts resolved (majority/weighted/evidence strategies)
- Processing time per PDF
- Agent success rates
- Token usage (if available)

Date: 2025-10-14
Phase: Phase 2B Hour 2 Phase 2 - Batch Testing
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import test script
from test_phase2b_integration import test_phase2b_integration


def load_test_corpus() -> List[str]:
    """Load 10-PDF test corpus (3 baseline + 7 selected)"""

    # Load selected PDFs
    selection_file = Path("test_corpus_selection.json")

    if not selection_file.exists():
        print("❌ Error: test_corpus_selection.json not found!")
        print("   Run quick_classify_pdfs.py first to select test corpus")
        sys.exit(1)

    with open(selection_file) as f:
        selection = json.load(f)

    selected_pdfs = selection["selected_pdfs"]

    # Deduplicate (baseline PDFs already in selected list)
    all_pdfs = list(set(selected_pdfs))

    print(f"📋 Loaded {len(all_pdfs)} PDFs for testing")
    print(f"   (3 baseline + 7 selected = 10 total)")

    return all_pdfs


def run_batch_test(pdf_paths: List[str], verbose: bool = True) -> Dict[str, Any]:
    """
    Run Phase 2B validation on all PDFs and collect metrics

    Args:
        pdf_paths: List of PDF file paths to test
        verbose: Print detailed progress

    Returns:
        Comprehensive test results dictionary
    """

    results = {
        "test_run": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_pdfs": len(pdf_paths),
            "phase": "Phase 2B Hour 2 Phase 2 - Batch Testing"
        },
        "per_pdf_results": [],
        "aggregate_metrics": {},
        "errors": []
    }

    print("\n" + "="*80)
    print("🧪 PHASE 2B BATCH TESTING - 10 PDFs")
    print("="*80 + "\n")

    for i, pdf_path in enumerate(pdf_paths, 1):
        pdf_name = Path(pdf_path).name
        print(f"\n📄 [{i}/{len(pdf_paths)}] Testing: {pdf_name}")
        print("-" * 60)

        try:
            # Run Phase 2B validation
            start_time = time.time()

            # Call test function (returns True/False for success)
            # We need to capture the actual results, not just success flag
            # So let's run the extraction directly

            from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel

            extraction_result = extract_all_agents_parallel(
                pdf_path=pdf_path,
                verbose=verbose
            )

            elapsed_time = time.time() - start_time

            # Extract validation metadata
            validation = extraction_result.get('_validation', {})

            if not validation:
                print("   ⚠️  WARNING: No validation metadata found!")
                print("       This suggests Phase 2B validation did not run")

            warnings = validation.get('warnings', [])
            warnings_count = validation.get('warnings_count', 0)
            high_severity_count = validation.get('high_severity_count', 0)
            rules_triggered = validation.get('rules_triggered', [])
            conflicts_resolved = validation.get('conflicts_resolved', 0)

            # Count severity levels
            medium_severity = sum(1 for w in warnings if w.get('severity') == 'medium')
            low_severity = sum(1 for w in warnings if w.get('severity') == 'low')

            # Count agent successes
            agents_tested = 0
            agents_succeeded = 0
            for key, value in extraction_result.items():
                if key.endswith('_agent') and not key.startswith('_'):
                    agents_tested += 1
                    if value and isinstance(value, dict) and value != {}:
                        agents_succeeded += 1

            # Store results
            pdf_result = {
                "pdf_name": pdf_name,
                "pdf_path": pdf_path,
                "success": True,
                "processing_time_seconds": round(elapsed_time, 2),
                "validation": {
                    "warnings_count": warnings_count,
                    "high_severity": high_severity_count,
                    "medium_severity": medium_severity,
                    "low_severity": low_severity,
                    "rules_triggered": rules_triggered,
                    "conflicts_resolved": conflicts_resolved
                },
                "agents": {
                    "tested": agents_tested,
                    "succeeded": agents_succeeded,
                    "success_rate": round(agents_succeeded / agents_tested * 100, 1) if agents_tested > 0 else 0.0
                },
                "extraction_result": extraction_result  # Full results for analysis
            }

            results["per_pdf_results"].append(pdf_result)

            # Print summary
            print(f"   ✅ Success in {elapsed_time:.1f}s")
            print(f"      Warnings: {warnings_count} "
                  f"(High: {high_severity_count}, Medium: {medium_severity}, Low: {low_severity})")
            print(f"      Rules Triggered: {', '.join(rules_triggered) if rules_triggered else 'None'}")
            print(f"      Conflicts Resolved: {conflicts_resolved}")
            print(f"      Agents: {agents_succeeded}/{agents_tested} ({pdf_result['agents']['success_rate']}%)")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

            # Store error
            error_result = {
                "pdf_name": pdf_name,
                "pdf_path": pdf_path,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

            results["per_pdf_results"].append(error_result)
            results["errors"].append(error_result)

    # Calculate aggregate metrics
    print("\n" + "="*80)
    print("📊 AGGREGATE METRICS")
    print("="*80 + "\n")

    successful_tests = [r for r in results["per_pdf_results"] if r.get("success", False)]
    failed_tests = results["errors"]

    if successful_tests:
        total_warnings = sum(r["validation"]["warnings_count"] for r in successful_tests)
        total_high = sum(r["validation"]["high_severity"] for r in successful_tests)
        total_medium = sum(r["validation"]["medium_severity"] for r in successful_tests)
        total_low = sum(r["validation"]["low_severity"] for r in successful_tests)
        total_conflicts = sum(r["validation"]["conflicts_resolved"] for r in successful_tests)

        avg_processing_time = sum(r["processing_time_seconds"] for r in successful_tests) / len(successful_tests)
        avg_agent_success_rate = sum(r["agents"]["success_rate"] for r in successful_tests) / len(successful_tests)

        # Collect all rules triggered
        all_rules = set()
        for r in successful_tests:
            all_rules.update(r["validation"]["rules_triggered"])

        results["aggregate_metrics"] = {
            "success_rate": round(len(successful_tests) / len(pdf_paths) * 100, 1),
            "total_warnings": total_warnings,
            "avg_warnings_per_pdf": round(total_warnings / len(successful_tests), 1),
            "severity_distribution": {
                "high": total_high,
                "medium": total_medium,
                "low": total_low
            },
            "total_conflicts_resolved": total_conflicts,
            "avg_conflicts_per_pdf": round(total_conflicts / len(successful_tests), 1),
            "avg_processing_time_seconds": round(avg_processing_time, 1),
            "avg_agent_success_rate": round(avg_agent_success_rate, 1),
            "unique_rules_triggered": sorted(list(all_rules)),
            "rule_coverage": f"{len(all_rules)}/10 validation rules"
        }

        # Print aggregate metrics
        print(f"Success Rate: {results['aggregate_metrics']['success_rate']}% "
              f"({len(successful_tests)}/{len(pdf_paths)} PDFs)")
        print(f"\nValidation Warnings:")
        print(f"  Total: {total_warnings} warnings across {len(successful_tests)} PDFs")
        print(f"  Average: {results['aggregate_metrics']['avg_warnings_per_pdf']} warnings/PDF")
        print(f"  Severity: High={total_high}, Medium={total_medium}, Low={total_low}")
        print(f"\nConflict Resolution:")
        print(f"  Total: {total_conflicts} conflicts resolved")
        print(f"  Average: {results['aggregate_metrics']['avg_conflicts_per_pdf']} conflicts/PDF")
        print(f"\nProcessing Performance:")
        print(f"  Average Time: {results['aggregate_metrics']['avg_processing_time_seconds']}s/PDF")
        print(f"  Average Agent Success: {results['aggregate_metrics']['avg_agent_success_rate']}%")
        print(f"\nValidation Rule Coverage:")
        print(f"  Rules Triggered: {len(all_rules)}/10")
        print(f"  Active Rules: {', '.join(sorted(all_rules)) if all_rules else 'None'}")

    else:
        print("❌ No successful tests to analyze!")
        results["aggregate_metrics"] = {
            "success_rate": 0.0,
            "error_message": "All tests failed"
        }

    if failed_tests:
        print(f"\n⚠️  Failed Tests: {len(failed_tests)}")
        for error in failed_tests:
            print(f"   - {error['pdf_name']}: {error['error_type']}")

    return results


def save_results(results: Dict[str, Any], output_path: str = "phase2b_batch_test_results.json"):
    """Save test results to JSON file"""

    output_file = Path(output_path)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    print(f"   Size: {output_file.stat().st_size:,} bytes")


def main():
    """Main execution"""

    print("\n" + "="*80)
    print("🚀 PHASE 2B BATCH TESTING")
    print("="*80)
    print("\nObjective: Test Phase 2B validation on 10 diverse PDFs")
    print("Metrics: Warnings, conflicts, time, agent success\n")

    # Load test corpus
    pdf_paths = load_test_corpus()

    # Run batch test
    results = run_batch_test(pdf_paths, verbose=False)  # Set to True for detailed output

    # Save results
    save_results(results)

    # Final summary
    print("\n" + "="*80)
    print("✅ BATCH TESTING COMPLETE")
    print("="*80)

    if results["aggregate_metrics"].get("success_rate", 0) >= 80:
        print("\n🎉 SUCCESS: ≥80% success rate achieved!")
    else:
        print(f"\n⚠️  WARNING: Only {results['aggregate_metrics'].get('success_rate', 0)}% success rate")

    print(f"\nNext: Analyze results in phase2b_batch_test_results.json")
    print(f"      Calculate accuracy improvement metrics")


if __name__ == "__main__":
    main()
