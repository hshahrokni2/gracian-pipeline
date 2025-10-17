# Schema Migration Guide: Phase 0 → Week 2

**Purpose**: Comprehensive guide for migrating from Phase 0 baseline schema to enhanced Week 2 schema with classification and intelligence layers

**Date**: October 17, 2025
**Target**: Week 2 Day 1 re-extraction preparation
**Impact**: 40+ new fields, 4 new output categories

---

## 📊 Overview

### **What Changed in Phase 0**

Phase 0 added **40+ new fields** across 4 categories:

1. **Enhanced Financial Fields** (Day 2) - 8 fields
2. **Governance Enhancements** (Day 1) - 5 fields
3. **Property Enhancements** (Day 2-3) - 7 fields
4. **Classification Outputs** (Day 4) - 20+ fields

### **Migration Scope**

| Component | Changes | Effort | Impact |
|-----------|---------|--------|--------|
| **Pydantic Schemas** | +40 fields, 4 new classes | 30 min | HIGH |
| **Agent Prompts** | Enhanced 8 agents | 45 min | HIGH |
| **Validation Rules** | +15 validation rules | 20 min | MEDIUM |
| **Database Schema** | +4 tables (optional) | 60 min | LOW |
| **Test Suites** | +20 test cases | 30 min | MEDIUM |

**Total Effort**: 3-4 hours

---

## 🗂️ Field Changes Catalog

### **1. Enhanced Financial Fields** (Day 2)

#### **New Fields**

| Field Name | Type | Purpose | Example |
|------------|------|---------|---------|
| `result_without_depreciation_current_year` | `int` | Cash flow before depreciation | `1_057_081` |
| `result_without_depreciation_prior_year` | `int` | Prior year cash flow | `945_230` |
| `cash_to_debt_ratio_current_year` | `float` | Cash as % of debt | `8.5` |
| `cash_to_debt_ratio_prior_year` | `float` | Prior year ratio | `7.2` |
| `interest_expense_to_revenue_ratio` | `float` | Interest burden | `18.5` |
| `interest_expense_yoy_increase_pct` | `float` | YoY interest change | `82.6` |
| `reserve_fund_to_revenue_ratio` | `float` | Reserve adequacy | `22.5` |
| `operating_income` | `int` | Operating profit | `950_000` |

#### **Schema Update**

```python
# gracian_pipeline/core/schema_comprehensive.py

from pydantic import BaseModel, Field
from typing import Optional

class FinancialData(BaseModel):
    # Existing fields...
    assets: Optional[int] = Field(None, description="Total assets (SEK)")
    liabilities: Optional[int] = Field(None, description="Total liabilities (SEK)")

    # NEW FIELDS - Phase 0 Day 2
    result_without_depreciation_current_year: Optional[int] = Field(
        None,
        description="Resultat före avskrivningar - current year (SEK)",
        alias="resultat_fore_avskrivningar_current"
    )

    result_without_depreciation_prior_year: Optional[int] = Field(
        None,
        description="Resultat före avskrivningar - prior year (SEK)"
    )

    cash_to_debt_ratio_current_year: Optional[float] = Field(
        None,
        description="Cash to debt ratio - current year (%)",
        ge=0,  # Validation: non-negative
        le=100
    )

    cash_to_debt_ratio_prior_year: Optional[float] = Field(
        None,
        description="Cash to debt ratio - prior year (%)",
        ge=0,
        le=100
    )

    interest_expense_to_revenue_ratio: Optional[float] = Field(
        None,
        description="Interest expense as % of total revenue",
        ge=0
    )

    interest_expense_yoy_increase_pct: Optional[float] = Field(
        None,
        description="YoY change in interest expense (%)"
    )

    reserve_fund_to_revenue_ratio: Optional[float] = Field(
        None,
        description="Reserve fund (underhållsfond) as % of revenue",
        ge=0
    )

    operating_income: Optional[int] = Field(
        None,
        description="Operating income (before interest/depreciation)"
    )
```

#### **Migration Steps**

1. **Update schema file** (5 minutes)
   ```bash
   # Edit gracian_pipeline/core/schema_comprehensive.py
   # Add 8 new fields to FinancialData class
   ```

2. **Update agent prompts** (15 minutes)
   ```python
   # gracian_pipeline/prompts/agent_prompts.py

   # Enhanced financial_agent prompt
   FINANCIAL_AGENT_PROMPT = """
   Extract the following financial data from the BRF annual report:

   ... [existing fields] ...

   NEW FIELDS:
   12. "result_without_depreciation_current_year": Resultat före avskrivningar (current year)
   13. "result_without_depreciation_prior_year": Resultat före avskrivningar (prior year)
   14. "cash_to_debt_ratio_current_year": Cash to debt ratio (%)
   15. "interest_expense_to_revenue_ratio": Interest expense as % of revenue

   IMPORTANT:
   - Result before depreciation is typically in Note 1 (Resultaträkning) or income statement footer
   - Cash to debt ratio = (Cash + short-term investments) / Total debt * 100
   - Cite source pages for all extractions
   """
   ```

3. **Update validation rules** (10 minutes)
   ```python
   # gracian_pipeline/classification/data_validator.py

   # Add to VALID_RANGES
   VALID_RANGES = {
       # Existing...
       'cash_to_debt_ratio_current_year': (0, 100),
       'cash_to_debt_ratio_prior_year': (0, 100),
       'interest_expense_to_revenue_ratio': (0, 100),
   }

   # Add to CALCULATED_FIELDS verification
   def _verify_cash_to_debt_ratio(self, data):
       """Verify cash-to-debt ratio calculation."""
       cash = data.get('cash_current_year')
       debt = data.get('total_debt')
       ratio = data.get('cash_to_debt_ratio_current_year')

       if cash and debt and debt > 0:
           expected_ratio = (cash / debt) * 100
           if ratio and abs(ratio - expected_ratio) > 1.0:
               return ValidationWarning(
                   field='cash_to_debt_ratio_current_year',
                   message=f'Calculated {expected_ratio:.1f}%, provided {ratio:.1f}%'
               )
       return None
   ```

4. **Update tests** (10 minutes)
   ```python
   # test_phase0_day2_integration.py

   def test_enhanced_financial_extraction():
       """Test extraction of new financial fields."""
       result = extract_financial_data('test_pdfs/brf_198532.pdf')

       # Test new fields present
       assert result.result_without_depreciation_current_year is not None
       assert result.cash_to_debt_ratio_current_year is not None

       # Test validation
       assert 0 <= result.cash_to_debt_ratio_current_year <= 100
   ```

---

### **2. Governance Enhancements** (Day 1)

#### **New Fields**

| Field Name | Type | Purpose | Example |
|------------|------|---------|---------|
| `board_members` | `List[BoardMember]` | Full board composition | `[{name, role, period}]` |
| `board_member_count` | `int` | Total board size | `7` |
| `nomination_committee` | `List[str]` | Valberedning members | `["Anna Svensson", "Erik Johansson"]` |
| `auditor_company` | `str` | Revisionsbolag name | `"HQV Stockholm AB"` |
| `auditor_type` | `str` | Authorized vs. approved | `"Authorized"` |

#### **Schema Update**

```python
# gracian_pipeline/core/schema_comprehensive.py

class BoardMember(BaseModel):
    """Individual board member details."""
    name: str = Field(..., description="Full name")
    role: Optional[str] = Field(None, description="Role (ordförande, ledamot, etc.)")
    period: Optional[str] = Field(None, description="Period served")

class GovernanceData(BaseModel):
    # Existing fields...
    chairman: Optional[str] = Field(None, description="Board chairman name")

    # NEW FIELDS - Phase 0 Day 1
    board_members: Optional[List[BoardMember]] = Field(
        default_factory=list,
        description="Full board composition"
    )

    board_member_count: Optional[int] = Field(
        None,
        description="Total number of board members",
        ge=3,  # Swedish law requires minimum 3
        le=15  # Sanity check
    )

    nomination_committee: Optional[List[str]] = Field(
        default_factory=list,
        description="Valberedning members"
    )

    auditor_company: Optional[str] = Field(
        None,
        description="Revisionsbolag (auditing company name)"
    )

    auditor_type: Optional[str] = Field(
        None,
        description="Authorized (auktoriserad) or approved (godkänd)"
    )
```

#### **Migration Steps**

1. **Add BoardMember class** (5 minutes)
2. **Update governance_agent prompts** (15 minutes)
3. **Update validation rules** (5 minutes - check board_member_count matches len(board_members))
4. **Update tests** (10 minutes)

---

### **3. Property Enhancements** (Day 2-3)

#### **New Fields**

| Field Name | Type | Purpose | Example |
|------------|------|---------|---------|
| `lokaler_area_sqm` | `int` | Commercial space area | `850` |
| `lokaler_area_percentage` | `float` | % of total area | `10.0` |
| `lokaler_revenue` | `int` | Commercial revenue | `4_800_000` |
| `lokaler_revenue_percentage` | `float` | % of total revenue | `38.4` |
| `tomtratt_cost_current_year` | `int` | Ground lease cost | `3_200_000` |
| `tomtratt_cost_prior_year` | `int` | Prior year cost | `1_450_000` |
| `tomtratt_escalation_percent` | `float` | YoY escalation | `120.7` |
| `tomtratt_percent_of_operating_costs` | `float` | % of operating budget | `17.3` |
| `maturity_cluster_months` | `int` | Months to loan cluster | `8` |

#### **Schema Update**

```python
# gracian_pipeline/core/schema_comprehensive.py

class PropertyData(BaseModel):
    # Existing fields...
    total_area: Optional[int] = Field(None, description="Total area (sqm)")

    # NEW FIELDS - Phase 0 Day 2-3
    lokaler_area_sqm: Optional[int] = Field(
        None,
        description="Commercial space area (sqm)"
    )

    lokaler_area_percentage: Optional[float] = Field(
        None,
        description="Commercial space as % of total area",
        ge=0,
        le=100
    )

    lokaler_revenue: Optional[int] = Field(
        None,
        description="Revenue from commercial tenants (SEK)"
    )

    lokaler_revenue_percentage: Optional[float] = Field(
        None,
        description="Commercial revenue as % of total revenue",
        ge=0,
        le=100
    )

    tomtratt_cost_current_year: Optional[int] = Field(
        None,
        description="Tomträtt (ground lease) cost - current year (SEK)"
    )

    tomtratt_cost_prior_year: Optional[int] = Field(
        None,
        description="Tomträtt cost - prior year (SEK)"
    )

    tomtratt_escalation_percent: Optional[float] = Field(
        None,
        description="YoY change in tomträtt cost (%)"
    )

    tomtratt_percent_of_operating_costs: Optional[float] = Field(
        None,
        description="Tomträtt as % of total operating costs",
        ge=0,
        le=100
    )

class LoanData(BaseModel):
    # Existing fields...

    # NEW FIELD - Phase 0 Day 3
    maturity_cluster_months: Optional[int] = Field(
        None,
        description="Months until majority (>50%) of loans mature",
        ge=0
    )
```

#### **Migration Steps**

1. **Update PropertyData class** (10 minutes)
2. **Update property_agent prompts** (20 minutes)
   ```python
   PROPERTY_AGENT_PROMPT = """
   NEW EXTRACTION TARGETS:

   Lokaler (Commercial Spaces):
   - Look in Note 2 (Lokaler) or building description
   - Extract: area (sqm), revenue (SEK), tenant types
   - Calculate lokaler_area_percentage = lokaler_area / total_area * 100

   Tomträtt (Ground Lease):
   - Look in Note 5 (Tomträtt) or operating costs
   - Extract: current cost, prior year cost
   - Calculate escalation_percent = (current - prior) / prior * 100
   - Calculate percent_of_operating_costs = tomtratt / total_costs * 100

   Loan Maturity:
   - Look in Note 6 (Loans) or financial statements
   - Identify maturity dates for all loans
   - Calculate maturity_cluster_months: months until >50% of loans mature
   """
   ```

3. **Update validation rules** (10 minutes)
4. **Update tests** (15 minutes)

---

### **4. Classification Outputs** (Day 4)

#### **New Output Structure**

Day 4 added complete classification and scoring output:

```python
# gracian_pipeline/classification/output_schema.py

from pydantic import BaseModel
from typing import Dict, Optional, List

class PatternDetectionOutput(BaseModel):
    """Pattern classification results."""

    # Categorical patterns
    refinancing_risk_tier: Optional[str] = Field(
        None,
        description="EXTREME / HIGH / MEDIUM / NONE"
    )

    fee_response_classification: Optional[str] = Field(
        None,
        description="DISTRESS / REACTIVE / AGGRESSIVE / PROACTIVE"
    )

    lokaler_dependency_risk_tier: Optional[str] = Field(
        None,
        description="HIGH / MEDIUM_HIGH / MEDIUM / LOW"
    )

    tomtratt_escalation_risk_tier: Optional[str] = Field(
        None,
        description="EXTREME / HIGH / MEDIUM / LOW / NONE"
    )

    # Boolean patterns
    depreciation_paradox_detected: Optional[bool] = Field(
        None,
        description="True if pattern detected"
    )

    cash_crisis_detected: Optional[bool] = Field(
        None,
        description="True if pattern detected"
    )

    pattern_b_detected: Optional[bool] = Field(
        None,
        description="True if young BRF with chronic losses"
    )

    interest_rate_victim_detected: Optional[bool] = Field(
        None,
        description="True if profit lost to rate shock"
    )

    # Evidence trails
    pattern_evidence: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Evidence for each pattern detection"
    )

    pattern_confidence: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Confidence scores (0-1) for each pattern"
    )


class RiskScoringOutput(BaseModel):
    """Composite risk scores."""

    management_quality_score: Optional[float] = Field(
        None,
        description="0-100 score",
        ge=0,
        le=100
    )

    management_quality_grade: Optional[str] = Field(
        None,
        description="A / B / C / D / F"
    )

    stabilization_probability_score: Optional[float] = Field(
        None,
        description="0-100 score",
        ge=0,
        le=100
    )

    operational_health_score: Optional[float] = Field(
        None,
        description="0-100 score",
        ge=0,
        le=100
    )

    structural_risk_score: Optional[float] = Field(
        None,
        description="0-100 score (HIGHER = HIGHER RISK)",
        ge=0,
        le=100
    )

    # Factor breakdowns
    scoring_factors: Optional[Dict[str, Dict[str, float]]] = Field(
        default_factory=dict,
        description="Detailed factor scores for each composite score"
    )


class ComparativeIntelligenceOutput(BaseModel):
    """Population comparison results."""

    soliditet_percentile: Optional[float] = Field(
        None,
        description="0-100 percentile rank",
        ge=0,
        le=100
    )

    soliditet_category: Optional[str] = Field(
        None,
        description="Well Above / Above / Average / Below / Well Below"
    )

    debt_per_sqm_percentile: Optional[float] = Field(None, ge=0, le=100)
    debt_per_sqm_category: Optional[str] = None

    fee_per_sqm_percentile: Optional[float] = Field(None, ge=0, le=100)
    fee_per_sqm_category: Optional[str] = None

    # Narratives
    comparative_narratives: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Human-readable comparison narratives"
    )


class ComprehensiveOutput(BaseModel):
    """Complete extraction + classification + intelligence output."""

    # Existing extraction output
    governance: GovernanceData
    financial: FinancialData
    property: PropertyData

    # NEW - Phase 0 Day 4 outputs
    pattern_detection: Optional[PatternDetectionOutput] = None
    risk_scoring: Optional[RiskScoringOutput] = None
    comparative_intelligence: Optional[ComparativeIntelligenceOutput] = None
```

#### **Migration Steps**

1. **Create output schema classes** (30 minutes)
2. **Update extraction pipeline** (20 minutes)
   ```python
   # gracian_pipeline/core/enhanced_pipeline.py

   def extract_with_intelligence(pdf_path: str) -> ComprehensiveOutput:
       """Extract + classify + score + compare."""

       # Step 1: Extract raw data
       raw_data = extract_all_agents_parallel(pdf_path)

       # Step 2: Validate and normalize
       from gracian_pipeline.classification import DataValidator
       validator = DataValidator()
       validation_result = validator.validate(raw_data)

       if not validation_result.valid:
           logger.warning(f"Validation warnings: {validation_result.warnings}")

       normalized_data = validation_result.normalized_data

       # Step 3: Pattern classification
       from gracian_pipeline.classification import PatternClassifier
       classifier = PatternClassifier('config/pattern_classification_rules.yaml')

       patterns = {}
       for pattern_name in classifier.get_pattern_names():
           result = classifier.classify(pattern_name, normalized_data)
           patterns[pattern_name] = result

       # Step 4: Risk scoring
       from gracian_pipeline.classification import RiskScorer
       scorer = RiskScorer()
       scores = scorer.calculate_all_scores(patterns, normalized_data)

       # Step 5: Comparative analysis
       from gracian_pipeline.classification import ComparativeAnalyzer
       analyzer = ComparativeAnalyzer()
       comparisons = analyzer.compare_multiple_metrics(normalized_data)

       # Step 6: Compile comprehensive output
       return ComprehensiveOutput(
           governance=raw_data['governance'],
           financial=raw_data['financial'],
           property=raw_data['property'],
           pattern_detection=patterns,
           risk_scoring=scores,
           comparative_intelligence=comparisons
       )
   ```

3. **Update tests** (20 minutes)

---

## 🔄 Backward Compatibility Strategy

### **Principle**: All new fields are Optional

**Why**: Existing extraction code should continue working without modification

### **Implementation**

```python
# All new fields use Optional with default None
result_without_depreciation_current_year: Optional[int] = Field(
    None,  # Default = None (backward compatible)
    description="..."
)

# List fields use default_factory
board_members: Optional[List[BoardMember]] = Field(
    default_factory=list,  # Default = empty list
    description="..."
)
```

### **Graceful Degradation**

Classification layers handle missing data gracefully:

```python
# Pattern classifier with partial data
result = classifier.classify('refinancing_risk', {
    'kortfristig_skulder_ratio': 55.2  # Only 1 of 3 fields
})

# Result includes confidence score reflecting data completeness
# confidence = 0.45 (only 1/3 fields present, but still classifies)
```

---

## 📦 Database Schema Changes (Optional)

### **Option 1: JSON Columns** (Recommended for Week 2)

Store classification outputs in existing JSON columns:

```sql
-- No schema changes needed!
-- Use existing extraction_results.json_data column

-- Store comprehensive output
INSERT INTO extraction_results (pdf_path, json_data) VALUES (
  'path/to/brf.pdf',
  '{
    "governance": {...},
    "financial": {...},
    "pattern_detection": {
      "refinancing_risk_tier": "HIGH",
      "depreciation_paradox_detected": true
    },
    "risk_scoring": {
      "management_quality_score": 72.5,
      "management_quality_grade": "B"
    }
  }'::jsonb
);
```

### **Option 2: Dedicated Tables** (Future Production)

Create separate tables for classification outputs:

```sql
-- Create pattern_detection table
CREATE TABLE pattern_detection (
    id SERIAL PRIMARY KEY,
    extraction_id INTEGER REFERENCES extraction_results(id),
    pdf_path TEXT,

    -- Categorical patterns
    refinancing_risk_tier VARCHAR(20),
    fee_response_classification VARCHAR(20),
    lokaler_dependency_risk_tier VARCHAR(20),
    tomtratt_escalation_risk_tier VARCHAR(20),

    -- Boolean patterns
    depreciation_paradox_detected BOOLEAN,
    cash_crisis_detected BOOLEAN,
    pattern_b_detected BOOLEAN,
    interest_rate_victim_detected BOOLEAN,

    -- Metadata
    pattern_evidence JSONB,
    pattern_confidence JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create risk_scoring table
CREATE TABLE risk_scoring (
    id SERIAL PRIMARY KEY,
    extraction_id INTEGER REFERENCES extraction_results(id),

    management_quality_score NUMERIC(5,2),
    management_quality_grade VARCHAR(1),

    stabilization_probability_score NUMERIC(5,2),
    operational_health_score NUMERIC(5,2),
    structural_risk_score NUMERIC(5,2),

    scoring_factors JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create comparative_intelligence table
CREATE TABLE comparative_intelligence (
    id SERIAL PRIMARY KEY,
    extraction_id INTEGER REFERENCES extraction_results(id),

    soliditet_percentile NUMERIC(5,2),
    soliditet_category VARCHAR(30),

    debt_per_sqm_percentile NUMERIC(5,2),
    fee_per_sqm_percentile NUMERIC(5,2),

    comparative_narratives JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_pattern_refinancing ON pattern_detection(refinancing_risk_tier);
CREATE INDEX idx_pattern_crisis ON pattern_detection(cash_crisis_detected) WHERE cash_crisis_detected = true;
CREATE INDEX idx_risk_management ON risk_scoring(management_quality_grade);
```

**Recommendation**: Use Option 1 (JSON columns) for Week 2, migrate to Option 2 after validating classification accuracy on larger corpus.

---

## ✅ Week 2 Day 1 Migration Checklist

### **Pre-Migration (30 minutes)**

- [ ] **Backup current schemas**
  ```bash
  cp gracian_pipeline/core/schema_comprehensive.py \
     gracian_pipeline/core/schema_comprehensive.py.backup
  ```

- [ ] **Review Phase 0 documentation**
  - Read PHASE_0_COMPLETE_SUMMARY.md
  - Read PATTERN_CATALOG_WITH_EXAMPLES.md
  - Understand all 40 new fields

- [ ] **Set up test environment**
  ```bash
  # Create test branch
  git checkout -b week2-schema-migration

  # Install dependencies
  pip install -r requirements.txt
  ```

### **Schema Updates (60 minutes)**

- [ ] **Update Pydantic schemas** (30 minutes)
  - Add 8 enhanced financial fields
  - Add 5 governance fields
  - Add 9 property/loan fields
  - Create classification output schemas

- [ ] **Update validation rules** (15 minutes)
  - Add range validation for new fields
  - Add calculated field verification
  - Add cross-field consistency checks

- [ ] **Update type hints** (15 minutes)
  - Ensure all Optional fields properly marked
  - Add default factories for list fields
  - Update docstrings

### **Agent Prompt Updates** (45 minutes)**

- [ ] **Update financial_agent** (15 minutes)
  - Add result_without_depreciation extraction
  - Add cash-to-debt ratio calculation
  - Add interest expense analysis

- [ ] **Update governance_agent** (10 minutes)
  - Add board_members list extraction
  - Add nomination_committee extraction
  - Add auditor_company extraction

- [ ] **Update property_agent** (15 minutes)
  - Add lokaler extraction (area + revenue)
  - Add tomträtt extraction (cost + escalation)

- [ ] **Update loans_agent** (5 minutes)
  - Add maturity_cluster_months calculation

### **Testing & Validation** (60 minutes)**

- [ ] **Run existing tests** (15 minutes)
  ```bash
  pytest test_phase0_day1_agents.py
  pytest test_phase0_day2_integration.py
  pytest test_phase0_day3_validation.py
  ```

- [ ] **Run classification tests** (10 minutes)
  ```bash
  pytest test_phase0_day4_classification.py
  ```

- [ ] **Test on sample PDFs** (30 minutes)
  ```bash
  python -c "
  from gracian_pipeline.core.enhanced_pipeline import extract_with_intelligence

  # Test on 3 diverse PDFs
  for pdf in ['brf_198532.pdf', 'brf_268882.pdf', 'brf_81563.pdf']:
      result = extract_with_intelligence(f'test_pdfs/{pdf}')
      print(f'{pdf}: {result.pattern_detection.refinancing_risk_tier}')
  "
  ```

- [ ] **Validate backward compatibility** (5 minutes)
  ```python
  # Test that old code still works
  from gracian_pipeline.core.pydantic_extractor import extract_single_agent

  result = extract_single_agent('governance_agent', 'test_pdfs/brf_198532.pdf')
  assert result.chairman is not None  # Old field still works
  ```

### **Documentation Updates** (30 minutes)**

- [ ] **Update README.md** (10 minutes)
  - Document new fields
  - Update example outputs

- [ ] **Update API documentation** (10 minutes)
  - Document classification API
  - Add usage examples

- [ ] **Update changelog** (10 minutes)
  - Document all schema changes
  - List breaking changes (if any)

### **Deployment** (30 minutes)**

- [ ] **Commit changes** (10 minutes)
  ```bash
  git add -A
  git commit -m "Week 2: Schema migration with 40+ new fields and classification layers"
  ```

- [ ] **Create pull request** (5 minutes)

- [ ] **Deploy to staging** (10 minutes)

- [ ] **Run smoke tests** (5 minutes)

---

## 🔍 Common Migration Issues & Solutions

### **Issue 1: Pydantic validation errors**

**Symptom**: `ValidationError: 1 validation error for FinancialData`

**Cause**: Required field marked without default value

**Solution**:
```python
# WRONG
result_without_depreciation_current_year: int  # Required field

# CORRECT
result_without_depreciation_current_year: Optional[int] = Field(
    None,  # Default = None
    description="..."
)
```

### **Issue 2: Agent prompts not returning new fields**

**Symptom**: New fields always None in extraction results

**Cause**: Agent prompts not updated to extract new fields

**Solution**:
1. Update agent prompt templates
2. Add examples for new field extraction
3. Test on diverse PDFs

### **Issue 3: Classification fails with partial data**

**Symptom**: `KeyError` or `AttributeError` in pattern classifier

**Cause**: Classifier assumes all fields present

**Solution**:
```python
# Add defensive checks
value = data.get('kortfristig_skulder_ratio')
if value is None:
    return ClassificationResult(
        tier='INSUFFICIENT_DATA',
        confidence=0.0
    )
```

### **Issue 4: Database schema mismatch**

**Symptom**: Cannot store comprehensive output in database

**Cause**: Database columns not updated

**Solution**: Use JSON columns (Option 1) for Week 2:
```python
# Store entire output as JSON
json_data = comprehensive_output.dict()
cursor.execute(
    "INSERT INTO extraction_results (pdf_path, json_data) VALUES (%s, %s)",
    (pdf_path, json.dumps(json_data))
)
```

---

## 📊 Validation Metrics

After migration, verify these metrics:

### **Schema Validation**

- [ ] All 40+ new fields compile without errors
- [ ] Pydantic validation passes for sample data
- [ ] Type hints correct (`mypy --strict`)

### **Extraction Validation**

- [ ] New financial fields extracted from ≥3 PDFs
- [ ] New governance fields extracted from ≥3 PDFs
- [ ] New property fields extracted from ≥3 PDFs
- [ ] Field coverage ≥80% (24/30 new fields)

### **Classification Validation**

- [ ] All 8 patterns classify without errors
- [ ] Evidence trails present for all classifications
- [ ] Confidence scores calculated correctly
- [ ] Risk scores in valid range (0-100)

### **Performance Validation**

- [ ] Extraction time <120s per PDF
- [ ] Classification time <30ms per PDF
- [ ] Memory usage <2GB
- [ ] No memory leaks (10 consecutive extractions)

---

## 🎯 Success Criteria

**Migration is successful when**:

✅ All existing tests pass (100% backward compatibility)
✅ New classification tests pass (100% on 4 layers)
✅ Extraction coverage improves (78.4% → 85%+)
✅ Pattern detection works on diverse PDFs (95% accuracy)
✅ No performance degradation (<10% slowdown)
✅ Documentation complete and accurate

---

## 📚 Reference Documentation

- **Phase 0 Summary**: `PHASE_0_COMPLETE_SUMMARY.md`
- **Pattern Catalog**: `PATTERN_CATALOG_WITH_EXAMPLES.md`
- **Day 4 Complete**: `PHASE_0_DAY4_COMPLETE.md`
- **Test Suites**: `test_phase0_day*.py`
- **Configuration**: `gracian_pipeline/config/classification/pattern_classification_rules.yaml`

---

**Document Version**: 1.0
**Last Updated**: October 17, 2025
**Target Audience**: Development team, Week 2 Day 1
**Estimated Migration Time**: 3-4 hours
