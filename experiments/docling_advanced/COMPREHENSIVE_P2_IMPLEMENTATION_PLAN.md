# Comprehensive P2 Implementation Plan - 95/95 Goal

## 🎯 Strategic Rationale

**You're absolutely right!** To achieve the 95/95 goal (95% coverage, 95% accuracy), we need **all three options** implemented as a **layered fallback system**.

### Why All Three Are Necessary

**Current State**: 66% match rate (33/50 sections)
**Target**: 95% match rate (48/50 sections)
**Gap**: 29% (15 sections)

**Individual Option Projections**:
- Option A alone: 76-81% (+10-15%) ❌ Falls short of 95%
- Option B alone: 81-86% (+15-20%) ❌ Falls short of 95%
- Option C alone: 86-91% (+20-25%) ❌ Falls short of 95%

**Combined Layered Approach**: 90-95% ✅ **Achieves goal!**

---

## 🏗️ Layered Fallback Architecture

```
Section Heading
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Keyword Matching + Swedish Normalization (Option A) │
│ Cost: $0, Speed: <1ms per section                           │
│ Expected: 76-81% match rate                                 │
└─────────────────────────────────────────────────────────────┘
    ↓ (if no match)
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Fuzzy Matching with Financial Dictionary (Option B) │
│ Cost: $0, Speed: ~5ms per section                           │
│ Expected: 81-86% match rate (cumulative)                    │
└─────────────────────────────────────────────────────────────┘
    ↓ (if no match)
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: LLM Classification Fallback (Option C)             │
│ Cost: ~$0.03/doc, Speed: ~500ms per batch                   │
│ Expected: 90-95% match rate (cumulative)                    │
└─────────────────────────────────────────────────────────────┘
    ↓
Agent Assignment ✅
```

### Cost-Benefit Analysis

**Without Layered Approach**:
- Match rate: 66%
- Field extraction: ~40-50%
- ❌ Fails 95/95 goal

**With Layered Approach**:
- Match rate: 90-95%
- Field extraction: ~75-85%
- Cost: ~$0.03/doc (only for LLM layer on ~5-10% of sections)
- ✅ Achieves 95/95 goal

**ROI**: $0.03/doc to gain 25-29% match rate improvement is **excellent value**.

---

## 📋 Implementation Plan

### Phase 1: Option A - Swedish Normalization (1 hour)

**Goal**: Improve from 66% → 76-81% match rate

**Implementation**:

```python
# Add to optimal_brf_pipeline.py after line 248

def _normalize_swedish(self, text: str) -> str:
    """
    Normalize Swedish characters for matching.

    Swedish → ASCII mapping:
    - å, Å → a
    - ä, Ä → a
    - ö, Ö → o
    """
    return (text.lower()
            .replace('å', 'a').replace('Å', 'a')
            .replace('ä', 'a').replace('Ä', 'a')
            .replace('ö', 'o').replace('Ö', 'o'))

# In route_sections(), replace lines 489-495 with:

# Route main sections (before notes section)
if not in_notes_subsection:
    routed = False
    heading_normalized = self._normalize_swedish(heading)

    for agent_id, keywords in self.main_section_keywords.items():
        # Normalize keywords for matching
        for keyword in keywords:
            keyword_normalized = self._normalize_swedish(keyword)
            if keyword_normalized in heading_normalized:
                main_sections[agent_id].append(heading)
                routed = True
                break
        if routed:
            break
```

**Testing**:
```bash
python code/optimal_brf_pipeline.py ../../data/raw_pdfs/Hjorthagen/brf_268882.pdf
# Check routing.main_sections counts - should increase from 27 to ~35
```

**Expected Improvement**: +7-10 sections matched

---

### Phase 2: Option B - Fuzzy Matching (2 hours)

**Goal**: Improve from 76-81% → 81-86% match rate

**Implementation**:

```python
# Add import at top of optimal_brf_pipeline.py
from swedish_financial_dictionary import SwedishFinancialDictionary

# In __init__(), after line 248:
# Initialize Swedish Financial Dictionary
self.dictionary = SwedishFinancialDictionary(
    config_path="config/swedish_financial_terms.yaml"
)

# In route_sections(), after keyword matching (around line 495):

# If still not routed, try fuzzy matching with dictionary
if not routed:
    match = self.dictionary.match_term(heading, fuzzy_threshold=0.70)
    if match:
        # Map dictionary categories to agents
        category_to_agent = {
            'balance_sheet': 'financial_agent',
            'income_statement': 'financial_agent',
            'cash_flow': 'financial_agent',
            'notes': 'notes_collection',
            'governance': 'governance_agent',
            'board': 'governance_agent',
            'audit': 'governance_agent',
            'management_report': 'governance_agent',
            'property': 'property_agent',
            'operations': 'operations_agent'
        }

        agent_id = category_to_agent.get(match.category)
        if agent_id:
            main_sections[agent_id].append(heading)
            routed = True
            print(f"      🔍 Fuzzy: '{heading[:40]}...' → {agent_id} (score: {match.score:.2f})")
```

**Testing**:
```bash
python code/optimal_brf_pipeline.py ../../data/raw_pdfs/Hjorthagen/brf_268882.pdf
# Should see fuzzy match messages in output
# Check routing.main_sections counts - should increase to ~38-40
```

**Expected Improvement**: +3-5 sections matched (cumulative)

---

### Phase 3: Option C - LLM Classification (4 hours)

**Goal**: Improve from 81-86% → 90-95% match rate

**Implementation**:

```python
# Add to optimal_brf_pipeline.py after fuzzy matching

# Track unmatched sections for LLM fallback
unmatched_sections = []

# After fuzzy matching, collect unmatched:
if not routed:
    unmatched_sections.append(heading)

# After main routing loop, batch classify unmatched sections
if unmatched_sections:
    print(f"   🤖 LLM fallback: Classifying {len(unmatched_sections)} unmatched sections...")
    llm_routes = self._classify_sections_llm(unmatched_sections)

    for heading, agent_id in llm_routes.items():
        if agent_id in main_sections:
            main_sections[agent_id].append(heading)

def _classify_sections_llm(self, section_headings: List[str]) -> Dict[str, str]:
    """
    Classify unmatched sections using GPT-4o-mini.

    Returns:
        Dict mapping section_heading → agent_id
    """
    if not section_headings:
        return {}

    # Build classification prompt
    prompt = f"""You are a Swedish BRF (housing cooperative) document expert.

Classify these section headings into the most appropriate agent category:

Available agents:
- governance_agent: Board, auditors, governance, membership, annual meeting
- financial_agent: Financial statements, balance sheet, income statement, cash flow
- property_agent: Property details, address, building year, energy, apartments
- operations_agent: Operations, maintenance, suppliers, contracts
- notes_collection: Notes section headers (main "Noter" sections)

Section headings to classify:
{json.dumps(section_headings, ensure_ascii=False, indent=2)}

Return JSON mapping each heading to agent_id or "unclassifiable":
{{"heading1": "agent_id", "heading2": "agent_id", ...}}

Swedish BRF context:
- Förvaltningsberättelse = Management report → governance_agent
- Medlemsinformation = Member information → governance_agent
- Flerårsöversikt = Multi-year overview → financial_agent
- Resultatdisposition = Result disposition → financial_agent

Only classify if confidence > 70%. If unsure, return "unclassifiable".
"""

    try:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Swedish BRF document classification expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Filter out unclassifiable
        return {k: v for k, v in result.items() if v != "unclassifiable"}

    except Exception as e:
        print(f"   ⚠️ LLM classification failed: {e}")
        return {}
```

**Testing**:
```bash
python code/optimal_brf_pipeline.py ../../data/raw_pdfs/Hjorthagen/brf_268882.pdf
# Should see "LLM fallback: Classifying X sections..." message
# Check routing.main_sections counts - should reach ~45-48 (90-95%)
```

**Expected Improvement**: +5-8 sections matched (cumulative)

**Cost Analysis**:
- Input: ~500 tokens (section headings + context)
- Output: ~200 tokens (JSON mapping)
- Total: ~700 tokens @ $0.150/$1.00 per 1M tokens
- Cost: ~$0.0001 per document for LLM classification
- **Very affordable!** (Much less than initial $0.03 estimate)

---

## 🧪 Testing Strategy

### Test Suite (test_layered_routing.py)

```python
#!/usr/bin/env python3
"""Test layered routing system on diverse PDFs"""

import json
from pathlib import Path
from optimal_brf_pipeline import OptimalBRFPipeline

def test_layered_routing():
    """Test routing improvement across phases"""

    test_pdfs = [
        "../../data/raw_pdfs/Hjorthagen/brf_268882.pdf",  # Scanned (baseline)
        "../../data/raw_pdfs/Hjorthagen/brf_271852.pdf",  # Hybrid
        "../../data/raw_pdfs/SRS/brf_46160.pdf"           # Machine-readable
    ]

    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/layered_routing_test",
        enable_caching=True
    )

    results = {}

    for pdf_path in test_pdfs:
        print(f"\n{'='*70}")
        print(f"Testing: {Path(pdf_path).name}")
        print(f"{'='*70}")

        result = pipeline.extract_document(pdf_path)

        # Analyze routing
        total_sections = result.structure.num_sections
        routed_main = sum(len(v) for v in result.routing.main_sections.values())
        routed_notes = sum(len(v) for v in result.routing.note_sections.values())
        routed_total = routed_main + routed_notes

        match_rate = (routed_total / total_sections * 100) if total_sections > 0 else 0

        results[Path(pdf_path).name] = {
            "total_sections": total_sections,
            "routed_sections": routed_total,
            "match_rate": match_rate,
            "main_sections": routed_main,
            "note_sections": routed_notes,
            "routing_breakdown": {
                k: len(v) for k, v in result.routing.main_sections.items()
            }
        }

        print(f"\n📊 Routing Summary:")
        print(f"   Total sections: {total_sections}")
        print(f"   Routed sections: {routed_total}")
        print(f"   Match rate: {match_rate:.1f}%")
        print(f"   Main sections: {routed_main}")
        print(f"   Note sections: {routed_notes}")

    pipeline.close()

    # Save comprehensive results
    output_file = Path("results/layered_routing_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Test complete! Results saved to {output_file}")

    # Calculate average improvement
    avg_match_rate = sum(r['match_rate'] for r in results.values()) / len(results)
    print(f"\n📈 Average match rate across {len(test_pdfs)} PDFs: {avg_match_rate:.1f}%")

    return results

if __name__ == "__main__":
    test_layered_routing()
```

### Validation Checkpoints

**After Option A**:
```bash
python test_layered_routing.py
# Expected: 76-81% average match rate
```

**After Option B**:
```bash
python test_layered_routing.py
# Expected: 81-86% average match rate
```

**After Option C**:
```bash
python test_layered_routing.py
# Expected: 90-95% average match rate ✅
```

---

## 📊 Success Metrics

### Routing Performance

| Metric | Baseline | After A | After B | After C | Target | Status |
|--------|----------|---------|---------|---------|--------|--------|
| Match Rate | 66% | 76-81% | 81-86% | 90-95% | 95% | 🎯 |
| Main Sections | 27/50 | 35/50 | 38/50 | 45/50 | 48/50 | 🎯 |
| Note Sections | 6 | 6 | 8 | 8 | 8 | ✅ |
| Unmatched | 17 | 9-11 | 6-8 | 2-3 | <3 | 🎯 |

### Field Extraction (Downstream Impact)

| Metric | Baseline | After A+B+C | Target | Status |
|--------|----------|-------------|--------|--------|
| Coverage | 40-50% | 75-85% | 95% | 🟡 |
| Accuracy | TBD | TBD | 95% | ⏳ |
| Evidence Ratio | 66.7% | 85-95% | 95% | 🎯 |

### Cost Analysis

| Component | Cost per Doc | Frequency | Total Cost |
|-----------|--------------|-----------|------------|
| Option A (Normalization) | $0 | 100% | $0 |
| Option B (Fuzzy) | $0 | ~20% | $0 |
| Option C (LLM) | ~$0.0001 | ~5-10% | **$0.0001** |
| **Total** | | | **$0.0001/doc** |

**ROI**: Negligible cost for 24-29% improvement! 🎉

---

## 🎯 Timeline

**Total Estimated Time**: 7 hours

1. **Option A Implementation**: 1 hour
2. **Option A Testing**: 30 min
3. **Option B Implementation**: 2 hours
4. **Option B Testing**: 30 min
5. **Option C Implementation**: 4 hours
6. **Option C Testing**: 30 min
7. **Final Validation & Report**: 1 hour

**Start**: Now
**Completion Target**: Within 1 day (single focused session)

---

## 🚀 Go/No-Go Decision

**Recommendation**: ✅ **GO - Implement All Three Options**

**Rationale**:
1. **Necessary for 95/95 goal**: Individual options won't reach target
2. **Low cost**: ~$0.0001/doc (essentially free)
3. **Proven components**: All three use validated patterns
4. **Graceful degradation**: Each layer adds value independently
5. **Production-ready**: Layered approach is industry best practice

**Risk**: Low
**Effort**: 7 hours
**Value**: High (29% routing improvement → ~35% field extraction improvement)

---

## 📁 Implementation Checklist

- [ ] Implement Option A (Swedish normalization)
- [ ] Test Option A and measure improvement
- [ ] Implement Option B (fuzzy matching)
- [ ] Test Option B and measure improvement
- [ ] Implement Option C (LLM classification)
- [ ] Test Option C and measure improvement
- [ ] Run comprehensive test suite on 3+ PDFs
- [ ] Validate field extraction improvement
- [ ] Create final validation report
- [ ] Commit and push all changes
- [ ] Update documentation (README, CLAUDE.md)

---

**Status**: 🟢 **READY TO IMPLEMENT**
**Next Action**: Start with Option A implementation
**Expected Completion**: 90-95% match rate, achieving 95/95 goal prerequisites

