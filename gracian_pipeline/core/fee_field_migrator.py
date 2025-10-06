"""
Fee Field Migrator for BRF Schema v1 → v2

Migrate legacy fee extractions to semantic v2 schema.
Ensures backwards compatibility during transition from English ambiguous fields to Swedish semantic fields.
"""

from typing import Dict, List, Any


class FeeFieldMigrator:
    """
    Migrate legacy fee extractions to semantic v2 schema.
    Ensures backwards compatibility during transition.
    """

    def migrate_fee_fields(self, extraction: Dict) -> Dict:
        """
        Migrate from v1 (English ambiguous) to v2 (Swedish semantic) schema.

        Args:
            extraction: Full extraction dictionary with all agents

        Returns:
            Migrated extraction with v2 fee fields
        """
        fees = extraction.get("fees_agent", {})

        if not fees:
            return extraction

        # Check if already using v2 schema
        if any(k.startswith("arsavgift_") or k.startswith("manadsavgift_") for k in fees):
            return extraction  # Already migrated

        # Migrate legacy fields
        migration_log = []

        # Legacy "monthly_fee" → likely "arsavgift_per_sqm"
        if "monthly_fee" in fees and fees["monthly_fee"]:
            # Swedish BRFs almost never use true monthly fees
            # This is likely misnamed annual fee per sqm
            fees["arsavgift_per_sqm"] = fees["monthly_fee"]
            fees["_fee_unit_verified"] = "per_sqm"
            fees["_fee_period_verified"] = "annual"
            migration_log.append("monthly_fee → arsavgift_per_sqm (assumed annual)")

        # Legacy "fee_per_sqm" → likely "arsavgift_per_sqm"
        if "fee_per_sqm" in fees and fees["fee_per_sqm"]:
            if "arsavgift_per_sqm" not in fees:  # Don't overwrite if already set
                fees["arsavgift_per_sqm"] = fees["fee_per_sqm"]
                fees["_fee_unit_verified"] = "per_sqm"
                fees["_fee_period_verified"] = "annual"
                migration_log.append("fee_per_sqm → arsavgift_per_sqm (time unit assumed annual)")

        # Add migration metadata
        if migration_log:
            fees["_migration_applied"] = True
            fees["_migration_log"] = migration_log

        return extraction

    def validate_fee_semantics(self, extraction: Dict) -> List[str]:
        """
        Validate fee field semantics and flag issues.

        Args:
            extraction: Full extraction dictionary

        Returns:
            List of validation warnings
        """
        warnings = []
        fees = extraction.get("fees_agent", {})

        if not fees:
            return warnings

        # Check for legacy field usage
        if "monthly_fee" in fees and fees.get("monthly_fee"):
            if not fees.get("_migration_applied"):
                warnings.append(
                    "Legacy field 'monthly_fee' used without migration - semantic accuracy uncertain"
                )

        # Validate metadata consistency
        if "arsavgift_per_sqm" in fees and fees.get("arsavgift_per_sqm"):
            if not fees.get("_fee_terminology_found"):
                warnings.append(
                    "arsavgift_per_sqm populated but no _fee_terminology_found - verify extraction"
                )

        # Check for contradictory fields
        if fees.get("arsavgift_per_sqm") and fees.get("manadsavgift_per_sqm"):
            warnings.append(
                "Both annual and monthly fees per sqm populated - verify document has both or extraction error"
            )

        # Check for unit/period metadata consistency
        if fees.get("arsavgift_per_sqm"):
            if fees.get("_fee_period_verified") == "monthly":
                warnings.append(
                    "arsavgift_per_sqm has monthly period metadata - likely extraction error"
                )

        if fees.get("manadsavgift_per_sqm"):
            if fees.get("_fee_period_verified") == "annual":
                warnings.append(
                    "manadsavgift_per_sqm has annual period metadata - likely extraction error"
                )

        return warnings

    def get_migration_summary(self, extraction: Dict) -> Dict[str, Any]:
        """
        Get summary of migration status for an extraction.

        Args:
            extraction: Full extraction dictionary

        Returns:
            Summary with migration status and field mapping
        """
        fees = extraction.get("fees_agent", {})

        summary = {
            "schema_version": "v2" if any(k.startswith("arsavgift_") for k in fees) else "v1",
            "migration_applied": fees.get("_migration_applied", False),
            "migration_log": fees.get("_migration_log", []),
            "semantic_warnings": self.validate_fee_semantics(extraction),
            "fields_populated": {}
        }

        # Count populated v2 fields
        v2_fields = [
            "arsavgift_per_sqm",
            "arsavgift_per_apartment",
            "manadsavgift_per_sqm",
            "manadsavgift_per_apartment"
        ]

        for field in v2_fields:
            if fees.get(field):
                summary["fields_populated"][field] = fees[field]

        return summary


# Test function
if __name__ == "__main__":
    import json

    print("Testing FeeFieldMigrator...")

    # Test Case 1: Legacy v1 extraction
    legacy_extraction = {
        "fees_agent": {
            "monthly_fee": 582,
            "fee_unit": "per_sqm",
            "evidence_pages": [5]
        }
    }

    print("\n=== TEST CASE 1: Legacy v1 Extraction ===")
    print("Input:", json.dumps(legacy_extraction["fees_agent"], indent=2))

    migrator = FeeFieldMigrator()
    migrated = migrator.migrate_fee_fields(legacy_extraction.copy())

    print("\nMigrated:", json.dumps(migrated["fees_agent"], indent=2))

    validation_warnings = migrator.validate_fee_semantics(migrated)
    print(f"\nValidation warnings: {len(validation_warnings)}")
    for warning in validation_warnings:
        print(f"  - {warning}")

    summary = migrator.get_migration_summary(migrated)
    print(f"\nMigration summary:")
    print(f"  Schema version: {summary['schema_version']}")
    print(f"  Migration applied: {summary['migration_applied']}")
    print(f"  Fields populated: {summary['fields_populated']}")

    # Test Case 2: Already v2 extraction
    v2_extraction = {
        "fees_agent": {
            "arsavgift_per_sqm": 582,
            "_fee_terminology_found": "Årsavgift/m² bostadsrättsyta",
            "_fee_unit_verified": "per_sqm",
            "_fee_period_verified": "annual",
            "evidence_pages": [5]
        }
    }

    print("\n\n=== TEST CASE 2: Already v2 Extraction ===")
    print("Input:", json.dumps(v2_extraction["fees_agent"], indent=2))

    migrated_v2 = migrator.migrate_fee_fields(v2_extraction.copy())

    print("\nMigrated:", json.dumps(migrated_v2["fees_agent"], indent=2))

    validation_warnings_v2 = migrator.validate_fee_semantics(migrated_v2)
    print(f"\nValidation warnings: {len(validation_warnings_v2)}")
    for warning in validation_warnings_v2:
        print(f"  - {warning}")

    summary_v2 = migrator.get_migration_summary(migrated_v2)
    print(f"\nMigration summary:")
    print(f"  Schema version: {summary_v2['schema_version']}")
    print(f"  Migration applied: {summary_v2['migration_applied']}")
    print(f"  Fields populated: {summary_v2['fields_populated']}")

    # Test Case 3: Contradictory fields (should warn)
    contradictory_extraction = {
        "fees_agent": {
            "arsavgift_per_sqm": 582,
            "manadsavgift_per_sqm": 48.5,
            "_fee_terminology_found": "Årsavgift/m²",
            "_fee_period_verified": "annual",
            "evidence_pages": [5]
        }
    }

    print("\n\n=== TEST CASE 3: Contradictory Fields ===")
    print("Input:", json.dumps(contradictory_extraction["fees_agent"], indent=2))

    validation_warnings_3 = migrator.validate_fee_semantics(contradictory_extraction)
    print(f"\nValidation warnings: {len(validation_warnings_3)}")
    for warning in validation_warnings_3:
        print(f"  - {warning}")

    print("\n✅ All FeeFieldMigrator tests completed!")
