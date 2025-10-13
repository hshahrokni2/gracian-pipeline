# Ultrathinking: Day 3 Perfect Implementation Design

**Date**: October 13, 2025
**Goal**: Design production-ready tolerant 3-tier validation system
**Philosophy**: Clean, testable, extensible, well-documented

---

## 🎯 Design Principles

### **1. Separation of Concerns**
- **ValidationResult enum** → `schema_v7.py` (core schema types)
- **Validation utilities** → `schema_v7_validation.py` (reusable functions)
- **Field validators** → `schema_v7.py` (within model classes)
- **Tests** → `tests/test_schema_v7_validation.py` (comprehensive coverage)

### **2. Tolerant by Design**
Real-world BRF extraction has inherent uncertainty:
- OCR errors (scanned PDFs = 49.3% of corpus)
- Format variations (Swedish: "12 345,67" vs "12345.67")
- Rounding differences (12345.67 vs 12345.7)
- String variations ("Rolf Johansson" vs "Rolf  Johansson")

**Solution**: 3-tier validation (valid/warning/error) with configurable tolerances

### **3. Multi-Source Validation**
The `alternative_values` field from Day 1 enables:
- Compare values from multiple extractors (table vs text vs OCR)
- Consensus-based confidence (3 agree → high confidence)
- Conflict detection (3 disagree → needs manual review)

### **4. Quality Scoring**
Enable extraction pipeline to:
- Rank extractions by quality (0.0-1.0 score)
- Prioritize manual review (low quality → human check)
- Track improvement over time (compare runs)

---

## 🏗️ Architecture Design

### **Module 1: ValidationResult Enum** (`schema_v7.py`)

```python
class ValidationResult(str, Enum):
    """
    Validation result for tolerant 3-tier validation.

    - VALID: Field passes validation with high confidence
    - WARNING: Field has minor issues but is usable (e.g., within tolerance)
    - ERROR: Field fails validation (e.g., out of bounds, type mismatch)
    - UNKNOWN: Field not validated yet (default state)
    """
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"
```

**Why**: Simple, clear, extensible. String enum for JSON serialization.

---

### **Module 2: Validation Utilities** (`schema_v7_validation.py`)

#### **2.1 Tolerant Comparison Functions**

```python
def tolerant_float_compare(
    value1: float,
    value2: float,
    relative_tolerance: float = 0.05,  # ±5%
    absolute_tolerance: float = 0.01   # For values near zero
) -> tuple[bool, float]:
    """
    Compare floats with configurable tolerance.

    Returns:
        (matches: bool, difference: float)

    Logic:
    - If both near zero (< absolute_tolerance), compare absolutely
    - Otherwise, compare relatively (±5% default)

    Examples:
        12345.67 vs 12400.00 → (True, 0.44%)  # Within 5%
        12345.67 vs 13000.00 → (False, 5.30%) # Exceeds 5%
        0.001 vs 0.002 → (True, 0.001)        # Within absolute tolerance
    """
    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 0.0)
    if value1 is None or value2 is None:
        return (False, float('inf'))

    # Both zero or near-zero
    if abs(value1) < absolute_tolerance and abs(value2) < absolute_tolerance:
        diff = abs(value1 - value2)
        return (diff <= absolute_tolerance, diff)

    # One is zero, other is not
    if abs(value1) < absolute_tolerance or abs(value2) < absolute_tolerance:
        return (False, abs(value1 - value2))

    # Relative comparison
    diff_abs = abs(value1 - value2)
    diff_rel = diff_abs / max(abs(value1), abs(value2))
    return (diff_rel <= relative_tolerance, diff_rel)


def tolerant_string_compare(
    value1: str,
    value2: str,
    case_sensitive: bool = False,
    ignore_whitespace: bool = True,
    ignore_punctuation: bool = True
) -> tuple[bool, float]:
    """
    Compare strings with normalization.

    Returns:
        (matches: bool, similarity: float)  # 0.0-1.0

    Normalization:
    - Lowercase (if not case_sensitive)
    - Strip/normalize whitespace
    - Remove punctuation (if ignore_punctuation)

    Similarity metric: Levenshtein distance normalized

    Examples:
        "Rolf Johansson" vs "Rolf  Johansson" → (True, 1.0)
        "769606-2533" vs "769606 2533" → (True, 0.95)
        "Chairman" vs "Ordförande" → (False, 0.0)  # Different words
    """
    import string
    from difflib import SequenceMatcher

    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 1.0)
    if value1 is None or value2 is None:
        return (False, 0.0)

    # Normalize
    s1, s2 = value1, value2

    if not case_sensitive:
        s1, s2 = s1.lower(), s2.lower()

    if ignore_whitespace:
        s1 = ' '.join(s1.split())  # Normalize multiple spaces to single
        s2 = ' '.join(s2.split())

    if ignore_punctuation:
        translator = str.maketrans('', '', string.punctuation)
        s1 = s1.translate(translator)
        s2 = s2.translate(translator)

    # Exact match after normalization
    if s1 == s2:
        return (True, 1.0)

    # Fuzzy match using SequenceMatcher
    similarity = SequenceMatcher(None, s1, s2).ratio()
    return (similarity >= 0.90, similarity)  # 90% threshold for "match"


def tolerant_date_compare(
    value1: str,  # ISO format YYYY-MM-DD
    value2: str,
    tolerance_days: int = 0
) -> tuple[bool, int]:
    """
    Compare dates with optional day tolerance.

    Returns:
        (matches: bool, diff_days: int)

    Examples:
        "2024-01-15" vs "2024-01-15" → (True, 0)
        "2024-01-15" vs "2024-01-16" → (False, 1)
        "2024-01-15" vs "2024-01-16", tolerance=1 → (True, 1)
    """
    from datetime import datetime

    # Handle None cases
    if value1 is None and value2 is None:
        return (True, 0)
    if value1 is None or value2 is None:
        return (False, 999999)

    try:
        date1 = datetime.fromisoformat(value1)
        date2 = datetime.fromisoformat(value2)
        diff_days = abs((date1 - date2).days)
        return (diff_days <= tolerance_days, diff_days)
    except (ValueError, TypeError):
        return (False, 999999)


def tolerant_list_compare(
    list1: List[Any],
    list2: List[Any],
    ordered: bool = False,
    element_compare_fn: Callable = None
) -> tuple[bool, float]:
    """
    Compare lists with optional ordering and custom element comparison.

    Returns:
        (matches: bool, similarity: float)  # 0.0-1.0

    Examples:
        [1, 2, 3] vs [1, 2, 3] → (True, 1.0)
        [1, 2, 3] vs [3, 2, 1], ordered=False → (True, 1.0)
        [1, 2, 3] vs [3, 2, 1], ordered=True → (False, 0.0)
        [1, 2] vs [1, 2, 3] → (False, 0.67)  # 2/3 overlap
    """
    # Handle None cases
    if list1 is None and list2 is None:
        return (True, 1.0)
    if list1 is None or list2 is None:
        return (False, 0.0)

    if len(list1) == 0 and len(list2) == 0:
        return (True, 1.0)

    if ordered:
        # Ordered comparison - must match element by element
        if len(list1) != len(list2):
            return (False, 0.0)

        matches = sum(1 for a, b in zip(list1, list2) if a == b)
        similarity = matches / len(list1) if list1 else 0.0
        return (similarity == 1.0, similarity)
    else:
        # Unordered comparison - set-like
        set1, set2 = set(list1), set(list2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        similarity = intersection / union if union > 0 else 0.0
        return (similarity >= 0.90, similarity)  # 90% threshold
```

#### **2.2 Quality Scoring Functions**

```python
def calculate_field_coverage(
    data: BaseModel,
    expected_fields: List[str] = None
) -> float:
    """
    Calculate field coverage (0.0-1.0).

    Args:
        data: Pydantic model instance
        expected_fields: List of field names to check (None = all fields)

    Returns:
        Coverage ratio (populated fields / total fields)

    Example:
        Model has 10 fields, 7 populated → 0.70
    """
    if expected_fields is None:
        expected_fields = list(data.model_fields.keys())

    populated = sum(1 for field in expected_fields if getattr(data, field, None) is not None)
    return populated / len(expected_fields) if expected_fields else 0.0


def calculate_validation_score(
    validation_statuses: List[str]
) -> float:
    """
    Calculate validation score (0.0-1.0) from validation_status values.

    Scoring:
    - VALID: 1.0
    - WARNING: 0.5
    - ERROR: 0.0
    - UNKNOWN: 0.0

    Returns:
        Average validation score

    Example:
        [VALID, VALID, WARNING, ERROR] → (1.0 + 1.0 + 0.5 + 0.0) / 4 = 0.625
    """
    score_map = {
        ValidationResult.VALID: 1.0,
        ValidationResult.WARNING: 0.5,
        ValidationResult.ERROR: 0.0,
        ValidationResult.UNKNOWN: 0.0
    }

    if not validation_statuses:
        return 0.0

    scores = [score_map.get(status, 0.0) for status in validation_statuses]
    return sum(scores) / len(scores)


def calculate_extraction_quality(
    data: BaseModel,
    expected_fields: List[str] = None,
    field_weights: Dict[str, float] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive extraction quality metrics.

    Args:
        data: Pydantic model with ExtractionField fields
        expected_fields: Fields to evaluate (None = all)
        field_weights: Importance weights (None = equal weights)

    Returns:
        {
            'coverage': 0.70,        # 70% fields populated
            'validation': 0.85,      # 85% validation score
            'confidence': 0.92,      # 92% average confidence
            'evidence': 0.80,        # 80% have evidence_pages
            'overall': 0.82          # Weighted average
        }
    """
    if expected_fields is None:
        expected_fields = list(data.model_fields.keys())

    # Coverage score
    coverage = calculate_field_coverage(data, expected_fields)

    # Validation score
    validation_statuses = []
    confidence_scores = []
    evidence_counts = 0
    total_fields = 0

    for field_name in expected_fields:
        field_value = getattr(data, field_name, None)

        if field_value is not None:
            total_fields += 1

            # Check if field has ExtractionField structure
            if hasattr(field_value, 'validation_status'):
                validation_statuses.append(field_value.validation_status or ValidationResult.UNKNOWN)

            if hasattr(field_value, 'confidence'):
                confidence_scores.append(field_value.confidence)

            if hasattr(field_value, 'evidence_pages') and field_value.evidence_pages:
                evidence_counts += 1

    validation_score = calculate_validation_score(validation_statuses)
    confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    evidence_score = evidence_counts / total_fields if total_fields > 0 else 0.0

    # Overall score (weighted average)
    overall = (
        coverage * 0.30 +      # 30% weight on coverage
        validation_score * 0.30 +  # 30% weight on validation
        confidence_score * 0.25 +  # 25% weight on confidence
        evidence_score * 0.15      # 15% weight on evidence
    )

    return {
        'coverage': coverage,
        'validation': validation_score,
        'confidence': confidence_score,
        'evidence': evidence_score,
        'overall': overall
    }
```

---

### **Module 3: Field Validators** (in `schema_v7.py`)

```python
class YearlyFinancialData(BaseModel):
    # ... existing fields ...

    @field_validator('nettoomsättning_tkr', 'resultat_efter_finansiella_tkr')
    @classmethod
    def validate_monetary_fields(cls, v):
        """Validate monetary fields are non-negative (or None)."""
        if v is not None and v < 0:
            # Don't raise - set validation_status instead
            # This is tolerant validation
            pass  # Will be handled by validation_status field
        return v

    @field_validator(
        'soliditet_procent',
        'räntekänslighet_procent',
        'årsavgift_andel_intäkter_procent'
    )
    @classmethod
    def validate_percentage_fields(cls, v):
        """Validate percentage fields are 0-100 (or None)."""
        if v is not None:
            if v < 0 or v > 100:
                # Out of bounds - but tolerant validation
                pass  # Handled by validation_status
        return v

    @model_validator(mode='after')
    def validate_financial_ratios(self):
        """Cross-field validation for financial sanity checks."""
        # Example: If soliditet_procent is very low (<5%), flag as warning
        if self.soliditet_procent is not None and self.soliditet_procent < 5:
            # Very low equity ratio - concerning but not invalid
            # This would be captured in validation_status as WARNING
            pass

        # Example: If debt_per_kvm exists, it should be positive
        if self.skuld_per_kvm_total is not None and self.skuld_per_kvm_total < 0:
            # Negative debt doesn't make sense
            pass  # Flag as ERROR in validation_status

        return self
```

**Why Tolerant**: Validators don't raise exceptions. Instead, they set `validation_status` field to VALID/WARNING/ERROR. This allows extraction to continue even with questionable values.

---

## 📊 Implementation Order

### **Phase 1: Core Infrastructure** (30 min)
1. Add `ValidationResult` enum to `schema_v7.py`
2. Create `schema_v7_validation.py` with comparison functions
3. Add import in `schema_v7.py`

### **Phase 2: Field Validators** (20 min)
4. Add @field_validator for monetary fields
5. Add @field_validator for percentage fields
6. Add @model_validator for cross-field validation

### **Phase 3: Quality Scoring** (20 min)
7. Implement calculate_field_coverage()
8. Implement calculate_validation_score()
9. Implement calculate_extraction_quality()

### **Phase 4: Comprehensive Testing** (50 min)
10. Write 5 tests for comparison functions
11. Write 5 tests for field validators
12. Write 5 tests for quality scoring
13. Write 5 tests for edge cases

**Total**: ~2 hours

---

## ✅ Success Criteria

**Code Quality**:
- ✅ Clean separation of concerns (schema vs validation vs utilities)
- ✅ Comprehensive docstrings with examples
- ✅ Type hints throughout
- ✅ Production-ready error handling

**Test Coverage**:
- ✅ 20 tests minimum
- ✅ 100% pass rate
- ✅ Edge cases covered (None, zero, negative, boundary values)

**Integration**:
- ✅ Seamlessly integrates with Days 1-2
- ✅ No breaking changes
- ✅ Backward compatible

**Documentation**:
- ✅ Clear examples in docstrings
- ✅ Completion report (DAY3_COMPLETE_TOLERANT_VALIDATION.md)

---

## 🎯 Why This Design is Perfect

1. **Separation of Concerns**: Validation logic separate from schema definitions
2. **Reusable Functions**: Comparison functions can be used in extraction pipelines
3. **Tolerant by Design**: 3-tier validation (valid/warning/error) instead of pass/fail
4. **Multi-Source Ready**: Comparison functions enable alternative_values validation
5. **Quality Scoring**: Quantitative metrics for extraction quality
6. **Production Ready**: Error handling, type hints, comprehensive docs
7. **Extensible**: Easy to add more validators or comparison functions
8. **Well Tested**: 20 tests covering core functionality and edge cases

---

**Created**: October 13, 2025
**Implementation Time**: ~2 hours
**Next**: Begin Phase 1 (Core Infrastructure)

**🎯 Perfect design ready for implementation! 🚀**
