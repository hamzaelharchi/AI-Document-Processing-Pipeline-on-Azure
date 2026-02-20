@description('Base name for all resources')
param baseName string = 'docpipeline'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environmentName string = 'dev'

var tags = {
  project: 'ai-document-pipeline'
  environment: environmentName
}

var resourceBaseName = '${baseName}-${environmentName}'

// Monitoring (deploy first for instrumentation)
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    baseName: resourceBaseName
    location: location
    tags: tags
  }
}

// Storage Account
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    baseName: resourceBaseName
    location: location
    tags: tags
  }
}

// Key Vault (created first, role assignment added after Function App)
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    baseName: resourceBaseName
    location: location
    tags: tags
  }
}

// Function App (depends on Key Vault for URI)
module functionApp 'modules/function.bicep' = {
  name: 'functionApp'
  params: {
    baseName: resourceBaseName
    location: location
    tags: tags
    storageAccountName: storage.outputs.storageAccountName
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    keyVaultUri: keyVault.outputs.keyVaultUri
  }
}

// Key Vault role assignment for Function App (after both are created)
module keyVaultRoleAssignment 'modules/keyvault-role.bicep' = {
  name: 'keyvaultRole'
  params: {
    keyVaultName: keyVault.outputs.keyVaultName
    principalId: functionApp.outputs.functionAppPrincipalId
  }
}

// Event Grid
module eventGrid 'modules/eventgrid.bicep' = {
  name: 'eventGrid'
  params: {
    baseName: resourceBaseName
    location: location
    tags: tags
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name

output STORAGE_ACCOUNT_NAME string = storage.outputs.storageAccountName
output LANDING_ZONE_CONTAINER string = storage.outputs.landingZoneContainerName
output EXTRACTED_DATA_CONTAINER string = storage.outputs.extractedDataContainerName

output FUNCTION_APP_NAME string = functionApp.outputs.functionAppName
output FUNCTION_APP_URL string = functionApp.outputs.functionAppUrl

output KEY_VAULT_NAME string = keyVault.outputs.keyVaultName
output KEY_VAULT_URI string = keyVault.outputs.keyVaultUri

output EVENT_GRID_TOPIC_NAME string = eventGrid.outputs.eventGridTopicName
output EVENT_GRID_ENDPOINT string = eventGrid.outputs.eventGridTopicEndpoint

output APP_INSIGHTS_NAME string = monitoring.outputs.appInsightsName
output APP_INSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString
