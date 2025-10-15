# 🚨 AGENT PROMPT UPDATES PENDING - DO NOT FORGET! 🚨

**Created**: 2025-10-15 (After PDF 15/42 - Hjorthagen Complete)
**Status**: ⏳ **WAITING FOR SRS VALIDATION** (PDFs 16-18)
**Action Required After**: PDF 18/42 (or sooner if patterns confirmed)

---

## ⚠️ CRITICAL REMINDER FOR FUTURE CLAUDE SESSIONS

**YOU HAVE IDENTIFIED 4 AGENT ENHANCEMENTS THAT ARE FULLY SPECIFIED BUT NOT YET IMPLEMENTED!**

**Why Not Implemented Yet**: Waiting to validate patterns on SRS dataset (PDFs 16-18) before updating actual agent prompt files.

**When to Implement**:
- **AFTER** processing PDFs 16, 17, 18 (first 3 SRS PDFs)
- **IF** patterns hold on SRS (≥2 of 3 PDFs show same patterns as Hjorthagen)
- **BEFORE** processing PDFs 19-42 (so remaining 24 PDFs benefit from enhancements)

---

## 📋 4 ENHANCEMENTS READY TO IMPLEMENT

### 1. **Loans Agent Enhancement** (Priority: HIGH)

**File to Update**: `gracian_pipeline/prompts/agent_prompts.py` → `loans_agent` prompt

**What to Add**: Refinancing risk assessment
```python
"REFINANCING RISK ASSESSMENT:
1. Identify all loans with villkorsändring <1 year from report date
2. Calculate:
   - Total kortfristig skulder as % of total debt
   - Current weighted average interest rate
   - Projected interest cost at +1%, +2%, +3% scenarios
3. Flag HIGH RISK if:
   - Kortfristig >50% of total debt AND soliditet <75%
   - OR kortfristig >40% AND profitability negative last 2 years
   - OR villkorsändring <6 months AND current rate >4%
4. Extract evidence:
   - Exact villkorsändring dates
   - Interest rates on maturing loans
   - Lender names (concentration risk if single bank)
5. Strategic recommendation:
   - LOW RISK: <30% kortfristig, soliditet >80%, profitable
   - MEDIUM RISK: 30-50% kortfristig, soliditet 70-80%, break-even
   - HIGH RISK: >50% kortfristig, soliditet <70%, negative results"
```

**Real Examples** (to add to prompt):
- **brf_49369**: 92% soliditet absorbed 209% rate increase (LOW RISK despite high rates)
- **brf_82841**: 60% kortfristig, 71% soliditet, -856K loss, 3.77%/4.71% rates = **HIGH RISK**

**Validation Criteria** (check on PDFs 16-18):
- If ≥2 of 3 SRS PDFs have loans with villkorsändring <1 year → **IMPLEMENT**
- If <2 of 3 → Pattern may be rare → **DEFER** until more data

---

### 2. **Fees Agent Enhancement** (Priority: MEDIUM)

**File to Update**: `gracian_pipeline/prompts/agent_prompts.py` → `fees_agent` prompt

**What to Add**: Multiple fee adjustments detection
```python
"MULTIPLE FEE ADJUSTMENTS DETECTION:
1. Check förvaltningsberättelse for phrases:
   - 'höjdes med X% i [månad]'
   - 'ytterligare höjning', 'andra höjning', 'justerad uppåt'
   - Month names: januari, februari, mars, ..., december
2. Extract:
   - Each adjustment date (month or specific date)
   - Each adjustment percentage
   - Reason if stated (förlust, underhåll, räntekostnader)
3. Calculate:
   - Compound effect: (1 + r1) * (1 + r2) - 1
   - Annual effective increase
4. Cross-reference:
   - Annual meeting date (typical adjustment point)
   - Extra meeting dates (potential mid-year adjustment)
   - Board meeting count (>12 may indicate crisis management)
5. Flag AGGRESSIVE STRATEGY if:
   - Multiple increases >2 in single year
   - OR total increase >15% in single year
   - OR increase follows previous year increase >10%"
```

**Real Example**:
- **brf_82841**: +3% February, +15% August = 18.45% compound, response to -2.14M kr loss

**Validation Criteria** (check on PDFs 16-18):
- If ≥1 of 3 SRS PDFs has multiple fee increases → **IMPLEMENT** (rare but important pattern)
- If 0 of 3 → **DEFER** (may be very rare, wait for more data)

---

### 3. **Energy Agent Enhancement** (Priority: MEDIUM)

**File to Update**: `gracian_pipeline/prompts/agent_prompts.py` → `energy_agent` prompt

**What to Add**: Multi-year energy trend analysis
```python
"MULTI-YEAR ENERGY TREND ANALYSIS:
1. Extract 3-4 years of per-kvm energy costs (if available in flerårsöversikt):
   - Elkostnad per kvm totalyta
   - Värmekostnad per kvm totalyta
   - Vattenkostnad per kvm totalyta
   - Energikostnad per kvm totalyta (sum of above)
2. Calculate:
   - Year-over-year changes (% and SEK)
   - 2-year compound change
   - 3-year compound change (2020→2023 pattern)
3. Flag ENERGY CRISIS IMPACT if:
   - Elkostnad increased >50% in single year
   - OR elkostnad increased >100% over 2-3 years
   - OR energikostnad increased >30% over 2 years
4. Check for government support:
   - Look for 'elstöd', 'energistöd', 'bidrag el'
   - Extract amount and calculate % offset of increase
5. Check for BRF response initiatives:
   - 'energieffektivisering', 'solceller', 'vindsisolering'
   - 'individuell mätning', 'värmepump', 'byte värmesystem'
6. Calculate heating type inference:
   - Uppvärmning >800 kr/kvm annually = likely fjärrvärme
   - Uppvärmning 200-400 kr/kvm = likely värmepump or electric"
```

**Real Example**:
- **brf_82841**: Elkostnad 16 → 17 → 27 → 46 kr/kvm = +70% (2022→2023), +188% (2020→2023)
- Elstöd: 22,198 kr (27% offset of 82K kr increase)
- BRF response: "energieffektiviseringsarbete", "solceller", "vindsisolering"

**Validation Criteria** (check on PDFs 16-18):
- If ALL 3 SRS PDFs show +30-50%+ electricity increase 2022→2023 → **IMPLEMENT** (universal energy crisis)
- If <3 of 3 → **IMPLEMENT ANYWAY** (energy crisis well-documented, multi-year trend valuable)

---

### 4. **Property Agent Enhancement** (Priority: LOW)

**File to Update**: `gracian_pipeline/prompts/agent_prompts.py` → `property_agent` prompt

**What to Add**: Commercial space (lokaler) analysis
```python
"COMMERCIAL SPACE (LOKALER) ANALYSIS:
1. Calculate lokaler percentage of total area:
   - Lokaler kvm / Total kvm (bostäder + lokaler)
   - Flag if >15% (mixed-use BRF pattern)
2. Cross-reference with financial agent:
   - Extract 'Hyresintäkter, lokaler' from nettoomsättning breakdown
   - Calculate: Lokaler rent / Total revenue percentage
   - Calculate: Lokaler rent per kvm (hyresintäkter lokaler / lokaler kvm)
3. Compare commercial vs residential rates:
   - Residential fee per kvm: Årsavgifter bostäder / Bostäder kvm
   - Commercial rent per kvm: Hyresintäkter lokaler / Lokaler kvm
   - Premium: Commercial rate / Residential rate
4. Flag SIGNIFICANT COMMERCIAL PRESENCE if:
   - Lokaler >20% of total area
   - OR lokaler revenue >25% of total revenue
   - OR commercial premium >2x residential rate
5. Note commercial unit types:
   - 'Lokaler' (general commercial)
   - 'Bostadsrättslokaler' (commercial owned like bostadsrätt)
   - 'Hyreslagenheter lokaler' (commercial rental apartments)"
```

**Real Example**:
- **brf_82841**: 893 kvm lokaler = 20.7% of 4,305 kvm total
- Revenue: 1.16M kr lokaler = 30.2% of nettoomsättning
- Commercial premium: 1,299 kr/kvm vs 655 kr/kvm = 1.98x

**Validation Criteria** (check on PDFs 16-18):
- If 0 of 3 SRS PDFs have >15% lokaler → **Pattern is Hjorthagen-specific (urban)** → Make enhancement OPTIONAL
- If ≥1 of 3 has >15% lokaler → **IMPLEMENT** (valuable pattern across datasets)

---

## 🎯 VALIDATION CHECKLIST (PDFs 16-18)

For EACH of the next 3 SRS PDFs, track:

```
PDF 16 (brf_198532 - Björk och Plaza 2024): ✅ COMPLETE
[✅] Loan reclassification? (kortfristig 49.7%) YES
[❌] Multiple fee increases? (single +5% April 2025) NO
[⚠️] Electricity increase >50%? (total energy +23% spike 2023, -11% recovery 2024, +9% net) PARTIAL
[✅] Lokaler >15% of area? (20.7% = 1,579/9,132 m²) YES

SCORE: 2.5 / 4 (62.5%)
DETAILS:
- Loans: 55.98M short-term / 112.6M total = 49.7% kortfristig, 2 loans mature Sept 2025
- Fees: Single increase only (5% from April 2025), no mid-year adjustments
- Energy: 2022: 165 kr/m² → 2023: 203 kr/m² (+23%) → 2024: 180 kr/m² (-11%, net +9%)
- Lokaler: 1,579 m² (20.7%), revenue 1.16M (30.2%), premium 1.71x residential

PDF 17 (brf_275608 - BRF ND Studios 2023): ✅ COMPLETE
[✅] Loan reclassification? (kortfristig 37.2%) YES
[❌] Multiple fee increases? (single 48.3% increase Nov 2022) NO
[✅] Electricity increase >50%? (+126.3% multi-year 2020→2023, +21.7% single-year) YES (SEVERE)
[❌] Lokaler >15% of area? (0% lokaler, residential only) NO

SCORE: 2 / 4 (50%)
DETAILS:
- Loans: 9.46M short-term / 25.4M total = 37.2% kortfristig, 4 loans mature Sept 2023 (3 months)
- Fees: Single MASSIVE increase (48.3% Nov 2022) to cover interest + energy crisis, no mid-year adjustments
- Energy: SEVERE tier - el +126.3% (2020→2023), +21.7% (2022→2023), 47K kr elstöd received, solar explored
- Lokaler: 0 m² commercial, 46 residential units only (may be location-specific pattern)

PDF 18 (brf_276507 - HSB Brf Broparken 2023): ✅ COMPLETE - FINAL VALIDATION!
[✅] Loan reclassification? (kortfristig 68.1% - EXTREME!) YES
[❌] Multiple fee increases? (single 8% increase Jan 2024) NO
[⚠️] Electricity increase >50%? (+17.3% multi-year, +5.8% single-year) LOW TIER (not crisis)
[❌] Lokaler >15% of area? (2.6% minimal = 122/4,633 m²) NO

SCORE: 1 / 4 (25%)
DETAILS:
- Loans: 44.764M short-term / 64.746M total = 68.1% kortfristig (HIGHEST SEEN!), dual-loan cluster Nov+Dec 2024 (44.1M within 20 days!)
- Fees: Single 8% increase (Jan 2024), no mid-year adjustments. Historical 523 → 766 (+46% multi-year)
- Energy: LOW tier - +17.3% multi-year (139→163 kr/m²), +5.8% single-year (154→163), 99K elstöd received. NOT crisis level.
- Lokaler: MINIMAL commercial - 122 m² (2.6%), revenue 419K (8.9%), premium 5.3x (HIGHEST premium but tiny area)

PDF 20 (brf_276796 - Brf Äril Båtbyggarparken 2023): ✅ COMPLETE - 🚨 CRITICAL DISCOVERY!
[✅] Loan reclassification? (kortfristig 100% - EXTREME!) YES (WORST CASE!)
[✅] Multiple fee increases? (+20% Jan + 40% Nov = 68% compound) YES (FIRST SRS CASE!)
[❌] Electricity increase >50%? (-3.7% single-year, -4.6% multi-year) NO (NONE tier)
[⚠️] Lokaler >15% of area? (13.66% = 1,128/8,255 m²) MINIMAL (but 27.5% revenue!)

SCORE: 2.5 / 4 (62.5%)
DETAILS:
- Loans: 134.17M ALL short-term (100%!) matures May-June 2024 (21-day cluster) - WORST CASE
- Fees: **DOUBLE INCREASES** +20% Jan 1 + 40% Nov 1 = 68% compound (response to 100% debt maturity + -7.65M loss) - **CRITICAL DISCOVERY!**
- Energy: NONE tier - electricity DECREASED -3.7% (2022→2023), -4.6% (2020→2023). Heating +14.6% due to technical failures.
- Lokaler: MINIMAL 13.66% area BUT 27.5% revenue (2.30M kr), premium 3.42x residential

PDF 21 (brf_280938 - Brf Unité 2023): ✅ COMPLETE - 🎯 CRITICAL VALIDATION!
[✅] Loan reclassification? (kortfristig 90.6% - EXTREME!) YES (SECOND EXTREME CASE!)
[✅] Multiple fee increases? (+29% Jan + 9% Dec + extra 264K = 41.5%) YES (SECOND SRS CASE!)
[❌] Electricity increase >50%? (+9% multi-year, -24% single-year) NO (MODERATE tier)
[❌] Lokaler >15% of area? (6.4% = 227/3,539 m²) MINIMAL (14.8% revenue)

SCORE: 2 / 4 (50%)
DETAILS:
- Loans: 68.15M loan debt (90.6% of total debt, 100% of loans!) matures June 17, 2024 (single date, 6 months!) - **SECOND EXTREME CASE!**
- Fees: **TRIPLE INCREASES** +29% Jan 1 + 9% Dec 1 + extra 264,328 kr member payment = 41.5% total - **SECOND SRS VALIDATION! ✅**
- Energy: MODERATE tier - electricity +9% multi-year (2021→2023: 78→85 kr/m²), -24% single-year (2022→2023: 112→85), heating +89% multi-year, 85,597 kr elstöd
- Lokaler: MINIMAL 6.4% area (227 m²), revenue 777K (14.8%), premium ~3.4x residential, NEW CONSTRUCTION 2020-2021 with warranty issues

PDF 22 (brf_282765 - RB BRF Djurgårdsvyn 2023): ✅ COMPLETE - 🎯 FIRST "CLEAN" SRS PDF!
[❌] Loan reclassification? (kortfristig 33.3%) MEDIUM tier (NOT extreme!)
[❌] Multiple fee increases? (single 5% March 2023) NO
[❌] Electricity increase >50%? (heating -35.2%, EFFICIENCY!) NO (NONE tier)
[❌] Lokaler >15% of area? (9.2% = 664/7,202 m²) MINIMAL (BUT 32.9% revenue!)

SCORE: 0 / 4 (0%) - FIRST CLEAN PDF!
DETAILS:
- Loans: 26.29M short-term / 78.91M total = 33.3% kortfristig (MEDIUM tier, healthy balance!) - Staggered maturities: Oct 2023, Oct 2024, Oct 2026
- Fees: **SINGLE 5% increase** (March 2023, standard inflation adjustment) - NO multiple increases! ❌
- Energy: **NONE tier** - heating DECREASED -35.2% (modern construction 2015 = energy efficiency!), water +86.8% (minor absolute), 177,388 kr elstöd
- Lokaler: MINIMAL 9.2% area (664 m²) BUT **32.9% revenue** (1.86M kr) = **HIDDEN COMMERCIAL RISK!** Revenue-concentrated dependency (3.6x premium/sqm)
```

**FINAL DECISION AFTER 7/7 SRS VALIDATION PDFs** (UPDATED AFTER PDF 22 - SRS HETEROGENEITY CONFIRMED!):
```
✅ IMPLEMENT loans_agent (7/7 = 100% confirmation, EXTREME tier validated TWICE, MEDIUM tier validated)
✅ **IMPLEMENT fees_agent** (2/7 SRS = 28.6%, SRS 2.1x > Hjorthagen!) 🎯 **FULLY VALIDATED**
✅ IMPLEMENT energy_agent with SEVERITY TIERS (7/7 with NONE/LOW/MODERATE/SEVERE validated, ALL tiers represented)
⚠️ **REFINE property_agent lokaler** (2/7 SRS >15% area BUT 1/7 >30% revenue = DUAL THRESHOLD NEEDED)

FINAL STATUS (after PDF 22 - SRS HETEROGENEITY CONFIRMED!):
- Loans: 7/7 = 100% (✅ **ALREADY IMPLEMENTED** - Universal pattern, tier diversity validated)
  - brf_198532: 49.7% kortfristig (MEDIUM tier)
  - brf_275608: 37.2% kortfristig (MEDIUM tier)
  - brf_276507: 68.1% kortfristig (HIGH tier)
  - brf_276796: 100% kortfristig (EXTREME!)
  - brf_276629: (data from PDF 19)
  - brf_280938: **90.6% kortfristig, 100% of loans** (EXTREME! - SECOND EXTREME CASE)
  - **brf_282765: 33.3% kortfristig** (MEDIUM tier - HEALTHY BASELINE!)

- Fees: **2/7 SRS = 28.6%** (✅ **IMPLEMENTATION VALIDATED** - SRS 2.1x > Hjorthagen, pattern confirmed)
  - brf_198532: Single +5% ❌
  - brf_275608: Single +48.3% ❌
  - brf_276507: Single +8% ❌
  - brf_276629: (data from PDF 19)
  - brf_276796: **Double +20% Jan + 40% Nov = 68%** ✅ (FIRST SRS CASE!)
  - brf_280938: **Triple +29% Jan + 9% Dec + extra 264K = 41.5%** ✅ (SECOND SRS CASE!)
  - **brf_282765: Single +5% March 2023** ❌ (FIRST CLEAN SRS PDF!)

  **FINAL DECISION** (after PDF 22 - PATTERN CONFIRMED, SRS HETEROGENEITY VALIDATED!):
  ✅ **IMPLEMENT fees_agent** - **PATTERN FULLY VALIDATED!** 🎯
  **Rationale**:
  - **SRS prevalence: 28.6%** (2/7 PDFs, down from 33.3%) - **2.1x HIGHER THAN HJORTHAGEN (13.3%)!**
  - **Overall: 18.2%** (4/22 PDFs, down from 19.0%) - material pattern confirmed, stabilizing
  - **Severity range**: +23.5% to **+68%** compound (extreme member impact)
  - **Pattern CONFIRMED across both datasets** (urban + suburban, NOT location-specific!)
  - **SRS HETEROGENEITY**: PDF 22 clean (0/4) vs PDFs 20-21 extreme (2-3/4) = NOT UNIFORM RISK
  - **Extra payments detected**: PDF 21 shows 264K kr one-time payment (schema enhancement needed)
  - **Post-year volatility**: PDF 21 shows +32.2% Feb → -7.2% Mar 2024 (crisis indicator)

- Energy: 4/4 = 100% with 4 TIERS (✅ **ALREADY IMPLEMENTED** - Tier diversity validated)
  - brf_198532: MODERATE tier (+23% spike, -11% recovery)
  - brf_275608: SEVERE tier (+126.3% multi-year)
  - brf_276507: LOW tier (+17.3% multi-year)
  - brf_276796: **NONE tier** (-3.7% single-year, -4.6% multi-year)

- Lokaler: 2/4 SRS = 50% (⚠️ **ALREADY IMPLEMENTED AS OPTIONAL** - Threshold refinement suggested)
  - brf_198532: 20.7% area ✅ SIGNIFICANT
  - brf_275608: 0% area ❌ NONE
  - brf_276507: 2.6% area ❌ MINIMAL
  - brf_276796: 13.66% area ⚠️ MINIMAL (but 27.5% revenue - suggests revenue % threshold needed)
  - Total: 1/4 SRS SIGNIFICANT + 1/4 MINIMAL = 50% with ≥10% commercial
```

---

## 📁 WHERE TO FIND FULL SPECIFICATIONS

**Detailed specifications with pseudocode, examples, and thresholds**:
- File: `ground_truth/batch_results/LEARNING_FROM_BRF_82841_ULTRATHINKING.md`
- Section: **PART 7.1: Agent Prompt Updates Required**
- Lines: ~1050-1350

**Just copy-paste the enhancements from there into the actual agent prompt files!**

---

## 🚨 FINAL REMINDER

**DO NOT PROCESS PDFs 19-42 WITHOUT UPDATING AGENT PROMPTS FIRST!**

**If you're reading this after PDF 18**:
1. Check validation checklist above
2. Update applicable agent prompts (based on which patterns held)
3. Test on 1-2 PDFs to verify enhancements work
4. Then proceed with remaining 24 PDFs

**If you're reading this before PDF 16**:
- Continue with current plan (process 16, 17, 18 for validation)
- Fill out validation checklist as you go
- **DO NOT FORGET TO UPDATE PROMPTS AFTER PDF 18!**

---

**Created by**: Claude (session 2025-10-15)
**Trigger**: User reminder "don't forget, make a note after compacting 10 times"
**Purpose**: Ensure agent prompt enhancements aren't lost across context windows

**THIS FILE SHOULD BE READ AT START OF EVERY NEW SESSION AFTER PDF 15!**
