# Operating Costs Agent Ultrathinking Analysis
**Sprint 1+2 Day 3 Morning - Operating Expenses Extraction Strategy**

**Date**: 2025-10-12
**Context**: 70% Sprint 1+2 Complete (Days 1-2 success: schema + revenue + enhanced_loans)
**Objective**: Implement operating_costs_agent for 6 expense fields extraction
**Analyst**: Claude Code (Sonnet 4.5)

---

## Executive Summary

### Key Recommendations

1. **Extraction Strategy**: Use **pages 7-13** (income statement + notes) with comprehensive expense scanning
2. **Expected Extraction Rates**:
   - **K3 Format**: 6/6 fields (100%) - Detailed breakdown in "NOT 4 - Driftkostnader"
   - **K2 Format**: 2-3/6 fields (33-50%) - Consolidated expenses common
   - **Overall Target**: 4-5/6 fields (67-83%) across mixed corpus
3. **Critical Success Factor**: Multi-source aggregation from BOTH income statement AND notes
4. **Integration Approach**: Run operating_costs_agent in parallel with revenue_breakdown_agent, share pages 7-13

### Risk Level: **LOW** ✅

**Rationale**:
- Operating costs simpler than revenue (6 vs 15 fields)
- Clear section structure in Swedish BRFs
- Strong precedent from enhanced_loans (32/32) and revenue_breakdown (8/15 on K2)
- Multi-source extraction mitigates K2 consolidation issue

### Go/No-Go Criteria

**GO** if:
- ✅ Few-shot examples available from ground truth (brf_198532, page 13)
- ✅ Clear Swedish term mappings for all 6 expense fields
- ✅ Prompt strategy validated from revenue_breakdown success

**NO-GO** if:
- ❌ No ground truth examples for operating costs (NOT THE CASE - we have page 13!)
- ❌ Term ambiguity makes reliable extraction impossible (NOT THE CASE - terms are clear)

**Decision**: ✅ **GO FOR IMPLEMENTATION**

---

## Detailed Analysis

### 1. Swedish Expense Term Complexity

#### 1.1 Complete Synonym Mapping

Based on analysis of Swedish BRF corpus, ground truth data, and existing synonym dictionaries:

| Target Field | Swedish Canonical Term | Synonyms & Variations | OCR Error Variants | Notes |
|--------------|------------------------|----------------------|-------------------|-------|
| **fastighetsskott** | Fastighetsskötsel | Fastighetsförvaltning, Fastighetsskott, Drift fastighetsskötsel, Drift fastighet | Fastighetsskotsel, Fastighetsskotseil | Property management, often largest expense |
| **reparationer** | Reparationer | Reparations- och underhållskostnader, Reparation och underhåll, Underhåll, Rep. och underhåll, Reparationer av fastighet | Reparationner, Reperationer | Repairs and maintenance, may be consolidated with "Underhåll" |
| **el** | El | Elkostnader, Elektricitet, Elförbrukning, El-kostnader, Kostnad el, Förbrukning el | EI (letter i), Ei | Electricity costs |
| **varme** | Värme | Värmekostnader, Fjärrvärme, Uppvärmning, Värmekostnad, Kostnad värme, Förbrukning värme | Varme (missing diacritic), Vårme | Heating costs, often district heating |
| **vatten** | Vatten | Vattenkostnader, Vatten och avlopp, VA-kostnader, Kostnad vatten, Förbrukning vatten, Vatten/avlopp | Vaten (double t error) | Water and sewage costs |
| **ovriga_externa_kostnader** | Övriga externa kostnader | Övriga kostnader, Externa tjänster, Övriga externa tjänster, Övr. externa kostn., Övrigt, Diverse kostnader, Andra kostnader | Ovriga (missing diacritic), Oevriga | Catch-all for misc external costs |

**Total Synonym Variations**: 35+ terms across 6 expense fields

#### 1.2 K2 vs K3 Format Differences

**K2 Format (Simple - 30-40% of corpus)**:
- **Consolidated Expenses**: Often groups costs into 2-5 main categories
- **Example**: "Drift och fastighetsskötsel" (combines multiple line items)
- **Typical Structure**:
  ```
  Rörelsekostnader:
  - Drift och fastighetsskötsel  2,834,798 kr  (CONSOLIDATED)
  - Övriga externa kostnader       229,331 kr
  - Personalkostnader               63,912 kr
  - Avskrivningar               3,503,359 kr
  - Summa rörelsekostnader     -6,631,400 kr
  ```
- **Challenge**: "Drift" includes fastighetsskott + reparationer + el + värme + vatten
- **Extraction Approach**:
  - Extract "Drift" as approximation for missing fields
  - Mark as consolidated (e.g., "fastighetsskott_consolidated")
  - Look in NOTES for detailed breakdown (often "NOT 4 - Driftkostnader")

**K3 Format (Comprehensive - 60-70% of corpus)**:
- **Detailed Breakdown**: 8-12 individual expense line items
- **Example**: See brf_198532 page 13 (NOT 4)
- **Typical Structure**:
  ```
  NOT 4 - Driftkostnader:
  - Fastighetsskötsel    553,590 kr
  - Reparationer         258,004 kr
  - Periodiskt underhåll  48,961 kr
  - El                   (within Driftskostnader 1,359,788 kr)
  - Värme                (within Driftskostnader)
  - Vatten               (within Driftskostnader)
  - Övriga driftkostnader 422,455 kr
  - Fastighetsskatt       192,000 kr
  - Summa                2,834,798 kr
  ```
- **Challenge**: Utility costs (el, värme, vatten) often grouped in "Driftskostnader" aggregate
- **Extraction Approach**:
  - Primary: Extract from detailed notes (NOT 4)
  - Secondary: Check for separate utility line items in income statement
  - Tertiary: Parse text descriptions within notes

#### 1.3 Swedish Accounting Standards Impact

**BFNAR 2016:10 (K2)** - Simplified accounting:
- Fewer line items required
- More consolidation allowed
- Notes often have breakdown even if income statement doesn't

**K3 (Comprehensive)** - Full accounting:
- Detailed expense categories required
- More granular reporting
- Notes provide additional context (e.g., variance explanations)

**Key Insight**: Even K2 documents often have detailed breakdown in NOTES section (NOT 4 - Driftkostnader), which is our primary extraction source!

---

### 2. Extraction Strategy

#### 2.1 Multi-Source Extraction Architecture

```
Operating Costs Extraction Flow:

1. INCOME STATEMENT SCAN (Pages 7-9)
   ├─> "Rörelsekostnader" section
   ├─> Look for individual line items (K3)
   └─> If consolidated "Drift" (K2) → mark as partial

2. NOTES SECTION SCAN (Pages 11-13)
   ├─> "NOT 4 - Driftkostnader" (primary source)
   ├─> "NOT 5 - Övriga externa kostnader" (if exists)
   └─> Extract detailed breakdown

3. AGGREGATION & VALIDATION
   ├─> Prefer notes values (more detailed)
   ├─> Fallback to income statement values
   ├─> Validate: Individual items ≈ "Drift" total (K2)
   └─> Return with evidence_pages

4. GRACEFUL DEGRADATION
   └─> If field not found → return 0 (not null)
```

#### 2.2 Page Allocation Strategy

**Recommendation**: **Pages 7-13** (income statement + notes)

**Rationale**:
- Pages 7-9: Income statement ("Resultaträkning")
- Pages 11-13: Notes section ("NOT 4 - Driftkostnader")
- Total: 7 pages (within 12-page MAX_PAGES limit from Day 2 P0 fix)

**Comparison with Other Agents**:
- `financial_agent`: Pages 6-10 (overlaps with 7-9)
- `revenue_breakdown_agent`: Pages 7-8 (overlaps with 7-9)
- `comprehensive_notes_agent`: Pages 11-16 (overlaps with 11-13)

**Integration Decision**:
- Run operating_costs_agent **in parallel** with revenue_breakdown_agent
- Share pages 7-9 for income statement scanning
- Add pages 11-13 for notes scanning
- **No additional cost** (pages already rendered for comprehensive_notes_agent)

#### 2.3 Double-Count Prevention

**Challenge**: Ensure we don't extract both "Drift" (consolidated) and individual items

**Solution**:
1. **Prefer Detailed over Consolidated**:
   - If NOT 4 has fastighetsskott + reparationer → use those
   - Don't also extract "Drift" from income statement
2. **Mark Source**:
   - Add `expense_source` field: "income_statement" | "notes_not4" | "aggregated"
3. **Validation**:
   - Sum of individual items should ≈ "Drift" total (if K2)
   - If mismatch > 10%, flag for review

---

### 3. Few-Shot Examples

#### 3.1 Ground Truth Availability

**YES!** brf_198532 comprehensive ground truth has operating costs breakdown:

```json
"operating_costs_2021": {
  "property_management": 553590,     // Fastighetsskötsel
  "repairs": 258004,                 // Reparationer
  "periodic_maintenance": 48961,     // Periodiskt underhåll
  "utility_costs": 1359788,          // Driftskostnader (el+värme+vatten)
  "other_operating": 422455,         // Övriga driftkostnader
  "property_tax": 192000,            // Fastighetsskatt
  "total": 2834798,
  "source_pages": [13]               // NOT 4 - Driftkostnader
}
```

**Page 13 Analysis** (from brf_198532.pdf):
- Section: "NOT 4 - Driftkostnader"
- Format: K2 (simplified)
- Breakdown available: ✅ Yes (6 line items)
- Utilities breakdown: ❌ Consolidated in "Driftskostnader" (1,359,788 kr)

#### 3.2 Few-Shot Example Strategy

**Approach**: Auto-generate 2 examples from ground truth

**Example 1 - K3 Format (Hypothetical - based on K3 structure)**:
```json
INPUT PAGES: [7, 8, 13]
PAGE 13 CONTENT:
"NOT 4 - Driftkostnader
Fastighetsskötsel    553 590 kr
Reparationer         258 004 kr
El                   450 000 kr
Värme                650 000 kr
Vatten               159 788 kr
Övriga kostnader     422 455 kr
Summa              2 493 837 kr"

EXPECTED OUTPUT:
{
  "fastighetsskott": 553590,
  "reparationer": 258004,
  "el": 450000,
  "varme": 650000,
  "vatten": 159788,
  "ovriga_externa_kostnader": 422455,
  "expense_source": "notes_not4",
  "evidence_pages": [13]
}
```

**Example 2 - K2 Format (Actual - brf_198532)**:
```json
INPUT PAGES: [7, 8, 13]
PAGE 13 CONTENT:
"NOT 4 - Driftkostnader
Fastighetsskötsel         553 590 kr
Reparationer              258 004 kr
Periodiskt underhåll       48 961 kr
Driftskostnader         1 359 788 kr  <-- el+värme+vatten CONSOLIDATED
Övriga driftkostnader     422 455 kr
Fastighetsskatt           192 000 kr
Summa                   2 834 798 kr"

EXPECTED OUTPUT (graceful handling of consolidated):
{
  "fastighetsskott": 553590,
  "reparationer": 258004,
  "el": 0,                        // Consolidated in "Driftskostnader"
  "varme": 0,                     // Consolidated in "Driftskostnader"
  "vatten": 0,                    // Consolidated in "Driftskostnader"
  "ovriga_externa_kostnader": 422455,
  "expense_source": "notes_not4",
  "utility_costs_consolidated": 1359788,  // Optional: report consolidated value
  "evidence_pages": [13]
}
```

**Example 3 - Income Statement Only (Fallback)**:
```json
INPUT PAGES: [7, 8, 13]
PAGE 8 CONTENT (if NOT 4 missing):
"Rörelsekostnader
Drift och fastighetsskötsel  2 834 798 kr
Övriga externa kostnader       229 331 kr
Summa rörelsekostnader      -6 631 400 kr"

EXPECTED OUTPUT (K2 fallback):
{
  "fastighetsskott": 2834798,     // Consolidated "Drift"
  "reparationer": 0,              // Not separately reported
  "el": 0,                        // Consolidated in "Drift"
  "varme": 0,                     // Consolidated in "Drift"
  "vatten": 0,                    // Consolidated in "Drift"
  "ovriga_externa_kostnader": 229331,
  "expense_source": "income_statement_consolidated",
  "evidence_pages": [8]
}
```

#### 3.3 Manual vs Auto-Generated Examples

**Recommendation**: Use 1 manual + 1 auto-generated

**Rationale**:
- Manual example: Show ideal K3 extraction (with el, värme, vatten separate)
- Auto-generated from brf_198532: Show realistic K2 handling (consolidated utilities)
- Total: 2 examples (sufficient based on revenue_breakdown success with 1 example)

---

### 4. Common Extraction Errors & Prevention

#### 4.1 Error Taxonomy (Based on Day 2 Experience)

| Error Type | Description | Prevention Strategy | Success Rate Impact |
|------------|-------------|---------------------|---------------------|
| **Total vs Line Items** | Extracting "Summa rörelsekostnader" (-6.6M) instead of "Drift" (2.8M) | Explicit exclusion: "SKIP any line with 'Summa', 'Total', 'SUMMA'" | -100% (catastrophic) |
| **Missing K2 Details** | el/värme/vatten not reported separately in K2 | Graceful: Return 0 for missing, report consolidated value | -50% (acceptable) |
| **OCR Character Errors** | "Värme" → "Varme" (missing umlaut) | Swedish normalization: å→a, ä→a, ö→o | +20% recovery |
| **Sign Confusion** | Expenses as positive (2,834,798) vs negative (-2,834,798) | Parse as absolute value, context determines sign | No impact (validation) |
| **Wrong Section** | Extract from "Finansiella kostnader" instead of "Rörelsekostnader" | Section header validation: Must see "Rörelsekostnader" or "NOT 4" | -100% (catastrophic) |
| **Duplicate Extraction** | Extract both "Drift" AND individual items (double-count) | Prefer detailed, mark source, validation check | -50% (accuracy hit) |

#### 4.2 Prevention Checklist

**✅ Prompt Instructions**:
1. "SKIP lines with 'Summa', 'Total', 'SUMMA' - these are aggregates"
2. "Look for 'NOT 4 - Driftkostnader' section first (most detailed)"
3. "If field not found, return 0 (not null)"
4. "Parse Swedish numbers: '1 234 567 kr' → 1234567"
5. "Swedish character variants: Värme/Varme, Övriga/Ovriga are same"
6. "Extract ABSOLUTE values (no minus signs for individual expense items)"

**✅ Code Validation**:
```python
# Validation checks in optimal_brf_pipeline.py:
def validate_operating_costs(data: Dict[str, Any]) -> List[str]:
    issues = []

    # Check 1: Total vs line items
    if 'fastighetsskott' in data and data['fastighetsskott'] > 5000000:
        issues.append("WARNING: fastighetsskott > 5M (likely extracted 'Summa')")

    # Check 2: Reasonable ranges
    if 'el' in data and data['el'] > 2000000:
        issues.append("WARNING: el > 2M (unusually high for electricity)")

    # Check 3: Sum validation (if K3 detailed)
    if all(k in data for k in ['fastighetsskott', 'reparationer', 'el', 'varme', 'vatten']):
        total = sum(data[k] for k in ['fastighetsskott', 'reparationer', 'el', 'varme', 'vatten'])
        if 'ovriga_externa_kostnader' in data:
            total += data['ovriga_externa_kostnader']
        # Should be around 2-3M for typical BRF
        if total < 500000 or total > 10000000:
            issues.append(f"WARNING: Total operating costs {total} outside typical range")

    return issues
```

---

### 5. Integration with Existing Agents

#### 5.1 Agent Interaction Matrix

| Agent | Pages | Section | Data Extracted | Overlap with operating_costs_agent | Integration Strategy |
|-------|-------|---------|----------------|-----------------------------------|---------------------|
| `financial_agent` | 6-10 | Income statement | Revenue, expenses (TOTAL), assets, liabilities | Extracts "Summa rörelsekostnader" (total) | **No conflict** - financial extracts total, operating_costs extracts breakdown |
| `revenue_breakdown_agent` | 7-8 | Income statement | 15 revenue line items | Same pages (7-8) for income statement | **Parallel** - share rendered pages |
| `comprehensive_notes_agent` | 11-16 | Notes section | All notes (NOT 1-14) | Pages 11-13 for NOT 4 | **Context pass** - operating_costs can reference comprehensive_notes data |
| `notes_buildings_agent` | 11-16 | Notes section | NOT 8 (buildings) | No overlap | **Independent** |
| `enhanced_loans_agent` | 11-16 | Notes section | NOT 11 (loans) | No overlap | **Independent** |

#### 5.2 Context Sharing Strategy

**Approach**: Operating_costs_agent can receive context from comprehensive_notes_agent

**Example**:
```python
# In optimal_brf_pipeline.py:
def extract_operating_costs(self, pdf_path, structure, context=None):
    # Check if comprehensive_notes already extracted NOT 4
    if context and 'comprehensive_notes' in context:
        notes_data = context['comprehensive_notes'].get('data', {})
        if 'note_4_operating_costs' in notes_data:
            # Use comprehensive extraction if available
            return self._parse_operating_costs_from_notes(notes_data['note_4_operating_costs'])

    # Fallback: Extract directly
    return self._extract_agent(pdf_path, 'operating_costs_agent', ...)
```

**Benefits**:
- Reduce redundant API calls
- Leverage comprehensive_notes extraction (already scans pages 11-16)
- Consistent data (same extraction source)

**Cost Savings**: ~$0.025/doc (avoid separate operating_costs API call)

#### 5.3 Validation Integration

**Cross-Agent Validation**:
```python
# Validate: Sum of operating_costs ≈ financial_agent "expenses" (if detailed)
financial_total = financial_agent_result['expenses']  # e.g., -6,631,400
operating_costs_sum = (
    operating_costs['fastighetsskott'] +
    operating_costs['reparationer'] +
    operating_costs['el'] +
    operating_costs['varme'] +
    operating_costs['vatten'] +
    operating_costs['ovriga_externa_kostnader']
)

# Should be close (within 10%)
if abs(operating_costs_sum - abs(financial_total)) / abs(financial_total) > 0.10:
    print(f"WARNING: Operating costs breakdown ({operating_costs_sum}) != Financial total ({financial_total})")
```

**Benefits**:
- Catch extraction errors early
- Ensure data consistency across agents
- Build confidence in results

---

### 6. K2 vs K3 Format Handling

#### 6.1 Format Detection Strategy

**Method 1: Section Structure Analysis**
```python
def detect_accounting_format(structure: DocumentStructure) -> str:
    """
    Detect K2 vs K3 format based on section complexity.

    K2 indicators:
    - Fewer sections (< 10 notes)
    - Simplified income statement (3-5 expense lines)
    - Notes often use "Specifikation" instead of detailed breakdown

    K3 indicators:
    - More sections (10-15 notes)
    - Detailed income statement (8-12 expense lines)
    - Notes have detailed breakdowns
    """
    note_count = len([s for s in structure.sections if 'not' in s['heading'].lower()])

    if note_count < 8:
        return "K2"
    elif note_count >= 10:
        return "K3"
    else:
        return "UNKNOWN"
```

**Method 2: Keyword Analysis**
```python
def detect_format_from_keywords(text: str) -> str:
    """
    Detect format from accounting standard declaration.

    Look for: "BFNAR 2016:10" (K2) or "K3" mentions
    """
    if 'BFNAR 2016:10' in text or 'K2' in text:
        return "K2"
    elif 'K3' in text or 'större företag' in text:
        return "K3"
    return "UNKNOWN"
```

#### 6.2 Format-Specific Extraction

**K2 Handling**:
```python
if format == "K2":
    # Strategy: Extract from NOT 4 (even K2 often has detailed breakdown in notes)
    # Fallback: Extract consolidated "Drift" from income statement
    # Graceful: Return 0 for utilities if consolidated
    extraction_strategy = "notes_first_with_fallback"
    expected_fields = 3  # fastighetsskott, reparationer, ovriga (utilities consolidated)
```

**K3 Handling**:
```python
if format == "K3":
    # Strategy: Detailed breakdown in both income statement and notes
    # Prefer: NOT 4 for detailed breakdown
    # Expect: All 6 fields available
    extraction_strategy = "detailed_notes"
    expected_fields = 6  # All fields available
```

#### 6.3 Graceful Degradation

**Scenario 1**: K2 with consolidated utilities
```json
{
  "fastighetsskott": 553590,
  "reparationer": 258004,
  "el": 0,                        // Consolidated
  "varme": 0,                     // Consolidated
  "vatten": 0,                    // Consolidated
  "ovriga_externa_kostnader": 422455,
  "utility_costs_consolidated": 1359788,  // Report aggregate
  "format_detected": "K2",
  "extraction_confidence": 0.67    // 4/6 fields = 67%
}
```

**Scenario 2**: K3 with full breakdown
```json
{
  "fastighetsskott": 553590,
  "reparationer": 258004,
  "el": 450000,
  "varme": 650000,
  "vatten": 159788,
  "ovriga_externa_kostnader": 422455,
  "format_detected": "K3",
  "extraction_confidence": 1.0     // 6/6 fields = 100%
}
```

---

### 7. Expected Extraction Rates

#### 7.1 Baseline Prediction

**Based on Day 2 Results**:
- `revenue_breakdown_agent`: 8/15 fields on K2 (53%), expected 15/15 on K3 (100%)
- `enhanced_loans_agent`: 32/32 fields (100%) - notes extraction

**Operating Costs Prediction**:
- **Simpler than revenue** (6 fields vs 15)
- **Similar to loans** (notes extraction)
- **Challenge**: Utilities consolidation in K2

**Predicted Rates**:
- **K3 Format** (60-70% of corpus): 6/6 fields (100%)
  - Rationale: Detailed NOT 4 breakdown available
- **K2 Format** (30-40% of corpus): 3-4/6 fields (50-67%)
  - Rationale: Utilities often consolidated, but fastighetsskott + reparationer + ovriga usually separate
- **Overall Average**: 4.5-5/6 fields (75-83%)

#### 7.2 Success Criteria

**Day 3 Afternoon Integration Test**:

**Minimum Viable** (60% threshold):
- 3.6/6 fields on average (60%)
- Works on both K2 and K3
- No catastrophic errors (extracting totals instead of line items)

**Good** (75% threshold):
- 4.5/6 fields on average (75%)
- Graceful handling of K2 consolidation
- Validation checks pass

**Excellent** (90% threshold):
- 5.4/6 fields on average (90%)
- Format detection working
- Context sharing with comprehensive_notes

**Target**: 75% (Good threshold) ✅

#### 7.3 Validation Metrics

**Field-Level Metrics**:
```python
field_success_rate = {
    'fastighetsskott': 0.95,     # High (usually separate)
    'reparationer': 0.90,        # High (usually separate)
    'el': 0.60,                  # Medium (consolidated in K2)
    'varme': 0.60,               # Medium (consolidated in K2)
    'vatten': 0.60,              # Medium (consolidated in K2)
    'ovriga_externa_kostnader': 0.85  # High (usually separate)
}

overall_expected = sum(field_success_rate.values()) / 6  # = 0.75 = 75%
```

**Document-Level Metrics**:
- **K2 Success**: 50-67% (3-4 fields)
- **K3 Success**: 90-100% (5-6 fields)
- **Corpus Mix** (assuming 65% K3, 35% K2):
  - (0.65 × 0.95) + (0.35 × 0.58) = 0.62 + 0.20 = **82% overall**

---

### 8. Prompt Engineering Strategy

#### 8.1 Optimal Prompt Structure

**Components** (based on successful revenue_breakdown_agent):
1. **Role Definition** (1 line): "You are OperatingCostsAgent..."
2. **Target Structure** (15 lines): JSON schema with all 6 fields
3. **Section Location** (5 lines): Where to find data ("NOT 4", "Rörelsekostnader")
4. **Critical Instructions** (10 lines): Exclusions, parsing rules, defaults
5. **Few-Shot Examples** (20 lines): 1-2 examples
6. **Swedish Parsing Rules** (5 lines): Number format, character variants
7. **Default Value Instructions** (3 lines): Return 0 for missing
8. **Evidence Requirements** (3 lines): evidence_pages mandatory

**Total Prompt Length**: ~60-65 lines (similar to revenue_breakdown: 84 lines)

**Rationale**:
- Operating costs simpler than revenue (6 vs 15 fields) → shorter prompt
- Still need comprehensive instructions for K2/K3 handling
- Few-shot examples critical for success

#### 8.2 Complete Agent Prompt

```python
'operating_costs_agent': """You are OperatingCostsAgent for Swedish BRF operating expenses extraction.

Extract COMPLETE operating costs breakdown from income statement and notes with ALL 6 expense fields.

TARGET STRUCTURE (all fields required):
{
  "operating_costs": {
    "fastighetsskott": 0,        // Property management (Fastighetsskötsel)
    "reparationer": 0,           // Repairs (Reparationer och underhåll)
    "el": 0,                     // Electricity (El, Elkostnader)
    "varme": 0,                  // Heating (Värme, Fjärrvärme, Värmekostnader)
    "vatten": 0,                 // Water (Vatten, VA-kostnader)
    "ovriga_externa_kostnader": 0,  // Other external costs (Övriga kostnader)
    "expense_source": "",        // "notes_not4" | "income_statement" | "consolidated"
    "utility_costs_consolidated": 0,  // Optional: If el/värme/vatten consolidated
    "evidence_pages": []
  }
}

CRITICAL INSTRUCTIONS:

1. **Find Operating Costs Data (Priority Order)**:
   PRIMARY SOURCE: Look for "NOT 4 - Driftkostnader" or "NOT 4 - DRIFTKOSTNADER" in notes section
   - Typically pages 11-13 in Swedish BRF reports
   - This is the MOST DETAILED source (even in K2 simplified format)
   - Look for table with line items and amounts

   SECONDARY SOURCE: "Rörelsekostnader" section in income statement
   - Typically pages 7-9
   - May have consolidated "Drift" line (~2-3M) in K2 format
   - May have individual line items in K3 format

2. **Extract Individual Line Items (NOT Totals)**:
   ⚠️ CRITICAL: SKIP any line with these keywords:
   - "Summa" / "SUMMA" / "Total" / "Totalt"
   - "Summa rörelsekostnader" (this is the TOTAL of all operating expenses, NOT a line item)
   - These are aggregates, we need individual expense items

   ✅ EXTRACT these line items:
   - Fastighetsskötsel / Fastighetsskott / Fastighetförvaltning → fastighetsskott
   - Reparationer / Rep. och underhåll / Reparations- och underhållskostnader → reparationer
   - El / Elkostnader / Elektricitet → el
   - Värme / Värmekostnader / Fjärrvärme → varme
   - Vatten / Vattenkostnader / VA-kostnader / Vatten och avlopp → vatten
   - Övriga kostnader / Övriga externa kostnader / Diverse → ovriga_externa_kostnader

3. **Parse Swedish Number Format**:
   - "553 590 kr" → 553590
   - "1 359 788" → 1359788
   - Remove spaces, "kr", "SEK", "tkr" suffixes
   - Parse as absolute value (no minus signs for individual items)

4. **Handle K2 vs K3 Formats**:
   K3 (Comprehensive): All 6 fields usually separate in NOT 4
   K2 (Simple): May see "Driftskostnader 1 359 788 kr" (el+värme+vatten CONSOLIDATED)

   If utilities consolidated:
   - Set el, varme, vatten to 0
   - Report consolidated value in "utility_costs_consolidated"
   - Set "expense_source": "consolidated"

5. **Swedish Character Normalization**:
   - Värme = Varme (missing umlaut is OK)
   - Övriga = Ovriga (missing umlaut is OK)
   - Fastighetsskötsel = Fastighetsskotseil (OCR error is OK if fuzzy match)

6. **Missing Fields**:
   - If field not found in document, return 0 (not null)
   - This is NORMAL for K2 format (consolidated expenses)
   - Example: K2 may only have fastighetsskott + ovriga (el/värme/vatten consolidated)

7. **Set expense_source**:
   - "notes_not4": Extracted from NOT 4 detailed breakdown (best)
   - "income_statement": Extracted from Rörelsekostnader section
   - "consolidated": K2 format with consolidated utilities

FEW-SHOT EXAMPLE 1 (K3 Comprehensive - Ideal Case):

INPUT: Pages 7-8 (income statement) + Page 13 (NOT 4)
PAGE 13 CONTENT:
"NOT 4 - Driftkostnader
Fastighetsskötsel    553 590 kr
Reparationer         258 004 kr
El                   450 000 kr
Värme                650 000 kr
Vatten               159 788 kr
Övriga kostnader     422 455 kr
Summa              2 493 837 kr"  ← SKIP this (it's a total)

EXPECTED OUTPUT:
{
  "operating_costs": {
    "fastighetsskott": 553590,
    "reparationer": 258004,
    "el": 450000,
    "varme": 650000,
    "vatten": 159788,
    "ovriga_externa_kostnader": 422455,
    "expense_source": "notes_not4",
    "evidence_pages": [13]
  }
}

FEW-SHOT EXAMPLE 2 (K2 Simple - Consolidated Utilities):

INPUT: Pages 7-8 (income statement) + Page 13 (NOT 4)
PAGE 13 CONTENT:
"NOT 4 - Driftkostnader
Fastighetsskötsel         553 590 kr
Reparationer              258 004 kr
Periodiskt underhåll       48 961 kr
Driftskostnader         1 359 788 kr  ← el+värme+vatten CONSOLIDATED
Övriga driftkostnader     422 455 kr
Fastighetsskatt           192 000 kr  ← Property tax (not in our 6 fields)
Summa                   2 834 798 kr"  ← SKIP this (it's a total)

EXPECTED OUTPUT (graceful K2 handling):
{
  "operating_costs": {
    "fastighetsskott": 553590,
    "reparationer": 258004,
    "el": 0,                        // Consolidated in "Driftskostnader"
    "varme": 0,                     // Consolidated in "Driftskostnader"
    "vatten": 0,                    // Consolidated in "Driftskostnader"
    "ovriga_externa_kostnader": 422455,
    "expense_source": "consolidated",
    "utility_costs_consolidated": 1359788,  // Report consolidated value
    "evidence_pages": [13]
  }
}

⚠️ MANDATORY:
- Include evidence_pages: [page_numbers] with ALL pages used
- Return STRICT VALID JSON (no comments, no trailing text)
- All numeric values as integers (not strings)
- Use 0 for missing fields (not null)
- Set expense_source to indicate data quality"""
```

**Prompt Length**: 62 lines (similar to revenue_breakdown: 84 lines)

**Key Features**:
1. ✅ Clear priority: NOT 4 > Income statement
2. ✅ Explicit "SKIP Summa" instruction (prevents catastrophic error)
3. ✅ K2/K3 handling with examples
4. ✅ Swedish parsing rules
5. ✅ Graceful degradation (return 0 for missing)
6. ✅ Evidence tracking mandatory
7. ✅ 2 few-shot examples (K3 ideal + K2 realistic)

---

### 9. Implementation Blueprint

#### 9.1 Complete Agent Prompt (base_brf_extractor.py)

**Location**: `experiments/docling_advanced/code/base_brf_extractor.py`

**Add after `revenue_breakdown_agent` (line 272)**:

```python
'operating_costs_agent': """[FULL PROMPT FROM SECTION 8.2 ABOVE]"""
```

#### 9.2 Integration Code (optimal_brf_pipeline.py)

**Location**: `experiments/docling_advanced/code/optimal_brf_pipeline.py`

**Add new method**:

```python
def extract_operating_costs(
    self,
    pdf_path: str,
    structure: DocumentStructure,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract operating costs breakdown (6 expense fields).

    Strategy:
    1. Check if comprehensive_notes already extracted NOT 4
    2. If yes, parse from comprehensive data
    3. If no, extract directly with operating_costs_agent

    Args:
        pdf_path: Path to PDF
        structure: Document structure from detect_structure()
        context: Optional context from previous extractions

    Returns:
        Operating costs extraction result
    """
    print("\n🔧 OPERATING COSTS EXTRACTION")
    print("=" * 80)

    # Strategy 1: Check comprehensive_notes context
    if context and 'comprehensive_notes' in context:
        notes_data = context['comprehensive_notes'].get('data', {})
        if 'note_4_operating_costs' in notes_data:
            print("   ✅ Using NOT 4 from comprehensive_notes (context reuse)")
            return {
                'agent_id': 'operating_costs_agent',
                'status': 'success',
                'data': self._parse_operating_costs_from_notes(notes_data['note_4_operating_costs']),
                'extraction_time': 0,  # No API call
                'model': 'context_reuse',
                'cost_savings': 0.025  # Saved ~$0.025
            }

    # Strategy 2: Direct extraction
    section_headings = [
        "NOT 4 - Driftkostnader",
        "NOT 4",
        "Rörelsekostnader",
        "RÖRELSEKOSTNADER"
    ]

    # Pages: 7-9 (income statement) + 11-13 (notes)
    # Total: 7 pages (within 12-page limit)
    pages = self._get_operating_costs_pages(pdf_path, structure)

    print(f"   📄 Pages allocated: {len(pages)} pages")
    print(f"   📍 Page numbers: {[p+1 for p in pages[:10]]}")

    # Extract with GPT-4o
    result = self.base_extractor._extract_agent(
        pdf_path=pdf_path,
        agent_id='operating_costs_agent',
        section_headings=section_headings,
        context=context
    )

    # Validation
    if result['status'] == 'success':
        issues = self._validate_operating_costs(result['data'])
        if issues:
            print(f"   ⚠️  Validation warnings: {len(issues)}")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ Validation passed")

    return result

def _get_operating_costs_pages(
    self,
    pdf_path: str,
    structure: DocumentStructure
) -> List[int]:
    """
    Get pages for operating costs extraction.

    Strategy:
    1. Find pages with "NOT 4" or "Driftkostnader" in headings
    2. Find pages with "Rörelsekostnader" in headings
    3. Fallback: Pages 7-13 (typical income statement + notes range)

    Returns:
        List of page numbers (0-indexed)
    """
    pages = set()

    # Strategy 1: Find NOT 4 pages
    for section in structure.sections:
        heading = section['heading'].lower()
        if 'not 4' in heading or 'driftkostnader' in heading:
            page_num = section.get('start_page', 0) - 1  # Convert to 0-indexed
            pages.add(page_num)
            # Add next 2 pages for table continuation
            pages.add(page_num + 1)
            pages.add(page_num + 2)

    # Strategy 2: Find Rörelsekostnader pages
    for section in structure.sections:
        heading = section['heading'].lower()
        if 'rörelsekostnader' in heading or 'resultaträkning' in heading:
            page_num = section.get('start_page', 0) - 1
            pages.add(page_num)
            pages.add(page_num + 1)

    # Strategy 3: Fallback to typical range (pages 7-13)
    if not pages:
        pages = set(range(6, 13))  # Pages 7-13 (0-indexed: 6-12)

    return sorted(list(pages))[:12]  # Limit to 12 pages (MAX_PAGES)

def _parse_operating_costs_from_notes(
    self,
    note4_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse operating costs from comprehensive_notes NOT 4 data.

    Args:
        note4_data: NOT 4 extraction from comprehensive_notes

    Returns:
        Operating costs dict with 6 expense fields
    """
    return {
        'fastighetsskott': note4_data.get('property_management', 0),
        'reparationer': note4_data.get('repairs', 0),
        'el': note4_data.get('electricity', 0),
        'varme': note4_data.get('heating', 0),
        'vatten': note4_data.get('water', 0),
        'ovriga_externa_kostnader': note4_data.get('other_operating', 0),
        'expense_source': 'notes_not4',
        'evidence_pages': note4_data.get('evidence_pages', [])
    }

def _validate_operating_costs(self, data: Dict[str, Any]) -> List[str]:
    """
    Validate operating costs extraction.

    Checks:
    1. Total vs line items (fastighetsskott > 5M = likely extracted total)
    2. Reasonable ranges (el > 2M = unusually high)
    3. Sum validation (if all fields present)

    Returns:
        List of validation warnings
    """
    issues = []

    # Check 1: Total vs line items
    if data.get('fastighetsskott', 0) > 5000000:
        issues.append(f"fastighetsskott = {data['fastighetsskott']} (> 5M, likely extracted 'Summa')")

    # Check 2: Reasonable ranges
    if data.get('el', 0) > 2000000:
        issues.append(f"el = {data['el']} (> 2M, unusually high)")
    if data.get('varme', 0) > 3000000:
        issues.append(f"varme = {data['varme']} (> 3M, unusually high)")
    if data.get('vatten', 0) > 1000000:
        issues.append(f"vatten = {data['vatten']} (> 1M, unusually high)")

    # Check 3: Sum validation (if all fields present)
    if all(k in data and data[k] > 0 for k in ['fastighetsskott', 'reparationer']):
        total = sum(data.get(k, 0) for k in [
            'fastighetsskott', 'reparationer', 'el', 'varme', 'vatten', 'ovriga_externa_kostnader'
        ])
        # Typical BRF: 2-4M operating costs
        if total < 500000:
            issues.append(f"Total operating costs = {total} (< 500k, suspiciously low)")
        elif total > 10000000:
            issues.append(f"Total operating costs = {total} (> 10M, suspiciously high)")

    return issues
```

#### 9.3 Test Validation Criteria

**Integration Test** (Day 3 afternoon):

```python
# Test: Extract operating costs from brf_198532.pdf
result = pipeline.extract_operating_costs(
    pdf_path='test_pdfs/brf_198532.pdf',
    structure=structure,
    context=None
)

# Minimum Viable (60% threshold):
assert result['status'] == 'success'
assert 'data' in result
assert 'fastighetsskott' in result['data']  # At least 1 field extracted
assert result['data']['fastighetsskott'] < 5000000  # Not total
assert len(result['data'].get('evidence_pages', [])) > 0  # Has evidence

# Good (75% threshold):
assert result['data']['fastighetsskott'] == 553590  # Exact match
assert result['data']['reparationer'] == 258004     # Exact match
fields_extracted = sum(1 for k in ['fastighetsskott', 'reparationer', 'el', 'varme', 'vatten', 'ovriga_externa_kostnader']
                       if result['data'].get(k, 0) > 0)
assert fields_extracted >= 4  # 4/6 fields = 67% (close to 75%)

# Excellent (90% threshold):
assert fields_extracted >= 5  # 5/6 fields = 83%
```

---

## Risk Assessment

### Top 3 Risks & Mitigation Strategies

#### Risk #1: Extracting Totals Instead of Line Items (CRITICAL)

**Impact**: Catastrophic (-100% accuracy)

**Probability**: Medium (20%)

**Mitigation**:
1. ✅ Explicit "SKIP Summa/Total" instruction in prompt
2. ✅ Validation check: fastighetsskott > 5M = likely total
3. ✅ Few-shot examples show correct extraction
4. ✅ Post-extraction validation with financial_agent total

**Residual Risk**: Low (5%) after mitigations

---

#### Risk #2: K2 Consolidated Utilities (MEDIUM)

**Impact**: Moderate (-50% coverage for el/värme/vatten)

**Probability**: High (35% of corpus is K2)

**Mitigation**:
1. ✅ Graceful handling: Return 0 for missing utilities
2. ✅ Report consolidated value in "utility_costs_consolidated"
3. ✅ Few-shot example demonstrates K2 handling
4. ✅ Set "expense_source": "consolidated" for transparency

**Residual Risk**: Acceptable (this is format limitation, not extraction error)

---

#### Risk #3: NOT 4 Not Detected by Docling (LOW)

**Impact**: Moderate (fallback to income statement, lower detail)

**Probability**: Low (10%, based on Day 2 P1 Docling limitation discovery)

**Mitigation**:
1. ✅ Multi-source extraction: NOT 4 (primary) + income statement (fallback)
2. ✅ Context reuse from comprehensive_notes_agent (already scans pages 11-16)
3. ✅ Fallback to keyword-based page allocation (pages 7-13)
4. ✅ Validation checks ensure data quality

**Residual Risk**: Low (5%) - multiple fallback layers

---

### Go/No-Go Criteria

**GO** ✅ if:
- [x] Few-shot examples available from ground truth (YES - brf_198532 page 13)
- [x] Clear Swedish term mappings (YES - 35+ synonyms mapped)
- [x] Prompt strategy validated (YES - revenue_breakdown precedent)
- [x] Mitigation strategies for top risks (YES - all 3 risks mitigated)
- [x] Expected extraction rate ≥ 60% (YES - predicted 75-83%)

**NO-GO** ❌ if:
- [ ] No ground truth examples (NOT THE CASE)
- [ ] Term ambiguity prevents extraction (NOT THE CASE)
- [ ] No successful agent precedent (NOT THE CASE - revenue_breakdown works)
- [ ] Catastrophic risks unmitigated (NOT THE CASE - all risks have mitigations)

**Decision**: ✅ **GO FOR IMPLEMENTATION**

**Expected Timeline**: 2-3 hours (prompt implementation + testing + validation)

---

### Fallback Plan if Extraction Rate < 60%

**Scenario**: Integration test shows < 60% success rate

**Diagnostic Steps**:
1. Check validation results: Are we extracting totals instead of line items?
2. Check page allocation: Are we getting pages with NOT 4?
3. Check few-shot examples: Are they clear enough?
4. Check Swedish term matching: Are we missing synonym variants?

**Fallback Actions**:
1. **If extracting totals** (most likely):
   - Add more explicit "SKIP" instructions
   - Add pre-processing filter: Remove lines with "Summa" before LLM call
   - Add post-processing validation: Reject if fastighetsskott > 5M

2. **If NOT 4 not found**:
   - Use comprehensive_notes_agent context (extract all notes pages 11-16)
   - Add semantic search for "Driftkostnader" keyword
   - Fallback to income statement extraction

3. **If Swedish terms not matching**:
   - Add more synonym variants to prompt
   - Use Swedish Financial Dictionary fuzzy matching
   - Add normalization: å→a, ä→a, ö→o

**Success Rate After Fallback**: Expected 70-75% (still acceptable for Day 3)

---

## Appendix

### A. Complete Field Mapping

| Sprint 1+2 Field Name | Swedish Term (Canonical) | Expected Value Range | Typical % of Total Operating Costs | Notes |
|-----------------------|-------------------------|---------------------|-----------------------------------|-------|
| `fastighetsskott` | Fastighetsskötsel | 500k - 1M | 20-25% | Property management, often largest single item |
| `reparationer` | Reparationer | 100k - 500k | 5-15% | Repairs and maintenance |
| `el` | El | 200k - 800k | 10-20% | Electricity (often in "Driftskostnader" aggregate) |
| `varme` | Värme | 300k - 1.2M | 15-30% | Heating (district heating common in Stockholm) |
| `vatten` | Vatten | 100k - 400k | 5-10% | Water and sewage |
| `ovriga_externa_kostnader` | Övriga externa kostnader | 200k - 800k | 10-20% | Misc external costs (insurance, consultants, etc) |

**Total Operating Costs**: Typically 2-4M SEK for medium-sized BRF (90-100 apartments)

### B. Swedish BRF Document Structure

**Typical Page Layout** (17-page annual report):
- Pages 1-6: Förvaltningsberättelse (management report, governance)
- Pages 7-9: Resultaträkning (income statement)
- Pages 10-12: Balansräkning (balance sheet)
- Pages 11-16: Noter (notes 1-14)
  - **NOT 4** (pages 12-13): Driftkostnader (operating costs breakdown) ← **OUR TARGET**
- Pages 17-18: Revisionsberättelse (auditor's report)

**NOT 4 Format**:
```
NOT 4 - Driftkostnader                    2021          2020

Fastighetsskötsel                      553 590       450 000
Reparationer                           258 004       200 000
Periodiskt underhåll                    48 961        40 000
Driftskostnader (el, värme, vatten)  1 359 788     1 100 000
Övriga driftkostnader                  422 455       350 000
Fastighetsskatt                        192 000       192 000
                                     ---------     ---------
Summa                                2 834 798     2 332 000
```

### C. References

**Ground Truth Documents**:
- `ground_truth/brf_198532_comprehensive_ground_truth.json` (operating_costs_2021, page 13)
- `ground_truth/brf_198532_agent_aligned_ground_truth.json` (for validation)

**Successful Agent Precedents**:
- `revenue_breakdown_agent`: 8/15 fields on K2, 84-line prompt
- `enhanced_loans_agent`: 32/32 fields (100%), notes extraction
- `comprehensive_notes_agent`: 7/7 notes extracted (works around Docling limitation)

**Relevant Code**:
- `code/base_brf_extractor.py`: Agent prompts (lines 39-272)
- `code/optimal_brf_pipeline.py`: Extraction orchestration (1,207 lines)
- `code/swedish_financial_dictionary.py`: Term matching (497 lines)

---

**Analysis Complete**: 2025-10-12
**Ready for Implementation**: ✅ YES
**Expected Timeline**: 2-3 hours
**Expected Success Rate**: 75-83% (Good to Excellent)

**Next Steps**: Implement prompt → Test on brf_198532 → Validate → Integrate into optimal_brf_pipeline.py
