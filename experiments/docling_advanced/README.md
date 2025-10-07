# Docling Advanced Experiments

**Status**: Ready for parallel experimentation
**Created**: 2025-10-07
**Purpose**: Test advanced Docling features on scanned Swedish BRF PDFs

## 🚀 Quick Start for Parallel Agent

```bash
# 1. Navigate to workspace
cd "/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/experiments/docling_advanced"

# 2. Read the main guide
cat ../../PARALLEL_DOCLING_EXPERIMENTS.md

# 3. Run your first experiment (OCR comparison)
# Create code/test_ocr_engines.py from guide, then:
python code/test_ocr_engines.py > logs/ocr_test_$(date +%Y%m%d_%H%M%S).log 2>&1

# 4. Check results
ls -lh results/
cat results/*.json | jq '.'
```

## 📁 What's Here

```
experiments/docling_advanced/
├── README.md (this file)
├── test_pdfs/
│   ├── brf_268882.pdf (21 pages, scanned, small)
│   ├── brf_271852.pdf (15 pages, scanned, small)
│   └── brf_276507.pdf (52 pages, scanned, medium)
├── code/ (create experiment scripts here)
├── results/ (JSON outputs go here)
└── logs/ (execution logs go here)
```

## 🧪 Available Experiments

1. **OCR Engine Comparison**: Which engine (EasyOCR, Tesseract, etc.) works best for Swedish?
2. **Table Extraction Quality**: How well does Docling extract financial tables from scans?
3. **Layout Analysis**: Does it correctly identify document structure (headers, sections)?

**Full instructions**: See `../../PARALLEL_DOCLING_EXPERIMENTS.md`

## 🎯 Your Mission

Find the **best Docling configuration** for scanned Swedish BRF documents:
- Fastest OCR engine without sacrificing accuracy
- Best table extraction settings
- Optimal pipeline parameters

**Report findings** in `FINDINGS.md` when done!

## ⚠️ Rules

1. ✅ Work only in this directory
2. ✅ Use test_pdfs/ PDFs (don't touch main corpus)
3. ✅ Log everything to logs/
4. ✅ Safe to run while main Week 3 testing runs
5. ❌ Don't modify main pipeline code

## 📊 Test PDFs Details

| PDF | Pages | Type | Size | Best For |
|-----|-------|------|------|----------|
| brf_268882.pdf | 21 | Scanned | 1.0MB | Quick iteration |
| brf_271852.pdf | 15 | Scanned | 0.8MB | Fast testing |
| brf_276507.pdf | 52 | Scanned | 2.7MB | Stress testing |

**Recommendation**: Start with brf_268882.pdf for fastest feedback.

## 🔗 Main Testing Status

**Main agent** is currently running:
- Week 3 Day 1-2 comprehensive testing (42 PDFs)
- **Don't interrupt**: Let it complete (~30-40 minutes total)
- Your experiments run in parallel (no conflicts)

**Check main test progress**:
```bash
cd ../..
ls -lh data/week3_sample_test_results/
```

## 📝 Reporting Template

Create `FINDINGS.md` with:

```markdown
# Docling Advanced Experiments - Findings

**Date**: YYYY-MM-DD
**PDFs Tested**: List which PDFs
**Experiments Run**: List experiments

## Key Findings

### OCR Quality
- Best engine: [EasyOCR/Tesseract/etc.]
- Swedish character accuracy: [%]
- Processing speed: [seconds per page]

### Table Extraction
- Tables detected: [X/Y]
- Extraction quality: [good/fair/poor]
- Issues found: [list]

### Recommendations
1. [Specific recommendation 1]
2. [Specific recommendation 2]

## Raw Results

[Link to JSON files or paste key metrics]
```

---

**Ready to start?** Copy code templates from `PARALLEL_DOCLING_EXPERIMENTS.md` and run your first experiment! 🚀
