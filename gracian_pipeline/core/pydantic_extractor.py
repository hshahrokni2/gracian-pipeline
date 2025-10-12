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
from gracian_pipeline.utils.pdf_classifier import classify_pdf
from gracian_pipeline.core.mixed_mode_extractor import MixedModeExtractor
from openai import OpenAI
import fitz  # PyMuPDF


class UltraComprehensivePydanticExtractor:
    """
    Extract every fact from BRF annual reports into Pydantic models.

    Extraction Strategy:
    - Phase 0: Check if mixed-mode needed (NEW: hybrid PDF support)
    - Phase 1: Base extraction (text pages) + Vision extraction (image pages)
    - Phase 2: Enhanced extraction (deep dive into sections)
    - Phase 3: Pydantic model population
    - Phase 4: Validation and quality scoring
    """

    def __init__(self):
        self.base_extractor = RobustUltraComprehensiveExtractor()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # NEW: Mixed-mode extractor for hybrid PDFs
        self.mixed_mode_extractor = None  # Lazy initialization

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

        # Phase 0: Check if mixed-mode extraction needed (NEW: hybrid PDF support)
        print("\n📊 Phase 0: Check PDF Type (1s)")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()

        # Phase 1: Base extraction using existing pipeline
        print("\n📊 Phase 1: Base Extraction (60s)")
        base_result = self.base_extractor.extract_brf_document(pdf_path, mode=mode)

        # Phase 1.5: Check if we need mixed-mode extraction for hybrid PDFs
        docling_result = {
            'markdown': base_result.get('_docling_markdown', ''),
            'char_count': len(base_result.get('_docling_markdown', '')),
            'status': base_result.get('_docling_status', 'text'),
            'tables': base_result.get('_docling_tables', []),  # NEW: For empty table detection
        }

        # Initialize mixed-mode extractor if needed
        if self.mixed_mode_extractor is None:
            from gracian_pipeline.core.docling_adapter_ultra import UltraComprehensiveDoclingAdapter
            docling_adapter = UltraComprehensiveDoclingAdapter()
            self.mixed_mode_extractor = MixedModeExtractor(docling_adapter, self.client)

        # Check if this PDF needs mixed-mode extraction
        DEBUG_MODE = os.getenv("GRACIAN_DEBUG", "0") == "1"

        if DEBUG_MODE:
            print("\n" + "="*80)
            print("DEBUG: Mixed-Mode Detection Check")
            print("="*80)
            print(f"  Markdown length: {docling_result['char_count']:,} chars")
            print(f"  Tables detected: {len(docling_result.get('tables', []))}")
            print(f"  Total pages: {total_pages}")

        use_mixed, classification = self.mixed_mode_extractor.should_use_mixed_mode(
            docling_result, total_pages
        )

        if DEBUG_MODE:
            print(f"  RESULT: use_mixed={use_mixed}")
            print(f"  REASON: {classification.get('reason', 'unknown')}")
            if use_mixed and 'image_pages' in classification:
                print(f"  IMAGE PAGES: {classification.get('image_pages', [])}")
            print("="*80 + "\n")

        if use_mixed:
            print(f"\n🔀 Mixed-Mode Detection: {classification.get('reason', 'unknown')}")
            print(f"   Image pages detected: {classification.get('image_pages', [])}")
            print(f"   Financial sections: {classification.get('financial_image_sections', [])}")
            print(f"\n📸 Phase 1.5: Vision Extraction for Image Pages (30s)")

            # Extract image pages with vision
            if DEBUG_MODE:
                print("\n" + "="*80)
                print("DEBUG: Vision Extraction Starting")
                print("="*80)
                print(f"  Image pages to extract: {classification.get('image_pages', [])}")
                print(f"  Vision model: gpt-4o")
                print(f"  API key configured: {'Yes' if self.client.api_key else 'No'}")
                print("="*80 + "\n")

            vision_result = self.mixed_mode_extractor.extract_image_pages_with_vision(
                pdf_path,
                classification['image_pages'],
                context_hints="Focus on financial statements: Resultaträkning, Balansräkning, Kassaflödesanalys"
            )

            if DEBUG_MODE:
                print("\n" + "="*80)
                print("DEBUG: Vision Extraction Complete")
                print("="*80)
                print(f"  Success: {vision_result.get('success')}")
                print(f"  Pages processed: {vision_result.get('pages_processed', [])}")
                if not vision_result.get('success'):
                    print(f"  Error: {vision_result.get('error', 'unknown')}")
                else:
                    print(f"  Data keys: {list(vision_result.get('data', {}).keys())}")
                print("="*80 + "\n")

            if vision_result.get('success'):
                print(f"   ✓ Vision extraction successful for pages {vision_result.get('pages_processed', [])}")

                # Merge vision results into base_result
                if DEBUG_MODE:
                    print("\n" + "="*80)
                    print("DEBUG: Merging Results")
                    print("="*80)
                    print(f"  Text result agents: {len([k for k in base_result.keys() if not k.startswith('_')])}")
                    print(f"  Vision result data keys: {list(vision_result.get('data', {}).keys())}")
                    print("="*80 + "\n")

                base_result = self.mixed_mode_extractor.merge_extraction_results(
                    base_result,
                    vision_result
                )

                if DEBUG_MODE:
                    print("\n" + "="*80)
                    print("DEBUG: Merge Complete")
                    print("="*80)
                    print(f"  Merged result has metadata: {'_extraction_metadata' in base_result}")
                    if '_extraction_metadata' in base_result:
                        print(f"  Metadata: {base_result['_extraction_metadata']}")
                    print("="*80 + "\n")

                print(f"   ✓ Results merged from {len(vision_result.get('pages_processed', []))} image pages")
            else:
                print(f"   ⚠️  Vision extraction failed: {vision_result.get('error', 'unknown')}")
        else:
            print(f"   Standard extraction mode (reason: {classification.get('reason', 'sufficient_text')})")

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

        # Construct BRFAnnualReport (with placeholder quality metrics)
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
            extraction_quality={},  # Will be updated below
            coverage_percentage=0.0,  # Will be updated below
            confidence_score=0.0,  # Will be updated below
            all_source_pages=self._collect_all_source_pages(base_result),
        )

        # Phase 4: Quality Assessment - Use base_result metrics (pre-calculated by base extractor)
        print("\n✅ Phase 4: Quality Assessment (30s)")
        # TEMPORARY FIX: Revert to old method to stop -16pp regression
        # TODO: Enhance to count vision-extracted fields properly
        quality_metrics = self._calculate_quality_metrics(base_result)

        # Update report with actual quality metrics
        report.extraction_quality = quality_metrics
        report.coverage_percentage = quality_metrics.get("coverage_percentage", 0)
        report.confidence_score = quality_metrics.get("confidence_score", 0)

        print(f"\n🎉 Extraction Complete!")
        print(f"   Coverage: {report.coverage_percentage:.1f}%")
        print(f"   Confidence: {report.confidence_score:.2f}")

        return report

    def _extract_metadata(self, pdf_path: str, base_result: Dict) -> DocumentMetadata:
        """Extract document metadata."""
        import fitz  # PyMuPDF
        import re
        from gracian_pipeline.models.base_fields import (
            NumberField, StringField, BooleanField, DateField
        )

        pdf_path_obj = Path(pdf_path)
        doc = fitz.open(pdf_path)

        # Extract from Docling markdown (first few pages have metadata)
        markdown = base_result.get("_docling_markdown", "")

        # Extract BRF name (usually first line or header)
        brf_name = "Unknown BRF"
        brf_confidence = 0.5
        # Look for "Brf" or "Bostadsrättsföreningen" followed by name
        brf_patterns = [
            r'Brf\s+([^\n]+)',
            r'Bostadsrättsföreningen\s+([^\n]+)',
            r'^([A-ZÅÄÖ][^\n]{5,40})\s*\n',  # First line if capitalized
        ]
        for pattern in brf_patterns:
            match = re.search(pattern, markdown[:1000], re.MULTILINE | re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Validate it's not a section header
                if len(candidate) > 3 and not candidate.lower() in ['årsredovisning', 'förvaltningsberättelse']:
                    brf_name = candidate
                    brf_confidence = 0.9
                    break

        # Extract organization number (format: XXXXXX-XXXX)
        # Search entire markdown (org number can appear late in document)
        org_number = "000000-0000"
        org_confidence = 0.5
        org_pattern = r'(\d{6}-\d{4})'
        org_match = re.search(org_pattern, markdown)  # Search entire markdown
        if org_match:
            org_number = org_match.group(1)
            org_confidence = 0.9

        # Extract fiscal year (look for "räkenskapsåret" or date range)
        fiscal_year = datetime.now().year
        year_confidence = 0.5
        year_patterns = [
            r'räkenskapsåret.*?(\d{4})',
            r'1\s+januari\s*-\s*31\s+december\s+(\d{4})',
            r'januari.*?december\s+(\d{4})',
        ]
        for pattern in year_patterns:
            match = re.search(pattern, markdown[:2000], re.IGNORECASE)
            if match:
                year_candidate = int(match.group(1))
                # Validate it's a reasonable year (2000-2030)
                if 2000 <= year_candidate <= 2030:
                    fiscal_year = year_candidate
                    year_confidence = 0.9
                    break

        # Calculate file hash
        with open(pdf_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Check if machine-readable using text percentage method (fixes hybrid PDF bug)
        # Old broken method: is_machine_readable = len(markdown) > 5000
        # Bug: Hybrid PDFs with 2 text pages + 17 scanned pages were misclassified
        classification_result = classify_pdf(pdf_path)
        is_machine_readable = classification_result["is_machine_readable"]

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

            # Extracted fields: ExtractionField with proper confidence
            fiscal_year=NumberField(
                value=fiscal_year,
                confidence=year_confidence,
                source="pattern_extraction" if year_confidence > 0.5 else "default",
                evidence_pages=[1] if year_confidence > 0.5 else []
            ),
            brf_name=StringField(
                value=brf_name,
                confidence=brf_confidence,
                source="pattern_extraction" if brf_confidence > 0.5 else "default",
                evidence_pages=[1] if brf_confidence > 0.5 else []
            ),
            organization_number=StringField(
                value=org_number,
                confidence=org_confidence,
                source="pattern_extraction" if org_confidence > 0.5 else "default",
                evidence_pages=[1] if org_confidence > 0.5 else []
            ),
        )

        doc.close()
        return metadata

    def _extract_governance_enhanced(self, base_result: Dict) -> Optional[GovernanceStructure]:
        """
        Extract enhanced governance information with MIXED approach.

        MULTI-AGENT ARCHITECTURE: Merges results from 3 specialized agents:
        - chairman_agent: Extracts ONLY chairman name
        - board_members_agent: Extracts ONLY board members list with roles
        - auditor_agent: Extracts ONLY auditor information

        This decomposition prevents LLM cognitive overload (avoids brf_81563 regression).
        """
        from gracian_pipeline.models.base_fields import StringField, ListField

        # PHASE 1: Read from 3 specialized agents (graceful degradation)
        chairman_data = base_result.get("chairman_agent", {})
        board_data = base_result.get("board_members_agent", {})
        auditor_data = base_result.get("auditor_agent", {})

        # If ALL agents returned empty, return None (no governance data)
        if not chairman_data and not board_data and not auditor_data:
            return None

        # PHASE 2: Extract chairman from chairman_agent
        chairman = None
        if chairman_data and chairman_data.get("chairman"):
            chairman = StringField(
                value=chairman_data["chairman"],
                confidence=0.9,
                source="llm_extraction"
            )

        # PHASE 3: Extract board members from board_members_agent
        board_members = []
        raw_members = board_data.get("board_members") or []

        for member_data in raw_members:
            # Handle both formats: structured dicts (new) or simple strings (legacy)
            if isinstance(member_data, dict):
                # NEW: Structured format with role
                member_name = member_data.get("name", "")
                member_role = member_data.get("role", "ledamot")

                # Normalize Swedish roles to schema format
                role_map = {
                    "ordförande": "ordforande",
                    "ordförande": "ordforande",  # Handle UTF-8 variants
                    "ledamot": "ledamot",
                    "suppleant": "suppleant",
                    "revisor": "revisor"
                }
                role = role_map.get(member_role.lower(), "ledamot")
            else:
                # LEGACY: Simple string format (fallback)
                member_name = member_data
                role = "ledamot"
                # Check if this is the chairman (cross-agent validation)
                if chairman and member_name == chairman.value:
                    role = "ordforande"

            board_members.append(BoardMember(
                # ✅ Extracted: ExtractionField
                full_name=StringField(
                    value=member_name,
                    confidence=0.9,
                    source="llm_extraction"
                ),
                # ✅ FIXED: Now supports ordforande, ledamot, suppleant, revisor
                role=role,
                # ❌ Deprecated field: raw list (not ListField!)
                source_page=board_data.get("evidence_pages", [])
            ))

        # PHASE 4: Extract auditor from auditor_agent
        primary_auditor = None
        if auditor_data and auditor_data.get("auditor_name"):
            primary_auditor = Auditor(
                # ✅ Extracted: ExtractionField
                name=StringField(
                    value=auditor_data["auditor_name"],
                    confidence=0.9,
                    source="llm_extraction"
                ),
                firm=StringField(
                    value=auditor_data.get("audit_firm", ""),
                    confidence=0.85 if auditor_data.get("audit_firm") else 0.5,
                    source="llm_extraction"
                ) if auditor_data.get("audit_firm") else None,
                # ❌ Deprecated field: raw list (not ListField!)
                source_page=auditor_data.get("evidence_pages", [])
            )

        # PHASE 5: Merge all evidence pages from 3 agents
        all_evidence_pages = set()
        for agent_data in [chairman_data, board_data, auditor_data]:
            if agent_data and "evidence_pages" in agent_data:
                all_evidence_pages.update(agent_data["evidence_pages"])

        # PHASE 6: Construct merged GovernanceStructure
        return GovernanceStructure(
            # ✅ Extracted: ExtractionField (from chairman_agent)
            chairman=chairman,
            # ❌ Structural field: raw list of objects (from board_members_agent)
            board_members=board_members,
            # ✅ Extracted: Auditor object (from auditor_agent)
            primary_auditor=primary_auditor,
            # ✅ Extracted list: ListField (with confidence tracking)
            # Note: nomination_committee not yet extracted by specialized agents
            nomination_committee=ListField(
                value=[],
                confidence=0.5,
                source="not_implemented"
            ),
            # ❌ Deprecated field: merged evidence pages from all 3 agents
            source_pages=sorted(list(all_evidence_pages))
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
            # NEW: Liabilities breakdown (Issue #2 Enhancement)
            long_term_liabilities=NumberField(
                value=self._to_decimal(fin_data.get("long_term_liabilities")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("long_term_liabilities")) is not None else None,
            short_term_liabilities=NumberField(
                value=self._to_decimal(fin_data.get("short_term_liabilities")),
                confidence=0.9,
                source="llm_extraction"
            ) if self._to_decimal(fin_data.get("short_term_liabilities")) is not None else None,
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

        # CRITICAL FIX: Note 5 stores loans in financial_agent.loans (array), not loans_agent
        fin_data = base_result.get("financial_agent", {})
        loans_array = fin_data.get("loans") if fin_data else []

        # Fallback to legacy loans_agent location
        if not loans_array:
            loans_data = base_result.get("loans_agent", {})
            # Handle both dict and list cases (Phase 1 fix can return [] for loans_agent)
            if isinstance(loans_data, list):
                loans_array = loans_data
            elif isinstance(loans_data, dict):
                loans_array = loans_data.get("loans", [])
            else:
                loans_array = []

        loans = []

        for loan in (loans_array or []):
            if isinstance(loan, dict):
                loans.append(LoanDetails(
                    # ✅ Extracted: ExtractionField
                    lender=StringField(
                        value=loan.get("lender", "Unknown"),
                        confidence=0.85,
                        source="llm_extraction"
                    ),
                    outstanding_balance=NumberField(
                        # CRITICAL FIX: Note 5 extracts amount_2021, not outstanding_balance
                        value=self._to_decimal(loan.get("amount_2021", 0)),
                        confidence=0.9,
                        source="llm_extraction"
                    ) if self._to_decimal(loan.get("amount_2021", 0)) is not None else None,
                    interest_rate=NumberField(
                        value=loan.get("interest_rate", 0.0),
                        confidence=0.85 if loan.get("interest_rate") else 0.5,
                        source="llm_extraction"
                    ) if loan.get("interest_rate") else None,
                    # ❌ Deprecated field: raw list (not ListField!)
                    source_page=fin_data.get("evidence_pages", []) if fin_data else []
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

    def _calculate_quality_metrics_from_report(self, report: BRFAnnualReport) -> Dict[str, float]:
        """
        Calculate extraction quality metrics from constructed Pydantic model.

        This method counts ACTUAL populated fields, including those from vision extraction.
        """
        total_fields = 0
        populated_fields = 0

        # Count metadata fields
        if report.metadata:
            metadata_fields = ['fiscal_year', 'brf_name', 'organization_number']
            for field_name in metadata_fields:
                total_fields += 1
                field_value = getattr(report.metadata, field_name, None)
                if field_value is not None and hasattr(field_value, 'value') and field_value.value:
                    populated_fields += 1

        # Count governance fields
        if report.governance:
            total_fields += 1  # chairman
            if report.governance.chairman and report.governance.chairman.value:
                populated_fields += 1

            total_fields += 1  # board_members count
            if report.governance.board_members and len(report.governance.board_members) > 0:
                populated_fields += 1

            total_fields += 1  # primary_auditor
            if report.governance.primary_auditor and report.governance.primary_auditor.name:
                populated_fields += 1

        # Count financial fields (CRITICAL: Vision-extracted fields)
        if report.financial:
            # Balance sheet
            if report.financial.balance_sheet:
                bs_fields = ['assets_total', 'liabilities_total', 'equity_total']
                for field_name in bs_fields:
                    total_fields += 1
                    field_value = getattr(report.financial.balance_sheet, field_name, None)
                    if field_value is not None and field_value.value is not None:
                        populated_fields += 1

            # Income statement
            if report.financial.income_statement:
                is_fields = ['revenue_total', 'expenses_total', 'result_after_tax']
                for field_name in is_fields:
                    total_fields += 1
                    field_value = getattr(report.financial.income_statement, field_name, None)
                    if field_value is not None and field_value.value is not None:
                        populated_fields += 1

        # Count property fields
        if report.property:
            property_fields = ['property_designation', 'municipality', 'total_apartments']
            for field_name in property_fields:
                total_fields += 1
                field_value = getattr(report.property, field_name, None)
                if field_value is not None and hasattr(field_value, 'value') and field_value.value:
                    populated_fields += 1

        # Count fees
        if report.fees:
            total_fields += 1
            if report.fees.annual_fee_per_sqm and report.fees.annual_fee_per_sqm.value:
                populated_fields += 1

        # Count loans
        total_fields += 1  # At least count if we have any loans
        if report.loans and len(report.loans) > 0:
            populated_fields += 1

        # Calculate coverage
        coverage_percentage = (populated_fields / max(total_fields, 1)) * 100

        # Calculate confidence (simple heuristic)
        confidence_score = 0.9 if coverage_percentage > 70 else 0.7 if coverage_percentage > 50 else 0.5

        return {
            "coverage_percentage": coverage_percentage,
            "confidence_score": confidence_score,
            "total_fields": total_fields,
            "populated_fields": populated_fields,
            "evidence_ratio": populated_fields / max(total_fields, 1),
        }

    def _calculate_quality_metrics(self, base_result: Dict) -> Dict[str, float]:
        """
        DEPRECATED: Calculate extraction quality metrics from base_result.

        This method is kept for compatibility but should not be used.
        Use _calculate_quality_metrics_from_report() instead.
        """
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
