"""
Unit tests for PyMuPDF extractor.
"""

import pytest
from src.extraction import PyMuPDFExtractor


class TestPyMuPDFBasicExtraction:
    """Test basic PyMuPDF extraction functionality"""

    def test_pymupdf_extracts_text_from_all_pdfs(self, all_subset_pdfs):
        """Verify all 4 PDFs extract successfully"""
        extractor = PyMuPDFExtractor(debug=True)

        for pdf_path in all_subset_pdfs:
            result = extractor.extract(str(pdf_path))
            assert result.success, f"Failed to extract {pdf_path.name}: {result.errors}"

    def test_extraction_returns_non_empty_text(self, all_subset_pdfs):
        """Ensure extracted text is not empty for each PDF"""
        extractor = PyMuPDFExtractor()

        for pdf_path in all_subset_pdfs:
            result = extractor.extract(str(pdf_path))
            assert result.extracted_text, f"No text extracted from {pdf_path.name}"
            assert len(result.extracted_text) > 100, f"Suspiciously short text from {pdf_path.name}"

    def test_page_count_metadata(self, employee_handbook_pdf):
        """Verify page_count in metadata matches expected values"""
        extractor = PyMuPDFExtractor()
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success
        assert 'page_count' in result.metadata
        assert result.metadata['page_count'] > 0
        assert isinstance(result.metadata['page_count'], int)

    def test_page_text_map_generated(self, budget_pdf):
        """Ensure page_text_map exists and has correct number of pages"""
        extractor = PyMuPDFExtractor()
        result = extractor.extract(str(budget_pdf))

        assert result.success
        assert 'page_text_map' in result.metadata

        page_text_map = result.metadata['page_text_map']
        page_count = result.metadata['page_count']

        # Page text map should have entry for each page
        assert len(page_text_map) == page_count

        # Each entry should have start and end positions
        for page_num, (start, end) in page_text_map.items():
            assert isinstance(start, int)
            assert isinstance(end, int)
            assert end > start, f"Page {page_num} has invalid text positions"

    def test_extraction_method_in_metadata(self, contract_pdf):
        """Confirm metadata contains correct extraction_method"""
        # Test simple extraction
        extractor_simple = PyMuPDFExtractor(use_layout=False)
        result_simple = extractor_simple.extract(str(contract_pdf))
        assert result_simple.metadata['extraction_method'] == 'pymupdf_simple'

        # Test layout extraction
        extractor_layout = PyMuPDFExtractor(use_layout=True)
        result_layout = extractor_layout.extract(str(contract_pdf))
        assert result_layout.metadata['extraction_method'] == 'pymupdf_layout'

    def test_simple_vs_layout_extraction(self, meeting_minutes_pdf):
        """Compare output between use_layout=False and use_layout=True"""
        extractor_simple = PyMuPDFExtractor(use_layout=False)
        extractor_layout = PyMuPDFExtractor(use_layout=True)

        result_simple = extractor_simple.extract(str(meeting_minutes_pdf))
        result_layout = extractor_layout.extract(str(meeting_minutes_pdf))

        assert result_simple.success
        assert result_layout.success

        # Both should extract text
        assert result_simple.extracted_text
        assert result_layout.extracted_text

        # Layout extraction typically produces different formatting
        # but should have similar length (within reasonable range)
        len_simple = len(result_simple.extracted_text)
        len_layout = len(result_layout.extracted_text)
        ratio = min(len_simple, len_layout) / max(len_simple, len_layout)
        assert ratio > 0.5, "Layout vs simple extraction produced vastly different lengths"


class TestPyMuPDFErrorHandling:
    """Test error handling in PyMuPDF extractor"""

    def test_invalid_file_path(self):
        """Test extraction with non-existent file"""
        extractor = PyMuPDFExtractor()
        result = extractor.extract("nonexistent_file.pdf")

        assert not result.success
        assert len(result.errors) > 0

    def test_non_pdf_file(self, sample_text):
        """Test extraction with non-PDF file"""
        # Create a temporary text file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text)
            txt_path = f.name

        extractor = PyMuPDFExtractor()
        result = extractor.extract(txt_path)

        assert not result.success

        # Clean up
        import os
        os.unlink(txt_path)


class TestPyMuPDFMetadata:
    """Test metadata extraction"""

    def test_file_metadata_included(self, employee_handbook_pdf):
        """Verify file metadata is added to results"""
        extractor = PyMuPDFExtractor()
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success
        # File path should be stored (in document_path attribute)
        assert result.document_path is not None
        assert 'employee-handbook' in result.document_path.lower()

    def test_page_markers_in_text(self, contract_pdf):
        """Verify page markers are added to extracted text"""
        extractor = PyMuPDFExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success
        # Should contain page markers like "--- Page 1 ---"
        assert "--- Page 1 ---" in result.extracted_text

        # Count page markers should match page count (or be close)
        import re
        markers = re.findall(r'--- Page \d+ ---', result.extracted_text)
        assert len(markers) == result.metadata['page_count']
