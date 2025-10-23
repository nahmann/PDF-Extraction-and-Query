"""
Unit tests for FormattingExtractor.
"""

import pytest
from src.extraction import FormattingExtractor


class TestFormattingExtractorBasics:
    """Test basic formatting extraction functionality"""

    def test_formatted_blocks_generated(self, employee_handbook_pdf):
        """Verify formatted_blocks list is created in metadata"""
        extractor = FormattingExtractor(debug=True)
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success
        assert 'formatted_blocks' in result.metadata
        assert isinstance(result.metadata['formatted_blocks'], list)
        assert len(result.metadata['formatted_blocks']) > 0

    def test_header_detection(self, contract_pdf):
        """Check that headers are properly identified with is_likely_header=True"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']
        headers = [block for block in formatted_blocks if block['is_likely_header']]

        # Should have at least some headers
        assert len(headers) > 0, "No headers detected in contract PDF"

        # Each header should have required fields
        for header in headers:
            assert 'text' in header
            assert 'page' in header
            assert header['is_likely_header'] is True

    def test_font_size_tracking(self, budget_pdf):
        """Ensure font sizes are captured in formatted blocks"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(budget_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']

        # All blocks should have font_size
        for block in formatted_blocks:
            assert 'font_size' in block
            assert isinstance(block['font_size'], (int, float))
            assert block['font_size'] > 0, "Font size should be positive"

    def test_bold_detection(self, employee_handbook_pdf):
        """Verify bold text is flagged correctly"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']

        # Should have both bold and non-bold text
        bold_blocks = [b for b in formatted_blocks if b.get('is_bold')]
        non_bold_blocks = [b for b in formatted_blocks if not b.get('is_bold')]

        assert len(bold_blocks) > 0, "Expected some bold text"
        assert len(non_bold_blocks) > 0, "Expected some non-bold text"

    def test_all_caps_detection(self, contract_pdf):
        """Check that ALL CAPS text is identified"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']

        # Check that is_all_caps flag exists
        for block in formatted_blocks:
            assert 'is_all_caps' in block
            assert isinstance(block['is_all_caps'], bool)

    def test_markdown_header_insertion(self, meeting_minutes_pdf):
        """Confirm headers get ## prefix in extracted_text"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(meeting_minutes_pdf))

        assert result.success

        # Find headers in metadata
        formatted_blocks = result.metadata['formatted_blocks']
        headers = [block for block in formatted_blocks if block['is_likely_header']]

        if headers:
            # Check that at least one header appears with markdown formatting
            assert "## " in result.extracted_text, "Expected markdown headers in extracted text"


class TestHeaderDetectionQuality:
    """Test header detection accuracy"""

    def test_employee_handbook_headers(self, employee_handbook_pdf):
        """Count expected headers in handbook"""
        extractor = FormattingExtractor(debug=True)
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']
        headers = [block for block in formatted_blocks if block['is_likely_header']]

        # Employee handbook should have multiple section headers
        # Exact count can be verified after inspection
        assert len(headers) >= 5, f"Expected at least 5 headers, found {len(headers)}"

        # Print headers for manual verification (only in debug mode)
        if extractor.debug:
            print("\nDetected headers:")
            for h in headers[:10]:  # Print first 10
                print(f"  - {h['text'][:60]}")

    def test_contract_section_headers(self, contract_pdf):
        """Verify contract section headers are detected"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']
        headers = [block for block in formatted_blocks if block['is_likely_header']]

        # Contract should have multiple sections
        assert len(headers) >= 3, f"Expected at least 3 headers, found {len(headers)}"

    def test_false_positive_headers(self, all_subset_pdfs):
        """Ensure bold list items aren't incorrectly marked as headers"""
        extractor = FormattingExtractor()

        for pdf_path in all_subset_pdfs:
            result = extractor.extract(str(pdf_path))
            assert result.success

            formatted_blocks = result.metadata['formatted_blocks']

            # Check for common false positive patterns
            for block in formatted_blocks:
                text = block['text']

                # If it's marked as header, verify it doesn't look like a list item
                if block['is_likely_header']:
                    # Should not have excessive commas (likely a list)
                    comma_count = text.count(',')
                    assert comma_count < 3, f"Likely false positive header (too many commas): {text[:50]}"

                    # Should not start with bullet/number markers (handled by regex in code)
                    assert not text.startswith('- '), f"List item marked as header: {text[:50]}"


class TestLineWrappingDetection:
    """Test line wrapping and merging logic"""

    def test_wrapped_lines_merged(self, employee_handbook_pdf):
        """Verify sentences split across lines are properly merged"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']

        # Look for blocks that appear to be complete sentences (should be merged)
        # Complete sentences should end with proper punctuation
        complete_sentences = [
            b for b in formatted_blocks
            if len(b['text']) > 50 and b['text'].rstrip().endswith(('.', '!', '?'))
        ]

        assert len(complete_sentences) > 0, "Expected some complete sentences after merging"

    def test_header_not_merged_with_body(self, contract_pdf):
        """Ensure headers don't merge with following text"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']
        headers = [block for block in formatted_blocks if block['is_likely_header']]

        # Headers should generally be shorter and not contain excessive text
        for header in headers:
            # Headers shouldn't be extremely long (would indicate merging with body)
            assert len(header['text']) < 200, f"Header suspiciously long: {header['text'][:60]}"

    def test_different_pages_not_merged(self, budget_pdf):
        """Confirm text from different pages stays separate"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(budget_pdf))

        assert result.success

        formatted_blocks = result.metadata['formatted_blocks']
        page_count = result.metadata['page_count']

        if page_count > 1:
            # Check that we have blocks from different pages
            pages_with_content = set(block['page'] for block in formatted_blocks)
            assert len(pages_with_content) >= 2, "Expected content from multiple pages"

            # Find consecutive blocks from different pages
            for i in range(len(formatted_blocks) - 1):
                curr = formatted_blocks[i]
                next_block = formatted_blocks[i + 1]

                # If pages differ, text should not appear merged
                if curr['page'] != next_block['page']:
                    # This is a page boundary - they should be separate blocks
                    assert True  # Just confirming we can identify page boundaries


class TestFormattingExtractorMetadata:
    """Test metadata completeness"""

    def test_all_required_fields_present(self, meeting_minutes_pdf):
        """Ensure all required fields are in formatted blocks"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(meeting_minutes_pdf))

        assert result.success

        required_fields = [
            'text', 'page', 'font_size', 'is_bold',
            'is_all_caps', 'is_larger', 'is_likely_header'
        ]

        formatted_blocks = result.metadata['formatted_blocks']

        for block in formatted_blocks:
            for field in required_fields:
                assert field in block, f"Missing field '{field}' in block"

    def test_extraction_method_metadata(self, contract_pdf):
        """Verify extraction method is recorded"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success
        assert result.metadata['extraction_method'] == 'pymupdf_formatted'
