"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path

# PDF path fixtures
@pytest.fixture
def subset_pdfs_dir():
    """Directory containing subset test PDFs"""
    return Path("tests/fixtures/subset_pdfs")

@pytest.fixture
def employee_handbook_pdf(subset_pdfs_dir):
    """Employee handbook PDF path"""
    return subset_pdfs_dir / "deepshield-systems-employee-handbook-2023.pdf"

@pytest.fixture
def budget_pdf(subset_pdfs_dir):
    """Budget allocation PDF path"""
    return subset_pdfs_dir / "engineering-department-budget-allocation.pdf"

@pytest.fixture
def meeting_minutes_pdf(subset_pdfs_dir):
    """Meeting minutes PDF path"""
    return subset_pdfs_dir / "board-meeting-minutes-series-c-closing.pdf"

@pytest.fixture
def contract_pdf(subset_pdfs_dir):
    """Security contract PDF path"""
    return subset_pdfs_dir / "security-implementation-contract.pdf"

@pytest.fixture
def all_subset_pdfs(subset_pdfs_dir):
    """List of all subset PDF paths"""
    return list(subset_pdfs_dir.glob("*.pdf"))

# Text fixtures
@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return "This is a sample text for testing purposes."

@pytest.fixture
def sample_text_with_page_markers():
    """Sample text with page markers for cleaning tests"""
    return """Some content here.
--- Page 1 ---
First page content.
--- Page 2 ---
Second page content.
--- PAGE 3 ---
Third page content."""

@pytest.fixture
def sample_text_with_whitespace():
    """Sample text with excessive whitespace"""
    return """Line one    has    multiple   spaces.


Too many newlines above.

Normal paragraph here."""
