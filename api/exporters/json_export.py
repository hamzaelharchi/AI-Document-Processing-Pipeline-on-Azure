import json
from models import ExtractionResult


class JsonExporter:
    def export(self, result: ExtractionResult, indent: int = 2) -> str:
        output = {
            "document_id": result.document_id,
            "extracted_at": result.extracted_at.isoformat(),
            "model_version": result.model_version,
            "page_count": result.page_count,
            "processing_time_ms": result.processing_time_ms,
            "confidence": {
                "overall": result.confidence.overall,
                "is_low_confidence": result.confidence.is_low_confidence
            },
            "fields": [
                {
                    "name": field.name,
                    "value": field.value,
                    "confidence": field.confidence
                }
                for field in result.fields
            ],
            "tables": result.tables,
            "content": {
                "raw_text": result.raw_text,
                "markdown": result.markdown_content
            }
        }

        return json.dumps(output, indent=indent, ensure_ascii=False)
