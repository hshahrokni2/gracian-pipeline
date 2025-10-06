# Robust & Scalable Fixes for Ultra-Comprehensive Extraction
**Date**: 2025-10-06
**Status**: Architecture Design (Ready for Implementation)
**Target**: Production-grade solution for 26,342 document corpus

---

## Executive Summary

**3 Critical Issues** identified in POST_COMPACTION_ANALYSIS.md require **architectural solutions**, not quick fixes:

1. **Financial Table Details Gap** → Multi-pass hierarchical table extraction
2. **Apartment Breakdown Granularity** → Intelligent table detection with fallback
3. **Fee Field Semantics** → Multi-lingual schema redesign

**Key Insight**: These are not bugs, they're **structural patterns in Swedish BRF documents** that require specialized handling at scale.

---

## Issue 1: Financial Table Details - Hierarchical Multi-Pass Solution

### Problem Analysis

**Root Cause**: Note 4 (DRIFTKOSTNADER) and similar financial notes have **nested table structures**:

```
DRIFTKOSTNADER                           2021        2020
├─ Fastighetskostnader                   553,590     653,192
│  ├─ Fastighetsskötsel entreprenad      185,600     184,529
│  ├─ Fastighetsskötsel beställning       15,291      10,122
│  └─ ... (15+ items)
├─ Reparationer                          258,004     206,330
│  ├─ Lokaler                             35,731           0
│  ├─ Sophantering/återvinning             4,223      29,450
│  └─ ... (13+ items)
└─ ... (5 categories total, 50+ line items)
```

**Current Extraction** (WRONG):
```json
"operating_costs_breakdown": {
  "Driftkostnader": 2834798  // ❌ Top-level summary only
}
```

**Required Extraction** (CORRECT):
```json
"operating_costs_breakdown": {
  "Fastighetskostnader": {
    "items": [
      {"name": "Fastighetsskötsel entreprenad", "2021": 185600, "2020": 184529},
      // ... ALL 15 items
    ],
    "subtotal": {"2021": 553590, "2020": 653192}
  },
  // ... all 5 categories with full detail
}
```

### Robust Solution: Hierarchical Table Parser

#### Architecture

```python
class HierarchicalFinancialExtractor:
    """
    Specialized extractor for nested Swedish BRF financial tables.
    Handles Note 4, 8, 9, 10 with full line-item preservation.
    """

    def __init__(self):
        self.note_patterns = {
            "note_4": {
                "name": "DRIFTKOSTNADER",
                "categories": ["Fastighetskostnader", "Reparationer", "Periodiskt underhåll",
                              "Taxebundna kostnader", "Övriga driftkostnader"],
                "expected_items": 50,
                "page_hint": "typically pages 7-9"
            },
            "note_8": {
                "name": "BYGGNADER",
                "structure": "depreciation_schedule",
                "expected_items": 5,
                "page_hint": "typically page 10"
            },
            # ... other notes
        }

    def extract_note_4_detailed(self, pdf_path: str, note_pages: List[int]) -> Dict[str, Any]:
        """
        Extract complete Note 4 with all 50+ line items.

        Uses 3-stage process:
        1. Identify category boundaries
        2. Extract all items per category
        3. Validate subtotals match
        """

        # Stage 1: Extract markdown for just note pages
        note_markdown, note_tables = self.extract_note_section(pdf_path, note_pages)

        # Stage 2: Use specialized prompt for hierarchical structure
        prompt = self.build_hierarchical_prompt(
            note_id="note_4",
            markdown=note_markdown,
            tables=note_tables
        )

        # Stage 3: Extract with high token limit for full detail
        result = self.call_gpt4o_extended(
            prompt=prompt,
            max_tokens=12000,  # Increased for 50+ items
            temperature=0
        )

        # Stage 4: Validate structure
        validated = self.validate_hierarchical_structure(
            result,
            expected_categories=self.note_patterns["note_4"]["categories"],
            expected_min_items=self.note_patterns["note_4"]["expected_items"]
        )

        return validated

    def build_hierarchical_prompt(self, note_id: str, markdown: str, tables: List[Dict]) -> str:
        """
        Build specialized prompt for hierarchical table extraction.
        """

        pattern = self.note_patterns[note_id]

        return f"""
Extract COMPLETE hierarchical breakdown from {pattern["name"]}.

CRITICAL STRUCTURE RULES:
1. This is a NESTED table with category headers and line items
2. Extract ALL categories: {", ".join(pattern["categories"])}
3. Under each category, extract EVERY line item (not just first few)
4. Each line item must have both years: 2021 and 2020
5. Each category must have a subtotal
6. Minimum expected items: {pattern["expected_items"]}

OUTPUT SCHEMA:
{{
  "category_name": {{
    "items": [
      {{"name": "Line item name", "2021": number, "2020": number}},
      // ... ALL items under this category
    ],
    "subtotal": {{"2021": number, "2020": number}}
  }},
  // ... repeat for ALL categories
}}

VALIDATION:
- Count items extracted: Must be ≥ {pattern["expected_items"]}
- All categories present: {len(pattern["categories"])}
- Subtotals mathematically correct

DOCUMENT TEXT (pages {note_pages}):
{markdown}

TABLES:
{self.format_tables_hierarchical(tables)}

REMEMBER: Extract EVERY line item, not summaries. This is for detailed financial analysis.
"""

    def validate_hierarchical_structure(self, extraction: Dict, expected_categories: List[str],
                                       expected_min_items: int) -> Dict[str, Any]:
        """
        Validate extracted hierarchical structure.
        Returns extraction + validation metadata.
        """

        validation = {
            "categories_found": len(extraction),
            "categories_expected": len(expected_categories),
            "total_items_extracted": 0,
            "subtotals_validated": True,
            "warnings": []
        }

        # Check all categories present
        for expected_cat in expected_categories:
            if expected_cat not in extraction:
                validation["warnings"].append(f"Missing category: {expected_cat}")

        # Count total items and validate subtotals
        for category, data in extraction.items():
            items = data.get("items", [])
            subtotal = data.get("subtotal", {})

            validation["total_items_extracted"] += len(items)

            # Validate subtotal matches sum of items
            if items and subtotal:
                calculated_2021 = sum(item.get("2021", 0) for item in items)
                claimed_2021 = subtotal.get("2021", 0)

                if abs(calculated_2021 - claimed_2021) > 1:  # Allow rounding error
                    validation["subtotals_validated"] = False
                    validation["warnings"].append(
                        f"{category}: Subtotal mismatch (items sum: {calculated_2021}, "
                        f"claimed: {claimed_2021})"
                    )

        # Check minimum item count
        if validation["total_items_extracted"] < expected_min_items:
            validation["warnings"].append(
                f"Low item count: {validation['total_items_extracted']} < {expected_min_items} expected"
            )

        # Add validation metadata to extraction
        extraction["_validation"] = validation

        return extraction

    def extract_note_section(self, pdf_path: str, page_indices: List[int]) -> Tuple[str, List[Dict]]:
        """
        Extract markdown + tables for specific pages only.
        Increases context focus on target section.
        """
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        # Filter to just target pages
        filtered_markdown = self.filter_markdown_by_pages(result.document.export_to_markdown(), page_indices)
        filtered_tables = [t for t in result.document.tables if t.page_number in page_indices]

        return filtered_markdown, filtered_tables
```

#### Implementation Strategy

**Phase 1: Single-Note Proof of Concept** (1-2 days)
```python
# Test on Note 4 only with brf_198532.pdf
extractor = HierarchicalFinancialExtractor()
note_4_result = extractor.extract_note_4_detailed(
    "SRS/brf_198532.pdf",
    note_pages=[7, 8, 9]  # Known location for this document
)

# Validate: Should have 50+ items across 5 categories
assert note_4_result["_validation"]["total_items_extracted"] >= 50
```

**Phase 2: Multi-Note Extraction** (2-3 days)
```python
# Extend to Notes 8, 9, 10
for note_id in ["note_4", "note_8", "note_9", "note_10"]:
    result = extractor.extract_note_detailed(pdf_path, note_id)
```

**Phase 3: Integration with Ultra-Comprehensive** (1 day)
```python
class UltraComprehensiveDoclingAdapterV2(UltraComprehensiveDoclingAdapter):
    """
    Enhanced with hierarchical financial extraction.
    """

    def extract_brf_data_ultra(self, pdf_path: str) -> Dict[str, Any]:
        # Pass 1: Standard ultra-comprehensive (fast, broad)
        base_result = super().extract_brf_data_ultra(pdf_path)

        # Pass 2: Hierarchical financial notes (slow, deep)
        if self.should_extract_detailed_notes(base_result):
            financial_extractor = HierarchicalFinancialExtractor()

            detailed_notes = financial_extractor.extract_all_notes(
                pdf_path,
                notes=["note_4", "note_8", "note_9", "note_10"]
            )

            # Merge into base result
            base_result["financial_agent"]["operating_costs_breakdown"] = detailed_notes["note_4"]
            base_result["financial_agent"]["building_details"] = detailed_notes["note_8"]
            # ... merge other notes

            base_result["_extraction_mode"] = "ultra_comprehensive_v2_hierarchical"

        return base_result
```

**Scalability**:
- ✅ Works for all 26,342 documents (Note 4 structure is standardized)
- ✅ Parallel processing possible (each note independently)
- ✅ Graceful degradation if note missing
- ✅ Self-validating with quality warnings

---

## Issue 2: Apartment Breakdown - Intelligent Table Detection

### Problem Analysis

**Two Forms in Documents**:

1. **Summary** (what we're currently getting):
   ```
   "Föreningen består av 94 lägenheter och 2 lokaler"
   ```

2. **Detailed Table** (what we want):
   ```
   | Lägenhetsstorlek | Antal |
   |------------------|-------|
   | 1 rok            | 10    |
   | 2 rok            | 24    |
   | 3 rok            | 30    |
   | ...              | ...   |
   ```

### Robust Solution: Progressive Detail Extraction

```python
class ApartmentBreakdownExtractor:
    """
    Intelligent apartment breakdown extraction with fallback levels.
    Tries detailed table first, falls back to summary if not found.
    """

    def extract_apartment_breakdown(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract apartment breakdown with progressive detail levels.

        Priority:
        1. Detailed table (1 rok, 2 rok, etc.) - BEST
        2. Summary counts (total lägenheter, lokaler) - ACCEPTABLE
        3. Null with warning - DOCUMENTED FAILURE
        """

        # Try Level 1: Detailed table extraction
        detailed = self.try_extract_detailed_breakdown(markdown, tables)
        if detailed:
            return {
                "granularity": "detailed",
                "breakdown": detailed,
                "source": "table_extraction"
            }

        # Try Level 2: Summary extraction
        summary = self.try_extract_summary_breakdown(markdown)
        if summary:
            return {
                "granularity": "summary",
                "breakdown": summary,
                "source": "text_extraction",
                "_warning": "Detailed breakdown table not found, using summary counts"
            }

        # Level 3: Failed extraction
        return {
            "granularity": "none",
            "breakdown": None,
            "source": "failed",
            "_error": "No apartment count information found in document"
        }

    def try_extract_detailed_breakdown(self, markdown: str, tables: List[Dict]) -> Optional[Dict[str, int]]:
        """
        Attempt to extract detailed breakdown table.

        Table patterns to match:
        - Headers: "Lägenhetsstorlek", "Antal rum", "Typ", "Storlek"
        - Rows: "1 rok", "2 rok", "3 rok", "4 rok", "5 rok", "Lokaler"
        """

        prompt = f"""
Search for a DETAILED apartment breakdown table in this document.

TARGET TABLE CHARACTERISTICS:
- Has rows for different apartment sizes: "1 rok", "2 rok", "3 rok", etc.
- Has a count/antal column
- May include "Lokaler" or "Kommersiella lokaler" row
- Common headers: "Lägenhetsstorlek", "Antal rum", "Typ", "Antal"

CRITICAL: Only extract if you find a DETAILED TABLE with multiple room types.
DO NOT extract if you only see summary text like "94 lägenheter".

OUTPUT FORMAT (only if detailed table found):
{{
  "1_rok": 10,
  "2_rok": 24,
  "3_rok": 30,
  "4_rok": 20,
  "5_rok": 10,
  "lokaler": 2
}}

If no detailed table found, return: {{"_not_found": true}}

DOCUMENT:
{markdown}

TABLES:
{self.format_tables(tables)}
"""

        result = self.call_gpt4o(prompt)

        # Validate it's actually detailed (has multiple rok types)
        if result and not result.get("_not_found"):
            rok_keys = [k for k in result.keys() if "rok" in k]
            if len(rok_keys) >= 3:  # At least 3 room types
                return result

        return None

    def try_extract_summary_breakdown(self, markdown: str) -> Optional[Dict[str, int]]:
        """
        Fallback: Extract summary apartment counts from text.

        Common patterns:
        - "Föreningen består av 94 lägenheter och 2 lokaler"
        - "Totalt antal lägenheter: 94"
        - "Lägenheter: 94, Lokaler: 2"
        """

        prompt = f"""
Extract summary apartment counts from text.

Look for phrases like:
- "X lägenheter" / "X apartments"
- "Y lokaler" / "Y commercial units"
- Total counts mentioned in text

OUTPUT:
{{
  "total_apartments": X,
  "commercial_units": Y
}}

DOCUMENT:
{markdown}
"""

        result = self.call_gpt4o(prompt)
        return result if result else None
```

#### Integration Strategy

```python
# In UltraComprehensiveDoclingAdapter
def extract_all_ultra_comprehensive(self, markdown: str, tables: List[Dict]) -> Dict[str, Any]:
    # ... existing extraction ...

    # Enhanced apartment breakdown extraction
    apt_extractor = ApartmentBreakdownExtractor()
    apartment_data = apt_extractor.extract_apartment_breakdown(markdown, tables)

    # Store with metadata
    result["property_agent"]["apartment_breakdown"] = apartment_data["breakdown"]
    result["property_agent"]["_apartment_breakdown_granularity"] = apartment_data["granularity"]

    if apartment_data.get("_warning"):
        result["property_agent"]["_warnings"] = [apartment_data["_warning"]]

    return result
```

**Scalability**:
- ✅ Handles both detailed and summary forms gracefully
- ✅ Self-documenting (granularity field)
- ✅ Can measure corpus statistics (% with detailed vs summary)
- ✅ Human review can focus on flagged summary cases

---

## Issue 3: Fee Field Semantics - Multi-Lingual Schema Redesign

### Problem Analysis

**Terminology Mismatch**:
- Swedish documents use: "Årsavgift/m²" (annual fee per square meter)
- English schema has: `monthly_fee` (assumes per-apartment, monthly)
- LLM correctly extracts Swedish but field name is misleading

### Robust Solution: Semantic Swedish-First Schema

```python
# gracian_pipeline/core/schema_comprehensive_v2.py

"""
Swedish-First BRF Schema with Semantic Clarity
Version 2.0 - Multi-lingual field naming
"""

from typing import Dict

# SEMANTIC FEE SCHEMA (Swedish-First)
COMPREHENSIVE_TYPES_V2 = {
    "fees_agent": {
        # SWEDISH BRF STANDARD FIELDS (Primary)
        "arsavgift_per_sqm": "num",           # Årsavgift/m² bostadsrättsyta (MOST COMMON)
        "arsavgift_per_apartment": "num",     # Årsavgift per lägenhet (rare)
        "manadsavgift_per_sqm": "num",        # Månadsavgift/m² (very rare)
        "manadsavgift_per_apartment": "num",  # Månadsavgift per lägenhet (uncommon)

        # FEE CHANGE INFORMATION
        "planned_fee_change": "str",          # E.g., "Oförändrade närmaste året"
        "fee_calculation_basis": "str",       # E.g., "självkostnadsprincipen"
        "fee_policy": "str",

        # METADATA (for validation and migration)
        "_fee_terminology_found": "str",      # Original Swedish term in PDF
        "_fee_unit_verified": "str",          # "per_sqm" | "per_apartment"
        "_fee_period_verified": "str",        # "annual" | "monthly"

        # LEGACY FIELDS (deprecated but maintained for backwards compatibility)
        "monthly_fee": "num",    # DEPRECATED: Use specific fields above
        "fee_per_sqm": "num",    # DEPRECATED: Time unit ambiguous
        "fee_unit": "str",       # DEPRECATED: Separate unit field not needed

        "evidence_pages": "list"
    }
}

# EXTRACTION GUIDANCE
FEE_EXTRACTION_GUIDE = """
FEE EXTRACTION RULES (Swedish BRF Documents):

STEP 1: Find exact Swedish terminology in document
Look for phrases:
- "Årsavgift/m² bostadsrättsyta: X"
- "Månadsavgift per lägenhet: Y"
- "Avgift per m² och år: Z"

STEP 2: Map to correct semantic field

Swedish Term                          → Field Name
"Årsavgift/m²"                        → arsavgift_per_sqm
"Årsavgift per lägenhet"              → arsavgift_per_apartment
"Månadsavgift/m²"                     → manadsavgift_per_sqm
"Månadsavgift per lägenhet"           → manadsavgift_per_apartment

STEP 3: Extract value and store metadata

Example:
PDF says: "Årsavgift/m² bostadsrättsyta: 582 kr"

Correct extraction:
{
  "arsavgift_per_sqm": 582,
  "_fee_terminology_found": "Årsavgift/m² bostadsrättsyta",
  "_fee_unit_verified": "per_sqm",
  "_fee_period_verified": "annual"
}

CRITICAL: Do NOT use legacy fields (monthly_fee, fee_per_sqm, fee_unit).
Use semantic Swedish-first fields.
"""
```

#### Migration Strategy for Existing Extractions

```python
class FeeFieldMigrator:
    """
    Migrate legacy fee extractions to semantic v2 schema.
    Ensures backwards compatibility during transition.
    """

    def migrate_fee_fields(self, extraction: Dict) -> Dict:
        """
        Migrate from v1 (English ambiguous) to v2 (Swedish semantic) schema.
        """
        fees = extraction.get("fees_agent", {})

        if not fees:
            return extraction

        # Check if already using v2 schema
        if any(k.startswith("arsavgift_") or k.startswith("manadsavgift_") for k in fees):
            return extraction  # Already migrated

        # Migrate legacy fields
        migration_log = []

        # Legacy "monthly_fee" → likely "arsavgift_per_sqm"
        if "monthly_fee" in fees and fees["monthly_fee"]:
            # Swedish BRFs almost never use true monthly fees
            # This is likely misnamed annual fee per sqm
            fees["arsavgift_per_sqm"] = fees["monthly_fee"]
            fees["_fee_unit_verified"] = "per_sqm"
            fees["_fee_period_verified"] = "annual"
            migration_log.append("monthly_fee → arsavgift_per_sqm (assumed annual)")

        # Legacy "fee_per_sqm" → likely "arsavgift_per_sqm"
        if "fee_per_sqm" in fees and fees["fee_per_sqm"]:
            if "arsavgift_per_sqm" not in fees:  # Don't overwrite if already set
                fees["arsavgift_per_sqm"] = fees["fee_per_sqm"]
                fees["_fee_unit_verified"] = "per_sqm"
                fees["_fee_period_verified"] = "annual"
                migration_log.append("fee_per_sqm → arsavgift_per_sqm (time unit assumed annual)")

        # Add migration metadata
        if migration_log:
            fees["_migration_applied"] = True
            fees["_migration_log"] = migration_log

        return extraction

    def validate_fee_semantics(self, extraction: Dict) -> List[str]:
        """
        Validate fee field semantics and flag issues.
        """
        warnings = []
        fees = extraction.get("fees_agent", {})

        # Check for legacy field usage
        if "monthly_fee" in fees:
            if not fees.get("_migration_applied"):
                warnings.append(
                    "Legacy field 'monthly_fee' used without migration - semantic accuracy uncertain"
                )

        # Validate metadata consistency
        if "arsavgift_per_sqm" in fees:
            if not fees.get("_fee_terminology_found"):
                warnings.append(
                    "arsavgift_per_sqm populated but no _fee_terminology_found - verify extraction"
                )

        # Check for contradictory fields
        if "arsavgift_per_sqm" in fees and "manadsavgift_per_sqm" in fees:
            warnings.append(
                "Both annual and monthly fees per sqm populated - verify document has both or extraction error"
            )

        return warnings
```

#### Prompt Enhancement for v2 Schema

```python
def schema_comprehensive_prompt_block_v2(agent_id: str) -> str:
    """
    Enhanced prompt for v2 schema with fee guidance.
    """

    if agent_id == "fees_agent":
        return f"""
FEES AGENT SCHEMA (v2 - Swedish-First Semantic Fields):

{FEE_EXTRACTION_GUIDE}

OUTPUT SCHEMA:
{{
  "arsavgift_per_sqm": number,           // If "Årsavgift/m²" found
  "arsavgift_per_apartment": number,     // If "Årsavgift per lägenhet" found
  "manadsavgift_per_sqm": number,        // If "Månadsavgift/m²" found
  "manadsavgift_per_apartment": number,  // If "Månadsavgift per lägenhet" found

  "planned_fee_change": "string",
  "fee_calculation_basis": "string",
  "fee_policy": "string",

  "_fee_terminology_found": "string",    // Exact Swedish phrase from PDF
  "_fee_unit_verified": "per_sqm" | "per_apartment",
  "_fee_period_verified": "annual" | "monthly",

  "evidence_pages": [page_numbers]
}}

CRITICAL: Extract exact Swedish terminology. Use semantic v2 fields only.
"""

    # ... other agents
```

**Scalability**:
- ✅ Works for all Swedish BRF documents
- ✅ Extensible to Norwegian, Finnish, Danish documents
- ✅ Clear migration path from v1 to v2
- ✅ Self-validating with semantic warnings
- ✅ Backwards compatible during transition

---

## Integrated Production Architecture

### Multi-Pass Extraction Pipeline

```python
class RobustUltraComprehensiveExtractor:
    """
    Production-grade multi-pass extractor with specialized handlers.
    Combines fast broad extraction with deep targeted extraction.
    """

    def __init__(self):
        self.base_extractor = UltraComprehensiveDoclingAdapter()
        self.financial_extractor = HierarchicalFinancialExtractor()
        self.apartment_extractor = ApartmentBreakdownExtractor()
        self.fee_migrator = FeeFieldMigrator()

    def extract_brf_document(self, pdf_path: str, mode: str = "auto") -> Dict[str, Any]:
        """
        Main extraction pipeline with progressive detail levels.

        Modes:
        - "fast": Base extraction only (60s)
        - "deep": Base + hierarchical financial (120s)
        - "auto": Adaptive based on document type (90s avg)
        """

        # PASS 1: Base ultra-comprehensive extraction
        print("Pass 1: Base extraction...")
        base_result = self.base_extractor.extract_brf_data_ultra(pdf_path)

        # PASS 2: Specialized deep extractions (if needed)
        if mode in ["deep", "auto"]:
            print("Pass 2: Deep extraction...")

            # 2a. Hierarchical financial notes
            if self.should_extract_financial_details(base_result):
                financial_details = self.financial_extractor.extract_all_notes(
                    pdf_path,
                    notes=["note_4", "note_8", "note_9", "note_10"]
                )
                base_result["financial_agent"]["operating_costs_breakdown"] = financial_details.get("note_4", {})
                base_result["financial_agent"]["_detailed_extraction"] = True

            # 2b. Detailed apartment breakdown (if summary detected)
            if base_result.get("property_agent", {}).get("_apartment_breakdown_granularity") == "summary":
                detailed_apt = self.apartment_extractor.try_extract_detailed_breakdown(
                    base_result["_docling_markdown"],
                    base_result["_docling_tables"]
                )
                if detailed_apt:
                    base_result["property_agent"]["apartment_breakdown"] = detailed_apt
                    base_result["property_agent"]["_apartment_breakdown_granularity"] = "detailed"
                    base_result["property_agent"]["_apartment_breakdown_upgraded"] = True

        # PASS 3: Semantic validation and migration
        print("Pass 3: Validation...")
        validated_result = self.validate_and_migrate(base_result)

        # PASS 4: Quality scoring
        print("Pass 4: Quality check...")
        final_result = self.calculate_quality_metrics(validated_result)

        return final_result

    def should_extract_financial_details(self, base_result: Dict) -> bool:
        """
        Decide if document needs deep financial extraction.

        Heuristic: If operating_costs_breakdown has < 10 items,
        it's likely summary-only and needs deep extraction.
        """
        breakdown = base_result.get("financial_agent", {}).get("operating_costs_breakdown", {})
        return len(breakdown) < 10

    def validate_and_migrate(self, extraction: Dict) -> Dict:
        """
        Validate extraction and migrate legacy fields.
        """
        # Migrate fee fields
        extraction = self.fee_migrator.migrate_fee_fields(extraction)

        # Validate semantics
        fee_warnings = self.fee_migrator.validate_fee_semantics(extraction)
        if fee_warnings:
            extraction.setdefault("_validation_warnings", []).extend(fee_warnings)

        # Validate financial details
        if extraction.get("financial_agent", {}).get("_detailed_extraction"):
            fin_validation = self.validate_financial_details(extraction["financial_agent"])
            if fin_validation.get("warnings"):
                extraction.setdefault("_validation_warnings", []).extend(fin_validation["warnings"])

        return extraction

    def validate_financial_details(self, financial_data: Dict) -> Dict:
        """
        Validate hierarchical financial extraction quality.
        """
        validation = {"warnings": []}

        breakdown = financial_data.get("operating_costs_breakdown", {})

        # Check item count
        if breakdown.get("_validation"):
            total_items = breakdown["_validation"]["total_items_extracted"]
            if total_items < 30:
                validation["warnings"].append(
                    f"Low financial detail: {total_items} items (expected 50+)"
                )

        return validation

    def calculate_quality_metrics(self, extraction: Dict) -> Dict:
        """
        Calculate comprehensive quality score.
        """
        metrics = {
            "total_fields": 107,
            "extracted_fields": self.count_extracted_fields(extraction),
            "coverage_percent": 0,
            "quality_score": "A",
            "warnings_count": len(extraction.get("_validation_warnings", [])),
            "detailed_extraction_applied": extraction.get("financial_agent", {}).get("_detailed_extraction", False)
        }

        metrics["coverage_percent"] = round(
            (metrics["extracted_fields"] / metrics["total_fields"]) * 100, 1
        )

        # Quality scoring
        if metrics["coverage_percent"] >= 95 and metrics["warnings_count"] == 0:
            metrics["quality_score"] = "A+"
        elif metrics["coverage_percent"] >= 90:
            metrics["quality_score"] = "A"
        elif metrics["coverage_percent"] >= 80:
            metrics["quality_score"] = "B"
        else:
            metrics["quality_score"] = "C"

        extraction["_quality_metrics"] = metrics
        return extraction

    def count_extracted_fields(self, extraction: Dict) -> int:
        """Count non-null fields across all agents."""
        count = 0
        for agent_data in extraction.values():
            if isinstance(agent_data, dict):
                count += sum(1 for v in agent_data.values() if v not in [None, [], {}, ""])
        return count
```

### Usage Examples

```python
# Production usage
extractor = RobustUltraComprehensiveExtractor()

# Fast mode (for quick screening)
result = extractor.extract_brf_document("path/to/doc.pdf", mode="fast")

# Deep mode (for complete analysis)
result = extractor.extract_brf_document("path/to/doc.pdf", mode="deep")

# Auto mode (adaptive)
result = extractor.extract_brf_document("path/to/doc.pdf", mode="auto")

# Access quality metrics
print(f"Coverage: {result['_quality_metrics']['coverage_percent']}%")
print(f"Quality: {result['_quality_metrics']['quality_score']}")
print(f"Warnings: {result.get('_validation_warnings', [])}")

# Access detailed financial data
financial_details = result["financial_agent"]["operating_costs_breakdown"]
if "_validation" in financial_details:
    print(f"Items extracted: {financial_details['_validation']['total_items_extracted']}")
```

---

## Implementation Roadmap

### Phase 1: Core Fixes (Week 1)

**Day 1-2: Hierarchical Financial Extractor**
- [ ] Implement `HierarchicalFinancialExtractor` class
- [ ] Test Note 4 extraction on brf_198532.pdf
- [ ] Validate 50+ items extracted

**Day 3: Apartment Breakdown Extractor**
- [ ] Implement `ApartmentBreakdownExtractor` class
- [ ] Test on 5 documents with known detailed tables
- [ ] Validate granularity detection

**Day 4-5: Schema v2 Migration**
- [ ] Create `schema_comprehensive_v2.py`
- [ ] Implement `FeeFieldMigrator`
- [ ] Test migration on existing extractions

### Phase 2: Integration (Week 2)

**Day 6-7: Multi-Pass Pipeline**
- [ ] Implement `RobustUltraComprehensiveExtractor`
- [ ] Test all 3 modes (fast, deep, auto)
- [ ] Validate quality metrics calculation

**Day 8-9: Validation & Testing**
- [ ] Run on SRS corpus (28 PDFs)
- [ ] Run on Hjorthagen corpus (15 PDFs)
- [ ] Collect quality statistics

**Day 10: Documentation & Deployment**
- [ ] Update README with v2 architecture
- [ ] Create migration guide for existing data
- [ ] Deploy to production environment

### Phase 3: Scale Testing (Week 3)

**Day 11-13: Corpus Testing**
- [ ] Run on 1,000 document sample
- [ ] Measure performance metrics
- [ ] Identify edge cases

**Day 14-15: Optimization**
- [ ] Optimize prompts based on corpus results
- [ ] Tune quality thresholds
- [ ] Implement caching for repeated documents

---

## Success Metrics

### Coverage Targets

| Metric | Current | Phase 1 Target | Phase 3 Target |
|--------|---------|----------------|----------------|
| Overall Coverage | 68.2% | 85% | 95% |
| Financial Detail Coverage | 4 items | 50+ items | 50+ items |
| Apartment Breakdown Detailed | 0% | 60% | 80% |
| Fee Semantic Accuracy | 60% | 95% | 98% |

### Quality Metrics

- **A+ grade**: ≥95% coverage, 0 warnings
- **A grade**: ≥90% coverage, <3 warnings
- **B grade**: ≥80% coverage, <5 warnings

### Performance Targets

- **Fast mode**: <60s per document
- **Deep mode**: <120s per document
- **Auto mode**: <90s per document (average)

---

## Conclusion

This architecture provides:

✅ **Robust**: Handles missing data, validates extraction quality, provides warnings
✅ **Scalable**: Works for entire 26,342 corpus, parallel processing ready
✅ **Self-Documenting**: Quality metrics, granularity flags, migration metadata
✅ **Production-Ready**: Multiple modes, graceful degradation, backwards compatible

**Ready for implementation**. Each component can be developed and tested independently, then integrated into the multi-pass pipeline.
