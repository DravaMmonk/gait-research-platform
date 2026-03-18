@description('Azure region for Hound Forward resources.')
param location string

@description('Azure Service Bus namespace name.')
param serviceBusNamespaceName string

@description('Queue name for pipeline run execution.')
param runQueueName string = 'runs'

@description('Queue name for agent execution.')
param agentQueueName string = 'agent-runs'

resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: serviceBusNamespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource runQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: runQueueName
  parent: serviceBus
  properties: {
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 5
  }
}

resource agentQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: agentQueueName
  parent: serviceBus
  properties: {
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 5
  }
}

output serviceBusNamespaceId string = serviceBus.id
output serviceBusNamespaceName string = serviceBus.name
output runQueueName string = runQueueName
output agentQueueName string = agentQueueName
