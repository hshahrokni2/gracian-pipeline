#!/usr/bin/env python3
"""
Process Hjorthagen + NDS with Two-LLM System + Schema Evolution

Features:
- Processes all PDFs in Hjorthagen and NDS folders
- Two-LLM consensus validation (Claude + GPT)
- Dynamic schema evolution from discovered fields
- Anti-hallucination tracking and validation
- Progress tracking and resumption

Date: 2025-10-15
User Request: Process all Hjorthagen and NDS, train Pydantic schemas from discoveries
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ground_truth" / "scripts"))
sys.path.insert(0, str(project_root / "experiments" / "docling_advanced" / "code"))

# Change to experiments directory for config files
os.chdir(str(project_root / "experiments" / "docling_advanced"))

from create_two_llm_ground_truth import TwoLLMGroundTruthCreator
from schema_evolution_manager import SchemaEvolutionManager


class BatchProcessor:
    """
    Batch processor for Hjorthagen + NDS with schema evolution.
    """

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = str(project_root / "ground_truth" / "batch_results")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize schema evolution manager
        self.schema_manager = SchemaEvolutionManager()

        # Track processing state
        self.state_file = self.output_dir / "processing_state.json"
        self.state = self._load_state()

        # Statistics
        self.stats = {
            "total_pdfs": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0,
            "fields_discovered": 0,
            "consensus_achieved": 0,
            "human_needed": 0
        }

    def _load_state(self) -> Dict:
        """Load processing state for resumption."""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "processed_pdfs": [],
            "failed_pdfs": [],
            "last_updated": None
        }

    def _save_state(self):
        """Save processing state."""
        self.state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def find_pdfs(self, directory: str) -> List[Path]:
        """Find all PDFs in directory."""
        dir_path = project_root / directory
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {directory}")
            return []

        pdfs = list(dir_path.glob("*.pdf"))
        print(f"📂 Found {len(pdfs)} PDFs in {directory}")
        return pdfs

    def process_pdf(self, pdf_path: Path) -> Tuple[bool, Dict]:
        """
        Process single PDF with two-LLM system + schema evolution.

        Returns:
            (success, result_summary)
        """
        pdf_name = pdf_path.name

        # Skip if already processed
        if pdf_name in self.state["processed_pdfs"]:
            print(f"⏭️  Skipping {pdf_name} (already processed)")
            self.stats["skipped"] += 1
            return True, {"skipped": True}

        print(f"\n{'='*80}")
        print(f"📄 Processing: {pdf_name}")
        print(f"{'='*80}")

        start_time = time.time()

        try:
            # Stage 1-4: Two-LLM ground truth creation
            creator = TwoLLMGroundTruthCreator(str(pdf_path), output_dir=str(self.output_dir))
            consensus_gt, human_needed = creator.run_full_pipeline()

            elapsed = time.time() - start_time

            # Analyze for schema evolution
            self.schema_manager.analyze_extraction_result(pdf_name, consensus_gt)

            # Update statistics
            self.stats["successful"] += 1
            self.stats["total_time"] += elapsed
            if human_needed:
                self.stats["human_needed"] += len(human_needed)
            else:
                self.stats["consensus_achieved"] += 1

            # Mark as processed
            self.state["processed_pdfs"].append(pdf_name)
            self._save_state()

            result_summary = {
                "pdf_name": pdf_name,
                "success": True,
                "time_seconds": round(elapsed, 2),
                "consensus_fields": len(creator.gpt_results or {}) - len(human_needed),
                "human_needed": len(human_needed),
                "output_files": {
                    "consensus": f"{pdf_path.stem}_consensus_*.json",
                    "questions": f"{pdf_path.stem}_verify_*.md" if human_needed else None
                }
            }

            print(f"\n✅ Successfully processed in {elapsed:.1f}s")
            print(f"   Consensus: {result_summary['consensus_fields']} fields")
            print(f"   Human needed: {len(human_needed)} fields")

            return True, result_summary

        except Exception as e:
            elapsed = time.time() - start_time
            self.stats["failed"] += 1

            # Mark as failed
            self.state["failed_pdfs"].append({
                "pdf_name": pdf_name,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            self._save_state()

            print(f"\n❌ FAILED after {elapsed:.1f}s: {e}")

            return False, {
                "pdf_name": pdf_name,
                "success": False,
                "error": str(e),
                "time_seconds": round(elapsed, 2)
            }

    def process_batch(self, directories: List[str]):
        """Process all PDFs in given directories."""
        # Collect all PDFs
        all_pdfs = []
        for directory in directories:
            pdfs = self.find_pdfs(directory)
            all_pdfs.extend(pdfs)

        self.stats["total_pdfs"] = len(all_pdfs)

        print(f"\n🚀 Starting batch processing of {len(all_pdfs)} PDFs")
        print(f"={'='*80}\n")

        # Process each PDF
        results = []
        for i, pdf_path in enumerate(all_pdfs, 1):
            print(f"\n[{i}/{len(all_pdfs)}] ", end='')
            success, result = self.process_pdf(pdf_path)
            results.append(result)
            self.stats["processed"] += 1

            # Save intermediate results
            if i % 5 == 0:  # Every 5 PDFs
                self._save_intermediate_report(results)

        # Final report
        self._save_final_report(results)

    def _save_intermediate_report(self, results: List[Dict]):
        """Save intermediate processing report."""
        report_file = self.output_dir / "processing_report_intermediate.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "statistics": self.stats,
                "results": results,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2, ensure_ascii=False)

    def _save_final_report(self, results: List[Dict]):
        """Save final processing report and schema updates."""
        print(f"\n{'='*80}")
        print("📊 FINAL PROCESSING REPORT")
        print(f"{'='*80}\n")

        # Print statistics
        print(f"Total PDFs: {self.stats['total_pdfs']}")
        print(f"Processed: {self.stats['processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Total time: {self.stats['total_time']/60:.1f} minutes")
        print(f"Avg time/PDF: {self.stats['total_time']/max(self.stats['successful'],1):.1f}s")
        print(f"")
        print(f"Consensus achieved: {self.stats['consensus_achieved']} PDFs")
        print(f"Human verification needed: {self.stats['human_needed']} fields total")

        # Save JSON report
        report_file = self.output_dir / "processing_report_final.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "statistics": self.stats,
                "results": results,
                "processed_pdfs": self.state["processed_pdfs"],
                "failed_pdfs": self.state["failed_pdfs"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Report saved: {report_file}")

        # Generate schema updates
        print(f"\n🔬 Generating schema evolution report...")
        self.schema_manager.save_update_summary()

        print(f"\n✅ Batch processing complete!")
        print(f"\nOutput directory: {self.output_dir}")
        print(f"  - Ground truths: *_consensus_*.json")
        print(f"  - Human questions: *_verify_*.md")
        print(f"  - Schema evolution: ../schema_evolution/")
        print(f"  - Processing report: processing_report_final.json")


def main():
    """Main entry point."""
    print("🚀 Hjorthagen + NDS Batch Processing with Schema Evolution")
    print("="*80)
    print("")

    # Initialize processor
    processor = BatchProcessor()

    # Process both folders
    directories = ["Hjorthagen", "ground_truth/norra_djurgardsstaden"]

    # Check if NDS has PDFs
    nds_path = project_root / "ground_truth" / "norra_djurgardsstaden"
    if not nds_path.exists() or not list(nds_path.glob("*.pdf")):
        print("⚠️  NDS directory empty or missing, processing only Hjorthagen")
        directories = ["Hjorthagen"]

    processor.process_batch(directories)


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Run: export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    main()
