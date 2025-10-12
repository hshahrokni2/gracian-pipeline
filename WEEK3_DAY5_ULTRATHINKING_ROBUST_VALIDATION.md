# Week 3 Day 5: Ultrathinking - Robust & Scalable Semantic Validation

## 🎯 The Real Problem (Not Just Year Suffixes)

### Current Symptom
- Coverage: 3.3% (6/172 fields matched)
- Extraction: 118 fields successfully extracted
- **Diagnosis**: Field name mismatch, NOT extraction failure

### Surface Issue
```
Ground Truth: "annual_fee_per_sqm_2021", "annual_fee_per_sqm_2020", ...
Extraction:   "annual_fee_per_sqm"
Result:       No match → appears "missing"
```

### Deeper Issues (The Real Challenge)

1. **Temporal Variations**
   - Year suffixes: `_2021`, `_2020`, `_2019`, `_2018`
   - Date ranges: `income_2021`, `expenses_2020_2021`
   - Periods: `q1_2021`, `fy_2021`

2. **Structural Variations**
   - Nested vs flat: `governance.chairman` vs `chairman`
   - Prefixes: `governance_chairman` vs `chairman`
   - Arrays: `board_members[0].name` vs `board_member_names`

3. **Semantic Equivalences**
   - Swedish/English: `ordförande` / `chairman`
   - Synonyms: `liquid_assets` / `cash_and_bank` / `cash_and_cash_equivalents`
   - Abbreviations: `brf_name` / `organization_name`

4. **Type Variations**
   - Single vs multiple years: `fee_2021` vs `fees: {2021: x, 2020: y}`
   - Aggregated vs detailed: `total_loans` vs `loans[].amount`

## 🚨 Why Quick Fixes Won't Scale

### Proposed Quick Fix
```python
# Strip year suffix
field_name = field_name.replace("_2021", "").replace("_2020", "")
```

**Problems**:
- ❌ Hardcoded year list (requires updates every year)
- ❌ Doesn't handle `income_2020_2021` (range)
- ❌ Doesn't handle `q1_2021` (periods)
- ❌ False positives: `loan_2021_refinanced` → `loan_refinanced` (wrong)

### Production Reality (26,342 PDFs)
- **Schema evolution**: 5-10 field changes/quarter
- **Vendor variations**: 200+ municipalities, 50+ accounting software
- **Format drift**: K1/K2/K3 standards, vintage reports (2015-2025)
- **Manual updates needed**: 4-8 hours/month to maintain synonym dict

**Conclusion**: Manual synonym lists and regex hacks DON'T SCALE.

---

## 💡 Robust Solution: Multi-Layer Semantic Matching

### Architecture Principles

1. **Separation of Concerns**
   - Normalization layer (structural)
   - Temporal abstraction layer (time-series)
   - Semantic matching layer (meaning)
   - Confidence scoring layer (uncertainty)

2. **Fail-Open Design**
   - Layer 1 fails → Try Layer 2
   - Layer 2 fails → Try Layer 3
   - All layers fail → Low confidence (not error)

3. **Self-Learning**
   - Track successful matches
   - Build synonym graph from usage
   - Update confidence scores based on validation

---

## 🏗️ Implementation: 4-Layer Validation System

### Layer 1: Structural Normalization (Fast, Deterministic)

**Purpose**: Handle structural variations without semantic understanding

```python
class StructuralNormalizer:
    """
    Normalizes field names to canonical form.
    Examples:
        "governance.chairman" → "chairman"
        "governance_chairman" → "chairman"
        "board_members[0].name" → "board_member_name"
    """

    def normalize(self, field_name: str) -> str:
        # 1. Remove common prefixes
        prefixes = ["governance_", "financial_", "metadata_", "property_"]
        for prefix in prefixes:
            if field_name.startswith(prefix):
                field_name = field_name[len(prefix):]

        # 2. Remove array indices
        field_name = re.sub(r'\[\d+\]', '', field_name)

        # 3. Convert nested paths to flat
        field_name = field_name.split('.')[-1]  # Take last segment

        # 4. Standardize separators
        field_name = field_name.replace('-', '_').replace(' ', '_')

        return field_name.lower().strip('_')
```

**Coverage Impact**: +10-15% (handles structural mismatches)

### Layer 2: Temporal Abstraction (Smart, Pattern-Based)

**Purpose**: Abstract away time-series variations

```python
class TemporalAbstractor:
    """
    Removes temporal qualifiers while preserving semantic meaning.
    Examples:
        "annual_fee_per_sqm_2021" → ("annual_fee_per_sqm", ["2021"])
        "income_2020_2021" → ("income", ["2020", "2021"])
        "q1_2021_revenue" → ("revenue", ["2021_q1"])
    """

    TEMPORAL_PATTERNS = [
        # Year suffixes
        (r'_(\d{4})$', 'year_suffix'),
        # Year prefixes
        (r'^(\d{4})_', 'year_prefix'),
        # Year ranges
        (r'_(\d{4})_(\d{4})', 'year_range'),
        # Quarters
        (r'_(q[1-4])_(\d{4})', 'quarter'),
        # Fiscal years
        (r'_(fy)_?(\d{4})', 'fiscal_year'),
    ]

    def abstract(self, field_name: str) -> Tuple[str, List[str], str]:
        """
        Returns: (base_name, temporal_qualifiers, pattern_type)
        """
        for pattern, pattern_type in self.TEMPORAL_PATTERNS:
            match = re.search(pattern, field_name, re.IGNORECASE)
            if match:
                # Extract temporal parts
                temporal_parts = list(match.groups())

                # Remove temporal part from field name
                base_name = re.sub(pattern, '', field_name).strip('_')

                return (base_name, temporal_parts, pattern_type)

        # No temporal qualifiers found
        return (field_name, [], 'none')
```

**Coverage Impact**: +15-20% (handles year suffixes and more)

### Layer 3: Semantic Matching (Powerful, Graph-Based)

**Purpose**: Match fields by meaning, not just text similarity

```python
class SemanticFieldMatcher:
    """
    Graph-based semantic matching using synonym network.
    Auto-learns from successful matches.
    """

    def __init__(self):
        # Core synonym graph (349 entries from current SYNONYM_DICT)
        self.synonym_graph = self._build_initial_graph()

        # Dynamic synonyms learned from validation
        self.learned_synonyms = {}

        # Confidence scores per edge
        self.edge_confidence = {}

    def find_semantic_match(
        self,
        canonical_field: str,
        available_fields: List[str],
        threshold: float = 0.5
    ) -> Tuple[Optional[str], float]:
        """
        Find best semantic match using graph traversal.

        Algorithm:
        1. Normalize both canonical and available fields
        2. Check direct match (confidence = 1.0)
        3. Check 1-hop synonyms (confidence = 0.9)
        4. Check 2-hop synonyms (confidence = 0.7)
        5. Use fuzzy string matching (confidence = 0.5-0.7)
        """
        # Normalize
        canonical_norm = self._normalize(canonical_field)

        # Direct match
        for field in available_fields:
            if self._normalize(field) == canonical_norm:
                return (field, 1.0)

        # 1-hop synonyms
        direct_synonyms = self.synonym_graph.get(canonical_norm, set())
        for field in available_fields:
            field_norm = self._normalize(field)
            if field_norm in direct_synonyms:
                confidence = self.edge_confidence.get(
                    (canonical_norm, field_norm),
                    0.9  # Default for manual synonyms
                )
                return (field, confidence)

        # 2-hop synonyms (transitive)
        for synonym in direct_synonyms:
            indirect_synonyms = self.synonym_graph.get(synonym, set())
            for field in available_fields:
                field_norm = self._normalize(field)
                if field_norm in indirect_synonyms:
                    return (field, 0.7)

        # Fuzzy matching (fallback)
        best_match, best_score = self._fuzzy_match(
            canonical_norm,
            [self._normalize(f) for f in available_fields]
        )

        if best_score >= threshold:
            # Find original field name
            original_field = available_fields[
                [self._normalize(f) for f in available_fields].index(best_match)
            ]
            return (original_field, best_score * 0.6)  # Penalty for fuzzy

        return (None, 0.0)

    def learn_synonym(self, field1: str, field2: str, confidence: float):
        """
        Add learned synonym to graph.
        Called when validation confirms a match.
        """
        norm1 = self._normalize(field1)
        norm2 = self._normalize(field2)

        # Add bidirectional edge
        if norm1 not in self.synonym_graph:
            self.synonym_graph[norm1] = set()
        if norm2 not in self.synonym_graph:
            self.synonym_graph[norm2] = set()

        self.synonym_graph[norm1].add(norm2)
        self.synonym_graph[norm2].add(norm1)

        # Store confidence
        self.edge_confidence[(norm1, norm2)] = confidence
        self.edge_confidence[(norm2, norm1)] = confidence

        # Persist to learned_synonyms.json
        self._save_learned_synonyms()
```

**Coverage Impact**: +20-25% (handles complex semantic variations)

### Layer 4: Value-Based Validation (Ultimate Fallback)

**Purpose**: Match by value when field names are completely different

```python
class ValueBasedMatcher:
    """
    Match fields by comparing actual values.
    Used when semantic matching fails.
    """

    TYPE_SIGNATURES = {
        'org_number': r'^\d{6}-\d{4}$',  # Swedish org format
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'percentage': lambda v: isinstance(v, (int, float)) and 0 <= v <= 100,
        'currency_sek': lambda v: isinstance(v, (int, float)) and v > 1000,
    }

    def find_value_match(
        self,
        canonical_field: str,
        canonical_value: Any,
        available_data: Dict[str, Any],
        threshold: float = 0.8
    ) -> Tuple[Optional[str], float]:
        """
        Find field by matching value characteristics.

        Strategy:
        1. Type signature matching (org number, dates, etc.)
        2. Exact value matching (for unique values)
        3. Range matching (for numeric values)
        """
        # Determine value type
        value_type = self._classify_value(canonical_value)

        # Find candidates with same type
        candidates = []
        for field_name, field_value in self._flatten_dict(available_data).items():
            if self._classify_value(field_value) == value_type:
                # Calculate similarity score
                similarity = self._value_similarity(canonical_value, field_value)
                if similarity >= threshold:
                    candidates.append((field_name, similarity))

        if not candidates:
            return (None, 0.0)

        # Return best match
        best_field, best_score = max(candidates, key=lambda x: x[1])
        return (best_field, best_score * 0.5)  # Lower confidence for value-based
```

**Coverage Impact**: +5-10% (handles extreme edge cases)

---

## 📊 Expected Performance

### Coverage Progression

| Layer | Additional Coverage | Cumulative | Confidence |
|-------|-------------------|------------|------------|
| **Baseline** (current) | - | 3.3% | 0.95 |
| **+ Layer 1** (structural) | +12% | 15.3% | 0.90 |
| **+ Layer 2** (temporal) | +18% | 33.3% | 0.85 |
| **+ Layer 3** (semantic) | +22% | 55.3% | 0.75 |
| **+ Layer 4** (value) | +8% | **63.3%** | 0.60 |

### Confidence Distribution

```
High Confidence (≥0.85):  35-40% of matches
Medium Confidence (0.65-0.84):  25-30% of matches
Low Confidence (0.50-0.64):  10-15% of matches
```

---

## 🚀 Implementation Plan

### Phase 1: Quick Win (2 hours) - TODAY

**Goal**: 3.3% → 30-35% coverage

**Implementation**:
1. Add `TemporalAbstractor` to `semantic_matcher.py` (45 min)
2. Integrate into `find_field()` method (30 min)
3. Expand SYNONYM_DICT with 25 critical entries (30 min)
4. Test and validate (15 min)

**Files Modified**:
- `gracian_pipeline/validation/semantic_matcher.py` (add TemporalAbstractor)
- Test with `test_confidence_validator.py`

### Phase 2: Robust Foundation (4 hours) - Week 4 Day 1

**Goal**: 30% → 55% coverage

**Implementation**:
1. Implement `SemanticFieldMatcher` with graph (2 hours)
2. Add `StructuralNormalizer` (1 hour)
3. Integrate layers 1-3 into validation pipeline (1 hour)

**Files Created**:
- `gracian_pipeline/validation/structural_normalizer.py`
- `gracian_pipeline/validation/semantic_field_matcher.py`
- `gracian_pipeline/validation/learned_synonyms.json` (dynamic)

### Phase 3: Self-Learning System (6 hours) - Week 4 Day 2-3

**Goal**: 55% → 65%+ coverage with auto-improvement

**Implementation**:
1. Implement `ValueBasedMatcher` (2 hours)
2. Add learning feedback loop (2 hours)
3. Build synonym graph persistence (1 hour)
4. Comprehensive testing on 42-PDF corpus (1 hour)

**Files Created**:
- `gracian_pipeline/validation/value_based_matcher.py`
- `gracian_pipeline/validation/learning_engine.py`

---

## 🎯 Immediate Action (Next 2 Hours)

### Step 1: Implement TemporalAbstractor (45 min)

```python
# In gracian_pipeline/validation/semantic_matcher.py
# Add after line 227 (end of SYNONYM_DICT)

import re
from typing import Tuple, List

class TemporalAbstractor:
    """
    Removes temporal qualifiers from field names.
    Handles year suffixes, ranges, quarters, fiscal years.
    """

    TEMPORAL_PATTERNS = [
        # Year suffix: field_2021
        (r'_(\d{4})$', 'year_suffix'),
        # Year prefix: 2021_field
        (r'^(\d{4})_', 'year_prefix'),
        # Year range: field_2020_2021
        (r'_(\d{4})_(\d{4})', 'year_range'),
        # Quarter: field_q1_2021
        (r'_(q[1-4])_?(\d{4})', 'quarter'),
        # Fiscal year: field_fy_2021 or field_fy2021
        (r'_(fy)_?(\d{4})', 'fiscal_year'),
    ]

    def abstract(self, field_name: str) -> Tuple[str, List[str], str]:
        """
        Remove temporal qualifiers and return base name.

        Returns:
            (base_name, temporal_parts, pattern_type)

        Examples:
            "annual_fee_2021" → ("annual_fee", ["2021"], "year_suffix")
            "income_2020_2021" → ("income", ["2020", "2021"], "year_range")
            "revenue_q1_2021" → ("revenue", ["q1", "2021"], "quarter")
        """
        for pattern, pattern_type in self.TEMPORAL_PATTERNS:
            match = re.search(pattern, field_name, re.IGNORECASE)
            if match:
                temporal_parts = list(match.groups())
                base_name = re.sub(pattern, '', field_name).strip('_')
                return (base_name, temporal_parts, pattern_type)

        return (field_name, [], 'none')
```

### Step 2: Integrate into SemanticMatcher (30 min)

```python
# In class SemanticMatcher, update __init__ (around line 229)

def __init__(self):
    self.synonyms = SYNONYM_DICT
    self.temporal_abstractor = TemporalAbstractor()  # NEW

# Update find_field method (around line 254)

def find_field(self, data: Dict, canonical_field_name: str) -> Tuple[Optional[Any], float]:
    """
    Find field in data dict using semantic matching with temporal abstraction.
    """
    # NEW: Abstract temporal qualifiers
    base_canonical, temporal_parts, pattern_type = \
        self.temporal_abstractor.abstract(canonical_field_name)

    # Try with base name (without temporal qualifiers)
    found_value, confidence = self._search_nested_dict(data, base_canonical)

    if found_value is not None:
        return (found_value, confidence)

    # Fallback: Try original name (with temporal qualifiers)
    return self._search_nested_dict(data, canonical_field_name)
```

### Step 3: Expand Critical Synonyms (30 min)

```python
# Add to SYNONYM_DICT (around line 44)

# Building/Note 8 variations
"acquisition_value": ["anskaffningsvarde", "opening_acquisition_value",
                      "closing_acquisition_value", "acquisition_cost"],
"accumulated_depreciation": ["ackumulerade_avskrivningar", "opening_depreciation",
                             "closing_depreciation", "total_depreciation"],
"book_value": ["planenligt_restvarde", "net_book_value", "carrying_amount",
               "restvarde", "net_value"],

# Cash flow variations
"liquid_assets": ["likvida_medel", "cash_and_bank", "cash_and_cash_equivalents",
                  "kassa_bank", "liquid_funds"],
"cash_change": ["change_in_liquid_assets", "forandra_likvida_medel",
                "cash_flow", "net_cash_flow"],

# Governance variations
"auditor": ["revisor", "primary_auditor", "auditor_name", "external_auditor"],
"audit_firm": ["revisionsbolag", "auditor_firm", "audit_company"],
"board_members": ["styrelseledamoter", "board", "styrelsens_ledamoter"],

# Financial statement variations
"revenue": ["intakter", "net_sales", "nettoomsattning", "total_revenue"],
"operating_costs": ["driftkostnader", "operating_expenses", "drift"],
"result": ["resultat", "net_result", "year_result", "arets_resultat"],

# Property variations
"apartments": ["lagenheter", "apartment_count", "total_apartments", "antal_lagenheter"],
"built_year": ["byggnad", "construction_year", "year_built", "byggar"],

# Fee variations
"annual_fee_per_sqm": ["arsavgift_per_kvm", "fee_per_sqm", "avgift_per_kvm",
                       "monthly_fee_annual", "arsavgift"],
```

### Step 4: Test (15 min)

```bash
# Run validation
python test_confidence_validator.py

# Expected output:
# Coverage: 30-35% (52-60 fields matched, up from 6)
# High confidence: 40-50 fields (up from 5)
```

---

## 📈 Success Metrics

### Immediate (Phase 1 - Today)
- ✅ Coverage: 3.3% → **30-35%**
- ✅ Implementation time: **2 hours**
- ✅ Code quality: No breaking changes, backward compatible

### Short-term (Phase 2 - Week 4)
- ✅ Coverage: 30% → **55%**
- ✅ Maintainability: Self-learning reduces manual synonym updates by 80%
- ✅ Scalability: Handles 26K PDFs without degradation

### Long-term (Phase 3 - Production)
- ✅ Coverage: 55% → **65%+**
- ✅ Auto-improvement: Synonym graph grows from validation feedback
- ✅ Production-ready: Handles schema evolution automatically

---

## 🔧 Files to Modify (Phase 1)

1. **`gracian_pipeline/validation/semantic_matcher.py`**
   - Line 228: Add `TemporalAbstractor` class
   - Line 229: Add instance to `__init__`
   - Line 254: Update `find_field()` to use temporal abstraction
   - Line 44: Expand `SYNONYM_DICT` with 25 entries

2. **Test with**:
   - `test_confidence_validator.py`
   - `ground_truth/brf_198532_comprehensive_ground_truth.json`
   - `validation_extraction_brf_198532.json`

---

**Status**: ✅ **READY TO IMPLEMENT**
**Time Budget**: 2 hours (Phase 1)
**Risk**: Low (additive changes, no rewrites)
**Expected Impact**: 10x improvement in coverage (3.3% → 30-35%)
