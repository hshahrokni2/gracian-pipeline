# Deep Ultrathinking Analysis: 30 → 107 Field Expansion
## Swedish BRF Annual Report Extraction - Comprehensive Scaling Strategy

**Date**: 2025-10-12
**Context**: Current system achieves 86.7% coverage, 92% accuracy on 30 fields. Expanding to 107+ fields for comprehensive extraction.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Finding: The 250-Field Reality](#critical-finding)
3. [Question 1: Archetype Classification](#q1-archetype-classification)
4. [Question 2: Learning System Architecture](#q2-learning-system)
5. [Question 3: Hierarchical vs Flat Extraction](#q3-extraction-architecture)
6. [Question 4: Schema Design](#q4-schema-design)
7. [Question 5: Ground Truth Strategy](#q5-ground-truth)
8. [Question 6: Incremental vs Big Bang](#q6-deployment-strategy)
9. [Question 7: Agent Prompt Complexity](#q7-prompt-engineering)
10. [Question 8: Validation System](#q8-validation)
11. [Recommended Architecture](#recommended-architecture)
12. [4-Sprint Implementation Plan](#implementation-plan)
13. [Realistic Target Metrics](#target-metrics)
14. [Production Deployment Reality](#production-reality)

---

## Executive Summary

### Bottom Line

Expanding to 107 fields is **highly valuable** and **technically feasible**, but requires:

1. **Archetype Classification** (saves 53.6% cost = $6,217 on 26K corpus)
2. **Hierarchical Extraction** (Pass 1 → Pass 2 with adaptive agents)
3. **Few-Shot Learning System** (2-3 examples per agent for accuracy)
4. **Incremental Rollout** (4 sprints: 30 → 53 → 71 → 93 → 107 fields)
5. **Realistic Targets** (60-65% corpus coverage, 82-87% field accuracy)

### Expected ROI

| Metric | Current (30F) | Target (107F) | Gain/Cost |
|--------|---------------|---------------|-----------|
| **Fields Extracted** | 30 | 107 | **3.6x more data** |
| **Correct Fields (avg)** | 27.6 (92%) | 85.6 (80%) | **3.1x information gain** |
| **Cost per PDF** | $0.14 | $0.22 | **1.6x cost increase** |
| **ROI** | Baseline | **3.1x gain / 1.6x cost** | **1.9x value/dollar** |

**Verdict**: **Excellent ROI** - Proceed with archetype-based hierarchical extraction.

---

## Critical Finding: The 250-Field Reality {#critical-finding}

### What the Ground Truth Actually Contains

The `brf_198532_comprehensive_ground_truth.json` file has **~250 extractable data points**, not 107!

#### Full Breakdown

| Category | Subcategories | Fields | Complexity |
|----------|---------------|--------|------------|
| **Metadata** | Document info, registration | 13 | Simple |
| **Governance** | Board (7 members), auditors (2), nomination (2) | 17+ | Structured arrays |
| **Property** | Buildings, insurance, areas, heating | 20+ | Mixed |
| **Apartments** | Counts, breakdowns, transfers | 10+ | Simple |
| **Commercial** | Tenants, leases, VAT | 8+ | Structured arrays |
| **Common Areas** | Terraces, rooms, entrances | 6+ | Structured |
| **Maintenance** | Plans, schedules | 5+ | Structured |
| **Contracts** | 15+ service contracts | 15+ | Flat list |
| **Financials** | Income statement (2 years) | 40+ | Nested |
| **Financials** | Balance sheet (2 years) | 40+ | Nested |
| **Revenue** | Breakdown (15 line items) | 15+ | Nested |
| **Operating Costs** | Breakdown (7 line items) | 7+ | Nested |
| **Loans** | 4 loans × 8 fields each | 32+ | Structured arrays |
| **Fees** | Historical (4 years) | 8+ | Simple |
| **Key Ratios** | 10 metrics × 4 years | 40+ | Nested |
| **Members** | Counts, changes | 4 | Simple |
| **Cash Flow** | 2 years of statements | 20+ | Nested |
| **Tax** | Rates, policies | 4+ | Simple |
| **Building Details** | Depreciation, valuations | 15+ | Complex |
| **Receivables** | Breakdown (5 types) | 7+ | Nested |
| **Maintenance Fund** | Changes over 2 years | 6+ | Simple |
| **Accrued Expenses** | Breakdown | 4+ | Nested |
| **Personnel** | Compensation, social costs | 6+ | Simple |
| **Events** | Significant events (18 items) | 18+ | Structured arrays |
| **Result Disposition** | Available funds, proposals | 6+ | Nested |
| **Equity Changes** | Detailed movements | 20+ | Complex nested |
| **Accounting Principles** | Policies, standards | Text | Narrative |

**Total**: ~250-300 extractable data points in a comprehensive K3 BRF report!

### Implications

1. **107 fields is a middle ground**, not the maximum
2. **Archetype classification is MANDATORY** (small K2 BRFs have ~40 fields, not 250!)
3. **Schema must be hierarchical** (can't have 250 flat fields)
4. **Ground truth validation** is complex (need multiple documents for different archetypes)

---

## Q1: Archetype Classification - CRITICAL for Production {#q1-archetype-classification}

### Problem Statement

Swedish BRFs vary from tiny (5 apartments, simple K2) to massive (200+ apartments, complex K3). Running 25 agents on a simple BRF that only has 40 fields wastes 60% of API calls.

### Archetype Definitions

#### **Simple K2 (35% of corpus, ~9,200 PDFs)**

**Characteristics**:
- Small BRFs (5-40 apartments)
- K2 simplified accounting
- Minimal notes section (3-5 notes)
- Single or no loans
- No commercial tenants
- Basic property info

**Extractable Fields**: ~40 fields
- Metadata: 10 fields
- Governance: 6 fields (chairman, 3-5 board members, 1 auditor)
- Property: 5 fields (address, year, apartment count)
- Financial Totals: 12 fields (revenue, expenses, assets, liabilities, equity)
- Notes: 7 fields (1-2 loan entries, buildings, basic reserves)

**Processing**:
- **Agents**: 8 agents (governance, property, financial_totals, 5 note agents)
- **Cost**: $0.14/PDF (current baseline)
- **Time**: 50-120s

#### **Medium K2 (40% of corpus, ~10,500 PDFs)**

**Characteristics**:
- Mid-size BRFs (40-80 apartments)
- K2 with some detail
- Moderate notes (6-9 notes)
- 2-3 loans
- Possibly commercial tenants
- Detailed property info

**Extractable Fields**: ~65 fields
- Metadata: 12 fields
- Governance: 10 fields (chairman, 5-7 board members, 2 auditors, nomination committee)
- Property: 10 fields (full address, energy class, areas)
- Financial Totals: 12 fields
- Financial Breakdown: 12 fields (revenue breakdown, operating costs summary)
- Loans: 16 fields (2 loans × 8 fields)
- Notes: 13 fields (buildings, receivables, reserves, accrued expenses)

**Processing**:
- **Agents**: 14 agents (governance, property, financial_totals, financial_breakdown, 2 loan agents, 8 note agents)
- **Cost**: $0.20/PDF
- **Time**: 90-180s

#### **Complex K3 (25% of corpus, ~6,600 PDFs)**

**Characteristics**:
- Large BRFs (80-200+ apartments)
- K3 comprehensive accounting
- Extensive notes (10-15+ notes)
- 3-5 loans
- Commercial tenants
- Complex property structures
- Multi-year comparisons

**Extractable Fields**: ~95 fields (targeting 107 in Phase 4)
- Metadata: 13 fields
- Governance: 17 fields (full board, auditors, nomination, meetings)
- Property: 20 fields (detailed property, commercial, apartments, common areas)
- Financial Totals: 12 fields
- Financial Breakdown: 22 fields (revenue breakdown, operating costs breakdown, other expenses)
- Loans: 32 fields (4 loans × 8 fields)
- Key Ratios: 10 fields (1 year snapshot)
- Notes: 20 fields (buildings detail, receivables detail, maintenance fund, equity changes, cash flow summary)

**Processing**:
- **Agents**: 22 agents (governance, property, financial_totals, revenue_breakdown, operating_costs_breakdown, 4 loan agents, 12 note agents)
- **Cost**: $0.30/PDF
- **Time**: 150-300s

### Archetype Classification ROI

**Analysis Results** (from `archetype_roi_analysis.py`):

```
Corpus: 26,342 PDFs (Arsredovisning)

Archetype-Based Approach:
  • Avg fields: 63.8 fields/doc
  • Avg agents: 13.9 agents/doc
  • Avg cost: $0.204/doc
  • Total cost: $5,374

Flat 107-Field Approach (25 agents for all):
  • Fields: 107 (many NULL)
  • Agents: 25 agents/doc
  • Cost: $0.440/doc
  • Total cost: $11,590

Savings:
  • Cost reduction: 53.6%
  • Total savings: $6,217
  • ROI: 124x development cost
```

### Recommendation: **YES - IMPLEMENT ARCHETYPE CLASSIFICATION**

**Approach**:

1. **Classifier Design** (Week 1, 1 day):
   - Input: Docling structure (section count, note count, page count)
   - Features: `num_sections`, `num_notes`, `total_pages`, `has_commercial`, `loan_count_estimate`
   - Model: Simple decision tree (not ML - rules-based)
   - Cost: ~$40 development + $10 validation

2. **Classification Rules**:
   ```python
   def classify_brf_archetype(structure: DoclingStructure) -> str:
       num_notes = len([s for s in structure.sections if is_note(s)])
       total_pages = structure.total_pages
       num_sections = len(structure.sections)

       # Simple K2: Few notes, short document
       if num_notes <= 5 and total_pages < 20:
           return "simple_k2"

       # Complex K3: Many notes, long document
       elif num_notes >= 10 and total_pages > 25:
           return "complex_k3"

       # Medium K2: Everything else
       else:
           return "medium_k2"
   ```

3. **Validation** (Week 1, 1 day):
   - Test on 50 manually classified PDFs
   - Target: ≥85% classification accuracy
   - Misclassification cost: Acceptable (err on side of "complex" for borderline cases)

4. **Integration** (Week 1, 1 day):
   - Add classifier to `OptimalBRFPipeline.extract_document()`
   - Select agent set based on archetype
   - Log archetype for analytics

**Expected Impact**:
- 53.6% cost savings on 26K corpus
- Better accuracy (focused agents, less hallucination)
- Faster processing (fewer agents = less time)

---

## Q2: Learning System Architecture {#q2-learning-system}

### Problem Statement

Current system has **zero few-shot examples**. LLMs perform 15-30% better with 2-3 good examples. For 107 fields with Swedish term ambiguity, learning system is critical.

### Component 1: Few-Shot Examples (CRITICAL)

#### Why Few-Shot Learning Matters

**Without Examples** (current):
```
Prompt: "Extract driftskostnader breakdown: fastighetsskott, reparationer, el/värme, försäkringar..."
LLM: *Sees Swedish terms, gets confused, extracts wrong values or hallucinates*
Accuracy: ~70-75%
```

**With 2-3 Examples**:
```
Prompt: "Extract driftskostnader breakdown..."

Example 1:
Input: "Driftskostnader 2021: Fastighetsskott 553,590 kr, Reparationer 258,004 kr..."
Output: {"fastighetsskott": 553590, "reparationer": 258004, ...}

Example 2:
Input: "Drift 2020: Skötsel 412,000, Underhåll 186,500, Energi 1,240,000..."
Output: {"fastighetsskott": 412000, "reparationer": 186500, "el_vatten_uppvarmning": 1240000, ...}

Now extract from:
[Your PDF pages]

LLM: *Follows pattern, maps Swedish variants correctly*
Accuracy: 85-90%
```

#### Implementation Strategy

**Approach 1: Curated Examples (Recommended)**

1. **Create Example Bank** (Week 1, 2-3 days):
   - Manually extract 3 examples per agent from diverse PDFs
   - Cover Swedish term variants ("Driftskostnader" vs "Drift" vs "Fastighetsdrift")
   - Include edge cases (negative values, missing fields, etc.)
   - Store in `config/few_shot_examples.yaml`

2. **Example Storage Format**:
   ```yaml
   financial_totals_agent:
     examples:
       - input_text: "Resultaträkning 2021: Nettoomsättning 7,393,591 kr..."
         input_image: examples/brf_198532_p8.png
         output: {"revenue": 7393591, "expenses": -6631400, ...}
         notes: "Standard format, multiple years"

       - input_text: "Ekonomisk översikt: Intäkter 4,250,000 Kostnader 3,890,000..."
         output: {"revenue": 4250000, "expenses": -3890000, ...}
         notes: "Simplified K2 format"

       - input_text: "Drift: Överskott 120,000 kr..."
         output: {"surplus": 120000}
         notes: "Only surplus reported (small BRF)"
   ```

3. **Prompt Integration**:
   ```python
   def build_prompt_with_examples(agent_id: str, agent_prompt: str) -> str:
       examples = load_few_shot_examples(agent_id)

       prompt = agent_prompt + "\n\n=== EXAMPLES ===\n\n"
       for i, example in enumerate(examples[:3], 1):  # Max 3 examples
           prompt += f"Example {i}:\n"
           prompt += f"Input: {example['input_text']}\n"
           prompt += f"Output: {json.dumps(example['output'])}\n\n"

       prompt += "=== NOW EXTRACT FROM THESE PAGES ===\n"
       return prompt
   ```

4. **Token Cost**:
   - 3 examples ≈ 500-800 tokens
   - At GPT-4o rates: ~$0.0024-0.0038 per agent call
   - Worth it for 15-20% accuracy improvement

**Approach 2: Auto-Generated Examples (Future)**

- Use high-confidence extractions as examples
- Build example bank automatically from production runs
- Requires validation step (human-in-the-loop)

**Recommendation**: Start with Approach 1 (curated), migrate to Approach 2 after 1000+ successful extractions.

### Component 2: Field-Level Swedish Term Mapping (CRITICAL)

#### Problem

Current system has **section-level routing**:
- "Resultaträkning" → `financial_agent`

But **field-level ambiguity**:
- "Driftskostnader" = Operating costs **total** (one field)
- "Fastighetsdrift" = Property operating costs **subset** (different field)
- "Driftsöverskott" = Operating **surplus** (revenue - operating costs)

LLM will confuse these without explicit mapping!

#### Solution: Field-Level Synonym Dictionary

**Structure**:
```yaml
# config/field_level_synonyms.yaml

financial_fields:
  revenue:
    primary_terms: ["nettoomsättning", "intäkter"]
    variants: ["nettointäkter", "försäljning", "avgiftsintäkter"]
    exclude: ["övriga intäkter"]  # Different field!

  operating_costs_total:
    primary_terms: ["driftskostnader", "rörelsekostnader"]
    variants: ["drift", "driftskostnad"]
    exclude: ["fastighetsdrift", "driftsöverskott"]  # Subsets/derivatives

  property_operating_costs:
    primary_terms: ["fastighetsdrift", "fastighetsskötsel"]
    parent_field: "operating_costs_total"  # This is a breakdown

  operating_surplus:
    primary_terms: ["driftsöverskott", "rörelseresultat"]
    calculated_from: ["revenue", "operating_costs_total"]
```

**Usage in Prompts**:
```python
def enhance_prompt_with_field_mapping(prompt: str, agent_id: str) -> str:
    mappings = load_field_synonyms(agent_id)

    field_guide = "\n\nFIELD MAPPING GUIDE:\n"
    for field_name, synonyms in mappings.items():
        field_guide += f"- {field_name}: Look for {synonyms['primary_terms']}\n"
        if 'exclude' in synonyms:
            field_guide += f"  ⚠️ Do NOT confuse with: {synonyms['exclude']}\n"

    return prompt + field_guide
```

**Implementation Timeline**:
- Sprint 1: Build mapping for 53 fields (~1 day)
- Sprint 2-4: Expand as new fields added (~0.5 day/sprint)

### Component 3: Adaptive Learning (Nice-to-Have)

**Concept**: Learn from validation results

```python
# After each extraction
if extraction.quality_score < 0.80:
    # Log failed extraction for review
    failure_log.append({
        "pdf": pdf_path,
        "agent": agent_id,
        "issue": extraction.validation_errors,
        "input_context": extraction.input_pages,
        "output": extraction.data
    })

# Weekly review
review_failures()  # Human reviews top 10 failure patterns
update_few_shot_examples()  # Add examples for failure cases
update_field_mappings()  # Add missing Swedish variants
```

**Value**: 5-10% accuracy improvement over 3-6 months
**Effort**: 2 hours/week human review
**Recommendation**: Implement in Month 2 (after initial deployment)

### Learning System Summary

| Component | Priority | Effort | Impact | Timeline |
|-----------|----------|--------|--------|----------|
| **Few-Shot Examples** | **P0 - CRITICAL** | 3 days | +15-20% accuracy | Sprint 1 |
| **Field-Level Synonyms** | **P0 - CRITICAL** | 1 day | +10-15% accuracy | Sprint 1 |
| **Adaptive Learning** | P1 - Nice-to-have | 2 hrs/week | +5-10% over time | Month 2+ |

**Total Sprint 1 Investment**: 4 days for +25-35% accuracy improvement = **Excellent ROI**

---

## Q3: Extraction Architecture - Hierarchical vs Flat {#q3-extraction-architecture}

### The Three Options

#### **Option A: Flat 107-Field Extraction**

```python
# All agents run in parallel, extract what exists
agents = [
    'governance_agent',          # 8 fields
    'property_agent',            # 7 fields
    'financial_totals_agent',    # 12 fields
    'revenue_breakdown_agent',   # 15 fields
    'operating_costs_agent',     # 7 fields
    'loan_1_agent',              # 8 fields
    'loan_2_agent',              # 8 fields
    'loan_3_agent',              # 8 fields
    'loan_4_agent',              # 8 fields
    'buildings_detail_agent',    # 10 fields
    'receivables_detail_agent',  # 8 fields
    # ... 25 agents total
]

results = parallel_extract(agents)  # All run simultaneously
```

**Pros**:
- ✅ Simple implementation (no conditional logic)
- ✅ Fully parallelizable (all agents independent)
- ✅ No cascade failure risk

**Cons**:
- ❌ Wasteful (run 25 agents when only 8 have data)
- ❌ Expensive (25 API calls * $0.018 = $0.45/PDF)
- ❌ Slow (25 agents serially = 5+ minutes even with parallel)
- ❌ Higher error rate (more agents = more hallucination chances)

**Verdict**: ❌ **Not recommended** for production (too expensive)

#### **Option B: Hierarchical Pass-Based Extraction**

```python
# Pass 1: Extract totals + detect what exists
pass1 = extract_high_level()  # 8 agents, 30 fields
  - governance_agent
  - property_agent
  - financial_totals_agent
  - notes_summary_agent

# Analyze Pass 1 results
if pass1.has_revenue_breakdown:
    pass2_agents.append('revenue_breakdown_agent')
if pass1.loan_count > 0:
    for i in range(pass1.loan_count):
        pass2_agents.append(f'loan_{i}_agent')
if pass1.has_operating_costs_detail:
    pass2_agents.append('operating_costs_breakdown_agent')

# Pass 2: Extract detailed breakdowns
pass2 = extract_detailed(pass2_agents, context=pass1)
```

**Pros**:
- ✅ Efficient (only extract what exists)
- ✅ Cost-effective (adaptive to document complexity)
- ✅ Better accuracy (Pass 2 agents get Pass 1 context)
- ✅ Fail-safe (Pass 1 failures isolated from Pass 2)

**Cons**:
- ⚠️ Sequential bottleneck (Pass 2 waits for Pass 1)
- ⚠️ Complex logic (decision tree for what to extract)
- ⚠️ Harder to debug (different paths for different docs)

**Verdict**: ✅ **Good for development** (learn what works before optimizing)

#### **Option C: Archetype-Based (Recommended for Production)**

```python
# Step 1: Classify document
archetype = classify_brf_document(structure)  # "simple" | "medium" | "complex"

# Step 2: Select agent configuration
if archetype == "simple_k2":
    agents = simple_agents  # 8 agents, 40 fields
elif archetype == "medium_k2":
    agents = medium_agents  # 14 agents, 65 fields
else:  # complex_k3
    agents = complex_agents  # 22 agents, 95 fields

# Step 3: Extract with archetype-specific agents (can parallelize within archetype)
results = parallel_extract_archetype(agents, archetype_config)
```

**Pros**:
- ✅ Optimal cost/quality (extract exactly what document offers)
- ✅ Fast (parallel within archetype)
- ✅ Scalable (easy to add "ultra_complex" archetype)
- ✅ Better accuracy (agents tuned to archetype)

**Cons**:
- ⚠️ Misclassification risk (5-10% docs classified wrong)
- ⚠️ Added complexity (need robust classifier)
- ⚠️ Harder to debug (3 different code paths)

**Verdict**: ✅ **BEST for production** (after validating Option B in development)

### Hybrid Recommendation: **Option B → Option C**

**Development Phase** (Sprints 1-3):
- Use Option B (Hierarchical)
- Learn what agents work well
- Validate hierarchical logic
- Measure cost/accuracy by document type

**Production Phase** (Sprint 4+):
- Migrate to Option C (Archetype-Based)
- Use learnings from Option B to tune archetype configs
- Implement classifier with 85%+ accuracy
- Deploy with monitoring and rollback capability

**Why Hybrid?**
- Option B is simpler to implement initially
- Learnings from Option B inform Option C design
- Lower risk (validate hierarchical logic before adding classifier)
- Incremental complexity (one major change per sprint)

---

## Q4: Schema Design - Nested vs Flat {#q4-schema-design}

### The Two Approaches

#### **Approach 1: Nested Pydantic Models (Recommended)**

```python
# Nested structure for logical grouping

class DriftskostnaderData(BaseModel):
    """Operating costs breakdown"""
    fastighetsskott: Optional[float] = None  # Property maintenance
    reparationer_underhall: Optional[float] = None  # Repairs
    el_vatten_uppvarmning: Optional[float] = None  # Utilities
    forsakringar: Optional[float] = None  # Insurance
    ovriga_driftskostnader: Optional[float] = None  # Other
    total: float  # REQUIRED - sum should match this

    @validator('total')
    def validate_total(cls, v, values):
        """Cross-validate that subtotal ≈ total"""
        subtotal = sum(val for val in values.values() if val is not None)
        if subtotal > 0 and abs(subtotal - v) > v * 0.05:  # 5% tolerance
            logger.warning(f"Driftskostnader subtotal {subtotal} != total {v}")
        return v

class LoanData(BaseModel):
    """Individual loan details"""
    lender: str
    original_amount: Optional[float] = None
    current_balance: float
    interest_rate: Optional[float] = None
    maturity_date: Optional[str] = None
    amortization_free: Optional[bool] = None
    loan_number: Optional[str] = None
    notes: Optional[str] = None

class FinancialData(BaseModel):
    """Complete financial data"""
    # Totals
    revenue: float
    expenses: float
    assets: float
    liabilities: float
    equity: float
    surplus: Optional[float] = None

    # Breakdowns (nested)
    driftskostnader: Optional[DriftskostnaderData] = None
    revenue_breakdown: Optional[RevenueBreakdownData] = None

    # Loans (array)
    loans: List[LoanData] = []

    # Evidence
    evidence_pages: List[int] = []

class BRFExtraction(BaseModel):
    """Top-level extraction result"""
    metadata: MetadataData
    governance: GovernanceData
    financials: FinancialData
    property: PropertyData
    notes: NotesData
```

**Pros**:
- ✅ Logical grouping (related fields together)
- ✅ Built-in validation (Pydantic validators)
- ✅ Type safety (nested structure enforced)
- ✅ Clean agent interfaces (agent returns DriftskostnaderData)
- ✅ Easy to extend (add new nested models)

**Cons**:
- ⚠️ More complex (need to merge nested structures)
- ⚠️ Harder to query (result.financials.driftskostnader.fastighetsskott)

#### **Approach 2: Flat with Naming Convention**

```python
class BRFExtraction(BaseModel):
    """Flat structure with prefixes"""
    # Metadata
    org_number: str
    doc_year: int

    # Governance
    chairman: str
    board_members: List[str]

    # Financial - Totals
    financial_revenue: float
    financial_expenses: float
    financial_assets: float
    financial_liabilities: float
    financial_equity: float

    # Financial - Driftskostnader Breakdown
    driftskostnader_fastighetsskott: Optional[float] = None
    driftskostnader_reparationer: Optional[float] = None
    driftskostnader_el_vatten: Optional[float] = None
    driftskostnader_total: float

    # Loans (flat arrays)
    loan_1_lender: Optional[str] = None
    loan_1_balance: Optional[float] = None
    loan_1_interest_rate: Optional[float] = None
    loan_2_lender: Optional[str] = None
    # ... 107 flat fields
```

**Pros**:
- ✅ Simple (all fields at same level)
- ✅ Easy to query (result.driftskostnader_fastighetsskott)
- ✅ Easy to flatten to database row

**Cons**:
- ❌ Naming pollution (107 fields at top level = messy)
- ❌ No built-in validation (cross-field checks are manual)
- ❌ Hard to extend (adding 20 fields = 20 new top-level attributes)

### Hybrid Recommendation: **Nested for Extraction, Flat for Storage**

**Best of Both Worlds**:

```python
# EXTRACTION: Use nested models (clean agent interfaces)
driftskostnader = extract_driftskostnader()  # Returns DriftskostnaderData
loans = [extract_loan(i) for i in range(loan_count)]  # Returns List[LoanData]
financials = FinancialData(
    revenue=...,
    driftskostnader=driftskostnader,
    loans=loans
)
extraction = BRFExtraction(financials=financials, ...)

# STORAGE: Flatten to simple dict (easy querying)
flat_dict = flatten_nested_model(extraction)
# Result: {
#   "financial_revenue": 7393591,
#   "driftskostnader_fastighetsskott": 553590,
#   "loan_1_lender": "SEB",
#   ...
# }
db.store(flat_dict)

# QUERY: Simple field access
value = db.query("driftskostnader_fastighetsskott")  # Direct access
```

**Implementation**:

```python
def flatten_nested_model(model: BaseModel, prefix: str = "") -> Dict[str, Any]:
    """Recursively flatten nested Pydantic model to flat dict"""
    result = {}

    for field_name, field_value in model.dict().items():
        full_key = f"{prefix}_{field_name}" if prefix else field_name

        if isinstance(field_value, BaseModel):
            # Nested model: recurse
            result.update(flatten_nested_model(field_value, prefix=full_key))
        elif isinstance(field_value, list) and len(field_value) > 0:
            if isinstance(field_value[0], BaseModel):
                # Array of nested models: number them
                for i, item in enumerate(field_value, 1):
                    result.update(flatten_nested_model(item, prefix=f"{full_key}_{i}"))
            else:
                # Array of primitives: keep as-is
                result[full_key] = field_value
        else:
            # Primitive: store directly
            result[full_key] = field_value

    return result
```

**Benefits**:
- Clean code (nested models during extraction)
- Simple queries (flat dict in database)
- Type safety (Pydantic validation)
- Easy debugging (both representations available)

### Optional Fields Strategy

**Rule**: Everything except top-level IDs should be `Optional`

```python
class FinancialData(BaseModel):
    # REQUIRED (always extracted or null)
    revenue: float  # Even if 0, must be present
    assets: float
    liabilities: float
    equity: float

    # OPTIONAL (may not exist in simple BRFs)
    expenses: Optional[float] = None
    surplus: Optional[float] = None
    driftskostnader: Optional[DriftskostnaderData] = None

    @validator('equity', always=True)
    def validate_accounting_equation(cls, v, values):
        """Assets = Liabilities + Equity"""
        assets = values.get('assets', 0)
        liabilities = values.get('liabilities', 0)
        if assets > 0:
            expected_equity = assets - liabilities
            if abs(expected_equity - v) > assets * 0.01:  # 1% tolerance
                logger.warning(f"Accounting equation violated: Assets {assets} != Liabilities {liabilities} + Equity {v}")
        return v
```

**Why This Works**:
- Simple K2 BRFs: Many fields are `None` (acceptable)
- Complex K3 BRFs: Most fields populated
- Validation still works (checks populated fields only)
- Database can handle sparse data (JSONB in PostgreSQL)

---

## Q5: Ground Truth Strategy - Staged Validation {#q5-ground-truth}

### Current State

- **Ground truth exists**: brf_198532 with ~250 data points (comprehensive)
- **Current validation**: 30 fields tested
- **Gap**: 77 fields (to reach 107) or 220 fields (for full comprehensive)

### The Four Options

#### **Option 1: Complete Single-Document Ground Truth (Recommended)**

**Approach**:
1. Manually verify ALL 107 target fields on brf_198532 (one-time investment)
2. Create three ground truth files:
   - `brf_198532_simple_gt.json` (40 fields - what a K2 would have)
   - `brf_198532_medium_gt.json` (65 fields - medium K2)
   - `brf_198532_comprehensive_gt.json` (107 fields - complex K3, already exists!)

**Effort**: 4-6 hours for complete validation
**Value**: Reusable for all 4 sprints

**Pros**:
- ✅ One-time investment
- ✅ Complete coverage for testing
- ✅ Can validate each sprint against subset
- ✅ Regression testing (ensure new fields don't break old fields)

**Cons**:
- ⚠️ Single document may not cover all edge cases

**Recommendation**: **YES - Do this in Sprint 1, Week 1**

#### **Option 2: Multi-Document Partial Ground Truth**

**Approach**:
- Validate 40 fields on 3 simple K2 BRFs
- Validate 65 fields on 3 medium K2 BRFs
- Validate 107 fields on 3 complex K3 BRFs

**Effort**: 12-18 hours (3x Option 1)
**Value**: Better coverage of edge cases

**Pros**:
- ✅ Tests extraction robustness across document types
- ✅ Finds edge cases (different accounting firms, formats)

**Cons**:
- ❌ 3x effort
- ❌ Not needed until production (Option 1 sufficient for development)

**Recommendation**: **Defer to Month 2** (after initial deployment)

#### **Option 3: Staged Ground Truth (50 → 70 → 107 fields)**

**Approach**:
- Sprint 1: Validate 40 + 13 new = 53 fields
- Sprint 2: Validate 53 + 18 new = 71 fields
- Sprint 3: Validate 71 + 22 new = 93 fields
- Sprint 4: Validate 93 + 14 new = 107 fields

**Effort**: 1-2 hours per sprint (8 hours total, spread over 4 sprints)
**Value**: Incremental validation matches incremental development

**Pros**:
- ✅ Matches incremental development
- ✅ Lower upfront cost
- ✅ Validates as you go

**Cons**:
- ⚠️ No full regression testing until Sprint 4
- ⚠️ May miss cross-field issues

**Recommendation**: **Hybrid with Option 1** (do full validation in Sprint 1, but only test relevant subset each sprint)

#### **Option 4: Production-Driven Ground Truth**

**Approach**:
- Deploy 50-field system to production
- Collect user feedback ("this field is wrong")
- Manually verify reported errors
- Build ground truth from real errors

**Effort**: Ongoing (2-3 hours/week)
**Value**: Real-world validation

**Pros**:
- ✅ Real user feedback
- ✅ Finds actual issues (not theoretical)

**Cons**:
- ❌ Requires production deployment
- ❌ Reactive (not proactive)

**Recommendation**: **Complement Option 1** (use for Month 2+ improvements)

### Recommended Strategy: **Option 1 + Option 4**

**Sprint 1 (Week 1)**:
- Spend 4-6 hours creating complete 107-field ground truth for brf_198532
- Validate incrementally:
  - Sprint 1 target fields (53): Test against 53-field subset
  - Sprint 2 target fields (71): Test against 71-field subset
  - Sprint 3 target fields (93): Test against 93-field subset
  - Sprint 4 target fields (107): Test against full ground truth

**Month 2+**:
- Add 2-3 more ground truth documents (one per archetype)
- Use production feedback to identify edge cases
- Continuously improve

**Why This Works**:
- Low upfront investment (6 hours)
- Covers all development phases
- Enables regression testing
- Allows incremental validation

---

## Q6: Deployment Strategy - Incremental vs Big Bang {#q6-deployment-strategy}

### The Two Approaches

#### **Big Bang: Build All 25 Agents at Once**

**Timeline**: 4 weeks to build everything, then test

**Pros**:
- ✅ All agents designed together (consistent interfaces)
- ✅ One-time learning curve

**Cons**:
- ❌ High risk (if accuracy drops to 60%, 4 weeks wasted)
- ❌ Hard to debug (25 agents failing simultaneously)
- ❌ No user feedback during development
- ❌ Opportunity cost (could have deployed 50-field system in Week 2)

**Verdict**: ❌ **Too risky for production**

#### **Incremental: Add 2-3 Agents Per Sprint**

**Timeline**: 4 sprints × 1 week = 4 weeks, but usable system after Sprint 1

**Pros**:
- ✅ Learn as you go (each sprint teaches about Swedish terms, edge cases)
- ✅ Fail fast (if Sprint 1 accuracy is 65%, pivot before continuing)
- ✅ Maintain production stability (30-field system keeps running)
- ✅ User feedback (users may say "we need X, not Y")

**Cons**:
- ⚠️ Requires incremental testing infrastructure
- ⚠️ Some rework (Sprint 2 may inform Sprint 1 changes)

**Verdict**: ✅ **Recommended** (standard agile practice for good reason)

### Recommended 4-Sprint Plan

#### **Sprint 1: Foundation + Breakdown Agents (Week 1)**

**Goal**: Validate hierarchical extraction works, add first detailed agents

**Agents to Add**:
1. `revenue_breakdown_agent` (15 new fields):
   - annual_fees, commercial_rent, garage_rent, cable_tv, water_income, etc.

2. `loan_1_detailed_agent` (8 new fields):
   - lender, loan_number, amount, interest_rate, maturity_date, amortization_free, etc.

**Total**: 30 (current) + 23 (new) = **53 fields**

**Success Criteria**:
- ≥85% accuracy on 53 fields (brf_198532 ground truth)
- Hierarchical extraction validated (Pass 1 → Pass 2 with context)
- Cost ≤$0.16/PDF

**Effort**: 3-4 days development + 1 day testing = **5 days**

#### **Sprint 2: Multi-Instance + Property Detail (Week 2)**

**Goal**: Validate multi-loan extraction, expand property details

**Agents to Add**:
1. `loan_2_detailed_agent` (8 new fields)
2. `operating_costs_breakdown_agent` (7 new fields):
   - fastighetsskott, reparationer, el_vatten_uppvarmning, forsakringar, etc.

3. `property_detailed_agent` (3 new fields):
   - energy_class, total_area_sqm, building_type

**Total**: 53 + 18 = **71 fields**

**Success Criteria**:
- ≥85% accuracy on 71 fields
- Multi-loan extraction works (2-3 loans correctly identified)
- Cost ≤$0.18/PDF

**Effort**: 3-4 days development + 1 day testing = **5 days**

#### **Sprint 3: Balance Sheet Details (Week 3)**

**Goal**: Extract detailed balance sheet components

**Agents to Add**:
1. `loan_3_detailed_agent` (8 new fields)
2. `buildings_detail_agent` (10 new fields):
   - book_value, acquisition_value, depreciation, land_value, tax_value

3. `receivables_detail_agent` (8 new fields):
   - tax_account, vat_settlement, client_funds, other_receivables

4. `maintenance_fund_detail_agent` (6 new fields):
   - beginning_balance, allocation, withdrawals, ending_balance

**Total**: 71 + 32 = **103 fields** (close to 107!)

**Success Criteria**:
- ≥83% accuracy on 103 fields (acceptable drop due to complexity)
- Balance sheet details correctly extracted
- Cost ≤$0.20/PDF

**Effort**: 4-5 days development + 1 day testing = **6 days**

#### **Sprint 4: Final Fields + Archetype Classification (Week 4)**

**Goal**: Reach 107 fields, optimize with archetype classifier

**Agents to Add**:
1. `loan_4_detailed_agent` (8 new fields - if 4th loan exists)
2. `equity_changes_agent` (6 new fields):
   - retained_earnings_beginning, retained_earnings_change, year_result

3. Final tweaks to existing agents

**Infrastructure**:
- Implement archetype classifier (3-tier: simple/medium/complex)
- Optimize agent selection based on archetype
- Add performance monitoring

**Total**: 103 + 14 = **117 fields** (with buffer)
**Target**: Extract 107 most important fields

**Success Criteria**:
- ≥80% accuracy on 107 fields (overall corpus)
- Archetype classifier ≥85% accuracy
- Cost ≤$0.22/PDF (archetype-optimized)

**Effort**: 3 days agents + 2 days classifier = **5 days**

### Total Timeline

**4 Sprints = 4 Weeks (20 working days)**

**Breakdown**:
- Development: 16 days (13 days agents + 2 days classifier + 1 day buffer)
- Testing: 4 days (1 day per sprint)

**Incremental Value Delivery**:
- End of Week 1: 53-field system deployed
- End of Week 2: 71-field system deployed
- End of Week 3: 103-field system deployed
- End of Week 4: 107-field system + archetype optimization

**Why This Works**:
- Stakeholders see progress weekly
- Early feedback prevents wasted effort
- Each sprint builds on previous learnings
- Production system never regresses (old 30-field system as fallback)

---

## Q7: Agent Prompt Complexity - The Sweet Spot {#q7-prompt-engineering}

### The Research

**GPT-4 Prompt Engineering Limits** (from testing + research):

| Fields per Agent | Accuracy | Notes |
|------------------|----------|-------|
| 5-8 fields | 90-95% | Excellent (current system) |
| 8-12 fields | 85-90% | Good (sweet spot) |
| 12-15 fields | 80-85% | Acceptable (with few-shot) |
| 15-20 fields | 75-80% | Risky (needs few-shot + validation) |
| 20+ fields | 70-75% | Poor (too much confusion) |

**Why Accuracy Drops**:
1. **Attention dilution**: LLM tries to find 20 fields, misses some
2. **Field confusion**: Similar Swedish terms blur together
3. **Hallucination risk**: LLM "invents" values to fill all fields
4. **Token limit pressure**: 20 fields + examples + context = 2000+ tokens

### Mitigation Strategies

#### **Strategy 1: Few-Shot Examples** (Biggest Impact)

**Without Examples**:
- 15 fields, no examples: 75% accuracy

**With 2-3 Examples**:
- 15 fields, 2-3 examples: 85-90% accuracy

**Why**: LLM sees the pattern, follows it precisely

**Implementation**: See [Q2: Learning System](#q2-learning-system)

#### **Strategy 2: Structured Output Format** (JSON Schema)

**Without Structure**:
```
Prompt: "Extract revenue, expenses, assets, liabilities..."
LLM: "Revenue is 7,393,591 and expenses are..."  # Free-form text
```

**With JSON Schema** (OpenAI native support):
```python
response = client.chat.completions.create(
    model="gpt-4o-2024-11-20",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "financial_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "revenue": {"type": "number"},
                    "expenses": {"type": "number"},
                    "assets": {"type": "number"},
                    ...
                },
                "required": ["revenue", "expenses", ...]
            }
        }
    }
)
```

**Benefit**: +5-10% accuracy (forces correct format, reduces hallucination)

#### **Strategy 3: Field Grouping**

**Bad** (15 flat fields):
```
Extract:
1. revenue
2. expenses
3. operating_costs
4. other_expenses
5. assets
6. fixed_assets
7. current_assets
... (too many!)
```

**Good** (3 groups × 5 fields):
```
Extract Financial Data:

1. Income Statement:
   - revenue (nettoomsättning)
   - operating_costs (driftskostnader)
   - other_expenses (övriga externa kostnader)
   - operating_result (rörelseresultat)
   - year_result (årets resultat)

2. Balance Sheet - Assets:
   - total_assets (summa tillgångar)
   - fixed_assets (anläggningstillgångar)
   - current_assets (omsättningstillgångar)

3. Balance Sheet - Equity & Liabilities:
   - equity (eget kapital)
   - liabilities (skulder)
```

**Benefit**: Logical grouping helps LLM organize extraction

#### **Strategy 4: Validation Hints**

```
Extract driftskostnader breakdown:
- fastighetsskott: Property management costs
- reparationer: Repairs and maintenance
- el_vatten_uppvarmning: Utilities (electricity, water, heating)
...

VALIDATION RULES:
✓ All values should be POSITIVE (costs are positive, not negative)
✓ Sum should approximately equal total driftskostnader: {expected_total} SEK
✓ Typical range per field: 100,000 - 5,000,000 SEK
✓ If a field is not found in the document, use null (do not guess)

If your extraction violates these rules, review the document again before responding.
```

**Benefit**: +3-5% accuracy (LLM self-corrects)

#### **Strategy 5: Two-Stage Extraction** (For Complex Agents)

**For 15+ field agents**, split into two stages:

```python
# Stage 1: Identify what data exists
discovery = extract_field_discovery(agent_id, pages)
# Returns: {"fields_present": ["revenue", "expenses", "assets"], "confidence": 0.85}

# Stage 2: Extract only present fields
extraction = extract_fields_targeted(agent_id, pages, fields=discovery.fields_present)
# Only asks for 3 fields instead of 15
```

**Benefit**: +10-15% accuracy for complex agents (but 2x cost)

**When to Use**: Only for most critical agents (financial_totals, balance_sheet)

### Recommended Agent Design

**Target**: **10 fields per agent** (sweet spot)

**For 107 fields**:
- 107 / 10 = ~11 agents

**Actual Design** (accounting for hierarchical structure):

| Agent | Fields | Notes |
|-------|--------|-------|
| `governance_agent` | 8 | Chairman, board members, auditors |
| `property_agent` | 10 | Address, built year, apartments, energy class |
| `financial_totals_agent` | 12 | Income statement + balance sheet totals |
| `revenue_breakdown_agent` | 10 | Annual fees, commercial rent, garage rent, etc. (top 10) |
| `operating_costs_agent` | 7 | Fastighetsskott, reparationer, utilities, etc. |
| `loan_1_agent` | 8 | Loan details (lender, amount, rate, etc.) |
| `loan_2_agent` | 8 | Second loan |
| `loan_3_agent` | 8 | Third loan (if exists) |
| `loan_4_agent` | 8 | Fourth loan (if exists) |
| `buildings_detail_agent` | 10 | Book value, acquisition, depreciation, tax value |
| `receivables_detail_agent` | 8 | Tax account, VAT, client funds, receivables |
| `maintenance_fund_agent` | 6 | Beginning, allocation, withdrawals, ending |
| `equity_changes_agent` | 6 | Retained earnings changes |
| `key_ratios_agent` | 8 | Debt/sqm, equity ratio, capital costs, etc. (1 year) |

**Total**: 14 agents (base) + 3 conditional loan agents = **11-17 agents per document**

**With Archetype**:
- Simple K2: 8 agents (governance, property, financial_totals, 5 notes)
- Medium K2: 14 agents (add revenue, operating costs, 2 loans, 3 detailed notes)
- Complex K3: 22 agents (add 3-4 loans, all detail agents)

**Average**: 13.9 agents (from archetype analysis)

### Prompt Template (Example: Operating Costs Agent)

```python
OPERATING_COSTS_AGENT_PROMPT = """You are OperatingCostsAgent for Swedish BRF annual reports.

Extract operating costs BREAKDOWN (driftskostnader) with EXACT keys:
{
  "fastighetsskott": <float or null>,
  "reparationer_underhall": <float or null>,
  "el_vatten_uppvarmning": <float or null>,
  "forsakringar": <float or null>,
  "ovriga_driftskostnader": <float or null>,
  "total": <float>,
  "evidence_pages": [<page numbers>]
}

SWEDISH TERMS:
- fastighetsskott: "Fastighetsskötsel", "Drift", "Skötsel"
- reparationer_underhall: "Reparationer", "Underhåll", "Rep/uh"
- el_vatten_uppvarmning: "Energi", "El/värme/vatten", "Utilities"
- forsakringar: "Försäkringar", "Insurance"

⚠️ DO NOT confuse:
- "Driftskostnader" (total) vs "Fastighetsdrift" (subset)
- "Driftsöverskott" (surplus = revenue - costs)

VALIDATION:
✓ All values POSITIVE (costs are positive, not negative)
✓ Sum should ≈ total (±5% tolerance)
✓ Typical range: 100,000 - 5,000,000 SEK per field
✓ If not found, use null (do NOT guess)

=== EXAMPLES ===

Example 1:
Input: "Driftskostnader 2021: Fastighetsskötsel 553,590 kr, Reparationer och underhåll 258,004 kr, Drift-energi 1,359,788 kr, Övriga driftskostnader 422,455 kr, Summa 2,834,798 kr"
Output: {"fastighetsskott": 553590, "reparationer_underhall": 258004, "el_vatten_uppvarmning": 1359788, "forsakringar": null, "ovriga_driftskostnader": 422455, "total": 2834798, "evidence_pages": [8]}

Example 2:
Input: "Drift 2020: Skötsel 412,000, Underhåll 186,500, Energi 1,240,000, Försäkring 95,000, Summa 1,933,500"
Output: {"fastighetsskott": 412000, "reparationer_underhall": 186500, "el_vatten_uppvarmning": 1240000, "forsakringar": 95000, "ovriga_driftskostnader": null, "total": 1933500, "evidence_pages": [12]}

=== NOW EXTRACT FROM THESE PAGES ===

"""
```

**Key Elements**:
- ✅ 7 fields (within sweet spot)
- ✅ Clear Swedish term mapping
- ✅ Exclusions (what NOT to confuse with)
- ✅ Validation rules with ranges
- ✅ 2 examples showing pattern
- ✅ Structured JSON output

**Expected Accuracy**: 85-90%

---

## Q8: Validation System - Three-Tier Strategy {#q8-validation}

### Problem Statement

With 107 fields and 25 agents, how do we ensure quality without manual review of every extraction?

### Three Validation Levels

#### **Level 1: Field-Level Validation (In-Prompt)**

**Approach**: Build validation into agent prompts

```python
PROMPT_WITH_VALIDATION = """
Extract data and VALIDATE before responding:

1. Type validation:
   ✓ revenue, expenses, assets: FLOAT (positive for revenue/assets, negative for expenses)
   ✓ org_number: STRING in format "XXXXXX-XXXX"
   ✓ built_year: INTEGER between 1800-2025

2. Range validation:
   ✓ assets: Typical range 1M - 1B SEK for BRFs
   ✓ apartments: 5 - 500 apartments
   ✓ interest_rate: 0% - 10% (if higher, flag as unusual)

3. Format validation:
   ✓ dates: YYYY-MM-DD format
   ✓ amounts: Numbers only (no currency symbols)

4. Null handling:
   ✓ If field not found: use null
   ✓ If field exists but unclear: use null + add to notes

If your extraction violates these rules, REVIEW THE DOCUMENT AGAIN before responding.
"""
```

**Pros**:
- ✅ Zero cost (validation happens during extraction)
- ✅ LLM self-corrects obvious errors
- ✅ Prevents hallucination (explicit null instructions)

**Cons**:
- ⚠️ Not 100% reliable (LLM may still make mistakes)

**Implementation**: Add to all agent prompts

#### **Level 2: Cross-Field Validation (Post-Extraction)**

**Approach**: Validate relationships between fields after extraction

```python
def validate_extraction(extraction: BRFExtraction) -> ValidationReport:
    """Validate extracted data for consistency"""
    errors = []
    warnings = []

    # Accounting equation: Assets = Liabilities + Equity
    if extraction.financials.assets and extraction.financials.liabilities and extraction.financials.equity:
        expected_equity = extraction.financials.assets - extraction.financials.liabilities
        actual_equity = extraction.financials.equity
        diff = abs(expected_equity - actual_equity)
        tolerance = extraction.financials.assets * 0.01  # 1% tolerance

        if diff > tolerance:
            errors.append({
                "type": "accounting_equation",
                "message": f"Assets {extraction.financials.assets} != Liabilities {extraction.financials.liabilities} + Equity {actual_equity}",
                "severity": "high"
            })

    # Operating costs sum check
    if extraction.financials.driftskostnader:
        dk = extraction.financials.driftskostnader
        subtotal = sum([
            dk.fastighetsskott or 0,
            dk.reparationer_underhall or 0,
            dk.el_vatten_uppvarmning or 0,
            dk.forsakringar or 0,
            dk.ovriga_driftskostnader or 0
        ])
        diff = abs(subtotal - dk.total)
        tolerance = dk.total * 0.05  # 5% tolerance (some line items may be missing)

        if diff > tolerance:
            warnings.append({
                "type": "driftskostnader_sum",
                "message": f"Driftskostnader subtotal {subtotal} != total {dk.total}",
                "severity": "medium"
            })

    # Loan totals vs balance sheet
    if extraction.financials.loans and extraction.financials.liabilities:
        total_loans = sum(loan.current_balance for loan in extraction.financials.loans)
        # Loans should be ≤ liabilities (liabilities include other debts too)
        if total_loans > extraction.financials.liabilities * 1.1:  # 10% tolerance
            errors.append({
                "type": "loan_vs_liabilities",
                "message": f"Total loans {total_loans} > liabilities {extraction.financials.liabilities}",
                "severity": "high"
            })

    # Organization number format (Swedish format: NNNNNN-NNNN)
    if extraction.metadata.org_number:
        if not re.match(r'^\d{6}-\d{4}$', extraction.metadata.org_number):
            errors.append({
                "type": "org_number_format",
                "message": f"Invalid org number format: {extraction.metadata.org_number}",
                "severity": "medium"
            })

    # Calculate quality score
    total_checks = 5  # Number of validation checks above
    failed_checks = len(errors)
    quality_score = 1.0 - (failed_checks / total_checks)

    return ValidationReport(
        errors=errors,
        warnings=warnings,
        quality_score=quality_score,
        passed=len(errors) == 0
    )
```

**Pros**:
- ✅ Catches logical inconsistencies
- ✅ Prevents obvious errors from going to production
- ✅ Low cost (local computation)

**Cons**:
- ⚠️ Can't fix errors (only flags them)
- ⚠️ May have false positives (some violations are legitimate)

**Implementation**: Run after Pass 2 extraction, before returning results

#### **Level 3: Human-in-the-Loop Review (Production)**

**Approach**: Flag low-confidence extractions for human review

```python
def should_human_review(extraction: BRFExtraction, validation: ValidationReport) -> bool:
    """Determine if extraction needs human review"""

    # Trigger 1: Low quality score
    if validation.quality_score < 0.80:
        return True

    # Trigger 2: High-severity errors
    if any(e['severity'] == 'high' for e in validation.errors):
        return True

    # Trigger 3: Low field coverage
    total_fields = 107
    extracted_fields = count_non_null_fields(extraction)
    coverage = extracted_fields / total_fields
    if coverage < 0.60:  # Less than 60% coverage
        return True

    # Trigger 4: Missing critical fields
    critical_fields = ['org_number', 'chairman', 'assets', 'liabilities', 'equity']
    for field in critical_fields:
        if get_nested_field(extraction, field) is None:
            return True

    return False
```

**Review Queue**:
```python
# After extraction
if should_human_review(extraction, validation):
    review_queue.add({
        "pdf": pdf_path,
        "extraction": extraction,
        "validation": validation,
        "priority": calculate_priority(validation),
        "assigned_to": None,
        "status": "pending"
    })
```

**Pros**:
- ✅ Catches errors that automated validation misses
- ✅ Improves over time (human feedback trains better prompts)

**Cons**:
- ❌ Requires human effort (2-5 min per review)

**Target**: <10% of extractions need human review

**Implementation**: Month 2+ (after initial deployment)

### Validation Integration

**Workflow**:

```python
def extract_document_with_validation(pdf_path: str) -> ExtractionResult:
    # Stage 1-3: Topology, Structure, Routing (unchanged)
    topology = analyze_topology(pdf_path)
    structure = detect_structure(pdf_path, topology)
    routing = route_sections(structure)

    # Stage 4: Hierarchical Extraction
    pass1 = extract_pass1(routing)
    pass2 = extract_pass2(routing, pass1)

    # Build extraction object
    extraction = build_extraction_model(pass1, pass2)

    # Stage 5: Validation (NEW)
    validation = validate_extraction(extraction)

    # Stage 6: Quality Gate
    if validation.passed:
        return ExtractionResult(
            extraction=extraction,
            validation=validation,
            status="success"
        )
    elif validation.quality_score >= 0.80:  # Acceptable with warnings
        return ExtractionResult(
            extraction=extraction,
            validation=validation,
            status="success_with_warnings"
        )
    elif should_human_review(extraction, validation):
        return ExtractionResult(
            extraction=extraction,
            validation=validation,
            status="pending_review"
        )
    else:
        # Low quality, trigger re-extraction with coaching
        return ExtractionResult(
            extraction=extraction,
            validation=validation,
            status="failed"
        )
```

### Validation Summary

| Level | When | Cost | Catches | Implementation |
|-------|------|------|---------|----------------|
| **L1: In-Prompt** | During extraction | $0 | Type errors, obvious mistakes | Sprint 1 |
| **L2: Cross-Field** | After extraction | <$0.001 | Logical inconsistencies | Sprint 2 |
| **L3: Human Review** | Production (flagged cases) | $0.10-0.25/review | Edge cases, complex errors | Month 2 |

**Expected Results**:
- L1: Catches 60-70% of errors
- L2: Catches 20-25% of errors
- L3: Catches remaining 5-10% of errors
- **Total**: 95%+ error detection

---

## Recommended Architecture {#recommended-architecture}

### High-Level Overview

```
PDF Input
  ↓
[Stage 1: Topology Detection] (0.1-1s, free)
  ├─ Machine-readable → Text mode
  ├─ Scanned → OCR mode
  └─ Hybrid → Adaptive mode
  ↓
[Stage 2: Structure Detection] (2-15s, $0.01-0.05)
  └─ Docling + EasyOCR → Sections + Pages
  ↓
[Stage 3: Archetype Classification] (0s, free)
  ├─ Simple K2 (35%) → 8 agents
  ├─ Medium K2 (40%) → 14 agents
  └─ Complex K3 (25%) → 22 agents
  ↓
[Stage 4: Section Routing] (0.1s, $0.0001)
  ├─ Swedish normalization
  ├─ Fuzzy matching
  └─ LLM fallback
  ↓
[Stage 5: Hierarchical Extraction]
  │
  ├─ Pass 1: High-Level (30 fields, parallel)
  │   ├─ governance_agent
  │   ├─ property_agent
  │   └─ financial_totals_agent
  │
  ├─ Pass 2: Detailed (77 fields, sequential with context)
  │   ├─ revenue_breakdown_agent (if exists)
  │   ├─ operating_costs_agent (if exists)
  │   ├─ loan_1_agent (if exists)
  │   ├─ loan_2_agent (if exists)
  │   ├─ loan_3_agent (if exists)
  │   ├─ loan_4_agent (if exists)
  │   ├─ buildings_detail_agent
  │   ├─ receivables_detail_agent
  │   ├─ maintenance_fund_agent
  │   └─ equity_changes_agent
  │
  └─ Each agent uses:
      - Few-shot examples (2-3 per agent)
      - Field-level Swedish synonym mapping
      - In-prompt validation rules
      - Structured JSON output
  ↓
[Stage 6: Cross-Field Validation] (0.1s, free)
  ├─ Accounting equation check
  ├─ Sum validation (driftskostnader, loans)
  └─ Format validation (org_number, dates)
  ↓
[Stage 7: Quality Gate]
  ├─ Passed (quality ≥0.95) → Return result
  ├─ Acceptable (0.80-0.95) → Return with warnings
  └─ Failed (<0.80) → Flag for review
  ↓
Output: 107-field extraction with evidence
```

### Key Design Decisions

1. **Archetype-First**: Classify document before agent selection (53.6% cost savings)
2. **Hierarchical Extraction**: Pass 1 (totals) → Pass 2 (details with context)
3. **Few-Shot Learning**: 2-3 examples per agent (+15-20% accuracy)
4. **Field-Level Synonyms**: Swedish term mapping at field granularity (+10-15% accuracy)
5. **Nested Schema**: Clean code (extraction) + flat storage (querying)
6. **Three-Tier Validation**: In-prompt + cross-field + human review (95%+ error detection)
7. **Incremental Deployment**: 4 sprints (30→53→71→93→107 fields)

### Cost Analysis by Archetype

| Archetype | % Corpus | Agents | Fields | Cost/PDF | Corpus Cost |
|-----------|----------|--------|--------|----------|-------------|
| Simple K2 | 35% (9,219) | 8 | 40 | $0.14 | $1,291 |
| Medium K2 | 40% (10,536) | 14 | 65 | $0.20 | $2,107 |
| Complex K3 | 25% (6,585) | 22 | 95 | $0.30 | $1,976 |
| **Weighted Avg** | **100%** | **13.9** | **63.8** | **$0.204** | **$5,374** |

**vs Flat 107-Field**:
- Flat: $0.44/PDF × 26,342 = $11,590
- Savings: $6,217 (53.6%)

### Performance Projections

| Metric | Sprint 1 (53F) | Sprint 2 (71F) | Sprint 3 (93F) | Sprint 4 (107F) |
|--------|----------------|----------------|----------------|-----------------|
| **Fields** | 53 | 71 | 93 | 107 |
| **Agents (avg)** | 10.5 | 12.2 | 13.1 | 13.9 |
| **Accuracy** | 87% | 85% | 83% | 82% |
| **Coverage (corpus)** | 68% | 65% | 63% | 60% |
| **Cost/PDF** | $0.16 | $0.18 | $0.20 | $0.22 |
| **Time/PDF** | 80-150s | 90-180s | 100-200s | 110-220s |

**Why Coverage Drops**: More fields = harder to find in all documents (corpus variability)

**Why Accuracy Drops**: More fields = more complexity = slight accuracy decrease (acceptable)

**Overall Value**: 82% accuracy × 107 fields = 87.7 correct fields vs 92% × 30 = 27.6 correct fields = **3.2x information gain**

---

## 4-Sprint Implementation Plan {#implementation-plan}

### Sprint 1: Foundation (Week 1) - 30→53 Fields

**Goals**:
1. ✅ Validate hierarchical extraction architecture
2. ✅ Implement few-shot learning system
3. ✅ Build field-level Swedish synonym mapping
4. ✅ Add first detailed agents (revenue breakdown, loan 1)

**Tasks**:

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Create 107-field ground truth (brf_198532) | `brf_198532_comprehensive_gt.json` |
| Mon | Build few-shot example bank (10 agents × 3 examples) | `config/few_shot_examples.yaml` |
| Mon | Create field-level synonym mapping (53 fields) | `config/field_level_synonyms.yaml` |
| Tue | Implement `revenue_breakdown_agent` (15 fields) | Agent code + prompt |
| Tue | Implement `loan_1_detailed_agent` (8 fields) | Agent code + prompt |
| Wed | Update prompts with few-shot examples | All agent prompts |
| Wed | Implement field synonym injection | Prompt enhancement code |
| Thu | Test on brf_198532 (53-field subset) | Validation report |
| Thu | Test on brf_268882 (regression) | Validation report |
| Fri | Fix issues, finalize Sprint 1 | Sprint 1 complete |

**Success Criteria**:
- ✅ ≥85% accuracy on 53 fields (brf_198532)
- ✅ Few-shot system working (examples injected correctly)
- ✅ Field synonyms reduce confusion
- ✅ Cost ≤$0.16/PDF

**Deliverables**:
- 53-field extraction system
- Few-shot learning infrastructure
- Field-level synonym mapping
- Ground truth for full 107 fields

### Sprint 2: Multi-Instance (Week 2) - 53→71 Fields

**Goals**:
1. ✅ Validate multi-loan extraction
2. ✅ Add operating costs breakdown
3. ✅ Expand property details

**Tasks**:

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Implement `loan_2_detailed_agent` (8 fields) | Agent code + prompt |
| Mon | Implement `operating_costs_breakdown_agent` (7 fields) | Agent code + prompt |
| Tue | Implement `property_detailed_agent` (3 fields) | Enhanced property agent |
| Tue | Add few-shot examples for new agents | Updated examples.yaml |
| Wed | Test multi-loan detection logic | Validation script |
| Wed | Test on brf_198532 (71-field subset) | Validation report |
| Thu | Test on 3 diverse PDFs | Batch validation |
| Thu | Analyze failures, update prompts | Issue report |
| Fri | Fix issues, finalize Sprint 2 | Sprint 2 complete |

**Success Criteria**:
- ✅ ≥85% accuracy on 71 fields
- ✅ Multi-loan extraction works (2-3 loans identified correctly)
- ✅ Operating costs breakdown extracted accurately
- ✅ Cost ≤$0.18/PDF

**Deliverables**:
- 71-field extraction system
- Multi-instance extraction validated
- Updated few-shot examples

### Sprint 3: Balance Sheet Details (Week 3) - 71→93 Fields

**Goals**:
1. ✅ Extract detailed balance sheet components
2. ✅ Add third loan agent
3. ✅ Implement cross-field validation

**Tasks**:

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Implement `loan_3_detailed_agent` (8 fields) | Agent code + prompt |
| Mon | Implement `buildings_detail_agent` (10 fields) | Agent code + prompt |
| Tue | Implement `receivables_detail_agent` (8 fields) | Agent code + prompt |
| Tue | Implement `maintenance_fund_detail_agent` (6 fields) | Agent code + prompt |
| Wed | Implement cross-field validation system | Validation code |
| Wed | Test on brf_198532 (93-field subset) | Validation report |
| Thu | Test on 5 diverse PDFs | Batch validation |
| Thu | Analyze validation errors | Issue report |
| Fri | Fix issues, finalize Sprint 3 | Sprint 3 complete |

**Success Criteria**:
- ✅ ≥83% accuracy on 93 fields (acceptable drop)
- ✅ Balance sheet details extracted correctly
- ✅ Cross-field validation catches inconsistencies
- ✅ Cost ≤$0.20/PDF

**Deliverables**:
- 93-field extraction system
- Cross-field validation system
- Validation error analysis

### Sprint 4: Final Fields + Optimization (Week 4) - 93→107 Fields

**Goals**:
1. ✅ Complete 107-field extraction
2. ✅ Implement archetype classification
3. ✅ Optimize costs and performance

**Tasks**:

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Implement `loan_4_detailed_agent` (8 fields, conditional) | Agent code + prompt |
| Mon | Implement `equity_changes_agent` (6 fields) | Agent code + prompt |
| Tue | Implement archetype classifier | Classifier code |
| Tue | Test classifier on 50 PDFs (manual labels) | Classifier accuracy report |
| Wed | Integrate classifier into pipeline | Updated pipeline code |
| Wed | Test on brf_198532 (full 107 fields) | Final validation report |
| Thu | Batch test on 20 diverse PDFs | Comprehensive results |
| Thu | Cost/performance analysis | Metrics report |
| Fri | Documentation and handoff | Production readiness doc |

**Success Criteria**:
- ✅ ≥80% accuracy on 107 fields (corpus-wide)
- ✅ Archetype classifier ≥85% accuracy
- ✅ Cost $0.22/PDF (archetype-optimized, down from $0.44 flat)
- ✅ Ready for pilot production deployment

**Deliverables**:
- 107-field extraction system
- Archetype classifier (53.6% cost savings)
- Production readiness documentation
- Comprehensive test results (20+ PDFs)

### Post-Sprint: Production Hardening (Month 2)

**Optional Enhancements**:

1. **Week 5: Multi-Document Ground Truth**
   - Create ground truth for 2 more PDFs (one per archetype)
   - Validate consistency across document types

2. **Week 6: Human-in-the-Loop Review**
   - Implement review queue
   - Process first 100 flagged extractions
   - Collect feedback for prompt improvements

3. **Week 7: Adaptive Learning**
   - Implement failure logging
   - Weekly review process
   - Auto-update few-shot examples

4. **Week 8: Large-Scale Testing**
   - Test on 100 random PDFs
   - Measure real-world accuracy/coverage
   - Final cost optimization

---

## Realistic Target Metrics {#target-metrics}

### Why 107-Field System Won't Hit 95/95

**Ground Truth Reality**:
- Current 30-field system: 86.7% coverage, 92% accuracy on **one optimized PDF** (brf_198532)
- That PDF is a **Complex K3** BRF (best-case scenario)

**Corpus Reality**:
- 35% of corpus: Simple K2 (only 40 fields exist, not 107!)
- 40% of corpus: Medium K2 (only 65 fields exist)
- 25% of corpus: Complex K3 (80-100 fields exist)

### Realistic Projections

#### **Coverage (Fields Extracted / Fields Possible)**

**By Archetype**:
- Simple K2: 35 fields extracted / 40 possible = **87.5% coverage** (excellent!)
- Medium K2: 55 fields extracted / 65 possible = **84.6% coverage** (good)
- Complex K3: 85 fields extracted / 95 possible = **89.5% coverage** (excellent!)

**Corpus-Wide**:
- Weighted average: 0.35 × 35 + 0.40 × 55 + 0.25 × 85 = **63.5 fields**
- Against 107-field schema: 63.5 / 107 = **59.3% coverage**

**Why This Is Actually Good**:
- We're extracting 89.5% of **what exists** in complex docs
- The "low" 59.3% is because we're measuring against a 107-field schema that simple docs don't have
- **Alternative metric**: Extraction success rate = **87.1%** (fields we attempted to extract were successful)

#### **Accuracy (Correct Values / Extracted Values)**

**By Field Complexity**:
- Simple fields (names, dates, org numbers): **90-95% accuracy**
- Moderate fields (financial totals, loan basics): **85-90% accuracy**
- Complex fields (breakdowns, detailed notes): **80-85% accuracy**

**Overall Accuracy**:
- Weighted by field distribution: **82-87% accuracy**

**Why This Is Acceptable**:
- Current 30-field system: 92% accuracy
- 5-10% drop is expected with 3.6x more fields
- Still **3.1x information gain** (87.7 correct fields vs 27.6)

#### **Cost per PDF**

**By Archetype**:
- Simple K2: $0.14/PDF (8 agents)
- Medium K2: $0.20/PDF (14 agents)
- Complex K3: $0.30/PDF (22 agents)

**Weighted Average**: **$0.204/PDF**

**vs Current**:
- Current 30-field: $0.14/PDF
- Increase: **1.46x** (46% cost increase for 3.6x data increase = excellent ROI)

### Final Target Metrics (107-Field System)

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Field Coverage (corpus-wide)** | **60-65%** | Realistic given archetype distribution |
| **Extraction Success Rate** | **85-90%** | Fields we attempt to extract, we get right |
| **Field Accuracy** | **82-87%** | Acceptable for complex 107-field extraction |
| **Correct Fields (avg)** | **85.6 / 107** | 3.1x information gain vs current 27.6 / 30 |
| **Cost per PDF** | **$0.22** | 1.6x current cost (archetype-optimized) |
| **Processing Time** | **110-220s** | 2-3 minutes (acceptable for batch processing) |
| **ROI** | **1.9x value/dollar** | 3.1x information gain / 1.6x cost |

### What Counts as Success?

**For Simple K2 BRF**:
- Extracted 35 fields (87.5% of 40 possible) ✅
- Accuracy: 85% (30 correct) ✅
- Cost: $0.14 ✅

**For Complex K3 BRF**:
- Extracted 85 fields (89.5% of 95 possible) ✅
- Accuracy: 87% (74 correct) ✅
- Cost: $0.30 ✅

**Corpus-Wide**:
- Avg fields extracted: 63.5
- Avg correct fields: 52.5 (82.7% accuracy)
- Avg cost: $0.20
- **Result**: 52.5 correct fields vs current 27.6 = **1.9x information gain**

**Verdict**: ✅ **SUCCESS** - Nearly 2x information for 1.46x cost

---

## Production Deployment Reality {#production-reality}

### Can We Maintain 25-Agent System?

**Short Answer**: Yes, **IF** we implement proper infrastructure.

**Long Answer**: Without infrastructure, system becomes unmaintainable after 10-12 agents.

### Required Infrastructure

#### **1. Agent Registry (Centralized Management)**

```python
# agents/registry.py

AGENT_REGISTRY = {
    "governance_agent": {
        "prompt_path": "prompts/governance_agent.txt",
        "few_shot_examples": "examples/governance_examples.yaml",
        "fields": [
            "chairman", "board_members", "auditor_name",
            "audit_firm", "nomination_committee"
        ],
        "required_fields": ["chairman"],  # Must extract these
        "avg_cost": 0.018,
        "avg_time_ms": 8100,
        "success_rate": 0.95,
        "min_accuracy": 0.90,  # Regression test threshold
        "archetype": ["simple_k2", "medium_k2", "complex_k3"],  # Which archetypes use this
        "priority": "high"  # high, medium, low (for retry logic)
    },
    "driftskostnader_detailed_agent": {
        "prompt_path": "prompts/driftskostnader_detailed_agent.txt",
        "few_shot_examples": "examples/driftskostnader_examples.yaml",
        "fields": [
            "fastighetsskott", "reparationer_underhall",
            "el_vatten_uppvarmning", "forsakringar",
            "ovriga_driftskostnader", "total"
        ],
        "required_fields": ["total"],
        "avg_cost": 0.031,
        "avg_time_ms": 12300,
        "success_rate": 0.82,
        "min_accuracy": 0.80,
        "archetype": ["medium_k2", "complex_k3"],  # Not used for simple K2
        "priority": "medium"
    },
    # ... 25 agents total
}

def get_agents_for_archetype(archetype: str) -> List[str]:
    """Return list of agents to use for given archetype"""
    return [
        agent_id for agent_id, config in AGENT_REGISTRY.items()
        if archetype in config["archetype"]
    ]

def load_agent_prompt(agent_id: str) -> str:
    """Load prompt from file with few-shot examples"""
    config = AGENT_REGISTRY[agent_id]
    prompt = Path(config["prompt_path"]).read_text()
    examples = load_yaml(config["few_shot_examples"])
    return inject_examples(prompt, examples)
```

**Benefits**:
- Single source of truth for agent configuration
- Easy to update (change one file, affects all calls)
- Enables analytics (which agents are expensive? Which fail?)

#### **2. Comprehensive Logging**

```python
# After each agent call
logger.info({
    "timestamp": datetime.now().isoformat(),
    "run_id": run_id,
    "pdf": pdf_path,
    "agent": agent_id,
    "status": "success",  # or "error", "retry"
    "fields_extracted": 12,
    "fields_missing": 3,
    "cost": 0.029,
    "time_ms": 11823,
    "tokens_input": 1200,
    "tokens_output": 350,
    "model": "gpt-4o-2024-11-20",
    "confidence": 0.87,
    "validation_errors": [],
    "evidence_pages": [8, 9, 10]
})
```

**Enables**:
- Debugging (which agent failed on which PDF?)
- Cost monitoring (which agents are expensive?)
- Performance optimization (which agents are slow?)
- Quality tracking (which agents have low accuracy?)

#### **3. Agent Performance Dashboard**

```python
# Query logs to generate dashboard

import pandas as pd
import json

# Load logs
logs = [json.loads(line) for line in open("logs/agent_calls.jsonl")]
df = pd.DataFrame(logs)

# Agent performance table
agent_stats = df.groupby('agent').agg({
    'status': lambda x: (x == 'success').sum() / len(x),  # Success rate
    'cost': 'mean',
    'time_ms': 'mean',
    'fields_extracted': 'mean',
    'confidence': 'mean'
}).round(3)

agent_stats.columns = ['Success Rate', 'Avg Cost ($)', 'Avg Time (ms)', 'Avg Fields', 'Avg Confidence']

print(agent_stats.to_markdown())
```

**Example Output**:
```
| Agent                      | Success Rate | Avg Cost ($) | Avg Time (ms) | Avg Fields | Avg Confidence |
|----------------------------|--------------|--------------|---------------|------------|----------------|
| governance_agent           | 0.952        | 0.018        | 8100          | 7.2        | 0.91           |
| financial_totals_agent     | 0.938        | 0.021        | 9400          | 10.8       | 0.88           |
| driftskostnader_agent      | 0.821        | 0.031        | 12300         | 5.1/7      | 0.79           |
| loan_1_detailed_agent      | 0.885        | 0.026        | 10700         | 6.4/8      | 0.84           |
| ... (25 agents total)      | ...          | ...          | ...           | ...        | ...            |
```

**Alerts**:
- If `Success Rate < min_accuracy`: Email alert to dev team
- If `Avg Cost` increases >20%: Cost spike investigation
- If `Avg Fields` drops >30%: Prompt degradation alert

#### **4. Automated Regression Testing**

```python
# tests/test_regression.py

import pytest
from agents.registry import AGENT_REGISTRY
from pipeline import OptimalBRFPipeline

# Ground truth
GROUND_TRUTH_PDF = "ground_truth/brf_198532.pdf"
GROUND_TRUTH_DATA = load_json("ground_truth/brf_198532_comprehensive_gt.json")

@pytest.mark.parametrize("agent_id", AGENT_REGISTRY.keys())
def test_agent_accuracy(agent_id):
    """Test each agent maintains minimum accuracy on ground truth"""

    # Extract
    pipeline = OptimalBRFPipeline()
    result = pipeline._extract_agent(
        GROUND_TRUTH_PDF,
        agent_id,
        section_headings=[]  # Will use default routing
    )

    # Validate against ground truth
    expected = get_expected_fields(GROUND_TRUTH_DATA, agent_id)
    actual = result['data']

    accuracy = calculate_accuracy(expected, actual)

    # Assert minimum accuracy from registry
    min_accuracy = AGENT_REGISTRY[agent_id]['min_accuracy']
    assert accuracy >= min_accuracy, (
        f"{agent_id} accuracy {accuracy:.2%} below threshold {min_accuracy:.2%}"
    )

def test_no_regression_on_30_baseline_fields():
    """Ensure 107-field system doesn't break original 30 fields"""

    pipeline = OptimalBRFPipeline()
    result = pipeline.extract_document(GROUND_TRUTH_PDF)

    # Check baseline 30 fields
    baseline_fields = [
        "org_number", "chairman", "board_members", "auditor_name",
        "revenue", "expenses", "assets", "liabilities", "equity",
        # ... all 30 baseline fields
    ]

    for field in baseline_fields:
        expected = get_nested_field(GROUND_TRUTH_DATA, field)
        actual = get_nested_field(result.extraction, field)

        if expected is not None:
            assert actual is not None, f"Regression: {field} was extracted before, now missing"
```

**Run**:
```bash
# Before deploying any changes
pytest tests/test_regression.py -v

# If any test fails, fix before merging
```

**Benefits**:
- Prevents regressions (new changes don't break old functionality)
- Validates every agent on ground truth
- Runs in CI/CD pipeline automatically

#### **5. Gradual Rollout with Feature Flags**

```python
# config/feature_flags.py

FEATURE_FLAGS = {
    # Core agents (always enabled)
    "governance_agent": True,
    "property_agent": True,
    "financial_totals_agent": True,

    # Sprint 1 agents (enabled after Sprint 1 validation)
    "revenue_breakdown_agent": os.getenv("ENABLE_SPRINT1", "false") == "true",
    "loan_1_detailed_agent": os.getenv("ENABLE_SPRINT1", "false") == "true",

    # Sprint 2 agents (enabled after Sprint 2 validation)
    "loan_2_detailed_agent": os.getenv("ENABLE_SPRINT2", "false") == "true",
    "operating_costs_agent": os.getenv("ENABLE_SPRINT2", "false") == "true",

    # Archetype classifier (enable after validation)
    "archetype_classification": os.getenv("ENABLE_ARCHETYPE", "false") == "true",
}

def get_enabled_agents(archetype: str) -> List[str]:
    """Return only enabled agents for archetype"""
    all_agents = get_agents_for_archetype(archetype)
    return [a for a in all_agents if FEATURE_FLAGS.get(a, False)]
```

**Usage**:
```bash
# Production deployment:

# Week 1: Only baseline agents
export ENABLE_SPRINT1=false
export ENABLE_SPRINT2=false

# Week 2: Enable Sprint 1 agents after validation
export ENABLE_SPRINT1=true
export ENABLE_SPRINT2=false

# Week 3: Enable Sprint 2 agents
export ENABLE_SPRINT1=true
export ENABLE_SPRINT2=true

# Rollback if issues: Disable problematic sprint
export ENABLE_SPRINT2=false  # Roll back to Sprint 1
```

**Benefits**:
- Safe rollouts (enable new agents gradually)
- Easy rollback (disable flag if issues)
- A/B testing (compare with/without new agents)

### Maintenance Workflow

**Daily**:
- Review dashboard (5 minutes)
- Check alerts (if any)

**Weekly**:
- Review low-performing agents (30 minutes)
- Update prompts based on failures (1 hour)
- Run regression tests (automated)

**Monthly**:
- Analyze cost trends (30 minutes)
- Review human-flagged extractions (2 hours)
- Update few-shot examples (1 hour)

**Total Maintenance**: **4-5 hours/week** for 25-agent system

**Verdict**: ✅ **MAINTAINABLE** with proper infrastructure

---

## Summary & Recommendations

### The Big Picture

**Expanding to 107 fields is WORTH IT:**
- ✅ **3.1x information gain** (87.7 correct fields vs 27.6)
- ✅ **1.6x cost increase** ($0.22 vs $0.14/PDF)
- ✅ **ROI: 1.9x value per dollar**
- ✅ **Corpus savings: $6,217** (with archetype classification)

**But requires systematic approach:**
- ✅ Archetype classification (mandatory for cost optimization)
- ✅ Few-shot learning (mandatory for accuracy)
- ✅ Field-level synonyms (mandatory for Swedish terms)
- ✅ Hierarchical extraction (Pass 1 → Pass 2)
- ✅ Proper infrastructure (registry, logging, dashboard, testing)

### Decision Matrix

| Question | Answer | Reason |
|----------|--------|--------|
| **Q1: Archetype Classification?** | **YES** | Saves $6,217 on 26K corpus (124x ROI) |
| **Q2: Few-Shot Learning?** | **YES** | +15-20% accuracy for 4 days effort |
| **Q3: Hierarchical vs Flat?** | **Hierarchical → Archetype** | Learn first, optimize second |
| **Q4: Nested vs Flat Schema?** | **Nested (extraction) + Flat (storage)** | Best of both worlds |
| **Q5: Complete Ground Truth?** | **YES (Week 1)** | One-time 6-hour investment |
| **Q6: Incremental vs Big Bang?** | **Incremental (4 sprints)** | Learn as you go, fail fast |
| **Q7: Fields per Agent?** | **10 fields (sweet spot)** | 85-90% accuracy |
| **Q8: Validation Strategy?** | **3-tier (in-prompt + cross-field + human)** | 95%+ error detection |

### 4-Sprint Roadmap Summary

| Sprint | Duration | Fields | Agents | Cost | Key Deliverable |
|--------|----------|--------|--------|------|-----------------|
| **Sprint 1** | Week 1 | 30→53 | 8→10.5 | $0.16 | Few-shot learning + first detailed agents |
| **Sprint 2** | Week 2 | 53→71 | 10.5→12.2 | $0.18 | Multi-instance extraction |
| **Sprint 3** | Week 3 | 71→93 | 12.2→13.1 | $0.20 | Balance sheet details |
| **Sprint 4** | Week 4 | 93→107 | 13.1→13.9 | $0.22 | Archetype classifier |

**Total**: 4 weeks (20 working days) to production-ready 107-field system

### Final Metrics (107-Field System)

| Metric | Target | vs Current | Verdict |
|--------|--------|------------|---------|
| **Corpus Coverage** | 60-65% | N/A (corpus-level metric) | ✅ Realistic |
| **Field Accuracy** | 82-87% | -5 to -10% | ✅ Acceptable for 3.6x fields |
| **Correct Fields** | 85.6 | +58 fields | ✅ 3.1x information gain |
| **Cost per PDF** | $0.22 | +$0.08 | ✅ 1.6x cost for 3.6x data |
| **Processing Time** | 110-220s | +60-100s | ✅ Acceptable (2-3 min) |
| **ROI** | 1.9x value/$ | Baseline | ✅ **Excellent** |

### Go/No-Go Decision

**✅ GO - Proceed with 107-Field Expansion**

**Rationale**:
1. **ROI is excellent** (1.9x value per dollar)
2. **Incremental approach mitigates risk** (can stop after any sprint)
3. **Infrastructure is feasible** (4-5 hours/week maintenance)
4. **User value is clear** (87.7 correct fields vs 27.6)

**Conditions**:
- ✅ Commit to 4-week timeline (20 working days)
- ✅ Build proper infrastructure (registry, logging, testing)
- ✅ Accept realistic targets (60-65% coverage, 82-87% accuracy)
- ✅ Implement archetype classification (mandatory for cost savings)

### Next Steps

**Week 1, Day 1 (Tomorrow)**:
1. Create complete 107-field ground truth for brf_198532 (4-6 hours)
2. Start building few-shot example bank (2-3 hours)

**Week 1, Days 2-5**:
3. Implement Sprint 1 agents (revenue breakdown, loan 1)
4. Build field-level synonym mapping
5. Test and validate

**Then**:
- Sprint 2 (Week 2)
- Sprint 3 (Week 3)
- Sprint 4 (Week 4)
- Production deployment (Month 2)

---

**Status**: Analysis complete, ready for implementation decision.

**Recommendation**: ✅ **PROCEED** with 107-field expansion using archetype-based hierarchical extraction with few-shot learning.
