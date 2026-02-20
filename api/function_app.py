import json
import logging
import os
import azure.functions as func
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from ocr import process_document
from utils import BlobStorageHelper, EventGridPublisher

app = func.FunctionApp()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_mistral_credentials():
    key_vault_uri = os.environ.get("KEY_VAULT_URI")
    if key_vault_uri:
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_uri, credential=credential)
            api_key = client.get_secret("MistralApiKey").value
            os.environ["MISTRAL_API_KEY"] = api_key
            logger.info("Loaded Mistral API key from Key Vault")
        except Exception as e:
            logger.warning(f"Could not load from Key Vault: {e}")


_load_mistral_credentials()


@app.blob_trigger(
    arg_name="blob",
    path="landing-zone/{name}",
    connection="AzureWebJobsStorage"
)
async def document_processor(blob: func.InputStream):
    blob_name = blob.name.replace("landing-zone/", "") if blob.name else "unknown"
    logger.info(f"Blob trigger fired for: {blob_name}, Size: {blob.length} bytes")

    try:
        blob_content = blob.read()

        storage_helper = BlobStorageHelper()
        event_publisher = EventGridPublisher()

        properties = {
            "content_type": blob.metadata.get("content_type", "application/pdf") if blob.metadata else "application/pdf",
            "size": blob.length or 0
        }

        result = await process_document(
            blob_name=blob_name,
            blob_content=blob_content,
            blob_properties=properties,
            storage_helper=storage_helper,
            event_publisher=event_publisher
        )

        logger.info(f"Document processed successfully: {result['document']['id']}")

        await storage_helper.close()
        await event_publisher.close()

    except Exception as e:
        logger.error(f"Error processing blob {blob_name}: {str(e)}")
        raise


@app.route(route="upload", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def upload_document(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Upload endpoint called")

    try:
        file = req.files.get("file")
        if not file:
            body = req.get_body()
            if body:
                filename = req.headers.get("X-Filename", "uploaded_document.pdf")
                content_type = req.headers.get("Content-Type", "application/pdf")
                file_content = body
            else:
                return func.HttpResponse(
                    json.dumps({"error": "No file provided"}),
                    status_code=400,
                    mimetype="application/json"
                )
        else:
            filename = file.filename
            content_type = file.content_type or "application/pdf"
            file_content = file.read()

        storage_helper = BlobStorageHelper()
        event_publisher = EventGridPublisher()

        properties = {
            "content_type": content_type,
            "size": len(file_content)
        }

        result = await process_document(
            blob_name=filename,
            blob_content=file_content,
            blob_properties=properties,
            storage_helper=storage_helper,
            event_publisher=event_publisher
        )

        await storage_helper.close()
        await event_publisher.close()

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="documents", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def list_documents(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("List documents endpoint called")

    try:
        storage_helper = BlobStorageHelper()
        results = await storage_helper.list_results()
        await storage_helper.close()

        documents = {}
        for result in results:
            base_name = result["name"].rsplit(".", 1)[0]
            if base_name not in documents:
                documents[base_name] = {
                    "id": base_name,
                    "exports": {}
                }
            ext = result["name"].rsplit(".", 1)[-1]
            documents[base_name]["exports"][ext] = result

        return func.HttpResponse(
            json.dumps({"documents": list(documents.values())}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="documents/{doc_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_document(req: func.HttpRequest) -> func.HttpResponse:
    doc_id = req.route_params.get("doc_id", "")
    logger.info(f"Get document endpoint called for: {doc_id}")

    try:
        storage_helper = BlobStorageHelper()

        json_content = await storage_helper.download_blob(
            container=storage_helper.extracted_data_container,
            blob_name=f"{doc_id}.json"
        )

        await storage_helper.close()

        return func.HttpResponse(
            json_content,
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Get document error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Document not found: {doc_id}"}),
            status_code=404,
            mimetype="application/json"
        )


@app.route(route="documents/{doc_id}/export", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def export_document(req: func.HttpRequest) -> func.HttpResponse:
    doc_id = req.route_params.get("doc_id", "")
    format_type = req.params.get("format", "json")
    logger.info(f"Export document endpoint called for: {doc_id}, format: {format_type}")

    format_map = {
        "json": ("application/json", "json"),
        "md": ("text/markdown", "md"),
        "markdown": ("text/markdown", "md"),
        "csv": ("text/csv", "csv"),
        "xml": ("application/xml", "xml")
    }

    if format_type not in format_map:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid format: {format_type}. Supported: json, md, csv, xml"}),
            status_code=400,
            mimetype="application/json"
        )

    mime_type, ext = format_map[format_type]

    try:
        storage_helper = BlobStorageHelper()

        content = await storage_helper.download_blob(
            container=storage_helper.extracted_data_container,
            blob_name=f"{doc_id}.{ext}"
        )

        await storage_helper.close()

        return func.HttpResponse(
            content,
            status_code=200,
            mimetype=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={doc_id}.{ext}"
            }
        )

    except Exception as e:
        logger.error(f"Export document error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Export not found: {doc_id}.{ext}"}),
            status_code=404,
            mimetype="application/json"
        )


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "service": "document-processor",
            "version": "1.0.0"
        }),
        status_code=200,
        mimetype="application/json"
    )
