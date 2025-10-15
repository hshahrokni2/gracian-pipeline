# Consensus Ground Truth Strategy: Synthesis of Two Approaches

**Date**: October 15, 2025
**Status**: 🤝 **STRATEGIC CONVERGENCE**
**Authors**: Claude (validation framework) + Claudia (learning-based strategy)

---

## 🎯 The Core Insight (AGREED)

**Both of us independently identified THE fundamental problem:**

- **Claudia's angle**: "Heterogeneity is the challenge - note numbers are arbitrary, content is not"
- **My angle**: "Agent success ≠ field accuracy - current '80%' metric is meaningless"

**Synthesis**: These are two perspectives on the same truth:
- Current rigid approach fails because documents vary wildly (Claudia)
- Current metrics hide this failure by measuring wrong thing (Me)

**We both concluded**: Need perfect ground truth to measure real extraction quality at field level.

---

## 📊 Approach Comparison

### Claudia's Learning-Based Strategy

**Core Method**:
1. Start with 200 PDFs from 3 priority districts (Hjorthagen, Norra Djurgårdsstaden, Hammarby Sjöstad)
2. Claude extracts ALL fields with confidence scores
3. Flag fields with confidence <95% for human review (~5 per PDF)
4. Human validates only flagged uncertainties
5. Iterative learning: 40 cycles with prompt versioning and efficacy tracking
6. Content-based specialists (NOT note-number based routing)

**Strengths**:
- ✅ Scales to 200 PDFs efficiently (40h human time vs 400h manual)
- ✅ Business-aligned (starts with priority districts)
- ✅ Systematic learning (prompt efficacy database persists)
- ✅ Adaptive to heterogeneity (learns from real variation)
- ✅ Content-based routing (more robust than structure-based)

**Timeline**: 9 weeks to production deployment on 26,800 PDFs

---

### My Validation Framework Strategy

**Core Method**:
1. Manual annotation of 3-10 PDFs (one per type: machine-readable, scanned, hybrid)
2. Record TRUE values from PDF inspection
3. Field-level validation with tolerances (fuzzy 85% for strings, ±1% for numbers)
4. P1/P2/P3 priority classification (critical/important/nice-to-have)
5. Validate extraction results against ground truth at FIELD level
6. Expose measurement flaw: "80%" means agents ran, not fields correct

**Strengths**:
- ✅ Rigorous measurement (field-level, not agent-level)
- ✅ Priority-driven (focus on critical fields first)
- ✅ Validation tolerances (realistic matching logic)
- ✅ Exposes false positives (10/10 agents ≠ 100% coverage)
- ✅ Foundation for improvement (know exactly which fields fail)

**Timeline**: Manual annotation bottleneck (2h per PDF × 10 = 20h for seeds)

---

## 🔄 Where We Diverge (Opportunities for Synthesis)

### 1. Ground Truth Creation Method

**Claudia**: Automated extraction with confidence scoring
**Me**: Manual annotation from scratch

**Synthesis** ✅:
- Use my approach for **3 seed PDFs** (one per type) → Establishes rigorous baseline
- Use Claudia's approach for **197 expansion PDFs** → Scales efficiently with targeted validation
- Result: Best of both worlds (rigor + scale)

---

### 2. Validation Methodology

**Claudia**: Implicit (compare to ground truth, track in efficacy DB)
**Me**: Explicit field-level validator with tolerance logic

**Synthesis** ✅:
- Build my `validate_field_accuracy.py` script
- Integrate with Claudia's efficacy tracking database
- Add columns: `field_accuracy_pct`, `p1_accuracy_pct`, `p2_accuracy_pct`, `p3_accuracy_pct`
- Result: Rigorous measurement + systematic learning

---

### 3. Agent Architecture

**Claudia**: Content-based specialists (12-15 agents)
**Me**: Current note-based agents (13 agents)

**Synthesis** ✅:
- Adopt Claudia's content-based routing (superior for heterogeneous documents)
- Keep my P1/P2/P3 priority classification within each specialist
- Migrate from: `notes_loans_agent` (assumes Note 7 structure)
- Migrate to: `loans_specialist_agent` (finds loans wherever they appear)
- Result: Robust routing + focused extraction

---

### 4. Learning Mechanism

**Claudia**: 40 iterative cycles with prompt versioning
**Me**: Use ground truth to identify gaps

**Synthesis** ✅:
- Claudia's 40 cycles provide systematic improvement
- My field-level validator provides precise gap identification
- Each cycle:
  1. Run extraction with current prompts
  2. Validate with my field-level validator
  3. Claudia's reflection: WHY did specific fields fail?
  4. Prompt revision targeting identified gaps
  5. A/B test and regression check
- Result: Systematic + precise improvement

---

## 🎯 Consensus Strategy: The Hybrid Approach

### Phase 1: Manual Seed Ground Truths (Week 1, 6-8 hours)

**Goal**: Establish rigorous baseline with 3 perfect ground truths

**Method**:
1. Select 3 PDFs representing document types:
   - **Machine-readable**: brf_268882.pdf (Hjorthagen, 28 pages)
   - **Scanned**: brf_81563.pdf (Hjorthagen, low quality)
   - **Hybrid**: [TBD - identify one with mixed content]

2. Manual annotation (2h per PDF):
   - Open PDF in viewer
   - Extract TRUE value for each field
   - Record source page, priority (P1/P2/P3), confidence (1.0 if certain, <1.0 if ambiguous)
   - Save as JSON with validation metadata

3. Establish baselines:
   - Field universe: Confirm 100-500 range
   - Priority distribution: How many P1/P2/P3 fields per PDF type?
   - Validation tolerances: Verify fuzzy/numeric thresholds work

**Output**: 3 perfect ground truth JSONs, baseline metrics established

---

### Phase 2: Confidence-Scored Expansion (Week 2-3, 40 hours)

**Goal**: Scale to 200 PDFs using Claudia's confidence-scoring approach

**Method**:
1. Select remaining 197 PDFs from 3 priority districts:
   - Hjorthagen: ~57 more PDFs
   - Norra Djurgårdsstaden: ~70 PDFs
   - Hammarby Sjöstad: ~70 PDFs

2. For each PDF:
   - Claude (me/Claudia) extracts ALL fields
   - Assign confidence score per field
   - Flag fields with confidence <95%
   - Expected: ~5-10 flagged fields per PDF

3. Human validation workflow:
   - Review flagged fields only (~1,000 total vs 20,000+ all fields)
   - Provide clarifications on ambiguous cases
   - Claude learns from clarifications
   - Save validated ground truth JSON

**Output**: 200 ground truth JSONs (3 manual + 197 confidence-validated)

---

### Phase 3: Baseline Agent Development (Week 4, 40 hours)

**Goal**: Build content-based specialists with P1/P2/P3 targeting

**Agents** (Claudia's content-based + My priority classification):

1. **loans_specialist_agent** (P1 fields: loan amounts, lenders)
   - Finds loan data wherever it appears (not just "Note 7")
   - Targets: 95% P1 accuracy (critical financial data)

2. **governance_specialist_agent** (P1/P2 fields: chairman, board, auditor)
   - Finds governance data in any section
   - Targets: 95% P1 (chairman, auditor), 85% P2 (board members)

3. **financial_statements_agent** (P1 fields: revenue, expenses, assets, liabilities, equity)
   - Extracts from balance sheet/income statement wherever located
   - Targets: 95% P1 accuracy

4. **depreciation_specialist_agent** (P2/P3 fields: building values, depreciation schedules)
   - Finds depreciation data in notes or balance sheet
   - Targets: 85% P2, 75% P3

5. **property_specialist_agent** (P1/P2 fields: address, apartments, built_year)
   - Extracts property metadata
   - Targets: 95% P1 (address, designation), 85% P2 (built_year, apartments)

[... 8-10 more content-based specialists]

**Key**: Each agent knows P1/P2/P3 fields and targets different accuracy thresholds.

---

### Phase 4: Iterative Learning with Field-Level Validation (Week 5-8, 160 hours)

**Goal**: 40 learning cycles to achieve 85-90% coverage with 95% P1 accuracy

**Each Cycle** (4 hours, 5 PDFs from validation set):

1. **Extract**: Run current best prompts on 5 PDFs
2. **Validate**: Use my field-level validator
   ```python
   result = validate_extraction_against_ground_truth(
       extraction,
       ground_truth,
       numeric_tolerance=0.01,
       string_fuzzy_threshold=0.85
   )
   # Returns: {field_accuracy, p1_accuracy, p2_accuracy, p3_accuracy, field_details}
   ```

3. **Reflect**: Analyze specific failures
   - Which P1 fields missed? (CRITICAL - must fix)
   - Which P2 fields missed? (Important - should fix)
   - Which P3 fields missed? (Nice-to-have - defer if costly)

4. **Revise**: Generate prompt v{N+1}
   - Add missing Swedish synonyms (e.g., "låneskuld" vs "lån")
   - Broaden structural patterns (table vs narrative)
   - Increase page limits if truncating
   - Keep ≤2000 tokens per agent

5. **Test**: A/B comparison
   - New prompt vs old prompt on same 5 PDFs
   - Regression check: Does new break previous successes?

6. **Track**: Update efficacy database
   ```sql
   INSERT INTO extraction_attempts (
       agent_id, prompt_version, pdf_id, pdf_type,
       field_accuracy, p1_accuracy, p2_accuracy, p3_accuracy,
       fields_missed_p1, fields_missed_p2, fields_missed_p3,
       failure_analysis, revision_notes
   ) VALUES (...);
   ```

7. **Learn**: Query best practices
   ```sql
   -- Which prompt version achieves highest P1 accuracy for this PDF type?
   SELECT prompt_version, AVG(p1_accuracy) as avg_p1
   FROM extraction_attempts
   WHERE agent_id = 'loans_specialist' AND pdf_type = 'scanned_K2'
   GROUP BY prompt_version
   ORDER BY avg_p1 DESC
   LIMIT 1;
   ```

**Success Criteria per Cycle**:
- Cycle 1-10: Baseline (60-70% field coverage)
- Cycle 11-20: Improvement (70-80% coverage)
- Cycle 21-30: Refinement (80-85% coverage)
- Cycle 31-40: Excellence (85-90% coverage, 95% P1 accuracy)

---

### Phase 5: Classification Decision (Week 7-8, integrated with Phase 4)

**Question**: After 150-180 PDFs, do we need PDF classification?

**Claudia's Insight** ✅: "Maybe let's not do it until we learn we have to?"

**Decision Criteria**:
- IF general prompts achieve ≥85% across ALL PDF types → No classification needed ✅
- IF >20% of PDFs fail with general prompts → Classify by complexity/standard/quality

**Potential Classifications** (only if data shows need):
```sql
CREATE TABLE pdf_classification (
    pdf_id VARCHAR(50),
    size_complexity VARCHAR(20),  -- small_simple / medium / large_complex
    accounting_standard VARCHAR(10), -- K2 / K3
    document_quality VARCHAR(20),    -- machine_readable / scanned_good / scanned_poor
    document_age INT,                -- 2020s / 2010s / 2000s / older
    classification_confidence NUMERIC(5,2)
);
```

**Routing Logic** (if needed):
```python
# Classify PDF first
pdf_type = classify_pdf(pdf_path)  # e.g., "scanned_K2_small"

# Use type-specific prompt variant
if pdf_type in prompt_efficacy_db:
    best_prompt = get_best_prompt_for_type(agent_id, pdf_type)
else:
    best_prompt = get_general_prompt(agent_id)
```

**My Contribution**: P1/P2/P3 classification helps even without PDF classification:
- Focus effort on critical fields first
- Accept lower accuracy on P3 fields if they're costly

---

## 🗄️ Unified Data Architecture

### Ground Truth Storage (My Framework)

```json
{
  "pdf": "brf_268882.pdf",
  "pdf_path": "../../data/raw_pdfs/Hjorthagen/brf_268882.pdf",
  "pdf_type": "scanned",
  "total_pages": 28,
  "manual_verification_date": "2025-10-15",
  "annotator": "human_expert",
  "confidence_scored": false,

  "ground_truth_fields": {
    "governance": {
      "chairman": {
        "value": "Ulf Dahlqvist",
        "source_page": 4,
        "priority": "P1",
        "field_type": "string",
        "confidence": 1.0,
        "notes": "Found in 'Styrelsens sammansättning' section"
      },
      "board_members": {
        "value": [
          "Anna Bernhardina Dolonius Bensalah",
          "Cindy Tuliao Sarceda",
          "Eugénie Bardin",
          "Hanna Jansson",
          "Pieter Gruyters",
          "Sjurður Eldeviq"
        ],
        "source_page": 4,
        "priority": "P2",
        "field_type": "array",
        "confidence": 1.0
      }
    },

    "financial": {
      "revenue": {
        "value": 2204019,
        "source_page": 9,
        "priority": "P1",
        "field_type": "integer",
        "confidence": 1.0,
        "notes": "Found in 'Resultaträkning' as 'Summa intäkter'"
      }
    }
  },

  "field_counts": {
    "total_annotated": 50,
    "p1_fields": 15,
    "p2_fields": 20,
    "p3_fields": 15
  }
}
```

---

### Efficacy Tracking Database (Claudia's Framework + My Metrics)

```sql
CREATE TABLE extraction_attempts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Extraction metadata
    agent_id VARCHAR(50),
    prompt_version VARCHAR(20),
    pdf_id VARCHAR(50),
    pdf_type VARCHAR(50),

    -- Field-level metrics (MY contribution)
    total_fields INT,
    correct_fields INT,
    field_accuracy NUMERIC(5,2),  -- Overall field accuracy

    p1_total INT,
    p1_correct INT,
    p1_accuracy NUMERIC(5,2),     -- Critical field accuracy

    p2_total INT,
    p2_correct INT,
    p2_accuracy NUMERIC(5,2),     -- Important field accuracy

    p3_total INT,
    p3_correct INT,
    p3_accuracy NUMERIC(5,2),     -- Nice-to-have accuracy

    -- Failure analysis (CLAUDIA's contribution)
    fields_missed_p1 TEXT[],       -- Array of P1 field names that failed
    fields_missed_p2 TEXT[],
    fields_missed_p3 TEXT[],
    failure_analysis TEXT,         -- WHY did extraction fail?

    -- Learning metadata (CLAUDIA's contribution)
    revision_notes TEXT,           -- What changed in prompt v{N+1}?
    synonyms_added TEXT[],         -- New Swedish terms added
    patterns_added TEXT[],         -- New structural patterns recognized
    pages_expanded BOOLEAN,        -- Did we increase page limit?

    -- Performance
    processing_time_ms INT,
    llm_cost_usd NUMERIC(8,4)
);

-- Index for fast queries
CREATE INDEX idx_agent_prompt_type ON extraction_attempts(agent_id, prompt_version, pdf_type);
CREATE INDEX idx_p1_accuracy ON extraction_attempts(p1_accuracy);
```

**Key Queries**:

```sql
-- Best prompt for this agent + PDF type
SELECT prompt_version, AVG(p1_accuracy) as avg_p1
FROM extraction_attempts
WHERE agent_id = 'loans_specialist' AND pdf_type = 'scanned_K2'
GROUP BY prompt_version
ORDER BY avg_p1 DESC
LIMIT 1;

-- Which P1 fields fail most often?
SELECT unnest(fields_missed_p1) as field_name, COUNT(*) as fail_count
FROM extraction_attempts
WHERE agent_id = 'financial_statements_agent'
GROUP BY field_name
ORDER BY fail_count DESC
LIMIT 10;

-- Learning trajectory
SELECT prompt_version,
       AVG(p1_accuracy) as avg_p1,
       AVG(p2_accuracy) as avg_p2,
       AVG(field_accuracy) as avg_overall
FROM extraction_attempts
WHERE agent_id = 'governance_specialist'
GROUP BY prompt_version
ORDER BY prompt_version;
```

---

## 📅 Unified Timeline

**Week 1: Manual Seed Ground Truths** (6-8 hours)
- Manually annotate 3 PDFs (one per type)
- Establish P1/P2/P3 baselines
- Build field-level validator script
- **Deliverable**: 3 perfect ground truth JSONs + validator

**Week 2-3: Confidence-Scored Expansion** (40 hours)
- Claude extracts 197 PDFs with confidence scoring
- Human validates ~1,000 flagged fields (<95% confidence)
- **Deliverable**: 200 ground truth JSONs

**Week 4: Baseline Agent Development** (40 hours)
- Build 12-15 content-based specialists
- Integrate P1/P2/P3 targeting
- Version 1.0 prompts
- **Deliverable**: Working baseline agents (60-70% coverage)

**Week 5-8: Iterative Learning** (160 hours, 40 cycles)
- Field-level validation per cycle
- Prompt versioning with efficacy tracking
- Systematic improvement: 60% → 85-90% coverage
- **Deliverable**: Production-ready agents (95% P1 accuracy)

**Week 9+: Production Deployment**
- Deploy to remaining 26,800 PDFs
- Continuous learning from failures
- Field-level monitoring

---

## 🎯 Success Metrics (Consensus)

| Phase  | Target                     | Measurement                      |
|--------|----------------------------|----------------------------------|
| Week 1 | 3 manual ground truths     | 100% rigorous baseline           |
| Week 3 | 200 ground truths          | <20 user clarifications needed   |
| Week 4 | Baseline 60-70%            | Field accuracy on validation set |
| Week 6 | Improvement 75-80%         | P1 accuracy ≥90%                 |
| Week 8 | Excellence 85-90%          | P1 accuracy ≥95%, P2 ≥85%        |
| Week 9 | Production deployment      | Ready for 26,800 PDFs            |

---

## 💡 Why This Synthesis is Superior

**From Claudia**:
- ✅ Scales efficiently (40h validation vs 400h manual)
- ✅ Business-aligned (starts with priority districts)
- ✅ Systematic learning (prompt efficacy persists)
- ✅ Content-based routing (robust to heterogeneity)

**From Me**:
- ✅ Rigorous measurement (field-level, not agent-level)
- ✅ Priority-driven (P1/P2/P3 focus)
- ✅ Validation tolerances (realistic matching)
- ✅ Exposes false positives (agent success ≠ field accuracy)

**Combined Benefits**:
- 🎯 Same cost (~$13K for 27K PDFs)
- 🛡️ Much lower risk (learn from 200 first)
- 📊 Perfect measurement (field-level validation)
- 🔬 Systematic improvement (40 learning cycles)
- 📈 Higher quality (95% P1 accuracy target)
- 🗄️ Institutional knowledge (efficacy DB persists)

---

## 🚀 Immediate Next Steps

**Tonight** (2 hours):
1. Create ground truth directory structure
2. Select 3 seed PDFs (machine-readable, scanned, hybrid)
3. Set up efficacy tracking database schema

**Tomorrow** (8 hours):
1. Manually annotate first seed PDF (brf_268882.pdf)
2. Build basic field-level validator
3. Validate current extraction results to see REAL accuracy

**This Week** (40 hours):
1. Complete 3 manual seed ground truths
2. Refine field-level validator with validation tolerances
3. Begin confidence-scored expansion (first 20 PDFs)
4. Design content-based specialist architecture

---

**Status**: ✅ **CONSENSUS ACHIEVED**
**Next**: Begin implementation with hybrid approach
**Goal**: 95/95 (95% P1 accuracy on 95% of 27K PDFs)
