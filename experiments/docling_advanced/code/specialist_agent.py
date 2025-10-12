#!/usr/bin/env python3
"""
Specialist Agent Architecture - Foundation

Each specialist agent focuses on ONE extraction task with:
- Focused Pydantic schema (single responsibility)
- Self-learning capability (3-iteration refinement)
- Docling-powered section routing
- Ground truth validation

Based on ultrathinking analysis and user feedback:
"One specialist agent per table type/section - that must be what gives us 95/95"
"""

import json
import time
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod

# LLM client
from openai import OpenAI


@dataclass
class SpecialistPromptTemplate:
    """
    Template for specialist agent prompts with learning capability

    Components:
    1. Identity: Clear role definition
    2. Task: Exact fields to extract
    3. Context: Section/pages to analyze
    4. Golden examples: Real successful extractions
    5. Anti-examples: Common mistakes to avoid
    6. Output schema: Pydantic model
    7. Swedish terminology: Domain-specific mappings
    8. Validation rules: What makes a good extraction
    """

    # Core identification
    specialist_id: str
    identity: str  # "You are a Swedish BRF utilities cost specialist"
    task_description: str

    # Context
    target_section: str  # "Noter - Not 4 (Driftkostnader)"
    target_pages: List[int]  # Expected pages [13]

    # Fields to extract
    expected_fields: List[str]  # ["el", "varme", "vatten"]
    field_descriptions: Dict[str, str]  # {"el": "Electricity costs in SEK"}

    # Learning examples
    golden_examples: List[Dict] = field(default_factory=list)
    anti_examples: List[Dict] = field(default_factory=list)

    # Domain knowledge
    swedish_terms: Dict[str, str] = field(default_factory=dict)
    number_format_rules: List[str] = field(default_factory=list)

    # Quality control
    confidence_threshold: float = 0.7
    validation_rules: List[str] = field(default_factory=list)

    # Learning history
    prompt_version: int = 1
    learning_iterations: int = 0
    performance_history: List[float] = field(default_factory=list)

    def build_prompt(self) -> str:
        """Generate full LLM prompt from template"""

        prompt = f"""# {self.identity}

## Your Task
{self.task_description}

## Target Section
Look for: {self.target_section}
Expected pages: {self.target_pages}

## Fields to Extract
"""

        # Add field descriptions
        for field_name in self.expected_fields:
            description = self.field_descriptions.get(field_name, "")
            prompt += f"- **{field_name}**: {description}\n"

        # Add Swedish terminology
        if self.swedish_terms:
            prompt += "\n## Swedish BRF Terminology\n"
            for swedish, english in self.swedish_terms.items():
                prompt += f"- {swedish} → {english}\n"

        # Add number format rules
        if self.number_format_rules:
            prompt += "\n## Number Format Rules\n"
            for rule in self.number_format_rules:
                prompt += f"- {rule}\n"

        # Add golden examples
        if self.golden_examples:
            prompt += "\n## ✅ Golden Examples (Successful Extractions)\n"
            for i, example in enumerate(self.golden_examples, 1):
                prompt += f"\n### Example {i}:\n"
                prompt += f"```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```\n"

        # Add anti-examples
        if self.anti_examples:
            prompt += "\n## ❌ Common Mistakes to Avoid\n"
            for i, example in enumerate(self.anti_examples, 1):
                prompt += f"\n### Mistake {i}: {example.get('description', 'Unknown')}\n"
                if 'wrong_extraction' in example:
                    prompt += f"Wrong: {example['wrong_extraction']}\n"
                if 'correct_extraction' in example:
                    prompt += f"Correct: {example['correct_extraction']}\n"

        # Add validation rules
        if self.validation_rules:
            prompt += "\n## Validation Rules\n"
            for rule in self.validation_rules:
                prompt += f"- {rule}\n"

        # Add output format
        prompt += f"""
## Output Format
Return JSON with these fields: {', '.join(self.expected_fields)}
Include 'evidence_page' (page number where you found the data)
Include 'confidence' (0.0 to 1.0, your confidence in the extraction)

Example output structure:
```json
{{
  {', '.join([f'"{field}": <value>' for field in self.expected_fields])},
  "evidence_page": <page_number>,
  "confidence": <0.0_to_1.0>
}}
```

If you cannot find a field with confidence ≥{self.confidence_threshold}, set it to null and lower confidence accordingly.

Return ONLY valid JSON, no other text.
"""

        return prompt


class SpecialistAgent(ABC):
    """
    Base class for specialist extraction agents

    Each specialist:
    - Focuses on ONE extraction task (single responsibility)
    - Uses focused Pydantic schema for validation
    - Supports self-learning through GT comparison
    - Tracks performance across iterations
    """

    def __init__(
        self,
        prompt_template: SpecialistPromptTemplate,
        schema_class: Type[BaseModel],
        openai_api_key: Optional[str] = None,
        enable_llm: bool = True
    ):
        self.prompt_template = prompt_template
        self.schema_class = schema_class
        self.specialist_id = prompt_template.specialist_id
        self.enable_llm = enable_llm

        # LLM client (lazy initialization for testing)
        import os
        self._api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self._client = None

        # Performance tracking
        self.extraction_history = []
        self.learning_enabled = True

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.enable_llm:
                raise RuntimeError("LLM is disabled. This agent is in testing mode.")
            if not self._api_key:
                raise RuntimeError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    @abstractmethod
    def extract(self, pdf_path: str, pages: List[int]) -> Dict[str, Any]:
        """
        Extract data from PDF using specialist knowledge

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to analyze (0-indexed)

        Returns:
            Extracted data matching schema
        """
        pass

    def _render_pdf_pages(self, pdf_path: str, pages: List[int]) -> List[bytes]:
        """Render PDF pages as images for vision model"""
        import fitz

        doc = fitz.open(pdf_path)
        images = []

        for page_num in pages:
            if page_num < len(doc):
                page = doc[page_num]
                zoom = 200 / 72  # 200 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                images.append(pix.tobytes("png"))

        doc.close()
        return images

    def _call_llm_with_images(
        self,
        prompt: str,
        images: List[bytes],
        model: str = "gpt-4o-2024-11-20"
    ) -> Dict[str, Any]:
        """Call vision LLM with prompt and images"""
        import base64

        # Build message content
        content = [{"type": "text", "text": prompt}]

        for i, img_bytes in enumerate(images):
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })

        # Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=2000,
                temperature=0
            )

            raw_content = response.choices[0].message.content

            # Parse JSON (handle markdown fences)
            raw_content = raw_content.strip()
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]

            extracted_data = json.loads(raw_content.strip())

            return {
                'status': 'success',
                'data': extracted_data,
                'model': model,
                'tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'data': {}
            }

    def validate_with_schema(self, extracted_data: Dict) -> Dict[str, Any]:
        """Validate extraction against Pydantic schema"""
        try:
            validated = self.schema_class(**extracted_data)
            return {
                'valid': True,
                'data': validated.dict(),
                'warnings': [],
                'confidence_adjustment': 0.0
            }
        except Exception as e:
            return {
                'valid': False,
                'data': extracted_data,
                'warnings': [str(e)],
                'confidence_adjustment': -0.2
            }

    def compare_with_ground_truth(
        self,
        extracted: Dict,
        ground_truth: Dict
    ) -> Dict[str, Any]:
        """
        Compare extraction against ground truth

        Returns:
            - matches: List of correctly extracted fields
            - mismatches: List of incorrect/missing fields with details
            - accuracy: Float 0.0 to 1.0
        """
        matches = []
        mismatches = []

        for field, gt_value in ground_truth.items():
            if field in ['evidence_page', 'confidence']:
                continue  # Skip metadata fields

            ext_value = extracted.get(field)

            # Check if values match
            if self._values_match(ext_value, gt_value):
                matches.append(field)
            else:
                error_type = self._classify_error(ext_value, gt_value)
                mismatches.append({
                    'field': field,
                    'extracted': ext_value,
                    'expected': gt_value,
                    'error_type': error_type
                })

        accuracy = len(matches) / len(ground_truth) if ground_truth else 0.0

        return {
            'matches': matches,
            'mismatches': mismatches,
            'accuracy': accuracy,
            'total_fields': len(ground_truth)
        }

    def _values_match(self, val1: Any, val2: Any, tolerance: float = 0.05) -> bool:
        """Check if two values match (with tolerance for numbers)"""
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False

        # Numeric comparison with tolerance
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val2 == 0:
                return val1 == 0
            return abs(val1 - val2) / abs(val2) <= tolerance

        # String comparison (case-insensitive)
        if isinstance(val1, str) and isinstance(val2, str):
            return val1.lower().strip() == val2.lower().strip()

        # Direct comparison
        return val1 == val2

    def _classify_error(self, extracted: Any, ground_truth: Any) -> str:
        """Classify type of extraction error"""
        if extracted is None:
            return 'missing_extraction'

        if isinstance(ground_truth, (int, float)):
            if isinstance(extracted, (int, float)):
                diff_percent = abs(extracted - ground_truth) / ground_truth if ground_truth != 0 else 0
                if diff_percent > 0.5:
                    return 'numeric_large_error'
                else:
                    return 'numeric_small_error'
            else:
                return 'wrong_type'

        if isinstance(ground_truth, str):
            if isinstance(extracted, str):
                return 'string_mismatch'
            else:
                return 'wrong_type'

        return 'unknown_error'

    def get_performance_summary(self) -> Dict:
        """Get performance summary across all extractions"""
        if not self.extraction_history:
            return {'status': 'no_data'}

        accuracies = [h.get('accuracy', 0) for h in self.extraction_history]

        return {
            'specialist_id': self.specialist_id,
            'total_extractions': len(self.extraction_history),
            'avg_accuracy': sum(accuracies) / len(accuracies),
            'latest_accuracy': accuracies[-1] if accuracies else 0,
            'prompt_version': self.prompt_template.prompt_version,
            'learning_iterations': self.prompt_template.learning_iterations
        }


class SpecialistAgentFactory:
    """Factory for creating specialist agents"""

    @staticmethod
    def create_specialist(
        specialist_type: str,
        initial_examples: Optional[List[Dict]] = None
    ) -> SpecialistAgent:
        """
        Create specialist agent by type

        Args:
            specialist_type: Type of specialist (e.g., 'note4_utilities')
            initial_examples: Golden examples for few-shot learning

        Returns:
            Configured SpecialistAgent instance
        """

        if specialist_type == 'note4_utilities':
            from specialist_schemas import Note4UtilitiesSchema
            from specialist_note4_utilities import Note4UtilitiesAgent

            prompt_template = SpecialistPromptTemplate(
                specialist_id='note4_utilities_agent',
                identity='Swedish BRF Utilities Cost Specialist',
                task_description='Extract electricity, heating, and water costs from Note 4 (Driftkostnader)',
                target_section='Noter - Not 4 (Driftkostnader/Rörelsekostnader)',
                target_pages=[13],
                expected_fields=['el', 'varme', 'vatten'],
                field_descriptions={
                    'el': 'Electricity costs in SEK (Swedish: El)',
                    'varme': 'Heating costs in SEK (Swedish: Värme)',
                    'vatten': 'Water and drainage costs in SEK (Swedish: Vatten och avlopp)'
                },
                swedish_terms={
                    'El': 'Electricity',
                    'Värme': 'Heating',
                    'Vatten och avlopp': 'Water and drainage',
                    'Driftkostnader': 'Operating costs',
                    'Rörelsekostnader': 'Operating expenses'
                },
                number_format_rules=[
                    'Swedish number format uses spaces, not commas: "698 763" → 698763',
                    'Extract from rightmost column (current year)',
                    'Values are in SEK (Swedish Kronor)'
                ],
                validation_rules=[
                    'All costs must be positive numbers',
                    'Electricity typically 200k-1M SEK for BRF',
                    'Heating typically 300k-800k SEK',
                    'Water typically 100k-300k SEK'
                ],
                golden_examples=initial_examples or []
            )

            return Note4UtilitiesAgent(prompt_template, Note4UtilitiesSchema)

        # Add more specialist types here as we implement them
        else:
            raise ValueError(f"Unknown specialist type: {specialist_type}")
