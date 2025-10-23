"""
Unit tests for PDF extractors.

NOTE: This file has been superseded by more comprehensive tests:
- test_pymupdf_extraction.py - PyMuPDF extractor tests
- test_formatting_extraction.py - Formatting extractor tests
- test_line_wrapping.py - Line wrapping logic tests

These basic tests are kept for backwards compatibility.
"""

import pytest
from src.extraction import PyMuPDFExtractor, FormattingExtractor


def test_pymupdf_extractor_initialization():
    """Test PyMuPDF extractor initialization"""
    extractor = PyMuPDFExtractor(debug=True)
    assert extractor.debug is True


def test_formatting_extractor_initialization():
    """Test formatting extractor initialization"""
    extractor = FormattingExtractor(debug=False)
    assert extractor.debug is False
