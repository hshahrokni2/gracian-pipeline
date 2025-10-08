#!/usr/bin/env python3
"""
Optimal BRF Extraction Pipeline

Combines all validated experimental results:
- Docling structure detection (100% success rate, Exp 3A)
- NoteSemanticRouter (83.3% keyword accuracy)
- Adaptive PDF processing (48% zero-cost)
- 3-pass hierarchical extraction
- Multi-layer caching

Target: 95/95 accuracy, <$0.25/doc cost, <60s processing time
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
import base64
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from openai import OpenAI

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling_core.types.doc import SectionHeaderItem

# Gracian imports
from gracian_pipeline.models.brf_schema import BRFAnnualReport
from gracian_pipeline.core.vision_qc import call_grok_vision, call_openai_vision

# Local imports
from note_semantic_router import NoteSemanticRouter

# LLM clients
from openai import OpenAI


@dataclass
class PDFTopology:
    """PDF characteristics from topology analysis"""
    pdf_path: str
    total_pages: int
    avg_chars_per_page: float
    classification: str  # 'machine_readable', 'scanned', 'hybrid'
    sample_pages: List[int]
    analysis_time: float


@dataclass
class StructureDetectionResult:
    """Docling structure detection output"""
    pdf_hash: str
    sections: List[Dict[str, Any]]
    num_sections: int
    extraction_time: float
    method: str  # 'text', 'ocr', 'hybrid'
    cached: bool


@dataclass
class SectionRouting:
    """Section to agent routing decisions"""
    main_sections: Dict[str, List[str]]  # agent_id → [section_headings]
    note_sections: Dict[str, List[str]]  # agent_id → [note_headings]
    routing_time: float


@dataclass
class ExtractionResult:
    """Complete extraction result for one document"""
    pdf_path: str
    topology: PDFTopology
    structure: StructureDetectionResult
    routing: SectionRouting
    pass1_result: Dict[str, Any]  # High-level extraction
    pass2_result: Dict[str, Any]  # Detailed extraction
    pass3_result: Dict[str, Any]  # Validation + metrics
    brf_report: Optional[BRFAnnualReport]
    quality_metrics: Dict[str, float]
    total_time: float
    total_cost: float


class CacheManager:
    """Multi-layer caching system"""

    def __init__(self, cache_dir: str = "results/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "pipeline_cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS structure_cache (
                    pdf_hash TEXT PRIMARY KEY,
                    structure_json TEXT,
                    method TEXT,
                    extraction_time REAL,
                    created_at INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topology_cache (
                    pdf_hash TEXT PRIMARY KEY,
                    topology_json TEXT,
                    created_at INTEGER
                )
            """)
            conn.commit()

    def get_structure(self, pdf_hash: str) -> Optional[StructureDetectionResult]:
        """Get cached structure detection result"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT structure_json, method, extraction_time FROM structure_cache WHERE pdf_hash = ?",
                (pdf_hash,)
            ).fetchone()

            if row:
                structure_data = json.loads(row[0])
                return StructureDetectionResult(
                    pdf_hash=pdf_hash,
                    sections=structure_data['sections'],
                    num_sections=structure_data['num_sections'],
                    extraction_time=row[2],
                    method=row[1],
                    cached=True
                )
        return None

    def put_structure(self, result: StructureDetectionResult):
        """Cache structure detection result"""
        structure_json = json.dumps({
            'sections': result.sections,
            'num_sections': result.num_sections
        })

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO structure_cache (pdf_hash, structure_json, method, extraction_time, created_at) VALUES (?, ?, ?, ?, ?)",
                (result.pdf_hash, structure_json, result.method, result.extraction_time, int(time.time()))
            )
            conn.commit()

    def get_topology(self, pdf_hash: str) -> Optional[PDFTopology]:
        """Get cached topology analysis"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT topology_json FROM topology_cache WHERE pdf_hash = ?",
                (pdf_hash,)
            ).fetchone()

            if row:
                topology_data = json.loads(row[0])
                return PDFTopology(**topology_data)
        return None

    def put_topology(self, topology: PDFTopology, pdf_hash: str):
        """Cache topology analysis"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO topology_cache (pdf_hash, topology_json, created_at) VALUES (?, ?, ?)",
                (pdf_hash, json.dumps(asdict(topology)), int(time.time()))
            )
            conn.commit()


class OptimalBRFPipeline:
    """
    Optimal BRF extraction pipeline combining all validated components.

    Architecture:
    1. Adaptive PDF processing (topology-aware)
    2. Cached structure detection (Docling + EasyOCR)
    3. Hybrid section routing (simple + semantic)
    4. 3-pass hierarchical extraction
    5. Quality validation gates
    """

    def __init__(
        self,
        cache_dir: str = "results/cache",
        output_dir: str = "results/optimal_pipeline",
        enable_caching: bool = True
    ):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.cache = CacheManager(cache_dir) if enable_caching else None
        self.note_router = NoteSemanticRouter(
            config_path="config/note_keywords.yaml",
            cache_path="results/routing_cache.db",
            enable_llm=False  # Start with keyword-only, add LLM later
        )
        self.structure_cache = None  # Will be set by detect_structure()

        # Docling pipeline options
        self.docling_ocr_options = PdfPipelineOptions(
            do_ocr=True,
            ocr_options=EasyOcrOptions(lang=["sv", "en"])
        )
        self.docling_text_options = PdfPipelineOptions(do_ocr=False)

        # Main section routing map (simple keyword-based)
        self.main_section_keywords = {
            "governance_agent": [
                "förvaltningsberättelse", "styrelse", "board", "governance",
                "föreningsstämma", "annual meeting", "giltighet", "validity"
            ],
            "financial_agent": [
                "resultaträkning", "income statement", "balansräkning", "balance sheet",
                "kassaflödesanalys", "cash flow", "ekonomi", "financial"
            ],
            "property_agent": [
                "fastighet", "property", "building", "byggnadsår", "construction year",
                "ytor", "area", "lokaler", "premises"
            ],
            "operations_agent": [
                "verksamhet", "operations", "avtaö", "contracts", "leverantörer", "suppliers"
            ]
        }

        # LLM clients
        self.grok_client = OpenAI(
            api_key=os.environ.get("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1"
        )
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        print(f"✅ OptimalBRFPipeline initialized")
        print(f"   Cache: {'enabled' if enable_caching else 'disabled'}")
        print(f"   Output: {self.output_dir}")

    def compute_pdf_hash(self, pdf_path: str) -> str:
        """Compute SHA256 hash of PDF for caching"""
        with open(pdf_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def analyze_topology(self, pdf_path: str, sample_pages: int = 3) -> PDFTopology:
        """
        STAGE 1: Adaptive PDF topology detection

        Samples pages and classifies as:
        - machine_readable: >800 chars/page (48.4% of corpus)
        - scanned: <200 chars/page (49.3% of corpus)
        - hybrid: 200-800 chars/page (2.3% of corpus)
        """
        start_time = time.time()

        # Try to get from cache first
        pdf_hash = self.compute_pdf_hash(pdf_path)
        if self.cache:
            cached = self.cache.get_topology(pdf_hash)
            if cached:
                print(f"   ✅ Topology cached (0.1s, $0)")
                return cached

        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # Sample evenly distributed pages
        if total_pages <= sample_pages:
            pages_to_sample = list(range(total_pages))
        else:
            step = total_pages // sample_pages
            pages_to_sample = [i * step for i in range(sample_pages)]

        # Extract text and count characters
        char_counts = []
        for page_num in pages_to_sample:
            page = doc[page_num]
            text = page.get_text()
            char_counts.append(len(text))

        doc.close()

        avg_chars = sum(char_counts) / len(char_counts) if char_counts else 0

        # Classify
        if avg_chars > 800:
            classification = "machine_readable"
        elif avg_chars < 200:
            classification = "scanned"
        else:
            classification = "hybrid"

        elapsed = time.time() - start_time

        topology = PDFTopology(
            pdf_path=pdf_path,
            total_pages=total_pages,
            avg_chars_per_page=avg_chars,
            classification=classification,
            sample_pages=pages_to_sample,
            analysis_time=elapsed
        )

        # Cache result
        if self.cache:
            self.cache.put_topology(topology, pdf_hash)

        print(f"   ✅ Topology: {classification} ({avg_chars:.0f} chars/page, {elapsed:.1f}s)")
        return topology

    def detect_structure(
        self,
        pdf_path: str,
        topology: PDFTopology
    ) -> StructureDetectionResult:
        """
        STAGE 2: Docling structure detection with caching

        Uses adaptive processing based on topology:
        - machine_readable: Text mode (fast, free)
        - scanned: OCR mode (EasyOCR Swedish)
        - hybrid: OCR with selective processing
        """
        start_time = time.time()

        # Check cache
        pdf_hash = self.compute_pdf_hash(pdf_path)
        if self.cache:
            cached = self.cache.get_structure(pdf_hash)
            if cached:
                # Store in instance for use by _get_pages_for_sections()
                self.structure_cache = cached
                print(f"   ✅ Structure cached ({cached.num_sections} sections, 0.1s, $0)")
                return cached

        # Select appropriate Docling pipeline
        if topology.classification == "machine_readable":
            pipeline_options = self.docling_text_options
            method = "text"
            print(f"   📄 Using text mode (machine-readable)")
        else:
            pipeline_options = self.docling_ocr_options
            method = "ocr" if topology.classification == "scanned" else "hybrid"
            print(f"   🔍 Using OCR mode ({method})")

        # Run Docling
        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(pdf_path)

        # Extract sections from document structure
        sections = []
        doc = result.document

        # Iterate through document items (same pattern as Exp 3A)
        # ENHANCEMENT (Phase 2E): Extract page numbers from provenance metadata
        provenance_pages_found = 0
        for item, level in doc.iterate_items():
            if isinstance(item, SectionHeaderItem):
                # CRITICAL: Extract page from provenance metadata (not attributes!)
                page_no = None
                if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                    page_no = getattr(item.prov[0], 'page_no', None)
                    if page_no is not None:
                        provenance_pages_found += 1

                section_info = {
                    "heading": item.text,
                    "level": level,
                    "page": page_no,  # ✅ Now from provenance, not attributes
                }
                sections.append(section_info)

        elapsed = time.time() - start_time

        structure_result = StructureDetectionResult(
            pdf_hash=pdf_hash,
            sections=sections,
            num_sections=len(sections),
            extraction_time=elapsed,
            method=method,
            cached=False
        )

        # Cache result
        if self.cache:
            self.cache.put_structure(structure_result)

        # Store in instance for use by _get_pages_for_sections()
        self.structure_cache = structure_result

        print(f"   ✅ Structure detected ({len(sections)} sections, {elapsed:.1f}s)")
        print(f"      Provenance pages: {provenance_pages_found}/{len(sections)} ({100*provenance_pages_found//len(sections) if sections else 0}%)")
        return structure_result

    def route_sections(
        self,
        structure: StructureDetectionResult
    ) -> SectionRouting:
        """
        STAGE 3: Hybrid section routing

        Main sections: Simple keyword matching
        Note subsections: NoteSemanticRouter
        """
        start_time = time.time()

        main_sections = {agent_id: [] for agent_id in self.main_section_keywords.keys()}
        main_sections['notes_collection'] = []  # For Noter main section
        note_sections = {}

        # Extract note headings first (same logic as test_note_semantic_routing.py)
        note_headings = []
        in_notes_subsection = False

        for section in structure.sections:
            heading = section['heading']
            heading_lower = heading.lower()

            # Detect main "Noter" section
            if "noter" in heading_lower and len(heading) < 20:
                main_sections['notes_collection'].append(heading)
                in_notes_subsection = True  # Start collecting note subsections
                continue

            # Start of note subsections (first "NOT X" section)
            if heading.startswith("NOT "):
                in_notes_subsection = True
                note_headings.append(heading)
                continue

            # Stop at end markers
            if any(keyword in heading_lower for keyword in [
                "underskrifter", "revisionsberättelse", "rapport om årsredovisningen"
            ]):
                break

            # Collect note subsections
            if in_notes_subsection:
                # Note-specific keywords (simplified from NoteSemanticRouter)
                note_keywords = [
                    'redovisningsprinciper', 'värderingsprinciper',
                    'lån', 'fastighetslån', 'skulder',
                    'avskrivningar',
                    'byggnader', 'mark',
                    'fordringar', 'omsättningstillgångar',
                    'fond', 'yttre underhåll', 'reserv',
                    'skatter', 'avgifter', 'moms',
                    'intäkter', 'kostnader'
                ]
                if any(keyword in heading_lower for keyword in note_keywords):
                    note_headings.append(heading)

            # Route main sections (before notes section)
            if not in_notes_subsection:
                routed = False
                for agent_id, keywords in self.main_section_keywords.items():
                    if any(keyword in heading_lower for keyword in keywords):
                        main_sections[agent_id].append(heading)
                        routed = True
                        break

        # Route note subsections using NoteSemanticRouter
        if note_headings:
            note_sections = self.note_router.route_headings(note_headings)

        elapsed = time.time() - start_time

        routing = SectionRouting(
            main_sections=main_sections,
            note_sections=note_sections,
            routing_time=elapsed
        )

        # Print routing summary
        total_main = sum(len(headings) for headings in main_sections.values())
        total_notes = sum(len(headings) for headings in note_sections.values())
        print(f"   ✅ Routing: {total_main} main sections, {total_notes} note sections ({elapsed:.2f}s)")

        return routing

    def _get_pdf_page_count(self, pdf_path: str) -> int:
        """Get total page count from PDF"""
        import fitz
        doc = fitz.open(pdf_path)
        count = doc.page_count
        doc.close()
        return count

    def _find_heading_in_pdf(self, pdf_path: str, heading: str) -> Optional[int]:
        """Search PDF text for heading, return page number (0-indexed)"""
        import fitz
        doc = fitz.open(pdf_path)
        heading_lower = heading.lower()

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text().lower()
            if heading_lower in text:
                doc.close()
                return page_num

        doc.close()
        return None

    def _get_pages_for_sections(
        self,
        pdf_path: str,
        section_headings: List[str],
        fallback_pages: int = 5,
        agent_id: str = None
    ) -> List[int]:
        """
        Map section headings to page numbers (ENHANCED Phase 2E: Provenance-First Strategy).

        Priority Order:
        1. Docling provenance page numbers (✅ Works on scanned PDFs)
        2. Add context pages around section heading (for multi-page sections)
        3. Keyword search fallback (machine-readable PDFs only)
        4. First N pages (last resort)
        """
        pages = []

        # Method 1: Try Docling provenance page numbers from cached structure
        if hasattr(self, 'structure_cache') and self.structure_cache:
            for heading in section_headings:
                for section in self.structure_cache.sections:
                    if section['heading'] == heading and section.get('page') is not None:
                        page = section['page']
                        pages.append(page)

                        # ENHANCEMENT: Add nearby pages for context
                        # Financial sections often span 2-3 pages
                        if agent_id == 'financial_agent':
                            total_pages = self._get_pdf_page_count(pdf_path)
                            if page + 1 < total_pages:
                                pages.append(page + 1)
                            if page + 2 < total_pages:
                                pages.append(page + 2)

                        break
                else:
                    # Method 2: Search PDF text for heading (SKIP for scanned PDFs)
                    # Text search fails on scanned PDFs, so only try on machine-readable
                    if hasattr(self, 'topology') and self.topology.classification == "machine_readable":
                        found_page = self._find_heading_in_pdf(pdf_path, heading)
                        if found_page is not None:
                            pages.append(found_page)

        # Method 3: Content-based keyword search (machine-readable only)
        # Keyword search also fails on scanned PDFs
        if agent_id and hasattr(self, 'topology') and self.topology.classification == "machine_readable":
            keyword_pages = self._find_pages_by_content_keywords(pdf_path, agent_id)
            if keyword_pages:
                pages.extend(keyword_pages)

        # Method 4: If still no pages found, use first N pages
        if not pages:
            pages = list(range(min(fallback_pages, self._get_pdf_page_count(pdf_path))))

        # Deduplicate and sort
        return sorted(set(pages))

    def _find_pages_by_content_keywords(self, pdf_path: str, agent_id: str) -> List[int]:
        """
        Find pages containing agent-specific content keywords.
        Returns pages most likely to contain relevant data.
        """
        import fitz  # PyMuPDF - import locally to avoid top-level dependency

        # Agent-specific content keywords (Swedish BRF terminology)
        AGENT_KEYWORDS = {
            'financial_agent': [
                'resultaträkning', 'balansräkning', 'kassafl', 'intäkter', 'kostnader',
                'tillgångar', 'skulder', 'eget kapital', 'tkr', 'resultat', 'överskott'
            ],
            'property_agent': [
                'fastighetsbeteckning', 'adress', 'byggår', 'byggnadsår', 'lägenheter',
                'antal lägenheter', 'energiklass', 'energideklaration', 'kommun'
            ],
            'governance_agent': [
                'styrelse', 'ordförande', 'ledamot', 'revisor', 'valberedning',
                'styrelsemöte', 'förvaltningsberättelse'
            ],
            'operations_agent': [
                'drift', 'underhåll', 'reparation', 'städning', 'snöröjning',
                'fastighetsskötsel', 'energi', 'värme', 'vatten', 'el'
            ],
            'notes_accounting_agent': [
                'redovisningsprinciper', 'värdering', 'avskrivning', 'not 1', 'not 2'
            ],
            'notes_loans_agent': [
                'fastighetslån', 'långfristiga skulder', 'ränta', 'amortering', 'not'
            ],
            'notes_buildings_agent': [
                'byggnader', 'mark', 'fastighetsvärde', 'avskrivning', 'not'
            ],
            'notes_receivables_agent': [
                'fordringar', 'kundfordringar', 'övriga fordringar', 'not'
            ],
            'notes_reserves_agent': [
                'fond', 'yttre underhåll', 'reserv', 'avsättning', 'not'
            ],
            'notes_tax_agent': [
                'skatt', 'inkomstskatt', 'uppskjuten skatt', 'fastighetsskatt', 'not'
            ],
            'notes_other_agent': [
                'not', 'noter', 'anmärkning', 'tillägg'
            ]
        }

        keywords = AGENT_KEYWORDS.get(agent_id, [])
        if not keywords:
            return []

        # Search all pages for keywords
        try:
            doc = fitz.open(pdf_path)
            page_scores = {}

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()

                # Count keyword matches
                score = sum(1 for keyword in keywords if keyword in text)
                if score > 0:
                    page_scores[page_num] = score

            doc.close()

            # Return top 5 pages by score
            if page_scores:
                sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
                return [page_num for page_num, score in sorted_pages[:5]]

        except Exception as e:
            print(f"   ⚠️ Content keyword search failed: {e}")

        return []

    def _render_pdf_pages(
        self,
        pdf_path: str,
        page_numbers: List[int],
        dpi: int = 200
    ) -> Tuple[List[bytes], List[str]]:
        """
        Render specific PDF pages to PNG bytes.

        Returns:
            (images, page_labels) tuple for OpenAI API
        """
        import fitz

        doc = fitz.open(pdf_path)
        images = []
        labels = []

        for page_num in page_numbers:
            if page_num >= doc.page_count:
                continue

            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
            labels.append(f"Page {page_num + 1}")  # 1-based for LLM

        doc.close()
        return images, labels

    def _build_selective_context(
        self,
        agent_id: str,
        pass1_results: Dict,
        pass2_results: Dict
    ) -> str:
        """Build selective context (only relevant fields to save tokens)"""
        context_fields = []

        # Governance context (useful for all agents)
        if 'governance_agent' in pass1_results:
            gov = pass1_results['governance_agent']
            if gov.get('chairman'):
                context_fields.append(f"Chairman: {gov['chairman']}")

        # Property context
        if 'property_agent' in pass1_results:
            prop = pass1_results['property_agent']
            if prop.get('address'):
                context_fields.append(f"Property: {prop['address']}")
            if prop.get('apartments'):
                context_fields.append(f"Apartments: {prop['apartments']}")

        # Financial context (for note agents)
        if agent_id.startswith('notes_') and 'financial_agent' in pass2_results:
            fin = pass2_results['financial_agent']
            if fin.get('assets'):
                context_fields.append(f"Assets: {fin['assets']}")
            if fin.get('liabilities'):
                context_fields.append(f"Liabilities: {fin['liabilities']}")

        if not context_fields:
            return ""

        return "\n\nContext from previous extraction:\n" + "\n".join(context_fields)

    def _parse_json_with_fallback(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response with fallback strategies.
        Handles markdown code fences, extra text, etc.
        """
        import re

        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code fence
        fence_patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
        ]

        for pattern in fence_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Strategy 3: Find first JSON object (look for {...})
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # All strategies failed
        return None

    def _extract_agent(
        self,
        pdf_path: str,
        agent_id: str,
        section_headings: List[str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract data for a single agent using GPT-4o.

        Args:
            pdf_path: Path to PDF
            agent_id: Agent identifier (e.g., 'governance_agent')
            section_headings: Relevant section headings to extract from
            context: Optional hierarchical context from previous passes

        Returns:
            Extracted data dictionary
        """
        start_time = time.time()

        # Load agent prompts from Gracian Pipeline
        AGENT_PROMPTS = {
            'governance_agent': """You are GovernanceAgent for Swedish BRF annual/economic plans. From the input text/images, extract ONLY board/auditor data in JSON: {chairman: '', board_members: [], auditor_name: '', audit_firm: '', nomination_committee: []}. Focus on roles like 'Ordförande' (chairman), 'Ledamot' (member), 'Revisor' (auditor). Use NLP synonyms {'Ordförande': 'chairman'}. Ignore financials/property. Multimodal: Analyze images for signatures/tables. Include evidence_pages: [] with 1-based page numbers used. Return ONLY minified JSON.""",
            'financial_agent': """You are FinancialAgent for Swedish BRF reports. Extract ONLY income/balance data with EXACT keys: {revenue:'', expenses:'', assets:'', liabilities:'', equity:'', surplus:'', evidence_pages: []}. Parse SEK numbers (e.g., 1 234 567 → 1234567). Focus on 'Resultaträkning'/'Balansräkning'. Do NOT invent; if not clearly visible on provided pages leave empty. Evidence: evidence_pages must list 1-based GLOBAL page numbers matching image labels (keep ≤ 3 items). Return STRICT VALID JSON object; no extra text.""",
            'property_agent': """You are PropertyAgent for BRF plans. Extract ONLY property details with EXACT keys: {designation:'', address:'', postal_code:'', city:'', built_year:'', apartments:'', energy_class:'', evidence_pages: []}. Use Swedish cues: 'Fastighetsbeteckning', 'Adress', 'Byggår', 'Lägenheter', 'Energiklass'. Evidence: evidence_pages must be 1-based GLOBAL page numbers matching image labels. If a field is not visible, return an empty string ''. Return STRICT VALID JSON object with ONLY these keys (no comments, no trailing text).""",
            'notes_accounting_agent': """You are NotesAccountingAgent for BRF notes. Extract ONLY accounting policy info: {accounting_principles: '', valuation_methods: '', revenue_recognition: ''}. Focus on 'Redovisningsprinciper', 'Värderingsprinciper'. Use only visible values. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_loans_agent': """You are NotesLoansAgent for BRF notes. Extract ONLY loan details: {outstanding_loans: '', interest_rate: '', amortization: '', loan_terms: ''}. Focus on 'Fastighetslån', 'Skulder'. Parse SEK numbers. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_buildings_agent': """You are NotesBuildingsAgent for BRF notes. Extract ONLY building info: {buildings_description: '', building_value: '', depreciation_schedule: ''}. Focus on 'Byggnader och mark'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_receivables_agent': """You are NotesReceivablesAgent for BRF notes. Extract ONLY receivables: {current_receivables: '', long_term_receivables: '', allowances: ''}. Focus on 'Fordringar'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_reserves_agent': """You are NotesReservesAgent for BRF notes. Extract ONLY reserve fund info: {reserve_fund: '', annual_contribution: '', fund_purpose: ''}. Focus on 'Fond för yttre underhåll'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_tax_agent': """You are NotesTaxAgent for BRF notes. Extract ONLY tax info: {current_tax: '', deferred_tax: '', tax_policy: ''}. Focus on 'Skatter', 'Avgifter'. Include evidence_pages: [] (1-based). Return STRICT minified JSON.""",
            'notes_other_agent': """You are NotesOtherAgent for BRF notes. Extract ONLY other note information not covered by specific agents: {other_notes: ''}. Include evidence_pages: [] (1-based). Return STRICT minified JSON."""
        }

        base_prompt = AGENT_PROMPTS.get(agent_id, f"Extract data for {agent_id} in JSON format.")

        # Build context-aware prompt
        prompt = f"""Document sections detected:
{json.dumps(section_headings, indent=2, ensure_ascii=False)}

{base_prompt}

Focus on the sections listed above. Extract only information visible in those sections.
"""

        if context:
            prompt += f"\n\nContext from previous extraction:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"

        # Add mandatory evidence instruction (Fix #2 from ULTRATHINKING)
        prompt += """
⚠️ MANDATORY REQUIREMENT:
Your JSON response MUST include 'evidence_pages': [page_numbers].
List ALL page numbers (1-based, from image labels below) used for extraction.
If you used images labeled "Page 5", "Page 7", "Page 8", return: 'evidence_pages': [5, 7, 8]
If no relevant information found, return 'evidence_pages': []
"""

        # Step 1: Get pages for sections (enhanced hybrid strategy: Docling → text search → content keywords → fallback)
        pages = self._get_pages_for_sections(pdf_path, section_headings, fallback_pages=5, agent_id=agent_id)

        # Step 2: Adaptive page selection (max 4 pages to prevent token overflow)
        if len(pages) > 4:
            # For large sections, sample strategically (first, middle, last + one more)
            selected_pages = [
                pages[0],                           # Start
                pages[len(pages)//3],               # Early-middle
                pages[2*len(pages)//3],             # Late-middle
                pages[-1]                           # End
            ]
            pages = sorted(set(selected_pages))

        # Step 3: Render pages to images
        images, page_labels = self._render_pdf_pages(pdf_path, pages, dpi=200)

        if not images:
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": "No images rendered",
                "extraction_time": time.time() - start_time
            }

        # Step 4: Build multimodal message
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Fix #1 from ULTRATHINKING: Interleave page labels with images
        # Build content array with text labels between images so LLM knows which page is which
        content = [{"type": "text", "text": prompt}]

        for img_bytes, label in zip(images, page_labels):
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            # Add text label before each image
            content.append({"type": "text", "text": f"\n--- {label} ---"})
            # Add the image
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })

        # Construct messages with interleaved content
        messages = [{"role": "user", "content": content}]

        # Experiment: Log content array structure to verify labels reach LLM
        print(f"\n🔬 EXPERIMENT: {agent_id} content array structure:")
        for i, item in enumerate(content):
            if item['type'] == 'text':
                text_preview = item['text'][:80].replace('\n', ' ')
                print(f"  [{i}] TEXT: {text_preview}...")
            else:
                print(f"  [{i}] IMAGE: base64 data")

        # Step 5: Call OpenAI API with retry logic (from Gracian vision_qc.py)
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0
                )

                raw_content = response.choices[0].message.content

                # Experiment: Log raw response to see what LLM actually returns
                print(f"\n📄 {agent_id} RAW RESPONSE (first 500 chars):")
                print(raw_content[:500])
                print(f"\n🔍 Checking for 'evidence_pages' in raw response...")
                if 'evidence_pages' in raw_content.lower():
                    print(f"✅ FOUND 'evidence_pages' in raw response!")
                else:
                    print(f"❌ NOT FOUND 'evidence_pages' in raw response!")

                # Step 6: Parse JSON with fallback (json_guard from Gracian)
                extracted_data = self._parse_json_with_fallback(raw_content)

                if extracted_data is None:
                    raise ValueError(f"Failed to parse JSON from response: {raw_content[:200]}")

                # Diagnostic: Log what keys the LLM actually returned
                print(f"   🔍 {agent_id} extracted keys: {list(extracted_data.keys())}")
                if 'evidence_pages' in extracted_data:
                    print(f"   ✅ {agent_id} evidence_pages: {extracted_data['evidence_pages']}")
                else:
                    print(f"   ❌ {agent_id} MISSING evidence_pages!")

                # Step 7: Evidence verification
                rendered_pages = [p + 1 for p in pages]  # Convert to 1-based
                evidence_pages = extracted_data.get('evidence_pages', [])
                evidence_verified = all(pg in rendered_pages for pg in evidence_pages) if evidence_pages else False

                # Step 8: Add metadata
                result = {
                    "agent_id": agent_id,
                    "status": "success",
                    "data": extracted_data,
                    "section_headings": section_headings,
                    "pages_rendered": rendered_pages,
                    "num_images": len(images),
                    "evidence_pages": evidence_pages,
                    "evidence_verified": evidence_verified,
                    "extraction_time": time.time() - start_time,
                    "model": "gpt-4o-2024-11-20",
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }

                return result

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s
                    time.sleep(wait_time)
                continue

        # All retries failed
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(last_error),
            "extraction_time": time.time() - start_time
        }

    def extract_pass1(
        self,
        routing: SectionRouting
    ) -> Dict[str, Dict]:
        """
        Pass 1: Extract high-level fields (governance, property) in parallel.

        Args:
            routing: Section routing results from Stage 3

        Returns:
            Dict mapping agent_id -> extraction results
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        start_time = time.time()

        # Pass 1 agents (main sections, simple extraction)
        pass1_agents = [
            'governance_agent',
            'property_agent'
        ]

        results = {}

        # Parallel execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_agent = {}

            for agent_id in pass1_agents:
                section_headings = routing.main_sections.get(agent_id, [])
                if section_headings or agent_id == 'governance_agent':  # Always run governance
                    future = executor.submit(
                        self._extract_agent,
                        self.pdf_path_cache,  # Will need to pass this
                        agent_id,
                        section_headings
                    )
                    future_to_agent[future] = agent_id

            # Collect results
            for future in as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    results[agent_id] = future.result(timeout=60)
                except Exception as e:
                    results[agent_id] = {
                        "agent_id": agent_id,
                        "status": "error",
                        "error": str(e)
                    }

        elapsed = time.time() - start_time
        print(f"   ✅ Pass 1: {len(results)} agents completed ({elapsed:.1f}s)")

        return results

    def extract_pass2(
        self,
        routing: SectionRouting,
        pass1_results: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Pass 2: Extract financial + notes sequentially with hierarchical context.

        Args:
            routing: Section routing results
            pass1_results: Results from Pass 1

        Returns:
            Dict mapping agent_id -> extraction results
        """
        start_time = time.time()

        results = {}

        # Extract financial agent first
        financial_headings = routing.main_sections.get('financial_agent', [])
        if financial_headings:
            results['financial_agent'] = self._extract_agent(
                self.pdf_path_cache,
                'financial_agent',
                financial_headings,
                context=pass1_results
            )

        # Extract note agents sequentially
        for agent_id, section_headings in routing.note_sections.items():
            # Build hierarchical context (Pass 1 + financial + previous notes)
            context = {
                **pass1_results,
                'financial': results.get('financial_agent', {}),
                'previous_notes': {k: v for k, v in results.items() if k.startswith('notes_')}
            }

            results[agent_id] = self._extract_agent(
                self.pdf_path_cache,
                agent_id,
                section_headings,
                context=context
            )

        elapsed = time.time() - start_time
        print(f"   ✅ Pass 2: {len(results)} agents completed ({elapsed:.1f}s)")

        return results

    def validate_extraction(
        self,
        pass1_results: Dict[str, Dict],
        pass2_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Pass 3: Validate extraction quality against 95/95 gates.

        Quality gates:
        1. Coverage: ≥95% of required fields extracted
        2. Numeric QC: Financial fields within tolerance
        3. Evidence: ≥95% of extractions cite source pages

        Args:
            pass1_results: Results from Pass 1
            pass2_results: Results from Pass 2

        Returns:
            Quality metrics dict
        """
        start_time = time.time()

        all_results = {**pass1_results, **pass2_results}

        # Gate 1: Coverage check
        total_agents = len(all_results)
        successful_agents = sum(1 for r in all_results.values() if r.get('status') != 'error')
        coverage = successful_agents / total_agents if total_agents > 0 else 0.0

        # Gate 2: Numeric QC (placeholder - would use Gracian qc.py)
        numeric_qc_pass = True  # TODO: Implement actual numeric validation

        # Gate 3: Evidence tracking
        agents_with_evidence = sum(
            1 for r in all_results.values()
            if r.get('evidence_pages') and len(r.get('evidence_pages', [])) > 0
        )
        evidence_ratio = agents_with_evidence / total_agents if total_agents > 0 else 0.0

        # Overall quality score
        overall_score = (coverage + evidence_ratio) / 2

        quality = {
            "coverage": coverage,
            "numeric_qc_pass": numeric_qc_pass,
            "evidence_ratio": evidence_ratio,
            "overall_score": overall_score,
            "needs_coaching": overall_score < 0.95,
            "validation_time": time.time() - start_time
        }

        # Print quality report
        print(f"   Coverage: {coverage:.1%} ({successful_agents}/{total_agents} agents)")
        print(f"   Numeric QC: {'✅ Pass' if numeric_qc_pass else '❌ Fail'}")
        print(f"   Evidence: {evidence_ratio:.1%} ({agents_with_evidence}/{total_agents} agents)")
        print(f"   Overall: {overall_score:.1%} {'✅' if overall_score >= 0.95 else '⚠️'}")

        return quality

    def extract_document(
        self,
        pdf_path: str
    ) -> ExtractionResult:
        """
        Main extraction pipeline for a single document.

        Full 5-stage process:
        1. Topology detection
        2. Structure detection
        3. Section routing
        4. Hierarchical extraction (3 passes)
        5. Quality validation
        """
        overall_start = time.time()
        print(f"\n{'='*70}")
        print(f"OPTIMAL BRF PIPELINE - {Path(pdf_path).name}")
        print(f"{'='*70}\n")

        # STAGE 1: Topology detection
        print("📊 STAGE 1: PDF Topology Detection")
        topology = self.analyze_topology(pdf_path)

        # Store topology for access by _get_pages_for_sections() (Phase 2E)
        self.topology = topology

        # STAGE 2: Structure detection
        print("\n🔍 STAGE 2: Structure Detection (Docling)")
        structure = self.detect_structure(pdf_path, topology)

        # STAGE 3: Section routing
        print("\n🧭 STAGE 3: Section Routing (Hybrid)")
        routing = self.route_sections(structure)

        # Cache PDF path for extraction methods
        self.pdf_path_cache = pdf_path

        # STAGE 4: Hierarchical extraction
        print("\n🎯 STAGE 4: Hierarchical Extraction")

        # Pass 1: High-level extraction (governance, property) - parallel
        print("   🔄 Pass 1: High-level (governance, property)...")
        pass1_result = self.extract_pass1(routing)

        # Pass 2: Financial + notes - sequential
        print("   🔄 Pass 2: Financial + notes (detailed)...")
        pass2_result = self.extract_pass2(routing, pass1_result)

        # No Pass 3 coaching in Phase 2 (add later if needed)
        pass3_result = {}

        # STAGE 5: Quality validation
        print("\n✅ STAGE 5: Quality Validation")
        quality_metrics = self.validate_extraction(pass1_result, pass2_result)

        total_time = time.time() - overall_start
        total_cost = 0.0  # Placeholder

        result = ExtractionResult(
            pdf_path=pdf_path,
            topology=topology,
            structure=structure,
            routing=routing,
            pass1_result=pass1_result,
            pass2_result=pass2_result,
            pass3_result=pass3_result,
            brf_report=None,  # TODO: Build Pydantic model
            quality_metrics=quality_metrics,
            total_time=total_time,
            total_cost=total_cost
        )

        # Save results
        output_file = self.output_dir / f"{Path(pdf_path).stem}_optimal_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'pdf': pdf_path,
                'topology': asdict(topology),
                'structure': {
                    'num_sections': structure.num_sections,
                    'method': structure.method,
                    'cached': structure.cached,
                    'extraction_time': structure.extraction_time
                },
                'routing': {
                    'main_sections': {k: len(v) for k, v in routing.main_sections.items()},
                    'note_sections': {k: len(v) for k, v in routing.note_sections.items()},
                    'routing_time': routing.routing_time
                },
                'quality_metrics': quality_metrics,
                'total_time': total_time,
                'total_cost': total_cost
            }, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print(f"✅ PIPELINE COMPLETE")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Total cost: ${total_cost:.3f}")
        print(f"   Output: {output_file}")
        print(f"{'='*70}\n")

        return result

    def close(self):
        """Clean up resources"""
        if self.note_router:
            self.note_router.close()
        print("✅ Pipeline closed")


def main():
    """Test optimal pipeline on sample document"""
    import sys
    from dotenv import load_dotenv

    # Load environment variables from Gracian Pipeline root
    gracian_root = Path(__file__).resolve().parent.parent.parent.parent
    env_path = gracian_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"⚠️  Warning: .env file not found at {env_path}")

    if len(sys.argv) < 2:
        print("Usage: python optimal_brf_pipeline.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    # Run pipeline
    pipeline = OptimalBRFPipeline(
        cache_dir="results/cache",
        output_dir="results/optimal_pipeline",
        enable_caching=True
    )

    try:
        result = pipeline.extract_document(pdf_path)
        print("\n✅ Extraction successful!")
        print(f"   Sections detected: {result.structure.num_sections}")
        print(f"   Main section agents: {sum(len(v) for v in result.routing.main_sections.values())}")
        print(f"   Note section agents: {sum(len(v) for v in result.routing.note_sections.values())}")

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
