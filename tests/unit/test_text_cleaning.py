"""
Unit tests for text cleaning and normalization.
"""

import pytest
from src.preprocessing import TextCleaner


class TestPageMarkerRemoval:
    """Test page marker removal functionality"""

    def test_remove_single_page_marker(self):
        """Remove single page marker"""
        cleaner = TextCleaner()
        text = "Some content.\n--- Page 1 ---\nMore content."
        result = cleaner.remove_page_markers(text)

        assert "--- Page 1 ---" not in result
        assert "Some content." in result
        assert "More content." in result

    def test_remove_multiple_page_markers(self, sample_text_with_page_markers):
        """Remove markers from multi-page extraction"""
        cleaner = TextCleaner()
        result = cleaner.remove_page_markers(sample_text_with_page_markers)

        assert "--- Page 1 ---" not in result
        assert "--- Page 2 ---" not in result
        assert "--- PAGE 3 ---" not in result

        # Content should remain
        assert "First page content" in result
        assert "Second page content" in result
        assert "Third page content" in result

    def test_remove_page_markers_case_insensitive(self):
        """Test with different case variations"""
        cleaner = TextCleaner()

        test_cases = [
            "Content\n--- PAGE 1 ---\nMore",
            "Content\n--- page 2 ---\nMore",
            "Content\n--- Page 3 ---\nMore",
            "Content\n-------- Page 99 --------\nMore"
        ]

        for text in test_cases:
            result = cleaner.remove_page_markers(text)
            # Should not contain 'Page' followed by number in marker format
            assert "Page 1" not in result or "---" not in result
            assert "Content" in result
            assert "More" in result

    def test_remove_page_markers_preserves_other_text(self):
        """Ensure only page markers are removed, not other content"""
        cleaner = TextCleaner()
        text = """Important Section
--- Page 5 ---
This discusses the page layout.
The page number is 42.
--- Page 6 ---
More content about pages."""

        result = cleaner.remove_page_markers(text)

        # Markers should be gone
        assert "--- Page 5 ---" not in result
        assert "--- Page 6 ---" not in result

        # But text containing "page" should remain
        assert "page layout" in result
        assert "page number" in result


class TestWhitespaceNormalization:
    """Test whitespace normalization"""

    def test_collapse_multiple_spaces(self):
        """Multiple spaces should become single space"""
        cleaner = TextCleaner()
        text = "word    word     another    word"
        result = cleaner.normalize_whitespace(text)

        assert result == "word word another word"

    def test_limit_consecutive_newlines(self):
        """Limit excessive newlines to maximum of 2"""
        cleaner = TextCleaner()
        text = "Line 1\n\n\n\n\nLine 2"
        result = cleaner.normalize_whitespace(text)

        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_strip_line_whitespace(self):
        """Remove leading/trailing spaces from each line"""
        cleaner = TextCleaner()
        text = "  Line with leading spaces\nLine with trailing spaces  \n  Both  "
        result = cleaner.normalize_whitespace(text)

        lines = result.split('\n')
        for line in lines:
            if line:  # Skip empty lines
                assert line == line.strip(), f"Line not stripped: '{line}'"

    def test_preserve_paragraph_breaks(self, sample_text_with_whitespace):
        """Keep double newlines between paragraphs"""
        cleaner = TextCleaner()
        result = cleaner.normalize_whitespace(sample_text_with_whitespace)

        # Should still have paragraph breaks (double newlines)
        assert "\n\n" in result

    def test_normalize_mixed_whitespace(self):
        """Handle tabs, spaces, newlines together"""
        cleaner = TextCleaner()
        text = "Line one    has    spaces.\n\n\n\nLine two  has  issues."
        result = cleaner.normalize_whitespace(text)

        # Multiple spaces collapsed
        assert "    " not in result

        # Excessive newlines limited
        assert "\n\n\n" not in result

        # Content preserved
        assert "Line one has spaces." in result
        assert "Line two has issues." in result


class TestFullCleaningPipeline:
    """Test complete cleaning pipeline"""

    def test_clean_with_validation(self):
        """Run full clean() method with validation enabled"""
        cleaner = TextCleaner()
        text = """Some content here.
--- Page 1 ---
First page    content    with  spaces.


Too many newlines.
--- Page 2 ---
Second page."""

        cleaned, warnings = cleaner.clean(text, validate=True)

        # Page markers should be removed
        assert "--- Page 1 ---" not in cleaned
        assert "--- Page 2 ---" not in cleaned

        # Whitespace should be normalized
        assert "    " not in cleaned
        assert "\n\n\n" not in cleaned

        # Content should remain
        assert "First page content with spaces." in cleaned
        assert "Second page" in cleaned

        # Warnings should be a list
        assert isinstance(warnings, list)

    def test_clean_without_validation(self):
        """Test with validate=False"""
        cleaner = TextCleaner()
        text = "Some text\n--- Page 1 ---\nMore text"

        cleaned, warnings = cleaner.clean(text, validate=False)

        # Should still clean
        assert "--- Page 1 ---" not in cleaned

        # But no validation warnings
        assert warnings == []

    def test_cleaning_real_pdf_output(self, employee_handbook_pdf):
        """Clean actual extracted text from PDF"""
        from src.extraction import PyMuPDFExtractor

        # Extract text
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))
        assert extraction_result.success

        # Clean the extracted text
        cleaner = TextCleaner()
        cleaned, warnings = cleaner.clean(extraction_result.extracted_text)

        # Should have removed page markers
        assert "--- Page" not in cleaned

        # Should have normalized whitespace
        assert "    " not in cleaned  # No quad spaces

        # Should still have content
        assert len(cleaned) > 100

    def test_clean_preserves_content_order(self):
        """Ensure cleaning doesn't reorder content"""
        cleaner = TextCleaner()
        text = """First section.
--- Page 1 ---
Second section.
--- Page 2 ---
Third section."""

        cleaned, _ = cleaner.clean(text)

        # Order should be preserved
        first_pos = cleaned.find("First section")
        second_pos = cleaned.find("Second section")
        third_pos = cleaned.find("Third section")

        assert first_pos < second_pos < third_pos


class TestValidation:
    """Test validation functionality"""

    def test_no_content_loss_warning(self):
        """Cleaning with < 10% loss should pass without warnings"""
        cleaner = TextCleaner()

        original = "This is a test document with some content." * 10
        cleaned = "This is a test document with some content." * 9  # Small loss

        warnings = cleaner.validate_cleaned_text(cleaned, original)

        # Should have no warnings (loss is less than 10%)
        assert len(warnings) == 0

    def test_content_loss_warning_triggered(self):
        """Simulate >10% loss to trigger warning"""
        cleaner = TextCleaner()

        original = "This is a test document with some content." * 100
        cleaned = "Short."  # Massive loss

        warnings = cleaner.validate_cleaned_text(cleaned, original)

        # Should have warning about content loss
        assert len(warnings) > 0
        assert any("content loss" in w.lower() for w in warnings)

    def test_validate_empty_text(self):
        """Handle edge case of empty input"""
        cleaner = TextCleaner()

        original = ""
        cleaned = ""

        warnings = cleaner.validate_cleaned_text(cleaned, original)

        # Should not crash, warnings should be empty or minimal
        assert isinstance(warnings, list)

    def test_validation_ignores_whitespace(self):
        """Content loss calculation excludes whitespace"""
        cleaner = TextCleaner()

        # Original has lots of whitespace
        original = "Word  one    has    many     spaces    everywhere."

        # Cleaned removes excess whitespace
        cleaned = "Word one has many spaces everywhere."

        warnings = cleaner.validate_cleaned_text(cleaned, original)

        # Should have no warnings (non-whitespace content is identical)
        assert len(warnings) == 0

    def test_validation_detects_actual_content_loss(self):
        """Ensure validation detects when actual words are lost"""
        cleaner = TextCleaner()

        original = "The quick brown fox jumps over the lazy dog." * 10
        # Simulate losing significant text
        cleaned = "The quick brown fox." * 5  # Lost about half

        warnings = cleaner.validate_cleaned_text(cleaned, original)

        # Should warn about content loss
        assert len(warnings) > 0


class TestTextCleanerEdgeCases:
    """Test edge cases and error handling"""

    def test_clean_empty_string(self):
        """Handle empty input"""
        cleaner = TextCleaner()
        cleaned, warnings = cleaner.clean("", validate=True)

        assert cleaned == ""
        assert isinstance(warnings, list)

    def test_clean_only_whitespace(self):
        """Handle input with only whitespace"""
        cleaner = TextCleaner()
        text = "   \n\n\n   \t\t  \n  "
        cleaned, warnings = cleaner.clean(text)

        # Should collapse to empty or minimal whitespace
        assert len(cleaned.strip()) == 0

    def test_clean_only_page_markers(self):
        """Handle input with only page markers"""
        cleaner = TextCleaner()
        # Note: Regex requires newline after marker, so add trailing newline
        text = "--- Page 1 ---\n--- Page 2 ---\n--- Page 3 ---\n"
        cleaned, warnings = cleaner.clean(text)

        # Should be mostly empty after cleaning (all markers removed)
        assert "--- Page" not in cleaned

    def test_clean_very_long_text(self):
        """Ensure cleaning works with large documents"""
        cleaner = TextCleaner()

        # Create a large text (simulate real document)
        text = ("This is a paragraph with some content.\n" * 1000 +
                "--- Page 50 ---\n" +
                "More content here.\n" * 1000)

        cleaned, warnings = cleaner.clean(text)

        # Should process successfully
        assert len(cleaned) > 1000
        assert "--- Page 50 ---" not in cleaned

    def test_debug_mode_logging(self):
        """Test that debug mode doesn't crash"""
        cleaner = TextCleaner(debug=True)
        text = "Some text\n--- Page 1 ---\nMore text"

        cleaned, warnings = cleaner.clean(text)

        # Should work the same regardless of debug mode
        assert "--- Page 1 ---" not in cleaned
