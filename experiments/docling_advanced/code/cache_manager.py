#!/usr/bin/env python3
"""
Structure Detection Cache Manager

Multi-layer caching system for Docling structure detection results:
- Layer 1: Memory cache (process lifetime, sub-millisecond)
- Layer 2: SQLite cache (persistent, ~10ms)
- Layer 3: JSON file cache (backup, ~50ms)
- Layer 4: Docling detection (fallback, ~120s)

Features:
- Cache key versioning (PDF hash + Docling version)
- Integrity verification (checksums)
- Concurrent access safety (file locking)
- LRU eviction (configurable size limit)
- Cache warming (parallel processing)
"""

import os
import json
import time
import sqlite3
import hashlib
import logging
import fcntl  # Unix file locking
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from enhanced_structure_detector import EnhancedStructureDetector, DocumentMap, TableData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    cache_key: str
    pdf_filename: str
    pdf_size_bytes: int
    docling_version: str
    sections_json: str
    tables_json: str
    detection_time_seconds: float
    num_sections: int
    num_tables: int
    created_at: str
    accessed_at: str
    access_count: int
    checksum: str


class CacheManager:
    """
    Multi-layer cache manager for structure detection results.
    """

    def __init__(
        self,
        cache_dir: str = "results/cache",
        docling_version: str = "2.0.0",
        max_cache_size_gb: float = 1.0
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            docling_version: Docling version (for cache invalidation)
            max_cache_size_gb: Maximum cache size in GB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.docling_version = docling_version
        self.max_cache_size_gb = max_cache_size_gb

        # Layer 1: Memory cache (process lifetime)
        self.memory_cache: Dict[str, DocumentMap] = {}

        # Layer 2: SQLite cache (persistent)
        self.db_path = self.cache_dir / "structure_cache.db"
        self._init_db()

        # Layer 3: JSON cache directory
        self.json_cache_dir = self.cache_dir / "json"
        self.json_cache_dir.mkdir(exist_ok=True)

        # Structure detector (Layer 4: fallback)
        self.detector = EnhancedStructureDetector()

        logger.info(f"[Cache] Initialized at {self.cache_dir}")

    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS structure_cache (
                    cache_key TEXT PRIMARY KEY,
                    pdf_filename TEXT NOT NULL,
                    pdf_size_bytes INTEGER NOT NULL,
                    docling_version TEXT NOT NULL,
                    sections_json TEXT NOT NULL,
                    tables_json TEXT NOT NULL,
                    detection_time_seconds REAL,
                    num_sections INTEGER,
                    num_tables INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    checksum TEXT NOT NULL
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_pdf_filename ON structure_cache(pdf_filename)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_created_at ON structure_cache(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON structure_cache(accessed_at)")

            # Layer 3 LLM Classification Cache (v3.0)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_classification_cache (
                    heading_normalized TEXT PRIMARY KEY,
                    agents_json TEXT NOT NULL,
                    primary_agent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    model TEXT NOT NULL,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_cache_accessed_at ON llm_classification_cache(accessed_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_cache_primary_agent ON llm_classification_cache(primary_agent)")

            conn.commit()

    def compute_cache_key(self, pdf_path: str) -> str:
        """
        Compute deterministic cache key for PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            SHA256 hash combining PDF content + Docling version
        """
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Combine PDF hash + version + OCR config
        hash_input = pdf_bytes + self.docling_version.encode() + b"easyocr_swedish"
        return hashlib.sha256(hash_input).hexdigest()

    def _compute_checksum(self, sections_json: str, tables_json: str) -> str:
        """Compute checksum for integrity verification."""
        combined = sections_json + tables_json
        return hashlib.sha256(combined.encode()).hexdigest()

    def _verify_cache_integrity(self, entry: Dict) -> bool:
        """
        Verify cache entry hasn't been corrupted.

        Args:
            entry: Cache entry from database

        Returns:
            True if integrity check passes
        """
        computed_checksum = self._compute_checksum(
            entry['sections_json'],
            entry['tables_json']
        )

        if computed_checksum != entry['checksum']:
            logger.warning(f"[Cache] Corruption detected: {entry['pdf_filename']}")
            return False

        return True

    def _serialize_document_map(self, document_map: DocumentMap) -> Tuple[str, str]:
        """
        Serialize DocumentMap to JSON strings.

        Returns:
            (sections_json, tables_json)
        """
        # Serialize sections (list of dicts)
        sections_json = json.dumps(document_map.sections)

        # Serialize tables (dict of TableData objects)
        tables_dict = {}
        for table_name, table_data in document_map.tables.items():
            tables_dict[table_name] = {
                'table_type': table_data.table_type,
                'page': table_data.page,
                'rows': table_data.rows,
                'headers': table_data.headers,
                'related_note': table_data.related_note,
                'confidence': table_data.confidence
            }
        tables_json = json.dumps(tables_dict)

        return sections_json, tables_json

    def _deserialize_document_map(
        self,
        pdf_path: str,
        sections_json: str,
        tables_json: str,
        extraction_time: float,
        created_at: datetime
    ) -> DocumentMap:
        """
        Deserialize JSON strings to DocumentMap.

        Args:
            pdf_path: Path to PDF (for pdf_hash)
            sections_json: Serialized sections
            tables_json: Serialized tables
            extraction_time: Time taken for extraction
            created_at: When extraction was done

        Returns:
            Reconstructed DocumentMap
        """
        # Deserialize sections
        sections = json.loads(sections_json)

        # Deserialize tables
        tables_dict = json.loads(tables_json)
        tables = {}
        for table_name, table_data in tables_dict.items():
            tables[table_name] = TableData(
                table_type=table_data['table_type'],
                page=table_data['page'],
                rows=table_data['rows'],
                headers=table_data['headers'],
                related_note=table_data.get('related_note'),
                confidence=table_data.get('confidence', 0.0)
            )

        # Compute PDF hash
        pdf_hash = self.detector._compute_pdf_hash(pdf_path)

        return DocumentMap(
            pdf_path=pdf_path,
            pdf_hash=pdf_hash,
            sections=sections,
            tables=tables,
            term_index={},  # Not cached (rarely used)
            cross_references=[],  # Not cached (rarely used)
            extraction_time=extraction_time,
            created_at=created_at
        )

    def get_structure(self, pdf_path: str) -> Tuple[DocumentMap, float]:
        """
        Get structure detection result with multi-layer caching.

        Args:
            pdf_path: Path to PDF file

        Returns:
            (DocumentMap, retrieval_time_seconds)
        """
        start_time = time.time()
        cache_key = self.compute_cache_key(pdf_path)

        # Layer 1: Memory cache
        if pdf_path in self.memory_cache:
            elapsed = time.time() - start_time
            logger.info(f"[Cache] Memory hit: {Path(pdf_path).name} ({elapsed*1000:.1f}ms)")
            return self.memory_cache[pdf_path], elapsed

        # Layer 2: SQLite cache
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM structure_cache WHERE cache_key = ?
            """, (cache_key,))

            row = cursor.fetchone()

            if row:
                entry = dict(row)

                # Verify integrity
                if not self._verify_cache_integrity(entry):
                    # Corruption detected - remove and fall through
                    cursor.execute("DELETE FROM structure_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()
                else:
                    # Update access metadata
                    cursor.execute("""
                        UPDATE structure_cache
                        SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1
                        WHERE cache_key = ?
                    """, (cache_key,))
                    conn.commit()

                    # Deserialize
                    # Parse created_at from database (TIMESTAMP format)
                    created_at_str = entry['created_at']
                    if isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str)
                    else:
                        created_at = datetime.now()

                    document_map = self._deserialize_document_map(
                        pdf_path,
                        entry['sections_json'],
                        entry['tables_json'],
                        entry['detection_time_seconds'],
                        created_at
                    )

                    # Populate memory cache
                    self.memory_cache[pdf_path] = document_map

                    elapsed = time.time() - start_time
                    logger.info(f"[Cache] SQLite hit: {Path(pdf_path).name} ({elapsed*1000:.1f}ms)")
                    return document_map, elapsed

        # Layer 3: JSON file cache (backup)
        json_path = self.json_cache_dir / f"{cache_key}.json"
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    cached_data = json.load(f)

                # Parse created_at from ISO format
                created_at = datetime.fromisoformat(cached_data['created_at'])

                document_map = self._deserialize_document_map(
                    pdf_path,
                    cached_data['sections_json'],
                    cached_data['tables_json'],
                    cached_data['detection_time_seconds'],
                    created_at
                )

                # Populate memory cache
                self.memory_cache[pdf_path] = document_map

                # Restore to SQLite (if missing)
                self._save_to_sqlite(pdf_path, document_map, cached_data['detection_time_seconds'])

                elapsed = time.time() - start_time
                logger.info(f"[Cache] JSON file hit: {Path(pdf_path).name} ({elapsed*1000:.1f}ms)")
                return document_map, elapsed

            except Exception as e:
                logger.warning(f"[Cache] JSON file corrupted: {e}")

        # Layer 4: Docling detection (fallback)
        logger.info(f"[Cache] MISS - Running Docling detection: {Path(pdf_path).name}")
        detection_start = time.time()
        document_map = self.detector.extract_document_map(pdf_path)
        detection_time = time.time() - detection_start

        logger.info(f"[Cache] Docling detection complete: {detection_time:.1f}s")

        # Save to all cache layers
        self._save_to_all_caches(pdf_path, document_map, detection_time)

        elapsed = time.time() - start_time
        return document_map, elapsed

    def _save_to_all_caches(
        self,
        pdf_path: str,
        document_map: DocumentMap,
        detection_time: float
    ):
        """
        Save structure detection result to all cache layers.

        Args:
            pdf_path: Path to PDF
            document_map: Detected structure
            detection_time: Time taken for detection
        """
        # Memory cache
        self.memory_cache[pdf_path] = document_map

        # SQLite cache
        self._save_to_sqlite(pdf_path, document_map, detection_time)

        # JSON file cache
        self._save_to_json(pdf_path, document_map, detection_time)

        logger.info(f"[Cache] Saved to all layers: {Path(pdf_path).name}")

    def _save_to_sqlite(
        self,
        pdf_path: str,
        document_map: DocumentMap,
        detection_time: float
    ):
        """Save to SQLite cache with file locking."""
        cache_key = self.compute_cache_key(pdf_path)
        lock_path = self.cache_dir / f"{cache_key}.lock"

        # Serialize
        sections_json, tables_json = self._serialize_document_map(document_map)
        checksum = self._compute_checksum(sections_json, tables_json)

        # File-based locking for concurrent write safety
        with open(lock_path, 'w') as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    # Check if another process already cached it
                    cursor = conn.cursor()
                    cursor.execute("SELECT cache_key FROM structure_cache WHERE cache_key = ?", (cache_key,))
                    if cursor.fetchone():
                        logger.info(f"[Cache] Another process cached {Path(pdf_path).name}")
                        return

                    # Insert cache entry
                    conn.execute("""
                        INSERT INTO structure_cache (
                            cache_key, pdf_filename, pdf_size_bytes, docling_version,
                            sections_json, tables_json, detection_time_seconds,
                            num_sections, num_tables, checksum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cache_key,
                        Path(pdf_path).name,
                        os.path.getsize(pdf_path),
                        self.docling_version,
                        sections_json,
                        tables_json,
                        detection_time,
                        len(document_map.sections),
                        len(document_map.tables),
                        checksum
                    ))
                    conn.commit()

            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # Release lock
                lock_path.unlink()  # Clean up lock file

    def _save_to_json(
        self,
        pdf_path: str,
        document_map: DocumentMap,
        detection_time: float
    ):
        """Save to JSON file cache (human-readable backup)."""
        cache_key = self.compute_cache_key(pdf_path)
        json_path = self.json_cache_dir / f"{cache_key}.json"

        sections_json, tables_json = self._serialize_document_map(document_map)

        cache_data = {
            'cache_key': cache_key,
            'pdf_filename': Path(pdf_path).name,
            'docling_version': self.docling_version,
            'sections_json': sections_json,
            'tables_json': tables_json,
            'detection_time_seconds': detection_time,
            'num_sections': len(document_map.sections),
            'num_tables': len(document_map.tables),
            'created_at': datetime.now().isoformat()
        }

        with open(json_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def get_cache_size_gb(self) -> float:
        """Get total cache size in GB."""
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        json_size = sum(
            f.stat().st_size
            for f in self.json_cache_dir.glob("*.json")
        )

        total_bytes = db_size + json_size
        return total_bytes / (1024 ** 3)

    def evict_least_recently_used(self, target_size_gb: Optional[float] = None):
        """
        Evict least recently used cache entries until under size limit.

        Args:
            target_size_gb: Target size (defaults to max_cache_size_gb)
        """
        if target_size_gb is None:
            target_size_gb = self.max_cache_size_gb

        current_size = self.get_cache_size_gb()

        if current_size <= target_size_gb:
            logger.info(f"[Cache] Size OK: {current_size:.2f}GB <= {target_size_gb:.2f}GB")
            return

        logger.info(f"[Cache] Evicting LRU entries: {current_size:.2f}GB → {target_size_gb:.2f}GB")

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get entries sorted by last access time
            cursor.execute("""
                SELECT cache_key, pdf_filename, accessed_at
                FROM structure_cache
                ORDER BY accessed_at ASC
            """)

            entries = cursor.fetchall()

            for entry in entries:
                if self.get_cache_size_gb() <= target_size_gb:
                    break

                # Delete from SQLite
                cursor.execute("DELETE FROM structure_cache WHERE cache_key = ?", (entry['cache_key'],))

                # Delete from JSON cache
                json_path = self.json_cache_dir / f"{entry['cache_key']}.json"
                if json_path.exists():
                    json_path.unlink()

                logger.info(f"[Cache] Evicted: {entry['pdf_filename']}")

            conn.commit()

        logger.info(f"[Cache] After eviction: {self.get_cache_size_gb():.2f}GB")

    def clear_all(self):
        """Clear all cache layers."""
        logger.info("[Cache] Clearing all cache layers...")

        # Clear memory cache
        self.memory_cache.clear()

        # Clear SQLite cache
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM structure_cache")
            conn.commit()

        # Clear JSON cache
        for json_file in self.json_cache_dir.glob("*.json"):
            json_file.unlink()

        logger.info("[Cache] All cache layers cleared")

    def clear_pdf(self, pdf_path: str):
        """
        Clear cache for specific PDF.

        Args:
            pdf_path: Path to PDF file
        """
        cache_key = self.compute_cache_key(pdf_path)

        # Clear memory cache
        if pdf_path in self.memory_cache:
            del self.memory_cache[pdf_path]

        # Clear SQLite cache
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM structure_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()

        # Clear JSON cache
        json_path = self.json_cache_dir / f"{cache_key}.json"
        if json_path.exists():
            json_path.unlink()

        logger.info(f"[Cache] Cleared: {Path(pdf_path).name}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total entries
            cursor.execute("SELECT COUNT(*) as count FROM structure_cache")
            total_entries = cursor.fetchone()['count']

            # Total sections and tables
            cursor.execute("SELECT SUM(num_sections) as sections, SUM(num_tables) as tables FROM structure_cache")
            row = cursor.fetchone()
            total_sections = row['sections'] or 0
            total_tables = row['tables'] or 0

            # Average detection time
            cursor.execute("SELECT AVG(detection_time_seconds) as avg_time FROM structure_cache")
            avg_detection_time = cursor.fetchone()['avg_time'] or 0

            # Most accessed
            cursor.execute("""
                SELECT pdf_filename, access_count
                FROM structure_cache
                ORDER BY access_count DESC
                LIMIT 5
            """)
            most_accessed = [dict(row) for row in cursor.fetchall()]

        return {
            'total_entries': total_entries,
            'total_sections': total_sections,
            'total_tables': total_tables,
            'avg_detection_time_seconds': avg_detection_time,
            'cache_size_gb': self.get_cache_size_gb(),
            'memory_cache_size': len(self.memory_cache),
            'most_accessed': most_accessed
        }

    # ========================================================================
    # LAYER 3 LLM CLASSIFICATION CACHE METHODS (v3.0)
    # ========================================================================

    def _normalize_heading_for_cache(self, heading: str) -> str:
        """
        Normalize heading for cache key (Swedish character normalization).

        Args:
            heading: Section heading

        Returns:
            Normalized heading (lowercase, Swedish chars normalized)
        """
        return (heading.lower()
                .replace('å', 'a').replace('Å', 'a')
                .replace('ä', 'a').replace('Ä', 'a')
                .replace('ö', 'o').replace('Ö', 'o')
                .strip())

    def get_llm_classification(self, heading: str) -> Optional[Dict[str, Any]]:
        """
        Get cached LLM classification result.

        Args:
            heading: Section heading to classify

        Returns:
            Classification dict or None if not cached
        """
        heading_normalized = self._normalize_heading_for_cache(heading)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM llm_classification_cache WHERE heading_normalized = ?
            """, (heading_normalized,))

            row = cursor.fetchone()

            if row:
                # Update access metadata
                cursor.execute("""
                    UPDATE llm_classification_cache
                    SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE heading_normalized = ?
                """, (heading_normalized,))
                conn.commit()

                # Return classification
                return {
                    'agents': json.loads(row['agents_json']),
                    'primary_agent': row['primary_agent'],
                    'confidence': row['confidence'],
                    'reasoning': row['reasoning'],
                    'model': row['model'],
                    'cached': True
                }

        return None

    def put_llm_classification(
        self,
        heading: str,
        agents: List[str],
        primary_agent: str,
        confidence: float,
        reasoning: str,
        model: str,
        tokens_used: int,
        cost_usd: float
    ):
        """
        Cache LLM classification result.

        Args:
            heading: Section heading
            agents: List of agent IDs (multi-agent routing)
            primary_agent: Primary agent ID
            confidence: Confidence score (0-1)
            reasoning: Classification reasoning
            model: Model used
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
        """
        heading_normalized = self._normalize_heading_for_cache(heading)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO llm_classification_cache (
                    heading_normalized, agents_json, primary_agent, confidence,
                    reasoning, model, tokens_used, cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                heading_normalized,
                json.dumps(agents),
                primary_agent,
                confidence,
                reasoning,
                model,
                tokens_used,
                cost_usd
            ))
            conn.commit()

    def get_llm_classification_stats(self) -> Dict[str, Any]:
        """Get LLM classification cache statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total cached classifications
            cursor.execute("SELECT COUNT(*) as count FROM llm_classification_cache")
            total_cached = cursor.fetchone()['count']

            # Total cost saved
            cursor.execute("SELECT SUM(cost_usd) as total_cost FROM llm_classification_cache")
            total_cost = cursor.fetchone()['total_cost'] or 0.0

            # Total tokens saved (assuming 80% cache hit rate after warmup)
            cursor.execute("SELECT SUM(tokens_used) as total_tokens FROM llm_classification_cache")
            total_tokens = cursor.fetchone()['total_tokens'] or 0

            # Most common primary agents
            cursor.execute("""
                SELECT primary_agent, COUNT(*) as count
                FROM llm_classification_cache
                GROUP BY primary_agent
                ORDER BY count DESC
                LIMIT 5
            """)
            top_agents = [dict(row) for row in cursor.fetchall()]

            # Average confidence
            cursor.execute("SELECT AVG(confidence) as avg_conf FROM llm_classification_cache")
            avg_confidence = cursor.fetchone()['avg_conf'] or 0.0

        return {
            'total_cached_headings': total_cached,
            'total_cost_spent_usd': round(total_cost, 4),
            'total_tokens_used': total_tokens,
            'avg_confidence': round(avg_confidence, 3),
            'top_primary_agents': top_agents,
            'estimated_savings_80pct_hit_rate': round(total_cost * 0.8, 4)
        }


if __name__ == "__main__":
    # Quick test
    cache = CacheManager()

    # Test on sample PDF
    test_pdf = "test_pdfs/brf_268882.pdf"
    if Path(test_pdf).exists():
        print(f"\n{'='*80}")
        print("Testing Cache Manager")
        print(f"{'='*80}\n")

        # First call (cache miss)
        document_map, time1 = cache.get_structure(test_pdf)
        print(f"\nFirst call: {time1:.2f}s")
        print(f"Sections: {len(document_map.sections)}, Tables: {len(document_map.tables)}")

        # Second call (cache hit)
        document_map, time2 = cache.get_structure(test_pdf)
        print(f"\nSecond call: {time2:.4f}s (speedup: {time1/time2:.0f}x)")

        # Statistics
        stats = cache.get_statistics()
        print(f"\n{'='*80}")
        print("Cache Statistics")
        print(f"{'='*80}")
        print(json.dumps(stats, indent=2))
