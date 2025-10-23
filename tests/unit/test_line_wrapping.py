"""
Unit tests for line wrapping and reconstruction logic in FormattingExtractor.
"""

import pytest
from src.extraction import FormattingExtractor


class TestLineWrappingLogic:
    """Test line wrapping detection and merging"""

    def test_should_merge_same_formatting(self):
        """Lines with same formatting and incomplete sentence should merge"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'This is a long sentence that was broken across',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'multiple lines in the PDF document',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        # Should merge because: same page, same formatting, prev doesn't end with period
        should_merge = extractor._should_merge_lines(prev, curr)
        assert should_merge, "Expected lines to merge"

    def test_should_not_merge_different_pages(self):
        """Lines from different pages should not merge"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'Text at end of page one that continues',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'onto page two',
            'page': 2,
            'font_size': 12.0,
            'is_bold': False
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert not should_merge, "Should not merge across pages"

    def test_should_not_merge_different_bold_status(self):
        """Lines with different bold status should not merge"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'This is normal text that ends without',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'BOLD HEADER TEXT',
            'page': 1,
            'font_size': 12.0,
            'is_bold': True
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert not should_merge, "Should not merge different bold status"

    def test_should_not_merge_different_font_sizes(self):
        """Lines with significantly different font sizes should not merge"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'This is body text in normal size',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'Large header text',
            'page': 1,
            'font_size': 16.0,
            'is_bold': False
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert not should_merge, "Should not merge different font sizes"

    def test_should_not_merge_after_sentence_terminator(self):
        """Lines should not merge if previous ends with sentence terminator"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'This is a complete sentence.',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'This is the next sentence',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert not should_merge, "Should not merge after period"

    def test_should_not_merge_short_headers(self):
        """Short lines (likely headers) should not merge with following text"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'Introduction',
            'page': 1,
            'font_size': 14.0,
            'is_bold': True
        }

        curr = {
            'text': 'The following section describes the process',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert not should_merge, "Should not merge short header with body"

    def test_merge_with_lowercase_continuation(self):
        """Should merge when next line starts with lowercase (continuation)"""
        extractor = FormattingExtractor()

        prev = {
            'text': 'The employee shall maintain all confidential information and',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        curr = {
            'text': 'shall not disclose such information to third parties',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        should_merge = extractor._should_merge_lines(prev, curr)
        assert should_merge, "Should merge with lowercase continuation"

    def test_merge_with_conjunction_continuation(self):
        """Should merge when next line starts with continuation words"""
        extractor = FormattingExtractor()

        test_cases = [
            'and further requirements',
            'or alternatively',
            'with additional provisions',
            'for the purpose of',
            'of the agreement'
        ]

        prev = {
            'text': 'This agreement shall be binding upon the parties',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False
        }

        for continuation_text in test_cases:
            curr = {
                'text': continuation_text,
                'page': 1,
                'font_size': 12.0,
                'is_bold': False
            }

            should_merge = extractor._should_merge_lines(prev, curr)
            assert should_merge, f"Should merge with continuation: '{continuation_text}'"


class TestHeaderReeval:
    """Test header re-evaluation after line reconstruction"""

    def test_reevaluate_header_requires_bold_or_caps(self):
        """Headers must be bold OR all-caps"""
        extractor = FormattingExtractor()

        # Not bold, not all caps - should not be header
        block = {
            'text': 'This is just normal text',
            'page': 1,
            'font_size': 12.0,
            'is_bold': False,
            'is_all_caps': False,
            'is_larger': False
        }

        result = extractor._reevaluate_header_status(block)
        assert result['is_likely_header'] is False

    def test_reevaluate_bold_with_multiple_signals(self):
        """Bold text with 2+ additional signals should be header"""
        extractor = FormattingExtractor()

        # Bold, larger, short, ends with colon = should be header
        block = {
            'text': 'Introduction:',
            'page': 1,
            'font_size': 14.0,
            'is_bold': True,
            'is_all_caps': False,
            'is_larger': True
        }

        result = extractor._reevaluate_header_status(block)
        assert result['is_likely_header'] is True

    def test_reevaluate_rejects_list_items(self):
        """List items with commas should not be headers"""
        extractor = FormattingExtractor()

        # Bold but looks like a list item
        block = {
            'text': 'John Smith, Jane Doe, Bob Johnson',
            'page': 1,
            'font_size': 12.0,
            'is_bold': True,
            'is_all_caps': False,
            'is_larger': False
        }

        result = extractor._reevaluate_header_status(block)
        assert result['is_likely_header'] is False

    def test_reevaluate_accepts_short_bold_phrase(self):
        """Short bold phrase without commas should be header"""
        extractor = FormattingExtractor()

        block = {
            'text': 'Benefits and Compensation',
            'page': 1,
            'font_size': 13.0,
            'is_bold': True,
            'is_all_caps': False,
            'is_larger': True
        }

        result = extractor._reevaluate_header_status(block)
        assert result['is_likely_header'] is True


class TestReconstructionIntegration:
    """Test full reconstruction with real PDFs"""

    def test_reconstruction_reduces_fragment_count(self, employee_handbook_pdf):
        """Line reconstruction should produce fewer, longer blocks"""
        extractor = FormattingExtractor()

        # We can't easily test this without modifying internals,
        # but we can verify that reconstructed text has reasonable sentence lengths
        result = extractor.extract(str(employee_handbook_pdf))

        assert result.success
        formatted_blocks = result.metadata['formatted_blocks']

        # Count blocks with reasonable sentence length (> 40 chars)
        reasonable_length_blocks = [b for b in formatted_blocks if len(b['text']) > 40]

        # Should have a good number of properly reconstructed sentences
        assert len(reasonable_length_blocks) > 10, "Expected more reconstructed sentences"

    def test_reconstruction_preserves_headers(self, contract_pdf):
        """Headers should remain separate after reconstruction"""
        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))

        assert result.success
        formatted_blocks = result.metadata['formatted_blocks']
        headers = [b for b in formatted_blocks if b['is_likely_header']]

        # Headers should generally be moderate length (not merged with body)
        for header in headers:
            assert len(header['text']) < 150, f"Header too long (likely merged): {header['text'][:60]}"
