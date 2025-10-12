"""
PDF Classification Utilities

Provides robust PDF classification based on text percentage per page,
fixing the hybrid PDF misclassification bug discovered in Week 3 Day 6.
"""

import fitz  # PyMuPDF
from typing import Dict, Any
from pathlib import Path


def classify_pdf(pdf_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Classify PDF as scanned, hybrid, or machine-readable based on text percentage.

    The classification uses TEXT PERCENTAGE (not average chars/page) to avoid
    the hybrid PDF bug where 2 text pages + 17 scanned pages = "machine-readable".

    Args:
        pdf_path: Path to PDF file
        verbose: If True, print classification details

    Returns:
        Dictionary with:
        - classification: "scanned", "hybrid", or "machine_readable"
        - text_percentage: Percentage of pages with meaningful text (0-100)
        - pages_with_text: Number of pages with >100 characters
        - total_pages: Total number of pages
        - is_machine_readable: Boolean (for backward compatibility)
        - avg_chars_per_page: Average characters per page (for reference)
    """
    # Validate path
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Open PDF
    doc = fitz.open(pdf_path)

    # Extract text from each page
    page_char_counts = []
    total_chars = 0

    for page in doc:  # Iterate over document directly
        text = page.get_text()
        chars = len(text)
        page_char_counts.append(chars)
        total_chars += chars

    total_pages = len(doc)
    doc.close()

    # Calculate metrics
    pages_with_text = sum(1 for c in page_char_counts if c > 100)  # >100 chars = meaningful text
    text_percentage = (pages_with_text / total_pages * 100) if total_pages > 0 else 0
    avg_chars_per_page = total_chars / total_pages if total_pages > 0 else 0

    # Classify based on text percentage (NOT average!)
    if text_percentage > 80:
        classification = "machine_readable"
        is_machine_readable = True
    elif text_percentage > 20:
        classification = "hybrid"
        is_machine_readable = False  # CRITICAL: Treat hybrids as scanned for OCR
    else:
        classification = "scanned"
        is_machine_readable = False

    result = {
        "classification": classification,
        "text_percentage": text_percentage,
        "pages_with_text": pages_with_text,
        "total_pages": total_pages,
        "is_machine_readable": is_machine_readable,
        "avg_chars_per_page": avg_chars_per_page,
    }

    if verbose:
        print(f"PDF Classification: {pdf_path_obj.name}")
        print(f"  Total pages: {total_pages}")
        print(f"  Pages with text (>100 chars): {pages_with_text}/{total_pages} ({text_percentage:.1f}%)")
        print(f"  Avg chars/page: {avg_chars_per_page:.1f}")
        print(f"  Classification: {classification}")
        print(f"  Needs OCR: {not is_machine_readable}")

    return result


def needs_ocr(pdf_path: str) -> bool:
    """
    Check if PDF needs OCR (is scanned or hybrid).

    This is a convenience function for pipeline logic.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF is scanned or hybrid (needs OCR), False otherwise
    """
    result = classify_pdf(pdf_path)
    return result["classification"] in ["scanned", "hybrid"]


# Backward compatibility function (mimics old broken behavior for comparison)
def classify_pdf_old_method(pdf_path: str) -> Dict[str, Any]:
    """
    OLD BROKEN METHOD: Classify based on average chars/page.

    This function demonstrates the bug that was fixed in Week 3 Day 6.
    Kept for reference and testing only.

    DO NOT USE IN PRODUCTION!
    """
    doc = fitz.open(pdf_path)

    total_chars = 0
    for page in doc:  # Iterate over document directly
        total_chars += len(page.get_text())

    total_pages = len(doc)
    doc.close()

    avg_chars_per_page = total_chars / total_pages if total_pages > 0 else 0

    # BROKEN LOGIC: This misses hybrid PDFs!
    is_machine_readable = avg_chars_per_page > 100

    return {
        "classification": "machine_readable" if is_machine_readable else "scanned",
        "avg_chars_per_page": avg_chars_per_page,
        "total_pages": total_pages,
        "is_machine_readable": is_machine_readable,
        "text_percentage": None,  # Not calculated in old method
    }
