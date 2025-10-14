"""
Learning Loop for Path B Agents

Implements adaptive learning across documents:
1. Collect extraction patterns from successful extractions
2. Learn new Swedish terminology variants
3. Adapt confidence scoring based on validation results
4. Improve note detection patterns

Author: Claude Code
Date: 2025-10-13
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ExtractionPattern:
    """A learned pattern from successful extraction."""
    field_name: str
    swedish_term: str
    context_keywords: List[str]
    success_count: int = 0
    failure_count: int = 0
    confidence_avg: float = 0.0
    last_seen: datetime = field(default_factory=datetime.now)

    @property
    def reliability(self) -> float:
        """Calculate reliability score (0-1)."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    @property
    def is_reliable(self) -> bool:
        """Check if pattern is reliable (>80% success)."""
        return self.reliability > 0.8 and self.success_count >= 3


@dataclass
class TermVariant:
    """A learned Swedish term variant."""
    canonical_term: str
    variant: str
    document_count: int = 0
    confidence_avg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_term": self.canonical_term,
            "variant": self.variant,
            "document_count": self.document_count,
            "confidence_avg": self.confidence_avg
        }


@dataclass
class NotePattern:
    """A learned note heading pattern."""
    pattern: str
    note_type: str
    frequency: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "note_type": self.note_type,
            "frequency": self.frequency
        }


class LearningLoop:
    """
    Adaptive learning system for Path B agents.

    Learns from each document to improve future extractions:
    - Swedish term variants
    - Note heading patterns
    - Field extraction patterns
    - Confidence calibration
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize learning loop.

        Args:
            storage_path: Path to store learned patterns (default: gracian_pipeline/learned_patterns/)
        """
        if storage_path is None:
            base_dir = Path(__file__).parent.parent
            storage_path = base_dir / "learned_patterns"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Learning stores
        self.term_variants: Dict[str, List[TermVariant]] = defaultdict(list)
        self.note_patterns: List[NotePattern] = []
        self.extraction_patterns: List[ExtractionPattern] = []
        self.confidence_calibration: Dict[str, List[float]] = defaultdict(list)

        # Load existing learned patterns
        self._load_learned_patterns()

    def record_extraction(
        self,
        agent_id: str,
        field_name: str,
        value: Any,
        confidence: float,
        evidence: Dict[str, Any],
        validation_passed: bool
    ) -> None:
        """
        Record an extraction for learning.

        Args:
            agent_id: Agent that made extraction
            field_name: Field extracted
            value: Extracted value
            confidence: Confidence score
            evidence: Evidence dict (quotes, pages)
            validation_passed: Whether cross-validation passed
        """
        # Record for confidence calibration
        self.confidence_calibration[f"{agent_id}_{field_name}"].append(confidence)

        # Extract Swedish terms from evidence
        if "quotes" in evidence and evidence["quotes"]:
            for quote in evidence["quotes"]:
                self._learn_swedish_terms(field_name, quote, confidence)

        # Record extraction pattern
        if validation_passed and confidence > 0.7:
            pattern = self._create_extraction_pattern(
                field_name, value, evidence, confidence
            )
            self._update_extraction_pattern(pattern, success=True)
        elif not validation_passed or confidence < 0.5:
            pattern = self._create_extraction_pattern(
                field_name, value, evidence, confidence
            )
            self._update_extraction_pattern(pattern, success=False)

    def record_note_detection(
        self,
        heading: str,
        note_type: str,
        detection_confidence: float
    ) -> None:
        """
        Record a note detection for pattern learning.

        Args:
            heading: Note heading detected
            note_type: Type of note (depreciation, maintenance, tax)
            detection_confidence: Confidence in detection
        """
        if detection_confidence > 0.7:
            # Learn this heading pattern
            pattern = NotePattern(
                pattern=heading.lower().strip(),
                note_type=note_type,
                frequency=1
            )

            # Update existing or add new
            existing = next(
                (p for p in self.note_patterns if p.pattern == pattern.pattern),
                None
            )
            if existing:
                existing.frequency += 1
            else:
                self.note_patterns.append(pattern)

    def get_learned_terms(self, canonical_term: str) -> List[str]:
        """
        Get learned variants for a Swedish term.

        Args:
            canonical_term: Canonical term (e.g., "avskrivning")

        Returns:
            List of learned variants (e.g., ["avskrivningar", "avskrivningsmetod"])
        """
        variants = self.term_variants.get(canonical_term.lower(), [])
        # Return variants with >3 document occurrences
        return [v.variant for v in variants if v.document_count >= 3]

    def get_note_patterns(self, note_type: str) -> List[str]:
        """
        Get learned note heading patterns for a type.

        Args:
            note_type: Type of note (depreciation, maintenance, tax)

        Returns:
            List of heading patterns (sorted by frequency)
        """
        patterns = [p for p in self.note_patterns if p.note_type == note_type]
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        return [p.pattern for p in patterns[:10]]  # Top 10

    def get_reliable_patterns(self, field_name: str) -> List[ExtractionPattern]:
        """
        Get reliable extraction patterns for a field.

        Args:
            field_name: Field to get patterns for

        Returns:
            List of reliable patterns (>80% success rate)
        """
        patterns = [p for p in self.extraction_patterns if p.field_name == field_name]
        return [p for p in patterns if p.is_reliable]

    def calibrate_confidence(self, agent_id: str, field_name: str, raw_confidence: float) -> float:
        """
        Calibrate confidence score based on historical performance.

        Args:
            agent_id: Agent making prediction
            field_name: Field being extracted
            raw_confidence: Raw confidence from agent

        Returns:
            Calibrated confidence
        """
        key = f"{agent_id}_{field_name}"
        history = self.confidence_calibration.get(key, [])

        if len(history) < 10:
            # Not enough data, return raw
            return raw_confidence

        # Calculate average historical confidence
        avg_confidence = sum(history) / len(history)

        # Calibrate: if historically overconfident, reduce; if underconfident, increase
        if avg_confidence > 0.8:
            # Historically reliable, boost slightly
            return min(1.0, raw_confidence * 1.1)
        elif avg_confidence < 0.5:
            # Historically unreliable, reduce
            return raw_confidence * 0.8
        else:
            # Neutral, return raw
            return raw_confidence

    def save_learned_patterns(self) -> None:
        """Save learned patterns to disk."""
        try:
            # Save term variants
            term_variants_path = self.storage_path / "term_variants.json"
            with open(term_variants_path, 'w', encoding='utf-8') as f:
                data = {
                    canonical: [v.to_dict() for v in variants]
                    for canonical, variants in self.term_variants.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save note patterns
            note_patterns_path = self.storage_path / "note_patterns.json"
            with open(note_patterns_path, 'w', encoding='utf-8') as f:
                data = [p.to_dict() for p in self.note_patterns]
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save extraction patterns
            extraction_patterns_path = self.storage_path / "extraction_patterns.json"
            with open(extraction_patterns_path, 'w', encoding='utf-8') as f:
                data = [
                    {
                        "field_name": p.field_name,
                        "swedish_term": p.swedish_term,
                        "context_keywords": p.context_keywords,
                        "success_count": p.success_count,
                        "failure_count": p.failure_count,
                        "confidence_avg": p.confidence_avg,
                        "reliability": p.reliability
                    }
                    for p in self.extraction_patterns
                ]
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save confidence calibration
            calibration_path = self.storage_path / "confidence_calibration.json"
            with open(calibration_path, 'w', encoding='utf-8') as f:
                json.dump(self.confidence_calibration, f, indent=2)

            logger.info(f"Saved learned patterns to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save learned patterns: {e}")

    def _load_learned_patterns(self) -> None:
        """Load learned patterns from disk."""
        try:
            # Load term variants
            term_variants_path = self.storage_path / "term_variants.json"
            if term_variants_path.exists():
                with open(term_variants_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for canonical, variants in data.items():
                        self.term_variants[canonical] = [
                            TermVariant(**v) for v in variants
                        ]

            # Load note patterns
            note_patterns_path = self.storage_path / "note_patterns.json"
            if note_patterns_path.exists():
                with open(note_patterns_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.note_patterns = [NotePattern(**p) for p in data]

            # Load extraction patterns
            extraction_patterns_path = self.storage_path / "extraction_patterns.json"
            if extraction_patterns_path.exists():
                with open(extraction_patterns_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.extraction_patterns = [
                        ExtractionPattern(
                            field_name=p["field_name"],
                            swedish_term=p["swedish_term"],
                            context_keywords=p["context_keywords"],
                            success_count=p["success_count"],
                            failure_count=p["failure_count"],
                            confidence_avg=p["confidence_avg"]
                        )
                        for p in data
                    ]

            # Load confidence calibration
            calibration_path = self.storage_path / "confidence_calibration.json"
            if calibration_path.exists():
                with open(calibration_path, 'r', encoding='utf-8') as f:
                    self.confidence_calibration = defaultdict(list, json.load(f))

            logger.info(f"Loaded learned patterns from {self.storage_path}")

        except Exception as e:
            logger.warning(f"Failed to load learned patterns: {e}")

    def _learn_swedish_terms(self, field_name: str, quote: str, confidence: float) -> None:
        """
        Extract and learn Swedish terms from evidence quote.

        Args:
            field_name: Field being extracted
            quote: Evidence quote containing Swedish text
            confidence: Confidence of extraction
        """
        # Define canonical terms for common fields
        canonical_map = {
            "depreciation_method": "avskrivning",
            "useful_life_years": "nyttjandeperiod",
            "maintenance_plan": "underhåll",
            "tax_policy": "skatt",
        }

        canonical_term = canonical_map.get(field_name)
        if not canonical_term:
            return

        # Extract potential variants from quote
        words = quote.lower().split()
        for word in words:
            # Check if word is a variant of canonical term
            if canonical_term in word or word in canonical_term:
                # Learn this variant
                variant = TermVariant(
                    canonical_term=canonical_term,
                    variant=word,
                    document_count=1,
                    confidence_avg=confidence
                )

                # Update existing or add new
                existing = next(
                    (v for v in self.term_variants[canonical_term] if v.variant == word),
                    None
                )
                if existing:
                    existing.document_count += 1
                    existing.confidence_avg = (
                        existing.confidence_avg * (existing.document_count - 1) + confidence
                    ) / existing.document_count
                else:
                    self.term_variants[canonical_term].append(variant)

    def _create_extraction_pattern(
        self,
        field_name: str,
        value: Any,
        evidence: Dict[str, Any],
        confidence: float
    ) -> ExtractionPattern:
        """Create extraction pattern from successful extraction."""
        # Extract Swedish term from evidence
        swedish_term = ""
        if "quotes" in evidence and evidence["quotes"]:
            swedish_term = evidence["quotes"][0][:50]  # First 50 chars

        # Extract context keywords
        context_keywords = []
        if "quotes" in evidence:
            for quote in evidence["quotes"]:
                words = quote.lower().split()
                context_keywords.extend([w for w in words if len(w) > 4])

        return ExtractionPattern(
            field_name=field_name,
            swedish_term=swedish_term,
            context_keywords=context_keywords[:5],  # Top 5 keywords
            confidence_avg=confidence
        )

    def _update_extraction_pattern(self, pattern: ExtractionPattern, success: bool) -> None:
        """Update extraction pattern statistics."""
        # Find existing pattern
        existing = next(
            (
                p for p in self.extraction_patterns
                if p.field_name == pattern.field_name
                and p.swedish_term == pattern.swedish_term
            ),
            None
        )

        if existing:
            if success:
                existing.success_count += 1
            else:
                existing.failure_count += 1
            existing.last_seen = datetime.now()
        else:
            if success:
                pattern.success_count = 1
            else:
                pattern.failure_count = 1
            self.extraction_patterns.append(pattern)


# Global learning loop instance
_global_learning_loop: Optional[LearningLoop] = None


def get_learning_loop() -> LearningLoop:
    """Get global learning loop instance (singleton)."""
    global _global_learning_loop
    if _global_learning_loop is None:
        _global_learning_loop = LearningLoop()
    return _global_learning_loop
