"""
Ultra-comprehensive Pydantic-based extraction system.

Extracts EVERY fact from BRF annual reports using structured Pydantic models.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from decimal import Decimal

from gracian_pipeline.models import (
    BRFAnnualReport,
    DocumentMetadata,
    GovernanceStructure,
    BoardMember,
    Auditor,
    FinancialData,
    IncomeStatement,
    BalanceSheet,
    NotesCollection,
    BuildingDetails,
    ReceivablesBreakdown,
    PropertyDetails,
    ApartmentDistribution,
    CommercialTenant,
    CommonArea,
    FeeStructure,
    LoanDetails,
    OperationsData,
    Supplier,
    MaintenanceItem,
    Event,
    Policy,
)

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor
from openai import OpenAI


class UltraComprehensivePydanticExtractor:
    """
    Extract every fact from BRF annual reports into Pydantic models.

    Extraction Strategy:
    - Phase 1: Base extraction (existing pipeline)
    - Phase 2: Enhanced extraction (deep dive into sections)
    - Phase 3: Pydantic model population
    - Phase 4: Validation and quality scoring
    """

    def __init__(self):
        self.base_extractor = RobustUltraComprehensiveExtractor()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_brf_comprehensive(
        self,
        pdf_path: str,
        mode: str = "deep"
    ) -> BRFAnnualReport:
        """
        Extract complete BRF annual report into Pydantic model.

        Args:
            pdf_path: Path to PDF file
            mode: Extraction mode (fast/deep/auto)

        Returns:
            BRFAnnualReport instance with all extracted data
        """
        print(f"\n🚀 Ultra-Comprehensive Pydantic Extraction: {Path(pdf_path).name}")
        print(f"   Mode: {mode}")

        # Phase 1: Base extraction using existing pipeline
        print("\n📊 Phase 1: Base Extraction (60s)")
        base_result = self.base_extractor.extract_brf_document(pdf_path, mode=mode)

        # Phase 2: Extract document metadata
        print("\n📋 Phase 2: Document Metadata (5s)")
        metadata = self._extract_metadata(pdf_path, base_result)

        # Phase 3: Enhanced section extraction
        print("\n🔍 Phase 3: Enhanced Section Extraction (120s)")

        # Governance
        governance = self._extract_governance_enhanced(base_result)

        # Financial
        financial = self._extract_financial_enhanced(base_result)

        # Notes
        notes = self._extract_notes_enhanced(base_result)

        # Property
        property_details = self._extract_property_enhanced(base_result)

        # Fees
        fees = self._extract_fees_enhanced(base_result)

        # Loans
        loans = self._extract_loans_enhanced(base_result)

        # Operations
        operations = self._extract_operations_enhanced(base_result)

        # Events
        events = self._extract_events_enhanced(base_result)

        # Policies
        policies = self._extract_policies_enhanced(base_result)

        # Phase 4: Quality metrics
        print("\n✅ Phase 4: Quality Assessment (30s)")
        quality_metrics = self._calculate_quality_metrics(base_result)

        # Construct BRFAnnualReport
        report = BRFAnnualReport(
            metadata=metadata,
            governance=governance,
            financial=financial,
            notes=notes,
            property=property_details,
            fees=fees,
            loans=loans,
            operations=operations,
            events=events,
            policies=policies,
            extraction_quality=quality_metrics,
            coverage_percentage=quality_metrics.get("coverage_percentage", 0),
            confidence_score=quality_metrics.get("confidence_score", 0),
            all_source_pages=self._collect_all_source_pages(base_result),
        )

        print(f"\n🎉 Extraction Complete!")
        print(f"   Coverage: {report.coverage_percentage:.1f}%")
        print(f"   Confidence: {report.confidence_score:.2f}")

        return report

    def _extract_metadata(self, pdf_path: str, base_result: Dict) -> DocumentMetadata:
        """Extract document metadata."""
        import fitz  # PyMuPDF

        pdf_path_obj = Path(pdf_path)
        doc = fitz.open(pdf_path)

        # Extract basic info
        brf_name = base_result.get("metadata_agent", {}).get("brf_name", "Unknown BRF")
        org_number = base_result.get("metadata_agent", {}).get("organization_number", "000000-0000")
        fiscal_year = base_result.get("metadata_agent", {}).get("fiscal_year", datetime.now().year)

        # Calculate file hash
        with open(pdf_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Check if machine-readable
        markdown = base_result.get("_docling_markdown", "")
        is_machine_readable = len(markdown) > 5000

        metadata = DocumentMetadata(
            document_id=f"{org_number}_{fiscal_year}",
            document_type="arsredovisning",
            fiscal_year=fiscal_year,
            brf_name=brf_name,
            organization_number=org_number,
            pages_total=doc.page_count,
            is_machine_readable=is_machine_readable,
            extraction_date=datetime.utcnow(),
            extraction_mode="deep",
            file_path=str(pdf_path_obj.absolute()),
            file_size_bytes=pdf_path_obj.stat().st_size,
            file_hash_sha256=file_hash,
        )

        doc.close()
        return metadata

    def _extract_governance_enhanced(self, base_result: Dict) -> Optional[GovernanceStructure]:
        """Extract enhanced governance information."""
        gov_data = base_result.get("governance_agent", {})

        if not gov_data:
            return None

        # Extract board members with details
        board_members = []
        for member_name in gov_data.get("board_members", []):
            # Determine role (simplistic - could be enhanced with LLM)
            role = "ledamot"
            if member_name == gov_data.get("chairman"):
                role = "ordforande"

            board_members.append(BoardMember(
                full_name=member_name,
                role=role,
                source_page=gov_data.get("evidence_pages", [])
            ))

        # Extract auditors
        primary_auditor = None
        if gov_data.get("auditor_name"):
            primary_auditor = Auditor(
                name=gov_data["auditor_name"],
                firm=gov_data.get("audit_firm"),
                source_page=gov_data.get("evidence_pages", [])
            )

        return GovernanceStructure(
            chairman=gov_data.get("chairman"),
            board_members=board_members,
            primary_auditor=primary_auditor,
            nomination_committee=gov_data.get("nomination_committee", []),
            source_pages=gov_data.get("evidence_pages", []),
        )

    def _extract_financial_enhanced(self, base_result: Dict) -> Optional[FinancialData]:
        """Extract enhanced financial information."""
        fin_data = base_result.get("financial_agent", {})

        if not fin_data:
            return None

        # Income Statement
        income_statement = IncomeStatement(
            revenue_total=self._to_decimal(fin_data.get("revenue")),
            expenses_total=self._to_decimal(fin_data.get("expenses")),
            result_after_tax=self._to_decimal(fin_data.get("surplus")),
            source_pages=fin_data.get("evidence_pages", []),
        )

        # Balance Sheet
        balance_sheet = BalanceSheet(
            assets_total=self._to_decimal(fin_data.get("assets")),
            liabilities_total=self._to_decimal(fin_data.get("liabilities")),
            equity_total=self._to_decimal(fin_data.get("equity")),
            source_pages=fin_data.get("evidence_pages", []),
        )

        return FinancialData(
            income_statement=income_statement,
            balance_sheet=balance_sheet,
        )

    def _extract_notes_enhanced(self, base_result: Dict) -> Optional[NotesCollection]:
        """Extract enhanced notes information."""
        fin_data = base_result.get("financial_agent", {})

        # Note 8: Building Details
        building_details = None
        building_data = fin_data.get("building_details", {})
        if building_data:
            building_details = BuildingDetails(
                closing_acquisition_value=self._to_decimal(building_data.get("ackumulerade_anskaffningsvarden")),
                current_year_depreciation=self._to_decimal(building_data.get("arets_avskrivningar")),
                planned_residual_value=self._to_decimal(building_data.get("planenligt_restvarde")),
                tax_assessment_building=self._to_decimal(building_data.get("taxeringsvarde_byggnad")),
                tax_assessment_land=self._to_decimal(building_data.get("taxeringsvarde_mark")),
                source_pages=fin_data.get("evidence_pages", []),
            )

        # Note 9: Receivables
        receivables_breakdown = None
        receivables_data = fin_data.get("receivables_breakdown", {})
        if receivables_data:
            receivables_breakdown = ReceivablesBreakdown(
                tax_account=self._to_decimal(receivables_data.get("skattekonto")),
                vat_deduction=self._to_decimal(receivables_data.get("momsavrakning")),
                client_funds=self._to_decimal(receivables_data.get("klientmedel")),
                receivables=self._to_decimal(receivables_data.get("fordringar")),
                other_deductions=self._to_decimal(receivables_data.get("avrakning_ovrigt")),
                source_pages=fin_data.get("evidence_pages", []),
            )

        if building_details or receivables_breakdown:
            return NotesCollection(
                note_8_buildings=building_details,
                note_9_receivables=receivables_breakdown,
            )

        return None

    def _extract_property_enhanced(self, base_result: Dict) -> Optional[PropertyDetails]:
        """Extract enhanced property information."""
        prop_data = base_result.get("property_agent", {})

        if not prop_data:
            return None

        # Apartment distribution
        apartment_dist = None
        apt_data = prop_data.get("apartment_breakdown", {})
        if apt_data:
            apartment_dist = ApartmentDistribution(
                one_room=apt_data.get("1_rok", 0),
                two_rooms=apt_data.get("2_rok", 0),
                three_rooms=apt_data.get("3_rok", 0),
                four_rooms=apt_data.get("4_rok", 0),
                five_rooms=apt_data.get("5_rok", 0),
                more_than_five=apt_data.get(">5_rok", 0),
            )

        # Commercial tenants
        commercial_tenants = []
        for tenant in prop_data.get("commercial_tenants", []):
            if isinstance(tenant, dict):
                commercial_tenants.append(CommercialTenant(
                    business_name=tenant.get("business_name", "Unknown"),
                    business_type=tenant.get("business_type"),
                    source_page=prop_data.get("evidence_pages", []),
                ))

        # Common areas
        common_areas = []
        for area in prop_data.get("common_areas", []):
            if isinstance(area, dict):
                common_areas.append(CommonArea(
                    name=area.get("name", "Unknown"),
                    description=area.get("description"),
                ))

        return PropertyDetails(
            property_designation=prop_data.get("property_designation"),
            municipality=prop_data.get("municipality"),
            total_apartments=prop_data.get("total_apartments"),
            apartment_distribution=apartment_dist,
            commercial_tenants=commercial_tenants,
            common_areas=common_areas,
            source_pages=prop_data.get("evidence_pages", []),
        )

    def _extract_fees_enhanced(self, base_result: Dict) -> Optional[FeeStructure]:
        """Extract enhanced fee information."""
        fees_data = base_result.get("fees_agent", {})

        if not fees_data:
            return None

        return FeeStructure(
            annual_fee_per_sqm=self._to_decimal(fees_data.get("arsavgift_per_sqm")),
            source_pages=fees_data.get("evidence_pages", []),
        )

    def _extract_loans_enhanced(self, base_result: Dict) -> List[LoanDetails]:
        """Extract enhanced loan information."""
        loans_data = base_result.get("loans_agent", {})
        loans = []

        for loan in loans_data.get("loans", []):
            if isinstance(loan, dict):
                loans.append(LoanDetails(
                    lender=loan.get("lender", "Unknown"),
                    outstanding_balance=self._to_decimal(loan.get("outstanding_balance", 0)),
                    interest_rate=loan.get("interest_rate"),
                    source_page=loans_data.get("evidence_pages", []),
                ))

        return loans

    def _extract_operations_enhanced(self, base_result: Dict) -> Optional[OperationsData]:
        """Extract enhanced operations information."""
        ops_data = base_result.get("operations_agent", {})

        if not ops_data:
            return None

        # Suppliers
        suppliers = []
        for supplier in ops_data.get("suppliers", []):
            if isinstance(supplier, dict):
                suppliers.append(Supplier(
                    company_name=supplier.get("company_name", "Unknown"),
                    service_type=supplier.get("service_type", "Unknown"),
                    source_page=ops_data.get("evidence_pages", []),
                ))

        # Maintenance items
        maintenance = []
        for item in ops_data.get("planned_maintenance", []):
            if isinstance(item, dict):
                maintenance.append(MaintenanceItem(
                    description=item.get("description", "Unknown"),
                    planned_year=item.get("planned_year"),
                    source_page=ops_data.get("evidence_pages", []),
                ))

        if suppliers or maintenance:
            return OperationsData(
                suppliers=suppliers,
                planned_maintenance=maintenance,
                source_pages=ops_data.get("evidence_pages", []),
            )

        return None

    def _extract_events_enhanced(self, base_result: Dict) -> List[Event]:
        """Extract enhanced events information."""
        events_data = base_result.get("events_agent", {})
        events = []

        for event in events_data.get("events", []):
            if isinstance(event, dict):
                events.append(Event(
                    event_type=event.get("event_type", "Unknown"),
                    description=event.get("description", ""),
                    source_page=events_data.get("evidence_pages", []),
                ))

        return events

    def _extract_policies_enhanced(self, base_result: Dict) -> List[Policy]:
        """Extract enhanced policies information."""
        policies_data = base_result.get("policies_agent", {})
        policies = []

        for policy in policies_data.get("policies", []):
            if isinstance(policy, dict):
                policies.append(Policy(
                    policy_name=policy.get("policy_name", "Unknown"),
                    policy_description=policy.get("description", ""),
                    source_page=policies_data.get("evidence_pages", []),
                ))

        return policies

    def _calculate_quality_metrics(self, base_result: Dict) -> Dict[str, float]:
        """Calculate extraction quality metrics."""
        quality = base_result.get("_quality", {})

        return {
            "coverage_percentage": quality.get("coverage_percentage", 0),
            "confidence_score": quality.get("confidence_score", 0),
            "total_fields": quality.get("total_fields_extracted", 0),
            "evidence_ratio": quality.get("evidence_ratio", 0),
        }

    def _collect_all_source_pages(self, base_result: Dict) -> List[int]:
        """Collect all source pages from all agents."""
        all_pages = set()

        for agent_key, agent_data in base_result.items():
            if isinstance(agent_data, dict) and "evidence_pages" in agent_data:
                all_pages.update(agent_data["evidence_pages"])

        return sorted(list(all_pages))

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal, return None if not possible."""
        if value is None:
            return None

        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                # Remove spaces and Swedish formatting
                cleaned = value.replace(" ", "").replace(",", ".")
                return Decimal(cleaned)
            elif isinstance(value, Decimal):
                return value
        except:
            pass

        return None


def extract_brf_to_pydantic(pdf_path: str, mode: str = "deep") -> BRFAnnualReport:
    """
    Convenience function to extract BRF annual report to Pydantic model.

    Args:
        pdf_path: Path to PDF file
        mode: Extraction mode (fast/deep/auto)

    Returns:
        BRFAnnualReport instance
    """
    extractor = UltraComprehensivePydanticExtractor()
    return extractor.extract_brf_comprehensive(pdf_path, mode=mode)
