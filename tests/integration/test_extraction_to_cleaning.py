"""
Integration tests for extraction + cleaning pipeline.

Tests the flow from PDF extraction through text cleaning.
"""

import pytest
from src.extraction import PyMuPDFExtractor, FormattingExtractor
from src.preprocessing import TextCleaner


class TestExtractionToCleaningPipeline:
    """Test end-to-end extraction + cleaning"""

    def test_extract_and_clean_employee_handbook(self, employee_handbook_pdf):
        """Full pipeline on handbook PDF"""
        # Extract
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))

        assert extraction_result.success, f"Extraction failed: {extraction_result.errors}"
        assert extraction_result.extracted_text
        assert len(extraction_result.extracted_text) > 500

        # Clean
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(
            extraction_result.extracted_text,
            validate=True
        )

        # Verify cleaning worked
        assert cleaned_text
        assert len(cleaned_text) > 400  # Should still have substantial content

        # Page markers should be gone
        assert "--- Page" not in cleaned_text

        # Excessive whitespace should be normalized
        assert "    " not in cleaned_text  # No quad spaces
        assert "\n\n\n" not in cleaned_text  # No triple newlines

        # Should not have excessive content loss
        if warnings:
            assert not any("content loss" in w.lower() for w in warnings), \
                f"Unexpected content loss: {warnings}"

    def test_extract_and_clean_budget_pdf(self, budget_pdf):
        """Full pipeline on budget PDF"""
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(budget_pdf))

        assert extraction_result.success
        assert extraction_result.extracted_text

        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        # Verify content is preserved
        assert cleaned_text
        assert "--- Page" not in cleaned_text

        # Should have reasonable length
        assert len(cleaned_text) > 100

    def test_extract_and_clean_meeting_minutes(self, meeting_minutes_pdf):
        """Full pipeline on meeting minutes PDF"""
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(meeting_minutes_pdf))

        assert extraction_result.success

        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        assert cleaned_text
        assert "--- Page" not in cleaned_text

    def test_extract_and_clean_contract(self, contract_pdf):
        """Full pipeline on contract PDF"""
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(contract_pdf))

        assert extraction_result.success

        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        assert cleaned_text
        assert "--- Page" not in cleaned_text

    def test_formatting_extraction_plus_cleaning(self, employee_handbook_pdf):
        """FormattingExtractor → TextCleaner"""
        # Extract with formatting
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))

        assert extraction_result.success
        assert 'formatted_blocks' in extraction_result.metadata

        # Clean the formatted extraction
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(
            extraction_result.extracted_text,
            validate=True
        )

        # Markdown headers should be preserved (they're actual content)
        # But page markers should be removed
        assert "--- Page" not in cleaned_text

        # Headers might still have markdown formatting
        # (cleaning shouldn't remove those)
        assert cleaned_text

    def test_cleaned_text_ready_for_chunking(self, contract_pdf):
        """Verify output is clean and ready for next pipeline stage"""
        # Full extraction + cleaning
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(contract_pdf))
        assert extraction_result.success

        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        # Verify text is ready for chunking:
        # 1. No page markers
        assert "--- Page" not in cleaned_text

        # 2. No excessive whitespace
        assert "    " not in cleaned_text
        assert "\n\n\n" not in cleaned_text

        # 3. No trailing/leading whitespace on lines
        for line in cleaned_text.split('\n'):
            if line:  # Skip empty lines
                assert line == line.strip()

        # 4. Has actual content
        assert len(cleaned_text.strip()) > 100

        # 5. Content is string (not bytes or other type)
        assert isinstance(cleaned_text, str)


class TestPipelineWithAllPDFs:
    """Test pipeline on all subset PDFs"""

    def test_all_pdfs_extract_and_clean_successfully(self, all_subset_pdfs):
        """Run extraction + cleaning on all 4 PDFs"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()

        results = []

        for pdf_path in all_subset_pdfs:
            # Extract
            extraction_result = extractor.extract(str(pdf_path))
            assert extraction_result.success, \
                f"Extraction failed for {pdf_path.name}: {extraction_result.errors}"

            # Clean
            cleaned_text, warnings = cleaner.clean(
                extraction_result.extracted_text,
                validate=True
            )

            # Store results
            results.append({
                'pdf': pdf_path.name,
                'extracted_length': len(extraction_result.extracted_text),
                'cleaned_length': len(cleaned_text),
                'warnings': warnings
            })

            # Basic validation
            assert cleaned_text, f"Empty cleaned text for {pdf_path.name}"
            assert "--- Page" not in cleaned_text

        # Summary check: all PDFs processed successfully
        assert len(results) == len(all_subset_pdfs)

        # No PDF should have excessive content loss
        for result in results:
            if result['warnings']:
                assert not any("content loss" in w.lower() for w in result['warnings']), \
                    f"Content loss in {result['pdf']}: {result['warnings']}"

    def test_both_extractors_with_cleaning(self, meeting_minutes_pdf):
        """Test both PyMuPDF and Formatting extractors with cleaning"""
        cleaner = TextCleaner()

        # PyMuPDF extraction
        pymupdf_extractor = PyMuPDFExtractor()
        pymupdf_result = pymupdf_extractor.extract(str(meeting_minutes_pdf))
        assert pymupdf_result.success

        pymupdf_cleaned, _ = cleaner.clean(pymupdf_result.extracted_text)

        # Formatting extraction
        formatting_extractor = FormattingExtractor()
        formatting_result = formatting_extractor.extract(str(meeting_minutes_pdf))
        assert formatting_result.success

        formatting_cleaned, _ = cleaner.clean(formatting_result.extracted_text)

        # Both should produce cleaned text
        assert pymupdf_cleaned
        assert formatting_cleaned

        # Both should have page markers removed
        assert "--- Page" not in pymupdf_cleaned
        assert "--- Page" not in formatting_cleaned

        # Lengths should be comparable (not exact due to formatting differences)
        ratio = min(len(pymupdf_cleaned), len(formatting_cleaned)) / \
                max(len(pymupdf_cleaned), len(formatting_cleaned))
        assert ratio > 0.5, "Extractors produced vastly different cleaned lengths"


class TestPipelineMetadata:
    """Test metadata preservation through pipeline"""

    def test_metadata_preserved_after_cleaning(self, employee_handbook_pdf):
        """Ensure extraction metadata is available after cleaning"""
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))

        # Store metadata
        page_count = extraction_result.metadata['page_count']
        extraction_method = extraction_result.metadata['extraction_method']

        # Clean text
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        # Metadata should still be accessible from extraction_result
        assert extraction_result.metadata['page_count'] == page_count
        assert extraction_result.metadata['extraction_method'] == extraction_method

        # Cleaned text is ready for next stage
        assert cleaned_text

    def test_formatted_blocks_metadata_available(self, contract_pdf):
        """Ensure formatted_blocks metadata survives cleaning"""
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(contract_pdf))

        # Get formatted blocks
        formatted_blocks = extraction_result.metadata['formatted_blocks']
        assert formatted_blocks

        # Clean text
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        # Metadata should still be accessible
        assert extraction_result.metadata['formatted_blocks'] == formatted_blocks

        # We could use formatted_blocks for chunking later
        assert len(formatted_blocks) > 0


class TestPipelineErrorHandling:
    """Test error handling in the pipeline"""

    def test_extraction_failure_stops_pipeline(self):
        """If extraction fails, don't proceed to cleaning"""
        extractor = PyMuPDFExtractor()

        # Try to extract non-existent file
        extraction_result = extractor.extract("nonexistent.pdf")

        # Extraction should fail
        assert not extraction_result.success
        assert len(extraction_result.errors) > 0

        # Don't clean if extraction failed
        if not extraction_result.success:
            assert extraction_result.extracted_text == ""  # No text to clean

    def test_empty_extraction_handled_gracefully(self):
        """Handle case where extraction produces empty text"""
        cleaner = TextCleaner()

        # Clean empty text (edge case)
        cleaned_text, warnings = cleaner.clean("", validate=True)

        # Should handle gracefully
        assert cleaned_text == ""
        assert isinstance(warnings, list)

    def test_cleaning_with_formatted_blocks_metadata(self, budget_pdf):
        """Cleaning should work with formatted_blocks metadata passed"""
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(budget_pdf))

        assert extraction_result.success

        # Clean with formatted_blocks metadata
        cleaner = TextCleaner()
        formatted_blocks = extraction_result.metadata.get('formatted_blocks')

        cleaned_text, warnings = cleaner.clean(
            extraction_result.extracted_text,
            validate=True,
            formatted_blocks=formatted_blocks
        )

        # Should still work
        assert cleaned_text
        assert "--- Page" not in cleaned_text


class TestPipelinePerformance:
    """Basic performance tests"""

    def test_pipeline_completes_in_reasonable_time(self, employee_handbook_pdf):
        """Ensure extraction + cleaning doesn't take too long"""
        import time

        start_time = time.time()

        # Extract
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))
        assert extraction_result.success

        # Clean
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        end_time = time.time()
        elapsed = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        # For a small test PDF, this should be very fast
        assert elapsed < 10, f"Pipeline took too long: {elapsed:.2f}s"

        assert cleaned_text

    def test_all_pdfs_process_quickly(self, all_subset_pdfs):
        """Batch processing of all PDFs should be efficient"""
        import time

        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()

        start_time = time.time()

        for pdf_path in all_subset_pdfs:
            extraction_result = extractor.extract(str(pdf_path))
            assert extraction_result.success

            cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)
            assert cleaned_text

        end_time = time.time()
        elapsed = end_time - start_time

        # 4 PDFs should process quickly
        assert elapsed < 30, f"Batch processing took too long: {elapsed:.2f}s"
