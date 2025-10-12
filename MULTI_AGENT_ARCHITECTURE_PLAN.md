# Multi-Agent Architecture Plan - Gracian Pipeline Redesign

## 🎯 Core Insight
**"Many agents, focused on one subsection each, is the key"**

Current architecture: 13 comprehensive agents → Low accuracy due to cognitive overload
Optimal architecture: 50+ specialized agents → High accuracy through focus

## 📊 Evidence Supporting This Approach

### 1. The Regression Proof (brf_81563)
- **Original governance_agent** (~107 words): 4 board members extracted ✅
- **Enhanced governance_agent** (~300 words + 49 synonyms): "I can't assist" + 0 members ❌
- **Conclusion**: More complex prompt = Lower performance

### 2. Pattern Analysis from Week 3 Results
**✅ High Success Rates (Simple, Focused Tasks)**:
- Auditor extraction: 88.4% (35/43 PDFs)
- Chairman extraction: High on working PDFs
- Organization number: High (simple pattern matching)

**❌ Low Success Rates (Complex, Multi-Field Tasks)**:
- Board members: 81.4% (extracting multiple people + roles)
- Fee structure: Low (multiple interdependent fields)
- Apartment breakdown: Low (complex nested data)

### 3. Cognitive Load Limit
Swedish BRF documents are 20-30 pages with dense Swedish financial terminology.
- **Simple task**: "Find chairman name" → LLM processes 1-2 pages, 1 pattern → Success
- **Complex task**: "Find chairman, vice chair, 5-15 board members, auditor, committee..." → LLM processes 5+ pages, 20+ patterns → Failure

## 🏗️ Multi-Agent Architecture Design

### Current Architecture (13 Agents)
```
1. governance_agent           (10+ fields)
2. financial_agent            (30+ fields)
3. property_agent             (15+ fields)
4. fees_agent                 (8+ fields)
5. loans_agent                (5+ fields × N loans)
6. operations_agent           (10+ fields)
7. events_agent               (5+ fields)
8. policies_agent             (5+ fields)
9. notes_depreciation_agent   (5+ fields)
10. notes_maintenance_agent   (5+ fields)
11. notes_tax_agent           (3+ fields)
12. metadata_agent            (5+ fields)
13. environmental_agent       (5+ fields)
```
**Total**: 13 agents trying to extract ~150 fields → 55.9% average coverage

### Optimal Architecture (50+ Specialized Agents)

#### Governance Domain (1 → 8 agents)
```
Current: governance_agent (10+ fields, 81.4% success)
Optimal:
├─ chairman_agent                    [1 field]  Expected: 95%
├─ vice_chairman_agent               [1 field]  Expected: 90%
├─ board_members_names_agent         [1 list]   Expected: 92%
├─ board_members_roles_agent         [1 list]   Expected: 88%
├─ primary_auditor_agent             [2 fields] Expected: 95% (already high)
├─ deputy_auditor_agent              [2 fields] Expected: 85%
├─ nomination_committee_agent        [1 list]   Expected: 75%
└─ governance_meetings_agent         [3 fields] Expected: 70%
```

#### Financial Domain (1 → 20 agents)
```
Current: financial_agent (30+ fields, variable success)
Optimal:
Income Statement Group:
├─ revenue_agent                     [3 fields] Expected: 90%
├─ operating_expenses_agent          [3 fields] Expected: 88%
├─ financial_items_agent             [3 fields] Expected: 85%
└─ net_income_agent                  [2 fields] Expected: 92%

Balance Sheet Assets Group:
├─ fixed_assets_agent                [3 fields] Expected: 90%
├─ current_assets_agent              [3 fields] Expected: 88%
└─ cash_bank_agent                   [2 fields] Expected: 95%

Balance Sheet Liabilities Group:
├─ long_term_liabilities_agent       [3 fields] Expected: 85%
├─ current_liabilities_agent         [3 fields] Expected: 85%
└─ equity_agent                      [3 fields] Expected: 90%

Cash Flow Group:
├─ operating_activities_agent        [3 fields] Expected: 80%
├─ investing_activities_agent        [2 fields] Expected: 75%
└─ financing_activities_agent        [2 fields] Expected: 75%

Calculated Metrics Group:
├─ per_sqm_metrics_agent             [5 fields] Expected: 85%
├─ financial_ratios_agent            [5 fields] Expected: 80%
└─ multi_year_comparison_agent       [10 fields] Expected: 70%
```

#### Notes Domain (3 → 15 agents, one per note)
```
Current: notes_depreciation_agent, notes_maintenance_agent, notes_tax_agent
Optimal:
├─ note1_accounting_principles_agent [3 fields] Expected: 75%
├─ note2_revenue_breakdown_agent     [5 fields] Expected: 80%
├─ note3_employee_costs_agent        [4 fields] Expected: 70%
├─ note4_depreciation_agent          [5 fields] Expected: 85%
├─ note5_loans_detail_agent          [6 fields × N] Expected: 88%
├─ note6_pledged_assets_agent        [3 fields] Expected: 75%
├─ note7_contingent_liabilities_agent [3 fields] Expected: 70%
├─ note8_building_details_agent      [8 fields] Expected: 90%
├─ note9_receivables_agent           [5 fields] Expected: 85%
├─ note10_prepaid_expenses_agent     [4 fields] Expected: 75%
├─ note11_long_term_liabilities_agent [5 fields] Expected: 82%
├─ note12_accrued_expenses_agent     [5 fields] Expected: 78%
├─ note13_reserves_agent             [4 fields] Expected: 80%
├─ note14_equity_changes_agent       [6 fields] Expected: 85%
└─ note15_other_notes_agent          [variable] Expected: 65%
```

#### Property Domain (1 → 10 agents)
```
Current: property_agent (15+ fields, variable success)
Optimal:
├─ property_designation_agent        [2 fields] Expected: 95%
├─ property_address_agent            [4 fields] Expected: 92%
├─ building_basic_info_agent         [5 fields] Expected: 90%
├─ apartment_distribution_agent      [6 fields] Expected: 85%
├─ apartment_size_ranges_agent       [4 fields] Expected: 80%
├─ commercial_premises_agent         [4 fields] Expected: 75%
├─ parking_spaces_agent              [3 fields] Expected: 80%
├─ common_areas_agent                [5 fields] Expected: 70%
├─ samfallighet_agent                [3 fields] Expected: 65%
└─ property_management_agent         [4 fields] Expected: 75%
```

#### Fees Domain (1 → 5 agents)
```
Current: fees_agent (8+ fields, low success)
Optimal:
├─ monthly_fee_agent                 [2 fields] Expected: 90%
├─ annual_fee_agent                  [2 fields] Expected: 88%
├─ fee_per_sqm_agent                 [2 fields] Expected: 85%
├─ fee_components_agent              [4 fields] Expected: 70%
└─ fee_changes_agent                 [3 fields] Expected: 65%
```

#### Operations Domain (1 → 5 agents)
```
Current: operations_agent (10+ fields, variable success)
Optimal:
├─ energy_consumption_agent          [4 fields] Expected: 75%
├─ water_consumption_agent           [3 fields] Expected: 70%
├─ waste_management_agent            [3 fields] Expected: 65%
├─ maintenance_contracts_agent       [5 fields] Expected: 70%
└─ service_providers_agent           [4 fields] Expected: 60%
```

### Total Agent Count: 63 Specialized Agents

## 🎯 Expected Performance Improvement

### Coverage Projection
**Current (13 agents)**: 55.9% average coverage (Week 3 Day 3 results)
**Optimal (63 agents)**: **75-80% average coverage**

**Rationale**:
1. **Error Isolation**: One agent failure doesn't cascade to entire domain
2. **Focus Bonus**: Simple prompts → Higher individual agent success rate
3. **Graceful Degradation**: Missing 20% of fields across 63 agents better than missing 100% of fields in 1 failed agent

### Success Rate Projection (Board Members Example)
**Current**: 81.4% (35/43 PDFs)
- When governance_agent fails → Lose ALL governance data

**Optimal**: 90%+ (39/43 PDFs)
- chairman_agent fails → Still get board_members_agent results
- board_members_agent fails → Still get auditor_agent results
- Expected: Fix 4-5 previously failing PDFs through better focus

### Regression Prevention
**Current**: Enhanced prompt caused brf_81563 regression (4 → 0 board members)
**Optimal**: If board_members_agent fails → chairman_agent + auditor_agent still work
- brf_81563 would have: 0 board members, BUT ✅ chairman, ✅ auditor, ✅ nomination committee
- Graceful degradation instead of total failure

## 🛠️ Implementation Strategy

### Phase 1: Proof of Concept (Week 1) ⏰ IMMEDIATE

**Goal**: Prove multi-agent approach fixes regressions and improves accuracy

**Target**: Split governance_agent into 3 specialized agents
```
governance_agent (10+ fields)
    ↓
chairman_agent (1 field)
board_members_agent (1 list)
auditor_agent (2 fields)
```

**Test Plan**:
1. Create 3 new agent prompts (simple, focused, ~200 words each)
2. Update `agent_prompts.py` with new agents
3. Update orchestrator to call 3 agents instead of 1
4. Test on brf_81563 (the regression case)
   - Expected: No "I can't assist" error
   - Expected: Extract ≥2/3 fields successfully
5. Test on brf_53107, brf_83301 (failed cases)
   - Expected: Extract ≥1/3 fields (improvement from 0/10)

**Success Criteria**:
- ✅ Fix brf_81563 regression (extract ANY governance data)
- ✅ Improve coverage on 1 of the 2 failed PDFs
- ✅ No regressions on working PDFs (maintain 35/43 success rate)

**Time Estimate**: 8 hours
- 2 hours: Create 3 specialized prompts
- 2 hours: Update orchestrator logic
- 2 hours: Test on 5-PDF sample
- 2 hours: Bug fixes and validation

### Phase 2: Financial Domain (Week 2)

**Goal**: Decompose financial_agent into 10-15 specialized agents

**Rationale**: Financial data has highest field count (30+) and most interdependencies
- Expected biggest improvement in coverage
- Notes 4, 5, 8, 9 are prime candidates for specialization

**Agents to Create**:
1. revenue_agent
2. expenses_agent
3. assets_agent
4. liabilities_agent
5. equity_agent
6. cash_flow_operations_agent
7. note4_depreciation_agent
8. note5_loans_agent
9. note8_building_agent
10. note9_receivables_agent

**Success Criteria**:
- ✅ Financial coverage increases from ~60% → 75%+
- ✅ Note 5 (loans) extraction improves from 70% → 85%+
- ✅ Balance sheet equation validation passes more frequently

**Time Estimate**: 16 hours

### Phase 3: Property & Operations Domains (Week 3)

**Goal**: Decompose property_agent and operations_agent

**Property Decomposition (5 agents)**:
1. property_designation_agent
2. building_info_agent
3. apartment_distribution_agent
4. commercial_premises_agent
5. common_areas_agent

**Operations Decomposition (5 agents)**:
1. energy_agent
2. water_agent
3. maintenance_agent
4. service_providers_agent
5. environmental_agent

**Success Criteria**:
- ✅ Property coverage increases from ~50% → 70%+
- ✅ Operations coverage increases from ~40% → 60%+

**Time Estimate**: 12 hours

### Phase 4: Parallel Execution Optimization (Week 4)

**Goal**: Enable concurrent agent execution for performance

**Current**: Sequential execution (13 agents × 60s = 13 minutes)
**Optimal**: Parallel execution with ThreadPoolExecutor
```python
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {
        executor.submit(chairman_agent, pdf_path): "chairman",
        executor.submit(board_members_agent, pdf_path): "board_members",
        executor.submit(auditor_agent, pdf_path): "auditor",
        ...
    }
    results = {agent: future.result() for future, agent in futures.items()}
```

**Expected Performance**:
- 63 agents, 10 concurrent workers
- Execution time: max(all agent times) ≈ 60-90s (vs 63 × 60s = 63 minutes sequential)
- **70x speedup** through parallelization

**Time Estimate**: 8 hours

### Phase 5: Comprehensive Validation (Week 5)

**Goal**: Validate on full 42-PDF test suite

**Test Plan**:
1. Re-run comprehensive test with 63-agent architecture
2. Compare results to Week 3 Day 3 baseline
3. Generate detailed improvement report

**Success Criteria**:
- ✅ Coverage: 55.9% → 75%+ (target: +19 percentage points)
- ✅ Success rate: 35/43 → 39/43+ (target: +4 PDFs)
- ✅ Zero regressions on previously working PDFs
- ✅ Execution time: <90s per PDF (with parallel execution)

**Time Estimate**: 8 hours

## 📊 Projected Results

### Coverage Improvement by Domain

| Domain | Current (13 agents) | Projected (63 agents) | Improvement |
|--------|---------------------|------------------------|-------------|
| **Governance** | 81.4% (35/43) | 90%+ (39/43) | +8.6% |
| **Financial** | ~60% avg | ~75% avg | +15% |
| **Property** | ~50% avg | ~70% avg | +20% |
| **Fees** | ~30% avg | ~60% avg | +30% |
| **Operations** | ~40% avg | ~60% avg | +20% |
| **Notes** | ~65% avg | ~80% avg | +15% |
| **OVERALL** | **55.9%** | **75%+** | **+19%** |

### Success Rate Improvement (42-PDF Test)

**Current State (Week 3 Day 3)**:
- Successful: 35/43 (81.4%)
- Failed: 8/43 (18.6%)
- Average coverage: 55.9%

**Projected State (63-Agent Architecture)**:
- Successful: 39-40/43 (90%+)
- Failed: 3-4/43 (10%)
- Average coverage: 75%+

**Fixed PDFs** (Expected):
- brf_81563: Fixed regression (4 → 0 → 3+ board members)
- brf_53107: Partial extraction (0 → 2+ governance fields)
- brf_83301: Partial extraction (0 → 2+ governance fields)
- +1-2 other PDFs through improved focus

## 🎓 Key Principles for Agent Design

### 1. Single Responsibility Principle
**Rule**: Each agent extracts ONE semantic unit of data
- ✅ GOOD: chairman_agent extracts only chairman
- ❌ BAD: governance_agent extracts chairman + board + auditor + committee

### 2. Token Budget Management
**Rule**: Keep prompts under 500 tokens (~300 words)
- ✅ GOOD: Focused prompt with 5-10 keywords
- ❌ BAD: Comprehensive prompt with 50+ keywords, 49 synonyms

### 3. Swedish-First Pattern Matching
**Rule**: Use 3-5 most common Swedish terms, not all variants
- ✅ GOOD: "ordförande, styrelseordförande, ordf"
- ❌ BAD: "ordförande, styrelseordförande, ordf, ordf., v. ordf., vice-ordförande, ..."

### 4. Error Isolation
**Rule**: Agent failure must not cascade to sibling agents
- ✅ GOOD: chairman_agent fails → board_members_agent still runs
- ❌ BAD: governance_agent fails → lose ALL governance data

### 5. Evidence-Based Extraction
**Rule**: Each agent must cite source pages
- ✅ GOOD: Return {"chairman": "Name", "evidence_pages": [2, 3]}
- ❌ BAD: Return {"chairman": "Name"} with no provenance

## 🚀 Next Steps

### Immediate Action (This Session)
1. ✅ **Complete ULTRATHINKING analysis** (this document)
2. ⏰ **Create Phase 1 implementation plan** (3-agent proof of concept)
3. ⏰ **Write specialized prompts** for chairman_agent, board_members_agent, auditor_agent
4. ⏰ **Update orchestrator** to support multi-agent governance extraction

### Week 1 Deliverables
- 3 specialized governance agents implemented
- Test results on 5-PDF sample showing improvement
- Regression fix validation (brf_81563)
- Documentation of multi-agent orchestration pattern

### Long-term Roadmap
- Week 2: Financial domain decomposition (10-15 agents)
- Week 3: Property & operations decomposition (10 agents)
- Week 4: Parallel execution optimization
- Week 5: Full 42-PDF validation

## 📝 Success Metrics

### Phase 1 Success Criteria
- ✅ Fix brf_81563 regression (any data extracted vs "I can't assist")
- ✅ Improve 1 of 2 failed PDFs (brf_53107 or brf_83301)
- ✅ Maintain 35/43 baseline success rate (no new regressions)
- ✅ Demonstrate error isolation (one agent fails, others succeed)

### Final Success Criteria (Phase 5)
- ✅ Coverage: 75%+ average (current: 55.9%)
- ✅ Success rate: 90%+ (39/43 PDFs, current: 35/43)
- ✅ Execution time: <90s per PDF with parallel execution
- ✅ Graceful degradation on all PDFs (no total failures)

---

**Created**: 2025-10-11
**Architecture Insight**: User's observation about agent specialization
**Expected Impact**: +19% coverage improvement, +4 PDF success rate improvement
**Implementation Timeline**: 5 weeks to full deployment
