"""
PDF text extraction with formatting-aware header detection.

Uses font properties (size, weight, flags) to identify document structure.
"""

from pathlib import Path
from typing import List, Dict, Any
import re

import fitz  # PyMuPDF

from extraction.base import BaseExtractor
from utils.processing_result import ProcessingResult
from utils.exceptions import PyMuPDFError
from utils.validators import validate_pdf_file
from config.constants import FONT_FLAG_BOLD


class FormattingExtractor(BaseExtractor):
    """
    Extract text from PDFs with formatting metadata for header detection.

    Uses font properties to identify headers and structure.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize formatting extractor.

        Args:
            debug: Enable debug logging
        """
        super().__init__(debug)

    def supports_file(self, pdf_path: str) -> bool:
        """Check if file is a valid PDF"""
        try:
            validate_pdf_file(pdf_path)
            return True
        except Exception:
            return False

    def extract(self, pdf_path: str) -> ProcessingResult:
        """
        Extract text from PDF with detailed formatting information.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ProcessingResult with formatted blocks in metadata
        """
        result = self._create_result(pdf_path)

        try:
            # Validate file
            pdf_file = validate_pdf_file(pdf_path)
            self._add_file_metadata(result)

            # Open the PDF document
            doc = fitz.open(str(pdf_file))
            page_count = doc.page_count

            # Extract text with formatting details
            formatted_blocks = []

            for page_num in range(page_count):
                page = doc[page_num]

                # Get text as dictionary with detailed formatting
                text_dict = page.get_text("dict")

                # Calculate font size statistics for header detection
                page_font_sizes = []
                for block in text_dict.get("blocks", []):
                    if block.get("type") == 0:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                page_font_sizes.append(span.get("size", 0))

                # Determine normal body font size (most common)
                normal_font_size = (
                    max(set(page_font_sizes), key=page_font_sizes.count)
                    if page_font_sizes else 11
                )

                # Extract formatted text blocks
                for block in text_dict.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        formatted_blocks.extend(
                            self._extract_formatted_lines(
                                block, page_num + 1, normal_font_size
                            )
                        )

            doc.close()

            # Reconstruct wrapped lines
            formatted_blocks = self._reconstruct_wrapped_lines(formatted_blocks)

            # Store formatted blocks in metadata
            result.metadata['formatted_blocks'] = formatted_blocks
            result.metadata['page_count'] = page_count
            result.metadata['extraction_method'] = 'pymupdf_formatted'

            # Build plain text with header markers
            text_parts = []
            for block in formatted_blocks:
                if block['is_likely_header']:
                    text_parts.append(f"\n## {block['text']}\n")
                else:
                    text_parts.append(block['text'] + "\n")

            result.extracted_text = ''.join(text_parts)
            result.success = True

            if self.debug:
                headers = [b for b in formatted_blocks if b['is_likely_header']]
                self.logger.debug(
                    f"Detected {len(headers)} headers across {page_count} pages"
                )

        except Exception as e:
            result.add_error(f"Error processing PDF with formatting extraction: {str(e)}")
            if self.debug:
                self.logger.exception("Formatting extraction failed")

        return result

    def _extract_formatted_lines(
        self,
        block: Dict[str, Any],
        page_num: int,
        normal_font_size: float
    ) -> List[Dict[str, Any]]:
        """
        Extract lines from a text block with formatting metadata.

        Args:
            block: Text block from PyMuPDF
            page_num: Page number
            normal_font_size: Normal body font size for this page

        Returns:
            List of formatted line dictionaries
        """
        lines = []

        for line in block.get("lines", []):
            line_text = ""
            font_sizes = []
            font_flags = []

            # Collect text and font properties
            for span in line.get("spans", []):
                text = span.get("text", "")
                line_text += text
                font_sizes.append(span.get("size", 0))
                font_flags.append(span.get("flags", 0))

            line_text = line_text.strip()
            if not line_text:
                continue

            # Calculate line properties
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
            is_bold = any(flag & FONT_FLAG_BOLD for flag in font_flags)
            is_all_caps = line_text.isupper() and len(line_text) > 3
            is_larger = avg_font_size > normal_font_size
            is_short = len(line_text) < 80

            # Header detection heuristic
            is_likely_header = (
                (is_bold and is_all_caps) or
                (is_bold and is_larger) or
                (is_bold and is_short and re.match(r'^[\d\w]', line_text))
            )

            lines.append({
                'text': line_text,
                'page': page_num,
                'font_size': avg_font_size,
                'is_bold': is_bold,
                'is_all_caps': is_all_caps,
                'is_larger': is_larger,
                'is_likely_header': is_likely_header
            })

        return lines

    def _reconstruct_wrapped_lines(
        self,
        formatted_blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Reconstruct lines that were broken by PDF line wrapping.

        Args:
            formatted_blocks: List of text blocks with formatting metadata

        Returns:
            List of blocks with wrapped lines merged
        """
        if not formatted_blocks:
            return formatted_blocks

        reconstructed = []
        buffer = None

        for block in formatted_blocks:
            if buffer is None:
                buffer = block.copy()
                continue

            # Check if current block should be merged with buffer
            if self._should_merge_lines(buffer, block):
                # Merge the lines
                buffer['text'] += ' ' + block['text']
            else:
                # Save buffer and start new one
                buffer = self._reevaluate_header_status(buffer)
                reconstructed.append(buffer)
                buffer = block.copy()

        # Don't forget the last buffer
        if buffer:
            buffer = self._reevaluate_header_status(buffer)
            reconstructed.append(buffer)

        return reconstructed

    def _should_merge_lines(
        self,
        prev: Dict[str, Any],
        curr: Dict[str, Any]
    ) -> bool:
        """
        Determine if current line should be merged with previous line.

        Merge if:
        - Same page
        - Same formatting (bold status, similar font size)
        - Previous doesn't end with sentence terminator
        - Current starts with continuation indicator
        """
        # Must be on same page
        if prev['page'] != curr['page']:
            return False

        # Must have same bold status
        if prev['is_bold'] != curr['is_bold']:
            return False

        # Font size should be similar (within 1pt)
        if abs(prev['font_size'] - curr['font_size']) > 1.0:
            return False

        prev_text = prev['text'].strip()
        curr_text = curr['text'].strip()

        # Don't merge if previous line is very short (likely a header)
        if len(prev_text) < 15:
            return False

        # Check if previous line ends with sentence terminator
        if prev_text.endswith(('.', ':', '!', '?', ';')):
            return False

        # Check if current line starts with continuation markers
        continuation_starts = (
            curr_text[0].islower() if curr_text else False,
            curr_text.startswith('and '),
            curr_text.startswith('or '),
            curr_text.startswith('the '),
            curr_text.startswith('to '),
            curr_text.startswith('of '),
            curr_text.startswith('in '),
            curr_text.startswith('for '),
            curr_text.startswith('with ')
        )

        return any(continuation_starts)

    def _reevaluate_header_status(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate if a block is a header after line reconstruction.

        Uses multi-signal scoring for better accuracy.
        """
        text = block['text'].strip()

        # MANDATORY: Must be bold OR all-caps
        is_bold = block.get('is_bold', False)
        is_all_caps = block.get('is_all_caps', False)

        if not (is_bold or is_all_caps):
            block['is_likely_header'] = False
            return block

        # Calculate additional signals
        score = 0

        # Signal 1: Larger font
        if block.get('is_larger', False):
            score += 1

        # Signal 2: Reasonable header length (15-80 chars)
        if 15 <= len(text) <= 80:
            score += 1

        # Signal 3: Ends with colon OR is short standalone phrase
        if text.endswith(':') or (len(text) < 40 and ',' not in text):
            score += 1

        # Signal 4: NOT a list item
        is_list_item = (
            text.count(',') >= 2 or
            re.match(r'^-\s+', text) or
            re.match(r'^\d+\)\s+', text) or
            re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+,\s+', text)
        )
        if not is_list_item:
            score += 1

        # Require 2+ additional signals beyond bold/caps
        block['is_likely_header'] = score >= 2

        return block
