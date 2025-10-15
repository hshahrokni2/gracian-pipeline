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

PDF 17 (_____):
[ ] Loan reclassification? Y/N
[ ] Multiple fee increases? Y/N
[ ] Electricity increase >50%? Y/N
[ ] Lokaler >15% of area? Y/N

PDF 18 (_____):
[ ] Loan reclassification? Y/N
[ ] Multiple fee increases? Y/N
[ ] Electricity increase >50%? Y/N
[ ] Lokaler >15% of area? Y/N
```

**Decision Point After PDF 18**:
```
IF ≥2 of 3 for Loans → UPDATE loans_agent
IF ≥1 of 3 for Fees → UPDATE fees_agent
IF ALL 3 for Energy → UPDATE energy_agent (or if ≥2 show +30%+)
IF ≥1 of 3 for Lokaler → UPDATE property_agent (otherwise mark as optional urban-only pattern)

CURRENT STATUS (after PDF 16):
- Loans: 1/1 = 100% (IMPLEMENT if ≥2/3)
- Fees: 0/1 = 0% (DEFER - rare pattern)
- Energy: 1/1 = 100% partial (IMPLEMENT with severity classification)
- Lokaler: 2/2 = 100% (brf_82841 + brf_198532) → ✅ IMPLEMENT NOW!
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
