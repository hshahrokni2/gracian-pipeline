-- ============================================================================
-- GROUND TRUTH DATABASE SCHEMA
-- Purpose: Store extracted data + classification/calculated intelligence
-- Clear separation: extracted (from PDF) vs classified (from algorithms)
-- ============================================================================

-- ============================================================================
-- TABLE 1: GROUND TRUTH EXTRACTIONS (Source Data from PDFs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ground_truth_extractions (
    -- Primary Key
    extraction_id SERIAL PRIMARY KEY,

    -- Ground Truth Metadata
    brf_id VARCHAR(50) NOT NULL UNIQUE,  -- e.g., "brf_81563"
    is_ground_truth BOOLEAN DEFAULT TRUE,
    extraction_date TIMESTAMP DEFAULT NOW(),
    extraction_model VARCHAR(100) DEFAULT 'Claude 4.5',

    -- Source Document
    pdf_filename VARCHAR(255),
    pdf_pages_total INTEGER,

    -- Core Identity (EXTRACTED from PDF)
    organization_name VARCHAR(255),
    organization_number VARCHAR(20),
    report_year INTEGER,
    fiscal_year_start DATE,
    fiscal_year_end DATE,
    report_date DATE,
    location VARCHAR(100),
    accounting_standard VARCHAR(10),  -- K2 or K3

    -- Financial Data (EXTRACTED from PDF)
    assets_total BIGINT,
    equity_total BIGINT,
    liabilities_total BIGINT,
    net_revenue BIGINT,
    profit_loss BIGINT,
    soliditet_pct NUMERIC(5,2),
    cash_and_bank BIGINT,

    -- Operating Costs (EXTRACTED from PDF)
    total_driftskostnader BIGINT,
    el_cost BIGINT,
    varme_cost BIGINT,
    vatten_cost BIGINT,
    fastighetsskatt BIGINT,

    -- Loans (EXTRACTED from PDF)
    total_debt BIGINT,
    long_term_debt BIGINT,
    short_term_debt BIGINT,
    average_interest_rate_pct NUMERIC(5,2),

    -- Property (EXTRACTED from PDF)
    total_area_sqm INTEGER,
    bostadsratter_count INTEGER,
    construction_year INTEGER,

    -- Governance (EXTRACTED from PDF)
    chairman VARCHAR(255),
    board_size INTEGER,
    board_meetings_count INTEGER,
    auditor_name VARCHAR(255),
    auditor_firm VARCHAR(255),

    -- Full Extraction JSON (for reference)
    extraction_json JSONB NOT NULL,

    -- Evidence & Quality
    evidence_pages INTEGER[],
    extraction_confidence NUMERIC(3,2),

    -- Indexes
    CONSTRAINT unique_brf_id UNIQUE(brf_id)
);

-- ============================================================================
-- TABLE 2: CLASSIFICATION RESULTS (Calculated Intelligence from Algorithms)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ground_truth_classifications (
    -- Primary Key & Foreign Key
    classification_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,
    brf_id VARCHAR(50) NOT NULL,

    -- Classification Metadata
    classification_date TIMESTAMP DEFAULT NOW(),
    classification_version VARCHAR(20) DEFAULT '1.0',

    -- ========================================================================
    -- PATTERN 1: Refinancing Risk (CALCULATED)
    -- ========================================================================
    refinancing_risk_detected BOOLEAN,
    refinancing_risk_tier VARCHAR(20),  -- EXTREME/HIGH/MEDIUM/NONE
    refinancing_risk_score NUMERIC(5,2),
    refinancing_maturity_cluster_months INTEGER,
    refinancing_debt_maturing_1y_pct NUMERIC(5,2),
    refinancing_evidence TEXT,

    -- ========================================================================
    -- PATTERN 2: Fee Response (CALCULATED)
    -- ========================================================================
    fee_response_detected BOOLEAN,
    fee_response_type VARCHAR(20),  -- DISTRESS/REACTIVE/AGGRESSIVE/PROACTIVE
    fee_response_score NUMERIC(5,2),
    fee_increase_pct NUMERIC(5,2),
    fee_increase_reason TEXT,
    chronic_losses_years INTEGER,
    fee_response_evidence TEXT,

    -- ========================================================================
    -- PATTERN 3: Depreciation Paradox (CALCULATED)
    -- ========================================================================
    depreciation_paradox_detected BOOLEAN,
    depreciation_paradox_score NUMERIC(5,2),
    result_with_depreciation BIGINT,
    result_without_depreciation BIGINT,
    depreciation_amount BIGINT,
    depreciation_paradox_evidence TEXT,

    -- ========================================================================
    -- PATTERN 4: Cash Crisis (CALCULATED)
    -- ========================================================================
    cash_crisis_detected BOOLEAN,
    cash_crisis_severity VARCHAR(20),  -- EXTREME/HIGH/MEDIUM
    cash_to_debt_ratio NUMERIC(5,4),
    monthly_burn_rate BIGINT,
    months_until_insolvency NUMERIC(5,1),
    cash_crisis_evidence TEXT,

    -- ========================================================================
    -- PATTERN 5: Lokaler Dependency (CALCULATED)
    -- ========================================================================
    lokaler_dependency_detected BOOLEAN,
    lokaler_dependency_tier VARCHAR(20),  -- EXTREME/HIGH/MEDIUM/LOW/NONE
    lokaler_area_pct NUMERIC(5,2),
    lokaler_revenue_pct NUMERIC(5,2),
    lokaler_concentration_risk NUMERIC(5,2),
    lokaler_dependency_evidence TEXT,

    -- ========================================================================
    -- PATTERN 6: Tomträtt Escalation (CALCULATED)
    -- ========================================================================
    tomtratt_escalation_detected BOOLEAN,
    tomtratt_escalation_tier VARCHAR(20),  -- EXTREME/HIGH/MEDIUM/LOW/NONE
    tomtratt_yoy_increase_pct NUMERIC(5,2),
    tomtratt_current_annual BIGINT,
    tomtratt_per_sqm NUMERIC(10,2),
    tomtratt_escalation_evidence TEXT,

    -- ========================================================================
    -- PATTERN 7: Pattern B (Young BRF with Chronic Losses) (CALCULATED)
    -- ========================================================================
    pattern_b_detected BOOLEAN,
    pattern_b_years_consecutive_loss INTEGER,
    pattern_b_construction_year INTEGER,
    pattern_b_brf_age INTEGER,
    pattern_b_is_concern BOOLEAN,  -- FALSE for young BRFs (normal)
    pattern_b_evidence TEXT,

    -- ========================================================================
    -- PATTERN 8: Interest Rate Victim (CALCULATED)
    -- ========================================================================
    interest_rate_victim_detected BOOLEAN,
    interest_rate_increase_pct NUMERIC(5,2),
    interest_expense_yoy_increase BIGINT,
    profit_to_loss_trigger BOOLEAN,
    interest_rate_victim_evidence TEXT,

    -- ========================================================================
    -- COMPOSITE RISK SCORES (CALCULATED)
    -- ========================================================================

    -- Score 1: Management Quality (0-100, higher is better)
    management_quality_score NUMERIC(5,2),
    management_quality_grade VARCHAR(10),  -- A/B/C/D/F or N/A
    management_quality_factors JSONB,

    -- Score 2: Financial Stability (0-100, higher is better)
    financial_stability_score NUMERIC(5,2),
    financial_stability_grade VARCHAR(10),  -- A/B/C/D/F or N/A
    financial_stability_factors JSONB,

    -- Score 3: Stabilization Probability (0-100, higher is better)
    stabilization_probability_score NUMERIC(5,2),
    stabilization_probability_grade VARCHAR(10),  -- A/B/C/D/F or N/A
    stabilization_timeframe_years INTEGER,

    -- Score 4: Overall Risk Score (0-100, lower is better)
    overall_risk_score NUMERIC(5,2),
    overall_risk_grade VARCHAR(10),  -- A/B/C/D/F or N/A
    overall_risk_category VARCHAR(20),  -- LOW/MEDIUM/HIGH/CRITICAL

    -- ========================================================================
    -- COMPARATIVE INTELLIGENCE (CALCULATED from Population)
    -- ========================================================================
    soliditet_percentile NUMERIC(5,2),
    debt_per_sqm_percentile NUMERIC(5,2),
    fee_per_sqm_percentile NUMERIC(5,2),
    energy_cost_percentile NUMERIC(5,2),

    -- All Classification Data (for reference)
    classification_json JSONB,

    -- Indexes
    CONSTRAINT unique_classification_per_extraction UNIQUE(extraction_id),
    CONSTRAINT fk_brf_id FOREIGN KEY (brf_id) REFERENCES ground_truth_extractions(brf_id)
);

-- ============================================================================
-- TABLE 3: PATTERN SUMMARY (Denormalized for Easy Querying)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ground_truth_pattern_summary (
    summary_id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES ground_truth_extractions(extraction_id) ON DELETE CASCADE,
    brf_id VARCHAR(50) NOT NULL,

    -- Pattern Flags (for easy filtering)
    has_refinancing_risk BOOLEAN DEFAULT FALSE,
    has_fee_distress BOOLEAN DEFAULT FALSE,
    has_depreciation_paradox BOOLEAN DEFAULT FALSE,
    has_cash_crisis BOOLEAN DEFAULT FALSE,
    has_lokaler_risk BOOLEAN DEFAULT FALSE,
    has_tomtratt_escalation BOOLEAN DEFAULT FALSE,
    has_pattern_b BOOLEAN DEFAULT FALSE,
    has_interest_rate_shock BOOLEAN DEFAULT FALSE,

    -- Count of Critical Patterns
    critical_pattern_count INTEGER DEFAULT 0,
    high_risk_pattern_count INTEGER DEFAULT 0,

    -- Overall Assessment
    risk_category VARCHAR(20),  -- LOW/MEDIUM/HIGH/CRITICAL
    requires_attention BOOLEAN DEFAULT FALSE,

    CONSTRAINT unique_summary_per_extraction UNIQUE(extraction_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Extractions Table
CREATE INDEX idx_gt_extractions_brf_id ON ground_truth_extractions(brf_id);
CREATE INDEX idx_gt_extractions_year ON ground_truth_extractions(report_year);
CREATE INDEX idx_gt_extractions_location ON ground_truth_extractions(location);
CREATE INDEX idx_gt_extractions_ground_truth ON ground_truth_extractions(is_ground_truth);

-- Classifications Table
CREATE INDEX idx_gt_classifications_brf_id ON ground_truth_classifications(brf_id);
CREATE INDEX idx_gt_classifications_extraction_id ON ground_truth_classifications(extraction_id);
CREATE INDEX idx_gt_classifications_risk_category ON ground_truth_classifications(overall_risk_category);

-- Pattern Summary Table
CREATE INDEX idx_gt_summary_brf_id ON ground_truth_pattern_summary(brf_id);
CREATE INDEX idx_gt_summary_risk_category ON ground_truth_pattern_summary(risk_category);
CREATE INDEX idx_gt_summary_requires_attention ON ground_truth_pattern_summary(requires_attention);

-- Pattern-Specific Indexes
CREATE INDEX idx_gt_refinancing_risk ON ground_truth_pattern_summary(has_refinancing_risk);
CREATE INDEX idx_gt_cash_crisis ON ground_truth_pattern_summary(has_cash_crisis);
CREATE INDEX idx_gt_fee_distress ON ground_truth_pattern_summary(has_fee_distress);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Complete Ground Truth Records (Extracted + Classified)
CREATE OR REPLACE VIEW vw_ground_truth_complete AS
SELECT
    e.brf_id,
    e.organization_name,
    e.report_year,
    e.assets_total,
    e.total_debt,
    e.soliditet_pct,
    c.refinancing_risk_tier,
    c.fee_response_type,
    c.overall_risk_score,
    c.overall_risk_grade,
    s.critical_pattern_count,
    s.risk_category,
    e.extraction_date,
    c.classification_date
FROM ground_truth_extractions e
LEFT JOIN ground_truth_classifications c ON e.extraction_id = c.extraction_id
LEFT JOIN ground_truth_pattern_summary s ON e.extraction_id = s.extraction_id
WHERE e.is_ground_truth = TRUE
ORDER BY e.report_year DESC, e.organization_name;

-- View: High-Risk BRFs
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

-- View: Pattern Distribution
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

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE ground_truth_extractions IS
'Source data EXTRACTED from PDF annual reports - this is what the LLM reads from the document';

COMMENT ON TABLE ground_truth_classifications IS
'Intelligence CALCULATED by classification algorithms - this is what we compute from the extracted data';

COMMENT ON TABLE ground_truth_pattern_summary IS
'Denormalized pattern flags for easy querying and reporting';

COMMENT ON COLUMN ground_truth_extractions.is_ground_truth IS
'TRUE = manually validated ground truth, FALSE = automated extraction';

COMMENT ON COLUMN ground_truth_classifications.refinancing_risk_tier IS
'CALCULATED: EXTREME (80%+ debt in 6mo), HIGH (60%+), MEDIUM (40%+), NONE';

COMMENT ON COLUMN ground_truth_classifications.fee_response_type IS
'CALCULATED: DISTRESS (reactive after chronic losses), REACTIVE, AGGRESSIVE, PROACTIVE';

COMMENT ON COLUMN ground_truth_classifications.management_quality_score IS
'CALCULATED: 0-100 composite score based on 8 factors (fee timing, evidence quality, etc.)';
