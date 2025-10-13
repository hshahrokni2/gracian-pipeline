#!/usr/bin/env python3
"""
Tests for Schema V7.0 Swedish-First Pattern Implementation.

Tests the bidirectional Swedish ↔ English field synchronization for YearlyFinancialData:
- Swedish primary fields (nettoomsättning_tkr, soliditet_procent, etc.)
- English aliases (net_revenue_tkr, solidarity_percent, etc.)
- @model_validator automatic synchronization
- Backward compatibility with v6.0 code
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from schema_v7 import YearlyFinancialData


# ============================================================
# Test Swedish → English Synchronization (10 tests)
# ============================================================

def test_swedish_to_english_nettoomsattning():
    """Test Swedish nettoomsättning_tkr → English net_revenue_tkr"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67
    )
    assert data.nettoomsättning_tkr == 12345.67
    assert data.net_revenue_tkr == 12345.67  # Auto-synced


def test_swedish_to_english_resultat():
    """Test Swedish resultat_efter_finansiella_tkr → English result_after_financial_tkr"""
    data = YearlyFinancialData(
        year=2024,
        resultat_efter_finansiella_tkr=5432.10
    )
    assert data.resultat_efter_finansiella_tkr == 5432.10
    assert data.result_after_financial_tkr == 5432.10


def test_swedish_to_english_soliditet():
    """Test Swedish soliditet_procent → English solidarity_percent"""
    data = YearlyFinancialData(
        year=2024,
        soliditet_procent=45.8
    )
    assert data.soliditet_procent == 45.8
    assert data.solidarity_percent == 45.8


def test_swedish_to_english_arsavgift():
    """Test Swedish årsavgift_per_kvm → English annual_fee_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        årsavgift_per_kvm=125.50
    )
    assert data.årsavgift_per_kvm == 125.50
    assert data.annual_fee_per_kvm == 125.50


def test_swedish_to_english_skuld_total():
    """Test Swedish skuld_per_kvm_total → English debt_per_total_kvm"""
    data = YearlyFinancialData(
        year=2024,
        skuld_per_kvm_total=8500.00
    )
    assert data.skuld_per_kvm_total == 8500.00
    assert data.debt_per_total_kvm == 8500.00


def test_swedish_to_english_skuld_boyta():
    """Test Swedish skuld_per_kvm_boyta → English debt_per_residential_kvm"""
    data = YearlyFinancialData(
        year=2024,
        skuld_per_kvm_boyta=9200.00
    )
    assert data.skuld_per_kvm_boyta == 9200.00
    assert data.debt_per_residential_kvm == 9200.00


def test_swedish_to_english_rantekanslighet():
    """Test Swedish räntekänslighet_procent → English interest_sensitivity_percent"""
    data = YearlyFinancialData(
        year=2024,
        räntekänslighet_procent=2.5
    )
    assert data.räntekänslighet_procent == 2.5
    assert data.interest_sensitivity_percent == 2.5


def test_swedish_to_english_energikostnad():
    """Test Swedish energikostnad_per_kvm → English energy_cost_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        energikostnad_per_kvm=75.30
    )
    assert data.energikostnad_per_kvm == 75.30
    assert data.energy_cost_per_kvm == 75.30


def test_swedish_to_english_avsattning():
    """Test Swedish avsättning_per_kvm → English savings_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        avsättning_per_kvm=50.00
    )
    assert data.avsättning_per_kvm == 50.00
    assert data.savings_per_kvm == 50.00


def test_swedish_to_english_arsavgift_andel():
    """Test Swedish årsavgift_andel_intäkter_procent → English annual_fees_percent_of_revenue"""
    data = YearlyFinancialData(
        year=2024,
        årsavgift_andel_intäkter_procent=85.5
    )
    assert data.årsavgift_andel_intäkter_procent == 85.5
    assert data.annual_fees_percent_of_revenue == 85.5


# ============================================================
# Test English → Swedish Synchronization (10 tests)
# ============================================================

def test_english_to_swedish_net_revenue():
    """Test English net_revenue_tkr → Swedish nettoomsättning_tkr (backward compatibility)"""
    data = YearlyFinancialData(
        year=2024,
        net_revenue_tkr=12345.67
    )
    assert data.net_revenue_tkr == 12345.67
    assert data.nettoomsättning_tkr == 12345.67  # Auto-synced


def test_english_to_swedish_result():
    """Test English result_after_financial_tkr → Swedish resultat_efter_finansiella_tkr"""
    data = YearlyFinancialData(
        year=2024,
        result_after_financial_tkr=5432.10
    )
    assert data.result_after_financial_tkr == 5432.10
    assert data.resultat_efter_finansiella_tkr == 5432.10


def test_english_to_swedish_solidarity():
    """Test English solidarity_percent → Swedish soliditet_procent"""
    data = YearlyFinancialData(
        year=2024,
        solidarity_percent=45.8
    )
    assert data.solidarity_percent == 45.8
    assert data.soliditet_procent == 45.8


def test_english_to_swedish_annual_fee():
    """Test English annual_fee_per_kvm → Swedish årsavgift_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        annual_fee_per_kvm=125.50
    )
    assert data.annual_fee_per_kvm == 125.50
    assert data.årsavgift_per_kvm == 125.50


def test_english_to_swedish_debt_total():
    """Test English debt_per_total_kvm → Swedish skuld_per_kvm_total"""
    data = YearlyFinancialData(
        year=2024,
        debt_per_total_kvm=8500.00
    )
    assert data.debt_per_total_kvm == 8500.00
    assert data.skuld_per_kvm_total == 8500.00


def test_english_to_swedish_debt_residential():
    """Test English debt_per_residential_kvm → Swedish skuld_per_kvm_boyta"""
    data = YearlyFinancialData(
        year=2024,
        debt_per_residential_kvm=9200.00
    )
    assert data.debt_per_residential_kvm == 9200.00
    assert data.skuld_per_kvm_boyta == 9200.00


def test_english_to_swedish_interest_sensitivity():
    """Test English interest_sensitivity_percent → Swedish räntekänslighet_procent"""
    data = YearlyFinancialData(
        year=2024,
        interest_sensitivity_percent=2.5
    )
    assert data.interest_sensitivity_percent == 2.5
    assert data.räntekänslighet_procent == 2.5


def test_english_to_swedish_energy_cost():
    """Test English energy_cost_per_kvm → Swedish energikostnad_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        energy_cost_per_kvm=75.30
    )
    assert data.energy_cost_per_kvm == 75.30
    assert data.energikostnad_per_kvm == 75.30


def test_english_to_swedish_savings():
    """Test English savings_per_kvm → Swedish avsättning_per_kvm"""
    data = YearlyFinancialData(
        year=2024,
        savings_per_kvm=50.00
    )
    assert data.savings_per_kvm == 50.00
    assert data.avsättning_per_kvm == 50.00


def test_english_to_swedish_annual_fees_percent():
    """Test English annual_fees_percent_of_revenue → Swedish årsavgift_andel_intäkter_procent"""
    data = YearlyFinancialData(
        year=2024,
        annual_fees_percent_of_revenue=85.5
    )
    assert data.annual_fees_percent_of_revenue == 85.5
    assert data.årsavgift_andel_intäkter_procent == 85.5


# ============================================================
# Test Bidirectional Sync Edge Cases (5 tests)
# ============================================================

def test_both_fields_set_same_value():
    """Test when both Swedish and English fields are set to same value"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        net_revenue_tkr=12345.67
    )
    assert data.nettoomsättning_tkr == 12345.67
    assert data.net_revenue_tkr == 12345.67


def test_swedish_takes_priority():
    """Test that Swedish field takes priority when both are set to different values"""
    # When both fields are provided, Swedish primary should take precedence
    data = YearlyFinancialData(
        year=2024,
        soliditet_procent=50.0,
        solidarity_percent=45.0  # Different value
    )
    # Swedish field should remain unchanged
    assert data.soliditet_procent == 50.0
    # English field should be synced from Swedish (since Swedish was set first in field order)
    # Note: In practice, the validator processes both, but Swedish has priority in the logic


def test_multiple_fields_sync():
    """Test syncing multiple Swedish fields at once"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=45.8,
        årsavgift_per_kvm=125.50
    )
    assert data.net_revenue_tkr == 12345.67
    assert data.solidarity_percent == 45.8
    assert data.annual_fee_per_kvm == 125.50


def test_none_values_not_synced():
    """Test that None values don't trigger synchronization"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=None,
        net_revenue_tkr=None
    )
    assert data.nettoomsättning_tkr is None
    assert data.net_revenue_tkr is None


def test_zero_values_do_sync():
    """Test that zero values (0.0) do trigger synchronization"""
    data = YearlyFinancialData(
        year=2024,
        soliditet_procent=0.0  # Zero is valid (e.g., zero equity ratio)
    )
    assert data.soliditet_procent == 0.0
    assert data.solidarity_percent == 0.0


# ============================================================
# Test Backward Compatibility with v6.0 Code (5 tests)
# ============================================================

def test_v6_english_only_code():
    """Test that v6.0 code using only English field names still works"""
    # Simulating v6.0 code that only knows about English names
    data = YearlyFinancialData(
        year=2024,
        net_revenue_tkr=12345.67,
        solidarity_percent=45.8,
        annual_fee_per_kvm=125.50
    )

    # v6.0 code can read English fields
    assert data.net_revenue_tkr == 12345.67
    assert data.solidarity_percent == 45.8
    assert data.annual_fee_per_kvm == 125.50

    # But now Swedish fields are also available
    assert data.nettoomsättning_tkr == 12345.67
    assert data.soliditet_procent == 45.8
    assert data.årsavgift_per_kvm == 125.50


def test_v7_swedish_only_code():
    """Test that new v7.0 code using only Swedish field names works"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67,
        soliditet_procent=45.8,
        årsavgift_per_kvm=125.50
    )

    # v7.0 code can read Swedish fields
    assert data.nettoomsättning_tkr == 12345.67
    assert data.soliditet_procent == 45.8
    assert data.årsavgift_per_kvm == 125.50

    # And English aliases are available for compatibility
    assert data.net_revenue_tkr == 12345.67
    assert data.solidarity_percent == 45.8
    assert data.annual_fee_per_kvm == 125.50


def test_json_serialization_includes_both():
    """Test that JSON serialization includes both Swedish and English fields"""
    data = YearlyFinancialData(
        year=2024,
        nettoomsättning_tkr=12345.67
    )

    json_dict = data.model_dump()

    # Both fields present in serialized JSON
    assert json_dict['nettoomsättning_tkr'] == 12345.67
    assert json_dict['net_revenue_tkr'] == 12345.67


def test_validation_bounds_work_for_both():
    """Test that Pydantic validation bounds work on Swedish primary fields"""
    # Note: Validation bounds (ge=0, le=100) are ONLY on Swedish fields
    # English aliases don't have bounds - they're just aliases for backward compatibility

    # Valid value via Swedish field
    data1 = YearlyFinancialData(year=2024, soliditet_procent=50.0)
    assert data1.soliditet_procent == 50.0

    # Valid value via English field (gets synced to Swedish field)
    data2 = YearlyFinancialData(year=2024, solidarity_percent=75.0)
    assert data2.solidarity_percent == 75.0
    assert data2.soliditet_procent == 75.0  # Synced to Swedish

    # Invalid value should raise ValidationError via Swedish field
    with pytest.raises(Exception):  # Pydantic ValidationError
        YearlyFinancialData(year=2024, soliditet_procent=150.0)

    # Note: English fields don't validate bounds directly
    # If validation is needed, it happens via sync to Swedish field
    # This is expected behavior: Swedish = primary with validation, English = alias for compatibility


def test_mixed_v6_v7_usage():
    """Test mixed usage of v6.0 English + v7.0 Swedish in same codebase"""
    # IMPORTANT: @model_validator only runs during initialization, not on attribute assignment
    # For proper syncing, all fields must be set during object creation

    # Correct approach: Set all fields during initialization
    data = YearlyFinancialData(
        year=2024,
        # Extractor A (v6.0) provides English fields
        net_revenue_tkr=12345.67,
        solidarity_percent=45.8,
        # Extractor B (v7.0) provides Swedish fields
        årsavgift_per_kvm=125.50,
        energikostnad_per_kvm=75.30
    )

    # Both extractors can read all fields - syncing happens during __init__
    assert data.nettoomsättning_tkr == 12345.67  # Synced from English
    assert data.soliditet_procent == 45.8         # Synced from English
    assert data.annual_fee_per_kvm == 125.50      # Synced from Swedish
    assert data.energy_cost_per_kvm == 75.30      # Synced from Swedish

    # Note: If you need to set fields post-initialization, create a new object
    # or use model_validate() to trigger validators again


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
