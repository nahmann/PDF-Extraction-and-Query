"""
Unit tests for text cleaning.

NOTE: This file has been superseded by comprehensive tests in test_text_cleaning.py
These basic tests are kept for backwards compatibility.
"""

import pytest
from src.preprocessing import TextCleaner


def test_text_cleaner_initialization():
    """Test text cleaner initialization"""
    cleaner = TextCleaner(debug=True)
    assert cleaner.debug is True


def test_remove_page_markers():
    """Test page marker removal"""
    cleaner = TextCleaner()
    text = "Some text\n--- Page 1 ---\nMore text"
    cleaned = cleaner.remove_page_markers(text)
    assert "--- Page 1 ---" not in cleaned
