# Dictionary Routing Bug Analysis - 2025-10-11

## 🎯 Executive Summary

**Problem**: Routing logic achieves only 50% match rate (not 0% as initially reported, but still too low)

**Root Cause**: **Premature state machine transition** - routing switches to "notes mode" on table-of-contents "Noter" entry (page 2) instead of actual notes section (page 12)

**Impact**: All sections between page 2-12 are in "notes mode" but don't match note keywords → NO ROUTING → NO EXTRACTION

**Solution**: Multi-layer routing with preprocessing + more specific note detection

---

## 📊 Diagnostic Results (brf_268882.pdf)

### Match Statistics
- **Total sections**: 50
- **Matched**: 25 (50%)
- **Unmatched**: 25 (50%)

### Layer Performance
- **Layer 1** (substring): 21 matches
- **Layer 2** (preprocessed): 0 matches (no benefit)
- **Layer 3** (fuzzy): 12 matches

### Pattern Analysis
- **Swedish characters**: 62% of sections (å, ä, ö)
- **Uppercase**: 4% of sections
- **Numbering**: Minimal impact

---

## 🐛 Root Cause Analysis

### The Bug: False Positive Note Detection

```python
# Current logic (optimal_brf_pipeline.py:449)
if "noter" in heading_lower and len(heading) < 20:
    main_sections['notes_collection'].append(heading)
    in_notes_subsection = True  # ← BUG: Triggers on page 2!
    continue
```

### Section Order Reveals the Problem

```
Page  2: "Noter" ← FALSE POSITIVE (table of contents entry)
          ↓
    [SWITCHES TO NOTES MODE]
          ↓
Page  3: "Förvaltningsberättelse" ← Should match governance, but in notes mode
Page  3: "Verksamheten" ← Should match operations, but in notes mode
Page  5: "Medlemsinformation" ← Should match governance, but in notes mode
Page  6: "Flerårsöversikt" ← Should match financial, but in notes mode
Page  7: "Förändringar i eget kapital" ← Should match financial, but in notes mode
Page  7: "Resultatdisposition" ← Should match financial, but in notes mode
          ↓
Page 12: "Noter" ← ACTUAL notes section start
Page 12: "NOT 1 REDOVISNINGS-..." ← Real note subsection
```

### Impact Quantification

**Sections affected by premature notes mode**: ~15-20 sections (pages 2-12)

**Fields lost due to routing failure**:
- Governance: medlemsinformation, registrering, förening
- Financial: flerårsöversikt, eget kapital, resultatdisposition
- Operations: verksamhet details

**Estimated field extraction loss**: 30-40% of extractable fields

---

## ✅ Proven Matches (Working Well)

```
✅ Förvaltningsberättelse → governance_agent (1.00)
✅ Resultaträkning → financial_agent (1.00)
✅ Balansräkning → financial_agent (1.00)
✅ Kassaflödesanalys → financial_agent (1.00)
✅ Noter → notes (1.00 via fuzzy)
✅ Giltighet → governance_agent (1.00)
```

---

## ❌ Critical Failures (Needs Fix)

### Category 1: Premature Notes Mode
```
❌ Medlemsinformation → NO MATCH (should be governance)
❌ Flerårsöversikt → NO MATCH (should be financial)
❌ Förändringar i eget kapital → NO MATCH (should be financial)
❌ Resultatdisposition → NO MATCH (should be financial)
```

### Category 2: Note Subsections
```
❌ NOT 1 REDOVISNINGS-... → NO MATCH (should be notes_accounting)
   Problem: Preprocessing strips "NOT 1" → "redovisnings-..."
   Fix: Preserve note numbering for routing, strip after
```

### Category 3: Incomplete Keywords
```
❌ Registreringsdatum → NO MATCH (governance related)
❌ Äkta förening → NO MATCH (governance related)
```

---

## 🔧 Recommended Fixes (Priority Order)

### P0 - Fix Premature Notes Mode (Highest Impact)

**Current code**:
```python
# Line 449 of optimal_brf_pipeline.py
if "noter" in heading_lower and len(heading) < 20:
    main_sections['notes_collection'].append(heading)
    in_notes_subsection = True  # ← BUG
    continue
```

**Fixed code**:
```python
# More specific note detection
if heading.startswith("NOT ") and re.match(r"NOT \d+", heading):
    # Real note subsection detected
    in_notes_subsection = True
    note_headings.append(heading)
    continue

# Main "Noter" section (keep for collection, but don't switch mode yet)
if "noter" in heading_lower and len(heading) < 20:
    main_sections['notes_collection'].append(heading)
    # Don't switch to notes mode yet - wait for actual note subsections
    continue
```

**Expected improvement**: 25% → 70% match rate (add ~15 sections)

### P1 - Expand Keyword Coverage

Add missing terms to `main_section_keywords`:

```python
self.main_section_keywords = {
    "governance_agent": [
        "förvaltningsberättelse", "styrelse", "board", "governance",
        "föreningsstämma", "annual meeting", "giltighet", "validity",
        # ADD:
        "medlemsinformation", "medlemmar", "registrering",
        "äkta förening", "förening", "sammansättning"
    ],
    "financial_agent": [
        "resultaträkning", "income statement", "balansräkning", "balance sheet",
        "kassaflödesanalys", "cash flow", "ekonomi", "financial",
        # ADD:
        "flerårsöversikt", "förändringar", "eget kapital",
        "resultatdisposition", "förlust", "kapital"
    ],
    # ... (property_agent and operations_agent expanded similarly)
}
```

**Expected improvement**: 70% → 85% match rate (add ~7-10 sections)

### P2 - Integrate Swedish Financial Dictionary (Optional)

Use fuzzy matching from `swedish_financial_dictionary.py` for remaining edge cases:

```python
# In route_sections(), after keyword matching:
if not routed:
    # Try fuzzy matching with dictionary
    match = self.dictionary.match_term(heading, fuzzy_threshold=0.70)
    if match:
        # Map category to agent
        agent_map = {
            'balance_sheet': 'financial_agent',
            'income_statement': 'financial_agent',
            'notes': 'notes_collection',
            'governance': 'governance_agent',
            'audit': 'governance_agent'
        }
        if match.category in agent_map:
            agent_id = agent_map[match.category]
            main_sections[agent_id].append(heading)
            routed = True
```

**Expected improvement**: 85% → 95% match rate (add ~5 sections)

---

## 📈 Expected Outcomes

### Before Fix (Current)
- Match rate: 50% (25/50 sections)
- Field extraction: ~35.7% (estimated)
- Note routing: Broken (premature mode switch)

### After P0 Fix Only
- Match rate: 70% (35/50 sections)
- Field extraction: ~55% (estimated)
- Note routing: Fixed

### After P0 + P1 Fixes
- Match rate: 85% (42-43/50 sections)
- Field extraction: ~70% (estimated)
- Note routing: Fixed + expanded coverage

### After P0 + P1 + P2 Fixes
- Match rate: 95% (47-48/50 sections)
- Field extraction: ~75% (TARGET ✅)
- Note routing: Fixed + expanded + fuzzy fallback

---

## 🎯 Implementation Plan

### Step 1: Fix Premature Notes Mode (30 min)
- Update `route_sections()` line 449-452
- Use regex to detect actual note subsections: `r"NOT \d+"`
- Test on brf_268882.pdf

### Step 2: Expand Keywords (30 min)
- Update `main_section_keywords` with missing terms
- Add from failed matches: "medlemsinformation", "flerårsöversikt", etc.
- Test on brf_268882.pdf

### Step 3: Integrate Fuzzy Matching (60 min)
- Add Swedish Financial Dictionary to OptimalBRFPipeline.__init__()
- Add fallback fuzzy matching after keyword matching
- Map dictionary categories to agents
- Test on 3 diverse PDFs

### Step 4: Validate (30 min)
- Run on brf_268882.pdf (scanned)
- Run on brf_271852.pdf (hybrid)
- Check one machine-readable PDF
- Measure improvement: 50% → X%

---

## 📁 Files to Modify

1. **optimal_brf_pipeline.py**:
   - Lines 226-242: Expand `main_section_keywords`
   - Lines 449-452: Fix premature notes mode detection
   - Lines 482-489: Add fuzzy matching fallback

2. **swedish_financial_dictionary.py**: ✅ Already working (no changes needed)

3. **debug_dictionary_matching.py**: ✅ Diagnostic tool complete

---

## 🧪 Test Cases

### Test 1: Note Mode State Machine
```python
# Input sections (in order):
["Noter",  # Page 2 (table of contents)
 "Förvaltningsberättelse",  # Page 3
 "Medlemsinformation",  # Page 5
 "Noter",  # Page 12 (actual section)
 "NOT 1 REDOVISNINGS-..."]  # Page 12 (subsection)

# Expected routing:
{
    "notes_collection": ["Noter"],  # Only TOC entry
    "governance_agent": ["Förvaltningsberättelse", "Medlemsinformation"],
    "notes_accounting_agent": ["NOT 1 REDOVISNINGS-..."]
}
```

### Test 2: Keyword Coverage
```python
# Missing keyword sections:
["Flerårsöversikt", "Förändringar i eget kapital", "Resultatdisposition"]

# Should route to:
{"financial_agent": [...]}
```

### Test 3: Fuzzy Fallback
```python
# Edge cases with typos or variants:
["Styrelsens sammansättning", "Registreringsdatum"]

# Should fuzzy match to:
{"governance_agent": [...]}
```

---

## 📊 Success Metrics

### Routing Performance
- **Target**: 95% match rate (47-48/50 sections)
- **Current**: 50% match rate (25/50 sections)
- **After Fix**: Monitor in real-time during implementation

### Field Extraction
- **Target**: 75% field extraction (21/28 fields)
- **Current**: 35.7% field extraction (10/28 fields)
- **After Fix**: Re-run full pipeline to measure

### Note Routing
- **Target**: 100% of note subsections routed correctly
- **Current**: 0% (blocked by premature mode switch)
- **After Fix**: Validate all "NOT X" sections route properly

---

## 🔒 Rollback Plan

If fixes cause regressions:

1. **Git revert** to current commit
2. **Disable fuzzy matching** (keep P0 + P1 only)
3. **Add config flag**: `ENABLE_ENHANCED_ROUTING=false`

---

**Status**: ✅ **DIAGNOSIS COMPLETE** - Ready for implementation

**Next Step**: Implement P0 fix (premature notes mode) and test

**Time Estimate**: 2-3 hours total (30min P0 + 30min P1 + 60min P2 + 30min validation)
