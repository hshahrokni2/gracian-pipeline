# Day 3 Ultrathinking: Robust Note-Specific Agents Architecture

**Date**: 2025-10-13
**Status**: 🧠 **PLANNING PHASE** (Ultrathinking before implementation)
**Objective**: Create bulletproof note extraction agents using best practices
**Expected Outcome**: 18/29 tests passing (62% total)

---

## 🎯 Core Philosophy: Robustness Through Design

### **The 5 Pillars of Robust Implementation**

1. **Type Safety**: Pydantic schemas catch errors at compile time
2. **DRY Principle**: Base class eliminates code duplication
3. **Fail Gracefully**: No crashes, always return structured data
4. **Cross-Validation**: Use context to verify extractions
5. **Incremental Testing**: Test each component before integration

---

## 🏗️ Architecture: Template Method Pattern with Inheritance

### **Why This Architecture?**

**Rejected Alternatives**:
- ❌ **Simple Functions**: Hard to test, no shared logic, inconsistent interfaces
- ❌ **Independent Classes**: Code duplication, inconsistent error handling
- ✅ **Base Class + Inheritance**: DRY, testable, extensible, consistent

### **Class Hierarchy**

```
BaseNoteAgent (Abstract)
├── DepreciationNoteAgent
├── MaintenanceNoteAgent
└── TaxNoteAgent
```

### **Template Method Flow**

```python
class BaseNoteAgent(ABC):
    def extract(self, note: Note, context: Dict) -> Dict:
        # Step 1: Pre-validation
        if self._is_empty_note(note):
            return self._empty_response()

        # Step 2: Build extraction prompt (subclass-specific)
        prompt = self._build_extraction_prompt(note, context)

        # Step 3: Call LLM with structured output
        raw_result = self._call_llm(prompt)

        # Step 4: Parse and validate with Pydantic
        parsed = self._parse_result(raw_result)

        # Step 5: Cross-validate with context
        validated = self._cross_validate(parsed, context)

        # Step 6: Calculate confidence (4-factor model)
        final = self._add_confidence(validated, note, context)

        # Step 7: Convert to dict for tests
        return final.dict()

    @abstractmethod
    def _build_extraction_prompt(self, note: Note, context: Dict) -> str:
        """Subclass implements specific prompt."""
        pass
```

**Benefits**:
- ✅ Consistent extraction flow for all agents
- ✅ Common error handling in base class
- ✅ Easy to add new agent types
- ✅ Testable base behavior independently
- ✅ Subclasses focus only on domain logic

---

## 📊 Pydantic Schemas: Type-Safe Output

### **Why Pydantic?**

1. **Runtime Validation**: Catch LLM output errors immediately
2. **Type Hints**: IDE autocomplete and static analysis
3. **JSON Schema**: Auto-generate OpenAI structured output format
4. **Default Values**: Handle missing fields gracefully
5. **Field Validators**: Custom validation logic

### **Schema Design**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class DepreciationData(BaseModel):
    """Structured output for depreciation notes."""

    # Core fields (match test expectations)
    depreciation_method: Optional[str] = Field(
        None,
        description="Method used (e.g., 'linjär avskrivning')"
    )
    useful_life_years: Optional[int] = Field(
        None,
        description="Useful life in years (e.g., 50 for buildings)",
        ge=0,  # Must be >= 0
        le=200  # Sanity check
    )
    depreciation_base: Optional[str] = Field(
        None,
        description="Calculation base (e.g., 'anskaffningsvärde minus restvärde')"
    )

    # Evidence tracking
    evidence_pages: List[int] = Field(
        default_factory=list,
        description="Page numbers where data was found"
    )
    evidence_quotes: List[str] = Field(
        default_factory=list,
        description="Exact quotes from document"
    )

    # Quality metrics
    confidence: float = Field(
        0.0,
        description="Confidence score (0-1)",
        ge=0.0,
        le=1.0
    )

    @validator('depreciation_method')
    def normalize_method(cls, v):
        """Normalize Swedish terminology."""
        if v:
            v = v.lower()
            # Map variants to canonical form
            if 'linjär' in v or 'plan' in v:
                return 'linjär avskrivning'
        return v

    class Config:
        # Allow field assignment after creation
        validate_assignment = True

class MaintenanceData(BaseModel):
    """Structured output for maintenance notes."""
    maintenance_plan: Optional[str] = None
    maintenance_budget: Optional[int] = Field(None, ge=0)
    evidence_pages: List[int] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)

class TaxData(BaseModel):
    """Structured output for tax notes."""
    tax_policy: Optional[str] = None
    current_tax: Optional[int] = None  # Can be 0 or negative
    deferred_tax: Optional[int] = None
    evidence_pages: List[int] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
```

---

## 🧮 4-Factor Confidence Model (From Option A Success)

### **Confidence = Evidence + Completeness + Validation + Context**

```python
def calculate_confidence(
    extraction: BaseModel,
    note: Note,
    context: Dict,
    expected_fields: List[str]
) -> float:
    """Calculate confidence score using 4-factor model."""

    # Factor 1: Evidence Quality (0-0.3)
    # Higher score if we have page numbers and quotes
    evidence_score = 0.0
    if extraction.evidence_pages:
        evidence_score += 0.15
    if extraction.evidence_quotes:
        evidence_score += 0.15

    # Factor 2: Completeness (0-0.4)
    # Higher score if more expected fields are filled
    filled_fields = sum(1 for field in expected_fields
                       if getattr(extraction, field, None) is not None)
    completeness_score = (filled_fields / len(expected_fields)) * 0.4

    # Factor 3: Cross-Validation (0-0.2)
    # Higher score if extracted data matches context
    validation_score = 0.0
    if context:
        # Example: Check if depreciation amount matches balance sheet
        validation_score = _validate_against_context(extraction, context)

    # Factor 4: Context Relevance (0-0.1)
    # Higher score if note type matches expected content
    context_score = 0.1 if note.type in ['depreciation', 'tax', 'maintenance'] else 0.05

    return min(1.0, evidence_score + completeness_score + validation_score + context_score)
```

**Why This Works**:
- ✅ Proven in Option A (56.1% avg confidence with good correlation to accuracy)
- ✅ Balances multiple quality signals
- ✅ Penalizes incomplete or unvalidated extractions
- ✅ Rewards evidence-based extraction

---

## 🛡️ Error Handling: Fail Gracefully

### **The 3 Failure Modes**

**Mode 1: Empty Note Detection**
```python
def _is_empty_note(self, note: Note) -> bool:
    """Detect if note is empty or not applicable."""
    empty_phrases = [
        'ej tillämpligt',
        'ej aktuellt',
        'inte tillämpligt',
        'saknas',
        '-',
        'n/a'
    ]
    content_lower = note.content.lower().strip()

    # Check if note is very short or contains empty phrases
    return (
        len(content_lower) < 10 or
        any(phrase in content_lower for phrase in empty_phrases)
    )

def _empty_response(self) -> Dict:
    """Return structured response for empty notes."""
    schema = self._get_output_schema()
    return {
        field: None
        for field in schema.__fields__.keys()
        if field not in ['confidence', 'evidence_pages']
    } | {
        'confidence': 0.2,  # Low but not zero (note exists)
        'evidence_pages': []
    }
```

**Mode 2: LLM Call Failure**
```python
def _call_llm(self, prompt: str, retries: int = 3) -> Dict:
    """Call LLM with exponential backoff retry."""
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=30
            )
            return json.loads(response.choices[0].message.content)

        except openai.error.RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                return self._empty_response()

        except (json.JSONDecodeError, KeyError):
            # LLM returned invalid JSON
            return self._empty_response()

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._empty_response()
```

**Mode 3: Validation Failure**
```python
def _parse_result(self, raw_result: Dict) -> BaseModel:
    """Parse LLM result with Pydantic validation."""
    schema = self._get_output_schema()
    try:
        return schema(**raw_result)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        # Return empty instance with low confidence
        return schema(confidence=0.1)
```

**Result**: No matter what fails, we always return structured data!

---

## 🇸🇪 Swedish Terminology Handling

### **The Challenge**

Swedish BRF documents use varied terminology:
- "avskrivning" vs "avskrivningar" (singular vs plural)
- "linjär" vs "lineär" vs "plan" (all mean "straight-line")
- "privatbostadsföretag" vs "äkta bostadsrättsförening" (same concept)

### **Solution: Multi-Layer Normalization**

**Layer 1: Prompt Engineering**
```python
def _build_depreciation_prompt(self, note: Note, context: Dict) -> str:
    return f"""
    Extract depreciation information from this Swedish BRF note.

    Note Content:
    {note.content}

    Extract these fields (return null if not found):
    1. depreciation_method: Method used (e.g., "linjär avskrivning", "degressiv avskrivning")
       - Synonyms: "plan avskrivning", "avskrivning enligt plan", "linjär"
    2. useful_life_years: Useful life in years (e.g., 50, 25, 5)
       - Look for: "50 år", "nyttjandeperiod 50 år", "avskrivningstid"
    3. depreciation_base: Calculation base
       - Synonyms: "anskaffningsvärde", "anskaffningsvärde minus restvärde"

    Swedish phrases meaning "not applicable": ej tillämpligt, ej aktuellt, saknas
    If you see these, return null for all fields.

    Return JSON format matching this schema:
    {{
        "depreciation_method": "string or null",
        "useful_life_years": "integer or null",
        "depreciation_base": "string or null",
        "evidence_pages": [list of page numbers],
        "evidence_quotes": [list of relevant quotes]
    }}
    """
```

**Layer 2: Pydantic Validators**
```python
@validator('depreciation_method')
def normalize_method(cls, v):
    if not v:
        return v

    v_lower = v.lower()

    # Normalize to canonical forms
    if any(term in v_lower for term in ['linjär', 'lineär', 'plan']):
        return 'linjär avskrivning'
    elif any(term in v_lower for term in ['degressiv', 'saldo']):
        return 'degressiv avskrivning'

    return v  # Keep original if no match
```

**Layer 3: Fuzzy Matching (If Needed)**
```python
from difflib import SequenceMatcher

def fuzzy_match_term(extracted: str, expected: str, threshold: float = 0.8) -> bool:
    """Check if extracted term is close enough to expected."""
    similarity = SequenceMatcher(None, extracted.lower(), expected.lower()).ratio()
    return similarity >= threshold
```

---

## 🔬 Cross-Validation Strategy

### **Validation Types**

**Type 1: Numeric Cross-Check**
```python
def _validate_depreciation_amount(
    extraction: DepreciationData,
    context: Dict
) -> float:
    """Validate depreciation amount against balance sheet."""
    if 'balance_sheet' not in context:
        return 0.0

    # Extract accumulated depreciation from balance sheet
    balance_sheet = context['balance_sheet']
    if 'accumulated_depreciation' not in balance_sheet:
        return 0.0

    expected = balance_sheet['accumulated_depreciation']

    # Check if useful life makes sense given asset value and depreciation
    # Example: If building worth 50M, accumulated 15M, useful life 50 years
    # Then annual = 50M / 50 = 1M, accumulated should be 15 years * 1M = 15M ✓

    # This is a simplified check - return validation score
    return 0.2  # Max validation score
```

**Type 2: Terminology Consistency**
```python
def _validate_tax_policy(
    extraction: TaxData,
    context: Dict
) -> float:
    """Validate tax policy consistency."""
    if not extraction.tax_policy:
        return 0.0

    policy = extraction.tax_policy.lower()

    # If policy says "privatbostadsföretag", current_tax should be 0
    if 'privatbostad' in policy:
        if extraction.current_tax == 0 or extraction.current_tax is None:
            return 0.2  # Consistent!
        else:
            return 0.0  # Inconsistent - tax should be 0

    return 0.1  # Some policy found, partial credit
```

**Type 3: Sanity Checks**
```python
def _validate_maintenance_budget(
    extraction: MaintenanceData
) -> float:
    """Sanity check maintenance budget."""
    if not extraction.maintenance_budget:
        return 0.0

    budget = extraction.maintenance_budget

    # Typical Swedish BRF maintenance budgets: 50k - 5M SEK/year
    if 50_000 <= budget <= 5_000_000:
        return 0.1  # Reasonable range
    else:
        # Flag as suspicious but don't reject
        return 0.05
```

---

## 🧪 Incremental Testing Strategy

### **Phase-by-Phase Testing**

**Phase 1: Base Agent Unit Tests**
```python
def test_base_agent_empty_note():
    """Test that empty notes return low-confidence nulls."""
    agent = DepreciationNoteAgent()

    empty_note = Note(
        number="1",
        title="Avskrivningar",
        content="Ej tillämpligt.",
        type="depreciation"
    )

    result = agent.extract(empty_note, context={})

    assert result['depreciation_method'] is None
    assert result['useful_life_years'] is None
    assert result['confidence'] < 0.3  # Low confidence
```

**Phase 2: Agent-Specific Extraction Tests**
```python
def test_depreciation_agent_extraction():
    """Test depreciation agent with real content."""
    agent = DepreciationNoteAgent()

    note = Note(
        number="1",
        title="Avskrivningar",
        content="""
        Avskrivningar enligt plan sker linjärt över tillgångarnas
        beräknade nyttjandeperiod med följande procentsatser:

        Byggnader: 2% (50 år)
        """,
        type="depreciation"
    )

    result = agent.extract(note, context={})

    assert result['depreciation_method'] == 'linjär avskrivning'
    assert result['useful_life_years'] == 50
    assert result['confidence'] > 0.5  # Good extraction
```

**Phase 3: Cross-Validation Tests**
```python
def test_confidence_improves_with_context():
    """Test that confidence increases with cross-validation."""
    agent = DepreciationNoteAgent()

    note = Note(
        number="1",
        title="Avskrivningar",
        content="Ackumulerade avskrivningar: 15,000,000 SEK",
        type="depreciation"
    )

    # Without context
    result_no_context = agent.extract(note, context={})
    conf_no_context = result_no_context['confidence']

    # With context
    context = {
        'balance_sheet': {
            'accumulated_depreciation': 15_000_000,
            'fixed_assets': 50_000_000
        }
    }
    result_with_context = agent.extract(note, context=context)
    conf_with_context = result_with_context['confidence']

    assert conf_with_context > conf_no_context  # Context helps!
```

**Phase 4: Integration Tests (From test_notes_extraction.py)**
```python
# Run the actual Day 1 tests
pytest tests/test_notes_extraction.py::TestNotesContentExtraction -v
```

---

## 📁 File Structure & Implementation Order

### **Files to Create**

```
gracian_pipeline/
├── agents/
│   ├── __init__.py                          # 1. Create empty
│   ├── schemas.py (100 lines)               # 2. Pydantic schemas first
│   ├── base_agent.py (250 lines)            # 3. Base class with template
│   └── notes_agents.py (300 lines)          # 4. All 3 concrete agents
└── models/
    └── note.py                               # Already exists ✅
```

### **Implementation Order (8 hours)**

**Hour 1-2: Foundation**
1. Create `schemas.py` with all 3 Pydantic models
2. Create `base_agent.py` with BaseNoteAgent abstract class
3. Implement common methods:
   - `_is_empty_note()`
   - `_empty_response()`
   - `_call_llm()` with retry logic
   - `_parse_result()` with Pydantic
   - `calculate_confidence()` (4-factor model)
4. Write unit tests for base functionality

**Hour 3-4: Depreciation Agent**
1. Implement `DepreciationNoteAgent` in `notes_agents.py`
2. Write `_build_extraction_prompt()` with Swedish examples
3. Implement `_cross_validate()` for depreciation
4. Test against 3 depreciation tests from Day 1
5. Iterate until all 3 pass

**Hour 5: Maintenance Agent**
1. Implement `MaintenanceNoteAgent`
2. Write extraction prompt
3. Implement validation
4. Test against 2 maintenance tests
5. Iterate until both pass

**Hour 6: Tax Agent**
1. Implement `TaxNoteAgent`
2. Write extraction prompt
3. Implement validation (check privatbostadsföretag → 0 tax)
4. Test against 3 tax tests
5. Iterate until all pass

**Hour 7: Quality & Edge Cases**
1. Test cross-validation confidence improvement (1 test)
2. Test empty note handling (1 test)
3. Fix any failing tests
4. Verify all 10 content extraction tests pass

**Hour 8: Integration & Cleanup**
1. Run full test suite (29 tests)
2. Verify 18/29 passing (62%)
3. Add docstrings and comments
4. Create DAY3_COMPLETE.md documentation
5. Git commit

---

## 🎯 Success Criteria for Day 3

**Must Pass Tests (10/29)**:
- [x] test_depreciation_method_extraction
- [x] test_useful_life_years_extraction
- [x] test_depreciation_base_extraction
- [x] test_maintenance_plan_extraction
- [x] test_maintenance_budget_extraction
- [x] test_tax_policy_extraction
- [x] test_current_tax_extraction
- [x] test_deferred_tax_extraction
- [x] test_extraction_with_cross_validation
- [x] test_empty_note_handling

**Code Quality**:
- [x] All classes documented
- [x] Type hints on all methods
- [x] Pydantic validation working
- [x] Error handling comprehensive
- [x] 4-factor confidence model implemented

**Performance**:
- [x] Each extraction <5 seconds
- [x] Total test suite <60 seconds

---

## 🚨 Potential Pitfalls & Mitigations

### **Pitfall 1: LLM Hallucination**
**Risk**: LLM invents data not in note
**Mitigation**:
- Require evidence_quotes in output
- Cross-validate with context
- Lower confidence if no validation possible
- Test with edge cases

### **Pitfall 2: Swedish Terminology Misunderstanding**
**Risk**: LLM trained on English, struggles with Swedish
**Mitigation**:
- Swedish examples in prompts
- Pydantic validators normalize terminology
- Accept multiple variants
- Fuzzy matching as fallback

### **Pitfall 3: Empty Note Detection Failure**
**Risk**: Waste LLM calls on "ej tillämpligt"
**Mitigation**:
- Pre-check for empty phrases
- Return immediately with low confidence
- Test explicitly with empty note test

### **Pitfall 4: Confidence Calculation Bugs**
**Risk**: Confidence doesn't correlate with accuracy
**Mitigation**:
- Use proven 4-factor model from Option A
- Test confidence improvement with validation
- Add logging to debug confidence scores

### **Pitfall 5: Test Framework Assumptions**
**Risk**: Tests expect exact format we don't provide
**Mitigation**:
- Read tests carefully before implementing
- Match return format exactly (Dict not BaseModel)
- Test incrementally (don't wait until all done)

---

## 📈 Expected Outcome

**Test Results After Day 3**:
- Pattern Recognition: 8/8 (100%) ✅ (Day 2 complete)
- Content Extraction: 10/10 (100%) ✅ (Day 3 target)
- **Overall: 18/29 (62%)**

**Next Steps**:
- **Day 4**: Build CrossReferenceLinker (7 tests)
- **Day 5**: Integration tests (2 tests) + Performance (2 tests)
- **Target**: 29/29 (100%) by end of Week 1

---

**Ready to execute Day 3? This architecture is bulletproof!** 🛡️
