from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    blob_url: str = Field(..., description="URL to the original blob")
    size_bytes: int = Field(default=0, description="File size in bytes")
    content_type: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_blob_properties(cls, blob_name: str, blob_url: str, properties: dict) -> "Document":
        filename = blob_name.split("/")[-1]
        content_type = properties.get("content_type", "")
        size = properties.get("size", 0)

        doc_type = DocumentType.UNKNOWN
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            doc_type = DocumentType.PDF
        elif content_type.startswith("image/") or any(
            filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
        ):
            doc_type = DocumentType.IMAGE

        return cls(
            id=blob_name.replace("/", "_").replace(".", "_"),
            filename=filename,
            document_type=doc_type,
            blob_url=blob_url,
            size_bytes=size,
            content_type=content_type,
        )
