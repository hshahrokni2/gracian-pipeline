# Anti-Patterns vs Correct Patterns: Content-Based Routing

**The Core Principle**: **NOTE NUMBERS ARE ARBITRARY, CONTENT IS CONSISTENT**

This document shows side-by-side comparisons of incorrect (anti-pattern) and correct approaches to BRF document extraction.

---

## ❌ Anti-Pattern #1: Hard-Coded Note Numbers in Routing

### WRONG (Anti-Pattern)
```python
def route_section_to_agent(self, section_heading: str):
    """Route based on note numbers (BROKEN!)"""
    if "Not 4" in section_heading:
        return "UtilitiesAgent"
    elif "Not 8" in section_heading:
        return "BuildingsAgent"
    elif "Not 11" in section_heading:
        return "LiabilitiesAgent"
    else:
        return None  # ❌ Fails for different note numbering!
```

**Why This is Wrong**:
- Assumes "Not 4" is ALWAYS utilities
- Breaks on documents where utilities are "Not 3", "Not 5", "Not 7", etc.
- Not generalizable across BRF documents

**Real-World Failures**:
- **BRF A**: Utilities in "Not 3" → No extraction ❌
- **BRF B**: Utilities in "Not 7" → No extraction ❌
- **BRF C**: Utilities in "Not 4" → Works ✅ (by luck!)

### ✅ CORRECT (Content-Based)
```python
def route_section_to_agent(self, section_heading: str, preview_text: str):
    """Route based on CONTENT keywords (works everywhere!)"""
    # Layer 1: Direct keyword matching
    if any(kw in section_heading.lower() for kw in ["driftkostnader", "fastighetskostnader"]):
        return "OperatingCostsAgent"
    elif any(kw in section_heading.lower() for kw in ["byggnader och mark", "byggnader"]):
        return "PropertyAgent"
    elif any(kw in section_heading.lower() for kw in ["långfristiga skulder", "lån"]):
        return "LoansAgent"

    # Layer 2: Check preview text for content
    if any(kw in preview_text.lower() for kw in ["el", "värme", "vatten"]):
        return "OperatingCostsAgent"

    # Layer 3: Fuzzy/LLM fallback
    return self.router.route_section(section_heading, preview_text)
```

**Why This is Correct**:
- Routes by CONTENT ("Driftkostnader"), not structure ("Not 4")
- Works on ALL BRF documents regardless of note numbering
- Generalizable and robust

**Real-World Success**:
- **BRF A**: "Not 3 - Driftkostnader" → OperatingCostsAgent ✅
- **BRF B**: "Not 7 - Driftkostnader" → OperatingCostsAgent ✅
- **BRF C**: "Not 4 - Driftkostnader" → OperatingCostsAgent ✅

---

## ❌ Anti-Pattern #2: Note Numbers in Agent Names

### WRONG (Anti-Pattern)
```python
class Note4UtilitiesAgent:
    """Extracts utilities from Not 4"""
    schema = Note4UtilitiesSchema

    def extract(self, pages, docling_result):
        # Look for "Not 4" section
        for section in docling_result.sections:
            if section.heading == "Not 4":  # ❌ Brittle!
                return self.extract_utilities(section)
        return None
```

**Why This is Wrong**:
- Agent name coupled to arbitrary note number
- Implies utilities are ALWAYS in "Not 4"
- Misleading name (suggests structural dependency)

### ✅ CORRECT (Content-Based Name)
```python
class OperatingCostsAgent:
    """
    Extracts operating costs breakdown (driftkostnader).

    Target Fields:
        - electricity (El)
        - heating (Värme)
        - water_sewage (Vatten och avlopp)
        - maintenance_costs (Underhåll)
        - property_tax (Fastighetsskatt)
        - insurance (Försäkringar)
        - administration (Administration)

    Content Keywords:
        - Primary: "Driftkostnader", "Fastighetskostnader"
        - Secondary: "El", "Värme", "Vatten och avlopp"

    IMPORTANT: Do NOT rely on note numbers.
               Note numbers vary across BRF documents.
               Route by CONTENT, not structure.
    """
    schema = OperatingCostsSchema
    content_keywords = ["Driftkostnader", "El", "Värme", "Vatten"]

    def extract(self, pages, docling_result):
        # Look for section with content keywords (any note number!)
        for section in docling_result.sections:
            if any(kw in section.heading for kw in self.content_keywords):
                return self.extract_operating_costs(section)
        return None
```

**Why This is Correct**:
- Name describes WHAT is extracted (operating costs)
- No structural assumptions
- Clear documentation of content-based identification
- Generalizable across all documents

---

## ❌ Anti-Pattern #3: Note Numbers in Schema Names

### WRONG (Anti-Pattern)
```python
class Note4UtilitiesSchema(BaseModel):
    """Schema for Not 4 section"""
    electricity: Optional[float] = Field(None, description="El (SEK)")
    heating: Optional[float] = Field(None, description="Värme (SEK)")
    water_sewage: Optional[float] = Field(None, description="Vatten (SEK)")
```

**Why This is Wrong**:
- Schema coupled to note number
- Suggests data structure depends on note position
- Misleading for developers

### ✅ CORRECT (Content-Based Schema)
```python
class OperatingCostsSchema(BaseModel):
    """
    Operating costs breakdown (Driftkostnader).

    This data is typically found in:
        - Income statement notes
        - Section with heading containing "Driftkostnader" or "Fastighetskostnader"
        - May be labeled "Not X" where X varies by document

    IMPORTANT: Do NOT assume specific note number!
               Focus on CONTENT identification, not structure.
    """
    electricity: Optional[float] = Field(
        None,
        description="Electricity costs (El) in SEK",
        json_schema_extra={
            "swedish_terms": ["El", "Elektricitet", "Elenergi"],
            "typical_context": "Driftkostnader note"
        }
    )
    heating: Optional[float] = Field(
        None,
        description="Heating costs (Värme) in SEK",
        json_schema_extra={
            "swedish_terms": ["Värme", "Fjärrvärme", "Uppvärmning"],
            "typical_context": "Driftkostnader note"
        }
    )
    water_sewage: Optional[float] = Field(
        None,
        description="Water and sewage costs (Vatten och avlopp) in SEK",
        json_schema_extra={
            "swedish_terms": ["Vatten och avlopp", "Vatten", "VA"],
            "typical_context": "Driftkostnader note"
        }
    )
```

**Why This is Correct**:
- Name describes the data content (operating costs)
- Rich metadata for each field (Swedish terms, context)
- Clear documentation that note numbers vary
- Helpful for extraction and validation

---

## ❌ Anti-Pattern #4: Note Numbers in Prompts

### WRONG (Anti-Pattern)
```python
UTILITIES_PROMPT = """
Extract utility costs from Not 4 (Driftkostnader).

Instructions:
1. Find the "Not 4" section in the document
2. Look for the table under "Not 4" heading
3. Extract costs for El, Värme, Vatten

Return JSON with electricity, heating, water_sewage fields.
"""
```

**Why This is Wrong**:
- Hard-codes "Not 4" expectation
- Won't work on documents where utilities are different note number
- Misleads the LLM to look for structure instead of content

**Real-World Failure Example**:
```
Document: BRF Paradise (utilities in "Not 7")
LLM sees: "Find Not 4"
LLM finds: "Not 4" contains accounting principles (wrong section!)
Result: Extracts wrong data or empty results ❌
```

### ✅ CORRECT (Content-Based Prompt)
```python
OPERATING_COSTS_PROMPT = """
Extract operating costs breakdown (driftkostnader) from the provided pages.

TARGET CONTENT (identify by these keywords):
- Section heading containing: "Driftkostnader" OR "Fastighetskostnader"
- May also be labeled as "Not X" where X is an arbitrary number that varies by document

⚠️ IMPORTANT: Do NOT rely on specific note numbers (e.g., "Not 4").
   Note numbers vary across BRF documents. Focus on CONTENT, not structure.

EXTRACTION STRATEGY:
1. Scan all provided pages for section with content keywords above
2. Look for table or list structure with cost line items
3. Match Swedish terms to fields:
   - Electricity: "El", "Elektricitet", "Elenergi"
   - Heating: "Värme", "Fjärrvärme", "Uppvärmning"
   - Water: "Vatten och avlopp", "Vatten", "VA"
   - Maintenance: "Reparation och underhåll", "Löpande underhåll"
   - Property tax: "Fastighetsskatt"
   - Insurance: "Försäkringar", "Fastighetsförsäkring"
   - Administration: "Administration", "Förvaltningskostnader"

4. Extract numeric values (ignore "SEK", "kr", spaces, commas)
5. Cite page number where each value was found

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

**Why This is Correct**:
- Content-focused instructions (look for "Driftkostnader")
- Explicit warning about note number variability
- Multiple synonym terms for each field (handles variations)
- Step-by-step extraction strategy
- Evidence requirements for validation

**Real-World Success Example**:
```
Document: BRF Paradise (utilities in "Not 7")
LLM sees: "Find section with 'Driftkostnader'"
LLM finds: "Not 7 - Driftkostnader" (correct section!)
Result: Extracts utilities successfully ✅
```

---

## ❌ Anti-Pattern #5: Assuming Sequential Note Numbering

### WRONG (Anti-Pattern)
```python
# Routing dictionary based on assumed note structure
NOTE_STRUCTURE = {
    1: "accounting_principles",
    2: "revenue_breakdown",
    3: "personnel_costs",
    4: "utilities",           # ❌ NOT CONSISTENT!
    5: "maintenance",
    6: "financial_costs",
    7: "property_description",
    8: "buildings",            # ❌ NOT CONSISTENT!
    9: "depreciation",
    10: "receivables",
    11: "liabilities",         # ❌ NOT CONSISTENT!
    12: "equity"
}

def route_by_note_number(note_num: int):
    return NOTE_STRUCTURE.get(note_num, "unknown")
```

**Why This is Wrong**:
- Assumes all BRF documents follow same note numbering
- Real-world documents have varying structures
- Brittle and non-generalizable

**Real-World Variability**:
```
BRF A Note Structure:
  Not 1: Accounting principles
  Not 2: Revenue
  Not 3: Utilities          ← Different position!
  Not 4: Personnel
  ...

BRF B Note Structure:
  Not 1: Accounting principles
  Not 2: Personnel
  Not 3: Revenue
  Not 4: Financial costs
  Not 5: Utilities          ← Different position!
  ...

BRF C Note Structure:
  Not 1: Accounting principles
  Not 2: Revenue
  Not 3: Personnel
  Not 4: Utilities          ← Same as anti-pattern assumption
  ...
```

### ✅ CORRECT (Content-Based Routing)
```python
# Content keywords for each agent (position-independent)
AGENT_CONTENT_MAP = {
    "MetadataAgent": {
        "keywords": ["Organisationsnummer", "Räkenskapsår", "Årsredovisning"],
        "typical_location": "Cover page, first 2-3 pages"
    },
    "OperatingCostsAgent": {
        "keywords": ["Driftkostnader", "El", "Värme", "Vatten och avlopp"],
        "typical_location": "Income statement notes"
    },
    "PropertyAgent": {
        "keywords": ["Byggnader och mark", "Antal lägenheter", "Totalarea"],
        "typical_location": "Balance sheet notes"
    },
    "LoansAgent": {
        "keywords": ["Långfristiga skulder", "Lån", "Räntesats"],
        "typical_location": "Liability notes"
    },
    # ... more agents
}

def route_by_content(section_heading: str, preview_text: str):
    """Route based on content keywords (works everywhere!)"""
    for agent_name, config in AGENT_CONTENT_MAP.items():
        # Check if any keyword appears in heading or preview
        for keyword in config["keywords"]:
            if keyword.lower() in section_heading.lower():
                return agent_name
            if keyword.lower() in preview_text.lower():
                return agent_name

    # Fallback to fuzzy/LLM routing
    return advanced_router.route(section_heading, preview_text)
```

**Why This is Correct**:
- No assumptions about note positions
- Routes by semantic content
- Works across all BRF document variants
- Robust and generalizable

---

## 🎯 Summary: The Content-Based Mindset

### ❌ Anti-Pattern Mindset (Structure-Based)
> "Utilities are always in Not 4, buildings in Not 8, liabilities in Not 11"

**Assumptions**:
- All documents follow same structure
- Note numbers are consistent
- Position is reliable identifier

**Reality**:
- ❌ Note numbers vary across documents
- ❌ Structure changes between BRFs
- ❌ Non-generalizable approach

### ✅ Correct Mindset (Content-Based)
> "Utilities are identified by content keywords like 'Driftkostnader', 'El', 'Värme', regardless of note number"

**Principles**:
- Content is consistent across documents
- Keywords are reliable identifiers
- Route semantically, not structurally

**Reality**:
- ✅ Works on ALL BRF documents
- ✅ Handles structural variation
- ✅ Robust and generalizable

---

## 🔍 How to Identify Anti-Patterns in Your Code

### Red Flags (Anti-Patterns Present)
```python
# 🚨 If your code has ANY of these, it's an anti-pattern:

# 1. Note numbers in identifiers
class Note4UtilitiesAgent      # ❌
Note8BuildingsSchema           # ❌
extract_note11_liabilities()   # ❌

# 2. Hard-coded note number checks
if "Not 4" in heading:         # ❌
elif section_num == 8:         # ❌

# 3. Position-based routing
NOTE_MAP = {4: "utilities"}    # ❌
SECTION_AGENTS = {8: BuildingsAgent}  # ❌

# 4. Note numbers in documentation
"Extract from Not 4"           # ❌
"Look for section 8"           # ❌
```

### Green Flags (Correct Patterns)
```python
# ✅ If your code has these, you're doing it right:

# 1. Content-based identifiers
class OperatingCostsAgent      # ✅
PropertySchema                 # ✅
extract_utilities_by_content() # ✅

# 2. Content keyword checks
if "Driftkostnader" in heading:  # ✅
if any(kw in text for kw in keywords):  # ✅

# 3. Semantic routing
CONTENT_KEYWORDS = {"OperatingCostsAgent": ["Driftkostnader", "El"]}  # ✅

# 4. Content-focused documentation
"Find section containing 'Driftkostnader'"  # ✅
"Identify by keywords, not position"        # ✅
```

---

## 📚 Quick Reference Card

### Anti-Pattern Checklist
- [ ] No note numbers in class/function names
- [ ] No note numbers in variable names
- [ ] No hard-coded note number checks
- [ ] No position-based routing maps
- [ ] No note numbers in prompts/docs
- [ ] No assumptions about sequential numbering

### Correct Pattern Checklist
- [ ] Content-based naming (what, not where)
- [ ] Swedish keyword lists for routing
- [ ] 3-layer routing (keywords → fuzzy → LLM)
- [ ] Content-focused prompts
- [ ] Documentation warns about note number variability
- [ ] Tests verify routing consistency across note numbers

---

## 🎓 Key Takeaway

> **"Note numbers are arbitrary labels assigned by accountants.**
> **Content (Driftkostnader, Byggnader, Lån) is the consistent semantic identifier."**

**Design Principle**: Always route and identify by **CONTENT**, never by **STRUCTURE**.

This principle applies to:
- Agent naming
- Schema design
- Routing logic
- Prompt engineering
- Test design
- Documentation

**Test Your Design**: If changing a note number breaks your extraction, you have an anti-pattern!

---

## ✅ Migration Path

If you have anti-patterns in your codebase:

1. **Identify**: Use red flags checklist above
2. **Plan**: Follow `CONTENT_BASED_REFACTORING_PLAN.md`
3. **Implement**: Replace with correct patterns
4. **Test**: Verify routing consistency (same content → same agent)
5. **Validate**: Test on diverse BRF documents

**Success Criteria**: Extraction works correctly regardless of note numbering scheme.

---

**Remember**: Build for the general case, not the specific instance you tested on!
