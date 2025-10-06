# Gracian Pipeline

**Grok-Centric Multi-Agent BRF Extraction System**

A sophisticated orchestrated extraction pipeline for Swedish BRF (Bostadsrättsförening - housing cooperative) annual reports and economic plans. Uses multimodal LLM agents with iterative coaching to extract structured data from complex PDF documents.

## 🎯 Overview

Gracian Pipeline is designed to achieve **95/95 accuracy** (95% coverage, ±5% financial accuracy) for Swedish BRF document extraction through:
- **24 specialized extraction agents** (governance, financial, property, notes, etc.)
- **Multi-modal vision processing** (text + images for tables and scanned documents)
- **Iterative coaching system** (up to 5 rounds with GPT-5 orchestrator)
- **Multi-model benchmarking** (Grok, GPT-5, Gemini 2.5-Pro, Qwen 3-VL)
- **Intelligent document sectioning** (vision-based hierarchical structure detection)

---

## 🏗️ Architecture

### Core Components

**Orchestrator** (`gracian_pipeline/core/orchestrator.py`)
- Coordinates multi-agent extraction workflow
- Implements 5-round coaching loop for quality improvement
- Manages page allocation and agent scheduling
- Concurrent processing with configurable workers

**Vision Sectionizer** (`gracian_pipeline/core/vision_sectionizer.py`)
- Analyzes document structure using vision models
- Detects hierarchical sections (Förvaltningsberättelse, Resultaträkning, Noter, etc.)
- Maps sections to appropriate extraction agents
- Supports chunked processing (6-10 pages per API call)

**24 Specialized Agents** (`gracian_pipeline/prompts/agent_prompts.py`)
1. `governance_agent` - Board, chairman, auditors, nomination committee
2. `financial_agent` - Revenue, expenses, assets, liabilities, equity
3. `property_agent` - Designation, address, built year, energy class
4. `notes_depreciation_agent` - Depreciation methods and useful life
5. `notes_maintenance_agent` - Maintenance plans and budgets
6. `notes_tax_agent` - Tax policies and obligations
7. `events_agent` - Key events and annual meeting dates
8. `audit_agent` - Audit opinions and clean opinion status
9. `loans_agent` - Outstanding loans, interest rates, amortization
10. `reserves_agent` - Reserve funds and monthly fees
11. `energy_agent` - Energy class, performance, inspection dates
12. `fees_agent` - Monthly fees, planned changes, fee policies
13. `cashflow_agent` - Cash flow analysis
... (11 more agents to be implemented)

**Quality Control** (`gracian_pipeline/core/`)
- `vision_qc.py` - Vision-based quality control and extraction
- `qc.py` - Numeric validation and quality checks
- `enforce.py` - Schema enforcement and field verification
- `bench.py` - Multi-model benchmarking and scoring

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- API Keys for:
  - **xAI (Grok)**: Required for text extraction
  - **OpenAI (GPT-5)**: Required for orchestration and coaching
  - **Google (Gemini 2.5-Pro)**: Optional for benchmarking
  - **OpenRouter (Qwen 3-VL)**: Optional for vision sectioning

### Setup

```bash
# Clone the repository
git clone https://github.com/hshahrokni2/gracian-pipeline.git
cd gracian-pipeline

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Required Python Packages
```
openai>=1.0.0
google-generativeai>=0.3.0
PyMuPDF>=1.23.0
pdfplumber>=0.10.0
Pillow>=10.0.0
python-dotenv>=1.0.0
```

---

## 🚀 Usage

### Basic Extraction

```bash
# Orchestrated mode (recommended) - iterative coaching with GPT-5
bash run_orchestrated.sh ./data/raw_pdfs 1

# Or manually with Python
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```

### Modes

**1. Orchestrated Mode** (Default - Highest Quality)
```bash
export ORCHESTRATE=true
export ORCHESTRATOR_MAX_ROUNDS=5
export ORCHESTRATOR_TARGET_SCORE=95
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```

Features:
- Vision-based document sectioning
- GPT-5 coaches sectionizer to refine page assignments
- Each agent extracts with quality scoring
- Iterative coaching until score ≥95 or 5 rounds complete
- Automatic acceptance on coach approval

**2. One-Shot Mode** (Fast - Single Pass)
```bash
export ONESHOT=true
export ORCHESTRATE=false
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```

**3. Hybrid Mode** (Balanced - Selective Coaching)
```bash
export HYBRID_MODE=true
export ORCHESTRATOR_TARGET_SCORE=95
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```
- Runs one-shot extraction first
- Only orchestrates agents with score < 95
- Faster than full orchestration

**4. Vision-Only Mode** (Auto-detected for Scanned Documents)
```bash
export AUTO_VISION_IF_LOW_TEXT=true
python run_gracian.py --input-dir ./data/raw_pdfs --batch-size 1
```
- Automatically detected when >60% of pages have <500 chars
- Forces vision-based extraction for all agents

### Advanced Configuration

See `.env` for all configuration options:

```bash
# Model Selection
XAI_MODEL=grok-4-fast-reasoning-latest
OPENAI_MODEL=gpt-5
GEMINI_MODEL=gemini-2.5-pro
OPENROUTER_QWEN_MODEL=qwen/qwen3-vl-235b-a22b-instruct

# Performance Tuning
ORCHESTRATOR_CONCURRENCY=3          # Parallel agent processing
VISION_PAGES_PER_CALL=10           # Pages per vision API call
QC_PAGE_RENDER_DPI=220             # Image quality (200-220 recommended)
SECTIONIZER_PACE_MS=500            # Rate limiting delay

# Quality Control
ENFORCE_VERIFICATION=strict         # Schema validation mode
STRICT_NEEDS_EVIDENCE=true         # Require evidence_pages field
ORCHESTRATOR_TARGET_SCORE=95       # Acceptance threshold
```

---

## 📊 Output Format

### Extraction Results

```json
{
  "data/raw_pdfs/Hjorthagen/brf_46160.pdf": {
    "governance_agent": {
      "chairman": "Per Andersson",
      "board_members": ["Anna Svensson", "Karl Johansson"],
      "auditor_name": "Maria Berg",
      "audit_firm": "BRF Revision AB",
      "nomination_committee": ["Erik Larsson"],
      "evidence_pages": [3, 4]
    },
    "financial_agent": {
      "revenue": 1234567,
      "expenses": 987654,
      "assets": 5000000,
      "liabilities": 2000000,
      "equity": 3000000,
      "surplus": 246913,
      "evidence_pages": [8, 9, 10]
    },
    "_qc": {
      "governance_agent": {
        "rounds": [
          {
            "round": 1,
            "pages": [2, 3, 4, 5],
            "score": 85.0,
            "numeric_qc": {"passed": false},
            "verified_fields": ["chairman", "board_members"]
          }
        ],
        "coaching": [
          {
            "round": 1,
            "advice": {
              "ok": true,
              "revised_pages": [3, 4],
              "hints": "Focus on pages 3-4 for governance data"
            }
          }
        ]
      }
    }
  }
}
```

### Coaching History (JSONL)

```jsonl
{"pdf": "data/raw_pdfs/brf_46160.pdf", "agent": "governance_agent", "round": 1, "pages": [2, 3, 4, 5], "score": 85.0, "prompt_hash": "a3f2c1b..."}
{"pdf": "data/raw_pdfs/brf_46160.pdf", "agent": "governance_agent", "round": 2, "pages": [3, 4], "score": 92.5, "prompt_hash": "a3f2c1b..."}
```

Location: `data/raw_pdfs/outputs/coach_history/coach_log.jsonl`

---

## 📁 Project Structure

```
gracian-pipeline/
├── gracian_pipeline/
│   ├── core/                          # Core extraction logic (2,019 lines)
│   │   ├── orchestrator.py           # Coaching loop and coordination
│   │   ├── vision_sectionizer.py     # Document structure detection
│   │   ├── vision_qc.py              # Multimodal extraction
│   │   ├── bench.py                  # Model comparison
│   │   ├── sectionizer.py            # Text-based sectioning fallback
│   │   ├── schema.py                 # Schema definitions
│   │   ├── enforce.py                # Schema enforcement
│   │   ├── qc.py                     # Numeric quality control
│   │   ├── oneshot.py                # Single-pass extraction
│   │   └── vertex.py                 # Google Vertex AI integration
│   ├── prompts/
│   │   └── agent_prompts.py          # 24 agent system prompts
│   └── data/
│       └── raw_pdfs/                 # Test documents
│           ├── Hjorthagen/           # 15 BRF PDFs
│           ├── SRS/                  # 28 BRF PDFs
│           └── outputs/              # Extraction results
│               ├── sections/         # Sectionizer outputs
│               ├── coach_history/    # Coaching logs
│               └── agent_debug/      # Per-agent diagnostics
├── run_gracian.py                    # CLI entry point
├── run_orchestrated.sh               # Orchestrated mode runner
├── .env                              # Configuration
├── PROJECT_INDEX.json                # Code intelligence index
└── README.md                         # This file
```

---

## 🎯 Quality Targets

### 95/95 Accuracy Goal

**Coverage** (≥95% of required fields extracted):
```
Σ(extracted_fields) / Σ(required_fields) ≥ 0.95
```

**Accuracy** (±5% on financials, verbatim Swedish names):
- Financial numbers: ±5% tolerance
- Swedish names: Exact match after normalization
- Dates: ISO 8601 format
- Boolean fields: 100% accuracy

### Current Status (Test Run)
| Metric | Target | Current |
|--------|--------|---------|
| Overall Coverage | 95% | 15.4% ⚠️ |
| Numeric QC Pass Rate | 95% | 0% ⚠️ |
| Evidence Ratio | 95% | 15.4% ⚠️ |
| Governance Coverage | 95% | 80% ⚠️ |
| Financial Coverage | 95% | 0% ⚠️ |

**Status**: 🚧 Foundation complete, extraction quality needs improvement

---

## 🔧 Troubleshooting

### Low Extraction Coverage

**Symptom**: Most agents return 0% coverage
**Likely Causes**:
1. Vision model not extracting data despite correct pages
2. Swedish character encoding issues
3. PDF rendering quality too low
4. Prompt engineering needs refinement

**Solutions**:
```bash
# Increase image quality
export QC_PAGE_RENDER_DPI=250

# Enable verbose logging
export VERBOSE_ORCHESTRATOR=true
export VERBOSE_SECTIONIZER=true
export VERBOSE_VISION=true

# Test single agent
python -c "from gracian_pipeline.core.vision_qc import vision_qc_agent; \
  print(vision_qc_agent('data/raw_pdfs/Hjorthagen/brf_46160.pdf', 'governance_agent', \
  'Extract chairman and board members from Swedish BRF report'))"
```

### API Rate Limiting

```bash
# Reduce concurrency
export ORCHESTRATOR_CONCURRENCY=1

# Increase pacing delays
export SECTIONIZER_PACE_MS=1000
export GEMINI_PACING_MS=800
```

### Memory Issues

```bash
# Reduce pages per call
export VISION_PAGES_PER_CALL=6
export SECTIONIZER_PAGES_PER_CALL=4

# Lower DPI
export QC_PAGE_RENDER_DPI=150
```

---

## 🛣️ Roadmap

### Immediate Priorities (P0)
- [ ] Fix extraction coverage (debug vision models)
- [ ] Complete remaining 11 agent prompts
- [ ] Establish ground truth validation suite

### Short-term (P1)
- [ ] Run full test suite on SRS (28 PDFs) and Hjorthagen (15 PDFs)
- [ ] Implement Sjöstaden-2 style canary tests
- [ ] Add PostgreSQL persistence layer

### Medium-term (P2)
- [ ] Deploy to H100 infrastructure
- [ ] Implement receipts/artifacts system
- [ ] Add preflight checks and acceptance gates
- [ ] Optimize API costs via caching

### Long-term (P3)
- [ ] Support additional document types (energy declarations, bylaws)
- [ ] Multi-language support (Norwegian, Danish)
- [ ] Web UI for document upload and monitoring

---

## 📚 Documentation

- **GROK.md**: Grok-specific customization guide (`.grok/GROK.md`)
- **PROJECT_INDEX.json**: Code intelligence index for Claude Code
- **Coach History**: JSONL logs at `data/raw_pdfs/outputs/coach_history/coach_log.jsonl`

---

## 🤝 Contributing

This is a research project. For questions or collaboration:
- **Author**: Hossein Shahrokni
- **Email**: hosseins@kth.se
- **Institution**: KTH Royal Institute of Technology

---

## 📄 License

[To be determined]

---

## 🙏 Acknowledgments

- Built with Grok (xAI), GPT-5 (OpenAI), Gemini 2.5-Pro (Google), and Qwen 3-VL
- Swedish BRF domain expertise from industry partners
- Project indexing via [claude-code-project-index](https://github.com/ericbuess/claude-code-project-index)

---

## 📊 Performance Benchmarks

### Test Document: brf_46160.pdf (Hjorthagen)

**Orchestrated Mode** (5 rounds, GPT-5 coaching):
- Total processing time: ~3-5 minutes
- Agents processed: 13/24
- Section detection: 100% (6 main sections identified)
- Average score improvement: 15-25% per coaching round
- API calls: ~25-40 (depending on convergence)

**One-Shot Mode**:
- Total processing time: ~30-60 seconds
- Agents processed: 13/24
- No iterative improvement
- API calls: 13-24 (one per agent)

---

**Last Updated**: 2025-10-06
**Version**: 0.1.0-alpha
