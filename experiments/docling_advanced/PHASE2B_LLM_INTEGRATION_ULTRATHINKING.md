# Phase 2B: LLM Integration - ULTRATHINKING Analysis

**Date**: 2025-10-08
**Context**: Phase 2A complete (architecture), now implementing real OpenAI calls
**Goal**: Replace placeholders with actual GPT-4o multimodal extraction

---

## 🎯 Core Challenge

**Current State**: `_extract_agent()` returns placeholder results
**Target State**: `_extract_agent()` calls GPT-4o with PDF images and returns real JSON

**Key Question**: How do we bridge the gap between section headings and actual PDF pages?

---

## 🧠 ULTRATHINKING: Critical Implementation Decisions

### Decision #1: Section Headings → Page Numbers Mapping

**Problem**: We have section headings from Docling, but need page numbers for image rendering.

#### Evidence from Current Implementation
From `optimal_brf_pipeline.py:106-165` (StructureDetectionResult):
```python
@dataclass
class StructureDetectionResult:
    sections: List[Dict[str, Any]]  # Each section has: heading, level, page (optional)
    ...
```

From `detect_structure()` method:
```python
for item, level in doc.iterate_items():
    if isinstance(item, SectionHeaderItem):
        sections.append({
            "heading": item.text,
            "level": level,
            "page": getattr(item, 'page', None)  # ⚠️ May be None!
        })
```

**Key Insight**: Docling sections MAY have page numbers, but not guaranteed!

#### Option 1A: Use Docling Page Numbers (If Available)
```python
def _get_pages_for_sections(self, section_headings: List[str]) -> List[int]:
    """Map section headings to page numbers from Docling structure"""
    pages = []
    for heading in section_headings:
        # Search in cached structure
        for section in self.structure_cache.sections:
            if section['heading'] == heading and section.get('page'):
                pages.append(section['page'])
    return sorted(set(pages))
```

**Pros**: ✅ Uses Docling's layout detection
**Cons**: ⚠️ May miss pages if Docling didn't detect page numbers

#### Option 1B: Full Document Scan (Gracian Pattern)
```python
def _get_pages_for_agent(self, agent_id: str) -> List[int]:
    """Return pages spanning the whole document (Gracian orchestrator pattern)"""
    # Sample evenly distributed pages
    total_pages = self._get_pdf_page_count(pdf_path)

    if total_pages <= 10:
        return list(range(total_pages))  # Use all pages
    else:
        # Sample 10 pages evenly
        step = total_pages // 10
        return [i * step for i in range(10)]
```

**Pros**: ✅ Simple, always works, covers whole document
**Cons**: ⚠️ Inefficient (processes irrelevant pages), higher cost

#### Option 1C: Hybrid (Docling Pages + Keyword Fallback) ✅ **RECOMMENDED**
```python
def _get_pages_for_sections(
    self,
    section_headings: List[str],
    fallback_pages: int = 5
) -> List[int]:
    """
    Try Docling page numbers first, fall back to keyword search.

    Strategy:
    1. If section has page number → use it
    2. If no page number → search PDF text for section heading
    3. If not found → use first N pages as fallback
    """
    pages = []

    # Try Docling page numbers
    for heading in section_headings:
        for section in self.structure_cache.sections:
            if section['heading'] == heading and section.get('page'):
                pages.append(section['page'])
                break
        else:
            # Fallback: Search PDF text for heading
            found_page = self._find_heading_in_pdf(heading)
            if found_page:
                pages.append(found_page)

    # If no pages found, use first N pages
    if not pages:
        pages = list(range(fallback_pages))

    return sorted(set(pages))
```

**Pros**:
- ✅ Uses Docling when available (accurate)
- ✅ Fallback ensures always returns pages
- ✅ Text search catches headings Docling missed

**Cons**:
- ⚠️ More complex implementation
- ⚠️ Text search adds latency (~1s per heading)

**DECISION**: **Option 1C (Hybrid)** - Best balance of accuracy and robustness

---

### Decision #2: Image Rendering Strategy

**Question**: How many pages to render per agent call? What format/quality?

#### Evidence from Gracian Pipeline
From `vision_qc.py:15-34` (render_pdf_pages):
```python
def render_pdf_pages(pdf_path: str, max_pages: int = 2, dpi: int = 200) -> List[bytes]:
    """Render first N pages of a PDF to PNG bytes using PyMuPDF (fitz)."""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(min(max_pages, doc.page_count)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))

    return images
```

**Gracian Settings**:
- DPI: 200 (from `QC_PAGE_RENDER_DPI=220` in .env)
- Format: PNG
- Max pages per call: 2-10 (from `VISION_PAGES_PER_CALL=10`)

#### Option 2A: Conservative (2-3 pages per call)
```python
dpi = 200
format = "png"
max_pages_per_call = 3
```

**Pros**: ✅ Lower token cost, faster API calls
**Cons**: ⚠️ May miss relevant content if section spans many pages

#### Option 2B: Aggressive (10 pages per call)
```python
dpi = 220
format = "png"
max_pages_per_call = 10
```

**Pros**: ✅ Better context for LLM, catches multi-page sections
**Cons**: ⚠️ Higher token cost, slower API calls, may exceed context limits

#### Option 2C: Adaptive (Based on Section Size) ✅ **RECOMMENDED**
```python
def _render_section_pages(self, section_headings: List[str]) -> List[bytes]:
    """
    Render pages adaptively based on section size.

    Strategy:
    - Small sections (1-2 pages): Render all
    - Medium sections (3-5 pages): Render first 3 + last 1
    - Large sections (6+ pages): Render first 2 + middle 1 + last 1
    """
    pages = self._get_pages_for_sections(section_headings)

    if len(pages) <= 3:
        # Small: Render all
        render_pages = pages
    elif len(pages) <= 5:
        # Medium: First 3 + last
        render_pages = pages[:3] + [pages[-1]]
    else:
        # Large: First 2 + middle + last
        render_pages = [pages[0], pages[1], pages[len(pages)//2], pages[-1]]

    return self._render_pdf_pages(render_pages, dpi=200)
```

**Pros**:
- ✅ Balances cost and coverage
- ✅ Always includes first page (usually has key info)
- ✅ Samples large sections intelligently

**Cons**:
- ⚠️ May miss content between sampled pages

**DECISION**: **Option 2C (Adaptive)** - Cost-effective with good coverage

---

### Decision #3: OpenAI API Call Pattern

**Question**: How to structure the API call for reliability and performance?

#### Evidence from Gracian Pipeline
From `vision_qc.py:208-241` (call_openai_vision):
```python
def call_openai_vision(
    prompt: str,
    images_png: List[bytes],
    page_labels: List[str] | None = None
) -> str:
    """Call OpenAI Chat Completions with vision. Retries on transient errors."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Build multimodal messages
    content = [{"type": "text", "text": prompt}]
    for i, img_bytes in enumerate(images_png):
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        label = page_labels[i] if page_labels else f"Page {i+1}"
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high"  # High resolution for Swedish text
            }
        })

    # Retry logic (3 attempts)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[{"role": "user", "content": content}],
                max_tokens=2000,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

**Key Patterns**:
- ✅ Base64 encode images inline
- ✅ Page labels for evidence tracking
- ✅ `detail="high"` for Swedish OCR
- ✅ Retry with exponential backoff (3 attempts)
- ✅ `temperature=0` for deterministic JSON

#### Option 3A: Simple (No Retries)
```python
response = client.chat.completions.create(...)
return response.choices[0].message.content
```

**Pros**: ✅ Simple
**Cons**: ❌ Fails on transient errors (rate limits, network issues)

#### Option 3B: Gracian Pattern (3 Retries) ✅ **RECOMMENDED**
```python
for attempt in range(3):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[{"role": "user", "content": multimodal_content}],
            max_tokens=2000,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

**Pros**:
- ✅ Handles transient failures
- ✅ Proven in Gracian (95/95 accuracy)
- ✅ Exponential backoff prevents hammering

**Cons**:
- ⚠️ Adds latency on failures

**DECISION**: **Option 3B (Gracian Pattern)** - Production-grade reliability

---

### Decision #4: JSON Parsing Strategy

**Question**: How to robustly parse LLM responses into JSON?

#### Evidence from Gracian Pipeline
From `vision_qc.py:57-86` (json_guard):
```python
def json_guard(text: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Robust JSON parsing with fallbacks.

    Handles:
    - Markdown code fences (```json ... ```)
    - Leading/trailing whitespace
    - Invalid JSON (returns default)
    """
    if default is None:
        default = {}

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]  # Remove closing fence
        text = "\n".join(lines).strip()

    # Try parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default
```

**Common LLM JSON Issues**:
1. Markdown code fences: `\`\`\`json {...} \`\`\``
2. Trailing explanations: `{"key": "value"} \n\nI extracted...`
3. Partial JSON: Missing closing braces
4. Swedish characters: UTF-8 encoding issues

#### Option 4A: Naive Parsing
```python
result = json.loads(response_text)
```

**Pros**: ✅ Simple
**Cons**: ❌ Fails on common LLM formatting issues

#### Option 4B: Gracian json_guard ✅ **RECOMMENDED**
```python
from gracian_pipeline.core.vision_qc import json_guard

result = json_guard(response_text, default={"error": "JSON parsing failed"})
```

**Pros**:
- ✅ Handles markdown fences
- ✅ Graceful fallback on parse errors
- ✅ Proven in production

**Cons**:
- ⚠️ May silently return default on malformed JSON

**DECISION**: **Option 4B (json_guard)** - Reuse proven parsing logic

---

### Decision #5: Evidence Tracking (Page Citations)

**Question**: How to track which pages were used for each extraction?

#### Evidence from Gracian Pipeline
Agent prompts all require `evidence_pages: []` field:
```python
"""Include evidence_pages: [] with 1-based page numbers used."""
```

From `vision_qc.py:208-241`:
```python
page_labels = [f"Page {i+1}" for i in range(len(images))]
# Pass labels to LLM for citation
```

**Challenge**: How to ensure LLM returns actual page numbers, not just [1,2,3]?

#### Option 5A: Trust LLM (No Verification)
```python
# Just accept whatever evidence_pages LLM returns
evidence_pages = result.get('evidence_pages', [])
```

**Pros**: ✅ Simple
**Cons**: ⚠️ LLM may hallucinate page numbers

#### Option 5B: Verify Against Rendered Pages ✅ **RECOMMENDED**
```python
def _add_evidence_metadata(
    self,
    result: Dict,
    rendered_pages: List[int]
) -> Dict:
    """
    Add evidence metadata and verify page citations.

    Strategy:
    - Add _rendered_pages field (pages we sent to LLM)
    - Validate evidence_pages are subset of rendered_pages
    - Add _evidence_verified flag
    """
    result['_rendered_pages'] = rendered_pages

    evidence = result.get('evidence_pages', [])
    if evidence:
        # Verify all cited pages were actually rendered
        verified = all(page in rendered_pages for page in evidence)
        result['_evidence_verified'] = verified
    else:
        result['_evidence_verified'] = False

    return result
```

**Pros**:
- ✅ Tracks what LLM actually saw
- ✅ Detects hallucinated citations
- ✅ Useful for debugging

**Cons**:
- ⚠️ Extra metadata fields

**DECISION**: **Option 5B (Verified Evidence)** - Better for quality validation

---

### Decision #6: Context Passing (Pass 1 → Pass 2)

**Question**: How to pass hierarchical context from Pass 1 to Pass 2?

#### Current Implementation
From `extract_pass2()`:
```python
context = {
    **pass1_results,
    'financial': results.get('financial_agent', {}),
    'previous_notes': {k: v for k, v in results.items() if k.startswith('notes_')}
}
```

**Challenge**: Context dict is large (nested results), may exceed token limits.

#### Option 6A: Full Context (Everything)
```python
context = {**pass1_results, **pass2_results_so_far}
prompt += f"\n\nContext:\n{json.dumps(context, indent=2)}"
```

**Pros**: ✅ Maximum context for LLM
**Cons**: ⚠️ May exceed token limits, expensive

#### Option 6B: Selective Context (Only Relevant Fields) ✅ **RECOMMENDED**
```python
def _build_selective_context(
    self,
    agent_id: str,
    pass1_results: Dict,
    pass2_results: Dict
) -> str:
    """
    Build selective context based on agent dependencies.

    Dependencies:
    - financial_agent: needs governance (chairman for signatures)
    - notes_loans_agent: needs financial (debt validation)
    - notes_buildings_agent: needs property (building area)
    """
    context_fields = []

    # Governance context (always useful)
    if 'governance_agent' in pass1_results:
        gov = pass1_results['governance_agent']
        context_fields.append(f"Chairman: {gov.get('chairman', 'N/A')}")
        context_fields.append(f"Board members: {len(gov.get('board_members', []))}")

    # Property context
    if 'property_agent' in pass1_results:
        prop = pass1_results['property_agent']
        context_fields.append(f"Property: {prop.get('address', 'N/A')}")
        context_fields.append(f"Apartments: {prop.get('apartments', 'N/A')}")

    # Financial context (for note agents)
    if agent_id.startswith('notes_') and 'financial_agent' in pass2_results:
        fin = pass2_results['financial_agent']
        context_fields.append(f"Assets: {fin.get('assets', 'N/A')}")
        context_fields.append(f"Liabilities: {fin.get('liabilities', 'N/A')}")

    if not context_fields:
        return ""

    return "\n\nContext from previous extraction:\n" + "\n".join(context_fields)
```

**Pros**:
- ✅ Minimal token usage
- ✅ Only passes relevant context
- ✅ Matches hierarchical dependencies

**Cons**:
- ⚠️ Requires manual dependency mapping

**DECISION**: **Option 6B (Selective Context)** - Token-efficient and targeted

---

## 📋 Final Implementation Plan (Phase 2B)

### Step 1: Add Helper Methods to OptimalBRFPipeline

**New Methods** (add after `route_sections()`):

```python
def _get_pdf_page_count(self, pdf_path: str) -> int:
    """Get total page count from PDF"""
    import fitz
    doc = fitz.open(pdf_path)
    count = doc.page_count
    doc.close()
    return count

def _find_heading_in_pdf(self, pdf_path: str, heading: str) -> Optional[int]:
    """Search PDF text for heading, return page number (0-indexed)"""
    import fitz
    doc = fitz.open(pdf_path)
    heading_lower = heading.lower()

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text().lower()
        if heading_lower in text:
            doc.close()
            return page_num

    doc.close()
    return None

def _get_pages_for_sections(
    self,
    pdf_path: str,
    section_headings: List[str],
    fallback_pages: int = 5
) -> List[int]:
    """
    Map section headings to page numbers (Hybrid strategy).

    1. Try Docling page numbers
    2. Fall back to text search
    3. Fall back to first N pages
    """
    pages = []

    # Try Docling page numbers
    for heading in section_headings:
        for section in self.structure_cache.sections:
            if section['heading'] == heading and section.get('page') is not None:
                pages.append(section['page'])
                break
        else:
            # Fallback: Search PDF text
            found_page = self._find_heading_in_pdf(pdf_path, heading)
            if found_page is not None:
                pages.append(found_page)

    # If no pages found, use first N pages
    if not pages:
        pages = list(range(fallback_pages))

    return sorted(set(pages))

def _render_pdf_pages(
    self,
    pdf_path: str,
    page_numbers: List[int],
    dpi: int = 200
) -> Tuple[List[bytes], List[str]]:
    """
    Render specific PDF pages to PNG bytes.

    Returns:
        (images, page_labels) tuple
    """
    import fitz

    doc = fitz.open(pdf_path)
    images = []
    labels = []

    for page_num in page_numbers:
        if page_num >= doc.page_count:
            continue

        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))
        labels.append(f"Page {page_num + 1}")  # 1-based for LLM

    doc.close()
    return images, labels

def _build_selective_context(
    self,
    agent_id: str,
    pass1_results: Dict,
    pass2_results: Dict
) -> str:
    """Build selective context (only relevant fields)"""
    context_fields = []

    # Governance context
    if 'governance_agent' in pass1_results:
        gov = pass1_results['governance_agent']
        if gov.get('chairman'):
            context_fields.append(f"Chairman: {gov['chairman']}")

    # Property context
    if 'property_agent' in pass1_results:
        prop = pass1_results['property_agent']
        if prop.get('address'):
            context_fields.append(f"Property: {prop['address']}")
        if prop.get('apartments'):
            context_fields.append(f"Apartments: {prop['apartments']}")

    # Financial context (for note agents)
    if agent_id.startswith('notes_') and 'financial_agent' in pass2_results:
        fin = pass2_results['financial_agent']
        if fin.get('assets'):
            context_fields.append(f"Assets: {fin['assets']}")
        if fin.get('liabilities'):
            context_fields.append(f"Liabilities: {fin['liabilities']}")

    if not context_fields:
        return ""

    return "\n\nContext from previous extraction:\n" + "\n".join(context_fields)
```

**Estimated Lines**: ~120 lines

---

### Step 2: Update `_extract_agent()` Method

**Replace Placeholder** (lines 526-533) with real extraction:

```python
def _extract_agent(
    self,
    pdf_path: str,
    agent_id: str,
    section_headings: List[str],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Extract data for a single agent using GPT-4o."""
    import base64
    import json
    import time
    from openai import OpenAI

    start_time = time.time()

    # Agent prompts (keep existing dict)
    AGENT_PROMPTS = {...}  # Keep existing

    base_prompt = AGENT_PROMPTS.get(agent_id, f"Extract data for {agent_id} in JSON format.")

    # Get pages for this agent
    pages = self._get_pages_for_sections(pdf_path, section_headings, fallback_pages=5)

    # Render pages to images (adaptive: max 4 pages)
    if len(pages) > 4:
        render_pages = [pages[0], pages[1], pages[len(pages)//2], pages[-1]]
    else:
        render_pages = pages

    images, page_labels = self._render_pdf_pages(pdf_path, render_pages, dpi=200)

    # Build prompt with context
    prompt = f"""Document sections detected:
{json.dumps(section_headings, indent=2, ensure_ascii=False)}

{base_prompt}

Focus on the sections listed above. You are viewing {len(images)} page(s) from this document.
"""

    # Add selective context
    if context:
        context_str = self._build_selective_context(agent_id, context.get('pass1', {}), context.get('pass2', {}))
        if context_str:
            prompt += context_str

    # Build multimodal message
    content = [{"type": "text", "text": prompt}]
    for i, img_bytes in enumerate(images):
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high"  # High resolution for Swedish text
            }
        })

    # Call OpenAI with retry logic
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[{"role": "user", "content": content}],
                max_tokens=2000,
                temperature=0
            )

            response_text = response.choices[0].message.content

            # Parse JSON with fallback
            from gracian_pipeline.core.vision_qc import json_guard
            result = json_guard(response_text, default={})

            # Add metadata
            result['agent_id'] = agent_id
            result['status'] = 'success'
            result['section_headings'] = section_headings
            result['_rendered_pages'] = [p + 1 for p in render_pages]  # 1-based
            result['extraction_time'] = time.time() - start_time
            result['model'] = 'gpt-4o-2024-11-20'

            # Verify evidence
            evidence = result.get('evidence_pages', [])
            if evidence:
                rendered_pages_1based = [p + 1 for p in render_pages]
                result['_evidence_verified'] = all(page in rendered_pages_1based for page in evidence)
            else:
                result['_evidence_verified'] = False

            return result

        except Exception as e:
            if attempt == 2:
                # Final failure
                return {
                    "agent_id": agent_id,
                    "status": "error",
                    "error": str(e),
                    "section_headings": section_headings,
                    "extraction_time": time.time() - start_time
                }

            # Retry with exponential backoff
            time.sleep(2 ** attempt)
```

**Estimated Lines**: ~100 lines (replacing ~8 placeholder lines)

---

### Step 3: Update Context Passing in extract_pass2()

**Replace** (lines 625-629):
```python
context = {
    **pass1_results,
    'financial': results.get('financial_agent', {}),
    'previous_notes': {k: v for k, v in results.items() if k.startswith('notes_')}
}
```

**With**:
```python
context = {
    'pass1': pass1_results,
    'pass2': results  # Current pass2 results so far
}
```

**Estimated Lines**: 3 lines

---

### Step 4: Add Import for json_guard

**Add to imports** (top of file):
```python
# Add after existing imports
import base64
from openai import OpenAI
```

**Estimated Lines**: 2 lines

---

### Step 5: Cache structure in _extract_agent()

**Problem**: `_extract_agent()` needs access to `self.structure_cache.sections`

**Solution**: Add structure cache in `detect_structure()`:

```python
# In detect_structure(), after creating result:
self.structure_cache = result  # Cache for _get_pages_for_sections()
return result
```

**Estimated Lines**: 1 line

---

## 📊 Implementation Summary

### Total Changes
| Component | Lines Added | Lines Removed | Net Change |
|-----------|-------------|---------------|------------|
| Helper methods | ~120 | 0 | +120 |
| _extract_agent() | ~100 | ~8 | +92 |
| extract_pass2() | ~3 | ~5 | -2 |
| Imports | ~2 | 0 | +2 |
| Cache fix | ~1 | 0 | +1 |
| **TOTAL** | ~226 | ~13 | **+213 lines** |

### File Structure
```
optimal_brf_pipeline.py (current: 900 lines)
├── Imports (+2 lines)
├── Data classes (unchanged)
├── CacheManager (unchanged)
├── OptimalBRFPipeline.__init__() (unchanged)
├── PDF topology methods (unchanged)
├── Structure detection (+1 line cache fix)
├── Section routing (unchanged)
├── 🆕 Helper methods (+120 lines)
│   ├── _get_pdf_page_count()
│   ├── _find_heading_in_pdf()
│   ├── _get_pages_for_sections()
│   ├── _render_pdf_pages()
│   └── _build_selective_context()
├── 🆕 _extract_agent() (+92 net lines)
├── extract_pass1() (unchanged)
├── extract_pass2() (-2 net lines)
├── validate_extraction() (unchanged)
├── extract_document() (unchanged)
└── close() (unchanged)

TOTAL: ~1,113 lines
```

---

## ✅ Success Criteria (Phase 2B Complete)

### Functionality
- [ ] Real OpenAI API calls working
- [ ] Images rendering correctly (PyMuPDF)
- [ ] JSON parsing handling Swedish characters
- [ ] Evidence pages verified
- [ ] Retry logic functioning

### Quality
- [ ] Test on brf_268882.pdf shows real extractions
- [ ] Evidence ratio > 0% (was 0% with placeholders)
- [ ] Extracted data matches Gracian quality
- [ ] No API errors in happy path

### Performance
- [ ] Pass 1 completes in <10s (2 agents × 5s)
- [ ] Pass 2 completes in <50s (8 agents × 6s sequential)
- [ ] Total cost < $0.25 per document
- [ ] Retry logic doesn't add excessive latency

---

## 🎯 Testing Strategy

### Test 1: Single Agent Extraction
```bash
# Test governance_agent on first 3 pages
python -c "
from optimal_brf_pipeline import OptimalBRFPipeline
pipeline = OptimalBRFPipeline()
result = pipeline._extract_agent(
    'test_pdfs/brf_268882.pdf',
    'governance_agent',
    ['Styrelse', 'Revisorer']
)
print(result)
"
```

**Expected**: Real chairman name, board members extracted

### Test 2: Full Pipeline
```bash
python code/optimal_brf_pipeline.py test_pdfs/brf_268882.pdf
```

**Expected**:
- Stage 4: Pass 1-2 show real extraction times (not 0.0s)
- Stage 5: Evidence ratio > 0%
- Output JSON has real data, not placeholders

### Test 3: Ground Truth Validation
```bash
# Compare against Gracian results
python -c "
from optimal_brf_pipeline import OptimalBRFPipeline
result = pipeline.extract_document('test_pdfs/brf_268882.pdf')

# Compare governance
print('Chairman:', result.pass1_result['governance_agent']['chairman'])
# Should match ground truth
"
```

---

## 🚧 Potential Issues & Mitigations

### Issue #1: Page Number Mismatch (Docling vs Reality)
**Symptom**: Docling page numbers don't match actual PDF pages
**Mitigation**: Hybrid fallback with text search
**Test**: Manually verify rendered pages contain expected sections

### Issue #2: OpenAI API Key Missing
**Symptom**: `openai.error.AuthenticationError`
**Mitigation**: Add check in `_extract_agent()`:
```python
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    return {"status": "error", "error": "OPENAI_API_KEY not set"}
```

### Issue #3: Image Too Large (Token Limits)
**Symptom**: `openai.error.InvalidRequestError: image too large`
**Mitigation**: Adaptive page rendering (max 4 pages)
**Fallback**: Reduce DPI from 200 → 150 if still fails

### Issue #4: JSON Parsing Fails on Swedish Characters
**Symptom**: `json.JSONDecodeError` with UTF-8 issues
**Mitigation**: `json_guard()` already handles this gracefully
**Test**: Validate on document with Swedish characters (å, ä, ö)

### Issue #5: Context Exceeds Token Limit
**Symptom**: `openai.error.InvalidRequestError: max tokens exceeded`
**Mitigation**: Selective context already limits to key fields
**Fallback**: Omit context entirely if error persists

---

## 📈 Expected Outcomes (Phase 2B Complete)

### Extraction Quality
- **Coverage**: ≥80% (8/10 agents return non-empty data)
- **Accuracy**: Matches Gracian ground truth on governance/property
- **Evidence**: ≥50% of agents cite pages (was 0%)

### Performance
- **Time**: 45-60s per document (vs 0.0s placeholders)
- **Cost**: $0.15-$0.25 per document
- **API Success Rate**: ≥95% (with 3 retries)

### Deliverables
- [ ] Updated `optimal_brf_pipeline.py` (~1,113 lines)
- [ ] Test results showing real extractions
- [ ] `PHASE2B_IMPLEMENTATION_COMPLETE.md` (summary)

---

**Status**: ✅ **ULTRATHINKING COMPLETE**
**Next**: Implement Phase 2B following this plan (~3-4 hours)
**Confidence**: 🟢 High (all decisions evidence-based)
