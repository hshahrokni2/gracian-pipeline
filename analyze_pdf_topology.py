#!/usr/bin/env python3
"""
PDF Topology Analyzer for Swedish BRF Annual Reports

Analyzes PDFs to categorize them by readability:
1. Machine-readable (text-based PDFs with extractable text)
2. Locked/encrypted (password-protected or restricted)
3. Scanned/image-based (low text layer, mostly images)
4. Hybrid (mix of text and images)

Usage:
    python analyze_pdf_topology.py --local-dir ~/Dropbox/zeldadb/zeldabot/pdf_docs_old
    python analyze_pdf_topology.py --database  # Query H100 PostgreSQL
    python analyze_pdf_topology.py --both      # Analyze both local and remote
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import fitz  # PyMuPDF

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class PDFTopologyAnalyzer:
    def __init__(self):
        self.results = {
            'machine_readable': [],  # >80% text extractable
            'scanned': [],           # <20% text, mostly images
            'hybrid': [],            # 20-80% text
            'locked': [],            # Password-protected or encrypted
            'corrupted': [],         # Cannot open or process
        }
        self.stats = defaultdict(int)

    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze a single PDF and return its characteristics"""
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
            # Get file size
            result['size_mb'] = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)

            # Try to open PDF
            doc = fitz.open(pdf_path)

            # Check if encrypted/locked
            result['is_encrypted'] = doc.is_encrypted
            result['is_locked'] = doc.needs_pass

            if result['is_locked']:
                result['category'] = 'locked'
                self.results['locked'].append(result)
                doc.close()
                return result

            # Count pages and extract text
            result['pages'] = doc.page_count
            total_chars = 0

            # Sample pages (if >20 pages, sample every 5th page for speed)
            if doc.page_count > 20:
                sample_pages = list(range(0, doc.page_count, 5))[:10]  # Max 10 samples
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

            # Categorize based on text density
            if result['avg_chars_per_page'] > 800:  # >800 chars/page = machine-readable
                result['category'] = 'machine_readable'
                self.results['machine_readable'].append(result)
            elif result['avg_chars_per_page'] < 200:  # <200 chars/page = scanned
                result['category'] = 'scanned'
                self.results['scanned'].append(result)
            else:  # 200-800 chars/page = hybrid
                result['category'] = 'hybrid'
                self.results['hybrid'].append(result)

            doc.close()

        except Exception as e:
            result['error'] = str(e)
            result['category'] = 'corrupted'
            self.results['corrupted'].append(result)

        return result

    def analyze_directory(self, directory: str, pattern: str = "*.pdf") -> None:
        """Analyze all PDFs in a directory"""
        pdf_files = list(Path(directory).rglob(pattern))
        total = len(pdf_files)

        print(f"\n📁 Analyzing {total} PDFs in {directory}")
        print("=" * 80)

        for idx, pdf_path in enumerate(pdf_files, 1):
            if idx % 50 == 0 or idx == 1:
                print(f"Progress: {idx}/{total} ({idx*100//total}%)")

            result = self.analyze_pdf(str(pdf_path))
            self.stats[result['category']] += 1

    def analyze_database(self, db_url: str = None) -> None:
        """Query H100 PostgreSQL for PDF metadata"""
        if not db_url:
            db_url = os.getenv("DATABASE_URL", "postgresql://postgres:h100pass@localhost:15432/zelda_arsredovisning")

        try:
            import psycopg2
            print(f"\n🗄️  Connecting to PostgreSQL database...")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'arsredovisning_documents'
            """)

            if cursor.fetchone()[0] == 0:
                print("⚠️  Table 'arsredovisning_documents' not found. Trying alternative tables...")
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                print(f"Available tables: {[t[0] for t in tables]}")

                # Try to find document table
                for table in tables:
                    if 'doc' in table[0].lower() or 'pdf' in table[0].lower():
                        print(f"Using table: {table[0]}")
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cursor.fetchone()[0]
                        print(f"Total documents in {table[0]}: {count}")

                        # Get sample metadata
                        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                        rows = cursor.fetchall()
                        if rows:
                            print(f"\nSample records:")
                            for row in rows:
                                print(f"  {row}")

            else:
                # Query document metadata
                cursor.execute("""
                    SELECT COUNT(*) FROM arsredovisning_documents
                """)
                total_docs = cursor.fetchone()[0]

                print(f"✅ Total documents in database: {total_docs}")

                # Query by file type if metadata exists
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'arsredovisning_documents'
                """)
                columns = [col[0] for col in cursor.fetchall()]
                print(f"Available columns: {columns}")

            cursor.close()
            conn.close()

        except ImportError:
            print("⚠️  psycopg2 not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            print("\nTo connect to H100 database, first establish SSH tunnel:")
            print("  ssh -p 26983 -i ~/.ssh/BrfGraphRag root@45.135.56.10 -N -f -L 15432:localhost:5432")

    def print_summary(self) -> None:
        """Print analysis summary"""
        print("\n" + "=" * 80)
        print("📊 PDF TOPOLOGY ANALYSIS SUMMARY")
        print("=" * 80)

        total = sum(self.stats.values())

        print(f"\n📈 Total PDFs Analyzed: {total}")
        print("-" * 80)

        categories = [
            ('machine_readable', '📄 Machine-Readable', 'Text-based, easy to extract'),
            ('hybrid', '📑 Hybrid', 'Mix of text and images'),
            ('scanned', '🖼️  Scanned/Image-Based', 'Low text, mostly images'),
            ('locked', '🔒 Locked/Encrypted', 'Password-protected'),
            ('corrupted', '❌ Corrupted', 'Cannot open or process'),
        ]

        for key, emoji_name, description in categories:
            count = self.stats[key]
            pct = (count * 100 / total) if total > 0 else 0
            print(f"{emoji_name:30} {count:6,} ({pct:5.1f}%) - {description}")

        # Detailed breakdown
        print("\n" + "=" * 80)
        print("🔍 DETAILED BREAKDOWN")
        print("=" * 80)

        for key, emoji_name, description in categories:
            if self.results[key]:
                print(f"\n{emoji_name} ({len(self.results[key])} files):")
                # Show first 5 examples
                for result in self.results[key][:5]:
                    chars_info = f"{result['avg_chars_per_page']:.0f} chars/page" if 'avg_chars_per_page' in result else ""
                    print(f"  • {result['filename'][:60]:60} {result['size_mb']:6.1f}MB {result['pages']:4}pg {chars_info}")
                if len(self.results[key]) > 5:
                    print(f"  ... and {len(self.results[key]) - 5} more")

        # Recommendations
        print("\n" + "=" * 80)
        print("💡 EXTRACTION STRATEGY RECOMMENDATIONS")
        print("=" * 80)

        mr_pct = (self.stats['machine_readable'] * 100 / total) if total > 0 else 0
        scanned_pct = (self.stats['scanned'] * 100 / total) if total > 0 else 0
        hybrid_pct = (self.stats['hybrid'] * 100 / total) if total > 0 else 0

        print(f"\n1. Pattern/Text Extraction ({mr_pct:.1f}%):")
        print(f"   Use for {self.stats['machine_readable']} machine-readable PDFs")
        print(f"   Strategy: PyMuPDF text extraction + regex patterns")
        print(f"   Speed: Fast (1-2 seconds per document)")

        print(f"\n2. Vision/OCR Models ({scanned_pct:.1f}%):")
        print(f"   Use for {self.stats['scanned']} scanned PDFs")
        print(f"   Strategy: Qwen 2.5-VL, Gemini 2.5-Pro, GPT-5 Vision")
        print(f"   Speed: Slow (10-30 seconds per document)")

        print(f"\n3. Hybrid Approach ({hybrid_pct:.1f}%):")
        print(f"   Use for {self.stats['hybrid']} hybrid PDFs")
        print(f"   Strategy: Text extraction + vision for tables/scans")
        print(f"   Speed: Medium (5-15 seconds per document)")

        if self.stats['locked'] > 0:
            print(f"\n4. Special Handling ({self.stats['locked']} locked PDFs):")
            print(f"   May require password unlocking or skip")

        # Save detailed results to JSON
        output_file = "pdf_topology_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': dict(self.stats),
                'total': total,
                'results': self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze PDF topology for BRF documents')
    parser.add_argument('--local-dir', type=str, help='Directory containing PDFs to analyze')
    parser.add_argument('--database', action='store_true', help='Query H100 PostgreSQL database')
    parser.add_argument('--both', action='store_true', help='Analyze both local and database')
    parser.add_argument('--pattern', type=str, default='*.pdf', help='File pattern to match (default: *.pdf)')

    args = parser.parse_args()

    analyzer = PDFTopologyAnalyzer()

    if args.both or args.local_dir:
        local_dir = args.local_dir or os.path.expanduser('~/Dropbox/zeldadb/zeldabot/pdf_docs_old')
        if os.path.exists(local_dir):
            analyzer.analyze_directory(local_dir, args.pattern)
        else:
            print(f"❌ Directory not found: {local_dir}")

    if args.both or args.database:
        analyzer.analyze_database()

    if not args.local_dir and not args.database and not args.both:
        # Default: analyze local directory
        default_dir = os.path.expanduser('~/Dropbox/zeldadb/zeldabot/pdf_docs_old')
        if os.path.exists(default_dir):
            analyzer.analyze_directory(default_dir)
        else:
            print("❌ No directory specified and default not found.")
            print("Usage: python analyze_pdf_topology.py --local-dir <path> or --database")
            return

    analyzer.print_summary()


if __name__ == "__main__":
    main()
