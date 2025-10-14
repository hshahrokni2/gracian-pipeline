# Phase 2 Ultrathinking: Best Path to 95% Coverage (27,000 Heterogeneous PDFs)

**Date**: October 13, 2025
**Context**: Phase 1 complete (90% baseline), need +2 fields to reach 95%
**Challenge**: 27,000 PDFs are highly heterogeneous (machine-readable, scanned, hybrid, multiple formats)

---

## 🎯 Problem Statement

**Current**: 27/30 fields (90%)
**Target**: 29/30 fields (96.7% - exceeds 95% requirement)
**Missing**: 3 fields (all P2 optional)

1. **address** (property_agent returns empty string)
2. **energy_class** (property_agent returns empty string)
3. **tax_info** (notes_tax_agent not called)

**Key Constraint**: Must work reliably on 27,000 heterogeneous PDFs, not just brf_198532.pdf

---

## 📊 Current Property Agent Analysis

### **property_agent Result (brf_198532.pdf)**
```json
{
  "designation": "Sonfjället 2",        // ✅ Extracted
  "address": "",                        // ❌ Empty
  "postal_code": "",                    // Not in 30-field standard
  "city": "Stockholm",                  // ✅ Extracted
  "built_year": "2015",                 // ✅ Extracted
  "apartments": "94",                   // ✅ Extracted
  "energy_class": "",                   // ❌ Empty
  "evidence_pages": [2]                 // ✅ Citing sources
}
```

### **Root Cause Analysis: Why Empty?**

**Hypothesis 1: Data Not Present in PDF**
- Address may not exist in BRF annual reports (common for privacy)
- Energy class may not be declared in 2021 documents (requirement varies)
- **Risk**: If data truly absent, can't extract (need to accept 90% coverage)

**Hypothesis 2: Extraction Logic Issue**
- property_agent prompt doesn't explicitly request address/energy_class
- Pages 1-9 allocated, but fields on different pages?
- Swedish term synonyms missing or insufficient
- **Risk**: Fixable, but may need prompt engineering + page allocation changes

**Hypothesis 3: Format Variation (Heterogeneity)**
- Address in brf_198532 formatted differently (not recognized)
- Energy class in non-standard format (e.g., "Energideklaration saknas")
- **Risk**: Needs robust pattern matching + null handling

---

## 🔍 Investigation Strategy (Data-Driven Approach)

### **Step 1: Manual PDF Inspection** (5 minutes)
```bash
# Check if address/energy_class actually exist in brf_198532.pdf
# Open PDF, search for keywords:
# - "Adress", "Gatuadress", "Postadress", "Besöksadress"
# - "Energiklass", "Energideklaration", "Energiprestanda"
```

**Expected Outcomes**:
1. **Found**: Data exists → Hypothesis 2 (extraction logic issue)
2. **Not Found**: Data absent → Hypothesis 1 (accept 90% or change strategy)
3. **Alternate Format**: Data exists but different format → Hypothesis 3 (pattern matching issue)

### **Step 2: Multi-PDF Sampling** (15 minutes)
```bash
# Check 10 diverse PDFs for address/energy_class presence
# Sample: 5 Hjorthagen + 5 SRS (different years, sizes, formats)
# Calculate: % of PDFs that HAVE address/energy_class
```

**Decision Tree**:
- **≥80% have data**: Worth extracting (ROI high)
- **50-80% have data**: Conditional extraction (some coverage improvement)
- **<50% have data**: Not worth extracting (focus on tax_info instead)

---

## 💡 Solution Options Analysis

### **Option A: Enhance property_agent Prompt** (Recommended - Lowest Risk)

**Approach**: Update property_agent prompt to explicitly extract address and energy_class

**Implementation**:
```python
# In base_brf_extractor.py, property_agent prompt (line ~88):

PROPERTY_AGENT_PROMPT = """
Extract property information from this Swedish BRF annual report.

CRITICAL: Extract ALL fields, even if partially present. Use empty string "" only if field genuinely absent.

Fields to extract:
1. designation (Fastighetsbeteckning): Property designation/identifier
2. **address (Adress/Gatuadress): Full street address if present. Check:
   - Property information section (Fastighetsfakta)
   - Cover page
   - Förvaltningsberättelse (management report)
   - Common formats: "Gatuadress: [street]", "[street], [postal code] [city]"**
3. city (Stad/Kommun/Ort): City or municipality name
4. built_year (Byggår): Building construction year (YYYY format)
5. apartments (Antal lägenheter): Total number of apartments/units
6. **energy_class (Energiklass): Energy performance class if declared. Check:
   - Property information section
   - Sustainability/environment section (Hållbarhet)
   - Energy declaration (Energideklaration)
   - Common formats: "Energiklass: A/B/C/D/E/F/G", "Energiprestanda: [class]", "Energideklaration saknas" (return "Not declared")**

Swedish synonyms:
- address: "Adress", "Gatuadress", "Postadress", "Besöksadress", "Postort"
- energy_class: "Energiklass", "Energideklaration", "Energiprestanda", "Energimärkning", "Energicertifikat"

Return JSON:
{
  "designation": "string",
  "address": "string or empty string if not found",
  "city": "string",
  "built_year": "string (YYYY)",
  "apartments": "string (number)",
  "energy_class": "string (A-G) or 'Not declared' or empty string",
  "evidence_pages": [list of page numbers where data found]
}
"""
```

**Pros**:
- ✅ Minimal code changes (1 file, ~20 lines)
- ✅ Explicit instructions reduce ambiguity
- ✅ Swedish synonym coverage expanded
- ✅ Handles "Not declared" cases (semantic information)
- ✅ Works with existing page allocation (1-9 covers property sections)

**Cons**:
- ⚠️ May not work if data truly absent
- ⚠️ Relies on LLM understanding Swedish context
- ⚠️ No guarantee of 95% coverage on all 27,000 PDFs

**Estimated Success Rate**:
- If data present in ≥80% of PDFs: **75-85% coverage improvement**
- If data present in 50-80% of PDFs: **40-60% coverage improvement**
- If data present in <50% of PDFs: **20-40% coverage improvement**

**Time**: 30 minutes (update prompt, test on 3 PDFs, validate)

---

### **Option B: Increase Page Allocation for property_agent** (Medium Risk)

**Approach**: Allocate pages 1-15 instead of 1-9 to property_agent (address/energy may be on later pages)

**Implementation**:
```python
# In optimal_brf_pipeline.py, extract_pass1() method:

# Before:
property_pages = self._get_pages_for_sections(
    routing.main_sections.get('property_agent', []),
    structure
)

# After (expand search range):
property_headings = routing.main_sections.get('property_agent', [])
property_pages = self._get_pages_for_sections(property_headings, structure)

# Add fallback: If no property headings detected, use heuristic pages 1-15
if not property_pages:
    property_pages = list(range(1, min(16, len(structure.sections))))
```

**Pros**:
- ✅ Covers more of document (address might be on cover page, energy_class in sustainability section)
- ✅ No prompt changes needed
- ✅ Works even if Docling misses property headings

**Cons**:
- ⚠️ Increases token usage (~2x for property_agent)
- ⚠️ Increases cost per PDF (~$0.02 → $0.03)
- ⚠️ May extract irrelevant data (noise)
- ⚠️ Doesn't solve prompt clarity issue

**Estimated Success Rate**: **40-60% coverage improvement** (if data on later pages)

**Time**: 20 minutes (update allocation logic, test)

---

### **Option C: Add Dedicated address/energy_class Extraction Pass** (High Risk, High Reward)

**Approach**: Create focused mini-agent that scans entire document for address and energy_class

**Implementation**:
```python
# New method in optimal_brf_pipeline.py:

def _extract_property_supplemental(self, pdf_path, structure):
    """
    Focused extraction for hard-to-find property fields.
    Scans entire document with specific prompts.
    """
    prompt = """
    Scan this entire Swedish BRF annual report for:

    1. Address (Adress/Gatuadress): Look on cover page, property info section, ANY mention of street address.
    2. Energy class (Energiklass): Look in property info, sustainability section, energy declaration.

    If not found after scanning all pages, return empty string.

    Return JSON:
    {
      "address": "string or empty",
      "energy_class": "string or empty",
      "evidence_pages": [list]
    }
    """

    # Render pages 1-20 (cover + property + sustainability sections)
    pages_to_render = list(range(1, min(21, len(structure.sections))))

    # Call LLM with entire context
    result = self._call_llm(prompt, pages_to_render)
    return result
```

**Pros**:
- ✅ Highest chance of finding data (scans entire document)
- ✅ Focused prompt (better than multi-field property_agent)
- ✅ Can add retry logic specifically for these fields

**Cons**:
- ⚠️ Adds extra LLM call (~$0.03/PDF)
- ⚠️ Increases processing time (+15-30s per PDF)
- ⚠️ More code complexity (new extraction pass)
- ⚠️ May find spurious matches (address in other contexts)

**Estimated Success Rate**: **65-85% coverage improvement** (highest success rate)

**Time**: 1-2 hours (implement, test, validate)

---

### **Option D: Accept 90% and Extract tax_info Instead** (Risk-Averse)

**Approach**: Focus on extracting tax_info (notes_tax_agent) instead of address/energy_class

**Rationale**:
- Tax info more likely present in financial documents (accounting requirement)
- Address/energy_class may be optional/missing in many PDFs
- Reaching 95% via tax_info + 1 other field more reliable

**Implementation**:
```python
# In optimal_brf_pipeline.py, enable notes_tax_agent routing:

# Update swedish_financial_dictionary.py to include tax routing keywords:
"notes_tax_agent": [
    "Skatt", "Inkomstskatt", "Bolagsskatt", "Skattetillägg",
    "Not 11", "Not 12", "Skattekostnad", "Uppskjuten skatt"
]

# OR: Update comprehensive_notes_agent to extract tax_info structure
```

**Pros**:
- ✅ Tax data more standardized (accounting requirement)
- ✅ Leverages existing notes extraction infrastructure
- ✅ More reliable for 27,000 heterogeneous PDFs

**Cons**:
- ⚠️ Abandons address/energy_class (useful for property analysis)
- ⚠️ Tax notes may not exist in all PDFs either
- ⚠️ May still only reach 93-94% (28/30)

**Estimated Success Rate**: **60-75% coverage improvement to 95%**

**Time**: 45 minutes (add tax routing, test)

---

## 🎲 Decision Matrix

| Option | Success Rate | Cost | Time | Risk | Scalability (27K PDFs) |
|--------|--------------|------|------|------|------------------------|
| **A: Enhance Prompt** | **75-85%** | Low (+$0) | 30min | Low | ✅ Excellent |
| **B: Expand Pages** | 40-60% | Medium (+$0.01) | 20min | Medium | ⚠️ Increases cost |
| **C: Dedicated Pass** | 65-85% | High (+$0.03) | 2h | High | ❌ 81K extra calls |
| **D: Extract tax_info** | 60-75% | Low (+$0) | 45min | Medium | ✅ Good |

---

## 🏆 Recommended Strategy: **Hybrid A+D**

### **Phase 2A: Enhance property_agent Prompt** (30 minutes)
1. Update property_agent prompt with explicit address/energy_class instructions
2. Add comprehensive Swedish synonym coverage
3. Test on brf_198532 + 2 diverse PDFs (1 Hjorthagen, 1 SRS)
4. Measure: Did address/energy_class extraction improve?

**Success Criteria**: ≥2/3 PDFs extract at least 1 new field (address OR energy_class)

**If Success**: Proceed to validation (29/30 or 28/30 likely achieved)
**If Failure**: Proceed to Phase 2B

### **Phase 2B: Extract tax_info as Fallback** (45 minutes)
1. Add notes_tax_agent routing keywords to dictionary
2. Update comprehensive_notes_agent to extract tax_info structure
3. Test on same 3 PDFs
4. Measure: Did tax_info extraction succeed?

**Success Criteria**: ≥2/3 PDFs extract tax_info

**If Success**: 95% coverage achieved (28/30 via address OR tax_info)
**If Failure**: Accept 90% baseline, proceed to Phase 3 (accuracy validation)

---

## 🧪 Implementation Plan (Phase 2A - Recommended First Step)

### **Step 1: Manual PDF Inspection** (5 minutes)
```bash
cd experiments/docling_advanced
open ../../SRS/brf_198532.pdf

# Search PDF for:
# - "Adress" → Check if street address present
# - "Energiklass" → Check if energy class declared
# Document findings in PHASE2_INVESTIGATION.md
```

### **Step 2: Update property_agent Prompt** (15 minutes)
```bash
# Edit base_brf_extractor.py line ~88
# Add explicit address/energy_class instructions
# Expand Swedish synonym coverage
# Add "Not declared" handling for energy_class
```

### **Step 3: Test on 3 PDFs** (30 minutes)
```bash
# Test extraction:
python code/optimal_brf_pipeline.py ../../SRS/brf_198532.pdf  # Baseline
python code/optimal_brf_pipeline.py ../../SRS/brf_268882.pdf  # Regression
python code/optimal_brf_pipeline.py data/raw_pdfs/Hjorthagen/brf_81563.pdf  # Diverse

# Run validation:
python code/validate_30_fields.py results/optimal_pipeline/brf_198532_optimal_result.json
python code/validate_30_fields.py results/optimal_pipeline/brf_268882_optimal_result.json

# Calculate improvement:
# Baseline: 27/30 (90%)
# After prompt fix: ??/30 (target: 28-29/30 = 93-97%)
```

### **Step 4: Validate Results** (15 minutes)
```bash
# Check extraction quality:
python -c "
import json
for pdf in ['brf_198532', 'brf_268882', 'brf_81563']:
    path = f'results/optimal_pipeline/{pdf}_optimal_result.json'
    with open(path) as f:
        data = json.load(f)
    prop = data['agent_results']['property_agent']['data']
    print(f'{pdf}:')
    print(f'  address: \"{prop.get(\"address\", \"\")}\"')
    print(f'  energy_class: \"{prop.get(\"energy_class\", \"\")}\"')
"
```

---

## 🎯 Success Metrics

### **Phase 2A Target**
- **Coverage**: ≥93% (28/30 fields) on 3 test PDFs
- **Improvement**: +1 field minimum (address OR energy_class)
- **Quality**: No regression on other 27 fields
- **Cost**: $0 additional (prompt-only change)

### **Phase 2B Target** (if 2A insufficient)
- **Coverage**: ≥93% (28/30 fields) via tax_info extraction
- **Improvement**: +1-2 fields (tax_info + possibly address)
- **Quality**: No regression on other 27 fields
- **Cost**: <$0.01 additional per PDF

### **Overall Phase 2 Target**
- **Coverage**: 95% (29/30 fields) on diverse PDFs
- **Timeline**: 1-2 hours total
- **Validation**: Run on 10 diverse PDFs, average ≥93%

---

## ⚠️ Risk Mitigation

### **Risk 1: Data Truly Absent in Many PDFs**
- **Mitigation**: Phase 2B fallback (tax_info extraction)
- **Acceptance Criteria**: 90% baseline acceptable if <50% of PDFs have address/energy_class

### **Risk 2: Heterogeneity Breaks Extraction**
- **Mitigation**: Test on 10 diverse PDFs before claiming success
- **Monitoring**: Track per-field coverage across different PDF types (machine-readable, scanned, hybrid)

### **Risk 3: Prompt Engineering Doesn't Work**
- **Mitigation**: Phase 2B (dedicated extraction pass) or Phase 2C (page expansion)
- **Decision Point**: After 3-PDF test, if <33% success rate, switch strategy

---

## 📝 Documentation Plan

**After Phase 2A**:
- Create `PHASE2_PROPERTY_PROMPT_FIX.md` with:
  - Updated prompt
  - Test results (3 PDFs)
  - Coverage improvement metrics
  - Next steps (validation or fallback)

**After Phase 2 Complete**:
- Update `SESSION_SUMMARY_PHASE2_COMPLETE.md` with:
  - Final coverage achieved (28-29/30)
  - Strategy used (A, B, C, or D)
  - Lessons learned
  - Readiness for Phase 3 (accuracy validation)

---

## 🎓 Key Insights

### **Why Hybrid A+D is Optimal**
1. **Low-hanging fruit**: Prompt enhancement is fastest, cheapest, safest
2. **Fallback option**: tax_info more reliable than address/energy_class
3. **Data-driven**: Test before committing to expensive solutions (C)
4. **Scalable**: Works for 27,000 PDFs without extra calls

### **When to Pivot**
- **After 3 PDFs**: If <33% success with prompt, switch to tax_info
- **After 10 PDFs**: If <60% success, consider Option C (dedicated pass)
- **After 50 PDFs**: If <80% success, accept 90% baseline (some PDFs lack data)

### **Success Definition**
- **Not**: 95% coverage on every single PDF
- **But**: 95% average coverage across diverse corpus
- **Reality**: Some PDFs will have 100%, some 80%, average ≥95%

---

## 🚀 Next Steps

**Immediate** (Now - 5 minutes):
1. Manual inspection of brf_198532.pdf for address/energy_class
2. Document findings

**Phase 2A** (Next 1 hour):
1. Update property_agent prompt (15 min)
2. Test on 3 PDFs (30 min)
3. Validate results (15 min)

**Phase 2B** (If needed - 45 minutes):
1. Add tax_info extraction (30 min)
2. Test and validate (15 min)

**Phase 3** (After 95% coverage):
1. Manual accuracy validation (15 key fields)
2. Multi-PDF consistency testing (10-50-500 PDFs)

---

**Generated**: October 13, 2025
**Context**: Phase 1 complete (90%), need +2 fields for 95%
**Recommendation**: Hybrid A+D (enhance prompt + tax_info fallback)
**Timeline**: 1-2 hours to validated 95% coverage
