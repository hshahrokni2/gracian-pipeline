# Gracian Pipeline - Claude Code Quick Reference

## 🚀 Quick Start (First Thing After Context Loss)

```
Please read @PROJECT_INDEX.json to understand the codebase architecture
```

---

## 📋 Project Overview

**Gracian Pipeline** is a Grok-centric multi-agent extraction system for Swedish BRF (housing cooperative) annual reports. It achieves 95/95 accuracy through:
- 24 specialized extraction agents (governance, financial, property, etc.)
- Iterative coaching system (5 rounds with GPT-5)
- Multi-modal vision processing (text + images)
- Multi-model benchmarking (Grok, GPT-5, Gemini, Qwen)

**Current Status**: 🚧 Foundation complete (2,019 lines core code), extraction quality needs improvement (15.4% coverage vs 95% target)

---

## 📍 Key Files & Locations

### Core Architecture
- **Entry Point**: `run_gracian.py` (592 lines)
- **Orchestrator**: `gracian_pipeline/core/orchestrator.py` (335 lines)
- **Vision Sectionizer**: `gracian_pipeline/core/vision_sectionizer.py` (13KB)
- **Vision QC**: `gracian_pipeline/core/vision_qc.py` (19KB)
- **Agent Prompts**: `gracian_pipeline/prompts/agent_prompts.py` (24 agents, 13 implemented)

### Configuration
- **Environment**: `.env` (74 lines, DO NOT commit - contains API keys)
- **Example**: `.env.example` (template for new users)
- **Shell Runner**: `run_orchestrated.sh` (orchestrated mode with GPT-5)

### Documentation
- **Main Docs**: `README.md` (comprehensive project documentation)
- **Grok Config**: `.grok/GROK.md` (Grok-specific customization)
- **Project Index**: `PROJECT_INDEX.json` (auto-generated code map)
- **This File**: `CLAUDE.md` (you are here)

### Data & Outputs
- **Test PDFs**: `data/raw_pdfs/Hjorthagen/` (15 BRF PDFs), `data/raw_pdfs/SRS/` (28 BRF PDFs)
- **Results**: `data/raw_pdfs/extraction_results.json`
- **Coaching Logs**: `data/raw_pdfs/outputs/coach_history/coach_log.jsonl`
- **Sections**: `data/raw_pdfs/outputs/sections/*.json`

---

## 🛠️ Common Commands

### Before Starting Work
```bash
# Always check project index for architectural awareness
cat PROJECT_INDEX.json | jq '.functions[] | select(.name == "your_function")'

# Update index after significant changes
python3 ~/.claude-code-project-index/scripts/project_index.py
```

### Running Extractions

**Orchestrated Mode** (Highest Quality):
```bash
bash run_orchestrated.sh ./data/raw_pdfs 1
```

**Quick Test** (Single Agent):
```bash
export VERBOSE_VISION=true
python -c "
from gracian_pipeline.core.vision_qc import vision_qc_agent
result, meta = vision_qc_agent(
    'data/raw_pdfs/Hjorthagen/brf_46160.pdf',
    'governance_agent',
    'Extract chairman and board members from Swedish BRF report'
)
print(result)
"
```

**Custom Modes**:
```bash
# One-shot (fast, no coaching)
export ONESHOT=true ORCHESTRATE=false
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1

# Hybrid (selective coaching)
export HYBRID_MODE=true ORCHESTRATOR_TARGET_SCORE=95
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1

# Vision-only (for scanned docs)
export AUTO_VISION_IF_LOW_TEXT=true
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```

### Debugging

**Enable Verbose Logging**:
```bash
export VERBOSE_ORCHESTRATOR=true
export VERBOSE_SECTIONIZER=true
export VERBOSE_VISION=true
export COACH_HISTORY_PATH=data/raw_pdfs/outputs/coach_history/coach_log.jsonl
```

**Check Coaching History**:
```bash
tail -f data/raw_pdfs/outputs/coach_history/coach_log.jsonl | jq '.'
```

**Analyze Results**:
```bash
cat data/raw_pdfs/outputs/summary.json | jq '.["data/raw_pdfs/Hjorthagen/brf_46160.pdf"]'
```

---

## 🏗️ Architecture Quick Reference

### Module Hierarchy

```
run_gracian.py (CLI entry)
    ↓
gracian_pipeline/core/orchestrator.py (coordination)
    ↓
    ├→ vision_sectionizer.py (document structure)
    ├→ vision_qc.py (multimodal extraction)
    ├→ bench.py (model comparison)
    ├→ schema.py (field definitions)
    ├→ enforce.py (validation)
    └→ qc.py (numeric checks)
         ↓
gracian_pipeline/prompts/agent_prompts.py (24 agents)
```

### Key Functions (From PROJECT_INDEX.json)

**Orchestration**:
- `orchestrate_pdf()` - Main coaching loop (orchestrator.py:141)
- `_coach_sectionizer_once()` - Refine page assignments (orchestrator.py:32)
- `_coach_agent_once()` - Improve agent extraction (orchestrator.py:74)

**Vision Processing**:
- `vision_sectionize()` - Detect document sections (vision_sectionizer.py)
- `vision_qc_agent()` - Extract with quality control (vision_qc.py)
- `render_pdf_pages_subset()` - Convert pages to images (vision_qc.py)

**Quality Control**:
- `score_output()` - Heuristic scoring (bench.py)
- `numeric_qc()` - Validate financial fields (qc.py)
- `enforce()` - Schema enforcement (enforce.py)

### Agent Schema (EXPECTED_TYPES)

**Governance Agent**:
```python
{
    "chairman": "str",
    "board_members": "list",
    "auditor_name": "str",
    "audit_firm": "str",
    "nomination_committee": "list",
    "evidence_pages": "list"
}
```

**Financial Agent**:
```python
{
    "revenue": "num",
    "expenses": "num",
    "assets": "num",
    "liabilities": "num",
    "equity": "num",
    "surplus": "num",
    "evidence_pages": "list"
}
```

*(See `gracian_pipeline/core/schema.py:7-93` for all 13 agent schemas)*

---

## 🎯 Current Focus Areas

### P0 - Critical Issues (Fix First)
1. **Low Extraction Coverage** (15.4% vs 95% target)
   - Symptom: Most agents return 0% coverage
   - Files to check: `vision_qc.py`, `agent_prompts.py`
   - Possible causes: Vision model prompts, PDF rendering quality, Swedish encoding

2. **Missing Agent Prompts** (11/24 agents missing)
   - Location: `gracian_pipeline/prompts/agent_prompts.py:43-61`
   - Need to add: 11 more agents following existing format (87-120 words, Swedish-focused, multimodal)

3. **No Ground Truth Validation**
   - Create: Ground truth for 1-2 test documents
   - Implement: Sjöstaden-2 style canary tests
   - Target: 95/95 accuracy verification

### P1 - Short-term Improvements
- Run full test suite on SRS (28 PDFs) and Hjorthagen (15 PDFs)
- Add PostgreSQL persistence layer (like ZeldaDemo system)
- Implement receipts/artifacts system for auditability

### P2 - Medium-term Goals
- Deploy to H100 infrastructure (see parent ZeldaDemo for reference)
- Optimize API costs via caching
- Add preflight checks and acceptance gates

---

## 📊 Key Metrics & Targets

### 95/95 Goal
- **Coverage**: Σ(extracted_fields) / Σ(required_fields) ≥ 0.95
- **Accuracy**: ±5% on financials, verbatim Swedish names
- **Evidence**: 95% of extractions must cite source pages

### Current Performance (brf_46160.pdf)
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Overall Coverage | 95% | 15.4% | 🔴 |
| Numeric QC Pass | 95% | 0% | 🔴 |
| Evidence Ratio | 95% | 15.4% | 🔴 |
| Governance Coverage | 95% | 80% | 🟡 |
| Section Detection | 95% | 100% | 🟢 |

---

## 🔑 API Keys & Environment

### Required APIs (from .env)
```bash
XAI_API_KEY=xai-...                    # Grok (text extraction)
OPENAI_API_KEY=sk-proj-...             # GPT-5 (orchestration)
GEMINI_API_KEY=AIzaSy...               # Gemini 2.5-Pro (benchmarking)
OPENROUTER_API_KEY=sk-or-v1-...        # Qwen 3-VL (vision sectioning)
```

### Critical Settings
```bash
# Orchestrator
ORCHESTRATE=true
ORCHESTRATOR_MAX_ROUNDS=5
ORCHESTRATOR_TARGET_SCORE=95
ORCHESTRATOR_CONCURRENCY=3

# Vision
VISION_PAGES_PER_CALL=10
QC_PAGE_RENDER_DPI=220
PASS_PAGE_LABELS=true

# Quality
ENFORCE_VERIFICATION=strict
STRICT_NEEDS_EVIDENCE=true
```

---

## 🚫 What NOT to Do

1. **DO NOT** commit `.env` file (contains API keys)
2. **DO NOT** commit large PDFs to git (use .gitignore)
3. **DO NOT** modify agent prompts without checking PROJECT_INDEX.json structure
4. **DO NOT** change schema without updating `enforce.py` and `bench.py`
5. **DO NOT** skip updating PROJECT_INDEX.json after major changes:
   ```bash
   python3 ~/.claude-code-project-index/scripts/project_index.py
   ```

---

## 🔄 Development Workflow

### Making Changes
1. **Before coding**: Check @PROJECT_INDEX.json for existing functions
2. **During coding**: Follow Swedish-specific patterns (see `.grok/GROK.md`)
3. **After coding**: Update PROJECT_INDEX.json, test with single document
4. **Before commit**: Run preflight checks, update this CLAUDE.md

### Testing New Agents
```bash
# 1. Add agent prompt to agent_prompts.py
# 2. Add schema to schema.py EXPECTED_TYPES
# 3. Test single agent
export VERBOSE_VISION=true
python -c "
from gracian_pipeline.core.vision_qc import vision_qc_agent
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS
from gracian_pipeline.core.schema import schema_prompt_block

agent_id = 'your_new_agent'
prompt = AGENT_PROMPTS[agent_id] + '\n\n' + schema_prompt_block(agent_id)
result, meta = vision_qc_agent(
    'data/raw_pdfs/Hjorthagen/brf_46160.pdf',
    agent_id,
    prompt
)
print(f'Result: {result}')
print(f'Meta: {meta}')
"

# 4. Run full orchestration
bash run_orchestrated.sh ./data/raw_pdfs/Hjorthagen 1
```

---

## 📚 Related Systems

### ZeldaDemo (Parent System)
- **Location**: `~/Dropbox/Zelda/ZeldaDemo/`
- **Architecture**: Qwen 2.5-VL on H100, Gemini twin-agent, PostgreSQL
- **Key Difference**: Production-ready with database persistence, receipts system

### Potential Merge
- Use Gracian's GPT-5 orchestration + ZeldaDemo's H100 performance
- Adopt ZeldaDemo's PostgreSQL schema and acceptance gates
- Keep Gracian's multi-model benchmarking system

---

## 🐛 Troubleshooting Guide

### Problem: Low Extraction Coverage
```bash
# Increase DPI
export QC_PAGE_RENDER_DPI=250

# Test vision model directly
python -c "
from gracian_pipeline.core.vision_qc import call_openai_responses_vision, render_pdf_pages_subset
pages = render_pdf_pages_subset('data/raw_pdfs/Hjorthagen/brf_46160.pdf', [0,1,2], dpi=220)
result = call_openai_responses_vision('Extract all text from these pages', pages, page_labels=['Page 1', 'Page 2', 'Page 3'])
print(result)
"
```

### Problem: API Rate Limiting
```bash
export ORCHESTRATOR_CONCURRENCY=1
export SECTIONIZER_PACE_MS=1000
export GEMINI_PACING_MS=800
```

### Problem: Import Errors
```bash
# Always use absolute imports from gracian_pipeline/
from gracian_pipeline.core.orchestrator import orchestrate_pdf
from gracian_pipeline.prompts.agent_prompts import AGENT_PROMPTS
```

---

## 📈 Success Criteria (When Feature is "Done")

✅ **Extraction Quality**:
- Overall coverage ≥95%
- Numeric QC pass rate ≥95%
- Evidence ratio ≥95%

✅ **Test Coverage**:
- Tested on all 43 PDFs (15 Hjorthagen + 28 SRS)
- Ground truth validation passing
- Canary tests implemented

✅ **Production Readiness**:
- PostgreSQL persistence working
- Receipts/artifacts system operational
- Preflight checks passing
- H100 deployment successful

---

## 🎓 Learning Resources

- **Swedish BRF Terms**: See `.grok/GROK.md` line 26-27 (NLP_DICT)
- **Multi-modal Prompting**: See `agent_prompts.py` examples (lines 6-46)
- **Coaching Algorithm**: See `orchestrator.py:141-334`
- **Quality Scoring**: See `bench.py:50-180`

---

## 📝 Update History

| Date | Change | Updated By |
|------|--------|------------|
| 2025-10-06 | Initial CLAUDE.md creation with PROJECT_INDEX.json integration | Claude Code |

---

**Remember**: Always check @PROJECT_INDEX.json before adding new code to avoid duplication and ensure proper architecture!
