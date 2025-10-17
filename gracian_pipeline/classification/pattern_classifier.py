"""
Layer 3: Pattern Classification

Configuration-driven pattern classification system.
Classifies BRF patterns based on validated data and configurable rules.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from enum import Enum


class LogicOperator(Enum):
    """Logical operators for condition evaluation."""
    ALL = "ALL"  # AND logic
    ANY = "ANY"  # OR logic
    COMPLEX = "COMPLEX"  # Nested logic


@dataclass
class EvaluationResult:
    """Result of condition evaluation."""
    matched: bool
    confidence: float  # 0-1, based on data completeness
    evidence: List[str] = field(default_factory=list)
    thresholds_met: List[str] = field(default_factory=list)
    fields_used: List[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Result of pattern classification."""
    pattern_name: str
    tier: str  # e.g., "HIGH", "EXTREME", "MEDIUM", "NONE"
    detected: Optional[bool] = None  # For boolean patterns
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    thresholds_met: List[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)


class PatternClassifier:
    """
    Generic pattern classifier driven by YAML configuration.

    Supports:
    - Multi-tier classifications (EXTREME, HIGH, MEDIUM, LOW, NONE)
    - Boolean pattern detection (TRUE/FALSE)
    - Complex nested conditions (AND/OR logic)
    - Evidence tracking (why was this classification made?)
    - Confidence scoring (based on data completeness)
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize classifier with configuration file.

        Args:
            config_path: Path to YAML configuration file with pattern definitions
        """
        self.config_path = Path(config_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Load pattern classification rules from YAML config."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        if not config or 'patterns' not in config:
            raise ValueError(f"Invalid config file: {self.config_path}")

        return config['patterns']

    def classify(self, pattern_name: str, data: Dict[str, Any]) -> ClassificationResult:
        """
        Classify a pattern based on validated data.

        Args:
            pattern_name: Pattern to classify (e.g., "refinancing_risk")
            data: Validated and normalized extraction data

        Returns:
            ClassificationResult with tier/detection, confidence, and evidence
        """
        if pattern_name not in self.rules:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        pattern = self.rules[pattern_name]
        pattern_type = pattern.get('type', 'categorical')

        if pattern_type == 'boolean':
            return self._classify_boolean(pattern_name, pattern, data)
        else:
            return self._classify_categorical(pattern_name, pattern, data)

    def _classify_boolean(
        self,
        pattern_name: str,
        pattern: Dict[str, Any],
        data: Dict[str, Any]
    ) -> ClassificationResult:
        """Classify boolean pattern (detected/not detected)."""

        conditions = pattern.get('conditions', [])
        logic = pattern.get('logic', 'ALL')

        result = self._evaluate_conditions(conditions, data, logic)

        return ClassificationResult(
            pattern_name=pattern_name,
            tier=None,
            detected=result.matched,
            confidence=result.confidence,
            evidence=result.evidence,
            thresholds_met=result.thresholds_met,
            debug_info={
                'pattern_type': 'boolean',
                'conditions_evaluated': len(conditions),
                'fields_used': result.fields_used
            }
        )

    def _classify_categorical(
        self,
        pattern_name: str,
        pattern: Dict[str, Any],
        data: Dict[str, Any]
    ) -> ClassificationResult:
        """Classify categorical pattern (tiered: EXTREME, HIGH, MEDIUM, etc.)."""

        tiers = pattern.get('tiers', {})

        # Evaluate tiers in order (assuming EXTREME → HIGH → MEDIUM → NONE)
        for tier_name, tier_config in tiers.items():
            if tier_config.get('default'):
                continue  # Skip default tier for now

            conditions = tier_config.get('conditions', [])
            logic = tier_config.get('logic', 'ALL')

            result = self._evaluate_conditions(conditions, data, logic)

            if result.matched:
                return ClassificationResult(
                    pattern_name=pattern_name,
                    tier=tier_name,
                    detected=None,
                    confidence=result.confidence,
                    evidence=result.evidence,
                    thresholds_met=result.thresholds_met,
                    debug_info={
                        'pattern_type': 'categorical',
                        'tier_config': tier_config,
                        'fields_used': result.fields_used
                    }
                )

        # No tier matched → Default tier or INSUFFICIENT_DATA
        default_tier = self._get_default_tier(tiers)

        return ClassificationResult(
            pattern_name=pattern_name,
            tier=default_tier,
            detected=None,
            confidence=0.5,  # Low confidence for default
            evidence=["No threshold conditions met - using default tier"],
            thresholds_met=[],
            debug_info={
                'pattern_type': 'categorical',
                'reason': 'default_tier'
            }
        )

    def _evaluate_conditions(
        self,
        conditions: List[Dict],
        data: Dict[str, Any],
        logic: str
    ) -> EvaluationResult:
        """
        Evaluate a list of conditions against data.

        Supports:
        - Simple comparisons: >, <, >=, <=, ==, BETWEEN
        - Logical operators: ALL (AND), ANY (OR), COMPLEX (nested)
        - Missing data handling: graceful degradation
        """
        matched_conditions = []
        evidence = []
        fields_used = set()
        total_conditions = len(conditions)

        for condition in conditions:
            # Handle nested OR logic
            if 'OR' in condition:
                or_result = self._evaluate_conditions(
                    condition['OR'],
                    data,
                    logic='ANY'
                )
                if or_result.matched:
                    matched_conditions.append(condition)
                    evidence.extend([f"({e})" for e in or_result.evidence])
                    fields_used.update(or_result.fields_used)
                continue

            # Handle nested AND logic
            if 'AND' in condition:
                and_result = self._evaluate_conditions(
                    condition['AND'],
                    data,
                    logic='ALL'
                )
                if and_result.matched:
                    matched_conditions.append(condition)
                    evidence.extend([f"({e})" for e in and_result.evidence])
                    fields_used.update(and_result.fields_used)
                continue

            # Extract condition components
            field = condition.get('field')
            operator = condition.get('operator')
            threshold = condition.get('value')

            if not all([field, operator, threshold is not None]):
                continue  # Skip malformed conditions

            # Get actual value from data
            actual = data.get(field)
            if actual is None:
                total_conditions -= 1  # Don't count missing data against us
                continue

            fields_used.add(field)

            # Evaluate comparison
            try:
                matched = self._compare_value(actual, operator, threshold)

                if matched:
                    matched_conditions.append(condition)
                    evidence.append(
                        f"{field}: {actual} {operator} {threshold} ✓"
                    )
            except Exception as e:
                # Skip invalid comparisons
                continue

        # Apply logic operator
        if logic == 'ALL':
            final_matched = len(matched_conditions) == total_conditions and total_conditions > 0
        elif logic == 'ANY':
            final_matched = len(matched_conditions) > 0
        else:  # COMPLEX - handled recursively
            final_matched = len(matched_conditions) > 0

        # Calculate confidence based on data completeness
        if total_conditions > 0:
            confidence = (len(matched_conditions) + (len(conditions) - total_conditions)) / len(conditions)
        else:
            confidence = 0.0

        confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

        return EvaluationResult(
            matched=final_matched,
            confidence=confidence,
            evidence=evidence,
            thresholds_met=[c.get('field') for c in matched_conditions if c.get('field')],
            fields_used=list(fields_used)
        )

    def _compare_value(
        self,
        actual: Union[int, float, str],
        operator: str,
        threshold: Union[int, float, str, List]
    ) -> bool:
        """Compare actual value against threshold using operator."""

        if operator == '>':
            return actual > threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '>=':
            return actual >= threshold
        elif operator == '<=':
            return actual <= threshold
        elif operator == '==':
            return actual == threshold
        elif operator == '!=':
            return actual != threshold
        elif operator == 'BETWEEN':
            if not isinstance(threshold, list) or len(threshold) != 2:
                return False
            return threshold[0] <= actual <= threshold[1]
        elif operator == 'IN':
            return actual in threshold
        elif operator == 'NOT_IN':
            return actual not in threshold
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _get_default_tier(self, tiers: Dict[str, Any]) -> str:
        """Get the default tier from tier configuration."""
        for tier_name, tier_config in tiers.items():
            if tier_config.get('default'):
                return tier_name

        # No explicit default → return INSUFFICIENT_DATA
        return "INSUFFICIENT_DATA"

    def classify_all(
        self,
        data: Dict[str, Any],
        patterns: Optional[List[str]] = None
    ) -> Dict[str, ClassificationResult]:
        """
        Classify all patterns (or specified patterns) for given data.

        Args:
            data: Validated extraction data
            patterns: List of pattern names to classify (None = all patterns)

        Returns:
            Dictionary mapping pattern_name → ClassificationResult
        """
        if patterns is None:
            patterns = list(self.rules.keys())

        results = {}
        for pattern_name in patterns:
            if pattern_name in self.rules:
                try:
                    results[pattern_name] = self.classify(pattern_name, data)
                except Exception as e:
                    # Log error but don't fail entire classification
                    results[pattern_name] = ClassificationResult(
                        pattern_name=pattern_name,
                        tier="ERROR",
                        confidence=0.0,
                        evidence=[f"Classification error: {str(e)}"]
                    )

        return results
