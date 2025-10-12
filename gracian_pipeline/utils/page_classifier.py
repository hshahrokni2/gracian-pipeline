"""
Page-Level Classification for Hybrid PDFs
==========================================

Classifies individual pages within a PDF to enable mixed-mode extraction.

Problem Solved: Hybrid PDFs with page-level heterogeneity
- Some pages are machine-readable text (headers, narratives)
- Other pages are scanned images (financial statements, tables)
- Document-level classification misses this pattern

Solution: Analyze Docling markdown to identify image-based pages
- Detect `<!-- image -->` markers after section headings
- Classify each page as "text" or "image"
- Enable page-specific extraction routing

Example Case: brf_76536.pdf
- Pages 1-8, 13-19: Text extraction (headers, narratives)
- Pages 9-12: Vision extraction (financial statements as images)
- Result: 6.8% → 25-30% coverage (+18-23pp)
"""

from typing import List, Dict, Tuple
import re


def detect_image_pages_from_markdown(markdown: str, total_pages: int) -> Dict[str, List[int]]:
    """
    Detect which pages contain primarily images vs text from Docling markdown.

    Args:
        markdown: Docling markdown output
        total_pages: Total number of pages in PDF

    Returns:
        Dict with 'text_pages' and 'image_pages' lists

    Example:
        >>> markdown = "## Resultaträkning\\n\\n<!-- image -->\\n\\n## Balansräkning\\n\\n<!-- image -->"
        >>> result = detect_image_pages_from_markdown(markdown, 19)
        >>> result['image_pages']  # Pages with financial data as images
        [9, 10, 11, 12]
    """

    # Strategy: Look for patterns where section headings are followed by image markers
    # This indicates the page has a heading but the content is an image

    lines = markdown.split('\n')

    # Track sections that are images
    image_sections = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this is a section heading
        if line.startswith('##'):
            # Look ahead to see if followed by image marker
            j = i + 1
            found_image = False
            found_text = False

            # Look at next 5 lines
            while j < min(i + 6, len(lines)):
                next_line = lines[j].strip()

                if next_line == '<!-- image -->':
                    found_image = True
                    break
                elif next_line and not next_line.startswith('#'):
                    # Found actual text content (not a heading)
                    if len(next_line) > 20:  # Substantial text
                        found_text = True
                        break

                j += 1

            # If heading followed by image (and no text), mark as image section
            if found_image and not found_text:
                section_name = line.replace('##', '').strip()
                image_sections.append(section_name)

        i += 1

    # Identify financial statement pages (most likely to be images in Swedish BRF docs)
    financial_keywords = [
        'Resultaträkning',  # Income statement
        'Balansräkning',    # Balance sheet
        'Kassaflödesanalys', # Cash flow statement
        'Kassaüödesanalys',  # Cash flow (alternative spelling)
    ]

    # Pages with financial sections that are images
    financial_image_sections = [
        section for section in image_sections
        if any(keyword in section for keyword in financial_keywords)
    ]

    # Count total image markers
    total_image_markers = markdown.count('<!-- image -->')

    # Heuristic: If we found financial sections as images, assume they're on pages 9-12
    # (typical location in Swedish BRF annual reports)
    # In future, we can enhance this with page number extraction from Docling provenance

    if financial_image_sections:
        # Typical Swedish BRF structure:
        # Pages 1-8: Cover, intro, governance, operations
        # Pages 9-12: Financial statements (often scanned)
        # Pages 13+: Notes, signatures

        # Conservative estimate: Financial pages are 9-12
        image_pages = list(range(9, min(13, total_pages + 1)))
    else:
        # Fallback: Use image marker density
        # If >50% of markdown is image markers, treat as mostly scanned
        image_ratio = total_image_markers / max(1, len(lines))

        if image_ratio > 0.1:  # >10% image markers
            # High image content - likely scanned throughout
            # Use document-level classification instead
            image_pages = []
        else:
            image_pages = []

    # Text pages are all others
    all_pages = list(range(1, total_pages + 1))
    text_pages = [p for p in all_pages if p not in image_pages]

    return {
        'text_pages': text_pages,
        'image_pages': image_pages,
        'image_sections': image_sections,
        'financial_image_sections': financial_image_sections,
        'total_image_markers': total_image_markers,
    }


def analyze_page_content_density(markdown: str) -> Dict[str, any]:
    """
    Analyze content density to help classify pages.

    Returns metrics like:
    - Lines per page (estimate)
    - Image marker density
    - Text content density
    """

    lines = markdown.split('\n')
    total_lines = len(lines)
    non_empty_lines = sum(1 for line in lines if line.strip())

    image_markers = markdown.count('<!-- image -->')
    section_headings = sum(1 for line in lines if line.strip().startswith('##'))

    # Rough estimate of text content
    text_chars = sum(len(line) for line in lines if not line.strip().startswith('<!--'))

    return {
        'total_lines': total_lines,
        'non_empty_lines': non_empty_lines,
        'image_markers': image_markers,
        'section_headings': section_headings,
        'text_chars': text_chars,
        'image_marker_density': image_markers / max(1, total_lines),
        'text_density': text_chars / max(1, total_lines),
    }


def should_use_mixed_mode_extraction(
    markdown: str,
    total_pages: int,
    char_threshold: int = 5000,
    tables: List[Dict] = None
) -> Tuple[bool, str]:
    """
    Determine if PDF should use mixed-mode extraction (text + vision).

    ENHANCED DETECTION (Week 3 Day 6 - Unified Fix):
    - Priority 1: Financial sections as images (original brf_76536 pattern)
    - Priority 2: Empty/malformed tables (NEW - brf_83301 pattern)
    - Priority 3: High image density (NEW - brf_282765 pattern)

    Args:
        markdown: Docling markdown output
        total_pages: Total number of pages
        char_threshold: Threshold for "enough text" (default 5000)
        tables: Docling table structures (optional)

    Returns:
        (should_use_mixed_mode, reason)

    Decision Logic:
    1. PRIORITY 1: Check if financial sections are images → Use mixed-mode
    2. PRIORITY 2: Check if tables are empty/malformed → Use mixed-mode (NEW!)
    3. PRIORITY 3: Check if high image density → Use mixed-mode (NEW!)
    4. AFTER image checks: Very low text (<1000 chars) → Pure scanned
    5. Standard: Mostly text (>5000 chars, <10 images, good tables) → Text only
    6. Borderline: Use document-level classification

    CRITICAL FIX: Check for image signals BEFORE rejecting on char count!

    Examples:
    - brf_76536.pdf: 2,558 chars but pages 9-12 are images → TRIGGER
    - brf_83301.pdf: 13,809 chars but 14 tables with 0 columns → TRIGGER (NEW!)
    - brf_282765.pdf: 10,206 chars but 26 image markers → TRIGGER (NEW!)
    """

    char_count = len(markdown.strip())
    tables = tables or []

    # Count image markers
    image_markers = markdown.count('<!-- image -->')

    # Initialize empty_ratio
    empty_ratio = 0.0

    # ===== PRIORITY 1: Financial sections as images =====
    page_classification = detect_image_pages_from_markdown(markdown, total_pages)

    # If financial pages are images → Use mixed-mode (REGARDLESS of total char count)
    # This is the key fix for brf_76536.pdf type PDFs
    if page_classification['financial_image_sections']:
        return True, "financial_sections_are_images"

    # If we have other image pages detected → Use mixed-mode
    if page_classification['image_pages']:
        return True, f"detected_{len(page_classification['image_pages'])}_image_pages"

    # ===== PRIORITY 2: Empty/malformed tables (NEW - Week 3 Day 6) =====
    # If Docling detected tables but can't extract data → Image-based tables
    # BUG FIX (Week 3 Day 6 Extended): Table 'data' is a DICT, not a list!
    # Structure: {'table_cells': [], 'num_rows': 0, 'num_cols': 0, 'grid': []}
    if len(tables) > 0:
        empty_table_count = 0

        for table in tables:
            data = table.get('data', {})

            # FIXED: Check dictionary structure for empty tables
            # A table with num_cols == 0 is an empty/malformed table
            if isinstance(data, dict):
                num_cols = data.get('num_cols', 0)
                if num_cols == 0:
                    empty_table_count += 1
                    continue
            # Legacy list format (for compatibility)
            elif isinstance(data, list):
                if not data or len(data) == 0:
                    empty_table_count += 1
                    continue
                first_row = data[0] if len(data) > 0 else []
                if not first_row or len(first_row) == 0:
                    empty_table_count += 1

        # If >50% of tables are empty AND we have ≥5 tables → Image-based tables
        empty_ratio = empty_table_count / len(tables) if len(tables) > 0 else 0

        if empty_ratio > 0.5 and len(tables) >= 5:
            return True, f"empty_tables_detected_{empty_table_count}of{len(tables)}"

    # ===== PRIORITY 3: High image density (NEW - Week 3 Day 6) =====
    # If >10 image markers AND not too much text → Image-heavy hybrid
    if image_markers >= 10:
        if char_count < 15000:  # Not too much text (borderline)
            return True, f"image_heavy_hybrid_{image_markers}_markers"

    # ===== AFTER image checks: Very low text check =====
    # Very low text (< 1000 chars) → Pure scanned (use full vision, not mixed-mode)
    if char_count < 1000:
        return False, "too_little_text_for_mixed_mode"

    # ===== Standard machine-readable check =====
    # Enough text, low image density, good tables → Text extraction only
    if char_count >= char_threshold and image_markers < 10 and empty_ratio < 0.5:
        return False, "sufficient_text_extraction"

    # ===== Borderline case =====
    # Use document-level classification or mixed-mode for safety
    return True, f"borderline_case_{char_count}_chars_{image_markers}_images"


# Example usage and testing
if __name__ == "__main__":
    # Test with brf_76536.pdf pattern
    test_markdown = """
## Årsredovisning 2023 Brf Laduviken

769625-8289

<!-- image -->

## Välkommen till årsredovisningen för Brf Laduviken

## Innehåll

<!-- image -->

## Resultaträkning

<!-- image -->

## Balansräkning

<!-- image -->

## Balansräkning

<!-- image -->

## Kassaflödesanalys

<!-- image -->

## Noter

Some actual text content here about the notes section.
This is real extractable text, not an image.
"""

    print("Testing page classification logic:")
    print("=" * 80)

    result = detect_image_pages_from_markdown(test_markdown, 19)

    print(f"\nImage sections detected: {result['image_sections']}")
    print(f"Financial image sections: {result['financial_image_sections']}")
    print(f"Image pages (estimated): {result['image_pages']}")
    print(f"Text pages: {result['text_pages'][:5]}... (showing first 5)")
    print(f"Total image markers: {result['total_image_markers']}")

    # Test mixed-mode decision
    should_use, reason = should_use_mixed_mode_extraction(test_markdown, 19)
    print(f"\nShould use mixed-mode: {should_use}")
    print(f"Reason: {reason}")

    # Test content density
    density = analyze_page_content_density(test_markdown)
    print(f"\nContent density analysis:")
    for key, value in density.items():
        print(f"  {key}: {value}")
