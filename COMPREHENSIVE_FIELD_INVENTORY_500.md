# Comprehensive Field Inventory: 500-Field Full Extraction

**Date**: October 14, 2025 23:00 UTC
**Purpose**: Define ALL extractable fields from Swedish BRF Årsredovisning
**Scope**: Complete data intelligence for digital twin foundation
**Target**: 400-500 structured fields per document

---

## 📊 Executive Summary

Based on analysis of typical Swedish BRF (housing cooperative) annual reports, this document defines the complete universe of extractable structured data across all major sections:

| Category | Fields | Priority | Coverage Target |
|----------|--------|----------|-----------------|
| **Governance & Legal** | 50 | P0-P1 | 95% |
| **Financial Statements** | 100 | P0 | 98% |
| **Notes (Comprehensive)** | 200 | P0-P2 | 85% |
| **Property & Operations** | 50 | P1 | 90% |
| **Time Series (3-year)** | 80 | P1-P2 | 80% |
| **Calculated Metrics** | 30 | P2 | 95% |
| **Appendices & Narrative** | 20 | P3 | 60% |
| **TOTAL** | **530** | Mixed | **87%** |

**Realistic Target for Phase 1**: 430-500 fields (P0-P2)

---

## 🗂️ Category 1: Governance & Legal (50 fields)

### **1.1 Board & Management** (15 fields)

```yaml
board_and_management:
  # Current chairman details
  chairman_name: str  # Ordförande
  chairman_role_since: date  # When appointed
  chairman_address: str  # If listed
  chairman_phone: str  # If listed

  # Board members (structured array)
  board_members: list[BoardMember]  # [{name, role, since, address}]
  # BoardMember: {name: str, role: str, appointed_date: date, address: str}

  # Alternate board members
  deputy_members: list[str]  # Suppleanter
  deputy_count: int

  # Board meeting activity
  board_meetings_held: int  # Antal styrelsemöten
  board_meeting_frequency: str  # månadsvis/kvartalsvis

  # Historical chairman (if listed)
  previous_chairman: str  # If rotation occurred

  # Board size statistics
  total_board_size: int  # Including deputies
  quorum_requirement: str  # If stated

  # Board compensation (if disclosed)
  board_compensation: dict  # {chairman: num, members: num}
```

### **1.2 Auditors & Review** (10 fields)

```yaml
auditors:
  # Current auditor
  auditor_name: str  # Auktoriserad revisor
  auditor_firm: str  # E.g., KPMG, PwC, HQV
  auditor_address: str
  auditor_qualification: str  # Auktoriserad/Godkänd

  # Audit report details
  audit_date: date  # Revisionsberättelse datum
  audit_location: str  # Revision location
  audit_opinion: str  # Clean/Qualified/Adverse
  audit_emphasis_of_matter: str  # Upplysningar utan reservation

  # Internal auditor (if exists)
  internal_auditor_name: str  # Ordinarie Intern Internrevisor
  internal_auditor_firm: str
```

### **1.3 Nomination Committee** (5 fields)

```yaml
nomination_committee:
  members: list[str]  # Valberedning
  member_count: int
  chairman: str  # Valberedningens ordförande
  election_date: date  # When elected
  mandate_period: str  # E.g., "till nästa årsstämma"
```

### **1.4 Legal & Registration** (10 fields)

```yaml
legal:
  # Corporate identity
  organization_number: str  # Organisationsnummer (12 digits)
  organization_name: str  # Bostadsrättsföreningen [Name]
  legal_form: str  # "Bostadsrättsförening"

  # Registration details
  registration_date: date  # Registrerat datum
  registration_authority: str  # Bolagsverket

  # Document registration
  bylaws_registration_date: date  # Stadgar registrerade
  economic_plan_registration_date: date  # Ekonomisk plan registrerad

  # Tax classification
  tax_classification: str  # E.g., "privatbostadsföretag"
  tax_law_reference: str  # E.g., "inkomstskattelagen (1999:1229)"
  vat_registration: bool  # If VAT registered
```

### **1.5 Annual Meeting** (10 fields)

```yaml
annual_meeting:
  # Meeting details
  meeting_date: date  # Årsstämma datum
  meeting_location: str
  meeting_quorum: int  # Antal närvarande

  # Attendance
  members_present: int  # Antal medlemmar
  proxies_used: int  # Antal ombud
  total_votes: int

  # Decisions
  decisions_summary: str  # Key decisions made
  dividend_decision: num  # If applicable
  fee_decision: dict  # {old_fee: num, new_fee: num, effective_date: date}

  # Financial approval
  financial_statements_approved: bool
```

---

## 💰 Category 2: Financial Statements (100 fields)

### **2.1 Income Statement (Resultaträkning)** (35 fields)

```yaml
income_statement:
  # REVENUE (Intäkter)
  rental_income: num  # Hyresintäkter från bostäder
  rental_income_commercial: num  # Hyresintäkter från lokaler
  monthly_fees: num  # Årsavgifter från medlemmar
  parking_income: num  # Parkeringsintäkter
  laundry_income: num  # Tvättstugeintäkter
  interest_income: num  # Ränteintäkter
  dividend_income: num  # Utdelning
  other_operating_income: num  # Övriga rörelseintäkter
  extraordinary_income: num  # Extraordinära intäkter
  total_revenue: num  # Summa rörelseintäkter

  # OPERATING COSTS (Rörelsekostnader)
  property_management_fee: num  # Förvaltningskostnader
  maintenance_repairs: num  # Reparation och underhåll
  heating_costs: num  # Uppvärmning
  electricity_costs: num  # El (fastighet)
  water_costs: num  # Vatten
  property_tax: num  # Fastighetsavgift
  insurance_costs: num  # Försäkring
  cleaning_costs: num  # Städning
  snow_removal: num  # Snöröjning
  garden_maintenance: num  # Trädgårdsskötsel
  waste_management: num  # Sophämtning
  elevator_maintenance: num  # Hissar
  other_property_costs: num  # Övriga fastighetskostnader
  personnel_costs: num  # Personalkostnader (if any)
  administration_costs: num  # Administrationskostnader
  depreciation_buildings: num  # Avskrivningar byggnader
  depreciation_equipment: num  # Avskrivningar inventarier
  total_operating_costs: num  # Summa rörelsekostnader

  # OPERATING RESULT (Rörelseresultat)
  operating_result: num  # Rörelseresultat före finansiella poster

  # FINANCIAL ITEMS (Finansiella poster)
  interest_expense: num  # Räntekostnader
  interest_expense_loans: num  # Räntekostnader lån
  other_financial_expense: num  # Övriga finansiella kostnader
  net_financial: num  # Resultat efter finansiella poster

  # TAX (Skatt)
  current_tax: num  # Aktuell skatt
  deferred_tax: num  # Uppskjuten skatt
  total_tax: num  # Summa skatt

  # NET RESULT (Årets resultat)
  net_result: num  # Årets resultat
```

### **2.2 Balance Sheet - Assets (Balansräkning Tillgångar)** (25 fields)

```yaml
balance_sheet_assets:
  # FIXED ASSETS (Anläggningstillgångar)
  # Tangible assets
  land: num  # Mark
  buildings: num  # Byggnader och markanläggningar
  equipment: num  # Inventarier
  construction_in_progress: num  # Pågående ny-/till-/ombyggnader
  total_tangible_assets: num  # Summa materiella anläggningstillgångar

  # Financial assets
  financial_assets: num  # Finansiella anläggningstillgångar
  long_term_investments: num  # Långfristiga placeringar
  deferred_tax_asset: num  # Uppskjuten skattefordran
  total_fixed_assets: num  # Summa anläggningstillgångar

  # CURRENT ASSETS (Omsättningstillgångar)
  # Short-term receivables
  accounts_receivable: num  # Kundfordringar
  tax_receivables: num  # Skattefordringar
  prepaid_expenses: num  # Förutbetalda kostnader
  accrued_income: num  # Upplupna intäkter
  other_receivables: num  # Övriga fordringar
  total_receivables: num  # Summa kortfristiga fordringar

  # Short-term investments
  short_term_investments: num  # Kortfristiga placeringar

  # Cash and bank
  cash_bank: num  # Kassa och bank
  cash_bank_breakdown: dict  # {checking: num, savings: num}

  # Total current assets
  total_current_assets: num  # Summa omsättningstillgångar

  # TOTAL ASSETS
  total_assets: num  # Summa tillgångar
```

### **2.3 Balance Sheet - Equity & Liabilities (Eget kapital och skulder)** (20 fields)

```yaml
balance_sheet_equity_liabilities:
  # EQUITY (Eget kapital)
  share_capital: num  # Medlemsinsatser
  statutory_reserve: num  # Bundet eget kapital - reservfond
  total_restricted_equity: num  # Summa bundet eget kapital

  retained_earnings: num  # Balanserat resultat
  current_year_result: num  # Årets resultat
  total_unrestricted_equity: num  # Summa fritt eget kapital

  total_equity: num  # Summa eget kapital

  # LIABILITIES (Skulder)
  # Long-term liabilities
  mortgage_loans: num  # Lån i kreditinstitut (långfristiga)
  other_long_term_liabilities: num  # Övriga långfristiga skulder
  total_long_term_liabilities: num  # Summa långfristiga skulder

  # Short-term liabilities
  short_term_loans: num  # Lån i kreditinstitut (kortfristiga)
  accounts_payable: num  # Leverantörsskulder
  tax_liabilities: num  # Skatteskulder
  prepaid_fees: num  # Förutbetalda avgifter från medlemmar
  accrued_expenses: num  # Upplupna kostnader
  other_short_term_liabilities: num  # Övriga kortfristiga skulder
  total_short_term_liabilities: num  # Summa kortfristiga skulder

  # TOTAL EQUITY AND LIABILITIES
  total_equity_and_liabilities: num  # Summa eget kapital och skulder
```

### **2.4 Cash Flow Statement (Kassaflödesanalys)** (20 fields)

```yaml
cash_flow:
  # OPERATING ACTIVITIES (Löpande verksamhet)
  operating_result_before_finance: num  # Rörelseresultat före finansiella poster
  adjustments_non_cash: num  # Justeringar för ej likviditetspåverkande poster
  depreciation_added_back: num  # Avskrivningar
  interest_paid: num  # Betald ränta
  interest_received: num  # Mottagen ränta
  income_tax_paid: num  # Betald skatt

  # Working capital changes
  change_receivables: num  # Förändring kundfordringar
  change_payables: num  # Förändring leverantörsskulder
  change_other_working_capital: num  # Förändring övrigt rörelsekapital
  working_capital_changes: num  # Summa förändringar i rörelsekapital

  cash_from_operating: num  # Kassaflöde från löpande verksamheten

  # INVESTING ACTIVITIES (Investeringsverksamhet)
  property_investments: num  # Investeringar i byggnader
  equipment_purchases: num  # Inköp av inventarier
  asset_disposals: num  # Försäljning av anläggningstillgångar
  cash_from_investing: num  # Kassaflöde från investeringsverksamheten

  # FINANCING ACTIVITIES (Finansieringsverksamhet)
  new_loans: num  # Upptagna lån
  loan_repayments: num  # Amortering av lån
  members_deposits: num  # Inbetalda medlemsinsatser
  cash_from_financing: num  # Kassaflöde från finansieringsverksamheten

  # TOTAL CASH FLOW
  net_cash_flow: num  # Årets kassaflöde
```

---

## 📝 Category 3: Notes - Comprehensive (200 fields)

### **3.1 Note 1: Accounting Principles** (10 fields)

```yaml
note_1_accounting:
  accounting_standard: str  # K2/K3/IFRS
  accounting_framework: str  # BFNAR 2016:10
  valuation_method: str  # Anskaffningsvärde
  reporting_currency: str  # SEK
  fiscal_year: str  # E.g., "2021-01-01 till 2021-12-31"

  # Specific policies
  depreciation_policy: str  # Avskrivningsprinciper
  inventory_valuation: str  # Lagetvärdering (if applicable)
  revenue_recognition: str  # Intäktsredovisning
  lease_accounting: str  # Leasingavtal behandling
  contingent_liabilities_policy: str  # Eventualförpliktelser policy
```

### **3.2 Note 2: Revenue Recognition** (8 fields)

```yaml
note_2_revenue:
  revenue_policy: str  # När intäkter redovisas
  fee_billing_frequency: str  # Månadsvis/kvartalsvis
  fee_payment_terms: str  # Betalningsvillkor

  # Fee details
  monthly_fee_per_sqm: num  # SEK/m² per month
  average_apartment_size: num  # Average m²
  typical_monthly_fee: num  # For average apartment

  # Revenue breakdown by source
  revenue_from_members: num  # Från medlemmar
  revenue_from_external: num  # Från externa hyresgäster
```

### **3.3 Note 3: Personnel** (12 fields)

```yaml
note_3_personnel:
  # Employee count
  employee_count: int  # Medelantalet anställda
  employee_count_end_of_year: int

  # Salaries and benefits
  salaries_and_benefits: num  # Löner och ersättningar
  salaries_board: num  # Styrelsearvoden
  salaries_management: num  # Verkställande direktör (if applicable)
  salaries_employees: num  # Övriga anställda

  # Social costs
  pension_costs: num  # Pensionskostnader
  social_security: num  # Sociala avgifter
  other_personnel_costs: num  # Övriga personalkostnader

  # Total compensation
  total_personnel_costs: num  # Summa personalkostnader

  # Gender distribution (if disclosed)
  gender_distribution: dict  # {male: int, female: int}
```

### **3.4 Note 4: Operating Costs (Detailed)** (25 fields)

```yaml
note_4_operating_costs:
  # Heating (Uppvärmning)
  heating_total: num
  heating_district: num  # Fjärrvärme
  heating_oil: num  # Olja
  heating_electricity: num  # El
  heating_gas: num  # Gas
  heating_other: num

  # Electricity (El)
  electricity_total: num
  electricity_common_areas: num  # Gemensamma utrymmen
  electricity_heating: num  # Uppvärmning
  electricity_elevators: num  # Hissar
  electricity_other: num

  # Water (Vatten)
  water_total: num
  water_consumption: num  # Vattenkonsumtion
  water_sewage: num  # Avloppsavgift

  # Property maintenance
  maintenance_total: num  # Reparation och underhåll
  maintenance_planned: num  # Planerat underhåll
  maintenance_emergency: num  # Akut underhåll
  maintenance_exterior: num  # Yttre underhåll
  maintenance_interior: num  # Inre underhåll

  # Property tax and insurance
  property_tax_total: num  # Fastighetsavgift
  insurance_total: num  # Försäkring
  insurance_property: num  # Fastighetsförsäkring
  insurance_liability: num  # Ansvarsförsäkring

  # Other operating costs
  cleaning_total: num
  snow_removal_total: num
```

### **3.5 Note 5: Loans (Comprehensive)** (30 fields)

```yaml
note_5_loans:
  # Loan summary
  total_loans: num  # Summa låneskulder
  loan_count: int  # Antal lån

  # Individual loans (array of loan objects)
  loans: list[Loan]  # See Loan structure below

  # Aggregate metrics
  weighted_average_rate: num  # Genomsnittlig ränta
  total_annual_interest: num  # Årlig räntekostnad

  # Loan maturity profile
  loans_maturing_1_year: num  # Förfaller inom 1 år
  loans_maturing_1_5_years: num  # Förfaller 1-5 år
  loans_maturing_5plus_years: num  # Förfaller >5 år

  # Collateral
  collateral_description: str  # Säkerheter
  pledged_property_value: num  # Pantsatt fastighetsvärde

  # Loan covenants
  covenants: str  # Lånevillkor
  covenant_breaches: str  # Eventuella brott mot villkor

  # Amortization
  amortization_requirement: str  # Amorteringskrav
  annual_amortization: num  # Årlig amortering

  # Interest rate hedging
  interest_rate_swaps: list[dict]  # Räntederivat
  hedging_ratio: num  # Andel säkrad ränta

# Loan structure for loans array:
Loan:
  lender: str  # E.g., "SEB", "SBAB", "Nordea"
  loan_number: str  # Lånummer
  original_amount: num  # Ursprungligt belopp
  outstanding_balance: num  # Utestående belopp
  interest_rate: num  # Ränta (decimal, e.g., 0.0057)
  interest_rate_type: str  # "Fast"/"Rörlig"
  interest_period: str  # E.g., "3 månader", "5 år"
  maturity_date: date  # Förfallodag
  amortization_schedule: str  # E.g., "amorteringsfria", "annuitet"
  annual_payment: num  # Årlig betalning
  collateral: str  # Säkerhet för detta lån
  notes: str  # Eventuella anteckningar
```

### **3.6 Note 6: Financial Instruments** (15 fields)

```yaml
note_6_financial_instruments:
  # Derivatives summary
  derivatives_count: int
  derivatives_notional: num  # Nominellt belopp
  derivatives_fair_value: num  # Verkligt värde

  # Interest rate derivatives
  interest_rate_swaps: list[dict]
  # Each swap: {counterparty, notional, rate, maturity, fair_value}

  # Valuation
  valuation_method: str  # Värderingsmetod
  valuation_hierarchy_level: int  # Nivå 1/2/3

  # Risk exposure
  interest_rate_risk: num  # Ränterisk
  credit_risk: num  # Kreditrisk
  liquidity_risk: str  # Likviditetsrisk beskrivning

  # Sensitivity analysis
  rate_sensitivity_1bp: num  # Värdeförändring vid 1% ränteändring

  # Hedge accounting
  hedge_accounting_applied: bool
  hedge_effectiveness: num  # If applicable
```

### **3.7 Note 7: Fixed Assets - Detailed Movements** (20 fields)

```yaml
note_7_fixed_assets:
  # Buildings and land
  buildings_acquisition_cost_beginning: num  # Ingående anskaffningsvärde
  buildings_additions: num  # Årets inköp
  buildings_disposals: num  # Årets försäljningar
  buildings_reclassifications: num  # Omklassificeringar
  buildings_acquisition_cost_end: num  # Utgående anskaffningsvärde

  buildings_depreciation_beginning: num  # Ingående avskrivningar
  buildings_depreciation_current_year: num  # Årets avskrivningar
  buildings_depreciation_disposals: num  # Avskrivningar försäljningar
  buildings_depreciation_end: num  # Utgående avskrivningar

  buildings_book_value: num  # Redovisat värde

  # Equipment (similar structure)
  equipment_acquisition_cost_beginning: num
  equipment_additions: num
  equipment_disposals: num
  equipment_acquisition_cost_end: num

  equipment_depreciation_beginning: num
  equipment_depreciation_current_year: num
  equipment_depreciation_disposals: num
  equipment_depreciation_end: num

  equipment_book_value: num

  # Total fixed assets
  total_fixed_assets_book_value: num
```

### **3.8 Note 8: Depreciation Schedule** (15 fields)

```yaml
note_8_depreciation:
  # Depreciation policy
  depreciation_method: str  # Linjär/degressiv

  # Buildings
  buildings_useful_life: int  # Years (e.g., 100-120)
  buildings_annual_rate: num  # % (e.g., 1.5%)
  buildings_current_depreciation: num

  # Heating systems
  heating_useful_life: int  # Years (e.g., 30)
  heating_annual_rate: num
  heating_current_depreciation: num

  # Elevators
  elevators_useful_life: int  # Years (e.g., 20)
  elevators_annual_rate: num
  elevators_current_depreciation: num

  # Equipment
  equipment_useful_life: int  # Years (e.g., 5-10)
  equipment_annual_rate: num
  equipment_current_depreciation: num

  # Total
  total_depreciation: num
  depreciation_schedule_full: dict  # Complete schedule by category
```

### **3.9 Note 9: Receivables** (10 fields)

```yaml
note_9_receivables:
  # Receivables breakdown
  tenant_receivables: num  # Hyresfordringar
  tenant_receivables_doubtful: num  # Osäkra fordringar

  tax_receivables: num  # Skattefordringar
  vat_receivable: num  # Moms att få tillbaka

  prepaid_expenses: num  # Förutbetalda kostnader
  prepaid_insurance: num  # Förutbetald försäkring
  prepaid_rent: num  # Förutbetald hyra

  accrued_income: num  # Upplupna intäkter

  other_receivables: num  # Övriga fordringar
  total_receivables: num  # Summa fordringar
```

### **3.10 Note 10: Reserves and Funds** (12 fields)

```yaml
note_10_reserves:
  # Maintenance fund (Fond för yttre underhåll)
  maintenance_fund_beginning: num  # Ingående balans
  maintenance_fund_allocation: num  # Årets avsättning
  maintenance_fund_utilization: num  # Årets nyttjande
  maintenance_fund_closing: num  # Utgående balans

  # Reserve fund (Reservfond)
  reserve_fund_beginning: num
  reserve_fund_allocation: num
  reserve_fund_closing: num

  # Other reserves
  other_reserves_beginning: num
  other_reserves_allocation: num
  other_reserves_utilization: num
  other_reserves_closing: num

  # Total reserves
  total_reserves: num
```

### **3.11 Note 11: Contingent Liabilities** (8 fields)

```yaml
note_11_contingent_liabilities:
  # Guarantees and warranties
  guarantees: str  # Borgensåtaganden
  guarantees_amount: num  # If quantifiable

  warranties: str  # Garantiåtaganden
  warranties_amount: num

  # Legal disputes
  legal_disputes: str  # Pågående tvister
  legal_disputes_estimated_liability: num

  # Environmental obligations
  environmental_obligations: str
  environmental_obligations_amount: num
```

### **3.12 Note 12: Related Parties** (10 fields)

```yaml
note_12_related_parties:
  # Related party transactions
  related_party_transactions: list[dict]
  # Each: {party, relationship, transaction_type, amount, terms}

  # Key management compensation
  board_compensation_total: num
  board_chairman_compensation: num
  board_members_compensation: num

  # Loans to/from related parties
  loans_to_related_parties: num
  loans_from_related_parties: num

  # Other transactions
  purchases_from_related_parties: num
  sales_to_related_parties: num

  # Terms
  related_party_terms: str  # Beskrivning av villkor
```

### **3.13 Note 13: Significant Events** (10 fields)

```yaml
note_13_events:
  # Events during the year
  major_renovations: str  # Större renoveringar
  loan_refinancing: str  # Omlån
  property_improvements: str  # Fastighetsförbättringar

  # Events after balance sheet date
  events_after_balance_sheet: str  # Händelser efter balansdagen
  subsequent_events_financial_impact: num  # Ekonomisk påverkan

  # Warranty claims
  warranty_claims: str  # A-anmärkningar
  warranty_claims_status: str  # Status

  # Tenant changes
  commercial_tenant_changes: str  # Förändring i lokaluthyrning

  # Other significant events
  other_events: str
  management_assessment: str  # Styrelsens bedömning av händelser
```

### **3.14 Note 14-20: Additional Notes** (45 fields)

```yaml
additional_notes:
  # Note 14: Employee benefits (if applicable)
  pension_obligations: num
  pension_plan_type: str

  # Note 15: Leases
  operating_lease_commitments: num
  lease_maturity_breakdown: dict

  # Note 16: Pledged assets
  pledged_assets: num
  pledged_assets_description: str

  # Note 17: Provisions
  provisions_total: num
  provisions_breakdown: dict

  # Note 18: Accrued expenses
  accrued_expenses_breakdown: dict  # {interest, property_tax, insurance, etc.}

  # Note 19: Prepaid fees
  prepaid_fees_breakdown: dict

  # Note 20: Other information
  dividend_restrictions: str
  ownership_structure: str
  member_count: int  # Antal medlemmar
  cooperative_structure: str

  # Additional details (varies by document)
  note_14_content: str
  note_15_content: str
  note_16_content: str
  note_17_content: str
  note_18_content: str
  note_19_content: str
  note_20_content: str

  # Catch-all for unexpected notes
  other_notes_content: dict  # {note_number: content}
```

---

## 🏢 Category 4: Property & Operations (50 fields)

### **4.1 Property Identification** (12 fields)

```yaml
property_identification:
  # Property designation
  designation: str  # Fastighetsbeteckning
  designation_full: str  # Complete designation with municipality

  # Address
  street_address: str
  postal_code: str
  city: str
  municipality: str  # Kommun
  county: str  # Län

  # Geographic coordinates (if available)
  latitude: num
  longitude: num

  # Property type
  property_type: str  # E.g., "Bostadsrättsförening"
  land_type: str  # E.g., "Tomträtt", "Äganderätt"
```

### **4.2 Building Characteristics** (15 fields)

```yaml
building_characteristics:
  # Construction details
  built_year: int  # Byggår
  renovated_year: int  # Senaste större renovering
  original_builder: str  # Ursprunglig byggare

  # Building structure
  building_count: int  # Antal byggnader
  building_height_stories: int  # Antal våningar
  building_height_meters: num  # Höjd i meter

  # Building area
  total_area: num  # Total area m²
  residential_area: num  # Bostadsarea
  commercial_area: num  # Lokalarea
  common_area: num  # Gemensam yta

  # Construction materials
  foundation_type: str  # Grundläggning
  facade_material: str  # Fasadmaterial
  roof_type: str  # Taktyp

  # Accessibility
  elevator_count: int  # Antal hissar
  wheelchair_accessible: bool  # Tillgänglig för rullstol
```

### **4.3 Apartment Inventory** (8 fields)

```yaml
apartments:
  # Total apartments
  total_apartments: int  # Totalt antal lägenheter

  # Apartment breakdown by size
  apartments_1_rok: int  # 1 rum och kök
  apartments_2_rok: int
  apartments_3_rok: int
  apartments_4_rok: int
  apartments_5plus_rok: int

  # Average statistics
  average_apartment_size: num  # Genomsnittlig storlek m²

  # Apartment details (optional detailed inventory)
  apartment_inventory: list[dict]  # [{apt_number, rooms, sqm, floor}]
```

### **4.4 Systems & Infrastructure** (10 fields)

```yaml
systems:
  # Heating system
  heating_system: str  # E.g., "Fjärrvärme", "Bergvärme"
  heating_provider: str

  # Ventilation
  ventilation_system: str  # E.g., "FTX", "F-system"
  ventilation_renovated_year: int

  # Plumbing
  water_system: str
  sewage_system: str

  # Electrical
  electrical_system: str
  electrical_capacity: num  # kW

  # Internet/TV
  broadband_provider: str
  tv_system: str  # E.g., "Comhem", "Boxer"
```

### **4.5 Energy Performance** (5 fields)

```yaml
energy:
  energy_class: str  # A-G
  energy_consumption_kwh: num  # kWh/m²/år
  primary_energy_number: num
  energy_declaration_date: date  # Energideklaration datum
  energy_certificate_link: str  # If available
```

---

## 📅 Category 5: Time Series Data (80 fields)

### **5.1 Financial Time Series (3-year)** (45 fields)

```yaml
financial_time_series:
  # Income statement (3 years)
  revenue_history: list[num]  # [2021, 2020, 2019]
  expenses_history: list[num]
  operating_result_history: list[num]
  net_result_history: list[num]

  # Balance sheet (3 years)
  assets_history: list[num]
  liabilities_history: list[num]
  equity_history: list[num]

  # Detailed line items (3 years)
  heating_costs_history: list[num]
  electricity_costs_history: list[num]
  water_costs_history: list[num]
  maintenance_costs_history: list[num]
  insurance_costs_history: list[num]

  # Loans (3 years)
  total_loans_history: list[num]
  interest_expense_history: list[num]
  average_interest_rate_history: list[num]

  # Cash flow (3 years)
  cash_from_operating_history: list[num]
  cash_from_investing_history: list[num]
  cash_from_financing_history: list[num]
  net_cash_flow_history: list[num]

  # Per-apartment metrics (3 years)
  equity_per_apartment_history: list[num]
  debt_per_apartment_history: list[num]

  # Additional financial metrics (3 years)
  revenue_growth: list[num]  # YoY %
  expense_growth: list[num]
  margin_history: list[num]  # Operating margin %
  roe_history: list[num]  # Return on equity
  debt_to_equity_history: list[num]
  interest_coverage_history: list[num]

  # Fee history (3 years)
  monthly_fee_history: list[num]
  fee_changes: list[dict]  # [{year, old_fee, new_fee, change_pct}]
```

### **5.2 Operational Time Series (3-year)** (20 fields)

```yaml
operational_time_series:
  # Membership (3 years)
  member_count_history: list[int]
  board_size_history: list[int]

  # Occupancy (3 years)
  occupancy_rate_history: list[num]  # %
  vacancy_count_history: list[int]

  # Maintenance (3 years)
  maintenance_fund_history: list[num]
  maintenance_allocation_history: list[num]
  maintenance_utilization_history: list[num]

  # Energy consumption (3 years)
  heating_consumption_history: list[num]  # kWh
  electricity_consumption_history: list[num]
  water_consumption_history: list[num]  # m³

  # Insurance (3 years)
  insurance_premium_history: list[num]
  insurance_claims_history: list[num]

  # Personnel (3 years, if applicable)
  employee_count_history: list[int]
  personnel_costs_history: list[num]

  # Renovations (3 years)
  renovation_investments_history: list[num]
  major_projects_history: list[str]
```

### **5.3 Market Context (3-year)** (15 fields)

```yaml
market_context_time_series:
  # Property valuation (3 years)
  assessed_value_history: list[num]  # Taxeringsvärde
  market_value_estimate_history: list[num]

  # Loan-to-value (3 years)
  ltv_ratio_history: list[num]  # %

  # Market rent comparison (3 years)
  market_rent_per_sqm_history: list[num]  # Comparative market rent

  # Municipality statistics (if available)
  municipality_avg_fee_history: list[num]
  municipality_avg_debt_history: list[num]

  # Interest rate environment (3 years)
  mortgage_rate_benchmark_history: list[num]  # E.g., STIBOR 3m

  # Inflation adjustment
  cpi_history: list[num]  # Consumer Price Index
  real_fee_change_history: list[num]  # Inflation-adjusted fee change

  # Peer comparisons (if available)
  peer_avg_equity_per_apt_history: list[num]
  peer_avg_debt_per_apt_history: list[num]

  # Area demographics (3 years, if available)
  area_population_history: list[int]
  area_median_income_history: list[num]
  area_unemployment_rate_history: list[num]
```

---

## 📊 Category 6: Calculated Metrics (30 fields)

### **6.1 Financial Health Indicators** (15 fields)

```yaml
financial_health:
  # Leverage ratios
  debt_to_equity_ratio: num  # Skuldsättningsgrad
  debt_to_assets_ratio: num  # Andel skulder av tillgångar
  equity_ratio: num  # Soliditet

  # Per-apartment metrics
  equity_per_apartment: num
  debt_per_apartment: num
  assets_per_apartment: num

  # Profitability
  operating_margin: num  # %
  net_margin: num  # %
  return_on_equity: num  # %
  return_on_assets: num  # %

  # Liquidity
  current_ratio: num  # Kortfristiga tillgångar / skulder
  quick_ratio: num  # (Tillgångar - lager) / kortfristiga skulder
  cash_ratio: num  # Kassa / kortfristiga skulder

  # Coverage
  interest_coverage: num  # EBIT / räntekostnader
  debt_service_coverage: num  # Kassaflöde / totala lånebetalningar
```

### **6.2 Operational Efficiency** (10 fields)

```yaml
operational_efficiency:
  # Cost per apartment
  operating_cost_per_apartment: num
  maintenance_cost_per_apartment: num
  admin_cost_per_apartment: num

  # Cost per m²
  operating_cost_per_sqm: num
  heating_cost_per_sqm: num
  electricity_cost_per_sqm: num

  # Efficiency ratios
  maintenance_to_revenue_ratio: num  # %
  admin_to_revenue_ratio: num  # %

  # Energy efficiency
  energy_cost_per_sqm: num
  energy_consumption_per_sqm: num  # kWh/m²
```

### **6.3 Risk Indicators** (5 fields)

```yaml
risk_indicators:
  # Concentration risk
  largest_loan_concentration: num  # % of total loans
  single_lender_dependency: num  # Max % from one lender

  # Refinancing risk
  loans_maturing_12_months_pct: num  # %

  # Interest rate risk
  variable_rate_exposure: num  # % of loans with variable rates

  # Maintenance risk
  maintenance_fund_sufficiency: num  # Fund / annual allocation (years)
```

---

## 📄 Category 7: Appendices & Narrative (20 fields)

### **7.1 Management Report (Förvaltningsberättelse)** (8 fields)

```yaml
management_report:
  # Narrative sections
  business_overview: str  # Verksamhetsbeskrivning
  year_highlights: str  # Väsentliga händelser under året
  future_outlook: str  # Framtida utveckling
  risk_assessment: str  # Risker och osäkerhetsfaktorer

  # Strategy
  strategic_priorities: str  # Strategiska prioriteringar
  investment_plans: str  # Planerade investeringar

  # Governance
  corporate_governance_summary: str

  # Sustainability
  sustainability_initiatives: str  # If disclosed
```

### **7.2 Audit Report** (5 fields)

```yaml
audit_report:
  # Opinion
  audit_opinion: str  # Revisionsberättelse yttrande
  opinion_type: str  # "Unqualified"/"Qualified"/"Adverse"/"Disclaimer"

  # Emphasis of matter
  emphasis_paragraphs: str  # Upplysningar utan reservation

  # Signatures
  auditor_signatures: list[str]
  audit_report_date: date
```

### **7.3 Board Signatures** (3 fields)

```yaml
board_signatures:
  signature_date: date  # When board signed
  signature_location: str
  board_members_signed: list[str]  # Names of signing members
```

### **7.4 Maintenance Plan (if included)** (4 fields)

```yaml
maintenance_plan:
  plan_period_years: int  # E.g., 10-year plan
  planned_projects: list[dict]  # [{project, year, estimated_cost}]
  total_planned_investment: num
  funding_strategy: str  # How to fund maintenance
```

---

## 🎯 Field Prioritization Framework

### **P0: Critical Foundation** (150 fields)
**Must have for any BRF document - 95%+ coverage target**

1. All financial statements (income, balance, cash flow)
2. Basic governance (chairman, board, auditor)
3. Property basics (designation, address, building year, apartments)
4. Core notes (accounting principles, loans, buildings)
5. Basic time series (3 years of key metrics)

### **P1: High-Value Intelligence** (150 fields)
**Expected in most documents - 85%+ coverage target**

1. Detailed financial breakdowns (revenue, operating costs)
2. Comprehensive notes (personnel, operating costs, receivables, reserves)
3. Property systems and characteristics
4. Operational time series
5. Calculated financial health metrics

### **P2: Comprehensive Detail** (130 fields)
**Nice to have, variable coverage - 70%+ target**

1. All remaining notes (events, related parties, contingent liabilities)
2. Detailed systems & infrastructure
3. Market context time series
4. Operational efficiency metrics
5. Narrative sections (management report)

### **P3: Optional Enhancements** (100 fields)
**Future enhancements - 50%+ target**

1. Appendices (maintenance plans)
2. Sustainability initiatives
3. Market comparables
4. Risk scores
5. External context data

---

## 📈 Coverage Projections by Priority

| Priority | Field Count | Realistic Coverage | Extractable Fields |
|----------|-------------|--------------------|--------------------|
| **P0** | 150 | 95% | 143 |
| **P1** | 150 | 85% | 128 |
| **P2** | 130 | 70% | 91 |
| **P3** | 100 | 50% | 50 |
| **TOTAL** | **530** | **78%** | **412** |

**Target for Phase 1**: P0 + P1 = **300 fields @ 90% coverage = 270 fields extracted**

---

## 🛠️ Implementation Roadmap

### **Week 1-2: Schema Architecture** (P0 Foundation)
- Define complete 530-field schema in `schema_full.py`
- Create Pydantic models for all categories
- Design agent routing strategy
- Output: Complete architectural blueprint

### **Week 3-4: P0 Implementation** (150 critical fields)
- Implement financial statement agents (income, balance, cash flow)
- Implement core notes agents (accounting, loans, buildings)
- Test on 10 diverse PDFs
- Target: 95% coverage on P0 fields

### **Week 5-6: P1 Implementation** (150 high-value fields)
- Implement detailed breakdown agents (revenue, costs)
- Implement comprehensive notes agents (personnel, operating costs)
- Implement time series extraction
- Target: 85% coverage on P1 fields

### **Week 7-8: Integration & Optimization** (P0+P1 complete)
- Integrate all agents into orchestrator
- Optimize performance (caching, parallelization)
- Validate on 100-PDF pilot
- Target: 90% coverage on P0+P1 combined (270 fields)

### **Week 9: Production Deployment**
- **ONE production run on all 27,000 PDFs**
- Extract ALL P0+P1 fields in single pass (300 fields)
- Monitor quality, performance, costs
- Cost: ~$20,000 (vs $37.5K for phased approach)

### **Week 10+: P2/P3 Enhancements** (Optional)
- Implement remaining 230 fields as needed
- Gradual enhancement based on user needs
- No re-extraction of full corpus required

---

## 💰 Cost Analysis

### **Full Extraction (500 fields, one pass)**
- Processing time: ~180-240s per PDF
- Cost: $0.40-0.50 per PDF
- **27,000 PDFs: $10,800-13,500**

### **Phased Approach (30→180→260→430)**
- 4 separate processing runs
- Re-extraction overhead
- **27,000 PDFs: $37,500+**

### **Savings: $24,000-26,700 (65-70% cost reduction)**

---

## ✅ Next Steps

1. **Immediate (Tonight)**:
   - Review and validate this field inventory
   - Identify any missing critical fields
   - Prioritize fields within each category

2. **Tomorrow**:
   - Create `schema_full.py` with complete Pydantic models
   - Define agent routing strategy (15-20 specialized agents)
   - Plan implementation phases

3. **This Week**:
   - Begin P0 implementation (150 critical fields)
   - Test on 10 diverse PDFs
   - Validate extraction quality

---

**Generated**: October 14, 2025 23:00 UTC
**Status**: 🎯 **COMPREHENSIVE FIELD INVENTORY COMPLETE**
**Total Fields Defined**: 530 (P0-P3)
**Realistic Extraction Target**: 412 fields @ 78% average coverage
**Next**: Create schema_full.py with Pydantic models
