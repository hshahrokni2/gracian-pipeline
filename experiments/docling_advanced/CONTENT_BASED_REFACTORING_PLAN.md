# Content-Based Architecture Refactoring Plan

**Date**: 2025-10-12
**Status**: 🔴 CRITICAL - Current architecture has fundamental design flaw
**Priority**: P0 - Blocks production deployment

---

## 🚨 The Critical Design Flaw

### Current Anti-Pattern (WRONG)
```python
# ❌ Embedding arbitrary note numbers into agent names
Note4UtilitiesAgent
Note8BuildingsAgent
Note11LiabilitiesAgent

# ❌ Routing by note numbers
if "Not 4" in heading:
    return "Note4UtilitiesAgent"
```

### The Reality
**Note numbers are ARBITRARY and vary across BRF documents:**
- **BRF A**: Utilities = "Not 3", Buildings = "Not 7", Liabilities = "Not 10"
- **BRF B**: Utilities = "Not 5", Buildings = "Not 9", Liabilities = "Not 12"
- **BRF C**: Utilities = "Not 4", Buildings = "Not 8", Liabilities = "Not 11"

**The constant**: CONTENT (Driftkostnader, Byggnader, Skulder)
**The variable**: NOTE NUMBERS (completely arbitrary!)

### User Feedback
> "the number next to not is arbitrary, the content is not. So never rely on notnumbers dear."

---

## ✅ The Correct Architecture

### Content-Based Agent Names
```python
# ✅ Named by CONTENT, not note numbers
OperatingCostsAgent      # Extracts: Driftkostnader (utilities, maintenance)
PropertyAgent            # Extracts: Byggnader, area, apartments
LiabilitiesAgent         # Extracts: Kortfristiga skulder
```

### Content-Based Routing
```python
# ✅ Route by Swedish content keywords
AGENT_KEYWORDS = {
    "OperatingCostsAgent": ["Driftkostnader", "El", "Värme", "Vatten"],
    "PropertyAgent": ["Byggnader och mark", "Antal lägenheter", "Totalarea"],
    "LiabilitiesAgent": ["Leverantörsskulder", "Övriga kortfristiga skulder"]
}
```

---

## 🎯 The 10 Content-Based Specialists

Based on Swedish BRF financial structure and Pydantic schema:

| # | Agent Name | Extracts | Primary Keywords |
|---|------------|----------|------------------|
| 1 | **MetadataAgent** | org_number, brf_name, financial_year | Organisationsnummer, Räkenskapsår |
| 2 | **GovernanceAgent** | chairman, board_members, auditor | Styrelse, Ordförande, Revisorer |
| 3 | **PropertyAgent** | buildings[], apartments_count, total_area | Byggnader och mark, Antal lägenheter |
| 4 | **LoansAgent** | loans[] (all 4 with details) | Långfristiga skulder, Lån, Räntesats |
| 5 | **AssetsAgent** | cash, receivables, fixed_assets | Kassa och bank, Likvida medel |
| 6 | **LiabilitiesAgent** | accounts_payable, short_term | Leverantörsskulder, Kortfristiga skulder |
| 7 | **EquityAgent** | total_equity, reserves, maintenance_fund | Eget kapital, Reservfond, Underhållsfond |
| 8 | **RevenueAgent** | monthly_fees, parking, other_income | Årsavgifter, Månadsavgift, Hyresintäkter |
| 9 | **OperatingCostsAgent** | utilities, maintenance, taxes | Driftkostnader, El, Värme, Vatten |
| 10 | **FinancialCostsAgent** | interest_expenses, interest_income | Räntekostnader, Ränteintäkter |

---

## 🏗️ Refactoring Plan (7 Phases)

### Phase 1: Create New Infrastructure ✅ COMPLETE
**Status**: ✅ Done (2025-10-12)

**Deliverables**:
- ✅ `config/content_based_routing.yaml` - Content keywords for all 10 agents
- ✅ `code/content_based_router.py` - 3-layer routing (keywords → fuzzy → LLM)
- ✅ `CONTENT_BASED_REFACTORING_PLAN.md` - This document

**Testing**:
```bash
# Test content-based router
python code/content_based_router.py

# Expected output:
# ✅ Routed to: OperatingCostsAgent (confidence: 0.90)
# ✅ Routed to: PropertyAgent (confidence: 0.95)
```

---

### Phase 2: Rename Agent Classes
**Status**: 🔴 TODO
**Estimated Time**: 2 hours
**Files to Change**: All agent files in `code/`

**Before**:
```python
# code/note4_utilities_agent.py
class Note4UtilitiesAgent:
    schema = Note4UtilitiesSchema

    def extract(self, pages, docling_result):
        # Extract utilities from "Not 4"
        ...
```

**After**:
```python
# code/operating_costs_agent.py
class OperatingCostsAgent:
    """
    Extracts operating costs breakdown (driftkostnader).

    Target Fields:
        - electricity (El)
        - heating (Värme)
        - water_sewage (Vatten och avlopp)
        - maintenance_costs (Underhåll)
        - property_tax (Fastighetsskatt)
        - insurance_costs (Försäkringar)
        - administration_costs (Administration)

    Content Keywords:
        - Primary: "Driftkostnader", "El", "Värme", "Vatten"
        - Secondary: "Fastighetskostnader", "Underhåll"

    Note: Do NOT rely on note numbers (e.g., "Not 4").
          Note numbers vary across BRF documents.
          Route by CONTENT, not structure.
    """
    schema = OperatingCostsSchema
    content_keywords = ["Driftkostnader", "El", "Värme", "Vatten och avlopp"]

    def extract(self, pages, docling_result):
        # Extract utilities from section with content keywords
        # (regardless of note number!)
        ...
```

**Rename Map**:
```python
AGENT_RENAME_MAP = {
    # Old (note-based) → New (content-based)
    "Note4UtilitiesAgent": "OperatingCostsAgent",
    "Note8BuildingsAgent": "PropertyAgent",
    "Note11LiabilitiesAgent": "LiabilitiesAgent",
    "Note5LoansAgent": "LoansAgent",
    "Note2GovernanceAgent": "GovernanceAgent",
    # ... complete for all agents
}
```

**Files to Rename**:
```bash
# Before
code/note4_utilities_agent.py
code/note8_buildings_agent.py
code/note11_liabilities_agent.py

# After
code/operating_costs_agent.py
code/property_agent.py
code/liabilities_agent.py
```

**Testing**:
```python
# Verify all agent classes renamed
from code.operating_costs_agent import OperatingCostsAgent
from code.property_agent import PropertyAgent

assert hasattr(OperatingCostsAgent, 'content_keywords')
assert "Driftkostnader" in OperatingCostsAgent.content_keywords
```

---

### Phase 3: Update Pydantic Schemas
**Status**: 🔴 TODO
**Estimated Time**: 1 hour
**Files to Change**: All schema definitions

**Before**:
```python
# schemas.py
class Note4UtilitiesSchema(BaseModel):
    electricity: Optional[float] = Field(None, description="El (SEK)")
    heating: Optional[float] = Field(None, description="Värme (SEK)")
    # ...
```

**After**:
```python
# schemas.py
class OperatingCostsSchema(BaseModel):
    """
    Operating costs breakdown (Driftkostnader).

    Typically found in:
        - Income statement section
        - Note with heading containing "Driftkostnader" or "Fastighetskostnader"
        - May be labeled "Not X" where X varies by document

    Do NOT assume specific note number!
    """
    electricity: Optional[float] = Field(
        None,
        description="El/Elektricitet (SEK)",
        json_schema_extra={"swedish_terms": ["El", "Elektricitet", "Elenergi"]}
    )
    heating: Optional[float] = Field(
        None,
        description="Värme/Fjärrvärme (SEK)",
        json_schema_extra={"swedish_terms": ["Värme", "Fjärrvärme", "Uppvärmning"]}
    )
    water_sewage: Optional[float] = Field(
        None,
        description="Vatten och avlopp (SEK)",
        json_schema_extra={"swedish_terms": ["Vatten och avlopp", "Vatten", "VA"]}
    )
    # ... rest of fields
```

**Schema Rename Map**:
```python
SCHEMA_RENAME_MAP = {
    "Note4UtilitiesSchema": "OperatingCostsSchema",
    "Note8BuildingsSchema": "PropertySchema",
    "Note11LiabilitiesSchema": "LiabilitiesSchema",
    # ... complete for all schemas
}
```

**Add Swedish Term Metadata**:
```python
# For each field, add json_schema_extra with Swedish terms
# This helps with extraction and validation
{
    "swedish_terms": ["El", "Elektricitet", "Elenergi"],
    "typical_context": "Driftkostnader note",
    "note_number_varies": True  # Important flag!
}
```

---

### Phase 4: Rewrite Agent Prompts
**Status**: 🔴 TODO
**Estimated Time**: 3 hours
**Impact**: High - This affects extraction quality

**Before** (WRONG - mentions note numbers):
```python
UTILITIES_PROMPT = """
Extract utility costs from Not 4 (Driftkostnader).

Look for:
- "Not 4" heading in the document
- Table under "Not 4" section
- Costs for El, Värme, Vatten

Return JSON with electricity, heating, water_sewage fields.
"""
```

**After** (CORRECT - content-focused):
```python
OPERATING_COSTS_PROMPT = """
Extract operating costs breakdown (driftkostnader) from the provided pages.

TARGET CONTENT (identify by these keywords):
- Section heading containing: "Driftkostnader" OR "Fastighetskostnader"
- May also be labeled as "Not X" where X is an arbitrary number that varies by document

⚠️ IMPORTANT: Do NOT rely on specific note numbers (e.g., "Not 4").
   Note numbers vary across BRF documents. Focus on CONTENT, not structure.

EXTRACT THESE FIELDS:

1. **Electricity (El/Elektricitet)**:
   - Swedish terms: "El", "Elektricitet", "Elenergi"
   - Return amount in SEK (numeric value only)

2. **Heating (Värme)**:
   - Swedish terms: "Värme", "Fjärrvärme", "Uppvärmning"
   - Return amount in SEK

3. **Water & Sewage (Vatten och avlopp)**:
   - Swedish terms: "Vatten och avlopp", "Vatten", "VA"
   - Return amount in SEK

4. **Maintenance (Underhåll)**:
   - Swedish terms: "Reparation och underhåll", "Löpande underhåll"
   - Return amount in SEK

5. **Property Tax (Fastighetsskatt)**:
   - Return amount in SEK

6. **Insurance (Försäkringar)**:
   - Swedish terms: "Försäkringar", "Fastighetsförsäkring"
   - Return amount in SEK

7. **Administration**:
   - Swedish terms: "Administration", "Förvaltningskostnader"
   - Return amount in SEK

EXTRACTION STRATEGY:
1. Scan all provided pages for section with content keywords above
2. Look for table or list structure with cost line items
3. Match Swedish terms to fields (use synonyms)
4. Extract numeric values (ignore "SEK", "kr", spaces, commas)

EVIDENCE REQUIREMENTS:
- Cite page number where each value was found
- Include surrounding context (table row or line item)

Return JSON:
{
    "electricity": 450000,
    "electricity_evidence": {"page": 15, "text": "El 450 000 SEK"},
    "heating": 890000,
    "heating_evidence": {"page": 15, "text": "Värme 890 000 SEK"},
    ...
}
"""
```

**Key Changes in Prompts**:
1. ✅ Remove ALL mentions of specific note numbers
2. ✅ Add warning about note number variability
3. ✅ Focus on Swedish content keywords
4. ✅ Provide multiple synonym terms for each field
5. ✅ Emphasize content-based identification
6. ✅ Add extraction strategy section
7. ✅ Require evidence with page numbers

**Prompt Template Structure**:
```python
AGENT_PROMPT_TEMPLATE = """
Extract {target_content} from the provided pages.

TARGET CONTENT (identify by these keywords):
{content_keywords}

⚠️ IMPORTANT: Do NOT rely on specific note numbers.
   Focus on CONTENT, not structure.

EXTRACT THESE FIELDS:
{field_descriptions_with_swedish_terms}

EXTRACTION STRATEGY:
{step_by_step_strategy}

EVIDENCE REQUIREMENTS:
{evidence_format}

Return JSON:
{output_schema}
"""
```

**Testing**:
```python
# Test prompt with same content, different note numbers
test_cases = [
    {"heading": "Not 4 - Driftkostnader", "should_extract": True},
    {"heading": "Not 7 - Driftkostnader", "should_extract": True},
    {"heading": "Driftkostnader", "should_extract": True},
    {"heading": "Not 4 - Byggnader", "should_extract": False},
]
```

---

### Phase 5: Update Routing Logic
**Status**: 🔴 TODO
**Estimated Time**: 2 hours
**Files to Change**: `optimal_brf_pipeline.py`, routing dictionaries

**Before** (WRONG - note number routing):
```python
# optimal_brf_pipeline.py
def route_section_to_agent(self, section_heading: str):
    """Route based on note numbers (BROKEN!)"""
    SECTION_MAP = {
        "Not 4": "Note4UtilitiesAgent",
        "Noter - Not 4": "Note4UtilitiesAgent",
        "Not 8": "Note8BuildingsAgent",
        "Not 11": "Note11LiabilitiesAgent"
    }

    for pattern, agent in SECTION_MAP.items():
        if pattern in section_heading:
            return agent

    return None  # ❌ Fails for different note numbering!
```

**After** (CORRECT - content-based routing):
```python
# optimal_brf_pipeline.py
from code.content_based_router import ContentBasedRouter, SectionInfo

def __init__(self):
    self.router = ContentBasedRouter()
    # ... rest of init

def route_section_to_agent(self, section_heading: str, preview_text: str, page_range: tuple):
    """Route based on CONTENT keywords (works across all BRFs!)"""
    section = SectionInfo(
        heading=section_heading,
        preview_text=preview_text,
        page_range=page_range
    )

    result = self.router.route_section(section)

    if result.confidence < 0.5:
        # Low confidence, log for review
        print(f"⚠️ Low confidence routing: {section_heading} → {result.agent_name} ({result.confidence:.2f})")

    return result.agent_name
```

**Replace All Routing Dictionaries**:
```bash
# Find all instances
grep -r "Not 4" code/
grep -r "Not 8" code/
grep -r "Note.*Agent" code/

# Replace with content-based routing
# Use ContentBasedRouter instead
```

**Testing**:
```python
# Test routing consistency across different note numbering
router = ContentBasedRouter()

test_cases = [
    # Same content, different note numbers
    ("Not 4 - Driftkostnader", "OperatingCostsAgent"),
    ("Not 7 - Driftkostnader", "OperatingCostsAgent"),
    ("Driftkostnader", "OperatingCostsAgent"),

    # Buildings
    ("Not 8 - Byggnader och mark", "PropertyAgent"),
    ("Not 5 - Byggnader och mark", "PropertyAgent"),
    ("Byggnader och mark", "PropertyAgent"),
]

for heading, expected_agent in test_cases:
    section = SectionInfo(heading, "", (1, 1))
    result = router.route_section(section)
    assert result.agent_name == expected_agent, f"Failed for: {heading}"
    print(f"✅ {heading} → {expected_agent}")
```

---

### Phase 6: Update File Names & Imports
**Status**: 🔴 TODO
**Estimated Time**: 1 hour
**Impact**: Code organization, imports

**File Rename Map**:
```bash
# Agent files
code/note4_utilities_agent.py → code/operating_costs_agent.py
code/note8_buildings_agent.py → code/property_agent.py
code/note11_liabilities_agent.py → code/liabilities_agent.py
code/note5_loans_agent.py → code/loans_agent.py
code/note2_governance_agent.py → code/governance_agent.py

# Schema files (if separate)
schemas/note4_utilities_schema.py → schemas/operating_costs_schema.py
# ... etc
```

**Update All Imports**:
```python
# Before
from code.note4_utilities_agent import Note4UtilitiesAgent
from schemas.note4_utilities_schema import Note4UtilitiesSchema

# After
from code.operating_costs_agent import OperatingCostsAgent
from schemas.operating_costs_schema import OperatingCostsSchema
```

**Script to Update Imports**:
```bash
#!/bin/bash
# update_imports.sh

# Find all Python files
find . -name "*.py" -type f | while read file; do
    # Replace imports
    sed -i '' 's/Note4UtilitiesAgent/OperatingCostsAgent/g' "$file"
    sed -i '' 's/Note4UtilitiesSchema/OperatingCostsSchema/g' "$file"
    sed -i '' 's/Note8BuildingsAgent/PropertyAgent/g' "$file"
    sed -i '' 's/Note8BuildingsSchema/PropertySchema/g' "$file"
    # ... add all other renames
done

echo "✅ Imports updated"
```

---

### Phase 7: Update Documentation & Comments
**Status**: 🔴 TODO
**Estimated Time**: 2 hours
**Files**: All markdown docs, code comments

**Update Documentation**:
```markdown
# Before
## Note4UtilitiesAgent
Extracts utility costs from Not 4 section.

# After
## OperatingCostsAgent
Extracts operating costs breakdown (driftkostnader).

**Content Keywords**: "Driftkostnader", "El", "Värme", "Vatten och avlopp"

**Important**: Do NOT rely on note numbers. Note numbers vary across BRF documents.
This agent identifies sections by CONTENT, not structure.
```

**Update Code Comments**:
```python
# Before
# Look for Not 4 which contains utility costs

# After
# Look for section containing "Driftkostnader" (operating costs breakdown)
# Note: Section may be labeled "Not X" where X varies by document
# Route by CONTENT keywords, not note numbers
```

**Add Anti-Pattern Documentation**:
```markdown
## Anti-Patterns (What NOT to Do)

❌ **Don't hard-code note numbers**:
   ```python
   if "Not 4" in heading: return "UtilitiesAgent"
   ```

❌ **Don't use note numbers in names**:
   ```python
   class Note4UtilitiesAgent  # WRONG
   ```

❌ **Don't assume sequential numbering**:
   ```python
   NOTE_MAP = {4: "utilities", 8: "buildings"}  # WRONG
   ```

✅ **Do use content keywords**:
   ```python
   if "Driftkostnader" in heading: return "OperatingCostsAgent"
   ```
```

---

## 📊 Refactoring Impact Analysis

### Files to Change
```
Total Files: ~25
├── Agent Classes: 10 files
├── Schema Definitions: 10 files
├── Routing Logic: 3 files
├── Test Files: 5 files
└── Documentation: 8 files
```

### Risk Assessment
| Phase | Risk Level | Reason | Mitigation |
|-------|-----------|--------|------------|
| Phase 1 | 🟢 Low | New files, no breakage | Thorough testing |
| Phase 2 | 🟡 Medium | Class renames affect imports | Git branch, gradual migration |
| Phase 3 | 🟢 Low | Schema renames, isolated | Update schema references |
| Phase 4 | 🔴 High | Prompts affect extraction quality | A/B testing, validation |
| Phase 5 | 🔴 High | Routing affects correctness | Comprehensive testing |
| Phase 6 | 🟡 Medium | Import updates, easy to miss | Automated script, linting |
| Phase 7 | 🟢 Low | Documentation only | No code impact |

### Testing Strategy
```python
# Create comprehensive test suite
tests/test_content_based_refactoring.py

def test_routing_consistency():
    """Test same content routes to same agent regardless of note number"""
    router = ContentBasedRouter()

    # Test: Same content, different note numbers
    assert route("Not 4 - Driftkostnader") == "OperatingCostsAgent"
    assert route("Not 7 - Driftkostnader") == "OperatingCostsAgent"
    assert route("Driftkostnader") == "OperatingCostsAgent"

def test_no_note_number_dependencies():
    """Ensure no agent relies on specific note numbers"""
    # Scan all agent code for note number patterns
    agents = glob.glob("code/*_agent.py")

    for agent_file in agents:
        code = open(agent_file).read()
        # Should NOT contain hard-coded note numbers
        assert not re.search(r'Not \d+', code), f"{agent_file} contains note number!"
        assert not re.search(r'Noter - Not \d+', code), f"{agent_file} contains note number!"

def test_extraction_quality_regression():
    """Ensure refactoring doesn't break extraction"""
    # Test on 5 PDFs with known ground truth
    # Compare old vs new agent results

    for pdf_path, ground_truth in TEST_CASES:
        old_result = old_pipeline.extract(pdf_path)
        new_result = new_pipeline.extract(pdf_path)

        assert new_result.coverage >= old_result.coverage
        assert new_result.accuracy >= old_result.accuracy
```

---

## 🎯 Success Criteria

### Phase Completion Checklist
- [ ] Phase 1: ✅ Content-based router implemented and tested
- [ ] Phase 2: All agent classes renamed (no "NoteX" in names)
- [ ] Phase 3: All schema classes renamed (content-based names)
- [ ] Phase 4: All prompts rewritten (no note number mentions)
- [ ] Phase 5: Routing logic uses ContentBasedRouter
- [ ] Phase 6: All files renamed, imports updated
- [ ] Phase 7: Documentation updated with anti-patterns

### Quality Gates
1. **No Note Number Dependencies**:
   ```bash
   # Should return 0 matches
   grep -r "Not [0-9]" code/*.py | grep -v "# " | grep -v "Do NOT"
   ```

2. **Routing Consistency**:
   - Same content → same agent (regardless of note number)
   - 95%+ routing accuracy on test corpus

3. **Extraction Quality**:
   - No regression in field coverage
   - No regression in accuracy
   - Evidence tracking still works

4. **Documentation**:
   - All agents have content keyword lists
   - Anti-patterns documented
   - Examples use content-based routing

---

## 🚀 Migration Strategy

### Option A: Big Bang (Not Recommended)
- Refactor all phases at once
- High risk, hard to debug
- ❌ Not recommended for production system

### Option B: Gradual Migration (Recommended)
```python
# Hybrid approach during migration
class OptimalBRFPipeline:
    def __init__(self, use_content_routing=False):
        self.use_content_routing = use_content_routing
        self.old_router = OldRouter()  # Note number based
        self.new_router = ContentBasedRouter()  # Content based

    def route_section(self, section):
        if self.use_content_routing:
            return self.new_router.route_section(section)
        else:
            return self.old_router.route_section(section)
```

**Migration Steps**:
1. Week 1: Implement Phase 1-3 (infrastructure, rename classes/schemas)
2. Week 2: Implement Phase 4 (rewrite prompts), A/B test
3. Week 3: Implement Phase 5-6 (routing, imports), parallel testing
4. Week 4: Complete Phase 7 (docs), full cutover

**Rollback Plan**:
- Keep old router as fallback
- Feature flag: `USE_CONTENT_ROUTING=false` reverts to old behavior
- Git branch: `refactor/content-based-routing` for safe testing

---

## 📈 Expected Improvements

### Routing Accuracy
- **Before**: 50% match rate (note number dependent)
- **After**: 94%+ match rate (content-based, 3-layer fallback)

### Generalization
- **Before**: Only works on documents with specific note numbering
- **After**: Works across ALL BRF documents regardless of structure

### Maintenance
- **Before**: Need to update agent names/routing for each document variant
- **After**: Single agent works for all variants (automatic content detection)

### Code Quality
- **Before**: Anti-pattern names (Note4UtilitiesAgent)
- **After**: Semantic names (OperatingCostsAgent)

---

## 🎓 Key Learnings

### The Core Insight
> **"Note numbers are arbitrary, content is consistent"**

This applies to ANY document processing pipeline:
1. Don't hard-code structural patterns (section numbers, page positions)
2. Use semantic content identification (keywords, semantic matching)
3. Design for variability, not specific instances
4. Content-based > Structure-based

### Anti-Pattern Recognition
```python
# ❌ If your code has ANY of these, it's an anti-pattern:
- Agent names with numbers (Note4Agent, Section8Agent)
- Routing by position ("page 5", "section 3")
- Assuming specific document structure
- Hard-coded maps (NOTE_MAP = {4: "utilities"})

# ✅ Correct patterns:
- Agent names describe WHAT they extract
- Routing by content keywords
- Flexible document structure handling
- Semantic matching with fallbacks
```

---

## 📋 Next Steps

1. **Immediate** (Today):
   - ✅ Phase 1 complete (infrastructure created)
   - Review this refactoring plan
   - Get stakeholder approval for migration

2. **Week 1** (Oct 13-19):
   - Complete Phase 2-3 (rename classes/schemas)
   - Update imports and references
   - Test on 5 sample PDFs

3. **Week 2** (Oct 20-26):
   - Complete Phase 4 (rewrite prompts)
   - A/B test old vs new prompts
   - Validate extraction quality

4. **Week 3** (Oct 27-Nov 2):
   - Complete Phase 5-6 (routing, file renames)
   - Parallel testing: old router vs new router
   - Performance validation

5. **Week 4** (Nov 3-9):
   - Complete Phase 7 (documentation)
   - Full cutover to content-based system
   - Remove old routing code

---

## 🎉 Success Metrics (Post-Migration)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Routing Accuracy** | 94%+ | Test on 100 diverse BRF PDFs |
| **Extraction Coverage** | 86.7%+ | Maintain current level |
| **Generalization** | 100% | Works on all BRF variants |
| **Code Quality** | Zero anti-patterns | No note numbers in code |
| **Documentation** | Complete | Anti-patterns documented |

**Definition of Done**:
- ✅ All 7 phases complete
- ✅ All tests passing (no regressions)
- ✅ Documentation updated
- ✅ Zero note number dependencies in code
- ✅ Routing accuracy >94% on test corpus
- ✅ Production deployment successful

---

## 📚 References

- Content-based routing config: `config/content_based_routing.yaml`
- Router implementation: `code/content_based_router.py`
- Test suite: `tests/test_content_based_refactoring.py` (to be created)
- Ground truth validation: `experiments/docling_advanced/FINAL_SESSION_REPORT_2025_10_12.md`

---

**Remember**: The goal is not just to fix a bug, but to build a **robust, generalizable architecture** that works across ALL BRF documents, regardless of their specific structure or note numbering scheme.

🎯 **"Content is constant, structure is variable"**
