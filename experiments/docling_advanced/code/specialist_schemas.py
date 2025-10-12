#!/usr/bin/env python3
"""
Specialist Pydantic Schemas

Each specialist agent has ONE focused schema (single responsibility).
Schemas include:
- Field validation (types, ranges, formats)
- Cross-field validation
- Swedish number format handling
- Confidence tracking
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import warnings


class OperatingCostsSchema(BaseModel):
    """
    Specialist schema for operating costs (utilities)

    Extracts from: Driftkostnader/Rörelsekostnader section (note number varies!)
    Content keywords: "Driftkostnader", "El", "Värme", "Vatten och avlopp"
    Typical page: 13-14
    """

    el: Optional[float] = Field(
        None,
        description="Electricity costs in SEK (Swedish: El)",
        ge=0
    )
    varme: Optional[float] = Field(
        None,
        description="Heating costs in SEK (Swedish: Värme)",
        ge=0
    )
    vatten: Optional[float] = Field(
        None,
        description="Water and drainage costs in SEK (Swedish: Vatten och avlopp)",
        ge=0
    )
    evidence_page: Optional[int] = Field(
        None,
        description="Page number where data was found"
    )
    confidence: float = Field(
        1.0,
        description="Extraction confidence (0.0 to 1.0)",
        ge=0,
        le=1.0
    )

    @field_validator('el', 'varme', 'vatten')
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Cost must be positive")
        return v

    @field_validator('el')
    @classmethod
    def validate_el_range(cls, v):
        """Electricity typically 200k-1M SEK for BRF"""
        if v and (v < 50_000 or v > 2_000_000):
            warnings.warn(f"Unusual electricity cost: {v:,.0f} SEK (expected 50k-2M)")
        return v

    @field_validator('varme')
    @classmethod
    def validate_varme_range(cls, v):
        """Heating typically 300k-800k SEK for BRF"""
        if v and (v < 100_000 or v > 1_500_000):
            warnings.warn(f"Unusual heating cost: {v:,.0f} SEK (expected 100k-1.5M)")
        return v

    @field_validator('vatten')
    @classmethod
    def validate_vatten_range(cls, v):
        """Water typically 100k-300k SEK for BRF"""
        if v and (v < 30_000 or v > 500_000):
            warnings.warn(f"Unusual water cost: {v:,.0f} SEK (expected 30k-500k)")
        return v

    class Config:
        validate_assignment = True


class BuildingsSchema(BaseModel):
    """
    Specialist schema for buildings and property

    Extracts from: Byggnader och mark section (note number varies!)
    Content keywords: "Byggnader", "Anskaffningsvärde", "Avskrivningar", "Bokfört värde"
    Typical page: 14-15
    """

    acquisition_value: Optional[float] = Field(
        None,
        description="Total acquisition value of buildings (Swedish: Anskaffningsvärde)",
        ge=0
    )
    accumulated_depreciation: Optional[float] = Field(
        None,
        description="Accumulated depreciation (Swedish: Ackumulerade avskrivningar)",
        le=0  # Depreciation is negative
    )
    book_value: Optional[float] = Field(
        None,
        description="Current book value (Swedish: Bokfört värde)",
        ge=0
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_book_value_calculation(self):
        """Book value should equal acquisition - depreciation"""
        acquisition = self.acquisition_value
        depreciation = self.accumulated_depreciation
        book = self.book_value

        if all([acquisition, depreciation, book]):
            expected_book = acquisition + depreciation  # depreciation is negative
            tolerance = 0.02  # 2% tolerance

            if abs(book - expected_book) / book > tolerance:
                warnings.warn(
                    f"Book value mismatch: {book:,.0f} vs expected {expected_book:,.0f}"
                )

        return self


class LiabilitiesSchema(BaseModel):
    """
    Specialist schema for liabilities (loans and debt)

    Extracts from: Långfristiga skulder section (note number varies!)
    Content keywords: "Långfristiga skulder", "Kortfristiga skulder", "Lån", "Räntesats"
    Typical pages: 15-16
    """

    long_term_debt: Optional[float] = Field(
        None,
        description="Long-term debt (Swedish: Långfristiga skulder)",
        ge=0
    )
    short_term_debt: Optional[float] = Field(
        None,
        description="Short-term debt (Swedish: Kortfristiga skulder)",
        ge=0
    )
    total_debt: Optional[float] = Field(
        None,
        description="Total debt (Swedish: Totala skulder)",
        ge=0
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_total_debt(self):
        """Total debt should equal long-term + short-term"""
        long_term = self.long_term_debt
        short_term = self.short_term_debt
        total = self.total_debt

        if all([long_term, short_term, total]):
            expected_total = long_term + short_term
            tolerance = 0.02

            if abs(total - expected_total) / total > tolerance:
                warnings.warn(
                    f"Total debt mismatch: {total:,.0f} vs expected {expected_total:,.0f}"
                )

        return self


class BalanceSheetAssetsSchema(BaseModel):
    """
    Specialist schema for balance sheet assets

    Extracts from: Balansräkning - Tillgångar
    Typical pages: 9-10
    """

    fixed_assets: Optional[float] = Field(
        None,
        description="Fixed assets (Swedish: Anläggningstillgångar)",
        ge=0
    )
    current_assets: Optional[float] = Field(
        None,
        description="Current assets (Swedish: Omsättningstillgångar)",
        ge=0
    )
    cash_and_equivalents: Optional[float] = Field(
        None,
        description="Cash and bank deposits (Swedish: Kassa och bank)",
        ge=0
    )
    total_assets: Optional[float] = Field(
        None,
        description="Total assets (Swedish: Summa tillgångar)",
        ge=0
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_total_assets(self):
        """Total assets should equal fixed + current"""
        fixed = self.fixed_assets
        current = self.current_assets
        total = self.total_assets

        if all([fixed, current, total]):
            expected_total = fixed + current
            tolerance = 0.02

            if abs(total - expected_total) / total > tolerance:
                warnings.warn(
                    f"Total assets mismatch: {total:,.0f} vs expected {expected_total:,.0f}"
                )

        return self


class BalanceSheetLiabilitiesSchema(BaseModel):
    """
    Specialist schema for balance sheet liabilities & equity

    Extracts from: Balansräkning - Skulder och eget kapital
    Typical pages: 10-11
    """

    equity: Optional[float] = Field(
        None,
        description="Total equity (Swedish: Eget kapital)",
        ge=0
    )
    long_term_liabilities: Optional[float] = Field(
        None,
        description="Long-term liabilities (Swedish: Långfristiga skulder)",
        ge=0
    )
    short_term_liabilities: Optional[float] = Field(
        None,
        description="Short-term liabilities (Swedish: Kortfristiga skulder)",
        ge=0
    )
    total_liabilities_and_equity: Optional[float] = Field(
        None,
        description="Total liabilities and equity (Swedish: Summa skulder och eget kapital)",
        ge=0
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_balance_sheet_equation(self):
        """Assets = Liabilities + Equity"""
        equity = self.equity
        long_term = self.long_term_liabilities
        short_term = self.short_term_liabilities
        total = self.total_liabilities_and_equity

        if all([equity, long_term, short_term, total]):
            expected_total = equity + long_term + short_term
            tolerance = 0.02

            if abs(total - expected_total) / total > tolerance:
                warnings.warn(
                    f"Balance sheet mismatch: {total:,.0f} vs expected {expected_total:,.0f}"
                )

        return self


class IncomeStatementSchema(BaseModel):
    """
    Specialist schema for income statement

    Extracts from: Resultaträkning
    Typical pages: 6-8
    """

    revenue: Optional[float] = Field(
        None,
        description="Total revenue (Swedish: Nettoomsättning)",
        ge=0
    )
    operating_expenses: Optional[float] = Field(
        None,
        description="Operating expenses (Swedish: Rörelsekostnader)",
        le=0  # Expenses are negative
    )
    operating_result: Optional[float] = Field(
        None,
        description="Operating result (Swedish: Rörelseresultat)"
    )
    financial_income: Optional[float] = Field(
        None,
        description="Financial income (Swedish: Finansiella intäkter)",
        ge=0
    )
    financial_expenses: Optional[float] = Field(
        None,
        description="Financial expenses (Swedish: Finansiella kostnader)",
        le=0
    )
    net_result: Optional[float] = Field(
        None,
        description="Net result (Swedish: Årets resultat)"
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_operating_result(self):
        """Operating result = Revenue + Operating expenses (expenses are negative)"""
        revenue = self.revenue
        expenses = self.operating_expenses
        operating = self.operating_result

        if all([revenue, expenses, operating]):
            expected_operating = revenue + expenses  # expenses negative
            tolerance = 0.05  # 5% tolerance for income statement

            if operating != 0 and abs(operating - expected_operating) / abs(operating) > tolerance:
                warnings.warn(
                    f"Operating result mismatch: {operating:,.0f} vs expected {expected_operating:,.0f}"
                )

        return self


class GovernanceChairmanSchema(BaseModel):
    """
    Specialist schema for chairman extraction

    Extracts from: Förvaltningsberättelse or Styrelse section
    Typical pages: 1-3
    """

    chairman_name: Optional[str] = Field(
        None,
        description="Name of board chairman (Swedish: Ordförande)"
    )
    chairman_title: Optional[str] = Field(
        None,
        description="Chairman's title if specified"
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @field_validator('chairman_name')
    @classmethod
    def validate_name_format(cls, v):
        """Chairman name should have at least first and last name"""
        if v:
            parts = v.strip().split()
            if len(parts) < 2:
                warnings.warn(f"Chairman name might be incomplete: '{v}'")
        return v


class CashFlowSchema(BaseModel):
    """
    Specialist schema for cash flow statement

    Extracts from: Kassaflödesanalys
    Typical pages: 7-8
    """

    cash_from_operations: Optional[float] = Field(
        None,
        description="Cash flow from operating activities (Swedish: Kassaflöde från löpande verksamhet)"
    )
    cash_from_investments: Optional[float] = Field(
        None,
        description="Cash flow from investing activities (Swedish: Kassaflöde från investeringsverksamhet)"
    )
    cash_from_financing: Optional[float] = Field(
        None,
        description="Cash flow from financing activities (Swedish: Kassaflöde från finansieringsverksamhet)"
    )
    net_cash_flow: Optional[float] = Field(
        None,
        description="Net change in cash (Swedish: Årets kassaflöde)"
    )
    evidence_page: Optional[int] = None
    confidence: float = Field(1.0, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_net_cash_flow(self):
        """Net cash flow should equal sum of all categories"""
        operations = self.cash_from_operations
        investments = self.cash_from_investments
        financing = self.cash_from_financing
        net = self.net_cash_flow

        if all([operations, investments, financing, net]):
            expected_net = operations + investments + financing
            tolerance = 0.02

            if net != 0 and abs(net - expected_net) / abs(net) > tolerance:
                warnings.warn(
                    f"Net cash flow mismatch: {net:,.0f} vs expected {expected_net:,.0f}"
                )

        return self
