#!/usr/bin/env python3
"""
30-Field Ground Truth Validator

Validates extraction results against the 30 comprehensive BRF fields.
Target: 95% Coverage (29/30) / 95% Accuracy (29/30)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class FieldResult:
    """Result for a single field validation"""
    field_name: str
    category: str
    extracted: bool
    value: Any
    value_type: str
    required: bool
    priority: str  # P0, P1, P2


@dataclass
class ValidationResult:
    """Overall validation result"""
    total_fields: int
    populated_fields: int
    required_fields: int
    required_populated: int
    coverage: float
    field_results: List[FieldResult]
    missing_fields: List[str]
    balance_check_passed: bool
    evidence_ratio: float


class GroundTruth30Validator:
    """Validates extraction against 30-field ground truth standard"""

    def __init__(self, config_path: str = "config/ground_truth_30_fields.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load ground truth configuration"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        Example: "governance_agent.data.chairman" → data['governance_agent']['data']['chairman']
        """
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _check_field(
        self,
        extraction_data: Dict,
        field_name: str,
        field_config: Dict,
        category: str
    ) -> FieldResult:
        """Check if a single field is populated"""
        path = field_config.get('path')
        required = field_config.get('required', False)
        field_type = field_config.get('type', 'string')

        # Extract value from nested path
        value = self._get_nested_value(extraction_data, path)

        # Check if extracted
        extracted = False
        if value is not None:
            if isinstance(value, str):
                extracted = len(value.strip()) > 0
            elif isinstance(value, list):
                min_items = field_config.get('min_items', 1)
                extracted = len(value) >= min_items
            elif isinstance(value, dict):
                min_fields = field_config.get('min_fields', 1)
                extracted = len(value) >= min_fields
            elif isinstance(value, (int, float)):
                extracted = value != 0  # Assume 0 means not extracted
            else:
                extracted = True

        # Determine priority
        priority = "P2"
        for p, fields in self.config.get('priority', {}).items():
            if field_name in fields:
                priority = p.replace('_', ' ').upper()
                break

        return FieldResult(
            field_name=field_name,
            category=category,
            extracted=extracted,
            value=value,
            value_type=field_type,
            required=required,
            priority=priority
        )

    def _check_balance(self, extraction_data: Dict) -> bool:
        """
        Check if assets = liabilities + equity (within tolerance).
        """
        assets = self._get_nested_value(extraction_data, "financial_agent.data.assets")
        liabilities = self._get_nested_value(extraction_data, "financial_agent.data.liabilities")
        equity = self._get_nested_value(extraction_data, "financial_agent.data.equity")

        if not all([assets, liabilities, equity]):
            return False

        try:
            assets_val = float(str(assets).replace(',', '').replace(' ', ''))
            liabilities_val = float(str(liabilities).replace(',', '').replace(' ', ''))
            equity_val = float(str(equity).replace(',', '').replace(' ', ''))

            expected = liabilities_val + equity_val
            tolerance = self.config['validation']['balance_check']['tolerance']
            diff_pct = abs(assets_val - expected) / assets_val if assets_val > 0 else 1.0

            return diff_pct <= tolerance

        except (ValueError, TypeError):
            return False

    def _calculate_evidence_ratio(self, extraction_data: Dict) -> float:
        """Calculate ratio of agents that provided evidence pages"""
        agent_results = extraction_data.get('agent_results', {})
        if not agent_results:
            return 0.0

        total_agents = len(agent_results)
        agents_with_evidence = 0

        for agent_id, agent_data in agent_results.items():
            evidence_pages = agent_data.get('evidence_pages', [])
            if evidence_pages and len(evidence_pages) > 0:
                agents_with_evidence += 1

        return agents_with_evidence / total_agents if total_agents > 0 else 0.0

    def validate(self, extraction_json_path: str) -> ValidationResult:
        """
        Validate extraction results against 30-field standard.

        Args:
            extraction_json_path: Path to extraction result JSON

        Returns:
            ValidationResult with detailed metrics
        """
        # Load extraction data
        with open(extraction_json_path, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)

        field_results = []
        missing_fields = []
        required_fields = 0
        required_populated = 0

        # Check each field category
        for category, fields in self.config['fields'].items():
            for field_name, field_config in fields.items():
                result = self._check_field(extraction_data, field_name, field_config, category)
                field_results.append(result)

                if result.required:
                    required_fields += 1
                    if result.extracted:
                        required_populated += 1

                if not result.extracted:
                    missing_fields.append(field_name)

        # Calculate coverage
        total_fields = len(field_results)
        populated_fields = sum(1 for r in field_results if r.extracted)
        coverage = populated_fields / total_fields if total_fields > 0 else 0.0

        # Validate balance sheet
        balance_check_passed = self._check_balance(extraction_data)

        # Calculate evidence ratio
        evidence_ratio = self._calculate_evidence_ratio(extraction_data)

        return ValidationResult(
            total_fields=total_fields,
            populated_fields=populated_fields,
            required_fields=required_fields,
            required_populated=required_populated,
            coverage=coverage,
            field_results=field_results,
            missing_fields=missing_fields,
            balance_check_passed=balance_check_passed,
            evidence_ratio=evidence_ratio
        )

    def print_report(self, result: ValidationResult, pdf_name: str = ""):
        """Print detailed validation report"""
        print("\n" + "="*70)
        print(f"30-FIELD GROUND TRUTH VALIDATION - {pdf_name}")
        print("="*70)

        # Coverage metrics
        print(f"\n📊 COVERAGE METRICS:")
        print(f"   Total fields: {result.total_fields}/30")
        print(f"   Populated: {result.populated_fields}/30 ({result.coverage:.1%})")
        print(f"   Required populated: {result.required_populated}/{result.required_fields}")
        print(f"   Missing: {len(result.missing_fields)}/30")

        # Target comparison
        target_coverage = self.config['target_coverage']
        target_needed = int(target_coverage * result.total_fields)
        gap = target_needed - result.populated_fields

        print(f"\n🎯 TARGET COMPARISON:")
        print(f"   Target coverage: {target_coverage:.0%} ({target_needed}/{result.total_fields} fields)")
        print(f"   Current: {result.coverage:.1%} ({result.populated_fields}/{result.total_fields} fields)")
        if gap > 0:
            print(f"   Gap: Need +{gap} more fields to hit 95% target")
            print(f"   Status: 🟡 NOT REACHED (need {gap} more)")
        else:
            print(f"   Gap: ✅ TARGET EXCEEDED by {abs(gap)} fields!")
            print(f"   Status: ✅ 95% TARGET REACHED!")

        # Quality metrics
        print(f"\n✅ QUALITY METRICS:")
        print(f"   Balance check: {'✅ Pass' if result.balance_check_passed else '❌ Fail'} (assets = liabilities + equity)")
        print(f"   Evidence ratio: {result.evidence_ratio:.1%} (agents citing source pages)")
        print(f"   Evidence target: {self.config['validation']['evidence_check']['min_evidence_ratio']:.0%}")
        print(f"   Evidence status: {'✅ Pass' if result.evidence_ratio >= 0.80 else '⚠️ Below target'}")

        # Field breakdown by category
        print(f"\n📋 FIELD BREAKDOWN BY CATEGORY:")
        categories = {}
        for fr in result.field_results:
            if fr.category not in categories:
                categories[fr.category] = {'total': 0, 'populated': 0}
            categories[fr.category]['total'] += 1
            if fr.extracted:
                categories[fr.category]['populated'] += 1

        for cat, stats in categories.items():
            pct = stats['populated'] / stats['total'] * 100 if stats['total'] > 0 else 0
            status = "✅" if pct >= 80 else "⚠️" if pct >= 60 else "❌"
            print(f"   {status} {cat:25s}: {stats['populated']:2d}/{stats['total']:2d} ({pct:5.1f}%)")

        # Missing fields by priority
        print(f"\n⚠️  MISSING FIELDS ({len(result.missing_fields)}):")
        if result.missing_fields:
            priority_groups = {'P0 CRITICAL': [], 'P1 IMPORTANT': [], 'P2 OPTIONAL': []}
            for fr in result.field_results:
                if not fr.extracted:
                    priority_groups[fr.priority].append(fr.field_name)

            for priority, fields in priority_groups.items():
                if fields:
                    print(f"\n   {priority}:")
                    for field in fields:
                        print(f"      - {field}")
        else:
            print("   ✅ ALL FIELDS POPULATED!")

        # Next steps
        print(f"\n🚀 NEXT STEPS TO 95/95:")
        if gap > 0:
            print(f"   1. Fix {gap} missing fields (prioritize P0, then P1)")
            print(f"   2. Validate accuracy of populated fields")
            print(f"   3. Test on 10 diverse PDFs")
        else:
            print(f"   1. ✅ Coverage target reached!")
            print(f"   2. Validate accuracy of all fields")
            print(f"   3. Test consistency on 10 diverse PDFs")

        print("\n" + "="*70 + "\n")

        return result


def main():
    """Validate brf_198532 extraction against 30-field standard"""
    import sys

    if len(sys.argv) < 2:
        extraction_path = "results/optimal_pipeline/brf_198532_optimal_result.json"
    else:
        extraction_path = sys.argv[1]

    if not Path(extraction_path).exists():
        print(f"❌ Extraction file not found: {extraction_path}")
        sys.exit(1)

    validator = GroundTruth30Validator()
    result = validator.validate(extraction_path)

    pdf_name = Path(extraction_path).stem.replace('_optimal_result', '')
    validator.print_report(result, pdf_name)

    # Exit with appropriate code
    target_coverage = validator.config['target_coverage']
    if result.coverage >= target_coverage:
        print("✅ 95% coverage target REACHED!")
        sys.exit(0)
    else:
        gap = int(target_coverage * result.total_fields) - result.populated_fields
        print(f"⚠️  Need +{gap} more fields to reach 95% target")
        sys.exit(1)


if __name__ == "__main__":
    main()
