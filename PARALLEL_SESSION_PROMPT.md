# Gracian Pipeline - Parallel Experimentation Session

**Use this prompt to start a new Claude Code session for experimenting with pipeline tools**

---

## 🎯 Quick Context

I'm working on the **Gracian Pipeline** - a multi-agent extraction system for Swedish BRF (housing cooperative) annual reports.

**Location**: `/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/`

**Goal**: Achieve 95/95 accuracy (95% coverage, ±5% financial accuracy) through:
- 24 specialized extraction agents (governance, financial, property, notes, etc.)
- GPT-5 orchestration with 5-round iterative coaching
- Multi-modal vision processing (Qwen 2.5-VL, Gemini 2.5-Pro, GPT-5 Vision)

---

## 📋 Your Task: Pipeline Tool Experimentation

I want to experiment with **new tools and approaches** for the extraction pipeline. Current focus areas:

### 🔧 Potential Experiments

1. **Vision Model Testing**:
   - Compare Qwen 2.5-VL vs Gemini 2.5-Pro on scanned PDFs
   - Test different DPI settings (current: 220)
   - Evaluate OCR alternatives (EasyOCR, Tesseract, Mistral Pixtral)

2. **Agent Prompt Engineering**:
   - Test different prompt formats for Swedish text extraction
   - Experiment with few-shot examples vs zero-shot
   - Compare JSON schema enforcement strategies

3. **Sectioning Improvements**:
   - Test LLM-based sectioning vs heuristic anchor matching
   - Evaluate hierarchical section detection
   - Benchmark speed vs accuracy tradeoffs

4. **Coaching System Optimization**:
   - Test different scoring thresholds
   - Experiment with adaptive coaching strategies
   - Evaluate early termination conditions

---

## 📂 Key Files to Review First

**CRITICAL - Read These First**:
```bash
# 1. Quick reference and corpus locations
cat CLAUDE.md

# 2. Project architecture
cat PROJECT_INDEX.json | jq '.f | keys'

# 3. Current agent prompts (13 implemented, 11 missing)
cat gracian_pipeline/prompts/agent_prompts.py

# 4. PDF topology analysis results
cat PDF_TOPOLOGY_REPORT.md
```

**For Experiments**:
- `gracian_pipeline/core/vision_qc.py` - Vision model integration
- `gracian_pipeline/core/orchestrator.py` - Coaching loop
- `gracian_pipeline/core/vision_sectionizer.py` - Document sectioning
- `gracian_pipeline/core/schema.py` - Agent schemas (13 agents defined)

---

## 🗄️ Test Data Available

**Small Test Set** (15 PDFs):
```bash
data/raw_pdfs/Hjorthagen/brf_46160.pdf  # Known good test document
```

**Large Corpus** (89,955 PDFs, 194GB):
- **Årsredovisning**: 26,342 PDFs (91GB) - `~/Dropbox/zeldadb/zeldabot/pdf_docs/Årsredovisning/`
- **Stadgar**: ~27,000 PDFs (75GB)
- **Ekonomisk plan**: ~6,500 PDFs (18GB)
- **Energideklaration**: ~3,500 PDFs (9.8GB)

**PDF Distribution** (from topology analysis):
- 48.4% Machine-readable (text extraction)
- 49.3% Scanned/Image (vision LLMs required)
- 2.3% Hybrid (mixed approach)

---

## 🚀 Quick Start Commands

### Run Single Agent Test
```bash
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline"

export VERBOSE_VISION=true
python -c "
from gracian_pipeline.core.vision_qc import vision_qc_agent
result, meta = vision_qc_agent(
    'data/raw_pdfs/Hjorthagen/brf_46160.pdf',
    'governance_agent',
    'Extract chairman and board members from Swedish BRF report'
)
print(f'Result: {result}')
print(f'Meta: {meta}')
"
```

### Run Orchestrated Extraction (5-round coaching)
```bash
bash run_orchestrated.sh ./data/raw_pdfs/Hjorthagen 1
```

### Test Vision Sectioning
```bash
python -c "
from gracian_pipeline.core.vision_sectionizer import vision_sectionize
sections = vision_sectionize('data/raw_pdfs/Hjorthagen/brf_46160.pdf')
import json
print(json.dumps(sections, indent=2, ensure_ascii=False))
"
```

---

## 🎯 Experiment Workflow

### 1. Choose Your Experiment
Pick ONE focus area from the list above.

### 2. Create Test Script
```bash
# Create a new experiment script
touch experiments/test_your_feature.py
```

### 3. Run on Small Sample
Test on `brf_46160.pdf` first before scaling up.

### 4. Document Results
```bash
# Create experiment report
cat > experiments/YOUR_EXPERIMENT_RESULTS.md <<'EOF'
# Experiment: [Name]
Date: $(date)
Hypothesis: ...
Results: ...
Conclusion: ...
EOF
```

### 5. Share Findings
Commit interesting results to the repository.

---

## 📊 Current System Status

**Extraction Performance** (as of 2025-10-06):
- Overall Coverage: **15.4%** (Target: 95%) 🔴
- Numeric QC Pass: **0%** (Target: 95%) 🔴
- Evidence Ratio: **15.4%** (Target: 95%) 🔴
- Governance Coverage: **80%** (Target: 95%) 🟡
- Section Detection: **100%** (Target: 95%) 🟢

**Agents Status**:
- Implemented: 13/24 agents
- Missing: 11 agents (need prompts added)

**Infrastructure**:
- Git repository: https://github.com/hshahrokni2/gracian-pipeline
- Latest commit: `bddaf95` (Mass scanning infrastructure)
- Total code: 2,019 lines core + 414 lines scanning

**Background Tasks Running**:
- Mass PDF scanning (26,342 Årsredovisning corpus) - check with `tail -f mass_scan.log`

---

## 🔑 API Keys Required (in .env)

```bash
XAI_API_KEY=xai-...                    # Grok (text extraction)
OPENAI_API_KEY=sk-proj-...             # GPT-5 (orchestration)
GEMINI_API_KEY=AIzaSy...               # Gemini 2.5-Pro (benchmarking)
OPENROUTER_API_KEY=sk-or-v1-...        # Qwen 3-VL (vision sectioning)
```

---

## 🚫 Important Notes

**DO NOT**:
- Modify existing agent prompts without testing first
- Run mass extraction on full corpus (use small samples)
- Commit API keys or PDFs to git
- Interrupt the background mass scanning process

**DO**:
- Test on small samples first (1-5 PDFs)
- Document all experiments with results
- Update PROJECT_INDEX.json after significant changes:
  ```bash
  python3 ~/.claude-code-project-index/scripts/project_index.py
  ```
- Check CLAUDE.md for latest instructions and corpus locations

---

## 💡 Suggested Experiments to Start With

### Easy (1-2 hours):
1. **Test different DPI settings** - Compare 150, 220, 300 DPI on 5 scanned PDFs
2. **Add missing agent prompts** - Implement 1-2 of the 11 missing agents
3. **Swedish number parsing** - Test regex patterns for Swedish financial numbers

### Medium (2-4 hours):
4. **Vision model comparison** - Run same PDF through Qwen, Gemini, GPT-5 Vision
5. **Prompt engineering** - Test 3-5 prompt variations for governance agent
6. **Sectioning accuracy** - Compare LLM vs heuristic sectioning on 10 PDFs

### Advanced (4-8 hours):
7. **Coaching optimization** - Test adaptive vs fixed coaching strategies
8. **Multi-modal fusion** - Combine text + vision extraction intelligently
9. **H100 deployment** - Set up pipeline on H100 GPU infrastructure

---

## 📚 Additional Resources

- **Swedish BRF Terms**: See `.grok/GROK.md` (NLP_DICT)
- **Multi-modal Prompting**: See `agent_prompts.py` examples
- **Quality Scoring**: See `bench.py` heuristic scoring
- **Related Systems**: ZeldaDemo (`~/Dropbox/Zelda/ZeldaDemo/`) - Production system with H100 + PostgreSQL

---

## 🎓 Example Experiment: Testing OCR Alternatives

```python
# experiments/test_ocr_comparison.py
import fitz
from PIL import Image
import io
import easyocr  # pip install easyocr

def compare_ocr_methods(pdf_path, page_num=0):
    """Compare PyMuPDF text extraction vs EasyOCR"""

    # Method 1: PyMuPDF direct text
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pymupdf_text = page.get_text("text")

    # Method 2: EasyOCR on rendered image
    pix = page.get_pixmap(dpi=220)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    reader = easyocr.Reader(['sv', 'en'])  # Swedish + English
    ocr_results = reader.readtext(img)
    easyocr_text = "\n".join([text for (_, text, _) in ocr_results])

    # Compare
    print(f"PyMuPDF chars: {len(pymupdf_text)}")
    print(f"EasyOCR chars: {len(easyocr_text)}")
    print(f"\n--- PyMuPDF Sample ---\n{pymupdf_text[:500]}")
    print(f"\n--- EasyOCR Sample ---\n{easyocr_text[:500]}")

    doc.close()
    return pymupdf_text, easyocr_text

# Run test
pdf = "data/raw_pdfs/Hjorthagen/brf_46160.pdf"
pymupdf, easyocr = compare_ocr_methods(pdf)
```

---

**Ready to experiment? Start by reading CLAUDE.md and PROJECT_INDEX.json, then pick an experiment from the list above!**

**GitHub**: https://github.com/hshahrokni2/gracian-pipeline
**Status**: Foundation complete, extraction quality needs improvement (15.4% → 95% target)
