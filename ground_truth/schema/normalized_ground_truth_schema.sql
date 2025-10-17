-- ============================================================================
-- NORMALIZED GROUND TRUTH DATABASE SCHEMA
-- Purpose: Proper relational datamodel for all extraction data
-- Architecture: Normalized 3NF schema with proper foreign keys
-- Date: 2025-10-17
-- ============================================================================

-- Drop existing tables (CASCADE to handle dependencies)
DROP TABLE IF EXISTS operational_cost_details CASCADE;
DROP TABLE IF EXISTS operational_costs CASCADE;
DROP TABLE IF EXISTS loan_details CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS fee_history CASCADE;
DROP TABLE IF EXISTS fees CASCADE;
DROP TABLE IF EXISTS commercial_tenants CASCADE;
DROP TABLE IF EXISTS commercial CASCADE;
DROP TABLE IF EXISTS board_members CASCADE;
DROP TABLE IF EXISTS governance CASCADE;
DROP TABLE IF EXISTS property_details CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
DROP TABLE IF EXISTS membership CASCADE;
DROP TABLE IF EXISTS tax_assessment CASCADE;
DROP TABLE IF EXISTS maintenance_plan CASCADE;
DROP TABLE IF EXISTS maintenance_completed CASCADE;
DROP TABLE IF EXISTS maintenance_planned CASCADE;
DROP TABLE IF EXISTS significant_events CASCADE;
DROP TABLE IF EXISTS multi_year_metrics CASCADE;
DROP TABLE IF EXISTS financial_statements CASCADE;
DROP TABLE IF EXISTS income_statements CASCADE;
DROP TABLE IF EXISTS balance_sheets CASCADE;
DROP TABLE IF EXISTS audit CASCADE;
DROP TABLE IF EXISTS energy CASCADE;
DROP TABLE IF EXISTS insurance CASCADE;
DROP TABLE IF EXISTS management_contracts CASCADE;
DROP TABLE IF EXISTS samfallighet CASCADE;
DROP TABLE IF EXISTS reserves_funds CASCADE;
DROP TABLE IF EXISTS ground_truth_extractions CASCADE;
DROP TABLE IF EXISTS ground_truth_classifications CASCADE;
DROP TABLE IF EXISTS ground_truth_pattern_summary CASCADE;

-- ============================================================================
-- CORE TABLE: EXTRACTIONS (Master record for each BRF)
-- ============================================================================
CREATE TABLE ground_truth_extractions (
    extraction_id SERIAL PRIMARY KEY,
    brf_id VARCHAR(50) NOT NULL UNIQUE,
    is_ground_truth BOOLEAN DEFAULT TRUE,
    extraction_date TIMESTAMP DEFAULT NOW(),
    extraction_model VARCHAR(100) DEFAULT 'Claude 4.5',

    -- Document metadata
    pdf_filename VARCHAR(255),
    pdf_pages_total INTEGER,

    -- Basic identification
    organization_name VARCHAR(255),
    organization_number VARCHAR(20),
    report_year INTEGER,
    fiscal_year_start DATE,
    fiscal_year_end DATE,
    report_date DATE,
    accounting_standard VARCHAR(10),

    -- Preserve original JSON for reference
    extraction_json JSONB,
    evidence_pages INTEGER[],
    extraction_confidence NUMERIC(3,2) DEFAULT 1.0
);

CREATE INDEX idx_extractions_brf_id ON ground_truth_extractions(brf_id);
CREATE INDEX idx_extractions_year ON ground_truth_extractions(report_year);
CREATE INDEX idx_extractions_org_number ON ground_truth_extractions(organization_number);

-- ============================================================================
-- PROPERTIES TABLE (Property details and physical characteristics)
-- ============================================================================
CREATE TABLE properties (
    property_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Location
    address VARCHAR(255),
    city VARCHAR(100),
    property_designation VARCHAR(100),

    -- Dates
    acquisition_year INTEGER,
    construction_year INTEGER,
    valuation_year INTEGER,

    -- Building characteristics
    buildings_count INTEGER,
    building_type VARCHAR(100),
    total_area_sqm INTEGER,
    residential_area_sqm INTEGER,
    commercial_area_sqm INTEGER,

    -- Systems
    heating_system VARCHAR(100),
    ownership_type VARCHAR(50),
    insurance_provider VARCHAR(255),
    insurance_type VARCHAR(255),

    -- Management
    property_manager_technical VARCHAR(255),
    property_manager_economic VARCHAR(255),

    -- Samfällighet (shared facility)
    member_in_samfallighet BOOLEAN,
    samfallighet_name VARCHAR(255),
    samfallighet_share_pct NUMERIC(5,2),
    samfallighet_manages TEXT,

    -- Evidence
    evidence_pages INTEGER[]
);

CREATE INDEX idx_properties_extraction ON properties(extraction_id);
CREATE INDEX idx_properties_area ON properties(total_area_sqm);

-- ============================================================================
-- MEMBERSHIP TABLE (Unit and member information)
-- ============================================================================
CREATE TABLE membership (
    membership_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Units
    total_apartments INTEGER,
    total_commercial_units INTEGER,
    commercial_unit_type VARCHAR(100),

    -- Apartment breakdown
    apartments_1_rok INTEGER,
    apartments_2_rok INTEGER,
    apartments_3_rok INTEGER,
    apartments_4_rok INTEGER,
    apartments_5_rok INTEGER,
    apartments_6plus_rok INTEGER,

    -- Member counts
    members_start_of_year INTEGER,
    members_new INTEGER,
    members_departed INTEGER,
    members_end_of_year INTEGER,
    transfers_during_year INTEGER,

    -- Sublets
    sublet_approvals_active INTEGER,
    sublet_details JSONB,

    -- Common spaces
    common_spaces JSONB,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_membership_extraction ON membership(extraction_id);

-- ============================================================================
-- GOVERNANCE TABLE (Board and leadership)
-- ============================================================================
CREATE TABLE governance (
    governance_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Chairman
    chairman VARCHAR(255),
    chairman_period VARCHAR(100),
    previous_chairman VARCHAR(255),
    previous_chairman_period VARCHAR(100),

    -- Board statistics
    board_size INTEGER,
    board_deputies_count INTEGER,
    board_meetings_count INTEGER,
    annual_meeting_date DATE,

    -- Auditor
    auditor_name VARCHAR(255),
    auditor_firm VARCHAR(255),
    auditor_type VARCHAR(100),

    -- Nomination committee
    nomination_committee_size INTEGER,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_governance_extraction ON governance(extraction_id);

-- ============================================================================
-- BOARD_MEMBERS TABLE (Individual board members)
-- ============================================================================
CREATE TABLE board_members (
    board_member_id SERIAL PRIMARY KEY,
    governance_id INTEGER NOT NULL REFERENCES governance(governance_id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    role VARCHAR(100),  -- Ledamot, Suppleant, etc.
    member_type VARCHAR(50),  -- board_member, deputy, nomination_committee
    period VARCHAR(100),
    is_deputy BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_board_members_governance ON board_members(governance_id);

-- ============================================================================
-- FINANCIAL_STATEMENTS TABLE (High-level financial summary)
-- ============================================================================
CREATE TABLE financial_statements (
    financial_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Income Statement Totals
    total_revenue BIGINT,
    total_revenue_previous_year BIGINT,
    total_operating_expenses BIGINT,
    total_operating_expenses_previous_year BIGINT,
    operating_result BIGINT,
    operating_result_previous_year BIGINT,

    -- Financial Items
    financial_income BIGINT,
    financial_expenses BIGINT,
    result_after_financial BIGINT,
    result_after_financial_previous_year BIGINT,

    -- Balance Sheet Totals
    total_assets BIGINT,
    total_assets_previous_year BIGINT,
    total_equity BIGINT,
    total_equity_previous_year BIGINT,
    soliditet_pct NUMERIC(5,2),
    total_liabilities BIGINT,
    long_term_liabilities BIGINT,
    short_term_liabilities BIGINT,

    -- Cash Position
    cash_and_bank BIGINT,
    cash_and_bank_previous_year BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_financial_extraction ON financial_statements(extraction_id);

-- ============================================================================
-- MULTI_YEAR_METRICS TABLE (Historical performance data)
-- ============================================================================
CREATE TABLE multi_year_metrics (
    metric_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    metric_year INTEGER NOT NULL,
    revenue BIGINT,
    result BIGINT,
    soliditet_pct NUMERIC(5,2),
    fee_per_sqm NUMERIC(8,2),
    debt_per_sqm_residential NUMERIC(10,2),
    debt_per_sqm_total NUMERIC(10,2),
    savings_per_sqm NUMERIC(8,2),
    interest_sensitivity_pct NUMERIC(5,2),
    energy_cost_per_sqm NUMERIC(8,2),
    fees_pct_of_revenue NUMERIC(5,2),

    UNIQUE(extraction_id, metric_year)
);

CREATE INDEX idx_multi_year_extraction ON multi_year_metrics(extraction_id);
CREATE INDEX idx_multi_year_year ON multi_year_metrics(metric_year);

-- ============================================================================
-- LOANS TABLE (Summary of all debt)
-- ============================================================================
CREATE TABLE loans (
    loans_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Total debt
    total_debt BIGINT,
    total_debt_previous_year BIGINT,
    short_term_debt BIGINT,
    long_term_debt BIGINT,

    -- Amortization
    amortization_year BIGINT,
    amortization_free BOOLEAN,

    -- Interest
    average_interest_rate_pct NUMERIC(5,2),
    interest_rate_context TEXT,

    -- Collateral
    pledged_collateral BIGINT,
    collateral_type VARCHAR(100),

    evidence_pages INTEGER[]
);

CREATE INDEX idx_loans_extraction ON loans(extraction_id);

-- ============================================================================
-- LOAN_DETAILS TABLE (Individual loans)
-- ============================================================================
CREATE TABLE loan_details (
    loan_detail_id SERIAL PRIMARY KEY,
    loans_id INTEGER NOT NULL REFERENCES loans(loans_id) ON DELETE CASCADE,

    lender VARCHAR(255),
    loan_id_external VARCHAR(100),
    amount BIGINT,
    interest_rate_pct NUMERIC(5,2),
    interest_change_date DATE,
    maturity_classification VARCHAR(50),  -- short_term, long_term
    loan_type VARCHAR(50),  -- fixed, variable
    original_amount BIGINT,
    original_date DATE,
    amortization_amount BIGINT
);

CREATE INDEX idx_loan_details_loans ON loan_details(loans_id);
CREATE INDEX idx_loan_details_lender ON loan_details(lender);

-- ============================================================================
-- FEES TABLE (Fee structure and history)
-- ============================================================================
CREATE TABLE fees (
    fees_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Current year fees
    total_fees_collected BIGINT,
    avg_fee_per_sqm_residential NUMERIC(8,2),
    avg_fee_per_sqm_residential_previous_year NUMERIC(8,2),

    -- Fee increase
    fee_increase_pct NUMERIC(5,2),
    fee_increase_date DATE,
    fee_increase_reason TEXT,

    -- Special fees (TV/Broadband)
    tv_broadband_fee_reduction BOOLEAN,
    tv_broadband_old_fee NUMERIC(8,2),
    tv_broadband_new_fee NUMERIC(8,2),
    tv_broadband_change_date DATE,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_fees_extraction ON fees(extraction_id);

-- ============================================================================
-- FEE_HISTORY TABLE (Historical fee changes)
-- ============================================================================
CREATE TABLE fee_history (
    fee_history_id SERIAL PRIMARY KEY,
    fees_id INTEGER NOT NULL REFERENCES fees(fees_id) ON DELETE CASCADE,

    change_year INTEGER,
    change_date DATE,
    old_fee_per_sqm NUMERIC(8,2),
    new_fee_per_sqm NUMERIC(8,2),
    increase_pct NUMERIC(5,2),
    reason TEXT
);

CREATE INDEX idx_fee_history_fees ON fee_history(fees_id);

-- ============================================================================
-- COMMERCIAL TABLE (Commercial space summary)
-- ============================================================================
CREATE TABLE commercial (
    commercial_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    has_commercial_space BOOLEAN,
    total_commercial_rent_collected BIGINT,
    commercial_rent_per_sqm_avg NUMERIC(8,2),
    commercial_rent_pct_of_revenue NUMERIC(5,2),
    vat_registered BOOLEAN,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_commercial_extraction ON commercial(extraction_id);

-- ============================================================================
-- COMMERCIAL_TENANTS TABLE (Individual commercial leases)
-- ============================================================================
CREATE TABLE commercial_tenants (
    tenant_id SERIAL PRIMARY KEY,
    commercial_id INTEGER NOT NULL REFERENCES commercial(commercial_id) ON DELETE CASCADE,

    tenant_name VARCHAR(255),
    area_sqm NUMERIC(10,2),
    lease_start DATE,
    lease_end DATE,
    annual_rent BIGINT,
    monthly_rent BIGINT,
    lease_type VARCHAR(100)
);

CREATE INDEX idx_commercial_tenants_commercial ON commercial_tenants(commercial_id);
CREATE INDEX idx_commercial_tenants_name ON commercial_tenants(tenant_name);

-- ============================================================================
-- OPERATIONAL_COSTS TABLE (Operating expense summary)
-- ============================================================================
CREATE TABLE operational_costs (
    operational_costs_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Total costs
    total_operating_costs BIGINT,
    total_operating_costs_previous_year BIGINT,
    total_driftskostnader BIGINT,
    total_driftskostnader_previous_year BIGINT,

    -- Change analysis
    operating_costs_change_pct NUMERIC(5,2),
    operating_cost_per_sqm NUMERIC(8,2),

    -- Utility pattern classification
    utility_pattern VARCHAR(100),
    pattern_type VARCHAR(100),

    evidence_pages INTEGER[]
);

CREATE INDEX idx_operational_costs_extraction ON operational_costs(extraction_id);

-- ============================================================================
-- OPERATIONAL_COST_DETAILS TABLE (Line-item costs)
-- ============================================================================
CREATE TABLE operational_cost_details (
    cost_detail_id SERIAL PRIMARY KEY,
    operational_costs_id INTEGER NOT NULL REFERENCES operational_costs(operational_costs_id) ON DELETE CASCADE,

    -- Cost identification
    cost_category VARCHAR(100),  -- utilities, maintenance, property_management, etc.
    cost_item VARCHAR(255),      -- el, värme, vatten, reparationer, etc.
    cost_item_normalized VARCHAR(255),  -- Normalized name for aggregation

    -- Amounts
    amount_current_year BIGINT,
    amount_previous_year BIGINT,
    change_pct NUMERIC(5,2),

    -- Per unit metrics
    cost_per_sqm NUMERIC(8,2),
    cost_per_apartment NUMERIC(8,2),

    -- Additional context
    note_reference VARCHAR(50),
    is_taxebunden BOOLEAN,  -- Tax-bound cost
    is_major_item BOOLEAN,  -- Major cost driver

    evidence_pages INTEGER[]
);

CREATE INDEX idx_cost_details_operational ON operational_cost_details(operational_costs_id);
CREATE INDEX idx_cost_details_category ON operational_cost_details(cost_category);
CREATE INDEX idx_cost_details_item ON operational_cost_details(cost_item_normalized);

-- ============================================================================
-- TAX_ASSESSMENT TABLE (Property tax and assessment values)
-- ============================================================================
CREATE TABLE tax_assessment (
    tax_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Tax status
    property_tax_exemption BOOLEAN,
    property_tax_exemption_years INTEGER,
    property_tax_exemption_based_on VARCHAR(255),

    -- Tax rates
    property_tax_rate_per_apartment NUMERIC(10,2),
    property_tax_rate_max_pct NUMERIC(5,4),
    property_tax_calculation_base TEXT,

    -- Assessment values
    tax_assessment_value_building BIGINT,
    tax_assessment_value_land BIGINT,
    tax_assessment_value_total BIGINT,

    -- Breakdown (stored as JSONB for flexibility)
    tax_assessment_breakdown JSONB,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_tax_extraction ON tax_assessment(extraction_id);

-- ============================================================================
-- ENERGY TABLE (Energy providers and consumption)
-- ============================================================================
CREATE TABLE energy (
    energy_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    -- Providers
    heating_provider VARCHAR(255),
    electricity_provider VARCHAR(255),
    water_provider VARCHAR(255),

    -- Consumption (if available)
    annual_electricity_kwh BIGINT,
    annual_heating_kwh BIGINT,
    annual_water_m3 BIGINT,

    -- Costs
    electricity_cost BIGINT,
    heating_cost BIGINT,
    water_cost BIGINT,

    -- Efficiency metrics
    energy_cost_per_sqm NUMERIC(8,2),
    electricity_cost_per_kwh NUMERIC(6,4),
    heating_cost_per_kwh NUMERIC(6,4),

    evidence_pages INTEGER[]
);

CREATE INDEX idx_energy_extraction ON energy(extraction_id);

-- ============================================================================
-- INSURANCE TABLE (Insurance coverage)
-- ============================================================================
CREATE TABLE insurance (
    insurance_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    insurance_provider VARCHAR(255),
    insurance_type VARCHAR(255),
    annual_premium BIGINT,
    coverage_amount BIGINT,
    deductible BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_insurance_extraction ON insurance(extraction_id);

-- ============================================================================
-- MAINTENANCE_PLAN TABLE (Long-term maintenance planning)
-- ============================================================================
CREATE TABLE maintenance_plan (
    maintenance_plan_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    plan_exists BOOLEAN,
    plan_period VARCHAR(100),
    plan_status VARCHAR(100),
    plan_update_year INTEGER,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_maintenance_plan_extraction ON maintenance_plan(extraction_id);

-- ============================================================================
-- MAINTENANCE_COMPLETED TABLE (Completed maintenance items)
-- ============================================================================
CREATE TABLE maintenance_completed (
    completed_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    item_description TEXT,
    completion_year INTEGER,
    cost BIGINT,
    category VARCHAR(100),  -- planned, emergency, preventive

    evidence_pages INTEGER[]
);

CREATE INDEX idx_maintenance_completed_extraction ON maintenance_completed(extraction_id);
CREATE INDEX idx_maintenance_completed_year ON maintenance_completed(completion_year);

-- ============================================================================
-- MAINTENANCE_PLANNED TABLE (Planned future maintenance)
-- ============================================================================
CREATE TABLE maintenance_planned (
    planned_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    item_description TEXT,
    planned_year VARCHAR(50),  -- Can be "2025" or "2025-2026"
    estimated_cost BIGINT,
    priority VARCHAR(50),  -- urgent, normal, deferred
    category VARCHAR(100),

    evidence_pages INTEGER[]
);

CREATE INDEX idx_maintenance_planned_extraction ON maintenance_planned(extraction_id);
CREATE INDEX idx_maintenance_planned_year ON maintenance_planned(planned_year);

-- ============================================================================
-- SIGNIFICANT_EVENTS TABLE (Material events during year)
-- ============================================================================
CREATE TABLE significant_events (
    event_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    event_type VARCHAR(100),  -- during_year, post_balance
    event_date DATE,
    event_title VARCHAR(500),
    event_description TEXT,
    financial_impact BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_events_extraction ON significant_events(extraction_id);
CREATE INDEX idx_events_type ON significant_events(event_type);

-- ============================================================================
-- AUDIT TABLE (Audit information)
-- ============================================================================
CREATE TABLE audit (
    audit_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    auditor_name VARCHAR(255),
    auditor_firm VARCHAR(255),
    auditor_type VARCHAR(100),
    audit_date DATE,
    audit_opinion VARCHAR(50),  -- unqualified, qualified, adverse, disclaimer
    audit_notes TEXT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_audit_extraction ON audit(extraction_id);

-- ============================================================================
-- MANAGEMENT_CONTRACTS TABLE (Service contracts)
-- ============================================================================
CREATE TABLE management_contracts (
    contract_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    contract_type VARCHAR(100),  -- property_management, technical, economic
    provider_name VARCHAR(255),
    contract_start DATE,
    contract_end DATE,
    annual_cost BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_management_contracts_extraction ON management_contracts(extraction_id);

-- ============================================================================
-- SAMFALLIGHET TABLE (Shared facility associations)
-- ============================================================================
CREATE TABLE samfallighet (
    samfallighet_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    is_member BOOLEAN,
    samfallighet_name VARCHAR(255),
    share_pct NUMERIC(5,2),
    manages_description TEXT,
    annual_fee BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_samfallighet_extraction ON samfallighet(extraction_id);

-- ============================================================================
-- RESERVES_FUNDS TABLE (Reserve funds and restricted equity)
-- ============================================================================
CREATE TABLE reserves_funds (
    fund_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,

    fund_type VARCHAR(100),  -- maintenance_fund, renovation_fund, etc.
    fund_balance BIGINT,
    fund_balance_previous_year BIGINT,
    change_during_year BIGINT,

    evidence_pages INTEGER[]
);

CREATE INDEX idx_reserves_extraction ON reserves_funds(extraction_id);

-- ============================================================================
-- CLASSIFICATIONS TABLE (Existing pattern classifications)
-- ============================================================================
CREATE TABLE ground_truth_classifications (
    classification_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,
    brf_id VARCHAR(50) NOT NULL,
    classification_date TIMESTAMP DEFAULT NOW(),

    -- Pattern 1: Refinancing Risk
    refinancing_risk_detected BOOLEAN,
    refinancing_risk_tier VARCHAR(20),
    refinancing_risk_score NUMERIC(5,2),
    refinancing_maturity_cluster_months INTEGER,
    refinancing_debt_maturing_1y_pct NUMERIC(5,2),
    refinancing_evidence TEXT,

    -- Pattern 2: Fee Response
    fee_response_detected BOOLEAN,
    fee_response_type VARCHAR(20),
    fee_response_score NUMERIC(5,2),
    fee_increase_pct NUMERIC(5,2),
    fee_increase_reason TEXT,
    chronic_losses_years INTEGER,
    fee_response_evidence TEXT,

    -- Pattern 3: Depreciation Paradox
    depreciation_paradox_detected BOOLEAN,
    depreciation_paradox_score NUMERIC(5,2),
    result_with_depreciation BIGINT,
    result_without_depreciation BIGINT,
    depreciation_amount BIGINT,
    depreciation_paradox_evidence TEXT,

    -- Pattern 4: Cash Crisis
    cash_crisis_detected BOOLEAN,
    cash_crisis_severity VARCHAR(20),
    cash_to_debt_ratio NUMERIC(5,4),
    monthly_burn_rate BIGINT,
    months_until_insolvency NUMERIC(5,1),
    cash_crisis_evidence TEXT,

    -- Pattern 5: Lokaler Dependency
    lokaler_dependency_detected BOOLEAN,
    lokaler_dependency_tier VARCHAR(20),
    lokaler_area_pct NUMERIC(5,2),
    lokaler_revenue_pct NUMERIC(5,2),
    lokaler_concentration_risk NUMERIC(5,2),
    lokaler_dependency_evidence TEXT,

    -- Pattern 6: Tomträtt Escalation
    tomtratt_escalation_detected BOOLEAN,
    tomtratt_escalation_tier VARCHAR(20),
    tomtratt_yoy_increase_pct NUMERIC(5,2),
    tomtratt_current_annual BIGINT,
    tomtratt_per_sqm NUMERIC(10,2),
    tomtratt_escalation_evidence TEXT,

    -- Pattern 7: Pattern B
    pattern_b_detected BOOLEAN,
    pattern_b_years_consecutive_loss INTEGER,
    pattern_b_construction_year INTEGER,
    pattern_b_brf_age INTEGER,
    pattern_b_is_concern BOOLEAN,
    pattern_b_evidence TEXT,

    -- Pattern 8: Interest Rate Victim
    interest_rate_victim_detected BOOLEAN,
    interest_rate_increase_pct NUMERIC(5,2),
    interest_expense_yoy_increase BIGINT,
    profit_to_loss_trigger BOOLEAN,
    interest_rate_victim_evidence TEXT,

    -- Risk Scores
    management_quality_score NUMERIC(5,2),
    management_quality_grade VARCHAR(10),
    management_quality_factors JSONB,
    financial_stability_score NUMERIC(5,2),
    financial_stability_grade VARCHAR(10),
    financial_stability_factors JSONB,
    stabilization_probability_score NUMERIC(5,2),
    stabilization_probability_grade VARCHAR(10),
    stabilization_timeframe_years INTEGER,
    overall_risk_score NUMERIC(5,2),
    overall_risk_grade VARCHAR(10),
    overall_risk_category VARCHAR(20),

    -- Comparative Intelligence
    soliditet_percentile NUMERIC(5,2),
    debt_per_sqm_percentile NUMERIC(5,2),
    fee_per_sqm_percentile NUMERIC(5,2),
    energy_cost_percentile NUMERIC(5,2),

    classification_json JSONB,

    UNIQUE(extraction_id)
);

CREATE INDEX idx_classifications_extraction ON ground_truth_classifications(extraction_id);
CREATE INDEX idx_classifications_brf ON ground_truth_classifications(brf_id);

-- ============================================================================
-- PATTERN_SUMMARY TABLE (Denormalized pattern flags)
-- ============================================================================
CREATE TABLE ground_truth_pattern_summary (
    summary_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,
    brf_id VARCHAR(50) NOT NULL,

    has_refinancing_risk BOOLEAN DEFAULT FALSE,
    has_fee_distress BOOLEAN DEFAULT FALSE,
    has_depreciation_paradox BOOLEAN DEFAULT FALSE,
    has_cash_crisis BOOLEAN DEFAULT FALSE,
    has_lokaler_risk BOOLEAN DEFAULT FALSE,
    has_tomtratt_escalation BOOLEAN DEFAULT FALSE,
    has_pattern_b BOOLEAN DEFAULT FALSE,
    has_interest_rate_shock BOOLEAN DEFAULT FALSE,

    critical_pattern_count INTEGER DEFAULT 0,
    high_risk_pattern_count INTEGER DEFAULT 0,
    risk_category VARCHAR(20),
    requires_attention BOOLEAN DEFAULT FALSE,

    UNIQUE(extraction_id)
);

CREATE INDEX idx_pattern_summary_extraction ON ground_truth_pattern_summary(extraction_id);
CREATE INDEX idx_pattern_summary_brf ON ground_truth_pattern_summary(brf_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Complete operational cost breakdown with all line items
CREATE OR REPLACE VIEW vw_operational_costs_complete AS
SELECT
    e.brf_id,
    e.organization_name,
    e.report_year,
    oc.total_operating_costs,
    oc.total_driftskostnader,
    oc.operating_cost_per_sqm,
    oc.utility_pattern,
    json_agg(
        json_build_object(
            'category', ocd.cost_category,
            'item', ocd.cost_item,
            'amount', ocd.amount_current_year,
            'previous_year', ocd.amount_previous_year,
            'change_pct', ocd.change_pct,
            'per_sqm', ocd.cost_per_sqm
        )
        ORDER BY ocd.amount_current_year DESC
    ) as cost_details
FROM ground_truth_extractions e
JOIN operational_costs oc ON e.extraction_id = oc.extraction_id
LEFT JOIN operational_cost_details ocd ON oc.operational_costs_id = ocd.operational_costs_id
GROUP BY e.brf_id, e.organization_name, e.report_year, oc.total_operating_costs,
         oc.total_driftskostnader, oc.operating_cost_per_sqm, oc.utility_pattern;

-- Complete financial summary with all linked data
CREATE OR REPLACE VIEW vw_financial_summary_complete AS
SELECT
    e.brf_id,
    e.organization_name,
    e.report_year,
    fs.total_revenue,
    fs.operating_result,
    fs.result_after_financial,
    fs.total_assets,
    fs.total_equity,
    fs.soliditet_pct,
    fs.cash_and_bank,
    l.total_debt,
    l.average_interest_rate_pct,
    f.avg_fee_per_sqm_residential,
    oc.total_operating_costs,
    oc.operating_cost_per_sqm
FROM ground_truth_extractions e
LEFT JOIN financial_statements fs ON e.extraction_id = fs.extraction_id
LEFT JOIN loans l ON e.extraction_id = l.extraction_id
LEFT JOIN fees f ON e.extraction_id = f.extraction_id
LEFT JOIN operational_costs oc ON e.extraction_id = oc.extraction_id;

-- Pattern distribution view
CREATE OR REPLACE VIEW vw_pattern_distribution AS
SELECT
    COUNT(*) as total_brfs,
    SUM(CASE WHEN has_refinancing_risk THEN 1 ELSE 0 END) as refinancing_risk_count,
    SUM(CASE WHEN has_fee_distress THEN 1 ELSE 0 END) as fee_distress_count,
    SUM(CASE WHEN has_depreciation_paradox THEN 1 ELSE 0 END) as depreciation_paradox_count,
    SUM(CASE WHEN has_cash_crisis THEN 1 ELSE 0 END) as cash_crisis_count,
    SUM(CASE WHEN has_lokaler_risk THEN 1 ELSE 0 END) as lokaler_risk_count,
    SUM(CASE WHEN has_tomtratt_escalation THEN 1 ELSE 0 END) as tomtratt_escalation_count,
    SUM(CASE WHEN has_pattern_b THEN 1 ELSE 0 END) as pattern_b_count,
    SUM(CASE WHEN has_interest_rate_shock THEN 1 ELSE 0 END) as interest_rate_shock_count,
    ROUND(AVG(critical_pattern_count), 2) as avg_critical_patterns,
    ROUND(AVG(high_risk_pattern_count), 2) as avg_high_risk_patterns
FROM ground_truth_pattern_summary;

-- High risk BRFs view
CREATE OR REPLACE VIEW vw_high_risk_brfs AS
SELECT
    e.brf_id,
    e.organization_name,
    e.report_year,
    s.critical_pattern_count,
    s.high_risk_pattern_count,
    c.overall_risk_score,
    c.overall_risk_category,
    s.has_refinancing_risk,
    s.has_cash_crisis,
    s.has_fee_distress
FROM ground_truth_extractions e
JOIN ground_truth_classifications c ON e.extraction_id = c.extraction_id
JOIN ground_truth_pattern_summary s ON e.extraction_id = s.extraction_id
WHERE s.risk_category IN ('HIGH', 'CRITICAL')
   OR s.critical_pattern_count > 0
ORDER BY c.overall_risk_score DESC;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE ground_truth_extractions IS 'Master table for each BRF extraction with basic identification';
COMMENT ON TABLE properties IS 'Physical property characteristics and ownership details';
COMMENT ON TABLE membership IS 'Unit distribution and member counts';
COMMENT ON TABLE governance IS 'Board structure and leadership';
COMMENT ON TABLE board_members IS 'Individual board members and roles';
COMMENT ON TABLE financial_statements IS 'High-level financial statement summary';
COMMENT ON TABLE multi_year_metrics IS 'Historical performance metrics across multiple years';
COMMENT ON TABLE loans IS 'Debt summary and aggregate loan information';
COMMENT ON TABLE loan_details IS 'Individual loan details with rates and maturities';
COMMENT ON TABLE fees IS 'Fee structure and changes';
COMMENT ON TABLE fee_history IS 'Historical fee adjustments';
COMMENT ON TABLE commercial IS 'Commercial space summary';
COMMENT ON TABLE commercial_tenants IS 'Individual commercial tenant leases';
COMMENT ON TABLE operational_costs IS 'Operating expense summary';
COMMENT ON TABLE operational_cost_details IS 'Line-item operational costs with categorization';
COMMENT ON TABLE tax_assessment IS 'Property tax and assessment values';
COMMENT ON TABLE energy IS 'Energy providers and consumption';
COMMENT ON TABLE insurance IS 'Insurance coverage details';
COMMENT ON TABLE maintenance_plan IS 'Long-term maintenance planning';
COMMENT ON TABLE maintenance_completed IS 'Completed maintenance items';
COMMENT ON TABLE maintenance_planned IS 'Planned future maintenance';
COMMENT ON TABLE significant_events IS 'Material events during and after balance sheet date';
COMMENT ON TABLE audit IS 'Audit information and opinions';
COMMENT ON TABLE management_contracts IS 'Property management and service contracts';
COMMENT ON TABLE samfallighet IS 'Shared facility association membership';
COMMENT ON TABLE reserves_funds IS 'Reserve funds and restricted equity';
COMMENT ON TABLE ground_truth_classifications IS 'Pattern classifications and risk scores';
COMMENT ON TABLE ground_truth_pattern_summary IS 'Denormalized pattern flags for easy querying';
