# PDF Processing Pipeline - Test Suite

This directory contains comprehensive tests for the PDF processing pipeline using the subset PDFs in `tests/fixtures/subset_pdfs/`.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures (PDF paths, sample text)
├── unit/                                # Unit tests
│   ├── test_pymupdf_extraction.py      # PyMuPDF extractor tests
│   ├── test_formatting_extraction.py    # Formatting extractor tests
│   ├── test_line_wrapping.py           # Line wrapping/merging logic
│   ├── test_text_cleaning.py           # Text cleaning tests
│   ├── test_chunking.py                # Chunking tests (TDD - will fail until implemented)
│   ├── test_extractors.py              # Legacy basic tests
│   └── test_cleaners.py                # Legacy basic tests
└── integration/                         # Integration tests
    ├── test_extraction_to_cleaning.py   # Extraction → Cleaning pipeline
    ├── test_full_pipeline.py            # Complete pipeline (includes TDD tests)
    └── test_pipeline.py                 # Legacy integration tests
```

## Test PDFs

Located in `tests/fixtures/subset_pdfs/`:
1. **deepshield-systems-employee-handbook-2023.pdf** - Multi-page handbook with sections
2. **engineering-department-budget-allocation.pdf** - Budget document
3. **board-meeting-minutes-series-c-closing.pdf** - Meeting minutes
4. **security-implementation-contract.pdf** - Legal contract

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run only unit tests:
```bash
pytest tests/unit/
```

### Run only integration tests:
```bash
pytest tests/integration/
```

### Run specific test file:
```bash
pytest tests/unit/test_pymupdf_extraction.py
```

### Run with verbose output:
```bash
pytest -v tests/
```

### Skip TDD tests (chunking not yet implemented):
```bash
pytest -v -m "not skip"
```

### Run only tests that currently pass:
```bash
pytest tests/unit/test_pymupdf_extraction.py tests/unit/test_formatting_extraction.py tests/unit/test_text_cleaning.py tests/integration/test_extraction_to_cleaning.py
```

## Test Categories

### ✅ **Extraction Tests** (Ready to Run)

#### `test_pymupdf_extraction.py`
- **Basic extraction**: Extract text from all PDFs successfully
- **Non-empty text**: Ensure meaningful content is extracted
- **Metadata**: Page count, page text map, extraction method
- **Simple vs Layout**: Compare extraction modes
- **Error handling**: Invalid files, non-PDFs
- **Page markers**: Verify page markers are inserted

#### `test_formatting_extraction.py`
- **Formatted blocks**: Verify formatted_blocks metadata is generated
- **Header detection**: Identify headers with bold/caps/size heuristics
- **Font properties**: Track font size, bold, caps
- **Markdown headers**: Headers get `## ` prefix
- **Header quality**: Expected header counts per PDF
- **False positives**: List items shouldn't be marked as headers
- **Line wrapping**: Wrapped lines merged, headers stay separate

#### `test_line_wrapping.py`
- **Merge logic**: Same formatting, incomplete sentences should merge
- **Don't merge**: Different pages, formatting, font sizes
- **Sentence terminators**: Don't merge after periods
- **Short headers**: Don't merge short lines with body
- **Continuations**: Merge with lowercase or conjunction starts
- **Header re-evaluation**: Multi-signal header scoring

### ✅ **Text Cleaning Tests** (Ready to Run)

#### `test_text_cleaning.py`
- **Page marker removal**: Single/multiple markers, case insensitive
- **Whitespace normalization**: Collapse spaces, limit newlines, strip lines
- **Full pipeline**: Complete clean() with validation
- **Validation**: Content loss detection, whitespace handling
- **Real PDFs**: Clean actual extracted text
- **Edge cases**: Empty text, whitespace-only, very long text

### ⚠️ **Chunking Tests** (TDD - Will Fail Until Implementation)

#### `test_chunking.py`
All tests marked with `@pytest.mark.skip(reason="Chunking not yet implemented - TDD test")`

- **Basic chunking**: Max size, overlap, return format
- **Section-aware**: Respect headers, hierarchical metadata
- **LangChain integration**: Create Document objects
- **Real PDFs**: Chunk handbook, contract
- **Oversized sections**: Handle sections larger than max size
- **Edge cases**: Long words, unicode, empty content

### ✅ **Integration Tests - Extraction + Cleaning** (Ready to Run)

#### `test_extraction_to_cleaning.py`
- **Full pipeline**: Extract → Clean for all PDFs
- **Both extractors**: PyMuPDF and Formatting
- **Metadata preservation**: Ensure metadata survives cleaning
- **Output validation**: Text ready for chunking
- **Performance**: Pipeline completes in reasonable time

### ⚠️ **Integration Tests - Full Pipeline** (Partial - TDD)

#### `test_full_pipeline.py`
- ✅ **Without chunking**: Extraction → Cleaning (ready to run)
- ⚠️ **With chunking**: Complete pipeline (TDD, will fail)
- ⚠️ **Batch processing**: All PDFs through pipeline (TDD)
- ⚠️ **Validation**: Content preservation end-to-end (TDD)

## Fixtures

Defined in `conftest.py`:

### PDF Fixtures
- `subset_pdfs_dir` - Path to subset PDFs directory
- `employee_handbook_pdf` - Employee handbook path
- `budget_pdf` - Budget document path
- `meeting_minutes_pdf` - Meeting minutes path
- `contract_pdf` - Contract path
- `all_subset_pdfs` - List of all PDF paths

### Text Fixtures
- `sample_text` - Simple sample text
- `sample_text_with_page_markers` - Text with page markers for testing removal
- `sample_text_with_whitespace` - Text with excessive whitespace

## Test Coverage Goals

| Component | Target Coverage | Status |
|-----------|----------------|--------|
| PyMuPDF Extractor | 90%+ | ✅ Tests ready |
| Formatting Extractor | 90%+ | ✅ Tests ready |
| Text Cleaner | 95%+ | ✅ Tests ready |
| LangChain Chunker | 85%+ | ⚠️ TDD tests written |

## Development Workflow

### Current State (Post-Refactoring)
1. ✅ Extraction tests ready - **Run these first**
2. ✅ Cleaning tests ready - **Run these second**
3. ⚠️ Chunking tests written but skipped - **Implement chunking to make them pass**

### Testing Strategy
1. **Start with what works**: Run extraction and cleaning tests to verify current functionality
2. **Verify integration**: Run extraction-to-cleaning integration tests
3. **TDD for chunking**: Use skipped chunking tests as specification
4. **Unskip as you implement**: Remove `@pytest.mark.skip` decorators as chunking features are completed

### Example Test Run

```bash
# Run tests that should currently pass
pytest tests/unit/test_pymupdf_extraction.py -v
pytest tests/unit/test_formatting_extraction.py -v
pytest tests/unit/test_line_wrapping.py -v
pytest tests/unit/test_text_cleaning.py -v
pytest tests/integration/test_extraction_to_cleaning.py::TestExtractionToCleaningPipeline -v

# See what's waiting for chunking implementation
pytest tests/unit/test_chunking.py -v
# (All will show as SKIPPED)
```

## Notes on Header Detection Tests

Some tests check for expected header counts (e.g., `test_employee_handbook_headers`). If exact counts are unknown:
- Tests use minimum thresholds (e.g., "at least 5 headers")
- Run with debug mode to see detected headers
- Update test assertions with actual counts after verification

Example:
```python
# After running test in debug mode and seeing 12 headers detected:
assert len(headers) >= 12, f"Expected 12+ headers, found {len(headers)}"
```

## Troubleshooting

### Import Errors
If you get import errors, ensure project root is in Python path:
```bash
# From project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### PDF Not Found Errors
Verify PDFs exist in `tests/fixtures/subset_pdfs/`:
```bash
ls tests/fixtures/subset_pdfs/*.pdf
```

### Windows-Specific Issues
The project includes Windows encoding fixes in `verify_installation.py`. If you encounter encoding issues:
```python
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## What is "Fixture Setup"?

**Fixtures** are reusable test components that provide data or setup/teardown. Benefits:
- **DRY**: Define paths/data once, use everywhere
- **Automatic**: pytest automatically passes fixtures to tests
- **Scoping**: Can be per-test, per-module, or per-session
- **Cleanup**: Can handle teardown automatically

Example:
```python
# In conftest.py
@pytest.fixture
def employee_handbook_pdf(subset_pdfs_dir):
    return subset_pdfs_dir / "deepshield-systems-employee-handbook-2023.pdf"

# In test file
def test_something(employee_handbook_pdf):
    # employee_handbook_pdf is automatically provided
    extractor.extract(str(employee_handbook_pdf))
```

## Next Steps

1. **Run current tests** to verify extraction and cleaning work correctly
2. **Implement chunking logic** in `src/chunking/langchain_chunker.py`
3. **Unskip chunking tests** one by one as features are implemented
4. **Run full test suite** to ensure complete pipeline works
5. **Add new tests** as edge cases are discovered

## Contributing Tests

When adding new tests:
1. Follow existing naming conventions (`test_*.py`)
2. Use descriptive test names (`test_what_it_does`)
3. Add docstrings explaining what's being tested
4. Use appropriate fixtures from `conftest.py`
5. Mark TDD tests with `@pytest.mark.skip` until implementation ready
6. Update this README with new test descriptions
