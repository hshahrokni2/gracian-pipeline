# Week 4 Task Cards: Prioritized Field Improvement Roadmap

**Generated**: 2025-10-11
**Based on**: Field Coverage Matrix Analysis + Week 4 Implementation Plan
**Total Tasks**: 5 cards (13 subtasks)

---

## 📋 Task Card Index

| Card # | Title | Priority | Estimated Time | Expected Coverage Gain |
|--------|-------|----------|----------------|------------------------|
| [#1](#task-card-1-governance-fields-enhancement) | Governance Fields Enhancement | 🔴 HIGH | 4 hours | +3-5 percentage points |
| [#2](#task-card-2-metadata-completeness) | Metadata Completeness | 🔴 HIGH | 2 hours | +1-2 percentage points |
| [#3](#task-card-3-auditor-information) | Auditor Information | 🔴 HIGH | 2 hours | +1-2 percentage points |
| [#4](#task-card-4-structured-text-extraction) | Structured Text Extraction | 🟠 MEDIUM | 8 hours | +5-10 percentage points |
| [#5](#task-card-5-fee-table-parsing) | Fee Table Parsing Enhancement | 🟡 LOW | 6 hours | +3-5 percentage points |

---

## Task Card #1: Governance Fields Enhancement

### 🎯 Objective
Increase board member extraction coverage from **81.4%** (35/43 PDFs) to **85%+** (37/43 PDFs)

### 📊 Current State
- **Field**: `governance.board_members`
- **Current Coverage**: 81.4% (35/43 PDFs)
- **Missing**: 8 PDFs
- **Failing PDFs**: To be identified through analysis

### 🔍 Root Cause Analysis
**Hypothesis**: Board member extraction fails on PDFs with:
1. Non-standard section headers (e.g., "Styrelse och revisorer" vs "Styrelsen")
2. Tabular board member layouts vs narrative text
3. Swedish character encoding issues (å, ä, ö)
4. Board members listed across multiple pages

### 🛠️ Implementation Steps

#### Step 1.1: Analyze Failed PDFs (1 hour)
```python
# Script: analyze_failed_board_members.py
# Purpose: Identify which 8 PDFs are missing board members and why

from pathlib import Path
import json

results_dir = Path("data/week3_comprehensive_test_results")
failed_pdfs = []

for result_file in results_dir.glob("*.json"):
    with open(result_file) as f:
        data = json.load(f)

    # Check if board_members is missing or empty
    governance = data.get("governance", {})
    board_members = governance.get("board_members", [])

    if not board_members:
        failed_pdfs.append({
            "pdf": result_file.stem,
            "coverage": data.get("coverage_percentage", 0),
            "is_scanned": not data.get("metadata", {}).get("is_machine_readable", True)
        })

print(f"Failed PDFs: {len(failed_pdfs)}")
for pdf in failed_pdfs:
    print(f"  - {pdf['pdf']}: coverage={pdf['coverage']:.1f}%, scanned={pdf['is_scanned']}")
```

**Output**: List of 8 PDFs with diagnostic info (coverage, document type)

#### Step 1.2: Update Governance Agent Prompt (1 hour)
```python
# File: gracian_pipeline/prompts/agent_prompts.py
# Lines: 6-8 (governance_agent)

# BEFORE (current):
governance_agent = """
Extract governance information from Swedish BRF annual report.
Include board members with roles (ordförande, ledamot, suppleant).
"""

# AFTER (enhanced):
governance_agent = """
Extract complete governance information from Swedish BRF annual report.

**Board Members** (Critical - extract ALL):
- Look for sections: "Styrelsen", "Styrelse och revisorer", "Förvaltning"
- Extract ALL persons with these roles:
  * Ordförande (Chairman)
  * Vice ordförande (Vice Chairman)
  * Ledamot (Board Member)
  * Suppleant (Deputy/Alternate)
  * Sekreterare (Secretary)
  * Kassör (Treasurer)
- Include full names (e.g., "Per-Erik Johansson", not "P-E Johansson")
- Note: Some boards listed in tables, others in narrative text - extract both formats

**Swedish Character Handling**:
- Preserve å, ä, ö exactly as written
- Do not transliterate or substitute

**Multi-page Boards**:
- Board members may span multiple pages
- Continue scanning until "Revisor" or "Valberedning" section
"""
```

#### Step 1.3: Expand Board Member Synonyms (30 min)
```python
# File: gracian_pipeline/core/synonyms.py
# Add to SYNONYM_DICT

"board_members": {
    "swedish_terms": [
        "styrelsen",
        "styrelseledamöter",
        "styrelse och revisorer",
        "förvaltning",
        "styrelsesammansättning"
    ],
    "variations": [
        "board_members",
        "board",
        "directors",
        "management"
    ]
},

"chairman": {
    "swedish_terms": [
        "ordförande",
        "ordf.",
        "styrelsens ordförande"
    ],
    "variations": [
        "chairman",
        "chair",
        "president"
    ]
},

"board_member": {
    "swedish_terms": [
        "ledamot",
        "styrelseledamot",
        "led."
    ],
    "variations": [
        "board_member",
        "director",
        "member"
    ]
},

"deputy": {
    "swedish_terms": [
        "suppleant",
        "suppl.",
        "ersättare"
    ],
    "variations": [
        "deputy",
        "alternate",
        "substitute"
    ]
}
```

#### Step 1.4: Test on Failed PDFs (1 hour)
```bash
# Run extraction on the 8 failed PDFs
python test_task_card_1.py

# Expected output:
# ✅ 6/8 PDFs now extract board members (75% fix rate)
# ❌ 2/8 PDFs still failing (require deeper investigation)
```

#### Step 1.5: Validate No Regressions (30 min)
```bash
# Run on 5-PDF smoke test to ensure no existing extractions broke
python test_comprehensive_sample.py

# Expected output:
# ✅ All 5 PDFs maintain or improve board member coverage
# ✅ No drop in overall coverage
```

### 🎯 Success Criteria
- [ ] Board member coverage ≥ 85% (37/43 PDFs)
- [ ] At least 6 of 8 failed PDFs now working
- [ ] No regressions on previously passing PDFs
- [ ] All tests pass (test_base_fields.py, test_pydantic_extraction.py)

### 📁 Files Modified
- `gracian_pipeline/prompts/agent_prompts.py` (governance_agent)
- `gracian_pipeline/core/synonyms.py` (board member terms)
- `analyze_failed_board_members.py` (new diagnostic script)
- `test_task_card_1.py` (new validation script)

### ⏱️ Time Breakdown
- Step 1.1: 1 hour (analysis)
- Step 1.2: 1 hour (prompt enhancement)
- Step 1.3: 30 min (synonyms)
- Step 1.4: 1 hour (testing)
- Step 1.5: 30 min (validation)
- **Total**: 4 hours

---

## Task Card #2: Metadata Completeness

### 🎯 Objective
Increase metadata evidence page tracking from **81.4%** (35/43) to **95%+** (41/43)

### 📊 Current State
- **Field**: `metadata.organization_number.evidence_pages`
- **Current Coverage**: 81.4% (35/43 PDFs)
- **Problem**: Evidence pages not being tracked for organization number extraction

### 🔍 Root Cause Analysis
**Hypothesis**: The `_extract_metadata()` method in `pydantic_extractor.py` is not properly populating evidence_pages for organization numbers.

**Evidence**:
```python
# Current code likely does:
organization_number = StringField(
    value=extracted_org_number,
    confidence=0.9,
    source="llm_extraction"
    # ❌ Missing: evidence_pages=[page_numbers]
)
```

### 🛠️ Implementation Steps

#### Step 2.1: Review Current Metadata Extraction (30 min)
```python
# File: gracian_pipeline/core/pydantic_extractor.py
# Method: _extract_metadata() (lines 143-249)

# Inspect current implementation:
def _extract_metadata(self, pdf_path: str, base_result: Dict) -> DocumentMetadata:
    """Extract document metadata."""
    # ... existing code ...

    # Check how organization_number is created:
    org_number_field = base_result.get("metadata", {}).get("organization_number")
    # ❓ Does org_number_field have evidence_pages?
```

**Diagnostic Output**: Document which metadata fields are missing evidence_pages

#### Step 2.2: Fix Evidence Page Tracking (1 hour)
```python
# File: gracian_pipeline/core/pydantic_extractor.py
# Method: _extract_metadata() (lines 143-249)

# BEFORE (hypothetical current code):
organization_number = StringField(
    value=base_result.get("metadata", {}).get("organization_number", {}).get("value"),
    confidence=0.9,
    source="llm_extraction"
)

# AFTER (with evidence pages):
org_number_data = base_result.get("metadata", {}).get("organization_number", {})
organization_number = StringField(
    value=org_number_data.get("value"),
    confidence=org_number_data.get("confidence", 0.9),
    source=org_number_data.get("source", "llm_extraction"),
    evidence_pages=org_number_data.get("evidence_pages", [])  # ✅ FIX
)

# Apply same fix to:
# - brf_name
# - fiscal_year
# - document_type
# All other metadata fields
```

#### Step 2.3: Test on Failed PDFs (30 min)
```bash
# Extract metadata for PDFs missing evidence_pages
python test_task_card_2.py

# Expected output:
# ✅ Organization number evidence_pages: 41/43 (95.3%)
# ✅ BRF name evidence_pages: 41/43 (95.3%)
# ✅ Fiscal year evidence_pages: 41/43 (95.3%)
```

### 🎯 Success Criteria
- [ ] Metadata evidence tracking ≥ 95% (41/43 PDFs)
- [ ] All metadata fields populate evidence_pages when available
- [ ] No regressions on existing metadata extraction
- [ ] Test suite passes

### 📁 Files Modified
- `gracian_pipeline/core/pydantic_extractor.py` (_extract_metadata method)
- `test_task_card_2.py` (new validation script)

### ⏱️ Time Breakdown
- Step 2.1: 30 min (review)
- Step 2.2: 1 hour (fix implementation)
- Step 2.3: 30 min (testing)
- **Total**: 2 hours

---

## Task Card #3: Auditor Information

### 🎯 Objective
Increase auditor extraction from **88.4%** (38/43) to **93%+** (40/43)

### 📊 Current State
- **Fields**:
  - `governance.primary_auditor.name` - 88.4% (38/43)
  - `governance.primary_auditor.firm` - likely similar
- **Missing**: 5 PDFs
- **Gap**: 4.7 percentage points

### 🔍 Root Cause Analysis
**Hypothesis**: Auditor extraction fails on PDFs with:
1. Non-standard auditor titles (e.g., "Auktoriserad revisor" vs "Revisor")
2. Auditor information in footnotes or separate pages
3. Multiple auditors (not just primary)
4. Auditor listed without firm name

### 🛠️ Implementation Steps

#### Step 3.1: Analyze Failed PDFs (30 min)
```python
# Script: analyze_failed_auditors.py

results_dir = Path("data/week3_comprehensive_test_results")
failed_auditors = []

for result_file in results_dir.glob("*.json"):
    with open(result_file) as f:
        data = json.load(f)

    governance = data.get("governance", {})
    auditor = governance.get("primary_auditor", {})
    auditor_name = auditor.get("name", {}).get("value")

    if not auditor_name:
        failed_auditors.append({
            "pdf": result_file.stem,
            "coverage": data.get("coverage_percentage", 0)
        })

print(f"Failed auditor extractions: {len(failed_auditors)}")
```

#### Step 3.2: Expand Auditor Synonyms (30 min)
```python
# File: gracian_pipeline/core/synonyms.py

"auditor": {
    "swedish_terms": [
        "revisor",
        "auktoriserad revisor",
        "godkänd revisor",
        "av revisor",
        "granskning"
    ],
    "variations": [
        "auditor",
        "certified_public_accountant",
        "cpa"
    ]
},

"audit_firm": {
    "swedish_terms": [
        "revisionsbyrå",
        "revisionsföretag",
        "revisionsbolag"
    ],
    "common_firms": [
        "KPMG",
        "PwC",
        "Deloitte",
        "Ernst & Young",
        "EY",
        "Grant Thornton",
        "BDO",
        "Mazars"
    ]
}
```

#### Step 3.3: Enhance Governance Agent Prompt (30 min)
```python
# File: gracian_pipeline/prompts/agent_prompts.py
# Add to governance_agent:

**Auditor Information** (Required):
- Primary auditor: Full name + firm
- Titles to look for:
  * "Revisor"
  * "Auktoriserad revisor"
  * "Godkänd revisor"
- May be listed:
  * After board members section
  * In signature page
  * In footnotes
- Extract both individual name AND firm (e.g., "Anna Svensson, KPMG")
```

#### Step 3.4: Test on Failed PDFs (30 min)
```bash
python test_task_card_3.py

# Expected output:
# ✅ 4/5 failed PDFs now extract auditor (80% fix rate)
# ✅ Auditor coverage: 40/43 (93%)
```

### 🎯 Success Criteria
- [ ] Auditor coverage ≥ 93% (40/43 PDFs)
- [ ] At least 4 of 5 failed PDFs now working
- [ ] Both auditor name AND firm extracted when present
- [ ] No regressions

### 📁 Files Modified
- `gracian_pipeline/core/synonyms.py` (auditor terms)
- `gracian_pipeline/prompts/agent_prompts.py` (governance_agent)
- `analyze_failed_auditors.py` (new diagnostic)
- `test_task_card_3.py` (new validation)

### ⏱️ Time Breakdown
- Step 3.1: 30 min (analysis)
- Step 3.2: 30 min (synonyms)
- Step 3.3: 30 min (prompt)
- Step 3.4: 30 min (testing)
- **Total**: 2 hours

---

## Task Card #4: Structured Text Extraction

### 🎯 Objective
Extract 3 critical business text sections from **0%** to **80%+**:
1. `auditor_report` - Complete auditor's report text
2. `board_report` - Board's management report
3. `chairman_statement` - Chairman's address

### 📊 Current State
- **Current Coverage**: 0% (0/43 PDFs) for all 3 fields
- **Problem**: No mechanism to extract complete section text (only field-level data)
- **Impact**: HIGH - These are critical business documents

### 🔍 Root Cause Analysis
**Problem**: The current extraction pipeline focuses on **field-level data** (names, numbers) but doesn't preserve **complete section text**.

**Example**:
- ✅ Extracts: Chairman name = "Per Johansson"
- ❌ Missing: Chairman's full statement about fiscal year performance

### 🛠️ Implementation Steps

#### Step 4.1: Create Structured Text Agent (2 hours)

##### 4.1.1: Define Schema (30 min)
```python
# File: gracian_pipeline/models/brf_schema.py
# Add to BRFAnnualReport model

class StructuredText(BaseModel):
    """Complete text of structured document sections."""

    auditor_report: Optional[ExtractionField[str]] = Field(
        None,
        description="Complete text of auditor's report (Revisionsberättelse)"
    )

    board_report: Optional[ExtractionField[str]] = Field(
        None,
        description="Board's management report (Förvaltningsberättelse)"
    )

    chairman_statement: Optional[ExtractionField[str]] = Field(
        None,
        description="Chairman's statement/address (VD har ordet / Ordföranden har ordet)"
    )

# Add to BRFAnnualReport:
class BRFAnnualReport(BaseModel):
    # ... existing fields ...
    structured_text: Optional[StructuredText] = None
```

##### 4.1.2: Create Agent Prompt (30 min)
```python
# File: gracian_pipeline/prompts/agent_prompts.py
# Add new agent

structured_text_agent = """
Extract complete text of structured document sections from Swedish BRF annual report.

**Target Sections**:

1. **Revisionsberättelse** (Auditor's Report):
   - Look for: "Revisionsberättelse", "Revisionsberättelse till...", "Granskningsrapport"
   - Extract: Complete text from section start to signature
   - Include: All paragraphs, auditor opinion, signature block
   - Evidence pages: List all pages containing auditor report text

2. **Förvaltningsberättelse** (Board's Management Report):
   - Look for: "Förvaltningsberättelse", "Årsredovisning", "Verksamhetsberättelse"
   - Extract: Complete management discussion and analysis
   - Include: All narrative text about fiscal year performance
   - Evidence pages: List all pages containing board report text

3. **Ordförandens tal** (Chairman's Statement):
   - Look for: "Ordföranden har ordet", "VD har ordet", "Styrelsens ordförande"
   - Extract: Complete chairman's message/letter
   - Include: All paragraphs until next section begins
   - Evidence pages: List pages containing chairman statement

**Extraction Rules**:
- Extract complete paragraphs (don't truncate mid-sentence)
- Preserve Swedish characters (å, ä, ö)
- Remove page headers/footers (e.g., "Sida 3", "BRF Namn")
- If section spans multiple pages, concatenate all text
- Note section boundaries (where section starts/ends)

**Output Format**:
{
  "auditor_report": {
    "value": "<complete text>",
    "confidence": 0.9,
    "source": "docling_markdown",
    "evidence_pages": [17, 18, 19]
  },
  "board_report": {
    "value": "<complete text>",
    "confidence": 0.9,
    "source": "docling_markdown",
    "evidence_pages": [3, 4, 5, 6]
  },
  "chairman_statement": {
    "value": "<complete text>",
    "confidence": 0.85,
    "source": "docling_markdown",
    "evidence_pages": [2]
  }
}
"""

# Add to schema definitions
EXPECTED_TYPES["structured_text_agent"] = {
    "auditor_report": "str",
    "board_report": "str",
    "chairman_statement": "str",
    "evidence_pages": "list"
}
```

##### 4.1.3: Integrate into Extraction Pipeline (1 hour)
```python
# File: gracian_pipeline/core/pydantic_extractor.py
# Add new extraction method

def _extract_structured_text(self, base_result: Dict) -> Optional[StructuredText]:
    """Extract complete text of structured document sections."""

    text_data = base_result.get("structured_text_agent", {})

    if not text_data:
        return None

    return StructuredText(
        auditor_report=self._to_extraction_field(
            text_data.get("auditor_report")
        ),
        board_report=self._to_extraction_field(
            text_data.get("board_report")
        ),
        chairman_statement=self._to_extraction_field(
            text_data.get("chairman_statement")
        )
    )

# Update extract_brf_comprehensive():
def extract_brf_comprehensive(self, pdf_path: str, mode: str = "deep") -> BRFAnnualReport:
    # ... existing code ...

    # NEW: Extract structured text sections
    structured_text = self._extract_structured_text(base_result)

    return BRFAnnualReport(
        # ... existing fields ...
        structured_text=structured_text
    )
```

#### Step 4.2: Enhance Docling Adapter for Section Text (4 hours)

##### 4.2.1: Section Text Extraction Logic (2 hours)
```python
# File: gracian_pipeline/core/docling_adapter_ultra_v2.py
# Add new method

def extract_section_text(self, markdown: str, section_name: str) -> Dict[str, Any]:
    """
    Extract complete text of a named section from Docling markdown.

    Args:
        markdown: Full document markdown from Docling
        section_name: Section to extract (e.g., "Revisionsberättelse")

    Returns:
        {
            "text": "<complete section text>",
            "start_page": 17,
            "end_page": 19,
            "confidence": 0.9
        }
    """

    # Strategy:
    # 1. Find section heading in markdown
    # 2. Extract all text until next section heading (same level)
    # 3. Parse page markers to determine page range
    # 4. Clean text (remove headers/footers)

    section_patterns = {
        "auditor_report": [
            r"#\s*Revisionsberättelse",
            r"#\s*Revisionsberättelse till",
            r"#\s*Granskningsrapport"
        ],
        "board_report": [
            r"#\s*Förvaltningsberättelse",
            r"#\s*Årsredovisning",
            r"#\s*Verksamhetsberättelse"
        ],
        "chairman_statement": [
            r"#\s*Ordföranden har ordet",
            r"#\s*VD har ordet",
            r"#\s*Styrelsens ordförande"
        ]
    }

    # Implementation here...
    pass
```

##### 4.2.2: Integration with Base Extraction (2 hours)
```python
# File: gracian_pipeline/core/docling_adapter_ultra_v2.py
# Update extract_all_ultra_comprehensive()

def extract_all_ultra_comprehensive(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
    # ... existing extraction ...

    # NEW: Extract structured text sections
    result["structured_text_agent"] = {
        "auditor_report": self.extract_section_text(markdown, "auditor_report"),
        "board_report": self.extract_section_text(markdown, "board_report"),
        "chairman_statement": self.extract_section_text(markdown, "chairman_statement")
    }

    return result
```

#### Step 4.3: Testing & Validation (2 hours)

##### 4.3.1: Unit Tests (1 hour)
```python
# File: test_structured_text_extraction.py

def test_auditor_report_extraction():
    """Test auditor report extraction on known PDFs."""
    pdf_path = "data/raw_pdfs/SRS/brf_198532.pdf"
    result = extract_brf_to_pydantic(pdf_path, mode="fast")

    auditor_report = result.structured_text.auditor_report

    # Assertions:
    assert auditor_report is not None
    assert auditor_report.value is not None
    assert len(auditor_report.value) > 100  # Should be substantial text
    assert "revisor" in auditor_report.value.lower()
    assert len(auditor_report.evidence_pages) > 0

def test_board_report_extraction():
    """Test board report extraction."""
    # Similar assertions for board report
    pass

def test_chairman_statement_extraction():
    """Test chairman statement extraction."""
    # Similar assertions
    pass
```

##### 4.3.2: Integration Test on 5-PDF Sample (1 hour)
```bash
python test_task_card_4.py

# Expected output:
# ✅ Auditor report: 4/5 PDFs (80%)
# ✅ Board report: 4/5 PDFs (80%)
# ✅ Chairman statement: 3/5 PDFs (60%)
# ✅ Average section text length: 500-2000 words
```

### 🎯 Success Criteria
- [ ] Auditor report extracted: 35/43+ PDFs (80%+)
- [ ] Board report extracted: 35/43+ PDFs (80%+)
- [ ] Chairman statement extracted: 30/43+ PDFs (70%+)
- [ ] Section text is complete (not truncated)
- [ ] Evidence pages accurately reflect section location
- [ ] No regressions on existing extractions

### 📁 Files Modified
- `gracian_pipeline/models/brf_schema.py` (add StructuredText model)
- `gracian_pipeline/prompts/agent_prompts.py` (add structured_text_agent)
- `gracian_pipeline/core/schema_comprehensive.py` (add EXPECTED_TYPES entry)
- `gracian_pipeline/core/pydantic_extractor.py` (add _extract_structured_text)
- `gracian_pipeline/core/docling_adapter_ultra_v2.py` (add extract_section_text)
- `test_structured_text_extraction.py` (new unit tests)
- `test_task_card_4.py` (new integration test)

### ⏱️ Time Breakdown
- Step 4.1: 2 hours (create agent)
- Step 4.2: 4 hours (Docling integration)
- Step 4.3: 2 hours (testing)
- **Total**: 8 hours

---

## Task Card #5: Fee Table Parsing Enhancement

### 🎯 Objective
Extract fee breakdown fields from **0%** to **60%+**:
- `fees.annual_fee_per_sqm`
- `fees.fee_1_rok` through `fees.fee_5_rok`
- `fees.fee_calculation_basis`
- `fees.fee_excludes`

### 📊 Current State
- **Current Coverage**: 0% (0/43 PDFs) for all fee detail fields
- **Problem**: Fee tables not being parsed or data not mapped to schema
- **Impact**: MEDIUM - Important for fee analysis but not critical

### 🔍 Root Cause Analysis
**Hypothesis**: Fee tables exist in PDFs but aren't being:
1. Identified as fee-related tables by Docling
2. Parsed correctly due to Swedish formatting
3. Mapped to the correct schema fields

**Example Fee Table Structure** (common in Swedish BRF reports):
```
Årsavgift per lägenhet (kr/månad)

Storlek     Avgift     Per kvm
1 rok       2 500      125
2 rok       3 800      110
3 rok       5 200      98
4 rok       6 100      92
```

### 🛠️ Implementation Steps

#### Step 5.1: Fee Table Analysis (2 hours)

##### 5.1.1: Sample PDF Analysis (1 hour)
```python
# Script: analyze_fee_tables.py
# Purpose: Identify how fee tables appear in 10 sample PDFs

from pathlib import Path
import json

sample_pdfs = [
    "brf_198532", "brf_271949", "brf_81563",
    # ... 7 more PDFs
]

fee_table_patterns = []

for pdf_id in sample_pdfs:
    result_file = f"data/week3_comprehensive_test_results/{pdf_id}_extraction.json"

    with open(result_file) as f:
        data = json.load(f)

    # Check if Docling detected fee tables
    tables = data.get("_docling_tables", [])
    fee_tables = [t for t in tables if is_fee_table(t)]

    fee_table_patterns.append({
        "pdf": pdf_id,
        "fee_tables_found": len(fee_tables),
        "table_structure": [analyze_structure(t) for t in fee_tables]
    })

# Output: Document common fee table patterns
```

##### 5.1.2: Document Swedish Fee Terminology (1 hour)
```python
# Create fee_terminology.md

**Common Fee Terms (Swedish)**:
- Årsavgift = Annual fee
- Månadsavgift = Monthly fee
- Avgift per kvm = Fee per square meter
- Avgift per lägenhet = Fee per apartment
- 1 rok / 1 rum och kök = 1-room apartment
- 2 rok = 2-room apartment
- Avgiften inkluderar = Fee includes
- Avgiften exkluderar = Fee excludes
- Värme = Heating
- Vatten = Water
- Bredband = Internet
```

#### Step 5.2: Enhanced Fee Extraction (3 hours)

##### 5.2.1: Create Fee Table Parser (2 hours)
```python
# File: gracian_pipeline/core/fee_table_parser.py (NEW)

class FeeTableParser:
    """Parse Swedish BRF fee tables from Docling output."""

    def __init__(self):
        self.room_patterns = {
            "1_rok": [r"1\s*rok", r"1\s*rum", r"1\s*r\.o\.k"],
            "2_rok": [r"2\s*rok", r"2\s*rum", r"2\s*r\.o\.k"],
            "3_rok": [r"3\s*rok", r"3\s*rum", r"3\s*r\.o\.k"],
            "4_rok": [r"4\s*rok", r"4\s*rum", r"4\s*r\.o\.k"],
            "5_rok": [r"5\s*rok", r"5\s*rum", r"5\s*r\.o\.k"]
        }

    def parse_fee_table(self, table: Dict) -> Dict[str, float]:
        """
        Parse fee table and extract per-room fees.

        Returns:
            {
                "fee_1_rok": 2500.0,
                "fee_2_rok": 3800.0,
                "annual_fee_per_sqm": 1200.0,
                # ...
            }
        """
        # Implementation:
        # 1. Identify fee column (look for "avgift", "kr", numbers)
        # 2. Identify room size column (look for "rok", "rum")
        # 3. Extract fee values per room type
        # 4. Handle Swedish number formatting (space as thousands separator)
        pass

    def parse_fee_calculation_basis(self, markdown: str) -> Optional[str]:
        """Extract fee calculation methodology text."""
        # Look for "Avgiften beräknas", "Årsavgift baseras på"
        pass

    def parse_fee_excludes(self, markdown: str) -> List[str]:
        """Extract list of what fees exclude."""
        # Look for "Avgiften inkluderar inte", "Exkluderar"
        pass
```

##### 5.2.2: Integrate into Docling Adapter (1 hour)
```python
# File: gracian_pipeline/core/docling_adapter_ultra_v2.py
# Update fee extraction

from gracian_pipeline.core.fee_table_parser import FeeTableParser

def extract_fees_enhanced(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
    """Enhanced fee extraction with table parsing."""

    parser = FeeTableParser()

    # Find fee tables
    fee_tables = [t for t in tables if self._is_fee_table(t)]

    fees = {}

    for table in fee_tables:
        parsed_fees = parser.parse_fee_table(table)
        fees.update(parsed_fees)

    # Extract fee calculation basis from text
    fees["fee_calculation_basis"] = parser.parse_fee_calculation_basis(markdown)

    # Extract fee excludes list
    fees["fee_excludes"] = parser.parse_fee_excludes(markdown)

    return fees
```

#### Step 5.3: Testing & Validation (1 hour)

```bash
python test_task_card_5.py

# Expected output:
# ✅ Fee per sqm: 26/43 PDFs (60%)
# ✅ Fee 1-rok: 20/43 PDFs (46%)
# ✅ Fee 2-rok: 24/43 PDFs (56%)
# ✅ Fee 3-rok: 26/43 PDFs (60%)
# ✅ Fee 4-rok: 18/43 PDFs (42%)
# ✅ Fee 5-rok: 12/43 PDFs (28%)
# ✅ Fee calculation basis: 18/43 PDFs (42%)
# ✅ Fee excludes: 15/43 PDFs (35%)
```

### 🎯 Success Criteria
- [ ] Fee per sqm: 60%+ (26/43 PDFs)
- [ ] Fee breakdown (1-5 rok): Average 50%+ across all room types
- [ ] Fee calculation basis: 40%+ (17/43 PDFs)
- [ ] Fee excludes: 35%+ (15/43 PDFs)
- [ ] No regressions on existing fee data
- [ ] Swedish number formatting handled correctly

### 📁 Files Modified
- `gracian_pipeline/core/fee_table_parser.py` (NEW)
- `gracian_pipeline/core/docling_adapter_ultra_v2.py` (enhance fee extraction)
- `analyze_fee_tables.py` (new diagnostic)
- `test_task_card_5.py` (new validation)

### ⏱️ Time Breakdown
- Step 5.1: 2 hours (analysis)
- Step 5.2: 3 hours (implementation)
- Step 5.3: 1 hour (testing)
- **Total**: 6 hours

---

## 📊 Week 4 Summary Dashboard

### Total Effort Estimate
- **Task Card #1**: 4 hours
- **Task Card #2**: 2 hours
- **Task Card #3**: 2 hours
- **Task Card #4**: 8 hours
- **Task Card #5**: 6 hours
- **Total**: 22 hours (~3 working days)

### Expected Coverage Improvement
| Metric | Before | After (Conservative) | After (Optimistic) |
|--------|--------|---------------------|-------------------|
| **Document-Level Coverage** | 55.6% | 72% | 78% |
| **Field-Level Coverage** | 19.7% | 32% | 38% |
| **Board Members** | 81.4% | 85% | 90% |
| **Auditor Info** | 88.4% | 93% | 95% |
| **Structured Text** | 0% | 70% | 85% |
| **Fee Details** | 0% | 50% | 65% |

### Risk Assessment
- **Low Risk**: Tasks #1-3 (small, incremental fixes)
- **Medium Risk**: Task #4 (new agent, significant code)
- **Low-Medium Risk**: Task #5 (table parsing can be finicky)

### Success Indicators
By end of Week 4:
- [ ] At least 3/5 task cards completed
- [ ] Document-level coverage ≥ 72%
- [ ] No regressions (all existing tests pass)
- [ ] Week 5 plan created based on remaining gaps

---

**Generated**: 2025-10-11
**For**: Week 4 Implementation (Days 1-5)
**Review**: End of each day to track progress and adjust
