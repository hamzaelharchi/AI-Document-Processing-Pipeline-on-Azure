import logging
import os
from datetime import datetime
from azure.eventgrid.aio import EventGridPublisherClient
from azure.eventgrid import EventGridEvent
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class EventGridPublisher:
    def __init__(
        self,
        topic_endpoint: str | None = None,
        topic_key: str | None = None
    ):
        self.topic_endpoint = topic_endpoint or os.environ.get("EVENT_GRID_TOPIC_ENDPOINT", "")
        self.topic_key = topic_key or os.environ.get("EVENT_GRID_TOPIC_KEY", "")
        self._client: EventGridPublisherClient | None = None

    def _get_client(self) -> EventGridPublisherClient | None:
        if not self.topic_endpoint or not self.topic_key:
            logger.warning("Event Grid not configured, skipping event publishing")
            return None

        if self._client is None:
            credential = AzureKeyCredential(self.topic_key)
            self._client = EventGridPublisherClient(
                endpoint=self.topic_endpoint,
                credential=credential
            )
        return self._client

    async def publish_document_processed(
        self,
        document_id: str,
        filename: str,
        confidence: float,
        exports: dict[str, str]
    ):
        client = self._get_client()
        if not client:
            return

        event = EventGridEvent(
            event_type="Document.Processed",
            subject=f"documents/{document_id}",
            data={
                "document_id": document_id,
                "filename": filename,
                "confidence": confidence,
                "exports": exports,
                "processed_at": datetime.utcnow().isoformat()
            },
            data_version="1.0"
        )

        try:
            await client.send([event])
            logger.info(f"Published Document.Processed event for {document_id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")

    async def publish_document_failed(
        self,
        document_id: str,
        filename: str,
        error: str
    ):
        client = self._get_client()
        if not client:
            return

        event = EventGridEvent(
            event_type="Document.Failed",
            subject=f"documents/{document_id}",
            data={
                "document_id": document_id,
                "filename": filename,
                "error": error,
                "failed_at": datetime.utcnow().isoformat()
            },
            data_version="1.0"
        )

        try:
            await client.send([event])
            logger.info(f"Published Document.Failed event for {document_id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
