#!/usr/bin/env python3
"""
Schema Evolution Manager for Two-LLM Ground Truth System

Purpose: Enable dynamic Pydantic schema learning from discovered fields
- New field pops up → Upgrade schema automatically
- Track field discoveries across PDFs
- Generate schema update recommendations
- Prevent hallucinations by validating against corpus

Date: 2025-10-15
Status: IMPLEMENTATION for Hjorthagen + NDS processing
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from gracian_pipeline.core.schema_comprehensive import (
    COMPREHENSIVE_TYPES,
    BASE_TYPES,
    get_comprehensive_types
)


class SchemaEvolutionManager:
    """
    Manages dynamic schema evolution based on discovered fields.

    Features:
    - Track new fields across multiple PDFs
    - Validate field legitimacy (not hallucinations)
    - Generate schema update recommendations
    - Auto-update Pydantic schema files
    """

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = str(project_root / "ground_truth" / "schema_evolution")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track discovered fields
        self.discoveries_file = self.output_dir / "field_discoveries.json"
        self.discoveries = self._load_discoveries()

        # Current schema state
        self.current_schema = COMPREHENSIVE_TYPES.copy()

    def _load_discoveries(self) -> Dict:
        """Load existing field discoveries from disk."""
        if self.discoveries_file.exists():
            with open(self.discoveries_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "new_fields": defaultdict(lambda: {
                "count": 0,
                "pdfs": [],
                "sample_values": [],
                "inferred_type": None,
                "validated": False
            }),
            "field_variations": defaultdict(list),
            "schema_updates": []
        }

    def _save_discoveries(self):
        """Save field discoveries to disk."""
        # Convert defaultdict to regular dict for JSON serialization
        discoveries_serializable = {
            "new_fields": dict(self.discoveries["new_fields"]),
            "field_variations": dict(self.discoveries["field_variations"]),
            "schema_updates": self.discoveries["schema_updates"]
        }

        with open(self.discoveries_file, 'w', encoding='utf-8') as f:
            json.dump(discoveries_serializable, f, indent=2, ensure_ascii=False)

    def analyze_extraction_result(self, pdf_name: str, extraction_result: Dict, agent_id: str = None):
        """
        Analyze extraction result for new fields.

        Args:
            pdf_name: Name of PDF being processed
            extraction_result: Dict with extracted fields
            agent_id: Optional agent ID for scoped analysis
        """
        known_fields = set()
        if agent_id and agent_id in self.current_schema:
            known_fields = set(self.current_schema[agent_id].keys())
        else:
            # Collect all known fields across all agents
            for agent_schema in self.current_schema.values():
                known_fields.update(agent_schema.keys())

        # Find new fields
        extracted_fields = self._extract_all_field_paths(extraction_result)

        for field_path, value in extracted_fields.items():
            field_name = field_path.split('.')[-1]  # Get leaf field name

            if field_name not in known_fields:
                # NEW FIELD DISCOVERED!
                self._record_new_field(
                    field_name=field_name,
                    field_path=field_path,
                    value=value,
                    pdf_name=pdf_name,
                    agent_id=agent_id
                )

    def _extract_all_field_paths(self, obj: Any, prefix: str = "") -> Dict[str, Any]:
        """
        Recursively extract all field paths and their values from nested dict.

        Returns:
            Dict mapping field_path → value
        """
        fields = {}

        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key

                # Skip metadata fields
                if key in ['confidence', 'source_page', 'verification_note', 'evidence_pages']:
                    continue

                # Add this field
                fields[field_path] = value

                # Recurse into nested dicts/lists
                if isinstance(value, dict):
                    fields.update(self._extract_all_field_paths(value, field_path))
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # Handle list of dicts (e.g., board_members)
                    for i, item in enumerate(value):
                        fields.update(self._extract_all_field_paths(item, f"{field_path}[{i}]"))

        return fields

    def _record_new_field(self, field_name: str, field_path: str, value: Any,
                          pdf_name: str, agent_id: Optional[str]):
        """Record discovery of a new field."""
        # Initialize if first discovery
        if field_name not in self.discoveries["new_fields"]:
            self.discoveries["new_fields"][field_name] = {
                "count": 0,
                "pdfs": [],
                "sample_values": [],
                "inferred_type": None,
                "validated": False,
                "agent_id": agent_id,
                "field_paths": []
            }

        field_info = self.discoveries["new_fields"][field_name]

        # Update statistics
        field_info["count"] += 1
        if pdf_name not in field_info["pdfs"]:
            field_info["pdfs"].append(pdf_name)

        # Add sample value (limit to 5)
        if len(field_info["sample_values"]) < 5:
            field_info["sample_values"].append({
                "value": self._serialize_value(value),
                "pdf": pdf_name,
                "path": field_path
            })

        # Track field path variations
        if field_path not in field_info["field_paths"]:
            field_info["field_paths"].append(field_path)

        # Infer type from value
        if field_info["inferred_type"] is None:
            field_info["inferred_type"] = self._infer_type(value)

        print(f"   🆕 NEW FIELD DISCOVERED: {field_name} ({field_info['inferred_type']})")
        print(f"      Found in: {pdf_name}")
        print(f"      Value: {self._truncate(str(value), 100)}")

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON storage."""
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in list(value.items())[:3]}  # Limit dict size
        elif isinstance(value, list):
            return [self._serialize_value(v) for v in value[:3]]  # Limit list size
        else:
            return str(value)

    def _infer_type(self, value: Any) -> str:
        """Infer Pydantic type from value."""
        if value is None:
            return "Optional[str]"  # Default to optional string
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, list):
            if not value:
                return "List[str]"
            # Infer from first element
            first_type = self._infer_type(value[0])
            return f"List[{first_type}]"
        elif isinstance(value, dict):
            return "Dict[str, Any]"
        else:
            return "Any"

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max_length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def validate_field(self, field_name: str, min_occurrences: int = 2) -> bool:
        """
        Validate if a discovered field is legitimate (not hallucination).

        Rules:
        - Must appear in at least min_occurrences PDFs
        - Must have consistent type across occurrences
        - Must have meaningful name (not gibberish)

        Returns:
            True if field is validated, False otherwise
        """
        if field_name not in self.discoveries["new_fields"]:
            return False

        field_info = self.discoveries["new_fields"][field_name]

        # Check occurrence count
        if field_info["count"] < min_occurrences:
            return False

        # Check field name is meaningful (not gibberish)
        if not self._is_meaningful_field_name(field_name):
            return False

        # Mark as validated
        field_info["validated"] = True
        return True

    def _is_meaningful_field_name(self, field_name: str) -> bool:
        """
        Check if field name is meaningful (not gibberish or hallucination).

        Rules:
        - Must be lowercase with underscores
        - Must be at least 3 characters
        - Must contain at least one vowel
        - Must not contain numbers (unless part of meaningful name like "note_4")
        """
        # Basic length check
        if len(field_name) < 3:
            return False

        # Must follow naming convention (lowercase_with_underscores)
        if not re.match(r'^[a-z][a-z0-9_]*$', field_name):
            return False

        # Must contain at least one vowel (Swedish or English)
        if not any(c in field_name for c in 'aeiouyåäö'):
            return False

        # Check if it's a known Swedish BRF term
        swedish_brf_terms = {
            'årsavgift', 'avgift', 'styrelse', 'revisor', 'ordförande',
            'årsstämma', 'förvaltning', 'underhåll', 'fond', 'lån',
            'skuld', 'tillgång', 'balansräkning', 'resultaträkning'
        }

        # If contains any Swedish BRF term, it's meaningful
        for term in swedish_brf_terms:
            if term in field_name:
                return True

        # Otherwise, assume it's meaningful if passes basic checks
        return True

    def generate_schema_updates(self, min_occurrences: int = 3) -> List[Dict]:
        """
        Generate schema update recommendations for validated fields.

        Args:
            min_occurrences: Minimum times a field must appear to be recommended

        Returns:
            List of schema update recommendations
        """
        recommendations = []

        for field_name, field_info in self.discoveries["new_fields"].items():
            # Only recommend if validated and appears frequently enough
            if field_info["count"] >= min_occurrences:
                if not field_info.get("validated"):
                    self.validate_field(field_name, min_occurrences=min_occurrences)

                if field_info["validated"]:
                    recommendations.append({
                        "field_name": field_name,
                        "agent_id": field_info.get("agent_id"),
                        "type": field_info["inferred_type"],
                        "occurrences": field_info["count"],
                        "pdfs": field_info["pdfs"],
                        "sample_values": field_info["sample_values"][:2],  # Show 2 examples
                        "recommendation": f"Add to {'agent ' + field_info['agent_id'] if field_info['agent_id'] else 'schema'}"
                    })

        return recommendations

    def generate_anti_hallucination_prompt(self) -> str:
        """
        Generate anti-hallucination prompt based on validated fields.

        Returns:
            Prompt text to add to LLM extraction prompts
        """
        validated_fields = [
            field_name for field_name, field_info in self.discoveries["new_fields"].items()
            if field_info.get("validated", False)
        ]

        prompt = """
🚨 ANTI-HALLUCINATION RULES - CRITICAL:

1. **ONLY EXTRACT FIELDS THAT EXIST IN THE DOCUMENT**
   - Do NOT invent field names
   - Do NOT create field values from imagination
   - If a field is not visible in the provided pages, use null or []

2. **KNOWN VALID FIELDS** (validated across multiple documents):
"""

        if validated_fields:
            prompt += "   " + ", ".join(sorted(validated_fields)[:20])  # Show top 20
        else:
            prompt += "   (No additional validated fields yet)"

        prompt += """

3. **IF YOU DISCOVER A NEW FIELD**:
   - It MUST be explicitly mentioned in the document
   - It MUST have a meaningful Swedish BRF term name
   - It MUST contain actual extracted data (not placeholders)
   - Add it to 'additional_facts' with source page

4. **FORBIDDEN**:
   - Do NOT create fields with gibberish names
   - Do NOT use placeholder values like "TBD", "N/A", "Unknown"
   - Do NOT infer fields that are not explicitly stated
   - Do NOT copy field names from other documents

5. **EVIDENCE IS MANDATORY**:
   - Every extracted field MUST cite source_page
   - If no source page, the field is likely hallucinated → use null
"""

        return prompt

    def save_update_summary(self):
        """Save summary of discoveries and recommendations."""
        recommendations = self.generate_schema_updates()
        anti_hallucination_prompt = self.generate_anti_hallucination_prompt()

        summary_file = self.output_dir / "schema_update_summary.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Schema Evolution Summary\n\n")
            f.write(f"**Generated**: {Path(self.discoveries_file).stat().st_mtime}\n\n")

            f.write("## 📊 Field Discovery Statistics\n\n")
            total_discoveries = len(self.discoveries["new_fields"])
            validated = sum(1 for fi in self.discoveries["new_fields"].values() if fi.get("validated"))
            f.write(f"- **Total new fields discovered**: {total_discoveries}\n")
            f.write(f"- **Validated fields**: {validated}\n")
            f.write(f"- **Pending validation**: {total_discoveries - validated}\n\n")

            f.write("## 🎯 Schema Update Recommendations\n\n")
            if recommendations:
                for rec in recommendations:
                    f.write(f"### {rec['field_name']}\n\n")
                    f.write(f"- **Type**: `{rec['type']}`\n")
                    f.write(f"- **Occurrences**: {rec['occurrences']} PDFs\n")
                    f.write(f"- **Agent**: {rec['agent_id'] or 'Unknown'}\n")
                    f.write(f"- **Found in**: {', '.join(rec['pdfs'][:3])}\n")
                    f.write(f"- **Sample values**:\n")
                    for sample in rec['sample_values']:
                        f.write(f"  - `{sample['value']}` (from {sample['pdf']})\n")
                    f.write(f"\n**Recommendation**: {rec['recommendation']}\n\n")
            else:
                f.write("No recommendations yet (need at least 3 occurrences).\n\n")

            f.write("## 🚨 Anti-Hallucination Prompt\n\n")
            f.write("```\n")
            f.write(anti_hallucination_prompt)
            f.write("\n```\n\n")

            f.write("## 📁 Raw Discovery Data\n\n")
            f.write(f"See `{self.discoveries_file.name}` for complete field discovery details.\n")

        print(f"\n✅ Schema update summary saved: {summary_file}")
        self._save_discoveries()


def main():
    """Example usage of SchemaEvolutionManager."""
    manager = SchemaEvolutionManager()

    # Example: Analyze a dummy extraction result
    dummy_result = {
        "metadata": {
            "brf_name": "Test BRF",
            "organization_number": "123456-7890",
            "new_discovered_field": "Some value"  # This will be flagged as new
        },
        "financial": {
            "revenue": 1000000,
            "unusual_revenue_source": "Parking fees"  # Another new field
        }
    }

    manager.analyze_extraction_result("test.pdf", dummy_result)
    manager.save_update_summary()

    print("\n✅ Schema evolution manager test complete!")


if __name__ == "__main__":
    main()
