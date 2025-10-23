"""
PDF text extraction module.

Provides multiple extraction strategies:
- PyMuPDFExtractor: Fast, simple extraction
- TextractExtractor: AWS Textract with OCR capabilities
- FormattingExtractor: Format-aware extraction with header detection
"""

from extraction.base import BaseExtractor
from extraction.pymupdf_extractor import PyMuPDFExtractor
from extraction.textract_extractor import TextractExtractor
from extraction.formatting_extractor import FormattingExtractor

__all__ = [
    'BaseExtractor',
    'PyMuPDFExtractor',
    'TextractExtractor',
    'FormattingExtractor',
]
