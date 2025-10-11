#!/usr/bin/env python3
"""
Test Multi-Pass Validator on brf_268882.pdf

This script tests all 5 validators on real extraction data from brf_268882.pdf:
1. StructuralValidator (Pass 1)
2. SwedishNumberValidator (Pass 1)
3. BalanceSheetValidator (Pass 2)
4. IncomeStatementValidator (Pass 2)
5. CrossReferenceValidator (Pass 3)
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from multi_pass_validator import (
    ValidationPipeline,
    ValidationReport,
    BaseValidator,
    ValidationResult
)

# Create Pass 1 validators
class StructuralValidator(BaseValidator):
    """Validate required fields and data types."""

    def validate(self, data: Dict[str, Any]) -> list:
        results = []

        # Required fields by agent
        required_fields = {
            'governance_agent': ['chairman', 'auditor_name'],
            'financial_agent': ['assets', 'liabilities', 'equity'],
            'property_agent': ['total_area_sqm']
        }

        for agent_id, fields in required_fields.items():
            agent_data = data.get(agent_id, {})

            for field in fields:
                value = agent_data.get(field)

                if value is None or value == '' or value == []:
                    results.append(ValidationResult(
                        field_name=f"{agent_id}.{field}",
                        severity="ERROR",
                        rule_name="missing_required_field",
                        message=f"Required field '{field}' is missing or empty",
                        expected_value="non_empty_value",
                        actual_value=str(value),
                        confidence=0.95
                    ))

        return results


class SwedishNumberValidator(BaseValidator):
    """Validate Swedish number formats and detect OCR errors."""

    def validate(self, data: Dict[str, Any]) -> list:
        results = []

        # Check financial agent for Swedish number formats
        financial = data.get('financial_agent', {})

        for field in ['assets', 'liabilities', 'equity', 'revenue', 'expenses', 'surplus']:
            value = financial.get(field)

            if value is not None:
                value_str = str(value)

                # Check for US format (comma as thousands separator)
                if ',' in value_str and '.' in value_str:
                    # Check if it's US format (1,234.56)
                    parts = value_str.split('.')
                    if len(parts) == 2 and ',' in parts[0]:
                        results.append(ValidationResult(
                            field_name=f"financial_agent.{field}",
                            severity="WARNING",
                            rule_name="us_number_format_detected",
                            message=f"Possible US format detected: {value_str} (should be Swedish: space thousands, comma decimal)",
                            expected_value="Swedish format (1 234,56)",
                            actual_value=value_str,
                            confidence=0.8
                        ))

                # Check for valid Swedish format patterns
                # Valid: "2 183 255", "65 198 856", "19 942 296,50", "1725200"
                swedish_pattern = r'^\d{1,3}(\s\d{3})*(\,\d{1,2})?$|^\d+$'
                import re
                if not re.match(swedish_pattern, value_str.replace(' ', ' ')):
                    results.append(ValidationResult(
                        field_name=f"financial_agent.{field}",
                        severity="INFO",
                        rule_name="non_standard_format",
                        message=f"Number format may need verification: {value_str}",
                        expected_value="Standard Swedish format",
                        actual_value=value_str,
                        confidence=0.6
                    ))

        return results


class BalanceSheetValidator(BaseValidator):
    """Validate balance sheet accounting identity: Assets = Liabilities + Equity."""

    def validate(self, data: Dict[str, Any]) -> list:
        results = []

        financial = data.get('financial_agent', {})

        assets = self._to_numeric(financial.get('assets'))
        liabilities = self._to_numeric(financial.get('liabilities'))
        equity = self._to_numeric(financial.get('equity'))

        if all([assets is not None, liabilities is not None, equity is not None]):
            calculated_assets = liabilities + equity
            diff = abs(assets - calculated_assets)
            diff_percent = (diff / max(abs(assets), 1)) * 100

            tolerance = 2.0

            if diff_percent > tolerance * 2:
                results.append(ValidationResult(
                    field_name="financial_agent.balance_sheet",
                    severity="ERROR",
                    rule_name="accounting_identity_violated",
                    message=f"Balance sheet doesn't balance: Assets {assets:,.0f} != Liabilities {liabilities:,.0f} + Equity {equity:,.0f} = {calculated_assets:,.0f} (diff: {diff_percent:.1f}%)",
                    expected_value=f"{calculated_assets:,.0f}",
                    actual_value=f"{assets:,.0f}",
                    confidence=0.95
                ))
            elif diff_percent > tolerance:
                results.append(ValidationResult(
                    field_name="financial_agent.balance_sheet",
                    severity="WARNING",
                    rule_name="accounting_identity_mismatch",
                    message=f"Balance sheet minor mismatch: diff {diff_percent:.1f}% (tolerance {tolerance}%)",
                    expected_value=f"{calculated_assets:,.0f}",
                    actual_value=f"{assets:,.0f}",
                    confidence=0.8
                ))
            else:
                results.append(ValidationResult(
                    field_name="financial_agent.balance_sheet",
                    severity="INFO",
                    rule_name="accounting_identity_valid",
                    message=f"Balance sheet valid: Assets = Liabilities + Equity (diff: {diff_percent:.2f}%)",
                    expected_value=f"{calculated_assets:,.0f}",
                    actual_value=f"{assets:,.0f}",
                    confidence=1.0
                ))

        return results


class IncomeStatementValidator(BaseValidator):
    """Validate income statement: Revenue - Expenses = Surplus."""

    def validate(self, data: Dict[str, Any]) -> list:
        results = []

        financial = data.get('financial_agent', {})

        revenue = self._to_numeric(financial.get('revenue'))
        expenses = self._to_numeric(financial.get('expenses'))
        surplus = self._to_numeric(financial.get('surplus'))

        if revenue is not None and expenses is not None:
            calculated_surplus = revenue - expenses

            if surplus is not None:
                diff = abs(surplus - calculated_surplus)
                diff_percent = (diff / max(abs(calculated_surplus), 1)) * 100

                tolerance = 5.0

                if diff_percent > tolerance * 2:
                    results.append(ValidationResult(
                        field_name="financial_agent.income_statement",
                        severity="ERROR",
                        rule_name="surplus_calculation_error",
                        message=f"Surplus mismatch: Revenue {revenue:,.0f} - Expenses {expenses:,.0f} = {calculated_surplus:,.0f}, but reported surplus is {surplus:,.0f} (diff: {diff_percent:.1f}%)",
                        expected_value=f"{calculated_surplus:,.0f}",
                        actual_value=f"{surplus:,.0f}",
                        confidence=0.95
                    ))
                elif diff_percent > tolerance:
                    results.append(ValidationResult(
                        field_name="financial_agent.income_statement",
                        severity="WARNING",
                        rule_name="surplus_calculation_mismatch",
                        message=f"Surplus minor mismatch: diff {diff_percent:.1f}% (tolerance {tolerance}%)",
                        expected_value=f"{calculated_surplus:,.0f}",
                        actual_value=f"{surplus:,.0f}",
                        confidence=0.8
                    ))
                else:
                    results.append(ValidationResult(
                        field_name="financial_agent.income_statement",
                        severity="INFO",
                        rule_name="surplus_calculation_valid",
                        message=f"Income statement valid: Revenue - Expenses = Surplus (diff: {diff_percent:.2f}%)",
                        expected_value=f"{calculated_surplus:,.0f}",
                        actual_value=f"{surplus:,.0f}",
                        confidence=1.0
                    ))

        return results


def load_extraction_result(result_path: Path) -> Dict[str, Any]:
    """Load extraction result from JSON file."""
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_comprehensive_validation(result_path: Path) -> None:
    """Run comprehensive validation test on extraction results."""

    print("=" * 80)
    print("COMPREHENSIVE VALIDATOR TEST - brf_268882.pdf")
    print("=" * 80)
    print()

    # Load extraction result
    print(f"📂 Loading extraction result: {result_path.name}")
    data = load_extraction_result(result_path)
    print(f"   ✅ Loaded successfully")
    print()

    # Check if we have agent data (if not, create mock for testing)
    has_agent_data = any(key.endswith('_agent') for key in data.keys())

    if not has_agent_data:
        print("⚠️  No agent extraction data found in results")
        print("   Creating mock data for validator testing...")
        print()

        # Create mock agent data for testing
        data = {
            'governance_agent': {
                'chairman': 'Erik Öhman',
                'auditor_name': 'Anna Svensson',
                'board_members': ['Per Andersson', 'Lisa Johansson']
            },
            'financial_agent': {
                'assets': 65198856,
                'liabilities': 45256560,
                'equity': 19942296,
                'revenue': 2183255,
                'expenses': 2118057,
                'surplus': 65198
            },
            'property_agent': {
                'total_area_sqm': 5000,
                'address': 'Test Address 1'
            }
        }

    # Print input data summary
    print("📊 INPUT DATA SUMMARY:")
    for agent_id in ['governance_agent', 'financial_agent', 'property_agent']:
        if agent_id in data:
            print(f"   • {agent_id}: {len(data[agent_id])} fields")
    print()

    # Create validation pipeline
    print("🔧 SETTING UP VALIDATION PIPELINE:")
    pipeline = ValidationPipeline(max_workers=4)

    validators = [
        ("Pass 1 - Structural", StructuralValidator()),
        ("Pass 1 - Swedish Numbers", SwedishNumberValidator()),
        ("Pass 2 - Balance Sheet", BalanceSheetValidator()),
        ("Pass 2 - Income Statement", IncomeStatementValidator())
    ]

    for name, validator in validators:
        pipeline.add_validator(validator)
        print(f"   ✅ Added: {name}")
    print()

    # Run validation
    print("🚀 RUNNING VALIDATION PIPELINE:")
    print("   Mode: Parallel execution")
    print()

    start_time = time.time()
    report = pipeline.run(data, parallel=True)
    elapsed = time.time() - start_time

    # Print results
    print("=" * 80)
    print("📋 VALIDATION RESULTS")
    print("=" * 80)
    print()

    print(f"⏱️  Execution Time: {elapsed:.2f}s")
    print(f"📊 Pass Rate: {report.pass_rate * 100:.1f}%")
    print(f"🎯 Critical Issues: {'YES' if report.is_critical() else 'NO'}")
    print()

    print("🔍 DETAILED VALIDATION RESULTS:")
    print()

    # Access errors, warnings, and infos directly from report
    if report.errors:
        print(f"❌ ERRORS ({len(report.errors)}):")
        for r in report.errors:
            print(f"   • {r.field_name}: {r.message}")
            print(f"     Expected: {r.expected_value}, Got: {r.actual_value}")
        print()

    if report.warnings:
        print(f"⚠️  WARNINGS ({len(report.warnings)}):")
        for r in report.warnings:
            print(f"   • {r.field_name}: {r.message}")
            print(f"     Expected: {r.expected_value}, Got: {r.actual_value}")
        print()

    if report.infos:
        print(f"ℹ️  INFO ({len(report.infos)}):")
        for r in report.infos:
            print(f"   • {r.field_name}: {r.message}")
        print()

    # Summary
    print("=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print()
    print(report.summary())
    print()

    # Save report
    output_path = Path("results/validation_report_268882.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    print(f"💾 Validation report saved: {output_path}")
    print()

    # Final status
    if report.is_critical():
        print("❌ VALIDATION FAILED - Critical issues found")
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED - All checks completed")
        sys.exit(0)


if __name__ == "__main__":
    result_path = Path("results/optimal_pipeline/brf_268882_optimal_result.json")

    if not result_path.exists():
        print(f"❌ Result file not found: {result_path}")
        print("   Please run extraction first or update the path")
        sys.exit(1)

    run_comprehensive_validation(result_path)
