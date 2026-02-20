@description('Base name for the storage account')
param baseName string

@description('Location for the storage account')
param location string = resourceGroup().location

@description('Tags to apply to resources')
param tags object = {}

// Generate a unique suffix based on resource group ID for global uniqueness
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = toLower(take('${replace(baseName, '-', '')}${uniqueSuffix}', 24))

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource landingZoneContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'landing-zone'
  properties: {
    publicAccess: 'None'
  }
}

resource extractedDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'extracted-data'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
output landingZoneContainerName string = landingZoneContainer.name
output extractedDataContainerName string = extractedDataContainer.name
