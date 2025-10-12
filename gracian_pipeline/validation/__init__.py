"""
Gracian Pipeline Validation Module

Provides semantic validation for heterogeneous BRF annual report PDFs.

Key Components:
- SemanticFieldMatcher: Finds fields by meaning, not exact path
- ConfidenceBasedValidator: Validates with confidence-weighted metrics
- LearningValidator: Learns from validated documents over time
"""

from .semantic_matcher import SemanticFieldMatcher, FieldMatch

__all__ = [
    'SemanticFieldMatcher',
    'FieldMatch',
]
