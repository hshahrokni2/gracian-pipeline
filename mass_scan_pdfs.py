#!/usr/bin/env python3
"""
Mass PDF Topology Scanner for Swedish BRF Documents
Designed to handle 80,000+ PDFs with resume capability and progress tracking.

Features:
- Resume capability (SQLite checkpointing)
- Batch processing with memory efficiency
- Progress tracking with ETA
- Incremental JSON saves
- Support for all document types

Usage:
    python mass_scan_pdfs.py --all                    # Scan all document types
    python mass_scan_pdfs.py --type arsredovisning    # Scan specific type
    python mass_scan_pdfs.py --resume                 # Resume from checkpoint
"""

import os
import sys
import argparse
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta
import fitz  # PyMuPDF

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


class MassPDFScanner:
    """Resume-capable mass PDF scanner with checkpoint system"""

    DOCUMENT_TYPES = {
        'arsredovisning': 'Årsredovisning',
        'stadgar': 'Stadgar',
        'ekonomisk_plan': 'Ekonomisk plan',
        'energideklaration': 'Energideklaration',
    }

    def __init__(self, base_dir: str, checkpoint_db: str = "scan_progress.db"):
        self.base_dir = Path(base_dir).expanduser()
        self.checkpoint_db = checkpoint_db
        self.results = {
            'machine_readable': [],
            'scanned': [],
            'hybrid': [],
            'locked': [],
            'corrupted': [],
        }
        self.stats = defaultdict(int)
        self.total_processed = 0
        self.start_time = time.time()

        # Initialize checkpoint database
        self._init_checkpoint_db()

    def _init_checkpoint_db(self):
        """Initialize SQLite checkpoint database"""
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_files (
                filepath TEXT PRIMARY KEY,
                category TEXT,
                size_mb REAL,
                pages INTEGER,
                avg_chars_per_page REAL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                total_files INTEGER,
                document_type TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _is_already_scanned(self, filepath: str) -> bool:
        """Check if file was already scanned"""
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM scanned_files WHERE filepath = ?", (filepath,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def _save_checkpoint(self, filepath: str, result: Dict[str, Any]):
        """Save file analysis to checkpoint database"""
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO scanned_files
            (filepath, category, size_mb, pages, avg_chars_per_page)
            VALUES (?, ?, ?, ?, ?)
        """, (
            filepath,
            result['category'],
            result['size_mb'],
            result['pages'],
            result['avg_chars_per_page']
        ))
        conn.commit()
        conn.close()

    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze a single PDF (same logic as analyze_pdf_topology.py)"""
        result = {
            'path': pdf_path,
            'filename': os.path.basename(pdf_path),
            'size_mb': 0,
            'pages': 0,
            'text_chars': 0,
            'avg_chars_per_page': 0,
            'is_encrypted': False,
            'is_locked': False,
            'category': 'unknown',
            'error': None
        }

        try:
            result['size_mb'] = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
            doc = fitz.open(pdf_path)

            result['is_encrypted'] = doc.is_encrypted
            result['is_locked'] = doc.needs_pass

            if result['is_locked']:
                result['category'] = 'locked'
                self.results['locked'].append(result)
                doc.close()
                return result

            result['pages'] = doc.page_count
            total_chars = 0

            # Sample pages for efficiency
            if doc.page_count > 20:
                sample_pages = list(range(0, doc.page_count, 5))[:10]
            else:
                sample_pages = range(doc.page_count)

            for page_num in sample_pages:
                page = doc.load_page(page_num)
                text = page.get_text("text")
                total_chars += len(text)

            # Extrapolate to full document
            if len(sample_pages) < doc.page_count:
                total_chars = int(total_chars * (doc.page_count / len(sample_pages)))

            result['text_chars'] = total_chars
            result['avg_chars_per_page'] = total_chars / doc.page_count if doc.page_count > 0 else 0

            # Categorize
            if result['avg_chars_per_page'] > 800:
                result['category'] = 'machine_readable'
                self.results['machine_readable'].append(result)
            elif result['avg_chars_per_page'] < 200:
                result['category'] = 'scanned'
                self.results['scanned'].append(result)
            else:
                result['category'] = 'hybrid'
                self.results['hybrid'].append(result)

            doc.close()

        except Exception as e:
            result['error'] = str(e)
            result['category'] = 'corrupted'
            self.results['corrupted'].append(result)

        return result

    def _format_eta(self, seconds: float) -> str:
        """Format ETA in human-readable form"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def scan_directory(self, doc_type_key: str, batch_size: int = 5000):
        """Scan all PDFs in a document type directory with batching"""
        doc_type_name = self.DOCUMENT_TYPES.get(doc_type_key, doc_type_key)
        doc_dir = self.base_dir / doc_type_name

        if not doc_dir.exists():
            print(f"❌ Directory not found: {doc_dir}")
            return

        # Find all PDFs
        print(f"\n📂 Scanning directory: {doc_dir}")
        print("   Finding all PDF files...")
        pdf_files = list(doc_dir.rglob("*.pdf"))
        total_files = len(pdf_files)

        if total_files == 0:
            print(f"⚠️  No PDF files found in {doc_dir}")
            return

        print(f"   Found {total_files:,} PDF files")

        # Check how many already scanned
        already_scanned = sum(1 for f in pdf_files if self._is_already_scanned(str(f)))
        remaining = total_files - already_scanned

        if already_scanned > 0:
            print(f"   ✅ {already_scanned:,} already scanned (resuming)")
            print(f"   ⏳ {remaining:,} remaining")

        # Start session
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scan_sessions (total_files, document_type) VALUES (?, ?)",
            (total_files, doc_type_key)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"\n🚀 Starting scan (Session #{session_id})")
        print("=" * 100)

        # Process files
        processed_this_run = 0
        last_save = time.time()
        last_checkpoint = 0

        for idx, pdf_path in enumerate(pdf_files, 1):
            pdf_str = str(pdf_path)

            # Skip if already scanned
            if self._is_already_scanned(pdf_str):
                continue

            # Analyze PDF
            result = self.analyze_pdf(pdf_str)
            self.stats[result['category']] += 1
            self.total_processed += 1
            processed_this_run += 1

            # Save checkpoint
            self._save_checkpoint(pdf_str, result)

            # Progress update every 100 files
            if processed_this_run % 100 == 0 or processed_this_run == 1:
                elapsed = time.time() - self.start_time
                rate = processed_this_run / elapsed if elapsed > 0 else 0
                eta_seconds = (remaining - processed_this_run) / rate if rate > 0 else 0

                print(f"Progress: {idx:,}/{total_files:,} ({idx*100//total_files}%) | "
                      f"Processed this run: {processed_this_run:,} | "
                      f"Rate: {rate:.1f} PDF/s | "
                      f"ETA: {self._format_eta(eta_seconds)}")
                print(f"  Categories: MR={self.stats['machine_readable']:,} | "
                      f"Scan={self.stats['scanned']:,} | "
                      f"Hybrid={self.stats['hybrid']:,} | "
                      f"Locked={self.stats['locked']:,} | "
                      f"Corrupt={self.stats['corrupted']:,}")

            # Save intermediate JSON every 1000 files
            if processed_this_run - last_checkpoint >= 1000:
                self._save_intermediate_json(doc_type_key, session_id)
                last_checkpoint = processed_this_run

        # Final save
        self._save_intermediate_json(doc_type_key, session_id, final=True)

        # Update session
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scan_sessions SET completed_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()

        print(f"\n✅ Scan complete for {doc_type_name}")
        print(f"   Processed: {processed_this_run:,} new files")
        print(f"   Total in database: {self.total_processed:,}")

    def _save_intermediate_json(self, doc_type_key: str, session_id: int, final: bool = False):
        """Save intermediate results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "final" if final else f"checkpoint_{timestamp}"
        filename = f"mass_scan_{doc_type_key}_{suffix}.json"

        output = {
            'session_id': session_id,
            'document_type': doc_type_key,
            'timestamp': timestamp,
            'total_processed': self.total_processed,
            'summary': dict(self.stats),
            'sample_results': {
                cat: self.results[cat][:5] for cat in self.results.keys()
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        if final:
            print(f"\n💾 Final results saved to: {filename}")
        else:
            print(f"   💾 Checkpoint saved: {filename}")

    def load_from_checkpoint(self) -> Dict[str, int]:
        """Load stats from checkpoint database"""
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*)
            FROM scanned_files
            GROUP BY category
        """)
        stats = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM scanned_files")
        total = cursor.fetchone()[0]

        conn.close()

        self.stats = defaultdict(int, stats)
        self.total_processed = total

        return stats

    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "=" * 100)
        print("📊 MASS SCAN SUMMARY")
        print("=" * 100)

        total = sum(self.stats.values())

        print(f"\n📈 Total PDFs Scanned: {total:,}")
        print("-" * 100)

        categories = [
            ('machine_readable', '📄 Machine-Readable'),
            ('hybrid', '📑 Hybrid'),
            ('scanned', '🖼️  Scanned/Image-Based'),
            ('locked', '🔒 Locked/Encrypted'),
            ('corrupted', '❌ Corrupted'),
        ]

        for key, emoji_name in categories:
            count = self.stats[key]
            pct = (count * 100 / total) if total > 0 else 0
            print(f"{emoji_name:30} {count:8,} ({pct:5.1f}%)")

        elapsed = time.time() - self.start_time
        print(f"\n⏱️  Total time: {self._format_eta(elapsed)}")
        print(f"📊 Average rate: {total/elapsed:.1f} PDFs/second")


def main():
    parser = argparse.ArgumentParser(description='Mass scan PDFs for topology analysis')
    parser.add_argument('--all', action='store_true', help='Scan all document types')
    parser.add_argument('--type', type=str, choices=list(MassPDFScanner.DOCUMENT_TYPES.keys()),
                       help='Scan specific document type')
    parser.add_argument('--batch-size', type=int, default=5000, help='Batch size for processing')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--checkpoint-db', type=str, default='scan_progress.db',
                       help='Checkpoint database file')
    parser.add_argument('--base-dir', type=str,
                       default='~/Dropbox/zeldadb/zeldabot/pdf_docs',
                       help='Base directory containing PDF folders')

    args = parser.parse_args()

    # Initialize scanner
    scanner = MassPDFScanner(args.base_dir, args.checkpoint_db)

    # Load checkpoint if resuming
    if args.resume or os.path.exists(args.checkpoint_db):
        print("📂 Loading checkpoint database...")
        stats = scanner.load_from_checkpoint()
        print(f"   ✅ Found {scanner.total_processed:,} previously scanned PDFs")
        print(f"   Categories: {dict(stats)}")

    # Scan based on arguments
    if args.all:
        print("\n🌍 Scanning ALL document types")
        for doc_type_key in MassPDFScanner.DOCUMENT_TYPES.keys():
            scanner.scan_directory(doc_type_key, args.batch_size)
    elif args.type:
        scanner.scan_directory(args.type, args.batch_size)
    else:
        print("❌ Please specify --all or --type <document_type>")
        print(f"   Available types: {', '.join(MassPDFScanner.DOCUMENT_TYPES.keys())}")
        return

    # Print final summary
    scanner.print_summary()


if __name__ == "__main__":
    main()
