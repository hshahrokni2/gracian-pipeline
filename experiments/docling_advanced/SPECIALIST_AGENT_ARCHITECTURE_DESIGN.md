# Specialist Agent Architecture with Self-Learning System
## Complete Implementation Design - 2025-10-12

---

## Executive Summary

**Goal**: Transform current 8 comprehensive agents (78.4% coverage) into 22+ specialist agents achieving **95/95** (95% coverage, 95% accuracy) through:
1. Fine-grained specialist agents (1 agent = 1-3 fields)
2. Self-learning loop (3 iterations per agent with GT-driven refinement)
3. Docling-powered intelligent orchestration
4. Pydantic schema validation for quality control

**Key Innovation**: Agents learn from ground truth mismatches and auto-refine their prompts through LLM coaching.

---

## Part 1: Specialist Agent Design from Real Examples

### 1.1 Extracting Specialist Patterns from Existing PDFs

**Current Validated Ground Truth**:
- `brf_198532.pdf`: K2 format, 19 pages, comprehensive GT (see `/ground_truth/brf_198532_comprehensive_ground_truth.json`)
- `brf_268882.pdf`: Regression test (scanned PDF)
- `brf_271852.pdf`: Additional validation

#### Pattern Analysis Framework

```python
class SpecialistPatternAnalyzer:
    """
    Extract golden patterns from successful extractions for specialist training.
    """

    def analyze_pdf_for_specialist(
        self,
        pdf_path: str,
        ground_truth: Dict,
        field_name: str
    ) -> SpecialistPattern:
        """
        For a specific field, extract:
        1. Section location (which pages, which headings)
        2. Success patterns (what worked in extraction)
        3. Anti-patterns (common failure modes)
        4. Golden examples (actual GT data + context)
        """

        # Step 1: Locate field in ground truth
        gt_value = self._extract_field_from_gt(ground_truth, field_name)

        # Step 2: Find section in PDF using Docling
        docling_result = self.docling_converter.convert(pdf_path)
        section_info = self._find_section_for_field(docling_result, field_name)

        # Step 3: Extract text/table context around field
        context = self._extract_context(pdf_path, section_info.pages)

        # Step 4: Identify success patterns
        patterns = self._identify_patterns(context, gt_value, field_name)

        return SpecialistPattern(
            field_name=field_name,
            gt_value=gt_value,
            section_heading=section_info.heading,
            pages=section_info.pages,
            swedish_terms=patterns.keywords,
            table_structure=patterns.table_layout,
            number_format=patterns.format_hints,
            golden_context=context,
            anti_patterns=self._identify_anti_patterns(field_name)
        )
```

#### Example: Note 4 Utilities Agent

**Ground Truth Analysis** (brf_198532.pdf, Page 13):

```json
{
  "note_4_utilities": {
    "el": 698763,
    "varme": 438246,
    "vatten": 162487
  }
}
```

**Docling Structure Detection**:
```python
{
  "heading": "Not 4 - Driftkostnader",
  "level": 2,
  "page": 12,  # 0-indexed (page 13 in PDF)
  "table_structure": {
    "headers": ["", "2021", "2020"],
    "rows": [
      ["Fastighetsskötsel", "553 590", "520 123"],
      ["El", "698 763", "358 792"],
      ["Värme", "438 246", "375 923"],
      ["Vatten och avlopp", "162 487", "138 045"],
      # ... more rows
    ]
  }
}
```

**Success Pattern**:
```python
class Note4UtilitiesPattern:
    section_keywords = ["not 4", "driftkostnader", "rörelsekostnader"]
    target_fields = {
        "el": {
            "swedish_terms": ["el", "elektricitet", "elkostnad"],
            "row_position": "within_table",
            "column": "rightmost",  # Current year (2021)
            "format": "swedish_thousands",  # "698 763" → 698763
            "typical_range": (200_000, 1_000_000),  # Validation check
            "unit": "SEK"
        },
        "varme": {
            "swedish_terms": ["värme", "uppvärmning", "värmekostnad"],
            "row_position": "within_table",
            "column": "rightmost",
            "format": "swedish_thousands",
            "typical_range": (300_000, 800_000),
            "unit": "SEK"
        },
        "vatten": {
            "swedish_terms": ["vatten", "vatten och avlopp", "vattenkostnad"],
            "row_position": "within_table",
            "column": "rightmost",
            "format": "swedish_thousands",
            "typical_range": (100_000, 300_000),
            "unit": "SEK"
        }
    }

    anti_patterns = [
        "Do NOT extract from 'Summa' line (total)",
        "Do NOT extract from income statement summary",
        "Do NOT extract from 2020 column (previous year)",
        "Do NOT confuse with 'ovriga kostnader' section"
    ]
```

**Golden Example for Few-Shot Learning**:
```python
golden_example = {
    "pdf": "brf_198532.pdf",
    "page": 13,
    "section": "Not 4 - Driftkostnader",
    "table_format": "swedish_brf_standard",
    "extraction": {
        "el": 698763,
        "varme": 438246,
        "vatten": 162487
    },
    "context": """
    NOT 4 DRIFTKOSTNADER

                              2021        2020
    Fastighetsskötsel      553 590     520 123
    Reparationer          258 004     195 889
    El                    698 763     358 792
    Värme                 438 246     375 923
    Vatten och avlopp     162 487     138 045
    Övriga kostnader      422 455     389 123
    """,
    "notes": "Utilities appear as individual line items in K2 format. Extract from 2021 column (rightmost)."
}
```

### 1.2 Specialist Agent Prompt Structure

```python
@dataclass
class SpecialistAgentPrompt:
    """Complete prompt specification for one specialist agent."""

    # Identity
    agent_id: str  # "note4_utilities_agent"
    agent_name: str  # "Note 4 Utilities Specialist"
    agent_description: str  # "Extracts electricity, heating, water costs from Note 4"

    # Task specification
    target_section: str  # "Noter - Not 4 (Driftkostnader)"
    target_pages: List[int]  # [13] (typical location)
    target_fields: List[str]  # ["el", "varme", "vatten"]

    # Domain knowledge
    swedish_terms: Dict[str, List[str]]  # Field → Swedish synonyms
    section_keywords: List[str]  # How to find the section
    table_format: str  # Expected table structure

    # Examples
    golden_examples: List[Dict]  # 2-3 successful extractions
    anti_examples: List[Dict]  # Common failure patterns

    # Output schema
    output_schema: Type[BaseModel]  # Pydantic model
    confidence_threshold: float  # When to flag uncertainty (default: 0.7)

    # Evidence tracking
    requires_evidence: bool = True
    min_evidence_pages: int = 1

def generate_specialist_prompt(spec: SpecialistAgentPrompt) -> str:
    """Generate complete LLM prompt from specification."""

    return f"""You are {spec.agent_name} for Swedish BRF annual reports.

**IDENTITY**: {spec.agent_description}

**TARGET SECTION**: {spec.target_section}
**TYPICAL PAGES**: {spec.target_pages}

**FIELDS TO EXTRACT**: {', '.join(spec.target_fields)}

**SWEDISH TERMINOLOGY**:
{json.dumps(spec.swedish_terms, indent=2, ensure_ascii=False)}

**OUTPUT SCHEMA** (Pydantic):
{spec.output_schema.schema_json(indent=2)}

**GOLDEN EXAMPLES** (Learn from these successful extractions):
{json.dumps(spec.golden_examples, indent=2, ensure_ascii=False)}

**ANTI-PATTERNS** (Avoid these mistakes):
{json.dumps(spec.anti_examples, indent=2, ensure_ascii=False)}

**EXTRACTION INSTRUCTIONS**:
1. Search for section using keywords: {', '.join(spec.section_keywords)}
2. Locate table with format: {spec.table_format}
3. Extract values from rightmost column (current year)
4. Parse Swedish number format: "698 763" → 698763
5. Return ONLY fields in schema (no extra keys)
6. Include evidence_pages: [] with 1-based page numbers
7. If field not found, return null (not empty string)
8. If confidence < {spec.confidence_threshold}, set confidence field

**CONFIDENCE SCORING**:
- 1.0: Exact match in expected table with clear labels
- 0.8: Match in table but label variation (e.g., "El" vs "Elektricitet")
- 0.6: Match in text but not table (narrative mention)
- 0.4: Inferred from related data (e.g., total - components)
- 0.0: Not found

Return STRICT VALID JSON matching output schema. No markdown fences, no extra text.
"""
```

---

## Part 2: Pydantic Schema Integration

### 2.1 Decomposing Comprehensive Schemas into Specialist Schemas

**Current Comprehensive Schema** (gracian_pipeline/core/schema_comprehensive.py):
```python
class ComprehensiveNotesSchema(BaseModel):
    note_4_utilities: Dict[str, float]  # el, varme, vatten
    note_8_buildings: List[BuildingData]
    note_9_receivables: Dict[str, float]
    note_10_maintenance_fund: Dict[str, float]
    note_11_liabilities: Dict[str, float]
```

**New Specialist Schemas** (One per agent):

```python
# experiments/docling_advanced/schemas/specialist_schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
import warnings

# ========================================
# SPECIALIST SCHEMA 1: Note 4 Utilities
# ========================================

class Note4UtilitiesSchema(BaseModel):
    """
    Specialist schema for Note 4 utility costs extraction.

    Target: NOT 4 - DRIFTKOSTNADER section, pages 13-14 typically.
    """

    el: Optional[float] = Field(
        None,
        description="Electricity costs in SEK (Swedish: El, Elektricitet)",
        ge=0,
        le=2_000_000
    )

    varme: Optional[float] = Field(
        None,
        description="Heating costs in SEK (Swedish: Värme, Uppvärmning)",
        ge=0,
        le=2_000_000
    )

    vatten: Optional[float] = Field(
        None,
        description="Water/drainage costs in SEK (Swedish: Vatten, Vatten och avlopp)",
        ge=0,
        le=500_000
    )

    evidence_pages: List[int] = Field(
        default_factory=list,
        description="Source page numbers (1-based) where data was extracted"
    )

    confidence: float = Field(
        1.0,
        description="Extraction confidence score (0-1)",
        ge=0,
        le=1
    )

    @validator('el', 'varme', 'vatten')
    def validate_positive_cost(cls, v):
        """Utility costs must be positive."""
        if v is not None and v < 0:
            raise ValueError("Utility costs must be positive")
        return v

    @validator('el')
    def validate_el_range(cls, v):
        """Electricity typically 200k-1M SEK for Swedish BRF."""
        if v and (v < 100_000 or v > 2_000_000):
            warnings.warn(f"Unusual electricity cost: {v} SEK (expected 200k-1M)")
        return v

    @validator('varme')
    def validate_varme_range(cls, v):
        """Heating typically 300k-800k SEK for Swedish BRF."""
        if v and (v < 200_000 or v > 1_500_000):
            warnings.warn(f"Unusual heating cost: {v} SEK (expected 300k-800k)")
        return v

    @validator('vatten')
    def validate_vatten_range(cls, v):
        """Water typically 100k-300k SEK for Swedish BRF."""
        if v and (v < 50_000 or v > 500_000):
            warnings.warn(f"Unusual water cost: {v} SEK (expected 100k-300k)")
        return v

    @validator('evidence_pages')
    def validate_evidence_exists(cls, v):
        """At least one evidence page required if any field extracted."""
        # Note: This is called AFTER field validators, so we can't access other fields directly
        # Validation happens in post-extraction logic
        return v

    class Config:
        schema_extra = {
            "example": {
                "el": 698763,
                "varme": 438246,
                "vatten": 162487,
                "evidence_pages": [13],
                "confidence": 1.0
            }
        }

# ========================================
# SPECIALIST SCHEMA 2: Note 8 Buildings
# ========================================

class BuildingItem(BaseModel):
    """Individual building entry."""
    name: Optional[str] = Field(None, description="Building name or identifier")
    acquisition_value: Optional[float] = Field(None, description="Acquisition value (SEK)", ge=0)
    accumulated_depreciation: Optional[float] = Field(None, description="Accumulated depreciation (SEK)", le=0)
    book_value: Optional[float] = Field(None, description="Book value (SEK)", ge=0)

class Note8BuildingsSchema(BaseModel):
    """
    Specialist schema for Note 8 buildings/property extraction.

    Target: NOT 8 - BYGGNADER OCH MARK section, pages 14-15 typically.
    """

    buildings: List[BuildingItem] = Field(
        default_factory=list,
        description="List of building entries"
    )

    total_acquisition_value: Optional[float] = Field(
        None,
        description="Total acquisition value across all buildings (SEK)",
        ge=0
    )

    total_book_value: Optional[float] = Field(
        None,
        description="Total book value across all buildings (SEK)",
        ge=0
    )

    land_value: Optional[float] = Field(
        None,
        description="Land value included in total (SEK)",
        ge=0
    )

    tax_value_total: Optional[float] = Field(
        None,
        description="Tax assessment value (Taxeringsvärde) (SEK)",
        ge=0
    )

    evidence_pages: List[int] = Field(
        default_factory=list,
        description="Source page numbers (1-based)"
    )

    confidence: float = Field(1.0, ge=0, le=1)

    @validator('total_book_value')
    def validate_book_value_realistic(cls, v, values):
        """Book value should be less than acquisition value."""
        if v and 'total_acquisition_value' in values:
            acq = values['total_acquisition_value']
            if acq and v > acq:
                warnings.warn(f"Book value ({v}) exceeds acquisition value ({acq})")
        return v

    class Config:
        schema_extra = {
            "example": {
                "total_acquisition_value": 682435875,
                "total_book_value": 666670761,
                "land_value": 332100000,
                "tax_value_total": 389200000,
                "evidence_pages": [15],
                "confidence": 1.0
            }
        }

# ========================================
# SPECIALIST SCHEMA 3: Loans (Note 5/11)
# ========================================

class LoanItem(BaseModel):
    """Individual loan entry."""
    lender: str = Field(..., description="Bank name (e.g., SEB, Handelsbanken)")
    loan_number: Optional[str] = Field(None, description="Loan identification number")
    amount_2021: float = Field(..., description="Outstanding balance current year (SEK)", ge=0)
    interest_rate: float = Field(..., description="Interest rate as decimal (0.57% → 0.0057)", ge=0, le=0.2)
    maturity_date: str = Field(..., description="Maturity date (YYYY-MM-DD)")
    amortization_free: bool = Field(False, description="Is loan amortization-free?")
    loan_type: Optional[str] = Field(None, description="Bundet (fixed) or Rörligt (variable)")
    collateral: Optional[str] = Field(None, description="Collateral type (e.g., Fastighetsinteckning)")

class LoansSchema(BaseModel):
    """
    Specialist schema for loan extraction.

    Target: NOT 5 or NOT 11 - LÅNESKULDER/SKULDER TILL KREDITINSTITUT, pages 15-16 typically.
    """

    loans: List[LoanItem] = Field(
        default_factory=list,
        description="List of individual loans (extract ALL loans, not summary)"
    )

    total_loans: Optional[float] = Field(
        None,
        description="Total outstanding loans (SEK)",
        ge=0
    )

    average_interest_rate: Optional[float] = Field(
        None,
        description="Average interest rate across all loans (decimal)",
        ge=0,
        le=0.2
    )

    evidence_pages: List[int] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0, le=1)

    @validator('total_loans')
    def validate_total_matches_sum(cls, v, values):
        """Total should match sum of individual loans."""
        if v and 'loans' in values:
            loans = values['loans']
            if loans:
                calculated_total = sum(loan.amount_2021 for loan in loans)
                if abs(v - calculated_total) > 1000:  # Allow 1k tolerance
                    warnings.warn(f"Total loans ({v}) doesn't match sum of individual loans ({calculated_total})")
        return v

    class Config:
        schema_extra = {
            "example": {
                "loans": [
                    {
                        "lender": "SEB",
                        "loan_number": "41431520",
                        "amount_2021": 30000000,
                        "interest_rate": 0.0057,
                        "maturity_date": "2024-09-28",
                        "amortization_free": True,
                        "loan_type": "Bundet",
                        "collateral": "Fastighetsinteckning"
                    }
                ],
                "total_loans": 114480000,
                "average_interest_rate": 0.0132,
                "evidence_pages": [16],
                "confidence": 1.0
            }
        }

# ========================================
# SPECIALIST SCHEMA 4: Chairman
# ========================================

class ChairmanSchema(BaseModel):
    """
    Ultra-focused schema for chairman extraction only.

    Target: STYRELSEN section or signature pages, typically pages 2-4 or 17-19.
    """

    chairman: Optional[str] = Field(
        None,
        description="Full name of chairman (Swedish: Ordförande)",
        min_length=2,
        max_length=100
    )

    evidence_pages: List[int] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0, le=1)

    @validator('chairman')
    def validate_name_format(cls, v):
        """Chairman name should have at least first and last name."""
        if v and ' ' not in v.strip():
            warnings.warn(f"Chairman name '{v}' may be incomplete (missing first or last name)")
        return v

    class Config:
        schema_extra = {
            "example": {
                "chairman": "Elvy Maria Löfvenberg",
                "evidence_pages": [2],
                "confidence": 1.0
            }
        }

# ... (Continue with remaining 18+ specialist schemas)

# ========================================
# SCHEMA REGISTRY
# ========================================

SPECIALIST_SCHEMAS = {
    "note4_utilities_agent": Note4UtilitiesSchema,
    "note8_buildings_agent": Note8BuildingsSchema,
    "loans_agent": LoansSchema,
    "chairman_agent": ChairmanSchema,
    # ... more mappings
}

def get_specialist_schema(agent_id: str) -> Type[BaseModel]:
    """Get Pydantic schema for specialist agent."""
    return SPECIALIST_SCHEMAS.get(agent_id)
```

### 2.2 Schema Validation for Quality Control

```python
# experiments/docling_advanced/code/schema_validator.py

class SchemaValidationResult:
    """Result of Pydantic validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    validated_data: Optional[Dict]
    confidence_adjusted: float

class SpecialistSchemaValidator:
    """Validates extraction results against Pydantic schemas."""

    def validate_extraction(
        self,
        agent_id: str,
        extracted_data: Dict,
        strict: bool = True
    ) -> SchemaValidationResult:
        """
        Validate extracted data against specialist schema.

        Args:
            agent_id: Specialist agent ID
            extracted_data: Raw extraction from LLM
            strict: If True, reject on any error; if False, allow warnings

        Returns:
            ValidationResult with validated data or errors
        """

        schema_class = get_specialist_schema(agent_id)
        if not schema_class:
            return SchemaValidationResult(
                valid=False,
                errors=[f"No schema found for agent: {agent_id}"],
                warnings=[],
                validated_data=None,
                confidence_adjusted=0.0
            )

        errors = []
        warnings_list = []

        try:
            # Pydantic validation (this runs all validators)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                validated = schema_class(**extracted_data)

                # Capture validation warnings
                for warning in w:
                    warnings_list.append(str(warning.message))

            # Additional custom validations
            custom_checks = self._run_custom_validations(agent_id, validated)
            warnings_list.extend(custom_checks)

            # Adjust confidence based on warnings
            confidence = validated.confidence
            if warnings_list:
                # Reduce confidence by 0.1 per warning (min 0.4)
                confidence = max(0.4, confidence - 0.1 * len(warnings_list))

            return SchemaValidationResult(
                valid=True,
                errors=[],
                warnings=warnings_list,
                validated_data=validated.dict(),
                confidence_adjusted=confidence
            )

        except ValidationError as e:
            # Pydantic validation failed
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                errors.append(f"{field}: {msg}")

            return SchemaValidationResult(
                valid=False if strict else True,
                errors=errors,
                warnings=[],
                validated_data=None if strict else extracted_data,
                confidence_adjusted=0.0 if strict else 0.3
            )

    def _run_custom_validations(
        self,
        agent_id: str,
        validated_data: BaseModel
    ) -> List[str]:
        """Run agent-specific custom validations."""
        warnings_list = []

        # Evidence page validation
        if not validated_data.evidence_pages:
            # Check if any substantive field was extracted
            data_dict = validated_data.dict(exclude={'evidence_pages', 'confidence'})
            if any(v is not None for v in data_dict.values()):
                warnings_list.append("Data extracted but no evidence_pages provided")

        # Agent-specific validations
        if agent_id == "note4_utilities_agent":
            # All utilities should be present (or all missing)
            fields = [validated_data.el, validated_data.varme, validated_data.vatten]
            present_count = sum(1 for f in fields if f is not None)
            if 0 < present_count < 3:
                warnings_list.append(
                    f"Partial utility extraction: {present_count}/3 fields. "
                    "Expected all or none (may indicate incomplete table extraction)"
                )

        elif agent_id == "loans_agent":
            # At least one loan should be present
            if not validated_data.loans:
                warnings_list.append("No individual loans extracted (expected 1-5 loans)")

            # Total should match sum
            if validated_data.total_loans and validated_data.loans:
                calculated = sum(loan.amount_2021 for loan in validated_data.loans)
                if abs(validated_data.total_loans - calculated) > 1000:
                    warnings_list.append(
                        f"Total loans mismatch: declared={validated_data.total_loans}, "
                        f"calculated={calculated}"
                    )

        return warnings_list
```

---

## Part 3: Self-Learning Loop Design

### 3.1 Three-Iteration Learning Algorithm

```python
# experiments/docling_advanced/code/specialist_learning_loop.py

from dataclasses import dataclass
from typing import List, Dict, Optional
import time
import json

@dataclass
class LearningIteration:
    """One iteration of the learning loop."""
    iteration: int
    prompt_version: str
    test_results: List[Dict]
    accuracy: float
    improvement_delta: float
    error_patterns: Dict[str, List]
    refinement_applied: str

class SpecialistLearningLoop:
    """
    Self-improving specialist agent with 3 refinement iterations.

    Process:
    1. Run extraction with current prompt on test PDFs
    2. Compare against ground truth
    3. Identify error patterns
    4. Generate refined prompt with LLM coaching
    5. Test refined prompt
    6. Accept if improvement > threshold, else revert
    """

    def __init__(
        self,
        specialist_id: str,
        initial_prompt: SpecialistAgentPrompt,
        ground_truth_examples: List[Dict],
        test_pdfs: List[str],
        max_iterations: int = 3,
        improvement_threshold: float = 0.05  # 5% minimum improvement
    ):
        self.specialist_id = specialist_id
        self.current_prompt = initial_prompt
        self.ground_truth = {ex['pdf']: ex for ex in ground_truth_examples}
        self.test_pdfs = test_pdfs
        self.max_iterations = max_iterations
        self.improvement_threshold = improvement_threshold

        self.learning_history: List[LearningIteration] = []
        self.iteration = 0

    def train(self) -> SpecialistAgentPrompt:
        """
        Run full training loop (3 iterations).

        Returns:
            Best performing prompt after training
        """

        print(f"\n{'='*70}")
        print(f"🎓 TRAINING: {self.specialist_id}")
        print(f"{'='*70}\n")

        # Baseline: Test initial prompt
        print(f"📊 Iteration 0: Baseline (initial prompt)")
        baseline_results = self._test_prompt(self.current_prompt)
        baseline_accuracy = self._calculate_accuracy(baseline_results)

        print(f"   Baseline accuracy: {baseline_accuracy:.1%}")

        best_prompt = self.current_prompt
        best_accuracy = baseline_accuracy

        # Iterative refinement
        for i in range(1, self.max_iterations + 1):
            self.iteration = i

            print(f"\n📊 Iteration {i}: Refinement")

            # Step 1: Analyze errors from previous iteration
            prev_results = baseline_results if i == 1 else iteration_results
            error_patterns = self._analyze_errors(prev_results)

            if not error_patterns['total_errors']:
                print(f"   ✅ Perfect accuracy achieved! No refinement needed.")
                break

            print(f"   Errors found: {error_patterns['total_errors']}")
            for category, errors in error_patterns.items():
                if errors and category != 'total_errors':
                    print(f"     - {category}: {len(errors)}")

            # Step 2: Refine prompt using LLM coaching
            print(f"   🤖 Generating refined prompt...")
            refined_prompt = self._refine_prompt(
                current_prompt=self.current_prompt,
                error_patterns=error_patterns,
                golden_examples=self._get_successful_cases(prev_results),
                failed_examples=self._get_failed_cases(prev_results)
            )

            # Step 3: Test refined prompt
            print(f"   🧪 Testing refined prompt...")
            iteration_results = self._test_prompt(refined_prompt)
            iteration_accuracy = self._calculate_accuracy(iteration_results)

            improvement = iteration_accuracy - best_accuracy

            print(f"   Accuracy: {iteration_accuracy:.1%} (Δ = {improvement:+.1%})")

            # Step 4: Accept or reject refinement
            if improvement >= self.improvement_threshold:
                print(f"   ✅ ACCEPTED (improvement ≥ {self.improvement_threshold:.1%})")
                self.current_prompt = refined_prompt
                best_prompt = refined_prompt
                best_accuracy = iteration_accuracy

                # Record learning
                self.learning_history.append(LearningIteration(
                    iteration=i,
                    prompt_version=f"v{i}",
                    test_results=iteration_results,
                    accuracy=iteration_accuracy,
                    improvement_delta=improvement,
                    error_patterns=error_patterns,
                    refinement_applied="accepted"
                ))
            else:
                print(f"   ❌ REJECTED (improvement < {self.improvement_threshold:.1%})")

                # Record failed attempt
                self.learning_history.append(LearningIteration(
                    iteration=i,
                    prompt_version=f"v{i}_rejected",
                    test_results=iteration_results,
                    accuracy=iteration_accuracy,
                    improvement_delta=improvement,
                    error_patterns=error_patterns,
                    refinement_applied="rejected"
                ))

                # Early stopping if no improvement
                if improvement < 0:
                    print(f"   ⚠️  Accuracy decreased. Stopping early.")
                    break

        # Final summary
        print(f"\n{'='*70}")
        print(f"🎯 TRAINING COMPLETE")
        print(f"   Initial accuracy: {baseline_accuracy:.1%}")
        print(f"   Final accuracy: {best_accuracy:.1%}")
        print(f"   Total improvement: {best_accuracy - baseline_accuracy:+.1%}")
        print(f"   Iterations run: {len(self.learning_history)}")
        print(f"{'='*70}\n")

        return best_prompt

    def _test_prompt(
        self,
        prompt: SpecialistAgentPrompt
    ) -> List[Dict]:
        """
        Test specialist prompt on all test PDFs.

        Returns:
            List of test results (one per PDF)
        """
        results = []

        for pdf_path in self.test_pdfs:
            # Extract using current prompt
            extracted = self._extract_with_prompt(pdf_path, prompt)

            # Get ground truth
            gt = self.ground_truth.get(pdf_path)

            # Compare
            comparison = self._compare_results(extracted, gt)

            results.append({
                'pdf': pdf_path,
                'extracted': extracted,
                'ground_truth': gt,
                'comparison': comparison
            })

        return results

    def _extract_with_prompt(
        self,
        pdf_path: str,
        prompt: SpecialistAgentPrompt
    ) -> Dict:
        """
        Run extraction using specialist prompt.

        This calls the actual extraction pipeline with the given prompt.
        """
        # Generate LLM prompt from spec
        llm_prompt = generate_specialist_prompt(prompt)

        # Create temporary extractor with this prompt
        from base_brf_extractor import BaseExtractor

        extractor = BaseExtractor()
        extractor.AGENT_PROMPTS[self.specialist_id] = llm_prompt

        # Run extraction
        result = extractor._extract_agent(
            pdf_path=pdf_path,
            agent_id=self.specialist_id,
            section_headings=prompt.section_keywords,
            context=None
        )

        return result.get('data', {})

    def _calculate_accuracy(self, test_results: List[Dict]) -> float:
        """
        Calculate overall accuracy across all test PDFs.

        Accuracy = (correct fields) / (total expected fields)
        """
        total_fields = 0
        correct_fields = 0

        for result in test_results:
            comp = result['comparison']
            total_fields += comp['total_fields']
            correct_fields += comp['correct_fields']

        return correct_fields / total_fields if total_fields > 0 else 0.0

    def _compare_results(
        self,
        extracted: Dict,
        ground_truth: Dict
    ) -> Dict:
        """
        Compare extracted data against ground truth.

        Returns:
            Detailed comparison with field-by-field analysis
        """
        if not ground_truth:
            return {
                'total_fields': 0,
                'correct_fields': 0,
                'missing_fields': [],
                'incorrect_fields': [],
                'extra_fields': []
            }

        gt_fields = ground_truth.get('fields', {})

        missing = []
        incorrect = []
        correct = 0

        for field, gt_value in gt_fields.items():
            ext_value = extracted.get(field)

            if ext_value is None:
                missing.append({
                    'field': field,
                    'expected': gt_value,
                    'extracted': None
                })
            elif not self._values_match(ext_value, gt_value):
                incorrect.append({
                    'field': field,
                    'expected': gt_value,
                    'extracted': ext_value,
                    'error_type': self._classify_error(ext_value, gt_value)
                })
            else:
                correct += 1

        # Check for extra fields (not in GT)
        extra = [f for f in extracted.keys() if f not in gt_fields and f not in ['evidence_pages', 'confidence']]

        return {
            'total_fields': len(gt_fields),
            'correct_fields': correct,
            'missing_fields': missing,
            'incorrect_fields': incorrect,
            'extra_fields': extra
        }

    def _values_match(self, extracted, ground_truth, tolerance=0.01) -> bool:
        """Check if extracted value matches ground truth (with tolerance for floats)."""
        if type(extracted) != type(ground_truth):
            return False

        if isinstance(extracted, (int, float)) and isinstance(ground_truth, (int, float)):
            # Numeric comparison with tolerance
            if ground_truth == 0:
                return extracted == 0
            return abs(extracted - ground_truth) / abs(ground_truth) < tolerance

        return extracted == ground_truth

    def _classify_error(self, extracted, ground_truth) -> str:
        """Classify type of extraction error."""
        if isinstance(extracted, (int, float)) and isinstance(ground_truth, (int, float)):
            ratio = extracted / ground_truth if ground_truth != 0 else float('inf')

            if 0.9 <= ratio <= 1.1:
                return "numeric_close"  # Within 10%
            elif ratio > 1000 or ratio < 0.001:
                return "magnitude_error"  # Order of magnitude wrong
            else:
                return "numeric_mismatch"

        if isinstance(extracted, str) and isinstance(ground_truth, str):
            if extracted.lower() == ground_truth.lower():
                return "case_mismatch"
            elif extracted in ground_truth or ground_truth in extracted:
                return "partial_match"
            else:
                return "string_mismatch"

        return "type_mismatch"

    def _analyze_errors(self, test_results: List[Dict]) -> Dict[str, List]:
        """
        Analyze errors from test results to identify patterns.

        Returns:
            Dict categorizing errors by type
        """
        error_categories = {
            'missing_extraction': [],  # Field in GT but not extracted
            'incorrect_value': [],      # Field extracted but wrong value
            'wrong_page': [],          # Looked at wrong page
            'format_parsing': [],      # Number format issues
            'swedish_terms': [],       # Swedish-English confusion
            'table_structure': [],     # Misunderstood table layout
            'total_errors': 0
        }

        for result in test_results:
            comp = result['comparison']
            pdf = result['pdf']

            # Missing fields
            for missing in comp['missing_fields']:
                error_categories['missing_extraction'].append({
                    'pdf': pdf,
                    'field': missing['field'],
                    'expected': missing['expected']
                })
                error_categories['total_errors'] += 1

            # Incorrect fields
            for incorrect in comp['incorrect_fields']:
                error_type = incorrect['error_type']

                if error_type in ['numeric_close', 'numeric_mismatch']:
                    category = 'format_parsing'
                elif error_type in ['string_mismatch', 'case_mismatch', 'partial_match']:
                    category = 'swedish_terms'
                elif error_type == 'magnitude_error':
                    category = 'table_structure'
                else:
                    category = 'incorrect_value'

                error_categories[category].append({
                    'pdf': pdf,
                    'field': incorrect['field'],
                    'expected': incorrect['expected'],
                    'extracted': incorrect['extracted'],
                    'error_type': error_type
                })
                error_categories['total_errors'] += 1

        return error_categories

    def _refine_prompt(
        self,
        current_prompt: SpecialistAgentPrompt,
        error_patterns: Dict,
        golden_examples: List[Dict],
        failed_examples: List[Dict]
    ) -> SpecialistAgentPrompt:
        """
        Use GPT-4o to refine specialist prompt based on error analysis.

        This is the key self-learning mechanism.
        """

        # Build refinement prompt for GPT-4o
        refinement_prompt = f"""You are a specialist prompt engineer for Swedish BRF document extraction.

**CURRENT SPECIALIST**: {current_prompt.agent_id}
**TARGET FIELDS**: {', '.join(current_prompt.target_fields)}

**CURRENT PROMPT**:
{generate_specialist_prompt(current_prompt)}

**ERROR ANALYSIS FROM TESTING**:
{json.dumps(error_patterns, indent=2, ensure_ascii=False)}

**SUCCESSFUL CASES** (Keep doing this):
{json.dumps(golden_examples, indent=2, ensure_ascii=False)}

**FAILED CASES** (Fix these):
{json.dumps(failed_examples, indent=2, ensure_ascii=False)}

**TASK**: Refine the prompt to fix the errors while maintaining successful patterns.

**SPECIFIC IMPROVEMENTS NEEDED**:
{self._generate_improvement_instructions(error_patterns)}

**CONSTRAINTS**:
1. Keep prompt under 500 words
2. Maintain structured format (Identity, Task, Examples, Instructions)
3. Add specific guidance for error patterns found
4. Update anti-examples with new failure modes
5. Strengthen Swedish term coverage if terminology errors found

Return ONLY a JSON object with the refined prompt components:
{{
  "refined_identity": "...",
  "refined_task_description": "...",
  "refined_instructions": "...",
  "new_anti_examples": [...]
}}
"""

        try:
            from openai import OpenAI
            import os

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[
                    {"role": "system", "content": "You are a Swedish BRF extraction prompt expert. Return only valid JSON."},
                    {"role": "user", "content": refinement_prompt}
                ],
                temperature=0.3,  # Lower temp for consistency
                response_format={"type": "json_object"}
            )

            refinement = json.loads(response.choices[0].message.content)

            # Create new prompt spec with refinements
            refined_prompt = SpecialistAgentPrompt(
                agent_id=current_prompt.agent_id,
                agent_name=current_prompt.agent_name,
                agent_description=refinement.get('refined_identity', current_prompt.agent_description),
                target_section=current_prompt.target_section,
                target_pages=current_prompt.target_pages,
                target_fields=current_prompt.target_fields,
                swedish_terms=current_prompt.swedish_terms,  # Could be enhanced too
                section_keywords=current_prompt.section_keywords,
                table_format=current_prompt.table_format,
                golden_examples=golden_examples[:3],  # Top 3 successful
                anti_examples=refinement.get('new_anti_examples', current_prompt.anti_examples),
                output_schema=current_prompt.output_schema,
                confidence_threshold=current_prompt.confidence_threshold
            )

            return refined_prompt

        except Exception as e:
            print(f"   ⚠️  Prompt refinement failed: {e}")
            return current_prompt  # Return unchanged on error

    def _generate_improvement_instructions(self, error_patterns: Dict) -> str:
        """Generate specific instructions based on error types."""
        instructions = []

        if error_patterns['missing_extraction']:
            fields = [e['field'] for e in error_patterns['missing_extraction'][:3]]
            instructions.append(
                f"- Add explicit instruction to look for: {', '.join(fields)}"
            )
            instructions.append(
                "- Expand search area (check more pages or section variations)"
            )

        if error_patterns['format_parsing']:
            instructions.append(
                "- Add Swedish number format handling examples (spaces not commas: '698 763' → 698763)"
            )
            instructions.append(
                "- Show examples of both positive and negative numbers"
            )

        if error_patterns['swedish_terms']:
            instructions.append(
                "- Expand Swedish term synonyms to cover OCR variations"
            )
            instructions.append(
                "- Add examples of term variations found in errors"
            )

        if error_patterns['table_structure']:
            instructions.append(
                "- Clarify table column selection (rightmost = current year)"
            )
            instructions.append(
                "- Add warning about skipping 'Summa' rows"
            )

        if not instructions:
            instructions.append(
                "- Strengthen existing instructions for better accuracy"
            )

        return "\n".join(instructions)

    def _get_successful_cases(self, test_results: List[Dict]) -> List[Dict]:
        """Extract successful extractions for few-shot learning."""
        successful = []

        for result in test_results:
            if result['comparison']['correct_fields'] == result['comparison']['total_fields']:
                successful.append({
                    'pdf': result['pdf'],
                    'extracted': result['extracted'],
                    'ground_truth': result['ground_truth']
                })

        return successful

    def _get_failed_cases(self, test_results: List[Dict]) -> List[Dict]:
        """Extract failed extractions for anti-examples."""
        failed = []

        for result in test_results:
            if result['comparison']['correct_fields'] < result['comparison']['total_fields']:
                failed.append({
                    'pdf': result['pdf'],
                    'extracted': result['extracted'],
                    'ground_truth': result['ground_truth'],
                    'errors': result['comparison']['missing_fields'] + result['comparison']['incorrect_fields']
                })

        return failed
```

---

## Part 4: Docling-Powered Orchestration

### 4.1 Intelligent Section Routing

```python
# experiments/docling_advanced/code/specialist_orchestrator.py

class SpecialistOrchestrator:
    """
    Orchestrator that uses Docling structure detection to route to specialists.

    Key improvements over current OptimalBRFPipeline:
    1. More granular agent routing (22+ specialists vs 8 comprehensive)
    2. Confidence-based fallback (if specialist fails, retry with broader agent)
    3. Cross-specialist validation (consistency checks across related fields)
    """

    def __init__(
        self,
        specialists: Dict[str, SpecialistAgent],
        cache_manager: CacheManager,
        enable_learning: bool = False
    ):
        self.specialists = specialists
        self.cache_manager = cache_manager
        self.enable_learning = enable_learning
        self.docling_converter = DocumentConverter()

        # Section → Specialist mapping (learned or predefined)
        self.routing_map = self._build_routing_map()

    def _build_routing_map(self) -> Dict[str, List[str]]:
        """
        Build section heading → specialist IDs mapping.

        Uses fuzzy matching + LLM classification + historical routing data.
        """
        return {
            # Financial sections
            "resultaträkning": ["financial_agent", "revenue_breakdown_agent", "operating_costs_agent"],
            "balansräkning": ["financial_agent", "balance_sheet_assets_agent", "balance_sheet_liabilities_agent"],

            # Notes sections (more granular)
            "not 1": ["notes_accounting_agent"],
            "not 2": ["notes_valuation_agent"],
            "not 3": ["notes_revenue_agent"],
            "not 4": ["note4_utilities_agent", "operating_costs_agent"],
            "not 5": ["loans_agent"],
            "not 8": ["note8_buildings_agent"],
            "not 9": ["note9_receivables_agent"],
            "not 10": ["note10_maintenance_fund_agent"],

            # Governance sections
            "styrelsen": ["chairman_agent", "board_members_agent"],
            "revisorer": ["auditor_agent"],
            "valberedning": ["nomination_committee_agent"],

            # Property sections
            "fastighet": ["property_agent", "apartments_agent", "energy_agent"],

            # ... more mappings
        }

    def orchestrate_extraction(self, pdf_path: str) -> ExtractionResult:
        """
        Main orchestration flow:
        1. Docling structure detection
        2. Section → Specialist routing
        3. Parallel specialist execution
        4. Cross-validation and merging
        5. Quality validation
        """

        overall_start = time.time()

        print(f"\n{'='*70}")
        print(f"🎯 SPECIALIST ORCHESTRATOR - {Path(pdf_path).name}")
        print(f"{'='*70}\n")

        # Stage 1: Structure detection (cached)
        print("🔍 Stage 1: Structure Detection (Docling)")
        structure = self._detect_structure_cached(pdf_path)

        # Stage 2: Intelligent routing
        print("\n🧭 Stage 2: Specialist Routing")
        routing = self._route_sections_to_specialists(structure)

        print(f"   Specialists activated: {len(routing)}")
        for specialist_id, sections in routing.items():
            print(f"     - {specialist_id}: {len(sections)} sections")

        # Stage 3: Parallel extraction
        print("\n⚡ Stage 3: Parallel Specialist Extraction")
        specialist_results = self._execute_specialists_parallel(pdf_path, routing)

        # Stage 4: Cross-validation
        print("\n✅ Stage 4: Cross-Validation")
        validated_results = self._cross_validate_results(specialist_results)

        # Stage 5: Merge and validate
        print("\n🔄 Stage 5: Merging & Quality Validation")
        final_result = self._merge_and_validate(validated_results)

        total_time = time.time() - overall_start

        print(f"\n{'='*70}")
        print(f"✅ ORCHESTRATION COMPLETE ({total_time:.1f}s)")
        print(f"   Specialists executed: {len(specialist_results)}")
        print(f"   Success rate: {final_result['success_rate']:.1%}")
        print(f"   Overall confidence: {final_result['confidence']:.2f}")
        print(f"{'='*70}\n")

        return final_result

    def _route_sections_to_specialists(
        self,
        structure: DoclingStructure
    ) -> Dict[str, List[str]]:
        """
        Map Docling-detected sections to specialist agents.

        Uses 3-layer routing (same as current optimal pipeline):
        1. Keyword matching (fast)
        2. Fuzzy matching (medium)
        3. LLM classification (slow, accurate)
        """

        routing = defaultdict(list)
        unrouted = []

        for section in structure.sections:
            heading = section.heading.lower()

            # Layer 1: Exact keyword match
            matched = False
            for keyword, specialists in self.routing_map.items():
                if keyword in heading:
                    for specialist_id in specialists:
                        routing[specialist_id].append(section.heading)
                    matched = True
                    break

            if not matched:
                unrouted.append(section.heading)

        # Layer 2: Fuzzy matching for unrouted
        if unrouted:
            fuzzy_routed = self._fuzzy_route_sections(unrouted)
            for specialist_id, headings in fuzzy_routed.items():
                routing[specialist_id].extend(headings)
                unrouted = [h for h in unrouted if h not in headings]

        # Layer 3: LLM classification for remaining
        if unrouted:
            llm_routed = self._llm_classify_sections(unrouted)
            for specialist_id, headings in llm_routed.items():
                routing[specialist_id].extend(headings)

        return dict(routing)

    def _execute_specialists_parallel(
        self,
        pdf_path: str,
        routing: Dict[str, List[str]]
    ) -> Dict[str, Dict]:
        """
        Execute specialists in parallel with ThreadPoolExecutor.

        Returns:
            Dict mapping specialist_id → extraction result
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_specialist = {}

            for specialist_id, section_headings in routing.items():
                if specialist_id not in self.specialists:
                    print(f"   ⚠️  Unknown specialist: {specialist_id}")
                    continue

                specialist = self.specialists[specialist_id]

                future = executor.submit(
                    self._execute_specialist,
                    specialist,
                    pdf_path,
                    section_headings
                )
                future_to_specialist[future] = specialist_id

            # Collect results
            for future in as_completed(future_to_specialist):
                specialist_id = future_to_specialist[future]
                try:
                    result = future.result(timeout=120)
                    results[specialist_id] = result

                    status = "✅" if result['status'] == 'success' else "❌"
                    conf = result.get('confidence', 0.0)
                    print(f"   {status} {specialist_id}: confidence={conf:.2f}")

                except Exception as e:
                    print(f"   ❌ {specialist_id}: {str(e)[:50]}")
                    results[specialist_id] = {
                        'specialist_id': specialist_id,
                        'status': 'error',
                        'error': str(e)
                    }

        return results

    def _cross_validate_results(
        self,
        specialist_results: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Cross-validate results across related specialists.

        Example validations:
        1. Total loans (loans_agent) should match liabilities (financial_agent)
        2. Revenue breakdown sum should match total revenue
        3. Building value (note8) should match fixed assets (balance_sheet)
        """

        validated = specialist_results.copy()

        # Validation 1: Loans vs Liabilities
        if 'loans_agent' in validated and 'financial_agent' in validated:
            loans_total = validated['loans_agent'].get('data', {}).get('total_loans')
            liabilities = validated['financial_agent'].get('data', {}).get('long_term_liabilities')

            if loans_total and liabilities:
                if abs(loans_total - liabilities) / liabilities > 0.1:  # > 10% mismatch
                    print(f"   ⚠️  Cross-validation warning: Loans ({loans_total}) vs Liabilities ({liabilities}) mismatch")
                    # Reduce confidence
                    validated['loans_agent']['confidence'] *= 0.8
                    validated['financial_agent']['confidence'] *= 0.8

        # Validation 2: Revenue breakdown sum
        if 'revenue_breakdown_agent' in validated and 'financial_agent' in validated:
            breakdown = validated['revenue_breakdown_agent'].get('data', {})
            total_revenue = validated['financial_agent'].get('data', {}).get('revenue')

            if breakdown and total_revenue:
                breakdown_sum = sum(v for k, v in breakdown.items() if isinstance(v, (int, float)) and 'summa' not in k.lower())

                if abs(breakdown_sum - total_revenue) / total_revenue > 0.05:  # > 5% mismatch
                    print(f"   ⚠️  Cross-validation warning: Revenue breakdown sum ({breakdown_sum}) vs total ({total_revenue}) mismatch")
                    validated['revenue_breakdown_agent']['confidence'] *= 0.9

        # ... more cross-validations

        return validated

    def _merge_and_validate(
        self,
        validated_results: Dict[str, Dict]
    ) -> Dict:
        """
        Merge all specialist results into final BRF report.

        Returns:
            Complete extraction result with quality metrics
        """

        # Merge all extractions
        merged_data = {}
        for specialist_id, result in validated_results.items():
            if result['status'] == 'success':
                merged_data[specialist_id] = result['data']

        # Calculate quality metrics
        total_specialists = len(validated_results)
        successful = sum(1 for r in validated_results.values() if r['status'] == 'success')

        avg_confidence = sum(
            r.get('confidence', 0.0)
            for r in validated_results.values()
            if r['status'] == 'success'
        ) / successful if successful > 0 else 0.0

        return {
            'merged_data': merged_data,
            'success_rate': successful / total_specialists,
            'confidence': avg_confidence,
            'specialist_count': total_specialists,
            'successful_count': successful,
            'failed_specialists': [
                sid for sid, r in validated_results.items()
                if r['status'] != 'success'
            ]
        }
```

---

## Part 5: Implementation Strategy

### 5.1 Implementation Order (Day 5, ~11 hours total)

```
PHASE 1: Foundation (2 hours)
├── Create specialist schemas (specialist_schemas.py)
│   ├── Note4UtilitiesSchema ✓
│   ├── Note8BuildingsSchema ✓
│   ├── LoansSchema ✓
│   ├── ChairmanSchema ✓
│   └── 18 more specialist schemas
├── Implement schema validator (schema_validator.py)
└── Test validation on ground truth data

PHASE 2: Core Specialists (3 hours)
├── Implement 5 note specialists
│   ├── note4_utilities_agent
│   ├── note8_buildings_agent
│   ├── note9_receivables_agent
│   ├── note10_maintenance_fund_agent
│   └── loans_agent (note5/11)
├── Implement 4 governance specialists
│   ├── chairman_agent
│   ├── board_members_agent
│   ├── auditor_agent
│   └── nomination_committee_agent
├── Implement 4 financial specialists
│   ├── financial_agent (core metrics)
│   ├── revenue_breakdown_agent
│   ├── operating_costs_agent
│   └── balance_sheet_assets_agent
└── Test extraction on brf_198532.pdf

PHASE 3: Learning Loop (2 hours)
├── Implement SpecialistLearningLoop class
├── Implement error pattern analysis
├── Implement LLM-based prompt refinement
├── Run 3-iteration training on note4_utilities_agent
└── Validate improvement (should see +5-10% accuracy)

PHASE 4: Orchestration (2 hours)
├── Implement SpecialistOrchestrator class
├── Implement specialist routing (3-layer)
├── Implement parallel execution (ThreadPoolExecutor)
├── Implement cross-validation logic
└── Test full pipeline on brf_198532.pdf

PHASE 5: Validation & Testing (2 hours)
├── Test all 13 specialists on 3 PDFs
│   ├── brf_198532.pdf (validated GT)
│   ├── brf_268882.pdf (scanned)
│   └── brf_271852.pdf (additional)
├── Measure coverage improvement (78.4% → 90%+ target)
├── Run regression tests (ensure no breakage)
└── Generate validation report
```

### 5.2 Data Structures Summary

```python
# Core data structures supporting the learning loop

@dataclass
class SpecialistAgent:
    """One specialist agent with learned prompt."""
    agent_id: str
    current_prompt: SpecialistAgentPrompt
    schema: Type[BaseModel]
    learning_history: List[LearningIteration]
    performance_stats: Dict[str, float]

@dataclass
class SpecialistTrainingData:
    """Training data for one specialist."""
    specialist_id: str
    target_fields: List[str]
    golden_examples: List[Dict]  # Successful extractions with context
    failed_examples: List[Dict]  # Failed extractions with errors
    prompt_versions: List[SpecialistAgentPrompt]  # History of prompts
    performance_history: List[float]  # Coverage over iterations

@dataclass
class GroundTruthExample:
    """One ground truth example for training."""
    pdf_path: str
    fields: Dict[str, Any]  # Expected field values
    section_location: str  # Which section to look in
    pages: List[int]  # Where data appears
    format_notes: str  # E.g., "Swedish thousands format", "K2 table"

class GroundTruthComparator:
    """Compare extraction results against ground truth."""

    def compare(
        self,
        extracted: Dict,
        ground_truth: Dict,
        tolerance: float = 0.01
    ) -> ComparisonResult:
        """
        Field-by-field comparison with tolerance for numeric fields.

        Returns:
            ComparisonResult(
                matches=[...],
                mismatches=[...],
                accuracy=0.87
            )
        """
        matches = []
        mismatches = []

        for field, gt_value in ground_truth.items():
            ext_value = extracted.get(field)

            if self._values_match(ext_value, gt_value, tolerance):
                matches.append(field)
            else:
                mismatches.append({
                    'field': field,
                    'extracted': ext_value,
                    'expected': gt_value,
                    'error_type': self._classify_error(ext_value, gt_value)
                })

        return ComparisonResult(
            matches=matches,
            mismatches=mismatches,
            accuracy=len(matches) / len(ground_truth) if ground_truth else 0.0
        )
```

### 5.3 Preventing Overfitting

```python
class OverfittingDetector:
    """
    Detect and prevent overfitting during specialist training.

    Techniques:
    1. Train/test split (80/20)
    2. Early stopping (no improvement for 2 iterations)
    3. Regularization (limit prompt complexity)
    4. Validation on unseen PDFs
    """

    def validate_generalization(
        self,
        specialist: SpecialistAgent,
        train_pdfs: List[str],
        test_pdfs: List[str]
    ) -> OverfittingReport:
        """
        Test specialist on unseen PDFs to detect overfitting.

        Red flags:
        - Train accuracy >> Test accuracy (> 15% gap)
        - Prompt mentions specific PDF names/values
        - Prompt too long (> 600 words)
        """

        # Measure on training set
        train_accuracy = self._test_specialist(specialist, train_pdfs)

        # Measure on held-out test set
        test_accuracy = self._test_specialist(specialist, test_pdfs)

        # Detect overfitting
        overfit_score = train_accuracy - test_accuracy

        is_overfitting = overfit_score > 0.15  # 15% gap threshold

        if is_overfitting:
            recommendations = [
                "Simplify prompt (remove PDF-specific examples)",
                "Add more diverse training PDFs",
                "Reduce golden examples from 5 to 2-3",
                "Strengthen anti-examples for edge cases"
            ]
        else:
            recommendations = ["Generalization is good!"]

        return OverfittingReport(
            train_accuracy=train_accuracy,
            test_accuracy=test_accuracy,
            overfit_score=overfit_score,
            is_overfitting=is_overfitting,
            recommendations=recommendations
        )
```

---

## Part 6: Complete Implementation Example

### 6.1 One Complete Specialist Agent (Note 4 Utilities)

**File**: `experiments/docling_advanced/code/specialist_agents/note4_utilities_agent.py`

```python
"""
Note 4 Utilities Specialist Agent
Extracts electricity, heating, water costs from NOT 4 - DRIFTKOSTNADER.
"""

from typing import Dict, List, Optional
from specialist_schemas import Note4UtilitiesSchema
from specialist_base import SpecialistAgentPrompt, SpecialistAgent

# ========================================
# GROUND TRUTH TRAINING DATA
# ========================================

GOLDEN_EXAMPLES = [
    {
        "pdf": "brf_198532.pdf",
        "page": 13,
        "section": "NOT 4 - DRIFTKOSTNADER",
        "table_format": "swedish_brf_k2",
        "extraction": {
            "el": 698763,
            "varme": 438246,
            "vatten": 162487,
            "evidence_pages": [13],
            "confidence": 1.0
        },
        "context": """
        NOT 4 DRIFTKOSTNADER

                              2021        2020
        Fastighetsskötsel  553 590     520 123
        El                 698 763     358 792
        Värme              438 246     375 923
        Vatten och avlopp  162 487     138 045
        """,
        "notes": "K2 format with individual utility line items. Extract from 2021 column."
    }
]

ANTI_EXAMPLES = [
    {
        "mistake": "Extracted from Summa line instead of individual items",
        "wrong_extraction": {"el": 2834798},  # This is the total!
        "correct_extraction": {"el": 698763},
        "lesson": "Skip rows containing 'Summa' keyword. Extract individual El line."
    },
    {
        "mistake": "Extracted from 2020 column instead of 2021",
        "wrong_extraction": {"el": 358792},
        "correct_extraction": {"el": 698763},
        "lesson": "Always extract from rightmost column (current year)."
    }
]

# ========================================
# AGENT SPECIFICATION
# ========================================

NOTE4_UTILITIES_SPEC = SpecialistAgentPrompt(
    agent_id="note4_utilities_agent",
    agent_name="Note 4 Utilities Cost Specialist",
    agent_description="Extracts electricity, heating, and water costs from Note 4 (Driftkostnader) section",

    target_section="Noter - Not 4 (Driftkostnader/Rörelsekostnader)",
    target_pages=[13],  # Typical location
    target_fields=["el", "varme", "vatten"],

    swedish_terms={
        "el": ["el", "elektricitet", "elkostnad", "elförbrukning"],
        "varme": ["värme", "uppvärmning", "värmekostnad"],
        "vatten": ["vatten", "vatten och avlopp", "vattenkostnad", "va-kostnad"]
    },

    section_keywords=["not 4", "driftkostnader", "rörelsekostnader"],
    table_format="swedish_brf_standard",

    golden_examples=GOLDEN_EXAMPLES,
    anti_examples=ANTI_EXAMPLES,

    output_schema=Note4UtilitiesSchema,
    confidence_threshold=0.7
)

# ========================================
# AGENT FACTORY
# ========================================

def create_note4_utilities_agent(
    enable_learning: bool = False
) -> SpecialistAgent:
    """
    Factory function to create Note 4 Utilities specialist agent.

    Args:
        enable_learning: If True, run 3-iteration learning loop on initialization

    Returns:
        Trained SpecialistAgent ready for production use
    """

    agent = SpecialistAgent(
        agent_id="note4_utilities_agent",
        current_prompt=NOTE4_UTILITIES_SPEC,
        schema=Note4UtilitiesSchema,
        learning_history=[],
        performance_stats={}
    )

    if enable_learning:
        from specialist_learning_loop import SpecialistLearningLoop

        # Load ground truth for training
        ground_truth = [
            {
                "pdf": "brf_198532.pdf",
                "fields": {
                    "el": 698763,
                    "varme": 438246,
                    "vatten": 162487
                }
            }
            # Add more GT examples as available
        ]

        # Run learning loop
        learning_loop = SpecialistLearningLoop(
            specialist_id="note4_utilities_agent",
            initial_prompt=NOTE4_UTILITIES_SPEC,
            ground_truth_examples=ground_truth,
            test_pdfs=["brf_198532.pdf", "brf_268882.pdf"],
            max_iterations=3
        )

        trained_prompt = learning_loop.train()
        agent.current_prompt = trained_prompt
        agent.learning_history = learning_loop.learning_history

    return agent
```

---

## Summary & Next Steps

### Key Innovations

1. **Specialist Pattern Analysis**: Extract golden patterns from successful extractions for targeted training
2. **Pydantic Schema Decomposition**: Fine-grained schemas with built-in validation for quality control
3. **3-Iteration Self-Learning**: Agents auto-refine prompts based on GT mismatches using LLM coaching
4. **Docling-Powered Orchestration**: Intelligent section routing with 3-layer fallback (keyword → fuzzy → LLM)
5. **Cross-Validation**: Consistency checks across related specialists prevent contradictory extractions

### Expected Outcomes

- **Coverage**: 78.4% → 95%+ (22+ specialists vs 8 comprehensive agents)
- **Accuracy**: Current → 95%+ (Pydantic validation + self-learning)
- **Maintainability**: Easier to debug/improve (1 specialist = 1-3 fields)
- **Adaptability**: Auto-learns from ground truth (no manual prompt engineering)

### Implementation Timeline

**Day 5 (11 hours)**:
- Phase 1 (2h): Foundation + schemas
- Phase 2 (3h): Core 13 specialists
- Phase 3 (2h): Learning loop
- Phase 4 (2h): Orchestration
- Phase 5 (2h): Validation

**Ready for production**: End of Day 5 with 90%+ coverage validated on 3 PDFs

This design provides a complete, implementable path to 95/95 through systematic specialist decomposition and self-learning.
