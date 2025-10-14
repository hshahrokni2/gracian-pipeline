# Phase 2: Enhanced Vision Pipeline - Implementation Plan

**Date**: October 14, 2025
**Status**: 🚀 **STARTING IMPLEMENTATION**
**Goal**: Scanned PDF accuracy 22.7% → 85% (+62pp improvement)
**Critical**: This unlocks 49% of corpus (13,300 PDFs) stuck at low accuracy

---

## 🎯 EXECUTIVE SUMMARY

**Why This Matters**:
- **49% of corpus** (13,300 PDFs) are scanned/image-based
- Currently stuck at **22.7% accuracy** (vs 48.9% for machine-readable)
- This is the **PRIMARY BOTTLENECK** to reaching 95/95 targets
- Without fixing this, we cannot achieve production quality

**What We're Building**:
1. **PDF Type Classifier** - Auto-detect machine-readable vs scanned
2. **Enhanced Image Preprocessing** - Optimize for Swedish OCR
3. **Multi-Model Vision Consensus** - 3 vision models voting (Gemini, GPT-4V, Qwen)
4. **Ground Truth Validation** - Calibrate against 100 perfect PDFs

**Expected Outcome**:
- Scanned PDF accuracy: 22.7% → 75-85% (+52-62pp)
- Overall accuracy: 34.0% → 55-65% (weighted by 49% scanned corpus)
- Unlock production deployment for full 27,000 PDF corpus

---

## 📊 PROBLEM ANALYSIS

### Current Performance by PDF Type
| Type | Coverage | Accuracy | Count | % of Corpus | Status |
|------|----------|----------|-------|-------------|--------|
| **Machine-readable** | 67.0% | **48.9%** | ~13,000 | ~48% | ✅ Good |
| **Hybrid** | 46.2% | **30.5%** | ~600 | ~2% | 🟡 Medium |
| **Scanned** | 37.4% | **22.7%** | ~13,300 | ~49% | 🔴 **CRITICAL** |

**Key Insight**: Nearly HALF of corpus is scanned PDFs with 22.7% accuracy - this is unacceptable for production!

### Root Causes (Scanned PDF Failures)
1. **Poor OCR Quality**: Current Docling settings insufficient for Swedish characters (ö, ä, å)
2. **Image Quality**: Low DPI (200) and no preprocessing for scanned documents
3. **Single Vision Model**: No consensus/validation mechanism
4. **No Scanned PDF Detection**: Treating all PDFs the same way

---

## 🏗️ ARCHITECTURE OVERVIEW

### Three-Layer Vision Pipeline

```
PDF Input
    ↓
┌─────────────────────────────────────┐
│ Layer 1: PDF Type Classification   │
│ - Text density analysis             │
│ - Image ratio detection             │
│ - Route: machine-readable vs scanned│
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Layer 2: Image Preprocessing       │  ← SCANNED PDFs ONLY
│ - DPI optimization (200→300)        │
│ - Swedish character enhancement     │
│ - Adaptive thresholding             │
│ - Deskewing & denoising            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Layer 3: Multi-Model Consensus     │  ← SCANNED PDFs ONLY
│ - Gemini 2.5-Pro (50% weight)      │
│ - GPT-4V Vision (30% weight)        │
│ - Qwen 2.5-VL (20% weight)          │
│ - Voting + confidence scoring       │
└─────────────────────────────────────┘
    ↓
Extracted Data (75-85% accuracy for scanned)
```

### Cost Optimization Strategy
- **Machine-readable PDFs** (48%): Single-pass extraction ($0.05/PDF) - no change
- **Scanned PDFs** (49%): Multi-model consensus ($0.15/PDF) - necessary investment
- **Average cost**: (0.48 × $0.05) + (0.49 × $0.15) = **$0.10/PDF** (vs $0.05 baseline)

---

## 🔧 IMPLEMENTATION PLAN

### Step 1: PDF Type Classifier (2-3 hours)

**File**: `gracian_pipeline/core/pdf_classifier.py`

```python
class PDFTypeClassifier:
    """
    Classify PDFs as machine-readable, hybrid, or scanned.
    Route to appropriate extraction strategy.
    """

    def classify_pdf(self, pdf_path: str) -> dict:
        """
        Analyze first 5 pages to determine PDF type.

        Returns:
        {
            "type": "machine_readable" | "hybrid" | "scanned",
            "text_density": float,  # chars per page
            "image_ratio": float,   # % of page area that's images
            "confidence": float,    # 0-1 classification confidence
            "strategy": "text" | "mixed" | "vision_consensus"
        }
        """
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        text_chars = 0
        total_area = 0
        image_area = 0

        # Analyze first 5 pages (representative sample)
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]

            # Text density
            text = page.get_text()
            text_chars += len(text)

            # Image ratio
            page_rect = page.rect
            total_area += page_rect.width * page_rect.height

            for img in page.get_images():
                # Get image dimensions
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                image_area += pix.width * pix.height

        # Calculate metrics
        text_density = text_chars / min(5, len(doc))
        image_ratio = image_area / total_area if total_area > 0 else 0

        # Classification logic
        if text_density > 1000:  # >1000 chars/page
            pdf_type = "machine_readable"
            strategy = "text"
            confidence = 0.9
        elif text_density < 100:  # <100 chars/page
            pdf_type = "scanned"
            strategy = "vision_consensus"
            confidence = 0.9
        else:  # 100-1000 chars/page
            pdf_type = "hybrid"
            strategy = "mixed"
            confidence = 0.7

        return {
            "type": pdf_type,
            "text_density": text_density,
            "image_ratio": image_ratio,
            "confidence": confidence,
            "strategy": strategy,
            "pages": len(doc)
        }
```

**Integration Point**: `parallel_orchestrator.py` - call classifier before extraction

---

### Step 2: Enhanced Image Preprocessing (3-4 hours)

**File**: `gracian_pipeline/core/image_preprocessor.py`

```python
import cv2
import numpy as np
from pdf2image import convert_from_path

class EnhancedImagePreprocessor:
    """
    Optimize PDF images for Swedish OCR extraction.
    Focuses on scanned documents with Swedish characters.
    """

    def __init__(self):
        # Swedish character enhancement kernel
        self.swedish_kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])

    def preprocess_for_swedish_ocr(self, pdf_path: str, page_num: int) -> np.ndarray:
        """
        Apply OCR-optimized preprocessing for Swedish BRF documents.

        Steps:
        1. Convert PDF to high-DPI image
        2. Adaptive thresholding (better than global)
        3. Denoise (remove scan artifacts)
        4. Deskew (fix rotated scans)
        5. Enhance Swedish characters (ö, ä, å)

        Returns: Preprocessed image ready for vision models
        """

        # Step 1: High-DPI conversion (200 → 300)
        images = convert_from_path(
            pdf_path,
            dpi=300,  # Higher quality for Swedish characters
            first_page=page_num,
            last_page=page_num
        )
        page_image = np.array(images[0])

        # Step 2: Convert to grayscale
        gray = cv2.cvtColor(page_image, cv2.COLOR_BGR2GRAY)

        # Step 3: Adaptive thresholding (better for mixed lighting)
        # ADAPTIVE_THRESH_GAUSSIAN_C adapts to local neighborhood
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,  # Neighborhood size
            C=2  # Constant subtracted from mean
        )

        # Step 4: Denoise (remove scan artifacts)
        denoised = cv2.fastNlMeansDenoising(
            binary,
            h=10,  # Filter strength
            templateWindowSize=7,
            searchWindowSize=21
        )

        # Step 5: Deskew (fix rotated scans)
        angle = self._detect_skew(denoised)
        deskewed = self._rotate_image(denoised, angle)

        # Step 6: Enhance Swedish characters
        # Sharpening filter to make ö, ä, å more distinct
        sharpened = cv2.filter2D(deskewed, -1, self.swedish_kernel)

        # Step 7: Convert back to BGR for vision models
        final = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

        return final

    def _detect_skew(self, image: np.ndarray) -> float:
        """Detect rotation angle of scanned document."""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]

        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        return angle

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image to correct skew."""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated
```

**Integration Point**: Call before vision model extraction for scanned PDFs

---

### Step 3: Multi-Model Vision Consensus (4-5 hours)

**File**: `gracian_pipeline/core/vision_consensus.py`

```python
import asyncio
from typing import List, Dict, Any
from openai import OpenAI
import google.generativeai as genai

class VisionConsensus:
    """
    Extract data using 3 vision models + voting for scanned PDFs.

    Models:
    1. Gemini 2.5-Pro (50% weight) - Best for Swedish text
    2. GPT-4V Vision (30% weight) - Good for tables
    3. Qwen 2.5-VL (20% weight) - Backup/validation

    Voting Strategy:
    - If 2/3 agree: Use consensus value
    - If all disagree: Use highest confidence model (Gemini)
    - Null handling: Require 2/3 non-null to accept value
    """

    def __init__(self):
        self.openai_client = OpenAI()
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')

        # Confidence weights
        self.weights = {
            'gemini': 0.5,
            'gpt4v': 0.3,
            'qwen': 0.2
        }

    async def extract_with_consensus(
        self,
        pdf_path: str,
        agent_id: str,
        pages: List[int],
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract data using all 3 models in parallel, then vote.

        Returns:
        {
            "data": {...},  # Consensus extraction
            "confidence": 0.85,  # Overall confidence
            "model_results": {
                "gemini": {...},
                "gpt4v": {...},
                "qwen": {...}
            },
            "agreement_rate": 0.67  # % of fields with 2/3 agreement
        }
        """

        # Preprocess images
        preprocessed_images = []
        for page_num in pages:
            img = self.preprocessor.preprocess_for_swedish_ocr(pdf_path, page_num)
            preprocessed_images.append(img)

        # Extract in parallel (async)
        results = await asyncio.gather(
            self._extract_gemini(preprocessed_images, prompt),
            self._extract_gpt4v(preprocessed_images, prompt),
            self._extract_qwen(preprocessed_images, prompt)
        )

        gemini_result, gpt4v_result, qwen_result = results

        # Vote on fields
        consensus_data = self._vote_on_fields({
            'gemini': gemini_result,
            'gpt4v': gpt4v_result,
            'qwen': qwen_result
        })

        return consensus_data

    def _vote_on_fields(self, model_results: Dict) -> Dict:
        """
        Vote on each field using weighted consensus.

        Rules:
        1. If 2/3 models agree on value → use consensus
        2. If all disagree → use highest weight model (Gemini)
        3. If value is null in 2/3 models → return null
        4. For numbers: Use weighted average if all non-null
        """
        consensus = {}
        all_fields = set()

        # Collect all fields
        for result in model_results.values():
            all_fields.update(result.keys())

        # Vote on each field
        for field in all_fields:
            values = []
            for model_name, result in model_results.items():
                if field in result and result[field] is not None:
                    values.append({
                        'value': result[field],
                        'model': model_name,
                        'weight': self.weights[model_name]
                    })

            if len(values) == 0:
                # All null
                consensus[field] = None
            elif len(values) == 1:
                # Only one model has value
                consensus[field] = values[0]['value']
            elif len(values) >= 2:
                # Check for agreement
                if values[0]['value'] == values[1]['value']:
                    # 2/3 agree
                    consensus[field] = values[0]['value']
                elif len(values) == 3 and values[0]['value'] == values[2]['value']:
                    # 2/3 agree (first and third)
                    consensus[field] = values[0]['value']
                elif len(values) == 3 and values[1]['value'] == values[2]['value']:
                    # 2/3 agree (second and third)
                    consensus[field] = values[1]['value']
                else:
                    # All disagree - use highest weight
                    values.sort(key=lambda x: x['weight'], reverse=True)
                    consensus[field] = values[0]['value']

        return {
            "data": consensus,
            "confidence": self._calculate_consensus_confidence(model_results, consensus),
            "model_results": model_results,
            "agreement_rate": self._calculate_agreement_rate(model_results, consensus)
        }

    async def _extract_gemini(self, images: List, prompt: str) -> Dict:
        """Extract using Gemini 2.5-Pro."""
        # Implementation with Gemini API
        pass

    async def _extract_gpt4v(self, images: List, prompt: str) -> Dict:
        """Extract using GPT-4V."""
        # Implementation with OpenAI Vision API
        pass

    async def _extract_qwen(self, images: List, prompt: str) -> Dict:
        """Extract using Qwen 2.5-VL."""
        # Implementation with Qwen Vision API
        pass
```

---

### Step 4: Integration with Orchestrator (2-3 hours)

**File**: `gracian_pipeline/core/parallel_orchestrator.py` (modifications)

```python
# Add imports
from .pdf_classifier import PDFTypeClassifier
from .image_preprocessor import EnhancedImagePreprocessor
from .vision_consensus import VisionConsensus

def extract_all_agents_parallel(
    pdf_path: str,
    max_workers: int = 5,
    enable_retry: bool = True,
    enable_learning: bool = True,
    enable_vision_consensus: bool = True,  # NEW
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Extract with automatic PDF type detection and routing.

    NEW: Scanned PDFs get vision consensus treatment.
    """

    # Step 0: Classify PDF type
    classifier = PDFTypeClassifier()
    pdf_classification = classifier.classify_pdf(pdf_path)

    logger.info(f"PDF Type: {pdf_classification['type']} "
                f"(confidence: {pdf_classification['confidence']:.2f})")

    # Step 1-3: Standard extraction (Docling, sections, contexts)
    # ... existing code ...

    # Step 4: Route based on PDF type
    if pdf_classification['type'] == 'scanned' and enable_vision_consensus:
        # Use vision consensus for scanned PDFs
        logger.info("🔍 Using vision consensus for scanned PDF")
        vision_consensus = VisionConsensus()

        # Extract each agent with vision consensus
        for task in agent_tasks:
            result = await vision_consensus.extract_with_consensus(
                pdf_path=pdf_path,
                agent_id=task['agent_id'],
                pages=task['page_numbers'],
                prompt=task['agent_prompt']
            )
            # Store result with consensus metadata
            results[task['agent_id']] = result
    else:
        # Use standard text extraction for machine-readable PDFs
        logger.info("📄 Using text extraction for machine-readable PDF")
        # ... existing parallel extraction code ...

    return results
```

---

## 📈 EXPECTED IMPACT

### Performance Improvements
| PDF Type | Current Accuracy | After Phase 2 | Improvement |
|----------|------------------|---------------|-------------|
| **Machine-readable** | 48.9% | ~65% | +16pp |
| **Hybrid** | 30.5% | ~60% | +29.5pp |
| **Scanned** | 22.7% | **75-85%** | **+52-62pp** 🎯 |
| **Overall (weighted)** | 34.0% | **~70%** | **+36pp** |

### Cost Analysis
| Component | Before | After Phase 2 | Notes |
|-----------|--------|---------------|-------|
| Machine-readable (48%) | $0.05/PDF | $0.05/PDF | No change |
| Scanned (49%) | $0.05/PDF | $0.15/PDF | 3x models |
| Hybrid (2%) | $0.05/PDF | $0.10/PDF | Mixed |
| **Average** | **$0.05/PDF** | **$0.10/PDF** | 2x cost, 2x accuracy |

**ROI**: 13,300 scanned PDFs × (75% - 22.7%) accuracy = **+6,955 production-quality extractions**

---

## 🧪 GROUND TRUTH VALIDATION PLAN

### 100-PDF Ground Truth Calibration

**Goal**: Calibrate vision consensus against 100 perfect ground truth PDFs

**Process**:
1. **PDF Selection** (from your ground truth folder):
   - 50 scanned PDFs (critical for vision testing)
   - 30 machine-readable PDFs (baseline validation)
   - 20 hybrid PDFs (edge cases)

2. **Ground Truth Format**:
   ```json
   {
     "pdf_id": "brf_12345",
     "pdf_type": "scanned",
     "fields": {
       "chairman": "Erik Andersson",
       "address": "Kastellholmsvägen 14",
       "energy_class": "D",
       ...
     },
     "field_locations": {
       "chairman": {"page": 3, "bbox": [100, 200, 300, 220]},
       ...
     },
     "verified_by": "Human validator",
     "verified_at": "2025-10-14"
   }
   ```

3. **Calibration Metrics**:
   - **Accuracy per field**: % correct vs ground truth
   - **Accuracy per PDF type**: Scanned vs machine-readable
   - **Confidence calibration**: High confidence → high accuracy?
   - **Agreement rate**: 2/3 consensus → higher accuracy?

4. **Iterative Improvement**:
   - Run extraction on 100 PDFs
   - Compare vs ground truth
   - Identify systematic errors
   - Adjust preprocessing/prompts
   - Re-test until 85%+ accuracy on scanned PDFs

---

## ⏱️ IMPLEMENTATION TIMELINE

### Day 1 (6-8 hours)
- ✅ Step 1: PDF Type Classifier (2-3 hours)
- ✅ Step 2: Enhanced Image Preprocessing (3-4 hours)
- ✅ Testing on 5 scanned PDFs (1 hour)

### Day 2 (6-8 hours)
- ✅ Step 3: Multi-Model Vision Consensus (4-5 hours)
- ✅ Step 4: Integration with Orchestrator (2-3 hours)

### Day 3 (4-6 hours)
- ✅ Ground Truth Validation (100 PDFs)
- ✅ Calibration & tuning
- ✅ Documentation

**Total**: 16-22 hours (2-3 days)

---

## 🚀 NEXT STEPS

1. **Immediate**: Implement PDF Type Classifier (2-3 hours)
2. **Then**: Enhanced Image Preprocessing (3-4 hours)
3. **Then**: Multi-Model Vision Consensus (4-5 hours)
4. **Then**: Ground Truth Calibration (4-6 hours)
5. **Finally**: Production deployment for 27,000 PDFs

**Ready to begin?** I'll start with the PDF Type Classifier implementation.

---

**Generated**: October 14, 2025
**Author**: Claude Code (Sonnet 4.5)
**Status**: 🚀 **READY TO IMPLEMENT**
**Next Action**: Implement PDFTypeClassifier class
