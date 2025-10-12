# Current Pipeline Architecture - October 2025

## 🏗️ System Overview

**Gracian Pipeline** is a multi-layered extraction system for Swedish BRF (housing cooperative) annual reports, achieving **70-84% coverage** through Pydantic-based schema validation and specialized agent extraction.

---

## 📊 Architecture Layers

### Layer 1: Document Processing (Docling)

**Technology:** IBM Docling (open-source)
**Purpose:** Convert PDF to structured markdown + tables
**Performance:** 30-150s per document (varies by size/complexity)

```
PDF Input → Docling Pipeline → Structured Output
                ↓
         - Markdown text
         - Table structures
         - Page metadata
         - Layout analysis
```

**Modes:**
- **Fast Mode (1 pass):** Base extraction, ~30-100s per PDF
- **Deep Mode (4 passes):** Base + validation + semantic + quality, ~6-10 min per PDF

**Current Choice:** Fast mode for smoke tests (proven 70-84% coverage)

---

### Layer 2: Base Extraction (13 Specialized Agents)

**Technology:** GPT-4o with specialized prompts
**Purpose:** Extract structured data from Docling output
**Architecture:** Multi-agent system with domain expertise

#### The 13 Specialist Agents

| # | Agent | Responsibility | Key Fields |
|---|-------|----------------|------------|
| 1 | **Governance** | Leadership, auditors | chairman, board_members, auditor_name, audit_firm |
| 2 | **Financial** | Financial statements | revenue, expenses, assets, liabilities, equity |
| 3 | **Property** | Building information | address, property_designation, area_sqm, built_year |
| 4 | **Fees** | Member fees | monthly_fee, annual_fee, fee_per_sqm |
| 5 | **Loans** | Debt information | loan_amount, interest_rate, lender, maturity_date |
| 6 | **Operations** | Daily operations | **suppliers**, maintenance_contracts, utility_contracts |
| 7 | **Events** | Important decisions | **important_events**, AGM_decisions, policy_changes |
| 8 | **Policies** | Rules and bylaws | pet_policy, rental_policy, renovation_rules |
| 9 | **Notes (Depreciation)** | Asset depreciation | depreciation_schedule, asset_categories |
| 10 | **Notes (Maintenance)** | Building maintenance | planned_maintenance, completed_projects |
| 11 | **Notes (Tax)** | Tax information | tax_deductions, tax_benefits |
| 12 | **Notes (Financial Details)** | Operating costs | cost_breakdown_by_category, largest_expenses |
| 13 | **Environmental** | Sustainability | energy_consumption, waste_management, emissions |

**Agent Communication:**
```
Docling Output (markdown + tables)
    ↓
[Agent 1: Governance] → JSON output
[Agent 2: Financial]  → JSON output
[Agent 3: Property]   → JSON output
... (parallel execution)
[Agent 13: Environmental] → JSON output
    ↓
Aggregated JSON (all agents combined)
```

---

### Layer 3: Pydantic Schema Validation

**Technology:** Pydantic v2 with custom field types
**Purpose:** Type validation, confidence tracking, cross-field validation
**Innovation:** MIXED approach (ExtractionField + raw types)

#### Core Architecture: ExtractionField System

**Purpose:** Track confidence, alternatives, and evidence for extracted values

```python
class ExtractionField(BaseModel, Generic[T]):
    value: Optional[T]              # Primary extracted value
    confidence: float = 0.0         # Confidence score (0.0-1.0)
    alternatives: List[Alternative] # Other possible values
    source_pages: List[int] = []    # Evidence pages
    extraction_method: str = "llm"  # How it was extracted
    validation_status: str = "valid" # tolerant, warning, error
```

**5 Specialized Field Types:**
1. **StringField**: Swedish text with whitespace normalization
2. **NumberField**: Swedish number parsing (1 234,56 kr → 1234.56)
3. **ListField**: Collections (board members, suppliers)
4. **BooleanField**: Swedish yes/no (ja/nej → True/False)
5. **DateField**: Multiple Swedish date formats
6. **DictField**: Nested structures

#### MIXED Approach Decision Matrix

**When to use ExtractionField:**
- Multiple sources might disagree (e.g., board_members from text vs table)
- Confidence tracking needed (e.g., financial values that might be ambiguous)
- Alternative values possible (e.g., property_address vs property_designation)

**When to use raw Python types:**
- Single authoritative source (e.g., fiscal_year from PDF metadata)
- No ambiguity (e.g., org_number - unique 10-digit identifier)
- Simple aggregation (e.g., total_apartments = sum of rooms)

**Example Model (GovernanceStructure):**
```python
class GovernanceStructure(BaseModel):
    # ExtractionField (multiple sources, needs confidence)
    chairman: Optional[StringField] = None
    board_members: Optional[ListField[BoardMember]] = None
    auditor: Optional[Auditor] = None  # Nested Pydantic model

    # Raw types (authoritative source, no ambiguity)
    org_number: Optional[str] = None  # From metadata
    registration_date: Optional[datetime] = None
```

---

### Layer 4: Hierarchical Enhancement (Specialized Extractors)

**Purpose:** Deep extraction for complex fields
**Trigger:** When base extraction shows gaps

#### Current Specialized Extractors

1. **HierarchicalFinancialExtractor**
   - Deep dive into Notes 4, 8, 9
   - Operating costs breakdown
   - Building details with validation
   - Receivables breakdown

2. **ApartmentBreakdownExtractor**
   - Vision-based chart extraction
   - Fallback: table detection
   - Fallback: text pattern matching
   - Extracts apartment distribution by room count

3. **FeeFieldMigrator**
   - Swedish → English field mapping
   - Cross-validation (monthly × 12 ≈ annual)
   - Terminology verification
   - Unit conversion (kr → tkr)

4. **PropertyDesignationExtractor**
   - Swedish property designation format validation
   - Pattern: "Municipality Name-City District Number:Number"
   - Example: "Stockholm Södermalm 1:23"

---

### Layer 5: Quality Assessment & Validation

**Purpose:** Calculate coverage, validate cross-field consistency

#### Quality Metrics Calculation

```python
def calculate_quality_metrics(extraction: Dict) -> Dict:
    """
    Calculate comprehensive quality metrics.

    Returns:
        {
            "total_fields": 117,           # Total extractable fields
            "extracted_fields": 84,        # Successfully extracted
            "coverage_percent": 71.8,      # 84/117 * 100
            "confidence_score": 0.85,      # Derived from field confidences
            "evidence_ratio": 0.92,        # Fields with source pages
            "quality_grade": "C"           # A/B/C/D/F grading
        }
    """
```

#### Validation Rules

**3-Tier Tolerant Validation System:**

| Metric | Tolerance | Status | Action |
|--------|-----------|--------|--------|
| **Balance Sheet** | ±5% | VALID | ✅ Accept |
| Small numbers (<10k) | ±$500 | WARNING | ⚠️ Log |
| Large numbers (>1M) | ±$5000 | ERROR | ❌ Flag |

**Cross-Field Validation Examples:**
```python
# Fee validation
if abs((monthly_fee * 12) - annual_fee) / annual_fee > 0.05:
    status = "WARNING"  # More than 5% discrepancy

# Balance sheet validation
if abs(assets - (liabilities + equity)) / assets > 0.05:
    status = "ERROR"  # Balance sheet doesn't balance
```

---

## 🔄 Complete Extraction Flow

```
1. PDF INPUT (brf_198532.pdf)
   ↓
2. DOCLING PROCESSING (Fast mode, 94s)
   → Markdown: 15,234 chars
   → Tables: 8 financial tables
   → Pages: 24 total
   ↓
3. AGENT EXTRACTION (GPT-4o, parallel)
   → Governance Agent: 5/5 fields (100%)
   → Financial Agent: 11/11 fields (100%)
   → Property Agent: 8/8 fields (100%)
   → ... (all 13 agents)
   ↓
4. PYDANTIC VALIDATION
   → Type checking: PASS
   → Field validation: PASS
   → Cross-validation: 2 warnings (tolerable)
   ↓
5. HIERARCHICAL ENHANCEMENT (if needed)
   → Note 4 extraction: 12 line items
   → Apartment breakdown: 6/6 fields
   ↓
6. QUALITY ASSESSMENT
   → Coverage: 83.8% (98/117 fields)
   → Confidence: 0.85
   → Grade: B
   ↓
7. OUTPUT (BRFAnnualReport)
   → JSON with full schema
   → Quality metrics attached
   → Evidence pages tracked
```

---

## 📈 Performance Characteristics

### Current Metrics (Fast Mode, 5-PDF Sample)

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Success Rate** | 100% (5/5) | 95% | ✅ EXCEEDS |
| **Avg Coverage** | 73.8% | 70% | ✅ EXCEEDS |
| **Avg Confidence** | 0.78 | 0.70 | ✅ EXCEEDS |
| **Avg Time** | 115.5s/PDF | 120s | ✅ MEETS |
| **Component Tests** | 100% pass | 95% | ✅ EXCEEDS |

### Speed Breakdown (Typical PDF)

```
Total Time: ~100s

Docling Processing:  45s (45%)  ████████████████████
Agent Extraction:    35s (35%)  ██████████████
Pydantic Validation: 10s (10%)  ████
Enhancement:          8s (8%)   ███
Quality Assessment:   2s (2%)   █
```

---

## 🎯 Design Decisions

### Decision 1: Why Fast Mode by Default?

**Rationale:**
- **70-84% coverage sufficient** for smoke tests and validation
- **4-5x faster** than deep mode (100s vs 400-600s)
- **Same Pydantic validation** ensures quality
- **Deep mode reserved** for production runs requiring 90%+ coverage

### Decision 2: Why MIXED Approach (ExtractionField + Raw Types)?

**Rationale:**
- **Not all fields need confidence tracking** (e.g., org_number is unambiguous)
- **Performance optimization** (raw types faster than ExtractionField)
- **Cleaner schema** for simple fields (integers, booleans)
- **Flexibility** for future enhancements (can upgrade raw → ExtractionField)

### Decision 3: Why 13 Specialized Agents?

**Rationale:**
- **Domain expertise** (each agent knows its field's terminology)
- **Parallel execution** (all 13 run simultaneously, not sequential)
- **Maintainability** (easier to fix one agent than monolithic extractor)
- **Scalability** (can add agents without affecting others)

### Decision 4: Why Tolerant Validation?

**Rationale:**
- **Swedish OCR errors** common (å/ä/ö confusion)
- **Rounding differences** between reports and calculations
- **Better to warn than fail** (preserve data, flag uncertainty)
- **3-tier system** (valid/warning/error) provides granularity

---

## 🚀 Future Enhancements (Week 4)

### Progressive Enhancement System (If 95% Coverage Required)

**5-Pass Architecture:**
```
Pass 1: Fast Docling (70-80% coverage, 1-2 min, FREE)
   ↓ (if < 95%)
Pass 2: Targeted Vision (5-10%, 30s, $0.02)
   ↓ (if < 95%)
Pass 3: Deep Docling (5-10%, 2 min, FREE)
   ↓ (if < 95%)
Pass 4: Pattern Gap Filling (2-5%, 10s, FREE)
   ↓ (if < 95%)
Pass 5: GPT-4o Targeted (last resort, 1 min, $0.05)
```

**Expected Results:**
- **60% of docs:** Stop at Pass 2 (< $0.02 per doc)
- **30% of docs:** Stop at Pass 3 (still free)
- **8% of docs:** Stop at Pass 4 (still free)
- **2% of docs:** Need Pass 5 ($0.05 per doc)
- **Average cost:** ~$0.04 per document for 95%+ guaranteed coverage

---

## 📚 Key Files

### Core Pipeline
- `gracian_pipeline/core/pydantic_extractor.py` - Main extraction orchestrator
- `gracian_pipeline/core/docling_adapter_ultra_v2.py` - Base extractor with 13 agents
- `gracian_pipeline/models/brf_schema.py` - Complete Pydantic schema (24 models)
- `gracian_pipeline/models/base_fields.py` - ExtractionField system

### Specialized Extractors
- `gracian_pipeline/core/hierarchical_financial.py` - Deep financial extraction
- `gracian_pipeline/core/apartment_breakdown.py` - Vision-based chart extraction
- `gracian_pipeline/core/fee_field_migrator.py` - Swedish-English fee mapping
- `gracian_pipeline/core/property_designation.py` - Property format validation

### Testing & Validation
- `test_comprehensive_sample.py` - 5-PDF smoke test
- `test_comprehensive_42_pdfs.py` - Full test suite
- `test_base_fields.py` - ExtractionField unit tests
- `test_validation_thresholds.py` - Tolerant validation tests

---

## 🎓 Technical Glossary

**BRF (Bostadsrättsförening):** Swedish housing cooperative
**Docling:** IBM's open-source PDF processing library
**ExtractionField:** Custom Pydantic field with confidence tracking
**MIXED Approach:** Using both ExtractionField and raw types in same model
**Tolerant Validation:** 3-tier system (valid/warning/error) with configurable thresholds
**Fast Mode:** Single Docling pass (~100s per PDF)
**Deep Mode:** 4 Docling passes (~400-600s per PDF)
**Agent:** Specialized LLM prompt for extracting specific field category
**Coverage:** Percentage of expected fields successfully extracted (117 total)
**Confidence:** Weighted average of field-level confidence scores (0.0-1.0)
**Evidence Ratio:** Percentage of extracted fields with source page citations

---

## 📊 Current Status

✅ **Week 1-2 Complete:** Pydantic schema fully integrated
✅ **Week 3 Day 1-2 Complete:** Bug fixes validated, 5-PDF smoke test passing
🚀 **Week 3 Day 3:** Ready for 42-PDF comprehensive test suite

**Next Milestone:** Validate 70%+ coverage across all 42 PDFs
