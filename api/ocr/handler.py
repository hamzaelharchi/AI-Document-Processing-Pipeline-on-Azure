import logging
import os
from datetime import datetime

from models import Document, DocumentStatus
from utils.blob_helpers import BlobStorageHelper
from utils.eventgrid import EventGridPublisher
from .extractor import DocumentExtractor
from .mistral_client import MistralOCRClient

logger = logging.getLogger(__name__)


async def process_document(
    blob_name: str,
    blob_content: bytes,
    blob_properties: dict,
    storage_helper: BlobStorageHelper,
    event_publisher: EventGridPublisher | None = None
) -> dict:
    document = Document.from_blob_properties(
        blob_name=blob_name,
        blob_url=f"{storage_helper.account_url}/{storage_helper.landing_zone_container}/{blob_name}",
        properties=blob_properties
    )
    document.status = DocumentStatus.PROCESSING

    logger.info(f"Processing document: {document.id} ({document.filename})")

    try:
        mistral_endpoint = os.environ.get("MISTRAL_ENDPOINT", "")
        mistral_api_key = os.environ.get("MISTRAL_API_KEY", "")

        if not mistral_endpoint or not mistral_api_key:
            raise ValueError("Mistral endpoint and API key must be configured")

        client = MistralOCRClient(
            endpoint=mistral_endpoint,
            api_key=mistral_api_key
        )
        extractor = DocumentExtractor(client)

        result = await extractor.extract(
            document_id=document.id,
            file_bytes=blob_content,
            content_type=document.content_type or "application/pdf",
            filename=document.filename
        )

        from exporters import MarkdownExporter, JsonExporter, CsvExporter, XmlExporter

        base_name = os.path.splitext(document.filename)[0]
        exports = {}

        md_exporter = MarkdownExporter()
        exports["markdown"] = await storage_helper.upload_result(
            f"{base_name}.md",
            md_exporter.export(result),
            "text/markdown"
        )

        json_exporter = JsonExporter()
        exports["json"] = await storage_helper.upload_result(
            f"{base_name}.json",
            json_exporter.export(result),
            "application/json"
        )

        if result.tables:
            csv_exporter = CsvExporter()
            exports["csv"] = await storage_helper.upload_result(
                f"{base_name}.csv",
                csv_exporter.export(result),
                "text/csv"
            )

        xml_exporter = XmlExporter()
        exports["xml"] = await storage_helper.upload_result(
            f"{base_name}.xml",
            xml_exporter.export(result),
            "application/xml"
        )

        document.status = DocumentStatus.COMPLETED
        document.processed_at = datetime.utcnow()

        if event_publisher:
            await event_publisher.publish_document_processed(
                document_id=document.id,
                filename=document.filename,
                confidence=result.confidence.overall,
                exports=exports
            )

        logger.info(f"Successfully processed document: {document.id}")

        return {
            "document": document.to_dict(),
            "extraction": result.to_dict(),
            "exports": exports
        }

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        logger.error(f"Failed to process document {document.id}: {str(e)}")

        if event_publisher:
            await event_publisher.publish_document_failed(
                document_id=document.id,
                filename=document.filename,
                error=str(e)
            )

        raise
