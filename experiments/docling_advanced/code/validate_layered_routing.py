#!/usr/bin/env python3
"""
Validate Layered Routing System Against Ground Truth

Compares extraction results from optimal_brf_pipeline.py with
Pydantic ground truth to measure routing → extraction improvement.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict

class ValidationReport:
    """Comprehensive validation report"""

    def __init__(self, extraction_path: str, ground_truth_path: str):
        self.extraction_path = Path(extraction_path)
        self.ground_truth_path = Path(ground_truth_path)

        # Load data
        with open(self.extraction_path, 'r', encoding='utf-8') as f:
            self.extraction = json.load(f)

        with open(self.ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)

        # Analysis results
        self.field_results = []
        self.coverage_by_section = {}
        self.issues_by_category = defaultdict(list)

    def compare_field(self, section: str, field_path: str, extracted_value: Any,
                     ground_truth_value: Any) -> Dict[str, Any]:
        """Compare a single field"""

        # Normalize values for comparison
        extracted_norm = self._normalize_value(extracted_value)
        gt_norm = self._normalize_value(ground_truth_value)

        # Determine status
        if extracted_norm is None or extracted_norm == "":
            status = "MISSING"
        elif extracted_norm == gt_norm:
            status = "CORRECT"
        elif self._is_close_match(extracted_norm, gt_norm):
            status = "PARTIAL"
        else:
            status = "INCORRECT"

        return {
            "section": section,
            "field": field_path,
            "status": status,
            "extracted": extracted_value,
            "ground_truth": ground_truth_value,
            "match": status == "CORRECT"
        }

    def _normalize_value(self, value: Any) -> Any:
        """Normalize value for comparison"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            # Try to convert to number if it looks like one
            try:
                return int(value)
            except:
                try:
                    return float(value)
                except:
                    return value.lower()
        if isinstance(value, list):
            if len(value) == 0:
                return None
            return [self._normalize_value(v) for v in value]
        return value

    def _is_close_match(self, extracted: Any, ground_truth: Any) -> bool:
        """Check if values are close enough (for numeric tolerance)"""
        # Handle numeric comparisons with tolerance
        try:
            if isinstance(extracted, (int, float)) and isinstance(ground_truth, (int, float)):
                tolerance = abs(ground_truth) * 0.05  # 5% tolerance
                return abs(extracted - ground_truth) <= tolerance
        except:
            pass

        # Handle list comparisons (board members, etc.)
        if isinstance(extracted, list) and isinstance(ground_truth, list):
            if len(extracted) >= len(ground_truth) * 0.8:  # 80% coverage
                return True

        return False

    def analyze_governance(self):
        """Analyze governance section"""
        section = "governance"
        extracted = self.extraction['agent_results'].get('governance_agent', {}).get('data', {})
        gt = self.ground_truth.get('governance', {})

        # Chairman
        self.field_results.append(self.compare_field(
            section, "chairman",
            extracted.get('chairman'),
            gt.get('chairman')
        ))

        # Board members (count comparison)
        extracted_board = extracted.get('board_members', [])
        gt_board = gt.get('board_members', [])

        # Extract just names from GT (which has dicts)
        gt_board_names = [m['name'] if isinstance(m, dict) else m for m in gt_board]

        self.field_results.append(self.compare_field(
            section, "board_members_count",
            len(extracted_board),
            len(gt_board_names)
        ))

        # Check individual board members
        for name in gt_board_names:
            found = any(name in str(extracted_board) for _ in [name])
            self.field_results.append({
                "section": section,
                "field": f"board_member_{name.split()[0]}",
                "status": "CORRECT" if found else "MISSING",
                "extracted": extracted_board,
                "ground_truth": name,
                "match": found
            })

        # Auditors
        extracted_auditor = extracted.get('auditor_name')
        extracted_firm = extracted.get('audit_firm')
        gt_auditors = gt.get('auditors', [])

        if gt_auditors:
            # Check first auditor
            gt_auditor_name = gt_auditors[0].get('name') if gt_auditors else None
            gt_firm = gt_auditors[0].get('firm') if gt_auditors else None

            self.field_results.append(self.compare_field(
                section, "auditor_name",
                extracted_auditor,
                gt_auditor_name
            ))

            self.field_results.append(self.compare_field(
                section, "audit_firm",
                extracted_firm,
                gt_firm
            ))

        # Nomination committee
        self.field_results.append(self.compare_field(
            section, "nomination_committee",
            extracted.get('nomination_committee'),
            gt.get('nomination_committee')
        ))

    def analyze_property(self):
        """Analyze property section"""
        section = "property"
        extracted = self.extraction['agent_results'].get('property_agent', {}).get('data', {})
        gt = self.ground_truth.get('property', {})

        # Direct field comparisons
        fields = [
            ('designation', 'properties[0].designation' if gt.get('properties') else 'designation'),
            ('address', 'address'),
            ('city', 'properties[0].municipality' if gt.get('properties') else 'city'),
            ('built_year', 'construction_year'),
            ('apartments', 'total_apartments'),
        ]

        for extracted_field, gt_field in fields:
            # Navigate GT path
            gt_value = gt
            for part in gt_field.split('.'):
                if '[' in part:
                    # Handle array indexing
                    key, idx = part.split('[')
                    idx = int(idx.rstrip(']'))
                    gt_value = gt_value.get(key, [])
                    if isinstance(gt_value, list) and len(gt_value) > idx:
                        gt_value = gt_value[idx]
                    else:
                        gt_value = None
                        break
                else:
                    gt_value = gt_value.get(part) if isinstance(gt_value, dict) else None
                if gt_value is None:
                    break

            self.field_results.append(self.compare_field(
                section,
                extracted_field,
                extracted.get(extracted_field),
                gt_value
            ))

    def analyze_financial(self):
        """Analyze financial section"""
        section = "financial"
        extracted = self.extraction['agent_results'].get('financial_agent', {}).get('data', {})
        gt_financial = self.ground_truth.get('financial', {})

        # Income statement
        gt_income = gt_financial.get('income_statement', {})
        gt_revenue = gt_income.get('revenue', {}).get('total')
        gt_expenses = gt_income.get('operating_expenses', {}).get('total')
        gt_result = gt_income.get('year_result')

        self.field_results.append(self.compare_field(
            section, "revenue",
            extracted.get('revenue'),
            gt_revenue
        ))

        self.field_results.append(self.compare_field(
            section, "expenses",
            extracted.get('expenses'),
            gt_expenses
        ))

        self.field_results.append(self.compare_field(
            section, "surplus",
            extracted.get('surplus'),
            gt_result
        ))

        # Balance sheet
        gt_balance = gt_financial.get('balance_sheet', {})
        gt_assets = gt_balance.get('assets', {}).get('total_assets')
        gt_equity = gt_balance.get('equity_liabilities', {}).get('equity')
        gt_liabilities_long = gt_balance.get('equity_liabilities', {}).get('long_term_liabilities')
        gt_liabilities_short = gt_balance.get('equity_liabilities', {}).get('short_term_liabilities')

        self.field_results.append(self.compare_field(
            section, "assets",
            extracted.get('assets'),
            gt_assets
        ))

        self.field_results.append(self.compare_field(
            section, "equity",
            extracted.get('equity'),
            gt_equity
        ))

        self.field_results.append(self.compare_field(
            section, "liabilities",
            extracted.get('liabilities'),
            gt_liabilities_long + gt_liabilities_short if gt_liabilities_long and gt_liabilities_short else None
        ))

    def analyze_notes(self):
        """Check if notes were extracted"""
        gt_notes = self.ground_truth.get('notes', {})

        # Check if any note agents were executed
        note_agents_executed = [
            agent_id for agent_id in self.extraction['agent_results'].keys()
            if 'notes_' in agent_id
        ]

        for note_key in gt_notes.keys():
            self.field_results.append({
                "section": "notes",
                "field": note_key,
                "status": "MISSING" if not note_agents_executed else "PARTIAL",
                "extracted": f"{len(note_agents_executed)} note agents executed",
                "ground_truth": f"Should extract {note_key}",
                "match": False
            })

    def analyze_loans(self):
        """Check if loans were extracted"""
        gt_loans = self.ground_truth.get('loans', [])

        # Check if loans agent was executed
        loans_agent = self.extraction['agent_results'].get('notes_loans_agent')

        for i, loan in enumerate(gt_loans):
            self.field_results.append({
                "section": "loans",
                "field": f"loan_{i+1}",
                "status": "MISSING",
                "extracted": "No loans agent executed",
                "ground_truth": f"{loan.get('lender')} - {loan.get('amount_2021')}",
                "match": False
            })

    def categorize_issues(self):
        """Categorize issues by root cause"""

        for result in self.field_results:
            if result['status'] in ['MISSING', 'INCORRECT']:
                section = result['section']
                field = result['field']

                # Determine root cause
                if section == "notes" or section == "loans":
                    # Note sections not routed
                    self.issues_by_category['ROUTING'].append({
                        'field': f"{section}.{field}",
                        'issue': 'Note sections not detected/routed',
                        'fix': 'Improve note section detection in route_sections()'
                    })
                elif result['status'] == 'MISSING':
                    # Field not extracted by agent
                    self.issues_by_category['EXTRACTION'].append({
                        'field': f"{section}.{field}",
                        'issue': 'Agent received section but didn\'t extract field',
                        'fix': f'Improve {section}_agent prompt or page allocation'
                    })
                else:
                    # Field extracted incorrectly
                    self.issues_by_category['ACCURACY'].append({
                        'field': f"{section}.{field}",
                        'issue': f'Extracted {result["extracted"]} != {result["ground_truth"]}',
                        'fix': f'Improve {section}_agent extraction accuracy'
                    })

    def calculate_metrics(self):
        """Calculate overall metrics"""
        total = len(self.field_results)
        correct = sum(1 for r in self.field_results if r['status'] == 'CORRECT')
        partial = sum(1 for r in self.field_results if r['status'] == 'PARTIAL')
        missing = sum(1 for r in self.field_results if r['status'] == 'MISSING')
        incorrect = sum(1 for r in self.field_results if r['status'] == 'INCORRECT')

        return {
            'total_fields': total,
            'correct': correct,
            'partial': partial,
            'missing': missing,
            'incorrect': incorrect,
            'coverage': (correct + partial) / total if total > 0 else 0.0,
            'accuracy': correct / (correct + incorrect) if (correct + incorrect) > 0 else 0.0,
            'overall_score': correct / total if total > 0 else 0.0
        }

    def generate_report(self, output_path: str = None):
        """Generate comprehensive validation report"""

        # Run all analyses
        self.analyze_governance()
        self.analyze_property()
        self.analyze_financial()
        self.analyze_notes()
        self.analyze_loans()
        self.categorize_issues()

        # Calculate metrics
        metrics = self.calculate_metrics()

        # Build report
        report = {
            'extraction_file': str(self.extraction_path),
            'ground_truth_file': str(self.ground_truth_path),
            'metrics': metrics,
            'field_results': self.field_results,
            'issues_by_category': dict(self.issues_by_category),
            'routing_info': self.extraction.get('routing', {}),
            'quality_metrics': self.extraction.get('quality_metrics', {})
        }

        # Save report
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ Validation report saved to {output_path}")

        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print human-readable summary"""

        metrics = report['metrics']

        print("\n" + "="*70)
        print("LAYERED ROUTING VALIDATION REPORT")
        print("="*70)

        print(f"\n📄 Document: {Path(self.extraction_path).stem}")
        print(f"   Extraction: {self.extraction_path}")
        print(f"   Ground Truth: {self.ground_truth_path}")

        print("\n📊 OVERALL METRICS:")
        print(f"   Total Fields: {metrics['total_fields']}")
        print(f"   ✅ Correct: {metrics['correct']} ({metrics['correct']/metrics['total_fields']*100:.1f}%)")
        print(f"   ⚠️  Partial: {metrics['partial']} ({metrics['partial']/metrics['total_fields']*100:.1f}%)")
        print(f"   ❌ Missing: {metrics['missing']} ({metrics['missing']/metrics['total_fields']*100:.1f}%)")
        print(f"   ❌ Incorrect: {metrics['incorrect']} ({metrics['incorrect']/metrics['total_fields']*100:.1f}%)")
        print(f"\n   Coverage: {metrics['coverage']*100:.1f}% (target: 95%)")
        print(f"   Accuracy: {metrics['accuracy']*100:.1f}% (target: 95%)")
        print(f"   Overall Score: {metrics['overall_score']*100:.1f}% (target: 95%)")

        # Routing info
        routing = report.get('routing_info', {})
        print(f"\n🧭 ROUTING METRICS:")
        print(f"   Main sections routed: {sum(routing.get('main_sections', {}).values())}")
        for agent, count in routing.get('main_sections', {}).items():
            print(f"      • {agent}: {count} sections")
        print(f"   Note sections routed: {sum(routing.get('note_sections', {}).values())}")

        # Issues by category
        issues = report.get('issues_by_category', {})
        print(f"\n🐛 ISSUES BY CATEGORY:")
        for category, issue_list in issues.items():
            print(f"   {category}: {len(issue_list)} issues")
            for issue in issue_list[:3]:  # Show top 3
                print(f"      • {issue['field']}: {issue['issue']}")
            if len(issue_list) > 3:
                print(f"      ... and {len(issue_list) - 3} more")

        # Top missing fields
        print(f"\n❌ TOP MISSING FIELDS:")
        missing_fields = [r for r in report['field_results'] if r['status'] == 'MISSING']
        for i, field in enumerate(missing_fields[:10], 1):
            print(f"   {i}. {field['section']}.{field['field']}")
            print(f"      Expected: {field['ground_truth']}")

        print("\n" + "="*70)


def main():
    """Run validation"""
    if len(sys.argv) < 3:
        print("Usage: python validate_layered_routing.py <extraction_result.json> <ground_truth.json>")
        sys.exit(1)

    extraction_path = sys.argv[1]
    ground_truth_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else "validation_report_layered_routing.json"

    # Run validation
    validator = ValidationReport(extraction_path, ground_truth_path)
    report = validator.generate_report(output_path)
    validator.print_summary(report)

    # Exit code based on success
    metrics = report['metrics']
    if metrics['overall_score'] >= 0.95:
        print("\n🎉 SUCCESS: Achieved 95/95 goal!")
        sys.exit(0)
    else:
        print(f"\n⚠️  PARTIAL: {metrics['overall_score']*100:.1f}% vs 95% target")
        print(f"   Gap: {(0.95 - metrics['overall_score'])*100:.1f}%")
        sys.exit(1)


if __name__ == "__main__":
    main()
