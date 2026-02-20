# AI Document Processing Pipeline on Azure

A serverless document processing solution built on Microsoft Azure, featuring AI-powered OCR extraction with confidence scoring and multi-format export.

---

## Overview

This production-ready pipeline automatically extracts structured information from documents using **Azure Functions** and **Mistral OCR** via Azure AI Foundry.

**Key Capabilities:**
- Automatic document ingestion (PDF, images, scans)
- AI-powered text, table, and structured content extraction
- Confidence scoring for extraction quality assessment
- Multi-format export (Markdown, JSON, CSV, XML)
- Event-driven notifications via Event Grid

---

## Architecture

```
┌──────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User   │────▶│  Landing Zone   │────▶│  Azure Function │────▶│   Mistral OCR   │
│          │     │  (Blob Storage) │     │  (Python 3.11)  │     │ (AI Foundry)    │
└──────────┘     └─────────────────┘     └────────┬────────┘     └─────────────────┘
                                                  │
                         ┌────────────────────────┼────────────────────────┐
                         ▼                        ▼                        ▼
                ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                │ Extracted Data  │     │   Event Grid    │     │  App Insights   │
                │ (Blob Storage)  │     │  (Pub/Sub)      │     │  (Monitoring)   │
                └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Processing Flow:**
1. User uploads document via API or directly to Landing Zone blob container
2. Blob trigger activates the Azure Function
3. Function calls Mistral OCR for AI-powered extraction
4. Extraction results are scored for confidence
5. Results exported to multiple formats and saved to output container
6. Event Grid notifies downstream systems

---

## Features

### AI-Powered Document Processing
- **Mistral OCR** (`mistral-ocr-2503`) via Azure AI Foundry
- Extracts text, tables, and complex layouts
- Supports mathematical expressions and formulas
- Multilingual content support

### Confidence Scoring
- Overall document confidence score (0-100%)
- Field-level confidence for granular quality assessment
- Low-confidence flagging for manual review

### Multi-Format Export
| Format | Use Case |
|--------|----------|
| Markdown | Human-readable documentation |
| JSON | API integration, data pipelines |
| CSV | Spreadsheet analysis, tabular data |
| XML | Enterprise systems, legacy integration |

### Production-Ready Design
- Managed identities (no hardcoded secrets)
- Key Vault for secure secret management
- Application Insights for monitoring and diagnostics
- Event-driven architecture for scalability

---

## Technologies

| Category | Service |
|----------|---------|
| **Backend** | Azure Functions (Python 3.11) |
| **Storage** | Azure Blob Storage |
| **AI/OCR** | Mistral OCR via Azure AI Foundry |
| **Events** | Azure Event Grid |
| **Security** | Azure Key Vault, Managed Identity |
| **Monitoring** | Azure Application Insights |
| **IaC** | Bicep (modular templates) |
| **CI/CD** | GitHub Actions |

---

## Project Structure

```
AI-Document-Processing-Pipeline-on-Azure/
├── api/                              # Azure Functions backend
│   ├── function_app.py               # Main entry (blob + HTTP triggers)
│   ├── ocr/
│   │   ├── mistral_client.py         # Mistral API client
│   │   ├── extractor.py              # Extraction with confidence scoring
│   │   └── handler.py                # Processing orchestration
│   ├── models/
│   │   ├── document.py               # Document data model
│   │   └── extraction_result.py      # Extraction result with confidence
│   ├── exporters/
│   │   ├── markdown.py               # Markdown exporter
│   │   ├── json_export.py            # JSON exporter
│   │   ├── csv_export.py             # CSV exporter
│   │   └── xml_export.py             # XML exporter
│   ├── utils/
│   │   ├── blob_helpers.py           # Blob storage utilities
│   │   └── eventgrid.py              # Event Grid publisher
│   ├── requirements.txt
│   └── host.json
│
├── web/                              # Simple HTML/JS frontend (local)
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── infrastructure/                   # Bicep IaC
│   ├── main.bicep                    # Main orchestration
│   └── modules/
│       ├── storage.bicep             # Storage account + containers
│       ├── function.bicep            # Function App
│       ├── keyvault.bicep            # Key Vault
│       ├── eventgrid.bicep           # Event Grid topic
│       └── monitoring.bicep          # App Insights + Log Analytics
│
├── tests/                            # Python tests
│   └── unit/
│
├── docs/                             # Documentation
│   ├── architecture.md
│   ├── api-reference.md
│   └── deployment.md
│
├── .github/workflows/
│   ├── ci.yml                        # CI: lint, test, build
│   └── deploy.yml                    # CD: deploy to Azure
│
├── azure.yaml                        # Azure Developer CLI config
└── README.md
```

---

## Quick Start

### Prerequisites

- Azure subscription
- [Azure Developer CLI (azd)](https://aka.ms/azd-install)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)

### Deploy to Azure

```bash
# Clone the repository
git clone https://github.com/hamzaelharchi/AI-Document-Processing-Pipeline-on-Azure.git
cd AI-Document-Processing-Pipeline-on-Azure

# Login to Azure
azd auth login

# Deploy everything
azd up
```

This will provision:
- Storage Account with landing-zone and extracted-data containers
- Function App (Python 3.11)
- Key Vault for secrets
- Event Grid Topic
- Application Insights

### Post-Deployment Setup

Add your Mistral API key to Key Vault:

```bash
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name MistralApiKey \
  --value <your-mistral-api-key>
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/upload` | POST | Upload document for processing |
| `/api/documents` | GET | List all processed documents |
| `/api/documents/{id}` | GET | Get extraction results |
| `/api/documents/{id}/export?format=json` | GET | Export in specific format |

### Example: Upload Document

```bash
curl -X POST https://<function-app>.azurewebsites.net/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

### Example: Get Results

```bash
curl https://<function-app>.azurewebsites.net/api/documents/<document-id>
```

---

## Local Development

### Backend (Azure Functions)

```bash
cd api
pip install -r requirements.txt

# Copy local settings
cp local.settings.json.example local.settings.json

# Start Azurite (storage emulator) - optional
npm install -g azurite
azurite

# Start Functions
func start
```

### Frontend (Simple Web UI)

```bash
cd web
# Open index.html in browser, or use a simple server:
python -m http.server 8080
```

Then open `http://localhost:8080` and update `API_URL` in the page to point to your Function App.

---

## Sample Output

### Extraction Result (JSON)

```json
{
  "document_id": "abc123",
  "filename": "invoice.pdf",
  "status": "completed",
  "confidence": {
    "overall": 0.94,
    "fields": {
      "vendor": 0.98,
      "invoice_date": 0.95,
      "amount": 0.89
    }
  },
  "extracted_content": "# Invoice\n\n**Vendor:** Contoso Electronics..."
}
```

---

## Use Cases

- **Finance & AP Automation** - Invoice and receipt extraction
- **Logistics** - Bills of lading, delivery notes
- **Healthcare** - Patient forms, ID extraction
- **Insurance** - Claims document processing
- **Legal** - Contract clause extraction
- **HR** - Onboarding forms, resume parsing
- **RPA Integration** - AI intake layer for UiPath, Power Automate

---

## Cost Estimation

| Resource | Estimated Monthly Cost |
|----------|------------------------|
| Function App (Consumption) | $0-5 (pay per execution) |
| Storage Account | $1-5 (depending on volume) |
| Azure AI Foundry (Mistral) | ~$0.01-0.05 per page |
| Event Grid | ~$0.60 per million operations |
| Key Vault | ~$0.03 per 10K operations |
| App Insights | Free tier (5GB/month) |
| **Total (light usage)** | **~$5-15/month** |

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

MIT License
