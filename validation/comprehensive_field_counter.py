"""
Comprehensive Field Counter - Count ALL 300+ Fields Properly
============================================================

Problem: Current metrics only count 117 fields (top-level).
Solution: Count ALL nested fields in BRFAnnualReport schema.

This script:
1. Analyzes BRFAnnualReport schema recursively
2. Counts ALL fields (including nested structures)
3. Categorizes fields by applicability (always vs document-dependent)
4. Provides accurate coverage calculations

Author: Claude Code
Date: 2025-10-13
"""

import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple, Any
from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gracian_pipeline.models.brf_schema import (
    BRFAnnualReport,
    DocumentMetadata,
    GovernanceStructure,
    FinancialData,
    PropertyDetails,
    FeeStructure,
    NotesCollection,
    LoanDetails,
    DynamicMultiYearOverview,
    OperationsData,
    EnvironmentalData
)


class SchemaFieldCounter:
    """Count ALL fields in BRFAnnualReport schema recursively."""

    def __init__(self):
        """Initialize field counter."""
        self.core_fields: Set[str] = set()
        self.optional_fields: Set[str] = set()
        self.list_fields: Set[str] = set()
        self.field_paths: List[str] = []

    def count_model_fields(
        self,
        model: type[BaseModel],
        path: str = "",
        depth: int = 0
    ) -> int:
        """
        Recursively count all fields in a Pydantic model.

        Args:
            model: Pydantic model class
            path: Current field path (e.g., "financial.balance_sheet")
            depth: Current recursion depth

        Returns:
            Total field count
        """
        if depth > 10:  # Prevent infinite recursion
            return 0

        count = 0

        for field_name, field_info in model.model_fields.items():
            field_path = f"{path}.{field_name}" if path else field_name

            # Get field type
            field_type = field_info.annotation

            # Handle Optional types
            is_optional = False
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ is type(None) or "Optional" in str(field_type):
                    is_optional = True

            # Extract base type from Optional, List, etc.
            base_type = self._extract_base_type(field_type)

            # Count this field
            count += 1
            self.field_paths.append(field_path)

            # Categorize field
            if is_optional:
                self.optional_fields.add(field_path)
            else:
                self.core_fields.add(field_path)

            # Check if it's a list field
            if self._is_list_type(field_type):
                self.list_fields.add(field_path)

            # Recursively count nested model fields
            if self._is_pydantic_model(base_type):
                nested_count = self.count_model_fields(base_type, field_path, depth + 1)
                count += nested_count

        return count

    def _extract_base_type(self, field_type: Any) -> Any:
        """Extract base type from Optional, List, etc."""
        # Handle Optional[X]
        if hasattr(field_type, "__args__"):
            args = field_type.__args__
            if args:
                # Get first non-None type
                for arg in args:
                    if arg is not type(None):
                        return self._extract_base_type(arg)

        return field_type

    def _is_list_type(self, field_type: Any) -> bool:
        """Check if field is a List type."""
        if hasattr(field_type, "__origin__"):
            return field_type.__origin__ is list
        return False

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
        """Analyze complete BRFAnnualReport schema."""
        print(f"\n{'='*80}")
        print(f"Analyzing BRFAnnualReport Schema")
        print(f"{'='*80}")

        # Count all fields
        total_fields = self.count_model_fields(BRFAnnualReport)

        # Count by section
        sections = {
            "metadata": self._count_section_fields("metadata"),
            "governance": self._count_section_fields("governance"),
            "financial": self._count_section_fields("financial"),
            "multi_year_overview": self._count_section_fields("multi_year_overview"),
            "notes": self._count_section_fields("notes"),
            "property": self._count_section_fields("property"),
            "fees": self._count_section_fields("fees"),
            "loans": self._count_section_fields("loans"),
            "reserves": self._count_section_fields("reserves"),
            "operations": self._count_section_fields("operations"),
            "environmental": self._count_section_fields("environmental"),
        }

        # Report results
        analysis = {
            "total_fields": total_fields,
            "core_fields": len(self.core_fields),
            "optional_fields": len(self.optional_fields),
            "list_fields": len(self.list_fields),
            "sections": sections,
            "field_paths": self.field_paths[:50]  # First 50 for inspection
        }

        return analysis

    def _count_section_fields(self, section_name: str) -> int:
        """Count fields in a specific section."""
        return len([p for p in self.field_paths if p.startswith(section_name)])

    def print_analysis(self, analysis: Dict[str, Any]):
        """Pretty print schema analysis."""
        print(f"\n📊 Schema Analysis Results:")
        print(f"   Total Fields: {analysis['total_fields']}")
        print(f"   - Core (always applicable): {analysis['core_fields']}")
        print(f"   - Optional (document-dependent): {analysis['optional_fields']}")
        print(f"   - List fields (variable count): {analysis['list_fields']}")

        print(f"\n📋 Fields by Section:")
        for section, count in sorted(analysis['sections'].items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"   - {section:25s}: {count:3d} fields")

        print(f"\n🔍 Sample Field Paths (first 20):")
        for i, path in enumerate(analysis['field_paths'][:20], 1):
            print(f"   {i:2d}. {path}")

        print(f"\n💡 Key Insight:")
        print(f"   Current metrics count ~117 fields")
        print(f"   Actual schema has {analysis['total_fields']} fields")
        print(f"   Missing: {analysis['total_fields'] - 117} fields in coverage calculation!")


def main():
    """Analyze BRFAnnualReport schema and count all fields."""

    counter = SchemaFieldCounter()
    analysis = counter.analyze_schema()
    counter.print_analysis(analysis)

    # Save analysis
    import json
    output_file = Path(__file__).parent / "results" / "schema_field_analysis.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\n💾 Analysis saved to: {output_file}")

    return analysis


if __name__ == "__main__":
    main()
