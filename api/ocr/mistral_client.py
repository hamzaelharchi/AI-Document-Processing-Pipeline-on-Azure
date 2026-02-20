import base64
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class MistralOCRClient:
    """Client for Mistral Document AI via Azure AI Foundry."""

    def __init__(self, endpoint: str, api_key: str, model: str = "mistral-document-ai-2505"):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = 120.0

    async def extract_from_bytes(
        self,
        file_bytes: bytes,
        content_type: str,
        filename: Optional[str] = None
    ) -> dict:
        """Extract content from document bytes using Azure Mistral Document AI."""
        base64_content = base64.b64encode(file_bytes).decode("utf-8")

        # Determine document type and format
        if content_type == "application/pdf":
            doc_type = "document_url"
            data_uri = f"data:application/pdf;base64,{base64_content}"
        else:
            # Image types
            doc_type = "image_url"
            media_type = content_type if content_type in ["image/png", "image/jpeg", "image/jpg", "image/tiff"] else "image/png"
            data_uri = f"data:{media_type};base64,{base64_content}"

        # Azure AI Foundry Mistral Document AI format
        payload = {
            "model": self.model,
            "document": {
                "type": doc_type,
                doc_type: data_uri
            },
            "include_image_base64": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Azure AI Foundry Mistral OCR endpoint
        url = f"{self.endpoint}/providers/mistral/azure/ocr"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Calling Azure Mistral Document AI: {url}")
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Azure Mistral API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error calling Azure Mistral: {str(e)}")
                raise

    def parse_response(self, response: dict) -> dict:
        """Parse Mistral Document AI response into standardized format."""
        try:
            pages = response.get("pages", [])

            all_text = []
            all_tables = []
            page_confidences = []

            for page in pages:
                # Get markdown content from page
                page_markdown = page.get("markdown", "")
                all_text.append(page_markdown)

                # Extract tables if present
                if "tables" in page:
                    all_tables.extend(page["tables"])

                # Get confidence if available
                if "confidence" in page:
                    page_confidences.append(page["confidence"])

            # Combine all pages
            combined_text = "\n\n---\n\n".join(all_text) if len(all_text) > 1 else (all_text[0] if all_text else "")

            # Calculate average confidence
            avg_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.85

            return {
                "markdown_content": combined_text,
                "raw_text": combined_text,
                "tables": all_tables,
                "page_count": len(pages),
                "confidence": avg_confidence,
                "model": response.get("model", self.model)
            }
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return {
                "markdown_content": str(response),
                "raw_text": str(response),
                "tables": [],
                "page_count": 1,
                "confidence": 0.5,
                "model": self.model
            }
