# 🎯 PHASE 0 VALIDATION CYCLE - DETAILED IMPLEMENTATION PLAN

**Status**: ⏳ **READY TO EXECUTE**
**Duration**: 4 weeks (20 working days)
**Cost**: ~$2,000 (4 weeks × $500/week engineering time)
**Critical Path**: Must complete BEFORE 27K-PDF deployment
**Risk Mitigation**: Prevents $50K-$200K potential losses from unvalidated enhancements

---

## 📊 EXECUTIVE SUMMARY

### **The Problem We're Solving**
After 43 PDFs, we discovered 5 new patterns and specified 8 agent enhancements, but:
- ❌ Schema not updated (~50 missing fields)
- ❌ Agent prompts not updated (0/8 enhancements implemented)
- ❌ No validation that enhancements work
- ❌ Planning to deploy to 27K PDFs with untested code

### **The Solution: 4-Week Validation Cycle**
```
Week 1-2: Update schema (50 fields) + agents (8 prompts)
Week 3: Re-extract 43 PDFs + validate improvements
Week 4: Fix bugs + final approval gate
```

### **Success Criteria**
- ✅ All 50 new fields extracting correctly
- ✅ All 8 enhancements validated on ground truth (43 PDFs)
- ✅ ≥95% enhancement accuracy confirmed
- ✅ Edge cases validated (PDF 42 dual threshold, PDF 43 AGGRESSIVE, etc.)
- ✅ No critical bugs blocking 27K deployment

---

## 📅 WEEK 1: SCHEMA UPDATES + FIELD MAPPING (Days 1-5)

### **Day 1: Schema Design & Field Specification**

**Morning (4 hours): Review & Consolidate Missing Fields**

**Task 1.1**: Create comprehensive field list from anomaly analysis
```python
# File: config/schema_v2_fields.yaml

new_fields:
  # Category 1: Lokaler Revenue & Dual Threshold (property_agent)
  lokaler_revenue_2023: int  # From income statement
  lokaler_revenue_2022: int
  lokaler_revenue_percentage: float  # lokaler_revenue / total_revenue * 100
  lokaler_efficiency_multiplier: float  # revenue% / area%
  lokaler_dependency_risk_tier: str  # LOW/MEDIUM/MEDIUM-HIGH/HIGH
  residential_fee_impact_if_lokaler_lost: float  # % increase needed

  # Category 2: Fee Response Classification (fees_agent)
  fee_increase_count_2023: int  # Number of separate adjustments
  fee_increase_dates: List[str]  # ["2023-02-01", "2023-08-01"]
  fee_increase_percentages: List[float]  # [3.0, 15.0]
  compound_fee_effect: float  # Calculated compound %
  fee_response_classification: str  # REACTIVE/PROACTIVE/AGGRESSIVE/DISTRESS
  fee_decision_soliditet: float  # Soliditet at decision time
  fee_decision_cash_to_debt: float  # Cash ratio at decision time
  fee_stabilization_probability: float  # Predicted success 0-100%

  # Category 3: Refinancing Risk (loans_agent)
  refinancing_risk_tier: str  # NONE/MEDIUM/HIGH/EXTREME
  maturity_cluster_date: str  # ISO date of earliest major maturity
  maturity_cluster_months: int  # Months from report date to maturity
  maturity_cluster_amount: int  # Amount maturing in cluster (TSEK)
  lender_diversity_score: float  # unique_lenders / total_loans (0-1)
  interest_rate_scenario_plus1pct: int  # Annual cost increase (TSEK)
  interest_rate_scenario_plus2pct: int
  interest_rate_scenario_plus3pct: int
  affordability_impact_plus1pct: float  # % fee increase per apartment

  # Category 4: Depreciation Paradox (key_metrics_agent)
  result_without_depreciation_2023: int  # result + avskrivningar
  result_without_depreciation_2022: int
  depreciation_as_percent_of_revenue_2023: float
  depreciation_paradox_flag: bool
  depreciation_paradox_cash_flow_quality: str  # EXCELLENT/STRONG/NONE

  # Category 5: Cash Crisis Detection (balance_sheet_agent)
  total_liquidity_2023: int  # cash + short_term_investments
  total_liquidity_2022: int
  cash_to_debt_ratio_2023: float
  cash_to_debt_ratio_2022: float
  cash_to_debt_ratio_2021: float
  cash_trend: str  # declining/stable/improving
  cash_crisis_flag: bool
  months_to_zero_cash: int  # null if not declining

  # Category 6: Energy Analysis (key_metrics_agent)
  building_age_at_report: int
  electricity_reduction_percent: float
  total_energy_reduction_percent: float
  energy_reduction_hypothesis: str  # commissioning/retrofit/renovation/none
  energy_commissioning_issue_flag: bool
  energy_best_practice_flag: bool
  energy_measures_implemented: str
  government_energy_support_2023: int

  # Category 7: Tomträtt Analysis (property_agent)
  tomtratt_annual_cost_2023: int
  tomtratt_annual_cost_2022: int
  tomtratt_escalation_percent: float
  tomtratt_percent_of_operating_costs: float
  tomtratt_escalation_risk_tier: str
  tomtratt_20year_projection_stable: int
  tomtratt_20year_projection_25pct_escalation: int
  tomtratt_20year_projection_50pct_escalation: int
  tomtratt_20year_projection_100pct_escalation: int
  savings_vs_tomtratt_baseline: int  # For äganderätt properties
  savings_vs_tomtratt_20year: int
  structural_advantage_percent: float

  # Category 8: Pattern Flags (critical_analysis_agent)
  pattern_b_new_flag: bool
  interest_rate_victim_flag: bool
  aggressive_management_flag: bool
  reactive_management_flag: bool
  proactive_management_flag: bool
  distress_management_flag: bool
  lokaler_dual_threshold_flag: bool

  # Category 9: Quantitative Scores (critical_analysis_agent)
  management_quality_score: float  # 0-100
  stabilization_probability: float  # 0-100%
  operational_health_score: float  # 0-100
  structural_risk_score: float  # 0-100

total_new_fields: 59
```

**Expected Outcome**: Complete field specification with types, descriptions, and categories

---

**Afternoon (4 hours): Update Schema Files**

**Task 1.2**: Update Pydantic schema definitions
```python
# File: gracian_pipeline/core/schema_comprehensive.py

# Add to PropertyAgent model:
class PropertyAgentEnhanced(PropertyAgent):
    # Lokaler revenue tracking
    lokaler_revenue_2023: Optional[int] = None
    lokaler_revenue_2022: Optional[int] = None
    lokaler_revenue_percentage: Optional[float] = None
    lokaler_efficiency_multiplier: Optional[float] = None
    lokaler_dependency_risk_tier: Optional[str] = None
    residential_fee_impact_if_lokaler_lost: Optional[float] = None

    # Tomträtt analysis
    tomtratt_annual_cost_2023: Optional[int] = None
    tomtratt_annual_cost_2022: Optional[int] = None
    tomtratt_escalation_percent: Optional[float] = None
    tomtratt_percent_of_operating_costs: Optional[float] = None
    tomtratt_escalation_risk_tier: Optional[str] = None
    tomtratt_20year_projection_stable: Optional[int] = None
    tomtratt_20year_projection_25pct_escalation: Optional[int] = None
    tomtratt_20year_projection_50pct_escalation: Optional[int] = None
    tomtratt_20year_projection_100pct_escalation: Optional[int] = None
    savings_vs_tomtratt_baseline: Optional[int] = None
    savings_vs_tomtratt_20year: Optional[int] = None
    structural_advantage_percent: Optional[float] = None

# Add to FeesAgent model:
class FeesAgentEnhanced(FeesAgent):
    fee_increase_count_2023: Optional[int] = None
    fee_increase_dates: Optional[List[str]] = None
    fee_increase_percentages: Optional[List[float]] = None
    compound_fee_effect: Optional[float] = None
    fee_response_classification: Optional[str] = None
    fee_decision_soliditet: Optional[float] = None
    fee_decision_cash_to_debt: Optional[float] = None
    fee_stabilization_probability: Optional[float] = None

# [Continue for all agents...]
```

**Task 1.3**: Update JSON schema for validation
```python
# File: config/comprehensive_schema_v2.json

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BRF Comprehensive Extraction v2.0",
  "type": "object",
  "properties": {
    "property_agent": {
      "type": "object",
      "properties": {
        "lokaler_revenue_2023": {"type": ["integer", "null"]},
        "lokaler_revenue_2022": {"type": ["integer", "null"]},
        "lokaler_revenue_percentage": {"type": ["number", "null"]},
        "lokaler_efficiency_multiplier": {"type": ["number", "null"]},
        "lokaler_dependency_risk_tier": {
          "type": ["string", "null"],
          "enum": ["LOW", "MEDIUM", "MEDIUM-HIGH", "HIGH", null]
        },
        # [Continue...]
      }
    },
    # [Continue for all agents...]
  },
  "required_fields": 256  # 197 original + 59 new
}
```

**Expected Outcome**: Schema files updated with all 59 new fields, validation ready

---

### **Day 2: Agent Prompt Updates - Part 1 (Universal + High Priority)**

**Morning (4 hours): Tier 1 Enhancements (loans + fees classifier)**

**Task 2.1**: Update loans_agent prompt
```python
# File: gracian_pipeline/prompts/agent_prompts.py

LOANS_AGENT_ENHANCED = """
You are a loans extraction specialist for Swedish BRF annual reports.

[Keep existing extraction logic...]

NEW: REFINANCING RISK ASSESSMENT

1. Calculate refinancing risk tier:
   kortfristig_debt_ratio = (short_term_debt / total_debt) * 100

   IF kortfristig_debt_ratio < 30:
       refinancing_risk_tier = "NONE"
   ELIF 30 <= kortfristig_debt_ratio < 50:
       refinancing_risk_tier = "MEDIUM"
   ELIF 50 <= kortfristig_debt_ratio < 75:
       refinancing_risk_tier = "HIGH"
   ELSE:  # >= 75
       refinancing_risk_tier = "EXTREME"

2. Extract maturity cluster:
   - Find earliest major loan maturity date (>10% of total debt)
   - Calculate months from report_date to maturity_cluster_date
   - Sum amount maturing in cluster (within 12 months of earliest)

   maturity_cluster_date: "YYYY-MM-DD"
   maturity_cluster_months: int  # from report date
   maturity_cluster_amount: int  # TSEK

3. Calculate lender diversity:
   unique_lenders = count(distinct lender names from loans_detailed)
   total_loans = count(loans_detailed)
   lender_diversity_score = unique_lenders / total_loans

   # Example: 1 lender, 4 loans → 1/4 = 0.25 (100% concentration risk)
   # Example: 3 lenders, 4 loans → 3/4 = 0.75 (good diversification)

4. Project interest rate scenarios:
   current_weighted_avg_rate = sum(balance * rate) / sum(balance)

   scenario_plus1pct = total_debt * (current_rate + 0.01)
   scenario_plus2pct = total_debt * (current_rate + 0.02)
   scenario_plus3pct = total_debt * (current_rate + 0.03)

   interest_rate_scenario_plus1pct: int  # Annual increase TSEK
   interest_rate_scenario_plus2pct: int
   interest_rate_scenario_plus3pct: int

5. Calculate affordability impact:
   affordability_impact_plus1pct = (scenario_plus1pct - current_cost) / number_of_apartments / 12
   # Result: kr/month/apartment increase at +1% rates

OUTPUT EXAMPLE:
{
  "refinancing_risk_tier": "MEDIUM",
  "maturity_cluster_date": "2024-12-09",
  "maturity_cluster_months": 12,
  "maturity_cluster_amount": 14362260,
  "lender_diversity_score": 0.25,
  "interest_rate_scenario_plus1pct": 458329,
  "interest_rate_scenario_plus2pct": 916658,
  "interest_rate_scenario_plus3pct": 1374987,
  "affordability_impact_plus1pct": 2120.60
}
"""
```

**Task 2.2**: Update fees_agent prompt (fee_response_classifier)
```python
FEE_RESPONSE_CLASSIFIER_ENHANCED = """
You are a fee increase pattern analyzer for Swedish BRF annual reports.

[Keep existing extraction logic...]

NEW: FEE RESPONSE CLASSIFICATION

1. Extract all fee increases from report year:
   - Scan förvaltningsberättelse for: "höjdes med X%", "justerad uppåt", "ytterligare höjning"
   - Scan Note 17 "Väsentliga händelser" for planned increases
   - Extract month names: januari, februari, mars, april, maj, juni, juli, augusti, september, oktober, november, december

   fee_increase_count_2023: int  # Number of separate adjustments
   fee_increase_dates: ["2023-02-01", "2023-08-01"]  # YYYY-MM-DD
   fee_increase_percentages: [3.0, 15.0]  # Each increase %

2. Calculate compound effect:
   compound_fee_effect = (1 + r1/100) * (1 + r2/100) * ... - 1
   # Example: [3%, 15%] → (1.03 * 1.15) - 1 = 0.1845 = 18.45%

3. Get balance sheet context at decision time:
   fee_decision_soliditet: float  # Soliditet from balance_sheet_agent
   fee_decision_cash_to_debt: float  # (cash + investments) / total_debt * 100

4. Classify fee response pattern:
   IF fee_increase_count_2023 == 1 AND max(fee_increase_percentages) >= 20 AND fee_decision_soliditet >= 80 AND fee_decision_cash_to_debt >= 3:
       fee_response_classification = "AGGRESSIVE"
       fee_stabilization_probability = 75.0  # 70-80% success rate

   ELIF fee_increase_count_2023 >= 2 OR (fee_increase_count_2023 == 1 AND previous_year_had_increase):
       fee_response_classification = "REACTIVE"
       fee_stabilization_probability = 35.0  # 30-40% success rate

   ELIF fee_increase_count_2023 == 1 AND 8 <= max(fee_increase_percentages) <= 15 AND result_trend == "stable":
       fee_response_classification = "PROACTIVE"
       fee_stabilization_probability = 90.0  # 85-95% success rate

   ELIF max(fee_increase_percentages) >= 25 AND fee_decision_soliditet < 70:
       fee_response_classification = "DISTRESS"
       fee_stabilization_probability = 15.0  # <20% success rate

   ELSE:
       fee_response_classification = "REACTIVE"  # Default
       fee_stabilization_probability = 35.0

OUTPUT EXAMPLE:
{
  "fee_increase_count_2023": 1,
  "fee_increase_dates": ["2024-01-01"],
  "fee_increase_percentages": [25.0],
  "compound_fee_effect": 25.0,
  "fee_response_classification": "AGGRESSIVE",
  "fee_decision_soliditet": 82.0,
  "fee_decision_cash_to_debt": 4.4,
  "fee_stabilization_probability": 75.0
}
"""
```

**Expected Outcome**: Tier 1 enhancements (100% prevalence) implemented and tested

---

**Afternoon (4 hours): Tier 2 Enhancements (property lokaler + fees multiple)**

**Task 2.3**: Update property_agent prompt (dual threshold)
```python
PROPERTY_AGENT_LOKALER_ENHANCED = """
You are a commercial property dependency analyzer for Swedish BRF annual reports.

[Keep existing extraction logic...]

NEW: LOKALER DUAL THRESHOLD ASSESSMENT

1. Extract lokaler revenue:
   - From income statement: "Hyresintäkter lokaler", "Lokalhyror", "Intäkter lokaler"
   - Extract both 2023 and 2022 values

   lokaler_revenue_2023: int  # From resultaträkning
   lokaler_revenue_2022: int

2. Calculate lokaler metrics:
   # Revenue percentage
   total_revenue = nettoomsättning_2023
   lokaler_revenue_percentage = (lokaler_revenue_2023 / total_revenue) * 100

   # Efficiency multiplier
   lokaler_area_percentage = (lokaler_area_sqm / total_area_sqm) * 100
   lokaler_efficiency_multiplier = lokaler_revenue_percentage / lokaler_area_percentage
   # Example: 39.3% revenue / 14.3% area = 2.74x efficiency

3. Apply dual threshold logic:
   area_threshold_met = lokaler_area_percentage >= 15
   revenue_threshold_met = lokaler_revenue_percentage >= 30
   efficiency_threshold_met = lokaler_efficiency_multiplier >= 2.5

   IF area_threshold_met AND revenue_threshold_met:
       lokaler_dependency_risk_tier = "HIGH"
   ELIF (area_threshold_met OR revenue_threshold_met) AND efficiency_threshold_met:
       lokaler_dependency_risk_tier = "MEDIUM-HIGH"
   ELIF area_threshold_met OR revenue_threshold_met:
       lokaler_dependency_risk_tier = "MEDIUM"
   ELSE:
       lokaler_dependency_risk_tier = "LOW"

4. Calculate residential impact if lokaler lost:
   # If all lokaler revenue lost, how much must residential fees increase?
   residential_fee_base = arsavgifter_bostader_2023  # From revenue_breakdown
   residential_fee_impact_if_lokaler_lost = (lokaler_revenue_2023 / residential_fee_base) * 100

   # Example: 1,488k lokaler / 2,290k residential = 64.9% increase needed!

OUTPUT EXAMPLE (PDF 42 - brf_82839):
{
  "lokaler_revenue_2023": 1488000,
  "lokaler_revenue_2022": 1425000,
  "lokaler_revenue_percentage": 39.3,
  "lokaler_efficiency_multiplier": 2.74,
  "lokaler_dependency_risk_tier": "MEDIUM-HIGH",
  "residential_fee_impact_if_lokaler_lost": 64.9
}
"""
```

**Task 2.4**: Update fees_agent prompt (multiple increases)
```python
FEES_AGENT_MULTIPLE_INCREASES = """
You are a fee increase pattern detector for Swedish BRF annual reports.

NEW: MULTIPLE FEE INCREASES DETECTION

1. Scan for multiple increase indicators:
   - Phrases: "höjdes med X% i [månad]", "ytterligare höjning", "andra höjning", "justerad uppåt igen"
   - Month-specific: "i februari", "från och med augusti", etc.
   - Annual meeting: Check årsstämma date (typical adjustment point)
   - Extra meetings: Check if extra stämma held (potential mid-year adjustment)

2. Extract each increase chronologically:
   # Example from PDF 41 (brf_82841):
   fee_increase_dates: ["2023-02-01", "2023-08-01"]
   fee_increase_percentages: [3.0, 15.0]

3. Calculate metrics:
   # Compound effect
   compound_fee_effect = (1.03 * 1.15) - 1 = 0.1845 = 18.45%

   # Vs nominal sum
   nominal_sum = 3.0 + 15.0 = 18.0%
   # Difference: 18.45% vs 18.0% = 0.45pp compounding effect

4. Flag CHRONIC PATTERN if:
   fee_increase_count_2023 >= 2  # Multiple in single year
   OR
   (fee_increase_count_2023 >= 1 AND fee_increase_count_2022 >= 1)  # Sequential years

5. Correlate with financial deterioration:
   - Check result_trend: improving/stable/worsening
   - Check soliditet_trend: increasing/stable/decreasing
   - Check yttre_fond_trend: growing/stable/depleting

   IF chronic_pattern AND result_trend == "worsening" AND soliditet_trend == "decreasing":
       fee_fatigue_risk = True  # Member exodus risk
   ELSE:
       fee_fatigue_risk = False

OUTPUT EXAMPLE (brf_82841):
{
  "fee_increase_count_2023": 2,
  "fee_increase_dates": ["2023-02-01", "2023-08-01"],
  "fee_increase_percentages": [3.0, 15.0],
  "compound_fee_effect": 18.45,
  "chronic_pattern_flag": True,
  "fee_fatigue_risk": True
}
"""
```

**Expected Outcome**: Tier 2 enhancements (18.6% + 25.6% prevalence) implemented

---

### **Day 3: Agent Prompt Updates - Part 2 (Selective + Edge Cases)**

**Morning (4 hours): Tier 3 Enhancements (energy + tomträtt)**

**Task 3.1**: Update energy_agent prompt (bidirectional detection)
```python
ENERGY_AGENT_BIDIRECTIONAL = """
You are an energy efficiency analyzer for Swedish BRF annual reports.

[Keep existing crisis detection logic...]

NEW: EFFICIENCY EXEMPLAR DETECTION

1. Calculate year-over-year changes:
   electricity_reduction_percent = ((elkostnad_2023 - elkostnad_2022) / elkostnad_2022) * 100
   # Negative = reduction, Positive = increase

   total_energy_reduction_percent = ((total_energy_2023 - total_energy_2022) / total_energy_2022) * 100

2. Get building age context:
   building_age_at_report = report_year - construction_year
   # Example: 2023 - 2016 = 7 years old

3. Determine reduction hypothesis:
   IF building_age_at_report < 10 AND electricity_reduction_percent <= -30:
       energy_reduction_hypothesis = "commissioning"
       energy_commissioning_issue_flag = True
       # Young building shouldn't have 30%+ reduction unless commissioning issue fixed

   ELIF 15 <= building_age_at_report <= 30 AND electricity_reduction_percent <= -30:
       energy_reduction_hypothesis = "retrofit"
       energy_commissioning_issue_flag = False
       # Mid-age building: LED, insulation, HVAC upgrade

   ELIF building_age_at_report > 30 AND electricity_reduction_percent <= -30:
       energy_reduction_hypothesis = "renovation"
       energy_commissioning_issue_flag = False
       # Old building: Major renovation with energy focus

   ELSE:
       energy_reduction_hypothesis = "none"
       energy_commissioning_issue_flag = False

4. Flag best practice if significant reduction:
   IF electricity_reduction_percent <= -25 OR total_energy_reduction_percent <= -20:
       energy_best_practice_flag = True
   ELSE:
       energy_best_practice_flag = False

5. Extract improvement measures (scan notes for):
   - LED: "LED-belysning", "LED-armaturer"
   - Automation: "automatik", "styrning", "BMS", "byggnadsautomation"
   - Heat pump: "värmepump", "bergvärme"
   - Insulation: "isolering", "tilläggsisolering"
   - FTX: "FTX-system", "ventilation med värmeåtervinning"

   energy_measures_implemented: "LED retrofit, BMS automation"  # Text summary

6. Extract government support:
   - Search for: "elstöd", "energistöd", "ROT-avdrag energi"
   government_energy_support_2023: int  # Amount received

OUTPUT EXAMPLE (PDF 43 - brf_83301):
{
  "building_age_at_report": 7,
  "electricity_reduction_percent": -36.4,
  "total_energy_reduction_percent": -16.3,
  "energy_reduction_hypothesis": "commissioning",
  "energy_commissioning_issue_flag": True,
  "energy_best_practice_flag": True,
  "energy_measures_implemented": "Energy audit conducted, systems reconfigured",
  "government_energy_support_2023": 74295
}
"""
```

**Task 3.2**: Create new tomtratt_escalation_projector agent
```python
TOMTRATT_ESCALATION_PROJECTOR = """
You are a tomträtt (ground lease) cost analyzer for Swedish BRF annual reports.

1. Identify ownership type:
   - Search notes for: "tomträtt", "tomträttsavgäld", "arrende"
   - Contrast with: "äganderätt", "äger fastigheten", "full äganderätt"

   ownership_type: "tomträtt" OR "äganderätt"  # From property_agent

2. IF ownership_type == "tomträtt":

   a) Extract annual cost:
      - From fastighetskostnader: "Tomträttsavgäld", line item
      tomtratt_annual_cost_2023: int
      tomtratt_annual_cost_2022: int

   b) Calculate escalation:
      tomtratt_escalation_percent = ((cost_2023 - cost_2022) / cost_2022) * 100

   c) Calculate burden:
      tomtratt_percent_of_operating_costs = (tomtratt_cost / total_operating_costs) * 100

   d) Classify escalation risk:
      IF tomtratt_escalation_percent >= 50:
          tomtratt_escalation_risk_tier = "EXTREME"
      ELIF tomtratt_escalation_percent >= 25:
          tomtratt_escalation_risk_tier = "HIGH"
      ELIF 10 <= tomtratt_escalation_percent < 25:
          tomtratt_escalation_risk_tier = "MEDIUM"
      ELIF 0 <= tomtratt_escalation_percent < 10:
          tomtratt_escalation_risk_tier = "LOW"
      ELSE:  # Negative or stable
          tomtratt_escalation_risk_tier = "NONE"

   e) Project 20-year scenarios:
      current_annual = tomtratt_annual_cost_2023

      tomtratt_20year_projection_stable = current_annual * 20

      # 25% escalation year 10
      years_1_10 = current_annual * 10
      years_11_20 = (current_annual * 1.25) * 10
      tomtratt_20year_projection_25pct_escalation = years_1_10 + years_11_20

      # 50% escalation year 10
      years_11_20_50pct = (current_annual * 1.50) * 10
      tomtratt_20year_projection_50pct_escalation = years_1_10 + years_11_20_50pct

      # 100% escalation year 10
      years_11_20_100pct = (current_annual * 2.0) * 10
      tomtratt_20year_projection_100pct_escalation = years_1_10 + years_11_20_100pct

3. IF ownership_type == "äganderätt":

   a) Estimate tomträtt baseline (if it were tomträtt):
      # Size-based estimation
      IF number_of_apartments <= 30:
          estimated_tomtratt_baseline = 250000  # Small BRF
      ELIF number_of_apartments <= 60:
          estimated_tomtratt_baseline = 500000  # Medium BRF
      ELSE:
          estimated_tomtratt_baseline = 1000000  # Large BRF

      savings_vs_tomtratt_baseline = estimated_tomtratt_baseline

   b) Calculate 20-year savings:
      savings_vs_tomtratt_20year = estimated_tomtratt_baseline * 20

   c) Calculate as % of operating costs:
      structural_advantage_percent = (savings_vs_tomtratt_baseline / residential_fee_revenue) * 100

OUTPUT EXAMPLE (PDF 43 - brf_83301, äganderätt):
{
  "ownership_type": "äganderätt",
  "tomtratt_annual_cost_2023": null,
  "tomtratt_escalation_risk_tier": null,
  "savings_vs_tomtratt_baseline": 250000,
  "savings_vs_tomtratt_20year": 5000000,
  "structural_advantage_percent": 17.3
}
"""
```

**Expected Outcome**: Tier 3 enhancements (14% + 16% prevalence) implemented

---

**Afternoon (4 hours): Tier 4 Enhancements (depreciation paradox + cash crisis)**

**Task 3.3**: Update key_metrics_agent prompt (depreciation paradox)
```python
KEY_METRICS_DEPRECIATION_PARADOX = """
You are a financial health analyzer for Swedish BRF annual reports.

[Keep existing metrics calculations...]

NEW: DEPRECIATION PARADOX DETECTION

1. Calculate result without depreciation:
   result_without_depreciation_2023 = result_after_financial_2023 + avskrivningar_2023
   result_without_depreciation_2022 = result_after_financial_2022 + avskrivningar_2022

   # Example: -2,373,349 + 2,859,228 = +485,879

2. Calculate depreciation burden:
   depreciation_as_percent_of_revenue_2023 = (avskrivningar_2023 / revenue_2023) * 100
   # Example: 2,859,228 / 2,253,577 = 126.9% (depreciation exceeds revenue!)

3. Test paradox criteria (BOTH required):
   criterion_1 = result_without_depreciation_2023 >= 500000  # +500k TSEK threshold
   criterion_2 = soliditet_2023 >= 85  # 85% equity ratio threshold

   depreciation_paradox_flag = criterion_1 AND criterion_2

4. Assess cash flow quality if paradox:
   IF depreciation_paradox_flag:
       IF result_without_depreciation_2023 >= 1000000:
           depreciation_paradox_cash_flow_quality = "EXCELLENT"
       ELIF result_without_depreciation_2023 >= 500000:
           depreciation_paradox_cash_flow_quality = "STRONG"
   ELSE:
       depreciation_paradox_cash_flow_quality = "NONE"

OUTPUT EXAMPLE (PDF 42 - brf_82839):
{
  "result_without_depreciation_2023": 1057000,
  "result_without_depreciation_2022": 800000,
  "depreciation_as_percent_of_revenue_2023": 36.2,
  "depreciation_paradox_flag": True,
  "depreciation_paradox_cash_flow_quality": "EXCELLENT"
}

OUTPUT EXAMPLE (PDF 43 - brf_83301, near-miss):
{
  "result_without_depreciation_2023": 486000,
  "result_without_depreciation_2022": 450000,
  "depreciation_as_percent_of_revenue_2023": 126.9,
  "depreciation_paradox_flag": False,  # 486k < 500k OR 82% < 85%
  "depreciation_paradox_cash_flow_quality": "NONE"
}
"""
```

**Task 3.4**: Update balance_sheet_agent prompt (cash crisis)
```python
BALANCE_SHEET_CASH_CRISIS = """
You are a liquidity crisis detector for Swedish BRF annual reports.

[Keep existing balance sheet extraction...]

NEW: CASH CRISIS DETECTION

1. Calculate total liquidity:
   total_liquidity_2023 = cash_2023 + short_term_investments_2023
   total_liquidity_2022 = cash_2022 + short_term_investments_2022
   # Note: Get 2021 if available from flerarsoversikt

2. Calculate cash-to-debt ratios:
   cash_to_debt_ratio_2023 = (total_liquidity_2023 / total_debt_2023) * 100
   cash_to_debt_ratio_2022 = (total_liquidity_2022 / total_debt_2022) * 100
   cash_to_debt_ratio_2021 = (total_liquidity_2021 / total_debt_2021) * 100  # If available

3. Determine cash trend:
   IF cash_to_debt_ratio_2023 < cash_to_debt_ratio_2022:
       IF cash_to_debt_ratio_2022 < cash_to_debt_ratio_2021:  # 2-year decline
           cash_trend = "declining"
       ELSE:
           cash_trend = "declining"  # 1-year decline
   ELIF cash_to_debt_ratio_2023 > cash_to_debt_ratio_2022:
       cash_trend = "improving"
   ELSE:
       cash_trend = "stable"

4. Test crisis criteria (BOTH required):
   criterion_1 = cash_to_debt_ratio_2023 < 2.0  # <2% threshold
   criterion_2 = cash_trend == "declining"

   cash_crisis_flag = criterion_1 AND criterion_2

5. Project months to zero (if declining):
   IF cash_trend == "declining":
       # Calculate burn rate (simple linear projection)
       annual_burn = total_liquidity_2022 - total_liquidity_2023
       months_to_zero_cash = int((total_liquidity_2023 / annual_burn) * 12)

       IF months_to_zero_cash < 0:
           months_to_zero_cash = null  # Already negative trend reversal
   ELSE:
       months_to_zero_cash = null  # Not declining

OUTPUT EXAMPLE (Crisis case):
{
  "total_liquidity_2023": 367000,
  "total_liquidity_2022": 689000,
  "total_liquidity_2021": 1470000,
  "cash_to_debt_ratio_2023": 0.8,
  "cash_to_debt_ratio_2022": 1.5,
  "cash_to_debt_ratio_2021": 3.2,
  "cash_trend": "declining",
  "cash_crisis_flag": True,
  "months_to_zero_cash": 14
}

OUTPUT EXAMPLE (PDF 43 - brf_83301, healthy):
{
  "total_liquidity_2023": 2024432,
  "total_liquidity_2022": 1785512,
  "cash_to_debt_ratio_2023": 4.4,
  "cash_to_debt_ratio_2022": 3.9,
  "cash_trend": "improving",
  "cash_crisis_flag": False,
  "months_to_zero_cash": null
}
"""
```

**Expected Outcome**: Tier 4 enhancements (4.7% + 2.3% prevalence) implemented

---

### **Day 4: Pattern Flags & Scoring Logic**

**Morning (4 hours): Implement pattern classification flags**

**Task 4.1**: Update critical_analysis_agent with pattern flags
```python
CRITICAL_ANALYSIS_PATTERN_FLAGS = """
You are a pattern classification specialist for Swedish BRF annual reports.

[Keep existing critical analysis logic...]

NEW: PATTERN BOOLEAN FLAGS

1. Pattern B-NEW flag:
   # Criteria: Young building (<15 years) + chronic losses (≥3 years) + positive cash flow before depreciation

   building_age = report_year - construction_year
   consecutive_loss_years = count(years with negative result)
   result_before_depreciation = result_after_financial + avskrivningar

   pattern_b_new_flag = (
       building_age < 15
       AND consecutive_loss_years >= 3
       AND result_before_depreciation > 0
   )

2. Interest Rate Victim flag:
   # Criteria: Profit → loss conversion + interest cost explosion + operations stable/improving

   result_2022_positive = result_after_financial_2022 > 0
   result_2023_negative = result_after_financial_2023 < 0
   interest_increase_percent = ((interest_2023 - interest_2022) / interest_2022) * 100
   revenue_stable = revenue_change_percent >= -5  # Revenue not collapsing

   interest_rate_victim_flag = (
       result_2022_positive
       AND result_2023_negative
       AND interest_increase_percent > 50
       AND revenue_stable
   )

3. AGGRESSIVE Management flag:
   # Get from fees_agent
   aggressive_management_flag = (fee_response_classification == "AGGRESSIVE")

4. REACTIVE Management flag:
   reactive_management_flag = (fee_response_classification == "REACTIVE")

5. PROACTIVE Management flag:
   proactive_management_flag = (fee_response_classification == "PROACTIVE")

6. DISTRESS Management flag:
   distress_management_flag = (fee_response_classification == "DISTRESS")

7. Lokaler Dual Threshold flag:
   # Get from property_agent
   lokaler_dual_threshold_flag = (
       lokaler_dependency_risk_tier in ["MEDIUM-HIGH", "HIGH"]
   )

8. Depreciation Paradox flag:
   # Get from key_metrics_agent
   # Already calculated as depreciation_paradox_flag

OUTPUT EXAMPLE (PDF 43 - brf_83301):
{
  "pattern_b_new_flag": True,
  "interest_rate_victim_flag": False,
  "aggressive_management_flag": True,
  "reactive_management_flag": False,
  "proactive_management_flag": False,
  "distress_management_flag": False,
  "lokaler_dual_threshold_flag": False,
  "depreciation_paradox_flag": False
}
"""
```

**Task 4.2**: Implement quantitative scoring algorithms
```python
CRITICAL_ANALYSIS_QUANTITATIVE_SCORES = """
You are a BRF health scoring specialist.

NEW: QUANTITATIVE SCORES (0-100 scale)

1. Management Quality Score (0-100):
   base_score = 50

   # Fee response quality (+/- 30 points)
   IF fee_response_classification == "PROACTIVE":
       base_score += 30
   ELIF fee_response_classification == "AGGRESSIVE":
       base_score += 20
   ELIF fee_response_classification == "REACTIVE":
       base_score += 0
   ELIF fee_response_classification == "DISTRESS":
       base_score -= 30

   # Balance sheet strength (+/- 20 points)
   IF soliditet >= 80:
       base_score += 20
   ELIF soliditet >= 70:
       base_score += 10
   ELIF soliditet < 60:
       base_score -= 20

   management_quality_score = max(0, min(100, base_score))

2. Stabilization Probability (0-100%):
   # Get from fees_agent fee_stabilization_probability
   # Already calculated based on fee_response_classification + balance sheet

   stabilization_probability = fee_stabilization_probability

3. Operational Health Score (0-100):
   base_score = 50

   # Cash flow before depreciation (+/- 30 points)
   IF result_without_depreciation >= 1000000:
       base_score += 30
   ELIF result_without_depreciation >= 500000:
       base_score += 20
   ELIF result_without_depreciation >= 0:
       base_score += 10
   ELIF result_without_depreciation < -500000:
       base_score -= 30

   # Soliditet (+/- 20 points)
   IF soliditet >= 85:
       base_score += 20
   ELIF soliditet >= 75:
       base_score += 10
   ELIF soliditet < 65:
       base_score -= 20

   operational_health_score = max(0, min(100, base_score))

4. Structural Risk Score (0-100, higher = more risk):
   risk_score = 0

   # Refinancing risk (+0 to +40 points)
   IF refinancing_risk_tier == "EXTREME":
       risk_score += 40
   ELIF refinancing_risk_tier == "HIGH":
       risk_score += 25
   ELIF refinancing_risk_tier == "MEDIUM":
       risk_score += 10

   # Lokaler dependency (+0 to +25 points)
   IF lokaler_dependency_risk_tier == "HIGH":
       risk_score += 25
   ELIF lokaler_dependency_risk_tier == "MEDIUM-HIGH":
       risk_score += 15
   ELIF lokaler_dependency_risk_tier == "MEDIUM":
       risk_score += 10

   # Tomträtt escalation (+0 to +20 points)
   IF tomtratt_escalation_risk_tier == "EXTREME":
       risk_score += 20
   ELIF tomtratt_escalation_risk_tier == "HIGH":
       risk_score += 15
   ELIF tomtratt_escalation_risk_tier == "MEDIUM":
       risk_score += 10

   # Cash crisis (+0 to +15 points)
   IF cash_crisis_flag:
       risk_score += 15

   structural_risk_score = min(100, risk_score)

OUTPUT EXAMPLE (PDF 43 - brf_83301):
{
  "management_quality_score": 70.0,  # AGGRESSIVE (20) + soliditet 82% (10) = 80, capped at 70
  "stabilization_probability": 75.0,  # From fees_agent
  "operational_health_score": 60.0,  # Result +486k (10) + soliditet 82% (10) = 70
  "structural_risk_score": 10.0  # MEDIUM refinancing (10) + no other risks
}
"""
```

**Expected Outcome**: Pattern flags and quantitative scores implemented

---

**Afternoon (4 hours): Integration Testing & Unit Tests**

**Task 4.3**: Create unit tests for new field calculations
```python
# File: tests/test_enhancements.py

import pytest
from gracian_pipeline.core.enhanced_agents import *

class TestLokalerDualThreshold:
    def test_pdf42_edge_case(self):
        """PDF 42 (brf_82839): 14.3% area BUT 39.3% revenue should flag"""
        result = calculate_lokaler_risk(
            lokaler_area_percent=14.3,
            lokaler_revenue_percent=39.3,
            efficiency_multiplier=2.74
        )
        assert result["lokaler_dependency_risk_tier"] == "MEDIUM-HIGH"
        assert result["residential_fee_impact_if_lokaler_lost"] == 64.9

    def test_pdf43_no_lokaler(self):
        """PDF 43 (brf_83301): 0% commercial should not flag"""
        result = calculate_lokaler_risk(
            lokaler_area_percent=0,
            lokaler_revenue_percent=0,
            efficiency_multiplier=0
        )
        assert result["lokaler_dependency_risk_tier"] == "LOW"

class TestDepreciationParadox:
    def test_pdf42_paradox(self):
        """PDF 42: +1,057k cash flow + 85% soliditet should flag"""
        result = check_depreciation_paradox(
            result_without_depreciation=1057000,
            soliditet=85
        )
        assert result["depreciation_paradox_flag"] == True
        assert result["depreciation_paradox_cash_flow_quality"] == "EXCELLENT"

    def test_pdf43_near_miss(self):
        """PDF 43: +486k (< 500k) OR 82% (< 85%) should NOT flag"""
        result = check_depreciation_paradox(
            result_without_depreciation=486000,
            soliditet=82
        )
        assert result["depreciation_paradox_flag"] == False
        assert result["depreciation_paradox_cash_flow_quality"] == "NONE"

class TestFeeResponseClassification:
    def test_pdf43_aggressive(self):
        """PDF 43: +25% single increase + strong balance sheet = AGGRESSIVE"""
        result = classify_fee_response(
            fee_increases=[25.0],
            soliditet=82,
            cash_to_debt=4.4
        )
        assert result["fee_response_classification"] == "AGGRESSIVE"
        assert result["fee_stabilization_probability"] == 75.0

    def test_reactive_multiple_increases(self):
        """Multiple increases = REACTIVE"""
        result = classify_fee_response(
            fee_increases=[3.0, 15.0],
            soliditet=65,
            cash_to_debt=2.0
        )
        assert result["fee_response_classification"] == "REACTIVE"
        assert result["compound_fee_effect"] == 18.45

class TestRefinancingRiskTiers:
    def test_medium_tier(self):
        """31.3% kortfristig = MEDIUM tier"""
        result = calculate_refinancing_risk(kortfristig_ratio=31.3)
        assert result["refinancing_risk_tier"] == "MEDIUM"

    def test_high_tier(self):
        """60.6% kortfristig = HIGH tier"""
        result = calculate_refinancing_risk(kortfristig_ratio=60.6)
        assert result["refinancing_risk_tier"] == "HIGH"

    def test_extreme_tier(self):
        """69.5% kortfristig = EXTREME tier (but < 75%)"""
        result = calculate_refinancing_risk(kortfristig_ratio=69.5)
        assert result["refinancing_risk_tier"] == "HIGH"  # Not EXTREME (need ≥75%)

# Run tests:
# pytest tests/test_enhancements.py -v
```

**Task 4.4**: Integration test with sample PDF
```python
# File: tests/test_integration_enhanced.py

def test_full_pipeline_pdf43():
    """Full pipeline test on PDF 43 (brf_83301)"""
    from gracian_pipeline.core.enhanced_orchestrator import extract_enhanced

    result = extract_enhanced("test_pdfs/brf_83301.pdf")

    # Validate new lokaler fields
    assert result["property_agent"]["lokaler_revenue_percentage"] == 0
    assert result["property_agent"]["lokaler_dependency_risk_tier"] == "LOW"

    # Validate fee response classification
    assert result["fees_agent"]["fee_response_classification"] == "AGGRESSIVE"
    assert result["fees_agent"]["fee_increase_percentages"] == [25.0]
    assert result["fees_agent"]["fee_stabilization_probability"] == 75.0

    # Validate refinancing risk
    assert result["loans_agent"]["refinancing_risk_tier"] == "MEDIUM"
    assert result["loans_agent"]["kortfristig_debt_ratio_2023"] == 31.3

    # Validate depreciation paradox (should NOT flag)
    assert result["key_metrics_agent"]["depreciation_paradox_flag"] == False
    assert result["key_metrics_agent"]["result_without_depreciation_2023"] == 486000

    # Validate cash crisis (should NOT flag)
    assert result["balance_sheet_agent"]["cash_crisis_flag"] == False
    assert result["balance_sheet_agent"]["cash_to_debt_ratio_2023"] == 4.4

    # Validate pattern flags
    assert result["critical_analysis_agent"]["pattern_b_new_flag"] == True
    assert result["critical_analysis_agent"]["aggressive_management_flag"] == True
    assert result["critical_analysis_agent"]["depreciation_paradox_flag"] == False

    # Validate scores
    assert 60 <= result["critical_analysis_agent"]["management_quality_score"] <= 80
    assert result["critical_analysis_agent"]["stabilization_probability"] == 75.0

def test_full_pipeline_pdf42():
    """Full pipeline test on PDF 42 (brf_82839) - edge cases"""
    result = extract_enhanced("test_pdfs/brf_82839.pdf")

    # Validate lokaler dual threshold (edge case!)
    assert result["property_agent"]["lokaler_area_percentage"] == 14.3
    assert result["property_agent"]["lokaler_revenue_percentage"] == 39.3
    assert result["property_agent"]["lokaler_efficiency_multiplier"] == 2.74
    assert result["property_agent"]["lokaler_dependency_risk_tier"] == "MEDIUM-HIGH"

    # Validate depreciation paradox (should flag!)
    assert result["key_metrics_agent"]["depreciation_paradox_flag"] == True
    assert result["key_metrics_agent"]["result_without_depreciation_2023"] == 1057000
    assert result["key_metrics_agent"]["depreciation_paradox_cash_flow_quality"] == "EXCELLENT"

    # Validate refinancing HIGH tier
    assert result["loans_agent"]["refinancing_risk_tier"] == "HIGH"
    assert result["loans_agent"]["kortfristig_debt_ratio_2023"] == 60.6
```

**Expected Outcome**: All unit tests passing, integration tests validating edge cases

---

### **Day 5: Documentation & Validation Prep**

**Morning (4 hours): Update documentation**

**Task 5.1**: Update AGENT_PROMPT_UPDATES_PENDING.md
```markdown
# File: AGENT_PROMPT_UPDATES_PENDING.md

# 🎉 AGENT PROMPT UPDATES - IMPLEMENTATION COMPLETE!

**Status**: ✅ **ALL 8 ENHANCEMENTS IMPLEMENTED** (Week 1 Day 1-5)
**Next**: Week 2 Re-extraction + Validation

## ✅ IMPLEMENTED ENHANCEMENTS

### 1. loans_agent ✅ (100% prevalence)
- **Status**: IMPLEMENTED Day 2
- **Fields Added**: 9 (refinancing_risk_tier, maturity_cluster_*, lender_diversity_score, rate scenarios)
- **Test Coverage**: Unit tests passing
- **Validation Pending**: Re-extract 43 PDFs, verify tiers match manual analysis

### 2. fee_response_classifier ✅ (100% prevalence)
- **Status**: IMPLEMENTED Day 2
- **Fields Added**: 8 (count, dates, percentages, compound, classification, probability)
- **Test Coverage**: Unit tests passing (PDF 43 AGGRESSIVE, multiple increases REACTIVE)
- **Validation Pending**: Re-extract 43 PDFs, verify classifications

### 3. property_agent (lokaler dual threshold) ✅ (25% prevalence)
- **Status**: IMPLEMENTED Day 2
- **Fields Added**: 6 (revenue tracking, efficiency multiplier, risk tier, impact)
- **Test Coverage**: PDF 42 edge case validated (14.3% area + 39.3% revenue = MEDIUM-HIGH)
- **Validation Pending**: Re-extract 43 PDFs, confirm edge case capture

### 4. fees_agent (multiple increases) ✅ (18.6% prevalence)
- **Status**: IMPLEMENTED Day 2
- **Fields Added**: Integrated into fee_response_classifier
- **Test Coverage**: Compound effect calculation validated (3% + 15% = 18.45%)
- **Validation Pending**: Re-extract corpus, verify chronic pattern detection

### 5. energy_agent (bidirectional) ✅ (14% efficiency prevalence)
- **Status**: IMPLEMENTED Day 3
- **Fields Added**: 8 (building age, reduction %, hypothesis, commissioning flag, measures, support)
- **Test Coverage**: PDF 43 commissioning hypothesis validated (-36.4% el, 7 years old)
- **Validation Pending**: Re-extract corpus, verify best practice flagging

### 6. tomtratt_escalation_projector ✅ (16% prevalence)
- **Status**: IMPLEMENTED Day 3 (NEW AGENT)
- **Fields Added**: 13 (costs, escalation, risk tier, projections, äganderätt savings)
- **Test Coverage**: PDF 43 äganderätt advantage calculated (250k/year savings)
- **Validation Pending**: Re-extract corpus, verify escalation risk + projections

### 7. depreciation_paradox_detector ✅ (4.7% prevalence)
- **Status**: IMPLEMENTED Day 3
- **Fields Added**: 5 (result w/o depreciation, paradox flag, quality, depreciation %)
- **Test Coverage**: PDF 42 paradox validated (+1,057k + 85%), PDF 43 near-miss correct (486k + 82% → NO)
- **Validation Pending**: Re-extract corpus, verify threshold accuracy

### 8. cash_crisis_agent ✅ (2.3% prevalence)
- **Status**: IMPLEMENTED Day 3
- **Fields Added**: 8 (total liquidity, ratios, trend, crisis flag, months to zero)
- **Test Coverage**: PDF 43 healthy validated (4.4% improving → NO), crisis logic implemented
- **Validation Pending**: Re-extract corpus, verify crisis detection

## 📋 WEEK 2 VALIDATION PLAN

**Objective**: Re-extract 43 PDFs with enhanced schema/agents, validate improvements

**Day 6-7**: Re-extraction (batch processing)
**Day 8-9**: Validation (compare old vs new, verify edge cases)
**Day 10**: Bug fixes (expect 5-10 issues)

**Success Criteria**:
- ✅ All 59 new fields populating correctly
- ✅ Edge cases validated (PDF 42 dual threshold, PDF 43 AGGRESSIVE, PDF 42 paradox)
- ✅ Threshold accuracy (PDF 43 near-miss correctly NOT flagged)
- ✅ ≥95% enhancement accuracy confirmed
```

**Task 5.2**: Create validation checklist
```markdown
# File: VALIDATION_CHECKLIST_WEEK2.md

# Week 2 Validation Checklist

## Pre-Validation Setup
- [ ] All 59 new fields added to schema
- [ ] All 8 agent prompts updated
- [ ] Unit tests passing (100%)
- [ ] Integration tests passing (PDF 42, 43)
- [ ] Test environment configured

## Re-Extraction (Day 6-7)
- [ ] Batch process all 43 PDFs with enhanced pipeline
- [ ] Save old extractions for comparison (197-field JSONs)
- [ ] Save new extractions (256-field JSONs)
- [ ] Verify all 43 PDFs processed successfully

## Field Coverage Validation (Day 8)
- [ ] Lokaler revenue fields: Check 11 PDFs with commercial space
  - [ ] PDF 42: lokaler_revenue_percentage = 39.3% ✓
  - [ ] All 11: efficiency_multiplier calculated ✓
  - [ ] All 11: dependency_risk_tier assigned ✓

- [ ] Fee response classification: Check all 43 PDFs
  - [ ] PDF 43: fee_response_classification = "AGGRESSIVE" ✓
  - [ ] Multiple increase cases: compound_fee_effect calculated ✓
  - [ ] All 43: stabilization_probability assigned ✓

- [ ] Refinancing risk tiers: Check all 43 PDFs
  - [ ] PDF 43: refinancing_risk_tier = "MEDIUM" (31.3%) ✓
  - [ ] PDF 42: refinancing_risk_tier = "HIGH" (60.6%) ✓
  - [ ] PDF 41: refinancing_risk_tier = "HIGH" (69.5%) ✓ (not EXTREME, <75%)

- [ ] Depreciation paradox: Check 2 confirmed + 3 near-miss cases
  - [ ] PDF 42: depreciation_paradox_flag = True (+1,057k + 85%) ✓
  - [ ] PDF 43: depreciation_paradox_flag = False (+486k < 500k OR 82% < 85%) ✓
  - [ ] Verify BOTH criteria required (not OR)

- [ ] Cash crisis: Check 1 confirmed + 5 healthy cases
  - [ ] PDF 43: cash_crisis_flag = False (4.4% improving) ✓
  - [ ] PDF 42: cash_crisis_flag = False (recovery case) ✓
  - [ ] Confirm <2% + declining = crisis trigger

## Edge Case Validation (Day 9)
- [ ] PDF 42 lokaler dual threshold:
  - [ ] Area 14.3% alone would NOT flag (< 15%)
  - [ ] Revenue 39.3% DOES flag (> 30%) ✓
  - [ ] Efficiency 2.74x DOES flag (> 2.5x) ✓
  - [ ] Result: lokaler_dependency_risk_tier = "MEDIUM-HIGH" ✓

- [ ] PDF 43 AGGRESSIVE management:
  - [ ] Single increase 25% ✓
  - [ ] Soliditet 82% ✓
  - [ ] Cash-to-debt 4.4% ✓
  - [ ] Result: fee_response_classification = "AGGRESSIVE" ✓
  - [ ] Predicted: fee_stabilization_probability = 75% ✓

- [ ] PDF 43 depreciation paradox near-miss:
  - [ ] Result w/o depreciation: 486k (4% short of 500k) ✓
  - [ ] Soliditet: 82% (3pp short of 85%) ✓
  - [ ] Result: paradox_flag = False (correctly NOT flagged) ✓

- [ ] PDF 43 energy commissioning hypothesis:
  - [ ] Building age: 7 years ✓
  - [ ] Electricity reduction: -36.4% ✓
  - [ ] Hypothesis: "commissioning" (age <10 + reduction >30%) ✓
  - [ ] Flag: energy_commissioning_issue_flag = True ✓

## Accuracy Validation (Day 9)
- [ ] Compare pattern flags with manual ultrathinking:
  - [ ] Pattern B-NEW: 7/43 PDFs match manual count ✓
  - [ ] AGGRESSIVE management: ~9/43 PDFs match manual count ✓
  - [ ] Depreciation paradox: 2/43 PDFs match manual count ✓
  - [ ] Cash crisis: 1/43 PDFs match manual count ✓

- [ ] Verify prevalence rates match corpus analysis:
  - [ ] loans_agent: 43/43 = 100% ✓
  - [ ] fee_response_classifier: 43/43 = 100% ✓
  - [ ] fees_multiple: 8/43 = 18.6% ✓
  - [ ] property_lokaler: 11/43 = 25.6% ✓

- [ ] Quantitative scores sanity check:
  - [ ] management_quality_score: 0-100 range ✓
  - [ ] stabilization_probability: 0-100 range ✓
  - [ ] operational_health_score: 0-100 range ✓
  - [ ] structural_risk_score: 0-100 range ✓

## Bug Tracking (Day 10)
- [ ] Document all issues discovered (expect 5-10)
- [ ] Prioritize: P0 (blocking), P1 (high), P2 (medium), P3 (low)
- [ ] Fix P0 and P1 issues
- [ ] Re-run affected PDFs after fixes
- [ ] Confirm ≥95% enhancement accuracy

## Final Approval Gate
- [ ] All 59 fields extracting correctly
- [ ] All 8 enhancements validated
- [ ] Edge cases working as expected
- [ ] No P0 or P1 bugs remaining
- [ ] Validation report generated
- [ ] Approval to scale to 27K PDFs ✓
```

**Expected Outcome**: Complete documentation, validation checklist ready for Week 2

---

## 📅 WEEK 2: RE-EXTRACTION + VALIDATION (Days 6-10)

### **Day 6-7: Batch Re-Extraction**

**Task 6.1**: Configure batch processing
```bash
# File: scripts/batch_reextract_43pdfs.sh

#!/bin/bash

# Backup old extractions
mkdir -p results/old_extractions_197fields
cp ground_truth/batch_results/*.json results/old_extractions_197fields/

# Re-extract all 43 PDFs with enhanced schema/agents
for pdf_id in {81732,82839,83301,...}  # All 43 PDF IDs
do
    echo "Re-extracting PDF brf_${pdf_id}..."
    python scripts/extract_enhanced.py \
        --pdf-path "test_pdfs/brf_${pdf_id}.pdf" \
        --output-dir "results/new_extractions_256fields/" \
        --schema-version "v2" \
        --enhanced-agents true

    if [ $? -eq 0 ]; then
        echo "✅ brf_${pdf_id} complete"
    else
        echo "❌ brf_${pdf_id} FAILED"
    fi
done

echo "Re-extraction complete. Comparing old vs new..."
python scripts/compare_extractions.py \
    --old-dir "results/old_extractions_197fields/" \
    --new-dir "results/new_extractions_256fields/" \
    --output-report "results/validation_report.md"
```

**Task 6.2**: Monitor extraction progress
```python
# File: scripts/monitor_reextraction.py

import os
import json
from pathlib import Path

def monitor_progress():
    old_dir = Path("results/old_extractions_197fields")
    new_dir = Path("results/new_extractions_256fields")

    old_files = set(f.stem for f in old_dir.glob("*.json"))
    new_files = set(f.stem for f in new_dir.glob("*.json"))

    completed = len(new_files)
    total = len(old_files)
    pending = old_files - new_files

    print(f"Progress: {completed}/{total} PDFs re-extracted ({completed/total*100:.1f}%)")
    print(f"Pending: {', '.join(sorted(pending))}")

    # Check for new fields in completed extractions
    if new_files:
        sample_new = json.load(open(new_dir / f"{list(new_files)[0]}.json"))
        new_field_count = count_fields(sample_new)
        print(f"New schema: {new_field_count} fields (expected: 256)")

def count_fields(data, prefix=""):
    count = 0
    for key, value in data.items():
        if isinstance(value, dict):
            count += count_fields(value, f"{prefix}{key}.")
        else:
            count += 1
    return count

if __name__ == "__main__":
    monitor_progress()
```

**Expected Outcome**: All 43 PDFs re-extracted with 256-field schema

---

### **Day 8-9: Validation & Comparison**

**Task 8.1**: Compare old vs new extractions
```python
# File: scripts/compare_extractions.py

import json
from pathlib import Path
from typing import Dict, List

class ExtractionComparison:
    def __init__(self, old_dir: str, new_dir: str):
        self.old_dir = Path(old_dir)
        self.new_dir = Path(new_dir)
        self.results = []

    def compare_all(self):
        for old_file in self.old_dir.glob("*.json"):
            brf_id = old_file.stem
            new_file = self.new_dir / f"{brf_id}.json"

            if not new_file.exists():
                print(f"❌ {brf_id}: New extraction missing!")
                continue

            old_data = json.load(open(old_file))
            new_data = json.load(open(new_file))

            comparison = self.compare_single(brf_id, old_data, new_data)
            self.results.append(comparison)

    def compare_single(self, brf_id: str, old: Dict, new: Dict) -> Dict:
        old_fields = self.count_fields(old)
        new_fields = self.count_fields(new)
        added_fields = new_fields - old_fields

        # Validate specific enhancements
        validations = {
            "lokaler_revenue": self.check_lokaler_revenue(new),
            "fee_classification": self.check_fee_classification(new),
            "refinancing_tier": self.check_refinancing_tier(new),
            "depreciation_paradox": self.check_depreciation_paradox(new),
            "cash_crisis": self.check_cash_crisis(new),
            "pattern_flags": self.check_pattern_flags(new)
        }

        return {
            "brf_id": brf_id,
            "old_field_count": old_fields,
            "new_field_count": new_fields,
            "added_fields": added_fields,
            "validations": validations
        }

    def check_lokaler_revenue(self, data: Dict) -> Dict:
        prop = data.get("property_agent", {})

        has_revenue = prop.get("lokaler_revenue_2023") is not None
        has_percentage = prop.get("lokaler_revenue_percentage") is not None
        has_efficiency = prop.get("lokaler_efficiency_multiplier") is not None
        has_tier = prop.get("lokaler_dependency_risk_tier") is not None

        return {
            "revenue_extracted": has_revenue,
            "percentage_calculated": has_percentage,
            "efficiency_calculated": has_efficiency,
            "tier_assigned": has_tier,
            "all_fields_present": all([has_revenue, has_percentage, has_efficiency, has_tier])
        }

    def check_fee_classification(self, data: Dict) -> Dict:
        fees = data.get("fees_agent", {})

        has_count = fees.get("fee_increase_count_2023") is not None
        has_classification = fees.get("fee_response_classification") is not None
        has_probability = fees.get("fee_stabilization_probability") is not None

        classification = fees.get("fee_response_classification")
        valid_classification = classification in ["AGGRESSIVE", "REACTIVE", "PROACTIVE", "DISTRESS"]

        return {
            "count_extracted": has_count,
            "classification_assigned": has_classification,
            "classification_valid": valid_classification,
            "probability_calculated": has_probability,
            "all_fields_present": all([has_count, has_classification, has_probability])
        }

    # [Continue for other enhancements...]

    def generate_report(self, output_path: str):
        total = len(self.results)

        # Field coverage
        avg_old_fields = sum(r["old_field_count"] for r in self.results) / total
        avg_new_fields = sum(r["new_field_count"] for r in self.results) / total
        avg_added = sum(r["added_fields"] for r in self.results) / total

        # Enhancement validation rates
        enhancement_rates = {}
        for enhancement in ["lokaler_revenue", "fee_classification", "refinancing_tier",
                           "depreciation_paradox", "cash_crisis", "pattern_flags"]:
            passing = sum(1 for r in self.results
                         if r["validations"][enhancement].get("all_fields_present", False))
            enhancement_rates[enhancement] = (passing / total) * 100

        # Generate markdown report
        report = f"""# Validation Report: Old vs New Extraction Comparison

## Summary Statistics

**Total PDFs Compared**: {total}
**Field Coverage**:
- Old schema: {avg_old_fields:.0f} fields (197 expected)
- New schema: {avg_new_fields:.0f} fields (256 expected)
- Added: {avg_added:.0f} fields (59 expected)

## Enhancement Validation Rates

| Enhancement | Passing Rate | Status |
|-------------|--------------|--------|
| Lokaler Revenue Tracking | {enhancement_rates['lokaler_revenue']:.1f}% | {"✅" if enhancement_rates['lokaler_revenue'] >= 95 else "❌"} |
| Fee Response Classification | {enhancement_rates['fee_classification']:.1f}% | {"✅" if enhancement_rates['fee_classification'] >= 95 else "❌"} |
| Refinancing Risk Tier | {enhancement_rates['refinancing_tier']:.1f}% | {"✅" if enhancement_rates['refinancing_tier'] >= 95 else "❌"} |
| Depreciation Paradox | {enhancement_rates['depreciation_paradox']:.1f}% | {"✅" if enhancement_rates['depreciation_paradox'] >= 95 else "❌"} |
| Cash Crisis Detection | {enhancement_rates['cash_crisis']:.1f}% | {"✅" if enhancement_rates['cash_crisis'] >= 95 else "❌"} |
| Pattern Flags | {enhancement_rates['pattern_flags']:.1f}% | {"✅" if enhancement_rates['pattern_flags'] >= 95 else "❌"} |

## Edge Case Validation

### PDF 42 (brf_82839) - Lokaler Dual Threshold
"""

        # Find PDF 42 in results
        pdf42 = next(r for r in self.results if "82839" in r["brf_id"])
        # [Add PDF 42 specific validation...]

        # Write report
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"✅ Validation report generated: {output_path}")

# Usage:
# python scripts/compare_extractions.py
```

**Task 8.2**: Validate edge cases manually
```python
# File: scripts/validate_edge_cases.py

def validate_pdf42_lokaler_edge_case():
    """PDF 42: 14.3% area BUT 39.3% revenue should flag MEDIUM-HIGH"""
    data = json.load(open("results/new_extractions_256fields/brf_82839.json"))
    prop = data["property_agent"]

    assert prop["lokaler_area_percentage"] == 14.3, "Area % incorrect"
    assert prop["lokaler_revenue_percentage"] == 39.3, "Revenue % incorrect"
    assert prop["lokaler_efficiency_multiplier"] >= 2.7, "Efficiency multiplier incorrect"
    assert prop["lokaler_dependency_risk_tier"] == "MEDIUM-HIGH", "Risk tier incorrect (dual threshold failed!)"

    print("✅ PDF 42 lokaler dual threshold: PASSED")

def validate_pdf43_aggressive_management():
    """PDF 43: +25% single increase + strong balance sheet = AGGRESSIVE"""
    data = json.load(open("results/new_extractions_256fields/brf_83301.json"))
    fees = data["fees_agent"]

    assert fees["fee_increase_count_2023"] == 1, "Increase count incorrect"
    assert 25.0 in fees["fee_increase_percentages"], "Increase % incorrect"
    assert fees["fee_response_classification"] == "AGGRESSIVE", "Classification incorrect!"
    assert fees["fee_stabilization_probability"] >= 70, "Probability too low"

    print("✅ PDF 43 AGGRESSIVE management: PASSED")

def validate_pdf42_depreciation_paradox():
    """PDF 42: +1,057k cash flow + 85% soliditet should flag paradox"""
    data = json.load(open("results/new_extractions_256fields/brf_82839.json"))
    metrics = data["key_metrics_agent"]

    assert metrics["result_without_depreciation_2023"] >= 1000000, "Cash flow calculation incorrect"
    assert metrics["depreciation_paradox_flag"] == True, "Paradox not flagged!"
    assert metrics["depreciation_paradox_cash_flow_quality"] == "EXCELLENT", "Quality assessment incorrect"

    print("✅ PDF 42 depreciation paradox: PASSED")

def validate_pdf43_paradox_near_miss():
    """PDF 43: +486k (< 500k) OR 82% (< 85%) should NOT flag"""
    data = json.load(open("results/new_extractions_256fields/brf_83301.json"))
    metrics = data["key_metrics_agent"]

    assert metrics["result_without_depreciation_2023"] == 486000, "Cash flow calculation incorrect"
    balance = data["balance_sheet_agent"]
    assert balance["soliditet_2023"] == 82, "Soliditet incorrect"

    assert metrics["depreciation_paradox_flag"] == False, "Paradox incorrectly flagged (near-miss should NOT flag)!"

    print("✅ PDF 43 depreciation paradox near-miss: PASSED")

# Run all edge case validations
validate_pdf42_lokaler_edge_case()
validate_pdf43_aggressive_management()
validate_pdf42_depreciation_paradox()
validate_pdf43_paradox_near_miss()
print("\n✅ All edge case validations PASSED!")
```

**Expected Outcome**: Validation report generated, edge cases confirmed working

---

### **Day 10: Bug Fixes & Final Approval**

**Task 10.1**: Track and fix bugs
```markdown
# File: results/bug_tracker_week2.md

# Week 2 Validation Bug Tracker

## P0 Bugs (Blocking - Must Fix)
1. ❌ FIXED: Lokaler efficiency multiplier returns NaN when area = 0
   - Root cause: Division by zero (revenue% / 0)
   - Fix: Check if area > 0 before calculating, else set efficiency = 0
   - Affected PDFs: 18 (all without lokaler)
   - Status: FIXED, re-extracted affected PDFs

2. ❌ FIXED: Fee stabilization probability incorrect for DISTRESS
   - Root cause: Logic error, DISTRESS getting 75% instead of 15%
   - Fix: Update classification logic, DISTRESS → 15%
   - Affected PDFs: 4
   - Status: FIXED, re-extracted affected PDFs

## P1 Bugs (High - Should Fix)
3. ❌ FIXED: Maturity cluster date format inconsistent
   - Root cause: Some dates in "YYYY-MM-DD", others in "DD/MM/YYYY"
   - Fix: Standardize to ISO format "YYYY-MM-DD" in all cases
   - Affected PDFs: 12
   - Status: FIXED, re-extracted affected PDFs

4. ❌ FIXED: Energy commissioning hypothesis missing for some young buildings
   - Root cause: Building age calculation incorrect (using wrong year field)
   - Fix: Use report_year - construction_year consistently
   - Affected PDFs: 6
   - Status: FIXED, re-extracted affected PDFs

## P2 Bugs (Medium - Nice to Fix)
5. ⏳ DEFERRED: Tomträtt 20-year projections rounding errors
   - Root cause: Float precision issues in large number calculations
   - Impact: Minor (off by <100 kr in projections)
   - Decision: Accept for now, note in documentation
   - Will fix in future iteration if critical

6. ⏳ DEFERRED: Pattern flags occasionally missing when related data null
   - Root cause: Null propagation in boolean logic
   - Impact: Minor (affects <2% of cases)
   - Decision: Accept for now, improve in Phase 1+

## P3 Bugs (Low - Document Only)
7. ✅ DOCUMENTED: Lender diversity score 1.0 for single loan
   - Not a bug: 1 unique lender / 1 total loan = 1.0 (mathematically correct)
   - Clarification: 1.0 doesn't mean "perfect diversity", means "single loan case"
   - Action: Update documentation to explain edge case

Total Bugs Found: 7
P0 Fixed: 2/2 (100%)
P1 Fixed: 2/2 (100%)
P2 Deferred: 2/2
P3 Documented: 1/1

Overall Status: ✅ No blocking bugs, ready for approval
```

**Task 10.2**: Generate final validation report
```markdown
# File: results/FINAL_VALIDATION_REPORT.md

# Final Validation Report - Phase 0 Week 2

**Date**: [Date]
**Status**: ✅ **APPROVED FOR 27K-PDF DEPLOYMENT**

## Executive Summary

Successfully re-extracted all 43 PDFs with enhanced 256-field schema (197 original + 59 new).
All 8 agent enhancements validated and working correctly. Edge cases confirmed. No blocking bugs.

## Field Coverage Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Total Fields | 256 | 256 | ✅ |
| New Fields Added | 59 | 59 | ✅ |
| Field Population Rate | ≥80% | 87.3% | ✅ |
| Null Rate (acceptable) | ≤20% | 12.7% | ✅ |

## Enhancement Validation Results

| Enhancement | Prevalence Target | Actual Prevalence | Accuracy | Status |
|-------------|------------------|-------------------|----------|--------|
| loans_agent | 100% | 100% (43/43) | 100% | ✅ |
| fee_response_classifier | 100% | 100% (43/43) | 97.7% | ✅ |
| property_lokaler | 25.6% | 25.6% (11/43) | 100% | ✅ |
| fees_multiple | 18.6% | 18.6% (8/43) | 100% | ✅ |
| energy_bidirectional | 14% | 14.0% (6/43) | 100% | ✅ |
| tomtratt_escalation | 16.3% | 16.3% (7/43) | 100% | ✅ |
| depreciation_paradox | 4.7% | 4.7% (2/43) | 100% | ✅ |
| cash_crisis | 2.3% | 2.3% (1/43) | 100% | ✅ |

**Overall Enhancement Accuracy**: 99.7% (✅ Exceeds 95% target)

## Edge Case Validation

### ✅ PDF 42 (brf_82839) - Lokaler Dual Threshold
- Area: 14.3% (below 15% threshold)
- Revenue: 39.3% (above 30% threshold) → FLAGGED ✅
- Efficiency: 2.74x (above 2.5x threshold) → FLAGGED ✅
- Risk Tier: MEDIUM-HIGH ✅
- **Conclusion**: Dual threshold successfully catches edge case that area-only would miss!

### ✅ PDF 43 (brf_83301) - AGGRESSIVE Management
- Fee Increase: +25% (single)
- Soliditet: 82%
- Cash-to-Debt: 4.4%
- Classification: AGGRESSIVE ✅
- Probability: 75% ✅
- **Conclusion**: Classification logic working correctly!

### ✅ PDF 42 (brf_82839) - Depreciation Paradox
- Cash Flow (before depreciation): +1,057k TSEK ✅
- Soliditet: 85% ✅
- Paradox Flag: TRUE ✅
- Quality: EXCELLENT ✅
- **Conclusion**: Paradox detection working correctly!

### ✅ PDF 43 (brf_83301) - Depreciation Paradox Near-Miss
- Cash Flow (before depreciation): +486k (4% short of 500k threshold)
- Soliditet: 82% (3pp short of 85% threshold)
- Paradox Flag: FALSE ✅ (correctly NOT flagged)
- **Conclusion**: Threshold validation working, near-miss handled correctly!

## Bug Summary

**Total Bugs Found**: 7
- P0 (Blocking): 2 → Fixed ✅
- P1 (High): 2 → Fixed ✅
- P2 (Medium): 2 → Deferred (minor impact)
- P3 (Low): 1 → Documented

**No blocking bugs remaining.** ✅

## Prevalence Rate Validation

Compared actual extraction prevalence with manual corpus analysis predictions:

| Pattern | Manual Prediction | Actual Extraction | Variance |
|---------|------------------|-------------------|----------|
| Pattern B-NEW | 16.3% (7/43) | 16.3% (7/43) | 0% ✅ |
| AGGRESSIVE Mgmt | 20.9% (9/43) | 20.9% (9/43) | 0% ✅ |
| Depreciation Paradox | 4.7% (2/43) | 4.7% (2/43) | 0% ✅ |
| Cash Crisis | 2.3% (1/43) | 2.3% (1/43) | 0% ✅ |
| Lokaler Dual Threshold | 7.0% (3/43) | 7.0% (3/43) | 0% ✅ |

**Conclusion**: Extraction prevalence matches manual analysis perfectly (0% variance)! ✅

## Recommendations

### ✅ APPROVED FOR PRODUCTION
- All success criteria met
- Edge cases validated
- No blocking bugs
- Enhancement accuracy 99.7% (exceeds 95% target)

### Next Steps (Week 3-4)
1. Proceed with Phase 1-2 implementation (Tier 1-2 enhancements on 27K PDFs)
2. Use validated 256-field schema
3. Use validated 8-enhancement agent prompts
4. Monitor for any new edge cases at scale
5. Continue with implementation roadmap as planned

### Lessons Learned
1. Validation cycle was CRITICAL - found 7 bugs before scaling
2. Edge case testing prevented catastrophic failures at scale
3. Prevalence rate validation confirmed pattern detection accuracy
4. 4-week validation investment (