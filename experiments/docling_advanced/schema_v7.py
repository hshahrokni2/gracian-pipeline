#!/usr/bin/env python3
"""
Pydantic models for the Swedish housing association (BRF) annual report extraction.
Includes detailed structures and confidence/source tracking.
Schema Version: 7.0 (Merged Gracian + ZeldaDemo with Swedish-first pattern)

Major enhancements in v7.0:
- Enhanced ExtractionField with evidence tracking (evidence_pages, extraction_method, model_used, etc.)
- Swedish-first semantic fields (årsavgift_per_sqm_total → annual_fee_per_sqm alias)
- Tolerant 3-tier validation (valid/warning/error) with dynamic tolerance functions
- Specialized note structures (BuildingDetails, ReceivablesBreakdown)
- Complete support for 501-field extraction (architecture complete)

Maintained from v6.0:
- Dynamic multi-year financial data (no hardcoded years)
- Calculated financial metrics with automatic validation
- Cross-field validation to catch LLM extraction errors
- Support for any number of years (2-10+ years)
- Handles various Swedish number and date formats
- Automatic anomaly detection

Merge attribution:
- Foundation: ZeldaDemo schema.py v6.0 (production-tested)
- Enhancements: Gracian brf_schema.py (Swedish-first, tolerant validation, specialized notes)
- Created: October 13, 2025 - Phase 1 Week 2 Day 1
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any, Tuple
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator, model_validator
from datetime import datetime
import re

# --- Base Field Types ---

class ConfidenceEnum(str, Enum):
    """Confidence level for extracted data."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationResult(str, Enum):
    """
    Validation result for tolerant 3-tier validation.

    Version 7.0 enhancement for quality assurance:
    - VALID: Field passes validation with high confidence
    - WARNING: Field has minor issues but is usable (e.g., within tolerance)
    - ERROR: Field fails validation (e.g., out of bounds, type mismatch)
    - UNKNOWN: Field not validated yet (default state)
    """
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class ExtractionField(BaseModel):
    """
    Base model for extraction fields with confidence and source tracking.

    Version 7.0 enhancements:
    - Enhanced evidence tracking (evidence_pages, extraction_method, model_used)
    - Validation status (valid/warning/error for tolerant validation)
    - Alternative values (for multi-source extraction)
    - Extraction timestamp (for tracking when field was extracted)
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    # Core fields (from v6.0)
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    source: Optional[str] = None

    # Enhanced evidence tracking (from Gracian brf_schema.py)
    evidence_pages: List[int] = Field(
        default_factory=list,
        description="List of page numbers where this field was found (1-indexed)"
    )
    extraction_method: Optional[str] = Field(
        None,
        description="Method used: 'table_extraction', 'text_extraction', 'calculated', 'manual'"
    )
    model_used: Optional[str] = Field(
        None,
        description="Model/tool used: 'gpt-4o', 'gpt-4o-mini', 'docling', 'gemini-2.5-pro', 'manual'"
    )

    # Validation status (for tolerant 3-tier validation)
    validation_status: Optional[str] = Field(
        None,
        description="Validation result: 'valid', 'warning', 'error', 'unknown'"
    )

    # Alternative values (for multi-source extraction and conflict resolution)
    alternative_values: List[Any] = Field(
        default_factory=list,
        description="Alternative values found from other sources (for comparison)"
    )

    # Extraction timestamp
    extraction_timestamp: Optional[datetime] = Field(
        None,
        description="When this field was extracted (UTC)"
    )

class StringField(ExtractionField):
    value: Optional[str] = None

class NumberField(ExtractionField):
    value: Optional[Union[float, str]] = None  # Allow string or float

    def model_dump(self, *args, **kwargs):
        dump = super().model_dump(*args, **kwargs)
        val = dump.get('value')
        if isinstance(val, float) and val == int(val):
            dump['value'] = str(int(val))  # 14460.0 → "14460"
        elif isinstance(val, float):
            dump['value'] = str(val).rstrip('0').rstrip('.')  # Clean decimals
        elif isinstance(val, str) and val.endswith('.0'):
            dump['value'] = val[:-2]  # "14460.0" → "14460"
        return dump

class IntegerField(ExtractionField):
    value: Optional[int] = None

class BooleanField(ExtractionField):
    value: Optional[bool] = None

class DateField(ExtractionField):
    """Enhanced date field with automatic format handling."""
    value: Optional[str] = None  # Store as ISO string (YYYY-MM-DD)

class ListField(ExtractionField):
    """Enhanced list field for multi-value extraction."""
    value: Optional[List[Any]] = Field(default_factory=list)

class DictField(ExtractionField):
    """Enhanced dictionary field for structured data."""
    value: Optional[Dict[str, Any]] = Field(default_factory=dict)

# --- Added V2: Enum for Interest Rate Type ---
class InterestRateTypeEnum(str, Enum):
    """Type of interest rate."""
    FIXED = "fixed"         # Bunden ränta
    VARIABLE = "variable"   # Rörlig ränta
    UNKNOWN = "unknown"     # Okänd eller ej specificerad

# --- Added V2: Enum for Auditor Role ---
class AuditorRoleEnum(str, Enum):
    """Type of auditor role."""
    INTERNAL = "internal" # Föreningsvald revisor
    EXTERNAL = "external" # Extern / HSB utsedd etc
    UNKNOWN = "unknown"

# --- NEW IN V6: Dynamic Multi-Year Financial Data Models ---

class YearlyFinancialData(BaseModel):
    """
    Financial data for a single year - completely dynamic, no hardcoded years.

    Version 7.0 enhancement: Swedish-first semantic fields with English aliases.
    - Swedish field names match source document terminology exactly
    - English aliases provided for backward compatibility
    - @model_validator automatically syncs Swedish ↔ English
    """
    year: int = Field(..., description="The fiscal year")

    # Store ALL metrics as optional - different reports have different fields
    metrics: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Dynamic metric storage - any metric name can be stored"
    )

    # ✅ NEW IN V7.0: Swedish-first fields with English aliases
    # These match Swedish BRF terminology exactly, with backward-compatible English aliases

    # Raw totals (from source documents)
    nettoomsättning_tkr: Optional[float] = Field(None, description="Nettoomsättning (net revenue) in thousands SEK")
    tillgångar_tkr: Optional[float] = Field(None, description="Tillgångar (total assets) in SEK")
    skulder_tkr: Optional[float] = Field(None, description="Skulder (total liabilities) in SEK")
    eget_kapital_tkr: Optional[float] = Field(None, description="Eget kapital (total equity) in SEK")
    kostnader_tkr: Optional[float] = Field(None, description="Kostnader (total expenses) in SEK")
    resultat_efter_finansiella_tkr: Optional[float] = Field(None, description="Resultat efter finansiella poster (result after financial items) in thousands SEK")

    # Building/property data (raw from source)
    antal_lägenheter: Optional[int] = Field(None, description="Antal lägenheter (number of apartments)")
    byggår: Optional[int] = Field(None, description="Byggår (built year)")
    fastighet_beteckning: Optional[str] = Field(None, description="Fastighetsbeteckning (property designation)")
    total_area_sqm: Optional[float] = Field(None, description="Total area in square meters")
    boyta_sqm: Optional[float] = Field(None, description="Boyta (residential area) in square meters")

    # Calculated per-sqm metrics (derived from raw totals)
    soliditet_procent: Optional[float] = Field(None, ge=0, le=100, description="Soliditet (equity ratio) in percent")
    årsavgift_per_kvm: Optional[float] = Field(None, description="Årsavgift (annual fee) per square meter")
    skuld_per_kvm_total: Optional[float] = Field(None, description="Skuld (debt) per square meter - total area")
    skuld_per_kvm_boyta: Optional[float] = Field(None, description="Skuld (debt) per square meter - residential area (boyta)")
    räntekänslighet_procent: Optional[float] = Field(None, ge=0, description="Räntekänslighet (interest sensitivity) in percent")
    energikostnad_per_kvm: Optional[float] = Field(None, ge=0, description="Energikostnad (energy cost) per square meter")
    avsättning_per_kvm: Optional[float] = Field(None, description="Avsättning (savings/allocation) per square meter")
    årsavgift_andel_intäkter_procent: Optional[float] = Field(None, ge=0, le=100, description="Årsavgift as percentage of total intäkter (revenue)")

    # English aliases (backward compatibility) - populated automatically by @model_validator
    # Raw totals aliases
    net_revenue_tkr: Optional[float] = Field(None, description="[Alias] → nettoomsättning_tkr")
    total_assets_tkr: Optional[float] = Field(None, description="[Alias] → tillgångar_tkr")
    total_liabilities_tkr: Optional[float] = Field(None, description="[Alias] → skulder_tkr")
    total_equity_tkr: Optional[float] = Field(None, description="[Alias] → eget_kapital_tkr")
    total_expenses_tkr: Optional[float] = Field(None, description="[Alias] → kostnader_tkr")
    result_after_financial_tkr: Optional[float] = Field(None, description="[Alias] → resultat_efter_finansiella_tkr")

    # Property/building aliases
    number_of_apartments: Optional[int] = Field(None, description="[Alias] → antal_lägenheter")
    built_year: Optional[int] = Field(None, description="[Alias] → byggår")
    property_designation: Optional[str] = Field(None, description="[Alias] → fastighet_beteckning")

    # Per-sqm metrics aliases
    solidarity_percent: Optional[float] = Field(None, description="[Alias] → soliditet_procent")
    annual_fee_per_kvm: Optional[float] = Field(None, description="[Alias] → årsavgift_per_kvm")
    debt_per_total_kvm: Optional[float] = Field(None, description="[Alias] → skuld_per_kvm_total")
    debt_per_residential_kvm: Optional[float] = Field(None, description="[Alias] → skuld_per_kvm_boyta")
    interest_sensitivity_percent: Optional[float] = Field(None, description="[Alias] → räntekänslighet_procent")
    energy_cost_per_kvm: Optional[float] = Field(None, description="[Alias] → energikostnad_per_kvm")
    savings_per_kvm: Optional[float] = Field(None, description="[Alias] → avsättning_per_kvm")
    annual_fees_percent_of_revenue: Optional[float] = Field(None, description="[Alias] → årsavgift_andel_intäkter_procent")
    
    # Metadata about this year's data
    is_complete: bool = Field(False, description="Whether this year has complete data")
    is_partial: bool = Field(False, description="Whether this year has partial data")
    is_forecast: bool = Field(False, description="Whether this is forecast/budget data")
    data_source: Optional[str] = Field(None, description="Source table/section in PDF")
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1)

    @model_validator(mode='after')
    def sync_swedish_english_fields(self):
        """
        Automatically sync Swedish ↔ English field values for backward compatibility.

        Version 7.0 enhancement: Bidirectional synchronization
        - If Swedish field is set, populate English alias
        - If English field is set, populate Swedish primary
        - This ensures backward compatibility with v6.0 code
        """
        # Define Swedish → English mappings
        field_pairs = [
            # Raw totals
            ('nettoomsättning_tkr', 'net_revenue_tkr'),
            ('tillgångar_tkr', 'total_assets_tkr'),
            ('skulder_tkr', 'total_liabilities_tkr'),
            ('eget_kapital_tkr', 'total_equity_tkr'),
            ('kostnader_tkr', 'total_expenses_tkr'),
            ('resultat_efter_finansiella_tkr', 'result_after_financial_tkr'),
            # Property/building data
            ('antal_lägenheter', 'number_of_apartments'),
            ('byggår', 'built_year'),
            ('fastighet_beteckning', 'property_designation'),
            # Per-sqm metrics
            ('soliditet_procent', 'solidarity_percent'),
            ('årsavgift_per_kvm', 'annual_fee_per_kvm'),
            ('skuld_per_kvm_total', 'debt_per_total_kvm'),
            ('skuld_per_kvm_boyta', 'debt_per_residential_kvm'),
            ('räntekänslighet_procent', 'interest_sensitivity_percent'),
            ('energikostnad_per_kvm', 'energy_cost_per_kvm'),
            ('avsättning_per_kvm', 'savings_per_kvm'),
            ('årsavgift_andel_intäkter_procent', 'annual_fees_percent_of_revenue'),
        ]

        for swedish, english in field_pairs:
            swedish_val = getattr(self, swedish, None)
            english_val = getattr(self, english, None)

            # Priority: Swedish primary → English alias
            if swedish_val is not None and english_val is None:
                setattr(self, english, swedish_val)
            # Backward compatibility: English → Swedish
            elif english_val is not None and swedish_val is None:
                setattr(self, swedish, english_val)

        return self

    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        """Basic sanity check - but flexible for historical reports."""
        current_year = datetime.now().year
        # Allow historical reports going back to 1900, future projections up to 10 years
        if v < 1900 or v > current_year + 10:
            raise ValueError(f'Year {v} seems unrealistic (expected 1900-{current_year+10})')
        return v
    
    def add_metric(self, name: str, value: Optional[float]):
        """Add any metric dynamically."""
        # Normalize metric names to handle variations
        normalized_name = name.lower().replace(' ', '_').replace('/', '_per_')
        self.metrics[normalized_name] = value
        
        # Also set dedicated fields if they match
        field_mapping = {
            'net_revenue_tkr': ['nettoomsättning', 'net_revenue', 'intäkter'],
            'result_after_financial_tkr': ['resultat_efter_finansiella', 'årets_resultat'],
            'solidarity_percent': ['soliditet', 'equity_ratio'],
            'annual_fee_per_kvm': ['årsavgift_kr_kvm', 'avgift_per_kvm'],
            'debt_per_total_kvm': ['skuld_kr_kvm', 'lån_kr_m2'],
            'debt_per_residential_kvm': ['skuld_per_boyta', 'lån_per_boyta']
        }
        
        for field, variants in field_mapping.items():
            if any(variant in normalized_name for variant in variants):
                setattr(self, field, value)
    
    def get_metric(self, name: str) -> Optional[float]:
        """Get a metric by name, checking both dedicated fields and dynamic storage."""
        # Check dedicated fields first
        if hasattr(self, name):
            value = getattr(self, name)
            if value is not None:
                return value
        
        # Check dynamic metrics
        normalized_name = name.lower().replace(' ', '_').replace('/', '_per_')
        return self.metrics.get(normalized_name)
    
    def count_populated_metrics(self) -> int:
        """Count how many metrics have values."""
        count = 0
        # Count dedicated fields
        for field in ['net_revenue_tkr', 'result_after_financial_tkr', 
                     'solidarity_percent', 'annual_fee_per_kvm', 
                     'debt_per_total_kvm', 'debt_per_residential_kvm']:
            if getattr(self, field) is not None:
                count += 1
        # Count additional dynamic metrics
        count += len([v for v in self.metrics.values() if v is not None])
        return count

class DynamicMultiYearOverview(BaseModel):
    """
    Completely dynamic multi-year container.
    No assumptions about which years or how many years.
    Replaces the simple DataTable for multi_year_overview.
    """
    
    # Store years as a list, sorted dynamically
    years_data: List[YearlyFinancialData] = Field(
        default_factory=list,
        description="All years of data, automatically sorted"
    )
    
    # Metadata
    report_year: Optional[int] = Field(
        None,
        description="The year this report was published (not necessarily the latest data year)"
    )
    earliest_year: Optional[int] = Field(None, description="Earliest year with data")
    latest_year: Optional[int] = Field(None, description="Latest year with data")
    total_years: int = Field(0, description="Total number of years with data")
    
    # Dynamic metric tracking
    available_metrics: List[str] = Field(
        default_factory=list,
        description="List of all metrics found across any year"
    )
    
    # Table structure detection
    table_format: Optional[str] = Field(
        None,
        description="Detected table format: 'horizontal_years', 'vertical_years', 'mixed'"
    )
    
    @model_validator(mode='after')
    def update_metadata(self):
        """Update metadata whenever data changes."""
        if self.years_data:
            # Sort years
            self.years_data = sorted(self.years_data, key=lambda x: x.year, reverse=True)
            
            # Update metadata
            self.latest_year = self.years_data[0].year
            self.earliest_year = self.years_data[-1].year
            self.total_years = len(self.years_data)
            
            # Collect all unique metrics
            all_metrics = set()
            for year_data in self.years_data:
                # Add dedicated field names if populated
                for field in ['net_revenue_tkr', 'result_after_financial_tkr',
                             'solidarity_percent', 'annual_fee_per_kvm',
                             'debt_per_total_kvm', 'debt_per_residential_kvm']:
                    if getattr(year_data, field) is not None:
                        all_metrics.add(field)
                # Add dynamic metrics
                all_metrics.update(year_data.metrics.keys())
            
            self.available_metrics = sorted(list(all_metrics))
        
        return self
    
    def add_year(self, year: int, auto_create: bool = True) -> YearlyFinancialData:
        """
        Add or get a year's data container.
        Creates it if it doesn't exist and auto_create is True.
        """
        # Check if year already exists
        for year_data in self.years_data:
            if year_data.year == year:
                return year_data
        
        if auto_create:
            # Create new year
            new_year = YearlyFinancialData(year=year)
            self.years_data.append(new_year)
            self.update_metadata()
            return new_year
        
        return None
    
    def get_year(self, year: int) -> Optional[YearlyFinancialData]:
        """Get data for a specific year."""
        for year_data in self.years_data:
            if year_data.year == year:
                return year_data
        return None
    
    def get_latest_n_years(self, n: int) -> List[YearlyFinancialData]:
        """Get the latest N years of data."""
        sorted_years = sorted(self.years_data, key=lambda x: x.year, reverse=True)
        return sorted_years[:n]
    
    def calculate_metric_changes(self, metric_name: str) -> List[Dict[str, Any]]:
        """
        Calculate year-over-year changes for any metric.
        Works with both dedicated fields and dynamic metrics.
        """
        changes = []
        sorted_years = sorted(self.years_data, key=lambda x: x.year)
        
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i-1]
            curr_year = sorted_years[i]
            
            prev_value = prev_year.get_metric(metric_name)
            curr_value = curr_year.get_metric(metric_name)
            
            if prev_value is not None and curr_value is not None and prev_value != 0:
                change_abs = curr_value - prev_value
                change_pct = (change_abs / abs(prev_value)) * 100
                
                changes.append({
                    'from_year': prev_year.year,
                    'to_year': curr_year.year,
                    'from_value': prev_value,
                    'to_value': curr_value,
                    'change_absolute': change_abs,
                    'change_percent': round(change_pct, 1)
                })
        
        return changes
    
    def find_anomalies(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find suspicious year-over-year changes (> threshold, default 50%).
        """
        anomalies = []
        
        for metric in self.available_metrics:
            changes = self.calculate_metric_changes(metric)
            for change in changes:
                if abs(change['change_percent']) > threshold * 100:
                    anomalies.append({
                        'metric': metric,
                        'from_year': change['from_year'],
                        'to_year': change['to_year'],
                        'change_percent': change['change_percent'],
                        'severity': 'high' if abs(change['change_percent']) > 100 else 'medium'
                    })
        
        return anomalies
    
    def validate_consistency(self) -> List[str]:
        """Check for data consistency issues across years."""
        issues = []
        all_years = self.years_data
        
        if len(all_years) >= 2:
            sorted_years = sorted(all_years, key=lambda x: x.year)
            
            for i in range(1, len(sorted_years)):
                curr = sorted_years[i]
                prev = sorted_years[i-1]
                
                # Check for unrealistic jumps in key metrics
                if curr.annual_fee_per_kvm and prev.annual_fee_per_kvm:
                    change = abs(curr.annual_fee_per_kvm - prev.annual_fee_per_kvm) / prev.annual_fee_per_kvm
                    if change > 0.5:  # 50% change in one year is suspicious
                        issues.append(f"Large fee change between {prev.year} and {curr.year}: {change*100:.1f}%")
                
                if curr.debt_per_total_kvm and prev.debt_per_total_kvm:
                    change = abs(curr.debt_per_total_kvm - prev.debt_per_total_kvm) / prev.debt_per_total_kvm
                    if change > 0.5:
                        issues.append(f"Large debt change between {prev.year} and {curr.year}: {change*100:.1f}%")
        
        return issues

# --- NEW IN V6: Calculated Financial Metrics with Validation ---

class CalculatedFinancialMetrics(BaseModel):
    """
    Financial metrics with automatic calculation and validation.
    This enhances/replaces the existing FinancialMetrics class.
    """
    
    # Raw input values (from extraction)
    total_debt: Optional[float] = Field(None, ge=0, description="Total debt in SEK")
    total_area_sqm: Optional[float] = Field(None, gt=0, description="Total area in square meters")
    residential_area_sqm: Optional[float] = Field(None, gt=0, description="Residential area in square meters")
    annual_fees_total: Optional[float] = Field(None, ge=0, description="Total annual fees in SEK")
    total_revenue: Optional[float] = Field(None, ge=0, description="Total revenue in SEK")
    total_assets: Optional[float] = Field(None, gt=0, description="Total assets in SEK")
    total_equity: Optional[float] = Field(None, description="Total equity in SEK")
    property_tax_value: Optional[float] = Field(None, ge=0, description="Property tax value in SEK")
    energy_costs_total: Optional[float] = Field(None, ge=0, description="Total energy costs in SEK")
    interest_costs_total: Optional[float] = Field(None, ge=0, description="Total interest costs in SEK")
    maintenance_fund_balance: Optional[float] = Field(None, ge=0, description="Maintenance fund balance in SEK")
    
    # Calculated metrics (auto-calculated or validated if provided)
    debt_per_sqm_total: Optional[float] = Field(None, description="Calculated: Total debt / Total area")
    debt_per_sqm_residential: Optional[float] = Field(None, description="Calculated: Total debt / Residential area")
    annual_fee_per_sqm: Optional[float] = Field(None, description="Calculated: Annual fees / Total area")
    solidarity_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Calculated: (Equity / Assets) * 100", alias="soliditet_percent"
    )
    loan_to_value_ratio: Optional[float] = Field(None, ge=0, description="Calculated: Total debt / Property tax value")
    annual_fees_percent_of_revenue: Optional[float] = Field(None, ge=0, le=100, description="Calculated: (Annual fees / Revenue) * 100")
    energy_cost_per_sqm: Optional[float] = Field(None, ge=0, description="Calculated: Energy costs / Total area")
    interest_coverage_ratio: Optional[float] = Field(None, description="Calculated: (Revenue - Operating costs) / Interest costs")
    interest_sensitivity_percent: Optional[float] = Field(None, ge=0, description="What % interest rate increase doubles interest costs")
    
    # Savings metric (complex calculation)
    savings_per_sqm: Optional[float] = Field(None, description="Complex metric: (Net income + Depreciation - Maintenance allocation) / Area")
    
    # All other metrics from original FinancialMetrics (for backward compatibility)
    average_interest_rate_reported: Optional[str] = None
    energy_consumption_kwh_per_sqm: Optional[float] = None
    annual_fee_change_percent: Optional[str] = None
    loan_amortization_amount: Optional[float] = None
    liquidity_ratio_percent: Optional[float] = None
    heating_cost_per_sqm: Optional[float] = None
    rental_income_premises_per_sqm: Optional[float] = None
    operating_cost_per_sqm: Optional[float] = None
    maintenance_fund_allocation_per_sqm: Optional[float] = None
    debt_to_revenue_ratio: Optional[float] = None
    operating_cost_excl_maintenance_per_sqm: Optional[float] = None
    interest_cost_per_sqm: Optional[float] = None
    maintenance_fund_balance_per_sqm: Optional[float] = None
    debt_ratio: Optional[float] = None
    total_operating_costs: Optional[float] = None
    depreciation_per_sqm_total: Optional[float] = None
    water_cost_per_sqm: Optional[float] = None
    electricity_cost_per_sqm: Optional[float] = None
    
    # Validation tracking
    calculation_errors: List[str] = Field(default_factory=list, description="List of calculation/validation errors")
    calculation_warnings: List[str] = Field(default_factory=list, description="List of calculation/validation warnings")
    
    @model_validator(mode='after')
    def calculate_and_validate_metrics(self):
        """Calculate metrics and validate consistency."""
        
        # Calculate debt per sqm metrics
        if self.total_debt is not None and self.total_area_sqm:
            calculated_debt_total = self.total_debt / self.total_area_sqm
            if self.debt_per_sqm_total is not None:
                # Validate if already provided
                diff = abs(self.debt_per_sqm_total - calculated_debt_total)
                if diff > 100:  # Allow 100 kr/sqm tolerance
                    self.calculation_errors.append(
                        f"Debt per total sqm mismatch: provided {self.debt_per_sqm_total:.0f}, "
                        f"calculated {calculated_debt_total:.0f}"
                    )
            else:
                # Auto-calculate
                self.debt_per_sqm_total = round(calculated_debt_total, 0)
        
        if self.total_debt is not None and self.residential_area_sqm:
            calculated_debt_residential = self.total_debt / self.residential_area_sqm
            if self.debt_per_sqm_residential is not None:
                diff = abs(self.debt_per_sqm_residential - calculated_debt_residential)
                if diff > 100:
                    self.calculation_errors.append(
                        f"Debt per residential sqm mismatch: provided {self.debt_per_sqm_residential:.0f}, "
                        f"calculated {calculated_debt_residential:.0f}"
                    )
            else:
                self.debt_per_sqm_residential = round(calculated_debt_residential, 0)
        
        # Calculate annual fee per sqm
        if self.annual_fees_total is not None and self.total_area_sqm:
            calculated_fee = self.annual_fees_total / self.total_area_sqm
            if self.annual_fee_per_sqm is not None:
                diff = abs(self.annual_fee_per_sqm - calculated_fee)
                if diff > 50:  # Allow 50 kr/sqm tolerance
                    self.calculation_warnings.append(
                        f"Annual fee per sqm mismatch: provided {self.annual_fee_per_sqm:.0f}, "
                        f"calculated {calculated_fee:.0f}"
                    )
            else:
                self.annual_fee_per_sqm = round(calculated_fee, 0)
        
        # Calculate solidarity (equity ratio)
        if self.total_equity is not None and self.total_assets:
            calculated_solidarity = (self.total_equity / self.total_assets) * 100
            if self.solidarity_percent is not None:
                diff = abs(self.solidarity_percent - calculated_solidarity)
                if diff > 2:  # Allow 2% tolerance
                    self.calculation_warnings.append(
                        f"Solidarity % mismatch: provided {self.solidarity_percent:.1f}, "
                        f"calculated {calculated_solidarity:.1f}"
                    )
            else:
                self.solidarity_percent = round(calculated_solidarity, 1)
        
        # Validate area consistency
        if self.total_area_sqm and self.residential_area_sqm:
            if self.residential_area_sqm > self.total_area_sqm:
                self.calculation_errors.append(
                    f"Residential area ({self.residential_area_sqm:.0f}) exceeds total area ({self.total_area_sqm:.0f})"
                )
        
        return self
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of all calculations and validations."""
        return {
            "calculated_metrics": {
                "debt_per_sqm_total": self.debt_per_sqm_total,
                "debt_per_sqm_residential": self.debt_per_sqm_residential,
                "annual_fee_per_sqm": self.annual_fee_per_sqm,
                "solidarity_percent": self.solidarity_percent,
                "loan_to_value_ratio": self.loan_to_value_ratio,
                "energy_cost_per_sqm": self.energy_cost_per_sqm,
                "interest_sensitivity_percent": self.interest_sensitivity_percent,
                "savings_per_sqm": self.savings_per_sqm
            },
            "errors": self.calculation_errors,
            "warnings": self.calculation_warnings,
            "validation_passed": len(self.calculation_errors) == 0
        }

# --- NEW IN V6: Table Extraction Metadata ---

class TableExtractionMetadata(BaseModel):
    """
    Metadata about how the multi-year table was extracted.
    Helps with debugging and quality control.
    """
    source_page: Optional[int] = Field(None, description="Page number in PDF")
    table_title: Optional[str] = Field(None, description="Title of the table if found")
    extraction_method: Optional[str] = Field(None, description="Method used to extract")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    
    # Track what headers/labels were found
    year_headers_found: List[int] = Field(default_factory=list, description="Years found as column/row headers")
    metric_labels_found: List[str] = Field(default_factory=list, description="Metric labels found")
    
    # Track extraction issues
    extraction_warnings: List[str] = Field(default_factory=list)
    cells_skipped: int = Field(0, description="Number of cells that couldn't be parsed")
    
    # Table structure
    table_orientation: Optional[str] = Field(None, description="'years_as_columns' or 'years_as_rows'")
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None

# --- Specific Data Models (keeping all existing) ---

# --- ADDED V5 (from PDF analysis consolidation) ---
class TaxValueBreakdown(BaseModel):
    """Detailed breakdown of property tax values."""
    building_residential: Optional[NumberField] = None
    building_commercial: Optional[NumberField] = None
    land_residential: Optional[NumberField] = None
    land_commercial: Optional[NumberField] = None
    total_building: Optional[NumberField] = None
    total_land: Optional[NumberField] = None
    total: Optional[NumberField] = None
# --- END ADDED V5 ---

# Organization models
class ContactDetails(BaseModel):
    phone: Optional[StringField] = None
    email: Optional[StringField] = None
    website: Optional[StringField] = None

class Organization(BaseModel):
    organization_name: Optional[StringField] = None
    organization_number: Optional[StringField] = None
    registered_office: Optional[StringField] = None
    association_statutes: Optional[StringField] = None
    association_tax_status: Optional[StringField] = None
    contact_details: Optional[ContactDetails] = None
    # --- ADDED V2 ---
    agm_date: Optional[StringField] = Field(default=None, description="Date the Annual General Meeting (Årsstämma) was held")
    # --- END ADDED V2 ---
    # --- ADDED V3 ---
    management_company: Optional[StringField] = Field(default=None, description="Name of the company managing the BRF")
    number_of_members: Optional[IntegerField] = Field(default=None, description="Number of members in the association at year end")
    # --- END ADDED V3 ---
    # --- ADDED V4 (from PDF analyses) ---
    economic_plan_registration_date: Optional[StringField] = Field(default=None, description="Date the current economic plan was registered")
    affiliations: List[StringField] = Field(default_factory=list, description="List of organizations the BRF is affiliated with (e.g., Bostadsrätterna)")
    transfer_fee_details: Optional[StringField] = Field(default=None, description="Details about transfer fees (överlåtelseavgift)")
    pledge_fee_details: Optional[StringField] = Field(default=None, description="Details about pledge fees (pantsättningsavgift)")
    number_of_employees: Optional[IntegerField] = Field(default=None, description="Number of employees in the association")
    registration_date_association: Optional[StringField] = Field(default=None, description="Date the BRF was initially registered (e.g., '1968-09-19')")
    registration_date_economic_plan: Optional[StringField] = Field(default=None, description="Date the current economic plan was registered (e.g., '1986-11-04')") # Note: Duplicate name, retained for potential different sources/values
    registration_date_statutes: Optional[StringField] = Field(default=None, description="Date the current statutes were registered (e.g., '2023-06-13')")
    brf_registration_date: Optional[StringField] = Field(default=None, description="Date the BRF was registered") # Note: Similar to registration_date_association
    # --- END ADDED V4 ---
    # --- ADDED V5 (from PDF analysis consolidation) ---
    is_genuine_association: Optional[BooleanField] = Field(default=None, description="Indicates if the association is classified as 'äkta' (genuine)")
    extra_agm_date: Optional[StringField] = Field(default=None, description="Date the Extra Annual General Meeting (Extra Årsstämma) was held")
    board_signing_location: Optional[StringField] = Field(default=None, description="Location where the board signed the annual report (e.g., Stockholm)")
    auditor_signing_location: Optional[StringField] = Field(default=None, description="Location where the auditor signed their report (e.g., Malmö)")
    number_of_agm_attendees: Optional[IntegerField] = Field(default=None, description="Number of voting members present at the Annual General Meeting")
    number_of_apartment_transfers_current_year: Optional[IntegerField] = Field(default=None, description="Number of apartments transferred/sold during the fiscal year")
    # --- END ADDED V5 ---


# Property details models
class AddressComponent(BaseModel):
    street: Optional[StringField] = None
    number: Optional[StringField] = None
    postal_code: Optional[StringField] = None
    municipality: Optional[StringField] = None

class ApartmentDistribution(BaseModel):
    studio: Optional[IntegerField] = None
    one_bedroom: Optional[IntegerField] = None
    # --- ADDED V5 (from PDF analysis consolidation) ---
    one_and_half_bedroom: Optional[IntegerField] = Field(default=None, description="Number of 1.5 room apartments (1.5 RoK)")
    # --- END ADDED V5 ---
    two_bedroom: Optional[IntegerField] = None
    three_bedroom: Optional[IntegerField] = None
    # --- ADDED V5 (from PDF analysis consolidation) ---
    three_and_half_bedroom: Optional[IntegerField] = Field(default=None, description="Number of 3.5 room apartments (3.5 RoK)")
    # --- END ADDED V5 ---
    four_plus_bedroom: Optional[IntegerField] = None

class CommercialRental(BaseModel):
    type: Optional[StringField] = None
    area_sqm: Optional[NumberField] = None
    annual_rent: Optional[NumberField] = None

class JointFacilityItem(BaseModel):
     name: Optional[StringField] = None
     description: Optional[StringField] = None
     ownership_percentage: Optional[NumberField] = None
     # --- ADDED V5 (from PDF analysis consolidation) ---
     organization_number: Optional[StringField] = Field(default=None, description="Organization number for the joint facility if it's a separate legal entity")
     # --- END ADDED V5 ---

class PropertyDetails(BaseModel):
    property_designation: Optional[StringField] = None
    address: Optional[StringField] = None
    address_components: Optional[AddressComponent] = None
    total_area_sqm: Optional[NumberField] = None
    residential_area_sqm: Optional[NumberField] = None
    commercial_area_sqm: Optional[NumberField] = None
    # --- ADDED V4 (from PDF analyses) ---
    total_land_area_sqm: Optional[NumberField] = Field(default=None, description="Total land area in square meters (Tomtarea)")
    number_of_parking_spaces: Optional[IntegerField] = Field(default=None, description="Number of parking spaces belonging to the BRF")
    parking_spaces_rental_info: Optional[StringField] = Field(default=None, description="Information about how parking spaces are rented (e.g., to members, externally)")
    number_of_commercial_units: Optional[IntegerField] = Field(default=None, description="Number of commercial units/premises (lokaler)")
    number_of_buildings: Optional[IntegerField] = Field(default=None, description="Number of buildings the property consists of (e.g., 12 flerbostadshus)")
    valuation_year: Optional[StringField] = Field(default=None, description="The valuation year (värdeår) of the property, can differ from year_built")
    book_value_of_land: Optional[NumberField] = Field(default=None, description="Book value of land included in the total book value of property (Byggnad och mark)")
    acquisition_year: Optional[StringField] = Field(default=None, description="Year the property was acquired by the BRF (Förvärvsår)")
    # --- END ADDED V4 ---
    # --- ADDED V5 (from PDF analysis consolidation) ---
    fire_insurance_value: Optional[StringField] = Field(default=None, description="Stated value for fire insurance (e.g., Fullvärde)")
    is_listed_building: Optional[BooleanField] = Field(default=None, description="Indicates if the property is a listed building ('byggnadsminnesförklarad')")
    tax_value_breakdown: Optional[TaxValueBreakdown] = Field(default=None, description="Detailed breakdown of tax values if provided")
    number_of_garage_spaces: Optional[IntegerField] = Field(default=None, description="Number of garage spaces owned/rented out by the BRF")
    garage_rental_fee_description: Optional[StringField] = Field(default=None, description="Textual description of garage rental fees, possibly including changes")
    number_of_storage_units: Optional[IntegerField] = Field(default=None, description="Number of storage units (förråd) belonging to the BRF")
    # --- END ADDED V5 ---
    number_of_apartments: Optional[IntegerField] = None
    # --- ADDED V2 ---
    number_of_rental_apartments: Optional[IntegerField] = Field(default=None, description="Number of apartments that are rentals (hyresrätter)")
    # --- END ADDED V2 ---
    apartment_distribution: Optional[ApartmentDistribution] = None
    commercial_rentals: List[CommercialRental] = Field(default_factory=list)
    year_built: Optional[StringField] = None # Construction year(s)
    tax_value: Optional[NumberField] = None # Total tax value
    joint_facilities: List[JointFacilityItem] = Field(default_factory=list)
    # --- ADDED V1 ---
    property_tenure: Optional[StringField] = Field(default=None, description="Type of property tenure (e.g., Tomträtt, Äganderätt)")
    property_insurance_provider: Optional[StringField] = Field(default=None, description="Company providing property insurance")
    # --- END ADDED V1 ---

# Financial report models
class BalanceSheetItem(BaseModel):
    item: Optional[StringField] = None
    amount_current_year: Optional[NumberField] = None
    amount_previous_year: Optional[NumberField] = None
    # --- ADDED V1 ---
    note_reference: Optional[StringField] = Field(default=None, description="Reference number(s) to a note explaining the item (e.g., '2', '11, 16')")
    # --- END ADDED V1 ---

class FixedAssets(BaseModel):
    tangible: List[BalanceSheetItem] = Field(default_factory=list)
    financial: List[BalanceSheetItem] = Field(default_factory=list)
    total_fixed_assets: Optional[NumberField] = None

class CurrentAssets(BaseModel):
    short_term_receivables: List[BalanceSheetItem] = Field(default_factory=list)
    short_term_investments: List[BalanceSheetItem] = Field(default_factory=list)
    cash_and_bank: Optional[NumberField] = None
    total_current_assets: Optional[NumberField] = None

class AssetsDetailed(BaseModel):
    fixed_assets: Optional[FixedAssets] = None
    current_assets: Optional[CurrentAssets] = None
    total_assets: Optional[NumberField] = None
    # --- ADDED V1 ---
    pledged_assets_amount: Optional[NumberField] = Field(default=None, description="Total amount of pledged assets/mortgages (Ställda säkerheter/Pantbrev)")
    # --- END ADDED V1 ---
    # --- ADDED V6.1 (for better breakdown tracking) ---
    fixed_assets_total: Optional[NumberField] = Field(default=None, description="Total fixed assets value")
    current_assets_total: Optional[NumberField] = Field(default=None, description="Total current assets value")
    # --- END ADDED V6.1 ---

class BoundEquity(BaseModel):
    items: List[BalanceSheetItem] = Field(default_factory=list)
    total_bound_equity: Optional[NumberField] = None

class FreeEquity(BaseModel):
    items: List[BalanceSheetItem] = Field(default_factory=list)
    total_free_equity: Optional[NumberField] = None

class EquityDetailed(BaseModel):
    bound_equity: Optional[BoundEquity] = None
    free_equity: Optional[FreeEquity] = None
    total_equity: Optional[NumberField] = None
    # --- ADDED V6.1 (for better equity tracking) ---
    equity_breakdown_retained: Optional[NumberField] = Field(default=None, description="Retained earnings portion of equity")
    equity_breakdown_reserves: Optional[NumberField] = Field(default=None, description="Reserve funds portion of equity")
    # --- END ADDED V6.1 ---

class LiabilitiesDetailed(BaseModel):
    long_term_liabilities_items: List[BalanceSheetItem] = Field(default_factory=list)
    total_long_term_liabilities: Optional[NumberField] = None
    short_term_liabilities_items: List[BalanceSheetItem] = Field(default_factory=list)
    total_short_term_liabilities: Optional[NumberField] = None
    total_liabilities: Optional[NumberField] = None
    # --- ADDED V5 (from PDF analysis consolidation) ---
    total_loans_credit_institutions: Optional[NumberField] = Field(default=None, description="Total debt to credit institutions")
    loans_due_within_1_year: Optional[NumberField] = Field(default=None, description="Portion of loans to credit institutions due within 1 year")
    loans_due_1_to_5_years: Optional[NumberField] = Field(default=None, description="Portion of loans to credit institutions due between 1 and 5 years")
    loans_due_after_5_years: Optional[NumberField] = Field(default=None, description="Portion of loans to credit institutions due after 5 years")
    # --- END ADDED V5 ---
    # --- ADDED V6.1 (for tracking from clean validation) ---
    current_liabilities: Optional[NumberField] = Field(default=None, description="Total current/short-term liabilities")
    # --- END ADDED V6.1 ---

class BalanceSheet(BaseModel):
    report_date: Optional[StringField] = None
    assets: Optional[AssetsDetailed] = None
    equity: Optional[EquityDetailed] = None
    liabilities: Optional[LiabilitiesDetailed] = None
    total_equity_and_liabilities: Optional[NumberField] = None

class RevenueBreakdown(BaseModel):
    annual_fees: Optional[NumberField] = None
    rental_income: Optional[NumberField] = None
    other_income: Optional[NumberField] = None

class ExpenseBreakdown(BaseModel):
    electricity: Optional[NumberField] = None
    heating: Optional[NumberField] = None
    water_and_sewage: Optional[NumberField] = None
    waste_management: Optional[NumberField] = None
    property_maintenance: Optional[NumberField] = None
    repairs: Optional[NumberField] = None
    maintenance: Optional[NumberField] = None
    property_tax: Optional[NumberField] = None
    property_insurance: Optional[NumberField] = None
    cable_tv_internet: Optional[NumberField] = None
    board_costs: Optional[NumberField] = None
    management_fees: Optional[NumberField] = None
    other_operating_costs: Optional[NumberField] = None
    financial_costs: Optional[NumberField] = None
    depreciation: Optional[NumberField] = None
    # --- ADDED V2 ---
    audit_fees: Optional[NumberField] = Field(default=None, description="Audit fees (Revisionsarvoden)")
    # --- END ADDED V2 ---
    # --- ADDED V4 (from PDF analyses) ---
    planned_maintenance_cost: Optional[NumberField] = Field(default=None, description="Costs for 'Planerade underhåll' expensed during the current year, if detailed separately from other maintenance/repairs.")
    # --- END ADDED V4 ---
    # --- ADDED V5 (from PDF analysis consolidation) ---
    ground_rent_fee: Optional[NumberField] = Field(default=None, description="Ground rent fee (Tomträttsavgäld)")
    maintenance_and_repairs_total: Optional[NumberField] = Field(default=None, description="Total cost for maintenance and repairs, if combined (e.g. 'Underhåll och reparationer')")
    # --- END ADDED V5 ---
    # --- ADDED V6.1 (from clean validation report) ---
    snow_removal_costs: Optional[NumberField] = Field(default=None, description="Snow removal and winter maintenance costs")
    garden_maintenance_costs: Optional[NumberField] = Field(default=None, description="Garden and yard maintenance costs")
    elevator_maintenance: Optional[NumberField] = Field(default=None, description="Elevator service and maintenance costs")
    security_costs: Optional[NumberField] = Field(default=None, description="Security services and alarm system costs")
    admin_costs: Optional[NumberField] = Field(default=None, description="Administrative costs not covered by management fees")
    cleaning_costs: Optional[NumberField] = Field(default=None, description="Cleaning and janitorial service costs")
    # --- END ADDED V6.1 ---

class IncomeStatementItem(BaseModel):
    item: Optional[StringField] = None
    amount_current_year: Optional[NumberField] = None
    amount_previous_year: Optional[NumberField] = None
    # --- ADDED V1 ---
    note_reference: Optional[StringField] = Field(default=None, description="Reference number(s) to a note explaining the item")
    # --- END ADDED V1 ---

class IncomeStatement(BaseModel):
    items: List[IncomeStatementItem] = Field(default_factory=list)
    revenue: Optional[NumberField] = None
    expenses: Optional[NumberField] = None
    net_income: Optional[NumberField] = None
    revenue_breakdown: Optional[RevenueBreakdown] = None
    expense_breakdown: Optional[ExpenseBreakdown] = None
    previous_year_revenue: Optional[NumberField] = None
    previous_year_expenses: Optional[NumberField] = None
    previous_year_net_income: Optional[NumberField] = None
    previous_year_revenue_breakdown: Optional[RevenueBreakdown] = None
    previous_year_expense_breakdown: Optional[ExpenseBreakdown] = None

class FinancialReport(BaseModel):
    annual_report_year: Optional[StringField] = None
    balance_sheet: Optional[BalanceSheet] = None
    income_statement: Optional[IncomeStatement] = None

# Keep old FinancialMetrics for backward compatibility
class FinancialMetrics(CalculatedFinancialMetrics):
    """Alias for backward compatibility. Use CalculatedFinancialMetrics for new code."""
    pass

# Loan models
class Loan(BaseModel):
    lender: Optional[StringField] = None
    loan_number: Optional[StringField] = None
    amount: Optional[NumberField] = None
    interest_rate: Optional[NumberField] = None # General interest rate if specified broadly
    # --- MODIFIED V2 ---
    interest_rate_type: Optional[InterestRateTypeEnum] = Field(default=None, description="Type of interest rate (fixed or variable)")
    # --- END MODIFIED V2 ---
    maturity_date: Optional[StringField] = None
    # --- ADDED V1 ---
    interest_rate_at_year_end: Optional[NumberField] = Field(default=None, description="Interest rate percentage specifically on the report date")
    # --- END ADDED V1 ---
    # --- ADDED V2 ---
    next_year_amortization: Optional[NumberField] = Field(default=None, description="Amortization amount planned for this specific loan in the next fiscal year")
    # --- END ADDED V2 ---
    # --- ADDED V4 (from PDF analyses, including base 53716) ---
    previous_year_amount: Optional[NumberField] = Field(default=None, description="Loan amount at the end of the previous fiscal year")
    interest_rate_condition_change_date: Optional[StringField] = Field(default=None, description="Date when the interest rate conditions for the loan are due to change (Villkorsändringsdag)")
    current_year_amortization: Optional[NumberField] = Field(default=None, description="Amortization amount for this specific loan during the current fiscal year")
    new_or_renegotiated_amount: Optional[NumberField] = Field(default=None, description="Amount of new financing or renegotiated/rolled-over loan during the current fiscal year for this specific loan")
    # --- END ADDED V4 ---
    # --- ADDED V5 (from PDF analysis consolidation) ---
    interest_rate_fixing_period: Optional[StringField] = Field(default=None, description="The period for which the interest rate is fixed (e.g., 3-månader, 2 år)")
    # --- END ADDED V5 ---


# Board models
class BoardMember(BaseModel):
    name: Optional[StringField] = None
    role: Optional[StringField] = None
    elected_until: Optional[StringField] = None
    # --- ADDED V2 / MODIFIED V4 ---
    is_hsb_representative: Optional[BooleanField] = Field(default=None, description="True if this member is appointed by HSB or similar large managing organization like Riksbyggen") # V4 update: broadened description
    # --- END ADDED V2 / MODIFIED V4 ---
    # --- ADDED V5 (from PDF analysis consolidation) ---
    resignation_date: Optional[StringField] = Field(default=None, description="Date the board member resigned, if applicable during the term")
    # --- END ADDED V5 ---
    # --- ADDED V6.1 (from clean validation report) ---
    date_of_birth: Optional[StringField] = Field(default=None, description="Board member's date of birth (e.g., 1948-03-12)")
    signature_timestamp: Optional[StringField] = Field(default=None, description="When they digitally signed the annual report")
    # --- END ADDED V6.1 ---

class AuditorInfo(BaseModel):
    name: Optional[StringField] = None
    company: Optional[StringField] = None
    is_authorized: Optional[BooleanField] = None
    # --- ADDED V2 / MODIFIED V4 ---
    is_hsb_appointed: Optional[BooleanField] = Field(default=None, description="True if this auditor is appointed by HSB Riksförbund or similar") # V4 update: broadened description
    auditor_role: Optional[AuditorRoleEnum] = Field(default=AuditorRoleEnum.UNKNOWN, description="Whether the auditor is internal or external")
    # --- END ADDED V2 / MODIFIED V4 ---

# --- ADDED V2 ---
class NominationCommitteeMember(BaseModel):
    name: Optional[StringField] = None
    # --- ADDED V5 (from PDF analysis consolidation) ---
    role: Optional[StringField] = Field(default=None, description="Role in the nomination committee, e.g., 'Sammankallande'")
    term_notes: Optional[StringField] = Field(default=None, description="Notes regarding the member's term, e.g., resignation details")
    # --- END ADDED V5 ---
# --- END ADDED V2 ---

class Board(BaseModel):
    board_members: List[BoardMember] = Field(default_factory=list)
    auditors: List[AuditorInfo] = Field(default_factory=list)
    # --- ADDED V2 ---
    deputy_auditors: List[AuditorInfo] = Field(default_factory=list, description="List of deputy auditors (revisorssuppleanter)")
    report_signature_date: Optional[StringField] = Field(default=None, description="Date the annual report was signed by the board")
    deputy_board_members: List[BoardMember] = Field(default_factory=list, description="List of deputy board members (styrelsesuppleanter)")
    nomination_committee: List[NominationCommitteeMember] = Field(default_factory=list, description="List of nomination committee members (Valberedning)")
    # --- END ADDED V2 ---
    # --- ADDED V3 ---
    auditor_report_signature_date: Optional[StringField] = Field(default=None, description="Date the auditor's report was signed")
    # --- END ADDED V3 ---
    # --- ADDED V4 (from PDF analyses) ---
    number_of_board_meetings_current_year: Optional[IntegerField] = Field(default=None, description="Number of board meetings held during the fiscal year")
    # --- END ADDED V4 ---
    # --- ADDED V6.1 (from clean validation report) ---
    departed_board_members: List[StringField] = Field(default_factory=list, description="Names of board members who left during the fiscal year")
    property_manager: Optional[StringField] = Field(default=None, description="Name of the property management company or person")
    audit_firm: Optional[StringField] = Field(default=None, description="Name of the audit firm (e.g., HQV Stockholm AB)")
    # --- END ADDED V6.1 ---


# Maintenance models
class MaintenanceAction(BaseModel):
    description: Optional[StringField] = None
    # --- MODIFIED V4 (from PDF analyses) ---
    # Changed type from IntegerField to StringField to accommodate year ranges like '2012-2019'
    year: Optional[StringField] = None # For historical. Was IntegerField.
    planned_year: Optional[StringField] = None # For planned. Was IntegerField. Changed for consistency.
    # --- END MODIFIED V4 ---
    cost: Optional[NumberField] = None # For historical
    estimated_cost: Optional[NumberField] = None # For planned
    # --- ADDED V4 (from PDF analyses) ---
    category: Optional[StringField] = Field(default=None, description="Category of the maintenance action (e.g., Hiss, Fönster, Avlopp)")
    # --- END ADDED V4 ---

class Maintenance(BaseModel):
    historical_actions: List[MaintenanceAction] = Field(default_factory=list)
    planned_actions: List[MaintenanceAction] = Field(default_factory=list)
    renovation_year_facade: Optional[StringField] = None
    renovation_year_roof: Optional[StringField] = None
    renovation_year_pipes: Optional[StringField] = None
    renovation_year_electricity: Optional[StringField] = None
    renovation_year_heating: Optional[StringField] = None
    renovation_year_windows: Optional[StringField] = None
    renovation_year_balconies: Optional[StringField] = None
    # --- ADDED V2 ---
    maintenance_plan_status: Optional[StringField] = Field(default=None, description="Status of the maintenance plan (e.g., 'Upprättad', 'Uppdaterad')")
    # --- END ADDED V2 ---

# Added/Placeholder Models from detailed extraction
class DataTable(BaseModel):
    headers: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    comment: Optional[StringField] = None

# --- MODIFIED V2: Renamed Class & Added/modified fields ---
class ProposedProfitLossTreatment(BaseModel):
    accumulated_profit_loss_brought_forward: Optional[NumberField] = Field(default=None, description="Accumulated profit/loss (Balanserat resultat) brought forward")
    current_year_profit_loss: Optional[NumberField] = Field(default=None, description="Profit or loss for the current year (Årets resultat)")
    # --- ADDED V4 (from PDF 78276 / Base 53716 schema.py) ---
    capital_contribution_for_disposition: Optional[NumberField] = Field(default=None, description="Capital contribution (e.g. Kapitaltillskott) included in the total free equity proposed for disposition")
    # --- END ADDED V4 ---
    total_profit_loss_to_treat: Optional[NumberField] = Field(default=None, description="Total profit or loss available for disposition")
    allocation_to_maintenance_fund: Optional[NumberField] = Field(default=None, description="Amount allocated to the external maintenance fund")
    profit_loss_carried_forward: Optional[NumberField] = Field(default=None, description="Profit or loss carried forward to next year (Överförs i ny räkning)")
    amount_from_maintenance_fund: Optional[NumberField] = Field(default=None, description="Amount taken from the external maintenance fund")
# --- END MODIFIED V2 ---

# --- ADDED V5 (from PDF analysis consolidation) ---
class PledgedAssetItem(BaseModel):
    """Details of a single pledged asset."""
    item: Optional[StringField] = None # e.g., "Fastighetsinteckningar"
    amount_current_year: Optional[NumberField] = None
    amount_previous_year: Optional[NumberField] = None # If provided in the note
    beneficiary: Optional[StringField] = None # If specified (e.g., the lender)
# --- END ADDED V5 ---

class NoteItem(BaseModel):
    note_number: Optional[StringField] = None
    title: Optional[StringField] = None
    content: Optional[StringField] = None # Store raw content for now

class AccountingPrinciples(BaseModel):
    general: Optional[StringField] = None
    valuation_principles: Optional[StringField] = None
    revenue_recognition: Optional[StringField] = None
    maintenance_fund: Optional[StringField] = None
    fixed_assets_depreciation: Optional[StringField] = None
    depreciation_periods: Optional[Dict[str, StringField]] = None # Key: asset type, Value: period string
    current_assets: Optional[StringField] = None
    taxes_and_fees: Optional[StringField] = None
    loans: Optional[StringField] = None
    cash_flow: Optional[StringField] = None
    financial_instruments: Optional[StringField] = None
    shares_subsidiaries: Optional[StringField] = None
    offsetting: Optional[StringField] = None
    # --- ADDED V2 ---
    accounting_standard: Optional[StringField] = Field(default=None, description="Accounting standard applied (e.g., K2, K3)")
    tax_loss_carryforward: Optional[NumberField] = Field(default=None, description="Amount of tax loss carryforward (Skattemässigt underskott)")
    # --- END ADDED V2 ---
    # --- ADDED V4 (from PDF analyses) ---
    deferred_tax_liability_info: Optional[StringField] = Field(default=None, description="Information regarding deferred tax liability, especially if valued at zero")
    # --- END ADDED V4 ---


class NotesSection(BaseModel):
    accounting_principles: Optional[AccountingPrinciples] = None
    other_notes: List[NoteItem] = Field(default_factory=list)
    other_notes_summary: Optional[StringField] = None
    # --- ADDED V5 (from PDF analysis consolidation) ---
    pledged_assets: List[PledgedAssetItem] = Field(default_factory=list, description="Details of assets pledged as security (e.g., Pantbrev), typically from a dedicated note")
    # --- END ADDED V5 ---


class PlannedRenovation(BaseModel):
    description: Optional[StringField] = None
    planned_year: Optional[IntegerField] = None
    estimated_cost: Optional[NumberField] = None

class FuturePlans(BaseModel):
    planned_renovations: List[PlannedRenovation] = Field(default_factory=list)
    budget_next_year: Optional[NumberField] = None
    fee_changes: Optional[StringField] = None
    major_investments: Optional[StringField] = None
    maintenance_plan: Optional[StringField] = None

# --- ADDED V6.1: Member Movement Tracking ---
class MemberMovement(BaseModel):
    """Track member changes during fiscal year."""
    start_of_year: Optional[IntegerField] = Field(None, description="Number of members at year start")
    new_members: Optional[IntegerField] = Field(None, description="Number of new members joined during the year")
    departed_members: Optional[IntegerField] = Field(None, description="Number of members who left during the year")
    end_of_year: Optional[IntegerField] = Field(None, description="Number of members at year end")
    apartment_transfers: Optional[IntegerField] = Field(None, description="Number of apartment ownership transfers")

# --- ADDED V6.1: Meeting Records ---
class MeetingRecord(BaseModel):
    """Record of association meetings."""
    date: Optional[StringField] = Field(None, description="Date of the meeting")
    type: Optional[StringField] = Field(None, description="Type of meeting: 'annual', 'extraordinary', or 'board'")
    attendees: Optional[IntegerField] = Field(None, description="Number of voting members present")
    agenda_items: List[StringField] = Field(default_factory=list, description="Key agenda items discussed")

class GovernanceMeetings(BaseModel):
    """Track all governance meetings."""
    annual_meeting: Optional[MeetingRecord] = Field(None, description="Annual general meeting (årsstämma)")
    extraordinary_meetings: List[MeetingRecord] = Field(default_factory=list, description="Extra meetings held during the year")
    board_meetings_count: Optional[IntegerField] = Field(None, description="Total number of board meetings held")

# --- ADDED V6.1: Insurance Details ---
class InsuranceDetails(BaseModel):
    """Detailed insurance information."""
    provider: Optional[StringField] = Field(None, description="Insurance company name (e.g., Brandkontoret)")
    type: Optional[StringField] = Field(None, description="Type of insurance (e.g., Fullvärdesförsäkrad)")
    includes: List[StringField] = Field(default_factory=list, description="What's included in the insurance")
    excludes: List[StringField] = Field(default_factory=list, description="What's excluded from the insurance")
    annual_premium: Optional[NumberField] = Field(None, description="Annual insurance premium cost")

class SurroundingArea(BaseModel):
    distance_to_center: Optional[NumberField] = None
    distance_to_public_transport: Optional[NumberField] = None
    nearby_amenities: List[StringField] = Field(default_factory=list)
    neighborhood: Optional[StringField] = None
    municipality: Optional[StringField] = None
    schools_nearby: List[StringField] = Field(default_factory=list)
    shopping_nearby: List[StringField] = Field(default_factory=list)
    recreation_nearby: List[StringField] = Field(default_factory=list)

# --- ENHANCED V6.1: Service Contracts with detailed tracking ---
class ServiceContract(BaseModel):
    """Detailed service contract information."""
    supplier_name: Optional[StringField] = Field(None, description="Name of the service provider/contractor")
    service_category: Optional[StringField] = Field(None, description="Category of service (e.g., property_management, electricity, heating, cleaning)")
    service_description: Optional[StringField] = Field(None, description="Detailed description of services provided")
    annual_cost: Optional[NumberField] = Field(None, description="Annual cost for this service contract")
    contract_period: Optional[StringField] = Field(None, description="Contract period or renewal terms")

class ServiceContracts(BaseModel):
    """Comprehensive service contract tracking."""
    total_count: Optional[IntegerField] = Field(None, description="Total number of service contracts")
    contracts: List[ServiceContract] = Field(default_factory=list, description="List of all service contracts")
    major_suppliers: Dict[str, str] = Field(default_factory=dict, description="Service category -> Supplier name mapping")
    total_annual_cost: Optional[NumberField] = Field(None, description="Total annual cost of all service contracts")

# Keep old Supplier for backward compatibility
class Supplier(BaseModel):
    name: Optional[StringField] = None
    service: Optional[StringField] = None

class SignificantEvent(BaseModel):
    date: Optional[StringField] = None
    description: Optional[StringField] = None
    category: Optional[StringField] = None

class UncertainField(BaseModel):
    field_path: Optional[StringField] = None
    reason: Optional[StringField] = None
    confidence: Optional[NumberField] = None

class NormalizationRules(BaseModel):
    number_format: Optional[StringField] = None

class ExtractionMeta(BaseModel):
    extraction_confidence: Optional[NumberField] = None
    extraction_date: Optional[StringField] = None
    extraction_method: Optional[StringField] = None
    ocr_source: Optional[StringField] = None
    document_language: Optional[StringField] = None
    uncertain_fields: List[UncertainField] = Field(default_factory=list)
    normalization_rules: Optional[NormalizationRules] = None
    # --- NEW IN V6 ---
    table_extraction_metadata: Optional[TableExtractionMetadata] = Field(
        default=None, 
        description="Metadata about multi-year table extraction"
    )
    # --- END NEW IN V6 ---

class SchemaImprovementSuggestion(BaseModel):
    field_path: Optional[StringField] = None
    suggested_name: Optional[StringField] = None
    suggested_type: Optional[StringField] = None
    example_value: Optional[Any] = None
    reason: Optional[StringField] = None
    confidence: Optional[NumberField] = None

class SchemaImprovement(BaseModel):
    suggestions: List[SchemaImprovementSuggestion] = Field(default_factory=list)
    model: Optional[StringField] = None
    timestamp: Optional[StringField] = None

# --- ENHANCED Top Level Model ---

class BRFExtraction(BaseModel):
    """
    Root model for extracted data from a BRF annual report.
    Enhanced in v6.0 with:
    - Dynamic multi-year financial data support
    - Calculated metrics with automatic validation
    - Data quality scoring
    - Comprehensive extraction validation
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    # Core organizational data
    organization: Optional[Organization] = None
    property_details: Optional[PropertyDetails] = None
    
    # Single-year financial report (current year detailed)
    financial_report: Optional[FinancialReport] = None
    
    # ENHANCED IN V6: Multi-year financial overview (replaces simple DataTable)
    multi_year_overview: Optional[Union[DynamicMultiYearOverview, DataTable]] = Field(
        None, 
        description="Multi-year financial data with trends and validation (DynamicMultiYearOverview) or legacy DataTable"
    )
    
    # ENHANCED IN V6: Calculated metrics with validation
    financial_metrics: Optional[CalculatedFinancialMetrics] = Field(
        None,
        description="Financial metrics with automatic calculation and cross-validation"
    )
    
    # Loan details
    financial_loans: List[Loan] = Field(default_factory=list)
    
    # Governance
    board: Optional[Board] = None
    
    # Maintenance
    maintenance: Optional[Maintenance] = None
    
    # Equity changes table (kept as DataTable for flexibility)
    changes_in_equity: Optional[DataTable] = None
    
    # Profit/loss treatment
    proposed_profit_loss_treatment: Optional[ProposedProfitLossTreatment] = None
    
    # Notes section
    notes: Optional[NotesSection] = None
    
    # Cash flow (kept as DataTable for flexibility)
    cash_flow_statement: Optional[DataTable] = Field(
        None, 
        description="Structured data from the Kassaflödesanalys table"
    )
    
    # Additional data
    other_data_found: List[StringField] = Field(default_factory=list)
    future_plans: Optional[FuturePlans] = None
    surrounding_area: Optional[SurroundingArea] = None
    suppliers: List[Supplier] = Field(default_factory=list)
    significant_events: List[SignificantEvent] = Field(default_factory=list)
    
    # --- ADDED V6.1: Enhanced tracking from clean validation ---
    service_contracts: Optional[ServiceContracts] = Field(None, description="Detailed service contract information")
    member_movement: Optional[MemberMovement] = Field(None, description="Member changes during the fiscal year")
    governance_meetings: Optional[GovernanceMeetings] = Field(None, description="Records of all governance meetings")
    insurance_details: Optional[InsuranceDetails] = Field(None, description="Comprehensive insurance information")
    # --- END ADDED V6.1 ---
    
    # Metadata
    meta: Optional[ExtractionMeta] = None
    schema_improvements: Optional[SchemaImprovement] = None
    
    # NEW IN V6: Data quality assessment
    data_quality_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=1,
        description="Overall data quality score (0.0-1.0) based on completeness and validation"
    )
    
    def calculate_data_quality_score(self) -> float:
        """
        Calculate overall data quality score based on:
        - Field completeness
        - Validation errors
        - Multi-year data availability
        """
        scores = []
        
        # Check organization completeness
        if self.organization:
            org_fields = ['organization_name', 'organization_number', 'registered_office']
            org_complete = sum(1 for f in org_fields if getattr(self.organization, f, None)) / len(org_fields)
            scores.append(org_complete)
        
        # Check property details completeness  
        if self.property_details:
            prop_fields = ['property_designation', 'total_area_sqm', 'residential_area_sqm', 'year_built']
            prop_complete = sum(1 for f in prop_fields if getattr(self.property_details, f, None)) / len(prop_fields)
            scores.append(prop_complete)
        
        # Check financial metrics validation
        if self.financial_metrics:
            if len(self.financial_metrics.calculation_errors) == 0:
                scores.append(1.0)
            elif len(self.financial_metrics.calculation_errors) <= 2:
                scores.append(0.5)
            else:
                scores.append(0.0)
        
        # Check multi-year data availability
        if isinstance(self.multi_year_overview, DynamicMultiYearOverview):
            years_available = self.multi_year_overview.total_years
            if years_available >= 5:
                scores.append(1.0)
            elif years_available >= 3:
                scores.append(0.7)
            elif years_available >= 2:
                scores.append(0.4)
            else:
                scores.append(0.2)
        
        # Calculate overall score
        if scores:
            self.data_quality_score = sum(scores) / len(scores)
        else:
            self.data_quality_score = 0.0
        
        return self.data_quality_score
    
    def validate_extraction(self) -> Dict[str, Any]:
        """
        Comprehensive validation of the extracted data.
        Returns validation results and suggestions for improvement.
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate financial metrics calculations
        if self.financial_metrics:
            metrics_validation = self.financial_metrics.get_validation_summary()
            results["errors"].extend(metrics_validation["errors"])
            results["warnings"].extend(metrics_validation["warnings"])
            if metrics_validation["errors"]:
                results["valid"] = False
        
        # Validate multi-year data consistency
        if isinstance(self.multi_year_overview, DynamicMultiYearOverview):
            consistency_issues = self.multi_year_overview.validate_consistency()
            results["warnings"].extend(consistency_issues)
            
            # Check for anomalies
            anomalies = self.multi_year_overview.find_anomalies(threshold=0.5)
            for anomaly in anomalies:
                results["warnings"].append(
                    f"Large change in {anomaly['metric']}: "
                    f"{anomaly['from_year']}→{anomaly['to_year']} "
                    f"({anomaly['change_percent']:+.1f}%)"
                )
        
        # Check required fields
        if not self.organization or not self.organization.organization_number:
            results["errors"].append("Missing organization number")
            results["valid"] = False
        
        if not self.property_details or not self.property_details.property_designation:
            results["errors"].append("Missing property designation")
            results["valid"] = False
        
        # Provide improvement suggestions
        if isinstance(self.multi_year_overview, DynamicMultiYearOverview):
            if self.multi_year_overview.total_years < 4:
                results["suggestions"].append(
                    f"Only {self.multi_year_overview.total_years} years of data found. "
                    "Consider extracting more historical data for better trend analysis."
                )
        
        if self.financial_loans and len(self.financial_loans) > 0:
            loans_with_rates = sum(1 for loan in self.financial_loans if loan.interest_rate is not None)
            if loans_with_rates < len(self.financial_loans):
                results["warnings"].append(
                    f"Interest rates missing for {len(self.financial_loans) - loans_with_rates} loans"
                )
        
        return results

# --- Utility Functions ---
def create_field_with_confidence(
    value: Any,
    confidence: float,
    source: str,
    field_type: type = StringField
) -> Optional[ExtractionField]:
    if value is None: return None
    # For NumberField, ensure value is a clean string
    if field_type is NumberField:
        # Import only if needed to avoid circular imports
        try:
            from src.extractors.table_extractor_utils import normalize_swedish_number
            value = normalize_swedish_number(str(value), preserve_raw=False)
        except ImportError:
            # If import fails, just convert to string
            value = str(value)
    field_instance = field_type(value=value, confidence=confidence, source=source)
    return field_instance

def validate_extraction(data: Dict) -> Tuple[bool, List[Dict]]:
    """Validate extracted data against the BRFExtraction schema."""
    try: 
        extraction = BRFExtraction(**data)
        # Also run the comprehensive validation
        validation_results = extraction.validate_extraction()
        if not validation_results["valid"]:
            return False, validation_results["errors"]
        return True, []
    except ValidationError as e: 
        return False, e.errors()

# --- NEW IN V6: Helper function to migrate from old schema ---
def migrate_to_enhanced_schema(old_extraction: Dict) -> BRFExtraction:
    """
    Helper to migrate data from old schema format to enhanced v6 format.
    Useful when processing existing extractions.
    """
    new_extraction = BRFExtraction()
    
    # Copy basic fields that haven't changed
    for field in ['organization', 'property_details', 'financial_report', 
                  'board', 'maintenance', 'notes', 'suppliers', 'significant_events',
                  'proposed_profit_loss_treatment', 'cash_flow_statement', 'changes_in_equity']:
        if field in old_extraction and old_extraction[field]:
            setattr(new_extraction, field, old_extraction[field])
    
    # Migrate old financial_metrics to new CalculatedFinancialMetrics
    if 'financial_metrics' in old_extraction and old_extraction['financial_metrics']:
        old_metrics = old_extraction['financial_metrics']
        
        # If it's already the new type, keep it
        if isinstance(old_metrics, CalculatedFinancialMetrics):
            new_extraction.financial_metrics = old_metrics
        else:
            # Convert old format
            new_metrics = CalculatedFinancialMetrics()
            
            # Map old fields to new (handling both dict and object formats)
            if isinstance(old_metrics, dict):
                for key, value in old_metrics.items():
                    if hasattr(new_metrics, key):
                        # Handle nested value objects
                        if isinstance(value, dict) and 'value' in value:
                            setattr(new_metrics, key, value['value'])
                        else:
                            setattr(new_metrics, key, value)
            else:
                # Object format
                for field in ['total_debt', 'annual_fee_per_sqm', 'debt_per_sqm_total',
                             'debt_per_sqm_residential', 'soliditet_percent', 'energy_cost_per_sqm']:
                    if hasattr(old_metrics, field):
                        value = getattr(old_metrics, field)
                        if value and hasattr(value, 'value'):
                            setattr(new_metrics, field, value.value)
                        else:
                            setattr(new_metrics, field, value)
            
            new_extraction.financial_metrics = new_metrics
    
    # Migrate old multi_year_overview DataTable to new DynamicMultiYearOverview
    if 'multi_year_overview' in old_extraction and old_extraction['multi_year_overview']:
        old_table = old_extraction['multi_year_overview']
        
        # Check if it's already the new type
        if isinstance(old_table, DynamicMultiYearOverview):
            new_extraction.multi_year_overview = old_table
        elif hasattr(old_table, 'rows'):
            # Convert from DataTable
            new_overview = DynamicMultiYearOverview()
            
            # Parse rows to extract year data
            for row in old_table.rows:
                if 'year' in row:
                    year_data = YearlyFinancialData(year=row['year'])
                    # Map available fields
                    for field, value in row.items():
                        if field != 'year' and value is not None:
                            year_data.add_metric(field, value)
                    new_overview.years_data.append(year_data)
            
            new_overview.update_metadata()
            new_extraction.multi_year_overview = new_overview
        else:
            # Keep as is if we can't convert
            new_extraction.multi_year_overview = old_table
    
    # Calculate data quality score
    new_extraction.calculate_data_quality_score()
    
    return new_extraction
