"""
Gracian Pipeline Validation Module

Phase 2B: Multi-Agent Cross-Validation System

Key Components:
- SemanticFieldMatcher: Finds fields by meaning, not exact path (legacy)
- CrossValidator: Financial, governance, property consistency checks (Phase 2B)
- HallucinationDetector: Template text, suspicious numbers detection (Phase 2B)
- ConsensusResolver: Majority voting, weighted averaging (Phase 2B)
"""

from .semantic_matcher import SemanticFieldMatcher, FieldMatch

# Phase 2B: Cross-validation components
from .cross_validation import (
    CrossValidator,
    ValidationWarning,
    FinancialConsistencyValidator,
    GovernanceConsistencyValidator,
    PropertyConsistencyValidator,
)

from .hallucination_detector import (
    HallucinationDetector,
    detect_hallucinations,
)

from .consensus_resolver import (
    ConsensusResolver,
    Conflict,
    resolve_conflicts,
)

__all__ = [
    # Legacy (pre-Phase 2B)
    'SemanticFieldMatcher',
    'FieldMatch',

    # Phase 2B: Cross-validation
    'CrossValidator',
    'ValidationWarning',
    'FinancialConsistencyValidator',
    'GovernanceConsistencyValidator',
    'PropertyConsistencyValidator',

    # Phase 2B: Hallucination detection
    'HallucinationDetector',
    'detect_hallucinations',

    # Phase 2B: Consensus resolution
    'ConsensusResolver',
    'Conflict',
    'resolve_conflicts',
]

__version__ = '2B.1.0'
