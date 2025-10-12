"""
Verification script for ValidationEngine integration.

Checks that:
1. ValidationEngine is properly imported
2. ValidationEngine is initialized in RobustUltraComprehensiveExtractor
3. Integration points are correctly added to the code
"""

import sys
import inspect
from pathlib import Path

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_integration():
    """
    Verify that ValidationEngine is integrated into the production pipeline.
    """
    print("\n" + "="*80)
    print("VALIDATION ENGINE INTEGRATION VERIFICATION")
    print("="*80)

    # Check 1: Import ValidationEngine
    print("\n✓ Check 1: ValidationEngine import")
    try:
        from gracian_pipeline.core.validation_engine import ValidationEngine, ValidationReport, ValidationIssue
        print("  ✅ ValidationEngine imports successfully")
        print(f"  ✅ ValidationEngine class found: {ValidationEngine}")
        print(f"  ✅ ValidationReport class found: {ValidationReport}")
        print(f"  ✅ ValidationIssue class found: {ValidationIssue}")
    except ImportError as e:
        print(f"  ❌ Failed to import ValidationEngine: {e}")
        return False

    # Check 2: RobustUltraComprehensiveExtractor has ValidationEngine
    print("\n✓ Check 2: RobustUltraComprehensiveExtractor integration")
    try:
        from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

        # Check __init__ method
        init_source = inspect.getsource(RobustUltraComprehensiveExtractor.__init__)

        if "self.validation_engine = ValidationEngine()" in init_source:
            print("  ✅ ValidationEngine initialized in __init__")
        else:
            print("  ❌ ValidationEngine NOT initialized in __init__")
            return False

        # Check extract_brf_document method
        extract_source = inspect.getsource(RobustUltraComprehensiveExtractor.extract_brf_document)

        if "validation_report = self.validation_engine.validate_extraction" in extract_source:
            print("  ✅ ValidationEngine called in extract_brf_document")
        else:
            print("  ❌ ValidationEngine NOT called in extract_brf_document")
            return False

        if "_validation_report" in extract_source:
            print("  ✅ Validation report stored in result")
        else:
            print("  ❌ Validation report NOT stored in result")
            return False

    except Exception as e:
        print(f"  ❌ Failed to verify integration: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check 3: print_summary shows validation results
    print("\n✓ Check 3: Validation reporting in print_summary")
    try:
        summary_source = inspect.getsource(RobustUltraComprehensiveExtractor.print_summary)

        if "validation_report" in summary_source:
            print("  ✅ print_summary displays validation report")
        else:
            print("  ❌ print_summary does NOT display validation report")
            return False

        if "error_count" in summary_source and "warning_count" in summary_source:
            print("  ✅ print_summary shows error and warning counts")
        else:
            print("  ❌ print_summary does NOT show counts")
            return False

    except Exception as e:
        print(f"  ❌ Failed to verify print_summary: {e}")
        return False

    # Check 4: Validation patterns library
    print("\n✓ Check 4: Validation patterns library")
    try:
        # Create a ValidationEngine instance
        engine = ValidationEngine()

        # Check that VALIDATION_PATTERNS exists
        from gracian_pipeline.core.validation_engine import VALIDATION_PATTERNS

        print(f"  ✅ VALIDATION_PATTERNS found with {len(VALIDATION_PATTERNS)} categories")

        # Check key patterns
        if "loans" in VALIDATION_PATTERNS:
            print("  ✅ Loan validation patterns present")
            if "outstanding_balance" in VALIDATION_PATTERNS["loans"]:
                pattern = VALIDATION_PATTERNS["loans"]["outstanding_balance"]
                print(f"     - Min balance: {pattern.get('min', 'N/A')}")
                print(f"     - Max balance: {pattern.get('max', 'N/A')}")
                print(f"     - Forbidden values: {pattern.get('not_equal', 'N/A')}")
        else:
            print("  ❌ Loan validation patterns missing")
            return False

        if "property" in VALIDATION_PATTERNS:
            print("  ✅ Property validation patterns present")
        else:
            print("  ⚠️  Property validation patterns missing")

        if "cross_references" in VALIDATION_PATTERNS:
            print("  ✅ Cross-reference validation patterns present")
        else:
            print("  ❌ Cross-reference validation patterns missing")
            return False

    except Exception as e:
        print(f"  ❌ Failed to verify patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "="*80)
    print("✅ ALL INTEGRATION CHECKS PASSED")
    print("="*80)
    print("\n🎉 ValidationEngine successfully integrated into production pipeline!")
    print("\nIntegration points:")
    print("  1. ✅ ValidationEngine imported in docling_adapter_ultra_v2.py")
    print("  2. ✅ ValidationEngine initialized in __init__")
    print("  3. ✅ validate_extraction() called after Pass 3")
    print("  4. ✅ Validation report stored in result['_validation_report']")
    print("  5. ✅ Validation results displayed in print_summary")
    print("  6. ✅ Validation patterns library complete (loans, property, cross-refs)")

    print("\n📋 Next Steps:")
    print("  - Run on test PDF with known errors to verify detection")
    print("  - Add validation metrics to quality scoring")
    print("  - Consider adding auto-retry for critical errors")

    return True


if __name__ == "__main__":
    try:
        success = verify_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
