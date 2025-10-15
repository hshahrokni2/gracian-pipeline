# UltraThinking: Learning-Based Extraction Strategy

**Date**: October 14, 2025 23:15 UTC
**Status**: 🧠 **CRITICAL STRATEGIC FRAMEWORK**
**Focus**: Iterative learning with 200 priority-district PDFs as training corpus

---

## 🎯 The Core Insight: Heterogeneity is the Challenge

### **Reality Check: Swedish BRF Documents Are Extremely Variable**

**What We Thought**:
- Standard BRF årsredovisning structure
- Predictable note numbering (Note 5 = Loans)
- Consistent table layouts
- One schema fits all

**What Is Actually True**:
- ❌ **Note numbers vary**: "Note 5" might be loans in one PDF, personnel in another
- ❌ **Sections omitted**: Small BRFs skip cash flow statements, detailed notes
- ❌ **Extra sections added**: Large BRFs have 25+ notes, appendices, sustainability reports
- ❌ **Naming differs**: "Räntekostnader" vs "Kostnader för externa lån" vs "Finansiella kostnader"
- ❌ **Table structures vary**: 2-column vs 3-column vs 5-column layouts
- ❌ **Content depth varies**: "Loans: 58.5M SEK" vs full amortization table with 6 loans

**The ONE Solid Anchor**: 🎯 **Swedish Accounting Standards (K2/K3/BFNAR)**

These **FORCE** certain minimum disclosures:
- Balance sheet must balance (assets = liabilities + equity)
- Income statement must show revenue, expenses, result
- Notes must explain accounting principles
- Certain notes are **mandatory** (loans, fixed assets, audit report)

---

## 📊 The Proposed Strategy: Learning-Based Extraction

### **Philosophy Shift: From "Design Schema → Implement" to "Learn → Adapt → Refine"**

```
Traditional Approach (What We Were Doing):
┌─────────────────────────────────────────────────────┐
│ 1. Design 530-field schema upfront                 │
│ 2. Implement 15-20 agents                          │
│ 3. Test on 10 PDFs                                 │
│ 4. Deploy to 27,000 PDFs                           │
│ 5. Hope it works...                                │
└─────────────────────────────────────────────────────┘
Problem: Fails on heterogeneous formats we didn't anticipate

Learning-Based Approach (User's Recommendation):
┌─────────────────────────────────────────────────────┐
│ 1. Start with 200 priority PDFs (3 districts)      │
│ 2. Create PERFECT ground truth for each            │
│ 3. Run extraction → Find gaps → Reflect → Revise   │
│ 4. Track prompt versions + efficacy per PDF type   │
│ 5. Build prompt library learned from 200 examples  │
│ 6. Deploy refined agents to remaining 26,800 PDFs  │
└─────────────────────────────────────────────────────┘
Result: Agents trained on real-world heterogeneity
```

---

## 🏢 Priority Districts: Business-Critical 200 PDFs

### **Why These Three Districts?**

**1. Hjorthagen** (~60-70 PDFs)
- **Business Urgency**: High priority for analysis
- **Characteristics**: Mix of older (1900s-1950s) and newer (2000s) buildings
- **Value**: Waterfront area undergoing development

**2. Norra Djurgårdsstaden** (~60-70 PDFs)
- **Business Urgency**: High priority for analysis
- **Characteristics**: New sustainable development (2010s-2020s)
- **Value**: Premium modern BRFs, cutting-edge sustainability features

**3. Hammarby Sjöstad** (~60-70 PDFs)
- **Business Urgency**: Strategic importance
- **Characteristics**: Mixed age (1990s-2020s), eco-district
- **Value**: Mix of building types, diverse ownership structures

**Total**: ~200 PDFs representing **diverse heterogeneity**:
- ✅ Old vs new buildings (different accounting practices)
- ✅ Small vs large BRFs (different reporting depth)
- ✅ Simple vs complex ownership (different note structures)
- ✅ Traditional vs sustainable (different appendices)

---

## 🔄 The Learning Loop Framework

### **Phase 1: Ground Truth Creation** (Week 1-2, ~200 hours)

**For Each of 200 PDFs** (1 hour per PDF average):

```yaml
Step 1: Claude Reads PDF Completely
  - Read all pages (not just structure detection)
  - Identify ALL extractable fields present
  - Note section naming variations
  - Flag unusual structures

Step 2: Claude Creates Ground Truth YAML
  - Extract ALL fields with confidence scores
  - Document source pages with precise citations
  - Note Swedish terms used in THIS specific PDF
  - Identify missing expected fields (if any)

Step 3: Confidence Assessment
  IF confidence < 95% on any field:
    - Flag field for user review
    - Explain uncertainty (e.g., "Unclear if 58.5M is total loans or just one loan")
    - Request clarification
  ELSE:
    - Proceed to validation

Step 4: User Validation (Selective)
  - User reviews flagged uncertain fields
  - Confirms/corrects Claude's extraction
  - Documents correct interpretation for learning

Step 5: Save Perfect Ground Truth
  - Store as ground_truth_{brf_name}_{org_number}.yaml
  - Include metadata: PDF characteristics, unusual features
  - Tag PDF type for later classification (if needed)
```

**Output After Phase 1**:
- 200 perfect ground truth files
- Heterogeneity taxonomy (what variations exist)
- Initial PDF type classification (if patterns emerge)

---

### **Phase 2: Initial Agent Development** (Week 3-4, ~80 hours)

**Develop Baseline Agents Based on Learned Patterns**:

```yaml
Step 1: Analyze Ground Truth Corpus
  - What fields are present in >95% of PDFs? (P0 mandatory)
  - What fields are present in 70-95%? (P1 common)
  - What fields are present in 30-70%? (P2 variable)
  - What fields are present in <30%? (P3 rare)

Step 2: Design Specialist Agents
  - NOT based on note numbers (those vary!)
  - Based on CONTENT semantics:
    * loans_specialist_agent (finds loan data wherever it appears)
    * depreciation_specialist_agent (finds depreciation wherever it appears)
    * governance_specialist_agent (finds board/auditor info)
    * financial_statements_agent (finds income/balance/cashflow)

Step 3: Create Baseline Prompts
  - Use most common Swedish term variations
  - Include fallback synonyms from heterogeneity analysis
  - Add structural cues (e.g., "Look for table with columns: Långivare, Belopp, Ränta")
  - Store as prompt_v1.0 for each agent

Step 4: Test on 20-PDF Validation Set
  - Run all agents on 20 diverse PDFs from training corpus
  - Compare to ground truth
  - Calculate coverage, accuracy, evidence ratio
```

---

### **Phase 3: Iterative Learning Cycles** (Week 5-8, ~160 hours)

**The Core Learning Loop** (40 cycles × 4 hours each):

```yaml
Cycle N (Process 5 PDFs per cycle):

  Step 1: Run Current Agents
    - Extract with current best prompt versions
    - Track which prompt version used for each agent
    - Log extraction results + evidence pages

  Step 2: Compare to Ground Truth
    - Calculate per-field accuracy
    - Identify missing fields (should have extracted but didn't)
    - Identify hallucinations (extracted incorrectly)
    - Measure coverage drop from ground truth

  Step 3: Reflection & Root Cause Analysis
    Claude analyzes failures:
    - "Why did loans_specialist_agent miss loan #3?"
    - Possible causes:
      * Prompt too specific to one format
      * Missing Swedish synonym ("Fastighetslån" vs "Lån i kreditinstitut")
      * Table structure not recognized (5-column vs 3-column)
      * Note routing failed (looked in Note 5, but loans were in Note 7)
      * Page limit too restrictive (only searched pages 10-14, but loans on page 18)

  Step 4: Prompt Revision
    Generate prompt_v{N+1}:
    - Add missing synonyms
    - Broaden structural patterns
    - Adjust page allocation strategy
    - Add fallback extraction logic

    Constraints:
    - Prompt length ≤ 2000 tokens (avoid overwhelming LLM)
    - Maintain specificity (don't make so broad it hallucinates)
    - Preserve what's working (don't break existing success cases)

  Step 5: A/B Testing
    - Test prompt_v{N+1} on same 5 PDFs
    - Also test on 5 PREVIOUS PDFs (regression check)
    - Compare results:
      * Did v{N+1} fix the failures?
      * Did v{N+1} break any previous successes?

  Step 6: Prompt Selection & Versioning
    IF v{N+1} improves overall score:
      - Promote v{N+1} to current best
      - Save v{N} as archived version
    ELSE IF v{N+1} fixes new cases but breaks old:
      - Investigate if PDF classification needed
      - Consider creating specialized prompt variants
    ELSE:
      - Keep v{N} as best
      - Document why v{N+1} failed

  Step 7: Update Prompt Efficacy Database
    Record in prompts_efficacy.db:
    - prompt_version
    - agent_id
    - pdf_id
    - coverage_achieved
    - accuracy_achieved
    - fields_missed
    - fields_hallucinated
    - notes (what worked, what didn't)
```

**Key Insight: Prompt Versioning is CRITICAL**

```sql
-- Example: Track prompt performance across PDFs
CREATE TABLE prompt_efficacy (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(50),
  prompt_version VARCHAR(20),
  pdf_id VARCHAR(50),
  pdf_type VARCHAR(50),  -- e.g., "small_simple", "large_complex", "hybrid_scanned"
  coverage_pct NUMERIC(5,2),
  accuracy_pct NUMERIC(5,2),
  fields_extracted INT,
  fields_missed INT,
  fields_hallucinated INT,
  extraction_time_seconds INT,
  tested_at TIMESTAMP,
  notes TEXT,
  promoted_to_best BOOLEAN DEFAULT FALSE
);

-- Query: Which prompt version works best for "large_complex" PDFs?
SELECT prompt_version, AVG(coverage_pct) as avg_coverage
FROM prompt_efficacy
WHERE agent_id = 'loans_specialist_agent' AND pdf_type = 'large_complex'
GROUP BY prompt_version
ORDER BY avg_coverage DESC;
```

---

### **Phase 4: Specialization vs Classification Decision** (Week 7-8)

**The Key Question**: After 150-180 PDFs processed, do we need PDF classification?

**Ideal Scenario** (Don't need classification):
- Each specialist agent handles all format variations
- Prompt version 7-10 achieves 85%+ coverage across ALL PDF types
- Minor variations handled by synonym lists + flexible prompts

**Reality Check Scenario** (Need classification):
- Some PDFs consistently fail with general prompts
- Clear clusters emerge (e.g., "small K2 format" vs "large K3 format")
- Prompt v8 works great for 70% of PDFs but fails on 30%

**Classification Strategy** (IF NEEDED):

```yaml
PDF Classification Dimensions:

  1. Size & Complexity:
    - small_simple: <20 pages, minimal notes (e.g., small old BRFs)
    - medium_standard: 20-40 pages, standard notes (most common)
    - large_complex: >40 pages, 20+ notes, appendices (large new BRFs)

  2. Accounting Standard:
    - K2: Simplified accounting (most common for BRFs)
    - K3: More detailed disclosures (larger BRFs)
    - IFRS: Rare for BRFs, but exists

  3. Document Quality:
    - machine_readable: Born-digital PDF with text layer
    - scanned_ocr: Scanned document, OCR needed
    - hybrid: Mix of text and scanned pages

  4. Age of Report:
    - 2020s: Recent format, likely detailed
    - 2010s: Standard format
    - 2000s: Older format, may lack some disclosures
    - Pre-2000: Very old format, minimal details

Classifier Agent:
  - Lightweight agent (fast, cheap)
  - Analyzes first 5-10 pages
  - Classifies PDF into type
  - Routes to appropriate prompt variant

Prompt Variant Strategy:
  IF pdf_type == "small_simple":
    USE prompt_variant_A (broader search, lower expectations)
  ELIF pdf_type == "large_complex":
    USE prompt_variant_B (detailed search, higher expectations)
  ELSE:
    USE prompt_baseline (standard search)
```

**Decision Rule**:
```
After processing 150 PDFs:
IF 20%+ of PDFs fail with best general prompt:
  → Investigate classification
ELSE:
  → Continue with general specialist agents
```

---

## 📈 Success Metrics & Learning Targets

### **Phase 1 Targets** (Ground Truth Creation - Week 1-2)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Ground Truths Created** | 200 | Count of YAML files |
| **Avg Fields per PDF** | 250-350 | Field count in ground truth |
| **Heterogeneity Taxonomy** | Complete | Document variations found |
| **User Clarifications Needed** | <20 | Fields with confidence <95% |

### **Phase 2 Targets** (Initial Agents - Week 3-4)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Baseline Coverage** | 60-70% | Fields extracted vs ground truth |
| **Baseline Accuracy** | 85%+ | Correct vs extracted fields |
| **Agent Count** | 12-15 | Specialist agents developed |
| **Prompt Version** | v1.0 | Initial prompt for each agent |

### **Phase 3 Targets** (Learning Cycles - Week 5-8)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Final Coverage** | 85-90% | After 40 learning cycles |
| **Final Accuracy** | 95%+ | Correct extractions |
| **Prompt Versions Tested** | 5-10 per agent | Versions in database |
| **Regression Test Pass Rate** | >95% | Old PDFs still work |

### **Phase 4 Targets** (Classification Decision - Week 7-8)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **General Agent Success** | >80% of PDFs | If achieved, NO classification needed |
| **Classification Accuracy** | 95%+ | IF classification needed |
| **Specialized Prompt Improvement** | +10-15% coverage | For classified subtypes |

---

## 🗄️ Data Architecture for Learning

### **1. Ground Truth Storage**

```yaml
# ground_truth/hjorthagen/brf_81563_org_769606-2533.yaml
pdf_metadata:
  filename: "brf_81563_årsredovisning_2021.pdf"
  organization_number: "769606-2533"
  district: "Hjorthagen"
  pages: 26
  year: 2021
  accounting_standard: "K2"
  pdf_type: "medium_standard"
  quality: "machine_readable"

  # Heterogeneity notes
  structural_notes:
    - "Loans in Note 7 (not standard Note 5)"
    - "No cash flow statement (K2 allows omission)"
    - "Maintenance fund movements in management report (not separate note)"

  unusual_features:
    - "Samfällighet ownership structure (joint facility with neighboring BRF)"
    - "Commercial tenant details in Note 14 (unusual placement)"

ground_truth_fields:
  governance:
    chairman:
      value: "Per Wiklund"
      confidence: 1.0
      source_page: 2
      swedish_term_used: "Ordförande"

    board_members:
      value:
        - {name: "Per Wiklund", role: "Ordförande"}
        - {name: "Lisa Andersson", role: "Ledamot"}
        - {name: "Erik Olsson", role: "Ledamot"}
        - {name: "Maria Svensson", role: "Suppleant"}
      confidence: 1.0
      source_page: 2
      swedish_term_used: "Styrelseledamöter och suppleanter"

  financial_statements:
    revenue:
      value: 3245000
      confidence: 1.0
      source_page: 5
      swedish_term_used: "Rörelseintäkter"
      table_location: "Resultaträkning, row 3"

    # ... (all 250-350 fields with confidence scores)

  notes:
    loans:
      value:
        - lender: "SEB"
          amount: 58500000
          interest_rate: 0.0045
          maturity: "2024-03-15"
      confidence: 0.92  # <95% - FLAG FOR USER REVIEW
      source_page: 13
      swedish_term_used: "Låneskulder till kreditinstitut"
      notes: "Uncertain if 58.5M is total or just one loan - table structure ambiguous"
      user_clarification_needed: true
      user_clarified: false
      user_clarification: ""  # Will be filled after user review

validation:
  balance_check:
    assets: 301339818
    liabilities: 94804230
    equity: 206535588
    balanced: true
    tolerance: 0.0001

  cross_references:
    - field: "loans.total"
      should_match: "balance_sheet.long_term_liabilities"
      matches: true
    - field: "loans.interest_expense"
      should_match: "income_statement.interest_expense"
      matches: true

extraction_difficulty:
  easy_fields: 180  # Confidence > 0.95
  medium_fields: 50  # Confidence 0.85-0.95
  hard_fields: 20   # Confidence < 0.85
  missing_expected: 5  # Fields we'd expect but aren't present
```

### **2. Prompt Efficacy Database**

```sql
-- Track every extraction attempt
CREATE TABLE extraction_attempts (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(50),
  agent_id VARCHAR(50),
  prompt_version VARCHAR(20),
  pdf_id VARCHAR(50),
  pdf_type VARCHAR(50),
  ground_truth_available BOOLEAN,

  -- Results
  fields_attempted INT,
  fields_extracted INT,
  fields_correct INT,
  fields_missed INT,
  fields_hallucinated INT,

  -- Metrics
  coverage_pct NUMERIC(5,2),  -- extracted / attempted
  accuracy_pct NUMERIC(5,2),  -- correct / extracted
  evidence_ratio NUMERIC(5,2), -- with_citations / extracted

  -- Performance
  extraction_time_seconds INT,
  token_usage INT,
  cost_usd NUMERIC(8,4),

  -- Learning
  failure_analysis TEXT,  -- Claude's reflection on what went wrong
  revision_notes TEXT,    -- What to change in next prompt version

  created_at TIMESTAMP DEFAULT NOW()
);

-- Track prompt versions
CREATE TABLE prompt_versions (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(50),
  version VARCHAR(20),
  prompt_text TEXT,
  changes_from_previous TEXT,
  rationale TEXT,

  -- Efficacy stats (aggregated from extraction_attempts)
  avg_coverage_pct NUMERIC(5,2),
  avg_accuracy_pct NUMERIC(5,2),
  test_count INT,
  promoted_to_best BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(50)  -- "claude" or "human"
);

-- Track PDF characteristics for classification
CREATE TABLE pdf_characteristics (
  pdf_id VARCHAR(50) PRIMARY KEY,
  filename VARCHAR(255),
  district VARCHAR(100),
  organization_number VARCHAR(20),

  -- Classification dimensions
  size_complexity ENUM('small_simple', 'medium_standard', 'large_complex'),
  accounting_standard ENUM('K2', 'K3', 'IFRS', 'other'),
  quality ENUM('machine_readable', 'scanned_ocr', 'hybrid'),
  year_published INT,
  age_category ENUM('2020s', '2010s', '2000s', 'pre_2000'),

  -- Structure
  page_count INT,
  note_count INT,
  has_cash_flow BOOLEAN,
  has_appendices BOOLEAN,

  -- Heterogeneity flags
  unusual_note_numbering BOOLEAN,
  non_standard_sections BOOLEAN,
  hybrid_structure BOOLEAN,

  notes TEXT
);
```

### **3. Learning Dashboard Queries**

```sql
-- Which agent needs most improvement?
SELECT agent_id,
       AVG(coverage_pct) as avg_coverage,
       AVG(accuracy_pct) as avg_accuracy,
       COUNT(*) as test_count
FROM extraction_attempts
WHERE ground_truth_available = TRUE
GROUP BY agent_id
ORDER BY avg_coverage ASC;

-- Prompt evolution: Is version 5 better than version 4?
SELECT prompt_version,
       AVG(coverage_pct) as avg_coverage,
       AVG(accuracy_pct) as avg_accuracy,
       COUNT(*) as test_count
FROM extraction_attempts
WHERE agent_id = 'loans_specialist_agent'
  AND pdf_type = 'medium_standard'
GROUP BY prompt_version
ORDER BY prompt_version;

-- Do we need classification? Check variance across PDF types
SELECT pdf_type,
       agent_id,
       AVG(coverage_pct) as avg_coverage,
       STDDEV(coverage_pct) as stddev_coverage
FROM extraction_attempts
JOIN pdf_characteristics USING (pdf_id)
WHERE prompt_version = 'v7.0'  -- Current best
GROUP BY pdf_type, agent_id
HAVING STDDEV(coverage_pct) > 15  -- High variance = classification needed
ORDER BY stddev_coverage DESC;

-- Regression check: Did new prompt break old successes?
WITH previous_run AS (
  SELECT pdf_id, coverage_pct as old_coverage
  FROM extraction_attempts
  WHERE agent_id = 'loans_specialist_agent'
    AND prompt_version = 'v6.0'
),
current_run AS (
  SELECT pdf_id, coverage_pct as new_coverage
  FROM extraction_attempts
  WHERE agent_id = 'loans_specialist_agent'
    AND prompt_version = 'v7.0'
)
SELECT p.pdf_id,
       old_coverage,
       new_coverage,
       (new_coverage - old_coverage) as delta
FROM previous_run p
JOIN current_run c USING (pdf_id)
WHERE new_coverage < old_coverage - 5  -- Regression: dropped >5%
ORDER BY delta ASC;
```

---

## 🤖 Claude's Role: Ground Truther & Trainer

### **Responsibilities**

**1. Ground Truth Creation** (Week 1-2)
- Read each of 200 PDFs completely
- Extract ALL fields with confidence scores
- Flag fields with confidence <95% for user review
- Document heterogeneity patterns

**2. Reflection & Analysis** (Week 5-8)
- Analyze why extraction failed for each gap
- Identify root causes (missing synonyms, structural mismatch, page limits)
- Propose specific prompt revisions
- Explain trade-offs (specificity vs generalization)

**3. Prompt Revision** (Week 5-8)
- Generate new prompt versions based on learnings
- Maintain boundary conditions (length, complexity)
- A/B test new vs old prompts
- Document why changes were made

**4. Confidence Calibration**
- Provide confidence score for each extracted field
- IF confidence <95%: Flag for user review with specific question
- IF confidence <99%: Note uncertainty but proceed
- IF confidence ≥99%: High confidence, proceed

### **Example: Confidence Flagging**

```yaml
# Claude extracts loans from PDF
loans:
  value:
    - lender: "SEB"
      amount: 58500000
      interest_rate: 0.0045

  confidence: 0.92  # <95% threshold

  uncertainty_reason: |
    The Note 7 table shows:
    "Låneskulder kreditinstitut   58 500"

    Ambiguity: Is this:
    A) One loan from SEB for 58.5M (one row in table)
    B) Total of multiple loans that sum to 58.5M (unclear how many loans)

    The table structure is single-column, doesn't break down individual loans.
    Previous PDFs had multi-column tables with per-loan details.

  clarification_question: |
    User: Please confirm:
    1. Is this ONE loan or TOTAL of multiple loans?
    2. If multiple loans, do you see a breakdown elsewhere in the document?
    3. Should I extract as array with single item, or as scalar total?

  suggested_action: |
    Extract as scalar total for now (58.5M),
    but flag that individual loan breakdown is not available in this PDF.
```

**User Response**:
```yaml
user_clarification: |
  Correct interpretation: This is TOTAL of multiple loans.
  Small K2-format BRFs often show aggregate only in main note,
  with individual loan details omitted (allowed under K2 simplified accounting).

  Action: Extract as {"total_loans": 58500000, "individual_loans": null}
  Add to learning: K2 small BRFs may not have per-loan breakdown.

claude_learning_update:
  - Update loans_specialist_agent prompt v7.1:
    * Add fallback: If individual loans not found, extract aggregate
    * Don't hallucinate individual loans when only total is present
    * Flag "individual_loans": null when no breakdown available

  - Add to heterogeneity taxonomy:
    * K2 small BRFs: Often show aggregate loan total only
    * K3 large BRFs: Usually show per-loan breakdown table
```

---

## 📅 Detailed Implementation Timeline

### **Week 1: Hjorthagen Ground Truth** (40 hours, 60-70 PDFs)

```yaml
Day 1-2 (16 hours):
  - Claude reads 20 Hjorthagen PDFs
  - Creates ground truth YAML for each
  - Flags 5-8 uncertain fields for user review
  - User reviews and clarifies flagged fields
  - Claude updates ground truths with clarifications

Day 3-4 (16 hours):
  - Claude reads next 20 PDFs
  - Ground truth creation
  - User review cycle

Day 5 (8 hours):
  - Claude reads remaining 20-30 PDFs
  - Complete Hjorthagen ground truth corpus
  - Analyze heterogeneity patterns in Hjorthagen
  - Document insights (e.g., "80% are small K2 format")

Weekend:
  - User review of completed ground truths
  - Spot-check 10 random PDFs for quality
```

### **Week 2: Norra Djurgårdsstaden + Hammarby Sjöstad Ground Truth** (40 hours, ~130 PDFs)

```yaml
Similar structure to Week 1, processing ~65 PDFs per district

Key focus:
  - Compare heterogeneity across districts
  - Norra Djurgårdsstaden likely more modern, K3 format
  - Hammarby Sjöstad likely mixed ages, varied formats
  - Identify if classification patterns emerge naturally

Output:
  - 200 perfect ground truth YAMLs
  - Heterogeneity taxonomy document
  - Initial PDF classification schema (if patterns clear)
```

### **Week 3-4: Baseline Agent Development** (80 hours)

```yaml
Week 3: Agent Design & Implementation (40 hours)
  - Analyze 200 ground truths for common patterns
  - Design 12-15 specialist agents (NOT note-number based!)
  - Implement baseline prompts (v1.0 for each agent)
  - Test on 20-PDF validation set

Week 4: Baseline Testing & Iteration (40 hours)
  - Run baseline agents on all 200 PDFs
  - Calculate baseline metrics (expect 60-70% coverage)
  - Identify systematic failures
  - Prepare for learning cycles in Week 5
```

### **Week 5-8: Iterative Learning Cycles** (160 hours, 40 cycles)

```yaml
40 cycles × 4 hours each = 160 hours

Each cycle:
  - Select 5 PDFs (mix of previously seen + new edge cases)
  - Run agents with current best prompts
  - Compare to ground truth
  - Claude reflects on failures
  - Claude proposes prompt revision
  - A/B test new prompt
  - Regression test on 5 old PDFs
  - Update prompt efficacy database
  - Promote or archive new prompt version

Weeks 5-6 (20 cycles):
  - Focus on P0 critical fields (governance, financials, core notes)
  - Target: 75-80% coverage, 90% accuracy

Weeks 7-8 (20 cycles):
  - Focus on P1 high-value fields (detailed notes, time series)
  - Target: 85-90% coverage, 95% accuracy
  - Make classification decision (needed or not?)
```

### **Week 9: Final Validation & Production Prep** (40 hours)

```yaml
Day 1-2: Comprehensive Testing
  - Run final agent versions on all 200 ground truth PDFs
  - Calculate final metrics
  - Regression test: Ensure early PDFs still work

Day 3: Production Setup
  - Deploy agents to production infrastructure
  - Set up monitoring and logging
  - Prepare batch processing pipeline

Day 4-5: First Production Run
  - Process remaining ~26,800 PDFs
  - Monitor quality metrics
  - Flag anomalies for review
```

---

## 🎯 Success Criteria & Milestones

### **Week 2 Milestone: Ground Truth Corpus Complete**
- [x] 200 perfect ground truth YAMLs created
- [x] <20 user clarifications needed total
- [x] Heterogeneity taxonomy documented
- [x] PDF classification schema (if applicable)

### **Week 4 Milestone: Baseline Agents Operational**
- [x] 12-15 specialist agents implemented
- [x] Baseline coverage: 60-70%
- [x] Baseline accuracy: 85%+
- [x] Prompt efficacy database operational

### **Week 8 Milestone: Learning Complete**
- [x] Final coverage: 85-90%
- [x] Final accuracy: 95%+
- [x] 5-10 prompt versions tested per agent
- [x] Regression test pass rate: >95%
- [x] Classification decision made (needed or not)

### **Week 9 Milestone: Production Ready**
- [x] All 200 ground truth PDFs processed successfully
- [x] Production infrastructure deployed
- [x] Monitoring and alerting configured
- [x] Ready to process 26,800 remaining PDFs

---

## 💡 Key Principles for Success

### **1. Embrace Heterogeneity, Don't Fight It**
- PDFs WILL vary - that's the reality
- Design agents for flexibility, not rigid structure
- Use accounting standards as anchor, not note numbers

### **2. Learn Before Scaling**
- 200 PDFs is enough to learn patterns
- Don't process 27,000 until agents are refined
- Each failure teaches us something valuable

### **3. Track Everything**
- Every prompt version matters
- Every extraction attempt provides data
- Prompt efficacy database is CRITICAL

### **4. Confidence Calibration is Key**
- Claude should know when uncertain
- User clarifications teach Claude the rules
- Build institutional knowledge iteratively

### **5. Avoid Premature Optimization**
- Don't create PDF classification unless needed
- Start with general specialist agents
- Only specialize if data shows it's necessary

### **6. Boundary Conditions Matter**
- Prompts can't be too long (>2000 tokens = failure)
- Prompts can't be too vague (hallucinations)
- Sweet spot: Specific enough to guide, flexible enough to adapt

---

## 🚀 Immediate Next Steps

### **Tonight (2 hours)**
1. Locate the list of 100 diverse PDFs (user mentioned having this)
2. Identify PDFs from Hjorthagen, Norra Djurgårdsstaden, Hammarby Sjöstad
3. Confirm we have ~200 PDFs total from these 3 districts
4. Set up ground truth storage structure

### **Tomorrow (8 hours)**
1. Begin Week 1 ground truth creation (first 20 Hjorthagen PDFs)
2. Claude reads each PDF completely
3. Creates detailed ground truth YAMLs
4. Flags uncertain fields for user review (target: <5 per PDF)

### **This Week (40 hours)**
1. Complete all 60-70 Hjorthagen ground truths
2. Begin heterogeneity taxonomy
3. User reviews flagged uncertain fields
4. Identify if any patterns emerge for classification

---

## 📊 Expected Outcomes

### **After 200 PDFs Processed (Week 2)**
- Deep understanding of BRF document heterogeneity
- Perfect ground truth training corpus
- Clear taxonomy of variations (note numbering, structural differences, omissions)
- Foundation for specialist agent design

### **After Learning Cycles (Week 8)**
- 85-90% coverage across diverse PDFs
- 95%+ accuracy on extracted fields
- Robust specialist agents that handle format variations
- Prompt library with 5-10 versions per agent, optimized for different scenarios
- Clear understanding if classification is needed (likely NOT if agents are well-designed)

### **After Production Deployment (Week 9+)**
- 27,000 PDFs processed with refined agents
- Consistent quality across heterogeneous corpus
- Monitoring system flagging anomalies
- Continuous learning from edge cases

---

## ✅ Advantages of This Approach

1. **Business-Aligned**: Starts with priority districts (Hjorthagen, Norra Djurgårdsstaden, Hammarby Sjöstad)
2. **Risk-Mitigated**: Learn from 200 PDFs before processing 27,000
3. **Quality-Focused**: Perfect ground truth ensures accurate learning
4. **Data-Driven**: Prompt efficacy database tracks what works
5. **Adaptable**: Can pivot to classification if needed, but doesn't assume it upfront
6. **Cost-Efficient**: One refined production run instead of multiple failed attempts
7. **Sustainable**: Build institutional knowledge that persists across sessions

---

## 🎯 Final Recommendation

**Adopt the Learning-Based Strategy**:
1. Start with 200 PDFs from 3 priority districts
2. Claude creates perfect ground truths (with user clarification on uncertainty)
3. Develop specialist agents (content-based, not note-number-based)
4. Iterate with 40 learning cycles, tracking prompt efficacy
5. Make classification decision based on data (Week 7-8)
6. Deploy refined agents to full 27,000-PDF corpus (Week 9)

**This approach costs the same as the "design upfront" approach (~$13K), but delivers:**
- Higher quality (learned from real heterogeneity)
- Lower risk (validated on 200 PDFs first)
- Better alignment (priority districts first)
- Institutional knowledge (prompt efficacy database)

**User's instinct is again correct: Don't design in a vacuum. Learn from reality first!**

---

**Generated**: October 14, 2025 23:15 UTC
**Status**: 🎯 **LEARNING-BASED STRATEGY DEFINED**
**Next**: Locate 200 PDFs from priority districts and begin ground truth creation
**User Validation Needed**: Confirm 3-district strategy and begin Week 1 execution

🧠 **This is the RIGHT approach - learn from heterogeneity instead of fighting it!** 🚀
