import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add api/ directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from ocr.extractor import DocumentExtractor
from ocr.mistral_client import MistralOCRClient
from models import ExtractionResult


class TestDocumentExtractor:
    @pytest.fixture
    def mock_client(self, mock_mistral_response):
        client = MagicMock(spec=MistralOCRClient)
        client.extract_from_bytes = AsyncMock(return_value=mock_mistral_response)
        client.parse_response = MagicMock(return_value={
            "markdown_content": "# Invoice\n\n**Vendor:** Test Company\n**Amount:** $100.00",
            "raw_text": "# Invoice\n\n**Vendor:** Test Company\n**Amount:** $100.00",
            "tables": [],
            "page_count": 1,
            "confidence": 0.92,
            "model": "mistral-ocr-2503"
        })
        return client

    @pytest.fixture
    def extractor(self, mock_client):
        return DocumentExtractor(mock_client)

    @pytest.mark.asyncio
    async def test_extract_success(self, extractor, sample_pdf_bytes):
        result = await extractor.extract(
            document_id="test_doc",
            file_bytes=sample_pdf_bytes,
            content_type="application/pdf",
            filename="test.pdf"
        )

        assert isinstance(result, ExtractionResult)
        assert result.document_id == "test_doc"
        assert result.page_count == 1
        assert result.confidence.overall > 0

    @pytest.mark.asyncio
    async def test_extract_extracts_fields(self, extractor, sample_pdf_bytes):
        result = await extractor.extract(
            document_id="test_doc",
            file_bytes=sample_pdf_bytes,
            content_type="application/pdf"
        )

        assert len(result.fields) > 0
        field_names = [f.name for f in result.fields]
        assert "Vendor" in field_names or "Amount" in field_names

    def test_extract_fields_from_markdown(self, extractor):
        markdown = """# Invoice

**Vendor:** Acme Corp
**Date:** 2024-01-15
**Total:** $500.00
"""
        fields = extractor._extract_fields(markdown)

        assert len(fields) == 3
        assert any(f.name == "Vendor" and f.value == "Acme Corp" for f in fields)
        assert any(f.name == "Date" for f in fields)
        assert any(f.name == "Total" for f in fields)

    def test_extract_fields_ignores_headers(self, extractor):
        markdown = """# Header Title
## Another Header
**Field:** Value
"""
        fields = extractor._extract_fields(markdown)

        assert len(fields) == 1
        assert fields[0].name == "Field"
