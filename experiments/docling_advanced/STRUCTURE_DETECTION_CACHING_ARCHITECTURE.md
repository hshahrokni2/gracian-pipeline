# Structure Detection Caching Architecture - 2025-10-09

## 🎯 Problem Statement

**Current State**: Docling structure detection takes 100-120+ seconds on 28-page scanned PDFs, blocking:
- Full validation of extraction fix
- Rapid development iteration
- Production deployment on 27,000 PDFs

**Required State**: Sub-second structure retrieval from cache, enabling:
- Immediate re-testing after code changes
- Parallel processing of large PDF batches
- Production-scale efficiency

---

## 🏗️ Architectural Design

### Multi-Layer Caching Strategy

```
┌─────────────────────────────────────────────────┐
│ Layer 1: Memory Cache (Process Lifetime)       │  <-- Fastest (0.001s)
├─────────────────────────────────────────────────┤
│ Layer 2: SQLite Cache (Persistent)             │  <-- Fast (0.01s)
├─────────────────────────────────────────────────┤
│ Layer 3: JSON File Cache (Human-Readable)      │  <-- Backup (0.05s)
├─────────────────────────────────────────────────┤
│ Layer 4: Docling Detection (Fallback)          │  <-- Slow (120s)
└─────────────────────────────────────────────────┘
```

### Cache Key Design

**Primary Key**: SHA256(PDF_content + docling_version + ocr_config)

**Rationale**:
- PDF hash ensures cache invalidation if file changes
- Docling version ensures cache invalidation after upgrades
- OCR config ensures cache invalidation if settings change

**Implementation**:
```python
def compute_cache_key(pdf_path: str, docling_version: str = "2.0.0") -> str:
    """
    Compute deterministic cache key for structure detection.
    """
    # Read PDF bytes
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Combine PDF hash + version
    hash_input = pdf_bytes + docling_version.encode() + b"easyocr_swedish"
    return hashlib.sha256(hash_input).hexdigest()
```

---

## 📊 Cache Storage Schema

### SQLite Schema

```sql
CREATE TABLE structure_cache (
    cache_key TEXT PRIMARY KEY,          -- SHA256 hash
    pdf_filename TEXT NOT NULL,          -- Original filename
    pdf_size_bytes INTEGER NOT NULL,     -- File size for verification
    docling_version TEXT NOT NULL,       -- Version used for detection

    -- Structure detection results (JSON serialized)
    sections_json TEXT NOT NULL,         -- List[Dict] from DocumentMap.sections
    tables_json TEXT NOT NULL,           -- Dict[str, TableData] serialized

    -- Metadata
    detection_time_seconds REAL,         -- How long detection took
    num_sections INTEGER,                -- Quick stats
    num_tables INTEGER,

    -- Cache management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,

    -- Integrity
    checksum TEXT NOT NULL               -- SHA256 of stored JSON (corruption check)
);

CREATE INDEX idx_cache_pdf_filename ON structure_cache(pdf_filename);
CREATE INDEX idx_cache_created_at ON structure_cache(created_at);
CREATE INDEX idx_cache_accessed_at ON structure_cache(accessed_at);
```

**Design Decisions**:
1. **JSON Serialization**: Store complex Python objects as JSON for portability
2. **Checksum Field**: Detect cache corruption (rare but possible)
3. **Access Tracking**: Enable LRU eviction for cache size limits
4. **Metadata**: Enable diagnostics and performance analysis

---

## 🔄 Cache Invalidation Strategy

### When to Invalidate

1. **Automatic Invalidation** (Hash Mismatch):
   - PDF file modified
   - Docling version upgraded
   - OCR configuration changed

2. **Manual Invalidation** (API/CLI):
   ```bash
   python3 code/cache_manager.py --clear-all
   python3 code/cache_manager.py --clear-pdf test_pdfs/brf_268882.pdf
   python3 code/cache_manager.py --clear-older-than 30d
   ```

3. **Eviction Policy** (Size Limit):
   - LRU eviction when cache exceeds 1GB (configurable)
   - Keep most recently accessed entries

### Cache Warming

**Use Case**: Pre-populate cache for production batch processing

```bash
# Warm cache for all PDFs in directory
python3 code/cache_manager.py --warm data/raw_pdfs/Hjorthagen/

# Warm cache in parallel (8 workers)
python3 code/cache_manager.py --warm data/raw_pdfs/Hjorthagen/ --workers 8
```

**Expected Performance**:
- Sequential: 15 PDFs × 120s = 30 minutes
- Parallel (8 workers): 15 PDFs / 8 × 120s = 4 minutes

---

## 🛡️ Robustness Features

### 1. Cache Corruption Handling

```python
def verify_cache_integrity(cache_entry: Dict) -> bool:
    """
    Verify cache entry hasn't been corrupted.
    """
    # Recompute checksum of stored JSON
    stored_json = cache_entry['sections_json'] + cache_entry['tables_json']
    computed_checksum = hashlib.sha256(stored_json.encode()).hexdigest()

    if computed_checksum != cache_entry['checksum']:
        logger.warning(f"Cache corruption detected for {cache_entry['pdf_filename']}")
        return False

    return True
```

### 2. Fallback Gracefully

```python
def get_structure_with_fallback(pdf_path: str) -> DocumentMap:
    """
    Try cache layers in order, fall back to Docling if all fail.
    """
    # Layer 1: Memory cache
    if pdf_path in memory_cache:
        logger.info(f"[Cache] Memory hit: {pdf_path}")
        return memory_cache[pdf_path]

    # Layer 2: SQLite cache
    cache_entry = sqlite_cache.get(compute_cache_key(pdf_path))
    if cache_entry and verify_cache_integrity(cache_entry):
        logger.info(f"[Cache] SQLite hit: {pdf_path}")
        result = deserialize_cache_entry(cache_entry)
        memory_cache[pdf_path] = result  # Populate memory cache
        return result

    # Layer 3: JSON file cache (backup)
    json_path = get_cache_json_path(pdf_path)
    if json_path.exists():
        logger.info(f"[Cache] JSON file hit: {pdf_path}")
        result = load_json_cache(json_path)
        memory_cache[pdf_path] = result
        return result

    # Layer 4: Docling detection (fallback)
    logger.info(f"[Cache] MISS - Running Docling detection: {pdf_path}")
    start_time = time.time()
    result = run_docling_detection(pdf_path)
    detection_time = time.time() - start_time

    # Populate all cache layers
    save_to_all_caches(pdf_path, result, detection_time)

    return result
```

### 3. Concurrent Access Safety

**Challenge**: Multiple processes may try to cache same PDF simultaneously

**Solution**: File-based locking for cache writes

```python
import fcntl  # Unix file locking

def save_to_cache_safe(cache_key: str, data: Dict):
    """
    Thread-safe and process-safe cache write using file locks.
    """
    lock_path = cache_dir / f"{cache_key}.lock"

    with open(lock_path, 'w') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            # Check if another process already cached it while we waited
            if cache_key in sqlite_cache:
                logger.info(f"[Cache] Another process cached {cache_key}")
                return

            # Write to cache
            sqlite_cache.put(cache_key, data)
            json_cache.put(cache_key, data)

        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # Release lock
            lock_path.unlink()  # Clean up lock file
```

---

## 📈 Performance Projections

### Single Document (28-page PDF)

| Operation | Without Cache | With Cache | Speedup |
|-----------|---------------|------------|---------|
| **Structure Detection** | 120s | 0.01s | **12,000x** |
| **Full Pipeline (Fast)** | 125s | 5s | **25x** |
| **Full Pipeline (Deep)** | 180s | 60s | **3x** |

### 42-PDF Comprehensive Test Suite

| Scenario | Without Cache | With Cache | Speedup |
|----------|---------------|------------|---------|
| **Sequential** | 84 minutes | 3.5 minutes | **24x** |
| **Parallel (8 workers)** | 10.5 minutes | 0.4 minutes | **26x** |

### Production Scale (27,000 PDFs)

**Assumptions**:
- 50% machine-readable (fast detection: 15s)
- 50% scanned (slow detection: 120s)
- Average: 67.5s per PDF

**Cold Cache (First Run)**:
- Sequential: 27,000 × 67.5s = 506 hours (21 days)
- Parallel (32 workers): 506h / 32 = 15.8 hours

**Warm Cache (Re-runs)**:
- Sequential: 27,000 × 0.01s = 4.5 minutes
- Parallel (32 workers): 4.5m / 32 = 8 seconds

**Cache Storage Requirements**:
- Average cached structure: 50KB (JSON)
- Total: 27,000 × 50KB = 1.35GB

---

## 🔧 Implementation Plan

### Phase 1: Core Caching System (Week 3 Day 3)

**Files to Create**:
1. `code/cache_manager.py` (300 lines)
   - `CacheManager` class with 3-layer caching
   - Cache key computation
   - Integrity verification
   - Concurrent access safety

2. `code/cache_cli.py` (150 lines)
   - CLI for cache management
   - Cache warming functionality
   - Cache statistics and diagnostics

**Integration Points**:
1. `integrated_brf_pipeline.py` line 339-365:
   - Replace direct Docling calls with `cache_manager.get_structure()`

2. `enhanced_structure_detector.py` line 107-149:
   - Add caching layer to `extract_document_map()`

### Phase 2: Cache Warming (Week 3 Day 4)

**Parallel Cache Warming**:
```python
def warm_cache_parallel(pdf_dir: Path, workers: int = 8):
    """
    Warm cache for all PDFs in directory using multiprocessing.
    """
    pdf_paths = list(pdf_dir.glob("*.pdf"))

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(detect_and_cache, pdf): pdf
            for pdf in pdf_paths
        }

        for future in concurrent.futures.as_completed(futures):
            pdf = futures[future]
            try:
                result = future.result()
                print(f"✅ Cached: {pdf.name}")
            except Exception as e:
                print(f"❌ Failed: {pdf.name} - {e}")
```

### Phase 3: Production Optimization (Week 3 Day 5)

**Smart Cache Eviction**:
```python
def evict_least_recently_used(target_size_gb: float = 1.0):
    """
    Evict least recently used cache entries until under size limit.
    """
    current_size = get_cache_size_gb()

    if current_size <= target_size_gb:
        return

    # Get entries sorted by last access time
    entries = db.execute("""
        SELECT cache_key, pdf_filename, accessed_at
        FROM structure_cache
        ORDER BY accessed_at ASC
    """).fetchall()

    for entry in entries:
        if get_cache_size_gb() <= target_size_gb:
            break

        db.execute("DELETE FROM structure_cache WHERE cache_key = ?", (entry['cache_key'],))
        logger.info(f"[Cache] Evicted: {entry['pdf_filename']}")
```

---

## ✅ Success Criteria

1. **Performance**: Sub-second structure retrieval from cache (99th percentile < 0.1s)
2. **Reliability**: 0% cache corruption rate (verified by checksums)
3. **Scalability**: Support 27,000 PDFs without manual intervention
4. **Robustness**: Graceful degradation if cache unavailable
5. **Usability**: Clear CLI for cache management and diagnostics

---

## 🚀 Next Steps

1. **Implement CacheManager class** (this session)
2. **Integrate with existing pipeline** (this session)
3. **Test on 3-PDF sample** (validate cache hit/miss)
4. **Run 42-PDF comprehensive test** (measure actual speedup)
5. **Deploy for 27,000 PDF production** (Phase 4)
