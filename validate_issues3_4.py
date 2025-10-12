#!/usr/bin/env python3
"""
Phase 1 Full Validation: Issues #3 & #4 Integration Test
Tests board members with Suppleant roles and individual loans extraction.
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from gracian_pipeline.core.pydantic_extractor import extract_brf_to_pydantic

def main():
    print('=' * 80)
    print('PHASE 1 FULL VALIDATION: Issues #3 & #4 Integration Test')
    print('=' * 80)
    print()
    print('Document: brf_198532.pdf')
    print('Mode: deep (comprehensive extraction)')
    print('Fixes under test:')
    print('  - Issue #3: Board members with Suppleant roles')
    print('  - Issue #4: Individual loans from Note 5')
    print()
    print('Starting extraction...')
    print()

    try:
        # Force deep mode for comprehensive extraction
        result = extract_brf_to_pydantic(
            'SRS/brf_198532.pdf',
            mode='deep'
        )

        print('=' * 80)
        print('EXTRACTION COMPLETE')
        print('=' * 80)
        print()

        # ========================================
        # TEST 1: BOARD MEMBERS (Issue #3)
        # ========================================
        print('TEST 1: BOARD MEMBERS EXTRACTION (Issue #3)')
        print('-' * 80)

        if result.governance and result.governance.board_members:
            print(f'Total members extracted: {len(result.governance.board_members)}')
            print()
            print('Member Details:')

            role_counts = {'ordforande': 0, 'ledamot': 0, 'suppleant': 0, 'revisor': 0}

            for i, member in enumerate(result.governance.board_members, 1):
                name = member.full_name.value if hasattr(member.full_name, 'value') else member.full_name
                role = member.role  # Plain Literal, not ExtractionField

                # Count roles
                role_lower = str(role).lower()
                if 'ordförande' in role_lower or 'ordforande' in role_lower:
                    role_counts['ordforande'] += 1
                elif 'suppleant' in role_lower:
                    role_counts['suppleant'] += 1
                elif 'revisor' in role_lower:
                    role_counts['revisor'] += 1
                elif 'ledamot' in role_lower:
                    role_counts['ledamot'] += 1

                print(f'  {i}. {name}: {role}')

            print()
            print('Role Distribution:')
            print(f'  Ordförande: {role_counts["ordforande"]}')
            print(f'  Ledamot: {role_counts["ledamot"]}')
            print(f'  Suppleant: {role_counts["suppleant"]}')
            print(f'  Revisor: {role_counts["revisor"]}')
            print()

            # Validation
            print('ISSUE #3 VALIDATION:')
            if len(result.governance.board_members) >= 7:
                print('  ✅ Total members: 7+ (expected 7)')
            else:
                print(f'  ❌ Total members: {len(result.governance.board_members)} (expected 7)')

            if role_counts['suppleant'] >= 2:
                print(f'  ✅ Suppleant roles: {role_counts["suppleant"]} (expected 2)')
            else:
                print(f'  ❌ Suppleant roles: {role_counts["suppleant"]} (expected 2)')

            # Check for specific names from ground truth
            names = [member.full_name.value if hasattr(member.full_name, 'value') else member.full_name
                    for member in result.governance.board_members]
            names_str = ' '.join(names).lower()

            if 'lisa lind' in names_str:
                print('  ✅ Lisa Lind found (expected Suppleant)')
            else:
                print('  ❌ Lisa Lind NOT found (expected Suppleant)')

            if 'daniel wetter' in names_str:
                print('  ✅ Daniel Wetter found (expected Suppleant)')
            else:
                print('  ❌ Daniel Wetter NOT found (expected Suppleant)')
        else:
            print('❌ NO BOARD MEMBERS EXTRACTED')

        print()

        # ========================================
        # TEST 2: LOANS (Issue #4)
        # ========================================
        print('TEST 2: LOANS EXTRACTION (Issue #4)')
        print('-' * 80)

        if result.loans and len(result.loans) > 0:
            print(f'Total loans extracted: {len(result.loans)}')
            print()
            print('Loan Details:')

            total_balance = 0
            for i, loan in enumerate(result.loans, 1):
                lender = loan.lender.value if hasattr(loan.lender, 'value') else loan.lender
                loan_num = loan.loan_number.value if hasattr(loan.loan_number, 'value') else loan.loan_number
                balance = loan.outstanding_balance.value if hasattr(loan.outstanding_balance, 'value') else loan.outstanding_balance
                rate = loan.interest_rate.value if hasattr(loan.interest_rate, 'value') else loan.interest_rate

                total_balance += float(balance) if balance else 0

                print(f'  {i}. {lender} {loan_num}')
                print(f'     Balance: {float(balance):,.0f} kr')
                print(f'     Rate: {float(rate):.2%}' if rate else '     Rate: N/A')

            print()
            print(f'Total Outstanding: {total_balance:,.0f} kr')
            print()

            # Validation
            print('ISSUE #4 VALIDATION:')
            if len(result.loans) >= 4:
                print(f'  ✅ Total loans: {len(result.loans)} (expected 4)')
            else:
                print(f'  ❌ Total loans: {len(result.loans)} (expected 4)')

            # Check for specific loan numbers from ground truth
            loan_numbers = []
            for loan in result.loans:
                loan_num = loan.loan_number.value if hasattr(loan.loan_number, 'value') else loan.loan_number
                if loan_num:
                    loan_numbers.append(str(loan_num))

            expected_loans = ['41431520', '41441125', '10012345', '10023456']
            found_loans = [num for num in expected_loans if any(num in ln for ln in loan_numbers)]

            if len(found_loans) >= 4:
                print(f'  ✅ Expected loan numbers found: {len(found_loans)}/4')
            else:
                print(f'  ⚠️ Expected loan numbers found: {len(found_loans)}/4')

            # Check for structured format
            has_lender = any(loan.lender.value if hasattr(loan.lender, 'value') else loan.lender for loan in result.loans)
            has_loan_num = any(loan.loan_number.value if hasattr(loan.loan_number, 'value') else loan.loan_number for loan in result.loans)

            if has_lender and has_loan_num:
                print('  ✅ Structured format confirmed (lender + loan_number)')
            else:
                print('  ❌ Structured format incomplete')

        else:
            print('❌ NO LOANS EXTRACTED')
            print('ISSUE #4 VALIDATION:')
            print('  ❌ Total loans: 0 (expected 4)')

        print()
        print('=' * 80)
        print('PHASE 1 VALIDATION COMPLETE')
        print('=' * 80)

        # Return success status
        return 0

    except Exception as e:
        print(f'❌ EXTRACTION FAILED: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
