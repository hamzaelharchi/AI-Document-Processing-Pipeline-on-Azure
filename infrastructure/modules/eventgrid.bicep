@description('Base name for Event Grid resources')
param baseName string

@description('Location for Event Grid resources')
param location string = resourceGroup().location

@description('Tags to apply to resources')
param tags object = {}

resource eventGridTopic 'Microsoft.EventGrid/topics@2023-12-15-preview' = {
  name: '${baseName}-events'
  location: location
  tags: tags
  properties: {
    inputSchema: 'CloudEventSchemaV1_0'
    publicNetworkAccess: 'Enabled'
  }
}

output eventGridTopicId string = eventGridTopic.id
output eventGridTopicName string = eventGridTopic.name
output eventGridTopicEndpoint string = eventGridTopic.properties.endpoint
