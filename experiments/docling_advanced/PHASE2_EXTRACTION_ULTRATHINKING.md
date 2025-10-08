# Phase 2 Implementation - Hierarchical Extraction & QC ULTRATHINKING

**Date**: 2025-10-08
**Context**: Phase 1 complete (Stages 1-3), now designing Stages 4-5
**Goal**: Implement 3-pass hierarchical extraction + quality validation gates

---

## 🎯 Phase 2 Scope

### Stage 4: Hierarchical Extraction (3 Passes)
- **Pass 1**: High-level extraction (governance, property, operations) - Grok, parallel
- **Pass 2**: Financial + notes (detailed) - GPT-4o, sequential
- **Pass 3**: Validation + calculated metrics - GPT-5, conditional

### Stage 5: Quality Validation Gates
- **Coverage check**: ≥95% of required fields extracted
- **Numeric QC**: Financial tolerance validation
- **Evidence tracking**: ≥95% of extractions cite source pages

---

## 🧠 ULTRATHINKING: Critical Design Decisions

### Decision #1: Agent Grouping Strategy

**Question**: How to group 24 agents across 3 passes for optimal cost/performance?

#### Evidence from Gracian Pipeline
From `CLAUDE.md` and `agent_prompts.py`:
- Total agents: 24 (13 implemented, 11 missing prompts)
- Agent categories:
  - **Governance** (5 agents): governance, auditor, board, chair, nomination
  - **Financial** (3 agents): financial, balance_sheet, income_statement
  - **Property** (4 agents): property, apartments, commercial, common_areas
  - **Notes** (7 agents): notes_accounting, notes_loans, notes_buildings, notes_receivables, notes_reserves, notes_tax, notes_other
  - **Operations** (3 agents): operations, maintenance, suppliers
  - **Policies** (2 agents): policies, events

#### Option 1A: By Complexity (Simple → Complex)
```python
Pass 1 (Grok, parallel):     governance, property, operations (11 agents)
Pass 2 (GPT-4o, sequential): financial, notes (10 agents)
Pass 3 (GPT-5, conditional): validation, metrics (3 calculated fields)
```

**Pros**:
- ✅ Simple agents run cheap/fast in parallel
- ✅ Complex financial/notes get GPT-4o Swedish expertise
- ✅ Natural dependency flow (governance → financial → validation)

**Cons**:
- ⚠️ May need financial data earlier for other agents
- ⚠️ Parallel execution complexity

#### Option 1B: By Data Dependencies (Hierarchical)
```python
Pass 1 (Grok, parallel):     governance, property (5 agents) - no dependencies
Pass 2 (GPT-4o, sequential): financial, notes, operations (15 agents) - depends on Pass 1
Pass 3 (GPT-5, conditional): validation + 3 calculated metrics - depends on Pass 2
```

**Pros**:
- ✅ Clear dependency chain
- ✅ Financial + notes together (hierarchical extraction from Gracian)
- ✅ Operations can reference governance/property

**Cons**:
- ⚠️ Pass 2 very large (15 agents)
- ⚠️ Sequential execution may be slow

#### Option 1C: By Document Section (Routing-Based) ✅ **RECOMMENDED**
```python
Pass 1 (Grok, parallel):
  - Main sections: governance, property, operations (8 agents)
  - Simple routing, text-based extraction
  - Pages: governance (1-5), property (varies), operations (varies)

Pass 2 (GPT-4o, sequential):
  - Financial sections: financial, notes (8 agents)
  - Complex Swedish tables, hierarchical dependencies
  - Pages: financial statements (varies), notes (routed)

Pass 3 (GPT-5, conditional):
  - Cross-field validation
  - Calculated metrics (debt/sqm, solidarity %, fee/sqm)
  - Coaching if <95% quality
```

**Pros**:
- ✅ Leverages Stage 3 routing results directly
- ✅ Aligns with document structure (main sections vs notes)
- ✅ Optimized page allocation (no redundant PDF processing)
- ✅ Matches Gracian's proven hierarchical extraction pattern

**Cons**:
- ⚠️ Requires clear routing → extraction mapping

**DECISION**: **Option 1C (Routing-Based)** - Best alignment with Phase 1 architecture

---

### Decision #2: LLM Model Selection

**Question**: Which models for each pass, and why?

#### Available Models (from Gracian `.env`)
- **Grok**: `xai-grok-vision-beta` - Good for text, multimodal, cheap ($0.0005/1k input)
- **GPT-4o**: `gpt-4o-2024-11-20` - Best Swedish handling, multimodal ($0.0025/1k input)
- **GPT-5**: `gpt-5-mini` (?) - For validation/coaching
- **Gemini 2.5-Pro**: `gemini-2.5-pro` - Multimodal alternative ($0.00125/1k input)
- **Qwen 3-VL**: Via OpenRouter - Vision sectionizer ($0.0008/1k input)

#### Evidence from Gracian Pipeline
From `vision_qc.py:88-282`:
- Grok used for vision extraction (base64 images)
- Gemini used for retry fallback (exponential backoff)
- OpenAI/GPT-4o used for coaching (orchestrator)
- Qwen used for sectionizing (OpenRouter)

#### Option 2A: Cost-Optimized (All Grok)
```python
Pass 1: Grok (cheap, parallel)
Pass 2: Grok (cheap, sequential)
Pass 3: Grok (cheap, conditional)
Total: ~$0.01/doc
```

**Pros**: ✅ Minimal cost
**Cons**: ❌ May not handle Swedish financial tables well

#### Option 2B: Quality-Optimized (All GPT-4o) ✅ **RECOMMENDED**
```python
Pass 1: GPT-4o (reliable, parallel)
Pass 2: GPT-4o (Swedish expertise, sequential)
Pass 3: GPT-4o (consistency, conditional)
Total: ~$0.15/doc
```

**Pros**:
- ✅ Best Swedish language handling
- ✅ Proven in Gracian Pipeline (95/95 accuracy achieved)
- ✅ Consistent model behavior across passes

**Cons**:
- ⚠️ Higher cost than hybrid approach

#### Option 2C: Hybrid (Grok + GPT-4o + GPT-5)
```python
Pass 1: Grok (simple agents, parallel)     → $0.005
Pass 2: GPT-4o (complex Swedish, sequential) → $0.15
Pass 3: GPT-5 (validation, conditional)     → $0.05 (10% need coaching)
Total: ~$0.21/doc (weighted average)
```

**Pros**:
- ✅ Cost/quality balance
- ✅ Matches original ULTRATHINKING design (OPTIMAL_ARCHITECTURE_ULTRATHINKING.md)
- ✅ Leverages each model's strengths

**Cons**:
- ⚠️ Model consistency issues (different formats/quality)
- ⚠️ More complex error handling

**DECISION**: **Option 2B (All GPT-4o)** - Simplicity and proven Swedish performance outweigh cost savings

**Alternative**: If cost becomes issue, switch Pass 1 to Grok (Option 2C)

---

### Decision #3: Extraction Prompt Strategy

**Question**: How to structure prompts for each pass?

#### Evidence from Gracian Pipeline
From `agent_prompts.py:6-120`:
- Agent prompts: 87-120 words each
- Swedish-focused with multimodal instructions
- Schema prompt blocks appended (from `schema.py`)

Example (governance_agent):
```python
"""
You are analyzing a Swedish BRF annual report (årsredovisning). Extract governance information from the provided pages.

Focus on:
- Chairman (ordförande)
- Board members (styrelseledamöter)
- Auditors (revisorer)

Return JSON only. Include evidence_pages array.
"""
```

#### Option 3A: Reuse Gracian Agent Prompts Directly ✅ **RECOMMENDED**
```python
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS, get_prompt
from gracian_pipeline.core.schema import schema_prompt_block

prompt = AGENT_PROMPTS[agent_id] + "\n\n" + schema_prompt_block(agent_id)
```

**Pros**:
- ✅ Proven prompts (95/95 accuracy in Gracian)
- ✅ Zero prompt engineering needed
- ✅ Consistent with parent system

**Cons**:
- ⚠️ May need adaptation for Docling markdown vs images

#### Option 3B: Create New Prompts for Docling Context
```python
"""
You are analyzing Docling-extracted markdown from a Swedish BRF report.

Sections provided:
{section_headings}

Extract {agent_specific_fields}.
Return JSON only.
"""
```

**Pros**:
- ✅ Optimized for Docling markdown input
- ✅ Can reference section headings from Stage 3

**Cons**:
- ⚠️ Untested prompts (risk of lower accuracy)
- ⚠️ Prompt engineering time

**DECISION**: **Option 3A (Reuse Gracian Prompts)** with minor adaptations for Docling context

**Adaptation Strategy**:
```python
base_prompt = AGENT_PROMPTS[agent_id]
context_prompt = f"""
Document sections detected:
{json.dumps(section_headings, indent=2)}

{base_prompt}

Use the section headings above to locate relevant information.
"""
```

---

### Decision #4: Execution Strategy (Parallel vs Sequential)

**Question**: When to run agents in parallel vs sequential?

#### Evidence from Gracian Pipeline
From `orchestrator.py:141-334`:
- Orchestrator runs agents sequentially by default
- Concurrency controlled by `ORCHESTRATOR_CONCURRENCY=3` (env var)
- Threading/futures for parallel execution

From `OPTIMAL_ARCHITECTURE_ULTRATHINKING.md:223-226`:
- Pass 1: Parallel (no dependencies)
- Pass 2: Sequential (hierarchical dependencies)
- Pass 3: Conditional (only if needed)

#### Option 4A: All Parallel (Maximum Speed)
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(extract_agent, agent_id): agent_id
               for agent_id in all_agents}
    results = {agent_id: future.result()
               for future, agent_id in futures.items()}
```

**Pros**: ✅ Fastest execution (~15s for all agents)
**Cons**: ❌ Ignores hierarchical dependencies (financial needs governance context)

#### Option 4B: All Sequential (Maximum Reliability)
```python
results = {}
for agent_id in all_agents:
    results[agent_id] = extract_agent(agent_id)
```

**Pros**: ✅ Simple, predictable
**Cons**: ❌ Slow (~300s for 24 agents at 12s each)

#### Option 4C: Hybrid (Pass-Based Parallelism) ✅ **RECOMMENDED**
```python
# Pass 1: Parallel (no dependencies)
with ThreadPoolExecutor(max_workers=5) as executor:
    pass1_results = executor.map(extract_agent, pass1_agents)

# Pass 2: Sequential with context (hierarchical dependencies)
pass2_results = {}
for agent_id in pass2_agents:
    context = build_hierarchical_context(pass1_results, pass2_results)
    pass2_results[agent_id] = extract_agent(agent_id, context=context)

# Pass 3: Conditional validation
if quality_score(pass2_results) < 0.95:
    pass3_results = validate_and_coach(pass2_results)
```

**Pros**:
- ✅ Balances speed and reliability
- ✅ Respects data dependencies
- ✅ Matches original ULTRATHINKING design

**Cons**:
- ⚠️ More complex implementation

**DECISION**: **Option 4C (Hybrid Parallelism)** - Optimal speed/quality tradeoff

---

### Decision #5: Quality Gate Implementation

**Question**: How to implement the 95/95 quality gates?

#### Required Gates (from Phase 1 spec)
1. **Coverage check**: Σ(extracted_fields) / Σ(required_fields) ≥ 0.95
2. **Numeric QC**: Financial tolerance checks (±5% on amounts)
3. **Evidence tracking**: ≥95% of extractions cite source pages

#### Evidence from Gracian Pipeline
From `qc.py:8-75`:
- `numeric_qc()` function validates financial fields
- Tolerance checks: 6% for balance sheet, 10% for specific fields
- Returns dict with `errors`, `warnings`, `info`

From `bench.py:95-130`:
- `score_output()` heuristic scoring function
- Checks for non-empty values, evidence pages
- Returns float score 0.0-1.0

#### Option 5A: Simple Boolean Gates
```python
def passes_quality_gates(extraction: Dict) -> bool:
    coverage = calculate_coverage(extraction)
    numeric_ok = all(numeric_qc(agent_id, data) for agent_id, data in extraction.items())
    evidence_ok = has_sufficient_evidence(extraction)

    return coverage >= 0.95 and numeric_ok and evidence_ok
```

**Pros**: ✅ Simple pass/fail
**Cons**: ❌ No coaching opportunity, binary decision

#### Option 5B: Tiered Quality System ✅ **RECOMMENDED**
```python
class QualityResult:
    coverage: float
    numeric_qc_pass: bool
    evidence_ratio: float
    overall_score: float
    needs_coaching: bool
    failed_fields: List[str]

def evaluate_quality(extraction: Dict) -> QualityResult:
    result = QualityResult()
    result.coverage = calculate_coverage(extraction)
    result.numeric_qc_pass = validate_numeric_fields(extraction)
    result.evidence_ratio = calculate_evidence_ratio(extraction)
    result.overall_score = (result.coverage + result.evidence_ratio) / 2
    result.needs_coaching = result.overall_score < 0.95
    result.failed_fields = identify_failed_fields(extraction)
    return result
```

**Pros**:
- ✅ Detailed diagnostics
- ✅ Enables targeted coaching
- ✅ Matches Gracian's orchestrator pattern

**Cons**:
- ⚠️ More complex implementation

**DECISION**: **Option 5B (Tiered Quality System)** - Enables coaching in Pass 3

---

### Decision #6: Caching Strategy for Extraction Results

**Question**: Should we cache extraction results like we cache structure/routing?

#### Evidence from Phase 1
From `optimal_brf_pipeline.py:91-178`:
- Cache Layer 1: PDF structure (SHA256 hash)
- Cache Layer 2: Note routing decisions
- SQLite-based with 7-day TTL

#### Option 6A: Cache All Extractions
```python
class CacheManager:
    def get_extraction(self, pdf_hash: str, agent_id: str) -> Optional[Dict]:
        # Return cached extraction if exists
        pass

    def put_extraction(self, pdf_hash: str, agent_id: str, result: Dict):
        # Cache extraction result
        pass
```

**Pros**:
- ✅ Avoid re-running expensive LLM calls
- ✅ Useful for development/testing

**Cons**:
- ⚠️ Stale results if prompts/models change
- ⚠️ Large cache size (JSON blobs)

#### Option 6B: No Extraction Caching (Phase 2) ✅ **RECOMMENDED**
```python
# Only cache structure + routing (Phase 1)
# Re-run extractions each time
```

**Pros**:
- ✅ Always fresh results
- ✅ Simpler implementation
- ✅ Better for iterative prompt tuning

**Cons**:
- ⚠️ No cost savings on re-runs

**DECISION**: **Option 6B (No Extraction Caching)** for Phase 2 - Add in Phase 3 if needed

**Rationale**: Extraction is the valuable output, not an intermediate step. Cache hit rate would be low (5% per ULTRATHINKING analysis).

---

## 📋 Phase 2 Implementation Plan

### Priority 1: Implement Pass 1 Extraction

**Agents** (8 agents, parallel):
```python
PASS1_AGENTS = [
    'governance_agent',      # Chairman, board, auditor
    'property_agent',        # Address, designation, area
    'operations_agent',      # Suppliers, contracts, maintenance
    # ... other main section agents
]
```

**Method**:
```python
def extract_pass1(self, routing: SectionRouting) -> Dict[str, Dict]:
    """Extract high-level fields with Grok/GPT-4o in parallel"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for agent_id in PASS1_AGENTS:
            pages = routing.main_sections.get(agent_id, [])
            futures[agent_id] = executor.submit(
                self._extract_agent, agent_id, pages
            )

        results = {}
        for agent_id, future in futures.items():
            try:
                results[agent_id] = future.result(timeout=60)
            except Exception as e:
                results[agent_id] = {"error": str(e)}

        return results
```

**Target**: 15s parallel execution, $0.05/doc

---

### Priority 2: Implement Pass 2 Extraction

**Agents** (8 agents, sequential):
```python
PASS2_AGENTS = [
    'financial_agent',       # Income statement, balance sheet
    'notes_accounting_agent',
    'notes_loans_agent',
    'notes_buildings_agent',
    'notes_receivables_agent',
    'notes_reserves_agent',
    'notes_tax_agent',
    'notes_other_agent',
]
```

**Method**:
```python
def extract_pass2(self, routing: SectionRouting, pass1_results: Dict) -> Dict[str, Dict]:
    """Extract financial + notes with GPT-4o sequentially"""
    results = {}

    # Financial agent first
    financial_pages = routing.main_sections.get('financial_agent', [])
    results['financial_agent'] = self._extract_agent(
        'financial_agent', financial_pages
    )

    # Note agents with context
    for agent_id, note_headings in routing.note_sections.items():
        context = self._build_hierarchical_context(pass1_results, results)
        results[agent_id] = self._extract_agent(
            agent_id, note_headings, context=context
        )

    return results
```

**Target**: 40s sequential execution, $0.15/doc

---

### Priority 3: Implement Pass 3 Validation

**Validation Components**:
```python
def validate_extraction(self, pass1: Dict, pass2: Dict) -> QualityResult:
    """Run all quality gates"""

    # 1. Coverage check
    coverage = self._calculate_coverage(pass1, pass2)

    # 2. Numeric QC (reuse Gracian qc.py)
    from gracian_pipeline.core.qc import numeric_qc
    numeric_ok = numeric_qc('financial_agent', pass2['financial_agent'])

    # 3. Evidence tracking
    evidence_ratio = self._calculate_evidence_ratio(pass1, pass2)

    # 4. Calculate metrics (debt/sqm, solidarity %, fee/sqm)
    metrics = self._calculate_metrics(pass1, pass2)

    result = QualityResult(
        coverage=coverage,
        numeric_qc_pass=len(numeric_ok.get('errors', [])) == 0,
        evidence_ratio=evidence_ratio,
        calculated_metrics=metrics,
        overall_score=(coverage + evidence_ratio) / 2,
        needs_coaching=overall_score < 0.95
    )

    return result
```

**Target**: 5s validation, $0/doc (local computation)

---

### Priority 4: Integration into OptimalBRFPipeline

**Update** `optimal_brf_pipeline.py:479-577`:
```python
def extract_document(self, pdf_path: str) -> ExtractionResult:
    # STAGE 1-3: Existing (complete) ✅
    topology = self.analyze_topology(pdf_path)
    structure = self.detect_structure(pdf_path, topology)
    routing = self.route_sections(structure)

    # STAGE 4: Hierarchical extraction (NEW) ⏳
    pass1_results = self.extract_pass1(routing)
    pass2_results = self.extract_pass2(routing, pass1_results)
    pass3_results = None  # Optional coaching

    # STAGE 5: Quality validation (NEW) ⏳
    quality = self.validate_extraction(pass1_results, pass2_results)

    if quality.needs_coaching:
        pass3_results = self.coach_failed_fields(
            pass1_results, pass2_results, quality.failed_fields
        )

    # Combine all results
    result = ExtractionResult(
        pdf_path=pdf_path,
        topology=topology,
        structure=structure,
        routing=routing,
        pass1=pass1_results,
        pass2=pass2_results,
        pass3=pass3_results,
        quality=quality,
        timestamp=datetime.now(),
        total_time=time.time() - start_time
    )

    return result
```

---

## 🎯 Success Criteria (Phase 2 Complete)

### Functionality
- ✅ All 3 passes implemented
- ✅ Pass 1: 8 agents parallel extraction
- ✅ Pass 2: 8 agents sequential extraction
- ✅ Pass 3: Quality validation + optional coaching

### Quality
- ✅ Coverage ≥95% on test document
- ✅ Numeric QC passing
- ✅ Evidence ratio ≥95%

### Performance
- ✅ Total time: <60s/doc
- ✅ Total cost: <$0.25/doc
- ✅ Working on test PDFs (Hjorthagen, SRS)

### Deliverables
- ✅ Updated `optimal_brf_pipeline.py` (Stages 4-5)
- ✅ Test results on brf_268882.pdf
- ✅ `PHASE2_IMPLEMENTATION_COMPLETE.md` documentation

---

## 📈 Expected Timeline

**Phase 2A** (Implement Passes 1-3): ~3 hours
- Pass 1 extraction: 1 hour
- Pass 2 extraction: 1 hour
- Pass 3 validation: 1 hour

**Phase 2B** (Testing & Debugging): ~2 hours
- Test on brf_268882.pdf: 30 minutes
- Debug failures: 1 hour
- Validate against ground truth: 30 minutes

**Total**: ~5 hours for complete Phase 2

---

**Status**: ✅ **ULTRATHINKING COMPLETE**
**Next**: Implement Stages 4-5 based on this design
**Target**: Phase 2 complete in current session
