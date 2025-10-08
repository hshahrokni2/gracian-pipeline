# Scalable Note Semantic Router - Architecture ULTRATHINKING

**Date**: 2025-10-07
**Scope**: Production-grade router for 12,101+ documents
**Focus**: Scalability, maintainability, performance

---

## 🎯 Scalability Requirements

### Volume Requirements
- **12,101 documents** (initial corpus)
- **26,342 årsredovisning** (full corpus potential)
- **~50 note headings per document** (from Exp 3A)
- **Total classifications**: 605,050 - 1,317,100

### Performance Requirements
- **Throughput**: ≥100 docs/hour (single worker)
- **Latency**: <5s per document
- **Cost**: <$0.01 per document
- **Accuracy**: ≥90% correct routing

### Maintenance Requirements
- **Easy keyword updates** (new synonyms, OCR error patterns)
- **Easy agent type additions** (new specialized agents)
- **Versionable configuration** (track changes over time)
- **Testable** (unit tests for each routing decision)

---

## 🧠 ULTRATHINKING: Design Decisions

### Decision #1: Keyword Storage

**Option A: Hardcoded in Python** ❌
```python
KEYWORDS = {
    "notes_loans_agent": ["lån", "fastighetslån", ...]
}
```
**Pros**: Simple, fast
**Cons**: Requires code change to update, not versionable independently

**Option B: JSON/YAML Config File** ✅ **RECOMMENDED**
```yaml
# config/note_keywords.yaml
notes_loans_agent:
  primary:
    - lån
    - fastighetslån
    - skulder
  secondary:
    - långfristiga skulder
    - amortering
```
**Pros**: Versionable, easy to update, no code changes
**Cons**: Slightly slower to load (negligible)

**Verdict**: ✅ Use YAML config for keywords

---

### Decision #2: Caching Strategy

**Option A: No Caching** ❌
- Re-classify same heading every time
- 1.3M classifications for full corpus

**Option B: In-Memory Cache** ⚠️
```python
cache = {}  # heading → agent_id
```
**Pros**: Fast lookup
**Cons**: Lost on restart, memory usage unbounded

**Option C: Persistent Cache (SQLite)** ✅ **RECOMMENDED**
```sql
CREATE TABLE heading_cache (
    heading TEXT PRIMARY KEY,
    agent_id TEXT,
    method TEXT,  -- 'keyword' or 'llm'
    confidence REAL,
    timestamp INTEGER
);
```
**Pros**: Survives restarts, queryable, bounded memory
**Cons**: Slight I/O overhead (negligible with SQLite)

**Verdict**: ✅ Use SQLite cache with in-memory fallback

---

### Decision #3: LLM Batching Strategy

**Option A: One Heading at a Time** ❌
```python
for heading in headings:
    agent_id = grok_classify(heading)  # 13 LLM calls per doc
```
**Cost**: 13 × $0.002 = $0.026/doc
**Time**: 13 × 2s = 26s/doc

**Option B: Batch All Headings** ✅ **RECOMMENDED**
```python
# Single LLM call for all headings
agent_map = grok_classify_batch(headings)  # 1 LLM call per doc
```
**Cost**: 1 × $0.02 = $0.02/doc
**Time**: 1 × 10s = 10s/doc

**Verdict**: ✅ Always batch LLM calls

---

### Decision #4: Keyword Matching Algorithm

**Option A: Simple String Match** ⚠️
```python
if "lån" in heading.lower():
    return "notes_loans_agent"
```
**Pros**: Fast
**Cons**: Fails on word boundaries ("belåning" contains "lån" but ≠ loans)

**Option B: Word Boundary Regex** ✅ **RECOMMENDED**
```python
import re
pattern = r'\blån\b'  # Word boundary
if re.search(pattern, heading.lower()):
    return "notes_loans_agent"
```
**Pros**: Accurate word matching
**Cons**: Slightly slower (negligible)

**Option C: Fuzzy Matching (Levenshtein)** 💰
```python
from rapidfuzz import fuzz
if fuzz.ratio("lån", word) > 0.8:
    return "notes_loans_agent"
```
**Pros**: Handles OCR errors ("1ån" → "lån")
**Cons**: Much slower, may need LLM anyway for complex errors

**Verdict**: ✅ Use regex word boundaries, fallback to LLM for OCR errors

---

### Decision #5: Configuration Versioning

**Problem**: Keyword mappings will evolve over time
- New synonyms discovered
- OCR error patterns learned
- New agent types added

**Option A: Git-Only Versioning** ⚠️
```bash
git log config/note_keywords.yaml
```
**Pros**: Simple
**Cons**: No runtime tracking of which config version was used

**Option B: Embedded Version in Config** ✅ **RECOMMENDED**
```yaml
# config/note_keywords.yaml
version: "1.2.0"
updated: "2025-10-07"
changelog:
  - "1.2.0: Added 'fastighetslån' synonym for loans"
  - "1.1.0: Added notes_tax_agent keywords"

agents:
  notes_loans_agent:
    primary: [...]
```
**Pros**: Self-documenting, trackable in DB
**Cons**: Manual version updates (but good practice)

**Verdict**: ✅ Use semantic versioning in config file

---

### Decision #6: Error Handling & Fallbacks

**Failure Modes**:
1. **Keyword config missing** → Crash or use hardcoded defaults?
2. **LLM API failure** → Retry or fallback to "other" agent?
3. **Unknown heading** → Route to generic agent or skip?

**Recommended Strategy**:
```python
class NoteSemanticRouter:
    def __init__(self, config_path: str):
        try:
            self.config = load_yaml(config_path)
        except FileNotFoundError:
            logger.warning("Config not found, using embedded defaults")
            self.config = EMBEDDED_DEFAULTS

    def classify_heading(self, heading: str) -> str:
        try:
            # Try cache
            if cached := self.cache.get(heading):
                return cached

            # Try keywords
            if agent_id := self._match_keywords(heading):
                return agent_id

            # Try LLM with retries
            for attempt in range(3):
                try:
                    agent_id = self._llm_classify(heading)
                    return agent_id
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"LLM failed: {e}")
                        return "notes_other_agent"  # Safe fallback
                    time.sleep(2 ** attempt)

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "notes_other_agent"
```

**Verdict**: ✅ Multi-layer fallback with logging

---

### Decision #7: Metrics & Observability

**What to Track**:
- Classification method (keyword vs LLM)
- Confidence scores
- LLM usage rate (should be ~20%)
- Cache hit rate
- Unknown headings (for keyword expansion)

**Implementation**:
```python
class ClassificationMetrics:
    def __init__(self):
        self.total_classifications = 0
        self.keyword_matches = 0
        self.llm_calls = 0
        self.cache_hits = 0
        self.unknown_headings = []

    def record(self, heading: str, method: str, agent_id: str):
        self.total_classifications += 1
        if method == "cache":
            self.cache_hits += 1
        elif method == "keyword":
            self.keyword_matches += 1
        elif method == "llm":
            self.llm_calls += 1

        if agent_id == "notes_other_agent":
            self.unknown_headings.append(heading)

    def summary(self) -> dict:
        return {
            "total": self.total_classifications,
            "cache_rate": self.cache_hits / self.total_classifications,
            "keyword_rate": self.keyword_matches / self.total_classifications,
            "llm_rate": self.llm_calls / self.total_classifications,
            "unknown_count": len(self.unknown_headings)
        }
```

**Verdict**: ✅ Track metrics for optimization

---

## 🏗️ Final Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────┐
│         NoteSemanticRouter (Main Class)         │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Config Loader│  │ Cache Manager│            │
│  │ (YAML)       │  │ (SQLite)     │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Classification Pipeline                 │  │
│  ├──────────────────────────────────────────┤  │
│  │  1. Cache Lookup → if hit, return       │  │
│  │  2. Keyword Match → if match, cache     │  │
│  │  3. LLM Classify → cache result         │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Metrics      │  │ Batch Manager│            │
│  │ Tracker      │  │ (LLM)        │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘

         ↓ Input                    ↓ Output
   ["Lån", "Byggnader"]    {"notes_loans_agent": ["Lån"],
                            "notes_maintenance_agent": ["Byggnader"]}
```

### File Structure

```
experiments/docling_advanced/
├── code/
│   ├── note_semantic_router.py      # Main router class
│   ├── test_note_semantic_routing.py # Validation tests
│   └── utils/
│       ├── cache_manager.py          # SQLite cache
│       ├── config_loader.py          # YAML loading
│       └── metrics_tracker.py        # Observability
├── config/
│   ├── note_keywords.yaml            # Keyword definitions (versioned)
│   └── agent_types.yaml              # Agent metadata
├── results/
│   └── routing_cache.db              # SQLite persistent cache
└── logs/
    └── classification_metrics.json   # Performance logs
```

### Config File Schema

```yaml
# config/note_keywords.yaml
version: "1.0.0"
updated: "2025-10-07"
description: "Swedish BRF note heading to agent mapping"

# Agent type definitions
agents:
  notes_accounting_agent:
    display_name: "Notes: Accounting Principles"
    description: "Redovisnings- och värderingsprinciper"
    keywords:
      primary:
        - redovisningsprinciper
        - värderingsprinciper
        - accounting principles
      secondary:
        - intäktsredovisning
        - kostnadsredovisning
        - periodisering
      ocr_errors:
        # Common OCR misreadings
        - redov1sn1ngsprinciper  # 'i' → '1'
    examples:
      - "NOT 1 REDOVISNINGS- OCH VÄRDERINGSPRINCIPER"
      - "Accounting principles and valuation"

  notes_loans_agent:
    display_name: "Notes: Loans & Debt"
    description: "Fastighetslån, skulder, krediter"
    keywords:
      primary:
        - lån
        - fastighetslån
        - skulder
        - krediter
      secondary:
        - långfristiga skulder
        - amortering
        - ränta
      ocr_errors:
        - ångar  # Common OCR error for "lån"
        - 1ån    # OCR confusion
    examples:
      - "Fastighetslån"
      - "Långfristiga skulder"

  # ... (5 more agent types)

# Fallback configuration
fallback:
  default_agent: "notes_other_agent"
  confidence_threshold: 0.7  # For keyword matching
  llm_retry_attempts: 3
  llm_retry_delay: 2  # seconds
```

---

## 🔧 Implementation Checklist

### Phase 1: Core Router (2 hours)
- [x] YAML config schema design
- [ ] Config loader with validation
- [ ] Keyword matcher with regex
- [ ] LLM classifier (Grok)
- [ ] Batch routing method
- [ ] Error handling & fallbacks

### Phase 2: Caching Layer (1 hour)
- [ ] SQLite cache schema
- [ ] Cache manager class
- [ ] In-memory fallback
- [ ] Cache warming (pre-populate common headings)

### Phase 3: Observability (1 hour)
- [ ] Metrics tracker
- [ ] Classification logging
- [ ] Unknown heading collector
- [ ] Performance profiler

### Phase 4: Testing (1 hour)
- [ ] Unit tests (keyword matching)
- [ ] Integration tests (full pipeline)
- [ ] Validation on Exp 3A data
- [ ] Performance benchmarks

---

## 📊 Expected Performance (Scalable Architecture)

### Single Document (First Run)
- Cache: 0 hits (cold start)
- Keywords: ~10 headings matched (80%)
- LLM: ~3 headings batched (20%)
- Time: ~12s (10s LLM + 2s keywords/cache)
- Cost: $0.02 (1 batched LLM call)

### Single Document (Warm Cache)
- Cache: ~10 hits (80%)
- Keywords: ~2 headings matched (15%)
- LLM: ~1 heading (5%)
- Time: ~3s (mostly cache lookups)
- Cost: $0.003 (small LLM batch)

### 12,101 Documents (Full Corpus)
**First 1,000 docs** (cache building):
- Time: 1,000 × 12s = 3.3 hours
- Cost: 1,000 × $0.02 = $20

**Next 11,101 docs** (warm cache):
- Cache hit rate: ~90% (same headings across docs)
- Time: 11,101 × 3s = 9.3 hours
- Cost: 11,101 × $0.003 = $33

**Total**:
- Time: **12.6 hours** (single worker)
- Cost: **$53**
- Parallelized (10 workers): **1.3 hours**

**Compare to Naive** (no caching):
- Time: 12,101 × 12s = 40 hours
- Cost: 12,101 × $0.02 = $242

**Savings**: 68% time, 78% cost with caching

---

## ✅ Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Keyword Storage** | YAML config | Versionable, maintainable |
| **Caching** | SQLite + in-memory | Persistent, scalable |
| **LLM Batching** | Batch all headings | 13x cost reduction |
| **Keyword Matching** | Regex word boundaries | Accurate, fast |
| **Versioning** | Semantic in config | Trackable, auditable |
| **Error Handling** | Multi-layer fallback | Robust, logged |
| **Metrics** | Comprehensive tracking | Optimization-ready |

---

## 🚀 Next Action

Implement `NoteSemanticRouter` class with:
1. ✅ YAML config loading
2. ✅ SQLite caching
3. ✅ Keyword + LLM hybrid classification
4. ✅ Batch processing
5. ✅ Metrics tracking
6. ✅ Comprehensive error handling

**Estimated Time**: 5 hours (including testing)
**Expected Outcome**: Production-ready router handling 12,101+ documents

---

**Last Updated**: 2025-10-07
**Architecture Status**: Ready for implementation
**Scalability Target**: 26,342 documents (full årsredovisning corpus)
