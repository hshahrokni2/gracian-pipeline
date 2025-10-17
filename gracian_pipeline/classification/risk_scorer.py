"""
Layer 4: Risk Scoring

Calculates composite risk scores from pattern classifications and raw data.
Uses weighted factor models to aggregate multiple signals into 0-100 scores.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class ScoringResult:
    """Result of a risk score calculation."""
    score_name: str
    score: Optional[float]  # 0-100, or None if insufficient data
    grade: str  # A, B, C, D, F
    factors: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # {factor: (value, weight)}
    confidence: float = 1.0  # 0-1, based on data completeness
    missing_factors: List[str] = field(default_factory=list)
    interpretation: str = ""


class RiskScorer:
    """
    Calculates composite risk scores from classified patterns and raw data.

    Scores (0-100 scale):
    1. Management Quality Score - How well is the BRF managed?
    2. Stabilization Probability - Will fee increases stabilize finances?
    3. Operational Health Score - Current operational strength
    4. Structural Risk Score - Long-term structural vulnerabilities (higher = more risk)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize risk scorer.

        Args:
            config_path: Path to YAML config (optional, uses defaults if None)
        """
        if config_path and Path(config_path).exists():
            self.config = self._load_config(config_path)
        else:
            self.config = self._default_config()

    def _load_config(self, config_path: Path) -> Dict:
        """Load scoring configuration from YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _default_config(self) -> Dict:
        """Default scoring configuration."""
        return {
            'management_quality': {
                'weights': {
                    'fee_response': 0.40,
                    'balance_sheet': 0.25,
                    'profitability': 0.20,
                    'reserves': 0.15
                }
            },
            'stabilization_probability': {
                'weights': {
                    'fee_adequacy': 0.35,
                    'balance_sheet': 0.30,
                    'debt_burden': 0.20,
                    'trend': 0.15
                }
            },
            'operational_health': {
                'weights': {
                    'profitability': 0.30,
                    'liquidity': 0.25,
                    'soliditet': 0.25,
                    'cost_efficiency': 0.20
                }
            },
            'structural_risk': {
                'weights': {
                    'refinancing_risk': 0.30,
                    'debt_burden': 0.25,
                    'dependencies': 0.20,
                    'external_factors': 0.15,
                    'liquidity': 0.10
                }
            }
        }

    def calculate_management_quality_score(
        self,
        classified_patterns: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> ScoringResult:
        """
        Calculate management quality score (0-100).

        Higher score = better management

        Factors (with weights):
        1. Fee response appropriateness (40%)
        2. Balance sheet strength (25%)
        3. Profitability trend (20%)
        4. Reserve fund adequacy (15%)
        """
        factors = {}
        weights = self.config['management_quality']['weights']
        missing_factors = []

        # Factor 1: Fee Response Appropriateness (40%)
        fee_response = classified_patterns.get('fee_response', {}).get('tier')
        if fee_response:
            if fee_response == 'PROACTIVE':
                factors['fee_response'] = (90, weights['fee_response'])
            elif fee_response == 'AGGRESSIVE':
                factors['fee_response'] = (70, weights['fee_response'])
            elif fee_response == 'REACTIVE':
                factors['fee_response'] = (50, weights['fee_response'])
            elif fee_response == 'DISTRESS':
                factors['fee_response'] = (20, weights['fee_response'])
        else:
            missing_factors.append('fee_response')

        # Factor 2: Balance Sheet Strength (25%)
        soliditet = raw_data.get('soliditet_pct')
        if soliditet is not None:
            if soliditet >= 80:
                balance_score = 80 + (soliditet - 80)
            elif soliditet >= 60:
                balance_score = 40 + ((soliditet - 60) / 20) * 40
            else:
                balance_score = (soliditet / 60) * 40
            factors['balance_sheet'] = (balance_score, weights['balance_sheet'])
        else:
            missing_factors.append('balance_sheet')

        # Factor 3: Profitability Trend (20%)
        result_current = raw_data.get('result_without_depreciation_current_year')
        result_prior = raw_data.get('result_without_depreciation_prior_year')

        if result_current is not None:
            if result_current > 0:
                if result_prior and result_prior > 0:
                    profitability_score = 85  # Consistently profitable
                else:
                    profitability_score = 70  # Profitable now (improvement)
            else:
                if result_prior and result_prior < result_current:
                    profitability_score = 45  # Improving (less negative)
                else:
                    profitability_score = 25  # Declining or consistently negative
            factors['profitability'] = (profitability_score, weights['profitability'])
        else:
            missing_factors.append('profitability')

        # Factor 4: Reserve Fund Adequacy (15%)
        reserve_ratio = raw_data.get('reserve_fund_to_revenue_ratio')
        if reserve_ratio is not None:
            if reserve_ratio >= 20:
                reserve_score = 90
            elif reserve_ratio >= 10:
                reserve_score = 60 + (reserve_ratio - 10) * 3
            else:
                reserve_score = reserve_ratio * 6
            factors['reserves'] = (reserve_score, weights['reserves'])
        else:
            missing_factors.append('reserves')

        # Calculate weighted score
        if not factors:
            return ScoringResult(
                score_name="management_quality",
                score=None,
                grade="INSUFFICIENT_DATA",
                factors={},
                confidence=0.0,
                missing_factors=missing_factors
            )

        # Normalize weights to sum to 1.0
        total_weight = sum(w for _, w in factors.values())
        score = sum(v * (w / total_weight) for v, w in factors.values())

        # Grade assignment
        grade = self._assign_grade(score)

        # Confidence based on data completeness
        confidence = len(factors) / len(weights)

        return ScoringResult(
            score_name="management_quality",
            score=round(score, 1),
            grade=grade,
            factors=factors,
            confidence=confidence,
            missing_factors=missing_factors,
            interpretation=self._interpret_management_score(score)
        )

    def calculate_stabilization_probability(
        self,
        classified_patterns: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> ScoringResult:
        """
        Calculate stabilization probability (0-100%).

        Predicts likelihood that fee increases will stabilize finances.

        Factors:
        1. Fee adequacy vs. costs (35%)
        2. Balance sheet strength (30%)
        3. Debt burden (20%)
        4. Profitability trend (15%)
        """
        factors = {}
        weights = self.config['stabilization_probability']['weights']
        missing_factors = []

        # Factor 1: Fee Adequacy (35%)
        monthly_fee = raw_data.get('monthly_fee')
        operating_costs_per_unit = raw_data.get('operating_costs') / raw_data.get('total_apartments', 1) if raw_data.get('operating_costs') and raw_data.get('total_apartments') else None

        if monthly_fee and operating_costs_per_unit:
            coverage_ratio = (monthly_fee * 12) / operating_costs_per_unit if operating_costs_per_unit > 0 else 0

            if coverage_ratio >= 1.2:
                adequacy_score = 90
            elif coverage_ratio >= 1.0:
                adequacy_score = 70
            elif coverage_ratio >= 0.8:
                adequacy_score = 50
            else:
                adequacy_score = 30
            factors['fee_adequacy'] = (adequacy_score, weights['fee_adequacy'])
        else:
            missing_factors.append('fee_adequacy')

        # Factor 2: Balance Sheet Strength (30%)
        soliditet = raw_data.get('soliditet_pct')
        if soliditet:
            balance_score = min(100, soliditet * 1.2)  # 80% soliditet → 96 score
            factors['balance_sheet'] = (balance_score, weights['balance_sheet'])
        else:
            missing_factors.append('balance_sheet')

        # Factor 3: Debt Burden (20%)
        interest_to_revenue = raw_data.get('interest_expense_to_revenue_ratio')
        if interest_to_revenue:
            if interest_to_revenue < 10:
                debt_burden_score = 90
            elif interest_to_revenue < 20:
                debt_burden_score = 70
            elif interest_to_revenue < 30:
                debt_burden_score = 50
            else:
                debt_burden_score = 30
            factors['debt_burden'] = (debt_burden_score, weights['debt_burden'])
        else:
            missing_factors.append('debt_burden')

        # Factor 4: Trend (15%)
        result_current = raw_data.get('net_income')
        result_prior = raw_data.get('net_income_prior_year')

        if result_current is not None and result_prior is not None:
            if result_current > result_prior:
                trend_score = 80  # Improving
            elif result_current == result_prior:
                trend_score = 60  # Stable
            else:
                trend_score = 40  # Declining
            factors['trend'] = (trend_score, weights['trend'])
        else:
            missing_factors.append('trend')

        # Calculate score
        if not factors:
            return ScoringResult(
                score_name="stabilization_probability",
                score=None,
                grade="INSUFFICIENT_DATA",
                factors={},
                confidence=0.0,
                missing_factors=missing_factors
            )

        total_weight = sum(w for _, w in factors.values())
        score = sum(v * (w / total_weight) for v, w in factors.values())

        return ScoringResult(
            score_name="stabilization_probability",
            score=round(score, 1),
            grade=self._assign_grade(score),
            factors=factors,
            confidence=len(factors) / len(weights),
            missing_factors=missing_factors,
            interpretation=f"{score:.0f}% probability of successful stabilization"
        )

    def calculate_operational_health_score(
        self,
        classified_patterns: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> ScoringResult:
        """
        Calculate operational health score (0-100).

        Measures current operational strength.

        Factors:
        1. Profitability (30%)
        2. Liquidity (25%)
        3. Soliditet (25%)
        4. Cost efficiency (20%)
        """
        factors = {}
        weights = self.config['operational_health']['weights']
        missing_factors = []

        # Factor 1: Profitability (30%)
        net_income_margin = raw_data.get('net_income_margin')
        if net_income_margin is not None:
            if net_income_margin >= 15:
                profitability_score = 90
            elif net_income_margin >= 10:
                profitability_score = 75
            elif net_income_margin >= 5:
                profitability_score = 60
            elif net_income_margin >= 0:
                profitability_score = 45
            else:
                profitability_score = 30
            factors['profitability'] = (profitability_score, weights['profitability'])
        else:
            missing_factors.append('profitability')

        # Factor 2: Liquidity (25%)
        cash_ratio = raw_data.get('cash_to_debt_ratio_current_year')
        if cash_ratio is not None:
            if cash_ratio >= 15:
                liquidity_score = 90
            elif cash_ratio >= 10:
                liquidity_score = 75
            elif cash_ratio >= 5:
                liquidity_score = 60
            else:
                liquidity_score = 40
            factors['liquidity'] = (liquidity_score, weights['liquidity'])
        else:
            missing_factors.append('liquidity')

        # Factor 3: Soliditet (25%)
        soliditet = raw_data.get('soliditet_pct')
        if soliditet:
            soliditet_score = min(100, soliditet * 1.1)  # 90% → 99 score
            factors['soliditet'] = (soliditet_score, weights['soliditet'])
        else:
            missing_factors.append('soliditet')

        # Factor 4: Cost Efficiency (20%)
        operating_margin = raw_data.get('operating_margin')
        if operating_margin is not None:
            if operating_margin >= 20:
                efficiency_score = 90
            elif operating_margin >= 15:
                efficiency_score = 75
            elif operating_margin >= 10:
                efficiency_score = 60
            else:
                efficiency_score = 40
            factors['cost_efficiency'] = (efficiency_score, weights['cost_efficiency'])
        else:
            missing_factors.append('cost_efficiency')

        # Calculate score
        if not factors:
            return ScoringResult(
                score_name="operational_health",
                score=None,
                grade="INSUFFICIENT_DATA",
                factors={},
                confidence=0.0,
                missing_factors=missing_factors
            )

        total_weight = sum(w for _, w in factors.values())
        score = sum(v * (w / total_weight) for v, w in factors.values())

        return ScoringResult(
            score_name="operational_health",
            score=round(score, 1),
            grade=self._assign_grade(score),
            factors=factors,
            confidence=len(factors) / len(weights),
            missing_factors=missing_factors,
            interpretation=self._interpret_health_score(score)
        )

    def calculate_structural_risk_score(
        self,
        classified_patterns: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> ScoringResult:
        """
        Calculate structural risk score (0-100).

        Higher score = MORE risk

        Factors:
        1. Refinancing risk (30%)
        2. Debt burden (25%)
        3. Dependencies (lokaler, tomträtt) (20%)
        4. External factors (15%)
        5. Liquidity risk (10%)
        """
        factors = {}
        weights = self.config['structural_risk']['weights']
        missing_factors = []

        # Factor 1: Refinancing Risk (30%)
        refinancing_tier = classified_patterns.get('refinancing_risk', {}).get('tier')
        if refinancing_tier:
            refinancing_score = {
                'EXTREME': 95,
                'HIGH': 75,
                'MEDIUM': 50,
                'NONE': 20
            }.get(refinancing_tier, 50)
            factors['refinancing_risk'] = (refinancing_score, weights['refinancing_risk'])
        else:
            missing_factors.append('refinancing_risk')

        # Factor 2: Debt Burden (25%)
        debt_to_equity = raw_data.get('debt_to_equity_ratio')
        if debt_to_equity:
            if debt_to_equity >= 200:
                debt_score = 90
            elif debt_to_equity >= 100:
                debt_score = 70
            elif debt_to_equity >= 50:
                debt_score = 50
            else:
                debt_score = 30
            factors['debt_burden'] = (debt_score, weights['debt_burden'])
        else:
            missing_factors.append('debt_burden')

        # Factor 3: Dependencies (20%)
        lokaler_risk = classified_patterns.get('lokaler_dependency', {}).get('tier')
        tomtratt_risk = classified_patterns.get('tomtratt_escalation', {}).get('tier')

        dependency_scores = []
        if lokaler_risk:
            dependency_scores.append({
                'HIGH': 90,
                'MEDIUM_HIGH': 70,
                'MEDIUM': 50,
                'LOW': 20
            }.get(lokaler_risk, 50))

        if tomtratt_risk:
            dependency_scores.append({
                'EXTREME': 95,
                'HIGH': 75,
                'MEDIUM': 50,
                'LOW': 30,
                'NONE': 10
            }.get(tomtratt_risk, 30))

        if dependency_scores:
            factors['dependencies'] = (max(dependency_scores), weights['dependencies'])
        else:
            missing_factors.append('dependencies')

        # Factor 4: External Factors (15%)
        interest_victim = classified_patterns.get('interest_rate_victim', {}).get('detected')
        if interest_victim is not None:
            external_score = 80 if interest_victim else 30
            factors['external_factors'] = (external_score, weights['external_factors'])
        else:
            missing_factors.append('external_factors')

        # Factor 5: Liquidity Risk (10%)
        cash_crisis = classified_patterns.get('cash_crisis', {}).get('detected')
        if cash_crisis is not None:
            liquidity_score = 95 if cash_crisis else 25
            factors['liquidity'] = (liquidity_score, weights['liquidity'])
        else:
            missing_factors.append('liquidity')

        # Calculate score
        if not factors:
            return ScoringResult(
                score_name="structural_risk",
                score=None,
                grade="INSUFFICIENT_DATA",
                factors={},
                confidence=0.0,
                missing_factors=missing_factors
            )

        total_weight = sum(w for _, w in factors.values())
        score = sum(v * (w / total_weight) for v, w in factors.values())

        return ScoringResult(
            score_name="structural_risk",
            score=round(score, 1),
            grade=self._assign_risk_grade(score),  # Note: inverted grading for risk
            factors=factors,
            confidence=len(factors) / len(weights),
            missing_factors=missing_factors,
            interpretation=self._interpret_risk_score(score)
        )

    def _assign_grade(self, score: float) -> str:
        """Assign A-F grade (higher score = better grade)."""
        if score >= 85:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _assign_risk_grade(self, score: float) -> str:
        """Assign A-F grade for risk (higher score = WORSE grade)."""
        if score >= 85:
            return "F"  # Very high risk
        elif score >= 75:
            return "D"  # High risk
        elif score >= 60:
            return "C"  # Moderate risk
        elif score >= 50:
            return "B"  # Low risk
        else:
            return "A"  # Very low risk

    def _interpret_management_score(self, score: float) -> str:
        """Interpret management quality score."""
        if score >= 85:
            return "Excellent management with proactive financial planning"
        elif score >= 75:
            return "Good management with sound financial decisions"
        elif score >= 60:
            return "Average management meeting basic requirements"
        elif score >= 50:
            return "Below average management showing reactive decision-making"
        else:
            return "Poor management requiring improvement or consultation"

    def _interpret_health_score(self, score: float) -> str:
        """Interpret operational health score."""
        if score >= 85:
            return "Excellent operational health with strong fundamentals"
        elif score >= 75:
            return "Good operational health with stable performance"
        elif score >= 60:
            return "Fair operational health with some concerns"
        elif score >= 50:
            return "Weak operational health requiring attention"
        else:
            return "Poor operational health with significant issues"

    def _interpret_risk_score(self, score: float) -> str:
        """Interpret structural risk score."""
        if score >= 85:
            return "Very high risk requiring immediate intervention"
        elif score >= 75:
            return "High risk with multiple vulnerabilities"
        elif score >= 60:
            return "Moderate risk needing monitoring"
        elif score >= 50:
            return "Low risk with manageable issues"
        else:
            return "Very low risk with strong fundamentals"

    def calculate_all_scores(
        self,
        classified_patterns: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> Dict[str, ScoringResult]:
        """
        Calculate all 4 composite risk scores.

        Returns:
            Dictionary mapping score_name → ScoringResult
        """
        return {
            'management_quality': self.calculate_management_quality_score(
                classified_patterns, raw_data
            ),
            'stabilization_probability': self.calculate_stabilization_probability(
                classified_patterns, raw_data
            ),
            'operational_health': self.calculate_operational_health_score(
                classified_patterns, raw_data
            ),
            'structural_risk': self.calculate_structural_risk_score(
                classified_patterns, raw_data
            ),
        }
