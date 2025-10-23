"""
Text cleaning and normalization utilities.

Handles whitespace normalization, page marker removal, and validation.
"""

import re
from typing import Tuple, List, Dict, Any, Optional
import statistics

from config.constants import PATTERN_PAGE_MARKER, MAX_CONTENT_LOSS_PCT, MIN_SECTION_LENGTH
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TextCleaner:
    """Clean and normalize extracted text"""

    def __init__(self, debug: bool = False):
        """
        Initialize text cleaner.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.logger = logger

    def clean(
        self,
        text: str,
        validate: bool = True,
        formatted_blocks: Optional[List[Dict]] = None
    ) -> Tuple[str, List[str]]:
        """
        Clean and normalize text.

        Args:
            text: Raw extracted text
            validate: Whether to validate cleaned output
            formatted_blocks: Optional formatting metadata

        Returns:
            Tuple of (cleaned_text, warnings)
        """
        warnings = []
        original_text = text

        # Step 1: Remove page markers
        text = self.remove_page_markers(text)

        # Step 2: Normalize whitespace
        text = self.normalize_whitespace(text)

        # Step 3: Validate if requested
        if validate:
            validation_warnings = self.validate_cleaned_text(text, original_text)
            warnings.extend(validation_warnings)

        return text, warnings

    def remove_page_markers(self, text: str) -> str:
        """Remove page break markers like '--- Page N ---'"""
        return PATTERN_PAGE_MARKER.sub('', text)

    def normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace while preserving structure"""
        # Collapse multiple spaces to single space
        text = re.sub(r' +', ' ', text)
        # Limit consecutive newlines to 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    def validate_cleaned_text(
        self,
        cleaned_text: str,
        original_text: str
    ) -> List[str]:
        """
        Validate cleaned text and return warnings.

        Args:
            cleaned_text: Cleaned text
            original_text: Original text

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for significant content loss
        orig_len = len(re.sub(r'\s', '', original_text))
        clean_len = len(re.sub(r'\s', '', cleaned_text))

        if orig_len > 0:
            loss_pct = (1 - clean_len / orig_len) * 100
            if loss_pct > MAX_CONTENT_LOSS_PCT:
                warnings.append(
                    f"Significant content loss detected: {loss_pct:.1f}%"
                )

        return warnings
