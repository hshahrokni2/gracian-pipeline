#!/usr/bin/env python3
"""
Load Ground Truth Extractions and Run Classification System

This script:
1. Loads 43 ground truth JSON files from batch_results/
2. Creates PostgreSQL tables using the schema
3. Inserts extracted data with is_ground_truth=TRUE
4. Runs classification algorithms (8 patterns + 4 risk scores)
5. Generates summary report

Author: Gracian Pipeline Team
Date: 2025-10-17
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import Json, execute_values

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import classification system (Phase 0)
try:
    sys.path.append(str(PROJECT_ROOT / "gracian_pipeline"))
    from classification.pattern_classifier import PatternClassifier
    CLASSIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Classification modules not found: {e}")
    print("⚠️  Will load data only, classification will be skipped")
    CLASSIFICATION_AVAILABLE = False


class GroundTruthLoader:
    """Load and classify ground truth BRF extractions"""

    def __init__(self, db_url: str, schema_path: Path, classifier_config_path: Path):
        self.db_url = db_url
        self.schema_path = schema_path
        self.classifier_config_path = classifier_config_path
        self.conn = None
        self.cursor = None
        self.classifier = None

        # Initialize classifier if available
        if CLASSIFICATION_AVAILABLE:
            try:
                self.classifier = PatternClassifier(classifier_config_path)
                print(f"✅ Pattern classifier loaded from: {classifier_config_path}")
            except Exception as e:
                print(f"⚠️  Failed to load classifier: {e}")
                self.classifier = None

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    def create_schema(self):
        """Create database tables from schema file"""
        try:
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()

            self.cursor.execute(schema_sql)
            self.conn.commit()
            print("✅ Database schema created successfully")
        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            self.conn.rollback()
            sys.exit(1)

    def load_json_files(self, batch_results_dir: Path) -> List[Dict]:
        """Load all comprehensive_extraction.json files"""
        json_files = list(batch_results_dir.glob("*_comprehensive_extraction.json"))

        print(f"\n📂 Found {len(json_files)} ground truth JSON files")

        extractions = []
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract BRF ID from filename (e.g., "brf_81563_comprehensive_extraction.json" -> "brf_81563")
                brf_id = json_file.stem.replace("_comprehensive_extraction", "")

                extractions.append({
                    'brf_id': brf_id,
                    'filename': json_file.name,
                    'data': data
                })

            except Exception as e:
                print(f"⚠️  Failed to load {json_file.name}: {e}")

        print(f"✅ Successfully loaded {len(extractions)} ground truth files")
        return extractions

    def insert_extraction(self, extraction: Dict) -> Optional[int]:
        """Insert extraction data into ground_truth_extractions table"""
        try:
            data = extraction['data']
            brf_id = extraction['brf_id']

            # Extract metadata
            metadata = data.get('metadata_agent', {})

            # Extract financial data
            financial = data.get('financial_agent', {})

            # Extract property data
            property_data = data.get('property_agent', {})

            # Extract governance data
            governance = data.get('governance_agent', {})

            # Extract audit data
            audit = data.get('audit_agent', {})

            # Extract loans data
            loans = data.get('loans_agent', {})

            # Extract operating costs
            operating_costs = data.get('operating_costs_agent', {})

            # Build SQL insert
            insert_sql = """
            INSERT INTO ground_truth_extractions (
                brf_id, is_ground_truth, extraction_date, extraction_model,
                pdf_filename, pdf_pages_total,
                organization_name, organization_number, report_year,
                fiscal_year_start, fiscal_year_end, report_date,
                location, accounting_standard,
                assets_total, equity_total, liabilities_total,
                net_revenue, profit_loss, soliditet_pct, cash_and_bank,
                total_driftskostnader, el_cost, varme_cost, vatten_cost, fastighetsskatt,
                total_debt, long_term_debt, short_term_debt, average_interest_rate_pct,
                total_area_sqm, bostadsratter_count, construction_year,
                chairman, board_size, board_meetings_count,
                auditor_name, auditor_firm,
                extraction_json, evidence_pages, extraction_confidence
            ) VALUES (
                %(brf_id)s, TRUE, NOW(), 'Claude 4.5',
                %(pdf_filename)s, %(pdf_pages_total)s,
                %(organization_name)s, %(organization_number)s, %(report_year)s,
                %(fiscal_year_start)s, %(fiscal_year_end)s, %(report_date)s,
                %(location)s, %(accounting_standard)s,
                %(assets_total)s, %(equity_total)s, %(liabilities_total)s,
                %(net_revenue)s, %(profit_loss)s, %(soliditet_pct)s, %(cash_and_bank)s,
                %(total_driftskostnader)s, %(el_cost)s, %(varme_cost)s, %(vatten_cost)s, %(fastighetsskatt)s,
                %(total_debt)s, %(long_term_debt)s, %(short_term_debt)s, %(average_interest_rate_pct)s,
                %(total_area_sqm)s, %(bostadsratter_count)s, %(construction_year)s,
                %(chairman)s, %(board_size)s, %(board_meetings_count)s,
                %(auditor_name)s, %(auditor_firm)s,
                %(extraction_json)s, %(evidence_pages)s, %(extraction_confidence)s
            )
            RETURNING extraction_id;
            """

            # Prepare values
            values = {
                'brf_id': brf_id,
                'pdf_filename': extraction['filename'],
                'pdf_pages_total': metadata.get('pages_total'),
                'organization_name': metadata.get('organization_name'),
                'organization_number': metadata.get('organization_number'),
                'report_year': self._extract_year(metadata.get('fiscal_year_end')),
                'fiscal_year_start': metadata.get('fiscal_year_start'),
                'fiscal_year_end': metadata.get('fiscal_year_end'),
                'report_date': metadata.get('report_date'),
                'location': None,  # Not in current schema
                'accounting_standard': metadata.get('accounting_standard'),
                'assets_total': financial.get('assets_total'),
                'equity_total': financial.get('equity_total'),
                'liabilities_total': financial.get('liabilities_total'),
                'net_revenue': financial.get('net_revenue'),
                'profit_loss': financial.get('profit_loss'),
                'soliditet_pct': financial.get('soliditet_pct'),
                'cash_and_bank': financial.get('cash_and_bank'),
                'total_driftskostnader': operating_costs.get('total_driftskostnader'),
                'el_cost': operating_costs.get('el'),
                'varme_cost': operating_costs.get('varme'),
                'vatten_cost': operating_costs.get('vatten'),
                'fastighetsskatt': operating_costs.get('fastighetsskatt'),
                'total_debt': loans.get('total_debt'),
                'long_term_debt': loans.get('long_term_debt'),
                'short_term_debt': loans.get('short_term_debt'),
                'average_interest_rate_pct': loans.get('average_interest_rate_pct'),
                'total_area_sqm': property_data.get('total_area_sqm'),
                'bostadsratter_count': property_data.get('bostadsratter_count'),
                'construction_year': self._parse_construction_year(property_data.get('construction_year')),
                'chairman': governance.get('chairman'),
                'board_size': governance.get('board_size'),
                'board_meetings_count': governance.get('board_meetings_count'),
                'auditor_name': audit.get('auditor_name'),
                'auditor_firm': audit.get('auditor_firm'),
                'extraction_json': Json(data),
                'evidence_pages': metadata.get('evidence_pages', []),
                'extraction_confidence': 1.0  # Ground truth = 100% confidence
            }

            self.cursor.execute(insert_sql, values)
            extraction_id = self.cursor.fetchone()[0]

            return extraction_id

        except Exception as e:
            print(f"❌ Failed to insert {extraction['brf_id']}: {e}")
            return None

    def _extract_year(self, date_string: Optional[str]) -> Optional[int]:
        """Extract year from date string (e.g., '2023-06-30' -> 2023)"""
        if not date_string:
            return None
        try:
            return int(date_string.split('-')[0])
        except:
            return None

    def _normalize_extraction_data(self, data: Dict) -> Dict:
        """
        Normalize extraction data to match classification field names.
        Maps from comprehensive_extraction JSON structure to flat classification fields.
        """
        financial = data.get('financial_agent', {})
        loans = data.get('loans_agent', {})
        fees = data.get('fees_agent', {})
        property_data = data.get('property_agent', {})
        operating_costs = data.get('operating_costs_agent', {})
        commercial = data.get('commercial_tenants_agent', {})
        metadata = data.get('metadata_agent', {})

        # Calculate derived fields
        assets_total = financial.get('assets_total', 0)
        total_debt = loans.get('total_debt', 0)
        short_term_debt = loans.get('short_term_debt', 0)

        normalized = {
            # Financial basics
            'assets_total': assets_total,
            'equity_total': financial.get('equity_total', 0),
            'liabilities_total': financial.get('liabilities_total', 0),
            'net_income': financial.get('profit_loss', 0),
            'soliditet_pct': financial.get('soliditet_pct', 0),
            'cash_and_bank': financial.get('cash_and_bank', 0),

            # Debt structure
            'total_debt': total_debt,
            'short_term_debt': short_term_debt,
            'long_term_debt': loans.get('long_term_debt', 0),
            'kortfristig_skulder_ratio': (short_term_debt / total_debt * 100) if total_debt > 0 else 0,
            'short_term_debt_pct': (short_term_debt / total_debt * 100) if total_debt > 0 else 0,
            'average_interest_rate_pct': loans.get('average_interest_rate_pct', 0),

            # Cash position
            'cash_to_debt_ratio_current_year': (financial.get('cash_and_bank', 0) / total_debt * 100) if total_debt > 0 else 0,

            # Fees
            'fee_increase_total_pct': fees.get('fee_increase_pct', 0) if fees.get('fee_increase_pct') else 0,
            'fee_increase_count_current_year': 1 if fees.get('fee_increase_pct', 0) > 0 else 0,

            # Operating costs
            'total_driftskostnader': operating_costs.get('total_driftskostnader', 0),

            # Property
            'total_area_sqm': property_data.get('total_area_sqm', 0),
            'building_age_at_report': self._calculate_building_age(
                property_data.get('construction_year'),
                metadata.get('report_year')
            ),

            # Commercial space
            'lokaler_area_percentage': commercial.get('commercial_area_pct', 0) if commercial.get('has_commercial_space') else 0,
            'lokaler_revenue_percentage': commercial.get('commercial_rent_pct_of_revenue', 0) if commercial.get('has_commercial_space') else 0,

            # Special calculations for specific patterns
            'result_without_depreciation_current_year': self._calculate_result_without_depreciation(financial, data.get('depreciation_agent', {})),
            'consecutive_loss_years': self._count_consecutive_loss_years(data),
            'operating_income': financial.get('net_revenue', 0) - operating_costs.get('total_driftskostnader', 0),
        }

        return normalized

    def _calculate_building_age(self, construction_year: Optional[int], report_year: Optional[int]) -> int:
        """Calculate building age at report date"""
        if not construction_year or not report_year:
            return 0

        # Handle string ranges like "2017-2018" - take the first year
        if isinstance(construction_year, str):
            try:
                construction_year = int(construction_year.split('-')[0])
            except:
                return 0

        return report_year - construction_year

    def _parse_construction_year(self, construction_year: any) -> Optional[int]:
        """Parse construction year, handling ranges like '2017-2018'"""
        if construction_year is None:
            return None

        # If already an integer
        if isinstance(construction_year, int):
            return construction_year

        # If string, parse it
        if isinstance(construction_year, str):
            # Handle ranges like "2017-2018" - take the first year
            try:
                return int(construction_year.split('-')[0])
            except:
                return None

        return None

    def _calculate_result_without_depreciation(self, financial: Dict, depreciation: Dict) -> int:
        """Calculate result excluding depreciation"""
        profit_loss = financial.get('profit_loss', 0)
        depreciation_amount = depreciation.get('total_depreciation', 0)
        return profit_loss + depreciation_amount

    def _count_consecutive_loss_years(self, data: Dict) -> int:
        """Count consecutive years of losses (placeholder - needs multi-year data)"""
        # TODO: Implement when multi-year history available
        profit_loss = data.get('financial_agent', {}).get('profit_loss', 0)
        return 1 if profit_loss < 0 else 0

    def classify_extraction(self, extraction_id: int, brf_id: str, data: Dict):
        """Run classification algorithms on extraction data"""
        if not self.classifier:
            print(f"⚠️  Skipping classification for {brf_id} (classifier not available)")
            return

        try:
            # Normalize extraction data for classification
            normalized_data = self._normalize_extraction_data(data)

            # Run classification on all 8 patterns
            pattern_names = [
                'refinancing_risk',
                'fee_response',
                'depreciation_paradox',
                'cash_crisis',
                'lokaler_dependency',
                'tomtratt_escalation',
                'pattern_b',
                'interest_rate_victim'
            ]

            classifications = self.classifier.classify_all(normalized_data, pattern_names)

            # Extract results for each pattern
            refinancing = classifications.get('refinancing_risk')
            fee_response = classifications.get('fee_response')
            depreciation = classifications.get('depreciation_paradox')
            cash_crisis = classifications.get('cash_crisis')
            lokaler = classifications.get('lokaler_dependency')
            tomtratt = classifications.get('tomtratt_escalation')
            pattern_b = classifications.get('pattern_b')
            interest_victim = classifications.get('interest_rate_victim')

            # Calculate 4 risk scores (placeholder - implement later)
            mgmt_quality = {'score': 0, 'grade': 'N/A', 'factors': {}}
            financial_stability = {'score': 0, 'grade': 'N/A', 'factors': {}}
            stabilization = {'score': 0, 'grade': 'N/A', 'timeframe_years': None}
            overall_risk = {'score': 0, 'grade': 'N/A', 'category': 'UNKNOWN'}

            # Insert classification results
            insert_sql = """
            INSERT INTO ground_truth_classifications (
                extraction_id, brf_id, classification_date,

                -- Pattern 1: Refinancing Risk
                refinancing_risk_detected, refinancing_risk_tier, refinancing_risk_score,
                refinancing_maturity_cluster_months, refinancing_debt_maturing_1y_pct,
                refinancing_evidence,

                -- Pattern 2: Fee Response
                fee_response_detected, fee_response_type, fee_response_score,
                fee_increase_pct, fee_increase_reason, chronic_losses_years,
                fee_response_evidence,

                -- Pattern 3: Depreciation Paradox
                depreciation_paradox_detected, depreciation_paradox_score,
                result_with_depreciation, result_without_depreciation, depreciation_amount,
                depreciation_paradox_evidence,

                -- Pattern 4: Cash Crisis
                cash_crisis_detected, cash_crisis_severity,
                cash_to_debt_ratio, monthly_burn_rate, months_until_insolvency,
                cash_crisis_evidence,

                -- Pattern 5: Lokaler Dependency
                lokaler_dependency_detected, lokaler_dependency_tier,
                lokaler_area_pct, lokaler_revenue_pct, lokaler_concentration_risk,
                lokaler_dependency_evidence,

                -- Pattern 6: Tomträtt Escalation
                tomtratt_escalation_detected, tomtratt_escalation_tier,
                tomtratt_yoy_increase_pct, tomtratt_current_annual, tomtratt_per_sqm,
                tomtratt_escalation_evidence,

                -- Pattern 7: Pattern B (Young BRF with Chronic Losses)
                pattern_b_detected, pattern_b_years_consecutive_loss,
                pattern_b_construction_year, pattern_b_brf_age, pattern_b_is_concern,
                pattern_b_evidence,

                -- Pattern 8: Interest Rate Victim
                interest_rate_victim_detected, interest_rate_increase_pct,
                interest_expense_yoy_increase, profit_to_loss_trigger,
                interest_rate_victim_evidence,

                -- Risk Scores
                management_quality_score, management_quality_grade, management_quality_factors,
                financial_stability_score, financial_stability_grade, financial_stability_factors,
                stabilization_probability_score, stabilization_probability_grade, stabilization_timeframe_years,
                overall_risk_score, overall_risk_grade, overall_risk_category,

                classification_json
            ) VALUES (
                %(extraction_id)s, %(brf_id)s, NOW(),

                -- Refinancing
                %(ref_detected)s, %(ref_tier)s, %(ref_score)s,
                %(ref_cluster)s, %(ref_pct)s, %(ref_evidence)s,

                -- Fee Response
                %(fee_detected)s, %(fee_type)s, %(fee_score)s,
                %(fee_pct)s, %(fee_reason)s, %(fee_losses)s, %(fee_evidence)s,

                -- Depreciation
                %(dep_detected)s, %(dep_score)s,
                %(dep_with)s, %(dep_without)s, %(dep_amount)s, %(dep_evidence)s,

                -- Cash Crisis
                %(cash_detected)s, %(cash_severity)s,
                %(cash_ratio)s, %(cash_burn)s, %(cash_months)s, %(cash_evidence)s,

                -- Lokaler
                %(lok_detected)s, %(lok_tier)s,
                %(lok_area)s, %(lok_revenue)s, %(lok_risk)s, %(lok_evidence)s,

                -- Tomträtt
                %(tom_detected)s, %(tom_tier)s,
                %(tom_yoy)s, %(tom_annual)s, %(tom_sqm)s, %(tom_evidence)s,

                -- Pattern B
                %(patb_detected)s, %(patb_years)s,
                %(patb_construction)s, %(patb_age)s, %(patb_concern)s, %(patb_evidence)s,

                -- Interest Victim
                %(int_detected)s, %(int_pct)s,
                %(int_expense)s, %(int_trigger)s, %(int_evidence)s,

                -- Scores
                %(mgmt_score)s, %(mgmt_grade)s, %(mgmt_factors)s,
                %(fin_score)s, %(fin_grade)s, %(fin_factors)s,
                %(stab_score)s, %(stab_grade)s, %(stab_years)s,
                %(risk_score)s, %(risk_grade)s, %(risk_category)s,

                %(classification_json)s
            );
            """

            # Prepare values using ClassificationResult objects
            def get_evidence_string(result) -> str:
                """Convert evidence list to string"""
                if not result or not result.evidence:
                    return ""
                return "; ".join(result.evidence)

            values = {
                'extraction_id': extraction_id,
                'brf_id': brf_id,

                # Refinancing (categorical pattern)
                'ref_detected': refinancing.tier != 'NONE' if refinancing else False,
                'ref_tier': refinancing.tier if refinancing else 'NONE',
                'ref_score': refinancing.confidence * 100 if refinancing else 0,
                'ref_cluster': None,  # Not in current schema
                'ref_pct': None,  # Not in current schema
                'ref_evidence': get_evidence_string(refinancing),

                # Fee Response (categorical pattern)
                'fee_detected': fee_response.tier != 'PROACTIVE' if fee_response else False,
                'fee_type': fee_response.tier if fee_response else 'PROACTIVE',
                'fee_score': fee_response.confidence * 100 if fee_response else 0,
                'fee_pct': normalized_data.get('fee_increase_total_pct', 0),
                'fee_reason': None,  # Not in extraction
                'fee_losses': normalized_data.get('consecutive_loss_years', 0),
                'fee_evidence': get_evidence_string(fee_response),

                # Depreciation (boolean pattern)
                'dep_detected': depreciation.detected if depreciation else False,
                'dep_score': depreciation.confidence * 100 if depreciation else 0,
                'dep_with': normalized_data.get('net_income', 0),
                'dep_without': normalized_data.get('result_without_depreciation_current_year', 0),
                'dep_amount': None,  # Not in extraction
                'dep_evidence': get_evidence_string(depreciation),

                # Cash Crisis (boolean pattern)
                'cash_detected': cash_crisis.detected if cash_crisis else False,
                'cash_severity': 'EXTREME' if (cash_crisis and cash_crisis.detected) else None,
                'cash_ratio': normalized_data.get('cash_to_debt_ratio_current_year', 0),
                'cash_burn': None,  # Not in extraction
                'cash_months': None,  # Not in extraction
                'cash_evidence': get_evidence_string(cash_crisis),

                # Lokaler (categorical pattern)
                'lok_detected': lokaler.tier not in ['LOW', 'NONE'] if lokaler else False,
                'lok_tier': lokaler.tier if lokaler else 'NONE',
                'lok_area': normalized_data.get('lokaler_area_percentage', 0),
                'lok_revenue': normalized_data.get('lokaler_revenue_percentage', 0),
                'lok_risk': None,  # Not calculated
                'lok_evidence': get_evidence_string(lokaler),

                # Tomträtt (categorical pattern)
                'tom_detected': tomtratt.tier != 'NONE' if tomtratt else False,
                'tom_tier': tomtratt.tier if tomtratt else 'NONE',
                'tom_yoy': None,  # Not in extraction
                'tom_annual': None,  # Not in extraction
                'tom_sqm': None,  # Not in extraction
                'tom_evidence': get_evidence_string(tomtratt),

                # Pattern B (boolean pattern)
                'patb_detected': pattern_b.detected if pattern_b else False,
                'patb_years': normalized_data.get('consecutive_loss_years', 0),
                'patb_construction': data.get('property_agent', {}).get('construction_year'),
                'patb_age': normalized_data.get('building_age_at_report', 0),
                'patb_concern': pattern_b.detected if pattern_b else False,
                'patb_evidence': get_evidence_string(pattern_b),

                # Interest Victim (boolean pattern)
                'int_detected': interest_victim.detected if interest_victim else False,
                'int_pct': None,  # Not in extraction
                'int_expense': None,  # Not in extraction
                'int_trigger': interest_victim.detected if interest_victim else False,
                'int_evidence': get_evidence_string(interest_victim),

                # Scores (placeholders)
                'mgmt_score': mgmt_quality.get('score'),
                'mgmt_grade': mgmt_quality.get('grade'),
                'mgmt_factors': Json(mgmt_quality.get('factors', {})),
                'fin_score': financial_stability.get('score'),
                'fin_grade': financial_stability.get('grade'),
                'fin_factors': Json(financial_stability.get('factors', {})),
                'stab_score': stabilization.get('score'),
                'stab_grade': stabilization.get('grade'),
                'stab_years': stabilization.get('timeframe_years'),
                'risk_score': overall_risk.get('score'),
                'risk_grade': overall_risk.get('grade'),
                'risk_category': overall_risk.get('category'),

                'classification_json': Json({
                    'refinancing_risk': {
                        'tier': refinancing.tier if refinancing else 'NONE',
                        'confidence': refinancing.confidence if refinancing else 0,
                        'evidence': refinancing.evidence if refinancing else []
                    },
                    'fee_response': {
                        'tier': fee_response.tier if fee_response else 'PROACTIVE',
                        'confidence': fee_response.confidence if fee_response else 0,
                        'evidence': fee_response.evidence if fee_response else []
                    },
                    'depreciation_paradox': {
                        'detected': depreciation.detected if depreciation else False,
                        'confidence': depreciation.confidence if depreciation else 0,
                        'evidence': depreciation.evidence if depreciation else []
                    },
                    'cash_crisis': {
                        'detected': cash_crisis.detected if cash_crisis else False,
                        'confidence': cash_crisis.confidence if cash_crisis else 0,
                        'evidence': cash_crisis.evidence if cash_crisis else []
                    },
                    'lokaler_dependency': {
                        'tier': lokaler.tier if lokaler else 'NONE',
                        'confidence': lokaler.confidence if lokaler else 0,
                        'evidence': lokaler.evidence if lokaler else []
                    },
                    'tomtratt_escalation': {
                        'tier': tomtratt.tier if tomtratt else 'NONE',
                        'confidence': tomtratt.confidence if tomtratt else 0,
                        'evidence': tomtratt.evidence if tomtratt else []
                    },
                    'pattern_b': {
                        'detected': pattern_b.detected if pattern_b else False,
                        'confidence': pattern_b.confidence if pattern_b else 0,
                        'evidence': pattern_b.evidence if pattern_b else []
                    },
                    'interest_rate_victim': {
                        'detected': interest_victim.detected if interest_victim else False,
                        'confidence': interest_victim.confidence if interest_victim else 0,
                        'evidence': interest_victim.evidence if interest_victim else []
                    },
                    'management_quality': mgmt_quality,
                    'financial_stability': financial_stability,
                    'stabilization': stabilization,
                    'overall_risk': overall_risk
                })
            }

            self.cursor.execute(insert_sql, values)

            # Insert pattern summary
            self._insert_pattern_summary(extraction_id, brf_id, classifications)

        except Exception as e:
            print(f"❌ Classification failed for {brf_id}: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _insert_pattern_summary(self, extraction_id: int, brf_id: str, results: Dict):
        """Insert pattern summary for easy querying"""
        insert_sql = """
        INSERT INTO ground_truth_pattern_summary (
            extraction_id, brf_id,
            has_refinancing_risk, has_fee_distress, has_depreciation_paradox,
            has_cash_crisis, has_lokaler_risk, has_tomtratt_escalation,
            has_pattern_b, has_interest_rate_shock,
            critical_pattern_count, high_risk_pattern_count,
            risk_category, requires_attention
        ) VALUES (
            %(extraction_id)s, %(brf_id)s,
            %(ref)s, %(fee)s, %(dep)s,
            %(cash)s, %(lok)s, %(tom)s,
            %(patb)s, %(int)s,
            %(critical)s, %(high)s,
            %(risk)s, %(attention)s
        );
        """

        refinancing = results.get('refinancing_risk')
        fee_response = results.get('fee_response')
        depreciation = results.get('depreciation_paradox')
        cash_crisis = results.get('cash_crisis')
        lokaler = results.get('lokaler_dependency')
        tomtratt = results.get('tomtratt_escalation')
        pattern_b = results.get('pattern_b')
        interest_victim = results.get('interest_rate_victim')

        # Count critical and high-risk patterns
        critical_count = sum([
            cash_crisis and cash_crisis.detected,
            refinancing and refinancing.tier == 'EXTREME'
        ])

        high_count = sum([
            refinancing and refinancing.tier in ['HIGH', 'EXTREME'],
            fee_response and fee_response.tier == 'DISTRESS',
            cash_crisis and cash_crisis.detected,
            lokaler and lokaler.tier in ['HIGH', 'MEDIUM_HIGH'],
            tomtratt and tomtratt.tier in ['HIGH', 'EXTREME']
        ])

        values = {
            'extraction_id': extraction_id,
            'brf_id': brf_id,
            'ref': refinancing.tier != 'NONE' if refinancing else False,
            'fee': fee_response.tier != 'PROACTIVE' if fee_response else False,
            'dep': depreciation.detected if depreciation else False,
            'cash': cash_crisis.detected if cash_crisis else False,
            'lok': lokaler.tier not in ['LOW', 'NONE'] if lokaler else False,
            'tom': tomtratt.tier != 'NONE' if tomtratt else False,
            'patb': pattern_b.detected if pattern_b else False,
            'int': interest_victim.detected if interest_victim else False,
            'critical': critical_count,
            'high': high_count,
            'risk': 'UNKNOWN',  # Overall risk not calculated yet
            'attention': critical_count > 0 or high_count >= 2
        }

        self.cursor.execute(insert_sql, values)

    def generate_summary(self) -> Dict:
        """Generate summary report of classification results"""
        # Get pattern distribution
        self.cursor.execute("SELECT * FROM vw_pattern_distribution;")
        pattern_dist = self.cursor.fetchone()

        # Get high-risk BRFs
        self.cursor.execute("""
            SELECT brf_id, organization_name, overall_risk_category,
                   critical_pattern_count, high_risk_pattern_count
            FROM vw_high_risk_brfs
            ORDER BY overall_risk_score DESC
            LIMIT 10;
        """)
        high_risk = self.cursor.fetchall()

        # Get overall statistics
        self.cursor.execute("""
            SELECT
                COUNT(*) as total_brfs,
                AVG(overall_risk_score) as avg_risk_score,
                COUNT(CASE WHEN overall_risk_category = 'CRITICAL' THEN 1 END) as critical_count,
                COUNT(CASE WHEN overall_risk_category = 'HIGH' THEN 1 END) as high_count,
                COUNT(CASE WHEN overall_risk_category = 'MEDIUM' THEN 1 END) as medium_count,
                COUNT(CASE WHEN overall_risk_category = 'LOW' THEN 1 END) as low_count
            FROM ground_truth_classifications;
        """)
        stats = self.cursor.fetchone()

        return {
            'pattern_distribution': pattern_dist,
            'high_risk_brfs': high_risk,
            'overall_statistics': stats if stats else (0, None, 0, 0, 0, 0),
            'timestamp': datetime.now().isoformat()
        }

    def run(self, batch_results_dir: Path):
        """Main execution flow"""
        print("=" * 80)
        print("GROUND TRUTH LOADER & CLASSIFIER")
        print("=" * 80)

        # Step 1: Connect to database
        self.connect()

        # Step 2: Create schema
        print("\n📋 Creating database schema...")
        self.create_schema()

        # Step 3: Load JSON files
        print("\n📂 Loading ground truth JSON files...")
        extractions = self.load_json_files(batch_results_dir)

        # Step 4: Insert extractions and run classification
        print(f"\n💾 Processing {len(extractions)} ground truth records...")

        success_count = 0
        classification_count = 0

        for i, extraction in enumerate(extractions, 1):
            brf_id = extraction['brf_id']
            print(f"\n[{i}/{len(extractions)}] Processing {brf_id}...")

            # Insert extraction
            try:
                extraction_id = self.insert_extraction(extraction)

                if extraction_id:
                    success_count += 1
                    print(f"  ✅ Extraction inserted (ID: {extraction_id})")

                    # Run classification
                    try:
                        self.classify_extraction(extraction_id, brf_id, extraction['data'])
                        classification_count += 1
                        print(f"  ✅ Classification complete")
                    except Exception as e:
                        print(f"  ⚠️  Classification failed: {e}")

                    # Commit after each successful extraction
                    self.conn.commit()
                else:
                    print(f"  ❌ Extraction failed")
                    self.conn.rollback()

            except Exception as e:
                print(f"  ❌ Extraction failed: {e}")
                self.conn.rollback()

        print(f"\n✅ Processing complete!")

        # Step 5: Generate summary
        print("\n📊 Generating summary report...")
        summary = self.generate_summary()

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)

        stats = summary['overall_statistics']
        print(f"\n📈 Overall Statistics:")
        print(f"  Total BRFs: {stats[0]}")

        if stats[0] > 0:
            print(f"  Average Risk Score: {stats[1]:.2f}" if stats[1] else "  Average Risk Score: N/A")
            print(f"  Critical Risk: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
            print(f"  High Risk: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
            print(f"  Medium Risk: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
            print(f"  Low Risk: {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")

        pattern_dist = summary['pattern_distribution']
        if pattern_dist:
            print(f"\n🎯 Pattern Distribution:")
            print(f"  Refinancing Risk: {pattern_dist[1]}")
            print(f"  Fee Distress: {pattern_dist[2]}")
            print(f"  Depreciation Paradox: {pattern_dist[3]}")
            print(f"  Cash Crisis: {pattern_dist[4]}")
            print(f"  Lokaler Risk: {pattern_dist[5]}")
            print(f"  Tomträtt Escalation: {pattern_dist[6]}")
            print(f"  Pattern B: {pattern_dist[7]}")
            print(f"  Interest Rate Shock: {pattern_dist[8]}")

        print(f"\n✅ Processing complete!")
        print(f"  - {success_count}/{len(extractions)} extractions inserted")
        print(f"  - {classification_count}/{len(extractions)} classifications completed")

        # Save summary to JSON
        summary_path = batch_results_dir.parent / "CLASSIFICATION_SUMMARY.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n💾 Summary saved to: {summary_path}")

        return summary


def main():
    """Main entry point"""
    # Configuration
    DB_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/gracian_ground_truth')

    # Paths
    SCRIPT_DIR = Path(__file__).parent
    SCHEMA_PATH = SCRIPT_DIR.parent / "schema" / "ground_truth_database_schema.sql"
    BATCH_RESULTS_DIR = SCRIPT_DIR.parent / "batch_results"
    CLASSIFIER_CONFIG = PROJECT_ROOT / "gracian_pipeline" / "config" / "classification" / "pattern_classification_rules.yaml"

    # Validate paths
    if not SCHEMA_PATH.exists():
        print(f"❌ Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    if not BATCH_RESULTS_DIR.exists():
        print(f"❌ Batch results directory not found: {BATCH_RESULTS_DIR}")
        sys.exit(1)

    if not CLASSIFIER_CONFIG.exists():
        print(f"⚠️  Classifier config not found: {CLASSIFIER_CONFIG}")
        print(f"⚠️  Classification will be skipped")

    # Run loader
    loader = GroundTruthLoader(DB_URL, SCHEMA_PATH, CLASSIFIER_CONFIG)

    try:
        summary = loader.run(BATCH_RESULTS_DIR)
        print("\n🎉 Ground truth loading and classification complete!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        if loader.conn:
            loader.conn.rollback()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        if loader.conn:
            loader.conn.rollback()
        sys.exit(1)

    finally:
        if loader.conn:
            loader.conn.close()
            print("🔌 Database connection closed")


if __name__ == "__main__":
    main()
