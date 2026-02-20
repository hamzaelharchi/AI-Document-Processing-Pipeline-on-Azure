from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ExtractionConfidence(BaseModel):
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    is_low_confidence: bool = Field(default=False, description="Flag for low confidence results")

    @classmethod
    def calculate(cls, field_confidences: list[float], threshold: float = 0.7) -> "ExtractionConfidence":
        if not field_confidences:
            return cls(overall=0.0, is_low_confidence=True)

        overall = sum(field_confidences) / len(field_confidences)
        return cls(
            overall=round(overall, 3),
            is_low_confidence=overall < threshold
        )


class ExtractedField(BaseModel):
    name: str = Field(..., description="Field name")
    value: Any = Field(..., description="Extracted value")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    page_number: Optional[int] = Field(default=None, description="Page where field was found")
    bounding_box: Optional[dict] = Field(default=None, description="Bounding box coordinates")

    def to_dict(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)


class ExtractionResult(BaseModel):
    document_id: str = Field(..., description="Reference to source document")
    raw_text: str = Field(default="", description="Raw extracted text")
    markdown_content: str = Field(default="", description="Formatted markdown content")
    fields: list[ExtractedField] = Field(default_factory=list, description="Extracted fields")
    tables: list[dict] = Field(default_factory=list, description="Extracted tables")
    confidence: ExtractionConfidence = Field(..., description="Confidence metrics")
    page_count: int = Field(default=1, description="Number of pages processed")
    processing_time_ms: int = Field(default=0, description="Processing time in milliseconds")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(default="mistral-ocr-2503", description="OCR model version")

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    def get_field_value(self, field_name: str) -> Any:
        for field in self.fields:
            if field.name.lower() == field_name.lower():
                return field.value
        return None
