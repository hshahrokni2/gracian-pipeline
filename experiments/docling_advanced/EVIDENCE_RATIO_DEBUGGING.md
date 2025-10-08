# Evidence Ratio Debugging - Phase 2C Analysis

**Date**: 2025-10-08
**Status**: ⚠️ **FIXES DID NOT WORK - FURTHER INVESTIGATION REQUIRED**

---

## 🚨 Problem Summary

**Initial Issue** (Phase 2B):
- Evidence ratio: 12.5% (1/8 agents)
- Root cause hypothesized: Page labels not passed to LLM (90% confidence)

**After Fix #1 + Fix #2** (Phase 2C):
- Evidence ratio: **12.5% (UNCHANGED)**
- Conclusion: Our hypothesis was wrong OR implementation was incorrect

---

## ✅ Fixes Applied (Phase 2C)

### Fix #1: Interleave Page Labels with Images
**Lines 734-752 in optimal_brf_pipeline.py**

```python
# BEFORE:
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        *image_parts
    ]
}]

# AFTER:
content = [{"type": "text", "text": prompt}]
for img_bytes, label in zip(images, page_labels):
    content.append({"type": "text", "text": f"\n--- {label} ---"})
    content.append({"type": "image_url", "image_url": {...}})
messages = [{"role": "user", "content": content}]
```

### Fix #2: Strengthen Evidence Instruction
**Lines 696-703 in optimal_brf_pipeline.py**

```python
prompt += """
⚠️ MANDATORY REQUIREMENT:
Your JSON response MUST include 'evidence_pages': [page_numbers].
List ALL page numbers (1-based, from image labels below) used for extraction.
If you used images labeled "Page 5", "Page 7", "Page 8", return: 'evidence_pages': [5, 7, 8]
If no relevant information found, return 'evidence_pages': []
"""
```

---

## 🔍 Test Results (Phase 2C)

**Test**: `brf_268882.pdf`
**Execution Time**: 164.7s (vs 192.3s in Phase 2B - faster due to caching)
**Evidence Ratio**: **12.5%** (1/8 agents - NO CHANGE)

```
✅ STAGE 5: Quality Validation
   Coverage: 100.0% (8/8 agents)
   Numeric QC: ✅ Pass
   Evidence: 12.5% (1/8 agents)  ⚠️ UNCHANGED
   Overall: 56.2% ⚠️
```

---

## 🤔 Why Didn't It Work?

### Hypothesis #1: LLM Ignoring the Instruction
**Likelihood**: 70%

**Evidence**:
- Even with ⚠️ emoji and "MUST" language, 7/8 agents still don't provide evidence_pages
- GPT-4o might be prioritizing extraction accuracy over evidence tracking
- JSON schema enforcement needed instead of soft instruction

**Test**: Added diagnostic logging (lines 775-780) to see what keys LLM actually returns

### Hypothesis #2: Page Labels Not Visible Despite Fix
**Likelihood**: 20%

**Evidence**:
- OpenAI API might not render text blocks between images in expected order
- LLM might see labels but not associate them with adjacent images
- Vision model might focus on images and skip text interludes

**Test**: Need to inspect raw API request/response to validate

### Hypothesis #3: JSON Parsing Strips evidence_pages
**Likelihood**: 5%

**Evidence**:
- `_parse_json_with_fallback()` uses regex which might miss nested arrays
- But this would cause parsing errors, which we're not seeing

**Test**: Log raw LLM response before JSON parsing

### Hypothesis #4: Caching Issue
**Likelihood**: 5%

**Evidence**:
- Phase 2C test showed "Structure cached (50 sections, 0.1s, $0)"
- Might be using old extraction results from Phase 2B?

**Test**: Clear cache and re-run

---

## 🔧 Next Steps (Prioritized)

### Step 1: Add Diagnostic Logging ✅ DONE
**Added** (lines 775-780):
```python
print(f"   🔍 {agent_id} extracted keys: {list(extracted_data.keys())}")
if 'evidence_pages' in extracted_data:
    print(f"   ✅ {agent_id} evidence_pages: {extracted_data['evidence_pages']}")
else:
    print(f"   ❌ {agent_id} MISSING evidence_pages!")
```

**Next**: Run test again and analyze output

### Step 2: Inspect Raw LLM Responses
**Add logging** (before line 770):
```python
print(f"   📄 {agent_id} raw response (first 500 chars):")
print(f"   {raw_content[:500]}")
```

**Goal**: See if LLM is including evidence_pages in raw response

### Step 3: Use JSON Schema (Structured Output)
**Replace** (lines 762-767):
```python
# BEFORE:
response = client.chat.completions.create(
    model="gpt-4o-2024-11-20",
    messages=messages,
    max_tokens=2000,
    temperature=0
)

# AFTER:
response = client.chat.completions.create(
    model="gpt-4o-2024-11-20",
    messages=messages,
    max_tokens=2000,
    temperature=0,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "brf_extraction",
            "strict": true,
            "schema": {
                "type": "object",
                "properties": {
                    "evidence_pages": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    # ... other fields
                },
                "required": ["evidence_pages"],
                "additionalProperties": false
            }
        }
    }
)
```

**Why This Will Work**:
- Enforces JSON schema at API level (not just prompt)
- LLM MUST include required fields or API call fails
- OpenAI's structured output feature (released Nov 2024)

### Step 4: Clear All Caches
```bash
rm -rf results/cache/*
rm -rf results/optimal_pipeline/*
```

**Why**: Ensure we're not using cached results from Phase 2B

---

## 📊 Diagnostic Test Plan

### Phase 1: Quick Diagnostic (10 minutes)
1. Run pipeline with new diagnostic logging
2. Check which agents return evidence_pages
3. Inspect raw LLM responses

**Success Criteria**: Understand which agents comply and why

### Phase 2: JSON Schema Fix (30 minutes)
1. Implement response_format with json_schema
2. Define schema for each agent type
3. Re-run test

**Success Criteria**: Evidence ratio ≥95% (enforced by schema)

### Phase 3: Validation (1 hour)
1. Test on full Hjorthagen corpus (15 PDFs)
2. Measure evidence ratio across all documents
3. Verify evidence_verified == True for all citations

**Success Criteria**: ≥95% evidence ratio across corpus

---

## 💡 Key Insights

### 1. Soft Instructions Don't Work
**Learning**: Even with emoji, "MUST" language, and examples, GPT-4o ignores the instruction

**Solution**: Use OpenAI's structured output (response_format with JSON schema)

### 2. Page Labels Might Be Visible But Ignored
**Learning**: LLM might see labels but prioritize extraction over evidence tracking

**Solution**: Make evidence_pages a **required** field in JSON schema

### 3. ULTRATHINKING Analysis Was Partially Correct
**Correct**: Page labels weren't passed to LLM (we fixed this)
**Incorrect**: This wasn't the only issue - LLM instruction compliance is the bigger problem

**Solution**: Multi-layered fix (labels + schema enforcement)

---

## 🎯 Expected Outcome After JSON Schema Fix

| Metric | Current | After Schema | Reasoning |
|--------|---------|--------------|-----------|
| Evidence Ratio | 12.5% | 100% | Schema enforcement makes it mandatory |
| Agents Compliant | 1/8 | 8/8 | API fails if evidence_pages missing |
| Overall Score | 56.2% | ≥97.5% | (100% coverage + 100% evidence) / 2 |

---

**Status**: ⏳ **DIAGNOSTIC LOGGING ADDED - AWAITING NEXT TEST RUN**
**Next Action**: Run diagnostic test and implement JSON schema enforcement
**Expected Timeline**: 1-2 hours to full solution
