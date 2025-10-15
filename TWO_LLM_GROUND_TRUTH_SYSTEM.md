# Two-LLM Ground Truth Verification System

**Date**: 2025-10-15
**Purpose**: Create highest-quality ground truths using **two independent LLMs** before requesting human verification
**Status**: 🎯 **DESIGN COMPLETE - READY FOR IMPLEMENTATION**

---

## 🧠 Core Concept

**Problem**: Single LLM (Claude) has biases and blind spots that lead to:
- Misclassifications (Seed #3: predicted scanned when text-based)
- Extraction errors (Seed #1: 100K SEK equity error)
- Placeholder detection failures (Seed #1: real values flagged as placeholders)

**Solution**: **Two-LLM Consensus System**
1. **LLM 1 (Claude Sonnet 4)**: Creates initial ground truth with confidence scores
2. **LLM 2 (GPT-4o/4.5/5)**: Re-extracts ONLY fields where Claude <99% confidence
3. **Consensus Logic**: Compare results, flag disagreements for human verification
4. **User Time**: Only verify fields where LLMs disagree or both are uncertain

---

## 📊 System Architecture

### Stage 1: Claude Initial Extraction (Current Process)
```
PDF → Claude Sonnet 4 → Ground Truth JSON with confidence scores
  ↓
Flags fields with confidence <99%
  ↓
Example: 5 fields flagged (organization_number, energy_class, operating_costs, loans, balance_check)
```

### Stage 2: GPT Second Pass (NEW)
```
Flagged fields (confidence <99%) → GPT-4o → Independent extraction
  ↓
GPT re-extracts ONLY the 5 flagged fields
  ↓
Returns: field values + confidence scores + reasoning
```

### Stage 3: Consensus Analysis (NEW)
```
Compare Claude vs GPT results:
  ↓
CASE 1: Agreement (both extract same value) → Auto-accept, confidence = min(claude, gpt)
CASE 2: Disagreement (different values) → Flag for human verification with BOTH values
CASE 3: One succeeds, one fails → Accept success, confidence = succeeding LLM's score
CASE 4: Both fail/uncertain → Flag for human verification (high priority)
```

### Stage 4: Human Verification (Reduced Workload)
```
User verifies ONLY:
  - Fields where LLMs disagree
  - Fields where both LLMs have low confidence (<80%)

Expected reduction: 5 flagged fields → 1-2 need human verification
Time saved: 5 min → 1-2 min per PDF
```

---

## 🎯 Expected Impact

### Current System (Claude Only):
- **Seed #1**: 5 fields flagged → 5 min verification
- **Seed #2**: 2 fields flagged → 3 min verification
- **Seed #3**: 15 fields flagged → 15 min verification
- **Total**: 23 min

### With Two-LLM System:
- **Seed #1**: 5 flagged → 3 auto-resolved by GPT → 2 need human (2 min)
- **Seed #2**: 2 flagged → 1 auto-resolved → 1 need human (1 min)
- **Seed #3**: 15 flagged → 10 auto-resolved → 5 need human (5 min)
- **Total**: **8 min** (65% reduction!)

### Quality Improvements:
1. **Catch Claude errors**: GPT would catch equity error (46,872,029 vs 46,772,011)
2. **Validate classifications**: GPT would confirm Seed #3 is text-based, not scanned
3. **Cross-validate loans**: Both LLMs attempt extraction independently
4. **Reduce false flags**: "Placeholder" operating costs would be confirmed as real by GPT

---

## 🛠️ Implementation Design

### Script: `create_two_llm_ground_truth.py`

```python
#!/usr/bin/env python3
"""
Two-LLM Ground Truth Creation System
Creates consensus ground truths using Claude + GPT before human verification.
"""

import json
import os
from typing import Dict, List, Tuple
from openai import OpenAI

class TwoLLMGroundTruthCreator:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.claude_result = None
        self.gpt_result = None
        self.consensus_result = None
        self.human_verification_needed = []

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def stage1_claude_extraction(self) -> Dict:
        """
        Stage 1: Claude creates initial ground truth with confidence scores.
        Returns: Ground truth JSON with all fields + confidence scores
        """
        print("🤖 Stage 1: Claude Sonnet 4 initial extraction...")

        # Use existing extraction pipeline (docling + agents)
        # This is what we already have working
        claude_result = self._run_existing_extraction(self.pdf_path)

        # Identify fields with confidence <99%
        flagged_fields = self._identify_low_confidence_fields(claude_result)

        print(f"   ✅ Claude extracted {len(claude_result)} fields")
        print(f"   ⚠️  Flagged {len(flagged_fields)} fields for GPT review")

        self.claude_result = claude_result
        return claude_result, flagged_fields

    def stage2_gpt_second_pass(self, flagged_fields: List[str]) -> Dict:
        """
        Stage 2: GPT re-extracts ONLY flagged fields.
        Returns: GPT results for flagged fields only
        """
        print(f"\n🤖 Stage 2: GPT-4o second pass on {len(flagged_fields)} flagged fields...")

        gpt_results = {}

        for field_path in flagged_fields:
            print(f"   🔍 GPT reviewing: {field_path}")

            # Extract field-specific context from PDF
            field_context = self._get_field_context(field_path)

            # Create targeted GPT prompt for this specific field
            prompt = self._create_gpt_field_prompt(field_path, field_context)

            # Call GPT-4o with vision (if needed)
            gpt_response = self._call_gpt_extraction(prompt, field_path)

            gpt_results[field_path] = gpt_response

            print(f"      {'✅' if gpt_response['success'] else '❌'} GPT confidence: {gpt_response['confidence']:.2f}")

        self.gpt_result = gpt_results
        return gpt_results

    def stage3_consensus_analysis(self, claude_result: Dict, gpt_results: Dict) -> Tuple[Dict, List]:
        """
        Stage 3: Analyze Claude vs GPT, identify disagreements.
        Returns: (consensus_result, fields_needing_human_verification)
        """
        print("\n🤝 Stage 3: Consensus analysis...")

        consensus = claude_result.copy()
        human_verification_needed = []

        for field_path, gpt_data in gpt_results.items():
            claude_value = self._get_nested_field(claude_result, field_path)
            gpt_value = gpt_data['value']

            # CASE 1: Agreement
            if self._values_match(claude_value, gpt_value):
                consensus_confidence = min(
                    self._get_nested_field(claude_result, field_path + '.confidence'),
                    gpt_data['confidence']
                )
                self._set_nested_field(consensus, field_path + '.confidence', consensus_confidence)
                self._set_nested_field(consensus, field_path + '.verification_note',
                    f"✅ CONSENSUS: Both Claude and GPT agree (confidence: {consensus_confidence:.2f})")
                print(f"   ✅ {field_path}: AGREEMENT - auto-accepted")

            # CASE 2: Disagreement
            elif claude_value and gpt_value and not self._values_match(claude_value, gpt_value):
                human_verification_needed.append({
                    'field': field_path,
                    'claude_value': claude_value,
                    'gpt_value': gpt_value,
                    'claude_confidence': self._get_nested_field(claude_result, field_path + '.confidence'),
                    'gpt_confidence': gpt_data['confidence'],
                    'reason': 'LLM_DISAGREEMENT',
                    'priority': 'HIGH'
                })
                self._set_nested_field(consensus, field_path + '.verification_note',
                    f"⚠️ DISAGREEMENT: Claude={claude_value}, GPT={gpt_value}. Human verification required.")
                print(f"   ⚠️  {field_path}: DISAGREEMENT - needs human")

            # CASE 3: One succeeds, one fails
            elif claude_value and not gpt_value:
                # Trust Claude's extraction
                self._set_nested_field(consensus, field_path + '.verification_note',
                    f"✅ Claude extracted, GPT failed. Confidence: {self._get_nested_field(claude_result, field_path + '.confidence'):.2f}")
                print(f"   ✅ {field_path}: Claude success - accepted")

            elif gpt_value and not claude_value:
                # Trust GPT's extraction (GPT found what Claude missed!)
                self._set_nested_field(consensus, field_path + '.value', gpt_value)
                self._set_nested_field(consensus, field_path + '.confidence', gpt_data['confidence'])
                self._set_nested_field(consensus, field_path + '.verification_note',
                    f"✅ GPT extracted, Claude missed. GPT confidence: {gpt_data['confidence']:.2f}")
                print(f"   ✅ {field_path}: GPT success - accepted (Claude missed!)")

            # CASE 4: Both fail
            else:
                human_verification_needed.append({
                    'field': field_path,
                    'claude_value': None,
                    'gpt_value': None,
                    'reason': 'BOTH_FAILED',
                    'priority': 'HIGH'
                })
                self._set_nested_field(consensus, field_path + '.verification_note',
                    "❌ Both Claude and GPT failed to extract. Human verification required (field may not exist in document).")
                print(f"   ❌ {field_path}: Both failed - needs human")

        print(f"\n📊 Consensus Summary:")
        print(f"   Total flagged: {len(gpt_results)}")
        print(f"   Auto-resolved: {len(gpt_results) - len(human_verification_needed)}")
        print(f"   Need human: {len(human_verification_needed)}")
        print(f"   Time saved: ~{(len(gpt_results) - len(human_verification_needed)) * 1} minutes")

        self.consensus_result = consensus
        self.human_verification_needed = human_verification_needed

        return consensus, human_verification_needed

    def stage4_human_verification_prompt(self, human_verification_needed: List[Dict]) -> str:
        """
        Stage 4: Generate concise human verification questions.
        Returns: Markdown prompt for user
        """
        if not human_verification_needed:
            return "✅ No human verification needed! Both LLMs agreed on all flagged fields."

        prompt = f"## 🤝 Two-LLM Verification Required\n\n"
        prompt += f"**Fields needing human verification**: {len(human_verification_needed)}\n"
        prompt += f"**Estimated time**: {len(human_verification_needed) * 1} minutes\n\n"

        for i, field_data in enumerate(human_verification_needed, 1):
            prompt += f"### {i}. {field_data['field']}\n\n"

            if field_data['reason'] == 'LLM_DISAGREEMENT':
                prompt += f"**Claude says**: {field_data['claude_value']} (confidence: {field_data['claude_confidence']:.2f})\n"
                prompt += f"**GPT says**: {field_data['gpt_value']} (confidence: {field_data['gpt_confidence']:.2f})\n"
                prompt += f"**Question**: Which value is correct? Or provide the correct value.\n\n"

            elif field_data['reason'] == 'BOTH_FAILED':
                prompt += f"**Both LLMs failed** to extract this field.\n"
                prompt += f"**Question**: Does this field exist in the document? If yes, what is the value?\n\n"

        return prompt

    def _call_gpt_extraction(self, prompt: str, field_path: str) -> Dict:
        """
        Call GPT-4o with targeted prompt for specific field.
        Uses vision if PDF pages provided.
        """
        try:
            # Determine if we need vision (for scanned PDFs or images)
            needs_vision = self._field_needs_vision(field_path)

            if needs_vision:
                # Convert PDF pages to images and use GPT-4o vision
                images = self._get_pdf_images_for_field(field_path)

                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",  # Latest GPT-4o with vision
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a Swedish BRF document extraction expert. Extract the requested field with highest accuracy. Provide confidence score (0-1) and reasoning."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in images]
                            ]
                        }
                    ],
                    temperature=0
                )
            else:
                # Text-only extraction
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a Swedish BRF document extraction expert. Extract the requested field with highest accuracy. Provide confidence score (0-1) and reasoning."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )

            result = json.loads(response.choices[0].message.content)

            return {
                'success': True,
                'value': result.get('value'),
                'confidence': result.get('confidence', 0.5),
                'reasoning': result.get('reasoning', ''),
                'source_page': result.get('source_page')
            }

        except Exception as e:
            return {
                'success': False,
                'value': None,
                'confidence': 0.0,
                'reasoning': f"GPT extraction failed: {str(e)}"
            }

    def _values_match(self, val1, val2, tolerance: float = 0.01) -> bool:
        """
        Compare two values with appropriate tolerance.
        Handles strings (fuzzy), numbers (tolerance), arrays, etc.
        """
        if val1 is None or val2 is None:
            return False

        # Numeric comparison
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(val1 - val2) / max(abs(val1), abs(val2), 1) < tolerance

        # String comparison (fuzzy)
        if isinstance(val1, str) and isinstance(val2, str):
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
            return similarity > 0.85

        # Array comparison
        if isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                return False
            return all(self._values_match(v1, v2) for v1, v2 in zip(val1, val2))

        # Exact comparison for other types
        return val1 == val2

    def run_full_pipeline(self) -> Tuple[Dict, List]:
        """
        Run complete two-LLM ground truth creation pipeline.
        Returns: (consensus_ground_truth, human_verification_questions)
        """
        print(f"🚀 Two-LLM Ground Truth Creation: {self.pdf_path}\n")

        # Stage 1: Claude initial extraction
        claude_result, flagged_fields = self.stage1_claude_extraction()

        if not flagged_fields:
            print("\n✅ Perfect! Claude 100% confident on all fields. No GPT review needed.")
            return claude_result, []

        # Stage 2: GPT second pass on flagged fields
        gpt_results = self.stage2_gpt_second_pass(flagged_fields)

        # Stage 3: Consensus analysis
        consensus, human_needed = self.stage3_consensus_analysis(claude_result, gpt_results)

        # Stage 4: Generate human verification prompt
        human_prompt = self.stage4_human_verification_prompt(human_needed)

        print("\n" + "="*60)
        print(human_prompt)
        print("="*60)

        return consensus, human_needed


def main():
    """
    Example usage: Create ground truth for single PDF with two-LLM verification.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_two_llm_ground_truth.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    creator = TwoLLMGroundTruthCreator(pdf_path)
    consensus_gt, human_questions = creator.run_full_pipeline()

    # Save consensus ground truth
    output_path = pdf_path.replace('.pdf', '_two_llm_ground_truth.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consensus_gt, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Consensus ground truth saved: {output_path}")

    if human_questions:
        print(f"⚠️  {len(human_questions)} fields need human verification")
        print("   Please review the questions above and update the ground truth JSON.")
    else:
        print("🎉 No human verification needed! Both LLMs agreed on all fields.")


if __name__ == "__main__":
    main()
```

---

## 🎯 Model Selection Strategy

### LLM 1: Claude Sonnet 4 (Current)
- **Strengths**: Excellent reasoning, strong on Swedish text, comprehensive extraction
- **Weaknesses**: Can misclassify PDFs, occasional numeric errors
- **Role**: Initial extraction + flagging uncertain fields

### LLM 2: GPT-4o/4.5/5 (Second Pass)
- **Model Options**:
  1. **GPT-4o** (Current best): Vision + text, proven reliability
  2. **GPT-4.5** (If available): Improved reasoning over 4o
  3. **GPT-5** (Future): When released, upgrade automatically
- **Strengths**: Strong numeric accuracy, excellent vision, different biases than Claude
- **Weaknesses**: May be less nuanced on Swedish context
- **Role**: Independent verification of Claude's uncertain fields

### Why This Combination?
1. **Different architectures** → Different blind spots
2. **Complementary strengths** → Claude (reasoning) + GPT (precision)
3. **Cross-validation** → Catches errors both ways
4. **Cost-effective** → GPT only runs on flagged fields (~5-15 per PDF)

---

## 💰 Cost Analysis

### Current Cost (Claude Only):
- **Claude Sonnet 4**: ~$0.40/PDF (full extraction, 300 fields)
- **Human time**: 23 min × 3 PDFs = 69 min
- **Total**: $1.20 + 69 min human time

### With Two-LLM System:
- **Claude Sonnet 4**: ~$0.40/PDF (full extraction)
- **GPT-4o**: ~$0.05/PDF (5-15 flagged fields only, vision mode)
- **Human time**: 8 min × 3 PDFs = 24 min (65% reduction!)
- **Total**: $1.35 + 24 min human time

**Trade-off**: +$0.15/PDF (+13%) → -45 min human time (-65%)

**Value**: Absolutely worth it! $4.05 buys 45 minutes of your time back.

### Scaling to 197 PDFs (Week 2-3):
- **Additional cost**: 197 × $0.15 = **$29.55**
- **Time saved**: 197 × 3 min = **591 minutes (~10 hours!)**
- **ROI**: $29.55 / 10 hours = **$2.96/hour** (incredible value!)

---

## 🎓 Expected Improvements

### Quality Gains:
1. **Catch Numeric Errors**: GPT would catch Seed #1 equity error (46,872,029 vs 46,772,011)
2. **Validate Classifications**: GPT would confirm Seed #3 is text-based, not scanned
3. **Cross-Validate Extractions**: Loan details verified by both LLMs independently
4. **Reduce False Flags**: "Placeholder" detection validated by second opinion

### Efficiency Gains:
1. **Reduce Human Verification**: 23 min → 8 min (65% reduction)
2. **Higher Confidence**: Fields with LLM consensus are trustworthy
3. **Better Prioritization**: Human focuses only on true uncertainties/disagreements
4. **Faster Iteration**: Less back-and-forth with human verifier

### Learning Gains:
1. **Identify Systematic Biases**: Which types of fields each LLM struggles with
2. **Improve Prompts**: Learn from disagreements to refine extraction prompts
3. **Routing Optimization**: Know when to use which LLM for specific fields
4. **Ground Truth Quality**: Highest-quality seeds for training future models

---

## 🚀 Implementation Plan

### Phase 1: Build Core System (3-4 hours)
1. ✅ Design architecture (this document)
2. Implement `TwoLLMGroundTruthCreator` class
3. Integrate with existing Claude extraction pipeline
4. Test on 3 seed PDFs (brf_268882, brf_81563, brf_76536)

### Phase 2: Validate on Seeds (1 hour)
1. Re-run 3 seeds with two-LLM system
2. Compare results vs manual verification
3. Measure time savings and accuracy improvements
4. Refine consensus logic based on learnings

### Phase 3: Scale to 197 PDFs (Week 2-3)
1. Run two-LLM system on confidence-scored expansion
2. User verifies only LLM disagreements
3. Track consensus rate, time savings, cost
4. Document patterns and edge cases

### Phase 4: Optimize & Learn (Ongoing)
1. Analyze which fields have highest disagreement rates
2. Improve prompts for problem fields
3. Consider adding third LLM (Gemini 2.5 Pro?) for tie-breaking
4. Build automated learning loop from human corrections

---

## 📋 Next Steps

### Immediate:
1. **Tonight**: Implement `create_two_llm_ground_truth.py` script (3-4 hours)
2. **Tomorrow**: Test on 3 seed PDFs, measure improvements
3. **Document**: Update CONSENSUS_GROUND_TRUTH_STRATEGY.md with two-LLM approach

### Week 2-3:
4. Deploy two-LLM system for 197 PDF expansion
5. Track metrics: consensus rate, time savings, cost, accuracy
6. Use learnings to refine Week 4+ agent development

---

**Generated**: 2025-10-15
**Status**: 🎯 **DESIGN COMPLETE - READY FOR IMPLEMENTATION**
**Next**: Implement TwoLLMGroundTruthCreator class (3-4 hours)

🤝 **Two heads are better than one - especially when they're both AI!** 🚀
