# Architecture

## System Overview

The AI Document Processing Pipeline is a serverless, event-driven system built on Microsoft Azure that automatically extracts structured information from documents using Mistral Document AI.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              AZURE RESOURCE GROUP                                 │
│                                                                                   │
│  ┌─────────────┐                                 ┌─────────────────────────────┐  │
│  │   Simple    │                                 │       Event Grid            │  │
│  │  HTML/JS    │ (Local)                         │        Topic                │  │
│  │  Frontend   │                                 └──────────────▲──────────────┘  │
│  └──────┬──────┘                                                │                 │
│         │ HTTP                                                  │ Publish         │
│         ▼                                                       │                 │
│  ┌─────────────────────────────────────────┐                   │                 │
│  │           Azure Functions               │                   │                 │
│  │  ┌─────────────────────────────────┐   │                   │                 │
│  │  │  HTTP Triggers                  │   │                   │                 │
│  │  │  - POST /api/upload             │   │                   │                 │
│  │  │  - GET  /api/documents          │   │───────────────────┘                 │
│  │  │  - GET  /api/documents/{id}     │   │                                     │
│  │  │  - GET  /api/health             │   │                                     │
│  │  └─────────────────────────────────┘   │                                     │
│  │  ┌─────────────────────────────────┐   │      ┌──────────────────────────┐  │
│  │  │  Blob Trigger                   │◀──┼──────│    Landing Zone          │  │
│  │  │  - document_processor           │   │      │    (Blob Container)      │  │
│  │  └───────────────┬─────────────────┘   │      └──────────────────────────┘  │
│  └──────────────────┼─────────────────────┘                                     │
│                     │                                                            │
│                     │ Extract                                                    │
│                     ▼                                                            │
│  ┌─────────────────────────────────────────┐      ┌──────────────────────────┐  │
│  │        Azure AI Foundry                 │      │    Extracted Data        │  │
│  │        (Mistral Document AI)            │─────▶│    (Blob Container)      │  │
│  │        mistral-document-ai-2505         │      │    - .md, .json, .xml    │  │
│  └─────────────────────────────────────────┘      └──────────────────────────┘  │
│                                                                                   │
│  ┌─────────────────────────────────────────┐      ┌──────────────────────────┐  │
│  │           Key Vault                     │      │    Application Insights  │  │
│  │           (Secrets)                     │      │    (Monitoring)          │  │
│  └─────────────────────────────────────────┘      └──────────────────────────┘  │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Document Upload

1. User uploads document via HTTP API or directly to landing-zone container
2. Blob trigger activates Azure Function
3. Function downloads blob content

### 2. OCR Processing

1. Document sent to Mistral Document AI via Azure AI Foundry
2. OCR extracts text, tables, and structured content as Markdown
3. Confidence scores calculated for the extraction

### 3. Export & Storage

1. Results exported to multiple formats (MD, JSON, XML)
2. All formats uploaded to extracted-data container
3. Document.Processed event published to Event Grid

### 4. Downstream Integration

Event Grid enables:
- Logic Apps workflows
- Power Automate flows
- Custom webhook handlers
- RPA bot triggers

## Components

### Frontend (Simple HTML/JS)

- **Local only**: Runs in browser, no Azure hosting
- **Features**: Upload zone, document list, extraction viewer, export buttons
- **Tech**: Vanilla HTML, CSS, JavaScript

### Backend (Azure Functions)

- **Runtime**: Python 3.11
- **Triggers**: Blob trigger, HTTP triggers
- **Modules**:
  - `ocr/`: Mistral client, extractor, handler
  - `exporters/`: MD, JSON, CSV, XML exporters
  - `utils/`: Blob helpers, Event Grid publisher

### AI/OCR (Azure AI Foundry)

- **Model**: Mistral Document AI (`mistral-document-ai-2505`)
- **Endpoint**: `https://<resource>.services.ai.azure.com/providers/mistral/azure/ocr`
- **Capabilities**: PDF and image extraction, table detection, multilingual support

### Infrastructure (Bicep)

- **Modular design**: Separate modules for each resource type
- **Resources**: Storage, Function App, Key Vault, Event Grid, App Insights
- **azd support**: Tagged for Azure Developer CLI deployment

## Security

- **Managed Identity**: Function App uses system-assigned identity
- **Key Vault**: Can store API keys securely
- **RBAC**: Storage Blob Data Contributor role for Function App
- **HTTPS**: All traffic encrypted in transit
- **CORS**: Configured for local development

## Scalability

- **Consumption Plan**: Auto-scales based on demand (0 to N instances)
- **Blob Trigger**: Handles concurrent uploads automatically
- **Event Grid**: High-throughput event delivery

## Monitoring

- **Application Insights**: Request tracing, exceptions, metrics
- **Log Analytics**: Centralized logging workspace
- **Alerts**: Can be configured for failures or performance issues

## Cost Optimization

- **Consumption Plan**: Pay only for execution time
- **Storage**: Standard LRS for cost efficiency
- **Free tiers**: App Insights and Event Grid have generous free tiers
