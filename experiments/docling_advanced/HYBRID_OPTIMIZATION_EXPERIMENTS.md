# Hybrid OCR+LLM Optimization Experiments
## Finding the Perfect Balance for 12,101 Swedish BRF PDFs

**Date**: 2025-10-07
**Goal**: Achieve 95% accuracy with minimal LLM API costs
**Approach**: ULTRATHINKING-guided experimental design

---

## 🎯 Hypothesis Matrix

| Hypothesis | Test Method | Success Metric | Cost Impact |
|------------|-------------|----------------|-------------|
| **H1: Pattern matching handles 60% of fields** | Extract with regex first, measure coverage | ≥60% fields extracted without LLM | -60% API calls |
| **H2: Strategic page sampling maintains accuracy** | Test 5 pages vs all 20 pages | <5% accuracy drop | -75% OCR time |
| **H3: Section-aware extraction reduces LLM calls** | Route pages by section type | 95% accuracy, 50% fewer LLM calls | -50% API cost |
| **H4: Cheap model for simple, expensive for complex** | Grok for governance, GPT-5 for financial | 95% accuracy maintained | -40% API cost |
| **H5: Confidence thresholds optimize fallback** | Test 70%, 80%, 90% confidence cutoffs | Optimal accuracy/cost ratio | Variable |

---

## 📊 Experimental Framework

### Experiment 1: OCR-Only Baseline (Zero LLM Calls)

**Purpose**: Establish floor performance with pure pattern matching

**Method**:
```python
# Extract with Docling + EasyOCR (Swedish)
markdown = docling_extract(pdf_path, swedish_ocr=True)

# Try pattern-based extraction for all 13 agents
results = {
    "governance": extract_governance_patterns(markdown),
    "financial": extract_financial_patterns(markdown),
    "property": extract_property_patterns(markdown),
    # ... all 13 agents
}

# Measure coverage and accuracy
coverage = count_non_null_fields(results) / total_expected_fields
accuracy = compare_to_ground_truth(results, ground_truth)
```

**Patterns to Test**:
```python
PATTERNS = {
    "chairman": r"Ordförande[:\s]+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)+)",
    "org_number": r"(?:Org\.?\s*(?:nr|nummer)|Organisationsnummer)[:\s]+(\d{6}-\d{4})",
    "address": r"(?:Adress|Besöksadress)[:\s]+([A-ZÅÄÖ][^\n]+)",
    "revenue": r"(?:Intäkter|Nettoomsättning).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
    "assets": r"(?:Tillgångar|Summa tillgångar).*?(\d[\d\s]*\d)\s*(?:kr|SEK|tkr)",
    # ... more patterns
}
```

**Expected Results**:
- Coverage: 50-70% (easy fields work, complex fields fail)
- Accuracy: 80-90% on matched fields
- Speed: 30s/doc (no LLM calls)
- Cost: $0

**Success Criteria**: If ≥60% fields extracted with ≥85% accuracy → patterns work!

---

### Experiment 2: Strategic Page Sampling

**Purpose**: Reduce OCR processing time without losing accuracy

**Method**:
```python
# Test 4 different sampling strategies
strategies = {
    "all_pages": range(1, 21),  # Baseline
    "strategic_5": [1, 2, 3, 10, 20],  # Cover + middle + financials + end
    "strategic_7": [1, 2, 3, 8, 10, 15, 20],  # Add governance + notes
    "section_based": detect_key_pages_with_toc(pdf_path),  # Smart detection
}

for strategy_name, pages in strategies.items():
    # Extract only selected pages
    markdown = docling_extract(pdf_path, pages=pages, swedish_ocr=True)

    # Full LLM extraction
    results = llm_extract_all_agents(markdown)

    # Compare to full-document baseline
    accuracy = compare_to_baseline(results, full_baseline)
    time_saved = (20 - len(pages)) / 20 * 100
```

**Expected Results**:
- **All pages** (20): 95% accuracy, 600s
- **Strategic 5**: 90% accuracy, 150s (75% time saved)
- **Strategic 7**: 93% accuracy, 210s (65% time saved)
- **Section-based**: 94% accuracy, variable time

**Success Criteria**: If strategic sampling maintains ≥93% accuracy → massive speedup!

---

### Experiment 3: Section-Aware Routing

**Purpose**: Send only relevant pages to each LLM agent

**Method**:
```python
# 1. Use Docling to detect sections (fast, structure-only)
sections = docling_detect_sections(pdf_path)
# Example: {"governance": [1,2,3], "financial": [8,9,10], "notes": [15,16,17]}

# 2. Route pages to agents based on sections
results = {}
for agent_id, agent_prompt in agents.items():
    # Only extract pages relevant to this agent
    relevant_pages = sections.get(agent_id, [])

    if len(relevant_pages) > 0:
        # OCR only relevant pages
        markdown = docling_extract(pdf_path, pages=relevant_pages, swedish_ocr=True)

        # LLM extraction on minimal context
        results[agent_id] = llm_extract(markdown, agent_prompt)
    else:
        results[agent_id] = None  # Section not found

# 3. Measure vs full-document extraction
accuracy = compare_to_full_document(results)
pages_processed = sum(len(pages) for pages in sections.values())
llm_calls_reduced = (20 * 13 - pages_processed * 13) / (20 * 13) * 100
```

**Expected Results**:
- Accuracy: 93-95% (minimal loss)
- LLM calls: -60% (process 8 pages avg vs 20 pages)
- Cost: -60% ($0.40 vs $1.00 per document)

**Success Criteria**: If ≥94% accuracy with <50% LLM calls → optimal routing!

---

### Experiment 4: Multi-Model Cost Optimization

**Purpose**: Use cheap models for easy extractions, expensive for complex

**Method**:
```python
# Define complexity tiers
EXTRACTION_COMPLEXITY = {
    "easy": {
        "agents": ["governance", "property", "events"],
        "model": "grok-beta",  # $2/1M tokens
        "prompt_tokens": 5000,
        "cost_per_call": 0.01
    },
    "medium": {
        "agents": ["fees", "loans", "operations"],
        "model": "gpt-4o",  # $2.5/1M input
        "prompt_tokens": 8000,
        "cost_per_call": 0.02
    },
    "hard": {
        "agents": ["financial", "notes_depreciation", "notes_maintenance"],
        "model": "gpt-5",  # $10/1M tokens (hypothetical)
        "prompt_tokens": 15000,
        "cost_per_call": 0.15
    }
}

# Test each model on its complexity tier
results_by_model = {}
for tier, config in EXTRACTION_COMPLEXITY.items():
    for agent_id in config["agents"]:
        result = llm_extract(
            markdown,
            agent_prompt,
            model=config["model"]
        )
        results_by_model[agent_id] = {
            "result": result,
            "model": config["model"],
            "cost": config["cost_per_call"]
        }

# Compare accuracy vs baseline (all GPT-5)
accuracy_drop = compare_to_baseline(results_by_model)
cost_savings = calculate_cost_difference(results_by_model, baseline_cost)
```

**Expected Results**:
- Easy fields (Grok): 92% accuracy, $0.01/call
- Medium fields (GPT-4o): 94% accuracy, $0.02/call
- Hard fields (GPT-5): 96% accuracy, $0.15/call
- **Blended**: 94% accuracy, $0.05/call avg (vs $0.15 all-GPT-5)
- **Cost savings**: 67%

**Success Criteria**: If ≥94% accuracy with ≤$0.06/call → multi-model wins!

---

### Experiment 5: Confidence-Based Fallback Thresholds

**Purpose**: Determine optimal confidence threshold for pattern → LLM fallback

**Method**:
```python
# Test multiple confidence thresholds
thresholds = [0.60, 0.70, 0.80, 0.90, 0.95]

for threshold in thresholds:
    results = {}
    llm_calls = 0

    for agent_id in agents:
        # 1. Try pattern extraction first
        pattern_result, confidence = extract_with_patterns(markdown, agent_id)

        if confidence >= threshold:
            # Use pattern result (free)
            results[agent_id] = pattern_result
        else:
            # Fall back to LLM (expensive)
            results[agent_id] = llm_extract(markdown, agent_prompt)
            llm_calls += 1

    # Measure accuracy vs cost
    accuracy = compare_to_ground_truth(results)
    llm_call_ratio = llm_calls / len(agents)
    cost = llm_calls * 0.10  # $0.10 per LLM call

    print(f"Threshold {threshold}: {accuracy:.1%} accuracy, {llm_call_ratio:.1%} LLM calls, ${cost:.2f} cost")
```

**Expected Results**:
| Threshold | Accuracy | LLM Calls | Cost | Winner? |
|-----------|----------|-----------|------|---------|
| 0.60 | 89% | 20% | $0.20 | ❌ Too low accuracy |
| 0.70 | 92% | 35% | $0.35 | ⚠️ Borderline |
| 0.80 | 94% | 50% | $0.50 | ✅ **Good balance** |
| 0.90 | 95% | 70% | $0.70 | ⚠️ Diminishing returns |
| 0.95 | 95.5% | 85% | $0.85 | ❌ Too expensive |

**Success Criteria**: Find threshold where accuracy ≥94% and LLM calls ≤60%

---

## 🔄 Combined Hybrid Approach (Optimal Pipeline)

Based on experimental results, the optimal pipeline combines:

```python
class OptimalHybridExtractor:
    """
    Combines all winning strategies:
    1. Section-aware page routing (Exp 3)
    2. Pattern extraction with 80% confidence threshold (Exp 5)
    3. Multi-model routing (Exp 4)
    4. Strategic page sampling when no sections detected (Exp 2)
    """

    def extract(self, pdf_path):
        # Step 1: Detect sections (structure-only, fast)
        sections = docling_detect_sections(pdf_path)

        # Step 2: For each agent, extract only relevant pages
        results = {}
        for agent_id, agent_config in self.agents.items():
            # Get relevant pages
            pages = sections.get(agent_id, None)
            if not pages:
                # Fallback: strategic sampling
                pages = self.get_strategic_pages(agent_id)

            # OCR only these pages (Docling + EasyOCR Swedish)
            markdown = docling_extract(pdf_path, pages=pages, swedish_ocr=True)

            # Step 3: Try pattern extraction first
            pattern_result, confidence = self.extract_with_patterns(markdown, agent_id)

            if confidence >= 0.80:
                # Pattern worked! (free)
                results[agent_id] = pattern_result
            else:
                # Step 4: Fall back to appropriate LLM
                model = self.select_model(agent_id)  # Grok vs GPT-4o vs GPT-5
                results[agent_id] = llm_extract(markdown, agent_config, model=model)

        return results

    def select_model(self, agent_id):
        """Route to cheapest model that can handle complexity"""
        if agent_id in ["governance", "property", "events"]:
            return "grok-beta"  # Easy fields
        elif agent_id in ["fees", "loans", "operations"]:
            return "gpt-4o"  # Medium complexity
        else:
            return "gpt-5"  # Financial, notes (complex)
```

**Expected Performance**:
- **Accuracy**: 95%+ (same as full LLM)
- **Speed**: 180s/doc (vs 600s full processing) → **70% faster**
- **Cost**: $0.25/doc (vs $1.00 full LLM) → **75% cheaper**
- **Scalability**: 12,101 docs × 180s = 605 hours (25 days single-threaded, **2.5 days with 10 workers**)

---

## 📋 Experimental Test Suite

### Test Documents (Representative Sample)
1. **brf_268882.pdf** (Hagelbössan - already tested, use as baseline)
2. **brf_198532.pdf** (Björk och Plaza - machine-readable, easy case)
3. **brf_46160.pdf** (Hjorthagen - previous ground truth)
4. Pick 2 more: 1 scanned, 1 hybrid

### Metrics to Track
```python
METRICS = {
    "accuracy": {
        "overall_coverage": "extracted_fields / total_fields",
        "field_accuracy": "correct_values / extracted_values",
        "by_agent": {agent_id: accuracy_score}
    },
    "performance": {
        "total_time_seconds": elapsed,
        "ocr_time": docling_time,
        "llm_time": llm_calls_time,
        "pages_processed": num_pages
    },
    "cost": {
        "llm_calls": num_calls,
        "llm_cost_usd": total_cost,
        "cost_per_field": cost / num_fields
    },
    "reliability": {
        "error_rate": errors / total_attempts,
        "retry_count": num_retries
    }
}
```

---

## 🎯 Success Criteria Summary

**Minimum Viable Hybrid (MVH)**:
- ✅ Accuracy ≥94%
- ✅ Cost ≤$0.30/doc (vs $1.00 baseline)
- ✅ Speed ≤200s/doc (vs 600s baseline)
- ✅ Error rate <5%

**Stretch Goals**:
- 🎯 Accuracy ≥95%
- 🎯 Cost ≤$0.20/doc (80% savings)
- 🎯 Speed ≤150s/doc (75% faster)
- 🎯 Error rate <2%

---

## 📅 Experimental Timeline

**Phase 1: Individual Experiments** (2-3 days)
- Day 1: Run Experiments 1-3 on 5 test docs
- Day 2: Run Experiments 4-5 on 5 test docs
- Day 3: Analyze results, identify winners

**Phase 2: Combined Pipeline** (2 days)
- Day 4: Implement optimal hybrid pipeline
- Day 5: Test on 10 documents, validate 95% accuracy

**Phase 3: Scale Testing** (1 day)
- Day 6: Run on Hjorthagen (15 docs) + SRS (28 docs)
- Confirm performance at scale

**Total**: 6 days to production-ready hybrid system

---

## 🚀 Next Steps

1. **Implement experiment scripts** (code/test_hybrid_optimization.py)
2. **Run Experiment 1** (OCR-only baseline) - establishes floor
3. **Run Experiment 3** (section-aware routing) - likely biggest win
4. **Combine winners** into optimal pipeline
5. **Deploy to Gracian Pipeline**

---

**Key Insight**: We don't need to run ALL experiments sequentially. We can:
- Run Exp 1 & 3 first (independent)
- Skip Exp 2 & 4 if Exp 3 already gives 95% at low cost
- Only run Exp 5 if we need final optimization

**ULTRATHINKING Principle**: Measure first, optimize second, deploy third.
