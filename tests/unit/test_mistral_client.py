import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import sys
from pathlib import Path

# Add api/ directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from ocr.mistral_client import MistralOCRClient


class TestMistralOCRClient:
    @pytest.fixture
    def client(self):
        return MistralOCRClient(
            endpoint="https://test.inference.ai.azure.com",
            api_key="test-api-key"
        )

    def test_init(self, client):
        assert client.endpoint == "https://test.inference.ai.azure.com"
        assert client.api_key == "test-api-key"
        assert client.model == "mistral-document-ai-2505"

    def test_parse_response_single_page(self, client, mock_mistral_response):
        result = client.parse_response(mock_mistral_response)

        assert "markdown_content" in result
        assert "# Invoice" in result["markdown_content"]
        assert result["page_count"] == 1
        assert result["confidence"] == 0.92

    def test_parse_response_multiple_pages(self, client):
        response = {
            "pages": [
                {"markdown": "Page 1 content", "confidence": 0.9},
                {"markdown": "Page 2 content", "confidence": 0.85}
            ],
            "model": "mistral-ocr-2503"
        }

        result = client.parse_response(response)

        assert result["page_count"] == 2
        assert "Page 1 content" in result["markdown_content"]
        assert "Page 2 content" in result["markdown_content"]
        assert result["confidence"] == pytest.approx(0.875)

    def test_parse_response_empty(self, client):
        response = {"pages": [], "model": "mistral-ocr-2503"}
        result = client.parse_response(response)

        assert result["page_count"] == 0
        assert result["markdown_content"] == ""
        assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_extract_from_bytes_pdf(self, client, sample_pdf_bytes):
        mock_response = MagicMock()
        mock_response.json.return_value = {"pages": [{"markdown": "test"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            async with httpx.AsyncClient() as _:
                result = await client.extract_from_bytes(
                    file_bytes=sample_pdf_bytes,
                    content_type="application/pdf"
                )

            assert result == {"pages": [{"markdown": "test"}]}
