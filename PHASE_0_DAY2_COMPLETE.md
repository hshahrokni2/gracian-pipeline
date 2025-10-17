# ✅ PHASE 0 DAY 2 COMPLETE - AGENT PROMPT UPDATES

**Date**: 2025-10-17
**Duration**: 2 hours
**Status**: ✅ **COMPLETE** - All agent prompts updated with relative field names + 2 new agents created
**Branch**: docling-driven-gracian-pipeline

---

## 🎯 **SESSION OBJECTIVE**

Update all agent prompts to use relative year naming (from Day 1 fix) and create new agent prompts for Phase 0 enhancements.

---

## ✅ **WORK COMPLETED**

### **1. Updated Existing Agent Prompts** (3 agents)

#### **loans_agent** (Lines 432-561)
**Changes**:
- `interest_expense_2023` → `interest_expense_current_year`
- `interest_expense_2022` → `interest_expense_prior_year`

**Refinancing Logic**: ✅ Already present (validated on 100% of corpus)
- EXTREME: >60% kortfristig with <12 month cluster
- HIGH: >50% kortfristig AND (soliditet <75% OR profitability negative)
- MEDIUM: 30-50% kortfristig
- LOW: <30% kortfristig AND soliditet >80% AND profitable

#### **energy_agent** (Lines 576-620)
**Changes**:
- Added `electricity_yoy_increase_percent` (year-over-year, not hardcoded years)
- Added `heating_yoy_increase_percent`
- Added `water_yoy_increase_percent`
- `elstod_received` → `government_energy_support_current_year`

**Multi-Year Analysis**: ✅ Already present with severity tiers
- SEVERE: >50% single-year OR >100% multi-year
- MODERATE: 20-50% single-year OR 50-100% multi-year
- LOW: <20% single-year AND <50% multi-year
- NONE: No significant increase

#### **fees_agent** (Lines 622-697)
**Changes**:
- Added `fee_increase_count_current_year` field
- Added instructions for detecting multiple fee adjustments within fiscal year

**Multiple Fee Detection**: ✅ Pattern documented (19% of corpus)
- Look for: "höjdes med X% i [månad]", "ytterligare höjning"
- Example: "+3% February + +15% August" = count: 2

---

### **2. Created New Agent Prompts** (2 agents)

#### **key_metrics_agent** (Lines 809-866) - ✅ **NEW AGENT**
**Purpose**: Depreciation Paradox Detection (4.7% of corpus)

**Fields Extracted**:
```json
{
  "result_without_depreciation_current_year": int or null,
  "result_without_depreciation_prior_year": int or null,
  "depreciation_as_percent_of_revenue_current_year": float or null,
  "depreciation_paradox_detected": bool or null,
  "soliditet_pct": float or null,
  "evidence_pages": []
}
```

**Detection Criteria** (Both must be true):
1. result_without_depreciation_current_year ≥ 500,000 SEK (strong cash flow)
2. soliditet ≥ 85% (high equity cushion)

**Real Example**: brf_82839
- Annual result: -313,943 kr (paper loss)
- Depreciation: +1,371,024 kr
- **Result without depreciation: +1,057,081 kr** (strong cash flow!)
- Soliditet: 85%
- **Pattern**: K2 accounting creates paper loss but actual cash flow is excellent

#### **balance_sheet_agent** (Lines 868-932) - ✅ **NEW AGENT**
**Purpose**: Cash Crisis Detection (2.3% of corpus, but SEVERE when occurs)

**Fields Extracted**:
```json
{
  "total_liquidity_current_year": int or null,
  "total_liquidity_prior_year": int or null,
  "cash_to_debt_ratio_current_year": float or null,
  "cash_to_debt_ratio_prior_year": float or null,
  "cash_to_debt_ratio_prior_2_years": float or null,
  "cash_crisis_detected": bool or null,
  "short_term_debt_pct": float or null,
  "evidence_pages": []
}
```

**Detection Criteria** (All three must be true):
1. cash_to_debt_ratio_current_year < 5% (liquidity stress)
2. cash_to_debt_ratio < cash_to_debt_ratio_prior_year (deteriorating)
3. short_term_debt_pct > 50% (refinancing pressure)

**Real Example**: brf_80193
- Liquidity: 1,053k → 286k kr (-73% collapse!)
- Cash-to-debt ratio: 5.2% → 3.7% → 0.9% (3-year deterioration)
- Short-term debt: 95.9%
- **Pattern**: Rapid cash depletion + refinancing pressure = liquidity crisis

---

## 📊 **SUMMARY OF CHANGES**

### **Agent Prompts Updated**: 5 total

| Agent | Type | Changes |
|-------|------|---------|
| **loans_agent** | Updated | 2 fields renamed to relative naming |
| **energy_agent** | Updated | 4 fields added/renamed to relative naming |
| **fees_agent** | Updated | 1 field added (multiple adjustments detection) |
| **key_metrics_agent** | Created | 6 fields (depreciation paradox detection) |
| **balance_sheet_agent** | Created | 8 fields (cash crisis detection) |

### **Total Fields Using Relative Naming**: 21 fields

**From Day 1 Schema (17 fields)**:
- 2 loans fields
- 4 tomträtt fields
- 1 fee field
- 1 energy support field
- 3 depreciation fields
- 5 cash crisis fields
- 1 lokaler revenue (financial_agent)

**From Day 2 Agent Prompts (4 additional)**:
- 3 energy YoY increase fields
- 1 fee increase count field

---

## ✅ **VERIFICATION CHECKLIST**

- [x] All hardcoded year references replaced with relative naming
- [x] loans_agent: interest_expense fields updated
- [x] energy_agent: YoY fields added, government support renamed
- [x] fees_agent: fee_increase_count field added with detection logic
- [x] key_metrics_agent: Created with depreciation paradox detection
- [x] balance_sheet_agent: Created with cash crisis detection
- [x] All agents use anti-hallucination rules
- [x] All agents specify Swedish keywords and search locations
- [x] All agents include real examples from corpus
- [x] All agents follow consistent format and structure

---

## 🎯 **KEY INSIGHTS**

### **1. Relative Year Naming is Universal**
Every agent now uses relative naming (`_current_year`, `_prior_year`, `_prior_2_years`) instead of hardcoded years. This ensures:
- Schema works for ANY fiscal year (2015-2030+)
- No schema changes needed when processing different years
- Consistent with existing codebase patterns (synonyms.py)

### **2. Pattern Detection is Core Functionality**
Both new agents (key_metrics, balance_sheet) focus on detecting specific patterns:
- **Depreciation Paradox**: Identifies BRFs with strong cash flow despite paper losses
- **Cash Crisis**: Identifies BRFs with liquidity stress and refinancing pressure

These patterns were validated on 43 PDFs and represent material risks/opportunities in the corpus.

### **3. Multi-Year Trend Analysis is Essential**
All financial agents now track year-over-year changes:
- **Loans**: Interest expense changes (interest rate crisis detection)
- **Energy**: Electricity/heating/water cost trends (energy crisis severity)
- **Cash**: Liquidity trends (cash crisis deterioration)
- **Depreciation**: Multi-year profitability vs cash flow analysis

### **4. Evidence-Based Extraction**
All agents require:
- Exact values visible in documents (no inference)
- Source page citations (evidence_pages)
- Swedish keyword matching (not English translations)
- Anti-hallucination rules (strict validation)

---

## 📁 **FILES MODIFIED**

1. **gracian_pipeline/prompts/agent_prompts.py** (927 lines → 1,051 lines)
   - Updated 3 existing agents (loans, energy, fees)
   - Created 2 new agents (key_metrics, balance_sheet)
   - +124 lines added

**Git Diff Summary**:
- 5 agents modified/created
- 21 fields using relative year naming
- 2 new pattern detection agents
- Real examples from corpus added
- Anti-hallucination rules strengthened

---

## 🚀 **NEXT STEPS** (Day 3+)

### **Phase 0 Day 3**: Agent Testing & Validation (4 hours)
- Test all 5 updated/new agents on sample PDFs
- Verify field extraction works with relative naming
- Validate pattern detection (depreciation paradox, cash crisis)
- Check consistency with schema_comprehensive.py

### **Phase 0 Day 4**: Pattern Flags & Scoring (4 hours)
- Implement pattern classification logic
- Create scoring system for risk assessment
- Add pattern flags to extraction results
- Test on diverse PDF samples

### **Phase 0 Day 5**: Documentation & Handoff (4 hours)
- Document all Phase 0 enhancements
- Create testing guide for Week 2 re-extraction
- Prepare schema migration notes
- Final validation checklist

---

## 💡 **CRITICAL REMINDERS FOR FUTURE SESSIONS**

### **1. Agent Prompt Consistency**
All agent prompts now follow this structure:
```
1. Agent description and mission
2. Pattern detection criteria (if applicable)
3. JSON return structure with ALL fields
4. Real examples from corpus
5. Where to look (sections, pages)
6. Swedish keywords
7. Anti-hallucination rules
8. Return format instruction
```

### **2. Relative Year Naming Convention**
**ALWAYS use**:
- `*_current_year` = Fiscal year from metadata.fiscal_year
- `*_prior_year` = One year before current
- `*_prior_2_years` = Two years before current

**NEVER use**:
- `*_2023`, `*_2022`, `*_2021` (hardcoded years)
- Exception: Real examples showing actual data (clearly marked as examples)

### **3. Pattern Detection Validation**
Before implementing pattern detection in agents:
- Validate pattern exists in corpus (>5% prevalence for universal patterns)
- Document real examples with specific PDF references
- Define clear detection criteria (quantitative thresholds)
- Specify Swedish keywords for pattern matching

---

## 📚 **REFERENCES**

**Analysis Documents**:
- `ULTRATHINKING_YEAR_NAMING_STRATEGY.md` (364 lines) - Relative naming rationale
- `YEAR_NAMING_FIX_COMPLETE.md` (368 lines) - Day 1 schema fix
- `AGENT_PROMPT_UPDATES_PENDING.md` (1,097 lines) - Pattern validation on 43 PDFs

**Schema Files**:
- `config/schema_v2_fields.yaml` (712 lines) - Field specifications
- `gracian_pipeline/core/schema_comprehensive.py` (428 lines) - Pydantic schema
- `gracian_pipeline/prompts/agent_prompts.py` (1,051 lines) - Agent prompts

**Validation Evidence**:
- Depreciation paradox: 2/43 PDFs (4.7%) - brf_82839, brf_82841
- Cash crisis: 1/43 PDFs (2.3%) - brf_80193
- Multiple fees: 8/43 PDFs (18.6%) - brf_276796, brf_280938, etc.
- Refinancing risk: 43/43 PDFs (100%) - universal pattern

---

## ✅ **COMPLETION CRITERIA MET**

- ✅ All agent prompts updated with relative year naming
- ✅ 2 new agents created (key_metrics, balance_sheet)
- ✅ Pattern detection logic documented with real examples
- ✅ Anti-hallucination rules applied consistently
- ✅ Swedish keywords and search locations specified
- ✅ All changes align with Day 1 schema updates
- ✅ No hardcoded year references remain (except in examples)
- ✅ Ready for Day 3 testing and validation

---

**Status**: ✅ **PHASE 0 DAY 2 COMPLETE**
**Next**: Day 3 - Agent Testing & Validation (4 hours)
**Timeline**: On track for 4-week Phase 0 completion

🙏 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
