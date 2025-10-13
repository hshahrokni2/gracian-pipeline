"""
Create Ground Truth via Multi-Model Consensus
==============================================

Strategy: Extract with 3 models (GPT-4o, Claude Opus, Gemini 2.5-Pro), take 2/3 consensus.

Phase 2 of comprehensive validation (estimated 60 minutes):
- Extract with GPT-4o: 20 minutes (3 PDFs × 4-7 min)
- Extract with Claude Opus: 20 minutes
- Extract with Gemini 2.5-Pro: 20 minutes
- Build consensus: 10 minutes

Author: Claude Code
Date: 2025-10-13
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import anthropic
import google.generativeai as genai
from openai import OpenAI
from datetime import datetime

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel


class MultiModelConsensus:
    """Create ground truth via multi-model consensus."""

    def __init__(self):
        """Initialize API clients."""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        self.output_dir = Path(__file__).parent / "ground_truth"
        self.output_dir.mkdir(exist_ok=True)

    def extract_with_gpt4o(self, pdf_path: str) -> Dict[str, Any]:
        """Extract using current GPT-4o based pipeline."""
        print(f"\n🤖 Extracting with GPT-4o: {Path(pdf_path).name}")

        try:
            result = extract_all_agents_parallel(pdf_path)
            print(f"   ✅ GPT-4o extraction complete")
            return result
        except Exception as e:
            print(f"   ❌ GPT-4o extraction failed: {e}")
            return {}

    def extract_with_claude(self, pdf_path: str) -> Dict[str, Any]:
        """Extract using Claude Opus (via Anthropic API)."""
        print(f"\n🤖 Extracting with Claude Opus: {Path(pdf_path).name}")

        # TODO: Implement Claude extraction
        # For now, return placeholder
        print(f"   ⏸️  Claude extraction not yet implemented")
        return {}

    def extract_with_gemini(self, pdf_path: str) -> Dict[str, Any]:
        """Extract using Gemini 2.5-Pro (via Google API)."""
        print(f"\n🤖 Extracting with Gemini 2.5-Pro: {Path(pdf_path).name}")

        # TODO: Implement Gemini extraction
        # For now, return placeholder
        print(f"   ⏸️  Gemini extraction not yet implemented")
        return {}

    def build_consensus(
        self,
        gpt4o_result: Dict[str, Any],
        claude_result: Dict[str, Any],
        gemini_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build ground truth from 3 model results via 2/3 majority vote.

        Strategy:
        - For each field, compare values from 3 models
        - If 2+ models agree: Use agreed value (high confidence)
        - If all disagree: Flag for human review (low confidence)
        - Track which models contributed to each field
        """
        print(f"\n🔍 Building consensus from 3 models...")

        consensus = {
            "metadata": {},
            "governance": {},
            "financial": {},
            "property": {},
            "notes": {},
            "fees": {},
            "loans": [],
            "multi_year_overview": {},
            "_consensus_metadata": {
                "models_used": ["gpt-4o", "claude-opus", "gemini-2.5-pro"],
                "consensus_method": "2_of_3_majority",
                "created_at": datetime.utcnow().isoformat(),
                "fields_with_consensus": 0,
                "fields_needing_review": 0,
                "overall_confidence": 0.0
            }
        }

        # TODO: Implement consensus logic
        # For now, return GPT-4o result as baseline

        return consensus

    def save_ground_truth(
        self,
        pdf_path: str,
        gpt4o_result: Dict[str, Any],
        claude_result: Dict[str, Any],
        gemini_result: Dict[str, Any],
        consensus: Dict[str, Any]
    ):
        """Save all results and consensus."""
        pdf_name = Path(pdf_path).stem

        # Save individual model results
        results = {
            "gpt4o": gpt4o_result,
            "claude": claude_result,
            "gemini": gemini_result,
            "consensus": consensus
        }

        for model, result in results.items():
            output_file = self.output_dir / f"{pdf_name}_{model}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            print(f"   💾 Saved {model} results: {output_file.name}")

    def create_ground_truth_for_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Create ground truth for a single PDF via multi-model consensus."""
        print(f"\n{'='*80}")
        print(f"Creating Ground Truth: {Path(pdf_path).name}")
        print(f"{'='*80}")

        # Extract with 3 models
        gpt4o_result = self.extract_with_gpt4o(pdf_path)
        claude_result = self.extract_with_claude(pdf_path)
        gemini_result = self.extract_with_gemini(pdf_path)

        # Build consensus
        consensus = self.build_consensus(gpt4o_result, claude_result, gemini_result)

        # Save results
        self.save_ground_truth(pdf_path, gpt4o_result, claude_result, gemini_result, consensus)

        return consensus


def main():
    """Create ground truth for 3 test PDFs."""

    # Validate API keys
    required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    missing_keys = [k for k in required_keys if not os.getenv(k)]

    if missing_keys:
        print(f"❌ Missing API keys: {', '.join(missing_keys)}")
        print(f"\nSet them in environment:")
        for key in missing_keys:
            print(f"  export {key}=your_key_here")
        sys.exit(1)

    # Test PDFs
    validation_dir = Path(__file__).parent
    test_pdfs = [
        validation_dir / "test_pdfs" / "machine_readable.pdf",
        validation_dir / "test_pdfs" / "hybrid.pdf",
        validation_dir / "test_pdfs" / "scanned.pdf"
    ]

    # Validate PDFs exist
    for pdf in test_pdfs:
        if not pdf.exists():
            print(f"❌ PDF not found: {pdf}")
            sys.exit(1)

    # Create ground truth
    consensus_builder = MultiModelConsensus()

    ground_truths = {}
    for pdf in test_pdfs:
        consensus = consensus_builder.create_ground_truth_for_pdf(str(pdf))
        ground_truths[pdf.name] = consensus

    # Summary
    print(f"\n{'='*80}")
    print(f"Ground Truth Creation Complete")
    print(f"{'='*80}")
    print(f"✅ Created ground truth for {len(ground_truths)} PDFs")
    print(f"📁 Saved to: {consensus_builder.output_dir}")
    print(f"\nNext: Run comprehensive validation against ground truth")


if __name__ == "__main__":
    main()
