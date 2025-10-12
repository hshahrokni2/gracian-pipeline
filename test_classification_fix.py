#!/usr/bin/env python3
"""
Test PDF classification fix on 9 SRS low performers.

Expected results based on Week 3 Day 6 Phase 3 analysis:
- 4 Pure Scanned: brf_76536, brf_276629, brf_80193, brf_78730
- 3 Hybrid: brf_43334, brf_282765, brf_57125
- 2 Truly Machine-Readable: brf_83301, brf_53107
"""

import sys
from pathlib import Path
from gracian_pipeline.utils.pdf_classifier import classify_pdf

# Test PDFs with expected classifications
test_cases = [
    # Pure Scanned (text_percentage < 20%)
    ("SRS/brf_76536.pdf", "scanned", 0.0),
    ("SRS/brf_276629.pdf", "scanned", 1.7),
    ("SRS/brf_80193.pdf", "scanned", 1.7),
    ("SRS/brf_78730.pdf", "scanned", 4.3),

    # Hybrid (20% < text_percentage < 80%)
    ("SRS/brf_43334.pdf", "hybrid", 6.8),
    ("SRS/brf_282765.pdf", "hybrid", 13.7),
    ("SRS/brf_57125.pdf", "hybrid", 14.5),

    # Truly Machine-Readable (text_percentage > 80%)
    ("SRS/brf_83301.pdf", "machine_readable", 12.0),
    ("SRS/brf_53107.pdf", "machine_readable", 14.5),
]

print("🔍 Testing PDF Classification Fix on 9 SRS Low Performers\n")
print("=" * 80)

correct = 0
total = len(test_cases)
results = []

for pdf_path, expected_class, old_coverage in test_cases:
    full_path = Path(__file__).parent / pdf_path

    if not full_path.exists():
        print(f"⚠️  {pdf_path}: NOT FOUND")
        results.append({"pdf": pdf_path, "status": "NOT FOUND"})
        continue

    # Classify PDF
    try:
        result = classify_pdf(str(full_path), verbose=False)
        actual_class = result["classification"]
        text_pct = result["text_percentage"]
        pages_with_text = result["pages_with_text"]
        total_pages = result["total_pages"]

        # Check if classification matches expected
        is_correct = actual_class == expected_class
        status = "✅" if is_correct else "❌"

        if is_correct:
            correct += 1

        # Print result
        print(f"\n{status} {pdf_path}")
        print(f"   Expected: {expected_class}")
        print(f"   Actual: {actual_class}")
        print(f"   Text percentage: {text_pct:.1f}% ({pages_with_text}/{total_pages} pages)")
        print(f"   Old coverage: {old_coverage}%")

        results.append({
            "pdf": pdf_path,
            "expected": expected_class,
            "actual": actual_class,
            "correct": is_correct,
            "text_percentage": text_pct,
            "pages_with_text": pages_with_text,
            "total_pages": total_pages,
            "old_coverage": old_coverage
        })

    except Exception as e:
        print(f"❌ {pdf_path}: ERROR - {str(e)}")
        results.append({
            "pdf": pdf_path,
            "status": "ERROR",
            "error": str(e)
        })

# Summary
print("\n" + "=" * 80)
print(f"\n📊 CLASSIFICATION TEST RESULTS")
print(f"   Correct: {correct}/{total} ({correct/total*100:.1f}%)")
print(f"   Target: 100% accuracy")

# Breakdown by category
print(f"\n📋 Breakdown:")
scanned = [r for r in results if r.get("actual") == "scanned"]
hybrid = [r for r in results if r.get("actual") == "hybrid"]
machine = [r for r in results if r.get("actual") == "machine_readable"]

print(f"   Scanned: {len(scanned)} PDFs")
print(f"   Hybrid: {len(hybrid)} PDFs (THE KEY FIX!)")
print(f"   Machine-readable: {len(machine)} PDFs")

# Success determination
if correct == total:
    print(f"\n🎉 SUCCESS: All 9 PDFs classified correctly!")
    print(f"   - 4 Scanned PDFs detected (need OCR)")
    print(f"   - 3 Hybrid PDFs detected (were misclassified, now fixed!)")
    print(f"   - 2 Machine-readable PDFs detected (need separate investigation)")
    print(f"\n✅ Ready to proceed with Track 1 (OCR) and Track 2 (Hybrid extraction)")
    sys.exit(0)
else:
    print(f"\n⚠️  PARTIAL SUCCESS: {correct}/{total} correct")
    print(f"   Review misclassifications above")
    sys.exit(1)
