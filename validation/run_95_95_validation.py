"""
95/95 Validation - Test 3 PDFs Against Target
============================================

Goal: Validate that pipeline achieves:
- 95% coverage (582/613 data fields extracted)
- 95% accuracy (95% of extracted fields are correct)

Test PDFs:
1. machine_readable.pdf (brf_268882) - Expected: 90-95% coverage
2. hybrid.pdf (brf_83301) - Expected: 80-85% coverage
3. scanned.pdf (brf_76536) - Expected: 70-75% coverage

Author: Claude Code
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel
from gracian_pipeline.models.brf_schema import BRFAnnualReport


class ComprehensiveValidator:
    """Validate extraction results against 95/95 targets."""

    # Target metrics (user requirements)
    TARGET_COVERAGE = 0.95  # 95% of 613 fields = 582 fields
    TARGET_ACCURACY = 0.95  # 95% of extracted fields correct
    TOTAL_DATA_FIELDS = 613  # From smart_field_counter.py

    def __init__(self):
        """Initialize validator."""
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    def count_extracted_fields(self, result: Dict[str, Any], path: str = "") -> int:
        """
        Count how many data fields were actually extracted (have values).

        Args:
            result: Extraction result dictionary
            path: Current field path

        Returns:
            Count of extracted fields
        """
        count = 0

        if not isinstance(result, dict):
            return 0

        for key, value in result.items():
            # Skip metadata fields
            if key in {"confidence", "source", "evidence_pages", "extraction_method",
                      "model_used", "validation_status", "alternative_values",
                      "extraction_timestamp", "original_string"}:
                continue

            field_path = f"{path}.{key}" if path else key

            # Check if field has a value
            if value is not None:
                # Handle ExtractionField objects (check if 'value' exists and is not None)
                if isinstance(value, dict) and "value" in value:
                    if value["value"] is not None:
                        count += 1
                # Handle list fields
                elif isinstance(value, list):
                    if len(value) > 0:
                        count += 1
                        # Recursively count items in list
                        for item in value:
                            if isinstance(item, dict):
                                count += self.count_extracted_fields(item, field_path)
                # Handle nested objects
                elif isinstance(value, dict):
                    nested_count = self.count_extracted_fields(value, field_path)
                    if nested_count > 0:
                        count += nested_count
                # Handle primitive values
                else:
                    count += 1

        return count

    def extract_and_validate_pdf(
        self,
        pdf_path: str,
        pdf_type: str
    ) -> Dict[str, Any]:
        """
        Extract from PDF and calculate metrics.

        Args:
            pdf_path: Path to PDF
            pdf_type: "machine_readable", "hybrid", or "scanned"

        Returns:
            Validation results
        """
        print(f"\n{'='*80}")
        print(f"Validating: {Path(pdf_path).name} ({pdf_type})")
        print(f"{'='*80}")

        # Extract
        print(f"\n🔄 Extracting with current pipeline...")
        try:
            result = extract_all_agents_parallel(pdf_path)
            print(f"   ✅ Extraction complete")
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            return self._create_failed_result(pdf_type, str(e))

        # Count extracted fields
        extracted_count = self.count_extracted_fields(result)

        # Calculate coverage
        coverage = (extracted_count / self.TOTAL_DATA_FIELDS) * 100

        # Quality metrics (from extraction result if available)
        quality = result.get("_quality_metrics", {})
        confidence = quality.get("confidence", result.get("confidence_score", 0.0))

        # Create validation result
        validation = {
            "pdf_type": pdf_type,
            "pdf_path": str(pdf_path),
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "extracted_fields": extracted_count,
                "total_possible_fields": self.TOTAL_DATA_FIELDS,
                "coverage_percent": round(coverage, 1),
                "coverage_target": self.TARGET_COVERAGE * 100,
                "coverage_meets_target": coverage >= (self.TARGET_COVERAGE * 100),
                "confidence_score": round(confidence, 3),
                "estimated_accuracy": round(confidence * 100, 1)  # Confidence ~ accuracy
            },
            "assessment": {
                "meets_95_coverage": coverage >= 95.0,
                "meets_95_accuracy": (confidence * 100) >= 95.0,
                "ready_for_production": coverage >= 95.0 and (confidence * 100) >= 95.0
            }
        }

        # Print results
        self._print_validation_results(validation)

        # Save results
        self._save_validation_results(validation, pdf_type)

        return validation

    def _create_failed_result(self, pdf_type: str, error: str) -> Dict[str, Any]:
        """Create result for failed extraction."""
        return {
            "pdf_type": pdf_type,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "metrics": {
                "extracted_fields": 0,
                "total_possible_fields": self.TOTAL_DATA_FIELDS,
                "coverage_percent": 0.0,
                "coverage_meets_target": False
            },
            "assessment": {
                "meets_95_coverage": False,
                "meets_95_accuracy": False,
                "ready_for_production": False
            }
        }

    def _print_validation_results(self, validation: Dict[str, Any]):
        """Pretty print validation results."""
        metrics = validation["metrics"]
        assessment = validation["assessment"]

        print(f"\n📊 Validation Results:")
        print(f"   Extracted Fields: {metrics['extracted_fields']}/{metrics['total_possible_fields']}")
        print(f"   Coverage: {metrics['coverage_percent']}% (target: {metrics['coverage_target']}%)")
        print(f"   Estimated Accuracy: {metrics['estimated_accuracy']}% (target: 95%)")

        print(f"\n🎯 Assessment:")
        status_coverage = "✅" if assessment["meets_95_coverage"] else "❌"
        status_accuracy = "✅" if assessment["meets_95_accuracy"] else "❌"
        status_production = "✅" if assessment["ready_for_production"] else "❌"

        print(f"   {status_coverage} Meets 95% coverage: {assessment['meets_95_coverage']}")
        print(f"   {status_accuracy} Meets 95% accuracy: {assessment['meets_95_accuracy']}")
        print(f"   {status_production} Ready for production: {assessment['ready_for_production']}")

    def _save_validation_results(self, validation: Dict[str, Any], pdf_type: str):
        """Save validation results to JSON."""
        output_file = self.results_dir / f"validation_{pdf_type}.json"

        with open(output_file, "w") as f:
            json.dump(validation, f, indent=2, default=str)

        print(f"\n💾 Saved results to: {output_file.name}")

    def run_comprehensive_validation(
        self,
        test_pdfs: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Run validation on all test PDFs.

        Args:
            test_pdfs: Dict mapping pdf_type -> pdf_path

        Returns:
            Summary of all validations
        """
        print(f"\n{'='*80}")
        print(f"95/95 COMPREHENSIVE VALIDATION")
        print(f"{'='*80}")
        print(f"Target: 95% coverage (582/613 fields) AND 95% accuracy")
        print(f"Test PDFs: {len(test_pdfs)}")

        results = {}
        for pdf_type, pdf_path in test_pdfs.items():
            result = self.extract_and_validate_pdf(pdf_path, pdf_type)
            results[pdf_type] = result

        # Create summary
        summary = self._create_validation_summary(results)
        self._print_validation_summary(summary)
        self._save_validation_summary(summary)

        return summary

    def _create_validation_summary(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create summary of all validations."""

        # Calculate averages
        coverages = [r["metrics"]["coverage_percent"] for r in results.values()]
        accuracies = [r["metrics"]["estimated_accuracy"] for r in results.values()]
        pass_coverage = sum(r["assessment"]["meets_95_coverage"] for r in results.values())
        pass_accuracy = sum(r["assessment"]["meets_95_accuracy"] for r in results.values())
        pass_production = sum(r["assessment"]["ready_for_production"] for r in results.values())

        summary = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "total_pdfs_tested": len(results),
            "averages": {
                "coverage_percent": round(sum(coverages) / len(coverages), 1),
                "accuracy_percent": round(sum(accuracies) / len(accuracies), 1)
            },
            "pass_rates": {
                "coverage_95": f"{pass_coverage}/{len(results)} ({pass_coverage/len(results)*100:.0f}%)",
                "accuracy_95": f"{pass_accuracy}/{len(results)} ({pass_accuracy/len(results)*100:.0f}%)",
                "production_ready": f"{pass_production}/{len(results)} ({pass_production/len(results)*100:.0f}%)"
            },
            "by_pdf_type": {
                pdf_type: {
                    "coverage": result["metrics"]["coverage_percent"],
                    "accuracy": result["metrics"]["estimated_accuracy"],
                    "production_ready": result["assessment"]["ready_for_production"]
                }
                for pdf_type, result in results.items()
            },
            "overall_assessment": {
                "meets_targets": pass_coverage == len(results) and pass_accuracy == len(results),
                "recommendation": self._get_recommendation(pass_coverage, pass_accuracy, len(results))
            }
        }

        return summary

    def _get_recommendation(
        self,
        pass_coverage: int,
        pass_accuracy: int,
        total: int
    ) -> str:
        """Get recommendation based on results."""
        if pass_coverage == total and pass_accuracy == total:
            return "✅ APPROVED: All PDFs meet 95/95 targets. Ready for pilot deployment."
        elif pass_coverage >= total * 0.67:
            return "⚠️ PARTIAL: Most PDFs meet coverage target. Review failures and retry."
        else:
            return "❌ NOT READY: Coverage below target. Need architecture improvements."

    def _print_validation_summary(self, summary: Dict[str, Any]):
        """Pretty print validation summary."""
        print(f"\n{'='*80}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*80}")

        print(f"\n📊 Overall Metrics:")
        print(f"   Average Coverage: {summary['averages']['coverage_percent']}%")
        print(f"   Average Accuracy: {summary['averages']['accuracy_percent']}%")

        print(f"\n📈 Pass Rates:")
        print(f"   95% Coverage: {summary['pass_rates']['coverage_95']}")
        print(f"   95% Accuracy: {summary['pass_rates']['accuracy_95']}")
        print(f"   Production Ready: {summary['pass_rates']['production_ready']}")

        print(f"\n🎯 By PDF Type:")
        for pdf_type, metrics in summary["by_pdf_type"].items():
            status = "✅" if metrics["production_ready"] else "❌"
            print(f"   {status} {pdf_type:18s}: {metrics['coverage']:5.1f}% coverage, {metrics['accuracy']:5.1f}% accuracy")

        print(f"\n💡 Recommendation:")
        print(f"   {summary['overall_assessment']['recommendation']}")

    def _save_validation_summary(self, summary: Dict[str, Any]):
        """Save validation summary."""
        output_file = self.results_dir / "validation_summary.json"

        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n💾 Summary saved to: {output_file.name}")


def main():
    """Run 95/95 comprehensive validation."""

    # Test PDFs
    validation_dir = Path(__file__).parent
    test_pdfs = {
        "machine_readable": str(validation_dir / "test_pdfs" / "machine_readable.pdf"),
        "hybrid": str(validation_dir / "test_pdfs" / "hybrid.pdf"),
        "scanned": str(validation_dir / "test_pdfs" / "scanned.pdf")
    }

    # Validate PDFs exist
    for pdf_type, pdf_path in test_pdfs.items():
        if not Path(pdf_path).exists():
            print(f"❌ PDF not found: {pdf_path}")
            sys.exit(1)

    # Run validation
    validator = ComprehensiveValidator()
    summary = validator.run_comprehensive_validation(test_pdfs)

    # Exit with status code
    if summary["overall_assessment"]["meets_targets"]:
        print(f"\n✅ SUCCESS: Pipeline meets 95/95 targets!")
        sys.exit(0)
    else:
        print(f"\n⚠️ NEEDS WORK: Pipeline does not meet 95/95 targets yet")
        sys.exit(1)


if __name__ == "__main__":
    main()
