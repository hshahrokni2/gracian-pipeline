"""
Pydantic models for ultra-comprehensive BRF data extraction.
"""

from .brf_schema import (
    # Master model
    BRFAnnualReport,

    # Level 1: Metadata
    DocumentMetadata,

    # Level 2: Governance
    GovernanceStructure,
    BoardMember,
    Auditor,

    # Level 3: Financial
    FinancialData,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    FinancialLineItem,

    # Level 4: Notes
    NotesCollection,
    Note,
    BuildingDetails,
    ReceivablesBreakdown,

    # Level 5: Property
    PropertyDetails,
    ApartmentUnit,
    ApartmentDistribution,
    CommercialTenant,
    CommonArea,

    # Level 6: Fees & Loans
    FeeStructure,
    LoanDetails,
    ReserveFund,

    # Level 7: Operations
    OperationsData,
    Supplier,
    MaintenanceItem,

    # Level 8: Events & Policies
    Event,
    Policy,
    EnvironmentalData,
)

__all__ = [
    'BRFAnnualReport',
    'DocumentMetadata',
    'GovernanceStructure',
    'BoardMember',
    'Auditor',
    'FinancialData',
    'IncomeStatement',
    'BalanceSheet',
    'CashFlowStatement',
    'FinancialLineItem',
    'NotesCollection',
    'Note',
    'BuildingDetails',
    'ReceivablesBreakdown',
    'PropertyDetails',
    'ApartmentUnit',
    'ApartmentDistribution',
    'CommercialTenant',
    'CommonArea',
    'FeeStructure',
    'LoanDetails',
    'ReserveFund',
    'OperationsData',
    'Supplier',
    'MaintenanceItem',
    'Event',
    'Policy',
    'EnvironmentalData',
]
