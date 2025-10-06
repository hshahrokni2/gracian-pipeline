# Docling BRF Extraction - Validation Report

**Generated**: 2025-10-06 11:58:27

## Executive Summary

- **Test Documents**: 1
- **Extraction Methods Compared**: 3 (Docling+GPT-4o, Gracian Pipeline, OpenAI Vision Direct)
- **Target**: 95% coverage, 95% accuracy

## High-Level Performance

| Method | Chairman Extracted | Board Members Found | Assets Extracted |
|--------|-------------------|---------------------|------------------|
| **Docling + GPT-4o** | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| **Gracian Pipeline** | 1/1 (100%) | 1/1 (100%) | N/A |
| **OpenAI Direct** | 0/1 (0%) | N/A | 0/1 (0%) |

## Detailed Results

### 1. brf_198532.pdf

#### Governance Fields

| Field | Docling+GPT-4o | Gracian Pipeline | OpenAI Direct |
|-------|----------------|------------------|---------------|
| chairman | N/A | Elvy Maria Löfvenberg | N/A |
| auditor_name | N/A | Tobias Andersson | N/A |
| audit_firm | N/A | KPMG AB | N/A |
| board_members (count) | 0 | 4 | 0 |

#### Financial Fields

| Field | Docling+GPT-4o | OpenAI Direct |
|-------|----------------|---------------|
| assets | N/A | N/A |
| revenue | N/A | N/A |
| expenses | N/A | N/A |
| equity | N/A | N/A |

---

## Recommendations for 95/95 Target

### Key Findings

1. **Docling + GPT-4o**: Best for machine-readable PDFs with good structure
   - Pros: Extracts tables, handles multi-page documents well
   - Cons: Doesn't OCR scanned PDFs effectively

2. **Gracian Pipeline**: Good for governance extraction
   - Pros: Uses vision models, works on both scanned and text PDFs
   - Cons: Limited to configured agents

3. **OpenAI Vision Direct**: Baseline for validation
   - Pros: Simple, works on all PDF types
   - Cons: No table extraction, limited context

### Proposed Hybrid Pipeline

```python
def hybrid_extraction(pdf_path):
    # 1. Try Docling first (fast for text PDFs)
    docling_result = docling_extract(pdf_path)
    
    if is_text_pdf(docling_result):
        # Use Docling + GPT-4o for structured extraction
        return docling_to_brf_schema(docling_result)
    else:
        # Fall back to Gracian Pipeline for scanned PDFs
        return gracian_vision_extraction(pdf_path)
```

### Schema Mapping Integration

- Add `mappings.py` to convert docling tables to BRF financial schema
- Use regex patterns for Swedish number parsing ("301 339 818" → 301339818)
- Implement confidence scoring for each extracted field
- Add cross-validation between methods

