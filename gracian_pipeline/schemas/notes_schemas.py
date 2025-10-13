"""
Pydantic schemas for Swedish BRF notes extraction.

These schemas define the structure of data extracted from notes sections,
with validation, normalization, and evidence tracking.

Author: Claude Code
Date: 2025-10-13 (Path B Day 3)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List


class BaseNoteData(BaseModel):
    """
    Base class for all note data schemas.

    Provides common fields for evidence tracking and confidence scoring.
    All note-specific schemas inherit from this base class.
    """
    evidence_pages: List[int] = Field(
        default_factory=list,
        description="Page numbers where evidence was found"
    )
    evidence_quotes: List[str] = Field(
        default_factory=list,
        description="Direct quotes from the document supporting the extraction"
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) based on 4-factor model"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "evidence_pages": [10, 11],
                "evidence_quotes": ["Avskrivningar sker enligt linjär metod"],
                "confidence": 0.85
            }
        }


class DepreciationData(BaseNoteData):
    """
    Schema for depreciation note extraction.

    Extracts Swedish BRF depreciation information including:
    - Method used (linjär, rak, etc.)
    - Useful life in years
    - What assets are depreciated

    Swedish Terms:
    - avskrivning = depreciation
    - avskrivningsmetod = depreciation method
    - nyttjandeperiod = useful life
    - ekonomisk livslängd = economic life
    """

    depreciation_method: Optional[str] = Field(
        None,
        description="Depreciation method (e.g., 'linjär avskrivning', 'rak avskrivning')"
    )
    useful_life_years: Optional[int] = Field(
        None,
        ge=0,
        le=200,
        description="Useful life in years (typically 50 for buildings)"
    )
    depreciation_base: Optional[str] = Field(
        None,
        description="What is being depreciated (e.g., 'byggnader', 'inventarier')"
    )

    @validator('depreciation_method')
    def normalize_method(cls, v):
        """Normalize Swedish depreciation method terms."""
        if not v:
            return v

        v_lower = v.lower()

        # Normalize to standard Swedish terms
        if 'linjär' in v_lower:
            return 'linjär avskrivning'
        elif 'rak' in v_lower:
            return 'rak avskrivning'
        elif 'degressiv' in v_lower:
            return 'degressiv avskrivning'

        return v

    @validator('useful_life_years')
    def validate_useful_life(cls, v):
        """Validate useful life is reasonable for BRF assets."""
        if v is None:
            return v

        # BRF assets typically have 5-100 year useful lives
        # Buildings: 50-100 years
        # Equipment: 5-20 years
        if v < 5 or v > 100:
            # Likely extraction error
            return None

        return v

    @validator('depreciation_base')
    def normalize_base(cls, v):
        """Normalize Swedish asset type terms."""
        if not v:
            return v

        v_lower = v.lower()

        # Normalize common asset types
        if 'byggnad' in v_lower:
            return 'byggnader'
        elif 'inventari' in v_lower:
            return 'inventarier'
        elif 'maskiner' in v_lower or 'utrustning' in v_lower:
            return 'maskiner och inventarier'

        return v

    class Config:
        """Pydantic configuration with example."""
        json_schema_extra = {
            "example": {
                "depreciation_method": "linjär avskrivning",
                "useful_life_years": 50,
                "depreciation_base": "byggnader",
                "evidence_pages": [10],
                "evidence_quotes": [
                    "Avskrivningar sker enligt linjär avskrivningsmetod",
                    "Byggnader skrivs av över 50 år"
                ],
                "confidence": 0.92
            }
        }


class MaintenanceData(BaseNoteData):
    """
    Schema for maintenance plan note extraction.

    Extracts Swedish BRF maintenance plan information including:
    - Plan description
    - Start and end dates
    - Budget allocation

    Swedish Terms:
    - underhåll = maintenance
    - underhållsplan = maintenance plan
    - planerat underhåll = planned maintenance
    - underhållsfond = maintenance fund
    """

    maintenance_plan: Optional[str] = Field(
        None,
        description="Description of maintenance plan (e.g., '10-årig underhållsplan')"
    )
    plan_start_date: Optional[str] = Field(
        None,
        description="Plan start year (e.g., '2020')"
    )
    plan_end_date: Optional[str] = Field(
        None,
        description="Plan end year (e.g., '2030')"
    )
    maintenance_budget: Optional[float] = Field(
        None,
        ge=0,
        description="Total maintenance budget in SEK"
    )

    @validator('maintenance_plan')
    def normalize_plan_description(cls, v):
        """Normalize maintenance plan descriptions."""
        if not v:
            return v

        # Keep original text but clean up whitespace
        return ' '.join(v.split())

    @validator('plan_start_date', 'plan_end_date')
    def validate_year_format(cls, v):
        """Validate year format and range."""
        if not v:
            return v

        # Extract year from various formats
        import re
        year_match = re.search(r'(20\d{2})', str(v))
        if year_match:
            year = int(year_match.group(1))
            # Validate reasonable range (2000-2050)
            if 2000 <= year <= 2050:
                return str(year)

        return None

    @validator('plan_end_date')
    def validate_date_range(cls, v, values):
        """Validate end date is after start date."""
        if not v or 'plan_start_date' not in values:
            return v

        start_date = values.get('plan_start_date')
        if not start_date:
            return v

        try:
            start_year = int(start_date)
            end_year = int(v)

            # Plan should be 5-20 years (typical BRF maintenance cycle)
            if end_year <= start_year or (end_year - start_year) > 20:
                return None

        except (ValueError, TypeError):
            return None

        return v

    class Config:
        """Pydantic configuration with example."""
        json_schema_extra = {
            "example": {
                "maintenance_plan": "10-årig underhållsplan",
                "plan_start_date": "2020",
                "plan_end_date": "2030",
                "maintenance_budget": 15000000.0,
                "evidence_pages": [12],
                "evidence_quotes": [
                    "Styrelsen har upprättat en 10-årig underhållsplan för perioden 2020-2030"
                ],
                "confidence": 0.88
            }
        }


class TaxData(BaseNoteData):
    """
    Schema for tax note extraction.

    Extracts Swedish BRF tax information including:
    - Tax accounting policy
    - Current year tax
    - Deferred tax

    Swedish Terms:
    - skatt = tax
    - inkomstskatt = income tax
    - skattepolicy = tax policy
    - aktuell skatt = current tax
    - uppskjuten skatt = deferred tax
    - skattemässiga = tax-related
    - bokföringsmässiga = accounting-related
    """

    tax_policy: Optional[str] = Field(
        None,
        description="Tax accounting method (e.g., 'bokföringsmässiga', 'skattemässiga')"
    )
    current_tax: Optional[float] = Field(
        None,
        description="Current year tax amount in SEK"
    )
    deferred_tax: Optional[float] = Field(
        None,
        description="Deferred tax amount in SEK"
    )

    @validator('tax_policy')
    def normalize_tax_policy(cls, v):
        """Normalize Swedish tax policy terms."""
        if not v:
            return v

        v_lower = v.lower()

        # Normalize common tax policy terms
        if 'bokföringsmässig' in v_lower:
            return 'bokföringsmässiga grunder'
        elif 'skattemässig' in v_lower:
            return 'skattemässiga grunder'

        return v

    @validator('current_tax', 'deferred_tax')
    def validate_tax_amount(cls, v):
        """Validate tax amounts are reasonable."""
        if v is None:
            return v

        # BRF tax amounts typically range from 0 to several million SEK
        # Negative values allowed for tax assets
        if abs(v) > 100_000_000:  # 100 million SEK sanity check
            return None

        return v

    class Config:
        """Pydantic configuration with example."""
        json_schema_extra = {
            "example": {
                "tax_policy": "bokföringsmässiga grunder",
                "current_tax": 250000.0,
                "deferred_tax": -50000.0,
                "evidence_pages": [11],
                "evidence_quotes": [
                    "Redovisning av inkomstskatter sker enligt bokföringsmässiga grunder",
                    "Aktuell skatt uppgår till 250 tkr"
                ],
                "confidence": 0.85
            }
        }


# Export all schemas
__all__ = [
    'BaseNoteData',
    'DepreciationData',
    'MaintenanceData',
    'TaxData',
]
