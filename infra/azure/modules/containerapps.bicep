@description('Azure region for Hound Forward resources.')
param location string

@description('Deployment environment name.')
param environmentName string

@description('Container Apps environment name.')
param containerAppsEnvironmentName string

@description('API container app name.')
param apiAppName string

@description('Agent container app name.')
param agentAppName string

@description('Worker job name.')
param workerJobName string

@description('API container image.')
param apiImage string

@description('Agent container image.')
param agentImage string

@description('Worker container image.')
param workerImage string

@description('Blob endpoint exposed to the application.')
param blobAccountUrl string

@description('Blob container exposed to the application.')
param blobContainerName string

@description('Service Bus namespace exposed to the application.')
param serviceBusNamespaceName string

@description('Service Bus queue exposed to the worker runtime.')
param serviceBusRunQueueName string

@description('Service Bus queue exposed to the agent runtime.')
param serviceBusAgentQueueName string

@description('Metadata database URL secret value.')
@secure()
param metadataDatabaseUrl string

@description('Storage account resource id for RBAC.')
param storageAccountResourceId string

@description('Service Bus namespace resource id for RBAC.')
param serviceBusNamespaceResourceId string

var blobDataContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var serviceBusDataSenderRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39')
var serviceBusDataReceiverRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
var metadataDatabaseSecretName = 'hf-metadata-database-url'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: last(split(storageAccountResourceId, '/'))
}

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2024-01-01' existing = {
  name: last(split(serviceBusNamespaceResourceId, '/'))
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'hound-${environmentName}-logs'
  location: location
  properties: {
    retentionInDays: 30
  }
}

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: apiAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: [
        {
          name: metadataDatabaseSecretName
          value: metadataDatabaseUrl
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            {
              name: 'HF_METADATA_DATABASE_URL'
              secretRef: metadataDatabaseSecretName
            }
            {
              name: 'HF_AZURE_BLOB_ACCOUNT_URL'
              value: blobAccountUrl
            }
            {
              name: 'HF_AZURE_BLOB_CONTAINER'
              value: blobContainerName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_NAMESPACE'
              value: serviceBusNamespaceName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_QUEUE'
              value: serviceBusRunQueueName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_RUN_QUEUE'
              value: serviceBusRunQueueName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_AGENT_QUEUE'
              value: serviceBusAgentQueueName
            }
          ]
        }
      ]
    }
  }
}

resource agentApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: agentAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      secrets: [
        {
          name: metadataDatabaseSecretName
          value: metadataDatabaseUrl
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'agent'
          image: agentImage
          env: [
            {
              name: 'HF_METADATA_DATABASE_URL'
              secretRef: metadataDatabaseSecretName
            }
            {
              name: 'HF_AZURE_BLOB_ACCOUNT_URL'
              value: blobAccountUrl
            }
            {
              name: 'HF_AZURE_BLOB_CONTAINER'
              value: blobContainerName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_NAMESPACE'
              value: serviceBusNamespaceName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_RUN_QUEUE'
              value: serviceBusRunQueueName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_AGENT_QUEUE'
              value: serviceBusAgentQueueName
            }
          ]
        }
      ]
    }
  }
}

resource workerJob 'Microsoft.App/jobs@2024-03-01' = {
  name: workerJobName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerEnv.id
    configuration: {
      triggerType: 'Manual'
      replicaRetryLimit: 2
      replicaTimeout: 3600
      secrets: [
        {
          name: metadataDatabaseSecretName
          value: metadataDatabaseUrl
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerImage
          env: [
            {
              name: 'HF_METADATA_DATABASE_URL'
              secretRef: metadataDatabaseSecretName
            }
            {
              name: 'HF_AZURE_BLOB_ACCOUNT_URL'
              value: blobAccountUrl
            }
            {
              name: 'HF_AZURE_BLOB_CONTAINER'
              value: blobContainerName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_NAMESPACE'
              value: serviceBusNamespaceName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_QUEUE'
              value: serviceBusRunQueueName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_RUN_QUEUE'
              value: serviceBusRunQueueName
            }
            {
              name: 'HF_AZURE_SERVICE_BUS_AGENT_QUEUE'
              value: serviceBusAgentQueueName
            }
          ]
        }
      ]
    }
  }
}

resource apiBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountResourceId, apiApp.name, blobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: blobDataContributorRoleId
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource agentBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountResourceId, agentApp.name, blobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: blobDataContributorRoleId
    principalId: agentApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource workerBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountResourceId, workerJob.name, blobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: blobDataContributorRoleId
    principalId: workerJob.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource apiServiceBusSendAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespaceResourceId, apiApp.name, serviceBusDataSenderRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: serviceBusDataSenderRoleId
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource agentServiceBusReceiveAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespaceResourceId, agentApp.name, serviceBusDataReceiverRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: serviceBusDataReceiverRoleId
    principalId: agentApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource agentServiceBusSendAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespaceResourceId, agentApp.name, serviceBusDataSenderRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: serviceBusDataSenderRoleId
    principalId: agentApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource workerServiceBusReceiveAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespaceResourceId, workerJob.name, serviceBusDataReceiverRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: serviceBusDataReceiverRoleId
    principalId: workerJob.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output logAnalyticsWorkspaceName string = logAnalytics.name
output containerAppsEnvironmentId string = containerEnv.id
output metadataDatabaseUrlSecretName string = metadataDatabaseSecretName
