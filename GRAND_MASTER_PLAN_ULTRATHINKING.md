# 🧠 GRAND MASTER PLAN: Ultrathinking Path to 95% Success @ 75% Coverage

**Created**: October 11, 2025
**Context**: Post-Week 3 Day 3 Comprehensive Test (42 PDFs)
**Current State**: 88.1% success, 56.1% coverage
**Target State**: 95% success, 75% coverage
**Timeline**: Week 3 Day 4-7 (4 days intensive focus)

---

## 🎯 **EXECUTIVE SUMMARY**

The Week 3 Day 3 comprehensive test validated our multi-agent architecture works (88.1% success rate), but revealed **three critical blockers** preventing production readiness:

1. **SRS Dataset Coverage Gap**: 18-point drop (66.9% → 48.8%) on citywide documents
2. **Infrastructure Fragility**: 11.9% connection failures unacceptable for 26K PDF corpus
3. **Quality Outliers**: 24.3% of corpus achieving <50% coverage drags down average

**Ultrathinking Insight**: These are not isolated bugs but **architectural deficiencies** revealing fundamental assumptions about document diversity, error resilience, and extraction completeness.

---

## 🔬 **PART 1: ULTRATHINKING ROOT CAUSE ANALYSIS**

### **Issue 1: The SRS Dataset Coverage Gap (66.9% → 48.8%)**

#### **Surface Symptom**:
Hjorthagen PDFs (local neighborhood) extract at 66.9% average coverage, while SRS PDFs (citywide sample) only achieve 48.8% coverage.

#### **Ultrathinking Deep Dive**:

**Hypothesis 1: Document Structure Divergence**
- **Evidence**: Hjorthagen is a single neighborhood → standardized templates
- **Evidence**: SRS is citywide → diverse accounting firms, report formats
- **Conclusion**: Multi-agent prompts are optimized for Hjorthagen patterns

**Hypothesis 2: Scanned vs Machine-Readable Correlation**
- **Known**: 49.3% of corpus is scanned (requires OCR)
- **Question**: Is SRS dataset skewed toward scanned documents?
- **Test**: Compare Docling OCR quality between datasets
- **Expected**: Lower OCR quality = lower extraction coverage

**Hypothesis 3: Field Type Distribution**
- **Observation**: SRS has more failed financial extractions
- **Question**: Are SRS PDFs missing certain sections entirely?
- **Analysis Needed**: Field-by-field comparison (which fields fail in SRS?)
- **Expected**: Certain fields (e.g., loan details, notes) harder in SRS

**Ultrathinking Conclusion**:
The coverage gap is **not random**. It reflects:
1. **Template overfitting**: Agents trained on Hjorthagen patterns
2. **OCR quality variance**: Scanned documents underperforming
3. **Structural diversity**: SRS has more non-standard report formats

**Strategic Solution Path**:
- Create **diverse ground truth** from both datasets
- Implement **adaptive prompts** that detect document type
- Add **OCR quality gates** (if Docling confidence <0.7, use vision fallback)
- Test **Branch B** (Docling-heavy) which may handle diversity better

---

### **Issue 2: Connection Errors (5/42 = 11.9% Failure Rate)**

#### **Surface Symptom**:
5 PDFs failed with "Connection error" during LLM API calls:
- brf_47809.pdf
- brf_47903.pdf
- brf_48663.pdf
- brf_52576.pdf
- brf_53107.pdf

#### **Ultrathinking Deep Dive**:

**Hypothesis 1: API Rate Limiting**
- **Evidence**: Errors clustered in time (sequential processing)
- **OpenAI Rate Limits**: 10,000 requests/minute (tier 4)
- **Current Load**: ~15 agents × 42 PDFs = 630 calls in 4 hours
- **Conclusion**: NOT rate limiting (only ~2.6 calls/minute)

**Hypothesis 2: Network Timeouts**
- **Evidence**: Long-running PDFs (brf_53546 took 10,688s = 3 hours!)
- **Default Timeout**: 120s per OpenAI request
- **Failure Pattern**: Some PDFs very large or complex
- **Conclusion**: Timeouts likely culprit

**Hypothesis 3: OpenAI Service Degradation**
- **Evidence**: Errors transient (not reproducible on retry)
- **Known Issue**: OpenAI has intermittent 5xx errors
- **Industry Standard**: 99.9% uptime = 0.1% expected failures
- **Conclusion**: Some failures inevitable

**Ultrathinking Conclusion**:
Connection errors are **infrastructure hygiene**, not architecture flaws. But 11.9% is 119x higher than industry standard (0.1%). This suggests:
1. **No retry logic**: Single failures become permanent
2. **No timeout handling**: Long docs hang entire pipeline
3. **No graceful degradation**: One agent failure fails entire PDF

**Strategic Solution Path**:
- Implement **exponential backoff retry** (3 attempts: 1s, 2s, 4s delays)
- Add **per-agent timeouts** (120s for LLM call, 300s total extraction)
- Build **partial extraction mode** (save successful agents, mark failures)
- Add **circuit breaker pattern** (if 3 consecutive failures, pause and alert)
- Log **detailed error context** (request ID, model, payload size, latency)

---

### **Issue 3: Low Coverage Outliers (9 PDFs <50% Coverage)**

#### **Surface Symptom**:
24.3% of test corpus (9/37 successful PDFs) achieved <50% coverage:
- brf_78906: 6.0%
- brf_43334: 6.8%
- brf_282765: 13.7%
- brf_57125: 14.5%
- brf_76536: 0.0% (!)
- brf_276629: 1.7%
- brf_78730: 4.3%
- brf_80193: 1.7%
- brf_83301: 12.0%

#### **Ultrathinking Deep Dive**:

**Hypothesis 1: Missing Sections**
- **Test**: Check if these PDFs have all expected sections
- **Example**: brf_76536 at 0.0% suggests document fundamentally incompatible
- **Analysis**: Are these "economic plans" mislabeled as "annual reports"?
- **Conclusion**: Need **document type detection** before extraction

**Hypothesis 2: OCR Total Failure**
- **Evidence**: All low performers might be scanned documents
- **Test**: Check Docling OCR confidence scores
- **Threshold**: If confidence <0.5, flag for manual review
- **Conclusion**: May need **alternative OCR backend** (EasyOCR, RapidOCR)

**Hypothesis 3: Agent Routing Failure**
- **Evidence**: Low coverage despite sections present
- **Test**: Check LLM orchestrator page assignments
- **Question**: Are agents being sent to wrong pages?
- **Conclusion**: **Vision sectionizer** may misidentify section boundaries

**Hypothesis 4: Synonym Mapping Gaps**
- **Evidence**: Swedish term mapping only 78.4% for some PDFs
- **Test**: Check if low performers use non-standard terminology
- **Example**: "Förvaltningsberättelse" vs "Förvaltarens berättelse"
- **Conclusion**: Need **fuzzy matching** for synonyms (not exact string match)

**Ultrathinking Conclusion**:
Low performers reveal **edge cases** our system wasn't designed for:
1. **Non-annual-report documents**: Need type detection
2. **OCR catastrophic failures**: Need quality gates
3. **Routing logic failures**: Need validation of section detection
4. **Terminology variants**: Need fuzzy synonym matching

**Strategic Solution Path**:
- Add **document type classifier** (annual report vs other) before extraction
- Implement **OCR quality gates** (Docling confidence threshold)
- Add **section detection validation** (agent pages vs ground truth)
- Upgrade **synonym matcher** to fuzzy matching (Levenshtein distance <3)
- Create **manual review queue** for 0-10% coverage documents

---

## 📋 **PART 2: THE GRAND MASTER PLAN (4-Day Sprint)**

### **Day 4 (October 12): Infrastructure Resilience**

**Goal**: Eliminate connection errors, bring success rate to 95%+

#### **Task 4.1: Implement Exponential Backoff Retry**
**Location**: `gracian_pipeline/core/pydantic_extractor.py:_call_llm()`
**Implementation**:
```python
async def _call_llm_with_retry(prompt, context, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await openai_client.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"{prompt}\n\n{context}"}],
                timeout=120.0  # 2 minutes max per call
            )
            return response
        except (TimeoutError, ConnectionError, OpenAIError) as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # 1s, 2s, 4s
                logging.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
            else:
                logging.error(f"LLM call failed after {max_retries} attempts: {e}")
                return None  # Graceful degradation
```

**Testing**: Re-run 5 failed PDFs, expect 100% success

#### **Task 4.2: Add Partial Extraction Mode**
**Location**: `gracian_pipeline/core/parallel_orchestrator.py:extract_all_agents_parallel()`
**Implementation**:
```python
def extract_all_agents_parallel(pdf_path, allow_partial=True):
    results = {}
    failed_agents = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(extract_agent, agent): agent for agent in AGENTS}

        for future in as_completed(futures):
            agent = futures[future]
            try:
                results[agent] = future.result(timeout=300)  # 5 min max
            except Exception as e:
                logging.error(f"Agent {agent} failed: {e}")
                failed_agents.append(agent)
                if allow_partial:
                    results[agent] = None  # Mark as failed but continue
                else:
                    raise

    # Calculate success metrics
    success_rate = len([r for r in results.values() if r is not None]) / len(results)

    return {
        'results': results,
        'success_rate': success_rate,
        'failed_agents': failed_agents,
        'partial_extraction': len(failed_agents) > 0
    }
```

**Testing**: Simulate agent failure, verify pipeline continues

#### **Task 4.3: Add Circuit Breaker Pattern**
**Location**: `gracian_pipeline/core/circuit_breaker.py` (NEW)
**Implementation**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=300):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen("Circuit breaker is open, too many failures")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.reset()
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "OPEN"
                logging.error(f"Circuit breaker opened after {self.failures} failures")
            raise

    def reset(self):
        self.failures = 0
        self.state = "CLOSED"
```

**Testing**: Simulate OpenAI outage, verify graceful shutdown

**Day 4 Success Criteria**:
- ✅ 5 failed PDFs now succeed (100% retry success)
- ✅ Re-run 42-PDF test: 95%+ success rate (≤2 failures acceptable)
- ✅ Average processing time ≤120s per PDF (no hangs)

---

### **Day 5 (October 13): Quality Improvement - Fix Low Performers**

**Goal**: Boost low-performer coverage from <50% to 60%+, bring average to 65%

#### **Task 5.1: Document Type Classification**
**Location**: `gracian_pipeline/core/document_classifier.py` (NEW)
**Implementation**:
```python
def classify_document_type(pdf_path):
    """
    Classify if document is:
    - annual_report (Årsredovisning)
    - economic_plan (Ekonomisk plan)
    - bylaws (Stadgar)
    - energy_declaration (Energideklaration)
    """
    # Extract first 3 pages for classification
    with fitz.open(pdf_path) as doc:
        first_pages_text = " ".join([doc[i].get_text() for i in range(min(3, len(doc)))])

    # Keyword detection
    if "årsredovisning" in first_pages_text.lower():
        return "annual_report", 1.0
    elif "ekonomisk plan" in first_pages_text.lower():
        return "economic_plan", 0.9
    elif "stadgar" in first_pages_text.lower():
        return "bylaws", 0.9
    elif "energideklaration" in first_pages_text.lower():
        return "energy_declaration", 0.9
    else:
        # Fallback: Use LLM for classification
        prompt = f"Classify this Swedish BRF document: {first_pages_text[:500]}"
        response = openai_client.create(model="gpt-4o-mini", messages=[...])
        return response.type, response.confidence
```

**Testing**: Run on 9 low performers, expect 3-4 to be reclassified as non-annual-reports

#### **Task 5.2: OCR Quality Gate**
**Location**: `gracian_pipeline/core/docling_adapter_ultra.py:extract_with_docling()`
**Implementation**:
```python
def extract_with_docling(pdf_path):
    result = docling_pipeline.convert(pdf_path)

    # Calculate OCR confidence
    ocr_confidence = result.metadata.get('ocr_confidence', 1.0)

    if ocr_confidence < 0.5:
        logging.warning(f"Low OCR confidence ({ocr_confidence:.2f}) for {pdf_path}")
        # Try alternative OCR backend
        result_easyocr = extract_with_easyocr(pdf_path)
        if result_easyocr.confidence > ocr_confidence:
            logging.info(f"EasyOCR performed better ({result_easyocr.confidence:.2f})")
            return result_easyocr

    return result
```

**Testing**: Test on brf_76536 (0% coverage), expect improvement with EasyOCR

#### **Task 5.3: Fuzzy Synonym Matching**
**Location**: `gracian_pipeline/core/synonyms.py:find_matching_terms()`
**Implementation**:
```python
from fuzzywuzzy import fuzz

def find_matching_terms(text, term_list, threshold=85):
    """
    Find terms using fuzzy matching (Levenshtein distance).
    threshold=85 allows ~3 character differences
    """
    matches = []
    for term in term_list:
        # Check exact match first
        if term.lower() in text.lower():
            matches.append((term, 100))
            continue

        # Fuzzy match for near-misses
        ratio = fuzz.partial_ratio(term.lower(), text.lower())
        if ratio >= threshold:
            matches.append((term, ratio))

    return sorted(matches, key=lambda x: x[1], reverse=True)
```

**Testing**: Test on PDFs with low Swedish term mapping (78.4%), expect 90%+ after fix

#### **Task 5.4: Section Detection Validation**
**Location**: `gracian_pipeline/core/vision_sectionizer.py:vision_sectionize()`
**Implementation**:
```python
def vision_sectionize(pdf_path, validate=True):
    sections = _detect_sections_with_llm(pdf_path)

    if validate:
        # Validate section assignments make sense
        for section in sections:
            # Check: Does section page range contain expected keywords?
            expected_keywords = SECTION_KEYWORDS.get(section['name'], [])
            actual_text = extract_pages_text(pdf_path, section['start_page'], section['end_page'])

            keyword_matches = sum(1 for kw in expected_keywords if kw in actual_text.lower())
            confidence = keyword_matches / len(expected_keywords) if expected_keywords else 0.5

            section['validation_confidence'] = confidence

            if confidence < 0.3:
                logging.warning(f"Low validation confidence ({confidence:.2f}) for section {section['name']}")

    return sections
```

**Testing**: Check low performers, verify correct page assignments

**Day 5 Success Criteria**:
- ✅ 3-4 low performers reclassified as non-annual-reports (excluded from test)
- ✅ Remaining low performers boost to 60%+ coverage (from <50%)
- ✅ Overall average coverage: 56.1% → 65% (+8.9 points)

---

### **Day 6 (October 14): SRS Dataset Coverage Gap Analysis**

**Goal**: Identify and fix SRS-specific extraction failures, boost from 48.8% to 60%

#### **Task 6.1: Field-by-Field Comparison**
**Location**: `analyze_srs_hjorthagen_gap.py` (NEW)
**Implementation**:
```python
def compare_field_extraction(hjorthagen_results, srs_results):
    """
    Compare which fields fail more in SRS vs Hjorthagen
    """
    hjorthagen_by_field = defaultdict(list)
    srs_by_field = defaultdict(list)

    for result in hjorthagen_results:
        for field, value in result.items():
            hjorthagen_by_field[field].append(value is not None)

    for result in srs_results:
        for field, value in result.items():
            srs_by_field[field].append(value is not None)

    # Calculate success rates
    comparison = {}
    for field in hjorthagen_by_field.keys():
        hjorth_rate = sum(hjorthagen_by_field[field]) / len(hjorthagen_by_field[field])
        srs_rate = sum(srs_by_field[field]) / len(srs_by_field[field])
        gap = hjorth_rate - srs_rate

        comparison[field] = {
            'hjorthagen_success': hjorth_rate,
            'srs_success': srs_rate,
            'gap': gap,
            'priority': 'HIGH' if gap > 0.3 else 'MEDIUM' if gap > 0.15 else 'LOW'
        }

    return sorted(comparison.items(), key=lambda x: x[1]['gap'], reverse=True)
```

**Testing**: Run on Week 3 Day 3 results, identify top 5 problematic fields

#### **Task 6.2: Adaptive Prompts by Document Type**
**Location**: `gracian_pipeline/prompts/agent_prompts.py`
**Implementation**:
```python
def get_agent_prompt(agent_name, document_style='standard'):
    """
    Return different prompts based on document characteristics
    """
    base_prompt = AGENT_PROMPTS[agent_name]

    if document_style == 'scanned':
        # Add OCR error tolerance
        base_prompt += "\n\nNote: This document was scanned. Text may contain OCR errors. Be tolerant of minor typos."
    elif document_style == 'non_standard':
        # Add flexibility for unusual formats
        base_prompt += "\n\nNote: This document uses a non-standard format. Look for semantically equivalent sections."
    elif document_style == 'old':
        # Add historical format awareness
        base_prompt += "\n\nNote: This is an older document. Field names and formats may differ from modern standards."

    return base_prompt
```

**Testing**: Test on SRS low performers, measure coverage improvement

#### **Task 6.3: OCR Quality Comparison**
**Location**: `analyze_ocr_quality.py` (NEW)
**Implementation**:
```python
def compare_ocr_quality(hjorthagen_pdfs, srs_pdfs):
    """
    Check if SRS dataset has lower OCR quality
    """
    hjorth_confidences = []
    srs_confidences = []

    for pdf in hjorthagen_pdfs:
        result = docling_pipeline.convert(pdf)
        hjorth_confidences.append(result.metadata.get('ocr_confidence', 1.0))

    for pdf in srs_pdfs:
        result = docling_pipeline.convert(pdf)
        srs_confidences.append(result.metadata.get('ocr_confidence', 1.0))

    return {
        'hjorthagen_avg': np.mean(hjorth_confidences),
        'hjorthagen_std': np.std(hjorth_confidences),
        'srs_avg': np.mean(srs_confidences),
        'srs_std': np.std(srs_confidences),
        'significant_difference': stats.ttest_ind(hjorth_confidences, srs_confidences)
    }
```

**Testing**: Determine if OCR quality explains coverage gap

**Day 6 Success Criteria**:
- ✅ Identified top 5 fields causing SRS gap
- ✅ Validated OCR quality hypothesis (confirmed or rejected)
- ✅ Implemented fixes boosting SRS coverage: 48.8% → 58% (+9.2 points)

---

### **Day 7 (October 15): Validation & Missing Features**

**Goal**: Implement missing validation features to boost coverage 65% → 75%

#### **Task 7.1: Multi-Source Aggregation**
**Location**: `gracian_pipeline/core/multi_source_aggregator.py` (NEW)
**Implementation**:
```python
def aggregate_field_from_multiple_sources(field_name, agent_results):
    """
    Combine data from multiple agents for same field.
    Use highest-confidence value.
    """
    candidates = []

    for agent, result in agent_results.items():
        if field_name in result and result[field_name] is not None:
            confidence = result.get(f'{field_name}_confidence', 0.5)
            candidates.append({
                'value': result[field_name],
                'confidence': confidence,
                'source': agent,
                'source_page': result.get(f'{field_name}_page', None)
            })

    if not candidates:
        return None

    # Sort by confidence, return highest
    best_candidate = sorted(candidates, key=lambda x: x['confidence'], reverse=True)[0]

    return {
        'value': best_candidate['value'],
        'confidence': best_candidate['confidence'],
        'sources': [c['source'] for c in candidates],
        'consensus': len(set(c['value'] for c in candidates)) == 1  # All agree?
    }
```

**Testing**: Test on fields extracted by multiple agents (e.g., "tillgångar" from financial_agent and balance_sheet_agent)

#### **Task 7.2: Validation Thresholds (Tolerant Validation)**
**Location**: `gracian_pipeline/validation/validation_engine.py:validate_balance_sheet()`
**Implementation**:
```python
def validate_balance_sheet(balance_sheet, tolerance=0.05):
    """
    Validate balance sheet equation with tolerance for rounding errors.
    Assets = Liabilities + Equity (±5%)
    """
    assets = balance_sheet.get('assets', 0)
    liabilities = balance_sheet.get('liabilities', 0)
    equity = balance_sheet.get('equity', 0)

    if assets == 0:
        return True, "No assets to validate"

    right_side = liabilities + equity
    difference = abs(assets - right_side)
    relative_error = difference / assets

    if relative_error <= tolerance:
        return True, f"Balance sheet validates (error: {relative_error:.2%})"
    else:
        return False, f"Balance sheet doesn't balance (error: {relative_error:.2%}, diff: {difference:,.0f})"
```

**Testing**: Re-validate Week 3 Day 3 results, expect fewer validation errors

#### **Task 7.3: Swedish-First Fee Terminology**
**Location**: `gracian_pipeline/core/schema_comprehensive.py:Fee`
**Implementation**:
```python
class Fee(BaseModel):
    # Swedish fields (primary)
    arsavgift_per_sqm_sek: Optional[float] = None
    hyresavgift_per_sqm_sek: Optional[float] = None
    kapitalkostnad_per_sqm_sek: Optional[float] = None

    # English aliases (auto-populated)
    @computed_field
    @property
    def annual_fee_per_sqm_sek(self) -> Optional[float]:
        return self.arsavgift_per_sqm_sek

    @computed_field
    @property
    def rent_per_sqm_sek(self) -> Optional[float]:
        return self.hyresavgift_per_sqm_sek

    # Terminology tracking
    _fee_terminology_found: Optional[List[str]] = []
    _fee_extraction_confidence: Optional[float] = None
```

**Testing**: Re-run extraction, expect 0% → 95% on fee_swedish_primary test

#### **Task 7.4: Calculated Metrics**
**Location**: `gracian_pipeline/validation/calculated_metrics.py` (NEW)
**Implementation**:
```python
def calculate_financial_ratios(financial_data):
    """
    Calculate derived metrics for validation and analysis
    """
    metrics = {}

    # Debt-to-Equity Ratio
    if financial_data.liabilities and financial_data.equity:
        metrics['debt_to_equity_ratio'] = financial_data.liabilities / financial_data.equity

    # Current Ratio
    if financial_data.current_assets and financial_data.current_liabilities:
        metrics['current_ratio'] = financial_data.current_assets / financial_data.current_liabilities

    # Equity Ratio
    if financial_data.equity and financial_data.assets:
        metrics['equity_ratio'] = financial_data.equity / financial_data.assets

    # Per-apartment metrics
    if financial_data.total_apartments:
        metrics['assets_per_apartment'] = financial_data.assets / financial_data.total_apartments
        metrics['equity_per_apartment'] = financial_data.equity / financial_data.total_apartments

    return metrics
```

**Testing**: Validate calculated metrics match manual calculations

**Day 7 Success Criteria**:
- ✅ Multi-source aggregation: 0% → 80% test pass rate
- ✅ Validation thresholds: Fewer false errors, maintain quality
- ✅ Swedish-first fields: 0% → 95% test pass rate
- ✅ Calculated metrics: 0% → 100% test pass rate
- ✅ **Overall coverage boost**: 65% → 75% (+10 points)

---

## 📊 **PART 3: SUCCESS METRICS & VALIDATION**

### **End-of-Sprint Targets** (October 15 EOD)

| Metric | Day 3 Baseline | Day 7 Target | Test Method |
|--------|----------------|--------------|-------------|
| **Success Rate** | 88.1% | 95%+ | Re-run 42 PDFs + 5 failed |
| **Overall Coverage** | 56.1% | 75% | 42-PDF average |
| **Hjorthagen Coverage** | 66.9% | 75% | 15-PDF subset |
| **SRS Coverage** | 48.8% | 60% | 27-PDF subset |
| **Low Performers** | 24.3% <50% | 10% <50% | Count PDFs <50% |
| **Connection Errors** | 11.9% | <2% | Infrastructure test |
| **Swedish Terms** | 97.3% | 98%+ | Maintain excellence |

### **Component Test Pass Rates**

| Component | Day 3 | Day 7 Target |
|-----------|-------|--------------|
| Confidence Scores Present | 100% | 100% ✅ |
| Source Pages Tracked | 78.4% | 95% |
| Multi-Source Aggregation | 0% | 80% |
| Validation Thresholds | 0% | 100% |
| Swedish-First Fields | 0% | 95% |
| Calculated Metrics | 0% | 100% |
| Data Preservation | 97.3% | 99%+ |

### **Validation Protocol**

#### **Phase 1: Unit Tests** (Each feature as implemented)
```bash
# Test retry logic
python test_retry_logic.py

# Test OCR quality gate
python test_ocr_quality_gate.py

# Test fuzzy synonym matching
python test_fuzzy_synonyms.py

# Test multi-source aggregation
python test_multi_source_aggregation.py
```

#### **Phase 2: Integration Test** (Day 7 PM)
```bash
# Re-run comprehensive 42-PDF test
python test_comprehensive_42_pdfs.py --clean-run

# Expected results:
# - Success: 40+/42 (95%+)
# - Coverage: 75% average
# - Processing time: <120s average
```

#### **Phase 3: Production Readiness** (Post-Day 7)
```bash
# Scale to 100 PDFs (diverse sample)
python test_100_pdf_sample.py

# Validate:
# - Success rate 95%+
# - Coverage 70%+ (conservative)
# - Cost per PDF <$0.10
# - No infrastructure failures
```

---

## 🎯 **PART 4: RISK MITIGATION**

### **Risk 1: Fixes Don't Improve SRS Coverage**

**Probability**: Medium (30%)
**Impact**: High (blocks production)

**Mitigation**:
- Run **Branch B comparison test** (Docling-heavy pipeline)
- If Branch B achieves >60% on SRS, pivot to hybrid approach
- Use Branch B for structured data, Branch A for narratives

**Contingency**:
- Accept 60% SRS coverage as "good enough"
- Focus on 100% success rate instead
- Plan "SRS-specific training" for Week 4

---

### **Risk 2: Infrastructure Fixes Introduce New Bugs**

**Probability**: Low (20%)
**Impact**: Medium (delays timeline)

**Mitigation**:
- Implement **feature flags** (can disable retry logic if broken)
- Maintain **rollback capability** (git tags for each day)
- Add **comprehensive logging** to debug failures quickly

**Contingency**:
- Roll back to Day 3 baseline if critical bug found
- Fix incrementally, one feature at a time
- Extend timeline by 1-2 days if needed

---

### **Risk 3: Validation Features Don't Boost Coverage**

**Probability**: Medium (40%)
**Impact**: Medium (miss 75% target)

**Mitigation**:
- Prioritize features with **highest expected impact**:
  1. Multi-source aggregation (est. +5-10 points)
  2. Fuzzy synonym matching (est. +3-5 points)
  3. OCR quality gates (est. +2-4 points)
- If not working, pivot to **ground truth expansion** instead

**Contingency**:
- Accept 70% coverage as "Phase 1 complete"
- Plan "Phase 2: Table extraction" (Branch B) for Week 4
- Table extraction could add +10-15 points (financial fields)

---

## 🚀 **PART 5: EXECUTION PLAN**

### **Daily Standup Format**

**Each morning (9:00 AM)**:
1. Review previous day metrics
2. Adjust priorities based on results
3. Commit plan for today

**Each evening (6:00 PM)**:
1. Commit day's code with detailed message
2. Run comprehensive test
3. Document results in `WEEK3_DAY{X}_SUMMARY.md`

### **Git Workflow**

```bash
# Start each day
git checkout -b week3-day{X}-{feature}

# End each day
git add .
git commit -m "Week 3 Day {X} Complete: {Feature} Implementation"
git push origin week3-day{X}-{feature}

# Merge to main after validation
git checkout docling-driven-gracian-pipeline
git merge week3-day{X}-{feature}
git push
```

### **Communication Protocol**

**Daily Updates** (to CLAUDE.md):
- Update "Current Status Summary" section
- Update metrics tables
- Log progress in "Update History"

**End-of-Sprint** (Day 7):
- Create `WEEK3_SPRINT_COMPLETE.md` with full analysis
- Update README.md with new capabilities
- Tag release: `v1.0.0-week3-validated`

---

## 🎓 **PART 6: LEARNING & CONTINUOUS IMPROVEMENT**

### **Key Insights from Week 3 Day 3**

1. **Document Diversity Matters**: Hjorthagen (homogeneous) != SRS (diverse)
   - **Learning**: Always test on diverse samples, not just convenient ones
   - **Action**: Create "diversity score" for test datasets

2. **Infrastructure Is Product**: 11.9% connection failures = 119x industry standard
   - **Learning**: Don't assume external APIs are reliable
   - **Action**: Build resilience from day 1, not as afterthought

3. **Edge Cases Are Common**: 24.3% low performers = 1 in 4 documents
   - **Learning**: "Edge cases" are actually normal in production
   - **Action**: Design for failure, not just success

4. **Incremental Testing Works**: 5 PDF → 42 PDF → 100 PDF progression
   - **Learning**: Each test revealed new issues not seen at smaller scale
   - **Action**: Always plan multi-stage validation

### **Post-Sprint Retrospective Questions**

1. **What worked well?**
   - Multi-agent architecture (88.1% success proves concept)
   - Swedish term mapping (97.3% exceeds expectations)
   - Test-driven validation (caught all major issues)

2. **What needs improvement?**
   - Handling document diversity (SRS gap)
   - Infrastructure resilience (connection errors)
   - Quality consistency (low performers)

3. **What should we stop doing?**
   - Assuming homogeneous document types
   - Testing only on "clean" Hjorthagen PDFs
   - Ignoring infrastructure failure modes

4. **What should we start doing?**
   - Regular diversity audits of test data
   - Chaos engineering (intentional failure injection)
   - Ground truth expansion to match production diversity

---

## ✅ **PART 7: SUCCESS DEFINITION**

### **Sprint Success** = ALL of the following:

1. ✅ **Success Rate**: 95%+ on 42-PDF re-test (≤2 failures)
2. ✅ **Overall Coverage**: 75% average across all PDFs
3. ✅ **SRS Coverage**: 60%+ (12-point improvement from 48.8%)
4. ✅ **Infrastructure**: Zero connection errors in final test
5. ✅ **Low Performers**: Reduced from 24.3% to <10% of corpus
6. ✅ **Component Tests**: 80%+ pass rate on all missing features

### **Stretch Goals** (Bonus achievements):

- 🎯 **98% success rate** (only 1 failure acceptable)
- 🎯 **80% overall coverage** (exceed target by 5 points)
- 🎯 **70% SRS coverage** (match Hjorthagen performance)
- 🎯 **95% component test pass rate** (near-perfect implementation)

---

## 🧠 **FINAL ULTRATHINKING SYNTHESIS**

The Week 3 Day 3 test revealed **the real world** to our laboratory system:

- **Hjorthagen** was our **controlled experiment** (clean, consistent, high-quality)
- **SRS** is the **production reality** (messy, diverse, unpredictable)

**The core insight**: We built a system optimized for **Hjorthagen-like documents**, not for the **full diversity of the 26,342-PDF corpus**.

**The grand strategy**: This 4-day sprint transforms us from a **research prototype** to a **production-ready system** by:

1. **Hardening infrastructure** (resilience to failures)
2. **Expanding capabilities** (handling document diversity)
3. **Deepening intelligence** (multi-source aggregation, fuzzy matching)
4. **Validating at scale** (100-PDF readiness test)

**The ultimate goal**: Not just 75% coverage, but **75% coverage on ANY Swedish BRF annual report**, regardless of:
- Accounting firm producing it
- Scanned vs machine-readable
- Standard vs non-standard format
- Simple vs complex financial structure

**Success means**: We can confidently say "Deploy to 26,342 PDFs" and expect:
- 95% success rate (1,317 failures max, manageable)
- 70-75% average coverage (18-21 fields per document)
- $1,317-$2,634 total cost ($0.05-$0.10 per PDF)
- 24-48 hours processing time (50 workers parallel)

**This is achievable.** The architecture is sound. The gaps are understood. The fixes are targeted. The timeline is realistic.

**Let's execute. 🚀**

---

**Document Created**: October 11, 2025
**Last Updated**: October 11, 2025
**Status**: ACTIVE SPRINT PLAN
**Owner**: Claude Code + Human Collaboration
**Next Review**: October 15, 2025 (End of Sprint)

---

*"The master has failed more times than the beginner has even tried."* — This sprint is about **learning from failure** (Week 3 Day 3 gaps) and **systematically fixing** every identified issue. No shortcuts. No assumptions. Just **rigorous, ultrathinking-driven engineering**. 🎯
