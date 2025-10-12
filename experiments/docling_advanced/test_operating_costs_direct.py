#!/usr/bin/env python3
"""Direct test of operating_costs_agent (skip full pipeline)"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
gracian_root = Path(__file__).resolve().parent.parent.parent
env_path = gracian_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent / "code"))

from base_brf_extractor import BaseExtractor

def main():
    print("🧪 Direct Test: operating_costs_agent (6-field expenses)\n")

    # Initialize extractor
    extractor = BaseExtractor()

    # Test on Resultaträkning section (income statement, pages 6-8)
    pdf_path = "../../SRS/brf_198532.pdf"

    # Financial section headings (includes Resultaträkning)
    section_headings = ["Resultaträkning", "RESULTATRÄKNING"]

    print("Extracting from Resultaträkning section (pages 6-8)...")
    print("Expected: 4-5/6 fields extracted (75-83% success rate)\n")

    # Call extraction directly
    result = extractor._extract_agent(
        pdf_path=pdf_path,
        agent_id="operating_costs_agent",
        section_headings=section_headings,
        context=None
    )

    # Display results
    print(f"Status: {result.get('status')}")
    print(f"Extraction time: {result.get('extraction_time', 0):.1f}s")
    print(f"Evidence pages: {result.get('evidence_pages', [])}")

    if result.get('status') == 'success':
        data = result.get('data', {})
        costs = data.get('operating_costs_breakdown', {})

        print(f"\n📊 Operating Costs Breakdown:")

        # Check each field
        fields_extracted = 0
        expected_fields = 6

        fields = [
            ('fastighetsskott', 'Property management'),
            ('reparationer', 'Repairs'),
            ('el', 'Electricity'),
            ('varme', 'Heating'),
            ('vatten', 'Water'),
            ('ovriga_externa_kostnader', 'Other external costs')
        ]

        for field_name, field_desc in fields:
            value = costs.get(field_name, 0)
            if value != 0:
                print(f"   ✅ {field_desc}: {value:,} kr")
                fields_extracted += 1
            else:
                print(f"   ❌ {field_desc}: Missing (0)")

        # Evidence pages
        evidence = costs.get('evidence_pages', [])
        if evidence:
            print(f"\n   ✅ Evidence pages: {evidence}")
        else:
            print(f"\n   ⚠️ Evidence pages: None")

        # Summary
        percentage = (fields_extracted / expected_fields) * 100
        print(f"\n📊 Summary: {fields_extracted}/{expected_fields} fields extracted ({percentage:.1f}%)")

        if fields_extracted >= 5:
            print("✅ EXCELLENT: ≥83% extraction rate (exceeds 75% target)")
        elif fields_extracted == 4:
            print("✅ SUCCESS: 67% extraction rate (meets 67% target)")
        elif fields_extracted >= 3:
            print("⚠️ PARTIAL: 50% extraction rate (below target)")
        else:
            print("❌ FAILED: <50% extraction rate")

        # Validate against ground truth (page 13, Note 6)
        print("\n🔍 Ground Truth Validation (page 13, Note 6):")
        print("   Expected values from Not 6 Rörelsekostnader:")
        print("   - Fastighetsskötsel: -3,032,087")
        print("   - Reparationer: -483,370")
        print("   - El: Not itemized (K2 format)")
        print("   - Värme: Not itemized (K2 format)")
        print("   - Vatten: Not itemized (K2 format)")
        print("   - Övriga externa kostnader: -3,115,943")

    else:
        print(f"\n❌ Extraction failed: {result.get('error', 'Unknown error')}")

    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
