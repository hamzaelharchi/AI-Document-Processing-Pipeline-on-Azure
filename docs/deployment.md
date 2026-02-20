# Deployment Guide

## Prerequisites

- Azure subscription
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Developer CLI (azd)](https://aka.ms/azd-install)
- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- [Node.js 20+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- Mistral API key from [Azure AI Foundry](https://ai.azure.com/)

## Quick Deploy with Azure Developer CLI

The fastest way to deploy is using `azd`:

```bash
# Clone the repository
git clone https://github.com/<your-username>/AI-Document-Processing-Pipeline-on-Azure.git
cd AI-Document-Processing-Pipeline-on-Azure

# Login to Azure
azd auth login

# Deploy everything
azd up
```

This will:
1. Provision all Azure resources (Storage, Function App, Key Vault, Event Grid, App Insights)
2. Deploy the Function App
3. Configure all connections

After deployment, add your Mistral API key:

```bash
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name MistralApiKey \
  --value <your-mistral-api-key>
```

## Manual Deployment

### 1. Create Resource Group

```bash
az group create \
  --name doc-pipeline-rg \
  --location westeurope
```

### 2. Deploy Infrastructure

```bash
az deployment group create \
  --resource-group doc-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters environmentName=dev
```

### 3. Configure Secrets

```bash
# Get Key Vault name from deployment output
KEY_VAULT_NAME=$(az deployment group show \
  --resource-group doc-pipeline-rg \
  --name main \
  --query properties.outputs.keyVaultName.value -o tsv)

# Add Mistral API key
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name MistralApiKey \
  --value <your-mistral-api-key>
```

### 4. Deploy Function App

```bash
cd api
pip install -r requirements.txt

# Get Function App name
FUNC_APP_NAME=$(az deployment group show \
  --resource-group doc-pipeline-rg \
  --name main \
  --query properties.outputs.functionAppName.value -o tsv)

# Deploy
func azure functionapp publish $FUNC_APP_NAME
```

### 5. Run Frontend Locally

The frontend is a simple HTML/JS application that runs locally:

```bash
cd web
# Open index.html in browser, or use a simple server:
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## Environment Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `MISTRAL_ENDPOINT` | Azure AI Foundry endpoint |
| `MISTRAL_API_KEY` | Mistral API key (from Key Vault) |
| `STORAGE_ACCOUNT_NAME` | Azure Storage account name |
| `KEY_VAULT_URI` | Key Vault URI |
| `EVENT_GRID_TOPIC_ENDPOINT` | Event Grid topic endpoint |

### Local Development

1. Copy the example settings:

```bash
cp api/local.settings.json.example api/local.settings.json
```

2. Start Azurite (local storage emulator):

```bash
azurite --silent --location ./azurite-data
```

3. Run the Function App:

```bash
cd api
func start
```

4. Run the frontend:

```bash
cd web
python -m http.server 8080
# Open http://localhost:8080
```

5. Update API URL in `web/index.html` to `http://localhost:7071/api` for local development.

## CI/CD with GitHub Actions

### Setup

1. Create Azure Service Principal:

```bash
az ad sp create-for-rbac \
  --name "doc-pipeline-cicd" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/doc-pipeline-rg \
  --sdk-auth
```

2. Add GitHub Secrets:

| Secret | Value |
|--------|-------|
| `AZURE_CREDENTIALS` | Service principal JSON output |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID |
| `AZURE_RESOURCE_GROUP` | Resource group name |
| `FUNCTION_APP_NAME` | Function app name |
| `API_URL` | Function app URL |

### Workflows

- **CI** (`ci.yml`): Runs on PRs - lint, test, build
- **Deploy** (`deploy.yml`): Runs on merge to main - deploys to Azure

## Troubleshooting

### Common Issues

**Function App not processing documents**

1. Check Application Insights for errors
2. Verify Mistral API key is set in Key Vault
3. Ensure Function App has Key Vault access

**Frontend can't connect to API**

1. Check CORS settings in Function App
2. Verify `API_URL` in `web/index.html` is correct
3. Check network tab for specific errors

**Blob trigger not firing**

1. Verify storage connection string
2. Check container name matches trigger configuration
3. Look for poison messages in storage

### Logs

```bash
# Stream Function App logs
func azure functionapp logstream <function-app-name>

# Query Application Insights
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "traces | where timestamp > ago(1h)"
```
