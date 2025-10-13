# Path B: Enhanced Extraction Implementation Plan

**Created**: 2025-10-13
**Status**: READY TO EXECUTE (after Path A+C complete per user request)
**Estimated Time**: 1-2 weeks
**Expected Outcome**: 90-95% coverage on applicable fields

---

## 🎯 Goal

Enhance the extraction pipeline to reach **95% coverage** on applicable fields by implementing comprehensive extraction for currently under-extracted sections.

**Current State** (After Path A Metrics Fix):
- Coverage: 124.2% on 91 core fields (over-extraction due to counting issue)
- Realistic Coverage (corrected): Expected 60-75% on ~175 applicable fields
- Gap to 95% target: 20-35 percentage points

**Target State**:
- Coverage: 90-95% on applicable fields
- Accuracy: 90-95% on extracted fields
- Processing time: ≤5 min average per PDF

---

## 📊 Enhancement Areas (Based on ULTRATHINKING Analysis)

### 1. Enhanced Notes Extraction (+10-20 fields)

**Current Issue**: Notes section has 248 possible fields, but most PDFs have only 5-8 notes with limited content extraction.

**Improvements Needed**:
- **Better Note Detection**: Recognize notes by content pattern, not just numbering
- **Comprehensive Content Extraction**: Extract full note text, not just summaries
- **Building Details (Note 8)**: Extract 15+ fields (construction year, type, materials, etc.)
- **Receivables Breakdown (Note 9)**: Extract 10+ fields (trade receivables, prepaid expenses, etc.)
- **Related Parties (Note 15)**: Extract relationships, transactions, balances

**Implementation**:
```python
# File: gracian_pipeline/agents/enhanced_notes_agent.py

class EnhancedNotesExtractor:
    """Extract comprehensive data from all notes sections."""

    def extract_note_8_buildings(self, context: str) -> BuildingDetails:
        """Extract detailed building information from Note 8."""
        # Pattern matching for Swedish BRF building descriptions
        # - Construction year: "Byggnaden uppfördes år 1952"
        # - Building type: "Flerbostadshus"
        # - Materials: "Betongstomme med tegelfasad"
        pass

    def extract_note_9_receivables(self, context: str) -> ReceivablesBreakdown:
        """Extract receivables breakdown from Note 9."""
        # Table extraction for receivables categories
        # - Fordringar hos medlemmar
        # - Förutbetalda kostnader
        # - Upplupna intäkter
        pass
```

**Testing**: Validate on 10 PDFs with diverse note structures.

**Expected Impact**: +10-20 fields per PDF, +6-12 percentage points coverage

---

### 2. Property Details Expansion (+5-10 fields)

**Current Issue**: Property section extracts basic info (address, size) but misses important details.

**Improvements Needed**:
- **Energy Class**: Extract from energy declaration section
- **Postal Code**: Parse from full address
- **Renovation Years**: Extract major renovation dates
- **Heating Type**: Identify district heating vs other
- **Building Permissions**: Extract tillbyggnad (extension) permits

**Implementation**:
```python
# File: gracian_pipeline/agents/enhanced_property_agent.py

class EnhancedPropertyExtractor:
    """Extract comprehensive property details."""

    def extract_energy_class(self, context: str) -> str:
        """Extract energy performance certificate class."""
        # Pattern: "Energiklass: D" or "EPC: D"
        # Also check for "Energideklaration" section
        pass

    def extract_renovation_timeline(self, context: str) -> List[Renovation]:
        """Extract major renovation projects with years."""
        # Patterns:
        # - "Takbyte 2018"
        # - "Fasadrenovering genomförd 2015-2016"
        # - "Stambyten planerade 2024"
        pass
```

**Testing**: Validate energy class extraction on 20 PDFs with known values.

**Expected Impact**: +5-10 fields per PDF, +3-6 percentage points coverage

---

### 3. Multi-Year Overview Extraction (+10-15 fields)

**Current Issue**: Many PDFs contain 3-5 years of comparative data, but extraction doesn't capture this.

**Improvements Needed**:
- **Detect Multi-Year Tables**: Identify comparative financial tables
- **Extract Historical Data**: 2-5 years of revenue, expenses, results
- **Trend Analysis**: Calculate year-over-year changes
- **Handle Variable Year Counts**: Some PDFs have 3 years, others 5

**Implementation**:
```python
# File: gracian_pipeline/agents/multi_year_agent.py

class MultiYearOverviewExtractor:
    """Extract multi-year comparative financial data."""

    def detect_multi_year_table(self, tables: List[Table]) -> Optional[Table]:
        """Find the multi-year overview table."""
        # Look for tables with:
        # - Header row with multiple years (2023, 2022, 2021...)
        # - Rows: Intäkter, Kostnader, Resultat
        # - Typically on pages 2-4
        pass

    def extract_year_data(self, table: Table) -> List[YearData]:
        """Extract data for each year in the comparison."""
        # Parse each column as a year
        # Handle Swedish number formatting (space as thousands separator)
        pass
```

**Testing**: Test on 15 PDFs with known multi-year data.

**Expected Impact**: +10-15 fields per PDF, +6-9 percentage points coverage

---

### 4. Calculated Metrics Implementation (+5-10 fields)

**Current Issue**: Schema defines calculated metrics (debt per sqm, solidarity %, etc.) but they're not computed.

**Improvements Needed**:
- **Debt per SQM**: Total debt / total area
- **Debt-to-Equity Ratio**: Total debt / equity
- **Solidarity Percentage**: Equity / total assets
- **Operating Cost per SQM**: Operating costs / residential area
- **Maintenance Reserve per SQM**: Maintenance reserves / total area

**Implementation**:
```python
# File: gracian_pipeline/calculators/financial_metrics.py

class FinancialMetricsCalculator:
    """Calculate derived financial metrics from extracted data."""

    def calculate_debt_per_sqm(self, extraction: dict) -> Optional[float]:
        """Calculate total debt per square meter."""
        total_debt = extraction.get("financial", {}).get("balance_sheet", {}).get("liabilities_debt")
        total_area = extraction.get("property", {}).get("total_area_sqm")

        if total_debt and total_area:
            return total_debt / total_area
        return None

    def calculate_solidarity_percentage(self, extraction: dict) -> Optional[float]:
        """Calculate solidarity % (equity / assets)."""
        equity = extraction.get("financial", {}).get("balance_sheet", {}).get("equity_total")
        assets = extraction.get("financial", {}).get("balance_sheet", {}).get("assets_total")

        if equity and assets:
            return (equity / assets) * 100
        return None
```

**Testing**: Validate calculations against ground truth for 10 PDFs.

**Expected Impact**: +5-10 fields per PDF, +3-6 percentage points coverage

---

### 5. Operations and Environmental Sections (+10-15 fields)

**Current Issue**: These sections are often present but not extracted due to low priority.

**Improvements Needed**:

**Operations**:
- Maintenance plan details
- Supplier list (property manager, contractors)
- Insurance details (provider, coverage amounts)

**Environmental**:
- Energy consumption (kWh per year)
- Water consumption
- Waste management system
- Environmental certifications (if any)

**Implementation**:
```python
# File: gracian_pipeline/agents/operations_agent.py

class OperationsExtractor:
    """Extract operations and management details."""

    def extract_maintenance_plan(self, context: str) -> MaintenancePlan:
        """Extract planned maintenance activities."""
        # Look for "Underhållsplan" or "Planerade åtgärder"
        # Extract year, activity, estimated cost
        pass

    def extract_suppliers(self, context: str) -> List[Supplier]:
        """Extract key suppliers and service providers."""
        # Look for "Förvaltare", "Fastighetsskötare", "Försäkringsbolag"
        pass

# File: gracian_pipeline/agents/environmental_agent.py

class EnvironmentalExtractor:
    """Extract environmental and energy data."""

    def extract_energy_consumption(self, context: str) -> float:
        """Extract annual energy consumption in kWh."""
        # Pattern: "Energiförbrukning: 1 234 567 kWh"
        # Also check energy declaration section
        pass
```

**Testing**: Test on 10 PDFs with operations/environmental sections.

**Expected Impact**: +10-15 fields per PDF, +6-9 percentage points coverage

---

## 📅 Implementation Timeline (1-2 Weeks)

### Week 1: Core Enhancements

**Days 1-2** (Mon-Tue):
- Implement enhanced notes extraction (agents + tests)
- Validate on 10 PDFs with diverse note structures
- Expected: +10 fields per PDF

**Days 3-4** (Wed-Thu):
- Implement property details expansion (energy class, renovations)
- Implement multi-year overview extraction
- Validate on 15 PDFs
- Expected: +15 fields per PDF

**Day 5** (Fri):
- Implement calculated metrics calculator
- Integration testing with parallel orchestrator
- Validate calculations on 10 PDFs
- Expected: +8 fields per PDF

### Week 2: Refinement & Testing

**Days 6-7** (Mon-Tue):
- Implement operations and environmental extractors
- Integration with existing pipeline
- Expected: +12 fields per PDF

**Days 8-9** (Wed-Thu):
- Comprehensive testing on 42-PDF test set
- Performance optimization
- Bug fixes and edge case handling

**Day 10** (Fri):
- Final validation run
- Documentation update
- Production deployment preparation

---

## 🧪 Testing Strategy

### Unit Tests (Per Enhancement):
- Test pattern matching on 10 sample texts
- Test edge cases (missing data, malformed input)
- Test Swedish language specifics (number formatting, date formats)

### Integration Tests:
- Test each new agent with full orchestrator
- Verify no regression in existing extraction
- Test on 42-PDF comprehensive test set

### Validation Tests:
- Compare against ground truth for 10 PDFs
- Measure coverage improvement vs baseline
- Measure accuracy on newly extracted fields

---

## 💰 Cost-Benefit Analysis

### Development Cost:
- **Time**: 1-2 weeks (80-160 hours)
- **API Testing**: ~$5-10 (testing on 100+ PDFs)

### Expected Benefits:
- **Coverage Improvement**: 60-75% → 90-95% (+15-35 percentage points)
- **Field Count**: +45-65 fields per PDF
- **Production Readiness**: APPROVED status (meets 95/95 targets)

### ROI:
- **High**: Achieves production targets, enables pilot deployment
- **Value**: Comprehensive extraction = more valuable data for users

---

## 🎯 Success Criteria

After Path B implementation:

✅ **Coverage ≥90%** on applicable fields (measured correctly)
✅ **Accuracy ≥90%** on extracted fields
✅ **Processing Time ≤5 min** average per PDF
✅ **Success Rate ≥95%** (handles diverse PDF structures)
✅ **All 5 enhancement areas** implemented and tested

---

## 🔄 Integration with Path A+C

**Sequence** (Per user request):
1. ✅ **Path A** (Complete): Fix validation metrics
2. 🔄 **Path C** (Next): Deploy pilot with current extraction (60-75% coverage)
3. 🔄 **Path B** (After pilot): Implement enhancements based on user feedback

**Rationale**:
- Path C gives real-world validation of current extraction
- User feedback from pilot identifies which fields matter most
- Path B implementation can be prioritized based on actual user needs

---

## 📋 Files to Create/Modify

### New Files:
1. `gracian_pipeline/agents/enhanced_notes_agent.py` (~400 lines)
2. `gracian_pipeline/agents/enhanced_property_agent.py` (~300 lines)
3. `gracian_pipeline/agents/multi_year_agent.py` (~350 lines)
4. `gracian_pipeline/calculators/financial_metrics.py` (~250 lines)
5. `gracian_pipeline/agents/operations_agent.py` (~300 lines)
6. `gracian_pipeline/agents/environmental_agent.py` (~250 lines)

### Modified Files:
7. `gracian_pipeline/core/parallel_orchestrator.py` - Add new agents
8. `gracian_pipeline/prompts/agent_prompts.py` - Add new prompts
9. `gracian_pipeline/models/brf_schema.py` - Ensure all fields supported

### Test Files:
10. `tests/test_enhanced_notes.py`
11. `tests/test_property_expansion.py`
12. `tests/test_multi_year.py`
13. `tests/test_calculated_metrics.py`
14. `tests/test_operations_environmental.py`

**Total**: ~14 files, ~2,400 lines of new code

---

## 🚨 Risks & Mitigation

### Risk 1: Extraction Quality Degradation
**Mitigation**: Comprehensive regression testing on existing 42-PDF test set

### Risk 2: Performance Impact
**Mitigation**: Parallel execution of new agents, caching where possible

### Risk 3: Over-Engineering
**Mitigation**: Start with minimum viable enhancement, iterate based on pilot feedback

### Risk 4: Swedish Language Edge Cases
**Mitigation**: Test on diverse PDFs, handle multiple Swedish number/date formats

---

## 💡 Alternative: Hybrid Approach

Instead of implementing ALL enhancements, prioritize based on pilot feedback:

**High Priority** (if users request):
- Enhanced notes extraction (most variable data)
- Calculated metrics (high user value)

**Medium Priority**:
- Multi-year overview (useful for trend analysis)
- Property details expansion (nice-to-have)

**Low Priority**:
- Operations/Environmental (rarely requested)

This approach reduces implementation time to 3-5 days for high-priority items only.

---

**End of Plan**

**Status**: READY TO EXECUTE after Path A+C complete
**Owner**: To be assigned
**Next Review**: After Path C pilot feedback collected
