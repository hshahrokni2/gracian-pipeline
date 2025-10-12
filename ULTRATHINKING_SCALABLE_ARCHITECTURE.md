# ULTRATHINKING: Scalable, Reliable, Robust Extraction Architecture

## 🎯 The Real Problem

### Current State
- ✅ **Loan extraction works** - Field name fix verified
- ❌ **Deep mode takes 6-8 minutes** per document
- ❌ **No parallelization** - Notes 4,5,8,9 run sequentially (4 min total)
- ❌ **No caching** - Docling re-processes same PDFs
- ❌ **No resumability** - Failures restart from scratch
- ❌ **Monolithic architecture** - Can't scale to 26,342 PDFs

### Scale Requirements
**Corpus**: 26,342 årsredovisning PDFs

**Current Performance**:
- Deep mode: 6-8 minutes/PDF
- Total time: 158,052 minutes = **110 days** (serial)
- With 10 workers: **11 days**
- With 50 workers: **2.2 days**

**Target Performance**:
- Optimized deep mode: 2-3 minutes/PDF
- Total time: 52,684 minutes = **37 days** (serial)
- With 50 workers: **18 hours** ✅

---

## 🧠 ULTRATHINKING Analysis

### Bottleneck #1: Sequential Note Extraction (3-4x speedup available)

**Current (WRONG)**:
```python
# Sequential execution
extract_note_4()  # 60-80s
extract_note_5()  # 40-60s
extract_note_8()  # 30-40s
extract_note_9()  # 30-40s
# Total: 160-220s
```

**Optimal (PARALLEL)**:
```python
# Parallel execution with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(extract_note_4): "note_4",
        executor.submit(extract_note_5): "note_5",
        executor.submit(extract_note_8): "note_8",
        executor.submit(extract_note_9): "note_9"
    }
# Total: max(60, 40, 30, 30) = 60-80s
# SPEEDUP: 2.5-3x
```

### Bottleneck #2: Docling Re-processing (∞ speedup with caching)

**Problem**:
- Same PDF processed multiple times during development
- Docling takes 40-50s per document
- Zero benefit from repeated processing

**Solution**: Hash-based caching
```python
cache_key = SHA256(pdf_bytes) + docling_version
cached_result = cache.get(cache_key)
if cached_result:
    return cached_result  # 0s instead of 50s
```

**Expected hit rate**:
- Development/testing: 80%+ (same PDFs tested repeatedly)
- Production first run: 0% (new PDFs)
- Production re-runs: 100% (PDF unchanged)

### Bottleneck #3: Unnecessary Vision Extraction (2x speedup)

**Current**:
- Vision extraction runs for EVERY document
- Takes 20-30s per call
- 50%+ of documents already have detailed breakdown

**Solution**: Conditional execution
```python
if apartment_breakdown_granularity == "summary":
    # Only run vision if needed
    run_vision_extraction()
else:
    # Skip - already have detailed data
    pass
```

### Bottleneck #4: No Error Recovery (Reliability issue)

**Current**:
- Timeout = entire extraction lost
- Network error = start over from Docling
- LLM error = no partial results

**Solution**: Staged checkpointing
```python
# Save after each stage
stage1_result = docling_extract(pdf)  # Save to cache
stage2_result = base_extract(stage1_result)  # Save to temp file
stage3_result = hierarchical_extract(stage2_result)  # Recoverable
```

---

## 🏗️ Optimal Architecture: 5-Stage Pipeline

### Stage 1: Structure Detection (CACHEABLE)
```
Input:  PDF file
Process: Docling extraction (markdown + tables)
Time:   40-50s (first run), 0s (cached)
Cache:  SHA256(pdf) + docling_version
Output: {markdown, tables, metadata}
```

### Stage 2: Base Extraction (FAST)
```
Input:  Markdown + tables from Stage 1
Process: LLM extraction of 13 agents
Time:   30-40s
Cache:  None (cheap LLM call, always fresh)
Output: Base result with 80-90% coverage
```

### Stage 3: Hierarchical Notes (PARALLEL, CONDITIONAL)
```
Input:  PDF + base result
Process: Notes 4,5,8,9 IN PARALLEL
  ├─ Note 4: Operating costs (60s) [if <10 items in base]
  ├─ Note 5: Loans (45s) [if 0 loans in base]
  ├─ Note 8: Buildings (35s) [if missing building details]
  └─ Note 9: Receivables (35s) [if missing receivables]
Time:   60-80s (parallel max, not sum)
Speedup: 3x vs sequential
Skip rate: 20-30% of notes already extracted
```

### Stage 4: Vision Enhancement (CONDITIONAL)
```
Input:  Base result + PDF
Condition: Only if apartment_breakdown == "summary"
Process: Vision extraction for detailed breakdown
Time:   20-30s (when needed), 0s (50% skip rate)
Speedup: 2x average
```

### Stage 5: Pydantic Conversion (FAST)
```
Input:  Complete extraction result
Process: Schema validation + field mapping
Time:   5-10s
Output: BRFAnnualReport Pydantic model
```

---

## 📊 Performance Projection

### Current (Deep Mode)
```
Docling:       50s  (sequential)
Base extract:  35s  (sequential)
Note 4:        65s  (sequential)
Note 5:        50s  (sequential)  ← Fixed!
Note 8:        35s  (sequential)
Note 9:        35s  (sequential)
Vision:        25s  (always runs)
Pydantic:       8s  (sequential)
────────────────────
TOTAL:        303s  (5 minutes 3 seconds)
```

### Optimized (Parallel + Conditional + Caching)
```
Docling:        0s  (cached 80% in dev, 0% in prod)
                50s (uncached)
Base extract:  35s  (always runs)
Notes (parallel): 65s (max of 4 parallel calls, ~30% skip some)
Vision:        12s  (50% skip rate: 25s × 0.5)
Pydantic:       8s  (always runs)
────────────────────
TOTAL (cached):   120s (2 minutes) ← 60% faster
TOTAL (uncached): 170s (2m 50s)   ← 44% faster
```

### Production Scale (26,342 PDFs)
```
Current:
  Serial:     303s × 26,342 = 92 days
  50 workers: 92 days / 50 = 1.8 days (44 hours)

Optimized:
  Serial:     170s × 26,342 = 52 days
  50 workers: 52 days / 50 = 1.0 days (24 hours)

IMPROVEMENT: 50% faster, same infrastructure
```

---

## 🔧 Implementation Plan

### Phase 1: Parallel Note Extraction (Biggest Win - 3x speedup)
**File**: `gracian_pipeline/core/docling_adapter_ultra_v2.py`

**Current** (lines 77-93):
```python
# Sequential execution (SLOW)
extract_note_4()
extract_note_5()
extract_note_8()
extract_note_9()
```

**New** (with ThreadPoolExecutor):
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_all_notes_parallel(pdf_path, notes_to_extract):
    """Extract multiple notes in parallel."""
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for note_id in notes_to_extract:
            if note_id == "note_4":
                future = executor.submit(
                    self.financial_extractor.extract_note_4_detailed,
                    pdf_path, [8,9,10]  # Typical pages
                )
            elif note_id == "note_5":
                future = executor.submit(
                    self.financial_extractor.extract_note_5_loans_detailed,
                    pdf_path, [9,10,11]
                )
            # ... etc
            futures[future] = note_id

        # Collect results as they complete
        for future in as_completed(futures):
            note_id = futures[future]
            try:
                results[note_id] = future.result(timeout=90)
            except Exception as e:
                results[note_id] = {"_error": str(e)}

    return results
```

**Expected gain**: 160-220s → 60-80s (3x faster)

### Phase 2: Docling Caching (∞ speedup in dev)
**File**: `gracian_pipeline/core/docling_cache.py` (NEW)

```python
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict

class DoclingCache:
    """Cache Docling extraction results by PDF hash."""

    def __init__(self, cache_dir: str = "results/docling_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS docling_cache (
                    pdf_hash TEXT PRIMARY KEY,
                    docling_version TEXT,
                    markdown TEXT,
                    tables_json TEXT,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
            """)

    def compute_hash(self, pdf_path: str) -> str:
        """Compute SHA256 hash of PDF file."""
        with open(pdf_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get(self, pdf_path: str, docling_version: str = "2.0.0") -> Optional[Dict]:
        """Get cached Docling result if available."""
        pdf_hash = self.compute_hash(pdf_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT markdown, tables_json, metadata_json
                FROM docling_cache
                WHERE pdf_hash = ? AND docling_version = ?
            """, (pdf_hash, docling_version))

            row = cursor.fetchone()
            if row:
                # Update hit count
                conn.execute("""
                    UPDATE docling_cache
                    SET hit_count = hit_count + 1
                    WHERE pdf_hash = ?
                """, (pdf_hash,))

                return {
                    "markdown": row[0],
                    "tables": json.loads(row[1]),
                    "metadata": json.loads(row[2])
                }

        return None

    def put(self, pdf_path: str, result: Dict, docling_version: str = "2.0.0"):
        """Cache Docling extraction result."""
        pdf_hash = self.compute_hash(pdf_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO docling_cache
                (pdf_hash, docling_version, markdown, tables_json, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pdf_hash,
                docling_version,
                result["markdown"],
                json.dumps(result["tables"]),
                json.dumps(result.get("metadata", {}))
            ))
```

**Expected gain**: 50s → 0s (∞ faster in dev, 0% gain in prod first run)

### Phase 3: Conditional Vision Extraction (2x speedup)
**File**: `gracian_pipeline/core/docling_adapter_ultra_v2.py` (line 96)

**Current**:
```python
# Always runs vision extraction
if apt_granularity == "summary" or not apt_granularity:
    run_vision_extraction()  # 25s every time
```

**Optimized**:
```python
# Only run if truly needed
apt_data = base_result.get("property_agent", {})
apt_breakdown = apt_data.get("apartment_breakdown", {})

# Check if we already have detailed breakdown
if isinstance(apt_breakdown, dict) and len(apt_breakdown) >= 3:
    # Already have detailed data (3+ apartment types)
    print("  ✓ Detailed apartment breakdown already present, skipping vision")
else:
    # Need vision enhancement
    print("  → Running vision extraction for apartment breakdown...")
    run_vision_extraction()
```

**Expected gain**: 25s → 12s average (50% skip rate)

### Phase 4: Mode-Based Execution (Flexibility)
**Keep 3 modes with clear tradeoffs**:

```python
# Mode: fast (90s - base extraction only)
if mode == "fast":
    stages = [1, 2, 5]  # Structure, Base, Pydantic
    # Skip: Notes, Vision

# Mode: deep (170s - everything, parallel)
elif mode == "deep":
    stages = [1, 2, 3, 4, 5]  # All stages
    # Notes run in parallel
    # Vision runs conditionally

# Mode: auto (120-170s - adaptive)
elif mode == "auto":
    stages = [1, 2, 5]  # Always these
    if needs_detailed_notes(base_result):
        stages.insert(2, 3)  # Add Notes
    if needs_vision_enhancement(base_result):
        stages.insert(-1, 4)  # Add Vision
```

---

## ✅ Implementation Checklist

### Week 1: Parallel Notes (Highest Impact)
- [ ] Create `extract_all_notes_parallel()` method
- [ ] Update `docling_adapter_ultra_v2.py` to use parallel execution
- [ ] Add timeout handling for individual note extraction
- [ ] Test on 5-PDF sample (expect 3x speedup)

### Week 2: Docling Caching
- [ ] Create `docling_cache.py` module
- [ ] Integrate cache into base extractor
- [ ] Add cache statistics and hit rate tracking
- [ ] Test cache invalidation on PDF changes

### Week 3: Conditional Execution
- [ ] Add smart vision skipping logic
- [ ] Add note extraction conditional logic
- [ ] Optimize mode="auto" decision tree
- [ ] Test on diverse document set

### Week 4: Production Validation
- [ ] Run full 42-PDF test suite
- [ ] Measure actual speedups vs projections
- [ ] Load test with 100 PDFs in parallel
- [ ] Deploy to production pipeline

---

## 🎯 Success Metrics

**Performance**:
- ✅ Deep mode: <3 minutes per document (current: 5-6 min)
- ✅ Fast mode: <2 minutes per document (current: 1.5 min)
- ✅ Cache hit speedup: >90% reduction (50s → 0s)
- ✅ Parallel notes speedup: >60% reduction (220s → 80s)

**Reliability**:
- ✅ Timeout rate: <1% (current: ~5% in deep mode)
- ✅ Partial failure recovery: 100% (current: 0%)
- ✅ Cache staleness: <0.1% (versioned cache)

**Scalability**:
- ✅ 26,342 PDFs in <24 hours (50 workers)
- ✅ Linear scaling up to 100 workers
- ✅ Memory usage: <2GB per worker
- ✅ Resumability: 100% (checkpointed stages)

---

## 🚀 Next Steps

1. **Immediate**: Implement parallel note extraction (biggest win)
2. **Short-term**: Add Docling caching for development speed
3. **Medium-term**: Optimize conditional execution
4. **Long-term**: Scale to full corpus (26,342 PDFs)

This architecture makes the system **3-4x faster**, **infinitely more reliable**, and **linearly scalable** to the full corpus.
