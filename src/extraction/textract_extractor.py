"""
PDF text extraction using AWS Textract.

Supports synchronous processing for files up to 10MB.
"""

from pathlib import Path
from typing import Optional

from extraction.base import BaseExtractor
from utils.processing_result import ProcessingResult
from utils.exceptions import TextractError, TextractThrottleError, FileSizeError
from utils.validators import validate_pdf_file
from config.constants import TEXTRACT_SYNC_MAX_SIZE_MB
from config.settings import settings

# Optional AWS imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False
    ClientError = Exception
    NoCredentialsError = Exception


class TextractExtractor(BaseExtractor):
    """Extract text from PDFs using AWS Textract"""

    def __init__(self, aws_region: Optional[str] = None, debug: bool = False):
        """
        Initialize Textract extractor.

        Args:
            aws_region: AWS region (defaults to settings)
            debug: Enable debug logging
        """
        super().__init__(debug)
        self.aws_region = aws_region or settings.aws_region
        self._client = None

    @property
    def client(self):
        """Lazy-load Textract client"""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    def supports_file(self, pdf_path: str) -> bool:
        """
        Check if file can be processed with Textract.

        Textract sync API has a 10MB limit.
        """
        if not TEXTRACT_AVAILABLE:
            return False

        try:
            pdf_file = validate_pdf_file(pdf_path, max_size_mb=TEXTRACT_SYNC_MAX_SIZE_MB)
            return True
        except Exception:
            return False

    def extract(self, pdf_path: str) -> ProcessingResult:
        """
        Extract text from PDF using AWS Textract (synchronous).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ProcessingResult with extracted text and metadata
        """
        result = self._create_result(pdf_path)

        if not TEXTRACT_AVAILABLE:
            result.add_error("AWS Textract not available - boto3 not installed")
            return result

        try:
            # Validate file
            pdf_file = validate_pdf_file(pdf_path, max_size_mb=TEXTRACT_SYNC_MAX_SIZE_MB)
            self._add_file_metadata(result)

            file_size_mb = result.metadata.get('file_size_mb', 0)

            if self.debug:
                self.logger.debug(f"Textract extraction for: {pdf_path} ({file_size_mb} MB)")

            # Read the PDF file
            with open(pdf_file, 'rb') as document:
                document_bytes = document.read()

            if self.debug:
                self.logger.debug("Calling Textract API...")

            # Call Textract
            response = self.client.detect_document_text(
                Document={'Bytes': document_bytes}
            )

            if self.debug:
                self.logger.debug(f"Received {len(response.get('Blocks', []))} blocks")

            # Extract text from blocks
            extracted_lines = []
            confidences = []
            page_count = 0

            for block in response.get('Blocks', []):
                if block['BlockType'] == 'PAGE':
                    page_count += 1
                    extracted_lines.append(f"\n--- Page {page_count} ---\n")
                elif block['BlockType'] == 'LINE':
                    text = block.get('Text', '')
                    confidence = block.get('Confidence', 0)
                    extracted_lines.append(text)
                    confidences.append(confidence)

            result.extracted_text = '\n'.join(extracted_lines)
            result.metadata['page_count'] = page_count
            result.metadata['average_confidence'] = (
                sum(confidences) / len(confidences) if confidences else 0
            )
            result.metadata['extraction_method'] = 'textract'
            result.success = True

            if self.debug:
                self.logger.debug(
                    f"Extraction successful: {len(result.extracted_text)} characters, "
                    f"{page_count} pages, "
                    f"{result.metadata['average_confidence']:.1f}% avg confidence"
                )

        except FileSizeError as e:
            result.add_error(str(e))
            result.add_warning("Consider using PyMuPDF for larger files")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = f"AWS Textract error ({error_code}): {e.response['Error']['Message']}"

            if error_code == 'ThrottlingException':
                result.add_error("Textract API rate limit exceeded")
                raise TextractThrottleError(error_msg)
            else:
                result.add_error(error_msg)

            if self.debug:
                self.logger.error(error_msg)

        except NoCredentialsError:
            result.add_error("AWS credentials not found. Please configure AWS credentials.")

        except Exception as e:
            result.add_error(f"Error processing PDF with Textract: {str(e)}")
            if self.debug:
                self.logger.exception("Textract extraction failed")

        return result

    def _initialize_client(self):
        """Initialize AWS Textract client"""
        try:
            client = boto3.client('textract', region_name=self.aws_region)
            if self.debug:
                self.logger.debug(f"Initialized Textract client for region: {self.aws_region}")
            return client
        except NoCredentialsError:
            raise TextractError("AWS credentials not found. Please configure AWS credentials.")
        except Exception as e:
            raise TextractError(f"Failed to initialize Textract client: {str(e)}")
