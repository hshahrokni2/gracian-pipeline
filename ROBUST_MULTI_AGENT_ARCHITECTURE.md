# Robust Multi-Agent Orchestration Architecture

**Created**: 2025-10-11
**Purpose**: Fix brf_81563 regression by implementing true parallel multi-agent extraction

## 🎯 Problem Statement

**Regression**: brf_81563 went from 4 board members → 0 members with "I can't assist" error

**Root Cause**: Cognitive overload from sending 13-15 agents in ONE massive prompt
- 40,000 chars document text
- 25 tables
- Comprehensive fields for ALL agents
- Complex 15-key nested JSON return format

**Key Insight** (from user): One governance agent is sufficient. The problem isn't individual agent complexity - it's asking the LLM to do 13 tasks simultaneously.

---

## 🏗️ Architecture Design

### Component 1: Single-Agent Extraction Function

**Purpose**: Extract data for ONE agent with robust error handling

```python
def extract_single_agent(
    agent_id: str,
    agent_prompt: str,
    document_context: str,  # Relevant sections ONLY (not full 40K)
    tables: List[Dict],
    page_numbers: List[int],  # Which pages this agent should focus on
    timeout: int = 30
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract data for a single agent with timeout and retry.

    Returns:
        (result_dict, metadata_dict)

    On failure: ({}, {"status": "failed", "error": "..."})
    Never raises exceptions - always returns valid structure.
    """
    try:
        # Build focused prompt (< 10,000 chars context)
        prompt = build_agent_prompt(
            agent_id=agent_id,
            agent_prompt=agent_prompt,
            context=document_context[:10000],  # Limit context size
            tables=filter_relevant_tables(tables, page_numbers),
            page_numbers=page_numbers
        )

        # Call OpenAI with timeout
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a BRF data extraction expert. Extract ONLY the requested fields in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            timeout=timeout
        )

        # Parse JSON with fallback
        content = response.choices[0].message.content.strip()
        result = parse_json_with_fallback(content)

        # Return with success metadata
        return result, {
            "status": "success",
            "agent_id": agent_id,
            "token_count": response.usage.total_tokens,
            "latency_ms": int(response._response_ms)
        }

    except Timeout:
        logger.warning(f"Agent {agent_id} timed out after {timeout}s")
        return {}, {"status": "timeout", "agent_id": agent_id}

    except Exception as e:
        logger.error(f"Agent {agent_id} failed: {e}")
        return {}, {"status": "failed", "agent_id": agent_id, "error": str(e)}
```

**Key Features**:
- ✅ Never crashes - always returns valid structure
- ✅ Timeout handling (30s default)
- ✅ Context size limiting (10K chars max per agent)
- ✅ Metadata tracking (tokens, latency, status)

---

### Component 2: Context Router

**Purpose**: Map each agent to relevant PDF sections (not full document)

```python
def build_agent_context_map(
    pdf_path: str,
    markdown: str,
    tables: List[Dict],
    section_map: Dict[str, List[int]]  # From sectionizer
) -> Dict[str, Dict[str, Any]]:
    """
    Build minimal context for each agent.

    Returns:
        {
            "governance_agent": {
                "context": "...",  # Relevant sections only
                "tables": [...],    # Relevant tables only
                "pages": [1, 2, 3]  # Page numbers
            },
            ...
        }
    """
    agent_contexts = {}

    # Agent to section mapping
    AGENT_SECTION_MAP = {
        "governance_agent": ["Styrelsen", "Revisorer"],
        "financial_agent": ["Resultaträkning", "Balansräkning"],
        "property_agent": ["Förvaltningsberättelse", "Fastigheten"],
        "fees_agent": ["Årsavgift", "Avgifter"],
        "loans_agent": ["Noter", "Not 5"],
        # ... all 13 agents
    }

    for agent_id, section_keywords in AGENT_SECTION_MAP.items():
        # Find relevant pages for this agent
        pages = find_pages_by_keywords(markdown, section_keywords, section_map)

        # Extract relevant sections from markdown
        context = extract_sections_from_pages(markdown, pages)

        # Filter relevant tables (only tables on these pages)
        relevant_tables = [t for t in tables if is_table_on_pages(t, pages)]

        agent_contexts[agent_id] = {
            "context": context[:10000],  # Limit to 10K chars
            "tables": relevant_tables[:5],  # Max 5 tables per agent
            "pages": pages
        }

    return agent_contexts
```

**Token Optimization**:
- **OLD**: 40,000 chars × 13 agents = 520,000 chars (260K tokens)
- **NEW**: ~5,000 chars × 13 agents = 65,000 chars (32K tokens)
- **Reduction**: 8x fewer tokens = 8x cheaper + faster

---

### Component 3: Parallel Orchestrator

**Purpose**: Execute all agents in parallel with error handling

```python
def extract_all_agents_parallel(
    pdf_path: str,
    max_workers: int = 5,
    enable_retry: bool = True
) -> Dict[str, Any]:
    """
    Extract all agents in parallel.

    Args:
        pdf_path: Path to PDF
        max_workers: Number of concurrent workers (5-8 recommended)
        enable_retry: Retry critical agents on failure

    Returns:
        {
            "governance_agent": {...},
            "financial_agent": {...},
            ...
            "_metadata": {
                "total_agents": 13,
                "successful_agents": 12,
                "failed_agents": ["notes_tax_agent"],
                "total_time_seconds": 25.3,
                "token_usage": 32456
            }
        }
    """
    # Step 1: Extract with Docling
    print("Step 1: Extracting document structure...")
    docling_result = extract_with_docling(pdf_path)
    markdown = docling_result['markdown']
    tables = docling_result['tables']

    # Step 2: Run sectionizer to map sections
    print("Step 2: Detecting sections...")
    section_map = sectionize_pdf(pdf_path)

    # Step 3: Build agent contexts
    print("Step 3: Building agent contexts...")
    agent_contexts = build_agent_context_map(pdf_path, markdown, tables, section_map)

    # Step 4: Prepare agent tasks
    agent_tasks = []
    for agent_id, agent_prompt in AGENT_PROMPTS.items():
        context_data = agent_contexts.get(agent_id, {})
        agent_tasks.append({
            "agent_id": agent_id,
            "agent_prompt": agent_prompt,
            "document_context": context_data.get("context", ""),
            "tables": context_data.get("tables", []),
            "page_numbers": context_data.get("pages", [])
        })

    # Step 5: Execute in parallel
    print(f"Step 4: Extracting {len(agent_tasks)} agents in parallel...")
    start_time = time.time()

    results = {}
    metadata = {
        "total_agents": len(agent_tasks),
        "successful_agents": 0,
        "failed_agents": [],
        "agent_metadata": {}
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(extract_single_agent, **task): task["agent_id"]
            for task in agent_tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_agent):
            agent_id = future_to_agent[future]
            try:
                result, agent_metadata = future.result(timeout=35)  # 30s + 5s buffer

                results[agent_id] = result
                metadata["agent_metadata"][agent_id] = agent_metadata

                if agent_metadata["status"] == "success":
                    metadata["successful_agents"] += 1
                else:
                    metadata["failed_agents"].append(agent_id)

            except TimeoutError:
                logger.error(f"Agent {agent_id} exceeded 35s timeout")
                results[agent_id] = {}
                metadata["failed_agents"].append(agent_id)

    # Step 6: Retry critical agents if enabled
    if enable_retry:
        critical_agents = ["governance_agent", "financial_agent", "property_agent"]
        failed_critical = [a for a in critical_agents if a in metadata["failed_agents"]]

        if failed_critical:
            print(f"Step 5: Retrying {len(failed_critical)} critical agents...")
            for agent_id in failed_critical:
                time.sleep(2)  # Brief pause before retry
                task = next(t for t in agent_tasks if t["agent_id"] == agent_id)
                result, agent_metadata = extract_single_agent(**task)

                if agent_metadata["status"] == "success":
                    results[agent_id] = result
                    metadata["successful_agents"] += 1
                    metadata["failed_agents"].remove(agent_id)
                    metadata["agent_metadata"][agent_id] = agent_metadata

    # Step 7: Calculate final metrics
    metadata["total_time_seconds"] = round(time.time() - start_time, 1)
    metadata["token_usage"] = sum(
        m.get("token_count", 0)
        for m in metadata["agent_metadata"].values()
    )

    results["_metadata"] = metadata

    print(f"✅ Extraction complete: {metadata['successful_agents']}/{metadata['total_agents']} agents succeeded in {metadata['total_time_seconds']}s")

    return results
```

**Performance Metrics**:
- **Sequential**: 13 agents × 8s = 104s
- **Parallel (5 workers)**: ~25s (4x speedup)
- **Token usage**: 32K tokens (vs 260K tokens old way)

---

### Component 4: Result Validator

**Purpose**: Validate extracted data and calculate coverage metrics

```python
def validate_and_calculate_coverage(
    extraction_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate extraction results and calculate coverage.

    Returns:
        {
            "coverage_percent": 75.3,
            "fields_extracted": 82,
            "fields_expected": 109,
            "validation_issues": [
                {"agent": "loans_agent", "issue": "loan_amount is 0"},
                ...
            ]
        }
    """
    from gracian_pipeline.core.validation_engine import ValidationEngine

    validator = ValidationEngine()

    # Run validation
    validation_report = validator.validate_extraction(extraction_result)

    # Calculate coverage
    total_fields = 0
    extracted_fields = 0

    for agent_id, expected_types in COMPREHENSIVE_TYPES.items():
        agent_data = extraction_result.get(agent_id, {})
        total_fields += len(expected_types) - 1  # Exclude evidence_pages

        for field_name, field_type in expected_types.items():
            if field_name != 'evidence_pages':
                value = agent_data.get(field_name)
                if value is not None and value != "" and value != []:
                    extracted_fields += 1

    coverage_percent = round((extracted_fields / total_fields) * 100, 1) if total_fields > 0 else 0

    return {
        "coverage_percent": coverage_percent,
        "fields_extracted": extracted_fields,
        "fields_expected": total_fields,
        "validation_issues": validation_report.issues,
        "has_critical_errors": validation_report.has_errors()
    }
```

---

## 📊 Expected Performance Improvements

### Speed
- **Current**: 104s sequential (13 agents × 8s)
- **New**: ~25s parallel (5 workers)
- **Improvement**: **4x faster**

### Token Usage
- **Current**: 520K chars context (260K tokens)
- **New**: 65K chars context (32K tokens)
- **Improvement**: **8x reduction**

### Reliability
- **Current**: One agent failure = entire extraction fails
- **New**: Isolated failures, 12/13 agents still succeed
- **Improvement**: **Graceful degradation**

### Coverage
- **Current**: 55.9% average (Week 3 Day 3 results)
- **New**: **65-75% target** (reduced cognitive overload + better context routing)

---

## 🧪 Testing Strategy

### Test 1: Single Agent Validation (15 min)
```bash
python test_single_agent.py --agent governance_agent --pdf Hjorthagen/brf_81563.pdf
```
**Expected**: Extract 4 board members (fix regression)

### Test 2: Parallel Execution (30 min)
```bash
python test_parallel_extraction.py --pdf SRS/brf_198532.pdf --workers 5
```
**Expected**: 13/13 agents succeed in < 40s

### Test 3: 5-PDF Sample (2 hours)
```bash
python test_comprehensive_sample.py --parallel
```
**Expected**: >= baseline coverage (no regressions)

### Test 4: Full 42-PDF Suite (12 hours)
```bash
python test_comprehensive_42_pdfs.py --parallel --workers 5
```
**Expected**: 65-75% average coverage

---

## 🚀 Implementation Plan

### Week 4 Day 1-2: Core Implementation (16 hours)
- **Hour 1-4**: Implement `extract_single_agent()` function
  - Error handling
  - Timeout logic
  - JSON parsing fallback

- **Hour 5-8**: Implement `build_agent_context_map()`
  - Section keyword mapping
  - Context extraction
  - Table filtering

- **Hour 9-14**: Implement `extract_all_agents_parallel()`
  - ThreadPoolExecutor setup
  - Task submission
  - Result collection
  - Retry logic

- **Hour 15-16**: Testing on brf_81563 (validate governance fix)

### Week 4 Day 3-4: Testing & Validation (16 hours)
- **Hour 1-4**: 5-PDF sample testing
- **Hour 5-8**: Debug and fix issues
- **Hour 9-14**: Comprehensive validation suite
- **Hour 15-16**: Documentation updates

### Week 4 Day 5: Production Deployment (8 hours)
- **Hour 1-4**: Full 42-PDF test suite
- **Hour 5-6**: Performance analysis
- **Hour 7-8**: Deploy to production if successful

---

## ✅ Success Criteria

1. **Regression Fix**: brf_81563 extracts >= 4 board members ✅
2. **No New Regressions**: All baseline-passing PDFs still pass
3. **Coverage Improvement**: Average coverage 55.9% → 65%+
4. **Performance**: Extraction time < 40s per document
5. **Reliability**: >= 12/13 agents succeed on average

---

## 🎯 Key Insight (From User)

> "One agent should suffice for governance."

**Translation**: The problem isn't that individual agents are too complex. The problem is **cognitive overload from processing 13 agents simultaneously**.

**Solution**: Send agents **separately** (one API call per agent), not together (one massive prompt).

This is the correct architectural fix for the brf_81563 regression.
