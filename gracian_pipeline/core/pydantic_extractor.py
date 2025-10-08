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
        from gracian_pipeline.models.base_fields import (
            NumberField, StringField, BooleanField, DateField
        )

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

        # Create metadata with MIXED approach:
        # - Extracted fields → ExtractionField (with confidence tracking)
        # - System-generated fields → Raw Python types (no confidence needed)
        metadata = DocumentMetadata(
            # System-generated: raw types
            document_id=f"{org_number}_{fiscal_year}",
            document_type="arsredovisning",
            pages_total=doc.page_count,
            is_machine_readable=is_machine_readable,
            extraction_date=datetime.utcnow(),
            extraction_mode="deep",
            file_path=str(pdf_path_obj.absolute()),
            file_size_bytes=pdf_path_obj.stat().st_size,
            file_hash_sha256=file_hash,

            # Extracted fields: ExtractionField with confidence
            fiscal_year=NumberField(
                value=fiscal_year,
                confidence=0.9 if fiscal_year != datetime.now().year else 0.5,
                source="llm_extraction"
            ),
            brf_name=StringField(
                value=brf_name,
                confidence=0.9 if brf_name != "Unknown BRF" else 0.5,
                source="llm_extraction"
            ),
            organization_number=StringField(
                value=org_number,
                confidence=0.9 if org_number != "000000-0000" else 0.5,
                source="llm_extraction"
            ),
        )

        doc.close()
        return metadata

    def _extract_governance_enhanced(self, base_result: Dict) -> Optional[GovernanceStructure]:
        """Extract enhanced governance information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField, ListField

        gov_data = base_result.get("governance_agent", {})

        if not gov_data:
            return None

        # Extract board members with details
        board_members = []
        for member_name in (gov_data.get("board_members") or []):
            # Determine role (simplistic - could be enhanced with LLM)
            role = "ledamot"
            if member_name == gov_data.get("chairman"):
                role = "ordforande"

            board_members.append(BoardMember(
                # ✅ Extracted: ExtractionField
                full_name=StringField(
                    value=member_name,
                    confidence=0.9,
                    source="llm_extraction"
                ),
                # ❌ Literal type: raw string (not StringField!)
                role=role,
                # ❌ Deprecated field: raw list (not ListField!)
                source_page=gov_data.get("evidence_pages", [])
            ))

        # Extract auditors
        primary_auditor = None
        if gov_data.get("auditor_name"):
            primary_auditor = Auditor(
                # ✅ Extracted: ExtractionField
                name=StringField(
                    value=gov_data["auditor_name"],
                    confidence=0.9,
                    source="llm_extraction"
                ),
                firm=StringField(
                    value=gov_data.get("audit_firm", ""),
                    confidence=0.85 if gov_data.get("audit_firm") else 0.5,
                    source="llm_extraction"
                ) if gov_data.get("audit_firm") else None,
                # ❌ Deprecated field: raw list (not ListField!)
                source_page=gov_data.get("evidence_pages", [])
            )

        return GovernanceStructure(
            # ✅ Extracted: ExtractionField
            chairman=StringField(
                value=gov_data.get("chairman", ""),
                confidence=0.9 if gov_data.get("chairman") else 0.5,
                source="llm_extraction"
            ) if gov_data.get("chairman") else None,
            # ❌ Structural field: raw list of objects (not wrapped)
            board_members=board_members,
            primary_auditor=primary_auditor,
            # ✅ Extracted list: ListField (with confidence tracking)
            nomination_committee=ListField(
                value=gov_data.get("nomination_committee", []),
                confidence=0.85,
                source="llm_extraction"
            ),
            # ❌ Deprecated field: raw list (not ListField!)
            source_pages=gov_data.get("evidence_pages", [])
        )

    def _extract_financial_enhanced(self, base_result: Dict) -> Optional[FinancialData]:
        """Extract enhanced financial information with MIXED approach."""
        from gracian_pipeline.models.base_fields import NumberField

        fin_data = base_result.get("financial_agent", {})

        if not fin_data:
            return None

        # Income Statement
        income_statement = IncomeStatement(
            # ✅ Extracted: ExtractionField
            revenue_total=NumberField(
                value=self._to_decimal(fin_data.get("revenue")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("revenue")) is not None else None,
            expenses_total=NumberField(
                value=self._to_decimal(fin_data.get("expenses")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("expenses")) is not None else None,
            result_after_tax=NumberField(
                value=self._to_decimal(fin_data.get("surplus")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("surplus")) is not None else None,
            # ❌ Deprecated field: raw list (not ListField!)
            source_pages=fin_data.get("evidence_pages", [])
        )

        # Balance Sheet
        balance_sheet = BalanceSheet(
            # ✅ Extracted: ExtractionField
            assets_total=NumberField(
                value=self._to_decimal(fin_data.get("assets")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("assets")) is not None else None,
            liabilities_total=NumberField(
                value=self._to_decimal(fin_data.get("liabilities")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("liabilities")) is not None else None,
            equity_total=NumberField(
                value=self._to_decimal(fin_data.get("equity")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("equity")) is not None else None,
            # ❌ Deprecated field: raw list (not ListField!)
            source_pages=fin_data.get("evidence_pages", [])
        )

        return FinancialData(
            # ❌ Structural fields: raw objects (not wrapped)
            income_statement=income_statement,
            balance_sheet=balance_sheet,
        )

    def _extract_notes_enhanced(self, base_result: Dict) -> Optional[NotesCollection]:
        """Extract enhanced notes information with MIXED approach."""
        from gracian_pipeline.models.base_fields import NumberField

        fin_data = base_result.get("financial_agent", {})

        # Note 8: Building Details
        building_details = None
        building_data = fin_data.get("building_details", {})
        if building_data:
            building_details = BuildingDetails(
                # ✅ Extracted: ExtractionField
                closing_acquisition_value=NumberField(
                    value=self._to_decimal(building_data.get("ackumulerade_anskaffningsvarden")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(building_data.get("ackumulerade_anskaffningsvarden")) is not None else None,
                current_year_depreciation=NumberField(
                    value=self._to_decimal(building_data.get("arets_avskrivningar")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(building_data.get("arets_avskrivningar")) is not None else None,
                planned_residual_value=NumberField(
                    value=self._to_decimal(building_data.get("planenligt_restvarde")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(building_data.get("planenligt_restvarde")) is not None else None,
                tax_assessment_building=NumberField(
                    value=self._to_decimal(building_data.get("taxeringsvarde_byggnad")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(building_data.get("taxeringsvarde_byggnad")) is not None else None,
                tax_assessment_land=NumberField(
                    value=self._to_decimal(building_data.get("taxeringsvarde_mark")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(building_data.get("taxeringsvarde_mark")) is not None else None,
                # ❌ Deprecated field: raw list (not ListField!)
                source_pages=fin_data.get("evidence_pages", [])
            )

        # Note 9: Receivables
        receivables_breakdown = None
        receivables_data = fin_data.get("receivables_breakdown", {})
        if receivables_data:
            receivables_breakdown = ReceivablesBreakdown(
                # ✅ Extracted: ExtractionField
                tax_account=NumberField(
                    value=self._to_decimal(receivables_data.get("skattekonto")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(receivables_data.get("skattekonto")) is not None else None,
                vat_deduction=NumberField(
                    value=self._to_decimal(receivables_data.get("momsavrakning")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(receivables_data.get("momsavrakning")) is not None else None,
                client_funds=NumberField(
                    value=self._to_decimal(receivables_data.get("klientmedel")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(receivables_data.get("klientmedel")) is not None else None,
                receivables=NumberField(
                    value=self._to_decimal(receivables_data.get("fordringar")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(receivables_data.get("fordringar")) is not None else None,
                other_deductions=NumberField(
                    value=self._to_decimal(receivables_data.get("avrakning_ovrigt")),
                    confidence=0.9,
                    source="llm_extraction"
                ) if self._to_decimal(receivables_data.get("avrakning_ovrigt")) is not None else None,
                # ❌ Deprecated field: raw list (not ListField!)
                source_pages=fin_data.get("evidence_pages", [])
            )

        if building_details or receivables_breakdown:
            return NotesCollection(
                # ❌ Structural fields: raw objects (not wrapped)
                note_8_buildings=building_details,
                note_9_receivables=receivables_breakdown,
            )

        return None

    def _extract_property_enhanced(self, base_result: Dict) -> Optional[PropertyDetails]:
        """Extract enhanced property information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField, NumberField

        prop_data = base_result.get("property_agent", {})

        if not prop_data:
            return None

        # Apartment distribution
        apartment_dist = None
        apt_data = prop_data.get("apartment_breakdown", {})
        if apt_data:
            apartment_dist = ApartmentDistribution(
                # ❌ Structural data: raw integers (apartment counts)
                one_room=apt_data.get("1_rok", 0),
                two_rooms=apt_data.get("2_rok", 0),
                three_rooms=apt_data.get("3_rok", 0),
                four_rooms=apt_data.get("4_rok", 0),
                five_rooms=apt_data.get("5_rok", 0),
                more_than_five=apt_data.get(">5_rok", 0)
            )

        # Commercial tenants
        commercial_tenants = []
        for tenant in (prop_data.get("commercial_tenants") or []):
            if isinstance(tenant, dict):
                commercial_tenants.append(CommercialTenant(
                    # ✅ Extracted: ExtractionField
                    business_name=StringField(
                        value=tenant.get("business_name", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    business_type=StringField(
                        value=tenant.get("business_type", ""),
                        confidence=0.8 if tenant.get("business_type") else 0.5,
                        source="llm_extraction"
                    ) if tenant.get("business_type") else None,
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=prop_data.get("evidence_pages", [])
                ))

        # Common areas
        common_areas = []
        for area in (prop_data.get("common_areas") or []):
            if isinstance(area, dict):
                common_areas.append(CommonArea(
                    # ✅ Extracted: ExtractionField
                    name=StringField(
                        value=area.get("name", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    description=StringField(
                        value=area.get("description", ""),
                        confidence=0.8 if area.get("description") else 0.5,
                        source="llm_extraction"
                    ) if area.get("description") else None,
                ))

        return PropertyDetails(
            # ✅ Extracted: ExtractionField
            property_designation=StringField(
                value=prop_data.get("property_designation", ""),
                confidence=0.9 if prop_data.get("property_designation") else 0.5,
                source="llm_extraction"
            ) if prop_data.get("property_designation") else None,
            municipality=StringField(
                value=prop_data.get("municipality", ""),
                confidence=0.9 if prop_data.get("municipality") else 0.5,
                source="llm_extraction"
            ) if prop_data.get("municipality") else None,
            total_apartments=NumberField(
                value=prop_data.get("total_apartments", 0),
                confidence=0.85,
                source="llm_extraction"
            ) if prop_data.get("total_apartments") else None,
            # ❌ Structural fields: raw objects and lists
            apartment_distribution=apartment_dist,
            commercial_tenants=commercial_tenants,
            common_areas=common_areas,
            # ❌ Deprecated field: raw list (not ListField!)
            source_pages=prop_data.get("evidence_pages", [])
        )

    def _extract_fees_enhanced(self, base_result: Dict) -> Optional[FeeStructure]:
        """Extract enhanced fee information with MIXED approach."""
        from gracian_pipeline.models.base_fields import NumberField

        fees_data = base_result.get("fees_agent", {})

        if not fees_data:
            return None

        return FeeStructure(
            # ✅ Extracted: ExtractionField
            annual_fee_per_sqm=NumberField(
                value=self._to_decimal(fees_data.get("arsavgift_per_sqm")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fees_data.get("arsavgift_per_sqm")) is not None else None,
            # ❌ Deprecated field: raw list (not ListField!)
            source_pages=fees_data.get("evidence_pages", [])
        )

    def _extract_loans_enhanced(self, base_result: Dict) -> List[LoanDetails]:
        """Extract enhanced loan information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField, NumberField

        loans_data = base_result.get("loans_agent", {})
        loans = []

        for loan in (loans_data.get("loans") or []):
            if isinstance(loan, dict):
                loans.append(LoanDetails(
                    # ✅ Extracted: ExtractionField
                    lender=StringField(
                        value=loan.get("lender", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    outstanding_balance=NumberField(
                        value=self._to_decimal(loan.get("outstanding_balance", 0)),
                        confidence=0.9,
                        source="llm_extraction"
                    ) if self._to_decimal(loan.get("outstanding_balance", 0)) is not None else None,
                    interest_rate=NumberField(
                        value=loan.get("interest_rate", 0.0),
                        confidence=0.85 if loan.get("interest_rate") else 0.5,
                        source="llm_extraction"
                    ) if loan.get("interest_rate") else None,
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=loans_data.get("evidence_pages", [])
                ))

        return loans

    def _extract_operations_enhanced(self, base_result: Dict) -> Optional[OperationsData]:
        """Extract enhanced operations information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField, NumberField

        ops_data = base_result.get("operations_agent", {})

        if not ops_data:
            return None

        # Suppliers
        suppliers = []
        for supplier in (ops_data.get("suppliers") or []):
            if isinstance(supplier, dict):
                suppliers.append(Supplier(
                    # ✅ Extracted: ExtractionField
                    company_name=StringField(
                        value=supplier.get("company_name", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    service_type=StringField(
                        value=supplier.get("service_type", "Unknown"),
                        confidence=0.8,
                        source="llm_extraction"
                    ),
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=ops_data.get("evidence_pages", [])
                ))

        # Maintenance items
        maintenance = []
        for item in (ops_data.get("planned_maintenance") or []):
            if isinstance(item, dict):
                maintenance.append(MaintenanceItem(
                    # ✅ Extracted: ExtractionField
                    description=StringField(
                        value=item.get("description", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    planned_year=NumberField(
                        value=item.get("planned_year", 0),
                        confidence=0.8 if item.get("planned_year") else 0.5,
                        source="llm_extraction"
                    ) if item.get("planned_year") else None,
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=ops_data.get("evidence_pages", [])
                ))

        if suppliers or maintenance:
            return OperationsData(
                # ❌ Structural fields: raw lists of objects
                suppliers=suppliers,
                planned_maintenance=maintenance,
                # ❌ Deprecated field: raw list (not ListField!)
                source_pages=ops_data.get("evidence_pages", [])
            )

        return None

    def _extract_events_enhanced(self, base_result: Dict) -> List[Event]:
        """Extract enhanced events information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField

        events_data = base_result.get("events_agent", {})
        events = []

        for event in (events_data.get("events") or []):
            if isinstance(event, dict):
                events.append(Event(
                    # ✅ Extracted: ExtractionField
                    event_type=StringField(
                        value=event.get("event_type", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    description=StringField(
                        value=event.get("description", ""),
                        confidence=0.8,
                        source="llm_extraction"
                    ),
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=events_data.get("evidence_pages", [])
                ))

        return events

    def _extract_policies_enhanced(self, base_result: Dict) -> List[Policy]:
        """Extract enhanced policies information with MIXED approach."""
        from gracian_pipeline.models.base_fields import StringField

        policies_data = base_result.get("policies_agent", {})
        policies = []

        for policy in (policies_data.get("policies") or []):
            if isinstance(policy, dict):
                policies.append(Policy(
                    # ✅ Extracted: ExtractionField
                    policy_name=StringField(
                        value=policy.get("policy_name", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    policy_description=StringField(
                        value=policy.get("description", ""),
                        confidence=0.8,
                        source="llm_extraction"
                    ),
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=policies_data.get("evidence_pages", [])
                ))

        return policies

    def _calculate_quality_metrics(self, base_result: Dict) -> Dict[str, float]:
        """Calculate extraction quality metrics."""
        # FIXED: Base extractor stores in "_quality_metrics", not "_quality"
        quality = base_result.get("_quality_metrics", {})

        # FIXED: Map base extractor keys to Pydantic schema keys
        return {
            "coverage_percentage": quality.get("coverage_percent", 0),  # Note: no "age" suffix in base
            "confidence_score": 0.85 if quality.get("coverage_percent", 0) > 70 else 0.5,  # Derived from coverage
            "total_fields": quality.get("total_fields", 0),  # Not "total_fields_extracted"
            "evidence_ratio": quality.get("extracted_fields", 0) / max(quality.get("total_fields", 1), 1),  # Calculated
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
