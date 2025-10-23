"""
PDF text extraction using PyMuPDF (fitz).

Supports both simple and layout-aware extraction modes.
"""

from pathlib import Path
from typing import Dict, Tuple

import fitz  # PyMuPDF

from extraction.base import BaseExtractor
from utils.processing_result import ProcessingResult
from utils.exceptions import PyMuPDFError, FileNotFoundError
from utils.validators import validate_pdf_file


class PyMuPDFExtractor(BaseExtractor):
    """Extract text from PDFs using PyMuPDF library"""

    def __init__(self, use_layout: bool = False, debug: bool = False):
        """
        Initialize PyMuPDF extractor.

        Args:
            use_layout: Use layout-aware extraction for better paragraph detection
            debug: Enable debug logging
        """
        super().__init__(debug)
        self.use_layout = use_layout

    def supports_file(self, pdf_path: str) -> bool:
        """Check if file is a valid PDF"""
        try:
            validate_pdf_file(pdf_path)
            return True
        except Exception:
            return False

    def extract(self, pdf_path: str) -> ProcessingResult:
        """
        Extract text from PDF using PyMuPDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ProcessingResult with extracted text and metadata
        """
        result = self._create_result(pdf_path)

        try:
            # Validate file
            pdf_file = validate_pdf_file(pdf_path)
            self._add_file_metadata(result)

            # Open the PDF document
            doc = fitz.open(str(pdf_file))
            text_parts = []
            page_count = doc.page_count
            page_text_map = {}

            for page_num in range(page_count):
                page = doc[page_num]
                page_start_pos = len(''.join(text_parts))
                text_parts.append(f"\n--- Page {page_num + 1} ---\n")

                if self.use_layout:
                    # Block-based extraction for better paragraph preservation
                    text_parts.append(self._extract_with_blocks(page))
                else:
                    # Simple text extraction
                    page_text = page.get_text()
                    text_parts.append(page_text)
                    text_parts.append("\n")

                # Track page boundaries
                page_end_pos = len(''.join(text_parts))
                page_text_map[page_num + 1] = (page_start_pos, page_end_pos)

            # Store metadata
            result.metadata['page_count'] = page_count
            result.metadata['page_text_map'] = page_text_map
            result.metadata['extraction_method'] = (
                'pymupdf_layout' if self.use_layout else 'pymupdf_simple'
            )

            # Close document
            doc.close()

            # Build final text
            result.extracted_text = ''.join(text_parts)
            result.success = True

            if self.debug:
                self.logger.debug(
                    f"Extracted {len(result.extracted_text)} chars from "
                    f"{page_count} pages using PyMuPDF"
                )

        except FileNotFoundError as e:
            result.add_error(str(e))
        except Exception as e:
            result.add_error(f"Error processing PDF with PyMuPDF: {str(e)}")
            if self.debug:
                self.logger.exception("PyMuPDF extraction failed")

        return result

    def _extract_with_blocks(self, page) -> str:
        """
        Extract text using block-based method for better paragraph detection.

        Args:
            page: PyMuPDF page object

        Returns:
            Extracted text with preserved paragraph structure
        """
        text_parts = []
        blocks = page.get_text("blocks")

        for block in blocks:
            if block[6] == 0:  # Text block (not image)
                block_text = block[4]
                # Clean up block text
                lines = [line.strip() for line in block_text.split('\n') if line.strip()]
                cleaned_block = ' '.join(lines)
                if cleaned_block:
                    text_parts.append(cleaned_block + "\n\n")

        return ''.join(text_parts)
