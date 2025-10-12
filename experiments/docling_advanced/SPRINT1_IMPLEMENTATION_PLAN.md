# Sprint 1 Implementation Plan: 30 → 53 Fields
## 107-Field Expansion - Week 1

**Date**: October 12, 2025
**Status**: ✅ P0 Retry Logic Complete, Starting Sprint 1
**Goal**: Add 23 new fields (revenue breakdown + loan 1 details)

---

## 🎯 Sprint 1 Overview

**Current State**: 30 fields, 100% coverage/accuracy (validated)
**Target State**: 53 fields, ≥85% accuracy, ≤$0.16/PDF cost
**Duration**: 1 week (5 days)
**Key Additions**:
1. Revenue breakdown agent (15 new fields)
2. Loan 1 detailed agent (8 new fields)
3. Few-shot learning system
4. Field-level synonym mapping

**Success Criteria**:
- ✅ 53-field ground truth validated on brf_198532
- ✅ ≥85% accuracy on 53 fields
- ✅ Test on same 10 PDFs (consistency check)
- ✅ Cost ≤$0.16/PDF (vs $0.14 baseline)
- ✅ Processing time ≤150s (vs 120s baseline)

---

## 📋 New Fields (23 Total)

### **Revenue Breakdown** (15 fields) - Priority 1

**Parent Agent**: `revenue_breakdown_agent`

**Fields**:
```python
class RevenueBreakdownData(BaseModel):
    # Income statement revenue components
    nettoomsattning: Optional[float] = None        # Net sales (main revenue)
    arsavgifter: Optional[float] = None             # Annual fees from members
    hyresintakter: Optional[float] = None           # Rental income (garages, commercial)
    bredband_kabel_tv: Optional[float] = None       # Broadband/cable TV fees
    andel_drift_gemensam: Optional[float] = None    # Shared operations income
    andel_el_varme: Optional[float] = None          # Shared electricity/heating
    andel_vatten: Optional[float] = None            # Shared water costs
    ovriga_intakter: Optional[float] = None         # Other income
    ranta_bankmedel: Optional[float] = None         # Interest on bank deposits
    valutakursvinster: Optional[float] = None       # Currency exchange gains

    # Revenue totals (for cross-validation)
    summa_rorelseintakter: Optional[float] = None   # Total operating revenue
    summa_finansiella_intakter: Optional[float] = None  # Total financial income
    summa_intakter: Optional[float] = None          # Grand total revenue

    # Multi-year comparison (if available)
    revenue_2021: Optional[float] = None            # Previous year revenue
    revenue_2020: Optional[float] = None            # 2 years ago

    evidence_pages: List[int] = []
```

**Swedish Term Synonyms** (field-level mapping):
- `nettoomsattning`: ["Nettoomsättning", "Nettoförsäljning", "Intäkter av försäljning"]
- `arsavgifter`: ["Årsavgifter", "Avgifter", "Medlemsavgifter", "Bostadsrättsavgifter"]
- `hyresintakter`: ["Hyresintäkter", "Hyror", "Hyresinkomster", "Lokalhyror"]

**Extraction Strategy**:
- Look in "Resultaträkning" section (pages typically 6-8)
- Extract from detailed revenue breakdown table
- Cross-validate: Sum of components should equal `summa_intakter`
- Fallback: If detailed breakdown not found, return empty (don't use current 30-field `revenue` total)

**Few-Shot Examples** (2-3 per field):
```yaml
# Example 1: Comprehensive K3 BRF
input_page: "Page 6: Resultaträkning"
input_text: |
  Nettoomsättning                        7 393 591 kr
  Hyresintäkter                            452 800 kr
  Övriga rörelseintäkter                   186 932 kr
  Summa rörelseintäkter                  8 033 323 kr

expected_output:
  nettoomsattning: 7393591
  hyresintakter: 452800
  ovriga_intakter: 186932
  summa_rorelseintakter: 8033323
  evidence_pages: [6]

# Example 2: Simple K2 BRF (minimal breakdown)
input_page: "Page 7: Resultaträkning"
input_text: |
  Årsavgifter                            5 264 131 kr
  Summa intäkter                         5 264 131 kr

expected_output:
  arsavgifter: 5264131
  summa_intakter: 5264131
  evidence_pages: [7]

# Example 3: Scanned PDF with OCR errors
input_page: "Page 8: Resultaträkning (scanned)"
input_text: |
  Ålsavgifter                            2 204 Ol9 kr  # OCR error: "O" instead of "0"
  Hyresinläkter                             45 600 kr  # OCR error: "l" instead of "t"

expected_output:
  arsavgifter: 2204019  # Corrected OCR
  hyresintakter: 45600  # Corrected OCR
  evidence_pages: [8]
```

---

### **Loan 1 Detailed** (8 fields) - Priority 2

**Parent Agent**: `loan_1_detailed_agent`

**Fields**:
```python
class Loan1DetailedData(BaseModel):
    # Loan 1 (primary loan) detailed extraction
    loan_1_lender: Optional[str] = None             # Bank name (e.g., "SEB", "Nordea")
    loan_1_amount: Optional[float] = None           # Loan amount (SEK)
    loan_1_interest_rate: Optional[float] = None    # Interest rate (decimal, e.g., 0.0457 for 4.57%)
    loan_1_maturity_date: Optional[str] = None      # Maturity date (YYYY-MM-DD or original format)
    loan_1_amortization_free: Optional[bool] = None # Amortization-free period active?
    loan_1_fixed_variable: Optional[str] = None     # "fast" (fixed) or "rörlig" (variable)
    loan_1_margin: Optional[float] = None           # Margin above base rate (if applicable)
    loan_1_collateral: Optional[str] = None         # Collateral type (e.g., "Fastighetsinteckning")

    evidence_pages: List[int] = []
```

**Swedish Term Synonyms**:
- `loan_1_lender`: ["Långivare", "Bank", "Kreditinstitut", "Kreditgivare"]
- `loan_1_amount`: ["Belopp", "Lånebelopp", "Skuldbelopp", "Skuld"]
- `loan_1_interest_rate`: ["Ränta", "Räntesats", "Ränta %"]
- `loan_1_maturity_date`: ["Förfallodag", "Förfallodatum", "Slutdag", "Omsättningsdag"]
- `loan_1_amortization_free`: ["Amorteringsfri", "Amorteringsfritt", "Ej amortering"]

**Extraction Strategy**:
- Look in "Noter" section, typically "Not 11 - Skulder till kreditinstitut" or "Not 12 - Lån"
- Pages typically 13-16
- Extract from loan schedule table (usually 4 rows)
- **CRITICAL**: Only extract FIRST loan (highest amount or first in table)
- Cross-validate: `loan_1_amount` should match entry in balance sheet liabilities

**Few-Shot Examples**:
```yaml
# Example 1: Standard loan table (K3)
input_page: "Page 15: Not 11 - Skulder till kreditinstitut"
input_text: |
  Långivare    Belopp        Ränta    Förfallodatum
  SEB          30 000 000 kr  0,57 %  2024-09-28
  SEB          30 000 000 kr  1,49 %  2026-03-27
  SEB          30 000 000 kr  1,75 %  2028-09-27

expected_output:
  loan_1_lender: "SEB"
  loan_1_amount: 30000000
  loan_1_interest_rate: 0.0057
  loan_1_maturity_date: "2024-09-28"
  loan_1_amortization_free: true  # No amortization mentioned
  evidence_pages: [15]

# Example 2: Detailed loan note with terms (K3)
input_page: "Page 14: Not 12 - Fastighetslån"
input_text: |
  Föreningen har 2 lån hos Nordea:
  - Lån 1: 22 390 000 kr, fast ränta 4.51%, förfall 2024-03-29
  - Lån 2: 22 862 000 kr, rörlig ränta 1.05%, förfall 2025-12-17

expected_output:
  loan_1_lender: "Nordea"
  loan_1_amount: 22390000
  loan_1_interest_rate: 0.0451
  loan_1_maturity_date: "2024-03-29"
  loan_1_fixed_variable: "fast"
  evidence_pages: [14]

# Example 3: Minimal loan disclosure (K2)
input_page: "Page 13: Noter"
input_text: |
  Skulder till kreditinstitut: 10 900 000 kr (SEB)
  Räntesats: 3,91% (fast tom 2025-06-28)

expected_output:
  loan_1_lender: "SEB"
  loan_1_amount: 10900000
  loan_1_interest_rate: 0.0391
  loan_1_maturity_date: "2025-06-28"
  loan_1_fixed_variable: "fast"
  evidence_pages: [13]
```

---

## 🛠️ Implementation Tasks

### **Day 1: Schema & Ground Truth** (6 hours)

**Morning (3 hours)**:
1. ✅ Create `schema_53_fields.py` with nested Pydantic models
2. ✅ Update ground truth: Validate 23 new fields for brf_198532
   - Manual PDF review (pages 6-16)
   - Extract revenue breakdown (15 fields)
   - Extract loan 1 details (8 fields)
   - Save to `ground_truth/brf_198532_53_field_gt.json`

**Afternoon (3 hours)**:
3. ✅ Build few-shot example bank
   - Revenue breakdown: 3 examples (comprehensive, simple, scanned)
   - Loan 1 detailed: 3 examples (table, narrative, minimal)
   - Save to `config/few_shot_examples_sprint1.yaml`

**Deliverable**: Complete 53-field ground truth + 6 few-shot examples

---

### **Day 2: Revenue Breakdown Agent** (5 hours)

**Tasks**:
1. Create `revenue_breakdown_agent` prompt (2 hours)
   - Base prompt with 15 fields
   - Few-shot examples embedded
   - Swedish term synonyms
   - Cross-validation hints

2. Integrate into `base_brf_extractor.py` (1 hour)
   - Add to `AGENT_PROMPTS` dict
   - Add to page allocation logic

3. Test on brf_198532 (1 hour)
   - Run extraction
   - Validate against ground truth
   - Debug/fix issues

4. Test on brf_268882 (regression) (1 hour)
   - Ensure new agent doesn't break existing 30-field system
   - Check processing time impact

**Deliverable**: Working revenue breakdown agent with ≥85% accuracy

---

### **Day 3: Loan 1 Detailed Agent** (5 hours)

**Tasks**:
1. Create `loan_1_detailed_agent` prompt (2 hours)
   - Base prompt with 8 fields
   - Few-shot examples embedded
   - Swedish term synonyms
   - Loan table parsing hints

2. Integrate into `base_brf_extractor.py` (1 hour)
   - Add to `AGENT_PROMPTS` dict
   - Add to notes section routing

3. Test on brf_198532 (1 hour)
   - Run extraction
   - Validate against ground truth (4 loans expected, extract first)
   - Debug/fix issues

4. Test on brf_271852 (has 3 loans) (1 hour)
   - Ensure extracts FIRST loan only
   - Check comprehensive notes integration

**Deliverable**: Working loan 1 detailed agent with ≥85% accuracy

---

### **Day 4: Field-Level Synonym Mapping** (4 hours)

**Tasks**:
1. Create `field_level_synonyms.yaml` (3 hours)
   - 23 new fields × 4-6 synonyms each = ~100 mappings
   - Organize by field
   - Include confidence scores (for future fuzzy matching)

2. Update `swedish_financial_dictionary.py` (1 hour)
   - Add field-level lookup function
   - Integrate with existing section-level mapping

**Example Structure**:
```yaml
field_synonyms:
  nettoomsattning:
    canonical: "nettoomsattning"
    variants:
      - term: "Nettoomsättning"
        confidence: 1.0
      - term: "Nettoförsäljning"
        confidence: 0.95
      - term: "Intäkter av försäljning"
        confidence: 0.90
      - term: "Försäljningsintäkter"
        confidence: 0.85
    swedish_definition: "Intäkter från huvudsaklig verksamhet"
    english: "Net sales"
```

**Deliverable**: Complete field-level synonym database (23 fields)

---

### **Day 5: Testing & Validation** (6 hours)

**Tasks**:
1. Run 53-field extraction on all 10 PDFs (3 hours)
   - Same 10 PDFs from 30-field test
   - Collect metrics: coverage, accuracy, time, cost
   - Save results to `results/sprint1_10pdf_test/`

2. Analyze results vs 30-field baseline (2 hours)
   - Compare coverage (should stay ≥95%)
   - Compare accuracy (target ≥85%)
   - Compare cost (target ≤$0.16 vs $0.14)
   - Identify failures and patterns

3. Create Sprint 1 completion report (1 hour)
   - Metrics summary
   - Key findings
   - Recommend: Continue to Sprint 2 OR iterate

**Deliverable**: Sprint 1 completion report with go/no-go recommendation for Sprint 2

---

## 📊 Success Metrics

| Metric | Baseline (30F) | Target (53F) | Measurement |
|--------|----------------|--------------|-------------|
| **Coverage** | 100% | ≥95% | Extracted/Total on 10 PDFs |
| **Accuracy** | 100% | ≥85% | Correct/Extracted vs ground truth |
| **Cost per PDF** | $0.14 | ≤$0.16 | OpenAI API costs |
| **Processing Time** | 120s avg | ≤150s | Total extraction time |
| **Evidence Ratio** | 77.8% | ≥75% | Agents with evidence pages |
| **Correct Fields** | 27.6 | ≥45 | Absolute count (53 * 0.85) |

---

## 🚨 Risk Mitigation

### **Risk 1: Accuracy Drops Below 85%**

**Indicators**:
- Revenue breakdown extracts line items incorrectly
- Loan 1 extraction gets wrong loan (not first)
- Swedish term matching fails

**Mitigation**:
- Add more few-shot examples (up to 5 per field)
- Enhance synonym matching with fuzzy logic
- Add in-prompt validation hints

**Fallback**: If accuracy <80%, revert to 30-field system for production

---

### **Risk 2: Processing Time Exceeds 150s**

**Indicators**:
- New agents add 30+ seconds per PDF
- Total time approaches 200s

**Mitigation**:
- Reduce MAX_PAGES for new agents (8 instead of 12)
- Optimize page allocation (only send relevant pages)
- Consider parallel agent execution

**Fallback**: Accept 150-180s if quality justifies (2-3 minutes is acceptable for batch)

---

### **Risk 3: Cost Exceeds $0.16/PDF**

**Indicators**:
- New agents double token usage
- Total cost approaches $0.20

**Mitigation**:
- Use smaller images (150 DPI instead of 200 DPI)
- Reduce context length (fewer few-shot examples)
- Optimize prompts (more concise)

**Fallback**: Accept $0.16-$0.20 if accuracy justifies (still 53.6% cheaper than flat approach)

---

## 📋 Checklist

### Pre-Sprint
- [x] P0 exponential backoff retry logic implemented
- [x] Ultrathinking analysis reviewed
- [ ] Sprint 1 plan approved

### Day 1
- [ ] 53-field Pydantic schema created
- [ ] brf_198532 ground truth validated (23 new fields)
- [ ] 6 few-shot examples created (3 revenue + 3 loan)

### Day 2
- [ ] revenue_breakdown_agent prompt created
- [ ] Agent integrated into base_brf_extractor.py
- [ ] Tested on brf_198532 (≥85% accuracy)
- [ ] Regression test on brf_268882

### Day 3
- [ ] loan_1_detailed_agent prompt created
- [ ] Agent integrated into base_brf_extractor.py
- [ ] Tested on brf_198532 (≥85% accuracy)
- [ ] Tested on brf_271852 (3-loan case)

### Day 4
- [ ] field_level_synonyms.yaml created (23 fields)
- [ ] Swedish financial dictionary updated

### Day 5
- [ ] 10-PDF test executed (same PDFs as 30-field baseline)
- [ ] Results analyzed (coverage, accuracy, cost, time)
- [ ] Sprint 1 completion report created
- [ ] Go/No-Go decision for Sprint 2

---

## 🎯 Sprint 1 Completion Criteria

**PASS** if:
- ✅ ≥85% accuracy on 53 fields (ground truth validated)
- ✅ ≥95% coverage on 10 PDFs
- ✅ Cost ≤$0.16/PDF
- ✅ Processing time ≤150s
- ✅ No regressions on existing 30 fields

**PROCEED to Sprint 2** if PASS

**ITERATE Sprint 1** if:
- ⚠️ Accuracy 75-85% (fix with more examples)
- ⚠️ Coverage 85-95% (fix with better routing)

**STOP and reassess** if:
- ❌ Accuracy <75% (fundamental approach issue)
- ❌ Coverage <85% (routing broken)
- ❌ Cost >$0.20/PDF (not sustainable)

---

**Status**: Ready to start Day 1
**Next Action**: Create 53-field Pydantic schema
