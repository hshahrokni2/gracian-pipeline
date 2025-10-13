"""
Smart Field Counter - Distinguish Data Fields from Metadata
==========================================================

Problem: BRFAnnualReport has 4,405 TOTAL fields (including ExtractionField metadata).
Solution: Count separately:
1. DATA FIELDS: Actual extractable values (~300-400)
2. METADATA FIELDS: Confidence, evidence, etc. (per ExtractionField)

This provides accurate coverage metrics for the user's 95/95 target.

Author: Claude Code
Date: 2025-10-13
"""

import sys
from pathlib import Path
from typing import Dict, Set, List, Any
from pydantic import BaseModel

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gracian_pipeline.models.brf_schema import BRFAnnualReport
from gracian_pipeline.models.base_fields import (
    StringField, NumberField, DateField, ListField, BooleanField, DictField
)


class SmartFieldCounter:
    """
    Count data fields separately from metadata fields.

    Data field: Actual extractable value (e.g., "chairman", "total_assets")
    Metadata field: ExtractionField properties (e.g., ".confidence", ".evidence_pages")
    """

    # ExtractionField metadata properties
    METADATA_PROPERTIES = {
        "value", "confidence", "source", "evidence_pages", "extraction_method",
        "model_used", "validation_status", "alternative_values",
        "extraction_timestamp", "original_string"
    }

    # ExtractionField types
    EXTRACTION_FIELD_TYPES = (
        StringField, NumberField, DateField, ListField, BooleanField, DictField
    )

    def __init__(self):
        """Initialize counters."""
        self.data_fields: Set[str] = set()
        self.metadata_fields: Set[str] = set()
        self.core_data_fields: Set[str] = set()
        self.optional_data_fields: Set[str] = set()

    def count_model_fields(
        self,
        model: type[BaseModel],
        path: str = "",
        depth: int = 0
    ) -> Dict[str, int]:
        """
        Recursively count data vs metadata fields.

        Returns:
            {"data_fields": N, "metadata_fields": M}
        """
        if depth > 10:
            return {"data_fields": 0, "metadata_fields": 0}

        counts = {"data_fields": 0, "metadata_fields": 0}

        for field_name, field_info in model.model_fields.items():
            field_path = f"{path}.{field_name}" if path else field_name

            # Check if this is metadata within an ExtractionField
            if self._is_metadata_property(field_name):
                self.metadata_fields.add(field_path)
                counts["metadata_fields"] += 1
                continue  # Don't recurse into metadata

            # This is a data field
            self.data_fields.add(field_path)
            counts["data_fields"] += 1

            # Categorize as core or optional
            if field_info.is_required():
                self.core_data_fields.add(field_path)
            else:
                self.optional_data_fields.add(field_path)

            # Get field type
            field_type = field_info.annotation
            base_type = self._extract_base_type(field_type)

            # Recursively count nested model fields
            if self._is_pydantic_model(base_type):
                nested_counts = self.count_model_fields(base_type, field_path, depth + 1)
                counts["data_fields"] += nested_counts["data_fields"]
                counts["metadata_fields"] += nested_counts["metadata_fields"]

        return counts

    def _is_metadata_property(self, field_name: str) -> bool:
        """Check if field is an ExtractionField metadata property."""
        return field_name in self.METADATA_PROPERTIES

    def _extract_base_type(self, field_type: Any) -> Any:
        """Extract base type from Optional, List, etc."""
        if hasattr(field_type, "__args__"):
            args = field_type.__args__
            if args:
                for arg in args:
                    if arg is not type(None):
                        return self._extract_base_type(arg)
        return field_type

    def _is_pydantic_model(self, field_type: Any) -> bool:
        """Check if field type is a Pydantic model."""
        try:
            return (
                isinstance(field_type, type) and
                issubclass(field_type, BaseModel) and
                field_type is not BaseModel
            )
        except TypeError:
            return False

    def analyze_schema(self) -> Dict[str, Any]:
        """Analyze BRFAnnualReport schema with smart counting."""
        print(f"\n{'='*80}")
        print(f"Smart Field Analysis: Data Fields vs Metadata")
        print(f"{'='*80}")

        counts = self.count_model_fields(BRFAnnualReport)

        # Count by section (data fields only)
        sections = {}
        for field_path in sorted(self.data_fields):
            section = field_path.split(".")[0]
            sections[section] = sections.get(section, 0) + 1

        analysis = {
            "data_fields_total": counts["data_fields"],
            "metadata_fields_total": counts["metadata_fields"],
            "core_data_fields": len(self.core_data_fields),
            "optional_data_fields": len(self.optional_data_fields),
            "sections": sections,
            "sample_data_fields": sorted(list(self.data_fields))[:30],
            "sample_metadata_fields": sorted(list(self.metadata_fields))[:10]
        }

        return analysis

    def print_analysis(self, analysis: Dict[str, Any]):
        """Pretty print analysis."""
        print(f"\n📊 Smart Field Counting Results:")
        print(f"\n   DATA FIELDS (what we extract):")
        print(f"      Total: {analysis['data_fields_total']}")
        print(f"      - Core (always applicable): {analysis['core_data_fields']}")
        print(f"      - Optional (document-dependent): {analysis['optional_data_fields']}")

        print(f"\n   METADATA FIELDS (ExtractionField properties):")
        print(f"      Total: {analysis['metadata_fields_total']}")
        print(f"      (confidence, evidence_pages, source, etc.)")

        print(f"\n   TOTAL SCHEMA FIELDS: {analysis['data_fields_total'] + analysis['metadata_fields_total']}")

        print(f"\n📋 Data Fields by Section:")
        for section, count in sorted(analysis['sections'].items(), key=lambda x: -x[1]):
            print(f"   - {section:25s}: {count:3d} data fields")

        print(f"\n🔍 Sample Data Fields (first 15):")
        for i, field in enumerate(analysis['sample_data_fields'][:15], 1):
            print(f"   {i:2d}. {field}")

        print(f"\n🔍 Sample Metadata Fields:")
        for i, field in enumerate(analysis['sample_metadata_fields'], 1):
            print(f"   {i:2d}. {field}")

        print(f"\n💡 Key Insight for 95/95 Validation:")
        print(f"   - Use {analysis['data_fields_total']} DATA FIELDS as denominator")
        print(f"   - Current pipeline extracts ~84-117 fields")
        print(f"   - Coverage = extracted / {analysis['data_fields_total']} * 100%")
        print(f"   - Target: 95% coverage = {int(analysis['data_fields_total'] * 0.95)} fields")


def main():
    """Analyze schema with smart field counting."""

    counter = SmartFieldCounter()
    analysis = counter.analyze_schema()
    counter.print_analysis(analysis)

    # Save analysis
    import json
    output_file = Path(__file__).parent / "results" / "smart_field_analysis.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\n💾 Analysis saved to: {output_file}")

    return analysis


if __name__ == "__main__":
    main()
