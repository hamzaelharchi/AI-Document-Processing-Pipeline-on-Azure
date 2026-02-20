# API Reference

## Base URL

- **Local**: `http://localhost:7071/api`
- **Production**: `https://<function-app-name>.azurewebsites.net/api`

## Endpoints

### Health Check

Check if the API is running.

```http
GET /health
```

**Response**

```json
{
  "status": "healthy",
  "service": "document-processor",
  "version": "1.0.0"
}
```

---

### Upload Document

Upload and process a document directly via HTTP.

```http
POST /upload
Content-Type: multipart/form-data
```

**Request Body**

| Field | Type | Description |
|-------|------|-------------|
| file | File | Document file (PDF, PNG, JPG, TIFF) |

**Example (cURL)**

```bash
curl -X POST \
  -F "file=@invoice.pdf" \
  https://<function-app>/api/upload
```

**Response**

```json
{
  "document": {
    "id": "invoice_pdf",
    "filename": "invoice.pdf",
    "status": "completed"
  },
  "extraction": {
    "document_id": "invoice_pdf",
    "confidence": {
      "overall": 0.92,
      "is_low_confidence": false
    },
    "fields": [...],
    "page_count": 1
  },
  "exports": {
    "markdown": "https://storage.blob.core.windows.net/.../invoice.md",
    "json": "https://storage.blob.core.windows.net/.../invoice.json",
    "xml": "https://storage.blob.core.windows.net/.../invoice.xml"
  }
}
```

---

### List Documents

Get a list of all processed documents.

```http
GET /documents
```

**Response**

```json
{
  "documents": [
    {
      "id": "invoice_pdf",
      "exports": {
        "json": {
          "name": "invoice.json",
          "size": 2048,
          "content_type": "application/json"
        },
        "md": {...},
        "xml": {...}
      }
    }
  ]
}
```

---

### Get Document

Get extraction results for a specific document.

```http
GET /documents/{document_id}
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| document_id | string | Document identifier |

**Response**

```json
{
  "document_id": "invoice_pdf",
  "extracted_at": "2024-01-15T10:30:00Z",
  "model_version": "mistral-document-ai-2505",
  "page_count": 1,
  "processing_time_ms": 1500,
  "confidence": {
    "overall": 0.92,
    "is_low_confidence": false
  },
  "fields": [
    {
      "name": "Vendor",
      "value": "Acme Corp",
      "confidence": 0.95
    },
    {
      "name": "Total",
      "value": "$500.00",
      "confidence": 0.88
    }
  ],
  "tables": [],
  "content": {
    "raw_text": "...",
    "markdown": "..."
  }
}
```

---

### Export Document

Download extraction results in a specific format.

```http
GET /documents/{document_id}/export?format={format}
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| document_id | string | Document identifier |

**Query Parameters**

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| format | string | json | json, md, csv, xml |

**Example**

```bash
# Download as Markdown
curl -o invoice.md \
  "https://<function-app>/api/documents/invoice_pdf/export?format=md"

# Download as JSON
curl -o invoice.json \
  "https://<function-app>/api/documents/invoice_pdf/export?format=json"
```

**Response Headers**

```
Content-Type: text/markdown (or application/json, text/csv, application/xml)
Content-Disposition: attachment; filename=invoice_pdf.md
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

**HTTP Status Codes**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 404 | Document not found |
| 500 | Internal server error |

---

## Blob Trigger

Documents can also be processed by uploading directly to the `landing-zone` blob container:

```bash
az storage blob upload \
  --account-name <storage-account> \
  --container-name landing-zone \
  --name invoice.pdf \
  --file ./invoice.pdf
```

The blob trigger will automatically process the document and save results to `extracted-data` container.

---

## Event Grid Events

### Document.Processed

Published when a document is successfully processed.

```json
{
  "eventType": "Document.Processed",
  "subject": "documents/invoice_pdf",
  "data": {
    "document_id": "invoice_pdf",
    "filename": "invoice.pdf",
    "confidence": 0.92,
    "exports": {...},
    "processed_at": "2024-01-15T10:30:00Z"
  }
}
```

### Document.Failed

Published when document processing fails.

```json
{
  "eventType": "Document.Failed",
  "subject": "documents/invoice_pdf",
  "data": {
    "document_id": "invoice_pdf",
    "filename": "invoice.pdf",
    "error": "Error message",
    "failed_at": "2024-01-15T10:30:00Z"
  }
}
```
