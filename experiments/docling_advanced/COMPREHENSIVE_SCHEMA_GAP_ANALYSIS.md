# Comprehensive Schema Gap Analysis - Ground Truth Validation

**Date**: 2025-10-09
**Test Document**: `brf_198532.pdf` (BRF Björk och Plaza)
**Validation Method**: Field-by-field comparison against human-verified ground truth

---

## 🎯 Executive Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **TRUE Coverage** | **5.1%** (2/39 fields) | 100% | **-94.9%** ❌ |
| **TRUE Accuracy** | **0.0%** (0/2 correct) | 100% | **-100%** ❌ |

### Root Cause
**Fundamental Schema Mismatch**: The extraction pipeline extracts **flat, simple data** while ground truth expects **hierarchical, structured data**.

---

## 📊 Section-by-Section Gap Analysis

### 1. GOVERNANCE AGENT ⚠️ **25.0% Coverage, 0.0% Accuracy**

#### What's Extracted (CURRENT)
```json
{
  "board_members": [
    "Torbjörn Andersson",
    "Maria Annelie Eck Arvstrand",
    "Mats Eskilson",
    "Fredrik Linde",
    "Lisa Lind",
    "Daniel Wetter"
  ],
  "nomination_committee": []
}
```

#### What Ground Truth Expects
```json
{
  "board_members": [
    {
      "name": "Elvy Maria Löfvenberg",
      "role": "Ordförande",  // ← MISSING: Chairman role
      "term_expires_at_next_meeting": true
    },
    {
      "name": "Torbjörn Andersson",
      "role": "Ledamot",
      "term_expires_at_next_meeting": true
    },
    // ... 5 more structured members
    {
      "name": "Lisa Lind",
      "role": "Suppleant",  // ← MISSING: Alternate designation
      "term_expires_at_next_meeting": true
    }
  ],
  "board_meetings_count": 14,  // ← MISSING FIELD
  "auditors": [  // ← MISSING FIELD
    {
      "name": "Tobias Andersson",
      "type": "Ordinarie Extern",
      "firm": "KPMG AB"
    },
    {
      "name": "Oskar Klenell",
      "type": "Ordinarie Intern",
      "firm": "Internrevisor Brf"
    }
  ],
  "nomination_committee": [  // ← EXTRACTED AS EMPTY LIST
    {
      "name": "Victoria Blennborn",
      "role": "Sammankallande"
    },
    {
      "name": "Mattias Lovén",
      "role": "Member"
    }
  ],
  "annual_meeting_date": "2021-06-08",  // ← MISSING FIELD
  "samf_membership": {  // ← MISSING FIELD
    "name": "Sonfjällets samfällighetsförening",
    "ownership_share": 0.47,
    "purpose": "Förvaltar gård, garagefoajé och garageport"
  }
}
```

#### Critical Issues
1. **Board Members**: Simple list of names vs structured objects with roles
2. **Missing Chairman**: Elvy Maria Löfvenberg not extracted (role identification failure)
3. **Missing Suppleants**: Lisa Lind and Daniel Wetter not identified as alternates
4. **6 Completely Missing Fields**: board_meetings_count, auditors, annual_meeting_date, samf_membership

---

### 2. FINANCIAL AGENT 🔴 **0.0% Coverage**

#### What's Extracted (CURRENT)
```json
{
  // NOTHING - No financial fields extracted at all
}
```

#### What Ground Truth Expects
```json
{
  "income_statement": {
    "2021": {
      "revenue": {
        "net_sales": 7393591,
        "other_operating_income": 57994,
        "total": 7451585
      },
      "operating_expenses": {
        "operating_costs": -2834798,
        "other_external_costs": -229331,
        "personnel_costs": -63912,
        "depreciation": -3503359,
        "total": -6631400
      },
      "operating_result": 820184,
      "financial_items": {
        "interest_income": 190038,
        "interest_expenses": -1364032,
        "total": -1173994
      },
      "result_after_financial": -353810,
      "year_result": -353810
    },
    "2020": {
      // ... complete 2020 breakdown
    }
  },
  "balance_sheet": {
    "2021": {
      "assets": {
        "fixed_assets": {
          "buildings": 666670761,
          "total": 666670761
        },
        "current_assets": {
          "receivables": 5480836,
          "cash_bank": 3143189,
          "total": 8624026
        },
        "total_assets": 675294786
      },
      "equity_liabilities": {
        "equity": {
          "bound": {
            "member_deposits": 563055875,
            "maintenance_fund": 1026655,
            "total": 564082530
          },
          "accumulated_loss": {
            "retained_earnings": -3921044,
            "year_result": -353810,
            "total": -4274854
          },
          "total_equity": 559807676
        },
        "long_term_liabilities": {
          "bank_loans": 85980000,
          "total": 85980000
        },
        "short_term_liabilities": {
          "short_term_bank_loans": 28500000,
          "accounts_payable": 161253,
          "tax_liabilities": 384000,
          "accrued_expenses": 461858,
          "total": 29507111
        },
        "total_equity_liabilities": 675294786
      }
    },
    "2020": {
      // ... complete 2020 breakdown
    }
  }
}
```

#### Critical Issues
1. **0% Extraction**: No financial data extracted at all
2. **Missing Multi-Year Structure**: Expects 2-year comparative data (2021 + 2020)
3. **Missing Hierarchical Breakdown**: 3-4 levels deep (income_statement → 2021 → revenue → net_sales)
4. **Missing Totals Validation**: Ground truth includes calculated totals at each level

---

### 3. PROPERTY AGENT 🔴 **0.0% Coverage**

#### What's Extracted (CURRENT)
```json
{
  // NOTHING - All property fields empty strings
}
```

#### What Ground Truth Expects
```json
{
  "properties": [
    {
      "designation": "Sonfjället 2",
      "acquisition_year": 2015,
      "municipality": "Stockholm"
    }
  ],
  "construction_year": 2015,
  "building_count": 2,
  "building_type": "Flerbostadshus",
  "tax_value_year": 2017,
  "total_area_sqm": 8009,
  "residential_area_sqm": 7531,
  "commercial_area_sqm": 478,
  "heating_type": "Fjärrvärme",
  "insurance": {
    "provider": "Brandkontoret",
    "type": "Fullvärdesförsäkring",
    "includes_member_supplement": true,
    "includes_board_liability": true
  }
}
```

#### Critical Issues
1. **Complete Extraction Failure**: All 13 fields missing
2. **Property Array**: Expects list of property objects, not flat fields
3. **Nested Insurance Object**: Multi-field structure not extracted
4. **Diagnostic Needed**: Unknown if routing issue, prompt issue, or data location issue

---

### 4. APARTMENTS (operations_agent) 🔴 **0.0% Coverage**

#### What's Extracted (CURRENT)
```json
{
  // NOTHING
}
```

#### What Ground Truth Expects
```json
{
  "total_count": 94,
  "breakdown": {
    "1_rok": 10,
    "2_rok": 24,
    "3_rok": 23,
    "4_rok": 36,
    "5_rok": 1,
    "over_5_rok": 0
  },
  "transfers_during_year": 14,
  "secondhand_rentals_approved": 6,
  "secondhand_rental_reasons": [
    "Utlandstjänstgöring",
    "Studier på annan ort"
  ]
}
```

#### Critical Issues
1. **Missing Apartment Breakdown**: Detailed breakdown by room count (1 rok, 2 rok, etc.)
2. **Missing Operational Data**: Transfers, rental approvals
3. **Missing Reasons List**: Secondhand rental reasons (array of strings)

---

### 5. LOANS (notes_accounting_agent) 🔴 **0.0% Coverage**

#### What's Extracted (CURRENT)
```json
{
  // NOTHING
}
```

#### What Ground Truth Expects
```json
[
  {
    "lender": "SEB",
    "loan_number": "41431520",
    "amount_2021": 30000000,
    "amount_2020": 30000000,
    "interest_rate": 0.0057,
    "maturity_date": "2024-09-28",
    "amortization_free": true,
    "notes": "Villkorsändrat, löper på 3 år"
  },
  {
    "lender": "SEB",
    "amount_2021": 30000000,
    "amount_2020": 30000000,
    "interest_rate": 0.0059,
    "maturity_date": "2023-09-28",
    "amortization_free": true
  },
  {
    "lender": "SEB",
    "amount_2021": 28500000,
    "amount_2020": 28500000,
    "interest_rate": 0.0142,
    "maturity_date": "2022-09-28",
    "amortization_free": false,
    "notes": "Amorteras med 500.000 kr/kvartal (lån med högst ränta)"
  },
  {
    "lender": "SEB",
    "amount_2021": 25980000,
    "amount_2020": 25980000,
    "interest_rate": 0.0236,
    "maturity_date": "2025-09-28",
    "amortization_free": true
  }
]
```

#### Critical Issues
1. **Array of Loan Objects**: Expects 4 detailed loan objects, extracted nothing
2. **Multi-Year Data**: Each loan has amount_2021 and amount_2020
3. **Optional Fields**: Some loans have notes, some don't
4. **Note 5 Context**: This data comes from Note 5 in the PDF

---

### 6. FEES (operations_agent) 🔴 **0.0% Coverage**

#### What's Extracted (CURRENT)
```json
{
  // NOTHING
}
```

#### What Ground Truth Expects
```json
{
  "annual_fee_per_sqm_2021": 582,
  "annual_fee_per_sqm_2020": 582,
  "annual_fee_per_sqm_2019": 582,
  "annual_fee_per_sqm_2018": 582,
  "annual_fee_planned_change": "Oförändrade närmaste året",
  "rent_per_sqm_2021": 2113,
  "rent_per_sqm_2020": 1274,
  "rent_per_sqm_2019": 1256,
  "rent_per_sqm_2018": 1231
}
```

#### Critical Issues
1. **Multi-Year Fee Data**: 4 years of historical annual fees
2. **Multi-Year Rent Data**: 4 years of historical rent per sqm
3. **Planned Changes**: Text description of future fee changes
4. **9 Missing Fields**: All completely missing

---

## 🔬 Root Cause Analysis

### Primary Issue: Schema Architecture Mismatch

The extraction pipeline was designed with a **flat schema** optimized for simple field extraction:

```python
# CURRENT SCHEMA (Flat)
EXPECTED_TYPES = {
    "governance_agent": {
        "board_members": "list",  # Simple list of names
        "nomination_committee": "list"
    },
    "financial_agent": {
        "revenue": "num",  # Top-level number only
        "expenses": "num",
        "assets": "num"
    }
}
```

But ground truth expects a **hierarchical schema** with:
- **Nested objects** (e.g., `insurance.provider`, `samf_membership.name`)
- **Arrays of structured objects** (e.g., `board_members[].role`)
- **Multi-year comparative data** (e.g., `income_statement.2021` vs `income_statement.2020`)
- **Calculated totals at multiple levels** (e.g., `revenue.total`, `assets.total_assets`)

### Secondary Issues

1. **Agent Prompts Request Flat Data**
   - Current: "Extract chairman, board members as list"
   - Needed: "Extract board_members as array of objects with name, role, term_expires_at_next_meeting fields"

2. **Property Agent Complete Failure**
   - Unknown if routing issue, prompt issue, or data location
   - Needs diagnostic extraction with verbose logging

3. **Missing Hierarchical Validation**
   - Current validation compares flat fields
   - Needed: Recursive comparison of nested structures

---

## 📋 Action Items by Priority

### P0 - Critical (Blocks Progress)

1. **Update Pydantic Schemas** (`schema_comprehensive.py`)
   - Replace flat field definitions with hierarchical models
   - Add nested models for: insurance, samf_membership, income_statement, balance_sheet
   - Add BoardMember, Auditor, LoanDetails models

2. **Update Agent Prompts** (`base_brf_extractor.py` or `agent_prompts.py`)
   - governance_agent: Request structured board_members with roles
   - financial_agent: Request hierarchical income_statement/balance_sheet
   - property_agent: Request property array + insurance object
   - operations_agent: Request apartment breakdown object + fees object
   - notes_accounting_agent: Request loans array with structured objects

3. **Fix Property Agent**
   - Run diagnostic extraction with verbose logging
   - Check if routing sends correct pages
   - Verify prompt requests correct fields

### P1 - High (Improves Coverage)

4. **Preserve Hierarchical Data in Pipeline**
   - Review `_extract_agent()` in base_brf_extractor.py
   - Ensure JSON response parsing doesn't flatten nested data
   - Update quality metrics to handle nested structures

5. **Update Validation Logic**
   - Enhance `compare_values()` to handle nested dicts recursively
   - Add special handling for arrays of structured objects
   - Validate totals/calculations in hierarchical data

6. **Iterative Testing**
   - Run validation after each schema update
   - Measure coverage/accuracy improvement
   - Iterate on prompts until >90% coverage achieved

---

## 🎯 Success Criteria

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Overall Coverage | 5.1% | ≥90% | ❌ |
| Overall Accuracy | 0.0% | ≥95% | ❌ |
| Governance Coverage | 25.0% | ≥90% | ❌ |
| Financial Coverage | 0.0% | ≥90% | ❌ |
| Property Coverage | 0.0% | ≥90% | ❌ |
| Structured Extraction | 0% | 100% | ❌ |

---

## 📁 Files Requiring Updates

1. **Schema Files**:
   - `gracian_pipeline/core/schema_comprehensive.py` - Add hierarchical types
   - `gracian_pipeline/models/brf_schema.py` - Update Pydantic models

2. **Prompt Files**:
   - `experiments/docling_advanced/code/base_brf_extractor.py` - Update agent prompts
   - `gracian_pipeline/prompts/agent_prompts.py` - Update prompt templates

3. **Validation Files**:
   - `experiments/docling_advanced/code/validate_against_ground_truth.py` - Already handles nested structures ✅

4. **Test Files**:
   - Create `test_hierarchical_extraction.py` - Unit test for nested data extraction
   - Create `test_schema_alignment.py` - Validate schema matches ground truth structure

---

**Next Step**: Begin P0 tasks - Update Pydantic schemas to match ground truth hierarchical structure.
