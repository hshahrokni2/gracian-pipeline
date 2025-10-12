#!/usr/bin/env python3
"""
Quick schema structure test - verify BoardMember fields.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.models.brf_schema import BoardMember
from gracian_pipeline.models.base_fields import StringField

def main():
    print("=" * 80)
    print("SCHEMA STRUCTURE TEST: BoardMember")
    print("=" * 80)
    print()

    # Test 1: Create a BoardMember with full_name
    print("Test 1: Create BoardMember with full_name...")
    try:
        member = BoardMember(
            full_name=StringField(value="Test Person"),
            role="ledamot"
        )
        print(f"✅ BoardMember created successfully")
        print(f"   full_name: {member.full_name.value if hasattr(member.full_name, 'value') else member.full_name}")
        print(f"   role: {member.role}")
        print()
    except Exception as e:
        print(f"❌ Failed to create BoardMember: {e}")
        return 1

    # Test 2: Try to access 'name' attribute (should fail)
    print("Test 2: Try to access 'name' attribute (should not exist)...")
    try:
        _ = member.name
        print(f"❌ ERROR: 'name' attribute exists (should not!)")
        return 1
    except AttributeError as e:
        print(f"✅ Correct: 'name' attribute does not exist")
        print(f"   Error message: {e}")
        print()

    # Test 3: Verify full_name exists
    print("Test 3: Verify full_name attribute exists...")
    if hasattr(member, 'full_name'):
        print(f"✅ Correct: 'full_name' attribute exists")
        print()
    else:
        print(f"❌ ERROR: 'full_name' attribute missing")
        return 1

    print("=" * 80)
    print("ALL SCHEMA STRUCTURE TESTS PASSED ✅")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
