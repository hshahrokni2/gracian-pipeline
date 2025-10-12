"""
Comprehensive 95/95 Validation Test

Tests that the Gracian Pipeline achieves:
- 95% Coverage: (fields extracted / ground truth fields) × 100
- 95% Accuracy: (correct values / total extractions) × 100

Uses comprehensive ground truth with 200+ data points from brf_198532.pdf
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor


@dataclass
class FieldComparison:
    """Result of comparing a single field"""
    field_path: str
    gt_value: Any
    extracted_value: Any
    match: bool
    tolerance_used: float = 0.0
    notes: str = ""


@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics"""
    coverage_percent: float
    accuracy_percent: float
    total_gt_fields: int
    extracted_fields: int
    correct_values: int
    incorrect_values: int
    missing_fields: int

    # Validation engine metrics
    validation_errors_found: int
    validation_warnings_found: int
    true_errors_detected: int  # Errors that match GT issues
    false_positives: int  # Errors flagged but GT is correct

    # Detailed field breakdown
    field_comparisons: List[FieldComparison]


class ComprehensiveValidator:
    """Validates extraction against comprehensive ground truth"""

    def __init__(self, ground_truth_path: str):
        """Load ground truth"""
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)

        # Numeric tolerance for financial values (5%)
        self.numeric_tolerance = 0.05

        # Mapping from ground truth keys to extraction agent keys
        self.gt_to_agent_mapping = {
            'metadata': 'docling_metadata',  # Metadata comes from docling
            'governance': 'governance_agent',
            'financial': 'financial_agent',
            'loans': 'loans_agent',
            'fees': 'fees_agent',
            'property': 'property_agent',
            'apartments': 'property_agent',  # Apartment data is in property agent
            'commercial_tenants': 'property_agent',
            'common_areas': 'property_agent',
            'maintenance': 'notes_maintenance_agent',
            'tax': 'notes_tax_agent',
            'events_significant_during_year': 'events_agent',
            'events_after_year_end': 'events_agent',
            'members': 'governance_agent',
            'personnel_note6': 'notes_maintenance_agent',
            'operating_costs_2021': 'financial_agent',
            'other_operating_income_2021': 'financial_agent',
            'revenue_breakdown_2021': 'financial_agent',
            'cash_flow_2020': 'cashflow_agent',
            'cash_flow_2021': 'cashflow_agent',
            'building_details_note8': 'property_agent',
            'receivables_note9_2021': 'financial_agent',
            'maintenance_fund_note10': 'reserves_agent',
            'accrued_expenses_note13_2021': 'financial_agent',
            'equity_changes': 'financial_agent',
            'result_disposition': 'financial_agent',
            'key_ratios': 'financial_agent',
            'contracts': 'notes_maintenance_agent',
            'collateral': 'loans_agent',
            'loan_policy': 'loans_agent',
            'accounting_principles': 'financial_agent',
            'total_loans_2020': 'loans_agent',
            'total_loans_2021': 'loans_agent',
            'vat_registered_commercial': 'property_agent',
            'statistical_data': 'property_agent',
            'source_pages': '_source_pages',  # Special field
        }

    def normalize_string(self, value: Any) -> str:
        """Normalize string for comparison"""
        if value is None:
            return ""
        s = str(value).strip()
        # Remove multiple spaces
        s = ' '.join(s.split())
        return s.lower()

    def normalize_number(self, value: Any) -> float:
        """Extract numeric value from various formats"""
        if value is None:
            return 0.0

        # If already a number
        if isinstance(value, (int, float)):
            return float(value)

        # If string, remove spaces and parse
        if isinstance(value, str):
            # Remove spaces used as thousands separator
            cleaned = value.replace(' ', '').replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        return 0.0

    def compare_values(self, gt_value: Any, extracted_value: Any, field_path: str) -> FieldComparison:
        """Compare ground truth value with extracted value"""

        # Handle ExtractionField wrapper
        if isinstance(extracted_value, dict) and 'value' in extracted_value:
            extracted_value = extracted_value['value']

        # If both are None or empty
        if (gt_value is None or gt_value == "") and (extracted_value is None or extracted_value == ""):
            return FieldComparison(field_path, gt_value, extracted_value, True, notes="Both empty")

        # If ground truth exists but extraction is missing
        if gt_value and not extracted_value:
            return FieldComparison(field_path, gt_value, extracted_value, False, notes="Missing in extraction")

        # Numeric comparison (for financial values)
        if isinstance(gt_value, (int, float)) or (isinstance(gt_value, str) and any(c.isdigit() for c in str(gt_value))):
            gt_num = self.normalize_number(gt_value)
            ex_num = self.normalize_number(extracted_value)

            # Skip if both are 0
            if gt_num == 0 and ex_num == 0:
                return FieldComparison(field_path, gt_value, extracted_value, True, notes="Both zero")

            # Skip if ground truth is 0 (no comparison possible)
            if gt_num == 0:
                return FieldComparison(field_path, gt_value, extracted_value, False, notes="GT is zero, cannot validate")

            # Calculate relative difference
            diff = abs(gt_num - ex_num) / abs(gt_num)

            if diff <= self.numeric_tolerance:
                return FieldComparison(field_path, gt_value, extracted_value, True, tolerance_used=diff, notes=f"Match within {diff*100:.1f}% tolerance")
            else:
                return FieldComparison(field_path, gt_value, extracted_value, False, tolerance_used=diff, notes=f"Difference: {diff*100:.1f}%")

        # String comparison
        gt_str = self.normalize_string(gt_value)
        ex_str = self.normalize_string(extracted_value)

        if gt_str == ex_str:
            return FieldComparison(field_path, gt_value, extracted_value, True, notes="Exact string match")

        # Partial match (substring)
        if gt_str in ex_str or ex_str in gt_str:
            return FieldComparison(field_path, gt_value, extracted_value, True, notes="Partial match")

        return FieldComparison(field_path, gt_value, extracted_value, False, notes="String mismatch")

    def flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.', is_ground_truth: bool = False) -> Dict[str, Any]:
        """Flatten nested dictionary to dot-notation paths

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for path
            is_ground_truth: If True, apply gt_to_agent_mapping to remap keys
        """
        items = []
        for k, v in d.items():
            # Apply mapping for ground truth top-level keys
            if is_ground_truth and not parent_key and k in self.gt_to_agent_mapping:
                mapped_key = self.gt_to_agent_mapping[k]
            else:
                mapped_key = k

            new_key = f"{parent_key}{sep}{mapped_key}" if parent_key else mapped_key

            # Skip metadata fields
            if new_key.startswith('_'):
                continue

            if isinstance(v, dict) and not ('value' in v and len(v) <= 3):
                # Recursively flatten, but not ExtractionField dicts
                items.extend(self.flatten_dict(v, new_key, sep=sep, is_ground_truth=is_ground_truth).items())
            elif isinstance(v, list):
                # Handle lists (e.g., loans, board_members)
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self.flatten_dict(item, f"{new_key}[{i}]", sep=sep, is_ground_truth=is_ground_truth).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))

        return dict(items)

    def validate(self, extraction_result: Dict[str, Any]) -> ValidationMetrics:
        """Comprehensive validation of extraction against ground truth"""

        print("\n" + "="*80)
        print("95/95 VALIDATION: Comparing Extraction vs Ground Truth")
        print("="*80)

        # Flatten both dictionaries for field-by-field comparison
        # Apply mapping when flattening ground truth to match extraction structure
        gt_flat = self.flatten_dict(self.ground_truth, is_ground_truth=True)
        ex_flat = self.flatten_dict(extraction_result, is_ground_truth=False)

        print(f"\nGround Truth Fields: {len(gt_flat)}")
        print(f"Extraction Fields: {len(ex_flat)}")

        # Field-by-field comparison
        field_comparisons = []
        extracted_fields = 0
        correct_values = 0
        incorrect_values = 0
        missing_fields = 0

        for field_path, gt_value in gt_flat.items():
            # Check if field was extracted
            extracted_value = ex_flat.get(field_path)

            if extracted_value is not None:
                extracted_fields += 1

                # Compare values
                comparison = self.compare_values(gt_value, extracted_value, field_path)
                field_comparisons.append(comparison)

                if comparison.match:
                    correct_values += 1
                else:
                    incorrect_values += 1
            else:
                missing_fields += 1
                field_comparisons.append(FieldComparison(
                    field_path, gt_value, None, False, notes="Field not extracted"
                ))

        # Calculate metrics
        coverage = (extracted_fields / len(gt_flat)) * 100 if len(gt_flat) > 0 else 0
        accuracy = (correct_values / extracted_fields) * 100 if extracted_fields > 0 else 0

        # Validation engine metrics
        validation_report = extraction_result.get("_validation_report", {})
        validation_errors = validation_report.get("error_count", 0)
        validation_warnings = validation_report.get("warning_count", 0)

        # TODO: Calculate true positives/false positives (requires analyzing validation issues)

        metrics = ValidationMetrics(
            coverage_percent=coverage,
            accuracy_percent=accuracy,
            total_gt_fields=len(gt_flat),
            extracted_fields=extracted_fields,
            correct_values=correct_values,
            incorrect_values=incorrect_values,
            missing_fields=missing_fields,
            validation_errors_found=validation_errors,
            validation_warnings_found=validation_warnings,
            true_errors_detected=0,  # Will be calculated
            false_positives=0,  # Will be calculated
            field_comparisons=field_comparisons
        )

        return metrics

    def print_report(self, metrics: ValidationMetrics):
        """Print comprehensive validation report"""

        print("\n" + "="*80)
        print("95/95 VALIDATION REPORT")
        print("="*80)

        # Overall metrics
        print(f"\n📊 OVERALL METRICS:")
        print(f"   Coverage:  {metrics.coverage_percent:.1f}% (Target: 95%)")
        print(f"   Accuracy:  {metrics.accuracy_percent:.1f}% (Target: 95%)")

        # Coverage breakdown
        print(f"\n📋 COVERAGE BREAKDOWN:")
        print(f"   Total GT Fields:    {metrics.total_gt_fields}")
        print(f"   Extracted Fields:   {metrics.extracted_fields}")
        print(f"   Missing Fields:     {metrics.missing_fields}")

        # Accuracy breakdown
        print(f"\n✅ ACCURACY BREAKDOWN:")
        print(f"   Correct Values:     {metrics.correct_values}")
        print(f"   Incorrect Values:   {metrics.incorrect_values}")

        # Validation engine
        print(f"\n🔍 VALIDATION ENGINE:")
        print(f"   Errors Detected:    {metrics.validation_errors_found}")
        print(f"   Warnings Detected:  {metrics.validation_warnings_found}")

        # Pass/Fail
        print(f"\n🎯 95/95 TARGET:")
        coverage_pass = "✅ PASS" if metrics.coverage_percent >= 95 else "❌ FAIL"
        accuracy_pass = "✅ PASS" if metrics.accuracy_percent >= 95 else "❌ FAIL"

        print(f"   Coverage {metrics.coverage_percent:.1f}%: {coverage_pass}")
        print(f"   Accuracy {metrics.accuracy_percent:.1f}%: {accuracy_pass}")

        overall_pass = metrics.coverage_percent >= 95 and metrics.accuracy_percent >= 95

        if overall_pass:
            print(f"\n🎉 95/95 TARGET ACHIEVED!")
        else:
            print(f"\n⚠️  95/95 TARGET NOT MET - Gaps identified below")

        # Show failed fields (if any)
        failed_comparisons = [c for c in metrics.field_comparisons if not c.match]

        if failed_comparisons:
            print(f"\n❌ FAILED FIELDS ({len(failed_comparisons)} total):")

            # Group by type
            missing = [c for c in failed_comparisons if "not extracted" in c.notes.lower()]
            incorrect = [c for c in failed_comparisons if "not extracted" not in c.notes.lower()]

            if missing:
                print(f"\n   Missing Fields ({len(missing)}):")
                for c in missing[:10]:  # Show first 10
                    print(f"   - {c.field_path}: {c.gt_value}")

            if incorrect:
                print(f"\n   Incorrect Values ({len(incorrect)}):")
                for c in incorrect[:10]:  # Show first 10
                    print(f"   - {c.field_path}")
                    print(f"     GT: {c.gt_value}")
                    print(f"     Extracted: {c.extracted_value}")
                    print(f"     Notes: {c.notes}")

        print("\n" + "="*80)


def main():
    """Run 95/95 validation test"""

    print("\n" + "="*80)
    print("GRACIAN PIPELINE - 95/95 COMPREHENSIVE VALIDATION")
    print("="*80)

    # Paths
    test_pdf = "SRS/brf_198532.pdf"
    ground_truth = "ground_truth/brf_198532_comprehensive_ground_truth.json"

    # Verify files exist
    if not Path(test_pdf).exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return False

    if not Path(ground_truth).exists():
        print(f"❌ Ground truth not found: {ground_truth}")
        return False

    print(f"\n📄 Test PDF: {test_pdf}")
    print(f"📋 Ground Truth: {ground_truth}")
    print(f"🎯 Target: 95% Coverage + 95% Accuracy")

    # Load ground truth
    print(f"\n⏳ Loading ground truth...")
    validator = ComprehensiveValidator(ground_truth)
    print(f"   ✅ Loaded {len(validator.ground_truth)} top-level categories")

    # Run extraction
    print(f"\n⏳ Running extraction (mode=fast for testing)...")
    start_time = time.time()

    extractor = RobustUltraComprehensiveExtractor()
    result = extractor.extract_brf_document(test_pdf, mode="fast")

    extraction_time = time.time() - start_time
    print(f"   ✅ Extraction complete in {extraction_time:.1f}s")

    # Validate
    print(f"\n⏳ Validating extraction against ground truth...")
    metrics = validator.validate(result)

    # Print report
    validator.print_report(metrics)

    # Save detailed report
    report_path = f"validation_reports/95_95_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("validation_reports").mkdir(exist_ok=True)

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_pdf": test_pdf,
        "ground_truth": ground_truth,
        "extraction_time_seconds": round(extraction_time, 2),
        "metrics": {
            "coverage_percent": round(metrics.coverage_percent, 2),
            "accuracy_percent": round(metrics.accuracy_percent, 2),
            "total_gt_fields": metrics.total_gt_fields,
            "extracted_fields": metrics.extracted_fields,
            "correct_values": metrics.correct_values,
            "incorrect_values": metrics.incorrect_values,
            "missing_fields": metrics.missing_fields,
            "validation_errors_found": metrics.validation_errors_found,
            "validation_warnings_found": metrics.validation_warnings_found
        },
        "target_met": metrics.coverage_percent >= 95 and metrics.accuracy_percent >= 95,
        "failed_fields": [
            {
                "field": c.field_path,
                "gt_value": str(c.gt_value),
                "extracted_value": str(c.extracted_value),
                "notes": c.notes
            }
            for c in metrics.field_comparisons if not c.match
        ]
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Detailed report saved: {report_path}")

    # Return success/failure
    return metrics.coverage_percent >= 95 and metrics.accuracy_percent >= 95


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
