import logging
import time
from typing import Optional

from models import ExtractionResult, ExtractionConfidence, ExtractedField
from .mistral_client import MistralOCRClient

logger = logging.getLogger(__name__)


class DocumentExtractor:
    def __init__(self, mistral_client: MistralOCRClient):
        self.client = mistral_client
        self.confidence_threshold = 0.7

    async def extract(
        self,
        document_id: str,
        file_bytes: bytes,
        content_type: str,
        filename: Optional[str] = None
    ) -> ExtractionResult:
        start_time = time.time()

        try:
            response = await self.client.extract_from_bytes(
                file_bytes=file_bytes,
                content_type=content_type,
                filename=filename
            )

            parsed = self.client.parse_response(response)

            fields = self._extract_fields(parsed["markdown_content"])
            field_confidences = [f.confidence for f in fields] if fields else [parsed["confidence"]]

            confidence = ExtractionConfidence.calculate(
                field_confidences,
                threshold=self.confidence_threshold
            )

            processing_time = int((time.time() - start_time) * 1000)

            return ExtractionResult(
                document_id=document_id,
                raw_text=parsed["raw_text"],
                markdown_content=parsed["markdown_content"],
                fields=fields,
                tables=parsed["tables"],
                confidence=confidence,
                page_count=parsed["page_count"],
                processing_time_ms=processing_time,
                model_version=parsed["model"]
            )

        except Exception as e:
            logger.error(f"Extraction failed for document {document_id}: {str(e)}")
            raise

    def _extract_fields(self, markdown_content: str) -> list[ExtractedField]:
        fields = []
        lines = markdown_content.split("\n")

        for line in lines:
            if ":" in line and not line.startswith("#"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip().strip("*").strip("-").strip()
                    value = parts[1].strip().strip("*").strip()

                    if name and value and len(name) < 50:
                        fields.append(ExtractedField(
                            name=name,
                            value=value,
                            confidence=0.85
                        ))

        return fields
