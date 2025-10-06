# Ground Truth Validation Report

**Date**: 1759765701.1084194

## Executive Summary

- **Total Fields Validated**: 186
- **Accuracy**: 76.7% (23/165 fields correct)
- **Coverage**: 13.9% (23/165 fields extracted)

### Breakdown

- ✅ **Correct**: 23 fields
- ≈ **Correct (rounded)**: 0 fields
- ❌ **Incorrect**: 0 fields
- ⚠️ **Missing**: 7 fields (present in PDF but not extracted)
- ℹ️ **Expected Missing**: 21 fields (not in PDF)
- 🔍 **Unexpected**: 135 fields (extracted but shouldn't be)

## ⚠️ Missing Extractions (Data Present in PDF)

### property_agent.apartment_breakdown.1_rok
- **Expected Value**: `10`
- **Status**: extraction_failed
- **Message**: Expected '10' but got null/empty

### property_agent.apartment_breakdown.2_rok
- **Expected Value**: `24`
- **Status**: extraction_failed
- **Message**: Expected '24' but got null/empty

### property_agent.apartment_breakdown.3_rok
- **Expected Value**: `23`
- **Status**: extraction_failed
- **Message**: Expected '23' but got null/empty

### property_agent.apartment_breakdown.4_rok
- **Expected Value**: `36`
- **Status**: extraction_failed
- **Message**: Expected '36' but got null/empty

### property_agent.apartment_breakdown.5_rok
- **Expected Value**: `1`
- **Status**: extraction_failed
- **Message**: Expected '1' but got null/empty

### property_agent.apartment_breakdown.>5_rok
- **Expected Value**: `0`
- **Status**: extraction_failed
- **Message**: Expected '0' but got null/empty

### property_agent.property_designation
- **Expected Value**: `Sonfjället 2`
- **Status**: extraction_failed
- **Message**: Expected 'Sonfjället 2' but got null/empty

## ✅ Sample Successful Extractions

- **fees_agent.arsavgift_per_sqm**: `582` (correct)
- **financial_agent.assets**: `675294786` (correct)
- **financial_agent.building_details.ackumulerade_anskaffningsvarden**: `682435875` (correct)
- **financial_agent.building_details.arets_avskrivningar**: `3503359` (correct)
- **financial_agent.building_details.planenligt_restvarde**: `666670761` (correct)
- **financial_agent.building_details.taxeringsvarde_byggnad**: `214200000` (correct)
- **financial_agent.building_details.taxeringsvarde_mark**: `175000000` (correct)
- **financial_agent.equity**: `559807676` (correct)
- **financial_agent.expenses**: `6631400` (correct)
- **financial_agent.liabilities**: `115487111` (correct)
- **financial_agent.receivables_breakdown.avrakning_ovrigt**: `53100` (correct)
- **financial_agent.receivables_breakdown.fordringar**: `1911314` (correct)
- **financial_agent.receivables_breakdown.klientmedel**: `3297711` (correct)
- **financial_agent.receivables_breakdown.momsavrakning**: `25293` (correct)
- **financial_agent.receivables_breakdown.skattekonto**: `192990` (correct)
- **financial_agent.revenue**: `7451585` (correct)
- **financial_agent.surplus**: `-353810` (correct)
- **governance_agent.audit_firm**: `KPMG AB` (correct)
- **governance_agent.auditor_name**: `Tobias Andersson` (correct)
- **governance_agent.board_members**: `['Torbjörn Andersson', 'Maria Annelie Eck Arvstrand', 'Mats Eskilson', 'Fredrik Linde']` (correct)

---

**Conclusion**: ❌ **NEEDS IMPROVEMENT** - Accuracy below 90%, significant fixes required
