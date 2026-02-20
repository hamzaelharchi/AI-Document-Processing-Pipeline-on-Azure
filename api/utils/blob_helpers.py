import logging
import os
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class BlobStorageHelper:
    def __init__(
        self,
        account_name: str | None = None,
        landing_zone_container: str = "landing-zone",
        extracted_data_container: str = "extracted-data"
    ):
        self.account_name = account_name or os.environ.get("STORAGE_ACCOUNT_NAME", "")
        self.landing_zone_container = landing_zone_container
        self.extracted_data_container = extracted_data_container
        self.account_url = f"https://{self.account_name}.blob.core.windows.net"
        self._client: BlobServiceClient | None = None

    async def _get_client(self) -> BlobServiceClient:
        if self._client is None:
            connection_string = os.environ.get("AzureWebJobsStorage")
            if connection_string and "UseDevelopmentStorage" not in connection_string:
                self._client = BlobServiceClient.from_connection_string(connection_string)
            else:
                credential = DefaultAzureCredential()
                self._client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
        return self._client

    async def download_blob(self, container: str, blob_name: str) -> bytes:
        client = await self._get_client()
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        download = await blob_client.download_blob()
        return await download.readall()

    async def get_blob_properties(self, container: str, blob_name: str) -> dict:
        client = await self._get_client()
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        props = await blob_client.get_blob_properties()
        return {
            "content_type": props.content_settings.content_type,
            "size": props.size,
            "created_on": props.creation_time,
            "last_modified": props.last_modified
        }

    async def upload_result(
        self,
        blob_name: str,
        content: str,
        content_type: str = "text/plain"
    ) -> str:
        client = await self._get_client()
        blob_client = client.get_blob_client(
            container=self.extracted_data_container,
            blob=blob_name
        )

        await blob_client.upload_blob(
            content.encode("utf-8"),
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True
        )

        logger.info(f"Uploaded result to {self.extracted_data_container}/{blob_name}")
        return blob_client.url

    async def list_results(self, prefix: str = "") -> list[dict]:
        client = await self._get_client()
        container_client = client.get_container_client(self.extracted_data_container)

        results = []
        async for blob in container_client.list_blobs(name_starts_with=prefix):
            results.append({
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_settings.content_type if blob.content_settings else None,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None
            })

        return results

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
