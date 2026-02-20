import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_mistral_response():
    return {
        "pages": [
            {
                "markdown": "# Invoice\n\n**Vendor:** Test Company\n**Amount:** $100.00",
                "confidence": 0.92,
                "tables": []
            }
        ],
        "model": "mistral-ocr-2503"
    }


@pytest.fixture
def sample_pdf_bytes():
    return b"%PDF-1.4 fake pdf content for testing"


@pytest.fixture
def sample_image_bytes():
    return b"\x89PNG\r\n\x1a\n fake png content"


@pytest.fixture
def mock_blob_properties():
    return {
        "content_type": "application/pdf",
        "size": 1024,
        "created_on": "2024-01-01T00:00:00Z",
        "last_modified": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_storage_helper():
    helper = AsyncMock()
    helper.account_url = "https://teststorage.blob.core.windows.net"
    helper.landing_zone_container = "landing-zone"
    helper.extracted_data_container = "extracted-data"
    helper.upload_result = AsyncMock(return_value="https://teststorage.blob.core.windows.net/extracted-data/test.md")
    helper.download_blob = AsyncMock(return_value=b"test content")
    helper.list_results = AsyncMock(return_value=[])
    helper.close = AsyncMock()
    return helper


@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    publisher.publish_document_processed = AsyncMock()
    publisher.publish_document_failed = AsyncMock()
    publisher.close = AsyncMock()
    return publisher
