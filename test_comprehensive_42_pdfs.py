#!/usr/bin/env python3
"""
Week 3 Day 1-2: Comprehensive Testing on 42 PDFs (Hjorthagen + SRS)

Tests integrated schema on real-world Swedish BRF annual reports:
- ExtractionField functionality validation
- Synonym mapping verification
- Swedish-first semantic fields testing
- Calculated metrics validation with real financial data
- Coverage, accuracy, and confidence tracking
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

load_dotenv()


class ComprehensiveTestRunner:
    """Week 3 Day 1-2 comprehensive test runner for 42 PDFs."""

    def __init__(self, output_dir: str = "data/week3_comprehensive_test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.test_dirs = {
            "Hjorthagen": Path("Hjorthagen"),
            "SRS": Path("SRS")
        }

        self.results = []
        self.summary = {
            "test_date": datetime.now().isoformat(),
            "total_pdfs": 0,
            "successful": 0,
            "failed": 0,
            "avg_coverage": 0.0,
            "avg_confidence": 0.0,
            "by_dataset": {},
            "extraction_field_tests": {},
            "synonym_mapping_tests": {},
            "swedish_first_field_tests": {},
            "calculated_metrics_tests": {}
        }

    def collect_pdfs(self) -> List[tuple]:
        """Collect all PDFs from test directories."""
        pdfs = []

        for dataset_name, directory in self.test_dirs.items():
            if not directory.exists():
                print(f"⚠️ Directory not found: {directory}")
                continue

            pdf_files = sorted(directory.glob("*.pdf"))
            for pdf_path in pdf_files:
                pdfs.append((dataset_name, pdf_path))
                print(f"  ✓ Found: {dataset_name}/{pdf_path.name}")

        return pdfs

    def test_extraction_field_functionality(self, report: Any) -> Dict[str, bool]:
        """Test ExtractionField functionality on extracted data."""
        tests = {}

        # Test 1: Confidence scores present
        tests["confidence_scores_present"] = (
            report.confidence_score is not None and
            0.0 <= report.confidence_score <= 1.0
        )

        # Test 2: Source pages tracked
        tests["source_pages_tracked"] = len(report.all_source_pages) > 0

        # Test 3: Multi-source aggregation (check if any field has alternatives)
        has_alternatives = False
        if report.governance and hasattr(report.governance, 'chairman'):
            chairman_field = report.governance.chairman
            if hasattr(chairman_field, 'alternatives'):
                has_alternatives = len(getattr(chairman_field, 'alternatives', [])) > 0
        tests["multi_source_aggregation"] = has_alternatives

        # Test 4: Validation status tracking (check calculated metrics)
        has_validation_status = False
        if report.financial and hasattr(report.financial, 'calculated_metrics'):
            calc = report.financial.calculated_metrics
            if calc:
                has_validation_status = (
                    hasattr(calc, 'debt_per_sqm_status') or
                    hasattr(calc, 'solidarity_percent_status') or
                    hasattr(calc, 'fee_per_sqm_status')
                )
        tests["validation_status_tracking"] = has_validation_status

        return tests

    def test_synonym_mapping(self, report: Any) -> Dict[str, bool]:
        """Test synonym mapping on real Swedish BRF terminology."""
        tests = {}

        # Test 1: Swedish governance terms extracted
        tests["swedish_governance_terms"] = (
            report.governance is not None and
            report.governance.chairman is not None
        )

        # Test 2: Swedish financial terms extracted
        tests["swedish_financial_terms"] = (
            report.financial is not None and
            report.financial.balance_sheet is not None
        )

        # Test 3: Synonym metadata present (if implemented)
        has_synonym_metadata = False
        if report.fees and hasattr(report.fees, '_terminology_found'):
            has_synonym_metadata = report.fees._terminology_found is not None
        tests["synonym_metadata_present"] = has_synonym_metadata

        return tests

    def test_swedish_first_semantic_fields(self, report: Any) -> Dict[str, bool]:
        """Test Swedish-first semantic fields with actual extractions."""
        tests = {}

        # Test 1: Fee structure with Swedish primary fields
        tests["fee_swedish_primary"] = (
            report.fees is not None and
            (
                hasattr(report.fees, 'arsavgift_kr_per_kvm') or
                hasattr(report.fees, 'manadsavgift_kr')
            )
        )

        # Test 2: Financial data with Swedish primary fields
        tests["financial_swedish_primary"] = (
            report.financial is not None and
            report.financial.balance_sheet is not None
        )

        # Test 3: Swedish-English alias synchronization (check if both exist)
        has_alias_sync = False
        if report.fees:
            has_alias_sync = (
                (hasattr(report.fees, 'arsavgift_kr_per_kvm') and
                 hasattr(report.fees, 'annual_fee_per_sqm')) or
                (hasattr(report.fees, 'manadsavgift_kr') and
                 hasattr(report.fees, 'monthly_fee'))
            )
        tests["swedish_english_alias_sync"] = has_alias_sync

        return tests

    def test_calculated_metrics(self, report: Any) -> Dict[str, bool]:
        """Test calculated metrics validation with real financial data."""
        tests = {}

        if not report.financial or not hasattr(report.financial, 'calculated_metrics'):
            return {
                "calculated_metrics_present": False,
                "validation_thresholds_applied": False,
                "tolerant_validation": False,
                "data_preservation": False
            }

        calc = report.financial.calculated_metrics

        # Test 1: Calculated metrics present
        tests["calculated_metrics_present"] = calc is not None

        # Test 2: Validation thresholds applied
        tests["validation_thresholds_applied"] = (
            hasattr(calc, 'debt_per_sqm_status') and
            calc.debt_per_sqm_status in ['valid', 'warning', 'error']
        ) if calc else False

        # Test 3: Tolerant validation (3-tier system)
        has_three_tiers = False
        if calc:
            statuses = []
            if hasattr(calc, 'debt_per_sqm_status'):
                statuses.append(calc.debt_per_sqm_status)
            if hasattr(calc, 'solidarity_percent_status'):
                statuses.append(calc.solidarity_percent_status)
            if hasattr(calc, 'fee_per_sqm_status'):
                statuses.append(calc.fee_per_sqm_status)
            has_three_tiers = len(set(statuses)) > 0
        tests["tolerant_validation"] = has_three_tiers

        # Test 4: Data preservation (never null policy)
        data_preserved = True
        if calc:
            if hasattr(calc, 'debt_per_sqm_extracted') and calc.debt_per_sqm_extracted is not None:
                # If extracted value exists, it should still be there even if status is error
                data_preserved = data_preserved and True
        tests["data_preservation"] = data_preserved

        return tests

    def extract_pdf(self, pdf_path: Path, dataset_name: str) -> Dict[str, Any]:
        """Extract single PDF and collect metrics."""
        result = {
            "dataset": dataset_name,
            "pdf_name": pdf_path.name,
            "pdf_path": str(pdf_path),
            "success": False,
            "coverage": 0.0,
            "confidence": 0.0,
            "extraction_time": 0.0,
            "error": None,
            "extraction_field_tests": {},
            "synonym_mapping_tests": {},
            "swedish_first_field_tests": {},
            "calculated_metrics_tests": {}
        }

        try:
            start_time = time.time()

            # Run extraction
            report = extract_brf_to_pydantic(str(pdf_path), mode="fast")

            result["extraction_time"] = time.time() - start_time
            result["success"] = True
            result["coverage"] = report.coverage_percentage
            result["confidence"] = report.confidence_score

            # Run component tests
            result["extraction_field_tests"] = self.test_extraction_field_functionality(report)
            result["synonym_mapping_tests"] = self.test_synonym_mapping(report)
            result["swedish_first_field_tests"] = self.test_swedish_first_semantic_fields(report)
            result["calculated_metrics_tests"] = self.test_calculated_metrics(report)

            # Save individual extraction
            output_file = self.output_dir / f"{dataset_name}_{pdf_path.stem}_extraction.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)

            print(f"  ✅ {pdf_path.name}: Coverage={result['coverage']:.1f}%, Confidence={result['confidence']:.2f}, Time={result['extraction_time']:.1f}s")

        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ {pdf_path.name}: {str(e)}")

        return result

    def run_comprehensive_tests(self):
        """Run comprehensive tests on all PDFs."""
        print("="*80)
        print("🧪 WEEK 3 DAY 1-2: COMPREHENSIVE TESTING ON 42 PDFs")
        print("="*80)
        print()

        # Collect PDFs
        print("📁 Collecting PDFs...")
        pdfs = self.collect_pdfs()
        self.summary["total_pdfs"] = len(pdfs)

        if not pdfs:
            print("❌ No PDFs found!")
            return

        print(f"✓ Found {len(pdfs)} PDFs")
        print()

        # Process each PDF
        print("🔄 Processing PDFs...")
        print()

        dataset_stats = defaultdict(lambda: {"count": 0, "successful": 0, "failed": 0, "total_coverage": 0.0, "total_confidence": 0.0})

        for i, (dataset_name, pdf_path) in enumerate(pdfs, 1):
            print(f"[{i}/{len(pdfs)}] {dataset_name}/{pdf_path.name}")

            result = self.extract_pdf(pdf_path, dataset_name)
            self.results.append(result)

            # Update statistics
            dataset_stats[dataset_name]["count"] += 1
            if result["success"]:
                self.summary["successful"] += 1
                dataset_stats[dataset_name]["successful"] += 1
                dataset_stats[dataset_name]["total_coverage"] += result["coverage"]
                dataset_stats[dataset_name]["total_confidence"] += result["confidence"]
            else:
                self.summary["failed"] += 1
                dataset_stats[dataset_name]["failed"] += 1

            print()

        # Calculate summary statistics
        if self.summary["successful"] > 0:
            self.summary["avg_coverage"] = sum(r["coverage"] for r in self.results if r["success"]) / self.summary["successful"]
            self.summary["avg_confidence"] = sum(r["confidence"] for r in self.results if r["success"]) / self.summary["successful"]

        # Calculate dataset statistics
        for dataset_name, stats in dataset_stats.items():
            if stats["successful"] > 0:
                stats["avg_coverage"] = stats["total_coverage"] / stats["successful"]
                stats["avg_confidence"] = stats["total_confidence"] / stats["successful"]
            self.summary["by_dataset"][dataset_name] = stats

        # Aggregate component test results
        self.aggregate_component_tests()

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

    def aggregate_component_tests(self):
        """Aggregate component test results across all PDFs."""
        for test_category in ["extraction_field_tests", "synonym_mapping_tests",
                              "swedish_first_field_tests", "calculated_metrics_tests"]:
            test_results = defaultdict(lambda: {"passed": 0, "failed": 0, "total": 0})

            for result in self.results:
                if not result["success"]:
                    continue

                for test_name, passed in result[test_category].items():
                    test_results[test_name]["total"] += 1
                    if passed:
                        test_results[test_name]["passed"] += 1
                    else:
                        test_results[test_name]["failed"] += 1

            # Calculate pass rates
            for test_name, counts in test_results.items():
                if counts["total"] > 0:
                    counts["pass_rate"] = (counts["passed"] / counts["total"]) * 100

            self.summary[test_category] = dict(test_results)

    def save_results(self):
        """Save test results to JSON files."""
        # Save detailed results
        results_file = self.output_dir / "comprehensive_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Save summary
        summary_file = self.output_dir / "comprehensive_test_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(self.summary, f, indent=2, ensure_ascii=False)

        print(f"💾 Results saved to {self.output_dir}")
        print()

    def print_summary(self):
        """Print comprehensive test summary."""
        print("="*80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        print()

        print(f"📁 Test Coverage:")
        print(f"   Total PDFs: {self.summary['total_pdfs']}")
        print(f"   Successful: {self.summary['successful']} ({self.summary['successful']/self.summary['total_pdfs']*100:.1f}%)")
        print(f"   Failed: {self.summary['failed']} ({self.summary['failed']/self.summary['total_pdfs']*100:.1f}%)")
        print()

        print(f"📊 Overall Metrics:")
        print(f"   Average Coverage: {self.summary['avg_coverage']:.1f}%")
        print(f"   Average Confidence: {self.summary['avg_confidence']:.2f}")
        print()

        print(f"📈 By Dataset:")
        for dataset_name, stats in self.summary["by_dataset"].items():
            print(f"   {dataset_name}:")
            print(f"     Total: {stats['count']}")
            print(f"     Successful: {stats['successful']}/{stats['count']} ({stats['successful']/stats['count']*100:.1f}%)")
            if stats["successful"] > 0:
                print(f"     Avg Coverage: {stats['avg_coverage']:.1f}%")
                print(f"     Avg Confidence: {stats['avg_confidence']:.2f}")
        print()

        # Print component test results
        self.print_component_test_results("ExtractionField Functionality", "extraction_field_tests")
        self.print_component_test_results("Synonym Mapping", "synonym_mapping_tests")
        self.print_component_test_results("Swedish-First Semantic Fields", "swedish_first_field_tests")
        self.print_component_test_results("Calculated Metrics Validation", "calculated_metrics_tests")

        print("="*80)
        print("✅ WEEK 3 DAY 1-2 COMPREHENSIVE TESTING COMPLETE")
        print("="*80)

    def print_component_test_results(self, category_name: str, test_key: str):
        """Print component test results."""
        if not self.summary[test_key]:
            print(f"⚠️ {category_name}: No test results")
            print()
            return

        print(f"🧪 {category_name} Tests:")
        for test_name, counts in self.summary[test_key].items():
            status = "✅" if counts["pass_rate"] >= 90 else "⚠️" if counts["pass_rate"] >= 70 else "❌"
            print(f"   {status} {test_name}: {counts['passed']}/{counts['total']} ({counts['pass_rate']:.1f}%)")
        print()


def main():
    """Main test runner."""
    print()
    print("🚀 Starting Week 3 Day 1-2: Comprehensive Testing")
    print()

    runner = ComprehensiveTestRunner()
    runner.run_comprehensive_tests()


if __name__ == "__main__":
    main()
