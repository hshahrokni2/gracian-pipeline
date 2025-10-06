"""
Property Designation Extractor
Extracts property designation (fastighetsbeteckning) from Swedish BRF documents.
"""

import re
from typing import Optional, Dict, Any


class PropertyDesignationExtractor:
    """
    Specialized extractor for property designation field.
    Handles Swedish property designation format (e.g., "Sonfjället 2").
    """

    def extract_property_designation(self, markdown: str) -> Optional[str]:
        """
        Extract property designation from document markdown.

        Looks for patterns like:
        - "Fastighetsbeteckning: Sonfjället 2"
        - "Fastighetsbeteckning Sonfjället 2"
        - "Fastighet: Sonfjället 2"

        Args:
            markdown: Document markdown text

        Returns:
            Property designation string or None if not found
        """

        # Try multiple patterns
        patterns = [
            r'Fastighetsbeteckning[:\s]+([A-ZÅÄÖ][a-zåäö]+\s+\d+)',
            r'Fastighet[:\s]+([A-ZÅÄÖ][a-zåäö]+\s+\d+)',
            r'Fastighetsbeteckning[:\s]+([A-ZÅÄÖ][a-zåäö]+\s+\d+[A-Z]?)',
            r'Beteckning[:\s]+([A-ZÅÄÖ][a-zåäö]+\s+\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                designation = match.group(1).strip()
                # Validate format (e.g., "Sonfjället 2")
                if self._validate_designation_format(designation):
                    return designation

        return None

    def _validate_designation_format(self, designation: str) -> bool:
        """
        Validate property designation format.

        Swedish property designations typically follow pattern:
        - Starts with capitalized word (name)
        - Followed by number
        - Optional letter suffix

        Examples:
        - "Sonfjället 2" ✓
        - "Kungsholmen 12A" ✓
        - "Invalid123" ✗
        """

        # Must have at least one letter and one number
        has_letter = any(c.isalpha() for c in designation)
        has_number = any(c.isdigit() for c in designation)

        if not (has_letter and has_number):
            return False

        # Should start with capital letter
        if not designation[0].isupper():
            return False

        # Should contain a space between name and number
        if ' ' not in designation:
            return False

        return True
